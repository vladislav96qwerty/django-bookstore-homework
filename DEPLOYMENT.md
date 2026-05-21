# Деплой на Railway — покрокова інструкція

## 1. Підготовка проекту

Переконайся що всі файли є в репозиторії:
- `Procfile`
- `gunicorn.conf.py`
- `requirements.txt` (з `gunicorn`, `whitenoise`, `dj-database-url`)
- `bookstore/settings/` (base, development, production)

## 2. Реєстрація та підключення репозиторію

1. Зайди на [railway.app](https://railway.app) → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo**
3. Вибери `django-bookstore-homework`
4. Railway автоматично знайде `Procfile`

## 3. Додай PostgreSQL

1. В проекті натисни **+ New** → **Database** → **PostgreSQL**
2. Railway автоматично додасть `DATABASE_URL` до змінних середовища твого web сервісу

## 4. Додай Redis

1. **+ New** → **Database** → **Redis**
2. Railway автоматично додасть `REDIS_URL`

## 5. Налаштуй environment variables

В налаштуваннях web сервісу → **Variables** → додай:

```
DJANGO_ENV=production
SECRET_KEY=<згенеруй: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
ALLOWED_HOSTS=<твій-домен>.railway.app
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
DEBUG=False
```

Stripe (якщо є):
```
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 6. Перший деплой

Railway запустить:
```
web: gunicorn bookstore.wsgi:application ...
```

Після старту виконай міграції через Railway Shell:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 7. Перевірка

- Відкрий `https://<твій-домен>.railway.app/health/`
- Має повернути: `{"status": "ok", "database": "ok", "cache": "ok"}`

## 8. GitHub Actions secrets

В GitHub репозиторії → **Settings** → **Secrets and variables** → **Actions**:

| Secret | Значення |
|---|---|
| `DOCKERHUB_USERNAME` | твій Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub → Account Settings → Security → New Access Token |
| `CODECOV_TOKEN` | [codecov.io](https://codecov.io) → твій репо → Settings → token |

## 9. Codecov badge

1. Зайди на [codecov.io](https://codecov.io) → Login with GitHub
2. Додай свій репозиторій
3. Скопіюй токен у GitHub Secrets як `CODECOV_TOKEN`
4. Після першого CI запуску badge у README стане активним

## Troubleshooting

**`ALLOWED_HOSTS` помилка:**
```
ALLOWED_HOSTS=твій-домен.railway.app,localhost
```

**Статичні файли не завантажуються:**
```bash
python manage.py collectstatic --noinput
```
WhiteNoise роздає їх автоматично — nginx не потрібен.

**Celery не запускається:**
Перевір що `REDIS_URL` / `CELERY_BROKER_URL` правильно встановлені.
