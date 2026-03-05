# =============================================================================
# Mrki Azure Infrastructure - Variables
# =============================================================================

variable "azure_region" {
  description = "Azure region"
  type        = string
  default     = "East US"
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
# Network Variables
# =============================================================================
variable "vnet_cidr" {
  description = "Virtual network CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.0.0/20"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.16.0/20"]
}

# =============================================================================
# AKS Variables
# =============================================================================
variable "system_node_count" {
  description = "System node pool count"
  type        = number
  default     = 2
}

variable "system_node_min_count" {
  description = "System node pool minimum count"
  type        = number
  default     = 1
}

variable "system_node_max_count" {
  description = "System node pool maximum count"
  type        = number
  default     = 5
}

variable "system_node_vm_size" {
  description = "System node VM size"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "workload_node_count" {
  description = "Workload node pool count"
  type        = number
  default     = 2
}

variable "workload_node_min_count" {
  description = "Workload node pool minimum count"
  type        = number
  default     = 1
}

variable "workload_node_max_count" {
  description = "Workload node pool maximum count"
  type        = number
  default     = 10
}

variable "workload_node_vm_size" {
  description = "Workload node VM size"
  type        = string
  default     = "Standard_D4s_v3"
}

variable "enable_gpu_node_pool" {
  description = "Enable GPU node pool"
  type        = bool
  default     = false
}

# =============================================================================
# ACR Variables
# =============================================================================
variable "acr_sku" {
  description = "ACR SKU"
  type        = string
  default     = "Standard"
}

# =============================================================================
# PostgreSQL Variables
# =============================================================================
variable "postgres_sku" {
  description = "PostgreSQL SKU"
  type        = string
  default     = "B_Standard_B1ms"
}

variable "postgres_storage_mb" {
  description = "PostgreSQL storage in MB"
  type        = number
  default     = 32768
}

variable "postgres_admin_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "mrkiadmin"
}

variable "postgres_database_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "mrki"
}

# =============================================================================
# Redis Variables
# =============================================================================
variable "redis_capacity" {
  description = "Redis capacity"
  type        = number
  default     = 1
}

variable "redis_family" {
  description = "Redis family"
  type        = string
  default     = "C"
}

variable "redis_sku" {
  description = "Redis SKU"
  type        = string
  default     = "Basic"
}

# =============================================================================
# Service Bus Variables
# =============================================================================
variable "servicebus_sku" {
  description = "Service Bus SKU"
  type        = string
  default     = "Standard"
}

# =============================================================================
# Front Door Variables
# =============================================================================
variable "enable_frontdoor_premium" {
  description = "Enable Front Door Premium"
  type        = bool
  default     = false
}
