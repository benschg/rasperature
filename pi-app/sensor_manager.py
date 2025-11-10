"""
Sensor Manager - Manages multiple sensors and their lifecycle.
"""

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from sensors import get_sensor_class, get_available_sensors


class SensorManager:
    """
    Manages multiple sensor instances, their configuration, and data collection.
    """

    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize the sensor manager.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.sensors: Dict[str, Any] = {}
        self.config = self.load_config()
        self.is_running = False
        self.collection_thread = None
        self.data_callback = None

    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    print(f"✓ Configuration loaded from {self.config_file}")
                    return config
            except Exception as e:
                print(f"⚠ Error loading configuration: {e}")

        # Default configuration
        default_config = {
            'device_id': 'rpi_001',
            'customer_id': 'customer_001',
            'location': 'unknown',
            'update_frequency': 60,  # seconds
            'sensors': [],
            'cloud': {
                'enabled': False,
                'project_id': '',
                'topic_name': 'sensor-data-raw',
                'credentials_file': ''
            },
            'thresholds': {
                'temperature': 0.5,  # °C
                'pressure': 2.0,     # hPa
                'humidity': 2.0,     # %
                'altitude': 5.0      # meters
            }
        }

        # Save default configuration
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary (uses current config if None)
        """
        if config is None:
            config = self.config

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✓ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"✗ Error saving configuration: {e}")

    def add_sensor(self, sensor_id: str, sensor_type: str, sensor_config: Dict[str, Any]) -> bool:
        """
        Add a new sensor.

        Args:
            sensor_id: Unique identifier for the sensor
            sensor_type: Type of sensor (e.g., 'BMP280')
            sensor_config: Configuration specific to the sensor type

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if sensor already exists
            if sensor_id in self.sensors:
                print(f"⚠ Sensor '{sensor_id}' already exists")
                return False

            # Get sensor class
            sensor_class = get_sensor_class(sensor_type)

            # Create sensor instance
            sensor = sensor_class(sensor_id, sensor_config)

            # Initialize sensor hardware
            if not sensor.initialize():
                return False

            # Add to sensors dictionary
            self.sensors[sensor_id] = sensor

            # Add to config
            self.config['sensors'].append({
                'id': sensor_id,
                'type': sensor_type,
                'config': sensor_config,
                'added_at': datetime.now().isoformat()
            })
            self.save_config()

            print(f"✓ Sensor '{sensor_id}' added successfully")
            return True

        except Exception as e:
            print(f"✗ Error adding sensor '{sensor_id}': {e}")
            return False

    def remove_sensor(self, sensor_id: str) -> bool:
        """
        Remove a sensor.

        Args:
            sensor_id: ID of sensor to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            if sensor_id not in self.sensors:
                print(f"⚠ Sensor '{sensor_id}' not found")
                return False

            # Clean up sensor
            self.sensors[sensor_id].close()
            del self.sensors[sensor_id]

            # Remove from config
            self.config['sensors'] = [
                s for s in self.config['sensors'] if s['id'] != sensor_id
            ]
            self.save_config()

            print(f"✓ Sensor '{sensor_id}' removed")
            return True

        except Exception as e:
            print(f"✗ Error removing sensor '{sensor_id}': {e}")
            return False

    def get_sensor(self, sensor_id: str):
        """Get sensor instance by ID."""
        return self.sensors.get(sensor_id)

    def get_all_sensors(self) -> Dict[str, Any]:
        """Get all sensor instances."""
        return self.sensors

    def get_sensor_status(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific sensor.

        Args:
            sensor_id: ID of sensor

        Returns:
            Status dictionary or None if not found
        """
        sensor = self.get_sensor(sensor_id)
        if sensor:
            return sensor.get_status()
        return None

    def get_all_sensor_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all sensors.

        Returns:
            List of status dictionaries
        """
        return [sensor.get_status() for sensor in self.sensors.values()]

    def read_sensor(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Read data from a specific sensor.

        Args:
            sensor_id: ID of sensor

        Returns:
            Reading dictionary with metadata or None if not found
        """
        sensor = self.get_sensor(sensor_id)
        if sensor and sensor.is_active:
            return sensor.read_with_metadata()
        return None

    def read_all_sensors(self) -> List[Dict[str, Any]]:
        """
        Read data from all active sensors.

        Returns:
            List of reading dictionaries
        """
        readings = []
        for sensor in self.sensors.values():
            if sensor.is_active:
                reading = sensor.read_with_metadata()
                readings.append(reading)
        return readings

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration settings.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            True if successful
        """
        try:
            # Update configuration
            self.config.update(updates)
            self.save_config()

            # Restart collection if frequency changed
            if 'update_frequency' in updates and self.is_running:
                self.stop_collection()
                self.start_collection()

            print(f"✓ Configuration updated")
            return True

        except Exception as e:
            print(f"✗ Error updating configuration: {e}")
            return False

    def set_data_callback(self, callback):
        """
        Set callback function for data collection.

        Args:
            callback: Function to call with sensor readings
        """
        self.data_callback = callback

    def start_collection(self):
        """Start automatic data collection."""
        if self.is_running:
            print("⚠ Collection already running")
            return

        self.is_running = True
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        print(f"✓ Data collection started (interval: {self.config['update_frequency']}s)")

    def stop_collection(self):
        """Stop automatic data collection."""
        if not self.is_running:
            return

        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        print("✓ Data collection stopped")

    def _collection_loop(self):
        """Internal collection loop (runs in separate thread)."""
        while self.is_running:
            try:
                # Read all sensors
                readings = self.read_all_sensors()

                # Add device metadata
                for reading in readings:
                    reading['device_id'] = self.config['device_id']
                    reading['customer_id'] = self.config['customer_id']
                    reading['location'] = self.config['location']

                # Call callback if set
                if self.data_callback and readings:
                    self.data_callback(readings)

            except Exception as e:
                print(f"✗ Error in collection loop: {e}")

            # Sleep for configured interval
            time.sleep(self.config['update_frequency'])

    def initialize_from_config(self):
        """Initialize all sensors from configuration file."""
        for sensor_config in self.config['sensors']:
            sensor_id = sensor_config['id']
            sensor_type = sensor_config['type']
            config = sensor_config['config']

            print(f"Initializing sensor '{sensor_id}' ({sensor_type})...")
            self.add_sensor(sensor_id, sensor_type, config)

    def shutdown(self):
        """Shutdown sensor manager and cleanup resources."""
        print("\nShutting down sensor manager...")

        # Stop collection
        self.stop_collection()

        # Close all sensors
        for sensor_id in list(self.sensors.keys()):
            sensor = self.sensors[sensor_id]
            sensor.close()

        print("✓ Sensor manager shutdown complete")

    def get_available_sensor_types(self):
        """Get list of available sensor types."""
        return get_available_sensors()
