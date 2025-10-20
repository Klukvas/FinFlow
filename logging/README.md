# Accounting App Logging Infrastructure

This directory contains the complete logging infrastructure for the Accounting App, using Grafana, Loki, and Promtail for centralized log collection, storage, and visualization.

## Architecture

```
Services → Docker Logs → Promtail → Loki → Grafana
```

- **Promtail**: Log collector that scrapes Docker container logs and forwards them to Loki
- **Loki**: Log aggregation system that stores and indexes logs
- **Grafana**: Visualization platform that displays logs and metrics

## Components

### 1. Promtail Configuration
- **File**: `promtail-config-working.yml`
- **Purpose**: Collects logs from Docker containers and parses structured JSON logs
- **Features**:
  - Automatic container discovery
  - JSON log parsing for application services
  - Label extraction for filtering and querying
  - Support for various log formats

### 2. Loki Configuration
- **File**: `loki-config.yml`
- **Purpose**: Stores and indexes logs from Promtail
- **Features**:
  - 30-day log retention
  - Efficient compression and storage
  - Query optimization
  - Multi-tenant support (disabled for simplicity)

### 3. Grafana Configuration
- **Files**: 
  - `grafana-datasources.yml`: Auto-configures Loki as a data source
  - `grafana-dashboards.yml`: Auto-loads dashboards
- **Features**:
  - Automatic datasource configuration
  - Pre-built dashboards for service monitoring
  - Real-time log visualization

### 4. Dashboards
- **Service Overview**: High-level service health and performance metrics
- **Service Health**: Detailed service monitoring and error tracking
- **Performance**: API response times and throughput metrics
- **Business Metrics**: Business operation tracking and analytics

## Quick Start

### 1. Start the Logging Infrastructure

```bash
# Start all services including logging infrastructure
docker-compose up -d

# Or start just the logging services
docker-compose up -d loki promtail grafana
```

### 2. Access Grafana

- **URL**: http://localhost:3001
- **Username**: admin
- **Password**: admin123

### 3. View Logs

1. Open Grafana dashboard
2. Navigate to "Dashboards" → "Accounting App" → "Service Overview"
3. Verify that logs are flowing from your services

## Service Logging

All services are configured to output structured JSON logs with the following format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "user_service",
  "message": "API request: GET /api/users",
  "category": "api",
  "operation": "api_request",
  "method": "GET",
  "endpoint": "/api/users",
  "status_code": 200,
  "duration_ms": 150,
  "user_id": 123,
  "request_id": "uuid-here",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

## Log Categories

The logging system supports the following categories:

- **api**: API request/response logs
- **business**: Business operation logs
- **authentication**: Authentication and authorization logs
- **database**: Database operation logs
- **external_service**: External service call logs
- **security**: Security-related events
- **frontend**: Frontend application logs

## Querying Logs

### Basic Queries

```logql
# All logs from a specific service
{service="user_service"}

# Error logs across all services
{level="ERROR"}

# API logs with specific status codes
{category="api"} | json | status_code="200"

# Business operations for a specific user
{category="business"} | json | user_id="123"
```

### Advanced Queries

```logql
# Error rate by service
rate({level="ERROR"}[5m]) by (service)

# API response time percentiles
histogram_quantile(0.95, rate({category="api"} | json | unwrap duration_ms [5m]) by (service, le))

# Most active users
topk(10, sum by (user_id) (rate({user_id!=""}[5m])))
```

## Testing the Logging Pipeline

Use the provided test script to verify the logging infrastructure:

```bash
# Run the test script
python3 logging/test-logging.py
```

This will generate test logs for all services and scenarios.

## Troubleshooting

### No Logs Appearing in Grafana

1. **Check Promtail Status**:
   ```bash
   docker logs promtail
   ```

2. **Check Loki Status**:
   ```bash
   docker logs loki
   ```

3. **Verify Service Logs**:
   ```bash
   docker logs user_service
   ```

4. **Check Network Connectivity**:
   ```bash
   docker network ls
   docker network inspect accounting_app_logging
   ```

### Common Issues

1. **Services not on logging network**: Ensure all services have `networks: - logging` in docker-compose.yml
2. **Promtail not collecting logs**: Check that containers have the `logging=promtail` label
3. **JSON parsing errors**: Verify services are outputting valid JSON logs
4. **Permission issues**: Ensure Promtail has access to `/var/lib/docker/containers`

## Monitoring and Alerting

### Health Checks

All logging components have health checks configured:

- **Loki**: `http://localhost:3100/ready`
- **Promtail**: `http://localhost:9080/ready`
- **Grafana**: `http://localhost:3000/api/health`

### Alerting (Optional)

To set up alerting, configure alert rules in `grafana-alerting.yml` and enable the alerting module in Grafana.

## Performance Considerations

- **Log Retention**: Default 30 days, configurable in `loki-config.yml`
- **Log Volume**: Monitor disk usage for Loki storage
- **Query Performance**: Use label filters for better query performance
- **Resource Usage**: Adjust resource limits based on log volume

## Security

- **Authentication**: Grafana admin password should be changed in production
- **Network**: Logging network is isolated from external access
- **Data**: Logs may contain sensitive information - ensure proper access controls

## Maintenance

### Log Rotation

Logs are automatically rotated by Docker with the following settings:
- Max size: 10MB per file
- Max files: 3 per container

### Backup

To backup logs:

```bash
# Backup Loki data
docker run --rm -v accounting_app_loki_data:/data -v $(pwd):/backup alpine tar czf /backup/loki-backup.tar.gz -C /data .

# Restore Loki data
docker run --rm -v accounting_app_loki_data:/data -v $(pwd):/backup alpine tar xzf /backup/loki-backup.tar.gz -C /data
```

## Support

For issues with the logging infrastructure:

1. Check the troubleshooting section above
2. Review container logs for errors
3. Verify network connectivity between components
4. Check Grafana datasource configuration
5. Ensure all services are properly labeled for log collection