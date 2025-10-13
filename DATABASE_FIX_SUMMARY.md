# Database Connection Fix Summary

## Problem Identified

Your services were experiencing PostgreSQL authentication failures because of **hardcoded DATABASE_URL defaults** in the configuration files. When environment variables weren't properly set, the services fell back to these incorrect defaults, causing authentication errors.

## Root Causes

1. **Hardcoded DATABASE_URL with wrong credentials** in multiple services:
   - `goals_service`: `postgresql://postgres:postgres@db:5432/goals_db`
   - `recurring_service`: `postgresql://postgres:password@localhost:5432/recurring_db`
   - `income_service`: `postgresql://postgres:password@localhost:5432/income_db`
   - `account_service`: `postgresql://postgres:postgres@localhost:5433/account_service`
   - `debt_service`: `postgresql://postgres:postgres@localhost:5433/debt_service`

2. **Inconsistent Pydantic configuration**:
   - Some services used `case_sensitive = True` (goals_service)
   - Some used old Pydantic v1 `Config` class instead of `model_config`
   - Inconsistent variable naming (lowercase vs uppercase)

## Changes Made

### 1. Goals Service (`goals_service/app/config.py`)
- ✅ Removed hardcoded DATABASE_URL default
- ✅ Changed from `class Config` to `model_config` (Pydantic v2 style)
- ✅ Set `case_sensitive = False` for better environment variable handling
- ✅ Standardized to uppercase variable names (CORS_ORIGINS, DATABASE_URL, etc.)
- ✅ Added logging configuration

### 2. Recurring Service (`recurring_service/app/config.py`)
- ✅ Removed hardcoded DATABASE_URL default
- ✅ Updated to `model_config` (Pydantic v2 style)
- ✅ Standardized to uppercase variable names
- ✅ Fixed service URLs to use correct container names (expense_service instead of expense-service)
- ✅ Added logging configuration

### 3. Income Service (`income_service/app/config.py`)
- ✅ Removed hardcoded DATABASE_URL default
- ✅ Changed from lowercase to uppercase variable names
- ✅ Updated to `model_config` (Pydantic v2 style)
- ✅ Updated all 11 references across the codebase to use uppercase
- ✅ Added logging configuration

### 4. Account Service (`account_service/app/config.py`)
- ✅ Removed hardcoded DATABASE_URL default
- ✅ Made SECRET_KEY and INTERNAL_SECRET_TOKEN required (no defaults)
- ✅ Changed to uppercase variable names
- ✅ Updated all 15+ references across the codebase
- ✅ Fixed service URLs to use correct container names

### 5. Debt Service (`debt_service/app/config.py`)
- ✅ Removed hardcoded DATABASE_URL default
- ✅ Made SECRET_KEY and INTERNAL_SECRET_TOKEN required (no defaults)
- ✅ Changed to uppercase variable names
- ✅ Updated references in database.py, dependencies.py, and alembic/env.py
- ✅ Added logging configuration

## Next Steps to Deploy the Fix

### 1. **Commit and Push Changes**
```bash
git add .
git commit -m "Fix database configuration: remove hardcoded defaults and standardize config"
git push origin main
```

### 2. **Verify GitHub Secrets**
Ensure these secrets are set correctly in your GitHub repository settings:
- `DB_HOST` - Should be your database server IP (e.g., 10.10.0.3)
- `DB_PORT` - Database port (usually 5432)
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - **VERIFY THIS MATCHES YOUR ACTUAL DATABASE PASSWORD**
- `SECRET_KEY` - JWT secret key
- `INTERNAL_SECRET_TOKEN` - Internal service communication token

### 3. **Rebuild and Redeploy Services**
The GitHub Actions will automatically:
- Build new Docker images with the fixed configuration
- Deploy them to your server
- Restart the services with correct environment variables

Watch the deployment in: **Actions** tab in your GitHub repository

### 4. **Verify Database Server Configuration** (if authentication still fails)
SSH to your database server and verify:

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check PostgreSQL user exists
sudo -u postgres psql -c "\du"

# Verify connection from application server
psql -h 10.10.0.3 -U <DB_USER> -d <DB_NAME>
```

### 5. **Check pg_hba.conf** (if needed)
Ensure the database allows connections from your application server:

```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Should include a line like:
```
host    all    <DB_USER>    <APP_SERVER_IP>/32    md5
```

Then restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 6. **Monitor Deployment**
After deployment, check service logs:

```bash
# SSH to your application server
ssh root@<your-server-ip>

# Check service status
cd ~/app
docker compose ps

# Check logs for any service
docker compose logs goals_service
docker compose logs recurring_service
docker compose logs income_service
docker compose logs account_service
docker compose logs debt_service
```

## Expected Outcome

After these changes and redeployment:
- ✅ Services will **require** DATABASE_URL from environment (no fallback to wrong defaults)
- ✅ All services will use the correct database credentials from GitHub secrets
- ✅ Authentication errors should be resolved
- ✅ Services will start successfully and connect to the database

## Rollback Plan (if needed)

If issues occur, you can rollback to the previous version:
```bash
git revert HEAD
git push origin main
```

## Additional Notes

- **Local Development**: You'll need to create `.env` files for each service with proper DATABASE_URL when developing locally
- **Environment Variables**: All services now use uppercase environment variable names consistently
- **Required Variables**: DATABASE_URL, SECRET_KEY, and INTERNAL_SECRET_TOKEN are now required (will fail fast if missing)

---

**Created:** $(date)
**Services Fixed:** goals_service, recurring_service, income_service, account_service, debt_service

