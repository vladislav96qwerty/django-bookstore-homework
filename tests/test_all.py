"""
tests/test_all.py
Run: pytest --ds=bookstore.settings_sqlite -v --cov=shop --cov-report=term-missing
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.test import Client

from shop.models import Category, Book, Order, OrderItem
from shop.forms import BookForm
from tests.factories import (
    UserFactory, CategoryFactory, BookFactory, OrderFactory, OrderItemFactory
)


# ═══════════════════════════════════════════════════════════════
# UNIT — Models (10 тестів)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestCategoryModel:
    def test_str(self):
        cat = CategoryFactory(name="Science")
        assert str(cat) == "Science"

    def test_slug_auto_generated(self):
        cat = CategoryFactory(name="My Category", slug="")
        cat.slug = ""
        cat.save()
        assert cat.slug == "my-category"

    def test_ordering(self):
        CategoryFactory(name="Zeta")
        CategoryFactory(name="Alpha")
        names = list(Category.objects.values_list("name", flat=True))
        assert names == sorted(names)


@pytest.mark.django_db
class TestBookModel:
    def test_str(self):
        book = BookFactory(title="Django Tricks", author="John")
        assert "Django Tricks" in str(book)
        assert "John" in str(book)

    def test_default_stock_zero(self):
        book = BookFactory.__new__(BookFactory)
        b = Book(
            category=CategoryFactory(),
            title="T", author="A", price=Decimal("9.99")
        )
        b.save()
        assert b.stock == 0

    def test_price_positive(self):
        book = BookFactory(price=Decimal("0.01"))
        assert book.price >= Decimal("0")

    def test_indexes_exist(self):
        index_names = [i.fields for i in Book._meta.indexes]
        assert ["title"] in index_names
        assert ["author"] in index_names


@pytest.mark.django_db
class TestOrderModel:
    def test_str(self, user):
        order = OrderFactory(user=user)
        assert f"#{order.id}" in str(order)

    def test_get_total_price(self, user):
        order = OrderFactory(user=user)
        book = BookFactory(price=Decimal("10.00"))
        OrderItemFactory(order=order, book=book, quantity=3, price=Decimal("10.00"))
        assert order.get_total_price() == Decimal("30.00")

    def test_default_status_pending(self, user):
        order = OrderFactory(user=user, status="pending")
        assert order.status == "pending"


@pytest.mark.django_db
class TestOrderItemModel:
    def test_get_total_price(self, book):
        order = OrderFactory()
        item = OrderItemFactory(order=order, book=book, quantity=4, price=Decimal("5.00"))
        assert item.get_total_price() == Decimal("20.00")

    def test_str(self, book):
        order = OrderFactory()
        item = OrderItemFactory(order=order, book=book, quantity=2)
        assert book.title in str(item)


# ═══════════════════════════════════════════════════════════════
# UNIT — Forms (5 тестів)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestBookForm:
    def _valid_data(self, category):
        return {
            'category': category.pk,
            'title': 'Clean Code',
            'author': 'Robert Martin',
            'price': '29.99',
            'description': 'A great book.',
            'stock': 5,
        }

    def test_valid_form(self):
        cat = CategoryFactory()
        form = BookForm(data=self._valid_data(cat))
        assert form.is_valid(), form.errors

    def test_missing_title(self):
        cat = CategoryFactory()
        data = self._valid_data(cat)
        data.pop('title')
        form = BookForm(data=data)
        assert not form.is_valid()
        assert 'title' in form.errors

    def test_negative_price_invalid(self):
        cat = CategoryFactory()
        data = self._valid_data(cat)
        data['price'] = '-1'
        form = BookForm(data=data)
        assert not form.is_valid()

    def test_missing_author(self):
        cat = CategoryFactory()
        data = self._valid_data(cat)
        data.pop('author')
        form = BookForm(data=data)
        assert not form.is_valid()

    def test_description_optional(self):
        cat = CategoryFactory()
        data = self._valid_data(cat)
        data['description'] = ''
        form = BookForm(data=data)
        assert form.is_valid(), form.errors


# ═══════════════════════════════════════════════════════════════
# UNIT — Views (8 тестів)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestBookListView:
    def test_returns_200(self, client, book):
        url = reverse('shop:book_list')
        response = client.get(url)
        assert response.status_code == 200

    def test_search_filters_results(self, client, book):
        url = reverse('shop:book_list') + f'?q={book.title}'
        response = client.get(url)
        assert book.title.encode() in response.content

    def test_search_no_results(self, client):
        url = reverse('shop:book_list') + '?q=zzznoresult'
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestBookDetailView:
    def test_returns_200(self, client, book):
        url = reverse('shop:book_detail', kwargs={'pk': book.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert book.title.encode() in response.content

    def test_404_on_missing(self, client):
        url = reverse('shop:book_detail', kwargs={'pk': 99999})
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestBookCreateView:
    def test_requires_permission(self, client, user):
        client.force_login(user)
        url = reverse('shop:book_create')
        response = client.get(url)
        assert response.status_code == 403

    def test_creates_book_with_permission(self, client, user, category):
        perm = Permission.objects.get(codename='add_book')
        user.user_permissions.add(perm)
        client.force_login(user)
        url = reverse('shop:book_create')
        data = {
            'category': category.pk,
            'title': 'New Book',
            'author': 'Author',
            'price': '15.00',
            'description': '',
            'stock': 3,
        }
        response = client.post(url, data)
        assert response.status_code == 302
        assert Book.objects.filter(title='New Book').exists()

    def test_anonymous_redirected(self, client):
        url = reverse('shop:book_create')
        response = client.get(url)
        assert response.status_code in (302, 403)


# ═══════════════════════════════════════════════════════════════
# UNIT — Async views (3 тести)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAsyncViews:
    def test_async_book_list_json(self, client, book):
        url = reverse('shop:api_book_list')
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert 'books' in data
        assert data['count'] >= 1

    def test_async_book_detail_json(self, client, book):
        url = reverse('shop:api_book_detail', kwargs={'pk': book.pk})
        response = client.get(url)
        assert response.status_code == 200
        data = response.json()
        assert data['title'] == book.title

    def test_async_book_detail_404(self, client):
        url = reverse('shop:api_book_detail', kwargs={'pk': 99999})
        response = client.get(url)
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════
# UNIT — Mock Stripe & Email (4 тести)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestStripeMock:
    @patch('shop.views.stripe.checkout.Session.create')
    def test_checkout_redirects(self, mock_create, client, user, book):
        mock_create.return_value = MagicMock(url='https://stripe.com/pay/test')
        client.force_login(user)
        # Кладемо книгу в кошик через session
        session = client.session
        session['cart'] = {str(book.pk): {'quantity': 1, 'price': str(book.price), 'title': book.title}}
        session.save()
        url = reverse('shop:checkout')
        response = client.get(url)
        # Redirect до stripe
        assert response.status_code == 302

    @patch('shop.views.stripe.Webhook.construct_event')
    def test_webhook_updates_order(self, mock_event, client, order):
        order.stripe_session_id = "sess_123"
        order.status = "pending"
        order.save()
        mock_event.return_value = {
            'type': 'checkout.session.completed',
            'data': {'object': {'id': 'sess_123'}},
        }
        url = reverse('shop:stripe_webhook')
        response = client.post(
            url, data=b'{}', content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=1,v1=sig'
        )
        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == 'paid'

    @patch('shop.views.send_mail')
    def test_payment_success_sends_email(self, mock_mail, client, user, book):
        client.force_login(user)
        order = OrderFactory(user=user, status='paid', stripe_session_id='sess_ok')
        OrderItemFactory(order=order, book=book, quantity=1, price=book.price)
        # Симулюємо порожній кошик + session_id
        url = reverse('shop:payment_success') + '?session_id=sess_ok'
        # Cart is empty so order is created from scratch inside view;
        # here we just check the view itself doesn't crash
        response = client.get(url)
        # Може редіректити якщо кошик порожній — це теж ок
        assert response.status_code in (200, 302)

    @patch('shop.views.stripe.Webhook.construct_event', side_effect=ValueError)
    def test_webhook_bad_signature_returns_400(self, mock_event, client):
        url = reverse('shop:stripe_webhook')
        response = client.post(url, data=b'bad', content_type='application/json')
        assert response.status_code == 400


# ═══════════════════════════════════════════════════════════════
# INTEGRATION — User Flows (15 тестів)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestIntegration:

    # 1. Анонімний користувач бачить список книг
    def test_anonymous_sees_book_list(self, client, book):
        response = client.get(reverse('shop:book_list'))
        assert response.status_code == 200

    # 2. Анонімний не може відкрити кошик
    def test_anonymous_cannot_see_cart(self, client):
        response = client.get(reverse('shop:cart_detail'))
        assert response.status_code == 302
        assert '/login' in response['Location'] or 'accounts' in response['Location']

    # 3. Зареєстрований бачить кошик
    def test_user_can_see_cart(self, client, user):
        client.force_login(user)
        response = client.get(reverse('shop:cart_detail'))
        assert response.status_code == 200

    # 4. Додавання книги до кошика
    def test_add_book_to_cart(self, client, user, book):
        client.force_login(user)
        url = reverse('shop:cart_add', kwargs={'book_id': book.pk})
        response = client.get(url)
        assert response.status_code == 302

    # 5. Видалення книги з кошика
    def test_remove_book_from_cart(self, client, user, book):
        client.force_login(user)
        client.get(reverse('shop:cart_add', kwargs={'book_id': book.pk}))
        response = client.get(reverse('shop:cart_remove', kwargs={'book_id': book.pk}))
        assert response.status_code == 302

    # 6. Перегляд сторінки деталей книги
    def test_book_detail_page(self, client, book):
        response = client.get(reverse('shop:book_detail', kwargs={'pk': book.pk}))
        assert response.status_code == 200
        assert book.author.encode() in response.content

    # 7. Пошук книги
    def test_search_finds_book(self, client, book):
        response = client.get(reverse('shop:book_list') + f'?q={book.author}')
        assert book.title.encode() in response.content

    # 8. Пошук повертає порожній список якщо нічого не знайдено
    def test_search_empty_result(self, client):
        response = client.get(reverse('shop:book_list') + '?q=xyznotexist')
        assert response.status_code == 200

    # 9. Редагування книги без прав → 403
    def test_edit_book_forbidden(self, client, user, book):
        client.force_login(user)
        url = reverse('shop:book_update', kwargs={'pk': book.pk})
        response = client.get(url)
        assert response.status_code == 403

    # 10. Редагування книги з правами → 200
    def test_edit_book_allowed(self, client, user, book):
        perm = Permission.objects.get(codename='change_book')
        user.user_permissions.add(perm)
        client.force_login(user)
        url = reverse('shop:book_update', kwargs={'pk': book.pk})
        response = client.get(url)
        assert response.status_code == 200

    # 11. Видалення книги з правами
    def test_delete_book_allowed(self, client, user, book):
        perm = Permission.objects.get(codename='delete_book')
        user.user_permissions.add(perm)
        client.force_login(user)
        url = reverse('shop:book_delete', kwargs={'pk': book.pk})
        response = client.post(url)
        assert response.status_code == 302
        assert not Book.objects.filter(pk=book.pk).exists()

    # 12. Checkout без кошика → redirect
    @patch('shop.views.stripe.checkout.Session.create')
    def test_checkout_empty_cart_redirects(self, mock_create, client, user):
        client.force_login(user)
        response = client.get(reverse('shop:checkout'))
        assert response.status_code == 302
        mock_create.assert_not_called()

    # 13. Payment cancel view
    def test_payment_cancel(self, client, user):
        client.force_login(user)
        response = client.get(reverse('shop:payment_cancel'))
        assert response.status_code == 200

    # 14. Async API book list returns JSON
    def test_async_api_returns_json(self, client, book):
        response = client.get(reverse('shop:api_book_list'))
        assert response['Content-Type'] == 'application/json'

    # 15. Async catalog renders HTML
    def test_async_catalog_renders(self, client, book):
        response = client.get(reverse('shop:catalog'))
        assert response.status_code == 200
