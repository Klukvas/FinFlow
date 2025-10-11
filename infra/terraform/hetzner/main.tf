provider "hcloud" {
  token = var.hcloud_token
}

data "hcloud_ssh_key" "existing" {
  name = "gha-deploy"
}

# Private network for internal communication
resource "hcloud_network" "private" {
  name     = "${var.project_name}-net"
  ip_range = var.network_cidr
}

resource "hcloud_network_subnet" "subnet" {
  network_id   = hcloud_network.private.id
  type         = "cloud"
  network_zone = "eu-central"
  ip_range     = var.network_cidr
}

# Firewall for application server (docker host)
resource "hcloud_firewall" "app_server" {
  name = "${var.project_name}-app-fw"

  # SSH access
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTP access
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS access
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

# Firewall for database server
resource "hcloud_firewall" "db_server" {
  name = "${var.project_name}-db-fw"

  # SSH access (for maintenance)
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # PostgreSQL access from private network only
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "5432"
    source_ips = [var.network_cidr]
  }

  # ICMP (ping)
  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

# Generate secure password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Cloud-init script for application server
locals {
  app_cloud_init = <<-EOF
  #cloud-config
  package_update: true
  package_upgrade: true
  packages:
    - apt-transport-https
    - ca-certificates
    - curl
    - gnupg
    - lsb-release
  runcmd:
    # Install Docker
    - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    - echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    - apt-get update -y
    - apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    - usermod -aG docker ubuntu || true
    - systemctl enable docker
    - systemctl start docker
    # Create app directory
    - mkdir -p /home/ubuntu/app
    - chown ubuntu:ubuntu /home/ubuntu/app
  EOF
}

# Application server (runs all services via docker compose)
resource "hcloud_server" "app_server" {
  name        = "${var.project_name}-app"
  image       = var.server_image
  server_type = var.app_server_type
  location    = var.location
  ssh_keys    = [data.hcloud_ssh_key.existing.id]
  user_data   = local.app_cloud_init

  network {
    network_id = hcloud_network.private.id
    ip         = var.app_server_private_ip
  }

  depends_on = [hcloud_network_subnet.subnet]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
}

resource "hcloud_firewall_attachment" "app_server" {
  firewall_id = hcloud_firewall.app_server.id
  server_ids  = [hcloud_server.app_server.id]
}

# Cloud-init script for PostgreSQL server
locals {
  db_cloud_init = <<-EOF
  #cloud-config
  package_update: true
  package_upgrade: true
  packages:
    - postgresql
    - postgresql-contrib
  write_files:
    - path: /tmp/setup_postgres.sh
      permissions: '0755'
      content: |
        #!/bin/bash
        set -e
        
        # Wait for PostgreSQL to be ready
        until sudo -u postgres psql -c '\q' 2>/dev/null; do
          echo "Waiting for PostgreSQL to start..."
          sleep 2
        done
        
        # Create user and database
        sudo -u postgres psql -c "CREATE USER ${var.db_user} WITH PASSWORD '${random_password.db_password.result}';" || true
        sudo -u postgres psql -c "CREATE DATABASE ${var.db_name} OWNER ${var.db_user};" || true
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${var.db_name} TO ${var.db_user};" || true
        
        # Configure PostgreSQL to listen on private network
        PG_VERSION=$(ls /etc/postgresql/)
        PG_CONF="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
        PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
        
        # Update listen_addresses
        sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '${var.db_server_private_ip},127.0.0.1'/g" $PG_CONF
        
        # Add access from private network
        echo "host    all             all             ${var.network_cidr}           md5" >> $PG_HBA
        
        # Restart PostgreSQL
        systemctl restart postgresql
        
        echo "PostgreSQL setup completed successfully"
  runcmd:
    - systemctl enable postgresql
    - systemctl start postgresql
    - /tmp/setup_postgres.sh
  EOF
}

# Database server
resource "hcloud_server" "db_server" {
  name        = "${var.project_name}-db"
  image       = var.server_image
  server_type = var.db_server_type
  location    = var.location
  ssh_keys    = [data.hcloud_ssh_key.existing.id]
  user_data   = local.db_cloud_init

  network {
    network_id = hcloud_network.private.id
    ip         = var.db_server_private_ip
  }

  depends_on = [hcloud_network_subnet.subnet]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }
}

resource "hcloud_firewall_attachment" "db_server" {
  firewall_id = hcloud_firewall.db_server.id
  server_ids  = [hcloud_server.db_server.id]
}

# Outputs
output "app_server_public_ipv4" {
  description = "Public IPv4 address of the application server"
  value       = hcloud_server.app_server.ipv4_address
}

output "app_server_private_ip" {
  description = "Private IP address of the application server"
  value       = var.app_server_private_ip
}

output "db_server_public_ipv4" {
  description = "Public IPv4 address of the database server (for SSH maintenance)"
  value       = hcloud_server.db_server.ipv4_address
}

output "db_server_private_ip" {
  description = "Private IP address of the database server (use this for DB connections)"
  value       = var.db_server_private_ip
}

output "db_host" {
  description = "Database host (private IP) - use this in docker-compose"
  value       = var.db_server_private_ip
}

output "db_port" {
  description = "Database port"
  value       = "5432"
}

output "db_user" {
  description = "Database username"
  value       = var.db_user
}

output "db_name" {
  description = "Database name"
  value       = var.db_name
}

output "db_password" {
  description = "Database password"
  value       = random_password.db_password.result
  sensitive   = true
}

output "connection_string" {
  description = "Complete PostgreSQL connection string (use for docker-compose)"
  value       = "postgresql://${var.db_user}:${random_password.db_password.result}@${var.db_server_private_ip}:5432/${var.db_name}"
  sensitive   = true
}

output "ssh_command_app" {
  description = "SSH command to connect to application server"
  value       = "ssh ubuntu@${hcloud_server.app_server.ipv4_address}"
}

output "ssh_command_db" {
  description = "SSH command to connect to database server"
  value       = "ssh ubuntu@${hcloud_server.db_server.ipv4_address}"
}

