"""
shop/signals.py — cache invalidation + (existing accounts signals kept in accounts/signals.py)
"""
import logging

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Book, Category

logger = logging.getLogger(__name__)


# ── Book cache invalidation ───────────────────────────────────────────────────

@receiver(post_save, sender=Book)
def invalidate_book_cache_on_save(sender, instance, **kwargs):
    """
    Після збереження книги: інвалідуємо кеш деталей та списку.
    Використовуємо async task щоб не блокувати request/response цикл.
    """
    # Low-level cache invalidation
    cache.delete(f'book_detail_{instance.pk}')

    # Скидаємо всі сторінки книжкового списку через cache versioning
    cache.delete_many([
        f'book_list_page_{i}' for i in range(1, 20)
    ])

    # Скидаємо кеш категорії до якої належить книга
    cache.delete(f'category_books_{instance.category_id}')

    logger.info(f'[signal] Cache invalidated for Book #{instance.pk} "{instance.title}"')


@receiver(post_delete, sender=Book)
def invalidate_book_cache_on_delete(sender, instance, **kwargs):
    """Після видалення книги — теж чистимо кеш."""
    cache.delete(f'book_detail_{instance.pk}')
    cache.delete_many([
        f'book_list_page_{i}' for i in range(1, 20)
    ])
    cache.delete(f'category_books_{instance.category_id}')
    logger.info(f'[signal] Cache cleared after deleting Book #{instance.pk}')


# ── Category cache invalidation ───────────────────────────────────────────────

@receiver(post_save, sender=Category)
def invalidate_category_cache_on_save(sender, instance, **kwargs):
    cache.delete('category_list')
    cache.delete(f'category_books_{instance.pk}')
    logger.info(f'[signal] Cache invalidated for Category #{instance.pk} "{instance.name}"')


@receiver(post_delete, sender=Category)
def invalidate_category_cache_on_delete(sender, instance, **kwargs):
    cache.delete('category_list')
    cache.delete(f'category_books_{instance.pk}')
    logger.info(f'[signal] Cache cleared after deleting Category #{instance.pk}')
