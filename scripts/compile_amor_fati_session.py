#!/usr/bin/env python3
"""
SOTA Bare-Metal Master Production Session Compiler for FL Studio 2025
════════════════════════════════════════════════════════════════════
Artist: Borja Moskv
Title: AMOR FATI (Bare Metal Production Session)
Style: Radical Minimalism, Few Notes, Space Echo RE-201, Motorik Pulse, Maqam Bayati

Compiles a native binary FL Studio project (.flp) directly linking:
- 8 discrete channels with direct WAV audio bindings (Event 0xC4)
- Discrete mixer track routings 1..8 (Event 0x45)
- Dynamic panning and volume gain staging (Events 0x01, 0x02)
- Synchronized stem trigger notes (Pitch C5, duration 64 bars)
- Minimalist piano roll motifs for Rhodes stabs, Sakura harmonics, and Sub bass
- Seamless drag-and-drop replacement with native .fst synth presets
"""

import sys
import struct
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

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


def compile_amor_fati_bare_metal_flp(
    output_flp_path: str,
    bpm: float = 118.0,
    total_bars: int = 64
) -> Dict[str, Any]:
    """
    Compiles the native .flp binary file for AMOR FATI Bare-Metal Production Session.
    """
    out_path = Path(output_flp_path).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    project_title = "Borja Moskv - AMOR FATI (Bare Metal Production Session)"

    stems_base = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/samples/stems")
    flamenco_base = stems_base / "Dark_Cyber_Flamenco_Stems_16Bars"

    # 8 Bare-metal production channels with direct WAV sample paths
    channels_def = [
        {
            "index": 0,
            "name": "01 - Rhodes 73 (Space Echo)",
            "sample_path": str(stems_base / "04_Rhodes.wav"),
            "mixer_track": 1,
            "volume": 95,
            "pan": 60  # slightly left
        },
        {
            "index": 1,
            "name": "02 - Physical Pluck (Flamenco Arp)",
            "sample_path": str(flamenco_base / "04_Flamenco_Arp_Chords.wav"),
            "mixer_track": 2,
            "volume": 90,
            "pan": 68  # slightly right
        },
        {
            "index": 2,
            "name": "03 - Sub & Resonant Bass",
            "sample_path": str(stems_base / "02_Bass.wav"),
            "mixer_track": 3,
            "volume": 105,
            "pan": 64  # center
        },
        {
            "index": 3,
            "name": "04 - Motorik Acoustic Kick",
            "sample_path": str(flamenco_base / "01_Kick_4onTheFloor.wav"),
            "mixer_track": 4,
            "volume": 108,
            "pan": 64  # center
        },
        {
            "index": 4,
            "name": "05 - Organic Palmas & Perc",
            "sample_path": str(flamenco_base / "02_Snare_Clap_Flamenco.wav"),
            "mixer_track": 5,
            "volume": 85,
            "pan": 72  # right
        },
        {
            "index": 5,
            "name": "06 - Nietzsche & Alain Vocoder",
            "sample_path": str(stems_base / "06_Vocals_3D.wav"),
            "mixer_track": 6,
            "volume": 90,
            "pan": 64  # center
        },
        {
            "index": 6,
            "name": "07 - Analog Coil Drone (Bayati)",
            "sample_path": str(stems_base / "07_FX_Ambiance.wav"),
            "mixer_track": 7,
            "volume": 80,
            "pan": 58  # left
        },
        {
            "index": 7,
            "name": "08 - Space Echo Arp Bus",
            "sample_path": str(stems_base / "05_Space_Arp.wav"),
            "mixer_track": 8,
            "volume": 100,
            "pan": 64  # center
        }
    ]

    # Data stream
    dt_stream = bytearray()

    # 1. Event 0xC7: FL Studio Version String
    version_str = b"25.2.5.5055\x00"
    dt_stream.append(0xC7)
    dt_stream += encode_varlen(len(version_str))
    dt_stream += version_str

    # 2. Event 0x9B: Tempo (BPM * 1000)
    dt_stream.append(0x9B)
    tempo_int = int(bpm * 1000)
    dt_stream += struct.pack("<I", tempo_int)

    # 3. Event 0xCA: Project Title (UTF-16-LE)
    title_bytes = project_title.encode("utf-16-le") + b"\x00\x00"
    dt_stream.append(0xCA)
    dt_stream += encode_varlen(len(title_bytes))
    dt_stream += title_bytes

    # 4. Channels definitions
    for ch in channels_def:
        # Event 0x40: New Channel Index (Word)
        dt_stream.append(0x40)
        dt_stream += struct.pack("<H", ch["index"])

        # Event 0xCB: Channel Name (UTF-16-LE, FL Studio 12/20/21/2025 native)
        ch_name_bytes = ch["name"].encode("utf-16-le") + b"\x00\x00"
        dt_stream.append(0xCB)
        dt_stream += encode_varlen(len(ch_name_bytes))
        dt_stream += ch_name_bytes

        # Event 0xC0: Channel Name fallback (UTF-16-LE)
        dt_stream.append(0xC0)
        dt_stream += encode_varlen(len(ch_name_bytes))
        dt_stream += ch_name_bytes

        # Event 0xC4: Sample File Path
        if "sample_path" in ch and Path(ch["sample_path"]).exists():
            sample_bytes = str(Path(ch["sample_path"]).resolve()).encode("utf-8") + b"\x00"
            dt_stream.append(0xC4)
            dt_stream += encode_varlen(len(sample_bytes))
            dt_stream += sample_bytes

        # Event 0x45: Mixer Track Routing (Word)
        dt_stream.append(0x45)
        dt_stream += struct.pack("<H", ch["mixer_track"])

        # Event 0x01: Channel Volume (Byte)
        dt_stream.append(0x01)
        dt_stream.append(int(ch["volume"]))

        # Event 0x02: Channel Pan (Byte)
        dt_stream.append(0x02)
        dt_stream.append(int(ch["pan"]))

    # 5. Note Events (Stem Triggers + Minimalist Motifs)
    bar_ticks = 4 * DEFAULT_PPQ
    ticks_total = total_bars * bar_ticks
    notes: List[Dict[str, Any]] = []

    def add_note(pos: int, pitch: int, dur: int, vel: int, ch_idx: int, pan: int = 64):
        flags = int(0x00400000 | (ch_idx & 0xFF))
        notes.append({
            "pos": int(pos),
            "pitch": max(0, min(127, int(pitch))),
            "duration": max(1, int(dur)),
            "vel": max(0, min(127, int(vel))),
            "flags": flags,
            "pan": max(0, min(127, int(pan)))
        })

    # Pattern composition across 64 bars (Hypnotic Radical Minimalism, Maqam Bayati, Bulerías Compás)
    # Drone (Ch 6): Continuous D2 / D3 anchor across 64 bars
    drone_step = 8 * bar_ticks  # 8-bar sustained notes
    for b in range(0, total_bars, 8):
        pos = b * bar_ticks
        add_note(pos=pos, pitch=50, dur=drone_step - 24, vel=75, ch_idx=6, pan=58)  # D3
        add_note(pos=pos, pitch=57, dur=drone_step - 24, vel=65, ch_idx=6, pan=62)  # A3

    # Motorik Kick (Ch 3): 4-on-the-floor hypnotic pulse (quarter note = 96 ticks)
    # Starts at Bar 4 and drops out during negative space breakdown at Bars 32..40
    for b in range(0, total_bars):
        if 32 <= b < 40:
            # Negative space breakdown
            continue
        bar_start = b * bar_ticks
        for beat in range(4):
            pos = bar_start + (beat * DEFAULT_PPQ)
            vel = 112 if beat == 0 else (104 if beat == 2 else 98)
            add_note(pos=pos, pitch=60, dur=36, vel=vel, ch_idx=3, pan=64)  # C5 root

    # Sub Bass (Ch 2): Deep root notes in D, sliding to C and F
    for b in range(0, total_bars, 2):
        if 32 <= b < 40:
            continue
        pos = b * bar_ticks
        bass_pitch = 50  # D3 root
        if b in (8, 24, 48, 56):
            bass_pitch = 48  # C3
        elif b in (16, 40):
            bass_pitch = 53  # F3
        add_note(pos=pos, pitch=bass_pitch, dur=bar_ticks + 192, vel=106, ch_idx=2, pan=64)

    # Rhodes 73 (Ch 0): Dm9 / Dm11 voicings on beat 1 with micro-groove offset for Space Echo tails
    for b in range(0, total_bars, 4):
        pos = b * bar_ticks + 48  # micro-groove offset
        # Dm9 / Dm11 chord stab
        add_note(pos=pos, pitch=62, dur=180, vel=88, ch_idx=0, pan=56)  # D4
        add_note(pos=pos, pitch=65, dur=180, vel=82, ch_idx=0, pan=64)  # F4
        add_note(pos=pos, pitch=69, dur=180, vel=85, ch_idx=0, pan=62)  # A4
        add_note(pos=pos, pitch=72, dur=180, vel=78, ch_idx=0, pan=68)  # C5
        add_note(pos=pos, pitch=76, dur=180, vel=74, ch_idx=0, pan=72)  # E5

        # Syncopated 2nd stab on beat 3.5
        if b % 8 == 4:
            sync_pos = b * bar_ticks + (3 * DEFAULT_PPQ) + 48
            add_note(pos=sync_pos, pitch=62, dur=96, vel=80, ch_idx=0, pan=60)
            add_note(pos=sync_pos, pitch=67, dur=96, vel=76, ch_idx=0, pan=66)  # G4 (Dm11)

    # Sakura Physical Pluck (Ch 1): High crystalline harmonics
    for b in range(2, total_bars, 4):
        pos = b * bar_ticks + (2 * DEFAULT_PPQ)
        pitch = 69 if (b % 8 == 2) else 74  # A4 or D5
        add_note(pos=pos, pitch=pitch, dur=bar_ticks * 2, vel=92, ch_idx=1, pan=68)

    # Palmas & Percussion (Ch 4): Flamenco Bulerías Compás (accents on 3, 6, 8, 10, 12)
    step_48 = 48  # eighth-note ticks
    bulerias_accents = {3, 6, 8, 10, 12}
    for b in range(16, total_bars, 3):  # 3 bars of 4/4 = 12 eighth notes cycle
        if 32 <= b < 40:
            continue
        block_start = b * bar_ticks
        for step in range(1, 13):
            pos = block_start + (step - 1) * step_48
            if step in bulerias_accents:
                vel = 115 if step in (3, 10) else 100
                add_note(pos=pos, pitch=60, dur=32, vel=vel, ch_idx=4, pan=72)
            else:
                if step % 2 == 1:
                    add_note(pos=pos, pitch=58, dur=20, vel=60, ch_idx=4, pan=70)  # Ghost tap

    # Vocoder Resonator (Ch 5): Vocal formant sustained chords during climax (Bars 40..56)
    for b in range(40, 56, 4):
        pos = b * bar_ticks
        add_note(pos=pos, pitch=57, dur=bar_ticks * 4 - 48, vel=85, ch_idx=5, pan=64)  # A3
        add_note(pos=pos, pitch=62, dur=bar_ticks * 4 - 48, vel=88, ch_idx=5, pan=64)  # D4
        add_note(pos=pos, pitch=65, dur=bar_ticks * 4 - 48, vel=82, ch_idx=5, pan=64)  # F4

    # Space Arp / Patcher Bus (Ch 7): Atmospheric pulses in breakdown & climax (Bars 32..64)
    for b in range(32, 64, 2):
        pos = b * bar_ticks
        add_note(pos=pos, pitch=62, dur=96, vel=78, ch_idx=7, pan=60)
        add_note(pos=pos + 96, pitch=65, dur=96, vel=72, ch_idx=7, pan=68)
        add_note(pos=pos + 192, pitch=69, dur=96, vel=82, ch_idx=7, pan=62)
        add_note(pos=pos + 288, pitch=72, dur=96, vel=75, ch_idx=7, pan=66)

    # Sort notes strictly by position
    sorted_notes = sorted(notes, key=lambda n: n["pos"])
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
            128,  # release
            80    # mod
        )

    # Event 0xE0: Note Array
    dt_stream.append(0xE0)
    dt_stream += encode_varlen(len(notes_bytes))
    dt_stream += notes_bytes

    # End of Data Marker 0x1C (Byte: 1)
    dt_stream.append(0x1C)
    dt_stream.append(0x01)

    # Build Header FLhd: format 0 (project), channels count, ppq
    ch_count = len(channels_def)
    flhd = b"FLhd" + struct.pack("<IHHH", 6, 0, ch_count, DEFAULT_PPQ)
    fldt = b"FLdt" + struct.pack("<I", len(dt_stream)) + dt_stream

    flp_binary = flhd + fldt
    out_path.write_bytes(flp_binary)

    # Create session JSON metadata
    json_path = out_path.with_suffix(".json")
    meta = {
        "title": project_title,
        "artist": "Borja Moskv",
        "bpm": bpm,
        "ppq": DEFAULT_PPQ,
        "total_bars": total_bars,
        "channels": channels_def,
        "notes_count": len(sorted_notes),
        "flp_file": str(out_path),
        "file_size_bytes": len(flp_binary)
    }
    json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "status": "SUCCESS",
        "project_file": str(out_path),
        "json_file": str(json_path),
        "bpm": bpm,
        "channels_count": ch_count,
        "notes_count": len(sorted_notes),
        "file_size_bytes": len(flp_binary)
    }

if __name__ == "__main__":
    dest = Path.home() / "Documents" / "Image-Line" / "FL Studio" / "Projects" / "Borja_Moskv_-_AMOR_FATI_(Bare_Metal_Production_Session).flp"
    res = compile_amor_fati_bare_metal_flp(str(dest))
    print(json.dumps(res, indent=2))
