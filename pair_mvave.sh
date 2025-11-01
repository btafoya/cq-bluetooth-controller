#!/bin/bash
# Pair M-Vave Chocolate Plus Bluetooth Foot Controller

echo "============================================"
echo "M-Vave Chocolate Plus Pairing Helper"
echo "============================================"
echo ""
echo "Instructions:"
echo "1. Put your M-Vave in pairing mode"
echo "2. Wait for device to appear in scan"
echo "3. Note the MAC address (e.g., 00:11:22:33:44:55)"
echo "4. Follow prompts to pair"
echo ""
echo "Starting Bluetooth control..."
echo ""

sudo bluetoothctl << EOF
power on
agent on
default-agent
scan on
EOF

echo ""
echo "============================================"
echo "Scan running... Press Ctrl+C when you see your device"
echo "============================================"
echo ""
echo "After you find the MAC address, run:"
echo "sudo bluetoothctl"
echo ""
echo "Then in bluetoothctl:"
echo "  pair [MAC_ADDRESS]"
echo "  trust [MAC_ADDRESS]"
echo "  connect [MAC_ADDRESS]"
echo "  exit"
echo ""
