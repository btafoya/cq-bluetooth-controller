# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wireless MIDI bridge connecting M-Vave Chocolate Plus Bluetooth foot controller to Allen & Heath CQ-20B digital mixer via Raspberry Pi 3B for live performance control. **Mission-critical reliability** is paramount - this runs during live gigs.

**Signal Flow**: M-Vave (Bluetooth MIDI) → Raspberry Pi 3B (Bridge) → CQ-20B (TCP/IP MIDI on port 51325)

## Core Architecture

### Three-Component System
1. **MIDI Input Handler** (`cq_foot_controller.py:FootController`): Listens for Bluetooth MIDI from M-Vave, processes button CC messages
2. **TCP Connection Manager** (`cq_foot_controller.py:CQConnection`): Maintains persistent TCP connection to mixer, handles auto-reconnect, sends keepalive (0xFE every 300ms)
3. **NRPN Protocol Translator** (`build_nrpn()`): Converts button presses to NRPN messages for CQ-20B control

### Key Design Decisions
- **Config-driven**: All settings in `config.yaml` - no code changes needed for customization
- **Toggle state management**: Buttons maintain internal state (recording on/off, FX muted/unmuted, etc.)
- **Auto-reconnect**: Critical for live use - connection loss triggers automatic reconnection attempts
- **Break Mode**: Button D controls complex scene switch (mutes groups 1,2,4 + unmutes group 3, or inverse)

### NRPN Protocol (Critical!)
CQ-20B uses NRPN (Non-Registered Parameter Numbers), **not simple CC messages**. Format:
```
B0 63 [MSB]      # NRPN MSB
B0 62 [LSB]      # NRPN LSB
B0 06 [VAL_MSB]  # Data Entry MSB
B0 26 [VAL_LSB]  # Data Entry LSB
```

NRPN addresses are **already configured** from CQ MIDI Protocol V1.2 PDF:
- Mute Groups: MSB=0x04, LSB=0x00-0x03 (groups 1-4)
- Recording: Soft Key Note 0x30 (not NRPN)
- AUX Send: MSB=0x4F, LSB=0x01

## Development Commands

### Testing & Debugging
```bash
# Discover M-Vave button CC numbers
./test_midi.py

# Test mixer network connectivity and TCP connection
./test_connection.py

# Run controller manually (foreground with logging)
python3 cq_foot_controller.py
```

### Service Management
```bash
# View real-time logs
sudo journalctl -u cq-footcontroller -f

# Restart after config changes
sudo systemctl restart cq-footcontroller

# Check service status
sudo systemctl status cq-footcontroller
```

### Configuration Updates
After editing `config.yaml`:
```bash
sudo systemctl restart cq-footcontroller
sudo journalctl -u cq-footcontroller -n 20  # Verify restart
```

## File Responsibilities

- `cq_foot_controller.py`: Main controller - MIDI input, TCP connection, NRPN translation, state management
- `config.yaml`: **User-editable** configuration - mixer IP, button CC numbers, NRPN addresses, behaviors
- `test_midi.py`: Utility to discover M-Vave button CC numbers (required during setup)
- `test_connection.py`: Network/TCP connection validator
- `install.sh`: Dependency installer (mido, python-rtmidi, bluez, systemd service)
- `pair_mvave.sh`: Bluetooth pairing helper script
- `cq-footcontroller.service`: Systemd service definition with auto-restart

## Common Modifications

### Adding/Changing Button Functions
1. Identify the button's CC number using `./test_midi.py`
2. Update `config.yaml` → `button_mapping` section
3. Add handler in `FootController.handle_cc_message()` following existing pattern
4. Define behavior in `config.yaml` → `behaviors` section
5. Test with `python3 cq_foot_controller.py` before deploying

### Changing Mute Group Assignments
Edit `config.yaml` → `behaviors` → `break_mode` → `active_state/inactive_state`:
- `mute_groups`: List of groups to mute (1-4)
- `unmute_groups`: List of groups to unmute (1-4)

**No code changes needed** - just restart service after config edit.

### Finding NRPN Addresses
Reference: [CQ MIDI Protocol V1.2 PDF](https://www.allen-heath.com/content/uploads/2024/06/CQ_MIDI_Protocol_V1_2_0_iss2.pdf)

See `NRPN_CONFIGURATION_COMPLETE.md` for current mappings and extraction methodology.

## Critical Constraints

### Live Performance Requirements
- **Zero tolerance for crashes**: All exceptions caught and logged
- **Auto-reconnect mandatory**: TCP connection must recover from network interruptions
- **Keepalive required**: Send 0xFE every 300ms or mixer drops connection
- **Threading safety**: Keepalive runs in background thread, main thread handles MIDI

### Protocol Requirements
- **NRPN sequence critical**: MSB before LSB, Data Entry MSB before LSB
- **Delay between messages**: 10ms delay (`nrpn_send_delay`) prevents message corruption
- **Channel**: MIDI channel 0 (displays as channel 1 in mixer)
- **Value ranges**: 0-127 for all MIDI values

### Deployment Environment
- **Platform**: Raspberry Pi 3B with Raspbian/Raspberry Pi OS
- **Python**: 3.7+ (system Python, not virtualenv for systemd service)
- **Network**: Ethernet preferred over WiFi for stability
- **Bluetooth**: Built-in Pi 3B Bluetooth, bluez stack

## Troubleshooting Context

### Connection Issues
- Mixer IP must match actual CQ-20B IP (find in CQ MixPad app → Settings → Network)
- Port 51325 is hardcoded in mixer, rarely changes
- `test_connection.py` should show "Connected to mixer!" if network is correct

### Button Issues
- CC numbers vary between M-Vave units - **must run test_midi.py** to discover
- M-Vave sends CC messages on button **release**, not press
- State toggles are managed in software, not hardware

### NRPN Issues
- If controls don't work, verify MSB/LSB against CQ MIDI Protocol PDF (page references in config comments)
- Recording uses Note On/Off (0x30), not NRPN
- Some mixer functions may require specific firmware versions

## Documentation Structure

- `README.md`: Quick start and overview
- `SETUP_GUIDE.md`: Complete installation walkthrough
- `QUICK_REFERENCE.md`: Printable button reference for live use
- `TROUBLESHOOTING.md`: Common issues and solutions
- `NRPN_CONFIGURATION_COMPLETE.md`: Technical NRPN details and sources
- `.claude/CLAUDE.md`: Project context (this file - DO NOT edit)

## Code Style Notes

- Logging uses emoji prefixes for visual scanning: ✓ = success, ❌ = error, ⚠️ = warning, 🎹 = MIDI event
- Class-based architecture with single responsibility (Config, CQConnection, FootController)
- Defensive programming: all network/MIDI operations wrapped in try/except
- Config validation on startup with helpful error messages pointing to `config.yaml`

## Testing Strategy

Pre-deployment testing sequence:
1. `./test_midi.py` → Verify M-Vave pairing and CC numbers
2. `./test_connection.py` → Verify mixer network connectivity
3. `python3 cq_foot_controller.py` → Full integration test with logging
4. Test each button function individually
5. Test auto-reconnect (unplug/replug Ethernet)
6. Enable service and test reboot persistence
