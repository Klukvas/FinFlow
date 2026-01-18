# Category Service

## 1. One-liner

Manages hierarchical expense and income categories with MCC code integration, subscription-based limits, and workspace multi-tenancy support for expense tracking applications.

## 2. Ownership / Responsibility

### In Scope
- Create, read, update, delete (CRUD) operations for user categories
- Hierarchical category organization (parent-child relationships, max 2 levels deep)
- Merchant Category Code (MCC) integration with multi-language translations (EN, RU, UK)
- Category type management (EXPENSE vs INCOME)
- Workspace-scoped category isolation and multi-tenancy
- Category statistics and analytics per workspace
- Subscription-based category limits enforcement
- Internal API for category validation by other services (expense, income, recurring, etc.)

### Out of Scope
- User authentication/authorization (delegated to user_service via JWT)
- Workspace management and RBAC (delegated to workspace_service)
- Subscription plan management (delegated to subscription_service)
- Transaction/expense data (owned by expense_service)
- Income data (owned by income_service)
- MCC code management beyond read-only access (translations seeded via migrations)

### Domain Entities (Source of Truth)
- **Category**: User-defined hierarchical categories with optional parent-child relationships
- **MCCCode**: Merchant Category Codes with canonical English names
- **MCCTranslation**: Localized translations for MCC codes (EN, RU, UK)

## 3. Key Business Flows

### Flow 1: Create User Category
- **Input**: User ID, workspace ID, category name, optional parent ID, category type (EXPENSE/INCOME)
- **Rules**:
  - Name must be 3-100 characters, non-empty, trimmed
  - Name must be unique per user within workspace
  - Parent (if provided) must exist and belong to same workspace
  - Maximum hierarchy depth: 2 levels (root → level 1 → level 2)
  - No circular relationships allowed
  - User must have `member` role in workspace
  - Subscription limits enforced (checked via subscription_service)
- **Output**: Created category with ID, timestamps, workspace association
- **Invariants**: No category can exceed max depth; name uniqueness per user/workspace; workspace isolation

### Flow 2: Create Category from MCC Code
- **Input**: User ID, workspace ID, MCC code, optional custom name, optional parent ID, language preference
- **Rules**:
  - MCC code must exist in `mcc_codes` table (1-9999)
  - One category per MCC code per user per workspace (duplicate prevention)
  - Name resolution: custom_name → translation (if language != "en") → English name
  - Category marked as `SYSTEM` created_by (vs USER created)
  - Same validation rules as regular category creation (depth, parent, limits)
  - Batch creation supported (1-50 categories per request)
- **Output**: Category with MCC association, translated name, system flag
- **Invariants**: One MCC category per user/workspace/MCC triplet

### Flow 3: List Categories (Hierarchical or Flat)
- **Input**: User ID, workspace ID, pagination (page, size), flat flag
- **Rules**:
  - User must have `viewer` role in workspace
  - Hierarchical mode: returns root categories with children eagerly loaded
  - Flat mode: returns all categories as flat list, ordered by creation time descending
  - Pagination: 1-100 items per page (default 50)
  - Filtered by workspace_id
- **Output**: Paginated list with total count, current page, total pages
- **Invariants**: Only categories from requested workspace visible

### Flow 4: Update Category
- **Input**: Category ID, user ID, workspace ID, new name and/or parent ID
- **Rules**:
  - Category must exist and belong to user in workspace
  - User must have `member` role in workspace
  - New name must be unique (excluding current category)
  - New parent must exist in same workspace
  - Cannot create circular relationships
  - Cannot exceed max depth when changing parent
  - Workspace ID cannot be changed
- **Output**: Updated category with new values
- **Invariants**: Workspace immutability; hierarchy constraints maintained

### Flow 5: Delete Category
- **Input**: Category ID, user ID, workspace ID
- **Rules**:
  - Category must exist and belong to user in workspace
  - User must have `member` role in workspace
  - Category must not have children (delete children first)
- **Output**: Success message
- **Invariants**: No orphaned children; referential integrity maintained

### Flow 6: Internal Category Validation
- **Input**: Category ID, user ID, workspace ID (from another service)
- **Rules**:
  - Requires X-Internal-Token header
  - Validates category exists, belongs to user, in correct workspace
- **Output**: Category details or 404/403 error
- **Invariants**: Used by expense/income/recurring services before persisting transactions

### Flow 7: Internal MCC Lookup
- **Input**: MCC codes batch, user ID, workspace ID (from PDF parser or expense service)
- **Rules**:
  - Requires X-Internal-Token header
  - Returns existence status and category ID for each MCC code
  - Batch endpoint for performance (single query)
- **Output**: List of {mcc_code, exists, category_id}
- **Invariants**: Enables other services to map MCC codes to user categories

## 4. Public API (REST)

| Method | Path | Caller | Auth | Purpose | Key Responses |
|--------|------|--------|------|---------|---------------|
| POST | `/categories/` | Frontend | JWT + Workspace | Create new category | 201, 400 (validation), 404 (parent not found), 401 |
| POST | `/categories/from-mcc` | Frontend | JWT + Workspace | Create category from MCC code | 201, 400 (MCC not found/duplicate), 404 (parent), 401 |
| POST | `/categories/from-mcc/batch` | Frontend | JWT + Workspace | Batch create categories from MCC codes (1-50) | 201 (partial success), 400 (validation), 401 |
| GET | `/categories/` | Frontend | JWT + Workspace | List all categories (hierarchical or flat, paginated) | 200, 401 |
| GET | `/categories/statistics` | Frontend | JWT + Workspace | Get category statistics (counts by type/hierarchy) | 200, 401 |
| GET | `/categories/{id}` | Frontend | JWT + Workspace | Get category by ID | 200, 404, 403, 401 |
| GET | `/categories/{id}/children` | Frontend | JWT + Workspace | Get direct children of category | 200, 404, 401 |
| PUT | `/categories/{id}` | Frontend | JWT + Workspace | Update category | 200, 400, 404, 403, 401 |
| DELETE | `/categories/{id}` | Frontend | JWT + Workspace | Delete category (no children) | 200, 400 (has children), 404, 403, 401 |
| GET | `/mcc/defaults` | Frontend | JWT | Get default MCC categories (filtered by is_default=true) | 200, 401 |
| GET | `/mcc/codes` | Frontend | JWT | Get all MCC codes with translations | 200, 401 |
| GET | `/health` | Infra | Public | Health check | 200 |

**Versioning**: No explicit versioning yet. Breaking changes would require `/v2/` prefix.

**Headers**:
- `Authorization: Bearer <JWT>` (all endpoints except `/health` and `/internal/*`)
- `X-Workspace-Id: <UUID>` (all category CRUD endpoints)

## 5. Internal API (Service-to-Service)

| Method | Path | Caller | Purpose | Response |
|--------|------|--------|---------|----------|
| GET | `/internal/categories/{id}?user_id=X&workspace_id=Y` | expense_service, income_service, recurring_service | Validate category ownership and workspace | 200: CategoryOut, 403: unauthorized, 404: not found |
| GET | `/internal/categories/check-mcc/{mcc_code}?user_id=X&workspace_id=Y` | pdf_parser_service, expense_service | Check if user has category for MCC code | 200: {exists: bool} |
| GET | `/internal/categories/get-by-mcc/{mcc_code}?user_id=X&workspace_id=Y` | pdf_parser_service, expense_service | Get category ID by MCC code | 200: {exists: bool, category_id: int?} |
| POST | `/internal/categories/check-mcc-batch` | pdf_parser_service | Batch check multiple MCC codes | 200: {results: [{mcc_code, exists, category_id}]} |
| GET | `/internal/mcc/codes?language=ru` | pdf_parser_service | Get all MCC codes with translations for parsing | 200: MCCCodeListResponse |
| GET | `/internal/mcc/defaults?language=ru` | pdf_parser_service | Get default MCC categories for suggestions | 200: DefaultCategoryListResponse |

**Authentication**: All internal endpoints require `X-Internal-Token: INTERNAL_SECRET_TOKEN` header.

## 6. Data Model

### Core Tables

#### `categories`
User-defined categories with hierarchical relationships and workspace isolation.

**Key Fields**:
- `id` (int, PK): Auto-increment primary key
- `name` (varchar): Category name (3-100 chars)
- `user_id` (int, indexed): Owner user ID
- `workspace_id` (UUID, not null, indexed): Workspace isolation
- `parent_id` (int, FK, nullable): Self-referential parent category
- `type` (enum): EXPENSE or INCOME
- `mcc_code` (int, FK, nullable): Associated MCC code
- `created_by` (enum): USER or SYSTEM (for MCC-created categories)
- `created_at` (timestamp): Creation time
- `updated_at` (timestamp): Last update time

**Indexes**:
- `idx_categories_workspace_user` (workspace_id, user_id): Multi-tenancy queries
- `idx_categories_workspace_name_type` (workspace_id, name, type): Uniqueness checks

**Unique Constraints**:
- *Assumption*: Name uniqueness enforced in application layer (not DB constraint) per user/workspace

**Relationships**:
- Self-referential: `parent` → `children` (cascade delete orphans)
- FK to `mcc_codes.mcc_code` (nullable)

#### `mcc_codes`
Merchant Category Codes (read-only, seeded via migrations).

**Key Fields**:
- `mcc_code` (int, PK): MCC code (1-9999)
- `name` (varchar, not null): Canonical English name
- `is_default` (bool, default false): Whether this MCC is a commonly used category
- `created_at` (timestamp): Seed time
- `updated_at` (timestamp): Last update time

**Relationships**:
- One-to-many → `translations` (cascade delete)

#### `translations`
Localized translations for MCC codes.

**Key Fields**:
- `mcc_code` (int, PK, FK): References `mcc_codes.mcc_code`
- `lang` (varchar(5), PK): Language code (ru, uk, en)
- `text` (varchar, not null): Translated name

**Composite PK**: (mcc_code, lang)

### Consistency Rules
- Category names must be unique per user per workspace per type
- Maximum hierarchy depth: 2 levels (enforced in application layer)
- Workspace ID is immutable after creation
- Deleting a category requires children to be deleted first (cascade prevented)
- MCC code assignment is optional and unique per user per workspace

### Migrations
- **Tool**: Alembic
- **Location**: `alembic/versions/`
- **Application**: `startup.sh` runs `alembic upgrade head` before starting FastAPI
- **Versioning**: Sequential migration files with descriptive names
- **Seeding**: MCC codes and translations seeded via dedicated migration scripts (`seed_mcc_codes.py`, `seed_mcc_translations.py`)

## 7. Integrations & Dependencies

### Outbound Dependencies (This Service Calls)

#### workspace_service
- **Endpoint**: `POST /internal/workspaces/{id}/authorize`
- **Purpose**: Validate user has required role (viewer/member/admin/owner) in workspace
- **When**: Every category CRUD operation
- **Failure Behavior**: 
  - Timeout: 5s, fail closed (deny access)
  - 403/404: Return 403 to user
  - Connection error: Log + fail closed (deny access)

#### subscription_service
- **Endpoint**: `GET /v1/internal/features/{user_id}`
- **Purpose**: Check category creation limits based on subscription plan
- **When**: Before creating new category
- **Failure Behavior**: 
  - Timeout: 5s, return error to user (cannot verify limit)
  - Connection error: Log + return validation error (fail safe)

### Inbound Dependencies (Services That Call This)

#### expense_service
- **Endpoint**: `GET /internal/categories/{id}`
- **Purpose**: Validate category exists and belongs to user/workspace before creating expense
- **Usage Pattern**: Synchronous validation on expense creation

#### income_service
- **Endpoint**: `GET /internal/categories/{id}`
- **Purpose**: Validate category exists and belongs to user/workspace before creating income
- **Usage Pattern**: Synchronous validation on income creation

#### recurring_service
- **Endpoint**: `GET /internal/categories/{id}`
- **Purpose**: Validate category for recurring transaction templates
- **Usage Pattern**: Synchronous validation on recurring template creation

#### pdf_parser_service
- **Endpoints**: 
  - `POST /internal/categories/check-mcc-batch`
  - `GET /internal/mcc/codes`
  - `GET /internal/categories/get-by-mcc/{mcc_code}`
- **Purpose**: Map parsed MCC codes from bank statements to user categories; retrieve translations
- **Usage Pattern**: Batch checks for performance; retrieve all MCC codes for matching

### Failure Points & Mitigation

| Dependency | Failure Scenario | Impact | Mitigation |
|------------|------------------|--------|------------|
| workspace_service down | Cannot authorize users | All CRUD operations fail with 403 | Fail closed (security); health check fails; circuit breaker recommended |
| workspace_service timeout | Authorization takes >5s | Request fails with 403 | Timeout set to 5s; log errors; consider caching workspace membership |
| subscription_service down | Cannot check limits | Category creation blocked | Fail safe (deny creation); graceful error message; consider default limits fallback |
| Database down | All operations fail | Service unusable | Health check fails; Docker restart; connection pool retries |

## 8. Infrastructure & Runtime

### Containerization
- **Tool**: Docker with Docker Compose
- **Port**: 8000 (internal), exposed as 8002 (host)
- **Base Image**: `python:3.11-slim`
- **Package Manager**: Poetry
- **Additional Tools**: `postgresql-client` for `pg_isready` health checks

### Database
- **Engine**: PostgreSQL 15
- **Database Name**: `category_db`
- **Connection Pool**: SQLAlchemy default (5 connections, 10 max overflow)
- **Migrations**: Alembic (`alembic upgrade head` on startup)
- **Health Check**: `pg_isready -U postgres` every 2s

### Redis
- **Usage**: Not currently used by category_service
- **Assumption**: Could be added for caching workspace authorization results

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | JWT signing key (shared with user_service) |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `INTERNAL_SECRET_TOKEN` | Yes | - | Inter-service authentication token |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `MAX_CATEGORY_DEPTH` | No | `2` | Maximum category hierarchy depth |
| `CORS_ORIGINS` | No | localhost list | Comma-separated allowed origins |
| `SUBSCRIPTION_SERVICE_URL` | Yes | - | Subscription service base URL |
| `WORKSPACE_SERVICE_URL` | Yes | - | Workspace service base URL |

### Health Checks
- **Liveness**: `GET /health` returns `{"status": "healthy", "service": "category-service"}`
- **Readiness**: *Assumption*: Currently same as liveness; could be enhanced to check DB connectivity
- **What They Validate**:
  - Current: HTTP server is running
  - Recommended: Add DB connection check, dependency service reachability

### Startup Sequence
1. Wait for PostgreSQL to be healthy (`pg_isready`)
2. Run Alembic migrations (`alembic upgrade head`)
3. Start Uvicorn server on port 8000
4. FastAPI creates DB tables if not exists (`Base.metadata.create_all`)
5. Service is ready to accept requests

## 9. Approach & Architecture Decisions

### Layered Architecture
- **Routers** (`app/routers/`): FastAPI endpoints, request/response handling, OpenAPI docs
- **Services** (`app/services/`): Business logic, validation orchestration, transaction management
- **Repositories**: *Implicit* via SQLAlchemy ORM (no explicit repo layer)
- **Models** (`app/models/`): SQLAlchemy ORM models (DB schema)
- **Schemas** (`app/schemas/`): Pydantic models (request/response validation)
- **Serializers** (`app/serializers/`): Data transformation and complex validation logic
- **Clients** (`app/clients/`): HTTP clients for other services (workspace, subscription)

### Dependency Injection
- FastAPI `Depends()` for:
  - Database sessions (`get_db`)
  - Service instances (`get_category_service`)
  - Authentication (`get_current_user_id`, `get_workspace_id`)
  - Internal token verification (`verify_internal_token`)

### Idempotency
- **Create**: Not idempotent (each POST creates new category)
- **Update/Delete**: Idempotent by ID (same operation repeated has same effect)
- **MCC Creation**: Duplicate prevention via DB query (user + workspace + mcc_code triplet)
- **Assumption**: No idempotency keys; could add for retry safety

### Error Handling
- **Unified Format**:
  ```json
  {
    "detail": {
      "error": "Human-readable message",
      "errorCode": "MACHINE_READABLE_CODE"
    }
  }
  ```
- **Custom Exceptions**:
  - `CategoryNotFoundError` (404)
  - `CategoryValidationError` (400)
  - `CategoryOwnershipError` (403)
  - `CircularRelationshipError` (400)
  - `CategoryDepthExceededError` (400)
  - `CategoryNameConflictError` (400)
  - `CategoryLimitExceededError` (400)
- **Request ID Correlation**: Generated via middleware, included in all logs
- **Exception Handlers**: Global handlers registered in `main.py` for consistent responses

### Security
- **Public Auth**: JWT Bearer tokens (validated via shared SECRET_KEY)
- **Internal Auth**: `X-Internal-Token` header for service-to-service calls
- **Workspace RBAC**:
  - `viewer`: Can read categories
  - `member`: Can create/update/delete categories
  - `admin`/`owner`: Same as member (no special privileges in this service)
- **Workspace Isolation**: All queries filtered by `workspace_id`; workspace ID is immutable

### Validation Strategy
- **Schema Validation**: Pydantic field validators for basic checks (length, format)
- **Business Validation**: `CategorySerializer` handles:
  - Name uniqueness
  - Parent existence and workspace match
  - Circular relationship detection
  - Depth calculation and max depth enforcement
- **Authorization**: `WorkspaceAuthorizationMixin` handles workspace membership checks

## 10. Observability

### Structured Logging
- **Format**: JSON (via `logging_utils.py`)
- **Key Fields**:
  - `timestamp`: ISO8601
  - `level`: DEBUG/INFO/WARNING/ERROR
  - `service`: "category_service"
  - `category`: "api" / "business" / "database" / "security"
  - `operation`: Specific operation (e.g., "category_create_start")
  - `user_id`: User performing action
  - `workspace_id`: Workspace context
  - `resource_id`: Category ID
  - `request_id`: Correlation ID (via middleware)
  - `duration_ms`: Operation duration
  - `status_code`: HTTP response code
- **Log Locations**: Docker JSON logs → Promtail → Loki

### Metrics to Measure
- **RPS** (Requests Per Second):
  - Total requests
  - By endpoint (`/categories/`, `/categories/from-mcc`, etc.)
  - By status code (2xx, 4xx, 5xx)
- **Latency**:
  - P50, P95, P99 response time
  - By endpoint
  - Database query latency
  - External service call latency (workspace_service, subscription_service)
- **Error Rate**:
  - 4xx errors (client errors): validation failures, not found
  - 5xx errors (server errors): unexpected exceptions
  - By error code (CATEGORY_NOT_FOUND, CATEGORY_LIMIT_EXCEEDED, etc.)
- **Business Metrics**:
  - Categories created per minute
  - MCC category creation rate
  - Batch creation usage
  - Average categories per user
  - Hierarchy depth distribution
- **Dependency Metrics**:
  - workspace_service call success/failure rate
  - subscription_service call success/failure rate
  - Timeout frequency
- **Database Metrics**:
  - Connection pool usage
  - Query execution time
  - Transaction rollback rate

### Tracing & Correlation
- **Request ID**: UUID generated by middleware, propagated in logs
- **Structured Context**: All logs include user_id, workspace_id, operation
- **Log Levels**:
  - `INFO`: Business operations start/success
  - `ERROR`: Failures, validation errors, dependency failures
  - `DEBUG`: Detailed internal state (serializer validation steps)

### Dashboards (Assumption)
- **Service Health**: Status codes, error rates, RPS (Grafana)
- **Business Metrics**: Category creation trends, MCC usage
- **Performance**: Latency histograms, slow queries

## 11. Boundaries & Constraints

### Limits
- **Pagination**: 1-100 items per page (default 50)
- **Batch Size**: 1-50 categories per batch MCC creation
- **Hierarchy Depth**: Max 2 levels (root → level 1 → level 2)
- **Name Length**: 3-100 characters
- **MCC Code Range**: 1-9999
- **Category Count**: Enforced by subscription plan (varies by user)

### GDPR/PII
- **PII Fields**: None directly stored
- **User Association**: `user_id` (integer, not personally identifiable alone)
- **Data Deletion**: Categories should be deleted when user account is deleted (handled by user_service cascade)
- **Assumption**: No right-to-be-forgotten logic implemented; would require soft deletes or workspace purge

### Edge Cases

#### Concurrent Updates
- **Scenario**: Two requests try to create categories with same name for same user simultaneously
- **Behavior**: One succeeds, other fails with `CATEGORY_NAME_CONFLICT` (race condition possible)
- **Mitigation**: *Assumption*: Database unique constraint could be added; currently relies on application-level check

#### Retries
- **Scenario**: Client retries category creation after timeout
- **Behavior**: Duplicate category created (not idempotent)
- **Mitigation**: Client should check for existing category by name before retry

#### Partial Failures (Batch Creation)
- **Scenario**: Batch of 10 MCC categories, 3 succeed, 7 fail (limit exceeded)
- **Behavior**: Returns 201 with detailed results per MCC code
- **Mitigation**: Frontend should handle partial success (retry failed only)

#### Orphaned Categories on Workspace Delete
- **Scenario**: Workspace is deleted, categories remain
- **Behavior**: *Assumption*: Currently orphaned; no cascade delete
- **Mitigation**: workspace_service should call internal endpoint to delete all categories on workspace deletion

#### Parent Category Deletion
- **Scenario**: User deletes parent category without deleting children first
- **Behavior**: Blocked with error `CATEGORY_HAS_CHILDREN`
- **Mitigation**: Frontend must delete children first or show cascade delete warning

## 12. Testing

### Unit Tests
**Coverage**: Services, serializers, validation logic

**What to Cover**:
- `CategoryService`:
  - Create category with valid/invalid data
  - Name uniqueness validation
  - Parent validation (existence, same workspace)
  - Circular relationship detection
  - Depth limit enforcement
  - MCC category creation (name resolution, duplicate prevention)
- `CategorySerializer`:
  - Field validation (name length, trimming)
  - Complex validation logic (circular deps, depth calculation)
- `WorkspaceAuthorizationMixin`:
  - Authorization checks with mocked workspace_client
- Exception handling and error code correctness

### Integration Tests
**Coverage**: API endpoints with real database

**What to Cover**:
- Full CRUD lifecycle (create → read → update → delete)
- Hierarchical queries (root categories with children)
- Pagination (edge cases: empty, single page, multiple pages)
- MCC category creation with translations
- Batch creation (all succeed, partial failure, all fail)
- Internal API endpoints with correct headers
- Error responses (404, 400, 403)

**Mocked Dependencies**:
- `workspace_service`: Mock authorization responses (httpx mock)
- `subscription_service`: Mock feature limits (httpx mock)

**Real Dependencies**:
- PostgreSQL: Use test database or testcontainers
- Redis: Not used currently

### Contract Tests
**Assumption**: Not implemented yet

**Recommended**:
- Pact tests with expense_service for `/internal/categories/{id}` contract
- Pact tests with pdf_parser_service for batch MCC endpoints
- OpenAPI schema validation for public API

## 13. Risks & Future Improvements

### Risks
1. **Race Condition on Name Uniqueness**: Application-level check allows concurrent duplicate creation
   - *Mitigation*: Add unique constraint in DB on (workspace_id, user_id, name, type)

2. **Workspace Service Unavailable**: All operations fail (fail-closed security model)
   - *Mitigation*: Add workspace membership cache with TTL; circuit breaker pattern

3. **Subscription Service Unavailable**: Cannot verify limits, category creation blocked
   - *Mitigation*: Add default fallback limits (e.g., 100 categories for free tier)

4. **No Idempotency**: Duplicate categories on retry
   - *Mitigation*: Add idempotency key support (header + DB table)

5. **MCC Code Data Quality**: Seeded data may be incomplete or incorrect
   - *Mitigation*: Add admin endpoint to update MCC codes; periodic audit

6. **Orphaned Categories on Workspace Delete**: No cascade cleanup
   - *Mitigation*: Add internal endpoint for workspace_service to trigger bulk delete

7. **No Soft Deletes**: Deleted categories cannot be recovered
   - *Mitigation*: Add `deleted_at` column for soft deletes

8. **Circular Dependency Detection Inefficient**: Recursive parent traversal on every update
   - *Mitigation*: Use materialized path or closure table for hierarchy

9. **No Bulk Operations**: Expensive to delete many categories
   - *Mitigation*: Add batch delete endpoint

10. **Performance**: No caching of frequently accessed categories
    - *Mitigation*: Add Redis caching for popular MCC codes and default categories

### Future Improvements
1. **Caching Layer**: Cache MCC codes, default categories, workspace authorizations (Redis)
2. **Audit Log**: Track all category changes (who, what, when) for compliance
3. **Category Icons/Colors**: Add metadata fields for better UX
4. **Category Templates**: Pre-defined category sets for new users
5. **Category Suggestions**: ML-based category suggestions from transaction descriptions
6. **Bulk Import/Export**: CSV import/export for power users
7. **Category Merge**: Merge two categories and reassign transactions
8. **Archive Categories**: Hide unused categories without deletion
9. **Category Rules**: Auto-assign categories based on merchant/description patterns
10. **GraphQL API**: For complex nested queries (hierarchies)

---

**Last Updated**: 2026-01-14  
**Maintainers**: Category Service Team  
**Version**: 1.0.0
