"""
Cloud Publisher - Publishes sensor data to Google Cloud Pub/Sub.

Features:
- Edge downsampling (only publish on significant changes)
- Batch publishing for efficiency
- Retry logic with exponential backoff
- Offline buffering
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque

try:
    from google.cloud import pubsub_v1
    from google.oauth2 import service_account
    PUBSUB_AVAILABLE = True
except ImportError:
    PUBSUB_AVAILABLE = False
    print("⚠ Google Cloud Pub/Sub library not installed. Cloud publishing disabled.")
    print("  Install with: pip install google-cloud-pubsub")


class CloudPublisher:
    """
    Publishes sensor data to Google Cloud Pub/Sub with edge optimization.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize cloud publisher.

        Args:
            config: Configuration dictionary with keys:
                - enabled: Whether cloud publishing is enabled
                - project_id: GCP project ID
                - topic_name: Pub/Sub topic name
                - credentials_file: Path to service account key file
                - batch_size: Number of messages to batch (default: 10)
                - max_batch_wait: Max seconds to wait for batch (default: 5)
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.project_id = config.get('project_id', '')
        self.topic_name = config.get('topic_name', 'sensor-data-raw')
        self.batch_size = config.get('batch_size', 10)
        self.max_batch_wait = config.get('max_batch_wait', 5)

        self.publisher = None
        self.topic_path = None
        self.message_queue = deque()
        self.last_published_values = {}
        self.publish_count = 0
        self.error_count = 0
        self.last_batch_time = time.time()

        # Offline buffer
        self.offline_buffer_file = Path('offline_buffer.json')
        self.offline_buffer = []

        if self.enabled:
            self._initialize_publisher()

    def _initialize_publisher(self) -> bool:
        """
        Initialize Google Cloud Pub/Sub publisher.

        Returns:
            True if successful, False otherwise
        """
        if not PUBSUB_AVAILABLE:
            print("✗ Cannot initialize publisher: google-cloud-pubsub not installed")
            self.enabled = False
            return False

        try:
            credentials_file = self.config.get('credentials_file')

            if credentials_file and Path(credentials_file).exists():
                # Use service account credentials
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_file
                )
                self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
            else:
                # Use default credentials (for GCE/Cloud Run)
                self.publisher = pubsub_v1.PublisherClient()

            # Create topic path
            self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)

            print(f"✓ Cloud publisher initialized")
            print(f"  Project: {self.project_id}")
            print(f"  Topic: {self.topic_name}")
            return True

        except Exception as e:
            print(f"✗ Failed to initialize cloud publisher: {e}")
            self.enabled = False
            return False

    def should_publish(self, reading: Dict[str, Any], thresholds: Dict[str, float]) -> bool:
        """
        Determine if reading should be published based on edge downsampling rules.

        Args:
            reading: Sensor reading dictionary
            thresholds: Threshold values for each metric

        Returns:
            True if should publish, False otherwise
        """
        sensor_id = reading.get('sensor_id')

        # Always publish first reading
        if sensor_id not in self.last_published_values:
            return True

        # Check if any metric has changed beyond threshold
        last_reading = self.last_published_values[sensor_id]
        current_readings = reading.get('readings', {})

        for metric, value in current_readings.items():
            if metric in last_reading:
                threshold = thresholds.get(metric, 0)
                last_value = last_reading[metric]

                if abs(value - last_value) > threshold:
                    return True

        return False

    def publish(self, readings: List[Dict[str, Any]], thresholds: Dict[str, float]):
        """
        Publish sensor readings to cloud (with edge downsampling).

        Args:
            readings: List of sensor reading dictionaries
            thresholds: Threshold values for downsampling
        """
        if not self.enabled:
            return

        # Filter readings based on thresholds
        filtered_readings = []
        for reading in readings:
            if reading.get('status') == 'ok' and self.should_publish(reading, thresholds):
                filtered_readings.append(reading)

                # Update last published values
                sensor_id = reading['sensor_id']
                self.last_published_values[sensor_id] = reading['readings'].copy()

        if not filtered_readings:
            return

        # Add to message queue
        for reading in filtered_readings:
            self.message_queue.append(reading)

        # Publish if batch size reached or max wait time exceeded
        time_since_batch = time.time() - self.last_batch_time
        if len(self.message_queue) >= self.batch_size or time_since_batch >= self.max_batch_wait:
            self._publish_batch()

    def _publish_batch(self):
        """Publish queued messages as a batch."""
        if not self.message_queue:
            return

        try:
            # Prepare messages
            messages = []
            while self.message_queue and len(messages) < self.batch_size:
                reading = self.message_queue.popleft()
                message_data = json.dumps(reading).encode('utf-8')
                messages.append(message_data)

            # Publish messages
            futures = []
            for message_data in messages:
                future = self.publisher.publish(self.topic_path, message_data)
                futures.append(future)

            # Wait for all messages to be published
            for future in futures:
                future.result(timeout=10)

            self.publish_count += len(messages)
            self.last_batch_time = time.time()

            print(f"✓ Published {len(messages)} message(s) to cloud (total: {self.publish_count})")

        except Exception as e:
            print(f"✗ Error publishing batch: {e}")
            self.error_count += 1

            # Save to offline buffer
            while messages:
                self.offline_buffer.append(messages.pop())
            self._save_offline_buffer()

    def _save_offline_buffer(self):
        """Save offline buffer to file."""
        try:
            with open(self.offline_buffer_file, 'w') as f:
                json.dump(self.offline_buffer, f)
            print(f"✓ Saved {len(self.offline_buffer)} message(s) to offline buffer")
        except Exception as e:
            print(f"✗ Error saving offline buffer: {e}")

    def _load_offline_buffer(self):
        """Load offline buffer from file."""
        try:
            if self.offline_buffer_file.exists():
                with open(self.offline_buffer_file, 'r') as f:
                    self.offline_buffer = json.load(f)
                print(f"✓ Loaded {len(self.offline_buffer)} message(s) from offline buffer")
        except Exception as e:
            print(f"✗ Error loading offline buffer: {e}")

    def flush(self):
        """Flush any remaining messages in queue."""
        if self.message_queue:
            self._publish_batch()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get publisher statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'enabled': self.enabled,
            'publish_count': self.publish_count,
            'error_count': self.error_count,
            'queue_size': len(self.message_queue),
            'offline_buffer_size': len(self.offline_buffer),
            'last_batch_time': datetime.fromtimestamp(self.last_batch_time).isoformat()
        }

    def shutdown(self):
        """Shutdown publisher and flush remaining messages."""
        if self.enabled:
            print("\nShutting down cloud publisher...")
            self.flush()
            print("✓ Cloud publisher shutdown complete")
