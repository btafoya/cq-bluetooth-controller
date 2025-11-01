#!/bin/bash
# CQ-20B Foot Controller Installation Script

set -e  # Exit on error

echo "============================================"
echo "CQ-20B Foot Controller Installation"
echo "============================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please do NOT run this script as root!"
    echo "Run as: ./install.sh"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-yaml \
    bluez \
    libasound2-dev \
    libjack-dev

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user --break-system-packages mido python-rtmidi pyyaml

# Make script executable
echo "🔧 Making scripts executable..."
chmod +x cq_foot_controller.py
chmod +x test_midi.py
chmod +x test_connection.py
chmod +x pair_mvave.sh

# Check if config exists
if [ ! -f config.yaml ]; then
    echo "⚠️  No config.yaml found"
    echo "📝 Please edit config.yaml with your settings"
else
    echo "✓ config.yaml found"
fi

# Install systemd service
echo "⚙️  Installing systemd service..."
sudo cp cq-footcontroller.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "============================================"
echo "✅ Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit configuration:"
echo "   nano config.yaml"
echo ""
echo "2. Pair M-Vave foot controller:"
echo "   ./pair_mvave.sh"
echo ""
echo "3. Test the controller:"
echo "   python3 cq_foot_controller.py"
echo ""
echo "4. Enable service (auto-start on boot):"
echo "   sudo systemctl enable cq-footcontroller.service"
echo "   sudo systemctl start cq-footcontroller.service"
echo ""
echo "5. Check service status:"
echo "   sudo systemctl status cq-footcontroller.service"
echo ""
echo "6. View logs:"
echo "   sudo journalctl -u cq-footcontroller -f"
echo ""
