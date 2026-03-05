# =============================================================================
# Mrki GCP Infrastructure - Main Configuration
# =============================================================================
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "mrki-terraform-state"
    prefix = "gcp/infrastructure"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# =============================================================================
# APIs
# =============================================================================
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "cloudsql.googleapis.com",
    "redis.googleapis.com",
    "storage.googleapis.com",
    "cloudcdn.googleapis.com",
    "cloudfunctions.googleapis.com",
    "pubsub.googleapis.com",
    "cloudkms.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# =============================================================================
# VPC Network
# =============================================================================
resource "google_compute_network" "vpc" {
  name                    = "${var.project_name}-${var.environment}"
  auto_create_subnetworks = false
  routing_mode            = "GLOBAL"

  depends_on = [google_project_service.apis]
}

resource "google_compute_subnetwork" "private" {
  name          = "${var.project_name}-private-${var.environment}"
  ip_cidr_range = var.private_subnet_cidr
  region        = var.gcp_region
  network       = google_compute_network.vpc.id

  private_ip_google_access = true

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.4.0.0/14"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.0.32.0/20"
  }

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_subnetwork" "public" {
  name          = "${var.project_name}-public-${var.environment}"
  ip_cidr_range = var.public_subnet_cidr
  region        = var.gcp_region
  network       = google_compute_network.vpc.id
}

# =============================================================================
# Cloud Router and NAT
# =============================================================================
resource "google_compute_router" "router" {
  name    = "${var.project_name}-router-${var.environment}"
  region  = var.gcp_region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.project_name}-nat-${var.environment}"
  router                             = google_compute_router.router.name
  region                             = var.gcp_region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# =============================================================================
# Firewall Rules
# =============================================================================
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.project_name}-allow-internal-${var.environment}"
  network = google_compute_network.vpc.name

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = [var.private_subnet_cidr, var.public_subnet_cidr]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.project_name}-allow-ssh-${var.environment}"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["allow-ssh"]
}

# =============================================================================
# GKE Cluster
# =============================================================================
resource "google_container_cluster" "primary" {
  name     = "${var.project_name}-${var.environment}"
  location = var.gcp_region

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.private.name

  remove_default_node_pool = true
  initial_node_count       = 1

  release_channel {
    channel = "REGULAR"
  }

  min_master_version = var.kubernetes_version

  # Enable Autopilot for serverless experience
  enable_autopilot = var.enable_autopilot

  # If not using Autopilot, configure node pools
  dynamic "node_pool" {
    for_each = var.enable_autopilot ? [] : [1]
    content {
      name       = "default-pool"
      node_count = var.node_count

      node_config {
        machine_type = var.node_machine_type
        disk_size_gb = 100
        disk_type    = "pd-ssd"

        oauth_scopes = [
          "https://www.googleapis.com/auth/cloud-platform"
        ]

        labels = {
          environment = var.environment
        }

        tags = ["gke-node", "${var.project_name}-${var.environment}"]
      }

      autoscaling {
        min_node_count = var.node_min_count
        max_node_count = var.node_max_count
      }

      management {
        auto_repair  = true
        auto_upgrade = true
      }
    }
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All"
    }
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
  }

  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  maintenance_policy {
    recurring_window {
      start_time = "2024-01-01T00:00:00Z"
      end_time   = "2024-01-01T04:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=SA,SU"
    }
  }

  depends_on = [google_project_service.apis]
}

# =============================================================================
# Node Pools (if not using Autopilot)
# =============================================================================
resource "google_container_node_pool" "general" {
  count = var.enable_autopilot ? 0 : 1

  name       = "general"
  location   = var.gcp_region
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  node_config {
    machine_type = var.node_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      workload = "general"
    }

    tags = ["gke-node", "${var.project_name}-${var.environment}"]
  }

  autoscaling {
    min_node_count = var.node_min_count
    max_node_count = var.node_max_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

resource "google_container_node_pool" "spot" {
  count = var.enable_autopilot ? 0 : 1

  name       = "spot"
  location   = var.gcp_region
  cluster    = google_container_cluster.primary.name
  node_count = 0

  node_config {
    machine_type = var.node_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    spot = true

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      workload = "spot"
      spot     = "true"
    }

    taint {
      key    = "spot"
      value  = "true"
      effect = "NO_SCHEDULE"
    }

    tags = ["gke-node", "${var.project_name}-${var.environment}"]
  }

  autoscaling {
    min_node_count = 0
    max_node_count = 10
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# =============================================================================
# Cloud SQL PostgreSQL
# =============================================================================
resource "google_sql_database_instance" "postgres" {
  name             = "${var.project_name}-postgres-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.gcp_region

  settings {
    tier = var.db_tier

    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }

    maintenance_window {
      day          = 7  # Sunday
      hour         = 3
      update_track = "stable"
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    disk_size         = var.db_disk_size
    disk_autoresize   = true
    disk_type         = "PD_SSD"

    user_labels = {
      environment = var.environment
    }
  }

  deletion_protection = var.environment == "production"

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "mrki" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "admin" {
  name     = var.db_username
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# =============================================================================
# VPC Peering for Cloud SQL
# =============================================================================
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.project_name}-private-ip-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# =============================================================================
# Memorystore Redis
# =============================================================================
resource "google_redis_instance" "cache" {
  name           = "${var.project_name}-redis-${var.environment}"
  tier           = var.environment == "production" ? "STANDARD_HA" : "BASIC"
  memory_size_gb = var.redis_memory_size_gb
  region         = var.gcp_region

  redis_version     = "REDIS_7_0"
  display_name      = "Mrki Redis Cache"

  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  maintenance_policy {
    weekly_maintenance_window {
      day = "TUESDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }

  labels = {
    environment = var.environment
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# =============================================================================
# Cloud Storage
# =============================================================================
resource "google_storage_bucket" "assets" {
  name          = "${var.project_name}-assets-${var.environment}-${var.gcp_project_id}"
  location      = var.gcp_region
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage.id
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  labels = {
    environment = var.environment
  }
}

resource "google_storage_bucket" "backups" {
  name          = "${var.project_name}-backups-${var.environment}-${var.gcp_project_id}"
  location      = var.gcp_region
  storage_class = "NEARLINE"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage.id
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  labels = {
    environment = var.environment
  }
}

# =============================================================================
# KMS for Encryption
# =============================================================================
resource "google_kms_key_ring" "main" {
  name     = "${var.project_name}-${var.environment}"
  location = var.gcp_region
}

resource "google_kms_crypto_key" "storage" {
  name            = "storage-key"
  key_ring        = google_kms_key_ring.main.id
  rotation_period = "7776000s"  # 90 days

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

resource "google_kms_crypto_key" "sql" {
  name            = "sql-key"
  key_ring        = google_kms_key_ring.main.id
  rotation_period = "7776000s"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

# =============================================================================
# Cloud CDN
# =============================================================================
resource "google_compute_backend_bucket" "cdn" {
  name        = "${var.project_name}-cdn-${var.environment}"
  bucket_name = google_storage_bucket.assets.name
  enable_cdn  = true

  cdn_policy {
    cache_mode        = "CACHE_ALL_STATIC"
    default_ttl       = 3600
    max_ttl           = 86400
    serve_while_stale = 86400
  }
}

resource "google_compute_url_map" "cdn" {
  name            = "${var.project_name}-cdn-${var.environment}"
  default_service = google_compute_backend_bucket.cdn.id
}

resource "google_compute_managed_ssl_certificate" "cdn" {
  count = var.cdn_domain != "" ? 1 : 0

  name = "${var.project_name}-ssl-${var.environment}"

  managed {
    domains = [var.cdn_domain]
  }
}

resource "google_compute_target_https_proxy" "cdn" {
  count = var.cdn_domain != "" ? 1 : 0

  name    = "${var.project_name}-https-proxy-${var.environment}"
  url_map = google_compute_url_map.cdn.id
  ssl_certificates = [google_compute_managed_ssl_certificate.cdn[0].id]
}

resource "google_compute_global_forwarding_rule" "cdn" {
  count = var.cdn_domain != "" ? 1 : 0

  name       = "${var.project_name}-cdn-forwarding-rule-${var.environment}"
  target     = google_compute_target_https_proxy.cdn[0].id
  port_range = "443"
}

# =============================================================================
# Pub/Sub
# =============================================================================
resource "google_pubsub_topic" "events" {
  name = "${var.project_name}-events-${var.environment}"

  message_retention_duration = "86600s"

  labels = {
    environment = var.environment
  }

  message_storage_policy {
    allowed_persistence_regions = [var.gcp_region]
  }
}

resource "google_pubsub_subscription" "events" {
  name  = "${var.project_name}-events-sub-${var.environment}"
  topic = google_pubsub_topic.events.name

  ack_deadline_seconds = 20

  message_retention_duration = "1200s"
  retain_acked_messages      = true

  expiration_policy {
    ttl = "300000.5s"
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.events_dlq.id
    max_delivery_attempts = 5
  }
}

resource "google_pubsub_topic" "events_dlq" {
  name = "${var.project_name}-events-dlq-${var.environment}"
}

# =============================================================================
# Cloud Functions (Gen 2)
# =============================================================================
resource "google_cloudfunctions2_function" "processor" {
  name     = "${var.project_name}-processor-${var.environment}"
  location = var.gcp_region

  build_config {
    runtime     = "nodejs20"
    entry_point = "handler"

    source {
      storage_source {
        bucket = google_storage_bucket.functions_source.name
        object = google_storage_bucket_object.function_source.name
      }
    }
  }

  service_config {
    max_instance_count = 100
    min_instance_count = 0
    available_memory   = "512Mi"
    timeout_seconds    = 60
    environment_variables = {
      DB_HOST     = google_sql_database_instance.postgres.private_ip_address
      REDIS_HOST  = google_redis_instance.cache.host
      ENVIRONMENT = var.environment
    }

    vpc_connector = google_vpc_access_connector.functions.id

    ingress_settings               = "ALLOW_INTERNAL_ONLY"
    all_traffic_on_latest_revision = true
  }

  event_trigger {
    trigger_region = var.gcp_region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.events.id
    retry_policy   = "RETRY_POLICY_RETRY"
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket" "functions_source" {
  name     = "${var.project_name}-functions-source-${var.environment}"
  location = var.gcp_region

  uniform_bucket_level_access = true
}

resource "google_storage_bucket_object" "function_source" {
  name   = "function-source-${data.archive_file.function_source.output_md5}.zip"
  bucket = google_storage_bucket.functions_source.name
  source = data.archive_file.function_source.output_path
}

data "archive_file" "function_source" {
  type        = "zip"
  output_path = "${path.module}/function-source.zip"
  source {
    content  = <<-EOF
      exports.handler = async (message, context) => {
        console.log('Message:', JSON.stringify(message));
        return { statusCode: 200, body: 'Success' };
      };
    EOF
    filename = "index.js"
  }
}

resource "google_vpc_access_connector" "functions" {
  name          = "${var.project_name}-connector-${var.environment}"
  region        = var.gcp_region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
}

# =============================================================================
# Cloud Armor
# =============================================================================
resource "google_compute_security_policy" "waf" {
  name = "${var.project_name}-waf-${var.environment}"

  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-stable')"
      }
    }
    description = "SQL injection protection"
  }

  rule {
    action   = "deny(403)"
    priority = "1001"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-stable')"
      }
    }
    description = "XSS protection"
  }

  rule {
    action   = "rate_based_ban"
    priority = "1002"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
      ban_duration_sec = 3600
      conform_action   = "allow"
      exceed_action    = "deny(429)"
      enforce_on_key   = "IP"
    }
    description = "Rate limiting"
  }

  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "default rule"
  }
}
