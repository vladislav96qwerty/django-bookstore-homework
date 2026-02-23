from django.db.models import Q, Count, Avg
from .models import Book, Category


def books_price_gt_500():
    """Книги дороже 500."""
    return Book.objects.filter(price__gt=500)


def books_in_stock():
    """Книги в наличии."""
    return Book.objects.filter(stock__gt=0)


def books_by_category_slug(slug: str):
    """Книги по slug категории."""
    return Book.objects.filter(category__slug=slug)


def books_python_or_tolkien():
    """Пример Q-объектов: title содержит 'python' ИЛИ author содержит 'tolkien'."""
    return Book.objects.filter(
        Q(title__icontains="python") | Q(author__icontains="tolkien")
    )


def categories_with_total_books():
    """Категории с количеством книг (annotate + Count)."""
    return Category.objects.annotate(total_books=Count("books"))


def categories_with_avg_price():
    """Категории со средней ценой книг (annotate + Avg)."""
    return Category.objects.annotate(avg_price=Avg("books__price"))