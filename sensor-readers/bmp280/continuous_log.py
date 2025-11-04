#!/usr/bin/env python3
"""
Continuous BMP280 data logger.

This script continuously reads from the BMP280 sensor at a specified
interval and logs the data to a CSV file with timestamps.
"""

import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import argparse

from bmp280_reader import BMP280Reader


def create_log_file(output_dir: Path) -> Path:
    """
    Create a new CSV log file with timestamp in filename.

    Args:
        output_dir: Directory to store the log file

    Returns:
        Path to the created log file
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"bmp280_log_{timestamp}.csv"

    # Write CSV header
    with open(log_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'temperature_celsius', 'pressure_hpa', 'altitude_meters'])

    print(f"📝 Logging to: {log_file}")
    return log_file


def log_reading(log_file: Path, sensor: BMP280Reader) -> None:
    """
    Read sensor data and append to log file.

    Args:
        log_file: Path to the CSV log file
        sensor: BMP280Reader instance
    """
    # Get current timestamp
    timestamp = datetime.now().isoformat()

    # Read sensor data
    data = sensor.read_all()

    # Append to CSV file
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            f"{data['temperature']:.2f}",
            f"{data['pressure']:.2f}",
            f"{data['altitude']:.2f}"
        ])

    # Print to console
    print(f"{timestamp} | Temp: {data['temperature']:6.2f}°C | "
          f"Press: {data['pressure']:7.2f} hPa | Alt: {data['altitude']:7.2f}m")


def main():
    """Main logging loop."""
    parser = argparse.ArgumentParser(
        description="Continuously log BMP280 sensor data to CSV file"
    )
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=60.0,
        help='Logging interval in seconds (default: 60)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        default=Path('../../data'),
        help='Output directory for log files (default: ../../data)'
    )
    parser.add_argument(
        '-a', '--address',
        type=lambda x: int(x, 16),
        default=0x76,
        help='I2C address of sensor in hex (default: 0x76)'
    )

    args = parser.parse_args()

    print("BMP280 Continuous Data Logger")
    print("=" * 60)
    print(f"Logging interval: {args.interval} seconds")
    print(f"Output directory: {args.output_dir.resolve()}")
    print()

    try:
        # Initialize sensor
        print("Initializing sensor...")
        sensor = BMP280Reader(address=args.address)
        print()

        # Create log file
        log_file = create_log_file(args.output_dir)
        print()

        print("Starting data logging... (Press Ctrl+C to stop)")
        print("-" * 60)

        # Main logging loop
        while True:
            log_reading(log_file, sensor)
            time.sleep(args.interval)

    except RuntimeError as e:
        print(f"\n❌ Sensor Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if I2C is enabled: ls /dev/i2c*")
        print("  2. Verify sensor is detected: sudo i2cdetect -y 1")
        print("  3. Check wiring connections")
        return 1

    except KeyboardInterrupt:
        print("\n")
        print("-" * 60)
        print("✓ Logging stopped by user")
        print(f"📁 Log file saved: {log_file.resolve()}")
        return 0

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
