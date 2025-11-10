#!/usr/bin/env python3
"""
Rasperature Pi Application - Web interface for sensor configuration and monitoring.

This Flask application provides:
- Sensor management (add/remove/configure)
- Real-time sensor readings
- Cloud configuration
- System settings
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import signal
import sys
import atexit
from pathlib import Path

from sensor_manager import SensorManager
from cloud_publisher import CloudPublisher

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# Initialize sensor manager
sensor_manager = SensorManager('config.json')
cloud_publisher = None


def initialize_cloud_publisher():
    """Initialize cloud publisher if enabled."""
    global cloud_publisher

    if sensor_manager.config.get('cloud', {}).get('enabled', False):
        cloud_publisher = CloudPublisher(sensor_manager.config['cloud'])

        # Set callback to publish data
        def publish_callback(readings):
            if cloud_publisher:
                thresholds = sensor_manager.config.get('thresholds', {})
                cloud_publisher.publish(readings, thresholds)

        sensor_manager.set_data_callback(publish_callback)


# ============================================================================
# Web Routes
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/sensors')
def sensors_page():
    """Sensor management page."""
    return render_template('sensors.html')


@app.route('/config')
def config_page():
    """Configuration page."""
    return render_template('config.html')


# ============================================================================
# API Routes - System Info
# ============================================================================

@app.route('/api/info', methods=['GET'])
def get_info():
    """Get system information."""
    return jsonify({
        'device_id': sensor_manager.config.get('device_id'),
        'customer_id': sensor_manager.config.get('customer_id'),
        'location': sensor_manager.config.get('location'),
        'update_frequency': sensor_manager.config.get('update_frequency'),
        'is_collecting': sensor_manager.is_running,
        'cloud_enabled': sensor_manager.config.get('cloud', {}).get('enabled', False),
        'sensor_count': len(sensor_manager.sensors)
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics."""
    stats = {
        'sensor_count': len(sensor_manager.sensors),
        'active_sensors': sum(1 for s in sensor_manager.sensors.values() if s.is_active),
        'is_collecting': sensor_manager.is_running,
        'update_frequency': sensor_manager.config.get('update_frequency'),
    }

    if cloud_publisher:
        stats['cloud'] = cloud_publisher.get_stats()

    return jsonify(stats)


# ============================================================================
# API Routes - Sensors
# ============================================================================

@app.route('/api/sensors', methods=['GET'])
def list_sensors():
    """Get list of all sensors."""
    sensors = sensor_manager.get_all_sensor_status()
    return jsonify(sensors)


@app.route('/api/sensors/<sensor_id>', methods=['GET'])
def get_sensor(sensor_id):
    """Get specific sensor information."""
    status = sensor_manager.get_sensor_status(sensor_id)
    if status:
        return jsonify(status)
    return jsonify({'error': 'Sensor not found'}), 404


@app.route('/api/sensors', methods=['POST'])
def add_sensor():
    """Add a new sensor."""
    data = request.json
    sensor_id = data.get('sensor_id')
    sensor_type = data.get('sensor_type')
    sensor_config = data.get('config', {})

    if not sensor_id or not sensor_type:
        return jsonify({'error': 'sensor_id and sensor_type required'}), 400

    success = sensor_manager.add_sensor(sensor_id, sensor_type, sensor_config)

    if success:
        return jsonify({
            'success': True,
            'message': f"Sensor '{sensor_id}' added successfully"
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to add sensor'
        }), 400


@app.route('/api/sensors/<sensor_id>', methods=['DELETE'])
def remove_sensor(sensor_id):
    """Remove a sensor."""
    success = sensor_manager.remove_sensor(sensor_id)

    if success:
        return jsonify({
            'success': True,
            'message': f"Sensor '{sensor_id}' removed successfully"
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to remove sensor'
        }), 400


@app.route('/api/sensors/types', methods=['GET'])
def get_sensor_types():
    """Get available sensor types."""
    sensor_types = sensor_manager.get_available_sensor_types()
    return jsonify(sensor_types)


# ============================================================================
# API Routes - Readings
# ============================================================================

@app.route('/api/readings', methods=['GET'])
def get_all_readings():
    """Get current readings from all sensors."""
    readings = sensor_manager.read_all_sensors()
    return jsonify(readings)


@app.route('/api/readings/<sensor_id>', methods=['GET'])
def get_sensor_reading(sensor_id):
    """Get current reading from specific sensor."""
    reading = sensor_manager.read_sensor(sensor_id)
    if reading:
        return jsonify(reading)
    return jsonify({'error': 'Sensor not found or inactive'}), 404


# ============================================================================
# API Routes - Configuration
# ============================================================================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    return jsonify(sensor_manager.config)


@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update configuration."""
    updates = request.json

    # Don't allow updating sensors list directly
    if 'sensors' in updates:
        del updates['sensors']

    success = sensor_manager.update_config(updates)

    # Reinitialize cloud publisher if cloud config changed
    if 'cloud' in updates:
        initialize_cloud_publisher()

    if success:
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to update configuration'
        }), 400


@app.route('/api/config/thresholds', methods=['PUT'])
def update_thresholds():
    """Update downsampling thresholds."""
    thresholds = request.json

    sensor_manager.config['thresholds'].update(thresholds)
    sensor_manager.save_config()

    return jsonify({
        'success': True,
        'message': 'Thresholds updated successfully',
        'thresholds': sensor_manager.config['thresholds']
    })


# ============================================================================
# API Routes - Collection Control
# ============================================================================

@app.route('/api/collection/start', methods=['POST'])
def start_collection():
    """Start data collection."""
    sensor_manager.start_collection()
    return jsonify({
        'success': True,
        'message': 'Data collection started'
    })


@app.route('/api/collection/stop', methods=['POST'])
def stop_collection():
    """Stop data collection."""
    sensor_manager.stop_collection()
    return jsonify({
        'success': True,
        'message': 'Data collection stopped'
    })


# ============================================================================
# Shutdown handlers
# ============================================================================

def shutdown_handler(signum=None, frame=None):
    """Handle graceful shutdown."""
    print("\n\nReceived shutdown signal...")

    # Stop collection
    sensor_manager.shutdown()

    # Shutdown cloud publisher
    if cloud_publisher:
        cloud_publisher.shutdown()

    sys.exit(0)


# Register shutdown handlers
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)
atexit.register(shutdown_handler)


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    print("=" * 60)
    print("  Rasperature Pi Application")
    print("=" * 60)
    print()

    # Initialize sensors from config
    print("Initializing sensors from configuration...")
    sensor_manager.initialize_from_config()
    print()

    # Initialize cloud publisher
    initialize_cloud_publisher()
    print()

    # Start data collection
    if len(sensor_manager.sensors) > 0:
        sensor_manager.start_collection()
        print()

    # Get local IP address
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print("=" * 60)
    print(f"  Web Interface: http://{local_ip}:5000")
    print(f"  Local Access:  http://localhost:5000")
    print("=" * 60)
    print()
    print("Press Ctrl+C to stop")
    print()

    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
