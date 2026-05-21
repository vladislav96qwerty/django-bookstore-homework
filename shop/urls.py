from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    # Книги (sync)
    path("", views.BookListView.as_view(), name="book_list"),
    path("book/<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("book/new/", views.BookCreateView.as_view(), name="book_create"),
    path("book/<int:pk>/edit/", views.BookUpdateView.as_view(), name="book_update"),
    path("book/<int:pk>/delete/", views.BookDeleteView.as_view(), name="book_delete"),
    # Async views
    path("api/books/", views.async_book_list, name="api_book_list"),
    path("api/books/<int:pk>/", views.async_book_detail, name="api_book_detail"),
    path("catalog/", views.async_catalog, name="catalog"),
    # Кошик
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:book_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:book_id>/", views.cart_remove, name="cart_remove"),
    # Stripe
    path("checkout/", views.checkout, name="checkout"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),
    path("webhook/stripe/", views.stripe_webhook, name="stripe_webhook"),
]
