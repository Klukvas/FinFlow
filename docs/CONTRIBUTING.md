# Contributing Guide

## Prerequisites

- **Docker** and **Docker Compose** (v2+)
- **Node.js** >= 20.0.0 with **Yarn**
- **Python** >= 3.11 (for running services locally without Docker)
- **Git**

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd accounting_app

# 2. Start all backend services
docker compose up -d

# 3. Start the frontend development server
cd frontend && yarn install && yarn start
```

The frontend runs at `http://localhost:5173` (Vite).

## Project Structure

```
accounting_app/
├── frontend/                  # React + Vite + TypeScript (port 5173)
├── user_service/              # Auth, users (port 8001)
├── category_service/          # Categories (port 8002)
├── expense_service/           # Expenses (port 8003)
├── income_service/            # Incomes (port 8004)
├── recurring_service/         # Recurring payments (port 8005)
├── goals_service/             # Financial goals (port 8006)
├── pdf_parser_service/        # PDF bank statement parser (port 8007)
├── debt_service/              # Debts (port 8008)
├── account_service/           # Financial accounts (port 8009)
├── currency_service/          # Exchange rates (port 8010)
├── subscription_service/      # Plan limits (port 8011)
├── workspace_service/         # Workspaces & RBAC (port 8012)
├── payment_service/           # Paddle billing (port 8013)
├── scheduler_service/         # Cron jobs (port 8014)
├── ai_assistant_service/      # AI assistant (port 8015)
├── bank_sync_service/         # Bank API sync (port 8016, disabled)
├── shared/                    # Shared Python library (auth, clients, logging)
├── admin_panel/               # Admin dashboard (disabled)
├── infra/                     # Terraform (Hetzner)
├── e2e_ui_tests/              # Playwright E2E tests
├── docs/                      # Documentation
└── docker-compose.yml         # Local development orchestration
```

## Frontend Commands

<!-- AUTO-GENERATED: frontend-scripts -->

| Command | Description |
|---------|-------------|
| `yarn build` | Production build with Vite |
| `yarn build:seo` | Production build + SEO prerender |
| `yarn lint` | ESLint check (TS/TSX, zero warnings) |
| `yarn lint:fix` | ESLint auto-fix |
| `yarn preview` | Preview production build locally |
| `yarn type-check` | TypeScript type checking (`tsc --noEmit`) |
| `yarn test` | Run Playwright E2E tests |
| `yarn test:ui` | Playwright interactive UI mode |
| `yarn test:headed` | Playwright in headed browser mode |
| `yarn test:debug` | Playwright debug mode |
| `yarn test:report` | Open Playwright HTML report |

<!-- /AUTO-GENERATED: frontend-scripts -->

## Docker Compose Services

<!-- AUTO-GENERATED: docker-services -->

| Service | Port | Database | Health Check |
|---------|------|----------|-------------|
| db (PostgreSQL 15) | 5433 | -- | `pg_isready` |
| redis (Redis 7) | 6377 | -- | `redis-cli ping` |
| user_service | 8001 | user_db | `GET /health` |
| category_service | 8002 | category_db | -- |
| expense_service | 8003 | expense_db | -- |
| income_service | 8004 | income_db | -- |
| recurring_service | 8005 | recurring_db | -- |
| goals_service | 8006 | goals_db | -- |
| pdf_parser_service | 8007 | -- | -- |
| debt_service | 8008 | debt_db | -- |
| account_service | 8009 | account_db | `GET /health` |
| currency_service | 8010 | -- (Redis) | `GET /health` |
| subscription_service | 8011 | subscription_db | -- |
| workspace_service | 8012 | workspace_db | `GET /health` |
| payment_service | 8013 | payment_db | `GET /health/live` |
| scheduler_service | 8014 | -- | `GET /health/live` |
| ai_assistant_service | 8015 | -- (Redis) | `GET /health` |
| bank_sync_service | 8016 | bank_sync_db | `GET /health` |

<!-- /AUTO-GENERATED: docker-services -->

## Environment Variables

Each service has a `.env.docker` file for local development. Key variables shared across services:

<!-- AUTO-GENERATED: env-vars -->

| Variable | Used By | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Most services | PostgreSQL connection string |
| `SECRET_KEY` | Most services | JWT signing key (hex string) |
| `ALGORITHM` | Most services | JWT algorithm (default: `HS256`) |
| `INTERNAL_SECRET_TOKEN` | Most services | Inter-service auth token |
| `CORS_ORIGINS` | Most services | Allowed CORS origins |
| `LOG_LEVEL` | Most services | Logging level (default: `INFO`) |
| `REDIS_URL` | account, currency, ai_assistant, payment, scheduler | Redis connection string |
| `WORKSPACE_SERVICE_URL` | expense, income, account, bank_sync | Workspace service base URL |
| `CATEGORY_SERVICE_URL` | expense, income, recurring, ai_assistant, bank_sync | Category service base URL |
| `EXPENSE_SERVICE_URL` | account, recurring, ai_assistant, bank_sync | Expense service base URL |
| `INCOME_SERVICE_URL` | account, recurring, ai_assistant, bank_sync | Income service base URL |
| `ACCOUNT_SERVICE_URL` | expense, income, ai_assistant, bank_sync | Account service base URL |
| `SUBSCRIPTION_SERVICE_URL` | Most services | Subscription/limits service base URL |
| `PADDLE_API_KEY` | payment | Paddle Billing API key |
| `PADDLE_WEBHOOK_SECRET` | payment | Paddle webhook signing secret |
| `PADDLE_ENVIRONMENT` | payment | `sandbox` or `production` |
| `ANTHROPIC_API_KEY` | ai_assistant | Claude API key |
| `ANTHROPIC_MODEL` | ai_assistant | Claude model ID |
| `BANK_TOKEN_ENCRYPTION_KEY` | bank_sync | Fernet key for bank token encryption |

<!-- /AUTO-GENERATED: env-vars -->

## Testing

### Backend (Python)

```bash
# Run tests for a specific service
docker compose exec expense_service pytest -v

# Run with coverage
docker compose exec expense_service pytest --cov=app --cov-report=term-missing

# Run locally (requires virtualenv with service dependencies)
cd expense_service && pytest -v
```

Services with unit tests: `category_service`, `expense_service`, `user_service`, `payment_service`, `workspace_service`.

### Frontend (Playwright)

```bash
cd frontend

# Install browsers (first time)
yarn test:install

# Run all E2E tests
yarn test

# Interactive UI mode
yarn test:ui

# Run specific test file
npx playwright test tests/auth.spec.ts
```

### E2E (Standalone)

```bash
cd e2e_ui_tests
npm install
npx playwright test
```

## Code Style

### Frontend (TypeScript/React)

- ESLint with zero-warning policy
- Tailwind CSS for styling (theme classes: `theme-*`)
- i18n: all user-facing text via `react-i18next` (en/ru/uk)
- Immutable state updates (never mutate)
- Lazy loading for protected pages

### Backend (Python/FastAPI)

- FastAPI with Pydantic v2 schemas
- SQLAlchemy v2 ORM (database-per-service)
- Shared library (`shared/`) for auth, HTTP clients, logging
- Route ordering: literal paths before parameterized `/{id}` paths

## PR Checklist

- [ ] Code builds without errors (`yarn build` / `docker compose up --build`)
- [ ] No TypeScript errors (`yarn type-check`)
- [ ] No ESLint warnings (`yarn lint`)
- [ ] Tests pass for modified services
- [ ] i18n keys added for all 3 locales (en/ru/uk)
- [ ] No hardcoded secrets or credentials
- [ ] PR description includes summary and test plan
