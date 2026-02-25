# Payment Service

Payment Service is responsible for managing payments through Paddle Billing, handling webhooks, maintaining payment lifecycle, and notifying other services about payment events.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [API Documentation](#api-documentation)
- [Data Model](#data-model)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [Testing](#testing)
- [Observability](#observability)
- [Security](#security)

## Overview

The Payment Service acts as the source of truth for all payment-related data in the system. It:

- Creates payment invoices and generates Paddle checkout URLs
- Receives and validates webhooks from Paddle
- Maintains payment status lifecycle with a state machine
- Notifies subscription_service about successful/failed payments
- Provides idempotent API endpoints
- Tracks all payment events for audit purposes

### Responsibilities (In-Scope)

✅ Payment initiation and checkout URL generation  
✅ Payment status tracking and state management  
✅ Webhook signature verification and processing  
✅ Idempotent callback handling  
✅ Payment event auditing  
✅ Downstream service notifications  
✅ Refund support (optional)

### Not Responsibilities (Out-of-Scope)

❌ User management (handled by user_service)  
❌ Subscription activation logic (handled by subscription_service)  
❌ UI/payment pages (handled by frontend)  
❌ Business rules for access control (handled by subscription_service)

## Architecture

### Service Dependencies

**Outgoing Dependencies:**
- `subscription_service` - Notifies about payment success/failure
- `Paddle API` - External payment provider

**Incoming Dependencies:**
- `frontend/BFF` - Creates payments, views status
- `subscription_service` - May create payments internally
- `Paddle` - Sends webhook callbacks

### Tech Stack

- **Runtime:** Python 3.11 + FastAPI + Uvicorn
- **Database:** PostgreSQL (primary storage)
- **Cache:** Redis (idempotency keys, rate limiting)
- **Payment Provider:** Paddle Billing
- **Observability:** Prometheus metrics, JSON logging

### Layers

```
routers/          # HTTP endpoints (public, internal, webhooks)
  └─ services/    # Business logic
       └─ repositories/  # Database operations
            └─ models/  # SQLAlchemy models
```

## Features

### 1. Payment Creation (Checkout Flow)

**Endpoint:** `POST /v1/payments`

Creates a new payment and returns Paddle checkout URL.

**Flow:**
1. Client provides user_id, amount, currency, purpose (SUBSCRIPTION/ONE_TIME)
2. Service generates unique order_reference
3. Paddle checkout session is created
4. Payment saved with status CREATED
5. Client receives payment_url to redirect user

**Idempotency:** Supported via `Idempotency-Key` header

### 2. Webhook Processing

**Endpoint:** `POST /v1/webhooks/paddle`

Receives callbacks from Paddle when payment status changes.

**Flow:**
1. Paddle sends webhook notification with signature
2. Service verifies signature (Paddle webhook signature verification)
3. Finds payment by order_reference
4. Checks idempotency (prevents duplicate processing)
5. Updates payment status via state machine
6. Creates payment_event for audit
7. Notifies subscription_service if applicable
8. Always returns 200 OK (to prevent infinite retries)

**Idempotency:** Built-in via provider_event_id and payload hash

### 3. Payment Status Query

**Endpoint:** `GET /v1/payments/{payment_id}`

Returns current payment status and history.

**Security:** JWT required, users can only access their own payments

### 4. Internal API

**Endpoints:**
- `POST /v1/internal/payments` - Create payment (service-to-service)
- `GET /v1/internal/payments/{id}` - Get payment details
- `POST /v1/internal/payments/{id}/refund` - Request refund

**Security:** Requires `X-Internal-Token` header

## API Documentation

### Public API (JWT Required)

#### Create Payment

```http
POST /v1/payments
Authorization: Bearer <jwt_token>
Idempotency-Key: unique-key-123
Content-Type: application/json

{
  "user_id": "uuid",
  "workspace_id": "uuid",
  "purpose": "SUBSCRIPTION",
  "plan_code": "pro-monthly",
  "amount": 299.00,
  "currency": "UAH",
  "return_url": "https://example.com/return",
  "metadata": {}
}
```

**Response:**

```json
{
  "payment_id": "uuid",
  "order_reference": "ORDER_1705244400_abc123",
  "provider": "PADDLE",
  "amount": 299.00,
  "currency": "UAH",
  "status": "CREATED",
  "payment_url": "https://checkout.paddle.com/...",
  "created_at": "2026-01-14T12:00:00Z"
}
```

#### Get Payment

```http
GET /v1/payments/{payment_id}
Authorization: Bearer <jwt_token>
```

#### List Payments

```http
GET /v1/payments?limit=50&offset=0
Authorization: Bearer <jwt_token>
```

### Webhooks (Signature Verification)

#### Paddle Webhook

```http
POST /v1/webhooks/paddle
Content-Type: application/json
Paddle-Signature: ts=...;h1=...

{
  "event_id": "evt_01abc...",
  "event_type": "transaction.completed",
  "occurred_at": "2026-01-14T12:00:01Z",
  "data": {
    "id": "txn_01abc...",
    "status": "completed",
    "customer_id": "ctm_01abc...",
    "currency_code": "UAH",
    "details": {
      "totals": {
        "total": "29900",
        "subtotal": "29900"
      }
    },
    "custom_data": {
      "order_reference": "ORDER_123"
    }
  }
}
```

**Response:** Always 200 OK to acknowledge receipt

### Internal API (X-Internal-Token Required)

Same endpoints as public API but without JWT requirement and no user ownership checks.

## Data Model

### Payment Statuses

```
CREATED → PENDING → PAID
              ↓
           FAILED / EXPIRED / CANCELED

PAID → REFUNDED / PARTIALLY_REFUNDED
```

**State Machine Rules:**
- Cannot transition backwards (e.g., PAID → PENDING)
- PAID is terminal for success
- FAILED/EXPIRED/CANCELED are terminal for failure
- REFUNDED requires prior PAID status

### Database Tables

#### payments

Primary payment records.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| provider | ENUM | PADDLE |
| order_reference | VARCHAR(255) | Unique order ID |
| user_id | UUID | Payment owner |
| workspace_id | UUID | Workspace context (nullable) |
| purpose | ENUM | SUBSCRIPTION, ONE_TIME |
| plan_code | VARCHAR(64) | Plan code if subscription |
| amount | NUMERIC(10,2) | Payment amount |
| currency | CHAR(3) | Currency code (UAH, USD, EUR) |
| status | ENUM | Current status |
| provider_payment_url | TEXT | Paddle checkout URL |
| provider_payload | JSONB | Sent to provider |
| provider_response | JSONB | Response from provider |
| paid_at | TIMESTAMP | When paid |
| failed_at | TIMESTAMP | When failed |
| refunded_at | TIMESTAMP | When refunded |
| failure_reason | TEXT | Failure description |
| metadata | JSONB | Flexible additional data |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |

**Indexes:**
- `order_reference` (unique)
- `(user_id, created_at)`
- `(workspace_id, created_at)`
- `(status, created_at)`

#### payment_events

Audit log of all payment-related events.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| payment_id | UUID | Foreign key → payments |
| event_type | ENUM | CREATED, CALLBACK, STATUS_CHANGE, REFUND |
| provider_event_id | VARCHAR(255) | Provider's event ID |
| signature_valid | BOOLEAN | Signature check result |
| payload_raw | JSONB | Raw event data |
| status_before | VARCHAR(64) | Previous status |
| status_after | VARCHAR(64) | New status |
| created_at | TIMESTAMP | Event time |

**Indexes:**
- `(payment_id, created_at)`
- `provider_event_id`

#### idempotency_keys

Idempotency tracking for duplicate request prevention.

| Column | Type | Description |
|--------|------|-------------|
| key | VARCHAR(255) | Primary key, idempotency key |
| scope | VARCHAR(64) | Endpoint/action scope |
| request_hash | VARCHAR(64) | Hash of request body |
| response_body | JSONB | Cached response |
| response_status | VARCHAR(16) | HTTP status |
| expires_at | TIMESTAMP | Expiration time |
| created_at | TIMESTAMP | Creation time |

**Indexes:**
- `expires_at`

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DATABASE_URL | ✅ | - | PostgreSQL connection string |
| REDIS_URL | ⚠️ | redis://localhost:6379/0 | Redis connection (optional) |
| LOG_LEVEL | ❌ | INFO | Logging level |
| JWT_SECRET_KEY | ✅ | - | JWT verification key |
| JWT_ALGORITHM | ❌ | HS256 | JWT algorithm |
| INTERNAL_SECRET_TOKEN | ✅ | - | Internal API token |
| PADDLE_API_KEY | ✅ | - | Paddle API key |
| PADDLE_WEBHOOK_SECRET | ✅ | - | Paddle webhook signature secret |
| PADDLE_ENVIRONMENT | ❌ | sandbox | Paddle environment (sandbox/production) |
| PADDLE_RETURN_URL | ✅ | - | User return URL after payment |
| PADDLE_WEBHOOK_URL | ✅ | - | Webhook callback URL (public) |
| PADDLE_API_URL | ❌ | https://sandbox-api.paddle.com | Paddle API endpoint |
| SERVICE_BASE_URL | ❌ | http://localhost:8000 | This service URL |
| SUBSCRIPTION_SERVICE_URL | ✅ | - | Subscription service URL |
| IDEMPOTENCY_TTL_SECONDS | ❌ | 86400 | Idempotency key TTL (24h) |

### Paddle Configuration

1. Register at [Paddle](https://www.paddle.com)
2. Get API key and webhook secret from Paddle dashboard
3. Configure webhook URL in Paddle notification settings
4. Ensure webhook URL is publicly accessible (use ngrok for local dev)

## Development

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (optional)

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running with Docker Compose

```bash
# Start all services including payment_service
docker-compose up -d payment_service

# View logs
docker-compose logs -f payment_service

# Run migrations
docker-compose exec payment_service alembic upgrade head
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Deployment

### Health Checks

- **Liveness:** `GET /health/live` - Process is running
- **Readiness:** `GET /health/ready` - Can serve traffic (DB connected)

### Docker Build

```bash
docker build -t payment_service:latest -f Dockerfile .
```

### Production Checklist

- [ ] Use production Paddle credentials (not sandbox values)
- [ ] Set strong INTERNAL_SECRET_TOKEN
- [ ] Configure public PADDLE_WEBHOOK_URL (must be HTTPS)
- [ ] Enable database connection pooling
- [ ] Set up Redis for better idempotency
- [ ] Configure log aggregation (Loki/Elasticsearch)
- [ ] Set up Prometheus alerting
- [ ] Implement rate limiting on webhook endpoint
- [ ] Configure IP allowlist for Paddle webhooks (if supported)
- [ ] Set up backup and recovery for payment_db
- [ ] Test webhook signature verification thoroughly
- [ ] Implement outbox pattern for reliable notifications

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

### Manual Testing

Use the included `api.http` file with REST Client extension in VS Code.

## Observability

### Metrics

Prometheus metrics exposed at `/metrics`:

| Metric | Type | Description |
|--------|------|-------------|
| `payments_created_total` | Counter | Total payments created |
| `payment_webhooks_total` | Counter | Total webhooks received (by status) |
| `invalid_signature_total` | Counter | Invalid webhook signatures |
| `payment_status_transitions_total` | Counter | Status transitions (from/to) |
| `payment_creation_latency_seconds` | Histogram | Payment creation latency |
| `webhook_processing_latency_seconds` | Histogram | Webhook processing latency |

### Logging

Structured JSON logs with fields:

- `timestamp` - ISO8601 timestamp
- `level` - Log level (INFO, WARNING, ERROR)
- `logger` - Logger name
- `message` - Log message
- `payment_id` - Payment ID (if applicable)
- `order_reference` - Order reference (if applicable)
- `user_id` - User ID (if applicable)
- `status_from`, `status_to` - Status transitions
- `signature_valid` - Signature validation result
- `latency_ms` - Operation latency

### Tracing

Use `request_id` header for request correlation across services.

## Security

### Webhook Security

1. **Signature Verification** - All webhooks must have valid HMAC signature
2. **Idempotency** - Duplicate webhooks are detected and ignored
3. **IP Allowlist** (optional) - Restrict webhooks to Paddle IPs
4. **Rate Limiting** (recommended) - Prevent webhook flooding

### API Security

1. **JWT Authentication** - Public endpoints require valid JWT token
2. **User Ownership** - Users can only access their own payments
3. **Internal Token** - Internal endpoints require X-Internal-Token header
4. **Idempotency Keys** - Prevent duplicate payment creation

### Data Security

- Never store full card numbers (PCI compliance)
- Store only masked PAN (e.g., "4***1111") from Paddle
- Use HTTPS for all external communication
- Encrypt sensitive configuration (secrets management)

## State Machine

```
┌─────────┐
│ CREATED │
└────┬────┘
     │
     ▼
┌─────────┐
│ PENDING │◄───────┐
└────┬────┘        │
     │             │
     ├─────────────┤
     │             │
     ▼             ▼
┌────────┐    ┌──────────┐
│  PAID  │    │  FAILED  │
└────┬───┘    └──────────┘
     │             │
     │             ▼
     │        ┌──────────┐
     │        │ EXPIRED  │
     │        └──────────┘
     │             │
     │             ▼
     │        ┌──────────┐
     │        │ CANCELED │
     │        └──────────┘
     ▼
┌──────────┐
│ REFUNDED │
└──────────┘
```

## Troubleshooting

### Webhook not received

1. Check PADDLE_WEBHOOK_URL is publicly accessible
2. Verify URL is configured in Paddle notification settings
3. Check webhook logs for delivery attempts
4. Use ngrok for local development

### Invalid signature errors

1. Verify PADDLE_WEBHOOK_SECRET is correct
2. Check signature verification matches Paddle docs
3. Ensure no extra spaces in secret key
4. Review logs for signature_valid=false events

### Payment stuck in PENDING

1. Check Paddle dashboard for payment status
2. Use `GET /v1/payments/{id}` to verify status
3. Consider implementing status polling/verification
4. Check if webhook was received (payment_events table)

### Duplicate payments

1. Verify idempotency keys are being used
2. Check idempotency_keys table for conflicts
3. Ensure unique order_reference generation
4. Review payment_events for duplicate callbacks

## Contributing

1. Follow existing code structure (routers → services → repositories)
2. Add tests for new features
3. Update README for API changes
4. Use type hints (Pydantic models)
5. Log important events with structured data
6. Add Prometheus metrics for new operations

## License

Internal project - All rights reserved

## Support

For issues or questions, contact the platform team.

---

**Version:** 1.0.0  
**Last Updated:** 2026-01-14
