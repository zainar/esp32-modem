# Build Instructions

## Prerequisites

1. **ESP-IDF v5.0 or later**
   ```bash
   mkdir -p ~/esp
   cd ~/esp
   git clone --recursive https://github.com/espressif/esp-idf.git
   cd esp-idf
   ./install.sh esp32c3
   . ./export.sh  # Add this to your ~/.bashrc for persistence
   ```

2. **Python 3.6+** (for host-side bridge script)

3. **pyserial** (for host-side bridge)
   ```bash
   pip3 install pyserial
   ```

## Building the Firmware

```bash
cd /home/alex/Project/ESP32/Zainar_zps/esp32_modem

# Set ESP-IDF environment (if not in .bashrc)
. ~/esp/esp-idf/export.sh

# Configure target
idf.py set-target esp32c3

# Configure WiFi (optional - can also edit main/wifi_config.h)
idf.py menuconfig
# Navigate to: Component config → Example Configuration
# Set WiFi SSID and Password

# Build
idf.py build

# Flash to device
idf.py flash

# Monitor serial output
idf.py monitor
```

## Hardware Connection

1. Connect Seeed Studio XIAO ESP32-C3 to your laptop via USB-C cable
2. The device should appear as `/dev/ttyACM0` (or similar)
3. Check with: `lsusb | grep -i espressif`

## Host Setup

After flashing the firmware:

1. **Set up TAP interface:**
   ```bash
   cd host_setup
   sudo ./setup_tap.sh
   ```

2. **Start the USB bridge:**
   ```bash
   sudo python3 bridge_usb.py
   ```

3. **Configure network (in another terminal):**
   ```bash
   # The TAP interface should be up with IP 192.168.7.1
   # Configure your host to use it
   sudo ip route add 192.168.7.0/24 dev tap0
   ```

## Testing

1. **Check ESP32 connection:**
   - Monitor serial output: `idf.py monitor`
   - Should see "WiFi connected to AP" and "Got IP:..."

2. **Check host interface:**
   ```bash
   ip link show tap0
   ip addr show tap0
   ```

3. **Test connectivity:**
   ```bash
   ping 192.168.7.1  # Ping ESP32
   ```

## Troubleshooting

### Build Errors
- Ensure ESP-IDF is properly installed and exported
- Check ESP-IDF version: `idf.py --version`
- Clean build: `idf.py fullclean`

### Flash Errors
- Check USB connection: `lsusb`
- Try different USB port/cable
- Put device in download mode (hold BOOT button, press RESET)

### WiFi Connection Issues
- Verify SSID and password in `wifi_config.h`
- Check 2.4GHz network (ESP32-C3 doesn't support 5GHz)
- Monitor serial output for connection status

### Host Interface Issues
- Ensure TUN module is loaded: `lsmod | grep tun`
- Check permissions: `ls -l /dev/ttyACM0`
- Verify bridge script is running: `ps aux | grep bridge_usb`

## Notes

- The current implementation uses USB Serial JTAG for communication
- For production use, consider implementing true CDC-ECM for native network interface support
- Raw sockets require proper packet handling - current implementation is simplified for POC

