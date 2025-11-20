#!/usr/bin/env python3
"""
Setup TAP interface for ESP32 WiFi adapter
Creates a TAP interface and configures it for bridging with ESP32 USB connection
"""

import os
import sys
import subprocess
import glob
import argparse

TAP_IF = "esp0"
USB_DEV = None  # Will be auto-detected if not specified
IP_ADDR = "192.168.7.1"
NETMASK = "255.255.255.0"
ESPRESSIF_USB_VID = "303a"


def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        print("Error: This script must be run as root")
        print("Use: sudo python3 setup_tap.py")
        sys.exit(1)


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


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error running command: {cmd}")
            print(f"Error: {e}")
            sys.exit(1)
        return None


def check_tun_module():
    """Check if TUN/TAP module is loaded, load if not"""
    result = run_command("lsmod | grep -q '^tun'", check=False, capture_output=True)
    if result.returncode != 0:
        print("Loading TUN/TAP module...")
        run_command("modprobe tun")
    else:
        print("TUN/TAP module already loaded")


def interface_exists(ifname):
    """Check if network interface exists"""
    result = run_command(
        f"ip link show {ifname}",
        check=False,
        capture_output=True
    )
    return result.returncode == 0


def create_tap_interface():
    """Create and configure TAP interface"""
    if interface_exists(TAP_IF):
        print(f"TAP interface {TAP_IF} already exists")
        return

    print(f"Creating TAP interface: {TAP_IF}")
    run_command(f"ip tuntap add mode tap {TAP_IF}")
    run_command(f"ip addr add {IP_ADDR}/24 dev {TAP_IF}")
    run_command(f"ip link set {TAP_IF} up")
    print("TAP interface created and configured")


def check_usb_device(usb_dev):
    """Check if USB device exists"""
    if not usb_dev:
        print("Warning: No USB device specified")
        return

    if not os.path.exists(usb_dev):
        print(f"Warning: USB device {usb_dev} not found")
        print("Make sure ESP32 is connected and firmware is running")
    else:
        print(f"USB device found: {usb_dev}")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Setup TAP interface for ESP32 WiFi adapter"
    )
    parser.add_argument(
        "--dev", "-d",
        default=None,
        help="USB serial device (e.g. /dev/ttyACM1). "
             "If omitted, auto-detect ESP32 (VID 303a) on /dev/ttyACM*"
    )
    return parser.parse_args()


def main():
    print("ESP32 WiFi Adapter - Host Setup")
    print("=" * 40)

    # Check if running as root
    check_root()

    # Parse arguments
    args = parse_args()

    # Auto-detect USB device if not specified
    usb_dev = args.dev
    if not usb_dev:
        usb_dev = detect_esp32_acm()
        if not usb_dev:
            print("Error: Could not auto-detect ESP32 USB device")
            print("Please specify --dev manually: --dev /dev/ttyACM1")
            sys.exit(1)

    # Check if TUN module is loaded
    check_tun_module()

    # Create TAP interface
    create_tap_interface()

    # Check if USB device exists
    check_usb_device(usb_dev)

    print("")
    print("Setup complete!")
    print(f"TAP interface: {TAP_IF}")
    print(f"IP address: {IP_ADDR}")
    print(f"USB device: {usb_dev}")
    print("")
    print("To remove the interface later, run:")
    print(f"  sudo ip tuntap del mode tap {TAP_IF}")


if __name__ == "__main__":
    main()

