"""
BMP280 Sensor Reader Module

This module provides a simple, clean interface for reading temperature,
pressure, and altitude data from a BMP280 sensor connected via I2C.
"""

import board
import adafruit_bmp280
from typing import Dict, Optional


class BMP280Reader:
    """
    A class to interface with the BMP280 temperature and pressure sensor.

    The BMP280 is a digital sensor that measures:
    - Temperature (in Celsius)
    - Atmospheric pressure (in hectopascals/hPa)
    - Altitude (calculated from pressure, in meters)

    Attributes:
        sensor: The Adafruit BMP280 sensor object
        address: The I2C address of the sensor (default: 0x76)
    """

    # Default I2C addresses for BMP280
    ADDRESS_PRIMARY = 0x76    # SDO pin to GND
    ADDRESS_ALTERNATE = 0x77  # SDO pin to VCC

    def __init__(self, address: int = ADDRESS_PRIMARY, sea_level_pressure: float = 1013.25):
        """
        Initialize the BMP280 sensor reader.

        Args:
            address: I2C address of the sensor (0x76 or 0x77)
            sea_level_pressure: Reference sea level pressure in hPa for altitude calculation
                              (default: 1013.25 hPa, standard atmosphere)

        Raises:
            RuntimeError: If the sensor cannot be initialized
        """
        self.address = address

        try:
            # Initialize I2C bus
            i2c = board.I2C()

            # Initialize sensor
            self.sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=address)

            # Set sea level pressure for altitude calculation
            self.sensor.sea_level_pressure = sea_level_pressure

            print(f"BMP280 sensor initialized successfully at address 0x{address:02x}")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize BMP280 sensor at address 0x{address:02x}: {e}")

    @property
    def temperature(self) -> float:
        """
        Get the current temperature reading.

        Returns:
            Temperature in degrees Celsius
        """
        return self.sensor.temperature

    @property
    def pressure(self) -> float:
        """
        Get the current pressure reading.

        Returns:
            Atmospheric pressure in hectopascals (hPa)
        """
        return self.sensor.pressure

    @property
    def altitude(self) -> float:
        """
        Get the calculated altitude.

        Note: Altitude is calculated from pressure and sea level pressure.
        It's relative to the reference sea level pressure set during initialization.

        Returns:
            Altitude in meters
        """
        return self.sensor.altitude

    def read_all(self) -> Dict[str, float]:
        """
        Read all sensor values at once.

        Returns:
            Dictionary containing temperature, pressure, and altitude:
            {
                'temperature': float,  # Celsius
                'pressure': float,     # hPa
                'altitude': float      # meters
            }
        """
        return {
            'temperature': self.temperature,
            'pressure': self.pressure,
            'altitude': self.altitude
        }

    def set_sea_level_pressure(self, pressure: float) -> None:
        """
        Update the reference sea level pressure for altitude calculations.

        You can get accurate sea level pressure for your location from
        weather services or nearby airports.

        Args:
            pressure: Sea level pressure in hPa
        """
        self.sensor.sea_level_pressure = pressure
        print(f"Sea level pressure updated to {pressure} hPa")

    def __str__(self) -> str:
        """String representation of current sensor readings."""
        data = self.read_all()
        return (
            f"BMP280 Sensor (0x{self.address:02x})\n"
            f"  Temperature: {data['temperature']:.2f} °C\n"
            f"  Pressure: {data['pressure']:.2f} hPa\n"
            f"  Altitude: {data['altitude']:.2f} m"
        )


if __name__ == "__main__":
    # Simple test when run directly
    try:
        sensor = BMP280Reader()
        print("\nCurrent readings:")
        print(sensor)
    except RuntimeError as e:
        print(f"Error: {e}")
