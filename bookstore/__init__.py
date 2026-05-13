# Цей файл гарантує що Celery завантажується разом з Django
from .celery import app as celery_app

__all__ = ('celery_app',)
