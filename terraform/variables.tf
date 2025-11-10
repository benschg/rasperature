# Variables for Rasperature GCP Infrastructure

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "pubsub_topic_name" {
  description = "Pub/Sub topic name for sensor data"
  type        = string
  default     = "sensor-data-raw"
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
  default     = "sensor_data"
}

variable "bigquery_table_id" {
  description = "BigQuery table ID for sensor readings"
  type        = string
  default     = "readings"
}

variable "data_retention_days" {
  description = "Number of days to retain data in BigQuery"
  type        = number
  default     = 90
}

variable "enable_bigtable" {
  description = "Enable Bigtable for real-time queries (additional cost)"
  type        = bool
  default     = false
}

variable "cloud_run_api_image" {
  description = "Docker image for Cloud Run API service"
  type        = string
  default     = "gcr.io/PROJECT_ID/rasperature-api:latest"
}

variable "api_max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 10
}

variable "api_min_instances" {
  description = "Minimum number of Cloud Run instances"
  type        = number
  default     = 0
}
