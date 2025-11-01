#!/usr/bin/env python3
"""
Test MIDI Input from M-Vave Chocolate Plus
Run this to discover CC numbers for button mapping
"""

import mido
import sys

def main():
    print("=" * 60)
    print("MIDI Input Tester - M-Vave Chocolate Plus")
    print("=" * 60)
    print()

    # List available MIDI ports
    available_ports = mido.get_input_names()
    print("Available MIDI ports:")
    for i, port in enumerate(available_ports):
        print(f"  {i}: {port}")
    print()

    if not available_ports:
        print("❌ No MIDI ports found!")
        print("Check:")
        print("  1. M-Vave is paired via Bluetooth")
        print("  2. M-Vave is powered on")
        print("  3. Run: bluetoothctl devices")
        sys.exit(1)

    # Try to find M-Vave port
    mvave_port = None
    patterns = ["Chocolate", "M-VAVE", "M-vave", "Bluetooth"]

    for port in available_ports:
        for pattern in patterns:
            if pattern.lower() in port.lower():
                mvave_port = port
                break
        if mvave_port:
            break

    if not mvave_port:
        print("⚠️  M-Vave not auto-detected")
        print("Select port number: ", end="")
        try:
            choice = int(input())
            mvave_port = available_ports[choice]
        except (ValueError, IndexError):
            print("Invalid selection")
            sys.exit(1)

    print(f"✓ Opening MIDI port: {mvave_port}")
    print()
    print("=" * 60)
    print("Press buttons on M-Vave to see MIDI messages")
    print("Press Ctrl+C to exit")
    print("=" * 60)
    print()

    try:
        with mido.open_input(mvave_port) as inport:
            for msg in inport:
                print(f"⚡ {msg}")

                if msg.type == 'control_change':
                    print(f"   → CC Number: {msg.control}, Value: {msg.value}")
                elif msg.type == 'note_on':
                    print(f"   → Note: {msg.note}, Velocity: {msg.velocity}")
                elif msg.type == 'note_off':
                    print(f"   → Note Off: {msg.note}")
                print()

    except KeyboardInterrupt:
        print("\nDone!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
