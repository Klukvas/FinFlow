# Payment Service - Scheduler Tasks (TODO)

This document describes tasks that should be implemented in a future scheduler/cron service.

---

## 1. Payment Reconciliation (Lost Webhooks)

**Problem:** Payment went through successfully but webhook didn't arrive (network issues, server downtime, etc.)

**Solution:** Periodic job that checks stale payments with WayForPay API

### Endpoint
```
POST /v1/internal/reconciliation/cron
Header: X-Internal-Token: {INTERNAL_SECRET_TOKEN}
```

### Schedule
- **Frequency:** Every 5-10 minutes
- **What it does:**
  1. Finds payments in `CREATED` or `PENDING` status older than 10 minutes
  2. Calls WayForPay `CHECK_STATUS` API to verify actual status
  3. Updates payment status if changed
  4. Notifies `subscription_service` if payment was successful

### Cron Example
```bash
*/5 * * * * curl -X POST "http://payment_service:8000/v1/internal/reconciliation/cron" \
  -H "X-Internal-Token: $INTERNAL_SECRET_TOKEN" \
  >> /var/log/payment-reconciliation.log 2>&1
```

### Additional Endpoints (for manual use/monitoring)
- `GET /v1/internal/payments/stale?minutes_old=10` - List stale payments
- `POST /v1/internal/reconciliation/run?minutes_old=10&limit=100` - Run with custom params
- `POST /v1/internal/reconciliation/single` - Reconcile specific payment by ID or order_reference

---

## 2. Subscription Expiry Check

**Problem:** Subscriptions expire but status isn't updated automatically (for cleanliness/reporting)

**Note:** The `get_active_subscription()` query already checks `expires_at > now()`, so expired subscriptions won't grant access. This job is for data hygiene and notifications.

**Solution:** Periodic job that checks expired subscriptions

### What to implement
1. Find subscriptions where `expires_at < now()` and `status IN ('active', 'past_due', 'paused', 'canceled')`
2. Update status to `'expired'`
3. Send notification email to user about expired subscription
4. Optionally: downgrade to free plan

### Endpoint to create
```
POST /v1/internal/subscriptions/check-expired
```

### Schedule
- **Frequency:** Every hour or daily

---

## 3. Recurring Payments (Future)

**Problem:** User has recurring subscription, need to charge automatically before expiry

**Solution:** Periodic job that initiates recurring charges

### What to implement
1. Find subscriptions expiring in next 3-7 days
2. Use WayForPay `recToken` (saved from first payment) to charge automatically
3. Extend subscription on successful charge
4. Handle failed charges (retry logic, notifications)

### Prerequisites
- Save `recToken` from WayForPay callback during first payment
- Add `rec_token` field to payments/subscriptions table

### Schedule
- **Frequency:** Daily

---

## 4. Payment Expiry Cleanup

**Problem:** Old payments in `CREATED` status that were never completed

**Solution:** Mark old incomplete payments as expired

### What to implement
1. Find payments in `CREATED` status older than 24-48 hours
2. Mark them as `EXPIRED`
3. Log for analytics

### Schedule
- **Frequency:** Daily

---

## Implementation Notes

When creating the scheduler service:

1. **Use a proper job scheduler** (APScheduler, Celery Beat, or external like AWS EventBridge)
2. **Add distributed locking** to prevent duplicate runs (Redis lock)
3. **Add monitoring/alerting** for failed jobs
4. **Log all actions** for audit trail
5. **Make jobs idempotent** - safe to run multiple times

### Example Scheduler Service Structure
```
scheduler_service/
├── app/
│   ├── jobs/
│   │   ├── payment_reconciliation.py
│   │   ├── subscription_expiry.py
│   │   ├── recurring_payments.py
│   │   └── payment_cleanup.py
│   ├── config.py
│   └── main.py
├── Dockerfile
└── requirements.txt
```
