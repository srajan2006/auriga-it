 # AVault

AVault is a college AV equipment lending system. This repository currently contains **Phase 10: admin settings, borrowing limits, and transfer rules**: a Django REST API backed by PostgreSQL and a Next.js frontend connected to JWT authentication, inventory, availability, bookings, loans, returns, late fees, transfer history, and persisted system settings.

## Problem statement

The AV room's paper register makes availability, bookings, borrowers, returns, and late equipment difficult to track. AVault will replace that register with a shared system for students, staff, and administrators.

## Architecture

```text
Next.js frontend (localhost:3000)
	|
	v
Django REST API (localhost:8000)
	|
	v
PostgreSQL (localhost:5432)
```

The frontend only talks to the REST API. It never connects directly to PostgreSQL.

## Technology stack

- Next.js, TypeScript, and Tailwind CSS
- Python, Django, Django REST Framework, and SimpleJWT dependency
- PostgreSQL

## Repository structure

```text
avault/
├── backend/
│   ├── accounts/        # Custom user model, JWT auth, and role permissions
│   ├── common/          # Health endpoint
│   ├── inventory/       # Categories, equipment models, units, and seed data
│   ├── bookings/        # Reservation dates and assigned units for availability checks
│   ├── loans/           # Issued equipment and active loan records
│   ├── config/          # Django project configuration
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js App Router pages
│   ├── lib/              # API helper functions
│   ├── package.json
│   └── ...
├── .env.example
└── README.md
```

System settings are persisted in PostgreSQL and editable by admins through the settings API.

## Prerequisites

- Python 3.11+
- Node.js 18.17+
- PostgreSQL 14+

## PostgreSQL setup

Create a local PostgreSQL database and user. For the default development connection:

```sql
CREATE USER postgres WITH PASSWORD 'postgres';
CREATE DATABASE avault OWNER postgres;
```

If your local PostgreSQL installation already has a different user or password, update `DATABASE_URL` accordingly.

## Environment variables

Copy `.env.example` to `.env` for the backend and export the values before starting Django. The frontend reads `NEXT_PUBLIC_API_URL` from `frontend/.env.local`.

Backend `.env`:

```dotenv
SECRET_KEY=replace-with-a-long-random-development-value
DEBUG=True
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/avault
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
MAX_ACTIVE_LOANS_PER_USER=3
```

Frontend `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Do not commit real secrets or local environment files.

## Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py seed_data
python manage.py runserver 8000
```

Health endpoint:

```text
GET http://localhost:8000/api/health/
```

It returns HTTP 200 when Django and PostgreSQL are available, and HTTP 503 when Django is running but the database cannot be reached.

## Authentication API

All authentication endpoints are under `/api/auth/`:

```text
POST /api/auth/register/
POST /api/auth/login/
POST /api/auth/refresh/
POST /api/auth/logout/       # Requires Bearer access token
GET  /api/auth/me/           # Requires Bearer access token
```

Registration always creates a `STUDENT`. `STAFF` and `ADMIN` accounts must be created or promoted by an administrator; clients cannot submit a role during registration. Access tokens expire after 30 minutes, refresh tokens after one day, and logout blacklists the submitted refresh token.

Send protected requests with:

```text
Authorization: Bearer <access-token>
```

## Inventory API

Inventory reads require authentication. Category and equipment model writes, plus all physical unit management, require `STAFF` or `ADMIN` access.

```text
GET    /api/categories/
POST   /api/categories/             # STAFF/ADMIN
PATCH  /api/categories/{id}/        # STAFF/ADMIN
DELETE /api/categories/{id}/        # STAFF/ADMIN
GET    /api/equipment/
POST   /api/equipment/              # STAFF/ADMIN
PATCH  /api/equipment/{id}/         # STAFF/ADMIN
DELETE /api/equipment/{id}/         # STAFF/ADMIN
GET    /api/equipment/{id}/availability/
GET    /api/equipment-units/        # STAFF/ADMIN
POST   /api/equipment-units/        # STAFF/ADMIN
PATCH  /api/equipment-units/{id}/   # STAFF/ADMIN
DELETE /api/equipment-units/{id}/   # STAFF/ADMIN
```

Equipment supports `search`, `category`, and `availability=available|unavailable` query parameters. Students see active equipment and aggregate unit counts; physical asset records are staff/admin-only.

## Date-range availability

Check individual physical units for a date range without creating a booking:

```text
GET /api/equipment/{id}/availability/?start_date=2026-09-12&end_date=2026-09-14
```

The date range uses a half-open interval. An existing reservation conflicts when `requested_start < existing_end` and `requested_end > existing_start`; therefore, a request beginning on an existing reservation's end date is adjacent and does not conflict. Pending and approved reservations block assigned units. Rejected, cancelled, and completed reservations do not. Units with non-`AVAILABLE` status are excluded regardless of reservations.

The student-facing search is available at `/availability`. It displays available quantity and asset codes, but does not create or modify bookings.

## Booking API

Students can create and view their own booking requests. Staff and admins can view all requests, approve requests by assigning physical unit IDs, reject requests, and cancel eligible requests:

```text
GET  /api/bookings/
POST /api/bookings/
GET  /api/bookings/{id}/
POST /api/bookings/{id}/approve/   # STAFF/ADMIN, with unit_ids
POST /api/bookings/{id}/reject/    # STAFF/ADMIN
POST /api/bookings/{id}/cancel/    # Owner or STAFF/ADMIN
```

Booking creation re-checks date-range availability and equipment quantity limits on the backend. Approval uses a database transaction, locks selected units, verifies exact equipment quantities, prevents conflicts, and marks assigned units `RESERVED`. The frontend pages are `/bookings` for students and `/staff/bookings` for staff/admin users.

## Loans and equipment issue API

Only staff and admins can issue equipment. A booking must be `APPROVED`, have assigned physical units, and not already have a loan:

```text
GET  /api/loans/                         # Students see only their own loans
GET  /api/loans/{id}/
POST /api/loans/issue-booking/{booking_id}/  # STAFF/ADMIN
```

Issue requests require `due_at` and may include per-unit issue conditions. The backend transaction locks the booking and units, snapshots `condition_at_issue`, creates an `ACTIVE` loan, and changes units from `RESERVED` to `ISSUED`. The student loan page is `/loans`; the staff issue desk is `/staff/loans`.

## Returns and late fees API

Staff and admins process every issued unit in a loan in one transaction:

```text
POST /api/loans/{id}/return/
GET  /api/late-fees/
POST /api/late-fees/{id}/pay/      # STAFF/ADMIN
POST /api/late-fees/{id}/waive/    # STAFF/ADMIN
```

Each return item records a return condition and resulting unit status (`AVAILABLE`, `DAMAGED`, `MAINTENANCE`, or `LOST`). A loan can only be returned once. Late days are never negative and are calculated from the return date versus the due date; the fee is `late_days × late_fee_per_day`, summed across returned equipment units. On-time returns create a zero-value waived fee. The staff return desk is `/staff/returns`; students see overdue loans and pending fees at `/loans`.

## Active loan transfer API

Staff and admins can transfer an active or overdue loan to another active student without creating a new loan or changing equipment state:

```text
POST /api/loans/{id}/transfer/
GET  /api/loans/{id}/transfers/
```

The request body is `{ "new_borrower_id": 123, "reason": "Club handover" }`. The original loan ID, items, unit status, issue time, due date, loan status, booking, and late-fee timeline remain unchanged. Transfer history is append-only and returned newest first. `MAX_ACTIVE_LOANS_PER_USER` controls destination eligibility and defaults to `3`.

## System settings API

Authenticated users can read current settings, but only admins can modify them:

```text
GET   /api/settings/
PATCH /api/settings/       # ADMIN only
```

The persisted settings are:

- `max_active_loans_per_user`
- `max_units_per_booking`
- `default_late_fee_per_day`

Booking creation, transfer eligibility, and late-fee calculation read these values dynamically from PostgreSQL. `MAX_ACTIVE_LOANS_PER_USER` remains as a development environment fallback/compatibility setting, while the database singleton is authoritative after migration.

## Final lifecycle verification

The backend regression suite includes the complete path:

```text
student -> availability -> booking -> staff approval -> unit assignment
-> issue -> active loan -> staff transfer -> overdue state -> return -> late fee
```

The transfer lifecycle asserts that the same loan, loan item, and equipment unit remain in place; the unit stays `ISSUED` while transferred; the original due date and overdue duration are preserved; the original borrower loses access; the new borrower gains access; and the unit becomes `AVAILABLE` only after a good-condition return. Transfer records remain append-only.

## Run the frontend

In a second terminal:

```bash
cd frontend
cp ../.env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Use `/register` or `/login` to authenticate against Django, then `/dashboard` to view the authenticated `/me` response and role. Students can browse `/equipment`; staff and admins can manage inventory at `/staff/equipment`.

## Checks and tests

Backend checks:

```bash
cd backend
python manage.py check
```

Frontend checks:

```bash
cd frontend
npm run build
```

Run the Phase 2 through Phase 10 tests with:

```bash
cd backend
python manage.py test accounts common inventory bookings loans
```

The test command requires a running PostgreSQL server because the project intentionally uses PostgreSQL for both development and tests.

## Planned API and model surface

## Seed data

After migrations, run:

```bash
python manage.py seed_data
```

This creates one admin, one staff user, five students, five categories, and sample equipment models with physical units. Seeded users use the password `ChangeMe123!`:

```text
admin@avault.local
staff@avault.local
student1@avault.local through student5@avault.local
```

Later phases will add returns, late fees, and system settings. The REST API will remain under `/api/`.

## Default development credentials

No seed users exist yet. Staff and admin development credentials will be documented when the seed command is introduced.

## Future improvements

- Equipment availability and conflict-safe bookings
- Staff issue and return workflows
- Automatic overdue detection and late fees
- Student, staff, and admin dashboards
- Audit history and production deployment configuration
