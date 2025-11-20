# ESP32-C3 WiFi USB Adapter

This project turns a Seeed Studio XIAO ESP32-C3 module into a USB WiFi adapter that appears as a network interface (like eth0 or wlan0) on your Linux laptop.

## Features

- USB CDC-ECM (Ethernet Control Model) interface - appears as a network device
- WiFi Station mode with automatic 4-way handshake (WPA/WPA2/WPA3)
- Transparent packet bridging between USB and WiFi
- DHCP client support for automatic IP configuration
- Configurable via menuconfig or code

## Hardware

- **Board**: Seeed Studio XIAO ESP32-C3
- **USB**: Native USB support (no external USB-to-serial chip needed)
- **WiFi**: 2.4 GHz 802.11 b/g/n

## Building

### Prerequisites

1. Install ESP-IDF v5.0 or later:
```bash
mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh esp32c3
. ./export.sh
```

2. Connect your XIAO ESP32-C3 via USB

### Build and Flash

```bash
cd /home/alex/Project/ESP32/Zainar_zps/esp32_modem
idf.py set-target esp32c3
idf.py menuconfig  # Configure WiFi credentials (optional)
idf.py build
idf.py flash monitor
```

## Configuration

### WiFi Credentials

Edit `main/wifi_config.h` or configure via menuconfig:
- Component config → Example Configuration → WiFi SSID
- Component config → Example Configuration → WiFi Password

### USB Configuration

The USB CDC-ECM interface is automatically configured. The device will appear as:
- `/dev/ttyACM0` (serial console)
- Network interface (usb0 or similar)

## Host Setup (Linux)

### 1. Flash the Firmware

Make sure to use the correct serial port. If you have multiple USB devices:

```bash
# List available ports
ls /dev/ttyACM*

# Flash to the correct port (usually /dev/ttyACM0 or /dev/ttyACM1)
idf.py -p /dev/ttyACM1 flash  # Use the port where your ESP32-C3 is connected
```

**Note:** If flashing fails, put the ESP32-C3 into download mode:
1. Hold BOOT button
2. Press and release RESET button
3. Release BOOT button
4. Immediately run the flash command

### 2. Install USB Network Driver

The ESP32-C3 will appear as a CDC-ECM device. Linux should recognize it automatically, but you may need to load the driver:

```bash
sudo modprobe cdc_ether
```

### 3. Configure Network Interface

Once connected, the interface should appear. Check with:
```bash
ip link show
```

You should see a device like `usb0` or `enp0s...`.

### 3. Configure IP Address

**Option A: DHCP (if ESP32 provides DHCP server)**
```bash
sudo dhclient usb0
```

**Option B: Static IP**
```bash
sudo ip addr add 192.168.7.2/24 dev usb0
sudo ip link set usb0 up
```

The ESP32-C3 will have IP `192.168.7.1` by default.

### 4. Test Connection

```bash
ping 192.168.7.1  # Ping ESP32
ping 8.8.8.8      # Ping through WiFi (if ESP32 is connected to internet)
```

## Usage

1. Flash the firmware to your ESP32-C3
2. Connect via USB to your laptop
3. Configure the network interface as shown above
4. The ESP32 will automatically connect to WiFi (if configured)
5. All network traffic through the USB interface will be bridged to WiFi

## Architecture

```
[Linux Host] <--USB CDC-ECM--> [ESP32-C3] <--WiFi--> [Access Point]
   usb0                              Station Mode
```

- **USB Side**: CDC-ECM presents Ethernet frames over USB
- **WiFi Side**: ESP-IDF WiFi stack handles all 802.11 operations including 4-way handshake
- **Bridge**: Application bridges Ethernet frames between USB and WiFi

## Troubleshooting

### Device not recognized
- Check USB cable (data capable)
- Verify USB drivers: `lsusb` should show Espressif device
- Check dmesg: `dmesg | tail`

### Network interface not appearing
- Load driver: `sudo modprobe cdc_ether`
- Check: `ip link show`
- May need udev rules (see host_setup/)

### WiFi connection issues
- Check credentials in `wifi_config.h`
- Monitor serial output: `idf.py monitor`
- Verify AP is in range and 2.4GHz

### No internet connectivity
- Verify ESP32 connected to WiFi: check serial monitor
- Check routing: `ip route`
- Verify DNS: `cat /etc/resolv.conf`

## License

MIT License

