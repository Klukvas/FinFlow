# Subscription Plans

This document defines the standardized subscription plans for the accounting app.

## Plans Overview

All plans are **monthly subscriptions** (30 days period).

| Plan | Code | Price | Period |
|------|------|-------|--------|
| Basic | `basic` | Free | Forever |
| Professional | `professional` | $9.99 | Monthly |
| Enterprise | `enterprise` | $29.99 | Monthly |

## Feature Limits by Plan

### Basic Plan (Free)
Perfect for individuals starting with personal finance management.

| Feature | Limit |
|---------|-------|
| Categories | 10 |
| Accounts | 2 |
| Expenses | 100/month |
| Incomes | 100/month |
| Debts | 2 |
| Recurring Transactions | 3 |
| Goals | 2 |
| Workspaces | 1 |

**Limitations:**
- Limited analytics
- No data export
- Basic support

---

### Professional Plan ($9.99/month)
For individuals and families serious about financial management.

| Feature | Limit |
|---------|-------|
| Categories | 50 |
| Accounts | 10 |
| Expenses | 5,000/month |
| Incomes | 5,000/month |
| Debts | 20 |
| Recurring Transactions | 50 |
| Goals | 20 |
| Workspaces | 3 |

**Additional Features:**
- Advanced analytics
- Export to Excel/PDF
- Priority support
- Payment reminders

**No Limitations**

---

### Enterprise Plan ($29.99/month)
For teams and small businesses requiring unlimited resources.

| Feature | Limit |
|---------|-------|
| Categories | Unlimited (NULL) |
| Accounts | Unlimited (NULL) |
| Expenses | Unlimited (NULL) |
| Incomes | Unlimited (NULL) |
| Debts | Unlimited (NULL) |
| Recurring Transactions | Unlimited (NULL) |
| Goals | Unlimited (NULL) |
| Workspaces | 10 |

**Additional Features:**
- All Professional features
- API access
- Bank integrations
- Dedicated support manager
- Custom reports
- SLA 99.9%
- Priority feature requests

**No Limitations**

---

## Implementation Notes

### Database
- Plans are defined in the `plans` table
- Feature limits are defined in the `plan_features` table
- Each plan has a `period_days` of 30 (monthly)
- NULL limit_value means unlimited

### Migration
The standardized plans are created via migration `0006_standardize_plans.py` which:
1. Creates/updates the 3 standard plans
2. Removes any deprecated plans (e.g., `pro-monthly`, `pro-yearly`)
3. Migrates existing subscriptions to the new plan codes
4. Sets up feature limits for each plan

### Frontend
Plan codes must match exactly in the frontend i18n files:
- `basic` (not `basic-free`)
- `professional` (not `pro-monthly` or `pro`)
- `enterprise` (not `enterprise-monthly`)

### Upgrading Plans
When a user upgrades from one plan to another:
- Same plan renewal: extends from current `expires_at`
- Different plan: starts fresh from NOW

### Free Trial
The Basic plan is always free and serves as the default plan for new users.
