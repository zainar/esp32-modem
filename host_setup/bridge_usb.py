#!/usr/bin/env python3
"""
USB to TAP Bridge
Bridges data between ESP32 USB serial and TAP interface
"""

import serial
import struct
import socket
import select
import sys
import os
import fcntl
import argparse
import glob

TAP_IF = "esp0"           # safer than tap0, less likely to conflict
BAUDRATE = 921600         # High speed for network traffic
ESPRESSIF_USB_VID = "303a"  # Espressif vendor ID (seed XIAO ESP32-C3 uses this)

# TUN/TAP ioctl constants
TUNSETIFF = 0x400454ca
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000


def parse_args():
    parser = argparse.ArgumentParser(description="ESP32 USB-to-TAP bridge")
    parser.add_argument(
        "--dev", "-d",
        default=None,
        help="USB serial device (e.g. /dev/ttyACM1). "
             "If omitted, auto-detect ESP32 (VID 303a) on /dev/ttyACM*"
    )
    return parser.parse_args()


def find_usb_parent_sysfs(tty_path):
    """
    Given /dev/ttyACM0, find the corresponding USB device sysfs directory
    that contains idVendor / idProduct.
    """
    tty_name = os.path.basename(tty_path)  # e.g. ttyACM0
    base = f"/sys/class/tty/{tty_name}"
    if not os.path.exists(base):
        return None

    # Walk up a few levels until we find idVendor
    path = os.path.realpath(os.path.join(base, "device"))
    for _ in range(5):
        vid_path = os.path.join(path, "idVendor")
        pid_path = os.path.join(path, "idProduct")
        if os.path.exists(vid_path) and os.path.exists(pid_path):
            return path
        new_path = os.path.dirname(path)
        if new_path == path:
            break
        path = new_path
    return None


def detect_esp32_acm():
    """
    Auto-detect ESP32 (Espressif VID 303a) among /dev/ttyACM* devices.
    Returns path string or None.
    """
    candidates = sorted(glob.glob("/dev/ttyACM*"))
    if not candidates:
        print("Auto-detect: no /dev/ttyACM* devices found")
        return None

    print("Auto-detect: scanning /dev/ttyACM* for ESP32 (VID 303a)...")
    esp_ports = []

    for dev in candidates:
        sysfs_usb = find_usb_parent_sysfs(dev)
        if not sysfs_usb:
            print(f"  {dev}: no USB parent sysfs with idVendor/idProduct")
            continue

        try:
            with open(os.path.join(sysfs_usb, "idVendor"), "r") as f:
                vid = f.read().strip().lower()
            with open(os.path.join(sysfs_usb, "idProduct"), "r") as f:
                pid = f.read().strip().lower()
        except OSError:
            print(f"  {dev}: failed to read idVendor/idProduct")
            continue

        print(f"  {dev}: VID={vid}, PID={pid}")
        if vid == ESPRESSIF_USB_VID:
            esp_ports.append(dev)

    if len(esp_ports) == 1:
        print(f"Auto-detect: selected {esp_ports[0]} (Espressif VID 303a)")
        return esp_ports[0]
    elif len(esp_ports) > 1:
        print("Auto-detect: multiple ESP32-like devices found:")
        for p in esp_ports:
            print(f"  - {p}")
        print("Using the first one; specify --dev explicitly if this is wrong.")
        return esp_ports[0]
    else:
        print("Auto-detect: no ESP32 (VID 303a) found on /dev/ttyACM*")
        print("Falling back to first /dev/ttyACM* device.")
        return candidates[0]


def create_tap():
    """Create and configure TAP interface"""
    tap_fd = os.open("/dev/net/tun", os.O_RDWR)
    ifr = struct.pack('16sH', TAP_IF.encode(), IFF_TAP | IFF_NO_PI)
    fcntl.ioctl(tap_fd, TUNSETIFF, ifr)
    return tap_fd


def main():
    if os.geteuid() != 0:
        print("Error: This script must be run as root")
        print("Use: sudo python3 bridge_usb.py --dev /dev/ttyACM1")
        sys.exit(1)

    args = parse_args()

    # Decide which USB device to use
    if args.dev:
        usb_dev = args.dev
        print(f"Using USB device from argument: {usb_dev}")
    else:
        usb_dev = detect_esp32_acm()
        if not usb_dev:
            print("Failed to auto-detect any suitable /dev/ttyACM* device.")
            sys.exit(1)

    print("ESP32 WiFi Adapter - USB Bridge")
    print("=" * 40)
    print(f"Using USB device: {usb_dev}")
    print(f"Using TAP interface: {TAP_IF}")

    # Open USB serial
    try:
        ser = serial.Serial(usb_dev, BAUDRATE, timeout=0.1)
        print(f"Connected to {usb_dev}")
    except Exception as e:
        print(f"Error opening {usb_dev}: {e}")
        sys.exit(1)

    # Create TAP interface
    try:
        tap_fd = create_tap()
        print(f"TAP interface {TAP_IF} created")
        print("Note: configure IP/routes for this interface separately (e.g. via setup_tap.sh)")
    except Exception as e:
        print(f"Error creating TAP interface: {e}")
        print("Make sure /dev/net/tun exists (sudo modprobe tun)")
        ser.close()
        sys.exit(1)

    print("Bridge running... (Ctrl+C to stop)")

    try:
        while True:
            # Check for data from USB
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                if data:
                    os.write(tap_fd, data)

            # Check for data from TAP
            ready, _, _ = select.select([tap_fd], [], [], 0.1)
            if ready:
                data = os.read(tap_fd, 1500)  # Ethernet MTU
                if data:
                    ser.write(data)

    except KeyboardInterrupt:
        print("\nStopping bridge...")
    finally:
        ser.close()
        os.close(tap_fd)
        print("Bridge stopped")


if __name__ == "__main__":
    main()

