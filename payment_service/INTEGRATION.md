# Payment Service Integration Guide

## Overview

This document describes how `payment_service` integrates with other services in the system, particularly `subscription_service`.

## Architecture

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ 1. Create Payment (JWT)
       ▼
┌─────────────────┐
│ payment_service │
└────┬─────┬──────┘
     │     │
     │     │ 4. Notify success/failure (X-Internal-Token)
     │     ▼
     │  ┌─────────────────────┐
     │  │ subscription_service│
     │  └─────────────────────┘
     │
     │ 2. Payment form
     ▼
┌─────────────┐
│  WayForPay  │
└──────┬──────┘
       │ 3. Webhook (signature)
       ▼
┌─────────────────┐
│ payment_service │
└─────────────────┘
```

## Flow 1: Payment Creation

### 1. Frontend → payment_service

**Request:**
```http
POST /v1/payments
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "user_id": "uuid",
  "purpose": "SUBSCRIPTION",
  "plan_code": "pro-monthly",
  "amount": 299.00,
  "currency": "UAH"
}
```

**Response:**
```json
{
  "payment_id": "uuid",
  "payment_url": "https://secure.wayforpay.com/pay",
  "status": "CREATED"
}
```

### 2. Frontend redirects user to `payment_url`

User completes payment on WayForPay checkout page.

## Flow 2: Webhook Processing

### 3. WayForPay → payment_service

**Request:**
```http
POST /v1/webhooks/wayforpay
Content-Type: application/json

{
  "merchantAccount": "merchant",
  "orderReference": "ORDER_123",
  "merchantSignature": "signature",
  "transactionStatus": "Approved",
  "amount": 299.00,
  "currency": "UAH"
}
```

**Processing:**
1. Verify signature (HMAC SHA1)
2. Find payment by orderReference
3. Check idempotency (prevent duplicates)
4. Update payment status to PAID
5. Create payment_event for audit
6. Notify subscription_service (see Flow 3)

**Response:** Always 200 OK

```json
{
  "orderReference": "ORDER_123",
  "status": "accept",
  "time": 1705244400
}
```

## Flow 3: Subscription Activation

### 4. payment_service → subscription_service

**Request:**
```http
POST /v1/internal/subscriptions/activate
X-Internal-Token: my-secret-token
Content-Type: application/json

{
  "payment_id": "uuid",
  "user_id": "uuid",
  "workspace_id": "uuid",
  "plan_code": "pro-monthly",
  "amount": "299.00",
  "currency": "UAH"
}
```

**Processing (subscription_service):**
1. Verify internal token
2. Find plan by plan_code
3. Check if user has existing subscription
   - If yes: Extend expires_at by plan.period_days
   - If no: Create new subscription with expires_at = now + plan.period_days
4. Set status to "active"

**Response:**
```json
{
  "status": "success",
  "message": "Subscription activated",
  "payment_id": "uuid"
}
```

## Flow 4: Payment Failure

### payment_service → subscription_service

**Request:**
```http
POST /v1/internal/subscriptions/payment-failed
X-Internal-Token: my-secret-token
Content-Type: application/json

{
  "payment_id": "uuid",
  "user_id": "uuid",
  "plan_code": "pro-monthly",
  "reason": "Insufficient funds"
}
```

**Response:**
```json
{
  "status": "acknowledged",
  "message": "Payment failure recorded",
  "payment_id": "uuid"
}
```

## Security

### JWT Authentication (Public API)

- Used for: Frontend → payment_service
- Header: `Authorization: Bearer <token>`
- Contains: user_id, email, workspace_id
- Verified with: JWT_SECRET_KEY

### Internal Token (Service-to-Service)

- Used for: payment_service → subscription_service
- Header: `X-Internal-Token: <token>`
- Shared secret: INTERNAL_SECRET_TOKEN
- Must match on both services

### WayForPay Signature

- Used for: WayForPay → payment_service
- Algorithm: HMAC-MD5
- Fields: merchantAccount, orderReference, amount, currency, authCode, cardPan, transactionStatus, reasonCode
- Verified with: WAYFORPAY_MERCHANT_SECRET_KEY

## Data Flow

### Payment States

```
CREATED → PENDING → PAID → [subscription activated]
              ↓
           FAILED → [notification sent]
```

### Idempotency

**Payment Creation:**
- Use `Idempotency-Key` header
- Stored in `idempotency_keys` table
- TTL: 24 hours

**Webhook Processing:**
- Check by `provider_event_id` or payload hash
- Prevents duplicate callbacks
- Stored in `payment_events` table

## Error Handling

### payment_service → subscription_service Fails

**Options:**

1. **Immediate Retry** (current implementation)
   - Try notification 1-3 times
   - Log error if all attempts fail

2. **Outbox Pattern** (recommended for production)
   - Store notification in outbox table
   - Background worker retries periodically
   - Guarantees eventual delivery

3. **Event Queue** (advanced)
   - Publish to RabbitMQ/Kafka
   - subscription_service consumes from queue
   - Built-in retry and DLQ

### Implementation Priority

For production, implement outbox pattern:

```sql
CREATE TABLE payment_outbox (
  id UUID PRIMARY KEY,
  payment_id UUID,
  event_type VARCHAR(64),
  payload JSONB,
  status VARCHAR(32),  -- PENDING, SENT, FAILED
  retry_count INT,
  next_retry_at TIMESTAMP,
  created_at TIMESTAMP
);
```

## Configuration

### payment_service

```env
SUBSCRIPTION_SERVICE_URL=http://subscription_service:8080
INTERNAL_SECRET_TOKEN=my-secret-token
```

### subscription_service

```env
INTERNAL_SECRET_TOKEN=my-secret-token
```

**⚠️ Important:** INTERNAL_SECRET_TOKEN must match on both services!

## Testing

### Test Payment Flow (Development)

1. Start services:
```bash
docker-compose up payment_service subscription_service
```

2. Create payment:
```bash
curl -X POST http://localhost:8013/v1/payments \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "purpose": "SUBSCRIPTION",
    "plan_code": "basic-monthly",
    "amount": 99.00,
    "currency": "UAH"
  }'
```

3. Simulate webhook (use real signature in production):
```bash
curl -X POST http://localhost:8013/v1/webhooks/wayforpay \
  -H "Content-Type: application/json" \
  -d '{
    "merchantAccount": "test_merchant",
    "orderReference": "ORDER_...",
    "merchantSignature": "...",
    "transactionStatus": "Approved",
    "amount": 99.00,
    "currency": "UAH"
  }'
```

4. Check subscription:
```bash
curl http://localhost:8011/v1/subscriptions/{user_id} \
  -H "Authorization: Bearer <jwt>"
```

## Monitoring

### Key Metrics

**payment_service:**
- `payments_created_total` - Total payments created
- `payment_webhooks_total{status="Approved"}` - Successful webhooks
- `invalid_signature_total` - Invalid signatures (security alert!)
- `payment_status_transitions_total` - Status changes

**subscription_service:**
- `subscription_changes_total` - Subscription activations

### Alerts

1. **High invalid_signature_total**
   - Could indicate attack or misconfiguration
   - Check WAYFORPAY_MERCHANT_SECRET_KEY

2. **Webhook processing failures**
   - Check payment_service logs
   - Verify WayForPay callback URL is accessible

3. **Subscription activation failures**
   - Check subscription_service logs
   - Verify INTERNAL_SECRET_TOKEN matches

## Troubleshooting

### Payment stuck in PENDING

**Possible causes:**
- Webhook not received
- Webhook signature invalid
- Callback URL not accessible

**Debug:**
1. Check WayForPay dashboard
2. Verify callback URL in WayForPay settings
3. Check payment_service logs for webhook errors
4. Use ngrok for local development

### Subscription not activated after payment

**Possible causes:**
- subscription_service down
- INTERNAL_SECRET_TOKEN mismatch
- Plan code not found

**Debug:**
1. Check payment_events table for callbacks
2. Check payment_service logs for notification errors
3. Check subscription_service logs
4. Verify plan_code exists in plans table

## Future Improvements

1. **Outbox Pattern** - Reliable event delivery
2. **Webhook Retry Logic** - WayForPay side retries
3. **Payment Status Polling** - Periodic status checks
4. **Partial Refunds** - Support for partial amount refunds
5. **Multiple Payment Providers** - Add Stripe, PayPal, etc.
6. **Recurring Payments** - Subscription auto-renewal
7. **Payment Links** - Generate shareable payment links
8. **Promo Codes** - Discount and coupon support

## References

- [WayForPay API Documentation](https://wiki.wayforpay.com/)
- [Payment Service README](./README.md)
- [Subscription Service README](../subscription_service/README.md)
