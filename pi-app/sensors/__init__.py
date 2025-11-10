"""
Sensor module package.

This package provides a unified interface for various sensor types.
Each sensor implements the BaseSensor abstract class.
"""

from .base import BaseSensor
from .bmp280 import BMP280Sensor
from .dht22 import DHT22Sensor

# Registry of available sensor types
SENSOR_TYPES = {
    'BMP280': {
        'class': BMP280Sensor,
        'name': 'BMP280 Temperature & Pressure',
        'metrics': ['temperature', 'pressure', 'altitude'],
        'default_config': {
            'address': 0x76,
            'sea_level_pressure': 1013.25
        },
        'config_schema': {
            'address': {
                'type': 'select',
                'options': [0x76, 0x77],
                'label': 'I2C Address',
                'description': 'I2C address (0x76 if SDO to GND, 0x77 if SDO to VCC)'
            },
            'sea_level_pressure': {
                'type': 'number',
                'label': 'Sea Level Pressure (hPa)',
                'description': 'Reference pressure for altitude calculation',
                'min': 900,
                'max': 1100,
                'step': 0.1
            }
        },
        'status': 'available'
    },
    'DHT22': {
        'class': DHT22Sensor,
        'name': 'DHT22 Temperature & Humidity',
        'metrics': ['temperature', 'humidity'],
        'default_config': {
            'pin': 4
        },
        'config_schema': {
            'pin': {
                'type': 'number',
                'label': 'GPIO Pin (BCM)',
                'description': 'GPIO pin number (BCM numbering)',
                'min': 2,
                'max': 27,
                'step': 1
            }
        },
        'status': 'coming_soon'
    }
}


def get_sensor_class(sensor_type: str):
    """
    Get sensor class by type name.

    Args:
        sensor_type: Type of sensor (e.g., 'BMP280', 'DHT22')

    Returns:
        Sensor class

    Raises:
        ValueError: If sensor type not found
    """
    if sensor_type not in SENSOR_TYPES:
        raise ValueError(f"Unknown sensor type: {sensor_type}")

    return SENSOR_TYPES[sensor_type]['class']


def get_available_sensors():
    """
    Get list of available sensor types with metadata.

    Returns:
        Dictionary of sensor types with their metadata
    """
    return SENSOR_TYPES


__all__ = ['BaseSensor', 'BMP280Sensor', 'DHT22Sensor', 'SENSOR_TYPES', 'get_sensor_class', 'get_available_sensors']
