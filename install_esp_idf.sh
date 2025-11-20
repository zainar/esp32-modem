#!/bin/bash
# Install ESP-IDF for ESP32-C3 development

set -e

ESP_IDF_DIR="$HOME/esp/esp-idf"
ESP_IDF_VERSION="v5.1.2"

echo "ESP-IDF Installation Script"
echo "==========================="
echo ""

# Check if already installed
if [ -d "$ESP_IDF_DIR" ] && [ -f "$ESP_IDF_DIR/export.sh" ]; then
    echo "ESP-IDF appears to be already installed at: $ESP_IDF_DIR"
    echo "To use it, run: . $ESP_IDF_DIR/export.sh"
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
./install.sh esp32c3

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

