# GitHub Actions Quick Reference

## 🎯 Quick Start

### For Developers

**Pull Request Workflow**:
1. Create feature branch from `develop`
2. Make changes
3. Push to GitHub
4. Open PR → Automated checks run
5. Fix any issues
6. Merge when green ✅

**What Runs on PR**:
- ✅ Linting (Frontend & Backend)
- ✅ Type checking
- ✅ Unit tests
- ✅ Build verification
- ✅ Dockerfile linting

### For DevOps

**Deployment Flow**:
- `main` branch → Production (automatic)
- Manual deployments → Choose environment

**Manual Deploy**:
```
Actions → Manual Deployment → Run workflow
- Choose environment (production/staging)
- Select services (or leave empty for all)
- Pick image tag (default: latest)
- Toggle migrations (default: true)
```

## 📊 Workflow Matrix

| Workflow | Trigger | Purpose | Duration |
|----------|---------|---------|----------|
| CI/CD Pipeline | Push to main/develop | Full build & deploy | ~10-15 min |
| PR Checks | Pull requests | Quality gates | ~5-8 min |
| Frontend E2E | PR, daily | End-to-end tests | ~10 min |
| Backend Tests | PR, push | Unit & integration | ~8-12 min |
| Security | Weekly, PR | Vulnerability scan | ~15-20 min |
| Performance | Push, daily | Performance tests | ~5-10 min |
| Health Check | Every 6 hours | Monitor services | ~2-3 min |
| Cleanup | Weekly | Maintenance | ~5 min |

## 🔐 Required Secrets

### Essential (Must Configure)
```bash
# Docker Registry
DOCKER_USERNAME=your-username
DOCKER_PASSWORD=your-password

# Deployment
HZ_HOST=your-server-ip
HZ_SSH_KEY=your-private-key

# Database
DB_HOST=db-host
DB_NAME=appdb
DB_USER=appuser
DB_PASSWORD=secure-password
```

### Optional (Nice to Have)
```bash
# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
NOTIFICATION_EMAIL=team@example.com

# Email SMTP
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=notifications@example.com
MAIL_PASSWORD=app-password
```

## 🚀 Common Tasks

### Deploy Specific Services
```
Actions → Manual Deployment
Services: frontend user_service expense_service
```

### Run Database Backup
```
Actions → Database Management
Action: backup
```

### Run Migrations
```
Actions → Database Management
Action: migrate
Service: (leave empty for all)
```

### Check Service Health
```
Actions → Docker Health Check → Run workflow
```

### Create Version Tag
```
Actions → Version and Tag
Version type: patch/minor/major
```

## 🐛 Troubleshooting

### Build Failing?
1. Check Dockerfile syntax
2. Verify registry credentials
3. Review build logs in Actions tab

### Deployment Failing?
1. Check SSH key is valid
2. Verify host is accessible
3. Check Docker is running on host
4. Review deployment logs

### Tests Failing?
1. Run tests locally first
2. Check test database connection
3. Verify environment variables
4. Review test logs

### Health Check Failing?
1. SSH to server and check `docker ps`
2. Check service logs: `docker logs <service>`
3. Verify network connectivity
4. Check disk space: `df -h`

## 📈 Monitoring

### Check Workflow Status
- Go to **Actions** tab
- Filter by workflow name
- Click on run to see details

### View Deployment History
- Go to **Environments** (in repo settings)
- View deployment timeline
- See who deployed what and when

### Check Service Health
- Runs automatically every 6 hours
- Creates GitHub issues on failure
- Check Actions → Docker Health Check

## 🔄 Continuous Updates

### Dependabot
- Runs weekly (Mondays)
- Updates dependencies automatically
- Creates PRs for review
- Merge when tests pass

### Security Scans
- Runs weekly
- Uploads results to Security tab
- Check Security → Code scanning alerts

## 💡 Pro Tips

1. **Use Draft PRs** for work in progress (skips some checks)
2. **Manual deploys** to staging before production
3. **Create backups** before major changes
4. **Monitor notifications** for deployment status
5. **Review Dependabot PRs** weekly
6. **Check health dashboard** regularly

## 🎨 Status Badges

Add to your main README.md:

```markdown
![CI/CD](https://github.com/username/accounting_app/workflows/CI%2FCD%20Pipeline/badge.svg)
![Tests](https://github.com/username/accounting_app/workflows/Backend%20Tests/badge.svg)
![Security](https://github.com/username/accounting_app/workflows/Security%20Scanning/badge.svg)
![Health](https://github.com/username/accounting_app/workflows/Docker%20Health%20Check/badge.svg)
```

## 📞 Getting Help

1. **Check workflow logs** in Actions tab
2. **Review README.md** in `.github/` directory
3. **Search past issues** for similar problems
4. **Create issue** with workflow run link

## 🔄 Workflow Updates

To update workflows:
1. Edit workflow file in `.github/workflows/`
2. Test with manual run
3. Monitor first automatic run
4. Document changes in README

---

**Last Updated**: October 6, 2025  
**Version**: 1.0  
**Maintained by**: DevOps Team

