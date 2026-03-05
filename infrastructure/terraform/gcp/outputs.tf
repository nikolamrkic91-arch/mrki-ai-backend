# =============================================================================
# Mrki GCP Infrastructure - Outputs
# =============================================================================

output "vpc_id" {
  description = "VPC network ID"
  value       = google_compute_network.vpc.id
}

output "private_subnet_id" {
  description = "Private subnet ID"
  value       = google_compute_subnetwork.private.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = google_compute_subnetwork.public.id
}

output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
}

output "gke_cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "postgres_instance_name" {
  description = "Cloud SQL PostgreSQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "postgres_private_ip" {
  description = "Cloud SQL PostgreSQL private IP"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "postgres_connection_name" {
  description = "Cloud SQL PostgreSQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.cache.host
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.cache.port
}

output "storage_bucket_assets" {
  description = "Assets storage bucket name"
  value       = google_storage_bucket.assets.name
}

output "storage_bucket_backups" {
  description = "Backups storage bucket name"
  value       = google_storage_bucket.backups.name
}

output "pubsub_events_topic" {
  description = "Pub/Sub events topic name"
  value       = google_pubsub_topic.events.name
}

output "cloud_function_processor_url" {
  description = "Cloud Function processor URL"
  value       = google_cloudfunctions2_function.processor.service_config[0].uri
}

output "cloud_armor_security_policy_id" {
  description = "Cloud Armor security policy ID"
  value       = google_compute_security_policy.waf.id
}
