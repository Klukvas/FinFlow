variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

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

variable "network_cidr" {
  description = "Private network CIDR"
  type        = string
  default     = "10.10.0.0/16"
}

variable "server_type" {
  description = "Hetzner server type for Docker host"
  type        = string
  default     = "cpx21"
}

variable "server_image" {
  description = "Image for Docker host"
  type        = string
  default     = "ubuntu-22.04"
}

variable "ssh_public_key" {
  description = "Public SSH key content"
  type        = string
}

variable "db_version" {
  description = "Managed PostgreSQL version"
  type        = string
  default     = "15"
}

variable "db_tier" {
  description = "Managed DB tier (e.g., hobby, standard, premium)"
  type        = string
  default     = "hobby"
}

variable "db_maintenance_window" {
  description = "DB maintenance window day/time"
  type        = object({
    day_of_week = string
    time        = string
  })
  default = {
    day_of_week = "monday"
    time        = "02:00:00"
  }
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

variable "db_allowed_ips" {
  description = "Allowed IPv4 addresses/CIDRs to access DB from outside network"
  type        = list(string)
  default     = []
}

