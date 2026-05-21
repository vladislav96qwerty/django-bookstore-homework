"""
bookstore/settings/development.py — локальна розробка (SQLite, debug toolbar).
"""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['*']

# SQLite для локальної розробки — не потрібен Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

# Виводимо email у консоль замість реального SMTP
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Redis локально (запусти: docker run -p 6379:6379 redis:7-alpine)
REDIS_URL = 'redis://localhost:6379/0'
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'KEY_PREFIX': 'bookstore_dev',
        'TIMEOUT': 60 * 15,
    }
}

# CORS — дозволяємо фронтенд на localhost
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8080',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True
