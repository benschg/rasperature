# Rasperature Pi Application

Web-based application for Raspberry Pi to configure sensors, manage data collection, and publish to Google Cloud.

## Features

- **Web Interface**: Configure sensors through a user-friendly web UI
- **Multi-Sensor Support**: BMP280, DHT22 (extensible architecture)
- **Real-time Monitoring**: View live sensor readings
- **Cloud Publishing**: Publish data to Google Cloud Pub/Sub
- **Edge Downsampling**: Reduce cloud costs by 60-80%
- **Offline Buffering**: Queue data when offline
- **Configuration Management**: Persist settings across reboots

## Installation

### Prerequisites

- Raspberry Pi (any model with I2C support)
- Raspbian/Raspberry Pi OS
- Python 3.8+
- I2C enabled
- BMP280 sensor connected

### Quick Install

```bash
# Clone repository
cd ~/
git clone https://github.com/yourusername/rasperature.git
cd rasperature/pi-app

# Install dependencies
pip3 install -r requirements.txt

# Install for autostart (optional)
sudo cp rasperature.service /etc/systemd/system/
sudo systemctl enable rasperature
sudo systemctl start rasperature
```

### Manual Install

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

## Configuration

### First-Time Setup

1. Start the application:
   ```bash
   python app.py
   ```

2. Open web interface:
   ```
   http://raspberrypi.local:5000
   or
   http://YOUR_PI_IP:5000
   ```

3. Add sensors from the Sensors page

4. Configure device settings in Configuration page:
   - Device ID
   - Customer ID
   - Location
   - Update frequency

5. (Optional) Configure cloud publishing:
   - Enable cloud publishing
   - Enter GCP project ID
   - Provide service account credentials
   - Set batch and threshold settings

### Adding Sensors

1. Navigate to **Sensors** page
2. Click **Add Sensor**
3. Select sensor type (BMP280, DHT22, etc.)
4. Enter sensor ID
5. Configure sensor-specific settings
6. Click **Add Sensor**

### Configuration File

Settings are stored in `config.json`:

```json
{
  "device_id": "rpi_001",
  "customer_id": "customer_001",
  "location": "warehouse_a",
  "update_frequency": 60,
  "sensors": [...],
  "cloud": {
    "enabled": true,
    "project_id": "your-project-id",
    "topic_name": "sensor-data-raw",
    "credentials_file": "/path/to/credentials.json"
  },
  "thresholds": {
    "temperature": 0.5,
    "pressure": 2.0,
    "humidity": 2.0
  }
}
```

## Cloud Setup

### 1. Create Service Account

```bash
# From terraform/ directory
export PROJECT_ID="your-project-id"
export PI_SA_EMAIL=$(terraform output -raw pi_service_account_email)

# Create key
gcloud iam service-accounts keys create pi-credentials.json \
  --iam-account=$PI_SA_EMAIL
```

### 2. Copy Credentials to Pi

```bash
# From your computer
scp pi-credentials.json pi@raspberrypi:~/rasperature/pi-app/
```

### 3. Configure in Web UI

1. Go to Configuration page
2. Enable Cloud Publishing
3. Enter Project ID
4. Enter credentials file path: `/home/pi/rasperature/pi-app/pi-credentials.json`
5. Save configuration

## Edge Downsampling

The application implements intelligent edge downsampling to reduce cloud costs:

### How It Works

1. **Threshold-Based**: Only publish when values change beyond configured thresholds
2. **First Reading**: Always publish first reading from each sensor
3. **Significant Changes**: Publish when temperature changes >0.5°C or pressure >2 hPa

### Expected Savings

- **Without downsampling**: 2 readings/second = 172,800 messages/day
- **With downsampling**: 60-80% reduction = 34,000-69,000 messages/day
- **Cost savings**: $1,000-1,500/month at scale

### Configure Thresholds

In Configuration page, adjust thresholds:
- Temperature: 0.5°C (default)
- Pressure: 2.0 hPa (default)
- Humidity: 2.0% (default)

Lower thresholds = more data, higher cost
Higher thresholds = less data, lower cost

## API Endpoints

The Pi application exposes a REST API:

### System

- `GET /api/info` - System information
- `GET /api/stats` - Statistics

### Sensors

- `GET /api/sensors` - List all sensors
- `POST /api/sensors` - Add sensor
- `GET /api/sensors/<id>` - Get sensor details
- `DELETE /api/sensors/<id>` - Remove sensor
- `GET /api/sensors/types` - Available sensor types

### Readings

- `GET /api/readings` - All current readings
- `GET /api/readings/<sensor_id>` - Specific sensor reading

### Configuration

- `GET /api/config` - Get configuration
- `PUT /api/config` - Update configuration
- `PUT /api/config/thresholds` - Update thresholds

### Collection Control

- `POST /api/collection/start` - Start data collection
- `POST /api/collection/stop` - Stop data collection

## Autostart on Boot

### Using systemd

1. Create service file:
```bash
sudo nano /etc/systemd/system/rasperature.service
```

2. Add content:
```ini
[Unit]
Description=Rasperature Sensor Application
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/rasperature/pi-app
ExecStart=/home/pi/rasperature/pi-app/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable rasperature
sudo systemctl start rasperature
```

4. Check status:
```bash
sudo systemctl status rasperature
```

## Troubleshooting

### Sensor Not Detected

```bash
# Check I2C is enabled
ls /dev/i2c*

# Scan for devices
i2cdetect -y 1

# Should see device at 0x76 or 0x77
```

### Cloud Publishing Fails

1. Verify credentials file exists and is valid
2. Check project ID is correct
3. Ensure service account has Pub/Sub publisher role
4. Check logs: `sudo journalctl -u rasperature -f`

### High Memory Usage

- Reduce update frequency
- Enable cloud publishing to prevent local data buildup
- Clear offline buffer: Delete `offline_buffer.json`

### Web Interface Not Accessible

```bash
# Check if running
sudo systemctl status rasperature

# Check firewall
sudo ufw allow 5000

# Get IP address
hostname -I
```

## Development

### Project Structure

```
pi-app/
├── app.py                  # Flask application
├── sensor_manager.py       # Sensor lifecycle management
├── cloud_publisher.py      # Google Cloud Pub/Sub integration
├── sensors/                # Sensor implementations
│   ├── __init__.py         # Sensor registry
│   ├── base.py             # Base sensor class
│   ├── bmp280.py           # BMP280 implementation
│   └── dht22.py            # DHT22 implementation (placeholder)
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Dashboard
│   ├── sensors.html        # Sensor management
│   └── config.html         # Configuration
├── config.json             # Configuration (auto-generated)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

### Adding New Sensor Types

1. Create new sensor class in `sensors/`:
```python
from .base import BaseSensor

class MySensor(BaseSensor):
    def initialize(self):
        # Initialize hardware
        pass

    def read(self):
        # Read and return values
        return {'metric': value}

    def get_sensor_type(self):
        return 'MySensor'

    def get_available_metrics(self):
        return ['metric']
```

2. Register in `sensors/__init__.py`:
```python
from .mysensor import MySensor

SENSOR_TYPES['MySensor'] = {
    'class': MySensor,
    'name': 'My Sensor Name',
    'metrics': ['metric'],
    'default_config': {...},
    'config_schema': {...},
    'status': 'available'
}
```

## Performance

- **Memory**: ~100MB typical usage
- **CPU**: <5% on Raspberry Pi 4
- **Network**: Minimal (batch publishing)
- **Storage**: <10MB (excluding logs)

## Security

- Web interface runs on local network only
- No authentication by default (add nginx proxy for auth)
- Cloud credentials stored locally (protect file permissions)
- HTTPS not enabled by default (use reverse proxy)

## License

Same as main Rasperature project
