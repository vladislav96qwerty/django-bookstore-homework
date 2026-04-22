# AI Code Review — Django Bookstore Project

> **Reviewed by:** Claude (Anthropic)
> **Date:** 2026-04-22
> **Scope:** 3 most complex views from `shop/views.py`

---

## 1. `payment_success` view

### Original Code

```python
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
```

### AI Recommendations

1. **Idempotency risk** — if the user refreshes the success page, a duplicate `Order` will be created for the same `stripe_session_id`. Fix: check if an order with that session ID already exists before creating.
2. **`cart.clear()` outside the transaction** — if the server crashes after `commit` but before `cart.clear()`, the cart remains non-empty and the page can be re-submitted. Move `cart.clear()` inside `transaction.atomic()`.
3. **Empty cart not checked** — if the cart is empty at success time (e.g. cleared by another tab), an `Order` with zero items is created. Add a guard.
4. **`send_mail` inside the request cycle** — email sending blocks the HTTP response. Acceptable with `EMAIL_BACKEND = console`, but in production this should be a Celery task.
5. **`item['book']` assumes Cart stores the ORM object** — if the cart is session-serialised, `item['book']` may not exist; use `item['book_id']` and fetch safely.

### Final Improved Code

```python
@login_required
def payment_success(request):
    """
    Handle successful Stripe payment.

    Retrieves the Stripe session ID from the query string, creates an Order
    (idempotently), clears the cart, and sends a confirmation e-mail.

    Args:
        request (HttpRequest): The incoming HTTP request. Must be authenticated.

    Returns:
        HttpResponse: Renders ``shop/payment_success.html`` with the order,
        or redirects to the book list / cart on invalid state.
    """
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('shop:book_list')

    cart = Cart(request)
    if not cart:
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
        cart.clear()   # inside transaction — atomic with order creation

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
```

**Changes applied:** idempotency guard, cart empty check, `cart.clear()` moved inside `transaction.atomic()`, added docstring.

---

## 2. `checkout` view

### Original Code

```python
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
                'product_data': {'name': item['title']},
                'unit_amount': int(float(item['price']) * 100),
            },
            'quantity': item['quantity'],
        })

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=(
            request.build_absolute_uri(reverse('shop:payment_success'))
            + '?session_id={CHECKOUT_SESSION_ID}'
        ),
        cancel_url=request.build_absolute_uri(reverse('shop:cart_detail')),
    )

    return redirect(session.url, code=303)
```

### AI Recommendations

1. **`int(float(item['price']) * 100)` loses precision** — `Decimal('19.99') → float → 1998.9999...` which truncates to `1998` cents. Use `int(Decimal(str(item['price'])) * 100)` or `round(..., 0)`.
2. **No error handling for `stripe.checkout.Session.create`** — a `stripe.error.StripeError` will bubble up as a 500. Wrap in try/except and show a user-friendly error.
3. **`payment_method_types=['card']` is deprecated** — Stripe now recommends omitting this field and letting the Dashboard control payment methods.
4. **No stock validation before checkout** — a book could be out of stock by the time the user pays. Check `book.stock >= quantity` before creating the session.

### Final Improved Code

```python
from decimal import Decimal, ROUND_HALF_UP

@login_required
def checkout(request):
    """
    Create a Stripe Checkout session and redirect the user to the hosted page.

    Validates cart contents, checks stock availability, builds Stripe line items
    with safe Decimal-to-cents conversion, and redirects (303) to Stripe.

    Args:
        request (HttpRequest): Authenticated HTTP request.

    Returns:
        HttpResponseRedirect: Redirect to Stripe checkout URL (303)
        or to cart / book list on empty cart / stock error.
    """
    cart = Cart(request)
    if not cart:
        return redirect('shop:cart_detail')

    line_items = []
    for item in cart:
        # Safe cents conversion — avoids float precision loss
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
```

**Changes applied:** safe Decimal→cents conversion, Stripe error handling, removed deprecated `payment_method_types`, added docstring.

---

## 3. `BookListView` (with `get_queryset` + language switching)

### Original Code

```python
class BookListView(ListView):
    model = Book
    template_name = 'shop/book_list.html'
    context_object_name = 'books'
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('language')
        if lang in ['uk', 'en']:
            from django.utils import translation
            translation.activate(lang)
            request.session[translation.LANGUAGE_SESSION_KEY] = lang
        return super().get(request, *args, **kwargs)

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
```

### AI Recommendations

1. **`translation.LANGUAGE_SESSION_KEY` is removed in Django 4.0+** — use `django.conf.settings.LANGUAGE_COOKIE_NAME` and set a cookie, or use `django.middleware.locale.LocaleMiddleware` properly via `i18n_patterns`.
2. **Language change inside `get()` affects the current request only** — after `activate()`, the response must set the language cookie; otherwise the next request reverts to the default language.
3. **`get_queryset` strips to the first 10 results via pagination** but the total count is still correct — this is fine, but adding `select_related('category')` avoids N+1 if the template accesses `book.category`.
4. **Search query not sanitised** — `icontains` is safe against SQL injection via ORM, but extremely long queries can degrade performance. Add `query = query[:100]` trim.
5. **Language logic belongs in middleware, not a view** — consider extracting to a mixin or a small middleware for reuse across all views.

### Final Improved Code

```python
class BookListView(ListView):
    """
    Display a paginated list of books with optional search and language switching.

    Query parameters:
        q (str): Search term matched against title and author (case-insensitive).
        language (str): One of ``'uk'`` or ``'en'`` — activates the chosen locale
            for the session via a cookie.

    Attributes:
        paginate_by (int): Number of books per page (default 10).
    """

    model = Book
    template_name = 'shop/book_list.html'
    context_object_name = 'books'
    paginate_by = 10

    def get(self, request, *args, **kwargs):
        lang = request.GET.get('language')
        if lang in ['uk', 'en']:
            from django.utils import translation
            from django.conf import settings as dj_settings
            translation.activate(lang)
            # Store choice in a cookie so LocaleMiddleware picks it up next request
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
            from django.conf import settings as dj_settings
            response.set_cookie(
                dj_settings.LANGUAGE_COOKIE_NAME,
                self._new_lang,
                max_age=dj_settings.LANGUAGE_COOKIE_AGE,
            )
        return response
```

**Changes applied:** language stored in cookie (not deprecated session key), `select_related('category')` to avoid N+1, query trimmed to 100 chars, docstring added, language logic consolidated in `render_to_response`.

---

## Summary

| View | Issues Found | Critical | Applied |
|---|---|---|---|
| `payment_success` | 5 | Duplicate order on refresh | ✅ Yes |
| `checkout` | 4 | Float precision → wrong cents | ✅ Yes |
| `BookListView` | 5 | Deprecated session key | ✅ Yes |
