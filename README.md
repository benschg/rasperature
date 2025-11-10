# Rasperature

A Raspberry Pi sensor data collection project for environmental monitoring. Currently supports the BMP280 temperature and pressure sensor, with plans to expand to additional sensors.

## Features

- Clean, modular sensor reader architecture
- BMP280 temperature, pressure, and altitude readings
- CSV data logging with timestamps
- Simple test utilities
- Easy to extend for additional sensors

## Hardware Requirements

- Raspberry Pi (any model with I2C support)
- BMP280 sensor module
- Jumper wires

### BMP280 Wiring

Connect the BMP280 to your Raspberry Pi as follows:

| BMP280 Pin | Raspberry Pi Pin | Description |
|------------|------------------|-------------|
| VCC/VIN    | Pin 1 or 17      | 3.3V Power  |
| GND        | Pin 6, 9, 14, etc| Ground      |
| SCL        | Pin 5 (GPIO 3)   | I2C Clock   |
| SDA        | Pin 3 (GPIO 2)   | I2C Data    |

**Important:** Use 3.3V, NOT 5V. Some BMP280 modules can be damaged by 5V.

## Software Setup

### Quick Setup (Automated)

The easiest way to set up everything on your Raspberry Pi:

```bash
cd ~
git clone <your-repo-url> rasperature
cd rasperature

# Make setup script executable
chmod +x setup.sh

# Run automated setup
./setup.sh
```

The setup script will automatically:
- ✓ Enable I2C interface
- ✓ Install system dependencies (Python, i2c-tools, etc.)
- ✓ Install uv package manager
- ✓ Create virtual environment
- ✓ Install Python dependencies
- ✓ Detect BMP280 sensor
- ✓ Run sensor test

If I2C is enabled for the first time, you'll need to reboot and run the script again.

### Manual Setup (Step-by-Step)

If you prefer to set up manually or the automated script doesn't work:

#### 1. Enable I2C on Raspberry Pi

```bash
sudo raspi-config
```

Navigate to: **Interface Options → I2C → Enable**

Reboot after enabling:
```bash
sudo reboot
```

#### 2. Verify I2C is Working

```bash
# Check for I2C device
ls /dev/i2c*

# Scan for connected sensors (should show 76 or 77)
sudo i2cdetect -y 1
```

#### 3. Install uv (Fast Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

#### 4. Clone and Setup Project

```bash
cd ~
git clone <your-repo-url> rasperature
cd rasperature

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install adafruit-circuitpython-bmp280 rpi-lgpio
```

**Note:** `rpi-lgpio` is required for Raspberry Pi 5. Older Pi models may work without it.

## Usage

### Quick Test

Test if your sensor is working:

```bash
cd sensor-readers/bmp280
python3 test_sensor.py
```

Expected output:
```
BMP280 Sensor Test
==================================================

Initializing sensor...
BMP280 sensor initialized successfully at address 0x76

Reading sensor data...

Current Sensor Readings:
--------------------------------------------------
Temperature: 22.45 °C
Pressure:    1013.25 hPa
Altitude:    0.00 m

✓ Test completed successfully!
```

### Continuous Data Logging

Log sensor data continuously to a CSV file:

```bash
cd sensor-readers/bmp280

# Log every 60 seconds (default)
python3 continuous_log.py

# Log every 30 seconds
python3 continuous_log.py --interval 30

# Log every 5 minutes with custom output directory
python3 continuous_log.py --interval 300 --output-dir ~/sensor-data
```

**Example output:**
```
BMP280 Continuous Data Logger
============================================================
Logging interval: 60.0 seconds
Output directory: /home/pi/rasperature/data

Initializing sensor...
BMP280 sensor initialized successfully at address 0x76

📝 Logging to: /home/pi/rasperature/data/bmp280_log_20250104_143022.csv

Starting data logging... (Press Ctrl+C to stop)
------------------------------------------------------------
2025-01-04T14:30:22 | Temp:  22.45°C | Press: 1013.25 hPa | Alt:    0.00m
2025-01-04T14:31:22 | Temp:  22.46°C | Press: 1013.27 hPa | Alt:   -0.17m
```

Press `Ctrl+C` to stop logging. Data is saved in CSV format in the `data/` directory.

### Using the BMP280Reader Class

You can also use the sensor reader in your own Python scripts:

```python
from sensor_readers.bmp280 import BMP280Reader

# Initialize sensor
sensor = BMP280Reader()

# Read individual values
temperature = sensor.temperature  # Celsius
pressure = sensor.pressure        # hPa
altitude = sensor.altitude        # meters

# Or read all at once
data = sensor.read_all()
print(f"Temperature: {data['temperature']:.2f}°C")
print(f"Pressure: {data['pressure']:.2f} hPa")
print(f"Altitude: {data['altitude']:.2f} m")

# Update sea level pressure for better altitude accuracy
sensor.set_sea_level_pressure(1015.3)
```

## CSV Data Format

Log files are saved in the `data/` directory with the naming format:
```
bmp280_log_YYYYMMDD_HHMMSS.csv
```

CSV columns:
- `timestamp`: ISO 8601 format (e.g., 2025-01-04T14:30:22)
- `temperature_celsius`: Temperature in degrees Celsius
- `pressure_hpa`: Atmospheric pressure in hectopascals
- `altitude_meters`: Calculated altitude in meters

## Troubleshooting

### Sensor Not Detected

If `sudo i2cdetect -y 1` doesn't show your sensor (76 or 77):

1. **Check I2C is enabled:**
   ```bash
   ls /dev/i2c*
   ```
   Should show `/dev/i2c-1`

2. **Verify wiring connections** - ensure all pins are properly connected

3. **Check soldering** - the sensor pins must be properly soldered

4. **Try alternate I2C address** - if your sensor uses 0x77:
   ```python
   sensor = BMP280Reader(address=0x77)
   ```

5. **Try I2C bus 0** (older Raspberry Pi models):
   ```bash
   sudo i2cdetect -y 0
   ```

### Permission Errors

If you get permission errors accessing I2C:

```bash
sudo usermod -a -G i2c $USER
```

Log out and back in for the change to take effect.

## Project Structure

```
rasperature/
├── sensor-readers/
│   └── bmp280/
│       ├── __init__.py           # Package initialization
│       ├── bmp280_reader.py      # Main sensor class
│       ├── test_sensor.py        # Quick test script
│       └── continuous_log.py     # Data logging script
├── data/                         # CSV log files (gitignored)
├── .venv/                        # Virtual environment (gitignored)
├── .gitignore
├── setup.sh                     # Automated setup script
├── pyproject.toml               # Project dependencies
└── README.md                    # This file
```

## Future Plans

- Add support for additional sensors (DHT22, BME680, etc.)
- Cloud data streaming (AWS IoT, Azure IoT Hub, etc.)
- Web dashboard for real-time visualization
- SQLite database for local data storage
- Alert system for threshold violations

## Contributing

This is a learning project! Feel free to extend it or add support for more sensors.

## License

MIT License - Feel free to use and modify as needed.

## Resources

- [BMP280 Datasheet](https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp280/)
- [Adafruit BMP280 Library](https://github.com/adafruit/Adafruit_CircuitPython_BMP280)
- [Raspberry Pi I2C Documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#i2c)
