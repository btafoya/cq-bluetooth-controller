# Complete Setup Guide

Step-by-step instructions for setting up your CQ-20B Bluetooth Foot Controller.

## Prerequisites

- Raspberry Pi 3B with Raspberry Pi OS installed
- M-Vave Chocolate Plus Bluetooth foot controller
- Allen & Heath CQ-20B digital mixer
- Network connection (Ethernet recommended, WiFi works too)
- MicroSD card (8GB+) for Raspberry Pi
- Power supply for Raspberry Pi (5V 2.5A minimum)

## Step 1: Prepare Raspberry Pi

### 1.1 Fresh Install (if needed)

```bash
# Flash Raspberry Pi OS Lite to SD card
# Use Raspberry Pi Imager: https://www.raspberrypi.com/software/

# Boot Pi and complete initial setup
# Enable SSH if remote access needed:
sudo raspi-config
# Interface Options → SSH → Enable
```

### 1.2 Update System

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

## Step 2: Download Project

```bash
cd ~
# If using git:
git clone <repository-url> cq-controller

# OR download and extract zip:
wget <download-url>
unzip cq-controller.zip
mv cq-controller-main cq-controller

cd cq-controller
```

## Step 3: Run Installation

```bash
chmod +x install.sh
./install.sh
```

This installs:
- Python 3 and required libraries
- Bluetooth support (bluez)
- MIDI libraries (mido, python-rtmidi)
- Systemd service

## Step 4: Configure CQ-20B Mixer

### 4.1 Find Mixer IP Address

**Option A: Using CQ MixPad App**
1. Open CQ MixPad on tablet/phone
2. Connect to CQ-20B
3. Go to Settings → Network
4. Note the IP address (e.g., 192.168.1.100)

**Option B: Using Router Admin**
1. Log into your router admin page
2. Find DHCP client list
3. Look for "CQ-20B" or Allen & Heath device
4. Note the IP address

### 4.2 Setup Mute Groups in Mixer

Open CQ MixPad and configure mute groups:

**Mute Group 1: VOCALS**
- Add all vocal microphone channels
- This will be muted during breaks

**Mute Group 2: INSTRUMENTS**
- Add all instrument channels
- This will be muted during breaks

**Mute Group 3: BREAK MUSIC**
- Add ST2 In channel (your break music source)
- Connect music player/phone to ST2 In
- This plays only during breaks

**Mute Group 4: FX**
- Add FX return channels (reverb, delay, etc.)
- Use Button C to toggle effects on/off

## Step 5: Configure Project

```bash
cd ~/cq-controller
nano config.yaml
```

### 5.1 Update Mixer IP

```yaml
network:
  mixer_ip: "192.168.1.100"  # ← Change to YOUR CQ-20B IP!
```

### 5.2 NRPN Addresses ✅ **Already Configured**

Good news! NRPN addresses have been automatically configured from the CQ MIDI Protocol PDF.

**No action needed** - the following are already set in `config.yaml`:
```yaml
nrpn_addresses:
  recording:
    soft_key_note: 0x30  # ✅ Soft Key #1 (C3)
  mute_group_1:
    msb: 0x04  # ✅ MGRP1 (VOCALS)
    lsb: 0x00
  mute_group_2:
    msb: 0x04  # ✅ MGRP2 (INSTRUMENTS)
    lsb: 0x01
  mute_group_3:
    msb: 0x04  # ✅ MGRP3 (BREAK MUSIC)
    lsb: 0x02
  mute_group_4:
    msb: 0x04  # ✅ MGRP4 (FX)
    lsb: 0x03
  aux_send_level:
    msb: 0x4F  # ✅ Output level (Out1)
    lsb: 0x01
```

For technical details, see `NRPN_CONFIGURATION_COMPLETE.md`.

## Step 6: Pair M-Vave Foot Controller

### 6.1 Put M-Vave in Pairing Mode

1. Power on M-Vave Chocolate Plus
2. Press and hold Bluetooth button (usually auto-pairs)
3. Blue LED should flash indicating pairing mode

### 6.2 Pair with Raspberry Pi

```bash
cd ~/cq-controller
./pair_mvave.sh
```

Or manually:
```bash
sudo bluetoothctl
power on
agent on
scan on
# Wait for M-Vave to appear (look for "Chocolate" or "M-VAVE")
# Note the MAC address (e.g., 00:11:22:33:44:55)
pair 00:11:22:33:44:55
trust 00:11:22:33:44:55
connect 00:11:22:33:44:55
exit
```

### 6.3 Find Button CC Numbers

Run MIDI tester:
```bash
./test_midi.py
```

Press each button and note CC numbers:
- Button A: CC ___
- Button B: CC ___
- Button C: CC ___
- Button D: CC ___

Update config.yaml:
```yaml
button_mapping:
  button_a:
    cc_number: ___  # Your value
  button_b:
    cc_number: ___  # Your value
  button_c:
    cc_number: ___  # Your value
  button_d:
    cc_number: ___  # Your value
```

## Step 7: Test Connection

### 7.1 Test Mixer Connection

```bash
./test_connection.py
```

Should show:
```
✓ Can ping 192.168.1.100
✓ Connected to mixer!
✓ Keepalive sent
```

### 7.2 Test Controller Manually

```bash
python3 cq_foot_controller.py
```

Press buttons and verify log output:
```
✓ Connected to CQ-20B!
✓ Opening MIDI port: M-VAVE Chocolate Plus
🎹 Listening for footswitch presses...
🔴 Recording: STARTED
🔊 AUX Monitor: HIGH
🎛️ FX Mute Group 4: ON
☕ BREAK MODE: ACTIVE
```

**Test each button:**
- Button A: Check if recording starts on mixer
- Button B: Check if monitor level changes
- Button C: Check if FX are muted
- Button D: Check if break music plays and performance audio mutes

Press Ctrl+C to stop.

## Step 8: Enable Auto-Start Service

```bash
sudo systemctl enable cq-footcontroller.service
sudo systemctl start cq-footcontroller.service
sudo systemctl status cq-footcontroller.service
```

Should show:
```
● cq-footcontroller.service - CQ-20B Bluetooth Foot Controller Bridge
   Active: active (running)
```

## Step 9: Final Testing

### 9.1 Test Auto-Reconnect

1. Unplug Ethernet cable from mixer
2. Check logs: `sudo journalctl -u cq-footcontroller -f`
3. Should see: "Connection lost! Reconnecting..."
4. Plug Ethernet back in
5. Should see: "✓ Connected to CQ-20B!"

### 9.2 Test Reboot

```bash
sudo reboot
```

After reboot:
```bash
sudo systemctl status cq-footcontroller.service
# Should be running automatically
```

## Step 10: Pre-Gig Checklist

- [ ] Raspberry Pi boots and service auto-starts
- [ ] M-Vave pairs automatically on power-on
- [ ] All 4 buttons work correctly
- [ ] Break mode switches scenes properly
- [ ] Recording function works
- [ ] Monitor level toggle works
- [ ] FX toggle works
- [ ] Auto-reconnect works if cable unplugged
- [ ] CQ MixPad app available as backup

## Common Issues

### M-Vave Won't Pair

```bash
# Remove and re-pair:
sudo bluetoothctl
remove 00:11:22:33:44:55  # Your MAC
scan on
# Pair again
```

### Service Won't Start

```bash
# Check logs:
sudo journalctl -u cq-footcontroller -n 50

# Common issues:
# - config.yaml has wrong path in service file
# - Python dependencies not installed
# - Permissions issue
```

### Buttons Don't Work

```bash
# Check MIDI port is detected:
./test_midi.py

# Verify CC numbers in config match what M-Vave sends
```

### Connection to Mixer Fails

```bash
# Verify network:
ping 192.168.1.100  # Your mixer IP

# Test connection:
./test_connection.py

# Check mixer IP is correct in config.yaml
```

## Maintenance

### Update Configuration

```bash
cd ~/cq-controller
nano config.yaml
# Make changes
sudo systemctl restart cq-footcontroller.service
```

### View Logs

```bash
# Real-time logs:
sudo journalctl -u cq-footcontroller -f

# Last 100 lines:
sudo journalctl -u cq-footcontroller -n 100

# Since boot:
sudo journalctl -u cq-footcontroller -b
```

### Update Project

```bash
cd ~/cq-controller
git pull  # If using git
# OR download new version and replace files

sudo systemctl restart cq-footcontroller.service
```

## Support Resources

- CQ-20B User Guide: https://www.allen-heath.com/hardware/cq/cq-20b/
- MIDI Protocol: https://www.allen-heath.com/content/uploads/2024/06/CQ_MIDI_Protocol_V1_2_0_iss2.pdf
- M-Vave Manual: https://manuals.plus/asin/B0DJ3JKC7N
- Project Issues: <your-repo-url>/issues
