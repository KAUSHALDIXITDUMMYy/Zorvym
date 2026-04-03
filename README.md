# Finance Dashboard API

Backend for a finance dashboard: **users and roles**, **financial records (CRUD + filters)**, **aggregated dashboard endpoints**, **JWT authentication**, and **role-based access control**. Built with **FastAPI**, **SQLAlchemy 2**, and **SQLite** (easy local persistence; swap `DATABASE_URL` for PostgreSQL or another SQLAlchemy URL).

Interactive docs: run the server and open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Assumptions

- **Single-tenant org data**: financial records are shared for dashboard analytics; `created_by_id` is audit metadata, not row-level ownership.
- **Naive UTC datetimes** in SQLite for `created_at` / `updated_at`; clients may send ISO datetimes for `date` on records.
- **JWT** carries `sub` (user id) and `role`; each request reloads the user from the DB so **role changes and `is_active` take effect immediately** (good for admin workflows).
- **Amounts** are positive numbers; **income vs expense** is determined by `type`, not the sign of `amount`.

## Roles and permissions

| Capability | `viewer` | `analyst` | `admin` |
|------------|----------|-----------|---------|
| Login, `/users/me` | Yes | Yes | Yes |
| Dashboard: `/dashboard/*` | Yes | Yes | Yes |
| List / get `/records` | No | Yes | Yes |
| Create / update / delete `/records` | No | No | Yes |
| User admin: `/users` (list/create/update/delete) | No | No | Yes |

## Setup

```bash
cd finance-backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix: source .venv/bin/activate
pip install -r requirements.txt
```

Optional: copy `.env.example` to `.env` and set `SECRET_KEY` for anything beyond local demos.

### Seed demo data

Creates `admin`, `analyst`, and `viewer` users and sample transactions (skips if users already exist):

```bash
python -m scripts.seed
```

Passwords: `admin123`, `analyst123`, `viewer123` (demo only).

### Run the server

```bash
uvicorn app.main:app --reload
```

### Tests (optional)

```bash
pip install -r requirements-dev.txt
pytest tests -q
```

## API overview

**Auth**

- `POST /auth/login` — JSON `{ "username", "password" }` → `{ "access_token", "token_type": "bearer" }`. Use header `Authorization: Bearer <token>`.

**Users** (admin only, except profile)

- `GET /users/me` — current user profile.
- `GET /users` — paginated list (`skip`, `limit`).
- `POST /users` — create user (`email`, `username`, `password`, `role`, `is_active`).
- `PATCH /users/{id}` — partial update (email, username, role, is_active, password).
- `DELETE /users/{id}` — remove user (financial records keep `created_by_id` as null via `ON DELETE SET NULL`).

**Financial records** (auth required; see role table)

- `GET /records` — pagination (`skip`, `limit`); filters: `date_from`, `date_to`, `category`, `type` (`income` | `expense`).
- `GET /records/{id}`
- `POST /records` — body: `amount` (> 0), `type`, `category`, `date`, optional `notes`.
- `PATCH /records/{id}` — at least one field required.
- `DELETE /records/{id}`

**Dashboard** (all authenticated roles)

- `GET /dashboard/summary` — total income, total expenses, net balance, record count; optional `date_from`, `date_to`.
- `GET /dashboard/categories` — per `(category, type)` totals; optional date range.
- `GET /dashboard/recent` — recent entries (`limit` 1–50).
- `GET /dashboard/trends` — `granularity=weekly|monthly`, optional date range; uses SQLite `strftime` for buckets.

**Other**

- `GET /health` — liveness.

## Validation and errors

- Pydantic validates request bodies and query bounds (e.g. pagination limits, positive `amount`).
- `422` responses include a `detail` array (and a short `message` for validation failures).
- `401` missing/invalid token; `403` wrong role or inactive user; `404` missing resource; `409` duplicate email/username on user writes.

## Tradeoffs

- **SQLite** keeps the submission self-contained; production would typically use a server database and migrations (e.g. Alembic).
- **Weekly trends** use SQLite’s `%W` week numbering (documented behavior; swap SQL for your DB’s week function if needed).
- **JWT secret** defaults for local use only — override with `SECRET_KEY` in `.env`.
