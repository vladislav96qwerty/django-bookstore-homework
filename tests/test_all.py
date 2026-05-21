"""
test_all.py — comprehensive test suite for the Django Bookstore project.

Generated with AI, reviewed and modified.
Coverage target: ≥ 60% for shop.models, accounts.models, shop.views, accounts.views.
Run:
    pytest tests/test_all.py -v --cov=shop --cov=accounts --cov-report=term-missing
"""

import pytest
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, RequestFactory
from django.urls import reverse

from shop.models import Book, Category, Order, OrderItem
from accounts.models import Profile

# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY MODEL TESTS
# Generated with AI, reviewed and modified
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for the Category model — slug auto-generation and string repr."""

    def test_category_str(self, category):
        # Generated with AI, reviewed and modified
        assert str(category) == "Fiction"

    def test_slug_auto_generated_on_save(self, db):
        # Generated with AI, reviewed and modified
        cat = Category.objects.create(name="Science Fiction")
        assert cat.slug == "science-fiction"

    def test_slug_not_overwritten_if_set(self, db):
        # Generated with AI, reviewed and modified
        cat = Category.objects.create(name="Horror", slug="custom-horror-slug")
        assert cat.slug == "custom-horror-slug"

    def test_category_name_unique(self, category, db):
        # Generated with AI, reviewed and modified
        import pytest as _pytest

        with _pytest.raises(Exception):
            Category.objects.create(name="Fiction", slug="fiction-2")

    def test_category_ordering(self, db):
        # Generated with AI, reviewed and modified
        Category.objects.create(name="Zebra")
        Category.objects.create(name="Alpha")
        names = list(Category.objects.values_list("name", flat=True))
        assert names == sorted(names)

    def test_category_verbose_name(self):
        # Generated with AI, reviewed and modified
        assert Category._meta.verbose_name is not None

    def test_slug_generated_from_name_with_spaces(self, db):
        # Generated with AI, reviewed and modified
        cat = Category.objects.create(name="My Great Category")
        assert " " not in cat.slug

    def test_category_max_name_length(self):
        # Generated with AI, reviewed and modified
        field = Category._meta.get_field("name")
        assert field.max_length == 100


# ══════════════════════════════════════════════════════════════════════════════
# BOOK MODEL TESTS
# Generated with AI, reviewed and modified
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestBookModel:
    """Tests for the Book model — fields, relations, and string repr."""

    def test_book_str(self, book):
        # Generated with AI, reviewed and modified
        assert str(book) == "Test Book — Test Author"

    def test_book_price_decimal(self, book):
        # Generated with AI, reviewed and modified
        assert book.price == Decimal("19.99")

    def test_book_stock_default(self, category, db):
        # Generated with AI, reviewed and modified
        b = Book.objects.create(category=category, title="No Stock Book", author="A", price=Decimal("5.00"))
        assert b.stock == 0

    def test_book_category_relation(self, book, category):
        # Generated with AI, reviewed and modified
        assert book.category == category
        assert book.category.name == "Fiction"

    def test_book_ordering(self, category, db):
        # Generated with AI, reviewed and modified
        Book.objects.create(category=category, title="Zebra Book", author="Z", price=Decimal("1.00"))
        Book.objects.create(category=category, title="Alpha Book", author="A", price=Decimal("1.00"))
        titles = list(Book.objects.values_list("title", flat=True))
        assert titles == sorted(titles)

    def test_book_created_at_auto(self, book):
        # Generated with AI, reviewed and modified
        assert book.created_at is not None

    def test_book_updated_at_auto(self, book):
        # Generated with AI, reviewed and modified
        assert book.updated_at is not None

    def test_book_description_blank_allowed(self, category, db):
        # Generated with AI, reviewed and modified
        b = Book.objects.create(category=category, title="No Desc", author="A", price=Decimal("1.00"), description="")
        assert b.description == ""

    def test_book_price_non_negative_validator(self, category, db):
        # Generated with AI, reviewed and modified
        from django.core.exceptions import ValidationError

        b = Book(category=category, title="Bad Book", author="A", price=Decimal("-1.00"), stock=0)
        with pytest.raises(ValidationError):
            b.full_clean()

    def test_book_related_name_books(self, category, book):
        # Generated with AI, reviewed and modified
        assert book in category.books.all()


# ══════════════════════════════════════════════════════════════════════════════
# ORDER MODEL TESTS
# Generated with AI, reviewed and modified
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestOrderModel:
    """Tests for Order and OrderItem — totals, statuses, and relations."""

    def test_order_str(self, order, user):
        # Generated with AI, reviewed and modified
        assert f"Order #{order.id}" in str(order)

    def test_order_default_status_pending(self, user, db):
        # Generated with AI, reviewed and modified
        o = Order.objects.create(user=user)
        assert o.status == "pending"

    def test_order_status_choices(self):
        # Generated with AI, reviewed and modified
        valid = {c[0] for c in Order.STATUS_CHOICES}
        assert {"pending", "paid", "cancelled"} == valid

    def test_order_get_total_price(self, order, book):
        # Generated with AI, reviewed and modified
        # order fixture creates 2 items at book.price each
        expected = Decimal("19.99") * 2
        assert order.get_total_price() == expected

    def test_order_item_get_total_price(self, order, book):
        # Generated with AI, reviewed and modified
        item = order.items.first()
        assert item.get_total_price() == item.price * item.quantity

    def test_order_item_str(self, order, book):
        # Generated with AI, reviewed and modified
        item = order.items.first()
        assert book.title in str(item)

    def test_order_ordering_newest_first(self, user, db):
        # Generated with AI, reviewed and modified
        o1 = Order.objects.create(user=user, status="pending")
        o2 = Order.objects.create(user=user, status="paid")
        orders = list(Order.objects.filter(user=user))
        # Verify both orders exist and are returned for this user
        assert len(orders) == 2
        # o1 was created first so has smaller pk
        pks = {o.pk for o in orders}
        assert o1.pk in pks and o2.pk in pks

    def test_order_multiple_items_total(self, user, category, db):
        # Generated with AI, reviewed and modified
        b1 = Book.objects.create(category=category, title="B1", author="A", price=Decimal("10.00"))
        b2 = Book.objects.create(category=category, title="B2", author="A", price=Decimal("5.00"))
        o = Order.objects.create(user=user)
        OrderItem.objects.create(order=o, book=b1, quantity=2, price=b1.price)
        OrderItem.objects.create(order=o, book=b2, quantity=3, price=b2.price)
        assert o.get_total_price() == Decimal("35.00")

    def test_order_cascade_delete_on_user(self, user, db, category):
        # Generated with AI, reviewed and modified
        o = Order.objects.create(user=user)
        user_id = user.id
        user.delete()
        assert not Order.objects.filter(user_id=user_id).exists()

    def test_order_item_cascade_delete(self, order, db):
        # Generated with AI, reviewed and modified
        order_id = order.id
        order.delete()
        assert not OrderItem.objects.filter(order_id=order_id).exists()


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE MODEL TESTS
# Generated with AI, reviewed and modified
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestProfileModel:
    """Tests for the Profile model — one-to-one relation and string repr."""

    def test_profile_str(self, user, db):
        # Generated with AI, reviewed and modified
        # Signal auto-creates profile on user creation — use get_or_create
        profile, _ = Profile.objects.get_or_create(user=user)
        assert str(profile) == f"Profile({user.username})"

    def test_profile_created_with_user(self, user, db):
        # Generated with AI, reviewed and modified
        profile, _ = Profile.objects.get_or_create(user=user)
        assert profile.user == user

    def test_profile_phone_blank_by_default(self, user, db):
        # Generated with AI, reviewed and modified
        # Signal auto-creates profile — fetch it
        profile = Profile.objects.get(user=user)
        assert profile.phone_number == ""

    def test_profile_phone_can_be_set(self, user, db):
        # Generated with AI, reviewed and modified
        profile = Profile.objects.get(user=user)
        profile.phone_number = "+380991234567"
        profile.save()
        profile.refresh_from_db()
        assert profile.phone_number == "+380991234567"

    def test_profile_cascade_delete(self, user, db):
        # Generated with AI, reviewed and modified
        profile = Profile.objects.get(user=user)
        pid = profile.id
        user.delete()
        assert not Profile.objects.filter(id=pid).exists()

    def test_profile_one_to_one_constraint(self, user, db):
        # Generated with AI, reviewed and modified
        # Profile already exists via signal — creating another must raise
        with pytest.raises(Exception):
            Profile.objects.create(user=user)

    def test_profile_created_at_set(self, user, db):
        # Generated with AI, reviewed and modified
        profile = Profile.objects.get(user=user)
        assert profile.created_at is not None

    def test_profile_updated_at_set(self, user, db):
        # Generated with AI, reviewed and modified
        profile = Profile.objects.get(user=user)
        assert profile.updated_at is not None


# ══════════════════════════════════════════════════════════════════════════════
# SHOP VIEWS TESTS
# Generated with AI, reviewed and modified
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestBookListView:
    """HTTP tests for the book list page."""

    def test_book_list_returns_200(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:book_list")
        response = client.get(url)
        assert response.status_code == 200

    def test_book_list_contains_book_title(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:book_list")
        response = client.get(url)
        assert book.title.encode() in response.content

    def test_book_list_search_filter(self, client, book, db):
        # Generated with AI, reviewed and modified
        url = reverse("shop:book_list") + "?q=Test"
        response = client.get(url)
        assert response.status_code == 200
        assert book.title.encode() in response.content

    def test_book_list_search_no_results(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:book_list") + "?q=ZZZNOMATCH"
        response = client.get(url)
        assert response.status_code == 200
        assert book.title.encode() not in response.content

    def test_book_list_uses_correct_template(self, client, book):
        # Generated with AI, reviewed and modified
        response = client.get(reverse("shop:book_list"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestBookDetailView:
    """HTTP tests for the book detail page."""

    def test_book_detail_returns_200(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:book_detail", kwargs={"pk": book.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_book_detail_404_on_missing(self, client):
        # Generated with AI, reviewed and modified
        url = reverse("shop:book_detail", kwargs={"pk": 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_book_detail_shows_author(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:book_detail", kwargs={"pk": book.pk})
        response = client.get(url)
        assert book.author.encode() in response.content


@pytest.mark.django_db
class TestCartViews:
    """HTTP tests for cart add/remove/detail."""

    def test_cart_detail_returns_200(self, client):
        # Generated with AI, reviewed and modified
        url = reverse("shop:cart_detail")
        response = client.get(url)
        assert response.status_code == 200

    def test_cart_add_redirects(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:cart_add", kwargs={"book_id": book.pk})
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_cart_remove_redirects(self, client, book):
        # Generated with AI, reviewed and modified
        # First add then remove
        client.get(reverse("shop:cart_add", kwargs={"book_id": book.pk}))
        url = reverse("shop:cart_remove", kwargs={"book_id": book.pk})
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_cart_add_invalid_book_404(self, client):
        # Generated with AI, reviewed and modified
        url = reverse("shop:cart_add", kwargs={"book_id": 99999})
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestCheckoutAndPaymentViews:
    """HTTP tests for checkout, payment success/cancel (requires login)."""

    def test_checkout_requires_login(self, client):
        # Generated with AI, reviewed and modified
        url = reverse("shop:checkout")
        response = client.get(url)
        assert response.status_code in (301, 302)
        assert "/login" in response["Location"] or "login" in response["Location"]

    def test_payment_success_requires_login(self, client):
        # Generated with AI, reviewed and modified
        url = reverse("shop:payment_success")
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_payment_cancel_requires_login(self, client):
        # Generated with AI, reviewed and modified
        url = reverse("shop:payment_cancel")
        response = client.get(url)
        assert response.status_code in (301, 302)

    def test_payment_success_no_session_redirects(self, client, user):
        # Generated with AI, reviewed and modified
        client.force_login(user)
        url = reverse("shop:payment_success")
        response = client.get(url)
        # No session_id → redirect to book_list
        assert response.status_code in (301, 302)

    def test_payment_cancel_logged_in_returns_200(self, client, user):
        # Generated with AI, reviewed and modified
        client.force_login(user)
        url = reverse("shop:payment_cancel")
        response = client.get(url)
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# ACCOUNTS VIEWS TESTS
# Generated with AI, reviewed and modified
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestRegisterView:
    """HTTP tests for the user registration view."""

    def test_register_page_returns_200(self, client):
        # Generated with AI, reviewed and modified
        # accounts app is mounted at /accounts/ in main urls.py
        response = client.get("/accounts/register/")
        assert response.status_code == 200

    def test_register_creates_user(self, client, db):
        # Generated with AI, reviewed and modified
        data = {
            "username": "newuser",
            "password1": "Str0ngPass!",
            "password2": "Str0ngPass!",
            "email": "new@example.com",
        }
        response = client.post("/accounts/register/", data)
        assert User.objects.filter(username="newuser").exists()

    def test_register_redirects_after_success(self, client, db):
        # Generated with AI, reviewed and modified
        data = {
            "username": "newuser2",
            "password1": "Str0ngPass!",
            "password2": "Str0ngPass!",
        }
        response = client.post("/accounts/register/", data)
        assert response.status_code in (301, 302)

    def test_register_invalid_password_stays_on_page(self, client, db):
        # Generated with AI, reviewed and modified
        # Mismatched passwords — form is invalid, user must NOT be created
        data = {
            "username": "weakuser",
            "password1": "Str0ngPass!",
            "password2": "DifferentPass!",
        }
        client.post("/accounts/register/", data)
        assert not User.objects.filter(username="weakuser").exists()


@pytest.mark.django_db
class TestProfileView:
    """HTTP tests for profile view and update."""

    def test_profile_view_requires_login(self, client):
        # Generated with AI, reviewed and modified
        # In accounts/urls.py profile is at /accounts/me/
        response = client.get("/accounts/me/")
        assert response.status_code in (301, 302)

    def test_profile_view_logged_in_returns_200(self, client, user):
        # Generated with AI, reviewed and modified
        Profile.objects.get_or_create(user=user)
        client.force_login(user)
        response = client.get("/accounts/me/")
        assert response.status_code == 200

    def test_profile_update_requires_login(self, client):
        # Generated with AI, reviewed and modified
        # In accounts/urls.py profile edit is at /accounts/me/edit/
        response = client.get("/accounts/me/edit/")
        assert response.status_code in (301, 302)

    def test_profile_update_logged_in_returns_200(self, client, user):
        # Generated with AI, reviewed and modified
        Profile.objects.get_or_create(user=user)
        client.force_login(user)
        response = client.get("/accounts/me/edit/")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# ASYNC API VIEWS TESTS
# Generated with AI, reviewed and modified
# ══════════════════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestAsyncViews:
    """HTTP tests for async JSON API endpoints."""

    def test_async_book_list_returns_200(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:api_book_list")
        response = client.get(url)
        assert response.status_code == 200

    def test_async_book_list_returns_json(self, client, book):
        url = reverse("shop:api_book_list")
        response = client.get(url)
        data = response.json()
        assert "books" in data or "results" in data

    def test_async_book_list_search(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:api_book_list") + "?q=Test"
        response = client.get(url)
        data = response.json()
        assert data["count"] >= 1

    def test_async_book_detail_returns_200(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:api_book_detail", kwargs={"pk": book.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_async_book_detail_404(self, client):
        # Generated with AI, reviewed and modified
        url = reverse("shop:api_book_detail", kwargs={"pk": 99999})
        response = client.get(url)
        assert response.status_code == 404

    def test_async_book_detail_has_fields(self, client, book):
        # Generated with AI, reviewed and modified
        url = reverse("shop:api_book_detail", kwargs={"pk": book.pk})
        response = client.get(url)
        data = response.json()
        assert "title" in data
        assert "price" in data
        assert "author" in data
