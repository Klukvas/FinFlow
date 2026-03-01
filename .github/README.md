# GitHub Actions Workflows Documentation

This directory contains a comprehensive CI/CD setup for the accounting application microservices architecture.

## 📋 Table of Contents

- [Overview](#overview)
- [Workflows](#workflows)
- [Composite Actions](#composite-actions)
- [Configuration](#configuration)
- [Usage](#usage)
- [Secrets Required](#secrets-required)

## 🎯 Overview

The CI/CD pipeline is designed to:
- ✅ Automatically test code changes
- 🏗️ Build and push Docker images
- 🚀 Deploy to production/staging
- 🔒 Scan for security vulnerabilities
- 📊 Monitor application performance
- 🧹 Maintain infrastructure health

## Workflows

### Implemented

#### CI/CD Pipeline (`ci-cd.yml`)

**Triggers**: Push to `main`/`develop`, manual dispatch (`workflow_dispatch`)

**Path filters**: Changes to any of 18 services, `shared/`, or `frontend/` trigger selective builds.

**Jobs**:
1. `detect-changes` -- git diff to determine which services changed
2. `unit-tests` -- pytest for category, expense, user, payment, workspace services (on change)
3. `stage1`..`stage18` -- individual Docker build+push per service (conditional on detected changes)
   - `stage14` (admin_panel) -- disabled
   - `stage18` (bank_sync_service) -- disabled (`if: false`, feature not yet production-ready)
4. `e2e-tests` -- full docker-compose up, generates random secrets, runs `tests/e2e/` via pytest-asyncio
5. `deploy` -- uses `.github/actions/deploy` composite action, deploys to Hetzner via SSH (main branch or manual only)

**Services built** (18 total):

| Stage | Service | Port |
|-------|---------|------|
| 1 | frontend | 3000 |
| 2 | user_service | 8001 |
| 3 | category_service | 8002 |
| 4 | expense_service | 8003 |
| 5 | income_service | 8004 |
| 6 | currency_service | 8010 |
| 7 | workspace_service | 8012 |
| 8 | recurring_service | 8005 |
| 9 | goals_service | 8006 |
| 10 | pdf_parser_service | 8007 |
| 11 | debt_service | 8008 |
| 12 | account_service | 8009 |
| 13 | subscription_service | 8011 |
| 14 | admin_panel | -- (disabled) |
| 15 | payment_service | 8013 |
| 16 | scheduler_service | 8014 |
| 17 | ai_assistant_service | 8015 |
| 18 | bank_sync_service | 8016 (disabled) |

### Planned (Not Yet Implemented)

The following workflows are planned but **do not yet have workflow files**:

- **Pull Request Checks** (`pr-checks.yml`) -- Frontend linting, type checking, backend linting, Dockerfile linting
- **Frontend E2E Tests** (`frontend-e2e.yml`) -- Playwright E2E, visual regression, HTML reports
- **Backend Tests** (`backend-tests.yml`) -- Per-service pytest with PostgreSQL/Redis, coverage, Codecov
- **Security Scanning** (`security.yml`) -- Safety, Trivy, CodeQL, TruffleHog, Bandit
- **Manual Deployment** (`manual-deploy.yml`) -- Environment selection, rollback, incident issues
- **Performance Monitoring** (`performance.yml`) -- Lighthouse, bundle size, k6, memory profiling
- **Cleanup and Maintenance** (`cleanup.yml`) -- Artifact cleanup, Docker pruning
- **Database Management** (`database.yml`) -- Backup, migrate, rollback
- **Docker Health Check** (`docker-health.yml`) -- Container health, disk, memory, restarts
- **Notifications** (`notifications.yml`) -- Slack, email, PR comments, release creation
- **Dependabot** (`dependabot.yml`) -- npm, pip, Docker, GitHub Actions weekly updates

## 🔧 Composite Actions

### Build and Push (`build-push`)

Reusable action for building and pushing Docker images to a registry.

**Inputs**:
- `registry`: Container registry URL
- `docker-username`: Registry username
- `docker-password`: Registry password
- `services`: Space-separated list of services
- `platform`: Target platform (default: linux/amd64)

**Features**:
- Multi-service support
- Layer caching
- Multiple image tags (latest, SHA, timestamp)
- Build summary with success/failure tracking
- Progress output

### Deploy (`deploy`)

Reusable action for deploying services via SSH.

**Inputs**:
- `host`: Target host
- `user`: SSH user
- `ssh-private-key`: SSH private key
- `registry`: Container registry
- `image-prefix`: Image namespace
- `db-host`, `db-port`, `db-name`, `db-user`, `db-password`: Database config
- `services`: Services to deploy

**Features**:
- Generates docker-compose.yml on server
- Creates .env file with secrets
- Pulls latest images
- Recreates services
- Health status reporting
- Automatic cleanup

## 🔐 Secrets Required

Configure these secrets in GitHub repository settings:

### Docker Registry
```
REGISTRY                  # Container registry (default: docker.io)
DOCKER_USERNAME          # Registry username
DOCKER_PASSWORD          # Registry password/token
IMAGE_PREFIX             # Image namespace/prefix
```

### Deployment
```
HZ_HOST                  # Target host IP/domain
HZ_USER                  # SSH user (default: root)
HZ_SSH_KEY              # SSH private key
```

### Database
```
DB_HOST                  # Database host
DB_PORT                  # Database port (default: 5432)
DB_NAME                  # Database name
DB_USER                  # Database user
DB_PASSWORD              # Database password
```

### Optional Notifications
```
SLACK_WEBHOOK_URL        # Slack webhook for notifications
MAIL_SERVER             # SMTP server
MAIL_PORT               # SMTP port (default: 587)
MAIL_USERNAME           # Email username
MAIL_PASSWORD           # Email password
NOTIFICATION_EMAIL      # Email for notifications
```

### Optional Monitoring
```
API_URL                 # API URL for performance tests
```

## Usage

### Automatic Deployments

Push to `main` branch to automatically:
1. Detect changed services
2. Run unit tests for changed services
3. Build and push Docker images
4. Run E2E tests
5. Deploy to production via SSH

### Manual Deployments

Use the CI/CD workflow with `workflow_dispatch`:
1. Go to Actions -> CI/CD Pipeline
2. Click "Run workflow"
3. Select environment (`production` or `staging`)
4. (Optional) Specify services to deploy
5. Click "Run workflow"

## Pipeline Flow

```
┌─────────────────┐
│  Push to Main   │
└────────┬────────┘
         │
    ┌────▼──────────┐
    │ Detect Changes│
    └────┬──────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────────┐
│ Tests │ │ Build & Push │
└───┬───┘ └──┬──────────┘
    │         │
    └────┬────┘
         │
    ┌────▼────────┐
    │  E2E Tests  │
    └────┬────────┘
         │
    ┌────▼────────┐
    │   Deploy    │
    └─────────────┘
```

## 🛠️ Customization

### Adding a New Service

1. Ensure service has a Dockerfile
2. Add to `services` list in workflows (if not auto-detected)
3. Add Dependabot configuration if needed
4. Update health checks if needed

### Changing Deployment Target

Update secrets:
- `HZ_HOST`
- `HZ_USER`
- `HZ_SSH_KEY`

### Adding Notifications

Configure optional secrets:
- `SLACK_WEBHOOK_URL` for Slack
- `MAIL_*` secrets for email

## 📝 Best Practices

1. **Always create feature branches** from `develop`
2. **Open pull requests** to trigger automated checks
3. **Wait for tests** to pass before merging
4. **Review security scan results** regularly
5. **Monitor deployment notifications**
6. **Keep dependencies updated** (Dependabot PRs)
7. **Run manual deployments** to staging first
8. **Create database backups** before major changes

## 🐛 Troubleshooting

### Build Failures

Check:
- Dockerfile syntax
- Build context path
- Required build arguments
- Registry credentials

### Deployment Failures

Check:
- SSH connection
- Docker on target host
- Image availability
- Environment variables
- Service dependencies

### Test Failures

Check:
- Database connection
- Test data setup
- Environment variables
- Dependency versions

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Buildx](https://docs.docker.com/buildx/working-with-buildx/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Dependabot](https://docs.github.com/en/code-security/dependabot)

## 🤝 Contributing

When adding or modifying workflows:
1. Test in a feature branch
2. Document changes in this README
3. Update secrets documentation if needed
4. Test with manual workflow runs
5. Monitor first automatic run

## 📧 Support

For issues with workflows:
1. Check workflow logs in Actions tab
2. Review this documentation
3. Check secrets configuration
4. Open an issue with workflow run link

