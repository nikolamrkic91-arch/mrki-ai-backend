# =============================================================================
# Mrki Azure Infrastructure - Main Configuration
# =============================================================================
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.75"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.15"
    }
  }

  backend "azurerm" {
    resource_group_name  = "mrki-terraform-rg"
    storage_account_name = "mrkiterraformstate"
    container_name       = "tfstate"
    key                  = "azure/infrastructure.tfstate"
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
}

# =============================================================================
# Resource Group
# =============================================================================
resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-${var.environment}-rg"
  location = var.azure_region

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# =============================================================================
# Virtual Network
# =============================================================================
resource "azurerm_virtual_network" "main" {
  name                = "${var.project_name}-${var.environment}-vnet"
  address_space       = [var.vnet_cidr]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_subnet" "private" {
  name                 = "private"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = var.private_subnet_cidrs

  service_endpoints = [
    "Microsoft.Sql",
    "Microsoft.Storage",
    "Microsoft.KeyVault",
    "Microsoft.ContainerRegistry",
  ]

  delegation {
    name = "aks-delegation"
    service_delegation {
      name    = "Microsoft.ContainerInstance/containerGroups"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

resource "azurerm_subnet" "public" {
  name                 = "public"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = var.public_subnet_cidrs
}

# =============================================================================
# Network Security Groups
# =============================================================================
resource "azurerm_network_security_group" "private" {
  name                = "${var.project_name}-private-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "AllowVnetInBound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_subnet_network_security_group_association" "private" {
  subnet_id                 = azurerm_subnet.private.id
  network_security_group_id = azurerm_network_security_group.private.id
}

# =============================================================================
# NAT Gateway
# =============================================================================
resource "azurerm_public_ip" "nat" {
  name                = "${var.project_name}-nat-ip"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_nat_gateway" "main" {
  name                = "${var.project_name}-nat-gateway"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku_name            = "Standard"

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_nat_gateway_public_ip_association" "main" {
  nat_gateway_id       = azurerm_nat_gateway.main.id
  public_ip_address_id = azurerm_public_ip.nat.id
}

resource "azurerm_subnet_nat_gateway_association" "private" {
  subnet_id      = azurerm_subnet.private.id
  nat_gateway_id = azurerm_nat_gateway.main.id
}

# =============================================================================
# AKS Cluster
# =============================================================================
resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "${var.project_name}-${var.environment}"
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                = "system"
    node_count          = var.system_node_count
    vm_size             = var.system_node_vm_size
    type                = "VirtualMachineScaleSets"
    vnet_subnet_id      = azurerm_subnet.private.id
    enable_auto_scaling = true
    min_count           = var.system_node_min_count
    max_count           = var.system_node_max_count
    os_disk_size_gb     = 128
    os_disk_type        = "Managed"
    zones               = [1, 2, 3]

    node_labels = {
      "nodepool-type" = "system"
      "environment"   = var.environment
    }

    tags = {
      Environment = var.environment
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin     = "azure"
    network_policy     = "calico"
    load_balancer_sku  = "standard"
    service_cidr       = "10.1.0.0/16"
    dns_service_ip     = "10.1.0.10"
    docker_bridge_cidr = "172.17.0.1/16"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  azure_policy_enabled = true

  auto_scaler_profile {
    balance_similar_node_groups      = true
    expander                         = "random"
    max_graceful_termination_sec     = 600
    max_node_provision_time          = "15m"
    max_unready_nodes                = 3
    max_unready_percentage           = 45
    new_pod_scale_up_delay           = "10s"
    scale_down_delay_after_add       = "10m"
    scale_down_delay_after_delete    = "10s"
    scale_down_delay_after_failure   = "3m"
    scan_interval                    = "10s"
    scale_down_unneeded              = "10m"
    scale_down_unready               = "20m"
    scale_down_utilization_threshold = "0.5"
    empty_bulk_delete_max            = 10
    skip_nodes_with_local_storage    = false
    skip_nodes_with_system_pods      = false
  }

  maintenance_window {
    allowed {
      day   = "Saturday"
      hours = [22, 23]
    }
    allowed {
      day   = "Sunday"
      hours = [0, 1, 2, 3]
    }
  }

  tags = {
    Environment = var.environment
  }

  depends_on = [azurerm_subnet_nat_gateway_association.private]
}

# =============================================================================
# AKS Node Pools
# =============================================================================
resource "azurerm_kubernetes_cluster_node_pool" "workload" {
  name                  = "workload"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.workload_node_vm_size
  node_count            = var.workload_node_count
  vnet_subnet_id        = azurerm_subnet.private.id
  enable_auto_scaling   = true
  min_count             = var.workload_node_min_count
  max_count             = var.workload_node_max_count
  os_disk_size_gb       = 128
  os_type               = "Linux"
  zones                 = [1, 2, 3]

  node_labels = {
    "nodepool-type" = "workload"
    "workload"      = "general"
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "spot" {
  name                  = "spot"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.workload_node_vm_size
  node_count            = 0
  vnet_subnet_id        = azurerm_subnet.private.id
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = 10
  priority              = "Spot"
  eviction_policy       = "Delete"
  spot_max_price        = -1  # Pay up to on-demand price

  node_labels = {
    "nodepool-type" = "spot"
    "kubernetes.azure.com/scalesetpriority" = "spot"
    "workload"      = "spot"
  }

  node_taints = [
    "kubernetes.azure.com/scalesetpriority=spot:NoSchedule"
  ]

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "gpu" {
  count = var.enable_gpu_node_pool ? 1 : 0

  name                  = "gpu"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_NC6s_v3"
  node_count            = 0
  vnet_subnet_id        = azurerm_subnet.private.id
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = 4

  node_labels = {
    "nodepool-type" = "gpu"
    "workload"      = "gpu"
    "accelerator"   = "nvidia"
  }

  node_taints = [
    "nvidia.com/gpu=true:NoSchedule"
  ]

  tags = {
    Environment = var.environment
  }
}

# =============================================================================
# Azure Container Registry
# =============================================================================
resource "azurerm_container_registry" "main" {
  name                = "${var.project_name}${var.environment}acr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
  admin_enabled       = false

  identity {
    type = "SystemAssigned"
  }

  network_rule_set {
    default_action = "Deny"
  }

  retention_policy {
    enabled = true
    days    = 7
  }

  trust_policy {
    enabled = true
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.main.id
  skip_service_principal_aad_check = true
}

# =============================================================================
# PostgreSQL Flexible Server
# =============================================================================
resource "azurerm_private_dns_zone" "postgres" {
  name                = "${var.project_name}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "${var.project_name}-postgres-link"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.project_name}-postgres-${var.environment}"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "15"
  sku_name               = var.postgres_sku
  storage_mb             = var.postgres_storage_mb
  backup_retention_days  = var.environment == "production" ? 35 : 7
  geo_redundant_backup_enabled = var.environment == "production"

  delegated_subnet_id = azurerm_subnet.private.id
  private_dns_zone_id = azurerm_private_dns_zone.postgres.id

  administrator_login    = var.postgres_admin_username
  administrator_password = random_password.postgres_admin.result

  high_availability {
    mode = var.environment == "production" ? "ZoneRedundant" : "Disabled"
  }

  maintenance_window {
    day_of_week  = 0  # Sunday
    start_hour   = 3
    start_minute = 0
  }

  tags = {
    Environment = var.environment
  }

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "azurerm_postgresql_flexible_server_database" "mrki" {
  name      = var.postgres_database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "random_password" "postgres_admin" {
  length  = 32
  special = true
}

# =============================================================================
# Azure Cache for Redis
# =============================================================================
resource "azurerm_redis_cache" "main" {
  name                = "${var.project_name}-redis-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = var.redis_capacity
  family              = var.redis_family
  sku_name            = var.redis_sku
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {
    maxmemory_policy = "allkeys-lru"
  }

  patch_schedule {
    day_of_week    = "Sunday"
    start_hour_utc = 3
  }

  tags = {
    Environment = var.environment
  }
}

# =============================================================================
# Storage Account
# =============================================================================
resource "azurerm_storage_account" "main" {
  name                     = "${var.project_name}${var.environment}st"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = var.environment == "production" ? "GRS" : "LRS"
  access_tier              = "Hot"
  min_tls_version          = "TLS1_2"
  allow_nested_items_to_be_public = false

  blob_properties {
    versioning_enabled  = true
    change_feed_enabled = true

    delete_retention_policy {
      days = var.environment == "production" ? 30 : 7
    }

    container_delete_retention_policy {
      days = var.environment == "production" ? 30 : 7
    }
  }

  network_rules {
    default_action             = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.private.id]
    bypass                     = ["AzureServices"]
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_storage_container" "assets" {
  name                  = "assets"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "backups" {
  name                  = "backups"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# =============================================================================
# Key Vault
# =============================================================================
resource "azurerm_key_vault" "main" {
  name                       = "${var.project_name}-${var.environment}-kv"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = var.environment == "production"

  network_acls {
    default_action             = "Deny"
    bypass                     = "AzureServices"
    virtual_network_subnet_ids = [azurerm_subnet.private.id]
  }

  tags = {
    Environment = var.environment
  }
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault_access_policy" "current_user" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
}

resource "azurerm_key_vault_secret" "postgres_password" {
  name         = "postgres-admin-password"
  value        = random_password.postgres_admin.result
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault_access_policy.current_user]
}

# =============================================================================
# Log Analytics Workspace
# =============================================================================
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.project_name}-${var.environment}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "production" ? 90 : 30

  tags = {
    Environment = var.environment
  }
}

# =============================================================================
# Application Insights
# =============================================================================
resource "azurerm_application_insights" "main" {
  name                = "${var.project_name}-${var.environment}-appinsights"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id

  tags = {
    Environment = var.environment
  }
}

# =============================================================================
# Service Bus
# =============================================================================
resource "azurerm_servicebus_namespace" "main" {
  name                = "${var.project_name}-${var.environment}-sb"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = var.servicebus_sku

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_servicebus_queue" "events" {
  name                = "events"
  namespace_id        = azurerm_servicebus_namespace.main.id
  enable_partitioning = true
}

resource "azurerm_servicebus_queue" "events_dlq" {
  name                = "events-dlq"
  namespace_id        = azurerm_servicebus_namespace.main.id
  enable_partitioning = true
}

# =============================================================================
# Function App
# =============================================================================
resource "azurerm_service_plan" "functions" {
  name                = "${var.project_name}-${var.environment}-asp"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "Y1"  # Consumption plan
}

resource "azurerm_linux_function_app" "processor" {
  name                       = "${var.project_name}-${var.environment}-processor"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  service_plan_id            = azurerm_service_plan.functions.id
  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key

  site_config {
    application_stack {
      node_version = "20"
    }

    application_insights_key = azurerm_application_insights.main.instrumentation_key
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "node"
    "DB_HOST"                  = azurerm_postgresql_flexible_server.main.fqdn
    "REDIS_HOST"               = azurerm_redis_cache.main.hostname
    "ENVIRONMENT"              = var.environment
  }

  identity {
    type = "SystemAssigned"
  }

  virtual_network_subnet_id = azurerm_subnet.private.id

  tags = {
    Environment = var.environment
  }
}

# =============================================================================
# Front Door CDN
# =============================================================================
resource "azurerm_cdn_profile" "main" {
  name                = "${var.project_name}-${var.environment}-cdn"
  location            = "Global"
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard_Microsoft"

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_cdn_endpoint" "main" {
  name                      = "${var.project_name}-${var.environment}"
  profile_name              = azurerm_cdn_profile.main.name
  location                  = azurerm_resource_group.main.location
  resource_group_name       = azurerm_resource_group.main.name
  is_http_allowed           = false
  is_https_allowed          = true
  querystring_caching_behaviour = "IgnoreQueryString"

  origin {
    name      = "storage"
    host_name = azurerm_storage_account.main.primary_blob_host
  }

  global_delivery_rule {
    modify_response_header_action {
      action = "Append"
      name   = "X-Content-Type-Options"
      value  = "nosniff"
    }
  }

  delivery_rule {
    name  = "EnforceHTTPS"
    order = 1

    request_scheme_condition {
      operator     = "Equal"
      match_values = ["HTTP"]
    }

    url_redirect_action {
      redirect_type = "Found"
      protocol      = "Https"
    }
  }

  tags = {
    Environment = var.environment
  }
}

# =============================================================================
# Azure Front Door (Premium)
# =============================================================================
resource "azurerm_frontdoor" "main" {
  count = var.enable_frontdoor_premium ? 1 : 0

  name                = "${var.project_name}-${var.environment}-fd"
  resource_group_name = azurerm_resource_group.main.name

  routing_rule {
    name               = "default"
    accepted_protocols = ["Https"]
    patterns_to_match  = ["/*"]
    frontend_endpoints = ["default"]
    forwarding_configuration {
      forwarding_protocol = "HttpsOnly"
      backend_pool_name   = "default"
    }
  }

  backend_pool_load_balancing {
    name = "default"
  }

  backend_pool_health_probe {
    name = "default"
  }

  backend_pool {
    name = "default"
    backend {
      host_header = azurerm_storage_account.main.primary_blob_host
      address     = azurerm_storage_account.main.primary_blob_host
      http_port   = 80
      https_port  = 443
    }
  }

  frontend_endpoint {
    name      = "default"
    host_name = "${var.project_name}-${var.environment}-fd.azurefd.net"
  }
}

# =============================================================================
# Azure WAF Policy
# =============================================================================
resource "azurerm_web_application_firewall_policy" "main" {
  name                = "${var.project_name}-${var.environment}-waf"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  policy_settings {
    enabled                     = true
    mode                        = "Prevention"
    request_body_check          = true
    file_upload_limit_in_mb     = 100
    max_request_body_size_in_kb = 128
  }

  managed_rules {
    managed_rule_set {
      type    = "OWASP"
      version = "3.2"
    }
  }

  custom_rules {
    name      = "RateLimit"
    priority  = 1
    rule_type = "RateLimitRule"

    match_condition {
      match_variables {
        variable_name = "RemoteAddr"
      }
      operator           = "IPMatch"
      negation_condition = false
      match_values       = ["0.0.0.0/0"]
    }

    action = "Block"
    rate_limit_duration_in_minutes = 1
    rate_limit_threshold = 100
  }

  tags = {
    Environment = var.environment
  }
}
