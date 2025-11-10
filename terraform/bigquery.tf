# BigQuery configuration for data warehousing

# Create dataset for sensor data
resource "google_bigquery_dataset" "sensor_data" {
  dataset_id                 = var.bigquery_dataset_id
  friendly_name              = "Sensor Data"
  description                = "Dataset containing all sensor readings and analytics"
  location                   = var.region
  default_table_expiration_ms = var.data_retention_days * 24 * 60 * 60 * 1000

  labels = {
    environment = var.environment
    component   = "storage"
  }

  depends_on = [google_project_service.required_apis]
}

# Main table for sensor readings
resource "google_bigquery_table" "readings" {
  dataset_id          = google_bigquery_dataset.sensor_data.dataset_id
  table_id            = var.bigquery_table_id
  deletion_protection = true

  labels = {
    environment = var.environment
    component   = "storage"
  }

  # Partition by timestamp (day) for query optimization and cost reduction
  time_partitioning {
    type                     = "DAY"
    field                    = "timestamp"
    expiration_ms            = var.data_retention_days * 24 * 60 * 60 * 1000
    require_partition_filter = false
  }

  # Cluster by customer_id and sensor_id for query performance
  clustering = ["customer_id", "sensor_id", "sensor_type"]

  schema = jsonencode([
    {
      name        = "timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Time when the reading was taken"
    },
    {
      name        = "sensor_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Unique sensor identifier"
    },
    {
      name        = "sensor_type"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Type of sensor (e.g., BMP280, DHT22)"
    },
    {
      name        = "device_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Raspberry Pi device identifier"
    },
    {
      name        = "customer_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Customer identifier"
    },
    {
      name        = "location"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Physical location of the sensor"
    },
    {
      name        = "status"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Reading status (ok, error)"
    },
    {
      name        = "readings"
      type        = "RECORD"
      mode        = "NULLABLE"
      description = "Sensor readings"
      fields = [
        {
          name        = "temperature"
          type        = "FLOAT64"
          mode        = "NULLABLE"
          description = "Temperature in Celsius"
        },
        {
          name        = "pressure"
          type        = "FLOAT64"
          mode        = "NULLABLE"
          description = "Atmospheric pressure in hPa"
        },
        {
          name        = "altitude"
          type        = "FLOAT64"
          mode        = "NULLABLE"
          description = "Altitude in meters"
        },
        {
          name        = "humidity"
          type        = "FLOAT64"
          mode        = "NULLABLE"
          description = "Humidity in percentage"
        }
      ]
    },
    {
      name        = "error"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Error message if status is error"
    },
    {
      name        = "error_count"
      type        = "INT64"
      mode        = "NULLABLE"
      description = "Number of consecutive errors"
    }
  ])
}

# View for recent data (last 24 hours)
resource "google_bigquery_table" "recent_readings" {
  dataset_id          = google_bigquery_dataset.sensor_data.dataset_id
  table_id            = "recent_readings"
  deletion_protection = false

  view {
    query = <<-SQL
      SELECT
        timestamp,
        sensor_id,
        sensor_type,
        device_id,
        customer_id,
        location,
        status,
        readings.temperature,
        readings.pressure,
        readings.altitude,
        readings.humidity
      FROM `${var.project_id}.${var.bigquery_dataset_id}.${var.bigquery_table_id}`
      WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        AND status = 'ok'
      ORDER BY timestamp DESC
    SQL

    use_legacy_sql = false
  }
}

# View for latest reading per sensor
resource "google_bigquery_table" "latest_readings" {
  dataset_id          = google_bigquery_dataset.sensor_data.dataset_id
  table_id            = "latest_readings"
  deletion_protection = false

  view {
    query = <<-SQL
      WITH ranked_readings AS (
        SELECT
          *,
          ROW_NUMBER() OVER (
            PARTITION BY sensor_id
            ORDER BY timestamp DESC
          ) as rn
        FROM `${var.project_id}.${var.bigquery_dataset_id}.${var.bigquery_table_id}`
        WHERE status = 'ok'
      )
      SELECT
        timestamp,
        sensor_id,
        sensor_type,
        device_id,
        customer_id,
        location,
        readings.temperature,
        readings.pressure,
        readings.altitude,
        readings.humidity
      FROM ranked_readings
      WHERE rn = 1
    SQL

    use_legacy_sql = false
  }
}

# View for hourly aggregates (useful for dashboards)
resource "google_bigquery_table" "hourly_aggregates" {
  dataset_id          = google_bigquery_dataset.sensor_data.dataset_id
  table_id            = "hourly_aggregates"
  deletion_protection = false

  view {
    query = <<-SQL
      SELECT
        TIMESTAMP_TRUNC(timestamp, HOUR) as hour,
        sensor_id,
        sensor_type,
        customer_id,
        location,
        COUNT(*) as reading_count,
        AVG(readings.temperature) as avg_temperature,
        MIN(readings.temperature) as min_temperature,
        MAX(readings.temperature) as max_temperature,
        AVG(readings.pressure) as avg_pressure,
        MIN(readings.pressure) as min_pressure,
        MAX(readings.pressure) as max_pressure,
        AVG(readings.humidity) as avg_humidity,
        AVG(readings.altitude) as avg_altitude
      FROM `${var.project_id}.${var.bigquery_dataset_id}.${var.bigquery_table_id}`
      WHERE status = 'ok'
        AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
      GROUP BY hour, sensor_id, sensor_type, customer_id, location
      ORDER BY hour DESC
    SQL

    use_legacy_sql = false
  }
}

# View for daily statistics per customer
resource "google_bigquery_table" "daily_stats_by_customer" {
  dataset_id          = google_bigquery_dataset.sensor_data.dataset_id
  table_id            = "daily_stats_by_customer"
  deletion_protection = false

  view {
    query = <<-SQL
      SELECT
        DATE(timestamp) as date,
        customer_id,
        COUNT(DISTINCT sensor_id) as active_sensors,
        COUNT(*) as total_readings,
        COUNTIF(status = 'error') as error_count,
        AVG(readings.temperature) as avg_temperature,
        AVG(readings.pressure) as avg_pressure,
        AVG(readings.humidity) as avg_humidity
      FROM `${var.project_id}.${var.bigquery_dataset_id}.${var.bigquery_table_id}`
      WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
      GROUP BY date, customer_id
      ORDER BY date DESC, customer_id
    SQL

    use_legacy_sql = false
  }
}

# Scheduled query for data aggregation (optional, requires manual setup in Console)
# This would run daily to create optimized aggregated tables
# resource "google_bigquery_data_transfer_config" "daily_aggregation" {
#   display_name           = "Daily Sensor Data Aggregation"
#   location               = var.region
#   data_source_id         = "scheduled_query"
#   schedule               = "every day 01:00"
#   destination_dataset_id = google_bigquery_dataset.sensor_data.dataset_id
#
#   params = {
#     query = <<-SQL
#       -- Your aggregation query here
#     SQL
#   }
# }
