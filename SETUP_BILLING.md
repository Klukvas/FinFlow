# Paddle Billing Setup Guide

This guide covers everything you need to configure, test, and operate the Paddle Billing integration for subscription payments.

---

## Prerequisites

- **Paddle account** -- create one at [paddle.com](https://www.paddle.com/). Use the sandbox environment for development and testing; switch to production when ready to accept real payments.
- **Paddle API key** -- generate one from the Paddle Dashboard under **Developer Tools > Authentication**.
- **Publicly accessible URL for webhooks** -- Paddle must be able to reach your webhook endpoint over HTTPS. For local development, use [ngrok](https://ngrok.com/) to create a tunnel to your local `payment_service` (port 8013 by default).

---

## Environment Variables

Add the following variables to `payment_service/.env.docker` (or your environment configuration):

```bash
# Paddle API key from Dashboard > Developer Tools > Authentication
PADDLE_API_KEY=pdl_sbox_xxx

# Webhook signing secret from Dashboard > Notifications > notification destination settings
PADDLE_WEBHOOK_SECRET=pdl_ntfset_xxx

# "sandbox" for development/testing, "production" for live payments
PADDLE_ENVIRONMENT=sandbox

# URL the user is redirected to after a successful checkout
PADDLE_SUCCESS_URL=http://localhost:3000/payment/return

# URL the user is redirected to if they cancel the checkout (reserved for future use)
PADDLE_CANCEL_URL=http://localhost:3000/pricing

# Master switch -- set to "true" to enable payment processing
PAYMENTS_ENABLED=true
```

The `payment_service` reads these via the `Settings` class in `payment_service/app/config.py`. When `PAYMENTS_ENABLED` is `false` (the default in `docker-compose.yml`), the `POST /v1/payments` endpoint rejects all requests with a clear error message. This acts as a safety gate until Paddle is fully configured.

---

## Paddle Dashboard Setup

### 1. Create Products

In the Paddle Dashboard, navigate to **Catalog > Products** and create one product per plan:

| Product Name       | Description                             |
|--------------------|-----------------------------------------|
| Professional Plan  | Full-featured plan for individuals      |
| Enterprise Plan    | Advanced plan for teams and businesses  |

### 2. Create Prices

For each product, create one or more recurring prices:

| Product            | Price Name | Billing Period | Amount  | Currency |
|--------------------|------------|----------------|---------|----------|
| Professional Plan  | Monthly    | Monthly        | $9.99   | USD      |
| Professional Plan  | Yearly     | Yearly         | $99.99  | USD      |
| Enterprise Plan    | Monthly    | Monthly        | $29.99  | USD      |
| Enterprise Plan    | Yearly     | Yearly         | $299.99 | USD      |

### 3. Copy Price IDs

After creating prices, Paddle assigns each one an ID in the format `pri_01abc123...`. Copy these IDs -- you will need them for the plan-to-price mapping in the database (see the next section).

### 4. Configure Webhook Notification Destination

Navigate to **Notifications** in the Paddle Dashboard and create a new notification destination:

- **URL**: `https://your-domain/v1/webhooks/paddle`
  - For local development with ngrok: `https://<your-ngrok-subdomain>.ngrok-free.app/v1/webhooks/paddle`
- **Events to subscribe**:
  - `subscription.created`
  - `subscription.activated`
  - `subscription.updated`
  - `subscription.canceled`
  - `subscription.past_due`
  - `subscription.paused`
  - `subscription.resumed`
  - `transaction.completed`
  - `transaction.payment_failed`

### 5. Copy the Webhook Signing Secret

After saving the notification destination, Paddle displays a signing secret (e.g., `pdl_ntfset_xxx`). Copy this value and set it as `PADDLE_WEBHOOK_SECRET` in your environment.

---

## Plan Price Mapping

The `payment_service` resolves which Paddle price to charge by looking up the `paddle_price_map` table in the `payment_db` database. This table is created by the Alembic migration `0003_add_paddle_support`.

### Table Schema

| Column           | Type         | Description                                    |
|------------------|--------------|------------------------------------------------|
| `id`             | `integer`    | Auto-increment primary key                     |
| `plan_code`      | `string(64)` | Unique plan identifier (e.g., `professional`)  |
| `paddle_price_id`| `string(255)`| Paddle price ID (e.g., `pri_01abc123`)         |
| `billing_period` | `string(16)` | `monthly` or `yearly`                          |
| `is_active`      | `boolean`    | Whether this mapping is active                 |
| `created_at`     | `datetime`   | Row creation timestamp                         |
| `updated_at`     | `datetime`   | Row last-updated timestamp                     |

### Seed Data

After running migrations, insert rows for each plan/price combination:

```sql
INSERT INTO paddle_price_map (plan_code, paddle_price_id, billing_period, is_active)
VALUES
  ('professional', 'pri_01abc123', 'monthly', true),
  ('professional_yearly', 'pri_01abc456', 'yearly', true),
  ('enterprise', 'pri_01def789', 'monthly', true),
  ('enterprise_yearly', 'pri_01def012', 'yearly', true);
```

Replace the `pri_01...` values with the real Price IDs from your Paddle Dashboard.

When the frontend sends a `POST /v1/payments` request with `plan_code: "professional"`, the service queries `paddle_price_map` for an active row matching that `plan_code`, retrieves the `paddle_price_id`, and uses it to create a Paddle checkout session.

---

## Testing Locally

### 1. Start Services

```bash
docker-compose up --build
```

The `payment_service` is exposed on **port 8013**. Verify it is running:

```bash
curl http://localhost:8013/health/live
# {"status":"ok"}
```

### 2. Set Up ngrok

Paddle webhooks require a publicly reachable HTTPS endpoint. Use ngrok to tunnel to the local payment service:

```bash
ngrok http 8013
```

ngrok prints a forwarding URL such as `https://a1b2c3d4.ngrok-free.app`. Copy this URL.

### 3. Update Webhook URL in Paddle Dashboard

Go to **Notifications** in the Paddle Dashboard, edit your notification destination, and set the URL to:

```
https://<your-ngrok-subdomain>.ngrok-free.app/v1/webhooks/paddle
```

### 4. Verify Configuration

Call the config check endpoint to verify that all Paddle settings are in place:

```bash
curl http://localhost:8013/v1/config/check
```

Expected response when properly configured:

```json
{
  "status": "ok",
  "checks": {
    "api_key": { "configured": true },
    "webhook_secret": { "configured": true },
    "environment": { "value": "sandbox" },
    "success_url": { "configured": true }
  },
  "production_ready": false
}
```

`production_ready` is `false` because the environment is `sandbox`. This is expected for local testing.

### 5. Use Paddle Sandbox Test Cards

Paddle provides test card numbers for sandbox transactions. Refer to the [Paddle sandbox documentation](https://developer.paddle.com/concepts/payment-methods/credit-debit-card) for the latest test card details. Common test cards:

| Card Number          | Result             |
|----------------------|--------------------|
| `4242 4242 4242 4242`| Successful payment |
| `4000 0000 0000 0002`| Declined payment   |

Use any future expiry date and any 3-digit CVV.

### 6. Test the Full Flow

1. Open the frontend at `http://localhost:3000` and log in.
2. Navigate to the pricing page and click **Upgrade** (or the equivalent plan selection button).
3. The frontend calls `POST /v1/payments` with the selected `plan_code`, `amount`, and `user_id`.
4. The backend resolves the Paddle price from `paddle_price_map`, calls the Paddle API to create a checkout session, and returns a `checkout_url`.
5. The frontend redirects the user to the Paddle-hosted checkout page.
6. Complete the payment with a sandbox test card.
7. Paddle sends a `transaction.completed` webhook to `https://<ngrok>/v1/webhooks/paddle`.
8. The backend verifies the HMAC signature, updates the payment status to `PAID`, and notifies `subscription_service` to activate the subscription.
9. The user is redirected to the success URL (`/payment/return`).

---

## Architecture Overview

```
Frontend (React)                payment_service              Paddle API
      |                               |                          |
      |  POST /v1/payments             |                          |
      |  {plan_code, user_id, ...}    |                          |
      |------------------------------>|                          |
      |                               |  POST /transactions      |
      |                               |  {price_id, custom_data} |
      |                               |------------------------->|
      |                               |  {checkout_url, txn_id}  |
      |                               |<-------------------------|
      |  {checkout_url}               |                          |
      |<------------------------------|                          |
      |                               |                          |
      |  redirect to checkout_url     |                          |
      |------------------------------------------------------>  |
      |                               |                          |
      |       (user completes checkout on Paddle)                |
      |                               |                          |
      |                               |  POST /v1/webhooks/paddle|
      |                               |  (transaction.completed) |
      |                               |<-------------------------|
      |                               |                          |
      |                               |  verify HMAC signature   |
      |                               |  update payment -> PAID  |
      |                               |  notify subscription_svc |
      |                               |                          |

subscription_service                  |
      |  POST /v1/internal/            |
      |    subscriptions/activate      |
      |<------------------------------|
      |  activates subscription        |
      |  with Paddle IDs              |
```

### Key Design Decisions

1. **Paddle-hosted checkout** -- the user is redirected to Paddle's checkout page rather than using an embedded or custom form. This offloads PCI compliance and payment UI to Paddle.

2. **Webhook-driven status updates** -- payment and subscription statuses are always updated via verified Paddle webhooks, never from the frontend. The `Paddle-Signature` header is verified using HMAC-SHA256 before any state change.

3. **Idempotent webhook processing** -- every webhook event is recorded in the `processed_webhook_events` table by `event_id`. Duplicate deliveries are silently ignored.

4. **Always 200 OK on webhooks** -- the webhook endpoint always returns HTTP 200 to prevent Paddle from retrying indefinitely. Errors are logged for investigation.

5. **Paddle manages recurring billing** -- there is no internal scheduler for payment retries or renewals. Paddle handles all recurring charge attempts and notifies the application via subscription lifecycle webhooks.

6. **Service-to-service communication** -- when a payment succeeds, the `payment_service` notifies `subscription_service` via an authenticated internal HTTP call (`POST /v1/internal/subscriptions/activate`) carrying the Paddle customer ID, subscription ID, and price ID.

---

## Webhook Events Handled

The webhook endpoint is `POST /v1/webhooks/paddle` (defined in `payment_service/app/routers/webhooks.py`). The event routing logic lives in `payment_service/app/services/payment_service.py`.

| Paddle Event                  | Action Taken                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| `transaction.completed`       | Payment status set to `PAID`. Paddle IDs stored on payment record. `subscription_service` notified to activate the subscription. |
| `transaction.payment_failed`  | Payment status set to `FAILED`. Failure reason extracted from Paddle error code. `subscription_service` notified about the failure. |
| `subscription.created`        | Logged as an audit event on the associated payment record. No status change. |
| `subscription.activated`      | `subscription_service` notified with event type `activated`.                |
| `subscription.updated`        | Logged as an audit event on the associated payment record. No status change. |
| `subscription.canceled`       | `subscription_service` notified with event type `canceled` and the effective cancellation date. Auto-renew disabled on the subscription. |
| `subscription.past_due`       | `subscription_service` notified with event type `past_due`.                 |
| `subscription.paused`         | `subscription_service` notified with event type `paused`.                   |
| `subscription.resumed`        | `subscription_service` notified with event type `resumed`.                  |

---

## API Endpoints Reference

All endpoints are prefixed with `/v1` and served on port 8000 inside the container (mapped to 8013 on the host).

### Payment Endpoints (require JWT authentication)

| Method | Path                                     | Description                        |
|--------|------------------------------------------|------------------------------------|
| POST   | `/v1/payments`                           | Create a payment (Paddle checkout) |
| GET    | `/v1/payments`                           | List current user's payments       |
| GET    | `/v1/payments/{payment_id}`              | Get payment by ID                  |
| GET    | `/v1/payments/by-order/{order_reference}`| Get payment by order reference     |

### Configuration Endpoints (no authentication)

| Method | Path                | Description                                    |
|--------|---------------------|------------------------------------------------|
| GET    | `/v1/config/status` | Payment feature flag and service status         |
| GET    | `/v1/config/check`  | Paddle configuration diagnostics (no secrets)   |

### Webhook Endpoint (authenticated via Paddle signature)

| Method | Path                   | Description                     |
|--------|------------------------|---------------------------------|
| POST   | `/v1/webhooks/paddle`  | Paddle webhook receiver         |

### Health Endpoints (no authentication)

| Method | Path              | Description                          |
|--------|-------------------|--------------------------------------|
| GET    | `/health/live`    | Liveness probe (process is alive)    |
| GET    | `/health/ready`   | Readiness probe (database reachable) |

---

## Database Tables

The Paddle integration adds the following tables to the `payment_db` database (via Alembic migration `0003_add_paddle_support`):

### `paddle_price_map`

Maps plan codes to Paddle price IDs. Queried during payment creation.

### `processed_webhook_events`

Stores the `event_id` of every processed webhook for idempotency. Prevents duplicate processing when Paddle retries a delivery.

### Columns added to `payments`

| Column                    | Type          | Purpose                                    |
|---------------------------|---------------|--------------------------------------------|
| `paddle_customer_id`      | `string(255)` | Paddle customer ID (`ctm_...`)             |
| `paddle_subscription_id`  | `string(255)` | Paddle subscription ID (`sub_...`)         |
| `paddle_transaction_id`   | `string(255)` | Paddle transaction ID (`txn_...`)          |

The `subscription_service` also stores Paddle IDs on its `subscriptions` table (via migration `0011_add_paddle_fields`): `paddle_customer_id`, `paddle_subscription_id`, and `paddle_price_id`.

---

## Troubleshooting

### Webhook signature verification fails

- Confirm that `PADDLE_WEBHOOK_SECRET` matches the signing secret shown in the Paddle Dashboard notification destination settings. The secret starts with `pdl_ntfset_`.
- Ensure the raw request body is not modified before signature verification. The webhook endpoint reads `request.body()` before any JSON parsing.

### Webhooks not arriving

- Verify ngrok is running and forwarding to port 8013: `ngrok http 8013`.
- Confirm the URL in the Paddle Dashboard notification destination matches the ngrok URL exactly, including the path `/v1/webhooks/paddle`.
- Check the Paddle Dashboard **Notifications > Events** log for delivery attempts and HTTP response codes.
- Check payment service logs: `docker-compose logs payment_service`.

### Payment creation returns "PAYMENTS_DISABLED"

- Set `PAYMENTS_ENABLED=true` in `payment_service/.env.docker` or in the `docker-compose.yml` environment section.
- Restart the service: `docker-compose restart payment_service`.

### Payment creation returns "PRICE_NOT_CONFIGURED"

- Verify that the `paddle_price_map` table contains an active row for the requested `plan_code`.
- Connect to the database and check:
  ```bash
  docker-compose exec db psql -U postgres -d payment_db -c "SELECT * FROM paddle_price_map;"
  ```

### Paddle API returns an error during checkout creation

- Check that `PADDLE_API_KEY` is set and valid for the current environment (sandbox key for sandbox, live key for production).
- Call the config check endpoint: `curl http://localhost:8013/v1/config/check`.
- Review the payment service logs for detailed Paddle API error messages:
  ```bash
  docker-compose logs payment_service | grep "Paddle API error"
  ```

### Subscription not activated after successful payment

- Check that the `subscription_service` is running and reachable from `payment_service`.
- Verify `SUBSCRIPTION_SERVICE_URL` is set correctly (default: `http://subscription_service:8080`).
- Look for notification errors in the logs:
  ```bash
  docker-compose logs payment_service | grep "Failed to notify subscription_service"
  ```

### Checking overall system health

```bash
# Payment service liveness
curl http://localhost:8013/health/live

# Payment service readiness (includes DB check)
curl http://localhost:8013/health/ready

# Paddle configuration status
curl http://localhost:8013/v1/config/check

# Payment feature flag
curl http://localhost:8013/v1/config/status
```

---

## Going to Production

1. Create a production Paddle account (or switch your existing account to live mode).
2. Generate a production API key and webhook signing secret.
3. Update environment variables:
   ```bash
   PADDLE_API_KEY=pdl_live_xxx
   PADDLE_WEBHOOK_SECRET=pdl_ntfset_xxx
   PADDLE_ENVIRONMENT=production
   PADDLE_SUCCESS_URL=https://your-domain.com/payment/return
   PAYMENTS_ENABLED=true
   ```
4. Set up the webhook notification destination in the Paddle production dashboard pointing to your production URL: `https://your-domain.com/v1/webhooks/paddle`.
5. Seed the `paddle_price_map` table with production Price IDs.
6. Run the config check to verify: `curl https://your-domain.com/v1/config/check` -- `production_ready` should be `true`.
7. Perform a real test transaction to verify the full end-to-end flow.
