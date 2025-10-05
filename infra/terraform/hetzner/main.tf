provider "hcloud" {
  token = var.hcloud_token
}

resource "hcloud_ssh_key" "gha_deploy" {
  name       = "gha-deploy-new"
  public_key = file("~/.ssh/gha-deploy.pub")
}

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

resource "hcloud_firewall" "docker_host" {
  name = "${var.project_name}-fw"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "6379"
    source_ips = [hcloud_server.docker_host.ipv4_address]
  }

  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

locals {
  cloud_init = <<-EOF
  #cloud-config
  package_update: true
  packages:
    - apt-transport-https
    - ca-certificates
    - curl
    - gnupg
    - lsb-release
  runcmd:
    - curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    - echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    - apt-get update -y
    - apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    - usermod -aG docker ubuntu || true
    - systemctl enable docker
    - systemctl start docker
  EOF
}

resource "hcloud_server" "docker_host" {
  name        = "${var.project_name}-host"
  image       = var.server_image
  server_type = var.server_type
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.gha_deploy.id]
  user_data   = local.cloud_init

  network {
    network_id = hcloud_network.private.id
  }
}

resource "hcloud_firewall_attachment" "docker_host" {
  firewall_id = hcloud_firewall.docker_host.id
  server_ids  = [hcloud_server.docker_host.id]
}

# PostgreSQL Database Server
resource "hcloud_server" "postgres" {
  name        = "${var.project_name}-db"
  image       = "ubuntu-22.04"
  server_type = "cx22"
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.gha_deploy.id]

  network {
    network_id = hcloud_network.private.id
  }
}

locals {
  postgres_init = <<-EOF
  #cloud-config
  package_update: true
  packages:
    - postgresql-15
    - postgresql-contrib-15
  runcmd:
    - systemctl enable postgresql
    - systemctl start postgresql
    - sudo -u postgres psql -c "CREATE USER ${var.db_user} WITH PASSWORD '${random_password.db_password.result}';"
    - sudo -u postgres psql -c "CREATE DATABASE ${var.db_name} OWNER ${var.db_user};"
    - sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${var.db_name} TO ${var.db_user};"
    - echo "host all all 10.10.0.0/16 md5" >> /etc/postgresql/15/main/pg_hba.conf
    - echo "listen_addresses = '*'" >> /etc/postgresql/15/main/postgresql.conf
    - systemctl restart postgresql
  EOF
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

resource "hcloud_server" "postgres_with_init" {
  name        = "${var.project_name}-db-init"
  image       = "ubuntu-22.04"
  server_type = "cx22"
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.gha_deploy.id]
  user_data   = local.postgres_init

  network {
    network_id = hcloud_network.private.id
  }

  depends_on = [hcloud_server.postgres]
}

output "docker_host_ipv4" {
  value = hcloud_server.docker_host.ipv4_address
}

output "db_host" {
  value = hcloud_server.postgres_with_init.ipv4_address
}

output "db_port" {
  value = "5432"
}

output "db_user" {
  value = var.db_user
}

output "db_name" {
  value = var.db_name
}

output "db_password" {
  value     = random_password.db_password.result
  sensitive = true
}

output "db_ssl" {
  value = "prefer"
}

