# Accounting Application - System Architecture Document

**Version:** 1.0  
**Generated:** February 2026  
**Author:** System Analysis

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Microservices Map](#2-microservices-map)
3. [Microservice Deep Dive](#3-microservice-deep-dive)
4. [Inter-Service Communication](#4-inter-service-communication)
5. [Core User Flows](#5-core-user-flows-system-wide)
6. [Business Rules & Cross-Service Invariants](#6-business-rules--cross-service-invariants)
7. [Risks & Observations](#7-risks--observations)
8. [Summary & System Health Assessment](#8-summary--system-health-assessment)

---

# 1. System Overview

## What Business Problem the System Solves

This is a **personal finance management platform** that enables users to:
- Track expenses and income across multiple financial accounts
- Organize transactions with hierarchical categories
- Manage multiple currencies with real-time conversion
- Set and track financial goals and milestones
- Monitor and pay off debts (loans, credit cards, mortgages)
- Automate recurring transactions (expenses and income)
- Import bank statements from PDF files (currently Monobank)
- Collaborate with others through shared workspaces

## Who the End Users Are

1. **Individual Users** - Personal finance tracking, budgeting, goal setting
2. **Families/Small Groups** - Shared household finances via workspaces
3. **Small Businesses** - Basic expense/income tracking with team access
4. **Administrators** - User management, subscription oversight

## High-Level Architecture Style

- **Microservices Architecture**: 15 independent backend services
- **Synchronous Communication**: HTTP/REST APIs for real-time operations
- **Asynchronous Processing**: Background schedulers for recurring tasks
- **Event-Driven** (limited): Redis pub/sub for subscription change notifications
- **Database-per-Service**: Each service owns its PostgreSQL database
- **Shared Infrastructure**: Single PostgreSQL instance, Redis for caching

### Technology Stack

| Layer | Technology |
|-------|------------|
| Backend Services | Python 3.11+, FastAPI, SQLAlchemy |
| Databases | PostgreSQL 15 (13 databases) |
| Cache/Pub-Sub | Redis 7 |
| Frontend | React, TypeScript, Vite |
| Admin Panel | React, TypeScript, Tailwind CSS |
| Observability | Grafana, Loki, Promtail |
| Containerization | Docker, Docker Compose |
| Infrastructure | Terraform (Hetzner) |

## Key Non-Functional Assumptions

| Aspect | Approach |
|--------|----------|
| **Scalability** | Horizontal scaling of individual services; single DB instance limits scale |
| **Consistency** | Strong consistency within service boundaries; eventual consistency across services |
| **Availability** | No built-in HA; graceful degradation on external service failures |
| **Security** | JWT authentication, internal service tokens, workspace-based authorization |
| **Multi-tenancy** | Workspace-based isolation; users can belong to multiple workspaces |

---

# 2. Microservices Map

## Service Catalog

| # | Service | Port | Database | Core Responsibility |
|---|---------|------|----------|---------------------|
| 1 | **user_service** | 8001 | user_db | Authentication, user management, admin functions |
| 2 | **workspace_service** | 8012 | workspace_db | Workspaces, members, invitations, authorization |
| 3 | **category_service** | 8002 | category_db | Expense/income categories, MCC codes |
| 4 | **account_service** | 8009 | account_db | Financial accounts, balances |
| 5 | **expense_service** | 8003 | expense_db | Expense transactions |
| 6 | **income_service** | 8004 | income_db | Income transactions |
| 7 | **currency_service** | 8010 | - | Currency conversion, exchange rates |
| 8 | **debt_service** | 8008 | debt_db | Debt tracking, payments |
| 9 | **goals_service** | 8006 | goals_db | Financial goals, milestones |
| 10 | **recurring_service** | 8005 | recurring_db | Recurring payments automation |
| 11 | **subscription_service** | 8011 | subscription_db | Plans, features, entitlements |
| 12 | **payment_service** | 8013 | payment_db | Payment processing (Paddle Billing) |
| 13 | **scheduler_service** | 8014 | scheduler_db | Scheduled jobs (subscription renewal) |
| 14 | **pdf_parser_service** | 8007 | pdf_parser_db | Bank statement parsing |
| 15 | **admin_panel** | - | - | Administrative UI |
| 16 | **frontend** | 3000 | - | End-user web application |

## Service Summary

### Core Domain Services
- **user_service**: Identity and access management foundation
- **workspace_service**: Multi-tenant workspace management and authorization
- **account_service**: Financial accounts (cash, bank, crypto, investment)
- **expense_service**: Expense transaction management
- **income_service**: Income transaction management
- **category_service**: Hierarchical categorization with MCC support

### Supporting Domain Services
- **currency_service**: Real-time currency conversion
- **debt_service**: Debt tracking and repayment
- **goals_service**: Financial goal setting and tracking
- **recurring_service**: Recurring payment automation

### Platform Services
- **subscription_service**: SaaS subscription management
- **payment_service**: Payment gateway integration
- **scheduler_service**: Background job execution
- **pdf_parser_service**: Bank statement import

---

# 3. Microservice Deep Dive

---

## 3.1 User Service

### 3.1.1 Purpose
**Why this service exists:** Provides authentication, user identity, and account management for the entire platform.

**Business capability:** User lifecycle management, authentication, admin oversight.

**What would break if removed:** All user authentication; no one could log in or register; all service-to-service user lookups would fail.

### 3.1.2 Business Logic

**Core domain concepts:**
- User (email, username, password, role, status)
- JWT tokens (access/refresh)
- Admin vs regular user roles

**Key business rules:**
- Password policy: 8-128 chars, requires uppercase, lowercase, numbers
- Username policy: 3-50 chars, alphanumeric + underscores/hyphens
- Rate limiting: 10 login attempts/minute per email
- Account lockout: 5 failed attempts = 15-minute lockout
- JWT expiry: Access tokens (3 days), Refresh tokens (7 days)

**State transitions:**
- User status: `active` ↔ `disabled` (admin controlled)
- User role: `user` ↔ `admin` (admin controlled, cannot demote self)

### 3.1.3 Owned Data & Models

**Main entity: `users`**
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| email | String | Unique, indexed |
| username | String | Unique, indexed |
| hashed_password | String | Bcrypt hash |
| base_currency | String(3) | Default: "USD" |
| default_workspace_id | UUID | Nullable |
| tutorial_version | Integer | Tutorial completion tracking |
| role | String | "user" or "admin" |
| status | String | "active" or "disabled" |
| created_at | DateTime | |

**Storage:** PostgreSQL (`user_db`)

### 3.1.4 API & Endpoints

**Authentication (`/auth`)**
| Method | Path | Purpose | Critical |
|--------|------|---------|----------|
| POST | `/auth/register` | New user registration | ✅ |
| POST | `/auth/login` | User authentication | ✅ |
| GET | `/auth/me` | Get current user | ✅ |
| PUT | `/auth/me` | Update profile | |
| POST | `/auth/refresh` | Refresh access token | ✅ |
| POST | `/auth/change-password` | Password change | |

**Admin (`/admin`) - Requires admin role**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/admin/users` | List all users (paginated) |
| GET | `/admin/users/{id}` | Get user details |
| PATCH | `/admin/users/{id}/role` | Change user role |
| PATCH | `/admin/users/{id}/status` | Enable/disable user |

**Internal (`/internal`) - Service-to-service**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/internal/users/{id}` | Get user by ID |
| GET | `/internal/users/by-email/{email}` | Get user by email |

### 3.1.5 Dependencies (Outbound)

| Service | Purpose | Critical |
|---------|---------|----------|
| workspace_service | Create personal workspace on registration | Non-blocking |
| subscription_service | Bootstrap basic plan on registration | Non-blocking |
| currency_service | Validate currency codes | Fallback to USD |

### 3.1.6 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| workspace_service | Resolve user details for members |
| debt_service | Get user's base currency |
| goals_service | Get user's base currency |
| All services | Token validation (implicit via JWT) |

### 3.1.7 Failure Impact

- **If down:** Complete authentication failure. No logins, no registrations, no token validation.
- **User flows blocked:** ALL flows requiring authentication
- **Graceful degradation:** None possible - critical service

---

## 3.2 Workspace Service

### 3.2.1 Purpose
**Why this service exists:** Provides multi-tenant isolation and collaboration through workspaces.

**Business capability:** Workspace lifecycle, member management, role-based authorization, invitation system.

**What would break if removed:** Multi-tenancy; users couldn't organize data into workspaces; all authorization checks would fail.

### 3.2.2 Business Logic

**Core domain concepts:**
- Workspace (personal vs shared)
- Member (with role: owner/full/read)
- Invite (pending/accepted/rejected/expired/canceled)

**Key business rules:**
- Personal workspace: Auto-created, cannot be archived, owner cannot leave
- Role hierarchy: owner > full > read
- Ownership transfer: Only owner can transfer; becomes `full` member after
- Invite expiration: 3 days
- One pending invite per (workspace, invitee) pair

**State transitions:**
- Workspace: `active` ↔ `archived` (owner only, not personal)
- Member status: `active` → `left` | `removed`
- Invite: `pending` → `accepted` | `rejected` | `expired` | `canceled`

### 3.2.3 Owned Data & Models

**Main entities:**

`workspaces`
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String(255) | |
| type | String | "personal" or "shared" |
| owner_user_id | Integer | |
| archived_at | DateTime | Soft archive |

`workspace_members`
| Field | Type | Description |
|-------|------|-------------|
| workspace_id | UUID | FK |
| user_id | Integer | |
| role | String | owner/full/read |
| status | String | active/left/removed |

`workspace_invites`
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | |
| workspace_id | UUID | |
| invitee_user_id | Integer | |
| invitee_email | String | |
| role | String | Role on acceptance |
| status | String | pending/accepted/rejected/expired/canceled |
| expires_at | DateTime | |

**Storage:** PostgreSQL (`workspace_db`)

### 3.2.4 API & Endpoints

**Workspaces**
| Method | Path | Purpose | Role Required |
|--------|------|---------|---------------|
| POST | `/workspaces` | Create workspace | User |
| GET | `/workspaces` | List user's workspaces | User |
| GET | `/workspaces/{id}` | Get workspace details | Member |
| PATCH | `/workspaces/{id}` | Update workspace | Owner |
| POST | `/workspaces/{id}:archive` | Archive workspace | Owner |
| POST | `/workspaces/{id}:leave` | Leave workspace | Member (not owner) |

**Members**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/workspaces/{id}/members` | List members |
| PATCH | `/workspaces/{id}/members/{user_id}` | Update member role |
| DELETE | `/workspaces/{id}/members/{user_id}` | Remove member |

**Invites**
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/workspaces/{id}/invites` | Create invite |
| GET | `/me/invites` | Get my pending invites |
| POST | `/me/invites/{id}:accept` | Accept invite |
| POST | `/me/invites/{id}:reject` | Reject invite |

**Internal**
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/internal/workspaces/{id}/authorize` | Check user authorization |
| GET | `/internal/users/{id}/default-workspace` | Get default workspace |
| POST | `/internal/workspaces/personal` | Create personal workspace |

### 3.2.5 Dependencies (Outbound)

| Service | Purpose | Critical |
|---------|---------|----------|
| user_service | Resolve user details, lookup by email | Yes |
| subscription_service | Check workspace creation limits | Yes |

### 3.2.6 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| expense_service | Authorization checks |
| income_service | Authorization checks |
| account_service | Authorization checks |
| category_service | Authorization checks |
| debt_service | Authorization checks |
| goals_service | Authorization checks |
| recurring_service | Authorization checks |
| user_service | Create personal workspace |

### 3.2.7 Failure Impact

- **If down:** All write operations requiring authorization fail; users cannot access workspace-scoped data.
- **User flows blocked:** Creating/viewing expenses, income, accounts, categories, etc.
- **Graceful degradation:** Limited - some services may cache authorization results

---

## 3.3 Category Service

### 3.3.1 Purpose
**Why this service exists:** Provides hierarchical categorization for expenses and income with MCC code support.

**Business capability:** Category management, MCC code mapping, category statistics.

**What would break if removed:** No categorization of transactions; expense/income services would lose category validation.

### 3.3.2 Business Logic

**Core domain concepts:**
- Category (expense vs income type)
- Parent-child hierarchy (max 2 levels)
- MCC codes with translations (EN/RU/UK)

**Key business rules:**
- Category name: 3-100 characters, unique per workspace/type
- Maximum depth: 2 levels (root → child)
- One category per MCC code per user per workspace
- Cannot delete category with children

### 3.3.3 Owned Data & Models

`categories`
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | PK |
| name | String(100) | |
| user_id | Integer | |
| workspace_id | UUID | |
| parent_id | Integer | FK, self-referential |
| type | Enum | EXPENSE or INCOME |
| mcc_code | Integer | FK to mcc_codes |
| created_by | Enum | USER or SYSTEM |

`mcc_codes`
| Field | Type | Description |
|-------|------|-------------|
| mcc_code | Integer | PK (1-9999) |
| name | String | English name |
| is_default | Boolean | Commonly used |

`translations`
| Field | Type | Description |
|-------|------|-------------|
| mcc_code | Integer | PK, FK |
| lang | String(5) | PK (ru, uk, en) |
| text | String | Translated name |

**Storage:** PostgreSQL (`category_db`)

### 3.3.4 API & Endpoints

| Method | Path | Purpose | Critical |
|--------|------|---------|----------|
| POST | `/categories/` | Create category | |
| POST | `/categories/from-mcc` | Create from MCC | |
| POST | `/categories/from-mcc/batch` | Batch create from MCC | |
| GET | `/categories/` | List categories | ✅ |
| GET | `/categories/{id}` | Get category | |
| PUT | `/categories/{id}` | Update category | |
| DELETE | `/categories/{id}` | Delete category | |
| GET | `/mcc/defaults` | Get default MCCs | |
| GET | `/mcc/codes` | Get all MCC codes | |

**Internal endpoints** for expense/income validation.

### 3.3.5 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| workspace_service | Authorization |
| subscription_service | Category limit checks |

### 3.3.6 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| expense_service | Validate category |
| income_service | Validate category |
| recurring_service | Validate category |
| pdf_parser_service | MCC lookup, category check |

### 3.3.7 Failure Impact

- **If down:** Expense/income creation with category fails; PDF parsing fails for category enrichment
- **User flows blocked:** Creating categorized transactions
- **Graceful degradation:** Expenses/incomes can be created without category

---

## 3.4 Account Service

### 3.4.1 Purpose
**Why this service exists:** Manages user financial accounts and tracks balances.

**Business capability:** Account CRUD, balance management, transaction integration.

**What would break if removed:** No account tracking; expense/income services would fail account validation.

### 3.4.2 Business Logic

**Core domain concepts:**
- Account (cash, bank, crypto, investment, credit, savings, checking)
- Balance tracking with currency conversion
- Transaction integration (expenses decrease, income increases)

**Key business rules:**
- Balance range: -999,999,999.99 to 999,999,999.99
- Cannot update archived accounts
- Balance updates handle currency conversion automatically
- Prevents negative balances (insufficient funds check)

### 3.4.3 Owned Data & Models

`accounts`
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | PK |
| name | String(100) | |
| type | Enum | AccountType |
| currency | String(3) | ISO 4217 |
| balance | Float | Current balance |
| owner_id | Integer | |
| workspace_id | UUID | |
| is_active | Boolean | |
| is_archived | Boolean | Soft delete |

**Storage:** PostgreSQL (`account_db`)

### 3.4.4 API & Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/accounts` | Create account |
| GET | `/accounts` | List accounts |
| GET | `/accounts/statistics` | Get stats with conversion |
| GET | `/accounts/{id}` | Get account |
| PUT | `/accounts/{id}` | Update account |
| PATCH | `/accounts/{id}/archive` | Archive account |
| PATCH | `/accounts/{id}/balance` | Update balance |
| GET | `/accounts/{id}/transactions` | Get transactions |

### 3.4.5 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| expense_service | Fetch expenses for account |
| income_service | Fetch incomes for account |
| currency_service | Currency conversion |
| workspace_service | Authorization |
| user_service | Get user's base currency |
| subscription_service | Account limit checks |

### 3.4.6 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| expense_service | Validate account, update balance |
| income_service | Validate account, update balance |

### 3.4.7 Failure Impact

- **If down:** Cannot create expenses/incomes linked to accounts; account management unavailable
- **Graceful degradation:** Expenses/incomes can be created without account linkage

---

## 3.5 Expense Service

### 3.5.1 Purpose
**Why this service exists:** Manages expense transactions with category and account integration.

**Business capability:** Expense tracking, monthly limits, statistics.

**What would break if removed:** Core expense tracking functionality lost.

### 3.5.2 Business Logic

**Key business rules:**
- Amount: > 0, max 999,999.99
- Date: Not in future, not > 10 years old
- Monthly limit enforcement via subscription
- Account balance automatically updated on create/update/delete

**State transitions:**
- Account balance: Decreased on create, restored on delete, adjusted on update

### 3.5.3 Owned Data & Models

`expenses`
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | PK |
| amount | Float | > 0 |
| date | Date | |
| description | String(500) | Optional |
| user_id | Integer | |
| workspace_id | UUID | |
| category_id | Integer | Optional |
| account_id | Integer | Optional |
| currency | String(3) | Default: USD |

**Storage:** PostgreSQL (`expense_db`)

### 3.5.4 API & Endpoints

| Method | Path | Purpose | Critical |
|--------|------|---------|----------|
| POST | `/expenses/` | Create expense | ✅ |
| GET | `/expenses/` | List expenses | ✅ |
| GET | `/expenses/paginated` | Paginated list | |
| PATCH | `/expenses/{id}` | Update expense | |
| DELETE | `/expenses/{id}` | Delete expense | |
| GET | `/expenses/category/{id}` | By category | |
| GET | `/expenses/current-month-count` | Monthly count/limit | |

### 3.5.5 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| category_service | Validate category |
| account_service | Validate account, update balance |
| currency_service | Currency conversion |
| workspace_service | Authorization |
| subscription_service | Monthly limit check |

### 3.5.6 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| account_service | Fetch expenses for account |
| recurring_service | Create expenses automatically |

### 3.5.7 Failure Impact

- **If down:** Cannot track expenses; recurring expense creation fails
- **User flows blocked:** Core expense tracking
- **Graceful degradation:** None - critical feature

---

## 3.6 Income Service

### 3.6.1 Purpose
**Why this service exists:** Manages income transactions with category and account integration.

**Business capability:** Income tracking, statistics, account balance updates.

**What would break if removed:** Core income tracking functionality lost.

### 3.6.2 Business Logic

Same patterns as expense_service:
- Amount validation (> 0, max 999,999.99)
- Monthly limit enforcement
- Account balance automatically increased

### 3.6.3 Owned Data & Models

`incomes` - Same structure as expenses

**Storage:** PostgreSQL (`income_db`)

### 3.6.4 API & Endpoints

Similar to expense_service with `/incomes/` prefix.

### 3.6.5 Dependencies (Outbound)

Same as expense_service.

### 3.6.6 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| account_service | Fetch incomes for account |
| recurring_service | Create incomes automatically |

### 3.6.7 Failure Impact

Same as expense_service for income flows.

---

## 3.7 Currency Service

### 3.7.1 Purpose
**Why this service exists:** Provides real-time currency conversion for multi-currency support.

**Business capability:** Exchange rates, currency conversion, supported currencies list.

**What would break if removed:** Multi-currency features fail; statistics aggregation fails.

### 3.7.2 Business Logic

**Key business rules:**
- Top 10 currencies supported by default
- Rates cached for 1 hour, fallback cached for 24 hours
- Cross-rate calculation: to_rate / from_rate
- Graceful degradation with cached/fallback rates

**External data source:** ExchangeRate-API (api.exchangerate-api.com)

### 3.7.3 Owned Data & Models

No database - stateless service with Redis caching.

**Cache keys:**
- `currency:rates:{base}` - Exchange rates (1h TTL)
- `currency:fallback:{from}:{to}` - Fallback rates (24h TTL)
- `currency:currencies_top10` - Currency list (24h TTL)

### 3.7.4 API & Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/currencies` | Get supported currencies |
| GET | `/api/v1/rates` | Get exchange rates |
| POST | `/api/v1/convert` | Convert amount |
| POST | `/api/v1/currencies/refresh` | Force refresh |

### 3.7.5 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| ExchangeRate-API | External exchange rates |
| Redis | Caching |

### 3.7.6 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| expense_service | Currency conversion |
| income_service | Currency conversion |
| account_service | Balance conversion |
| debt_service | Debt conversion |
| goals_service | Goal amount conversion |
| user_service | Validate currency codes |

### 3.7.7 Failure Impact

- **If down:** Multi-currency features degrade; falls back to cached rates
- **User flows blocked:** None immediately (graceful degradation)
- **Graceful degradation:** Uses fallback cache, then hardcoded rates

---

## 3.8 Debt Service

### 3.8.1 Purpose
**Why this service exists:** Tracks debts and repayments with multi-currency support.

**Business capability:** Debt lifecycle, payment tracking, interest breakdown.

### 3.8.2 Business Logic

**Core domain concepts:**
- Debt (credit card, loan, mortgage, etc.)
- Contact (creditor/lender)
- Payment (with principal/interest split)

**Key business rules:**
- Balance auto-updates on payment
- Auto-marks as paid off when balance reaches 0
- Cannot change currency if payments exist

### 3.8.3 Owned Data & Models

`debts` - Debt accounts with balance, interest rate
`contacts` - Creditors/lenders
`debt_payments` - Payment history

**Storage:** PostgreSQL (`debt_db`)

### 3.8.4 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| workspace_service | Authorization |
| subscription_service | Debt limit check |
| currency_service | Multi-currency aggregation |
| user_service | Get base currency |

### 3.8.5 Failure Impact

- **If down:** Debt tracking unavailable
- **Graceful degradation:** Independent feature, doesn't block other flows

---

## 3.9 Goals Service

### 3.9.1 Purpose
**Why this service exists:** Enables users to set and track financial goals.

**Business capability:** Goal setting, milestone tracking, progress monitoring.

### 3.9.2 Business Logic

**Core domain concepts:**
- Goal (savings, debt payoff, investment, etc.)
- Milestone (sub-goals with targets)
- Progress tracking (auto-calculated percentage)

**Key business rules:**
- Auto-completion when progress >= 100%
- Milestones are ordered by index
- Cascading delete for milestones

### 3.9.3 Owned Data & Models

`goals` - Financial goals with target/current amounts
`milestones` - Sub-goals within a goal

**Storage:** PostgreSQL (`goals_db`)

### 3.9.4 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| workspace_service | Authorization |
| subscription_service | Goal limit check |
| user_service | Get base currency |
| currency_service | Amount conversion |

### 3.9.5 Failure Impact

- **If down:** Goal tracking unavailable
- **Graceful degradation:** Independent feature

---

## 3.10 Recurring Service

### 3.10.1 Purpose
**Why this service exists:** Automates recurring expenses and income on schedule.

**Business capability:** Recurring payment definitions, automatic execution.

### 3.10.2 Business Logic

**Core domain concepts:**
- Recurring payment (expense or income type)
- Schedule (daily, weekly, monthly, yearly)
- Execution history

**Key business rules:**
- Schedule config varies by type:
  - Daily: empty
  - Weekly: day_of_week (0-6)
  - Monthly: day_of_month (1-31)
  - Yearly: month + day
- Auto-executes via built-in scheduler (APScheduler)
- Creates actual expense/income on execution

**State transitions:**
- Status: `active` ↔ `paused` → `completed` | `cancelled`

### 3.10.3 Owned Data & Models

`recurring_payments` - Payment definitions
`payment_schedules` - Execution history

**Storage:** PostgreSQL (`recurring_db`)

### 3.10.4 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| expense_service | Create expenses |
| income_service | Create incomes |
| category_service | Validate category |
| workspace_service | Authorization |
| subscription_service | Recurring limit check |

### 3.10.5 Failure Impact

- **If down:** Recurring payments not executed
- **Graceful degradation:** Missed payments can be executed later

---

## 3.11 Subscription Service

### 3.11.1 Purpose
**Why this service exists:** Manages SaaS subscription plans and feature entitlements.

**Business capability:** Plan management, feature limits, subscription lifecycle.

**What would break if removed:** All feature limits would fail; payment flow breaks.

### 3.11.2 Business Logic

**Core domain concepts:**
- Plan (basic, professional, enterprise)
- Feature (categories, accounts, expenses, etc.)
- Entitlement (feature limits per plan)
- Subscription (user's active plan)

**Subscription plans:**

| Plan | Price | Categories | Accounts | Expenses/mo | Workspaces |
|------|-------|------------|----------|-------------|------------|
| Basic | Free | 10 | 2 | 50 | 1 |
| Professional | $9.99/mo | 50 | 10 | 5,000 | 3 |
| Enterprise | $29.99/mo | Unlimited | Unlimited | Unlimited | 10 |

**Key business rules:**
- Same plan renewal: Extends from current expiry
- Different plan: Starts fresh from now
- Cancellation: Can cancel immediately or at period end
- Auto-renewal: Via scheduler_service

**State transitions:**
- Status: `active` ↔ `past_due` ↔ `paused` → `canceled`

### 3.11.3 Owned Data & Models

`plans` - Available plans
`features` - Available features
`plan_features` - Feature limits per plan
`subscriptions` - User subscriptions
`subscription_consent_log` - Paddle compliance audit

**Storage:** PostgreSQL (`subscription_db`)

### 3.11.4 API & Endpoints

**Public:**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/plans` | List plans |
| GET | `/v1/entitlements/{user_id}` | Get entitlements |
| POST | `/v1/subscriptions/{user_id}:set_plan` | Set plan |
| DELETE | `/v1/subscriptions/{user_id}/cancel` | Cancel |

**Internal:**
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/internal/features/{user_id}` | Get feature limits |
| POST | `/v1/internal/subscriptions/activate` | Activate after payment |
| GET | `/v1/internal/subscriptions:expiring` | Get expiring subscriptions |

### 3.11.5 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| Redis | Entitlement caching, event pub/sub |

### 3.11.6 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| All domain services | Feature limit checks |
| payment_service | Payment success/failure notifications |
| scheduler_service | Subscription renewal |
| user_service | Bootstrap plan on registration |

### 3.11.7 Failure Impact

- **If down:** All feature limit checks fail (operations blocked)
- **User flows blocked:** Any operation with limits
- **Graceful degradation:** Services may cache entitlements briefly

---

## 3.12 Payment Service

### 3.12.1 Purpose
**Why this service exists:** Integrates with Paddle Billing for payment processing.

**Business capability:** Payment creation, webhook handling, recurring charges.

### 3.12.2 Business Logic

**Core domain concepts:**
- Payment (subscription or one-time)
- Payment events (audit trail)
- Recurring tokens (for auto-renewal)

**Key business rules:**
- Idempotent payment creation via `Idempotency-Key` header
- Webhook signature verification (HMAC)
- State machine prevents invalid transitions
- Recurring tokens extracted from webhook callbacks

**State transitions:**
- CREATED → PENDING → PAID
- PENDING → FAILED | EXPIRED | CANCELED
- PAID → REFUNDED | PARTIALLY_REFUNDED

### 3.12.3 Owned Data & Models

`payments` - Payment records
`payment_events` - Audit log
`idempotency_keys` - Deduplication

**Storage:** PostgreSQL (`payment_db`)

### 3.12.4 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| Paddle API | Payment gateway |
| subscription_service | Payment success/failure notifications |

### 3.12.5 Consumers (Inbound)

| Service | Purpose |
|---------|---------|
| frontend | Create payments |
| scheduler_service | Recurring payment execution |
| Paddle | Webhooks |

### 3.12.6 Failure Impact

- **If down:** Cannot process payments; subscription renewal fails
- **Graceful degradation:** Webhooks return 200 OK always (prevent retries)

---

## 3.13 Scheduler Service

### 3.13.1 Purpose
**Why this service exists:** Executes scheduled background jobs, primarily subscription auto-renewal.

**Business capability:** Job scheduling, execution tracking.

### 3.13.2 Business Logic

**Scheduled jobs:**
- **Subscription Renewal**: Runs hourly (`0 */1 * * *`)
  - Finds expiring subscriptions (within 1 day)
  - Creates recurring payments
  - Extends or marks as past_due based on result

**Key business rules:**
- Single instance per job (prevents duplicates)
- Coalesces missed runs
- Skips subscriptions without auto_renew or recurring_token

### 3.13.3 Owned Data & Models

`job_executions` - Job run history
`renewal_attempts` - Individual renewal attempts

**Storage:** PostgreSQL (`scheduler_db`)

### 3.13.4 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| subscription_service | Get expiring subscriptions, extend/mark past_due |
| payment_service | Create recurring payments |

### 3.13.5 Failure Impact

- **If down:** Subscription auto-renewal stops; manual intervention needed
- **Graceful degradation:** Missed renewals can be processed on recovery

---

## 3.14 PDF Parser Service

### 3.14.1 Purpose
**Why this service exists:** Imports transactions from bank PDF statements.

**Business capability:** PDF parsing, transaction extraction, MCC enrichment.

### 3.14.2 Business Logic

**Supported banks:**
- Monobank (fully implemented)
- Others planned but not implemented

**Key business rules:**
- File size limit: 10MB
- Monthly upload limit (subscription-based)
- Records per upload limit (subscription-based)
- 30-second parsing timeout

### 3.14.3 Owned Data & Models

`pdf_uploads` - Upload history for limit tracking

**Storage:** PostgreSQL (`pdf_parser_db`)

### 3.14.4 Dependencies (Outbound)

| Service | Purpose |
|---------|---------|
| category_service | MCC code lookup |
| subscription_service | Upload limit checks |

### 3.14.5 Failure Impact

- **If down:** Cannot import bank statements
- **Graceful degradation:** Independent feature, doesn't block manual entry

---

# 4. Inter-Service Communication

## Communication Protocols

| Protocol | Usage |
|----------|-------|
| HTTP/REST | All service-to-service communication |
| Redis Pub/Sub | Subscription change events (limited) |

## Authentication Between Services

**Pattern:** Internal token authentication

```
Header: X-Internal-Token: <shared_secret>
```

- All services share the same `INTERNAL_SECRET_TOKEN`
- Internal endpoints (`/internal/*`) require this token
- Public endpoints require JWT Bearer tokens

## Error Handling and Retries

**Observed patterns:**
- HTTP timeout: 5-10 seconds per call
- No automatic retries visible in code
- External service failures return 503 Service Unavailable
- Database errors trigger transaction rollback

## Coupling Analysis

### Tight Couplings (Synchronous, Blocking)

```
user_service ←── ALL services (JWT validation)
workspace_service ←── ALL domain services (authorization)
subscription_service ←── ALL domain services (feature limits)
```

### Cascading Failure Risks

1. **user_service down** → All authentication fails → System unusable
2. **workspace_service down** → All authorization fails → All writes blocked
3. **subscription_service down** → Feature checks fail → Operations blocked
4. **currency_service down** → Graceful degradation with cached rates

### Service Dependency Graph

```
                    ┌─────────────────┐
                    │   user_service  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │workspace_service│ │currency_service │ │subscription_svc │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             │                   │                   │
    ┌────────┴────────┬─────────┴─────────┬─────────┘
    │                 │                   │
    ▼                 ▼                   ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│expense  │ │income   │ │account  │ │category │
│_service │ │_service │ │_service │ │_service │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
    │                                     ▲
    │                                     │
    └─────────────────────────────────────┘
              (category validation)
```

---

# 5. Core User Flows (System-Wide)

## 5.1 User Registration

**Trigger:** User submits registration form

**Flow:**

```
1. Frontend → user_service: POST /auth/register
2. user_service: Validate email, username, password
3. user_service: Hash password, create user record
4. user_service → workspace_service: POST /internal/workspaces/personal
   - Creates personal workspace (non-blocking)
5. user_service → subscription_service: POST /v1/subscriptions/{user_id}:set_plan
   - Bootstraps basic plan (non-blocking)
6. user_service: Return JWT tokens
```

**Side effects:**
- User record created
- Personal workspace created (async, best-effort)
- Basic subscription created (async, best-effort)

## 5.2 User Authentication (Login)

**Trigger:** User submits login form

**Flow:**

```
1. Frontend → user_service: POST /auth/login
2. user_service: Validate credentials, check lockout
3. user_service: Generate JWT tokens
4. Frontend: Store tokens, redirect to dashboard
```

**Side effects:**
- Login attempt recorded (rate limiting)
- Access/refresh tokens issued

## 5.3 Creating an Expense

**Trigger:** User creates expense in UI

**Flow:**

```
1. Frontend → expense_service: POST /expenses/
   - Headers: Authorization: Bearer <JWT>, X-Workspace-Id: <uuid>

2. expense_service: Extract user from JWT

3. expense_service → workspace_service: POST /internal/workspaces/{id}/authorize
   - Check user has "member" role

4. expense_service → subscription_service: GET /v1/internal/features/{user_id}
   - Check monthly expense limit

5. IF category_id provided:
   expense_service → category_service: GET /internal/categories/{id}
   - Validate category belongs to user in workspace

6. IF account_id provided:
   expense_service → account_service: GET /internal/accounts/{id}/validate
   - Validate account ownership

7. expense_service: Create expense record

8. IF account_id provided:
   expense_service → account_service: PUT /internal/accounts/{id}/balance
   - Deduct amount (with currency conversion if needed)

9. expense_service: Return created expense
```

**Side effects:**
- Expense record created
- Account balance decreased (if linked)
- Monthly count incremented

## 5.4 Subscription Upgrade

**Trigger:** User selects paid plan

**Flow:**

```
1. Frontend → subscription_service: GET /v1/plans/with-features
   - Display available plans

2. Frontend → payment_service: POST /v1/payments
   - Create payment for selected plan
   - Include consent confirmation

3. payment_service → Paddle: Generate checkout URL

4. Frontend: Redirect to Paddle checkout

5. User completes payment on Paddle

6. Paddle → payment_service: POST /v1/webhooks/paddle
   - Webhook with payment result

7. payment_service: Verify signature, update payment status

8. IF payment successful:
   payment_service → subscription_service: POST /v1/internal/subscriptions/activate
   - Activate subscription, store recurring token

9. subscription_service: Update subscription, publish event

10. subscription_service → Redis: PUBLISH user.subscription.changed
```

**Side effects:**
- Payment record created
- Subscription activated
- Recurring token stored for auto-renewal
- Feature limits updated

## 5.5 Subscription Auto-Renewal

**Trigger:** Scheduler job (hourly)

**Flow:**

```
1. scheduler_service: Cron triggers subscription_renewal job

2. scheduler_service → subscription_service: GET /v1/internal/subscriptions:expiring
   - Get subscriptions expiring within 1 day

3. FOR EACH subscription:
   3a. scheduler_service: Validate has auto_renew and recurring_token
   
   3b. scheduler_service → payment_service: POST /v1/internal/payments:recurring
       - Execute recurring charge using stored token
   
   3c. IF payment successful:
       scheduler_service → subscription_service: POST /v1/internal/subscriptions/{id}:extend
       - Extend subscription period
   
   3d. IF payment failed:
       scheduler_service → subscription_service: POST /v1/internal/subscriptions/{id}:mark_past_due
       - Mark as past_due
```

**Side effects:**
- Payment records created
- Subscriptions extended or marked past_due
- Job execution logged

## 5.6 Recurring Payment Execution

**Trigger:** Recurring service scheduler (daily at 00:01)

**Flow:**

```
1. recurring_service: Built-in scheduler triggers

2. recurring_service: Query active payments where next_execution <= today

3. FOR EACH payment:
   3a. IF payment_type == EXPENSE:
       recurring_service → expense_service: POST /internal/
       - Create expense with defined amount, category, etc.
   
   3b. IF payment_type == INCOME:
       recurring_service → income_service: POST /api/v1/incomes
       - Create income with defined amount, category, etc.
   
   3c. recurring_service: Update last_executed, calculate next_execution
   
   3d. recurring_service: Log execution in payment_schedules
```

**Side effects:**
- Expense or income records created
- Account balances updated (if linked)
- Execution history recorded

---

# 6. Business Rules & Cross-Service Invariants

## Rules That Span Multiple Services

### 1. Feature Limits Enforcement

**Services involved:** subscription_service, expense_service, income_service, account_service, category_service, debt_service, goals_service, recurring_service

**Rule:** Users cannot exceed their plan's feature limits (e.g., expenses/month, number of accounts)

**Enforcement:** Each service calls `subscription_service` before creating resources.

**Risk:** Eventual consistency - limits could be exceeded in race conditions.

### 2. Workspace Authorization

**Services involved:** workspace_service, all domain services

**Rule:** Users can only access data in workspaces where they are members.

**Enforcement:** Each service calls `workspace_service` to verify authorization.

**Risk:** Authorization cached briefly - revoked access may not be immediate.

### 3. Account Balance Consistency

**Services involved:** account_service, expense_service, income_service

**Rule:** Account balance must reflect sum of all transactions.

**Enforcement:**
- Expense creates → deduct from account
- Income creates → add to account
- Delete → reverse the operation

**Risk:** If service crashes mid-transaction, balance may be inconsistent.

### 4. Category Ownership

**Services involved:** category_service, expense_service, income_service, recurring_service

**Rule:** Categories belong to specific users in specific workspaces.

**Enforcement:** Category service validates ownership on lookup.

### 5. Subscription Lifecycle

**Services involved:** subscription_service, payment_service, scheduler_service

**Rule:** Subscriptions follow a defined state machine.

**Enforcement:**
- payment_service notifies subscription_service on payment events
- scheduler_service extends subscriptions after successful renewal
- subscription_service validates state transitions

## Rules Enforced vs Convention

| Rule | Enforced | Convention Only |
|------|----------|-----------------|
| Feature limits | ✅ API validates | |
| Workspace authorization | ✅ API validates | |
| Account balance updates | | ⚠️ No saga/compensation |
| Category ownership | ✅ API validates | |
| Subscription state machine | ✅ State checks | |
| Data consistency on failures | | ⚠️ No distributed transactions |

## What MUST Stay in Sync

1. **User → Personal Workspace**: Created together (best-effort)
2. **User → Basic Subscription**: Created together (best-effort)
3. **Expense/Income → Account Balance**: Must match
4. **Payment → Subscription Status**: Must match
5. **Recurring Token → Payment Provider**: Must be valid

---

# 7. Risks & Observations

## Hidden Dependencies

1. **JWT Secret Sharing**: All services must use the same `SECRET_KEY` for token validation
2. **Internal Token**: All services share `INTERNAL_SECRET_TOKEN`
3. **Database Schema**: Services assume specific table structures exist

## Overlapping Responsibilities

1. **Authorization Logic**: Duplicated in each service's `WorkspaceAuthorizationMixin`
2. **Subscription Limit Checking**: Each service implements similar patterns
3. **Currency Conversion**: Multiple services have similar currency client code

## Chatty Service Communication

**Example: Creating an expense with category and account**

```
1 call to workspace_service (authorization)
1 call to subscription_service (limits)
1 call to category_service (validation)
1 call to account_service (validation)
1 call to account_service (balance update)
= 5 synchronous HTTP calls per expense creation
```

**Impact:** Increased latency, higher failure probability.

## Single Points of Failure

| Component | Impact if Down |
|-----------|----------------|
| PostgreSQL | All services fail |
| Redis | Currency caching fails, subscription events fail |
| user_service | All authentication fails |
| workspace_service | All authorization fails |
| subscription_service | All feature checks fail |

## Missing Abstractions or Contracts

1. **No API Gateway**: Each service exposes directly to frontend
2. **No Service Discovery**: Hardcoded service URLs
3. **No Circuit Breakers**: Failures cascade directly
4. **No Distributed Tracing**: Harder to debug cross-service issues
5. **No Schema Validation Contracts**: OpenAPI specs not shared between services
6. **No Saga Pattern**: For distributed transactions (e.g., account balance updates)

## Security Observations

1. **Internal Token**: Single shared secret for all service-to-service auth
2. **No Mutual TLS**: Service-to-service communication not encrypted
3. **Secrets in Environment**: Database passwords, API keys in env vars

---

# 8. Summary & System Health Assessment

## Overall Architecture Maturity

**Rating: 3/5 - Production-Ready MVP**

**Strengths:**
- Clear service boundaries with well-defined responsibilities
- Consistent patterns across services (FastAPI, SQLAlchemy, same structure)
- Proper workspace-based multi-tenancy
- Comprehensive API documentation (FastAPI auto-generates OpenAPI)
- Good logging infrastructure (Loki + Promtail + Grafana)
- Subscription-based feature limits properly enforced

**Weaknesses:**
- No API gateway or service mesh
- No circuit breakers for resilience
- Chatty inter-service communication
- Single database instance for all services
- No distributed tracing
- Limited event-driven architecture

## Main Technical and Business Risks

### Technical Risks

1. **Single Database Instance**: All 13 databases on one PostgreSQL instance
   - Risk: Single point of failure, performance bottleneck
   - Mitigation: Consider managed PostgreSQL with HA, or split databases

2. **No Distributed Transaction Handling**: Account balance updates can become inconsistent
   - Risk: Data integrity issues on failures
   - Mitigation: Implement saga pattern or eventual consistency with reconciliation

3. **Synchronous Coupling**: Many services depend on workspace_service and subscription_service
   - Risk: Cascading failures, high latency
   - Mitigation: Cache authorization results, use async patterns

### Business Risks

1. **Payment Provider Lock-in**: Deeply integrated with Paddle
   - Risk: Difficult to switch providers or support multiple providers
   - Mitigation: Abstract payment provider interface

2. **PDF Parser Limited**: Only Monobank supported
   - Risk: Limited market reach
   - Mitigation: Prioritize adding more bank parsers

3. **Subscription Service Criticality**: Feature limits fail if service is down
   - Risk: User experience degradation
   - Mitigation: Aggressive caching, graceful degradation

## Areas That Are Solid and Well-Designed

1. **Authentication & Authorization**: JWT + workspace-based RBAC is clean
2. **Subscription Management**: Well-thought-out plans, features, limits
3. **Currency Service**: Good caching strategy with fallbacks
4. **Recurring Payments**: Built-in scheduler is simple and effective
5. **API Design**: Consistent REST patterns, good error handling
6. **Observability**: Good logging setup with Grafana/Loki
7. **Workspace Model**: Supports both personal and shared use cases

## Top 3 Recommendations for Improvement

### 1. Add an API Gateway

**Why:** Reduce direct exposure, centralize auth, enable rate limiting, provide single entry point.

**How:** Introduce Kong, Traefik, or nginx as API gateway. Route all frontend traffic through it.

**Impact:** Improved security, easier monitoring, reduced coupling.

### 2. Implement Circuit Breakers

**Why:** Prevent cascading failures when dependent services are down.

**How:** Use libraries like `circuitbreaker` in Python clients. Add health-based routing.

**Impact:** Better resilience, faster failure recovery, improved user experience.

### 3. Add Distributed Tracing

**Why:** Debug complex flows across multiple services.

**How:** Integrate OpenTelemetry with Jaeger or Zipkin. Add trace IDs to all service calls.

**Impact:** Faster debugging, better understanding of performance bottlenecks.

---

## Appendix: Service Port Reference

| Service | Internal Port | External Port | Database |
|---------|--------------|---------------|----------|
| user_service | 8000 | 8001 | user_db |
| category_service | 8000 | 8002 | category_db |
| expense_service | 8000 | 8003 | expense_db |
| income_service | 8000 | 8004 | income_db |
| recurring_service | 8000 | 8005 | recurring_db |
| goals_service | 8000 | 8006 | goals_db |
| pdf_parser_service | 8000 | 8007 | pdf_parser_db |
| debt_service | 8000 | 8008 | debt_db |
| account_service | 8000 | 8009 | account_db |
| currency_service | 8000 | 8010 | - (Redis only) |
| subscription_service | 8080 | 8011 | subscription_db |
| workspace_service | 8000 | 8012 | workspace_db |
| payment_service | 8000 | 8013 | payment_db |
| scheduler_service | 8090 | 8014 | scheduler_db |
| PostgreSQL | 5432 | 5433 | - |
| Redis | 6379 | 6377 | - |
| Grafana | 3000 | 3001 | - |
| Loki | 3100 | 3100 | - |

---

*Document generated from codebase analysis. Always verify against actual implementation.*
