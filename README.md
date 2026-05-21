# Django Bookstore

[![CI/CD](https://github.com/vladislav96qwerty/django-bookstore-homework/actions/workflows/django.yml/badge.svg)](https://github.com/vladislav96qwerty/django-bookstore-homework/actions/workflows/django.yml)
[![codecov](https://codecov.io/gh/vladislav96qwerty/django-bookstore-homework/branch/main/graph/badge.svg)](https://codecov.io/gh/vladislav96qwerty/django-bookstore-homework)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![Django 6.0](https://img.shields.io/badge/django-6.0-green.svg)](https://docs.djangoproject.com/en/6.0/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/)

A full-featured online bookstore built with Django, featuring user authentication, a shopping cart, Stripe payments, async API views, and i18n support.

---

## Features

- Browse and search books by title or author
- Category-based catalog with async JSON API
- Shopping cart (session-based)
- Stripe Checkout integration with payment success/cancel flows
- User registration, login, and profile management
- Staff-only book CRUD (Create / Update / Delete)
- Stripe webhook handler for order status sync
- Ukrainian and English locale support
- Dockerised (PostgreSQL + Redis ready)
- Test suite with ≥ 60% coverage on core models and views
- GitHub Actions CI/CD (lint → test → Docker build & push)
- Deployed on Railway with PostgreSQL and Redis
- Health check endpoint at `/health/`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6.0 |
| Database | PostgreSQL (via psycopg3) |
| Cache / Broker | Redis |
| Async tasks | Celery + Celery Beat |
| Payments | Stripe |
| Tests | pytest + pytest-django + factory-boy |
| Coverage | pytest-cov + Codecov |
| Container | Docker / docker-compose |
| WSGI | Gunicorn |
| Static files | WhiteNoise |
| CI/CD | GitHub Actions |
| Deployment | Railway |
| Frontend | Bootstrap 5 + Django templates |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/vladislav96qwerty/django-bookstore-homework.git
cd django-bookstore-homework

# 2. Create .env
cp .env.example .env

# 3. Start with Docker
docker-compose up --build

# 4. Run migrations & load data
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput

# 5. Open http://localhost:8000
# 6. Health check: http://localhost:8000/health/
```

### Local (without Docker)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# SQLite + development settings
export DJANGO_SETTINGS_MODULE=bookstore.settings_sqlite

python manage.py migrate
python manage.py runserver
```

---

## Running Tests

```bash
# All tests with coverage report
pytest tests/ -v --cov=shop --cov=accounts --cov-report=term-missing

# Only API tests
pytest tests/test_api.py -v

# Only model/view tests
pytest tests/test_all.py -v
```

Expected coverage: **≥ 60%** for `shop` and `accounts`.

---

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/django.yml`) runs on every push to `main` or `develop`:

1. **Lint** — `flake8` + `black --check`
2. **Test** — `pytest` with coverage (fails if < 60%)
3. **Docker** — builds image and pushes to Docker Hub (only on `main`)

### Required GitHub Secrets

| Secret | Description |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `CODECOV_TOKEN` | Codecov upload token (optional) |

---

## Deployment (Railway)

1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Add PostgreSQL plugin → Add Redis plugin
4. Set environment variables (see `.env.example`):
   - `DJANGO_ENV=production`
   - `SECRET_KEY=<strong-random-key>`
   - `ALLOWED_HOSTS=<your-railway-domain>`
   - `DATABASE_URL` — автоматично Railway
   - `REDIS_URL` — автоматично Railway
5. Railway запустить `Procfile` автоматично

---

## Project Structure

```
bookstore/
├── settings/
│   ├── __init__.py     # вибирає dev або prod за DJANGO_ENV
│   ├── base.py         # спільні налаштування
│   ├── development.py  # SQLite, console email
│   └── production.py   # PostgreSQL, security headers, WhiteNoise
accounts/               # User registration, login, profile
shop/                   # Books, categories, cart, orders, Stripe views
  └── api/              # DRF ViewSets, serializers, filters
templates/              # HTML templates
tests/                  # pytest test suite
.github/
  └── workflows/
      └── django.yml    # CI/CD pipeline
Dockerfile
docker-compose.yml
Procfile                # Railway/Heroku process definitions
gunicorn.conf.py        # Gunicorn production config
```

---

## Health Check

```
GET /health/
```

Повертає `200 OK` якщо БД і Redis доступні:

```json
{"status": "ok", "database": "ok", "cache": "ok"}
```

Повертає `503` якщо щось недоступне.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | insecure dev key |
| `DJANGO_ENV` | `development` or `production` | `development` |
| `DEBUG` | Enable debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated hosts | — |
| `DATABASE_URL` | Full PostgreSQL URL | — |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `STRIPE_PUBLIC_KEY` | Stripe publishable key | — |
| `STRIPE_SECRET_KEY` | Stripe secret key | — |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | — |
| `EMAIL_HOST_USER` | SMTP username | — |
| `EMAIL_HOST_PASSWORD` | SMTP password | — |
| `CORS_ALLOWED_ORIGINS` | Comma-separated CORS origins | — |

---

## API Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/health/` | Health check (DB + Redis) |
| GET | `/api/books/` | List books (filter, search, paginate) |
| GET | `/api/books/<pk>/` | Book detail |
| GET | `/api/categories/` | List categories |
| GET | `/api/orders/` | List own orders (auth required) |
| GET | `/api/cart/` | Cart contents (auth required) |
| POST | `/api/cart/add/` | Add item to cart |
| POST | `/api/token/` | Obtain JWT token |
| POST | `/api/token/refresh/` | Refresh JWT token |
| GET | `/api/docs/` | Swagger UI |

---

## AI Usage

This project used AI assistance (Claude by Anthropic) in three areas as part of assignment ДЗ 25.1:

### 1. Code Review

Three complex views were reviewed by AI — full details in [`AI_REVIEW.md`](./AI_REVIEW.md).

### 2. Test Generation

AI generated the full test suite in `tests/test_all.py` and `tests/test_api.py`.

### 3. Documentation

AI generated view docstrings, this README, and [`AI_PROMPTS.md`](./AI_PROMPTS.md).

---

## License

MIT
