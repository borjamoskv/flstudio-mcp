#!/usr/bin/env python3
"""
FL Studio Native Score (.fsc) Binary Builder — C5-REAL Sovereign Engine
══════════════════════════════════════════════════════════════════════════
Reverse-engineers and constructs binary-perfect FL Studio Piano Roll Score
(.fsc) files compliant with FL Studio 2024/2025 event specification.

Binary Specification:
- Header: 'FLhd' + length (6 bytes: uint16 format=16, uint16 channels=5, uint16 ppq=96)
- Data Chunk: 'FLdt' + uint32 length + stream of events:
    - Event 0xC7: VarLen string ("3.0.0\0")
    - Event 0x41: Word 0 (score attributes)
    - Event 0xE0: VarLen note array (20 bytes per note):
        - uint32: position (ticks, PPQ=96)
        - uint32: rack_channel_flags (0x00400000 standard)
        - uint32: duration (ticks)
        - uint32: pitch (MIDI note 0..127)
        - uint8: pan (0..127, 64=center)
        - uint8: velocity (0..127, 100=default)
        - uint8: release (0..127, 128=default)
        - uint8: modulation (0..127, 80=default)
"""

import struct
from pathlib import Path
from typing import List, Dict, Any, Optional

PPQ_DEFAULT = 96  # Standard FL Studio Score PPQ


def encode_varlen(val: int) -> bytes:
    """Encodes an integer into FL Studio / MIDI variable-length quantity."""
    buf = bytearray()
    while True:
        b = val & 0x7F
        val >>= 7
        if val:
            buf.append(b | 0x80)
        else:
            buf.append(b)
            break
    return bytes(buf)


class FLScoreBuilder:
    """Constructs FL Studio Piano Roll Score (.fsc) files."""

    def __init__(self, ppq: int = PPQ_DEFAULT, channels: int = 5):
        self.ppq = ppq
        self.channels = channels
        self.notes: List[Dict[str, int]] = []

    def add_note(
        self,
        pos_ticks: int,
        pitch: int,
        duration_ticks: int = 24,
        velocity: int = 100,
        pan: int = 64,
        release: int = 128,
        modulation: int = 80,
        flags: int = 0x00400000
    ) -> "FLScoreBuilder":
        """Adds a note event to the score."""
        self.notes.append({
            "pos": int(pos_ticks),
            "pitch": max(0, min(127, int(pitch))),
            "duration": max(1, int(duration_ticks)),
            "vel": max(0, min(127, int(velocity))),
            "pan": max(0, min(127, int(pan))),
            "release": max(0, min(127, int(release))),
            "mod": max(0, min(127, int(modulation))),
            "flags": int(flags)
        })
        return self

    def add_flamenco_compas(self, root_pitch: int = 50, bars: int = 2) -> "FLScoreBuilder":
        """
        Adds a Flamenco 12-beat Compás (Bulérías / Soleá accents: 3, 6, 8, 10, 12).
        Ticks per beat = 96 (quarter note) or 48 (eighth note compás).
        """
        accents = {3, 6, 8, 10, 12}
        step_ticks = 48  # Eighth note
        current_tick = 0
        for _ in range(bars):
            for beat in range(1, 13):
                is_accent = beat in accents
                vel = 118 if is_accent else 82
                dur = 36 if is_accent else 24
                # Flamenco Phrygian chord arpeggio
                pitch_offset = 0 if not is_accent else (1 if beat in (3, 8) else 3)
                self.add_note(
                    pos_ticks=current_tick,
                    pitch=root_pitch + pitch_offset,
                    duration_ticks=dur,
                    velocity=vel,
                    pan=60 if not is_accent else 68
                )
                current_tick += step_ticks
        return self

    def build_binary(self) -> bytes:
        """Serializes the note events into .fsc binary format."""
        # Sort notes by position
        sorted_notes = sorted(self.notes, key=lambda n: n["pos"])

        # Pack note array (20 bytes per note)
        notes_bytes = bytearray()
        for n in sorted_notes:
            notes_bytes += struct.pack(
                "<IIIIBBBB",
                n["pos"],
                n["flags"],
                n["duration"],
                n["pitch"],
                n["pan"],
                n["vel"],
                n["release"],
                n["mod"]
            )

        # Build FLdt events
        dt_events = bytearray()
        # Event 0xC7: Version "3.0.0\0"
        version_str = b"3.0.0\x00"
        dt_events.append(0xC7)
        dt_events += encode_varlen(len(version_str))
        dt_events += version_str

        # Event 0x41: Word 0
        dt_events.append(0x41)
        dt_events += struct.pack("<H", 0)

        # Event 0xE0: Note block
        dt_events.append(0xE0)
        dt_events += encode_varlen(len(notes_bytes))
        dt_events += notes_bytes

        # Header: FLhd
        flhd_header = b"FLhd" + struct.pack("<IHHH", 6, 16, self.channels, self.ppq)
        # Data: FLdt
        fldt_chunk = b"FLdt" + struct.pack("<I", len(dt_events)) + dt_events

        return flhd_header + fldt_chunk

    def export_fsc(self, output_path: str) -> Dict[str, Any]:
        """Saves binary .fsc to disk."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw_bytes = self.build_binary()
        path.write_bytes(raw_bytes)
        return {
            "status": "SUCCESS",
            "file": str(path.resolve()),
            "total_notes": len(self.notes),
            "size_bytes": len(raw_bytes),
            "ppq": self.ppq,
            "format": "FL Studio Piano Roll Score (.fsc v3.0.0)"
        }


def generate_dark_cyber_flamenco_fsc(output_path: str, root_pitch: int = 50) -> Dict[str, Any]:
    """Generates a Dark Cyber-Flamenco compás score in native .fsc format."""
    builder = FLScoreBuilder(ppq=96)
    builder.add_flamenco_compas(root_pitch=root_pitch, bars=4)
    return builder.export_fsc(output_path)


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_score.fsc"
    res = generate_dark_cyber_flamenco_fsc(out)
    print(res)
