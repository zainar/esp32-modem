# Host Setup for ESP32 WiFi Adapter

This directory contains scripts to set up the ESP32-C3 as a network interface on your Linux host.

**📖 For detailed setup instructions, see [SETUP_MODEM.md](../SETUP_MODEM.md)**

## Scripts

- **`setup_tap.py`** - Python script to create and configure TAP interface (recommended)
- **`setup_tap.sh`** - Bash script alternative (legacy)
- **`bridge_usb.py`** - USB to TAP bridge (must stay running)
- **`setup_routing.py`** - Configure routing table to route traffic through ESP32

## Quick Start

1. **Flash the firmware** to your ESP32-C3 (see main README)

2. **Set up TAP interface:**
```bash
cd host_setup
sudo python3 setup_tap.py  # Auto-detects ESP32 USB device
# Or use bash script: sudo ./setup_tap.sh
```

3. **Start the USB bridge:**
```bash
sudo python3 bridge_usb.py  # Auto-detects ESP32 USB device
```

4. **Configure network interface:**
```bash
sudo ip addr add 192.168.7.2/24 dev esp0
sudo ip link set esp0 up
```

5. **Configure routing (optional):**
```bash
# Route all traffic through ESP32
sudo python3 setup_routing.py --default

# Or route specific networks only
sudo python3 setup_routing.py --route 192.168.1.0/24
```

6. **Test connectivity:**
```bash
ping 192.168.7.1  # Ping ESP32
ping 8.8.8.8      # Test internet (if routing configured)
```

## Architecture

```
[Linux Apps] <--TAP--> [bridge_usb.py] <--USB Serial--> [ESP32-C3] <--WiFi--> [AP]
```

- **TAP interface**: Virtual network interface on Linux
- **bridge_usb.py**: Bridges Ethernet frames between TAP and USB serial
- **ESP32-C3**: Bridges USB serial to WiFi

## Example
- sudo python3 setup_tap.py

    ESP32 WiFi Adapter: Host Setup
    Auto-detect: scanning /dev/ttyACM* for ESP32 (VID 303a)...
    /dev/ttyACM0: VID=0483, PID=5740
    /dev/ttyACM1: VID=303a, PID=1001
    Auto-detect: selected /dev/ttyACM1 (Espressif VID 303a)
    TUN/TAP module already loaded
    Creating TAP interface: esp0
    TAP interface created and configured
    - USB device found: /dev/ttyACM1

    Setup complete!
```
    TAP interface: esp0
    IP address: 192.168.7.1
    USB device: /dev/ttyACM1
```

- To remove the interface later, run:
```
  sudo ip tuntap del mode tap esp0
```

## Troubleshooting

### Permission denied
- Make sure scripts are run with `sudo`
- Check USB device permissions: `ls -l /dev/ttyACM*`

### TAP interface not created
- Check if TUN module is loaded: `lsmod | grep tun`
- Load manually: `sudo modprobe tun`

### No data flow
- Check ESP32 serial monitor for connection status
- Verify WiFi credentials in `wifi_config.h`
- Check USB connection: `dmesg | tail`

