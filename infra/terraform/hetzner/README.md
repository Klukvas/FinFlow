Terraform for Hetzner Cloud

Overview
- Managed PostgreSQL database (separate service)
- Private network
- Docker host VM for BE/FE/Redis (run with Docker/Compose)
- Basic firewall: SSH(22), HTTP(80), HTTPS(443), Redis (restricted)

Prerequisites
- Terraform >= 1.5
- Hetzner Cloud token
- An SSH public key

Usage
1. Create a tfvars file:
```hcl
hcloud_token   = "hc_..."
ssh_public_key = "ssh-ed25519 AAAA... user@host"
project_name   = "accounting-app"
location       = "hel1"
network_cidr   = "10.10.0.0/16"
server_type    = "cpx21"
server_image   = "ubuntu-22.04"
db_version     = "15"
db_tier        = "hobby"
db_name        = "appdb"
db_user        = "appuser"
db_allowed_ips = []
```

2. Init and apply:
```bash
terraform init
terraform apply -var-file=secrets.tfvars
```

Outputs
- docker_host_ipv4: public IPv4 of Docker host
- db_host, db_port, db_user, db_name, db_ssl

Next steps on the Docker host
- SSH to host and deploy your Docker stack (compose or swarm)
- Point services to DB using the output connection (private network recommended)

Notes
- Managed DB is separate from the Docker host
- Private network connects server and DB without public exposure
- Add your own reverse-proxy/SSL on the Docker host (e.g., Caddy/Traefik/Nginx)

Required GitHub Secrets
- REGISTRY (optional, default ghcr.io)
- REGISTRY_USERNAME (Docker Hub username if using Docker Hub)
- REGISTRY_PASSWORD (Docker Hub access token or GHCR PAT)
- HZ_HOST (Hetzner Docker host public IP)
- HZ_USER (optional, default ubuntu)
- HZ_SSH_PRIVATE_KEY (private key matching the SSH key provisioned)

Deploy usage
- Ensure the compose files are on the host in ~/app (copy deploy directory)
- Trigger workflow "Deploy to Hetzner" manually or on push
- It will ssh to host, docker compose pull, and docker compose up -d

