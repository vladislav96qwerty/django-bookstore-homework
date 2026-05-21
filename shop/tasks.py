"""
shop/tasks.py — Async Celery tasks
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.sessions.backends.db import SessionStore
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Email tasks ───────────────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id: int):
    """
    Async відправка email-підтвердження замовлення.
    При помилці повторює до 3 разів з інтервалом 60 секунд.
    """
    try:
        from shop.models import Order

        order = Order.objects.select_related("user").prefetch_related("items__book").get(id=order_id)

        subject = f"Bookshop — Order #{order.id} confirmed"
        total = order.get_total_price()
        items_text = "\n".join(
            f"  - {item.book.title} x{item.quantity} = ${item.get_total_price()}" for item in order.items.all()
        )
        message = (
            f"Hello {order.user.username}!\n\n"
            f"Your order #{order.id} has been confirmed.\n\n"
            f"Items:\n{items_text}\n\n"
            f"Total: ${total}\n\n"
            f"Thank you for shopping with us!"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )
        logger.info(f"Order confirmation email sent for order #{order_id}")
        return f"Email sent for order #{order_id}"

    except Exception as exc:
        logger.error(f"Failed to send email for order #{order_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_welcome_email(self, user_id: int):
    """
    Async відправка вітального email нового користувача.
    """
    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.get(id=user_id)

        send_mail(
            subject="Welcome to Bookshop!",
            message=(
                f"Hi {user.username}!\n\n"
                f"Welcome to our bookshop. Start exploring our catalog!\n\n"
                f"Best regards,\nBookshop Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to user #{user_id}")
        return f"Welcome email sent to user #{user_id}"

    except Exception as exc:
        logger.error(f"Failed to send welcome email to user #{user_id}: {exc}")
        raise self.retry(exc=exc)


# ── Report tasks ──────────────────────────────────────────────────────────────


@shared_task
def generate_sales_report():
    """
    Periodic task: генерує звіт продажів за останню годину
    і зберігає у Redis кеш на 2 години.
    """
    from shop.models import Order, OrderItem
    from django.db.models import Sum, Count

    since = timezone.now() - timedelta(hours=1)

    stats = Order.objects.filter(
        status="paid",
        updated_at__gte=since,
    ).aggregate(
        total_orders=Count("id"),
        total_revenue=Sum("items__price"),
    )

    top_books = (
        OrderItem.objects.filter(order__status="paid", order__updated_at__gte=since)
        .values("book__title")
        .annotate(sold=Sum("quantity"))
        .order_by("-sold")[:5]
    )

    report = {
        "generated_at": timezone.now().isoformat(),
        "period": "1 hour",
        "total_orders": stats["total_orders"] or 0,
        "total_revenue": str(stats["total_revenue"] or 0),
        "top_books": list(top_books),
    }

    cache.set("sales_report_latest", report, timeout=60 * 60 * 2)
    logger.info(f"Sales report generated: {report}")
    return report


# ── Session cleanup task ──────────────────────────────────────────────────────


@shared_task
def clear_expired_sessions():
    """
    Periodic task: очищає прострочені сесії з бази даних.
    Django зберігає сесії у БД якщо SESSION_ENGINE = db (за замовчуванням).
    """
    try:
        from django.contrib.sessions.backends.db import SessionStore

        SessionStore.clear_expired()
        logger.info("Expired sessions cleared successfully")
        return "Expired sessions cleared"
    except Exception as exc:
        logger.error(f"Failed to clear sessions: {exc}")
        raise


# ── Cache invalidation task ───────────────────────────────────────────────────


@shared_task
def invalidate_book_cache(book_id: int):
    """
    Async інвалідація кешу конкретної книги.
    Викликається через signal після збереження Book.
    """
    cache.delete(f"book_detail_{book_id}")
    cache.delete("book_list_page_1")  # скидаємо першу сторінку списку
    logger.info(f"Cache invalidated for book #{book_id}")
    return f"Cache cleared for book #{book_id}"
