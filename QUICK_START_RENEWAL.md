# Quick Start: Subscription Auto-Renewal

This guide will help you get the subscription auto-renewal system up and running.

## Prerequisites

- Docker & Docker Compose installed
- PostgreSQL and Redis running (via docker-compose)

## Step 1: Start All Services

```bash
# Start the entire stack including the new scheduler_service
docker-compose up -d
```

This will start:
- All existing services (user, payment, subscription, etc.)
- **NEW:** scheduler_service (runs on port 8014)

## Step 2: Run Database Migrations

Run migrations for the three affected services:

```bash
# Scheduler service (creates job tracking tables)
docker-compose exec scheduler_service alembic upgrade head

# Payment service (adds recurring_token field)
docker-compose exec payment_service alembic upgrade head

# Subscription service (adds renewal fields)
docker-compose exec subscription_service alembic upgrade head
```

## Step 3: Verify Scheduler is Running

```bash
# Check health
curl http://localhost:8014/health/ready

# Expected response:
# {"status": "ready"}

# List scheduled jobs
curl http://localhost:8014/scheduler/jobs

# Expected response:
# {
#   "jobs": [
#     {
#       "id": "subscription_renewal",
#       "name": "Subscription Renewal Job",
#       "next_run_time": "2026-01-20T15:00:00+00:00",
#       "trigger": "cron[hour='*/1']"
#     }
#   ]
# }
```

## Step 4: Create a Test Subscription with Recurring Token

For auto-renewal to work, subscriptions need a `recurring_token`. This token is obtained from WayForPay during the initial payment.

### Option A: Using Real WayForPay (Production-like)

1. Configure WayForPay credentials in `docker-compose.yml` (payment_service section)
2. Create a payment via payment_service
3. Complete the payment on WayForPay's checkout page
4. WayForPay will return a `recToken` in the callback
5. Payment service stores this token
6. Subscription service receives the token and stores it in the subscription

### Option B: Manual Database Insert (Testing)

For testing purposes, you can manually insert a recurring token:

```sql
-- Connect to subscription_db
psql -h localhost -p 5433 -U postgres -d subscription_db

-- Update an existing subscription with a test token
UPDATE subscriptions
SET 
  recurring_token = 'test_recurring_token_12345',
  payment_provider = 'WAYFORPAY',
  auto_renew = true,
  next_billing_date = NOW() + INTERVAL '1 hour',
  expires_at = NOW() + INTERVAL '1 hour'
WHERE user_id = 'YOUR_USER_ID';
```

**Note:** This test token won't work for real charges, but you can test the job execution flow.

## Step 5: Manually Trigger Renewal Job (Testing)

To test the renewal job without waiting for the cron schedule:

```bash
curl -X POST http://localhost:8014/scheduler/jobs/subscription_renewal/trigger
```

## Step 6: Monitor Job Execution

### View Logs

```bash
# Real-time logs
docker-compose logs -f scheduler_service

# Filter for renewal events
docker-compose logs scheduler_service | grep renewal
```

### Check Metrics

```bash
# View all metrics
curl http://localhost:8014/metrics

# Filter renewal metrics
curl http://localhost:8014/metrics | grep renewals

# Example metrics:
# scheduler_renewals_attempted_total{status="success"} 5
# scheduler_renewals_attempted_total{status="failed"} 1
# scheduler_renewals_payment_failed_total{reason="insufficient_funds"} 1
```

### Query Database

```bash
# View job executions
docker-compose exec db psql -U postgres -d scheduler_db -c \
  "SELECT id, job_name, status, items_processed, items_succeeded, items_failed, created_at 
   FROM job_executions 
   ORDER BY created_at DESC 
   LIMIT 10;"

# View renewal attempts
docker-compose exec db psql -U postgres -d scheduler_db -c \
  "SELECT id, subscription_id, user_id, amount, status, failure_reason, created_at 
   FROM renewal_attempts 
   ORDER BY created_at DESC 
   LIMIT 10;"
```

## Step 7: Verify Subscription Extension

After a successful renewal:

```bash
# Check subscription was extended
docker-compose exec db psql -U postgres -d subscription_db -c \
  "SELECT id, user_id, plan_code, status, expires_at, last_payment_id, auto_renew 
   FROM subscriptions 
   WHERE user_id = 'YOUR_USER_ID';"
```

You should see:
- `expires_at` extended by the plan's billing period (e.g., +30 days)
- `last_payment_id` updated with the new payment ID
- `status` remains `active`

## Troubleshooting

### Scheduler Not Starting

**Check logs:**
```bash
docker-compose logs scheduler_service
```

**Common issues:**
- Database migration not run: Run `alembic upgrade head`
- Database connection failed: Check `DATABASE_URL` in docker-compose.yml
- Service dependencies not ready: Wait for db and redis to be healthy

### Jobs Not Running

**Check scheduler status:**
```bash
curl http://localhost:8014/scheduler/jobs
```

**Manually trigger:**
```bash
curl -X POST http://localhost:8014/scheduler/jobs/subscription_renewal/trigger
```

### Renewals Skipped

**Check logs for reason:**
```bash
docker-compose logs scheduler_service | grep "SKIPPED"
```

**Common reasons:**
- `no_recurring_token`: Subscription doesn't have a payment token
- `invalid_amount`: Plan amount is 0 or negative
- `not_active`: Subscription status is not "active"
- `auto_renew_disabled`: Subscription has auto_renew = false

### Payment Failures

**Check renewal_attempts table:**
```bash
docker-compose exec db psql -U postgres -d scheduler_db -c \
  "SELECT * FROM renewal_attempts WHERE status = 'FAILED' ORDER BY created_at DESC LIMIT 5;"
```

**Common failure reasons:**
- WayForPay API errors
- Invalid recurring token
- Insufficient funds
- Card expired

## Configuration

### Change Renewal Schedule

Edit `docker-compose.yml`:

```yaml
scheduler_service:
  environment:
    # Run every 6 hours instead of every 1 hour
    RENEWAL_CHECK_CRON: "0 */6 * * *"
```

Restart scheduler:
```bash
docker-compose restart scheduler_service
```

### Change Renewal Window

Edit `docker-compose.yml`:

```yaml
scheduler_service:
  environment:
    # Check subscriptions expiring within 3 days
    RENEWAL_WINDOW_DAYS: "3"
```

## Monitoring in Production

### Grafana Dashboards

View scheduler metrics in Grafana:
```
http://localhost:3001
Username: admin
Password: admin123
```

### Prometheus Alerts

Set up alerts for:
- Job not running for > 2 hours
- High failure rate (> 20%)
- Long execution duration (> 10 minutes)

### Log Aggregation

All scheduler logs are sent to Loki and can be queried in Grafana:

```
{service="scheduler_service"} |= "renewal"
```

## Next Steps

1. ✅ Verify scheduler is running
2. ✅ Test with a real subscription + payment
3. ✅ Monitor metrics and logs
4. ✅ Set up alerts in production
5. ✅ Configure appropriate cron schedule
6. ✅ Test failure scenarios
7. ✅ Implement user notifications for failed renewals (future)

## Summary

The subscription auto-renewal system is now operational! The scheduler will:

- Run every hour (configurable)
- Check for subscriptions expiring within 1 day (configurable)
- Automatically charge users via stored payment tokens
- Extend subscriptions on successful payment
- Mark subscriptions as past_due on failure
- Track all attempts in the database
- Expose metrics for monitoring

For detailed documentation, see:
- `/scheduler_service/README.md` - Comprehensive service documentation
- `/IMPLEMENTATION_SUMMARY.md` - Full implementation details
