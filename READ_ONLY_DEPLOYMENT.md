# Read-Only Filesystem Deployment Guide

This guide covers installing and maintaining the CQ-20B Foot Controller on a Raspberry Pi with read-only overlay filesystem (overlayFS) enabled.

## Why Read-Only?

Read-only filesystem with overlayFS protects the SD card from corruption when the Pi is powered off abruptly (e.g., when the mixer is turned off). Perfect for live performance environments where the Pi runs headless.

## Current Setup Verification

Your Pi at **192.168.25.173** has overlayFS **ENABLED**:
```
overlayroot=tmpfs
Root: overlay (lowerdir=/media/root-ro, upperdir=/media/root-rw/overlay)
```

## How OverlayFS Works

- **Lower Layer** (`/media/root-ro`): Read-only SD card filesystem
- **Upper Layer** (`/media/root-rw`): RAM-based overlay (tmpfs) for changes
- **Merged View** (`/`): You see the SD card, but all changes go to RAM
- **On Reboot**: Upper layer (RAM) is wiped, system returns to clean SD card state

## Installation Process

### Step 1: Disable Overlay (Make SD Card Writable)

```bash
ssh btafoya@192.168.25.173

# Disable overlay filesystem
sudo raspi-config nonint do_overlayfs 1

# Reboot to apply
sudo reboot
```

After reboot, root filesystem will be writable directly to SD card.

### Step 2: Transfer Project

From your local machine:
```bash
scp -r /home/btafoya/projects/cq-bluetooth-controller btafoya@192.168.25.173:~/
```

### Step 3: Install Project

```bash
ssh btafoya@192.168.25.173

cd ~/cq-bluetooth-controller

# Run installation
./install.sh

# This installs:
# - System packages (python3, bluez, etc.)
# - Python libraries (mido, python-rtmidi, pyyaml)
# - Systemd service
# - Makes scripts executable
```

### Step 4: Configure

```bash
# Edit configuration
nano ~/cq-bluetooth-controller/config.yaml
```

**Update these critical settings:**
- `mixer_ip`: Your CQ-20B IP address
- `button_mapping`: CC numbers from your M-Vave (use `./test_midi.py`)

**Leave logging as console-only:**
```yaml
logging:
  file: ""  # Empty = journalctl only (works with read-only)
```

### Step 5: Pair M-Vave

```bash
./pair_mvave.sh
```

### Step 6: Test Thoroughly

```bash
# Test MIDI
./test_midi.py

# Test mixer connection
./test_connection.py

# Test full controller
python3 cq_foot_controller.py
# Press all buttons, verify functionality
```

### Step 7: Enable Service

```bash
sudo systemctl enable cq-footcontroller.service
sudo systemctl start cq-footcontroller.service
sudo systemctl status cq-footcontroller.service
```

### Step 8: Re-Enable Overlay (Make Read-Only)

**CRITICAL: Only do this after verifying everything works!**

```bash
# Enable overlay filesystem
sudo raspi-config nonint do_overlayfs 0

# Reboot to apply
sudo reboot
```

### Step 9: Verify Read-Only Operation

After reboot:
```bash
ssh btafoya@192.168.25.173

# Verify overlay is active
cat /proc/cmdline | grep overlayroot
# Should show: overlayroot=tmpfs

# Verify service auto-started
systemctl status cq-footcontroller.service
# Should show: Active: active (running)

# Verify logs
sudo journalctl -u cq-footcontroller -n 50

# Test buttons
# Service should respond to foot controller presses
```

## Maintaining Read-Only System

### Making Configuration Changes

When you need to update `config.yaml` or make other changes:

```bash
# 1. Disable overlay
sudo raspi-config nonint do_overlayfs 1
sudo reboot

# 2. Make changes
nano ~/cq-bluetooth-controller/config.yaml
sudo systemctl restart cq-footcontroller

# 3. Test changes
sudo systemctl status cq-footcontroller
sudo journalctl -u cq-footcontroller -f

# 4. Re-enable overlay
sudo raspi-config nonint do_overlayfs 0
sudo reboot
```

### Updating Project Code

```bash
# 1. Disable overlay
sudo raspi-config nonint do_overlayfs 1
sudo reboot

# 2. Transfer updated files
scp -r /home/btafoya/projects/cq-bluetooth-controller/* btafoya@192.168.25.173:~/cq-bluetooth-controller/

# 3. Restart service
sudo systemctl restart cq-footcontroller

# 4. Test
sudo systemctl status cq-footcontroller

# 5. Re-enable overlay
sudo raspi-config nonint do_overlayfs 0
sudo reboot
```

### Updating System Packages

```bash
# 1. Disable overlay
sudo raspi-config nonint do_overlayfs 1
sudo reboot

# 2. Update
sudo apt update
sudo apt upgrade -y

# 3. Re-enable overlay
sudo raspi-config nonint do_overlayfs 0
sudo reboot
```

## Alternative: Config on /boot Partition

For easier config changes without disabling overlay, you can move `config.yaml` to `/boot`:

**⚠️ This requires code modification and /boot must be remounted read-write**

### Option A: Config Symlink (Recommended)

```bash
# With overlay DISABLED:

# Move config to /boot
sudo mv ~/cq-bluetooth-controller/config.yaml /boot/cq-config.yaml

# Create symlink
ln -s /boot/cq-config.yaml ~/cq-bluetooth-controller/config.yaml

# Update service to remount /boot as RW before starting
sudo nano /etc/systemd/system/cq-footcontroller.service
```

Add before `ExecStart`:
```ini
ExecStartPre=/bin/mount -o remount,rw /boot
ExecStopPost=/bin/mount -o remount,ro /boot
```

Then to edit config (even with overlay enabled):
```bash
sudo mount -o remount,rw /boot
sudo nano /boot/cq-config.yaml
sudo mount -o remount,ro /boot
sudo systemctl restart cq-footcontroller
```

## Compatibility Summary

### ✅ Works Great
- **Systemd service**: Auto-starts on boot
- **Logging**: journalctl handles logs in RAM or persistent journal
- **MIDI input**: No persistent state needed
- **TCP connection**: Auto-reconnect handles network changes
- **Button state**: All state is in-memory

### ⚠️ Requires Awareness
- **Config changes**: Must disable overlay OR use /boot method
- **Code updates**: Must disable overlay before deploying
- **Package updates**: Must disable overlay before apt upgrade
- **Python dependencies**: Installed to home dir, works with overlay

### ❌ Won't Work
- **File logging** (`logging.file: /var/log/...`): File will exist but be lost on reboot
  - **Solution**: Use journalctl (already configured by default)
- **Writing state to files**: Any persistent state files will be lost
  - **Solution**: Project doesn't use persistent state files

## Troubleshooting

### Service not starting after reboot

```bash
# Check if overlay disabled installation
cat /proc/cmdline | grep overlayroot

# If overlayroot=tmpfs is present, installation was done with overlay enabled
# Solution: Disable overlay, reinstall, re-enable overlay
```

### Config changes not persisting

```bash
# Check if overlay is enabled
mount | grep " / "

# If you see "overlay", changes are in RAM only
# Solution: Disable overlay before making changes, OR use /boot method
```

### Python packages missing after reboot

```bash
# Check install location
pip3 show mido | grep Location

# If installed to /usr/local/lib, overlay was enabled during install
# Solution: Disable overlay, reinstall with ./install.sh, re-enable
```

### Can't edit config.yaml

```bash
# Check overlay status
mount | grep " / "

# Disable overlay temporarily
sudo raspi-config nonint do_overlayfs 1
sudo reboot
```

## Emergency Procedures

### System won't boot after enabling overlay

1. Remove SD card from Pi
2. Insert into computer with card reader
3. Mount boot partition
4. Edit `cmdline.txt`
5. Remove `overlayroot=tmpfs` from the line
6. Save and eject
7. Insert back into Pi and boot

### Need to make quick config change during gig

**Without /boot method (requires reboot):**
```bash
# This will lose changes on reboot, but works for current session
nano ~/cq-bluetooth-controller/config.yaml
sudo systemctl restart cq-footcontroller
```

**With /boot method (no reboot):**
```bash
sudo mount -o remount,rw /boot
sudo nano /boot/cq-config.yaml
sudo mount -o remount,ro /boot
sudo systemctl restart cq-footcontroller
```

## Best Practices

1. **Test fully before enabling overlay**: Do at least 2-3 complete reboot cycles with overlay disabled
2. **Document your config**: Keep a copy of `config.yaml` in your project repository
3. **Version control everything**: Git commit before each deployment to Pi
4. **Backup SD card**: After successful setup, create SD card image backup
5. **Monitor first gig**: Watch journalctl logs during first live use
6. **Keep CQ MixPad as backup**: Always have manual mixer control available

## Quick Reference

### Check Overlay Status
```bash
cat /proc/cmdline | grep overlayroot
mount | grep " / "
```

### Disable Overlay
```bash
sudo raspi-config nonint do_overlayfs 1
sudo reboot
```

### Enable Overlay
```bash
sudo raspi-config nonint do_overlayfs 0
sudo reboot
```

### View Logs
```bash
sudo journalctl -u cq-footcontroller -f
```

### Restart Service
```bash
sudo systemctl restart cq-footcontroller
```

---

**Remember**: Read-only mode is for protection, not convenience. Plan your changes, disable overlay, make changes thoroughly, test, then re-enable.
