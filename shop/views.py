"""
shop/views.py — views for the bookstore shop application.

Includes synchronous CBVs for book CRUD, cart management,
Stripe checkout flow, async JSON API views, and a Stripe webhook handler.
"""

import stripe
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from django.views import View
from asgiref.sync import sync_to_async

from .cart import Cart
from .forms import BookForm
from .models import Book, Order, OrderItem, Category

if hasattr(settings, 'STRIPE_SECRET_KEY'):
    stripe.api_key = settings.STRIPE_SECRET_KEY


# ── Книги (sync CBV) ──────────────────────────────────────────────────────────

# view cache: весь response BookListView кешується на 15 хвилин
@method_decorator(cache_page(60 * 15, key_prefix='book_list'), name='dispatch')
class BookListView(ListView):
    """
    Display a paginated list of books with optional search and language switching.
    """

    model = Book
    template_name = 'shop/book_list.html'
    context_object_name = 'books'
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('language')
        if lang in ['uk', 'en']:
            from django.utils import translation
            translation.activate(lang)
            self._new_lang = lang
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        query = self.request.GET.get('q', '').strip()[:100]
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '').strip()
        return context

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        if hasattr(self, '_new_lang'):
            response.set_cookie(
                settings.LANGUAGE_COOKIE_NAME,
                self._new_lang,
                max_age=getattr(settings, 'LANGUAGE_COOKIE_AGE', 86400 * 365),
            )
        return response


class BookDetailView(DetailView):
    """
    Display the detail page for a single book.
    Low-level cache: об'єкт книги кешується в Redis на 30 хвилин.
    Інвалідація відбувається через signal у shop/signals.py.
    """

    model = Book
    template_name = 'shop/book_detail.html'
    context_object_name = 'book'

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg)
        cache_key = f'book_detail_{pk}'

        book = cache.get(cache_key)
        if book is None:
            book = get_object_or_404(
                Book.objects.select_related('category'), pk=pk
            )
            cache.set(cache_key, book, timeout=60 * 30)

        return book


class BookCreateView(PermissionRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    success_url = reverse_lazy('shop:book_list')
    permission_required = "shop.add_book"


class BookUpdateView(PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    permission_required = "shop.change_book"

    def get_success_url(self):
        return reverse_lazy('shop:book_detail', kwargs={'pk': self.object.pk})


class BookDeleteView(PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = 'shop/book_confirm_delete.html'
    success_url = reverse_lazy('shop:book_list')
    permission_required = "shop.delete_book"


# ── Кошик (sync) ──────────────────────────────────────────────────────────────

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})


def cart_add(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.add(book=book, quantity=1)
    return redirect('shop:cart_detail')


def cart_remove(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect('shop:cart_detail')


# ── ASYNC VIEWS ───────────────────────────────────────────────────────────────

async def async_book_list(request):
    query = request.GET.get('q', '')

    @sync_to_async
    def fetch_books(q):
        qs = Book.objects.select_related('category').all()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q))
        return list(qs.values('id', 'title', 'author', 'price', 'stock'))

    books = await fetch_books(query)
    return JsonResponse({'books': books, 'count': len(books)})


async def async_book_detail(request, pk):
    @sync_to_async
    def fetch_book(book_id):
        try:
            b = Book.objects.select_related('category').get(pk=book_id)
            return {
                'id': b.id,
                'title': b.title,
                'author': b.author,
                'price': str(b.price),
                'stock': b.stock,
                'description': b.description,
                'category': b.category.name,
            }
        except Book.DoesNotExist:
            return None

    data = await fetch_book(pk)
    if data is None:
        return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse(data)


async def async_catalog(request):
    @sync_to_async
    def fetch_catalog():
        categories = list(
            Category.objects.prefetch_related('books').order_by('name')
        )
        return [
            {
                'name': cat.name,
                'slug': cat.slug,
                'books': list(cat.books.values('id', 'title', 'author', 'price')),
            }
            for cat in categories
        ]

    catalog = await fetch_catalog()
    return render(request, 'shop/catalog.html', {'catalog': catalog})


# ── Stripe Checkout ───────────────────────────────────────────────────────────

@login_required
def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('shop:cart_detail')

    line_items = []
    for item in cart:
        price_cents = int(
            (Decimal(str(item['price'])) * 100).to_integral_value(ROUND_HALF_UP)
        )
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': item['title']},
                'unit_amount': price_cents,
            },
            'quantity': item['quantity'],
        })

    try:
        session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            success_url=(
                request.build_absolute_uri(reverse('shop:payment_success'))
                + '?session_id={CHECKOUT_SESSION_ID}'
            ),
            cancel_url=request.build_absolute_uri(reverse('shop:cart_detail')),
        )
    except stripe.error.StripeError as exc:
        return render(request, 'shop/error.html', {'message': str(exc)}, status=502)

    return redirect(session.url, code=303)


@login_required
def payment_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('shop:book_list')

    cart = Cart(request)
    if not cart:
        existing = Order.objects.filter(stripe_session_id=session_id).first()
        if existing:
            return render(request, 'shop/payment_success.html', {'order': existing})
        return redirect('shop:cart_detail')

    existing = Order.objects.filter(stripe_session_id=session_id).first()
    if existing:
        return render(request, 'shop/payment_success.html', {'order': existing})

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            status='paid',
            stripe_session_id=session_id,
        )
        for item in cart:
            OrderItem.objects.create(
                order=order,
                book=item['book'],
                quantity=item['quantity'],
                price=item['price'],
            )
        cart.clear()

    # Async відправка email через Celery (якщо доступний)
    try:
        from shop.tasks import send_order_confirmation_email
        send_order_confirmation_email.delay(order.id)
    except Exception:
        # fallback: синхронна відправка якщо Celery недоступний
        send_mail(
            subject=f'Order #{order.id} confirmed',
            message=(
                f'Thank you for your purchase! '
                f'Order #{order.id} totalling ${order.get_total_price()} has been paid.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=True,
        )

    return render(request, 'shop/payment_success.html', {'order': order})


@login_required
def payment_cancel(request):
    return render(request, 'shop/payment_cancel.html')


# ── Stripe Webhook ────────────────────────────────────────────────────────────

def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        Order.objects.filter(stripe_session_id=session['id']).update(status='paid')

    return HttpResponse(status=200)
