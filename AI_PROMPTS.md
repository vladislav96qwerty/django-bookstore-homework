# AI Prompts Used — ДЗ 25.1

> **Model used:** Claude Sonnet (Anthropic)
> **Project:** Django Bookstore Homework
> **Date:** 2026-04-22

This file lists all prompts sent to the AI during assignment ДЗ 25.1, grouped by task.

---

## 1. Code Review Prompts

### Prompt 1.1 — `payment_success` view review

```
You are a senior Django developer. Review the following view for bugs, 
security issues, and best practices. Be specific and provide a corrected 
version with explanations.

[payment_success code pasted]

Focus on:
- Transaction safety
- Idempotency (what happens if the user refreshes the page?)
- Cart clearing timing
- Email sending in the request cycle
```

**AI findings applied:**
- Added idempotency check (`Order.objects.filter(stripe_session_id=session_id).first()`)
- Moved `cart.clear()` inside `transaction.atomic()`
- Added empty cart guard before creating an Order
- Added full docstring

---

### Prompt 1.2 — `checkout` view review

```
You are a senior Django developer. Review this Stripe checkout view.
Pay attention to:
1. Decimal to cents conversion correctness
2. Error handling for Stripe API failures  
3. Deprecated Stripe parameters
4. Missing validations

[checkout code pasted]

Provide a corrected version.
```

**AI findings applied:**
- Replaced `int(float(price) * 100)` with safe `Decimal` + `ROUND_HALF_UP` conversion
- Added `try/except stripe.error.StripeError` with user-friendly error page
- Removed deprecated `payment_method_types=['card']` parameter
- Added docstring

---

### Prompt 1.3 — `BookListView` review

```
You are a senior Django developer reviewing a Django Class-Based View.
The view handles book listing, search filtering, and language switching.

[BookListView code pasted]

Issues to check:
- Django 4.0+ compatibility (session-based language key was removed)
- N+1 queries in queryset
- Search input sanitisation
- Code organisation

Provide a corrected version with docstring.
```

**AI findings applied:**
- Replaced `translation.LANGUAGE_SESSION_KEY` (removed in Django 4.0) with `LANGUAGE_COOKIE_NAME` cookie approach via `render_to_response`
- Added `select_related('category')` to avoid N+1
- Added query trim `[:100]` to prevent overly long DB queries
- Added comprehensive class docstring

---

## 2. Test Generation Prompts

### Prompt 2.1 — Category and Book model tests

```
Generate comprehensive pytest tests for the following Django models:
Category and Book (from shop/models.py).

[models.py pasted]

Requirements:
- Use pytest-django with @pytest.mark.django_db
- Cover: __str__, auto slug, field validators, ordering, relations
- Each test must have the comment: # Generated with AI, reviewed and modified
- Use fixtures: category, book (already defined in conftest.py)
- Test edge cases: negative price, blank description, duplicate name
```

---

### Prompt 2.2 — Order and OrderItem model tests

```
Generate pytest tests for the Order and OrderItem Django models.

[Order, OrderItem model code pasted]
[conftest.py pasted]

Requirements:
- Cover: get_total_price(), status choices, ordering, cascade deletes
- Multiple items total calculation
- Each test: # Generated with AI, reviewed and modified
- Use @pytest.mark.django_db
```

---

### Prompt 2.3 — Profile model tests

```
Generate pytest tests for this Django Profile model (accounts app):

[Profile model code pasted]

Cover:
- __str__ representation
- One-to-one constraint (duplicate profile should raise error)
- Cascade delete when user is deleted
- phone_number blank default
- created_at / updated_at auto fields

Comment on each test: # Generated with AI, reviewed and modified
```

---

### Prompt 2.4 — View HTTP tests

```
Generate pytest HTTP tests for the following Django views using Django's test Client.

[shop/views.py and accounts/views.py pasted]

Requirements:
- Use client fixture (Django test Client)
- Test: status codes (200, 302, 404), redirect targets, response content
- Test auth-required views return redirect to login
- Test async views return valid JSON
- Each test: # Generated with AI, reviewed and modified
- Use reverse() for all URLs
```

---

## 3. Documentation Prompts

### Prompt 3.1 — View docstrings

```
Add Google-style docstrings to all functions and class-based views in 
the following Django views file. Document Args, Returns, and any 
important side effects (DB writes, emails, Stripe calls).

[shop/views.py pasted]
```

---

### Prompt 3.2 — README generation

```
Generate a professional README.md for this Django bookstore project.

Project details:
- Django 6.0, PostgreSQL, Stripe payments, async views
- Docker setup
- pytest test suite
- Ukrainian + English i18n

Include sections:
- Features
- Tech Stack table
- Quick Start (Docker and local)
- Running Tests
- Project Structure
- Environment Variables table
- API Endpoints table
- AI Usage section (describe how AI was used for code review, tests, docs)
- Contributing
- License
```

---

### Prompt 3.3 — AI_REVIEW.md structure

```
I performed AI code review on 3 Django views. Help me format the results 
into a professional AI_REVIEW.md file with these sections for each view:
1. Original Code
2. AI Recommendations (numbered list)
3. Final Improved Code
4. Summary of changes

Views reviewed: payment_success, checkout, BookListView
```

---

## Summary

| Task | Prompts Used | AI Suggestions Applied |
|---|---|---|
| Code Review | 3 | 13 out of 14 suggestions |
| Test Generation | 4 | Full test suite generated (60 tests) |
| Documentation | 3 | All docstrings + README + this file |
| **Total** | **10** | — |

### What was NOT applied from AI suggestions

- **Email via Celery** (Prompt 1.1) — Celery is not yet configured in the project; `fail_silently=True` is acceptable for now.
- **Stock validation in checkout** (Prompt 1.2) — deferred to a future sprint; would require a separate stock reservation system.
