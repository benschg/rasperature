# Main Terraform configuration for Rasperature GCP Infrastructure

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Uncomment to use GCS backend for state storage
  # backend "gcs" {
  #   bucket = "YOUR_STATE_BUCKET"
  #   prefix = "terraform/rasperature"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "pubsub.googleapis.com",
    "bigquery.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# Create a service account for Raspberry Pi devices
resource "google_service_account" "pi_publisher" {
  account_id   = "rasperature-pi-publisher"
  display_name = "Rasperature Raspberry Pi Publisher"
  description  = "Service account for Raspberry Pi devices to publish sensor data"
}

# Create a service account for Cloud Run API
resource "google_service_account" "api_service" {
  account_id   = "rasperature-api"
  display_name = "Rasperature API Service"
  description  = "Service account for Cloud Run API service"
}

# Grant Pub/Sub publisher role to Pi service account
resource "google_project_iam_member" "pi_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.pi_publisher.email}"
}

# Grant BigQuery data viewer role to API service account
resource "google_project_iam_member" "api_bigquery_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.api_service.email}"
}

# Grant BigQuery job user role to API service account
resource "google_project_iam_member" "api_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.api_service.email}"
}

# Outputs
output "project_id" {
  value       = var.project_id
  description = "GCP Project ID"
}

output "region" {
  value       = var.region
  description = "GCP Region"
}

output "pubsub_topic_name" {
  value       = google_pubsub_topic.sensor_data.name
  description = "Pub/Sub topic name"
}

output "bigquery_dataset_id" {
  value       = google_bigquery_dataset.sensor_data.dataset_id
  description = "BigQuery dataset ID"
}

output "bigquery_table_id" {
  value       = google_bigquery_table.readings.table_id
  description = "BigQuery table ID"
}

output "pi_service_account_email" {
  value       = google_service_account.pi_publisher.email
  description = "Service account email for Raspberry Pi devices"
}

output "api_service_account_email" {
  value       = google_service_account.api_service.email
  description = "Service account email for API service"
}
