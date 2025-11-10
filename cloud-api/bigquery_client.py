"""
BigQuery client for querying sensor data.
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import os

from models import (
    Sensor, SensorReading, SensorReadings, SensorStats, Customer,
    AggregationPeriod, AggregatedReading
)


class BigQueryClient:
    """Client for interacting with BigQuery sensor data."""

    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        """
        Initialize BigQuery client.

        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
        self.table_path = f"{project_id}.{dataset_id}.{table_id}"

    def test_connection(self):
        """Test BigQuery connection."""
        query = f"SELECT COUNT(*) as count FROM `{self.table_path}` LIMIT 1"
        self.client.query(query).result()

    def get_customers(self) -> List[Customer]:
        """Get list of all customers with their statistics."""
        query = f"""
        SELECT
            customer_id,
            COUNT(DISTINCT sensor_id) as sensor_count,
            COUNT(DISTINCT CASE WHEN status = 'ok' THEN sensor_id END) as active_sensors,
            MAX(timestamp) as last_activity,
            COUNT(*) as total_readings,
            ARRAY_AGG(DISTINCT location IGNORE NULLS) as locations
        FROM `{self.table_path}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        GROUP BY customer_id
        ORDER BY customer_id
        """

        results = self.client.query(query).result()

        customers = []
        for row in results:
            customers.append(Customer(
                customer_id=row.customer_id,
                sensor_count=row.sensor_count,
                active_sensors=row.active_sensors,
                last_activity=row.last_activity,
                total_readings=row.total_readings,
                locations=row.locations or []
            ))

        return customers

    def get_all_sensors(self) -> List[Sensor]:
        """Get list of all sensors."""
        query = f"""
        SELECT
            sensor_id,
            sensor_type,
            ANY_VALUE(device_id) as device_id,
            ANY_VALUE(customer_id) as customer_id,
            ANY_VALUE(location) as location,
            MAX(timestamp) as last_seen,
            COUNT(*) as total_readings,
            COUNTIF(timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)) > 0 as is_active
        FROM `{self.table_path}`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY sensor_id, sensor_type
        ORDER BY last_seen DESC
        """

        results = self.client.query(query).result()

        sensors = []
        for row in results:
            sensors.append(Sensor(
                sensor_id=row.sensor_id,
                sensor_type=row.sensor_type,
                device_id=row.device_id,
                customer_id=row.customer_id,
                location=row.location,
                last_seen=row.last_seen,
                total_readings=row.total_readings,
                is_active=row.is_active
            ))

        return sensors

    def get_sensors_by_customer(self, customer_id: str) -> List[Sensor]:
        """Get sensors for a specific customer."""
        query = f"""
        SELECT
            sensor_id,
            sensor_type,
            ANY_VALUE(device_id) as device_id,
            ANY_VALUE(customer_id) as customer_id,
            ANY_VALUE(location) as location,
            MAX(timestamp) as last_seen,
            COUNT(*) as total_readings,
            COUNTIF(timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)) > 0 as is_active
        FROM `{self.table_path}`
        WHERE customer_id = @customer_id
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY sensor_id, sensor_type
        ORDER BY last_seen DESC
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        sensors = []
        for row in results:
            sensors.append(Sensor(
                sensor_id=row.sensor_id,
                sensor_type=row.sensor_type,
                device_id=row.device_id,
                customer_id=row.customer_id,
                location=row.location,
                last_seen=row.last_seen,
                total_readings=row.total_readings,
                is_active=row.is_active
            ))

        return sensors

    def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Get details for a specific sensor."""
        sensors = self.get_all_sensors()
        for sensor in sensors:
            if sensor.sensor_id == sensor_id:
                return sensor
        return None

    def get_latest_reading(self, sensor_id: str) -> Optional[SensorReading]:
        """Get the latest reading for a sensor."""
        query = f"""
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
            readings.humidity,
            error
        FROM `{self.table_path}`
        WHERE sensor_id = @sensor_id
          AND status = 'ok'
        ORDER BY timestamp DESC
        LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("sensor_id", "STRING", sensor_id)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        for row in results:
            return SensorReading(
                timestamp=row.timestamp,
                sensor_id=row.sensor_id,
                sensor_type=row.sensor_type,
                device_id=row.device_id,
                customer_id=row.customer_id,
                location=row.location,
                status=row.status,
                readings=SensorReadings(
                    temperature=row.temperature,
                    pressure=row.pressure,
                    altitude=row.altitude,
                    humidity=row.humidity
                ),
                error=row.error
            )

        return None

    def get_readings(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[SensorReading]:
        """Get historical readings for a sensor."""
        query = f"""
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
            readings.humidity,
            error
        FROM `{self.table_path}`
        WHERE sensor_id = @sensor_id
          AND timestamp BETWEEN @start_time AND @end_time
          AND status = 'ok'
        ORDER BY timestamp DESC
        LIMIT @limit
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("sensor_id", "STRING", sensor_id),
                bigquery.ScalarQueryParameter("start_time", "TIMESTAMP", start_time),
                bigquery.ScalarQueryParameter("end_time", "TIMESTAMP", end_time),
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        readings = []
        for row in results:
            readings.append(SensorReading(
                timestamp=row.timestamp,
                sensor_id=row.sensor_id,
                sensor_type=row.sensor_type,
                device_id=row.device_id,
                customer_id=row.customer_id,
                location=row.location,
                status=row.status,
                readings=SensorReadings(
                    temperature=row.temperature,
                    pressure=row.pressure,
                    altitude=row.altitude,
                    humidity=row.humidity
                ),
                error=row.error
            ))

        return readings

    def get_sensor_stats(self, sensor_id: str, hours: int) -> Optional[SensorStats]:
        """Get aggregate statistics for a sensor."""
        query = f"""
        SELECT
            sensor_id,
            ANY_VALUE(sensor_type) as sensor_type,
            MIN(timestamp) as period_start,
            MAX(timestamp) as period_end,
            COUNT(*) as reading_count,
            AVG(readings.temperature) as temp_avg,
            MIN(readings.temperature) as temp_min,
            MAX(readings.temperature) as temp_max,
            STDDEV(readings.temperature) as temp_stddev,
            AVG(readings.pressure) as pressure_avg,
            MIN(readings.pressure) as pressure_min,
            MAX(readings.pressure) as pressure_max,
            STDDEV(readings.pressure) as pressure_stddev,
            AVG(readings.humidity) as humidity_avg,
            MIN(readings.humidity) as humidity_min,
            MAX(readings.humidity) as humidity_max,
            AVG(readings.altitude) as altitude_avg,
            MIN(readings.altitude) as altitude_min,
            MAX(readings.altitude) as altitude_max
        FROM `{self.table_path}`
        WHERE sensor_id = @sensor_id
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @hours HOUR)
          AND status = 'ok'
        GROUP BY sensor_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("sensor_id", "STRING", sensor_id),
                bigquery.ScalarQueryParameter("hours", "INT64", hours)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        for row in results:
            return SensorStats(
                sensor_id=row.sensor_id,
                sensor_type=row.sensor_type,
                period_start=row.period_start,
                period_end=row.period_end,
                reading_count=row.reading_count,
                temperature={
                    "avg": row.temp_avg,
                    "min": row.temp_min,
                    "max": row.temp_max,
                    "stddev": row.temp_stddev
                } if row.temp_avg is not None else None,
                pressure={
                    "avg": row.pressure_avg,
                    "min": row.pressure_min,
                    "max": row.pressure_max,
                    "stddev": row.pressure_stddev
                } if row.pressure_avg is not None else None,
                humidity={
                    "avg": row.humidity_avg,
                    "min": row.humidity_min,
                    "max": row.humidity_max
                } if row.humidity_avg is not None else None,
                altitude={
                    "avg": row.altitude_avg,
                    "min": row.altitude_min,
                    "max": row.altitude_max
                } if row.altitude_avg is not None else None
            )

        return None

    def get_customer_stats(self, customer_id: str, days: int) -> Optional[Dict[str, Any]]:
        """Get aggregate statistics for a customer."""
        query = f"""
        SELECT
            customer_id,
            COUNT(DISTINCT sensor_id) as sensor_count,
            COUNT(*) as total_readings,
            COUNTIF(status = 'error') as error_count,
            AVG(readings.temperature) as avg_temperature,
            AVG(readings.pressure) as avg_pressure,
            AVG(readings.humidity) as avg_humidity
        FROM `{self.table_path}`
        WHERE customer_id = @customer_id
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @days DAY)
        GROUP BY customer_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("customer_id", "STRING", customer_id),
                bigquery.ScalarQueryParameter("days", "INT64", days)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        for row in results:
            return {
                "customer_id": row.customer_id,
                "sensor_count": row.sensor_count,
                "total_readings": row.total_readings,
                "error_count": row.error_count,
                "avg_temperature": row.avg_temperature,
                "avg_pressure": row.avg_pressure,
                "avg_humidity": row.avg_humidity
            }

        return None

    def get_dashboard_overview(self, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Get overview statistics for dashboard."""
        where_clause = f"WHERE customer_id = '{customer_id}'" if customer_id else ""

        query = f"""
        SELECT
            COUNT(DISTINCT customer_id) as total_customers,
            COUNT(DISTINCT sensor_id) as total_sensors,
            COUNT(DISTINCT CASE WHEN timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) THEN sensor_id END) as active_sensors,
            COUNTIF(timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)) as total_readings_24h,
            AVG(CASE WHEN timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) THEN readings.temperature END) as avg_temperature,
            MAX(timestamp) as latest_reading_time
        FROM `{self.table_path}`
        {where_clause}
        """

        results = self.client.query(query).result()

        for row in results:
            return {
                "total_customers": row.total_customers,
                "total_sensors": row.total_sensors,
                "active_sensors": row.active_sensors,
                "total_readings_24h": row.total_readings_24h,
                "avg_temperature": row.avg_temperature,
                "latest_reading_time": row.latest_reading_time.isoformat() if row.latest_reading_time else None
            }

        return {}

    def get_recent_readings(self, customer_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent readings across all sensors."""
        where_clause = f"WHERE customer_id = '{customer_id}' AND" if customer_id else "WHERE"

        query = f"""
        SELECT
            timestamp,
            sensor_id,
            sensor_type,
            location,
            readings.temperature,
            readings.pressure,
            readings.altitude,
            readings.humidity
        FROM `{self.table_path}`
        {where_clause} status = 'ok'
        ORDER BY timestamp DESC
        LIMIT @limit
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        readings = []
        for row in results:
            readings.append({
                "timestamp": row.timestamp.isoformat(),
                "sensor_id": row.sensor_id,
                "sensor_type": row.sensor_type,
                "location": row.location,
                "temperature": row.temperature,
                "pressure": row.pressure,
                "altitude": row.altitude,
                "humidity": row.humidity
            })

        return readings

    def get_aggregated_data(
        self,
        customer_id: Optional[str],
        period: AggregationPeriod,
        hours: int
    ) -> List[Dict[str, Any]]:
        """Get aggregated sensor data for charts."""
        where_clause = f"WHERE customer_id = '{customer_id}' AND" if customer_id else "WHERE"

        # Determine aggregation period
        if period == AggregationPeriod.MINUTE:
            trunc_function = "MINUTE"
        elif period == AggregationPeriod.HOUR:
            trunc_function = "HOUR"
        else:  # DAY
            trunc_function = "DAY"

        query = f"""
        SELECT
            TIMESTAMP_TRUNC(timestamp, {trunc_function}) as period,
            sensor_id,
            sensor_type,
            COUNT(*) as reading_count,
            AVG(readings.temperature) as temperature_avg,
            MIN(readings.temperature) as temperature_min,
            MAX(readings.temperature) as temperature_max,
            AVG(readings.pressure) as pressure_avg,
            AVG(readings.humidity) as humidity_avg,
            AVG(readings.altitude) as altitude_avg
        FROM `{self.table_path}`
        {where_clause} status = 'ok'
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @hours HOUR)
        GROUP BY period, sensor_id, sensor_type
        ORDER BY period DESC, sensor_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("hours", "INT64", hours)
            ]
        )

        results = self.client.query(query, job_config=job_config).result()

        data = []
        for row in results:
            data.append({
                "timestamp": row.period.isoformat(),
                "sensor_id": row.sensor_id,
                "sensor_type": row.sensor_type,
                "reading_count": row.reading_count,
                "temperature_avg": row.temperature_avg,
                "temperature_min": row.temperature_min,
                "temperature_max": row.temperature_max,
                "pressure_avg": row.pressure_avg,
                "humidity_avg": row.humidity_avg,
                "altitude_avg": row.altitude_avg
            })

        return data

    def close(self):
        """Close the BigQuery client."""
        self.client.close()
