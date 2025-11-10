"""
Data models for the Rasperature Cloud API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AggregationPeriod(str, Enum):
    """Time period for data aggregation."""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


class TimeRange(BaseModel):
    """Time range for queries."""
    start: datetime
    end: datetime


class SensorReadings(BaseModel):
    """Individual sensor readings."""
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    altitude: Optional[float] = None
    humidity: Optional[float] = None


class SensorReading(BaseModel):
    """Complete sensor reading with metadata."""
    timestamp: datetime
    sensor_id: str
    sensor_type: str
    device_id: str
    customer_id: str
    location: Optional[str] = None
    readings: SensorReadings
    status: str = "ok"
    error: Optional[str] = None


class Sensor(BaseModel):
    """Sensor information."""
    sensor_id: str
    sensor_type: str
    device_id: str
    customer_id: str
    location: Optional[str] = None
    last_seen: Optional[datetime] = None
    total_readings: int = 0
    is_active: bool = True


class SensorStats(BaseModel):
    """Aggregate statistics for a sensor."""
    sensor_id: str
    sensor_type: str
    period_start: datetime
    period_end: datetime
    reading_count: int
    temperature: Optional[Dict[str, float]] = None  # min, max, avg, stddev
    pressure: Optional[Dict[str, float]] = None
    humidity: Optional[Dict[str, float]] = None
    altitude: Optional[Dict[str, float]] = None


class Customer(BaseModel):
    """Customer information."""
    customer_id: str
    sensor_count: int
    active_sensors: int
    last_activity: Optional[datetime] = None
    total_readings: int = 0
    locations: list[str] = []


class DashboardOverview(BaseModel):
    """Dashboard overview statistics."""
    total_customers: int
    total_sensors: int
    active_sensors: int
    total_readings_24h: int
    avg_temperature: Optional[float] = None
    latest_reading_time: Optional[datetime] = None


class AggregatedReading(BaseModel):
    """Aggregated sensor reading."""
    timestamp: datetime
    sensor_id: str
    reading_count: int
    temperature_avg: Optional[float] = None
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    pressure_avg: Optional[float] = None
    humidity_avg: Optional[float] = None
    altitude_avg: Optional[float] = None
