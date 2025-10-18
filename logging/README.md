# Logging Configuration

This directory contains all configuration files for the centralized logging infrastructure using Loki, Promtail, and Grafana.

## 🚀 Quick Start

### Start Monitoring Services
```bash
# Start just the logging infrastructure
docker-compose up -d loki promtail grafana

# Or start all services including logging
docker-compose up -d
```

### Access Grafana
- **URL**: http://localhost:3001
- **Username**: admin
- **Password**: admin123

### Access Loki
- **URL**: http://localhost:3100

## 📁 Files Overview

### Core Configuration
- **`loki-config.yml`** - Loki server configuration
- **`promtail-config.yml`** - Promtail log agent configuration
- **`grafana-datasources.yml`** - Grafana data source configuration
- **`grafana-dashboards.yml`** - Dashboard provisioning
- **`grafana-alerting.yml`** - Alerting configuration

### Dashboards
- **`dashboards/service-health.json`** - Service health monitoring
- **`dashboards/business-metrics.json`** - Business metrics and KPIs
- **`dashboards/performance.json`** - Performance monitoring

### Utilities
- **`logging_utils.py`** - Enhanced Python logging utilities
- **`log_enrichment.py`** - Log enrichment and correlation service
- **`log-parsing-rules.yml`** - Advanced log parsing rules
- **`monitoring-config.yml`** - Comprehensive monitoring configuration

## 📊 Available Dashboards

1. **Service Health Dashboard**
   - Service status overview
   - Error rates by service
   - Log volume trends
   - Recent errors

2. **Business Metrics Dashboard**
   - User registrations
   - Expense transactions
   - Authentication events
   - API usage by endpoint

3. **Performance Monitoring Dashboard**
   - API response times
   - Database query performance
   - Request rate by service
   - Error rate trends

## 🔍 Useful Log Queries

```logql
# All logs from a specific service
{service="user_service"}

# Error logs only
{level="ERROR"}

# API requests with response time >1s
{service=~".*"} | json | event_type="api_request" | duration_ms > 1000

# Authentication failures
{service="user_service"} | json | event_type="auth_failure"

# Business events by user
{service=~".*"} | json | category="business" | user_id="123"
```

## 🔧 Configuration

### Environment Variables
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
SERVICE_NAME=your_service_name
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

### Docker Compose
The logging services are automatically configured in the main `docker-compose.yml` files:
- **Development**: `docker-compose.yml`
- **Production**: `deploy/docker-compose.yml`

## 📚 Documentation

- **Quick Start**: See `LOGGING_QUICK_START.md` in the project root
- **Migration Guide**: See `MIGRATION_GUIDE.md` in the project root
- **Monitoring Guide**: See `MONITORING_GUIDE.md` in the project root

## 🛠️ Troubleshooting

### Check Service Status
```bash
docker-compose ps
```

### View Service Logs
```bash
docker-compose logs loki
docker-compose logs promtail
docker-compose logs grafana
```

### Restart Services
```bash
docker-compose restart loki promtail grafana
```

### Check Health
```bash
curl http://localhost:3100/ready  # Loki
curl http://localhost:9080/ready  # Promtail
curl http://localhost:3001/api/health  # Grafana
```