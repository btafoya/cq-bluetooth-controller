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
import ipaddress
from pathlib import Path
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# MIXER AUTO-DISCOVERY
# ============================================
class MixerDiscovery:
    """Automatic network discovery for CQ-20B mixer"""

    def __init__(self, config):
        self.config = config
        self.port = config.get('network', 'mixer_port', default=51325)

        # Auto-discovery settings
        auto_config = config.get('network', 'auto_discovery')
        if auto_config:
            self.enabled = auto_config.get('enabled', True)
            self.scan_interval = auto_config.get('scan_interval', 300)  # 5 minutes
            self.check_interval = auto_config.get('check_interval', 30)  # 30 seconds
            self.subnet = auto_config.get('subnet', 'auto')
            self.timeout = auto_config.get('timeout', 1.0)
        else:
            # Defaults if auto_discovery not in config
            self.enabled = True
            self.scan_interval = 300
            self.check_interval = 30
            self.subnet = 'auto'
            self.timeout = 1.0

        self.last_ip = None
        self.discovery_thread = None
        self.stop_discovery = threading.Event()

    def get_local_subnet(self):
        """Auto-detect local subnet"""
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # Assume /24 subnet
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            return str(network)
        except Exception as e:
            logging.warning(f"Could not auto-detect subnet: {e}. Using 192.168.1.0/24")
            return "192.168.1.0/24"

    def test_port(self, ip, timeout=1.0):
        """Test if port is open on given IP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((str(ip), self.port))
            sock.close()
            return result == 0
        except:
            return False

    def verify_mixer(self, ip):
        """Verify this is actually a CQ-20B by testing MIDI keepalive"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((str(ip), self.port))

            # Send MIDI keepalive byte
            sock.send(bytes([0xFE]))

            # If connection stays open, it's likely a MIDI device
            # (Non-MIDI services would typically close or respond differently)
            time.sleep(0.5)
            sock.close()
            return True
        except:
            return False

    def scan_network(self):
        """Scan network for mixer on port 51325"""
        subnet = self.subnet if self.subnet != 'auto' else self.get_local_subnet()
        logging.info(f"🔍 Scanning network {subnet} for CQ-20B mixer on port {self.port}...")

        try:
            network = ipaddress.IPv4Network(subnet, strict=False)
            candidates = []

            # Parallel port scanning for speed
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = {
                    executor.submit(self.test_port, str(ip), self.timeout): str(ip)
                    for ip in network.hosts()
                }

                for future in as_completed(futures):
                    ip = futures[future]
                    if future.result():
                        candidates.append(ip)
                        logging.info(f"  Found port {self.port} open on {ip}")

            # Verify candidates are actually MIDI devices
            for ip in candidates:
                if self.verify_mixer(ip):
                    logging.info(f"✓ Found CQ-20B mixer at {ip}")
                    return ip
                else:
                    logging.debug(f"  {ip}:{self.port} open but not responding to MIDI")

            logging.warning(f"⚠ No CQ-20B mixer found on network {subnet}")
            return None

        except Exception as e:
            logging.error(f"Network scan error: {e}")
            return None

    def find_mixer(self):
        """Find mixer: check last IP first, then full scan"""
        # Fast path: try last known IP
        if self.last_ip:
            logging.info(f"🔍 Checking last known IP: {self.last_ip}")
            if self.test_port(self.last_ip, timeout=2.0):
                if self.verify_mixer(self.last_ip):
                    logging.info(f"✓ Mixer still at {self.last_ip}")
                    return self.last_ip
                else:
                    logging.warning(f"⚠ Port open at {self.last_ip} but not responding to MIDI")

        # Full network scan
        mixer_ip = self.scan_network()
        if mixer_ip:
            self.last_ip = mixer_ip
        return mixer_ip

    def monitor_loop(self, connection_callback):
        """Background monitoring loop with periodic scanning"""
        next_full_scan = time.time() + self.scan_interval

        while not self.stop_discovery.is_set():
            try:
                # Quick check of last known IP
                if self.last_ip:
                    if not self.test_port(self.last_ip, timeout=2.0):
                        logging.warning(f"⚠ Lost connection to mixer at {self.last_ip}")
                        self.last_ip = None
                        # Trigger immediate full scan
                        next_full_scan = time.time()

                # Periodic full scan
                if time.time() >= next_full_scan:
                    mixer_ip = self.scan_network()
                    if mixer_ip and mixer_ip != self.last_ip:
                        logging.info(f"🔄 Mixer IP changed: {self.last_ip} → {mixer_ip}")
                        self.last_ip = mixer_ip
                        # Notify connection to reconnect
                        if connection_callback:
                            connection_callback(mixer_ip)
                    next_full_scan = time.time() + self.scan_interval

                # Sleep until next check
                self.stop_discovery.wait(self.check_interval)

            except Exception as e:
                logging.error(f"Discovery monitor error: {e}")
                self.stop_discovery.wait(self.check_interval)

    def start_monitoring(self, connection_callback=None):
        """Start background discovery monitoring"""
        if self.discovery_thread and self.discovery_thread.is_alive():
            return

        self.stop_discovery.clear()
        self.discovery_thread = threading.Thread(
            target=self.monitor_loop,
            args=(connection_callback,),
            daemon=True
        )
        self.discovery_thread.start()
        logging.info("✓ Discovery monitoring started")

    def stop_monitoring(self):
        """Stop background discovery monitoring"""
        self.stop_discovery.set()
        if self.discovery_thread:
            self.discovery_thread.join(timeout=5.0)
        logging.info("✓ Discovery monitoring stopped")

# ============================================
# TCP CONNECTION TO CQ-20B
# ============================================
class CQConnection:
    """Manages TCP connection to CQ-20B mixer"""

    def __init__(self, config, discovery=None):
        self.config = config
        self.discovery = discovery
        self.ip = config.get('network', 'mixer_ip')  # Optional with auto-discovery
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

    def on_discovery_update(self, new_ip):
        """Callback when discovery finds mixer at new IP"""
        if new_ip != self.ip:
            logging.info(f"🔄 Discovery found mixer at new IP: {new_ip}")
            self.ip = new_ip
            # Trigger reconnect if currently connected to old IP
            if self.connected:
                self.reconnect()

    def connect(self):
        """Connect to CQ-20B with auto-retry and auto-discovery"""
        while not self.connected:
            try:
                # Use discovery if IP not set
                if not self.ip and self.discovery:
                    logging.info("🔍 No mixer IP configured, using auto-discovery...")
                    self.ip = self.discovery.find_mixer()
                    if not self.ip:
                        logging.warning("⚠ Auto-discovery found no mixer. Retrying in 10s...")
                        time.sleep(10)
                        continue

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

                # Start discovery monitoring if enabled
                if self.discovery and not self.discovery.discovery_thread:
                    self.discovery.start_monitoring(self.on_discovery_update)

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

    # Setup auto-discovery if enabled
    mixer_ip = config.get('network', 'mixer_ip')
    auto_discovery_config = config.get('network', 'auto_discovery')
    use_discovery = (auto_discovery_config and auto_discovery_config.get('enabled', True)) or not mixer_ip

    if use_discovery:
        logging.info("Auto-discovery: ENABLED")
        discovery = MixerDiscovery(config)
    else:
        logging.info(f"Mixer: {mixer_ip}:{config.get('network', 'mixer_port')}")
        discovery = None

    logging.info("=" * 60)

    # Connect to CQ-20B
    cq = CQConnection(config, discovery=discovery)
    cq.connect()

    # Setup button handlers
    button_handler = ButtonHandler(config, cq)

    # Start MIDI processing
    midi_processor = MIDIProcessor(config, button_handler)
    midi_processor.process()

if __name__ == "__main__":
    main()
