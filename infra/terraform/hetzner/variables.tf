# Hetzner Cloud API token
variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

# General settings
variable "project_name" {
  description = "Project/name prefix for resources"
  type        = string
  default     = "accounting-app"
}

variable "location" {
  description = "Hetzner location (e.g., fsn1, nbg1, hel1)"
  type        = string
  default     = "hel1"
}

variable "server_image" {
  description = "Base OS image for servers"
  type        = string
  default     = "ubuntu-22.04"
}

# Network settings
variable "network_cidr" {
  description = "Private network CIDR"
  type        = string
  default     = "10.10.0.0/16"
}

variable "app_server_private_ip" {
  description = "Private IP address for application server"
  type        = string
  default     = "10.10.0.2"
}

variable "db_server_private_ip" {
  description = "Private IP address for database server"
  type        = string
  default     = "10.10.0.3"
}

# Application server settings
variable "app_server_type" {
  description = "Hetzner server type for application server (runs docker compose)"
  type        = string
  default     = "cpx31" # 4 vCPU, 8 GB RAM, 160 GB disk
}

# Database server settings
variable "db_server_type" {
  description = "Hetzner server type for database server"
  type        = string
  default     = "cx22" # 2 vCPU, 4 GB RAM, 40 GB disk
}

variable "db_name" {
  description = "Primary database name"
  type        = string
  default     = "appdb"
}

variable "db_user" {
  description = "Database user"
  type        = string
  default     = "appuser"
}

