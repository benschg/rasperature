"""
Rasperature Cloud API - FastAPI application for querying sensor data.

This API provides endpoints for:
- Listing customers and their sensors
- Querying sensor readings (latest, historical, aggregated)
- Sensor management
- Dashboard data
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Optional
import os

from models import (
    Sensor, SensorReading, SensorStats, Customer,
    TimeRange, AggregationPeriod
)
from bigquery_client import BigQueryClient

# Initialize FastAPI app
app = FastAPI(
    title="Rasperature Cloud API",
    description="API for querying sensor data from BigQuery",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize BigQuery client
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "sensor_data")
TABLE_ID = os.getenv("BIGQUERY_TABLE", "readings")

bq_client = BigQueryClient(PROJECT_ID, DATASET_ID, TABLE_ID)


# =============================================================================
# Health Check
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "rasperature-api",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    try:
        # Test BigQuery connection
        bq_client.test_connection()
        return {
            "status": "healthy",
            "bigquery": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# =============================================================================
# Customer Endpoints
# =============================================================================

@app.get("/api/customers", response_model=List[Customer])
async def list_customers():
    """Get list of all customers with their sensor counts."""
    try:
        customers = bq_client.get_customers()
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customers/{customer_id}/sensors", response_model=List[Sensor])
async def list_customer_sensors(customer_id: str):
    """Get list of sensors for a specific customer."""
    try:
        sensors = bq_client.get_sensors_by_customer(customer_id)
        if not sensors:
            raise HTTPException(status_code=404, detail="Customer not found or has no sensors")
        return sensors
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customers/{customer_id}/stats")
async def get_customer_stats(
    customer_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to include in stats")
):
    """Get aggregate statistics for a customer."""
    try:
        stats = bq_client.get_customer_stats(customer_id, days)
        if not stats:
            raise HTTPException(status_code=404, detail="Customer not found")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Sensor Endpoints
# =============================================================================

@app.get("/api/sensors", response_model=List[Sensor])
async def list_all_sensors(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type")
):
    """Get list of all sensors, optionally filtered."""
    try:
        if customer_id:
            sensors = bq_client.get_sensors_by_customer(customer_id)
        else:
            sensors = bq_client.get_all_sensors()

        if sensor_type:
            sensors = [s for s in sensors if s.sensor_type == sensor_type]

        return sensors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sensors/{sensor_id}", response_model=Sensor)
async def get_sensor(sensor_id: str):
    """Get details for a specific sensor."""
    try:
        sensor = bq_client.get_sensor(sensor_id)
        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")
        return sensor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sensors/{sensor_id}/latest", response_model=SensorReading)
async def get_latest_reading(sensor_id: str):
    """Get the latest reading from a sensor."""
    try:
        reading = bq_client.get_latest_reading(sensor_id)
        if not reading:
            raise HTTPException(status_code=404, detail="No readings found for sensor")
        return reading
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sensors/{sensor_id}/readings", response_model=List[SensorReading])
async def get_sensor_readings(
    sensor_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO 8601)"),
    hours: int = Query(24, ge=1, le=168, description="Hours of data (if start/end not specified)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of readings")
):
    """Get historical readings for a sensor."""
    try:
        # If no start/end specified, use hours parameter
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=hours)
        if not end_time:
            end_time = datetime.utcnow()

        readings = bq_client.get_readings(sensor_id, start_time, end_time, limit)
        return readings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sensors/{sensor_id}/stats", response_model=SensorStats)
async def get_sensor_stats(
    sensor_id: str,
    hours: int = Query(24, ge=1, le=720, description="Hours to calculate stats over")
):
    """Get aggregate statistics for a sensor."""
    try:
        stats = bq_client.get_sensor_stats(sensor_id, hours)
        if not stats:
            raise HTTPException(status_code=404, detail="No data found for sensor")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@app.get("/api/dashboard/overview")
async def get_dashboard_overview(customer_id: Optional[str] = None):
    """Get overview data for dashboard."""
    try:
        overview = bq_client.get_dashboard_overview(customer_id)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/recent")
async def get_recent_readings(
    customer_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get recent readings across all sensors."""
    try:
        readings = bq_client.get_recent_readings(customer_id, limit)
        return readings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/aggregates")
async def get_aggregated_data(
    customer_id: Optional[str] = None,
    period: AggregationPeriod = Query(AggregationPeriod.HOUR, description="Aggregation period"),
    hours: int = Query(24, ge=1, le=720, description="Hours of data to aggregate")
):
    """Get aggregated sensor data for charts."""
    try:
        data = bq_client.get_aggregated_data(customer_id, period, hours)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# =============================================================================
# Startup/Shutdown
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    print(f"Starting Rasperature Cloud API")
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Table: {TABLE_ID}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    print("Shutting down Rasperature Cloud API")
    bq_client.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
