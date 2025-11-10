# Monitoring and alerting configuration

# Alert policy for high error rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Sensor Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 10%"

    condition_threshold {
      filter          = "resource.type=\"global\" AND metric.type=\"custom.googleapis.com/sensor/error_rate\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.1

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = []

  documentation {
    content = "Sensor error rate has exceeded 10%. Check sensor connectivity and hardware."
  }

  enabled = true
}

# Alert policy for data ingestion lag
resource "google_monitoring_alert_policy" "data_lag" {
  display_name = "Data Ingestion Lag"
  combiner     = "OR"

  conditions {
    display_name = "No data received in 10 minutes"

    condition_threshold {
      filter          = "resource.type=\"pubsub_topic\" AND resource.label.topic_id=\"${var.pubsub_topic_name}\" AND metric.type=\"pubsub.googleapis.com/topic/send_message_operation_count\""
      duration        = "600s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = []

  documentation {
    content = "No sensor data has been received in the last 10 minutes. Check Raspberry Pi connectivity."
  }

  enabled = true
}

# Alert policy for Cloud Run API errors
resource "google_monitoring_alert_policy" "api_errors" {
  display_name = "API Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "5xx error rate > 5%"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${google_cloud_run_service.api.name}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = []

  documentation {
    content = "API is experiencing high error rates. Check Cloud Run logs for details."
  }

  enabled = true
}

# Dashboard for monitoring (JSON configuration)
resource "google_monitoring_dashboard" "main" {
  dashboard_json = jsonencode({
    displayName = "Rasperature Monitoring"
    gridLayout = {
      widgets = [
        {
          title = "Pub/Sub Message Rate"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"pubsub_topic\" AND resource.label.topic_id=\"${var.pubsub_topic_name}\" AND metric.type=\"pubsub.googleapis.com/topic/send_message_operation_count\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        },
        {
          title = "BigQuery Data Ingested"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"bigquery_dataset\" AND resource.label.dataset_id=\"${var.bigquery_dataset_id}\" AND metric.type=\"bigquery.googleapis.com/storage/stored_bytes\""
                  aggregation = {
                    alignmentPeriod  = "3600s"
                    perSeriesAligner = "ALIGN_MEAN"
                  }
                }
              }
            }]
          }
        },
        {
          title = "Cloud Run Request Count"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${google_cloud_run_service.api.name}\" AND metric.type=\"run.googleapis.com/request_count\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        },
        {
          title = "Cloud Run Response Latency"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${google_cloud_run_service.api.name}\" AND metric.type=\"run.googleapis.com/request_latencies\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_DELTA"
                  }
                }
              }
            }]
          }
        }
      ]
    }
  })
}

# Budget alert (optional)
# Uncomment and configure if you want budget alerts
# resource "google_billing_budget" "budget" {
#   billing_account = "YOUR_BILLING_ACCOUNT_ID"
#   display_name    = "Rasperature Monthly Budget"
#
#   budget_filter {
#     projects = ["projects/${data.google_project.project.number}"]
#   }
#
#   amount {
#     specified_amount {
#       currency_code = "USD"
#       units         = "100"
#     }
#   }
#
#   threshold_rules {
#     threshold_percent = 0.5
#   }
#
#   threshold_rules {
#     threshold_percent = 0.9
#   }
#
#   threshold_rules {
#     threshold_percent = 1.0
#   }
# }
