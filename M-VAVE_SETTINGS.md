# M-Vave Chocolate Plus Settings Guide

Complete configuration guide for the M-Vave Chocolate Plus Bluetooth MIDI foot controller used with the CQ-20B Foot Controller Bridge.

---

## Device Overview

**Model**: M-Vave Chocolate Plus
**Type**: 4-button Bluetooth MIDI foot controller
**Connection**: Bluetooth MIDI (BLE MIDI)
**Power**: Built-in rechargeable battery
**Manual**: [M-Vave Chocolate Plus Manual](https://manuals.plus/asin/B0DJ3JKC7N)

---

## Button Layout

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

---

## Button Configuration

### Default CC Numbers

Each button sends MIDI Control Change (CC) messages when pressed:

| Button | CC Number | Function | Value |
|--------|-----------|----------|-------|
| **A** | 20 | Recording Start/Stop | 127 (pressed) |
| **B** | 21 | Monitor Level Toggle | 127 (pressed) |
| **C** | 22 | FX Mute Toggle | 127 (pressed) |
| **D** | 23 | Break Mode Toggle | 127 (pressed) |

**⚠️ IMPORTANT**: These CC numbers may vary depending on your M-Vave configuration. Use `test_midi.py` to discover your actual CC numbers.

### Button Functions in CQ-20B Bridge

**Button A - Recording Control**
- **Action**: Start/Stop USB/SD recording on CQ-20B mixer
- **Protocol**: MIDI Note On/Off (Note 0x30 - Soft Key #1)
- **Behavior**: Toggle - press once to start, press again to stop

**Button B - Monitor Level**
- **Action**: Toggle AUX monitor level between high and low
- **Protocol**: NRPN (MSB: 0x4F, LSB: 0x01)
- **Values**:
  - Low: 50 (configurable in config.yaml)
  - High: 100 (configurable in config.yaml)

**Button C - FX Mute**
- **Action**: Toggle FX mute group on/off
- **Protocol**: NRPN Mute Group 4 (MSB: 0x04, LSB: 0x03)
- **Behavior**: Toggle - press to mute FX, press again to unmute

**Button D - Break Mode**
- **Action**: Scene switch between performance and break music
- **Protocol**: Multiple NRPN mute group commands
- **Active State** (Break Music Playing):
  - Mute: Groups 1 (Vocals), 2 (Instruments), 4 (FX)
  - Unmute: Group 3 (Break Music - ST2 In)
- **Inactive State** (Live Performance):
  - Mute: Group 3 (Break Music)
  - Unmute: Groups 1 (Vocals), 2 (Instruments), 4 (FX)

---

## Discovering Your CC Numbers

### Using test_midi.py

The M-Vave may send different CC numbers depending on factory settings or user configuration. To find your actual CC numbers:

```bash
cd ~/cq-bluetooth-controller
./test_midi.py
```

**Steps:**
1. Run the test script
2. Press each button one at a time
3. Note the CC number displayed for each button
4. Update `config.yaml` with your actual CC numbers

**Example Output:**
```
MIDI Input Test Utility
Listening for MIDI messages from M-Vave...
Press Ctrl+C to exit

Button A pressed → control_change channel=0 control=20 value=127
Button B pressed → control_change channel=0 control=21 value=127
Button C pressed → control_change channel=0 control=22 value=127
Button D pressed → control_change channel=0 control=23 value=127
```

---

## Bluetooth Pairing

### Pairing with Raspberry Pi

**Quick Method:**
```bash
./pair_mvave.sh
```

**Manual Method:**
```bash
sudo bluetoothctl
power on
agent on
scan on
# Wait for M-Vave to appear in scan results
# Look for device name containing "Chocolate", "M-VAVE", or "Bluetooth"
pair [MAC_ADDRESS]
trust [MAC_ADDRESS]
connect [MAC_ADDRESS]
exit
```

### Finding M-Vave MAC Address

The controller auto-detects M-Vave devices by name patterns:
- "Chocolate"
- "M-VAVE"
- "M-vave"
- "Bluetooth"

To find the exact MAC address:
```bash
bluetoothctl devices | grep -i "chocolate\|m-vave\|bluetooth"
```

---

## Configuration in config.yaml

### Button Mapping Section

```yaml
button_mapping:
  button_a:
    cc_number: 20  # Recording control
    description: "USB Recording Start/Stop"
  button_b:
    cc_number: 21  # Monitor level
    description: "AUX Monitor Level Toggle"
  button_c:
    cc_number: 22  # FX mute
    description: "FX Mute Group Toggle"
  button_d:
    cc_number: 23  # Break mode
    description: "Break Mode (Scene Switch)"
```

**To Update:**
1. Run `./test_midi.py` to discover your CC numbers
2. Edit `config.yaml` with your actual values
3. Restart the service: `sudo systemctl restart cq-footcontroller`

### Bluetooth Device Detection

```yaml
bluetooth:
  # Auto-detect M-Vave by these name patterns
  device_name_patterns:
    - "Chocolate"
    - "M-VAVE"
    - "M-vave"
    - "Bluetooth"
  # Leave empty to auto-detect, or specify exact MIDI port name
  midi_port: ""
```

**Manual MIDI Port:**
If auto-detection fails, specify the exact MIDI port name:
```yaml
bluetooth:
  midi_port: "M-Vave Chocolate MIDI 1"
```

---

## Customizing Button Behavior

### Changing Monitor Levels

Edit the `behaviors` section in `config.yaml`:

```yaml
behaviors:
  aux_monitor:
    type: "toggle"
    preset_levels:
      low: 50   # Adjust to your preference (0-127)
      high: 100 # Adjust to your preference (0-127)
```

**Values:**
- Range: 0-127 (MIDI standard)
- 0 = Silent
- 64 = Medium volume
- 127 = Maximum volume

### Changing Break Mode Groups

Customize which mute groups are affected by break mode:

```yaml
behaviors:
  break_mode:
    type: "toggle"
    active_state:
      mute_groups: [1, 2, 4]    # Which groups to mute
      unmute_groups: [3]        # Which groups to unmute
    inactive_state:
      mute_groups: [3]          # Which groups to mute
      unmute_groups: [1, 2, 4]  # Which groups to unmute
```

**Mute Group Numbers:**
- Group 1: Vocals
- Group 2: Instruments
- Group 3: Break Music (ST2 In)
- Group 4: FX (Effects)

---

## Troubleshooting

### M-Vave Not Detected

**Check Bluetooth Connection:**
```bash
bluetoothctl devices
# Should show M-Vave in the list
```

**Re-pair if needed:**
```bash
bluetoothctl
remove [MAC_ADDRESS]
scan on
pair [NEW_MAC_ADDRESS]
trust [NEW_MAC_ADDRESS]
```

**Check service logs:**
```bash
sudo journalctl -u cq-footcontroller -n 50
# Look for "MIDI Input initialized" message
```

### Buttons Not Responding

**Verify MIDI messages are being received:**
```bash
./test_midi.py
# Press each button and verify messages appear
```

**Check CC numbers match config.yaml:**
1. Note CC numbers from test_midi.py
2. Compare with config.yaml button_mapping section
3. Update config.yaml if different
4. Restart service

**Check service status:**
```bash
sudo systemctl status cq-footcontroller
# Should show "active (running)"
```

### Wrong Button Actions

**Verify button mapping in config.yaml:**
- Ensure CC numbers match your M-Vave output
- Verify NRPN addresses are correct
- Check mute group assignments

**Test each button individually:**
1. Press button
2. Check logs: `sudo journalctl -u cq-footcontroller -f`
3. Verify expected NRPN messages are sent

### Battery and Power

**Charging:**
- Use USB-C cable to charge
- Charge indicator LED shows status
- Fully charge before first use

**Battery Life:**
- Typical: 8-12 hours continuous use
- Bluetooth connection drains battery faster
- Turn off when not in use to conserve power

**Power Saving:**
- M-Vave auto-sleeps after inactivity
- Press any button to wake
- Controller automatically reconnects on wake

---

## Advanced Configuration

### MIDI Channel

By default, the controller uses MIDI channel 1 (channel 0 in zero-indexed):

```yaml
advanced:
  midi_channel: 0  # MIDI channel (0-15, where 0 = channel 1)
```

**To change:**
1. Update `midi_channel` value (0-15)
2. Ensure M-Vave is sending on same channel
3. Restart service

### Custom MIDI Port Name

If you have multiple MIDI devices, specify the exact M-Vave port:

```bash
# List available MIDI ports
python3 -c "import mido; print(mido.get_input_names())"
```

Update config.yaml:
```yaml
bluetooth:
  midi_port: "M-Vave Chocolate MIDI 1"  # Use exact name from list
```

---

## Resources

### Official Documentation
- [M-Vave Chocolate Plus Manual](https://manuals.plus/asin/B0DJ3JKC7N)
- [Amazon Product Page](https://www.amazon.com/dp/B0DJ3JKC7N)

### Project Documentation
- `README.md` - Project overview
- `SETUP_GUIDE.md` - Complete setup instructions
- `QUICK_REFERENCE.md` - Quick reference card for live use
- `TROUBLESHOOTING.md` - Common issues and solutions

### Testing Utilities
- `test_midi.py` - Discover CC numbers and test MIDI input
- `test_connection.py` - Test mixer connection
- `pair_mvave.sh` - Bluetooth pairing helper

---

## Quick Reference Card

| Button | CC# | Function | Toggle States |
|--------|-----|----------|--------------|
| **A** | 20 | Recording | Stop ↔ Recording |
| **B** | 21 | Monitor | Low (50) ↔ High (100) |
| **C** | 22 | FX Mute | FX On ↔ FX Muted |
| **D** | 23 | Break Mode | Performance ↔ Break Music |

**Service Commands:**
```bash
sudo systemctl status cq-footcontroller   # Check status
sudo systemctl restart cq-footcontroller  # Restart service
sudo journalctl -u cq-footcontroller -f   # View live logs
```

**Configuration:**
```bash
nano ~/cq-bluetooth-controller/config.yaml  # Edit config
./test_midi.py                              # Find CC numbers
./pair_mvave.sh                             # Pair M-Vave
```

---

*For technical details about the CQ-20B MIDI protocol and NRPN implementation, see `NRPN_CONFIGURATION_COMPLETE.md`*
