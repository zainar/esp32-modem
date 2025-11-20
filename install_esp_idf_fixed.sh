#!/bin/bash
# Install ESP-IDF for ESP32-C3 development
# This version temporarily uses public PyPI to avoid CodeArtifact issues

set -e

ESP_IDF_DIR="$HOME/esp/esp-idf"
ESP_IDF_VERSION="v5.1.2"
PIP_CONFIG_BACKUP="$HOME/.config/pip/pip.conf.backup"
PIP_CONFIG="$HOME/.config/pip/pip.conf"

echo "ESP-IDF Installation Script (with PyPI fix)"
echo "==========================================="
echo ""

# Backup and temporarily modify pip config to use public PyPI
if [ -f "$PIP_CONFIG" ]; then
    echo "Found pip config with private repository."
    echo "Temporarily switching to public PyPI for ESP-IDF installation..."
    
    # Create backup if it doesn't exist
    if [ ! -f "$PIP_CONFIG_BACKUP" ]; then
        cp "$PIP_CONFIG" "$PIP_CONFIG_BACKUP"
        echo "Backed up pip config to: $PIP_CONFIG_BACKUP"
    fi
    
    # Create temporary pip config using public PyPI
    cat > "$PIP_CONFIG" << 'EOF'
[global]
index-url = https://pypi.org/simple/
EOF
    echo "Temporarily using public PyPI for installation"
fi

# Restore function
restore_pip_config() {
    if [ -f "$PIP_CONFIG_BACKUP" ]; then
        echo ""
        echo "Restoring original pip configuration..."
        cp "$PIP_CONFIG_BACKUP" "$PIP_CONFIG"
        echo "Original pip config restored"
    fi
}

# Trap to restore config on exit
trap restore_pip_config EXIT

# Check if already installed
if [ -d "$ESP_IDF_DIR" ] && [ -f "$ESP_IDF_DIR/export.sh" ]; then
    echo "ESP-IDF appears to be already installed at: $ESP_IDF_DIR"
    echo "To use it, run: . $ESP_IDF_DIR/export.sh"
    restore_pip_config
    exit 0
fi

# Create directory
echo "Creating ESP directory..."
mkdir -p ~/esp
cd ~/esp

# Clone ESP-IDF
if [ ! -d "esp-idf" ]; then
    echo "Cloning ESP-IDF repository (this may take a while)..."
    git clone --recursive https://github.com/espressif/esp-idf.git
    cd esp-idf
    git checkout $ESP_IDF_VERSION
    git submodule update --init --recursive
else
    echo "ESP-IDF directory already exists, updating..."
    cd esp-idf
    git fetch
    git checkout $ESP_IDF_VERSION
    git submodule update --init --recursive
fi

# Install ESP-IDF
echo ""
echo "Installing ESP-IDF tools (this will take several minutes)..."
echo "Using public PyPI to avoid authentication issues..."
./install.sh esp32c3

# Restore pip config
restore_pip_config

echo ""
echo "=========================================="
echo "ESP-IDF installation complete!"
echo ""
echo "To use ESP-IDF, run:"
echo "  . ~/esp/esp-idf/export.sh"
echo ""
echo "Or add to your ~/.bashrc:"
echo "  alias get_idf='. ~/esp/esp-idf/export.sh'"
echo ""
echo "Then you can run:"
echo "  cd /home/alex/Project/ESP32/Zainar_zps/esp32_modem"
echo "  get_idf"
echo "  idf.py build"
echo "=========================================="

