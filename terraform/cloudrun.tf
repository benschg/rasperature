# Cloud Run configuration for API service

# Note: This configuration assumes you've built and pushed the Docker image
# Run: gcloud builds submit --tag gcr.io/PROJECT_ID/rasperature-api

resource "google_cloud_run_service" "api" {
  name     = "rasperature-api"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.api_service.email

      containers {
        image = var.cloud_run_api_image

        # Environment variables
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "BIGQUERY_DATASET"
          value = google_bigquery_dataset.sensor_data.dataset_id
        }

        env {
          name  = "BIGQUERY_TABLE"
          value = google_bigquery_table.readings.table_id
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        # Resource limits
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }

        # Health check
        ports {
          container_port = 8080
        }
      }

      # Autoscaling
      container_concurrency = 80
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = tostring(var.api_min_instances)
        "autoscaling.knative.dev/maxScale" = tostring(var.api_max_instances)
      }

      labels = {
        environment = var.environment
        component   = "api"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_project_service.required_apis,
    google_project_iam_member.api_bigquery_viewer,
    google_project_iam_member.api_bigquery_user
  ]
}

# Make API publicly accessible (or configure IAM for authenticated access)
resource "google_cloud_run_service_iam_member" "api_public_access" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"

  # For production, use authenticated access instead:
  # member = "serviceAccount:${google_service_account.web_app.email}"
}

# Output the API URL
output "api_url" {
  value       = google_cloud_run_service.api.status[0].url
  description = "URL of the Cloud Run API service"
}
