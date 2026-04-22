# Django Bookstore

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

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6.0 |
| Database | PostgreSQL (via psycopg3) |
| Payments | Stripe |
| Tests | pytest + pytest-django + factory-boy |
| Coverage | pytest-cov |
| Container | Docker / docker-compose |
| Frontend | Bootstrap 5 + Django templates |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/vladislav96qwerty/django-bookstore-homework.git
cd django-bookstore-homework

# 2. Create .env (see .env.example)
cp .env.example .env

# 3. Start with Docker
docker-compose up --build

# 4. Run migrations & load data
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py loaddata data.json

# 5. Open http://localhost:8000
```

### Local (without Docker)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Use SQLite settings for local dev
export DJANGO_SETTINGS_MODULE=bookstore.settings_sqlite

python manage.py migrate
python manage.py runserver
```

---

## Running Tests

```bash
# All tests with coverage report
pytest tests/ -v --cov=shop --cov=accounts --cov-report=term-missing

# Just the model tests
pytest tests/test_all.py -v -k "Model"
```

Expected coverage: **≥ 60%** for `shop.models`, `accounts.models`, `shop.views`, `accounts.views`.

---

## Project Structure

```
bookstore/          # Django project config (settings, urls, wsgi)
accounts/           # User registration, login, profile
shop/               # Books, categories, cart, orders, Stripe views
templates/          # HTML templates (base, shop, accounts)
tests/              # pytest test suite
static/css/         # Global styles
locale/             # i18n translations (en, uk)
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | insecure dev key |
| `DEBUG` | Enable debug mode | `False` |
| `DB_NAME` | PostgreSQL database name | `bookstore` |
| `DB_USER` | PostgreSQL user | `bookstore_user` |
| `DB_PASSWORD` | PostgreSQL password | `bookstore_password` |
| `DB_HOST` | PostgreSQL host | `db` |
| `STRIPE_PUBLIC_KEY` | Stripe publishable key | — |
| `STRIPE_SECRET_KEY` | Stripe secret key | — |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | — |
| `EMAIL_HOST_USER` | SMTP username | — |
| `EMAIL_HOST_PASSWORD` | SMTP password | — |

---

## API Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/shop/api/books/` | Async JSON list of books (supports `?q=`) |
| GET | `/shop/api/books/<pk>/` | Async JSON detail for a single book |
| GET | `/shop/catalog/` | Async catalog grouped by category (HTML) |
| POST | `/shop/webhook/` | Stripe webhook receiver |

---

## AI Usage

This project used AI assistance (Claude by Anthropic) in three areas as part of assignment ДЗ 25.1:

### 1. Code Review

Three complex views were reviewed by AI:
- `payment_success` — idempotency bug found and fixed (duplicate orders on refresh)
- `checkout` — float→cents precision bug fixed; deprecated Stripe param removed
- `BookListView` — deprecated `LANGUAGE_SESSION_KEY` replaced with cookie approach

Full details in [`AI_REVIEW.md`](./AI_REVIEW.md).

### 2. Test Generation

AI generated the full test suite in `tests/test_all.py` covering:
- `Category`, `Book`, `Order`, `OrderItem` model tests (fields, constraints, relations, totals)
- `Profile` model tests
- View HTTP tests (status codes, redirects, content assertions)
- Async view JSON API tests

Every test includes the comment: `# Generated with AI, reviewed and modified`

### 3. Documentation

AI generated:
- All view docstrings (Args / Returns / Raises documented)
- This README
- `AI_PROMPTS.md` — full list of prompts used

See [`AI_PROMPTS.md`](./AI_PROMPTS.md) for the exact prompts.

---

## Data Migration Notes

See [`DATA_MIGRATION.md`](./DATA_MIGRATION.md) for instructions on migrating from SQLite to PostgreSQL.

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Run tests and make sure coverage stays ≥ 60%
4. Open a Pull Request

---

## License

MIT
