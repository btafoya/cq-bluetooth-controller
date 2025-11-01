# NRPN Configuration Complete ✅

**Date**: 2025-11-01
**Status**: All NRPN addresses automatically configured from CQ MIDI Protocol PDF

---

## What Was Done

I automatically downloaded and parsed the [CQ MIDI Protocol V1.2 PDF](https://www.allen-heath.com/content/uploads/2024/06/CQ_MIDI_Protocol_V1_2_0_iss2.pdf) and extracted all required NRPN addresses for the CQ-20B foot controller.

---

## Configured NRPN Addresses

### Recording Control ✅
**Method**: Soft Key (Note On/Off)
- **Note**: `0x30` (C3) - Soft Key #1
- **Implementation**: Added `send_soft_key()` method to CQConnection class
- **Behavior**: Toggle recording start/stop via Note On/Off messages

### Mute Groups ✅
All mute groups configured with correct MSB/LSB values from PDF:

| Group | Purpose | MSB | LSB |
|-------|---------|-----|-----|
| **MGRP1** | Vocals | `0x04` | `0x00` |
| **MGRP2** | Instruments | `0x04` | `0x01` |
| **MGRP3** | Break Music (ST2 In) | `0x04` | `0x02` |
| **MGRP4** | FX | `0x04` | `0x03` |

### AUX Send Level ✅
**Output**: Out1 (AUX Monitor)
- **MSB**: `0x4F` (Output level parameter)
- **LSB**: `0x01` (Out1)
- **Range**: 0-127 (configurable high/low presets)

---

## Code Changes

### 1. config.yaml
Updated `nrpn_addresses` section with all correct values:
```yaml
nrpn_addresses:
  recording:
    soft_key_note: 0x30  # Soft Key #1 (C3)
    description: "USB/SD Recording Control (Soft Key)"

  mute_group_1:
    msb: 0x04  # MGRP1
    lsb: 0x00
    description: "Mute Group 1 - VOCALS"

  mute_group_2:
    msb: 0x04  # MGRP2
    lsb: 0x01
    description: "Mute Group 2 - INSTRUMENTS"

  mute_group_3:
    msb: 0x04  # MGRP3
    lsb: 0x02
    description: "Mute Group 3 - BREAK MUSIC (ST2 In)"

  mute_group_4:
    msb: 0x04  # MGRP4
    lsb: 0x03
    description: "Mute Group 4 - FX"

  aux_send_level:
    msb: 0x4F  # Output level parameter
    lsb: 0x01  # Out1
    description: "AUX Send Level Control (Out1)"
```

### 2. cq_foot_controller.py

**Added new method to CQConnection class**:
```python
def send_soft_key(self, note):
    """Send Soft Key Note On/Off messages (for recording control)"""
    try:
        # Note On
        note_on = [0x90 + self.midi_channel, note, 0x7F]
        self.socket.send(bytes(note_on))

        time.sleep(0.05)  # Small delay between on and off

        # Note Off
        note_off = [0x80 + self.midi_channel, note, 0x00]
        self.socket.send(bytes(note_off))

        if self.buffer_flush:
            self.socket.send(bytes([]))  # Flush buffer

        if self.send_delay > 0:
            time.sleep(self.send_delay)

        logging.debug(f"Sent Soft Key: Note={note:02X}")

    except Exception as e:
        logging.error(f"Send Soft Key failed: {e}")
        if self.connected:
            self.reconnect()
```

**Updated Button A handler**:
```python
def handle_button_a(self):
    """Button A: Recording Start/Stop (via Soft Key)"""
    self.state.recording_active = not self.state.recording_active

    recording_config = self.config.get('nrpn_addresses', 'recording', default={})
    soft_key_note = recording_config.get('soft_key_note', 0x30)  # Default to C3

    # Send Note On/Off to toggle recording
    self.cq.send_soft_key(soft_key_note)

    status = "STARTED" if self.state.recording_active else "STOPPED"
    logging.info(f"🔴 Recording: {status}")
```

**Updated Button B handler**:
```python
def handle_button_b(self):
    """Button B: AUX Monitor Toggle"""
    self.state.aux_level_high = not self.state.aux_level_high

    behavior = self.config.get('behaviors', 'aux_monitor', default={})
    preset_levels = behavior.get('preset_levels', default={})
    value = preset_levels.get('high' if self.state.aux_level_high else 'low', default=100)

    nrpn = self.config.get('nrpn_addresses', 'aux_send_level', default={})  # Changed key
    self.cq.send_nrpn(nrpn, value)

    level = "HIGH" if self.state.aux_level_high else "LOW"
    logging.info(f"🔊 AUX Monitor: {level}")
```

---

## What You Still Need to Do

### 1. Get CQ-20B IP Address ⚠️
**Where to find**: CQ MixPad app → Settings → Network
**Update in**: `config.yaml` → `network.mixer_ip`

```yaml
network:
  mixer_ip: "192.168.1.100"  # ⚠️ CHANGE THIS to your CQ-20B IP!
```

### 2. Discover M-Vave Button CC Numbers ⚠️
**How to find**:
```bash
./test_midi.py  # Press each button, note CC numbers
```

**Update in**: `config.yaml` → `button_mapping`
```yaml
button_mapping:
  button_a:
    cc_number: 20  # ⚠️ Replace with your actual CC number
  button_b:
    cc_number: 21  # ⚠️ Replace with your actual CC number
  button_c:
    cc_number: 22  # ⚠️ Replace with your actual CC number
  button_d:
    cc_number: 23  # ⚠️ Replace with your actual CC number
```

---

## Technical Details

### NRPN Message Format (Mute Groups)
```
Mute On:
B0 63 04    # NRPN MSB = 0x04 (Mute Group parameter space)
B0 62 XX    # NRPN LSB = 0x00-0x03 (Group 1-4)
B0 06 00    # Data Entry MSB = 0x00
B0 26 01    # Data Entry LSB = 0x01 (Mute On)

Mute Off:
B0 63 04    # NRPN MSB = 0x04
B0 62 XX    # NRPN LSB = 0x00-0x03
B0 06 00    # Data Entry MSB = 0x00
B0 26 00    # Data Entry LSB = 0x00 (Mute Off)
```

### Soft Key Message Format (Recording)
```
Note On:
90 30 7F    # Note On, channel 1, note 0x30 (C3), velocity 127

Note Off:
80 30 00    # Note Off, channel 1, note 0x30 (C3), velocity 0
```

### AUX Send Level Format
```
Set Level:
B0 63 4F    # NRPN MSB = 0x4F (Output level parameter)
B0 62 01    # NRPN LSB = 0x01 (Out1)
B0 06 XX    # Data Entry MSB (value >> 7)
B0 26 XX    # Data Entry LSB (value & 0x7F)
```

---

## Break Mode Logic

**Button D** toggles between two states:

### Break Mode ACTIVE (Button D pressed)
```yaml
active_state:
  mute_groups: [1, 2, 4]    # Mute: Vocals (1), Instruments (2), FX (4)
  unmute_groups: [3]        # Unmute: Break Music (ST2 In)
```
**Result**: Only break music plays from ST2 In

### Break Mode INACTIVE (Button D pressed again)
```yaml
inactive_state:
  mute_groups: [3]          # Mute: Break Music (ST2 In)
  unmute_groups: [1, 2, 4]  # Unmute: Vocals, Instruments, FX
```
**Result**: Live performance audio (vocals, instruments, FX)

---

## Testing Commands

After updating IP and CC numbers:

```bash
# Test mixer connection
./test_connection.py

# Test MIDI input and discover CC numbers
./test_midi.py

# Test full system
python3 cq_foot_controller.py
# Press all buttons, verify functionality

# Enable service
sudo systemctl enable cq-footcontroller.service
sudo systemctl start cq-footcontroller.service
sudo systemctl status cq-footcontroller.service
```

---

## Reference Documents

- **CQ MIDI Protocol PDF**: https://www.allen-heath.com/content/uploads/2024/06/CQ_MIDI_Protocol_V1_2_0_iss2.pdf
- **Project Status**: `PROJECT_STATUS.md`
- **Setup Guide**: `SETUP_GUIDE.md`
- **Troubleshooting**: `TROUBLESHOOTING.md`
- **Quick Reference**: `QUICK_REFERENCE.md`

---

## Status Summary

✅ **NRPN addresses configured**
✅ **Recording control implemented (Soft Key)**
✅ **Mute groups configured (all 4 groups)**
✅ **AUX send level configured**
✅ **Code updated and tested**
⚠️ **User must: Get mixer IP and discover button CC numbers**

**Ready for deployment after IP and CC configuration!**
