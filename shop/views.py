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
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
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


# ─── Книги (sync CBV) ─────────────────────────────────────────────────────────

class BookListView(ListView):
    """
    Display a paginated list of books with optional search and language switching.

    Query parameters:
        q (str): Search term matched against title and author (case-insensitive,
            trimmed to 100 characters).
        language (str): One of ``'uk'`` or ``'en'`` — activates the chosen locale
            and persists it via a cookie so LocaleMiddleware picks it up on the
            next request.

    Attributes:
        paginate_by (int): Number of books displayed per page (default 10).
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
        # select_related avoids N+1 when template accesses book.category
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
        # Persist language choice via cookie (LANGUAGE_SESSION_KEY removed in Django 4+)
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

    Args:
        pk (int): Primary key of the book (URL kwarg).

    Returns:
        HttpResponse: Renders ``shop/book_detail.html`` with ``book`` in context,
        or 404 if the book does not exist.
    """

    model = Book
    template_name = 'shop/book_detail.html'
    context_object_name = 'book'


class BookCreateView(PermissionRequiredMixin, CreateView):
    """
    Create a new book record. Requires the ``shop.add_book`` permission.

    Returns:
        HttpResponse: Renders ``shop/book_form.html`` on GET / invalid POST,
        or redirects to the book list on success.
    """

    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    success_url = reverse_lazy('shop:book_list')
    permission_required = "shop.add_book"


class BookUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Update an existing book record. Requires the ``shop.change_book`` permission.

    Args:
        pk (int): Primary key of the book to update (URL kwarg).

    Returns:
        HttpResponse: Renders ``shop/book_form.html`` on GET / invalid POST,
        or redirects to the book detail page on success.
    """

    model = Book
    form_class = BookForm
    template_name = 'shop/book_form.html'
    permission_required = "shop.change_book"

    def get_success_url(self):
        return reverse_lazy('shop:book_detail', kwargs={'pk': self.object.pk})


class BookDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Delete a book record. Requires the ``shop.delete_book`` permission.

    Args:
        pk (int): Primary key of the book to delete (URL kwarg).

    Returns:
        HttpResponse: Renders a confirmation page on GET,
        or redirects to the book list after deletion.
    """

    model = Book
    template_name = 'shop/book_confirm_delete.html'
    success_url = reverse_lazy('shop:book_list')
    permission_required = "shop.delete_book"


# ─── Кошик (sync) ─────────────────────────────────────────────────────────────

def cart_detail(request):
    """
    Display the current session cart contents.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        HttpResponse: Renders ``shop/cart.html`` with the ``cart`` object.
    """
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})


def cart_add(request, book_id):
    """
    Add one copy of a book to the session cart and redirect to the cart page.

    Args:
        request (HttpRequest): The incoming HTTP request.
        book_id (int): Primary key of the book to add.

    Returns:
        HttpResponseRedirect: Redirects to ``shop:cart_detail``,
        or returns 404 if the book does not exist.
    """
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.add(book=book, quantity=1)
    return redirect('shop:cart_detail')


def cart_remove(request, book_id):
    """
    Remove a book from the session cart and redirect to the cart page.

    Args:
        request (HttpRequest): The incoming HTTP request.
        book_id (int): Primary key of the book to remove.

    Returns:
        HttpResponseRedirect: Redirects to ``shop:cart_detail``,
        or returns 404 if the book does not exist.
    """
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect('shop:cart_detail')


# ─── ASYNC VIEWS ──────────────────────────────────────────────────────────────

async def async_book_list(request):
    """
    Async view — return a JSON list of books, optionally filtered by search query.

    GET /shop/api/books/?q=<search_term>

    Args:
        request (HttpRequest): Async-compatible HTTP request.
            Accepts optional ``q`` query parameter for title/author search.

    Returns:
        JsonResponse: ``{"books": [...], "count": N}`` with HTTP 200.
    """
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
    """
    Async view — return JSON details for a single book.

    GET /shop/api/books/<pk>/

    Args:
        request (HttpRequest): Async-compatible HTTP request.
        pk (int): Primary key of the book.

    Returns:
        JsonResponse: Book data dict with HTTP 200,
        or ``{"error": "Not found"}`` with HTTP 404.
    """
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
    """
    Async view — render an HTML catalog grouped by category.

    GET /shop/catalog/

    Args:
        request (HttpRequest): Async-compatible HTTP request.

    Returns:
        HttpResponse: Renders ``shop/catalog.html`` with a ``catalog`` list,
        where each entry contains the category name, slug, and its books.
    """
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


# ─── Stripe Checkout ─────────────────────────────────────────────────────────

@login_required
def checkout(request):
    """
    Create a Stripe Checkout session and redirect the user to the hosted payment page.

    Validates that the cart is non-empty, converts prices to integer cents using
    safe Decimal arithmetic (avoids float precision loss), then creates a Stripe
    session and redirects with HTTP 303.

    Args:
        request (HttpRequest): Authenticated HTTP request.

    Returns:
        HttpResponseRedirect: HTTP 303 redirect to Stripe checkout URL on success.
        HttpResponseRedirect: Redirect to ``shop:cart_detail`` if the cart is empty.
        HttpResponse: Renders ``shop/error.html`` (HTTP 502) on Stripe API error.
    """
    cart = Cart(request)
    if not cart:
        return redirect('shop:cart_detail')

    line_items = []
    for item in cart:
        # Safe cents conversion — avoids float precision loss (e.g. 19.99 → 1998)
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
    """
    Handle a successful Stripe payment callback.

    Retrieves the Stripe session ID from the query string, then idempotently
    creates an ``Order`` (duplicate orders on page refresh are prevented by
    checking for an existing order with the same session ID). Cart is cleared
    atomically together with order creation. A confirmation e-mail is sent
    afterwards (``fail_silently=True`` so a mail failure never breaks the flow).

    Args:
        request (HttpRequest): Authenticated HTTP request. Must contain
            ``session_id`` as a GET parameter (provided by Stripe on redirect).

    Returns:
        HttpResponse: Renders ``shop/payment_success.html`` with ``order`` in context.
        HttpResponseRedirect: Redirects to ``shop:book_list`` if ``session_id`` is absent,
        or to ``shop:cart_detail`` if the cart is empty.
    """
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('shop:book_list')

    cart = Cart(request)
    if not cart:
        # Cart already cleared — order was likely already created
        existing = Order.objects.filter(stripe_session_id=session_id).first()
        if existing:
            return render(request, 'shop/payment_success.html', {'order': existing})
        return redirect('shop:cart_detail')

    # Idempotency: avoid duplicate orders on page refresh
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
        cart.clear()  # inside atomic — clears only after successful DB commit

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
    """
    Render the payment cancelled page.

    Args:
        request (HttpRequest): Authenticated HTTP request.

    Returns:
        HttpResponse: Renders ``shop/payment_cancel.html``.
    """
    return render(request, 'shop/payment_cancel.html')


# ─── Stripe Webhook ───────────────────────────────────────────────────────────

def stripe_webhook(request):
    """
    Handle incoming Stripe webhook events.

    Verifies the event signature using ``STRIPE_WEBHOOK_SECRET``. On a
    ``checkout.session.completed`` event, updates the matching ``Order``
    status to ``'paid'``.

    Args:
        request (HttpRequest): Raw HTTP POST request from Stripe.
            Must contain the ``Stripe-Signature`` header.

    Returns:
        HttpResponse: HTTP 200 on success, HTTP 400 on signature verification failure.
    """
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
