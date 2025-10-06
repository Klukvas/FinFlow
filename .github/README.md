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

## 📦 Workflows

### 1. CI/CD Pipeline (`ci-cd.yml`)

**Triggers**: Push to main/develop, manual dispatch

**Features**:
- Detects changed services automatically
- Builds only modified services
- Runs tests before deployment
- Deploys to production on main branch
- Supports manual service selection

**Stages**:
1. Detect changed services
2. Build frontend (with linting and type checking)
3. Test backend services (with coverage)
4. Build and push Docker images
5. Deploy to target environment

### 2. Pull Request Checks (`pr-checks.yml`)

**Triggers**: Pull requests to main/develop

**Checks**:
- Frontend linting (ESLint)
- Frontend type checking (TypeScript)
- Frontend build verification
- Backend linting (Ruff, Black, Mypy)
- Backend tests with coverage
- Dockerfile linting (Hadolint)

### 3. Frontend E2E Tests (`frontend-e2e.yml`)

**Triggers**: PRs, daily schedule, manual

**Features**:
- Playwright end-to-end tests
- Visual regression testing
- Automatic browser installation
- Test result artifacts
- HTML reports

### 4. Backend Tests (`backend-tests.yml`)

**Triggers**: PRs, push to main, manual

**Features**:
- PostgreSQL and Redis test services
- Per-service test execution
- Code coverage reports
- Integration tests
- Codecov integration

### 5. Security Scanning (`security.yml`)

**Triggers**: Push to main, PRs, weekly schedule

**Scans**:
- Python dependency scanning (Safety)
- Frontend dependency audit (Yarn)
- Container vulnerability scanning (Trivy)
- Code security analysis (CodeQL)
- Secret scanning (TruffleHog)
- Python security scan (Bandit)

### 6. Manual Deployment (`manual-deploy.yml`)

**Triggers**: Manual dispatch only

**Features**:
- Select target environment (production/staging/development)
- Deploy specific services or all
- Choose image tag
- Skip build option
- Run migrations option
- Automatic rollback on failure
- Create incident issues

### 7. Performance Monitoring (`performance.yml`)

**Triggers**: Push to main, PRs, daily schedule

**Tests**:
- Lighthouse performance audit
- Bundle size analysis
- API performance tests (k6)
- Memory profiling

### 8. Security Scanning (`security.yml`)

**Triggers**: Weekly schedule, PRs, manual

**Features**:
- Dependency vulnerability scanning
- Container image scanning
- Code quality analysis
- Secret detection

### 9. Cleanup and Maintenance (`cleanup.yml`)

**Triggers**: Weekly schedule, manual

**Actions**:
- Remove old workflow artifacts
- Delete old workflow runs
- Prune unused Docker images
- Clean volumes and networks

### 10. Database Management (`database.yml`)

**Triggers**: Manual dispatch only

**Actions**:
- Database backup
- Run migrations
- Rollback migrations
- Restore from backup (manual)

### 11. Docker Health Check (`docker-health.yml`)

**Triggers**: Every 6 hours, manual

**Checks**:
- Running containers status
- Container health status
- Disk usage
- Error logs
- Restart counts
- Memory usage
- Frontend availability

### 12. Notifications (`notifications.yml`)

**Triggers**: After CI/CD or manual deployment completes

**Features**:
- Deployment status notifications
- PR comments with deployment status
- Slack notifications (optional)
- Email notifications on failure
- Automatic release creation

### 13. Dependabot Configuration (`dependabot.yml`)

**Updates**:
- Frontend npm packages (weekly)
- Python packages for all services (weekly)
- Docker base images (weekly)
- GitHub Actions (weekly)

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

## 🚀 Usage

### Automatic Deployments

Push to `main` branch to automatically:
1. Run tests
2. Build changed services
3. Deploy to production

### Manual Deployments

Use the "Manual Deployment" workflow:
1. Go to Actions → Manual Deployment
2. Click "Run workflow"
3. Select environment
4. (Optional) Specify services
5. (Optional) Choose image tag
6. Click "Run workflow"

### Running Tests

Tests run automatically on pull requests. To run manually:
1. Go to Actions → Backend Tests or Frontend E2E Tests
2. Click "Run workflow"

### Database Operations

Use the "Database Management" workflow:
1. Go to Actions → Database Management
2. Click "Run workflow"
3. Select action (backup, migrate, rollback)
4. Provide required parameters
5. Click "Run workflow"

### Health Checks

Health checks run automatically every 6 hours. To run manually:
1. Go to Actions → Docker Health Check
2. Click "Run workflow"

## 📊 Workflow Status Badges

Add these to your README.md:

```markdown
![CI/CD Pipeline](https://github.com/YOUR_USERNAME/accounting_app/workflows/CI%2FCD%20Pipeline/badge.svg)
![Security Scanning](https://github.com/YOUR_USERNAME/accounting_app/workflows/Security%20Scanning/badge.svg)
![Tests](https://github.com/YOUR_USERNAME/accounting_app/workflows/Backend%20Tests/badge.svg)
```

## 🔄 Workflow Dependencies

```
┌─────────────────┐
│   Pull Request  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│  Lint │ │  Tests  │
└───┬───┘ └──┬──────┘
    │         │
    └────┬────┘
         │
    ┌────▼────────┐
    │   Summary   │
    └─────────────┘

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
┌───▼───┐ ┌──▼──────┐
│ Build │ │  Tests  │
└───┬───┘ └──┬──────┘
    │         │
    └────┬────┘
         │
    ┌────▼────────┐
    │Build & Push │
    └────┬────────┘
         │
    ┌────▼────────┐
    │   Deploy    │
    └────┬────────┘
         │
    ┌────▼────────┐
    │   Notify    │
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

