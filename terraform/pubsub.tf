# Pub/Sub configuration for sensor data ingestion

# Main topic for raw sensor data
resource "google_pubsub_topic" "sensor_data" {
  name = var.pubsub_topic_name

  labels = {
    environment = var.environment
    component   = "ingestion"
  }

  message_retention_duration = "86400s" # 24 hours

  depends_on = [google_project_service.required_apis]
}

# Subscription for BigQuery streaming
resource "google_pubsub_subscription" "bigquery_sink" {
  name  = "${var.pubsub_topic_name}-to-bigquery"
  topic = google_pubsub_topic.sensor_data.name

  # Use BigQuery subscription for direct streaming
  bigquery_config {
    table               = "${var.project_id}.${google_bigquery_dataset.sensor_data.dataset_id}.${google_bigquery_table.readings.table_id}"
    use_topic_schema    = false
    write_metadata      = true
    drop_unknown_fields = false
  }

  # Message retention for 7 days
  message_retention_duration = "604800s" # 7 days

  # Retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  # Enable exactly once delivery
  enable_exactly_once_delivery = true

  labels = {
    environment = var.environment
    component   = "ingestion"
  }
}

# Dead letter topic for failed messages
resource "google_pubsub_topic" "dead_letter" {
  name = "${var.pubsub_topic_name}-dead-letter"

  labels = {
    environment = var.environment
    component   = "ingestion"
  }

  message_retention_duration = "2592000s" # 30 days
}

# Dead letter subscription
resource "google_pubsub_subscription" "dead_letter_sub" {
  name  = "${var.pubsub_topic_name}-dead-letter-sub"
  topic = google_pubsub_topic.dead_letter.name

  # Keep messages for investigation
  message_retention_duration = "2592000s" # 30 days
  ack_deadline_seconds       = 600

  labels = {
    environment = var.environment
    component   = "ingestion"
  }
}

# Optional: Subscription for real-time processing (Cloud Functions/Cloud Run)
resource "google_pubsub_subscription" "realtime_processing" {
  name  = "${var.pubsub_topic_name}-realtime"
  topic = google_pubsub_topic.sensor_data.name

  # Push to Cloud Run endpoint (configure after deploying Cloud Run)
  # push_config {
  #   push_endpoint = google_cloud_run_service.api.status[0].url
  #   oidc_token {
  #     service_account_email = google_service_account.api_service.email
  #   }
  # }

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s" # 7 days

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  # Dead letter policy
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  labels = {
    environment = var.environment
    component   = "realtime"
  }
}

# Grant Pub/Sub permission to write to BigQuery
resource "google_project_iam_member" "pubsub_bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# Get project number
data "google_project" "project" {
  project_id = var.project_id
}

# Grant permission to publish to dead letter topic
resource "google_pubsub_topic_iam_member" "dead_letter_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.dead_letter.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

# Grant permission to subscribe to dead letter topic
resource "google_pubsub_subscription_iam_member" "dead_letter_subscriber" {
  project      = var.project_id
  subscription = google_pubsub_subscription.dead_letter_sub.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}
