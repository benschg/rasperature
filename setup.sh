#!/bin/bash
#
# Rasperature Setup Script
#
# This script automates the complete setup of the BMP280 sensor reader
# on a Raspberry Pi, including I2C configuration, dependencies, and
# virtual environment setup.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "This doesn't appear to be a Raspberry Pi"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check if I2C is enabled
check_i2c_enabled() {
    if [ -e /dev/i2c-1 ]; then
        print_success "I2C is already enabled"
        return 0
    else
        print_warning "I2C is not enabled"
        return 1
    fi
}

# Enable I2C
enable_i2c() {
    print_info "Enabling I2C interface..."

    # Enable I2C in config.txt if not already enabled
    if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
        echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt > /dev/null
    fi

    # Load I2C kernel modules
    sudo modprobe i2c-dev

    # Add to /etc/modules for auto-load on boot
    if ! grep -q "^i2c-dev" /etc/modules; then
        echo "i2c-dev" | sudo tee -a /etc/modules > /dev/null
    fi

    # Add user to i2c group
    sudo usermod -a -G i2c $USER

    print_success "I2C enabled"
    print_warning "A reboot may be required for I2C to work properly"
}

# Install system dependencies
install_system_deps() {
    print_info "Installing system dependencies..."

    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        python3 \
        python3-pip \
        python3-dev \
        i2c-tools \
        git \
        curl

    print_success "System dependencies installed"
}

# Install uv
install_uv() {
    if command -v uv &> /dev/null; then
        print_success "uv is already installed"
        return 0
    fi

    print_info "Installing uv (fast Python package manager)..."

    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add uv to PATH - check multiple possible locations
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi

    # uv installs to ~/.local/bin by default
    if [ -d "$HOME/.local/bin" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi

    print_success "uv installed"
}

# Setup Python virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."

    # Ensure we have uv in PATH - check multiple locations
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
    if [ -d "$HOME/.local/bin" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # Create virtual environment
    if [ ! -d ".venv" ]; then
        uv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Install Python dependencies
    print_info "Installing Python dependencies..."
    uv pip install adafruit-circuitpython-bmp280

    print_success "Python dependencies installed"
}

# Detect BMP280 sensor
detect_sensor() {
    print_info "Scanning for BMP280 sensor..."

    if [ ! -e /dev/i2c-1 ]; then
        print_error "I2C device not found. Reboot may be required."
        return 1
    fi

    # Scan I2C bus
    SCAN_OUTPUT=$(sudo i2cdetect -y 1)

    if echo "$SCAN_OUTPUT" | grep -q "76\|77"; then
        if echo "$SCAN_OUTPUT" | grep -q "76"; then
            print_success "BMP280 sensor detected at address 0x76"
        else
            print_success "BMP280 sensor detected at address 0x77"
        fi
        return 0
    else
        print_warning "BMP280 sensor NOT detected"
        print_info "Please check:"
        echo "  • Sensor is properly wired"
        echo "  • VCC → 3.3V (Pin 1 or 17)"
        echo "  • GND → Ground (Pin 6, 9, 14, etc.)"
        echo "  • SCL → GPIO 3 (Pin 5)"
        echo "  • SDA → GPIO 2 (Pin 3)"
        echo ""
        echo "I2C scan results:"
        echo "$SCAN_OUTPUT"
        return 1
    fi
}

# Create data directory
create_data_dir() {
    print_info "Creating data directory..."
    mkdir -p data
    print_success "Data directory created"
}

# Run sensor test
run_test() {
    print_info "Running sensor test..."

    source .venv/bin/activate
    cd sensor-readers/bmp280

    if python3 test_sensor.py; then
        print_success "Sensor test passed!"
        return 0
    else
        print_error "Sensor test failed"
        return 1
    fi
}

# Print usage instructions
print_usage() {
    print_header "Setup Complete!"

    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   ${GREEN}source .venv/bin/activate${NC}"
    echo ""
    echo "2. Test the sensor:"
    echo "   ${GREEN}cd sensor-readers/bmp280${NC}"
    echo "   ${GREEN}python3 test_sensor.py${NC}"
    echo ""
    echo "3. Start continuous logging:"
    echo "   ${GREEN}python3 continuous_log.py${NC}"
    echo ""
    echo "For more options:"
    echo "   ${GREEN}python3 continuous_log.py --help${NC}"
    echo ""
}

# Main setup process
main() {
    print_header "Rasperature Setup"
    echo ""

    # Change to script directory
    cd "$(dirname "$0")"

    # Check if on Raspberry Pi
    check_raspberry_pi

    # Check and enable I2C
    if ! check_i2c_enabled; then
        enable_i2c
        NEED_REBOOT=true
    fi

    # Install system dependencies
    install_system_deps

    # Install uv
    install_uv

    # Setup virtual environment and install Python packages
    setup_venv

    # Create data directory
    create_data_dir

    # Try to detect sensor
    echo ""
    if ! detect_sensor; then
        SENSOR_NOT_DETECTED=true
    fi

    echo ""

    # Print final status
    if [ "$NEED_REBOOT" = true ]; then
        print_header "Reboot Required"
        echo ""
        print_warning "I2C was just enabled. Please reboot your Raspberry Pi:"
        echo "   ${GREEN}sudo reboot${NC}"
        echo ""
        echo "After rebooting, run this script again to verify the sensor."
        exit 0
    fi

    if [ "$SENSOR_NOT_DETECTED" = true ]; then
        print_header "Setup Complete (Sensor Not Detected)"
        echo ""
        print_warning "Setup completed but sensor was not detected."
        print_info "Please check your wiring and run the test manually:"
        echo "   ${GREEN}source .venv/bin/activate${NC}"
        echo "   ${GREEN}cd sensor-readers/bmp280${NC}"
        echo "   ${GREEN}python3 test_sensor.py${NC}"
        exit 1
    fi

    # Run sensor test
    echo ""
    if run_test; then
        echo ""
        print_usage
    else
        echo ""
        print_error "Setup completed but sensor test failed"
        print_info "Please check your sensor wiring and try again"
        exit 1
    fi
}

# Run main function
main
