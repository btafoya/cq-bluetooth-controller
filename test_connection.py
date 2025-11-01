#!/usr/bin/env python3
"""
Test TCP connection to CQ-20B mixer
Verifies network connectivity and MIDI protocol
"""

import socket
import time
import yaml
import sys
from pathlib import Path

def load_config():
    """Load mixer IP from config"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("❌ config.yaml not found")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config['network']['mixer_ip'], config['network']['mixer_port']

def test_connection(ip, port):
    """Test TCP connection to mixer"""
    print("=" * 60)
    print("CQ-20B Connection Tester")
    print("=" * 60)
    print()
    print(f"Mixer IP: {ip}")
    print(f"Port: {port}")
    print()

    # Test ping
    print("Testing network connectivity...")
    import os
    response = os.system(f"ping -c 1 -W 2 {ip} > /dev/null 2>&1")
    if response == 0:
        print(f"✓ Can ping {ip}")
    else:
        print(f"❌ Cannot ping {ip}")
        print("Check:")
        print("  1. Mixer is powered on")
        print("  2. Mixer is on same network")
        print("  3. Correct IP in config.yaml")
        return False

    # Test TCP connection
    print(f"Connecting to {ip}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((ip, port))
        print("✓ Connected to mixer!")

        # Send keepalive
        print("Sending keepalive byte...")
        sock.send(bytes([0xFE]))
        print("✓ Keepalive sent")

        # Wait for response (mixer may send data)
        sock.settimeout(1.0)
        try:
            data = sock.recv(1024)
            if data:
                print(f"✓ Received {len(data)} bytes from mixer")
                print(f"  Data: {' '.join(f'{b:02X}' for b in data)}")
        except socket.timeout:
            print("  (No immediate response - this is normal)")

        sock.close()
        print()
        print("=" * 60)
        print("✅ Connection test PASSED!")
        print("=" * 60)
        return True

    except socket.timeout:
        print("❌ Connection timeout")
        print("Mixer not responding on port 51325")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused")
        print("Port 51325 not open on mixer")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    try:
        ip, port = load_config()
        success = test_connection(ip, port)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nAborted")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
