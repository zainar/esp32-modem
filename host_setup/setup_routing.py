#!/usr/bin/env python3
"""
Setup routing for ESP32 WiFi modem
Configures routing table to route traffic through esp0 interface
"""

import os
import sys
import subprocess
import argparse
import json

ESP0_IF = "esp0"
ESP0_GATEWAY = "192.168.7.1"
HOST_IP = "192.168.7.2"
ROUTES_FILE = "/tmp/esp32_routes_backup.json"


def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        print("Error: This script must be run as root")
        print("Use: sudo python3 setup_routing.py")
        sys.exit(1)


def run_command(cmd, check=True, capture_output=True):
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


def interface_exists(ifname):
    """Check if network interface exists"""
    result = run_command(
        f"ip link show {ifname}",
        check=False,
        capture_output=True
    )
    return result.returncode == 0


def get_current_default_route():
    """Get current default route"""
    result = run_command("ip route show default", check=False, capture_output=True)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def get_current_routes():
    """Get all current routes"""
    result = run_command("ip route show", check=False, capture_output=True)
    if result.returncode == 0:
        return result.stdout.strip().split('\n')
    return []


def backup_routes():
    """Backup current routing configuration"""
    default_route = get_current_default_route()
    routes = get_current_routes()
    
    backup = {
        "default_route": default_route,
        "all_routes": routes
    }
    
    try:
        with open(ROUTES_FILE, 'w') as f:
            json.dump(backup, f, indent=2)
        print(f"✓ Backed up current routes to {ROUTES_FILE}")
        return True
    except Exception as e:
        print(f"Warning: Could not backup routes: {e}")
        return False


def restore_routes():
    """Restore backed up routes"""
    if not os.path.exists(ROUTES_FILE):
        print("No backup found. Cannot restore routes.")
        return False
    
    try:
        with open(ROUTES_FILE, 'r') as f:
            backup = json.load(f)
        
        # Note: We can't fully restore all routes automatically
        # User should restore manually if needed
        if backup.get("default_route"):
            print(f"Original default route was: {backup['default_route']}")
            print("You may need to restore it manually if needed.")
        
        return True
    except Exception as e:
        print(f"Error restoring routes: {e}")
        return False


def setup_default_route(metric=None):
    """Set esp0 as default route"""
    if not interface_exists(ESP0_IF):
        print(f"Error: Interface {ESP0_IF} does not exist")
        print("Run setup_tap.py first to create the interface")
        return False
    
    # Backup current routes
    backup_routes()
    
    # Remove existing default route if it exists
    result = run_command("ip route show default", check=False, capture_output=True)
    if result.returncode == 0 and result.stdout.strip():
        print("Removing existing default route...")
        run_command("ip route del default", check=False)
    
    # Add new default route through esp0
    metric_str = f" metric {metric}" if metric else ""
    cmd = f"ip route add default via {ESP0_GATEWAY} dev {ESP0_IF}{metric_str}"
    run_command(cmd)
    print(f"✓ Set default route via {ESP0_GATEWAY} dev {ESP0_IF}")
    
    return True


def setup_specific_route(network, metric=None):
    """Add specific route through esp0"""
    if not interface_exists(ESP0_IF):
        print(f"Error: Interface {ESP0_IF} does not exist")
        return False
    
    metric_str = f" metric {metric}" if metric else ""
    cmd = f"ip route add {network} via {ESP0_GATEWAY} dev {ESP0_IF}{metric_str}"
    
    result = run_command(cmd, check=False)
    if result.returncode == 0:
        print(f"✓ Added route: {network} via {ESP0_GATEWAY} dev {ESP0_IF}")
        return True
    else:
        print(f"✗ Failed to add route (may already exist): {network}")
        return False


def remove_default_route():
    """Remove default route through esp0"""
    cmd = f"ip route del default via {ESP0_GATEWAY} dev {ESP0_IF}"
    result = run_command(cmd, check=False)
    if result.returncode == 0:
        print(f"✓ Removed default route via {ESP0_GATEWAY}")
        return True
    else:
        print("✗ No default route found to remove")
        return False


def remove_specific_route(network):
    """Remove specific route"""
    cmd = f"ip route del {network} via {ESP0_GATEWAY} dev {ESP0_IF}"
    result = run_command(cmd, check=False)
    if result.returncode == 0:
        print(f"✓ Removed route: {network}")
        return True
    else:
        print(f"✗ Route not found: {network}")
        return False


def show_routes():
    """Show current routing table"""
    print("\nCurrent routing table:")
    print("=" * 60)
    run_command("ip route show", check=False, capture_output=False)
    print("=" * 60)


def test_connectivity():
    """Test connectivity through esp0"""
    print("\nTesting connectivity...")
    
    # Test ESP32 gateway
    result = run_command(f"ping -c 2 -W 2 {ESP0_GATEWAY}", check=False)
    if result.returncode == 0:
        print(f"✓ Can reach ESP32 gateway ({ESP0_GATEWAY})")
    else:
        print(f"✗ Cannot reach ESP32 gateway ({ESP0_GATEWAY})")
    
    # Test internet (if ESP32 is connected to WiFi)
    result = run_command("ping -c 2 -W 2 8.8.8.8", check=False)
    if result.returncode == 0:
        print("✓ Can reach internet (8.8.8.8)")
    else:
        print("✗ Cannot reach internet (ESP32 may not be connected to WiFi)")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Setup routing for ESP32 WiFi modem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set esp0 as default route (all traffic)
  sudo python3 setup_routing.py --default

  # Add specific route
  sudo python3 setup_routing.py --route 192.168.1.0/24

  # Remove default route
  sudo python3 setup_routing.py --remove-default

  # Show current routes
  sudo python3 setup_routing.py --show

  # Test connectivity
  sudo python3 setup_routing.py --test
        """
    )
    
    parser.add_argument(
        "--default", "-d",
        action="store_true",
        help="Set esp0 as default route (all traffic goes through ESP32)"
    )
    
    parser.add_argument(
        "--route", "-r",
        metavar="NETWORK",
        help="Add specific route (e.g., 192.168.1.0/24)"
    )
    
    parser.add_argument(
        "--remove-default",
        action="store_true",
        help="Remove default route through esp0"
    )
    
    parser.add_argument(
        "--remove-route",
        metavar="NETWORK",
        help="Remove specific route"
    )
    
    parser.add_argument(
        "--metric", "-m",
        type=int,
        help="Route metric (lower = higher priority)"
    )
    
    parser.add_argument(
        "--show", "-s",
        action="store_true",
        help="Show current routing table"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Test connectivity through esp0"
    )
    
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Show backup route information (manual restore may be needed)"
    )
    
    return parser.parse_args()


def main():
    check_root()
    args = parse_args()
    
    if args.show:
        show_routes()
        return
    
    if args.test:
        test_connectivity()
        return
    
    if args.restore:
        restore_routes()
        return
    
    if args.remove_default:
        remove_default_route()
        return
    
    if args.remove_route:
        remove_specific_route(args.remove_route)
        return
    
    if args.default:
        setup_default_route(metric=args.metric)
        show_routes()
        test_connectivity()
        return
    
    if args.route:
        setup_specific_route(args.route, metric=args.metric)
        show_routes()
        return
    
    # No action specified, show help
    print("ESP32 WiFi Modem - Routing Setup")
    print("=" * 40)
    print("\nNo action specified. Use --help for usage information.")
    print("\nQuick start:")
    print("  sudo python3 setup_routing.py --default  # Route all traffic through ESP32")
    print("  sudo python3 setup_routing.py --show     # Show current routes")


if __name__ == "__main__":
    main()

