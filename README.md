# Finora — Personal & Family Financial Management Platform

Build `v1.2.0-foundation` — first implementation pass against the spec, covering
authentication, financial profiles, accounts, categories, and transactions,
plus the security/correctness hardening described below.

This is a **foundation build**: the modules for Budgets, Savings Goals, Bank
Statement Import, Reports, Family collaboration, and Analytics are scaffolded
in navigation but not yet implemented (they show a "coming soon" placeholder).
Auth, profiles, accounts, and transactions — the core financial ledger — are
fully working, tested, and verified against a real PostgreSQL database.

---

## What's implemented

- **Auth**: email/password registration & login, JWT (access + rotating
  refresh tokens) for the API, Django sessions for the web UI, TOTP-based
  two-factor authentication with backup codes, account lockout after 5 failed
  logins, password strength validation.
- **Security**: field-level encryption (Fernet) for phone number, date of
  birth, and bank account last-4-digits — verified to store ciphertext in the
  database, not plaintext. Scoped rate limiting per endpoint type. Structured
  security logging separate from application logs. Append-only audit trail
  for every mutation.
- **Data integrity**: all money stored as `Decimal`, never float. Soft-delete
  on every financial model (nothing is ever hard-deleted). Optimistic
  concurrency control on transaction edits (prevents two people silently
  overwriting each other's changes). Duplicate-transaction detection with an
  override option. A database-level `CHECK` constraint that rejects
  non-positive amounts even if application code is bypassed.
- **Core models**: Users, Financial Profiles, Families (role-based, not yet
  exposed in the UI), Accounts, Categories (24 seeded defaults + 21
  auto-categorization rules), Transactions.
- **API**: REST endpoints under `/api/v1/`, browsable OpenAPI docs at
  `/api/docs/`, a DB-checking health endpoint at `/api/v1/health/`.
- **Web UI**: Django templates + Tailwind (CDN) + HTMX + Alpine.js — login,
  register, dashboard with real summary cards and category breakdown,
  transactions list, accounts list, settings.
- **Tests**: 18 automated tests covering auth, lockout, MFA, duplicate
  detection, concurrency conflicts, soft-delete, and the income/expense/
  savings formulas. All passing.

## What's *not* yet implemented

Budgets, Savings Goals, Bank Statement Import/OCR, Reports & PDF export,
Family invitations UI, Analytics/Monte Carlo, notifications, and data
export/delete (GDPR-style). These are the next build phases.

---

## Prerequisites (Windows)

1. **Python 3.11 or 3.12** — [python.org/downloads](https://www.python.org/downloads/).
   During install, check "Add python.exe to PATH".
2. **PostgreSQL 16** — [postgresql.org/download/windows](https://www.postgresql.org/download/windows/).
   Remember the password you set for the `postgres` user during install.
3. **Redis** — Windows doesn't ship Redis natively. Easiest options:
   - Install [Memurai](https://www.memurai.com/) (Redis-compatible, native Windows), or
   - Use WSL2 and run Redis inside it, or
   - Use Docker Desktop and run `docker run -p 6379:6379 redis:7`
4. **Git** (optional, if you want version control) — [git-scm.com](https://git-scm.com/).

## Setup

Open **PowerShell** in the project folder:

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the environment template and edit it
copy .env.example .env
notepad .env
```

In `.env`, at minimum set:
- `POSTGRES_PASSWORD` — the password you set for PostgreSQL during install
- `SECRET_KEY` — generate one:
  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- `FIELD_ENCRYPTION_KEY` — generate one:
  ```powershell
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
  **Do not lose this key after real data exists** — it's needed to decrypt
  phone numbers, DOB, and account digits. Losing it makes that data
  unrecoverable (by design — that's what encryption means).

```powershell
# 4. Create the database (using psql, or pgAdmin's GUI)
psql -U postgres -c "CREATE DATABASE finance_app_dev;"

# 5. Run migrations (creates tables + seeds default categories)
python manage.py migrate

# 6. Create an admin user for the Django admin panel
python manage.py createsuperuser

# 7. Collect static files
python manage.py collectstatic --noinput

# 8. Run the server
python manage.py runserver
```

Visit:
- **Web app**: http://localhost:8000/
- **Django admin**: http://localhost:8000/admin/
- **API docs**: http://localhost:8000/api/docs/
- **Health check**: http://localhost:8000/api/v1/health/

## Running the background worker (Celery)

Statement processing and scheduled tasks (not yet built, but wired up) run
through Celery. In a **second** PowerShell window, with the venv activated:

```powershell
celery -A config worker --loglevel=info --pool=solo
```

(`--pool=solo` is required on Windows — the default `prefork` pool doesn't
work there.)

## Running tests

```powershell
pytest
```

All 18 tests should pass. They run against a real (temporary, auto-created)
PostgreSQL test database — no mocking of the database layer.

---

## Project structure

```
financial_app/
├── config/              # Django settings, root URLconf, Celery app
├── apps/
│   ├── common/           # Base models (soft-delete, UUID, timestamps), shared utilities
│   ├── audit/             # Append-only audit log + request logging middleware
│   ├── users/              # Custom User model, auth service (login/MFA/lockout)
│   ├── profiles/            # Financial Profile model + service
│   ├── families/              # Family / FamilyMembership / FamilyInvitation models
│   ├── categories/              # Category + auto-categorization rules
│   ├── accounts/                  # Bank/cash/card account model
│   ├── transactions/                # Core ledger + financial calculation service
│   ├── api/                           # API URL routing + health check
│   └── web/                             # Template-driven frontend views
├── templates/            # Django templates (base layout, dashboard, auth pages)
├── static/                # CSS/JS (currently minimal — Tailwind loads via CDN)
├── .env.example           # All required environment variables, documented
└── requirements.txt        # Pinned dependency versions
```

Each domain app follows the same internal shape: `models.py` for data,
`services/` for business logic (never in views), `api/` for REST
serializers+views, `admin.py` for the Django admin, `tests/` for pytest tests.
This mirrors the layered architecture from the build spec — views and
serializers stay thin; all financial logic and validation lives in the
service layer so it's consistent across the API, the web UI, and any future
Celery tasks.

## Notes on production readiness

Before deploying this anywhere real:

- Set `DEBUG=False` and a real `ALLOWED_HOSTS` in `.env`.
- Put this behind a real WSGI server (`gunicorn`, already in requirements)
  and a reverse proxy (nginx) terminating TLS — the security settings in
  `config/settings.py` (HSTS, secure cookies, SSL redirect) activate
  automatically once `DEBUG=False`.
- Swap the Tailwind CDN `<script>` tag in `templates/base.html` for a
  compiled, purged Tailwind build — the CDN version is fine for development
  but ships the entire framework unminified.
- Set a real `SENTRY_DSN` for error monitoring.
- Set up automated PostgreSQL backups (not configured here — this is
  infrastructure-specific).
- Review and rotate `SECRET_KEY` and `FIELD_ENCRYPTION_KEY` through a real
  secrets manager rather than a `.env` file.
