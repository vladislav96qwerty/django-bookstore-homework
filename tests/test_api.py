"""
API tests for Bookshop REST API.
Run: pytest tests/test_api.py --ds=bookstore.settings_sqlite -v
"""

import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from shop.models import Book, Category, Order, OrderItem

# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(username="admin", password="adminpass123", email="admin@example.com")


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def category(db):
    return Category.objects.create(name="Fiction", slug="fiction")


@pytest.fixture
def book(db, category):
    return Book.objects.create(
        category=category,
        title="Test Book",
        author="Test Author",
        price=Decimal("19.99"),
        stock=10,
        description="Test description",
    )


@pytest.fixture
def book2(db, category):
    return Book.objects.create(
        category=category,
        title="Another Book",
        author="Another Author",
        price=Decimal("29.99"),
        stock=5,
    )


@pytest.fixture
def order(db, user, book):
    o = Order.objects.create(user=user, status="pending")
    OrderItem.objects.create(order=o, book=book, quantity=2, price=book.price)
    return o


# ──────────────────────────────────────────────────────────────────────────────
# JWT Authentication Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestJWTAuth:
    def test_obtain_token(self, api_client, user):
        """Test 1: JWT token obtain"""
        response = api_client.post(
            "/api/token/",
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_refresh_token(self, api_client, user):
        """Test 2: JWT token refresh"""
        res = api_client.post("/api/token/", {"username": "testuser", "password": "testpass123"})
        refresh = res.data["refresh"]
        response = api_client.post("/api/token/refresh/", {"refresh": refresh})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_verify_token(self, api_client, user):
        """Test 3: JWT token verify"""
        res = api_client.post("/api/token/", {"username": "testuser", "password": "testpass123"})
        access = res.data["access"]
        response = api_client.post("/api/token/verify/", {"token": access})
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_credentials(self, api_client, user):
        """Test 4: JWT with wrong credentials"""
        response = api_client.post("/api/token/", {"username": "testuser", "password": "wrongpass"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────────────────────────────────────────────────────────────────────────────
# Category API Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCategoryAPI:
    def test_list_categories_anonymous(self, api_client, category):
        """Test 5: Anyone can list categories"""
        response = api_client.get("/api/categories/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_retrieve_category(self, api_client, category):
        """Test 6: Retrieve a single category"""
        response = api_client.get(f"/api/categories/{category.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Fiction"

    def test_create_category_admin(self, admin_client):
        """Test 7: Admin can create category"""
        response = admin_client.post("/api/categories/", {"name": "Science", "slug": "science"})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Science"

    def test_create_category_forbidden_for_user(self, auth_client):
        """Test 8: Regular user cannot create category"""
        response = auth_client.post("/api/categories/", {"name": "Science", "slug": "science"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_category_admin(self, admin_client, category):
        """Test 9: Admin can delete category"""
        response = admin_client.delete(f"/api/categories/{category.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ──────────────────────────────────────────────────────────────────────────────
# Book API Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBookAPI:
    def test_list_books_anonymous(self, api_client, book):
        """Test 10: Anyone can list books"""
        response = api_client.get("/api/books/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_retrieve_book(self, api_client, book):
        """Test 11: Retrieve a single book"""
        response = api_client.get(f"/api/books/{book.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Test Book"
        assert response.data["author"] == "Test Author"

    def test_book_has_nested_category(self, api_client, book):
        """Test 12: Book response contains nested category"""
        response = api_client.get(f"/api/books/{book.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["category"]["name"] == "Fiction"

    def test_create_book_admin(self, admin_client, category):
        """Test 13: Admin can create book"""
        response = admin_client.post(
            "/api/books/",
            {
                "category_id": category.id,
                "title": "New Book",
                "author": "New Author",
                "price": "15.99",
                "stock": 5,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_book_forbidden(self, auth_client, category):
        """Test 14: Regular user cannot create book"""
        response = auth_client.post(
            "/api/books/",
            {
                "category_id": category.id,
                "title": "New Book",
                "author": "New Author",
                "price": "15.99",
                "stock": 5,
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_books_by_price(self, api_client, book, book2):
        """Test 15: Filter books by min/max price"""
        response = api_client.get("/api/books/?min_price=25")
        assert response.status_code == status.HTTP_200_OK
        titles = [b["title"] for b in response.data["results"]]
        assert "Another Book" in titles
        assert "Test Book" not in titles

    def test_search_books(self, api_client, book, book2):
        """Test 16: Search books by title"""
        response = api_client.get("/api/books/?search=Another")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Another Book"

    def test_pagination(self, api_client, category):
        """Test 17: Pagination returns correct structure"""
        for i in range(5):
            Book.objects.create(category=category, title=f"Book {i}", author=f"Author {i}", price="10.00", stock=1)
        response = api_client.get("/api/books/")
        assert "count" in response.data
        assert "next" in response.data
        assert "results" in response.data

    def test_update_book_admin(self, admin_client, book, category):
        """Test 18: Admin can update book"""
        response = admin_client.patch(f"/api/books/{book.id}/", {"price": "99.99"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["price"] == "99.99"

    def test_delete_book_admin(self, admin_client, book):
        """Test 19: Admin can delete book"""
        response = admin_client.delete(f"/api/books/{book.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ──────────────────────────────────────────────────────────────────────────────
# Order API Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOrderAPI:
    def test_list_orders_authenticated(self, auth_client, order):
        """Test 20: Authenticated user sees own orders"""
        response = auth_client.get("/api/orders/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_list_orders_unauthenticated(self, api_client):
        """Test 21: Unauthenticated user cannot see orders"""
        response = api_client.get("/api/orders/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_own_order(self, auth_client, order):
        """Test 22: User can retrieve own order"""
        response = auth_client.get(f"/api/orders/{order.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert "items" in response.data
        assert "total_price" in response.data

    def test_order_not_visible_to_other_user(self, db, order):
        """Test 23: Another user cannot access someone else's order"""
        other_user = User.objects.create_user(username="other", password="pass")
        client = APIClient()
        client.force_authenticate(user=other_user)
        response = client.get(f"/api/orders/{order.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_sees_all_orders(self, admin_client, order):
        """Test 24: Admin sees all orders"""
        response = admin_client.get("/api/orders/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1

    def test_filter_orders_by_status(self, auth_client, order):
        """Test 25: Filter orders by status"""
        response = auth_client.get("/api/orders/?status=pending")
        assert response.status_code == status.HTTP_200_OK
        for o in response.data["results"]:
            assert o["status"] == "pending"

    def test_order_has_nested_items(self, auth_client, order):
        """Test 26: Order response contains nested items with books"""
        response = auth_client.get(f"/api/orders/{order.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["items"]) >= 1
        assert "book" in response.data["items"][0]


# ──────────────────────────────────────────────────────────────────────────────
# Permissions & Security Tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPermissions:
    def test_anon_cannot_access_cart(self, api_client):
        """Test 27: Anonymous user cannot access cart"""
        response = api_client.get("/api/cart/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_can_access_cart(self, auth_client):
        """Test 28: Authenticated user can access cart"""
        response = auth_client.get("/api/cart/")
        assert response.status_code == status.HTTP_200_OK

    def test_is_owner_or_read_only(self, db, order):
        """Test 29: IsOwnerOrReadOnly — another user cannot update order"""
        other_user = User.objects.create_user(username="other2", password="pass")
        client = APIClient()
        client.force_authenticate(user=other_user)
        response = client.patch(f"/api/orders/{order.id}/", {"status": "cancelled"})
        # other user doesn't see this order at all (filtered queryset)
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]
