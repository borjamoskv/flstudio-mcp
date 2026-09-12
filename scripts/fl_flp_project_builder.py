#!/usr/bin/env python3
"""
FL Studio Native Project (.flp) Binary Compiler — C5-REAL Sovereign Engine
══════════════════════════════════════════════════════════════════════════
Compiles binary-perfect FL Studio Project (.flp) files from pure Python
without requiring FL Studio to be open or running.

Binary Specification (Image-Line FLP Standard):
- Header Chunk: 'FLhd' + uint32 len(6) + uint16 format(0) + uint16 channels + uint16 ppq(96)
- Data Chunk: 'FLdt' + uint32 len + event stream:
    - Event 0xC7: VarLen version string (e.g. "25.2.5.5055\0")
    - Event 0x9B: DWord tempo (BPM * 1000)
    - Event 0x40..0x7F: Channel definitions, panning, volume
    - Event 0xC0..0xDF: Channel names, sample paths, pattern definitions
    - Event 0xE0: Piano Roll Note Array (20 bytes per note)
"""

import sys
import json
import struct
from pathlib import Path
from typing import Dict, List, Any, Optional

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

MUSIC_BOUNCES_DIR = Path.home() / "Music" / "FL Studio Bounces"
DEFAULT_PPQ = 96


def encode_varlen(val: int) -> bytes:
    """Encodes integer as FL Studio variable-length byte sequence."""
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


class FLPProjectBuilder:
    """Constructs native FL Studio .flp project binary files."""

    def __init__(self, title: str = "Dark Cyber-Flamenco Master", bpm: float = 112.0, ppq: int = DEFAULT_PPQ):
        self.title = title
        self.bpm = bpm
        self.ppq = ppq
        self.channels: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []
        self.notes: List[Dict[str, int]] = []

    def add_channel(self, name: str, pan: int = 64, volume: int = 100) -> int:
        """Registers an audio/instrument channel in the project."""
        ch_idx = len(self.channels)
        self.channels.append({
            "index": ch_idx,
            "name": name,
            "pan": max(0, min(127, pan)),
            "volume": max(0, min(127, volume))
        })
        return ch_idx

    def add_note(
        self,
        pos_ticks: int,
        pitch: int,
        duration_ticks: int = 24,
        velocity: int = 100,
        channel_index: int = 0
    ) -> "FLPProjectBuilder":
        """Adds a note event to the project piano roll."""
        self.notes.append({
            "pos": int(pos_ticks),
            "pitch": max(0, min(127, int(pitch))),
            "duration": max(1, int(duration_ticks)),
            "vel": max(0, min(127, int(velocity))),
            "flags": int(0x00400000 | (channel_index & 0xFF))
        })
        return self

    def build_binary(self) -> bytes:
        """Serializes project into valid FLhd + FLdt binary stream."""
        dt_stream = bytearray()

        # 1. Event 0xC7: FL Studio Version String
        version_str = b"25.2.5.5055\x00"
        dt_stream.append(0xC7)
        dt_stream += encode_varlen(len(version_str))
        dt_stream += version_str

        # 2. Event 0x9B: Tempo (DWord: BPM * 1000)
        dt_stream.append(0x9B)
        tempo_int = int(self.bpm * 1000)
        dt_stream += struct.pack("<I", tempo_int)

        # 3. Project Title Event 0xCA
        title_bytes = self.title.encode("utf-8") + b"\x00"
        dt_stream.append(0xCA)
        dt_stream += encode_varlen(len(title_bytes))
        dt_stream += title_bytes

        # 4. Channels definitions
        for ch in self.channels:
            # New channel event 0x40 (Word: channel index)
            dt_stream.append(0x40)
            dt_stream += struct.pack("<H", ch["index"])

            # Channel name event 0xC0
            ch_name_bytes = ch["name"].encode("utf-8") + b"\x00"
            dt_stream.append(0xC0)
            dt_stream += encode_varlen(len(ch_name_bytes))
            dt_stream += ch_name_bytes

            # Volume event 0x01 (Byte)
            dt_stream.append(0x01)
            dt_stream.append(ch["volume"])

            # Pan event 0x02 (Byte)
            dt_stream.append(0x02)
            dt_stream.append(ch["pan"])

        # 5. Note Events (Event 0xE0 Note Array)
        if self.notes:
            sorted_notes = sorted(self.notes, key=lambda n: n["pos"])
            notes_bytes = bytearray()
            for n in sorted_notes:
                notes_bytes += struct.pack(
                    "<IIIIBBBB",
                    n["pos"],
                    n["flags"],
                    n["duration"],
                    n["pitch"],
                    64,            # pan center
                    n["vel"],       # velocity
                    128,           # release
                    80             # mod/cutoff
                )

            dt_stream.append(0xE0)
            dt_stream += encode_varlen(len(notes_bytes))
            dt_stream += notes_bytes

        # End of Data Marker 0x1C (Byte: 1)
        dt_stream.append(0x1C)
        dt_stream.append(0x01)

        # Build FLhd Header: format 0 (project), channels count, ppq
        ch_count = max(1, len(self.channels))
        flhd = b"FLhd" + struct.pack("<IHHH", 6, 0, ch_count, self.ppq)

        # Build FLdt Data Chunk
        fldt = b"FLdt" + struct.pack("<I", len(dt_stream)) + dt_stream

        return flhd + fldt

    def export_flp(self, output_path: str) -> Dict[str, Any]:
        """Writes .flp project to disk."""
        p = Path(output_path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        raw_bytes = self.build_binary()
        p.write_bytes(raw_bytes)
        return {
            "status": "SUCCESS",
            "project_file": str(p),
            "title": self.title,
            "bpm": self.bpm,
            "ppq": self.ppq,
            "channels_count": len(self.channels),
            "notes_count": len(self.notes),
            "file_size_bytes": len(raw_bytes)
        }


def compile_dark_cyber_flamenco_flp(output_file: Optional[str] = None) -> Dict[str, Any]:
    """Compiles the full Dark Cyber-Flamenco arrangement into a standalone native .flp file."""
    if not output_file:
        dest = MUSIC_BOUNCES_DIR / "Projects" / "Dark_Cyber_Flamenco_Master_v13.flp"
    else:
        dest = Path(output_file).expanduser().resolve()

    builder = FLPProjectBuilder(
        title="Dark Cyber-Flamenco (SOTA v13.0)",
        bpm=112.0,
        ppq=96
    )

    # Add standard channels
    c_kick = builder.add_channel("01_Kick_4onTheFloor", pan=64, volume=100)
    c_snare = builder.add_channel("02_Snare_Clap", pan=64, volume=95)
    c_bass = builder.add_channel("03_Rolling_Cyber_Bass", pan=64, volume=90)
    c_flamenco = builder.add_channel("04_Flamenco_Guitar_Arp", pan=70, volume=85)
    c_synth = builder.add_channel("05_Cyber_Lead_Sytrus", pan=58, volume=80)

    # 4 bars of Flamenco Compas (Bulerias: accents on 3, 6, 8, 10, 12)
    accents = {3, 6, 8, 10, 12}
    step_ticks = 48  # Eighth notes
    cur_tick = 0

    for bar in range(4):
        # 4-on-the-floor kick
        for beat in range(4):
            builder.add_note(pos_ticks=cur_tick + (beat * 96), pitch=36, duration_ticks=24, velocity=115, channel_index=c_kick)

        # Flamenco Bulerias Arpeggio & Snare/Palmas
        for beat in range(1, 13):
            tick = cur_tick + (beat - 1) * step_ticks
            is_accent = beat in accents

            # Snare/Palma on accents
            if is_accent:
                builder.add_note(pos_ticks=tick, pitch=38, duration_ticks=20, velocity=118, channel_index=c_snare)

            # Rolling Bass (D Phrygian Dominant: D, Eb, F#, G, A, Bb, C)
            bass_pitch = 38 if beat in (1, 5, 9) else (39 if beat in (3, 7) else 43)
            builder.add_note(pos_ticks=tick, pitch=bass_pitch, duration_ticks=36, velocity=105 if is_accent else 85, channel_index=c_bass)

            # Flamenco Arp Chords (D Phrygian: D4, Eb4, F#4, A4)
            arp_pitch = 62 if (beat % 4 == 1) else (63 if (beat % 4 == 2) else (66 if (beat % 4 == 3) else 69))
            builder.add_note(pos_ticks=tick, pitch=arp_pitch, duration_ticks=40, velocity=110 if is_accent else 75, channel_index=c_flamenco)

        cur_tick += (12 * step_ticks)

    return builder.export_flp(str(dest))


if __name__ == "__main__":
    res = compile_dark_cyber_flamenco_flp()
    print(json.dumps(res, indent=2))
