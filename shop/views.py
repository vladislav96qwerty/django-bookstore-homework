import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q

from .cart import Cart
from .forms import BookForm
from .models import Book, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


# ─── Книги ───────────────────────────────────────────────────────────────────

class BookListView(ListView):
    model = Book
    template_name = 'shop/book_list.html'
    context_object_name = 'books'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = 'shop/book_detail.html'
    context_object_name = 'book'


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


# ─── Кошик ───────────────────────────────────────────────────────────────────

@login_required
def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart.html', {'cart': cart})


@login_required
def cart_add(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.add(book=book, quantity=1)
    return redirect('shop:cart_detail')


@login_required
def cart_remove(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect('shop:cart_detail')


# ─── Stripe Checkout ─────────────────────────────────────────────────────────

@login_required
def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('shop:cart_detail')

    line_items = []
    for item in cart:
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': item['title'],
                },
                'unit_amount': int(float(item['price']) * 100),
            },
            'quantity': item['quantity'],
        })

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri(reverse('shop:payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('shop:cart_detail')),
    )

    return redirect(session.url, code=303)


@login_required
def payment_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('shop:book_list')

    cart = Cart(request)

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

    # Відправка email
    send_mail(
        subject=f'Замовлення #{order.id} підтверджено',
        message=f'Дякуємо за покупку! Ваше замовлення #{order.id} на суму ${order.get_total_price()} успішно оплачено.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[request.user.email],
        fail_silently=True,
    )

    return render(request, 'shop/payment_success.html', {'order': order})


@login_required
def payment_cancel(request):
    return render(request, 'shop/payment_cancel.html')


# ─── Webhook ─────────────────────────────────────────────────────────────────

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