"""
BMP280 Sensor implementation.
"""

import board
import adafruit_bmp280
from typing import Dict, List, Any

from .base import BaseSensor


class BMP280Sensor(BaseSensor):
    """
    BMP280 temperature and pressure sensor implementation.

    Measures:
    - Temperature (Celsius)
    - Atmospheric pressure (hPa)
    - Altitude (meters, calculated from pressure)
    """

    def __init__(self, sensor_id: str, config: Dict[str, Any]):
        """
        Initialize BMP280 sensor.

        Args:
            sensor_id: Unique identifier for this sensor
            config: Configuration dictionary with keys:
                - address: I2C address (0x76 or 0x77)
                - sea_level_pressure: Reference pressure for altitude (default: 1013.25)
        """
        super().__init__(sensor_id, config)
        self.sensor = None
        self.address = config.get('address', 0x76)
        self.sea_level_pressure = config.get('sea_level_pressure', 1013.25)

    def initialize(self) -> bool:
        """
        Initialize the BMP280 sensor hardware.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize I2C bus
            i2c = board.I2C()

            # Initialize sensor
            self.sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=self.address)

            # Set sea level pressure for altitude calculation
            self.sensor.sea_level_pressure = self.sea_level_pressure

            print(f"✓ BMP280 sensor '{self.sensor_id}' initialized at address 0x{self.address:02x}")
            return True

        except Exception as e:
            print(f"✗ Failed to initialize BMP280 sensor '{self.sensor_id}': {e}")
            self.is_active = False
            return False

    def read(self) -> Dict[str, Any]:
        """
        Read current values from BMP280 sensor.

        Returns:
            Dictionary with temperature, pressure, and altitude
        """
        if not self.sensor:
            raise RuntimeError("Sensor not initialized")

        return {
            'temperature': round(self.sensor.temperature, 2),
            'pressure': round(self.sensor.pressure, 2),
            'altitude': round(self.sensor.altitude, 2)
        }

    def get_sensor_type(self) -> str:
        """Get sensor type identifier."""
        return 'BMP280'

    def get_available_metrics(self) -> List[str]:
        """Get list of available metrics."""
        return ['temperature', 'pressure', 'altitude']

    def set_sea_level_pressure(self, pressure: float):
        """
        Update reference sea level pressure for altitude calculations.

        Args:
            pressure: Sea level pressure in hPa
        """
        self.sea_level_pressure = pressure
        if self.sensor:
            self.sensor.sea_level_pressure = pressure
            print(f"Sea level pressure updated to {pressure} hPa for sensor '{self.sensor_id}'")
