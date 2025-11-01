#!/bin/bash
# Automated deployment to read-only Raspberry Pi
# Usage: ./deploy_to_readonly_pi.sh [pi_ip] [pi_user]

set -e  # Exit on error

PI_IP="${1:-192.168.25.173}"
PI_USER="${2:-btafoya}"
PROJECT_NAME="cq-bluetooth-controller"
REMOTE_DIR="~/${PROJECT_NAME}"

echo "=========================================="
echo "CQ-20B Foot Controller - Automated Deployment"
echo "Target: ${PI_USER}@${PI_IP}"
echo "=========================================="
echo ""

# Step 1: Disable overlay filesystem
echo "Step 1: Disabling overlay filesystem..."
ssh ${PI_USER}@${PI_IP} "sudo raspi-config nonint do_overlayfs 1"
echo "✓ Overlay disabled"
echo ""

echo "Step 2: Rebooting Pi (waiting 30 seconds)..."
ssh ${PI_USER}@${PI_IP} "sudo reboot" || true
sleep 30

# Wait for Pi to come back online
echo "Waiting for Pi to boot..."
for i in {1..30}; do
    if ssh -o ConnectTimeout=2 ${PI_USER}@${PI_IP} "echo 'online'" &>/dev/null; then
        echo "✓ Pi is back online"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Verify overlay is disabled
echo "Verifying overlay is disabled..."
OVERLAY_STATUS=$(ssh ${PI_USER}@${PI_IP} "cat /proc/cmdline | grep -o 'overlayroot=[^ ]*' || echo 'disabled'")
echo "Overlay status: $OVERLAY_STATUS"
echo ""

# Step 3: Transfer project files
echo "Step 3: Transferring project files..."
ssh ${PI_USER}@${PI_IP} "rm -rf ${REMOTE_DIR}"
scp -r "$(dirname "$0")" ${PI_USER}@${PI_IP}:~/
ssh ${PI_USER}@${PI_IP} "mv ~/${PROJECT_NAME} ~/${PROJECT_NAME} 2>/dev/null || true"
echo "✓ Files transferred"
echo ""

# Step 4: Run installation
echo "Step 4: Running installation script..."
ssh ${PI_USER}@${PI_IP} "cd ${REMOTE_DIR} && chmod +x install.sh && ./install.sh"
echo "✓ Installation complete"
echo ""

# Step 5: Check installation
echo "Step 5: Verifying installation..."
ssh ${PI_USER}@${PI_IP} "cd ${REMOTE_DIR} && python3 -c 'import mido, yaml; print(\"✓ Python dependencies OK\")'"
ssh ${PI_USER}@${PI_IP} "systemctl status cq-footcontroller.service --no-pager || echo '⚠ Service installed but not started (needs config)'"
echo ""

# Step 6: Configuration reminder
echo "=========================================="
echo "⚠️  MANUAL STEP REQUIRED"
echo "=========================================="
echo "Before enabling overlay, you need to configure:"
echo ""
echo "1. Find your CQ-20B mixer IP address"
echo "2. Edit config.yaml on the Pi:"
echo "   ssh ${PI_USER}@${PI_IP}"
echo "   nano ${REMOTE_DIR}/config.yaml"
echo ""
echo "3. Update these settings:"
echo "   - mixer_ip: \"<YOUR_CQ20B_IP>\""
echo "   - button_mapping CC numbers (run ./test_midi.py)"
echo ""
echo "4. Pair M-Vave:"
echo "   cd ${REMOTE_DIR} && ./pair_mvave.sh"
echo ""
echo "5. Test:"
echo "   python3 ${REMOTE_DIR}/cq_foot_controller.py"
echo ""
echo "6. Enable and start service:"
echo "   sudo systemctl enable cq-footcontroller.service"
echo "   sudo systemctl start cq-footcontroller.service"
echo ""
echo "=========================================="
echo ""
read -p "Press Enter when configuration is complete, or Ctrl+C to finish manually..."

# Step 7: Re-enable overlay
echo ""
echo "Step 7: Re-enabling overlay filesystem..."
ssh ${PI_USER}@${PI_IP} "sudo raspi-config nonint do_overlayfs 0"
echo "✓ Overlay enabled"
echo ""

echo "Step 8: Final reboot..."
ssh ${PI_USER}@${PI_IP} "sudo reboot" || true
echo "✓ Pi rebooting..."
echo ""

sleep 30
echo "Waiting for Pi to boot with overlay enabled..."
for i in {1..30}; do
    if ssh -o ConnectTimeout=2 ${PI_USER}@${PI_IP} "echo 'online'" &>/dev/null; then
        echo "✓ Pi is back online"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# Final verification
echo "=========================================="
echo "Final Verification"
echo "=========================================="
ssh ${PI_USER}@${PI_IP} "echo '=== Overlay Status ===' && cat /proc/cmdline | grep -o 'overlayroot=[^ ]*' && echo '' && echo '=== Service Status ===' && systemctl status cq-footcontroller.service --no-pager -l"
echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "View logs: ssh ${PI_USER}@${PI_IP} 'sudo journalctl -u cq-footcontroller -f'"
