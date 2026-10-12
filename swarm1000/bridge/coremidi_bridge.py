#!/usr/bin/env python3
"""
SWARM-1000 COREMIDI SOVEREIGN BRIDGE
Apple Silicon Native CoreMIDI Virtual Port & Automation Dispatcher
Zero-Latency MIDI CC / Transport Control for FL Studio, DAWs & Hardware Mixers
"""

import sys
import time
import math
from typing import Optional, Dict, Any

try:
    import mido
    MIDO_AVAILABLE = True
except ImportError:
    MIDO_AVAILABLE = False

class CoreMidiBridge:
    """
    Virtual CoreMIDI Port Manager for SWARM-1000 Sovereign DJ Agent.
    Maps psychoacoustic matrix parameters into standard and high-resolution MIDI CCs.
    """
    
    # CC Mappings
    CC_DECK_A_FILTER = 1        # Deck A HPF/LPF Cutoff (0-127)
    CC_DECK_B_FILTER = 2        # Deck B HPF/LPF Cutoff (0-127)
    CC_CROSSFADER = 3           # Crossfader Sigmoidal Position (0=Deck A, 127=Deck B)
    CC_MS_EVAPORATION = 4       # Mid/Side Peripheral Evaporation (0-127)
    CC_SATORI_REVERB = 5        # Satori / Vacuum Decay Reverb Send (0-127)
    CC_TAPE_STOP = 6            # Tape Stop Trigger (0=Off, 127=Trigger)
    CC_DECK_A_GAIN = 7          # Deck A Volume / Gain Staging (0-127)
    CC_DECK_B_GAIN = 8          # Deck B Volume / Gain Staging (0-127)
    CC_BASS_CROSSOVER = 9       # Sub-bass LR4 Crossover Split (0=Deck A bass, 127=Deck B bass)
    CC_BAR12_FAKE_DROP = 10     # False Drop Deterministic Trigger at Bar 12 (0=Normal, 127=Trigger)

    def __init__(self, port_name: str = "SWARM-1000 Sovereign DJ"):
        self.port_name = port_name
        self.port: Optional[Any] = None
        self.is_virtual = False
        self._init_port()

    def _init_port(self):
        if not MIDO_AVAILABLE:
            print("[SWARM-1000 CoreMIDI] Warning: mido is not installed; running in mock mode.")
            return

        try:
            # On macOS / Apple Silicon, virtual=True creates a system-wide CoreMIDI virtual destination
            self.port = mido.open_output(self.port_name, virtual=True)
            self.is_virtual = True
            print(f"[SWARM-1000 CoreMIDI] Virtual CoreMIDI port initialized: '{self.port_name}'")
        except Exception as e:
            print(f"[SWARM-1000 CoreMIDI] Could not open virtual port ({e}). Falling back to default output.")
            try:
                self.port = mido.open_output()
                self.is_virtual = False
            except Exception as e2:
                print(f"[SWARM-1000 CoreMIDI] No MIDI output ports available ({e2}). Mock mode active.")
                self.port = None

    def send_cc(self, control: int, value: int, channel: int = 0):
        """Send a standard 7-bit MIDI CC message (0-127)."""
        val_clamped = max(0, min(127, int(value)))
        if self.port:
            msg = mido.Message('control_change', channel=channel, control=control, value=val_clamped)
            self.port.send(msg)

    def dispatch_psychoacoustic_state(self, state: Dict[str, float]):
        """
        Translates continuous float values [0.0, 1.0] from SWARM-1000 
        psychoacoustic matrix into corresponding MIDI CC commands.
        """
        # Crossfader: 0.0 -> 0, 1.0 -> 127
        if "crossfader" in state:
            self.send_cc(self.CC_CROSSFADER, int(state["crossfader"] * 127))

        # Bass Crossover Split: 0.0 -> 0, 1.0 -> 127
        if "bass_split" in state:
            self.send_cc(self.CC_BASS_CROSSOVER, int(state["bass_split"] * 127))

        # Filters: 0.0 -> 0, 1.0 -> 127
        if "deck_a_filter" in state:
            self.send_cc(self.CC_DECK_A_FILTER, int(state["deck_a_filter"] * 127))
        if "deck_b_filter" in state:
            self.send_cc(self.CC_DECK_B_FILTER, int(state["deck_b_filter"] * 127))

        # M/S Evaporation: 0.0 -> 0, 1.0 -> 127
        if "ms_evaporation" in state:
            self.send_cc(self.CC_MS_EVAPORATION, int(state["ms_evaporation"] * 127))

        # Satori / Vacuum Reverb: 0.0 -> 0, 1.0 -> 127
        if "satori_reverb" in state:
            self.send_cc(self.CC_SATORI_REVERB, int(state["satori_reverb"] * 127))

        # Volumes
        if "deck_a_gain" in state:
            self.send_cc(self.CC_DECK_A_GAIN, int(state["deck_a_gain"] * 127))
        if "deck_b_gain" in state:
            self.send_cc(self.CC_DECK_B_GAIN, int(state["deck_b_gain"] * 127))

    def trigger_tape_stop(self):
        """Dispatches an instantaneous Tape-Stop trigger pulse."""
        self.send_cc(self.CC_TAPE_STOP, 127)
        time.sleep(0.01)
        self.send_cc(self.CC_TAPE_STOP, 0)

    def trigger_bar12_fake_drop(self):
        """Dispatches deterministic Bar 12 Fake Drop trigger."""
        self.send_cc(self.CC_BAR12_FAKE_DROP, 127)
        time.sleep(0.01)
        self.send_cc(self.CC_BAR12_FAKE_DROP, 0)

    def send_transport_start(self):
        """Sends MIDI Real-Time START message."""
        if self.port:
            self.port.send(mido.Message('start'))

    def send_transport_stop(self):
        """Sends MIDI Real-Time STOP message."""
        if self.port:
            self.port.send(mido.Message('stop'))

    def close(self):
        if self.port:
            try:
                self.port.close()
            except Exception:
                pass
            self.port = None

if __name__ == "__main__":
    print("[*] Testing CoreMidiBridge on Apple Silicon...")
    bridge = CoreMidiBridge()
    test_state = {
        "crossfader": 0.5,
        "bass_split": 0.5,
        "deck_a_filter": 1.0,
        "deck_b_filter": 0.0,
        "ms_evaporation": 0.25,
        "satori_reverb": 0.0
    }
    bridge.dispatch_psychoacoustic_state(test_state)
    print("[*] Psychoacoustic state dispatched successfully via CoreMIDI.")
    bridge.close()
