provider "hcloud" {
  token = var.hcloud_token
}

data "hcloud_ssh_key" "existing" {
  name = "gha-deploy"
}

# =============================================================================
# SINGLE SERVER ARCHITECTURE - FinFlow Production
# =============================================================================
# All services run on ONE Hetzner server via Docker Compose:
#   PostgreSQL, Redis, 14 FastAPI services, Caddy
# =============================================================================

# --- Firewall (single, hardened) ---
resource "hcloud_firewall" "finflow" {
  name = "${var.project_name}-fw"

  # SSH - restricted to known IPs only
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = var.ssh_allowed_ips
  }

  # HTTP
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # ICMP (ping)
  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

# --- Cloud-init: Docker + SSH hardening ---
locals {
  cloud_init = <<-EOF
  #cloud-config
  package_update: true
  package_upgrade: true
  packages:
    - apt-transport-https
    - ca-certificates
    - curl
    - gnupg
    - lsb-release
    - fail2ban
    - unattended-upgrades

  write_files:
    - path: /etc/ssh/sshd_config.d/hardening.conf
      permissions: '0644'
      content: |
        PermitRootLogin prohibit-password
        PasswordAuthentication no
        PubkeyAuthentication yes
        X11Forwarding no
        MaxAuthTries 3
        AllowAgentForwarding no
        AllowTcpForwarding no
        ClientAliveInterval 300
        ClientAliveCountMax 2

    - path: /etc/fail2ban/jail.local
      permissions: '0644'
      content: |
        [sshd]
        enabled = true
        port = 22
        maxretry = 5
        bantime = 3600
        findtime = 600

  runcmd:
    # SSH hardening
    - systemctl restart ssh
    - systemctl enable fail2ban
    - systemctl start fail2ban

    # Install Docker CE
    - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    - echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    - apt-get update -y
    - apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    - systemctl enable docker
    - systemctl start docker

    # Create deploy user with docker access
    - usermod -aG docker ubuntu || true

    # Create app directory structure
    - mkdir -p /home/ubuntu/app/backup
    - mkdir -p /home/ubuntu/app/init
    - chown -R ubuntu:ubuntu /home/ubuntu/app

    # Create backup directory on host
    - mkdir -p /var/backups/postgres
    - chown ubuntu:ubuntu /var/backups/postgres
  EOF
}

# --- Single production server ---
resource "hcloud_server" "finflow" {
  name        = "${var.project_name}-server"
  image       = var.server_image
  server_type = var.server_type
  location    = var.location
  ssh_keys    = [data.hcloud_ssh_key.existing.id]
  user_data   = local.cloud_init
  backups     = true

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
}

resource "hcloud_firewall_attachment" "finflow" {
  firewall_id = hcloud_firewall.finflow.id
  server_ids  = [hcloud_server.finflow.id]
}

# --- Outputs ---
output "server_ipv4" {
  description = "Public IPv4 address of FinFlow server"
  value       = hcloud_server.finflow.ipv4_address
}

output "server_ipv6" {
  description = "Public IPv6 address of FinFlow server"
  value       = hcloud_server.finflow.ipv6_address
}

output "ssh_command" {
  description = "SSH command to connect to server"
  value       = "ssh ubuntu@${hcloud_server.finflow.ipv4_address}"
}
