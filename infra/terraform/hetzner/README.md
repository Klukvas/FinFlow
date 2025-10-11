# Terraform for Hetzner Cloud - Accounting App Infrastructure

## Architecture Overview

This Terraform configuration creates a production-ready infrastructure on Hetzner Cloud with:

- **Application Server** (1 server): Runs all microservices via Docker Compose
  - All backend services (user, category, expense, income, etc.)
  - Frontend (React/TypeScript)
  - Redis (caching)
  - Caddy (reverse proxy with automatic HTTPS)
  
- **Database Server** (1 server): Dedicated PostgreSQL instance
  - Configured to listen only on private network
  - Accessible only from application server via private network

- **Private Network**: 10.10.0.0/16 CIDR for secure communication
  - App Server: 10.10.0.2
  - DB Server: 10.10.0.3

- **Firewalls**:
  - App Server: SSH (22), HTTP (80), HTTPS (443)
  - DB Server: SSH (22 for maintenance), PostgreSQL (5432 from private network only)

## Prerequisites

- Terraform >= 1.5
- Hetzner Cloud account with API token
- SSH key already uploaded to Hetzner Cloud (named "gha-deploy")

## Configuration

### Server Specifications

**Application Server (default: cpx31)**
- 4 vCPU
- 8 GB RAM
- 160 GB NVMe SSD
- Runs: All microservices + frontend + Redis + Caddy

**Database Server (default: cx22)**
- 2 vCPU
- 4 GB RAM
- 40 GB NVMe SSD
- Runs: PostgreSQL 15

## Usage

### 1. Configure Variables

Edit `secrets.tfvars`:
```hcl
hcloud_token      = "YOUR_HETZNER_API_TOKEN"
project_name      = "accounting-app"
location          = "hel1"
server_image      = "ubuntu-22.04"
app_server_type   = "cpx31"  # 4 vCPU, 8 GB RAM
db_server_type    = "cx22"   # 2 vCPU, 4 GB RAM
db_name           = "appdb"
db_user           = "appuser"
```

### 2. Initialize Terraform

```bash
cd infra/terraform/hetzner
terraform init
```

### 3. Plan and Apply

```bash
# Review the plan
terraform plan -var-file=secrets.tfvars

# Apply the configuration
terraform apply -var-file=secrets.tfvars
```

### 4. Get Outputs

After successful apply, get important connection details:

```bash
# Get all outputs
terraform output

# Get specific values
terraform output app_server_public_ipv4
terraform output db_password  # sensitive
terraform output connection_string  # sensitive
```

## Outputs

| Output | Description |
|--------|-------------|
| `app_server_public_ipv4` | Public IP of app server (use for DNS) |
| `db_server_public_ipv4` | Public IP of DB server (for SSH maintenance only) |
| `app_server_private_ip` | Private IP of app server (10.10.0.2) |
| `db_server_private_ip` | Private IP of DB server (10.10.0.3) |
| `db_host` | Database host for docker-compose (private IP) |
| `db_port` | Database port (5432) |
| `db_user` | Database username |
| `db_name` | Database name |
| `db_password` | Generated database password (sensitive) |
| `connection_string` | Full PostgreSQL connection string (sensitive) |
| `ssh_command_app` | SSH command for app server |
| `ssh_command_db` | SSH command for DB server |

## Post-Deployment Steps

### 1. SSH to Application Server

```bash
ssh ubuntu@<app_server_public_ipv4>
```

### 2. Create Environment File

Create `~/app/.env` with database connection:

```bash
DB_HOST=10.10.0.3
DB_PORT=5432
DB_USER=appuser
DB_NAME=appdb
DB_PASSWORD=<from terraform output>
```

### 3. Deploy Application

Copy your `deploy` directory to the server:

```bash
scp -r deploy/* ubuntu@<app_server_ip>:~/app/
```

### 4. Start Services

On the app server:

```bash
cd ~/app
docker compose up -d
```

## Scaling Recommendations

To scale up, modify `secrets.tfvars`:

**For more traffic:**
```hcl
app_server_type = "cpx41"  # 8 vCPU, 16 GB RAM
```

**For larger database:**
```hcl
db_server_type = "cx32"    # 4 vCPU, 8 GB RAM
```

**Available Hetzner server types:**
- cx22: 2 vCPU, 4 GB RAM, 40 GB disk (~€5/month)
- cpx31: 4 vCPU, 8 GB RAM, 160 GB disk (~€14/month)
- cpx41: 8 vCPU, 16 GB RAM, 240 GB disk (~€28/month)
- cpx51: 16 vCPU, 32 GB RAM, 360 GB disk (~€56/month)

## Security Best Practices

✅ **Implemented:**
- Database accessible only via private network
- Firewalls configured for minimal attack surface
- Random 32-character database password
- Separate servers for app and database

⚠️ **Recommended:**
- Configure automated backups for DB server
- Set up monitoring (e.g., Prometheus + Grafana)
- Enable server snapshots before major changes
- Rotate database password periodically
- Configure SSH key-only authentication (disable password auth)

## Troubleshooting

### Check PostgreSQL Setup

SSH to DB server:
```bash
ssh ubuntu@<db_server_public_ipv4>
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"  # List databases
```

### Test Private Network Connectivity

From app server:
```bash
ping 10.10.0.3
telnet 10.10.0.3 5432
```

### Check Cloud-Init Logs

```bash
sudo cat /var/log/cloud-init-output.log
```

## Maintenance

### Destroy Infrastructure

```bash
terraform destroy -var-file=secrets.tfvars
```

**Warning:** This will delete all servers and data. Make sure to backup data first!

### Update Infrastructure

Modify variables and apply:
```bash
terraform apply -var-file=secrets.tfvars
```

## Cost Estimation

Monthly costs (Hetzner pricing as of 2024):
- Application Server (cpx31): ~€14/month
- Database Server (cx22): ~€5/month
- Network: Free
- **Total: ~€19/month**

## GitHub Actions Integration

Set these secrets in your GitHub repository:

- `HCLOUD_TOKEN`: Hetzner API token
- `SSH_PRIVATE_KEY`: Private key for gha-deploy
- `APP_SERVER_IP`: Output from `app_server_public_ipv4`
- `DB_PASSWORD`: Output from `db_password`
- `DB_HOST`: Output from `db_host` (10.10.0.3)

