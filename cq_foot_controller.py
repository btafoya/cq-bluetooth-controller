#!/usr/bin/env python3
"""
CQ-20B Bluetooth Foot Controller Bridge
Connects M-Vave Chocolate Plus foot controller to Allen & Heath CQ-20B mixer
"""

import mido
import socket
import time
import threading
import logging
import yaml
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# ============================================
# CONFIGURATION LOADER
# ============================================
class Config:
    """Load and manage configuration from YAML file"""

    def __init__(self, config_path="config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._setup_logging()

    def _load_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            logging.error(f"Config file not found: {self.config_path}")
            logging.info("Please create config.yaml file")
            sys.exit(1)

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_logging(self):
        """Configure logging based on config file"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))
        log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s')
        log_file = log_config.get('file', '')

        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(level)

        # Clear existing handlers
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            try:
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=log_config.get('max_file_size', 10485760),
                    backupCount=log_config.get('backup_count', 3)
                )
                file_handler.setFormatter(logging.Formatter(log_format))
                logger.addHandler(file_handler)
            except Exception as e:
                logging.warning(f"Could not create log file: {e}")

    def get(self, *keys, default=None):
        """Get nested config value"""
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value

# ============================================
# NRPN MESSAGE BUILDER
# ============================================
def build_nrpn(param_msb, param_lsb, value_msb, value_lsb, channel=0):
    """Build NRPN message for CQ-20B"""
    base = 0xB0 + channel
    return [
        base, 0x63, param_msb,  # NRPN MSB
        base, 0x62, param_lsb,  # NRPN LSB
        base, 0x06, value_msb,  # Data Entry MSB
        base, 0x26, value_lsb   # Data Entry LSB
    ]

# ============================================
# TCP CONNECTION TO CQ-20B
# ============================================
class CQConnection:
    """Manages TCP connection to CQ-20B mixer"""

    def __init__(self, config):
        self.config = config
        self.ip = config.get('network', 'mixer_ip')
        self.port = config.get('network', 'mixer_port')
        self.keepalive_interval = config.get('network', 'keepalive_interval', default=0.3)
        self.connection_timeout = config.get('network', 'connection_timeout', default=5.0)
        self.reconnect_delay = config.get('network', 'reconnect_delay', default=2.0)
        self.midi_channel = config.get('advanced', 'midi_channel', default=0)
        self.send_delay = config.get('advanced', 'nrpn_send_delay', default=0.01)
        self.buffer_flush = config.get('advanced', 'buffer_flush', default=True)

        self.socket = None
        self.connected = False
        self.keepalive_thread = None
        self.reconnecting = False

    def connect(self):
        """Connect to CQ-20B with auto-retry"""
        while not self.connected:
            try:
                logging.info(f"Connecting to CQ-20B at {self.ip}:{self.port}")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.connection_timeout)
                self.socket.connect((self.ip, self.port))
                self.connected = True
                self.reconnecting = False
                logging.info("✓ Connected to CQ-20B!")

                # Start keepalive thread
                if self.keepalive_thread is None or not self.keepalive_thread.is_alive():
                    self.keepalive_thread = threading.Thread(target=self._keepalive, daemon=True)
                    self.keepalive_thread.start()

            except Exception as e:
                logging.error(f"Connection failed: {e}. Retrying in {self.reconnect_delay}s...")
                time.sleep(self.reconnect_delay)

    def _keepalive(self):
        """Send keepalive byte every 300ms"""
        while True:
            if self.connected:
                try:
                    self.socket.send(bytes([0xFE]))
                    time.sleep(self.keepalive_interval)
                except Exception as e:
                    if self.connected:  # Only log if we thought we were connected
                        logging.error(f"Keepalive failed: {e}")
                        self.connected = False
                        if not self.reconnecting:
                            threading.Thread(target=self.reconnect, daemon=True).start()
            else:
                time.sleep(0.5)  # Wait before checking again

    def reconnect(self):
        """Reconnect after connection loss"""
        if self.reconnecting:
            return  # Already reconnecting

        self.reconnecting = True
        logging.warning("⚠ Connection lost! Reconnecting...")
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connect()

    def send_nrpn(self, param_config, value):
        """Send NRPN message to mixer"""
        try:
            param_msb = param_config.get('msb', 0)
            param_lsb = param_config.get('lsb', 0)

            msg = build_nrpn(
                param_msb, param_lsb,
                value >> 7, value & 0x7F,
                self.midi_channel
            )

            self.socket.send(bytes(msg))

            if self.buffer_flush:
                self.socket.send(bytes([]))  # Flush buffer

            if self.send_delay > 0:
                time.sleep(self.send_delay)

            logging.debug(f"Sent NRPN: MSB={param_msb:02X} LSB={param_lsb:02X} Value={value}")

        except Exception as e:
            logging.error(f"Send failed: {e}")
            if self.connected:
                self.reconnect()

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

# ============================================
# CONTROLLER STATE MANAGER
# ============================================
class ControllerState:
    """Manages toggle states for all buttons"""

    def __init__(self):
        self.recording_active = False
        self.break_mode_active = False
        self.aux_level_high = False
        self.fx_mute_active = False

# ============================================
# BUTTON HANDLERS
# ============================================
class ButtonHandler:
    """Handles button press events"""

    def __init__(self, config, cq_connection):
        self.config = config
        self.cq = cq_connection
        self.state = ControllerState()

        # Get button CC numbers from config
        self.button_map = {
            config.get('button_mapping', 'button_a', 'cc_number', default=20): self.handle_button_a,
            config.get('button_mapping', 'button_b', 'cc_number', default=21): self.handle_button_b,
            config.get('button_mapping', 'button_c', 'cc_number', default=22): self.handle_button_c,
            config.get('button_mapping', 'button_d', 'cc_number', default=23): self.handle_button_d,
        }

    def process_cc(self, cc_number, value):
        """Process incoming CC message"""
        # Only respond to button presses (value > 0)
        if value > 0:
            handler = self.button_map.get(cc_number)
            if handler:
                handler()
            else:
                logging.debug(f"Unmapped CC: {cc_number}")

    def handle_button_a(self):
        """Button A: Recording Start/Stop (via Soft Key)"""
        self.state.recording_active = not self.state.recording_active

        recording_config = self.config.get('nrpn_addresses', 'recording', default={})
        soft_key_note = recording_config.get('soft_key_note', 0x30)  # Default to C3

        # Send Note On/Off to toggle recording
        self.cq.send_soft_key(soft_key_note)

        status = "STARTED" if self.state.recording_active else "STOPPED"
        logging.info(f"🔴 Recording: {status}")

    def handle_button_b(self):
        """Button B: AUX Monitor Toggle"""
        self.state.aux_level_high = not self.state.aux_level_high

        behavior = self.config.get('behaviors', 'aux_monitor', default={})
        preset_levels = behavior.get('preset_levels', default={})
        value = preset_levels.get('high' if self.state.aux_level_high else 'low', default=100)

        nrpn = self.config.get('nrpn_addresses', 'aux_send_level', default={})
        self.cq.send_nrpn(nrpn, value)

        level = "HIGH" if self.state.aux_level_high else "LOW"
        logging.info(f"🔊 AUX Monitor: {level}")

    def handle_button_c(self):
        """Button C: FX Mute Group Toggle"""
        self.state.fx_mute_active = not self.state.fx_mute_active

        behavior = self.config.get('behaviors', 'fx_mute', default={})
        mute_group_num = behavior.get('mute_group', default=1)
        value = behavior.get('values', 'on' if self.state.fx_mute_active else 'off', default=127)

        nrpn_key = f"mute_group_{mute_group_num}"
        nrpn = self.config.get('nrpn_addresses', nrpn_key, default={})
        self.cq.send_nrpn(nrpn, value)

        status = "ON" if self.state.fx_mute_active else "OFF"
        logging.info(f"🎛️ FX Mute Group {mute_group_num}: {status}")

    def handle_button_d(self):
        """Button D: BREAK MODE"""
        self.state.break_mode_active = not self.state.break_mode_active

        behavior = self.config.get('behaviors', 'break_mode', default={})

        if self.state.break_mode_active:
            # Enter break mode
            state_config = behavior.get('active_state', {})
            mute_groups = state_config.get('mute_groups', [])
            unmute_groups = state_config.get('unmute_groups', [])

            for group_num in mute_groups:
                nrpn = self.config.get('nrpn_addresses', f'mute_group_{group_num}', default={})
                self.cq.send_nrpn(nrpn, 127)  # Mute

            for group_num in unmute_groups:
                nrpn = self.config.get('nrpn_addresses', f'mute_group_{group_num}', default={})
                self.cq.send_nrpn(nrpn, 0)  # Unmute

            logging.info("☕ BREAK MODE: ACTIVE")

        else:
            # Exit break mode
            state_config = behavior.get('inactive_state', {})
            mute_groups = state_config.get('mute_groups', [])
            unmute_groups = state_config.get('unmute_groups', [])

            for group_num in mute_groups:
                nrpn = self.config.get('nrpn_addresses', f'mute_group_{group_num}', default={})
                self.cq.send_nrpn(nrpn, 127)  # Mute

            for group_num in unmute_groups:
                nrpn = self.config.get('nrpn_addresses', f'mute_group_{group_num}', default={})
                self.cq.send_nrpn(nrpn, 0)  # Unmute

            logging.info("🎵 BREAK MODE: INACTIVE")

# ============================================
# BLUETOOTH MIDI INPUT
# ============================================
class MIDIProcessor:
    """Handles Bluetooth MIDI input from M-Vave"""

    def __init__(self, config, button_handler):
        self.config = config
        self.button_handler = button_handler

    def find_midi_port(self):
        """Find M-Vave MIDI input port"""
        available_ports = mido.get_input_names()
        logging.info(f"Available MIDI ports: {available_ports}")

        # Check for manually specified port
        manual_port = self.config.get('bluetooth', 'midi_port', default='')
        if manual_port and manual_port in available_ports:
            return manual_port

        # Auto-detect based on patterns
        patterns = self.config.get('bluetooth', 'device_name_patterns', default=[])
        for port in available_ports:
            for pattern in patterns:
                if pattern.lower() in port.lower():
                    return port

        return None

    def process(self):
        """Listen for MIDI from M-Vave foot controller"""
        try:
            midi_port = self.find_midi_port()

            if not midi_port:
                logging.error("❌ M-Vave foot controller not found!")
                logging.error("Available ports: " + ", ".join(mido.get_input_names()))
                logging.error("Check Bluetooth pairing and config.yaml device_name_patterns")
                return

            logging.info(f"✓ Opening MIDI port: {midi_port}")

            with mido.open_input(midi_port) as inport:
                logging.info("🎹 Listening for footswitch presses...")

                for msg in inport:
                    if msg.type == 'control_change':
                        self.button_handler.process_cc(msg.control, msg.value)
                    elif msg.type == 'note_on':
                        # Some controllers send Note On instead of CC
                        self.button_handler.process_cc(msg.note, msg.velocity)

        except KeyboardInterrupt:
            logging.info("Shutting down...")
        except Exception as e:
            logging.error(f"MIDI processing error: {e}")
            raise

# ============================================
# MAIN
# ============================================
def main():
    """Main entry point"""

    # Load configuration
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    config = Config(config_file)

    logging.info("=" * 60)
    logging.info("CQ-20B Bluetooth Foot Controller Bridge")
    logging.info("=" * 60)
    logging.info(f"Config file: {config.config_path.absolute()}")
    logging.info(f"Mixer: {config.get('network', 'mixer_ip')}:{config.get('network', 'mixer_port')}")
    logging.info("=" * 60)

    # Connect to CQ-20B
    cq = CQConnection(config)
    cq.connect()

    # Setup button handlers
    button_handler = ButtonHandler(config, cq)

    # Start MIDI processing
    midi_processor = MIDIProcessor(config, button_handler)
    midi_processor.process()

if __name__ == "__main__":
    main()
