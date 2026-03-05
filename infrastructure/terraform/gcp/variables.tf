# =============================================================================
# Mrki GCP Infrastructure - Variables
# =============================================================================

variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "mrki"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

# =============================================================================
# VPC Variables
# =============================================================================
variable "private_subnet_cidr" {
  description = "Private subnet CIDR block"
  type        = string
  default     = "10.0.0.0/20"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR block"
  type        = string
  default     = "10.0.16.0/20"
}

# =============================================================================
# GKE Variables
# =============================================================================
variable "enable_autopilot" {
  description = "Enable GKE Autopilot mode"
  type        = bool
  default     = false
}

variable "node_machine_type" {
  description = "GKE node machine type"
  type        = string
  default     = "e2-medium"
}

variable "node_count" {
  description = "Initial node count"
  type        = number
  default     = 2
}

variable "node_min_count" {
  description = "Minimum node count"
  type        = number
  default     = 1
}

variable "node_max_count" {
  description = "Maximum node count"
  type        = number
  default     = 10
}

# =============================================================================
# Database Variables
# =============================================================================
variable "db_tier" {
  description = "Cloud SQL tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size" {
  description = "Cloud SQL disk size in GB"
  type        = number
  default     = 10
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "mrki"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "mrki_admin"
}

# =============================================================================
# Redis Variables
# =============================================================================
variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

# =============================================================================
# CDN Variables
# =============================================================================
variable "cdn_domain" {
  description = "CDN domain name"
  type        = string
  default     = ""
}

variable "cors_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = ["*"]
}
