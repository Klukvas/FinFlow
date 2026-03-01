# Operations Runbook

## Infrastructure Overview

- **App Server** (Hetzner cpx31): 4 vCPU, 8 GB RAM, 160 GB NVMe -- all microservices + Redis + Caddy
- **DB Server** (Hetzner cx22): 2 vCPU, 4 GB RAM, 40 GB NVMe -- PostgreSQL 15
- **Private Network**: 10.10.0.0/16 (app=10.10.0.2, db=10.10.0.3)
- **Estimated Cost**: ~19 EUR/month

## Deployment

### Automatic (CI/CD)

Push to `main` branch triggers the CI/CD pipeline:
1. Detects changed services via `git diff`
2. Runs unit tests for changed services
3. Builds and pushes Docker images to registry
4. Runs E2E tests against full docker-compose
5. Deploys to production via SSH

### Manual

```bash
# Deploy all services
ssh <HZ_USER>@<HZ_HOST>
cd /opt/accounting_app
docker compose pull
docker compose up -d

# Deploy a specific service
docker compose up -d --no-deps <service_name>

# Deploy with rebuild
docker compose up --build -d <service_name>
```

### Rollback

```bash
# Roll back to a specific image tag
docker compose pull <service>:<previous-tag>
docker compose up -d --no-deps <service>

# Emergency: revert to previous state
docker compose down <service>
docker compose up -d <service>
```

## Health Check Endpoints

<!-- AUTO-GENERATED: health-endpoints -->

| Service | Port | Endpoint | Method |
|---------|------|----------|--------|
| user_service | 8001 | `/health` | GET |
| account_service | 8009 | `/health` | GET |
| currency_service | 8010 | `/health` | GET |
| workspace_service | 8012 | `/health` | GET |
| payment_service | 8013 | `/health/live` | GET |
| payment_service | 8013 | `/health/ready` | GET |
| scheduler_service | 8014 | `/health/live` | GET |
| scheduler_service | 8014 | `/health/ready` | GET |
| ai_assistant_service | 8015 | `/health` | GET |
| bank_sync_service | 8016 | `/health` | GET |
| pdf_parser_service | 8007 | `/pdf/health` | GET |

Note: category_service, expense_service, income_service, recurring_service, goals_service, debt_service, and subscription_service do not have health check endpoints configured in docker-compose.

<!-- /AUTO-GENERATED: health-endpoints -->

### Verify All Services

```bash
# Check all containers
docker compose ps

# Quick health check loop
for port in 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010 8012 8013 8014 8015 8016; do
  echo -n "Port $port: "
  curl -sf http://localhost:$port/health && echo "OK" || echo "FAIL"
done

# Subscription service uses port 8080 internally (8011 externally)
curl -sf http://localhost:8011/health && echo "OK" || echo "FAIL"
```

## Common Issues

### Service won't start (unhealthy)

1. Check logs: `docker compose logs <service> --tail 50`
2. Common causes:
   - Database not ready (check `db` container health)
   - Missing environment variable (check `.env.docker`)
   - Dependency service not running (check `depends_on` in docker-compose.yml)
   - Health check using `curl` but curl not installed (use `python -c "import urllib.request; ..."` instead)

### 422 Unprocessable Entity on routes like `/current-month-count`

FastAPI route ordering issue. Parameterized routes (`/{id}`) must come AFTER literal routes (`/current-month-count`). Check the router file and ensure literal paths are defined first.

### 404 after adding new endpoints

The Docker container needs to be rebuilt after code changes:
```bash
docker compose up --build -d <service_name>
```

### Inter-service communication failures (503)

1. Check target service is running: `docker compose ps <target_service>`
2. Verify service URL in source's `.env.docker`
3. Check `INTERNAL_SECRET_TOKEN` matches across services
4. Test connectivity: `docker compose exec <source> python -c "import httpx; print(httpx.get('http://<target>:8000/health').status_code)"`

### Database connection issues

```bash
# Check database container
docker compose ps db
docker compose logs db --tail 20

# Test connection from a service
docker compose exec <service> python -c "from sqlalchemy import create_engine; e=create_engine('postgresql://postgres:postgres@db:5432/<service>_db'); e.connect(); print('OK')"

# List all databases
docker compose exec db psql -U postgres -c '\l'
```

### Redis connection issues

```bash
docker compose exec redis redis-cli ping
# Should return: PONG
```

### Frontend build fails

```bash
cd frontend

# Check TypeScript errors
yarn type-check

# Check ESLint
yarn lint

# Full build
yarn build
```

### Out of disk space

```bash
# Check Docker disk usage
docker system df

# Remove unused images, containers, volumes
docker system prune -a --volumes
```

## Database Operations

### Migrations

Each service with a database uses Alembic for migrations. Migrations run automatically on container startup via `startup.sh`.

```bash
# Run migrations manually
docker compose exec <service> alembic upgrade head

# Check current migration version
docker compose exec <service> alembic current

# Rollback one migration
docker compose exec <service> alembic downgrade -1
```

### Backup

```bash
# Backup all databases
docker compose exec db pg_dumpall -U postgres > backup_$(date +%Y%m%d).sql

# Backup a specific database
docker compose exec db pg_dump -U postgres <database_name> > <database_name>_$(date +%Y%m%d).sql

# Restore
docker compose exec -T db psql -U postgres < backup.sql
```

## Monitoring

### Logs

```bash
# All services
docker compose logs -f --tail 100

# Specific service
docker compose logs -f <service_name> --tail 50

# Filter errors
docker compose logs <service_name> 2>&1 | grep -i error
```

### Resource Usage

```bash
# Container stats
docker stats --no-stream

# Disk usage
docker system df
```

## Service Dependencies

```
user_service          <- (no deps, core auth)
  workspace_service   <- user_service
    category_service  <- workspace_service
    account_service   <- workspace_service, currency_service, user_service
    expense_service   <- category_service, account_service, workspace_service
    income_service    <- category_service, account_service, workspace_service
    debt_service      <- workspace_service
    goals_service     <- workspace_service
    recurring_service <- expense_service, income_service, category_service
    pdf_parser_service <- expense_service, income_service, category_service, account_service
    bank_sync_service  <- expense_service, income_service, category_service, account_service
    ai_assistant_service <- all data services
  subscription_service <- user_service
    payment_service    <- subscription_service
    scheduler_service  <- payment_service, recurring_service
```

## Alerting and Escalation

Currently no automated alerting is configured. Planned workflows (not yet implemented):
- Docker health checks every 6 hours
- Slack notifications on deployment
- Email on failure

Manual monitoring:
1. Check `docker compose ps` for unhealthy containers
2. Review logs for ERROR-level messages
3. Monitor disk usage on both servers
