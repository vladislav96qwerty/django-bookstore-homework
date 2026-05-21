import pytest
from shop.models import Category, Book


@pytest.mark.django_db
class TestBasic:
    def test_category_creation(self, category):
        assert category.name == "Fiction"
        assert category.slug == "fiction"

    def test_book_creation(self, book):
        assert book.title == "Test Book"
        assert book.price == 19.99
        assert book.stock == 10

    def test_book_category_relation(self, category, book):
        assert book.category == category
        assert book.category.name == "Fiction"
