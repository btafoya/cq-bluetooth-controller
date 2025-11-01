# CQ-20B Bluetooth Foot Controller

Wireless MIDI foot controller bridge connecting M-Vave Chocolate Plus to Allen & Heath CQ-20B digital mixer via Raspberry Pi 3B.

## 🎯 Features

- **Wireless Control**: Bluetooth MIDI from foot controller to mixer via TCP/IP
- **4 Configurable Buttons**:
  - Recording start/stop (USB/SD)
  - Monitor level toggle (high/low)
  - FX mute control
  - Break mode (instant scene switching)
- **Mission-Critical Reliability**: Auto-reconnect on connection loss
- **Configuration-Driven**: Easy customization via YAML config
- **Production Ready**: Systemd service with auto-start and logging

## 📋 Requirements

### Hardware
- Raspberry Pi 3B (with built-in Bluetooth and Ethernet)
- M-Vave Chocolate Plus Bluetooth foot controller
- Allen & Heath CQ-20B digital mixer
- Network connection (Ethernet cable or WiFi)
- Power supply for Raspberry Pi

### Software
- Raspberry Pi OS (Raspbian)
- Python 3.7+
- Bluetooth support (bluez)

## 🚀 Quick Start

### 1. Download and Install

```bash
# Clone or download project
cd ~
git clone <repository-url> cq-controller
# OR download and extract zip file

cd cq-controller

# Run installation script
chmod +x install.sh
./install.sh
```

### 2. Configure

```bash
# Edit configuration file
nano config.yaml
```

**Critical settings to update:**
- `mixer_ip`: Your CQ-20B IP address (find in CQ MixPad app)
- `button_mapping`: CC numbers from your M-Vave controller (use `./test_midi.py`)
- ✅ `nrpn_addresses`: **Already configured** with correct values from CQ MIDI Protocol PDF

### 3. Pair M-Vave

```bash
# Run pairing helper
./pair_mvave.sh
```

Or manually:
```bash
sudo bluetoothctl
power on
agent on
scan on
# Wait for M-Vave to appear
pair [MAC_ADDRESS]
trust [MAC_ADDRESS]
connect [MAC_ADDRESS]
exit
```

### 4. Test

```bash
# Run manually to test
python3 cq_foot_controller.py

# Press buttons and verify functionality
```

### 5. Enable Service

```bash
# Install as system service
sudo cp cq-footcontroller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cq-footcontroller.service
sudo systemctl start cq-footcontroller.service

# Check status
sudo systemctl status cq-footcontroller.service
```

## 🎛️ Button Layout

```
┌────────────────────────────────────────────────┐
│        M-Vave Chocolate Plus Layout            │
├────────────────────────────────────────────────┤
│  [A]           [B]           [C]          [D]  │
│  Recording     Monitor       FX Mute      BREAK│
│  Start/Stop    Hi/Lo         Toggle       MODE │
│  ⏺️            🔊            🎛️           ☕   │
└────────────────────────────────────────────────┘
```

### Mute Groups
- **Group 1**: Vocals
- **Group 2**: Instruments
- **Group 3**: Break Music (ST2 In)
- **Group 4**: FX (Effects)

### Break Mode
- **Active**: Mutes vocals, instruments, FX; plays break music
- **Inactive**: Mutes break music; unmutes vocals, instruments, FX

## 📖 Documentation

- `QUICK_REFERENCE.md` - Quick reference card for live use
- `SETUP_GUIDE.md` - Detailed setup instructions
- `TROUBLESHOOTING.md` - Common issues and solutions
- `NRPN_CONFIGURATION_COMPLETE.md` - NRPN configuration details and technical reference
- `.claude/CLAUDE.md` - Complete project context for AI assistance

## 🔧 Configuration

All settings in `config.yaml`:

```yaml
network:
  mixer_ip: "192.168.1.100"  # YOUR CQ-20B IP
  mixer_port: 51325

button_mapping:
  button_a:
    cc_number: 20  # Check your M-Vave
  # ... etc

nrpn_addresses:
  # ✅ Already configured with correct values
  recording:
    soft_key_note: 0x30  # Soft Key #1 (C3)
  mute_group_1:
    msb: 0x04  # VOCALS
    lsb: 0x00
  mute_group_2:
    msb: 0x04  # INSTRUMENTS
    lsb: 0x01
  mute_group_3:
    msb: 0x04  # BREAK MUSIC
    lsb: 0x02
  mute_group_4:
    msb: 0x04  # FX
    lsb: 0x03
  aux_send_level:
    msb: 0x4F  # Out1
    lsb: 0x01
```

## 🛠️ Utilities

### Test MIDI Input
```bash
./test_midi.py
# Shows MIDI messages from M-Vave
```

### Test Mixer Connection
```bash
./test_connection.py
# Tests TCP connection to CQ-20B
```

### View Logs
```bash
# Real-time logs
sudo journalctl -u cq-footcontroller -f

# Last 100 lines
sudo journalctl -u cq-footcontroller -n 100
```

## 📚 Resources

- [CQ-20B MIDI Protocol PDF](https://www.allen-heath.com/content/uploads/2024/06/CQ_MIDI_Protocol_V1_2_0_iss2.pdf)
- [M-Vave Chocolate Plus Manual](https://manuals.plus/asin/B0DJ3JKC7N)
- [Allen & Heath CQ-20B Product Page](https://www.allen-heath.com/hardware/cq/cq-20b/)

## 🆘 Troubleshooting

**M-Vave not detected:**
```bash
./test_midi.py
# Check Bluetooth pairing: bluetoothctl devices
```

**Connection to mixer fails:**
```bash
./test_connection.py
# Verify IP: ping 192.168.1.100
```

**Service not starting:**
```bash
sudo systemctl status cq-footcontroller.service
sudo journalctl -u cq-footcontroller -n 50
```

## 🔐 Security Notes

- Runs as unprivileged user (pi)
- No external network access required
- Local network only (mixer connection)

## 📝 License

MIT License - Free to use and modify

## 🙏 Credits

Built for live performance with Allen & Heath CQ-20B digital mixers.

Based on Arduino MIDI-over-TCP research from Arduino forum community.
