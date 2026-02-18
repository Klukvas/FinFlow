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
  default     = "finflow"
}

variable "location" {
  description = "Hetzner location (e.g., fsn1, nbg1, hel1)"
  type        = string
  default     = "hel1"
}

variable "server_image" {
  description = "Base OS image for server"
  type        = string
  default     = "ubuntu-22.04"
}

# Server settings (single server runs everything)
variable "server_type" {
  description = "Hetzner server type - cpx42: 8 vCPU, 16 GB RAM, 320 GB disk"
  type        = string
  default     = "cpx42"
}

# SSH access restriction
variable "ssh_allowed_ips" {
  description = "List of CIDR blocks allowed to SSH (e.g., your office IP)"
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"] # Override in secrets.tfvars with actual IPs
}
