import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore.settings_sqlite')

import django
django.setup()

import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from shop.models import Category, Book, Order, OrderItem


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
        description="A test description.",
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="testuser",
        password="testpass123",
        email="test@example.com",
    )


@pytest.fixture
def staff_user(db):
    u = User.objects.create_user(username="staffuser", password="staffpass")
    u.is_staff = True
    u.save()
    return u


@pytest.fixture
def order(db, user, book):
    o = Order.objects.create(user=user, status="pending")
    OrderItem.objects.create(order=o, book=book, quantity=2, price=book.price)
    return o
