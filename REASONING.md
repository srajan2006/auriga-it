# AVault — Solution Reasoning

## 1. Purpose

AVault was designed to solve the operational problems associated with managing college AV-room equipment through a paper register or disconnected manual processes.

The primary problems are:

* Difficulty knowing which equipment is available.
* Risk of double-booking the same physical equipment.
* Manual approval processes.
* Lack of centralized borrowing history.
* Difficulty tracking issued equipment.
* Difficulty identifying overdue equipment.
* Manual late-fee calculation.
* Poor visibility into equipment condition.
* Lack of accountability when equipment changes hands.

The system therefore treats equipment lending as a stateful workflow rather than simply a CRUD application.

---

# 2. Why Separate Equipment Models and Physical Units?

A major design decision is separating an equipment **model/type** from an individual **physical unit**.

For example:

```text
Equipment Model:
Canon EOS 1500D

Physical Units:
Canon EOS 1500D — Unit 1
Canon EOS 1500D — Unit 2
Canon EOS 1500D — Unit 3
```

This distinction is necessary because the system needs to know exactly which physical item is booked or issued.

If only an equipment model were stored, the system could know that three cameras exist but could not reliably track:

* Which camera was issued.
* Which camera is damaged.
* Which camera is currently overdue.
* Which exact camera was returned.

Therefore:

```text
EquipmentModel
       ↓
EquipmentUnit
       ↓
Booking / Loan
```

---

# 3. Why PostgreSQL?

PostgreSQL was selected because AVault contains strongly related transactional data.

Important relationships include:

```text
User
 ↓
Booking
 ↓
BookingItem
 ↓
BookingUnit
 ↓
EquipmentUnit

User
 ↓
Loan
 ↓
LoanItem
 ↓
EquipmentUnit

Loan
 ↓
LateFee

Loan
 ↓
LoanTransfer
```

The application also needs transactional integrity for operations such as:

* Approving bookings.
* Issuing equipment.
* Returning equipment.
* Transferring loans.

A relational database fits these requirements naturally.

---

# 4. Why Django?

Django provides:

* ORM
* Authentication infrastructure
* Database migrations
* Admin capabilities
* Request handling
* Strong project structure

The application contains substantial business logic around equipment states and loan states.

Django provides a clear backend foundation for implementing these rules centrally.

---

# 5. Why Django REST Framework?

The frontend and backend are intentionally separated.

The frontend communicates with Django through REST APIs.

Conceptually:

```text
Next.js
   ↓
HTTP / REST
   ↓
Django REST Framework
   ↓
Django Services / Models
   ↓
PostgreSQL
```

This separation makes it possible to develop the frontend and backend independently.

It also means that critical business rules remain on the server instead of being dependent on frontend behavior.

---

# 6. Why Next.js?

Next.js provides a structured React-based frontend suitable for a multi-page application.

AVault requires different interfaces for:

```text
Student
Staff
Admin
```

For example:

```text
/student/dashboard
/staff/dashboard
/admin/dashboard
```

Next.js routing provides a straightforward way to organize these interfaces.

TypeScript is used to reduce errors caused by inconsistent data structures between UI components and API responses.

---

# 7. Why JWT Authentication?

The application is API-driven, so authentication needs to work cleanly between the Next.js frontend and Django REST API.

JWT provides:

```text
Login
 ↓
Access Token
 ↓
API Requests
 ↓
Backend Authentication
```

The backend can then determine:

```text
Who is the user?
What is the user's role?
Is the user allowed to perform this operation?
```

Authorization is enforced on the backend rather than relying solely on frontend route protection.

---

# 8. Role-Based Access Control

AVault uses three primary roles:

```text
STUDENT
STAFF
ADMIN
```

The roles represent different operational responsibilities.

### Student

Primarily interacts with:

```text
Equipment
Availability
Bookings
Loans
History
Fees
```

### Staff

Primarily interacts with:

```text
Bookings
Inventory
Issue
Return
Overdue
Loan Transfer
```

### Admin

Primarily interacts with:

```text
Users
System Settings
Inventory
Operational Management
```

This separation reduces the possibility of unauthorized operational actions.

---

# 9. Equipment State Design

A physical equipment unit has a current operational state.

The states are:

```text
AVAILABLE
RESERVED
ISSUED
OVERDUE
MAINTENANCE
DAMAGED
LOST
```

These states describe the lifecycle of the physical equipment.

A simplified lifecycle is:

```text
AVAILABLE
    ↓
RESERVED
    ↓
ISSUED
    ↓
RETURNED
    ↓
AVAILABLE
```

If the equipment is returned with a problem:

```text
ISSUED
   ↓
RETURN
   ↓
DAMAGED / MAINTENANCE
```

If a loan passes its due date:

```text
ISSUED
   ↓
OVERDUE
```

The state is important because availability should reflect the physical reality of the equipment.

---

# 10. Booking State Design

Bookings have their own lifecycle:

```text
PENDING
   ↓
APPROVED
   ↓
COMPLETED
```

Alternative paths include:

```text
PENDING → REJECTED
PENDING → CANCELLED
APPROVED → CANCELLED
```

A booking is different from a loan.

A booking represents a **request/reservation**.

A loan represents equipment that has actually been **issued to a borrower**.

This distinction is important because approving a booking does not necessarily mean the equipment has physically been handed over.

---

# 11. Loan State Design

Loans represent actual equipment possession.

The states are:

```text
ACTIVE
OVERDUE
RETURNED
LOST
```

Normal flow:

```text
ACTIVE
  ↓
RETURNED
```

Overdue flow:

```text
ACTIVE
  ↓
OVERDUE
  ↓
RETURNED
```

Lost equipment can transition to:

```text
LOST
```

Loan state and equipment state are related but are not identical concepts.

---

# 12. Availability and Double-Booking Prevention

The system must prevent two users from being assigned the same physical equipment for overlapping periods.

The overlap condition is:

```text
requested_start < existing_end
AND
requested_end > existing_start
```

This correctly identifies overlapping intervals.

For example:

```text
Existing:
10:00 ───────── 12:00

Requested:
11:00 ───────── 13:00
```

These overlap.

But:

```text
Existing:
10:00 ───────── 12:00

Requested:
12:00 ───────── 14:00
```

does not overlap if the application treats the end time as exclusive.

The backend must perform this validation because frontend-only validation can be bypassed.

---

# 13. Why Physical Units Are Assigned at the Correct Stage

The system distinguishes between requesting equipment and assigning a physical unit.

A booking may request:

```text
Canon EOS 1500D
Quantity: 1
```

The actual physical unit can then be selected/allocated according to the application's workflow.

This prevents the equipment model itself from being treated as one physical object.

The loan ultimately references the actual:

```text
EquipmentUnit
```

that was issued.

---

# 14. Borrowing Limits

Borrowing limits are configurable instead of hard-coded.

Examples:

```text
max_active_loans_per_user
max_units_per_booking
default_late_fee_per_day
```

This allows the institution to change operational policy without changing application logic.

Before creating or transferring a loan, the backend should calculate the destination user's current active loans and verify that the limit will not be exceeded.

---

# 15. Late-Fee Reasoning

Late fees should be deterministic.

The calculation is:

```text
late_days = current_date - due_date
```

with negative values treated as zero.

Then:

```text
late_fee = late_days × late_fee_per_day
```

This means:

```text
Returned before/on due date
→ 0 late days
→ 0 late fee
```

and:

```text
Returned 3 days late
→ 3 × configured daily fee
```

The configured rate is stored in system settings rather than embedded directly into application code.

---

# 16. Return Processing

Returning equipment is more than changing a loan status.

The application needs to determine the condition of the physical unit.

Conceptually:

```text
Return
  ↓
Condition Inspection
  ↓
┌───────────────┬────────────────┬──────────────┐
│ Good          │ Damaged        │ Maintenance  │
↓               ↓                ↓
AVAILABLE       DAMAGED          MAINTENANCE
```

This ensures that an item requiring repair is not immediately shown as available.

---

# 17. Active Loan Transfer

The active-loan transfer requirement introduces an important distinction.

A transfer is:

```text
Change current borrower
```

It is **not**:

```text
Return + New Booking + New Loan
```

This distinction prevents several problems.

If the application implemented transfer as a return followed by a new issue, it could accidentally:

* Release the equipment.
* Change the due date.
* Create a second loan.
* Create a new booking.
* Reset overdue status.
* Break the equipment availability state.
* Lose the original loan history.

Therefore the transfer operates on the existing loan.

---

# 18. Transfer Invariants

The following values must remain unchanged during a transfer:

```text
Loan ID
Equipment Unit
Issued At
Due At
Loan Status
Equipment Availability/Operational State
```

Only the current borrower changes.

Example:

```text
Before:

Loan #100
Borrower: Rahul
Equipment: Camera Unit 2
Issued: 15 Sep
Due: 20 Sep
Status: ACTIVE
```

After:

```text
Loan #100
Borrower: Aman
Equipment: Camera Unit 2
Issued: 15 Sep
Due: 20 Sep
Status: ACTIVE
```

This is why transfer is modeled as a mutation of the borrower relationship rather than creation of a new loan.

---

# 19. Why Transfer History Is Necessary

Simply overwriting:

```text
borrower = Aman
```

would destroy information about the previous borrower.

For accountability, the application maintains transfer history.

Conceptually:

```text
LoanTransfer
----------------------------
loan
previous_borrower
new_borrower
transferred_by
reason
transferred_at
```

This allows a chain such as:

```text
Rahul → Aman → Priya
```

while preserving the complete history.

The current loan still has only one current borrower.

---

# 20. Transfer Eligibility

A transfer should only be allowed when:

```text
Current loan status = ACTIVE or OVERDUE
```

The destination borrower should:

```text
be an active user
AND
have STUDENT role
AND
satisfy borrowing limits
```

Transfers to inactive users or unauthorized roles should be rejected.

Returned or lost loans cannot be transferred.

---

# 21. Why Transfers Preserve Overdue Status

Suppose:

```text
Due date: 10 September
Current date: 15 September
```

The loan is already overdue.

If the loan is transferred on 15 September:

```text
Old borrower → New borrower
```

the due date must remain:

```text
10 September
```

The transfer must not reset the clock.

Otherwise a borrower could effectively avoid overdue rules by transferring the equipment.

Therefore:

```text
OVERDUE
  +
TRANSFER
  =
OVERDUE
```

and the original due date remains the basis for late-fee calculation.

---

# 22. Atomic Transfer

The transfer should execute inside a database transaction.

Conceptually:

```text
BEGIN TRANSACTION

Validate current loan
Validate destination borrower
Validate borrowing limit
Update current borrower
Create transfer-history record

COMMIT
```

If any operation fails:

```text
ROLLBACK
```

This prevents partially completed transfers.

For example, the system should never reach a state where:

```text
Loan borrower changed
BUT
Transfer history was not recorded
```

---

# 23. Why Critical Rules Belong in the Backend

A frontend can be modified or bypassed.

A malicious or incorrectly implemented client could send an API request directly.

Therefore the backend must independently validate:

```text
Role
Authentication
Booking conflicts
Borrowing limits
Loan states
Equipment states
Transfer eligibility
Late fees
Return rules
```

The frontend should provide user-friendly validation, but the backend remains the authoritative enforcement layer.

---

# 24. Separation of Booking and Loan

The design intentionally separates:

```text
Booking
```

from:

```text
Loan
```

because they represent different business concepts.

### Booking

Represents planned/requested equipment usage.

### Loan

Represents physical possession of equipment.

This allows the system to model:

```text
Request
   ↓
Approval
   ↓
Issue
   ↓
Loan
   ↓
Return
```

without incorrectly treating a reservation as possession.

---

# 25. API Design

The API is organized around business resources.

Examples:

```text
/api/auth/
/api/categories/
/api/equipment/
/api/bookings/
/api/loans/
/api/late-fees/
/api/users/
/api/settings/
```

Operations that represent business actions use explicit endpoints.

Examples:

```text
POST /api/bookings/{id}/approve/
POST /api/bookings/{id}/reject/

POST /api/loans/{id}/issue/
POST /api/loans/{id}/return/
POST /api/loans/{id}/transfer/
```

This makes business operations explicit instead of relying entirely on generic CRUD operations.

---

# 26. Service-Layer Reasoning

Simple CRUD operations can remain close to serializers/viewsets.

Complex operations should use dedicated service/helper logic.

Examples:

```text
approve_booking()
issue_loan()
return_loan()
transfer_loan()
calculate_late_fee()
check_equipment_availability()
```

This keeps business rules centralized and makes them easier to test.

---

# 27. Testing Strategy

The most important tests are not only UI tests.

The backend should test business rules directly.

Examples:

### Booking

```text
Non-overlapping bookings succeed.
Overlapping bookings fail.
Unauthorized approval fails.
```

### Loan

```text
Approved booking can be issued.
Unauthorized issue fails.
```

### Return

```text
Normal return makes equipment available.
Damaged return makes equipment damaged.
```

### Late Fees

```text
On-time return produces no late fee.
Late return produces correct fee.
```

### Transfer

```text
Active loan can transfer.
Overdue loan can transfer.
Returned loan cannot transfer.
Lost loan cannot transfer.
Unauthorized user cannot transfer.
Inactive destination cannot receive transfer.
Borrowing-limit violation fails.
Due date remains unchanged.
Loan ID remains unchanged.
Equipment unit remains unchanged.
Equipment availability remains unchanged.
Transfer history is recorded.
Multiple transfers are supported.
```

These tests directly protect the application's business invariants.

---

# 28. Why the Architecture Avoids Unnecessary Complexity

The initial AVault implementation deliberately avoids technologies that are not required for the MVP.

The core architecture is:

```text
Next.js
    ↓
Django REST Framework
    ↓
PostgreSQL
```

The project does not require a distributed architecture to solve its initial problem.

Technologies such as Redis, Celery, message queues, payment gateways, cloud storage, and vector databases can be introduced later when there is a concrete requirement.

This keeps the initial system easier to understand, debug, test, and deploy.

---

# 29. Security Reasoning

Security is primarily enforced at the backend.

Important controls include:

```text
Authentication
Authorization
Role-based permissions
Input validation
Database constraints
Transaction handling
Secret management
```

Passwords should never be stored directly.

Sensitive configuration should be stored in environment variables.

The frontend should never be trusted to enforce authorization by itself.

---

# 30. Development vs Production

The PostgreSQL instance inside a GitHub Codespace is intended for development.

A Codespace can be deleted, recreated, or changed.

Therefore the development database should not be considered permanent production storage.

A production deployment should use persistent infrastructure, such as a managed PostgreSQL database.

The application architecture is kept sufficiently separated that the database connection can later be changed without redesigning the entire application.

---

# 31. Overall Design

The resulting architecture can be summarized as:

```text
                    AVault
                      │
          ┌───────────┴───────────┐
          │                       │
       Student                  Staff/Admin
          │                       │
          └───────────┬───────────┘
                      │
                Next.js Frontend
                      │
                   REST API
                      │
              Django + DRF
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    Booking         Loan         Inventory
       │              │              │
       │        ┌─────┴─────┐        │
       │        │           │        │
    Transfer  Returns   Late Fees    │
       │        │           │        │
       └────────┴───────────┴────────┘
                      │
                  PostgreSQL
```

The central design principle is that **the database and backend represent the authoritative state of the lending system**.

The frontend is responsible for presenting that state and providing an efficient user experience.

---

# 32. Final Design Principles

AVault follows these principles:

1. **Track physical equipment, not just equipment types.**
2. **Separate reservations from actual loans.**
3. **Prevent double booking at the backend.**
4. **Treat equipment and loan states explicitly.**
5. **Keep business rules on the server.**
6. **Use database transactions for critical multi-step operations.**
7. **Preserve historical information instead of overwriting it.**
8. **Never reset a loan's due date during a transfer.**
9. **Never release equipment during a borrower transfer.**
10. **Make borrowing limits configurable.**
11. **Calculate late fees deterministically.**
12. **Use role-based authorization.**
13. **Keep the MVP architecture simple enough to maintain.**
14. **Design the system so future features can be added without rewriting the core lending workflow.**

---

# Conclusion

AVault is designed as a transaction-oriented equipment lending system rather than a simple inventory CRUD application.

The most important architectural decision is maintaining a clear distinction between:

```text
Equipment Model
Equipment Unit
Booking
Loan
Current Borrower
Transfer History
Return
Late Fee
```

This separation allows the application to accurately represent the physical lifecycle of AV equipment while maintaining accountability and preventing inconsistent states.

The active-loan transfer capability follows the same principle: transferring responsibility changes the borrower associated with an existing loan while preserving the loan's identity, equipment, due date, and operational state.

The result is a simple but extensible foundation for a college AV-room equipment management platform.

