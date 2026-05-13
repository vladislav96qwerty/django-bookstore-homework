import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore.settings')

app = Celery('bookstore')

# Читаємо конфіг із Django settings, всі ключі з префіксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматично знаходить tasks.py у всіх INSTALLED_APPS
app.autodiscover_tasks()

# ── Periodic tasks (Celery Beat) ──────────────────────────────────────────────
app.conf.beat_schedule = {
    # Кожну добу о 3:00 ночі очищаємо прострочені сесії
    'clear-expired-sessions-daily': {
        'task': 'shop.tasks.clear_expired_sessions',
        'schedule': crontab(hour=3, minute=0),
    },
    # Кожну годину генеруємо звіт продажів
    'generate-sales-report-hourly': {
        'task': 'shop.tasks.generate_sales_report',
        'schedule': crontab(minute=0),
    },
}

app.conf.timezone = 'UTC'
