# AVault

AVault is a digital equipment lending and inventory management system designed for college AV rooms. It replaces the traditional paper-based equipment register with a centralized web application for managing equipment, bookings, loans, returns, overdue items, and borrowing history.

The system supports three roles:

* **STUDENT** — browse equipment, check availability, request bookings, view loans and fees.
* **STAFF** — manage bookings, issue equipment, process returns, handle overdue items, and transfer active loans.
* **ADMIN** — manage users and system-level borrowing settings.

---

## 1. Technology Stack

### Frontend

* Next.js
* TypeScript
* Tailwind CSS

### Backend

* Python
* Django
* Django REST Framework
* SimpleJWT

### Database

* PostgreSQL

### Development

* Git
* GitHub
* GitHub Codespaces

---

## 2. Project Structure

```text
avault/
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env
│   └── ...
│
├── frontend/
│   ├── package.json
│   ├── next.config.*
│   └── ...
│
├── README.md
├── REASONING.md
└── ...
```

The exact application folders may differ depending on the implementation.

---

# 3. Prerequisites

For local development or GitHub Codespaces, install/have available:

* Python 3
* pip
* Node.js and npm
* PostgreSQL
* Git

GitHub Codespaces can be used as the primary development environment.

---

# 4. PostgreSQL Setup

PostgreSQL is not automatically created simply because the project uses Django.

For a Codespace development environment, PostgreSQL can be installed locally inside the Codespace.

## Start PostgreSQL

```bash
sudo service postgresql start
```

Check its status:

```bash
sudo service postgresql status
```

If you are already operating as `root`, the `sudo` command is not required.

---

## Create the AVault database

Enter PostgreSQL as the PostgreSQL administrator:

```bash
su - postgres
psql
```

Check existing users:

```sql
\du
```

Create the application user if it does not already exist:

```sql
CREATE USER avault_user WITH PASSWORD 'avault_password';
```

If the user already exists, reset its password:

```sql
ALTER USER avault_user WITH PASSWORD 'avault_password';
```

Create the database:

```sql
CREATE DATABASE avault_db OWNER avault_user;
```

If the database already exists, do not create it again.

Grant privileges:

```sql
GRANT ALL PRIVILEGES ON DATABASE avault_db TO avault_user;
```

Exit:

```sql
\q
```

Then:

```bash
exit
```

---

## Test PostgreSQL

Run:

```bash
psql -U avault_user -d avault_db -h localhost
```

Enter:

```text
avault_password
```

A successful connection should display:

```text
avault_db=>
```

Exit with:

```sql
\q
```

---

# 5. Backend Setup

Open a terminal and move to the backend:

```bash
cd backend
```

Check that Django's management file exists:

```bash
ls
```

You should see:

```text
manage.py
```

---

## Create a virtual environment

If `.venv` does not exist:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

You should see something similar to:

```text
(.venv) ...
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

If PostgreSQL support is required and not already included:

```bash
pip install psycopg2-binary
```

If it was installed manually, make sure it is included in `requirements.txt`.

---

# 6. Environment Variables

The backend should contain a `.env` file.

For the Codespace PostgreSQL setup:

```env
DATABASE_URL=postgresql://avault_user:avault_password@localhost:5432/avault_db
```

Other required environment variables depend on the implementation.

Do **not** commit passwords, secret keys, or other credentials to GitHub.

Add `.env` to `.gitignore`.

Example:

```gitignore
.env
.venv/
__pycache__/
```

---

# 7. Run Django Checks

From the `backend` directory:

```bash
python manage.py check
```

If there are no configuration errors, continue.

---

# 8. Run Database Migrations

Run:

```bash
python manage.py makemigrations
```

Then:

```bash
python manage.py migrate
```

If migrations are already generated and tracked in the repository, normally only:

```bash
python manage.py migrate
```

is required.

---

# 9. Seed Development Data

If the project contains the custom seed command:

```bash
python manage.py seed_data
```

This can create development users, categories, equipment models, physical equipment units, and default settings.

Do not use development seed credentials in production.

---

# 10. Run the Backend

From:

```text
backend/
```

run:

```bash
python manage.py runserver 0.0.0.0:8000
```

The Django API will normally be available at:

```text
http://localhost:8000
```

In GitHub Codespaces, port `8000` should appear in the **Ports** section.

If the project contains a health endpoint, verify it using:

```text
/api/health/
```

---

# 11. Run the Frontend

Open a **second terminal**.

Go to:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start Next.js:

```bash
npm run dev
```

The frontend normally runs on:

```text
http://localhost:3000
```

Do not stop the backend terminal while running the frontend.

The development setup therefore normally uses:

```text
Terminal 1 → Django → port 8000
Terminal 2 → Next.js → port 3000
PostgreSQL → port 5432
```

---

# 12. Application Flow

The main workflow is:

```text
Student
   ↓
Browse Equipment
   ↓
Check Availability
   ↓
Create Booking Request
   ↓
Staff Approval
   ↓
Equipment Issue
   ↓
Active Loan
   ↓
Return
   ↓
Condition Check
   ↓
Available / Damaged / Maintenance
```

For overdue loans:

```text
Due Date Passed
      ↓
OVERDUE
      ↓
Late Fee Calculation
      ↓
Return
      ↓
Late Fee Pending / Paid / Waived
```

---

# 13. Active Loan Transfer

AVault supports transferring an active loan from one student to another.

A transfer is **not** a return and does not create a new loan.

The following remain unchanged:

* Loan ID
* Equipment unit
* Issue date
* Original due date
* Loan status
* Equipment availability state

Only the current borrower changes.

Example:

```text
Rahul
  ↓
Loan #25
  ↓
Canon EOS 1500D - Unit 2
  ↓
Due: 20 September
```

After transfer:

```text
Aman
  ↓
Loan #25
  ↓
Canon EOS 1500D - Unit 2
  ↓
Due: 20 September
```

The equipment must never temporarily become `AVAILABLE`.

---

## Transfer API

The transfer endpoint is:

```http
POST /api/loans/{id}/transfer/
```

Example request:

```json
{
  "new_borrower_id": 12,
  "reason": "Equipment responsibility transferred to project partner"
}
```

Transfer history can be retrieved using:

```http
GET /api/loans/{id}/transfers/
```

Only staff/admin users can perform transfers.

Students cannot transfer loans.

---

# 14. Important Business Rules

## Equipment Availability

A physical equipment unit cannot be double-booked.

Two booking periods overlap when:

```text
requested_start < existing_end
AND
requested_end > existing_start
```

This rule must be enforced by the backend.

---

## Borrowing Limits

The system uses configurable borrowing limits.

Important settings include:

```text
max_active_loans_per_user
max_units_per_booking
default_late_fee_per_day
```

A user must not exceed the configured active-loan limit.

---

## Late Fees

Late fees are calculated using:

```text
late_fee = late_days × late_fee_per_day
```

Late days cannot be negative.

The fee is based on the original due date.

Transferring an overdue loan does not reset or extend its due date.

---

## Return Conditions

When equipment is returned:

```text
Good condition
    → AVAILABLE

Damaged
    → DAMAGED

Requires maintenance
    → MAINTENANCE
```

The backend is responsible for enforcing these rules.

---

# 15. User Roles

## STUDENT

Students can:

* Register/login
* Browse equipment
* Check availability
* Create bookings
* View their bookings
* Cancel eligible bookings
* View current loans
* View loan history
* View late fees

Students cannot:

* Approve bookings
* Issue equipment
* Return equipment on behalf of staff
* Transfer loans
* Manage users
* Modify system settings

---

## STAFF

Staff can:

* View equipment
* Manage inventory
* Review bookings
* Approve/reject bookings
* Issue equipment
* Process returns
* View overdue loans
* Manage late fees
* Transfer active loans

---

## ADMIN

Admins can:

* Manage users
* Manage system settings
* Manage inventory
* Perform staff-level operations
* Configure borrowing limits and late-fee settings

---

# 16. Debugging Guide

## Backend is not running

Check:

```bash
cd backend
source .venv/bin/activate
python manage.py check
```

Then:

```bash
python manage.py migrate
```

Then:

```bash
python manage.py runserver 0.0.0.0:8000
```

---

## PostgreSQL connection error

Check PostgreSQL:

```bash
service postgresql status
```

Start it if necessary:

```bash
service postgresql start
```

Test the database:

```bash
psql -U avault_user -d avault_db -h localhost
```

If authentication fails, verify the password:

```bash
su - postgres
psql
```

Then:

```sql
ALTER USER avault_user WITH PASSWORD 'avault_password';
```

---

## `manage.py` not found

You are probably in the wrong directory.

Run:

```bash
pwd
ls
```

Then locate the backend:

```bash
find .. -name manage.py
```

Move into the directory containing `manage.py`.

---

## Python dependency error

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

---

## Migration errors

First check:

```bash
python manage.py check
```

Then:

```bash
python manage.py showmigrations
```

Do not delete migration files or reset the database blindly.

Inspect the exact migration error first.

---

## Port 8000 is already in use

Find the process:

```bash
lsof -i :8000
```

Alternatively, stop the previous Django development server from its terminal.

Then restart:

```bash
python manage.py runserver 0.0.0.0:8000
```

---

## Frontend is not running

From the frontend directory:

```bash
npm install
npm run dev
```

If dependencies are corrupted:

```bash
rm -rf node_modules
npm install
npm run dev
```

---

## Frontend cannot connect to backend

Verify that Django is running:

```text
http://localhost:8000
```

Check the frontend's API/base URL environment variable.

Make sure the frontend is pointing to the actual Codespace backend URL or configured local API URL.

---

# 17. Git Workflow

Check changes:

```bash
git status
```

Add files:

```bash
git add .
```

Commit:

```bash
git commit -m "Update AVault"
```

Push:

```bash
git push
```

Before committing, verify that secrets are not included:

```bash
git status
```

Never commit:

```text
.env
database passwords
JWT secrets
API keys
private credentials
```

---

# 18. Development Checklist

Before considering a feature complete:

* [ ] Backend starts successfully
* [ ] PostgreSQL is running
* [ ] Django checks pass
* [ ] Migrations apply successfully
* [ ] Frontend starts successfully
* [ ] Authentication works
* [ ] Role permissions work
* [ ] Equipment can be created
* [ ] Availability is calculated correctly
* [ ] Double booking is prevented
* [ ] Booking approval works
* [ ] Equipment issue works
* [ ] Returns work
* [ ] Overdue status works
* [ ] Late fees are calculated correctly
* [ ] Borrowing limits are enforced
* [ ] Active loan transfer works
* [ ] Transfer does not change due date
* [ ] Transfer does not release equipment
* [ ] Transfer history is preserved
* [ ] Students only see their current loans
* [ ] Staff can manage operational workflows
* [ ] Admin settings work

---

# 19. Development Principle

AVault follows a backend-first approach for important business rules.

Frontend validation improves user experience, but it must never be considered the security boundary.

The Django backend must independently validate:

* Authentication
* Authorization
* Booking conflicts
* Borrowing limits
* Loan state transitions
* Equipment state transitions
* Late-fee calculations
* Loan transfers
* Return operations

This prevents users from bypassing business rules by directly calling the API.

---

# 20. Development Environment

AVault is currently designed primarily for development in GitHub Codespaces.

The local PostgreSQL database inside a Codespace is suitable for development and testing. It should not be treated as the permanent production database.

For production deployment, a persistent managed PostgreSQL service should be configured separately.

---

## Quick Start

For an already configured Codespace:

### Terminal 1

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2

```bash
cd frontend
npm install
npm run dev
```

Then open the forwarded frontend port.

---

# AVault

**AVault — Digital AV Equipment Lending & Inventory Management System**
