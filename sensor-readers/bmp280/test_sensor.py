#!/usr/bin/env python3
"""
Simple test script for BMP280 sensor.

This script performs a single reading from the BMP280 sensor
and displays the results. Useful for verifying the sensor is
working correctly.
"""

from bmp280_reader import BMP280Reader


def main():
    """Run a simple sensor test."""
    print("BMP280 Sensor Test")
    print("=" * 50)
    print()

    try:
        # Initialize sensor at default address (0x76)
        print("Initializing sensor...")
        sensor = BMP280Reader()
        print()

        # Read all values
        print("Reading sensor data...")
        data = sensor.read_all()
        print()

        # Display results
        print("Current Sensor Readings:")
        print("-" * 50)
        print(f"Temperature: {data['temperature']:.2f} °C")
        print(f"Pressure:    {data['pressure']:.2f} hPa")
        print(f"Altitude:    {data['altitude']:.2f} m")
        print()

        # Alternative: use the string representation
        print("Alternative display:")
        print("-" * 50)
        print(sensor)

    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check if I2C is enabled: ls /dev/i2c*")
        print("  2. Verify sensor is detected: sudo i2cdetect -y 1")
        print("  3. Check wiring:")
        print("     - VCC → 3.3V (Pin 1 or 17)")
        print("     - GND → Ground (Pin 6, 9, 14, etc.)")
        print("     - SCL → GPIO 3 (Pin 5)")
        print("     - SDA → GPIO 2 (Pin 3)")
        return 1

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        return 0

    print("✓ Test completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())
