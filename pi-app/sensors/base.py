"""
Base sensor class that all sensor implementations must inherit from.
This provides a common interface for all sensor types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from datetime import datetime


class BaseSensor(ABC):
    """
    Abstract base class for all sensor implementations.

    All sensor classes must implement the abstract methods to ensure
    a consistent interface across different sensor types.
    """

    def __init__(self, sensor_id: str, config: Dict[str, Any]):
        """
        Initialize the sensor.

        Args:
            sensor_id: Unique identifier for this sensor instance
            config: Configuration dictionary specific to the sensor type
        """
        self.sensor_id = sensor_id
        self.config = config
        self.last_reading = None
        self.last_reading_time = None
        self.is_active = True
        self.error_count = 0

    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the sensor hardware.

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """
        Read current values from the sensor.

        Returns:
            Dictionary containing sensor readings with keys like:
            {
                'temperature': float,
                'humidity': float,
                'pressure': float,
                etc.
            }
        """
        pass

    @abstractmethod
    def get_sensor_type(self) -> str:
        """
        Get the sensor type identifier.

        Returns:
            String identifier for the sensor type (e.g., 'BMP280', 'DHT22')
        """
        pass

    @abstractmethod
    def get_available_metrics(self) -> List[str]:
        """
        Get list of metrics this sensor can provide.

        Returns:
            List of metric names (e.g., ['temperature', 'pressure', 'altitude'])
        """
        pass

    def read_with_metadata(self) -> Dict[str, Any]:
        """
        Read sensor values and add metadata.

        Returns:
            Dictionary with sensor data and metadata
        """
        try:
            readings = self.read()
            self.last_reading = readings
            self.last_reading_time = datetime.now()
            self.error_count = 0

            return {
                'sensor_id': self.sensor_id,
                'sensor_type': self.get_sensor_type(),
                'timestamp': self.last_reading_time.isoformat(),
                'readings': readings,
                'status': 'ok'
            }
        except Exception as e:
            self.error_count += 1
            return {
                'sensor_id': self.sensor_id,
                'sensor_type': self.get_sensor_type(),
                'timestamp': datetime.now().isoformat(),
                'readings': {},
                'status': 'error',
                'error': str(e),
                'error_count': self.error_count
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the sensor.

        Returns:
            Dictionary with status information
        """
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.get_sensor_type(),
            'is_active': self.is_active,
            'last_reading_time': self.last_reading_time.isoformat() if self.last_reading_time else None,
            'last_reading': self.last_reading,
            'error_count': self.error_count,
            'config': self.config
        }

    def should_publish(self, new_reading: Dict[str, Any], threshold: Dict[str, float]) -> bool:
        """
        Determine if new reading should be published based on threshold changes.

        Args:
            new_reading: New sensor reading
            threshold: Dictionary of thresholds for each metric

        Returns:
            True if reading should be published, False otherwise
        """
        # Always publish if this is the first reading
        if self.last_reading is None:
            return True

        # Check if any metric has changed beyond threshold
        for metric, value in new_reading.items():
            if metric in self.last_reading:
                old_value = self.last_reading[metric]
                threshold_value = threshold.get(metric, 0)

                if abs(value - old_value) > threshold_value:
                    return True

        return False

    def close(self):
        """
        Clean up sensor resources.
        Override in subclass if cleanup is needed.
        """
        pass
