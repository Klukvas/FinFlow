# Payment Service - Quick Start

## 🚀 Quick Start (5 minutes)

### 1. Configure Environment

Edit `docker-compose.yml` and set your WayForPay credentials:

```yaml
payment_service:
  environment:
    WAYFORPAY_MERCHANT_ACCOUNT: "your_real_merchant_account"
    WAYFORPAY_MERCHANT_SECRET_KEY: "your_real_secret_key"
    WAYFORPAY_MERCHANT_DOMAIN: "yourdomain.com"
    WAYFORPAY_CALLBACK_URL: "https://yourdomain.com/v1/webhooks/wayforpay"
```

### 2. Start Services

```bash
# Start payment_service and dependencies
docker-compose up -d payment_service

# Check logs
docker-compose logs -f payment_service

# Verify service is running
curl http://localhost:8013/health/ready
```

### 3. Test Payment Flow

#### Create Payment

```bash
curl -X POST http://localhost:8013/v1/payments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "purpose": "SUBSCRIPTION",
    "plan_code": "basic-monthly",
    "amount": 99.00,
    "currency": "UAH"
  }'
```

**Response:**
```json
{
  "payment_id": "uuid",
  "order_reference": "ORDER_1705244400_abc123",
  "payment_url": "https://secure.wayforpay.com/pay",
  "status": "CREATED"
}
```

#### Redirect user to `payment_url`

User completes payment on WayForPay.

#### WayForPay sends webhook

Your service at `/v1/webhooks/wayforpay` processes the callback automatically.

#### Check Payment Status

```bash
curl http://localhost:8013/v1/payments/{payment_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📚 Key Endpoints

### Public API (JWT required)

- `POST /v1/payments` - Create payment
- `GET /v1/payments/{id}` - Get payment details
- `GET /v1/payments` - List user payments

### Internal API (X-Internal-Token required)

- `POST /v1/internal/payments` - Create payment (service-to-service)
- `POST /v1/internal/payments/{id}/refund` - Request refund

### Webhooks (Signature verified)

- `POST /v1/webhooks/wayforpay` - WayForPay callback

### Health Checks

- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

## 🔑 Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `JWT_SECRET_KEY` | JWT verification key | Same as user_service |
| `INTERNAL_SECRET_TOKEN` | Service-to-service auth | Same across all services |
| `WAYFORPAY_MERCHANT_ACCOUNT` | WayForPay merchant ID | From WayForPay dashboard |
| `WAYFORPAY_MERCHANT_SECRET_KEY` | WayForPay secret key | From WayForPay dashboard |
| `WAYFORPAY_CALLBACK_URL` | Public webhook URL | `https://yourdomain.com/v1/webhooks/wayforpay` |
| `SUBSCRIPTION_SERVICE_URL` | Subscription service URL | `http://subscription_service:8080` |

## 🔐 Security Checklist

- [ ] Use HTTPS for WAYFORPAY_CALLBACK_URL in production
- [ ] Set strong INTERNAL_SECRET_TOKEN (min 32 chars)
- [ ] Never commit real credentials to git
- [ ] Verify JWT_SECRET_KEY matches user_service
- [ ] Test webhook signature verification
- [ ] Configure WayForPay callback URL in their dashboard
- [ ] Enable CORS only for your frontend domains

## 🧪 Testing Webhooks Locally

Since WayForPay can't reach `localhost`, use ngrok:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from ngrok.com

# Expose local service
ngrok http 8013

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Update WAYFORPAY_CALLBACK_URL to: https://abc123.ngrok.io/v1/webhooks/wayforpay
# Configure this URL in WayForPay dashboard
```

## 📊 Database Schema

### Tables

- `payments` - Payment records (source of truth)
- `payment_events` - Audit log of all events
- `idempotency_keys` - Duplicate prevention

### Migrations

```bash
# Run migrations
docker-compose exec payment_service alembic upgrade head

# Create new migration
docker-compose exec payment_service alembic revision --autogenerate -m "description"

# Rollback
docker-compose exec payment_service alembic downgrade -1
```

## 🐛 Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs payment_service

# Common issues:
# - Database not ready: Wait for db healthcheck
# - Port conflict: Check if 8013 is in use
# - Migration failed: Check DATABASE_URL
```

### Webhook not received

1. ✅ Verify WAYFORPAY_CALLBACK_URL is publicly accessible
2. ✅ Check URL is configured in WayForPay dashboard
3. ✅ Use ngrok for local testing
4. ✅ Check payment_service logs for incoming requests

### Invalid signature errors

1. ✅ Verify WAYFORPAY_MERCHANT_SECRET_KEY is correct
2. ✅ No extra spaces in secret key
3. ✅ Check logs for signature_valid=false events

### Payment stuck in PENDING

1. ✅ Check WayForPay dashboard for actual status
2. ✅ Verify webhook was received (check payment_events table)
3. ✅ May need to implement status polling

## 📈 Monitoring

### Prometheus Metrics

- `payments_created_total` - Total payments
- `payment_webhooks_total` - Webhooks received
- `invalid_signature_total` - Security alert!
- `payment_status_transitions_total` - Status changes

Access at: `http://localhost:8013/metrics`

### Logs

```bash
# Follow logs
docker-compose logs -f payment_service

# Search for payment
docker-compose logs payment_service | grep "ORDER_123"

# Check webhook processing
docker-compose logs payment_service | grep "webhook"
```

## 🔗 Related Documentation

- [README.md](./README.md) - Full documentation
- [INTEGRATION.md](./INTEGRATION.md) - Integration guide
- [api.http](./api.http) - API examples

## 🆘 Need Help?

1. Check logs: `docker-compose logs payment_service`
2. Check database: Connect to PostgreSQL and query `payments`, `payment_events`
3. Check WayForPay dashboard for payment status
4. Review [WayForPay API docs](https://wiki.wayforpay.com/)

## 🎯 Next Steps

1. ✅ Get payment_service running locally
2. ✅ Configure real WayForPay credentials
3. ✅ Set up ngrok for webhook testing
4. ✅ Create test payment and complete checkout
5. ✅ Verify subscription activation in subscription_service
6. ✅ Set up monitoring and alerts
7. ✅ Deploy to production with HTTPS

---

**Service URL:** http://localhost:8013  
**Swagger Docs:** http://localhost:8013/docs  
**Health:** http://localhost:8013/health/ready
