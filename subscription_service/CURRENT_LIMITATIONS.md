# Subscription Plan Limitations

This document describes the current feature limitations for each subscription plan in the accounting application.

**Last Updated:** 2026-01-31

---

## Overview

The application has **3 subscription plans**:
- **Basic** (Free) - Limited features for personal use
- **Professional** (Paid) - Enhanced limits for individuals and small businesses
- **Enterprise** (Paid) - Unlimited features for large organizations

All plans have **30-day (monthly) billing periods**.

---

## Feature Limits by Plan

| Feature | Basic (Free) | Professional | Enterprise | Limit Type |
|---------|-------------|--------------|------------|------------|
| **Expenses** | 50 | 5,000 | Unlimited | **Monthly** ✨ |
| **Incomes** | 50 | 5,000 | Unlimited | **Monthly** ✨ |
| **PDF Uploads** | 1 | 10 | Unlimited | **Monthly** ✨ |
| **PDF Records Per Upload** | 20 | 100 | Unlimited | Per Upload |
| **Categories** | 10 | 50 | Unlimited | Total |
| **Accounts** | 2 | 10 | Unlimited | Total |
| **Debts** | 2 | 20 | Unlimited | Total |
| **Recurring Transactions** | 3 | 50 | Unlimited | Total |
| **Goals** | 2 | 20 | Unlimited | Total |
| **Workspaces** | 1 | 3 | 10 | Total |

---

## Limit Types Explained

### Monthly Limits ✨
- **Resets on the 1st of each month** (UTC timezone)
- Count is based on creation date (`created_at` field)
- **Deleting items frees up quota** for the current month
- Examples: Expenses, Incomes

**Example:**
```
January: User creates 50 expenses → reaches limit
February 1st: Limit resets → user can create 50 more expenses
If user deletes 10 expenses in February → can create 10 more
```

### Total Limits
- **Cumulative across all time**
- Never resets
- Deleting items frees up quota permanently
- Examples: Categories, Accounts, Debts, Goals, Recurring, Workspaces

**Example:**
```
User creates 10 categories (Basic plan limit) → reaches limit
Must delete existing category to create a new one
```

---

## Implementation Details

### Monthly Limit Logic

Monthly limits are calculated using the current calendar month in UTC:

```python
current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
current_count = db.query(Model).filter(
    Model.user_id == user_id,
    Model.created_at >= current_month_start
).count()
```

**Key points:**
- Uses UTC timezone for consistency across all users
- Calendar month (not rolling 30-day window)
- Based on `created_at` timestamp
- Automatically resets when month changes

### Database Indexes

For performance, the following indexes exist for monthly limit checks:

```sql
-- Expenses
CREATE INDEX idx_expenses_user_created ON expenses(user_id, created_at);

-- Incomes
CREATE INDEX idx_incomes_user_created ON incomes(user_id, created_at);
```

---

## Feature Codes

The following feature codes are used in the system:

| Code | Name | Description |
|------|------|-------------|
| `expenses` | Expenses | Number of expense records user can create per month |
| `incomes` | Incomes | Number of income records user can create per month |
| `pdf_uploads_per_month` | PDF Uploads Per Month | Number of PDF files user can upload per calendar month |
| `pdf_records_per_upload` | PDF Records Per Upload | Maximum number of records per single PDF upload |
| `categories` | Categories | Number of categories user can create (total) |
| `accounts` | Accounts | Number of accounts user can create (total) |
| `debts` | Debts | Number of debts user can track (total) |
| `recurring` | Recurring Transactions | Number of recurring transactions user can create (total) |
| `goals` | Goals | Number of financial goals user can create (total) |
| `workspaces` | Workspaces | Number of workspaces user can create (total) |

---

## Migration History

### Recent Changes

**2026-01-31**: Implemented monthly limits for expenses and incomes
- Changed from total limits to monthly limits
- Reduced Basic plan from 100 to 50 (but now resets monthly)
- Added `created_at` and `updated_at` timestamp fields to expense/income tables
- Added database indexes for performance optimization

**Migrations:**
- `expense_service/alembic/versions/010_add_monthly_limit_index.py` - Added timestamp columns and index
- `income_service/alembic/versions/006_add_monthly_limit_index.py` - Added index (timestamps already existed)
- `subscription_service/alembic/versions/0009_update_monthly_limits.py` - Updated limit values in database

---

## Service Implementations

### Expense Service
- **File:** `expense_service/app/services/expense.py:168-179`
- **Check:** Counts expenses created in current month
- **Error:** `ExpenseLimitExceededError` when limit reached

### Income Service
- **File:** `income_service/app/services/income.py:80-86`
- **Check:** Counts incomes created in current month
- **Error:** `IncomeLimitExceededError` when limit reached

### PDF Parser Service
- **File:** `pdf_parser_service/app/routers/pdf_parser.py`
- **Check:** Two-stage validation for PDF uploads
- **Errors:**
  - `PDFUploadLimitExceededError` (HTTP 429) when monthly upload limit exceeded
  - `PDFRecordsLimitExceededError` (HTTP 422) when PDF contains too many records

#### Two-Stage Validation Logic

The PDF parser implements a sophisticated two-stage validation to ensure users stay within both their monthly transaction quotas AND PDF-specific limits:

**Stage 1: Per-Type Monthly Quota Check**
- Validates against existing expense/income monthly limits
- Checked in frontend before allowing user to proceed
- Example scenario:

```
User Status:
- Plan: Basic (50 expenses/month, 50 incomes/month)
- Current month: 30 expenses, 40 incomes
- Remaining: 20 expenses, 10 incomes

PDF Upload:
- Contains: 50 expenses + 50 incomes

Stage 1 Validation:
✅ Expenses: User selects 50, but only 20 allowed → reduce to ≤20
✅ Incomes: User selects 50, but only 10 allowed → reduce to ≤10
→ User must deselect records to: 20 expenses + 10 incomes = 30 total
```

**Stage 2: Total Records Per Upload Check**
- Validates against plan's max records per upload limit
- Checked after Stage 1 passes
- Continuing the example above:

```
After Stage 1:
- User has: 20 expenses + 10 incomes = 30 total selected

Stage 2 Validation (Basic Plan):
❌ Total: 30 records > 20 (max per upload for Basic)
→ User must deselect 10 MORE records (any type)
→ Final: Any combination totaling ≤20 (e.g., 15 expenses + 5 incomes)

After Stage 2:
✅ Total: 20 records ≤ 20 (limit satisfied)
✅ User can proceed with import
```

**Implementation Flow:**

1. **Upload Attempt** → Check monthly upload count (pdf_uploads_per_month)
2. **Parse PDF** → Extract all transactions
3. **Records Validation** → Check total count (pdf_records_per_upload)
4. **Frontend Display** → Show all parsed transactions with validation warnings
5. **User Selection** → User deselects records to meet both stages
6. **Import** → Create only selected/valid transactions

**Database Tracking:**
- Table: `pdf_uploads` (in pdf_parser_service database)
- Tracks: upload attempts, success/failure, record counts
- Index: `(user_id, created_at)` for efficient monthly counting
- Monthly reset: Automatic (based on calendar month in UTC)

---

### Two-Stage Validation Examples

#### Example 1: Basic Plan - Both Stages Required

**User Status:**
```
Plan: Basic
Monthly Limits: 50 expenses, 50 incomes
Current Usage: 30 expenses, 40 incomes
Remaining: 20 expenses, 10 incomes
```

**PDF Content:**
```
50 expense transactions
50 income transactions
Total: 100 transactions
```

**Validation Process:**

**Stage 1 - Per-Type Quota:**
```
Selected: 50 expenses, 50 incomes

Check Expenses:
  50 (selected) > 20 (remaining) ❌
  → Must reduce to ≤20 expenses

Check Incomes:
  50 (selected) > 10 (remaining) ❌
  → Must reduce to ≤10 incomes

User Action: Deselect to 20 expenses + 10 incomes
Result: 30 total transactions selected
```

**Stage 2 - Upload Limit:**
```
Selected: 20 expenses + 10 incomes = 30 total
Plan Limit: 20 records per upload (Basic)

Check Total:
  30 (selected) > 20 (limit) ❌
  → Must reduce by 10 more records

User Action: Deselect 10 more (any type)
Final Selection: 15 expenses + 5 incomes = 20 total ✅

Result: User can proceed with import
```

---

#### Example 2: Basic Plan - Only Stage 2 Required

**User Status:**
```
Plan: Basic
Monthly Limits: 50 expenses, 50 incomes
Current Usage: 10 expenses, 5 incomes
Remaining: 40 expenses, 45 incomes
```

**PDF Content:**
```
15 expense transactions
10 income transactions
Total: 25 transactions
```

**Validation Process:**

**Stage 1 - Per-Type Quota:**
```
Selected: 15 expenses, 10 incomes

Check Expenses:
  15 (selected) ≤ 40 (remaining) ✅

Check Incomes:
  10 (selected) ≤ 45 (remaining) ✅

Result: Stage 1 passed
```

**Stage 2 - Upload Limit:**
```
Selected: 15 expenses + 10 incomes = 25 total
Plan Limit: 20 records per upload (Basic)

Check Total:
  25 (selected) > 20 (limit) ❌
  → Must reduce by 5 records

User Action: Deselect 5 records (any type)
Final Selection: 12 expenses + 8 incomes = 20 total ✅

Result: User can proceed with import
```

---

#### Example 3: Professional Plan - Both Stages Pass

**User Status:**
```
Plan: Professional
Monthly Limits: 5,000 expenses, 5,000 incomes
Current Usage: 1,200 expenses, 800 incomes
Remaining: 3,800 expenses, 4,200 incomes
```

**PDF Content:**
```
60 expense transactions
40 income transactions
Total: 100 transactions
```

**Validation Process:**

**Stage 1 - Per-Type Quota:**
```
Selected: 60 expenses, 40 incomes

Check Expenses:
  60 (selected) ≤ 3,800 (remaining) ✅

Check Incomes:
  40 (selected) ≤ 4,200 (remaining) ✅

Result: Stage 1 passed
```

**Stage 2 - Upload Limit:**
```
Selected: 60 expenses + 40 incomes = 100 total
Plan Limit: 100 records per upload (Professional)

Check Total:
  100 (selected) ≤ 100 (limit) ✅

Result: User can proceed with import immediately!
```

---

#### Example 4: Professional Plan - Approaching Monthly Limit

**User Status:**
```
Plan: Professional
Monthly Limits: 5,000 expenses, 5,000 incomes
Current Usage: 4,990 expenses, 4,980 incomes
Remaining: 10 expenses, 20 incomes
```

**PDF Content:**
```
50 expense transactions
50 income transactions
Total: 100 transactions
```

**Validation Process:**

**Stage 1 - Per-Type Quota:**
```
Selected: 50 expenses, 50 incomes

Check Expenses:
  50 (selected) > 10 (remaining) ❌
  → Must reduce to ≤10 expenses

Check Incomes:
  50 (selected) > 20 (remaining) ❌
  → Must reduce to ≤20 incomes

User Action: Deselect to 10 expenses + 20 incomes
Result: 30 total transactions selected
```

**Stage 2 - Upload Limit:**
```
Selected: 10 expenses + 20 incomes = 30 total
Plan Limit: 100 records per upload (Professional)

Check Total:
  30 (selected) ≤ 100 (limit) ✅

Result: User can proceed with import
```

**Note:** Even with Professional plan's high upload limit (100), the monthly quota restrictions from Stage 1 still apply.

---

#### Example 5: Enterprise Plan - No Limits

**User Status:**
```
Plan: Enterprise
Monthly Limits: Unlimited expenses, Unlimited incomes
Current Usage: 10,000 expenses, 8,000 incomes
Remaining: Unlimited
```

**PDF Content:**
```
200 expense transactions
150 income transactions
Total: 350 transactions
```

**Validation Process:**

**Stage 1 - Per-Type Quota:**
```
Selected: 200 expenses, 150 incomes

Check Expenses:
  Unlimited ✅

Check Incomes:
  Unlimited ✅

Result: Stage 1 passed
```

**Stage 2 - Upload Limit:**
```
Selected: 200 expenses + 150 incomes = 350 total
Plan Limit: Unlimited (Enterprise)

Check Total:
  Unlimited ✅

Result: User can proceed with import immediately!
```

---

#### Example 6: Edge Case - Exact Limit Match

**User Status:**
```
Plan: Basic
Monthly Limits: 50 expenses, 50 incomes
Current Usage: 30 expenses, 40 incomes
Remaining: 20 expenses, 10 incomes
```

**PDF Content:**
```
15 expense transactions
5 income transactions
Total: 20 transactions
```

**Validation Process:**

**Stage 1 - Per-Type Quota:**
```
Selected: 15 expenses, 5 incomes

Check Expenses:
  15 (selected) ≤ 20 (remaining) ✅

Check Incomes:
  5 (selected) ≤ 10 (remaining) ✅

Result: Stage 1 passed
```

**Stage 2 - Upload Limit:**
```
Selected: 15 expenses + 5 incomes = 20 total
Plan Limit: 20 records per upload (Basic)

Check Total:
  20 (selected) ≤ 20 (limit) ✅

Result: Perfect match! User can proceed with import
```

---

### Summary of Validation Rules

| Stage | Check | Applies To | Error Type |
|-------|-------|------------|------------|
| **Stage 1** | Per-type monthly quota | Expenses and Incomes separately | Must reduce selected records per type |
| **Stage 2** | Total records per upload | All selected records combined | Must reduce total selection |

**Key Points:**
- Both stages must pass for import to succeed
- Stage 1 checked first (per-type quotas)
- Stage 2 checked after Stage 1 passes (total limit)
- Enterprise plan bypasses both stages (unlimited)
- Frontend validates in real-time and disables "Import" button until both stages pass

### Other Services
All other services (categories, accounts, debts, goals, recurring, workspaces) use total count checks without date filtering.

---

## Future Considerations

### Timezone Support
Currently using UTC for all monthly limit calculations. Future enhancement could:
- Store user's timezone preference
- Calculate month boundaries based on user's local timezone
- Provide more intuitive reset times

### Usage Analytics
Potential features to add:
- Show users their current usage vs. limits
- Send notifications when approaching limits
- Display usage history and trends
- Add dashboard with limit visualization

### Alternative Limit Models
Possible alternative approaches:
- **Rolling 30-day window**: Count last 30 days instead of calendar month
- **Usage tracking table**: Separate table to track monthly usage (faster queries)
- **Quota carry-over**: Allow unused quota to roll to next month
- **Soft limits**: Warnings before hard limits kick in

---

## Testing

To test monthly limits:

```bash
# Run the verification script
python test_monthly_limits.py

# Manually test in container
docker-compose exec expense_service bash
python -c "from datetime import datetime; print(datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0))"
```

---

## References

### Subscription Service
- Plan definitions: `subscription_service/alembic/versions/0006_standardize_plans.py`
- PDF features: `subscription_service/alembic/versions/0010_add_pdf_features.py`
- Feature definitions: `subscription_service/alembic/versions/0003_seed_features.py`
- Subscription models: `subscription_service/app/models/models.py`
- Entitlements service: `subscription_service/app/services/entitlements.py`

### PDF Parser Service
- Router with validation: `pdf_parser_service/app/routers/pdf_parser.py`
- Upload tracking model: `pdf_parser_service/app/models/pdf_upload.py`
- Subscription client: `pdf_parser_service/app/clients/subscription_client.py`
- Upload repository: `pdf_parser_service/app/repositories/pdf_upload_repository.py`
- Database migration: `pdf_parser_service/alembic/versions/001_create_pdf_uploads.py`

### Expense/Income Services
- Expense service: `expense_service/app/services/expense.py`
- Income service: `income_service/app/services/income.py`
- Current month count endpoints:
  - `expense_service/app/routers/expense.py` (GET /current-month-count)
  - `income_service/app/routers/income.py` (GET /current-month-count)
