# Scheduler Service

The **Scheduler Service** is a background job execution service responsible for running scheduled tasks, primarily subscription auto-renewals.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Jobs](#jobs)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Security](#security)

## Overview

The Scheduler Service provides automated background job execution for time-based tasks that don't require user interaction. The primary use case is **subscription auto-renewal**, where the service automatically charges users at subscription expiration.

### Key Responsibilities

✅ Execute subscription renewal jobs on schedule  
✅ Retry failed renewals with exponential backoff  
✅ Track job execution history and metrics  
✅ Coordinate with payment_service and subscription_service  
✅ Provide observability via metrics and structured logging  

### Out of Scope

❌ Business logic for subscriptions or payments  
❌ Direct payment provider integration  
❌ User notifications (handled by other services)  
❌ Manual payment retry UI  

## Features

### 1. Subscription Auto-Renewal

Automatically renews active subscriptions when they reach expiration:

**Process:**
1. Query subscriptions expiring within renewal window (default: 1 day)
2. Validate subscription has recurring payment token
3. Create recurring payment via payment_service
4. On success: Extend subscription by billing period
5. On failure: Mark subscription as past_due

**Idempotency:** Jobs use execution tracking to prevent duplicate processing.

**Error Handling:** Failed renewals are logged with detailed reason codes for investigation.

### 2. Job Execution Tracking

All job runs are persisted to database with:
- Execution status (PENDING, RUNNING, SUCCESS, FAILED)
- Start/end timestamps
- Items processed/succeeded/failed counts
- Error messages and details
- Execution metadata

### 3. Observability

**Metrics** (Prometheus format at `/metrics`):
- `scheduler_job_executions_total{job_name, status}`
- `scheduler_job_execution_duration_seconds{job_name}`
- `scheduler_job_items_processed_total{job_name, status}`
- `scheduler_renewals_attempted_total{status}`
- `scheduler_renewals_payment_failed_total{reason}`
- `scheduler_active_jobs`

**Structured Logging** (JSON):
- Job start/completion events
- Individual renewal attempts
- Payment success/failure
- Service errors with full context

## Architecture

### Service Dependencies

**Outgoing:**
- `subscription_service` - Get expiring subscriptions, update status
- `payment_service` - Create recurring payments

**Incoming:**
- None (scheduler is autonomous, no inbound API calls except admin/monitoring)

### Tech Stack

- **Runtime:** Python 3.11 + FastAPI + Uvicorn
- **Scheduler:** APScheduler (AsyncIOScheduler)
- **Database:** PostgreSQL (job execution tracking)
- **Cache:** Redis (optional, for distributed locking)
- **Observability:** Prometheus metrics, JSON logging

### Layers

```
app/
├── jobs/               # Job implementations
│   └── subscription_renewal_job.py
├── services/           # (reserved for future use)
├── repositories/       # Database operations
│   └── job_repository.py
├── clients/            # Service-to-service clients
│   ├── subscription_client.py
│   └── payment_client.py
├── models/             # SQLAlchemy models
│   └── models.py       # JobExecution, RenewalAttempt
├── utils/              # Utilities
│   ├── logging.py      # Structured logging setup
│   └── metrics.py      # Prometheus metrics
├── config.py           # Configuration management
├── database.py         # Database setup
└── main.py             # FastAPI app + scheduler
```

## Jobs

### Subscription Renewal Job

**Job ID:** `subscription_renewal`  
**Trigger:** Cron (default: `0 */1 * * *` - every hour)  
**Idempotency:** Single instance (max_instances=1)  

**Configuration:**
- `RENEWAL_CHECK_CRON` - Cron expression
- `RENEWAL_WINDOW_DAYS` - Days ahead to check (default: 1)
- `JOB_MAX_INSTANCES` - Max concurrent instances (default: 1)
- `JOB_COALESCE` - Merge missed runs (default: true)
- `JOB_MISFIRE_GRACE_TIME` - Grace time for late runs (seconds, default: 300)

**Process Flow:**

```
1. Job starts → Create JobExecution record
2. Query subscription_service for expiring subscriptions
3. For each subscription:
   a. Validate recurring_token exists
   b. Call payment_service to create recurring payment
   c. If payment succeeds:
      - Extend subscription via subscription_service
      - Record RenewalAttempt (SUCCESS)
   d. If payment fails:
      - Mark subscription as past_due
      - Record RenewalAttempt (FAILED)
   e. If exception occurs:
      - Log error
      - Record RenewalAttempt (FAILED)
4. Update JobExecution with final stats
5. Record metrics
```

## API Documentation

### Health Checks

#### Liveness Probe

```http
GET /health/live
```

Returns 200 if process is running.

#### Readiness Probe

```http
GET /health/ready
```

Returns 200 if scheduler is initialized and running.

### Admin Endpoints

#### List Scheduled Jobs

```http
GET /scheduler/jobs
```

**Response:**

```json
{
  "jobs": [
    {
      "id": "subscription_renewal",
      "name": "Subscription Renewal Job",
      "next_run_time": "2026-01-20T15:00:00+00:00",
      "trigger": "cron[hour='*/1']"
    }
  ]
}
```

#### Manually Trigger Job

```http
POST /scheduler/jobs/{job_id}/trigger
```

**Example:**

```http
POST /scheduler/jobs/subscription_renewal/trigger
```

**Response:**

```json
{
  "status": "triggered",
  "job_id": "subscription_renewal"
}
```

### Metrics

```http
GET /metrics
```

Returns Prometheus-formatted metrics.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | - | PostgreSQL connection string |
| `REDIS_URL` | ❌ | redis://localhost:6379/0 | Redis connection (optional) |
| `LOG_LEVEL` | ❌ | INFO | Logging level |
| `INTERNAL_SECRET_TOKEN` | ✅ | - | Internal API authentication |
| `SUBSCRIPTION_SERVICE_URL` | ✅ | http://localhost:8080 | Subscription service URL |
| `PAYMENT_SERVICE_URL` | ✅ | http://localhost:8000 | Payment service URL |
| `SCHEDULER_TIMEZONE` | ❌ | UTC | Timezone for scheduler |
| `RENEWAL_CHECK_CRON` | ❌ | 0 */1 * * * | Cron expression for renewal job |
| `RENEWAL_WINDOW_DAYS` | ❌ | 1 | Days ahead to check for expiring subscriptions |
| `MAX_RETRY_ATTEMPTS` | ❌ | 3 | Max retry attempts for failed operations |
| `RETRY_DELAY_SECONDS` | ❌ | 300 | Delay between retries (seconds) |
| `JOB_MAX_INSTANCES` | ❌ | 1 | Max concurrent job instances |
| `JOB_COALESCE` | ❌ | true | Merge missed runs |
| `JOB_MISFIRE_GRACE_TIME` | ❌ | 300 | Grace time for late runs (seconds) |

### Cron Expression Examples

| Expression | Description |
|------------|-------------|
| `0 */1 * * *` | Every hour |
| `0 */6 * * *` | Every 6 hours |
| `0 0 * * *` | Daily at midnight |
| `0 2 * * *` | Daily at 2 AM |
| `*/30 * * * *` | Every 30 minutes |

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
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/scheduler_db"
export REDIS_URL="redis://localhost:6379/0"
export INTERNAL_SECRET_TOKEN="my-secret-token"
export SUBSCRIPTION_SERVICE_URL="http://localhost:8080"
export PAYMENT_SERVICE_URL="http://localhost:8000"

# Run migrations
alembic upgrade head

# Start service
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
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

### Testing Job Manually

```bash
# Trigger job via API
curl -X POST http://localhost:8090/scheduler/jobs/subscription_renewal/trigger

# Check job status
curl http://localhost:8090/scheduler/jobs

# View metrics
curl http://localhost:8090/metrics
```

## Deployment

### Docker

```bash
# Build image
docker build -t scheduler_service:latest -f Dockerfile .

# Run container
docker run -d \
  --name scheduler_service \
  -p 8090:8090 \
  -e DATABASE_URL="postgresql://..." \
  -e SUBSCRIPTION_SERVICE_URL="http://subscription_service:8080" \
  -e PAYMENT_SERVICE_URL="http://payment_service:8000" \
  scheduler_service:latest
```

### Docker Compose

```bash
# Start scheduler_service
docker-compose up -d scheduler_service

# View logs
docker-compose logs -f scheduler_service

# Restart
docker-compose restart scheduler_service
```

### Production Checklist

- [ ] Set strong `INTERNAL_SECRET_TOKEN`
- [ ] Configure appropriate `RENEWAL_CHECK_CRON` (avoid peak hours)
- [ ] Set `RENEWAL_WINDOW_DAYS` based on business needs
- [ ] Enable database connection pooling
- [ ] Configure log aggregation (Loki/Elasticsearch)
- [ ] Set up Prometheus alerting for job failures
- [ ] Monitor `scheduler_renewals_payment_failed_total` metric
- [ ] Implement dead-letter queue for persistent failures (future)
- [ ] Configure database backups
- [ ] Test job execution during deployment

## Monitoring

### Key Metrics to Monitor

1. **Job Execution Rate**
   - `scheduler_job_executions_total{job_name="subscription_renewal", status="success"}`
   - Alert if no successful runs in 2 hours

2. **Renewal Success Rate**
   - `scheduler_renewals_attempted_total{status="success"} / scheduler_renewals_attempted_total`
   - Alert if success rate < 90%

3. **Payment Failures**
   - `scheduler_renewals_payment_failed_total{reason=*}`
   - Alert if high failure rate for specific reason

4. **Job Duration**
   - `scheduler_job_execution_duration_seconds{job_name="subscription_renewal"}`
   - Alert if duration > 10 minutes

### Logs to Monitor

- **Error Level:** Job failures, payment errors, service communication failures
- **Warning Level:** Skipped renewals (no token, invalid amount)
- **Info Level:** Job start/completion, renewal attempts

### Recommended Alerts

```yaml
# Example Prometheus alert rules
groups:
  - name: scheduler_service
    rules:
      - alert: SchedulerJobNotRunning
        expr: time() - scheduler_job_executions_total{status="success"} > 7200
        annotations:
          summary: "Scheduler job not running"
          
      - alert: HighRenewalFailureRate
        expr: rate(scheduler_renewals_attempted_total{status="failed"}[1h]) / rate(scheduler_renewals_attempted_total[1h]) > 0.2
        annotations:
          summary: "High renewal failure rate (>20%)"
          
      - alert: SchedulerJobDurationHigh
        expr: scheduler_job_execution_duration_seconds > 600
        annotations:
          summary: "Scheduler job duration > 10 minutes"
```

## Security

### Internal Service Authentication

- All calls to subscription_service and payment_service use `X-Internal-Token` header
- Token must match `INTERNAL_SECRET_TOKEN` environment variable
- Use strong, randomly generated tokens in production

### Database Security

- Scheduler has read/write access to `scheduler_db` only
- Does not store sensitive payment data (tokens remain in subscription_service)
- Job execution logs contain user_id but no PII

### Network Security

- Scheduler is internal-only service (no public-facing endpoints)
- Only admin/monitoring endpoints exposed (`/health/*`, `/metrics`, `/scheduler/jobs`)
- Use firewall rules to restrict access to admin endpoints

## Troubleshooting

### Job Not Running

**Symptoms:** No job executions in database, no metrics

**Check:**
1. Scheduler started: `GET /health/ready`
2. View jobs: `GET /scheduler/jobs`
3. Check logs for scheduler initialization errors
4. Verify cron expression is valid

### Renewals Failing

**Symptoms:** High failure rate, subscriptions not extended

**Check:**
1. View metrics: `GET /metrics | grep renewals_payment_failed`
2. Query `renewal_attempts` table for failure reasons
3. Verify payment_service is healthy
4. Check Paddle credentials and API status
5. Verify subscriptions have valid recurring_token

### Missing Recurring Token

**Symptoms:** Renewals skipped with reason "no_recurring_token"

**Cause:** Initial payment did not store recurring token

**Solution:**
1. Ensure payment_service stores `recurring_token` from Paddle
2. Ensure subscription_service persists token when payment succeeds
3. Re-process initial payment or ask user to re-subscribe

### Service Communication Failures

**Symptoms:** Errors in logs, renewals marked as FAILED

**Check:**
1. Verify `SUBSCRIPTION_SERVICE_URL` and `PAYMENT_SERVICE_URL` are correct
2. Verify services are running and healthy
3. Check `INTERNAL_SECRET_TOKEN` matches across services
4. Review network connectivity between services

## Future Enhancements

- [ ] Dead-letter queue for persistent renewal failures
- [ ] User notification on failed renewal (via notification_service)
- [ ] Grace period / dunning logic (retry X times before canceling)
- [ ] Support for multiple billing periods (yearly subscriptions)
- [ ] Manual retry API for failed renewals
- [ ] Distributed locking with Redis for multi-instance deployment
- [ ] Proration logic for mid-cycle plan changes
- [ ] Support for multiple payment providers

## License

Internal project - All rights reserved

## Support

For issues or questions, contact the platform team.

---

**Version:** 1.0.0  
**Last Updated:** 2026-01-20
