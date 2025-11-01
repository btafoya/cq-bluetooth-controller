# Troubleshooting Guide

Common issues and solutions for the CQ-20B Bluetooth Foot Controller.

## Quick Diagnostics

Run these commands to diagnose issues:

```bash
# Check service status
sudo systemctl status cq-footcontroller.service

# View recent logs
sudo journalctl -u cq-footcontroller -n 50

# Test MIDI input
./test_midi.py

# Test mixer connection
./test_connection.py

# Check Bluetooth devices
bluetoothctl devices

# Check network
ping 192.168.1.100  # Your mixer IP
```

---

## Bluetooth Issues

### M-Vave Won't Pair

**Symptoms:**
- M-Vave not appearing in Bluetooth scan
- Pairing fails repeatedly
- Blue LED not flashing

**Solutions:**

1. **Reset M-Vave Bluetooth:**
   - Power off M-Vave
   - Hold Bluetooth button while powering on
   - Should enter pairing mode (flashing blue)

2. **Remove Old Pairing:**
   ```bash
   sudo bluetoothctl
   remove [MAC_ADDRESS]  # Your M-Vave MAC
   scan on
   # Wait for device to appear
   pair [MAC_ADDRESS]
   trust [MAC_ADDRESS]
   connect [MAC_ADDRESS]
   ```

3. **Check Bluetooth Service:**
   ```bash
   sudo systemctl status bluetooth
   # Should show "active (running)"

   # If not running:
   sudo systemctl start bluetooth
   sudo systemctl enable bluetooth
   ```

4. **Check Range:**
   - M-Vave must be within 10 meters of Raspberry Pi
   - Remove obstacles between devices

### M-Vave Connects But No MIDI

**Symptoms:**
- Bluetooth paired successfully
- No MIDI port appears in `./test_midi.py`

**Solutions:**

1. **Check MIDI Service:**
   ```bash
   # List MIDI ports
   python3 -c "import mido; print(mido.get_input_names())"
   ```

2. **Reinstall MIDI Libraries:**
   ```bash
   pip3 install --user --force-reinstall python-rtmidi mido
   ```

3. **Reboot Both Devices:**
   ```bash
   # Power off M-Vave
   sudo reboot  # Raspberry Pi
   # Power on M-Vave
   ```

### Connection Drops Randomly

**Symptoms:**
- Foot controller works then stops
- Need to reconnect frequently

**Solutions:**

1. **Check Battery:**
   - M-Vave battery may be low
   - Charge for 2+ hours

2. **Reduce Interference:**
   - Move WiFi router away from Pi
   - Avoid 2.4GHz interference sources
   - Use 5GHz WiFi if possible

3. **Increase Trust:**
   ```bash
   sudo bluetoothctl
   trust [MAC_ADDRESS]
   ```

---

## Network Issues

### Can't Connect to Mixer

**Symptoms:**
- "Connection failed" in logs
- `./test_connection.py` fails
- Cannot ping mixer IP

**Solutions:**

1. **Verify Mixer IP:**
   - Check in CQ MixPad app: Settings → Network
   - Try mixer's web interface in browser
   - Check router's DHCP client list

2. **Check Network Cable:**
   - Try different Ethernet cable
   - Check link lights on both ends
   - Test with different port on switch/router

3. **Check Mixer Network Settings:**
   - Mixer must be on same subnet as Pi
   - Example: Pi=192.168.1.50, Mixer=192.168.1.100 ✓
   - Example: Pi=192.168.1.50, Mixer=10.0.0.100 ✗

4. **Test Pi Network:**
   ```bash
   # Check Pi IP
   ip addr show

   # Check default gateway
   ip route show

   # Test internet
   ping google.com
   ```

5. **Static IP for Mixer:**
   - In CQ MixPad, set static IP for mixer
   - Update config.yaml with new IP
   - Restart service

### Connection Drops During Performance

**Symptoms:**
- Works initially then loses connection
- "Connection lost! Reconnecting..." in logs

**Solutions:**

1. **Check Network Stability:**
   ```bash
   # Continuous ping test
   ping -i 0.3 192.168.1.100
   # Should have 0% packet loss
   ```

2. **Reduce Network Load:**
   - Disconnect unnecessary devices from network
   - Use dedicated switch for audio network
   - Prioritize audio traffic on router (QoS)

3. **Check Mixer Firmware:**
   - Update CQ-20B to latest firmware
   - Check Allen & Heath website for updates

4. **Increase Reconnect Speed:**
   Edit config.yaml:
   ```yaml
   network:
     reconnect_delay: 1.0  # Faster reconnect
     connection_timeout: 3.0  # Shorter timeout
   ```

---

## Button Issues

### Buttons Not Responding

**Symptoms:**
- Press buttons but nothing happens
- No log messages when pressing buttons

**Solutions:**

1. **Check MIDI Messages:**
   ```bash
   ./test_midi.py
   # Press each button
   # Note CC numbers
   ```

2. **Verify CC Numbers in Config:**
   ```yaml
   button_mapping:
     button_a:
       cc_number: 20  # Must match test_midi.py output
   ```

3. **Check Service Logs:**
   ```bash
   sudo journalctl -u cq-footcontroller -f
   # Press button
   # Should see: "Unmapped CC: XX" if wrong number
   ```

4. **Restart Service:**
   ```bash
   sudo systemctl restart cq-footcontroller.service
   ```

### Wrong Button Actions

**Symptoms:**
- Button A does Button B's action
- Button functions swapped

**Solutions:**

1. **Re-map Buttons:**
   ```bash
   ./test_midi.py
   # Press each button carefully
   # Note which CC is which button
   # Update config.yaml
   ```

2. **Verify M-Vave Configuration:**
   - M-Vave can be reprogrammed via CubeSuite app
   - Reset to factory defaults if changed
   - Re-test with `./test_midi.py`

### Break Mode Not Working

**Symptoms:**
- Button D pressed but mute groups don't change
- Break music doesn't play

**Solutions:**

1. **Verify Mute Group Assignment:**
   - Open CQ MixPad
   - Check Mute Group 3 contains ST2 In
   - Check Mute Groups 1,2,4 contain correct channels

2. **Check NRPN Addresses:**
   - Verify mute group NRPN addresses in config.yaml
   - Compare with CQ MIDI Protocol PDF
   - All 4 mute group addresses must be correct

3. **Test Break Music Source:**
   - Verify ST2 In source is connected
   - Check ST2 In is not muted in mixer
   - Test ST2 In plays manually in CQ MixPad

4. **Enable Debug Logging:**
   ```yaml
   logging:
     level: "DEBUG"  # In config.yaml
   ```
   Restart and check logs for NRPN messages

### Recording Button Not Working

**Symptoms:**
- Button A pressed but recording doesn't start

**Solutions:**

1. **Check USB/SD Card:**
   - Insert USB drive or SD card in CQ-20B
   - Verify sufficient free space
   - Format if necessary (FAT32)

2. **Verify Recording NRPN:**
   - Check recording NRPN address in config.yaml
   - Compare with CQ MIDI Protocol PDF

3. **Test Recording Manually:**
   - Start recording in CQ MixPad
   - Verify it works without foot controller
   - If not, check mixer settings

---

## Service Issues

### Service Won't Start

**Symptoms:**
- `sudo systemctl start cq-footcontroller.service` fails
- Service shows "failed" status

**Solutions:**

1. **Check Logs:**
   ```bash
   sudo journalctl -u cq-footcontroller -n 50
   ```

2. **Common Errors:**

   **"Config file not found":**
   ```bash
   # Check service file path
   sudo nano /etc/systemd/system/cq-footcontroller.service
   # Verify WorkingDirectory and ExecStart paths
   ```

   **"ModuleNotFoundError: No module named 'mido'":**
   ```bash
   # Install for system Python
   sudo pip3 install mido python-rtmidi pyyaml
   ```

   **"Permission denied":**
   ```bash
   # Fix ownership
   sudo chown -R pi:pi ~/cq-controller
   chmod +x ~/cq-controller/cq_foot_controller.py
   ```

3. **Test Manual Start:**
   ```bash
   cd ~/cq-controller
   python3 cq_foot_controller.py
   # If this works but service doesn't, check service file
   ```

### Service Restarts Constantly

**Symptoms:**
- Service keeps restarting
- Logs show repeated connection attempts

**Solutions:**

1. **Check Restart Policy:**
   ```bash
   sudo nano /etc/systemd/system/cq-footcontroller.service
   # Change: RestartSec=10  # Wait longer between restarts
   ```

2. **Fix Root Cause:**
   - Check why service is crashing
   - Review logs for errors
   - Fix configuration issues

3. **Disable Auto-Restart (temporarily):**
   ```bash
   sudo nano /etc/systemd/system/cq-footcontroller.service
   # Change: Restart=on-failure  # Only restart on crash
   sudo systemctl daemon-reload
   sudo systemctl restart cq-footcontroller
   ```

---

## Performance Issues

### High Latency

**Symptoms:**
- Delay between button press and action
- >500ms response time

**Solutions:**

1. **Check Network Latency:**
   ```bash
   ping -c 100 192.168.1.100
   # Check avg/max times
   ```

2. **Reduce Delay Settings:**
   ```yaml
   advanced:
     nrpn_send_delay: 0.005  # Reduce from 0.01
   ```

3. **Use Wired Ethernet:**
   - WiFi adds latency
   - Use Ethernet cable for Pi

4. **Check CPU Usage:**
   ```bash
   top
   # Look for high CPU processes
   ```

### System Freezes

**Symptoms:**
- Raspberry Pi becomes unresponsive
- Service stops responding

**Solutions:**

1. **Check Power Supply:**
   - Use official Pi power supply (5V 2.5A minimum)
   - Check for "under-voltage" warnings in logs

2. **Check SD Card:**
   - SD card may be failing
   - Try different SD card
   - Check for filesystem errors:
     ```bash
     sudo fsck /dev/mmcblk0p2
     ```

3. **Reduce Load:**
   - Disable unnecessary services
   - Don't run GUI (use Lite OS)

---

## Configuration Issues

### NRPN Values Wrong

**Symptoms:**
- Buttons send MIDI but wrong controls change
- Random mixer parameters affected

**Solutions:**

1. **Get Correct NRPN Values:**
   ```bash
   wget https://www.allen-heath.com/content/uploads/2024/06/CQ_MIDI_Protocol_V1_2_0_iss2.pdf
   # Open and find exact MSB/LSB values
   ```

2. **Verify Hex Format:**
   ```yaml
   # Correct:
   msb: 0x01
   lsb: 0x2F

   # Wrong:
   msb: 01  # Missing 0x
   lsb: 2F  # Missing 0x
   ```

3. **Test One Control at a Time:**
   - Comment out all but one button
   - Test that single function
   - Add others one by one

### Config Changes Not Applied

**Symptoms:**
- Edit config.yaml but no change in behavior

**Solutions:**

1. **Restart Service:**
   ```bash
   sudo systemctl restart cq-footcontroller.service
   ```

2. **Check YAML Syntax:**
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
   # Should show no errors
   ```

3. **Verify Config Path:**
   ```bash
   # Check service is using correct config
   sudo systemctl cat cq-footcontroller.service
   # Look at ExecStart line
   ```

---

## Emergency Procedures

### System Completely Not Working

**Quick Recovery:**

1. **Use CQ MixPad as backup**
   - Always have tablet ready
   - Can control everything from app

2. **Restart Everything:**
   ```bash
   # Raspberry Pi
   sudo reboot

   # Power cycle M-Vave

   # Power cycle mixer (if safe to do so)
   ```

3. **Run Manual Mode:**
   ```bash
   cd ~/cq-controller
   python3 cq_foot_controller.py
   # Bypass service, direct control
   ```

### During Performance

**If controller fails during gig:**

1. Don't panic - use CQ MixPad
2. Note what failed for later debugging
3. Keep performing with app backup
4. Debug after the show

---

## Getting Help

### Gather Debug Information

```bash
# Create debug report
cat > debug_report.txt << EOF
=== System Info ===
$(uname -a)
$(python3 --version)

=== Service Status ===
$(sudo systemctl status cq-footcontroller.service)

=== Recent Logs ===
$(sudo journalctl -u cq-footcontroller -n 50)

=== Network ===
$(ip addr show)
$(ping -c 5 192.168.1.100)

=== Bluetooth ===
$(bluetoothctl devices)

=== MIDI Ports ===
$(python3 -c "import mido; print(mido.get_input_names())")

=== Config ===
$(cat config.yaml)
EOF

cat debug_report.txt
```

### Contact Support

- Project Issues: <your-repo-url>/issues
- Include debug_report.txt
- Describe expected vs actual behavior
- Mention when problem started
