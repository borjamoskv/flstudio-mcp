#!/usr/bin/env python3
"""
Autopoietic FLP Multitrack Stem Compiler (v18.0 Demiurgic Nexus)
Compiles native binary FL Studio Project (.flp) files containing fully configured
audio sampler channels, direct sample file path bindings (Event 0xC4), discrete mixer track
routings (Event 0x45), volume/pan staging, and timeline arrangement trigger notes.

Binary Events Implemented:
- Header: FLhd (format 0, N channels, PPQ 96)
- Event 0xC7: FL Studio engine version string
- Event 0x9B: Tempo DWord (BPM * 1000)
- Event 0xCA: Project title string
- Event 0x40: New Channel ID (Word)
- Event 0xC0: Channel Name (VarLen String)
- Event 0xC4: Sampler Audio File Path (VarLen String)
- Event 0x45: Mixer Track Routing (Word)
- Event 0x01: Channel Volume (Byte)
- Event 0x02: Channel Pan (Byte)
- Event 0xE0: Note Array Triggering Stems at Bar 0 (20 bytes per note)
"""

import json
import struct
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("FLStudio-StemCompiler")

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


def compile_multitrack_stems_flp(
    stems_dir: Optional[str] = None,
    project_title: str = "Dark Cyber Flamenco Multitrack Session",
    bpm: float = 112.0,
    output_flp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compiles an autopoietic .flp project linking discrete WAV stems into channels with mixer routing.
    - stems_dir: path to directory containing WAV stems
    - project_title: embedded project title
    - bpm: project tempo
    - output_flp: target .flp path
    """
    if not stems_dir:
        bounces_dir = Path.home() / "Music" / "FL Studio Bounces"
        default_dir = bounces_dir / "Stems" / "Dark_Cyber_Flamenco_Stems_16Bars"
        if not default_dir.exists() or not list(default_dir.glob("*.wav")):
            from scripts.fl_stems_generator import generate_flamenco_stems_pack
            generate_flamenco_stems_pack()
        in_stems_path = default_dir
    else:
        in_stems_path = Path(stems_dir).expanduser().resolve()

    if not in_stems_path.exists():
        raise FileNotFoundError(f"Stems directory not found: {in_stems_path}")

    wav_files = sorted(list(in_stems_path.glob("*.wav")))
    if not wav_files:
        raise ValueError(f"No WAV stems found in {in_stems_path}")

    # Build binary stream
    dt_stream = bytearray()

    # 1. Event 0xC7: FL Studio Version
    version_str = b"25.2.5.5055\x00"
    dt_stream.append(0xC7)
    dt_stream += encode_varlen(len(version_str))
    dt_stream += version_str

    # 2. Event 0x9B: Tempo (BPM * 1000)
    dt_stream.append(0x9B)
    tempo_int = int(bpm * 1000)
    dt_stream += struct.pack("<I", tempo_int)

    # 3. Event 0xCA: Title
    title_bytes = project_title.encode("utf-8") + b"\x00"
    dt_stream.append(0xCA)
    dt_stream += encode_varlen(len(title_bytes))
    dt_stream += title_bytes

    channels_meta = []
    notes_bytes = bytearray()
    ticks_16_bars = 16 * 4 * DEFAULT_PPQ  # 6144 ticks

    for ch_idx, stem_file in enumerate(wav_files):
        mixer_track = ch_idx + 1  # Mixer 1, 2, 3...
        stem_name = stem_file.stem.replace("_", " ")

        # Event 0x40: New Channel index
        dt_stream.append(0x40)
        dt_stream += struct.pack("<H", ch_idx)

        # Event 0xC0: Channel Name
        ch_name_b = stem_name.encode("utf-8") + b"\x00"
        dt_stream.append(0xC0)
        dt_stream += encode_varlen(len(ch_name_b))
        dt_stream += ch_name_b

        # Event 0xC4: Sample File Path
        sample_path_b = str(stem_file.resolve()).encode("utf-8") + b"\x00"
        dt_stream.append(0xC4)
        dt_stream += encode_varlen(len(sample_path_b))
        dt_stream += sample_path_b

        # Event 0x45: Mixer Track Routing (Word)
        dt_stream.append(0x45)
        dt_stream += struct.pack("<H", mixer_track)

        # Event 0x01: Volume (100 out of 127)
        dt_stream.append(0x01)
        dt_stream.append(100)

        # Event 0x02: Pan (64 = center)
        dt_stream.append(0x02)
        dt_stream.append(64)

        channels_meta.append({
            "channel_index": ch_idx,
            "channel_name": stem_name,
            "sample_file": str(stem_file),
            "mixer_track": mixer_track,
            "volume": 100,
            "pan": 64
        })

        # Add trigger note at Bar 0 (pitch C5 = 60)
        flags = int(0x00400000 | (ch_idx & 0xFF))
        notes_bytes += struct.pack(
            "<IIIIBBBB",
            0,              # pos = 0
            flags,          # flags
            ticks_16_bars,  # duration 16 bars
            60,             # pitch C5
            64,             # pan center
            100,            # velocity
            128,            # release
            80              # mod
        )

    # Event 0xE0: Note Array
    if notes_bytes:
        dt_stream.append(0xE0)
        dt_stream += encode_varlen(len(notes_bytes))
        dt_stream += notes_bytes

    # End of Data Marker 0x1C
    dt_stream.append(0x1C)
    dt_stream.append(0x01)

    # Build Header FLhd
    num_ch = len(wav_files)
    flhd = b"FLhd" + struct.pack("<IHHH", 6, 0, num_ch, DEFAULT_PPQ)
    fldt = b"FLdt" + struct.pack("<I", len(dt_stream)) + dt_stream
    flp_binary = flhd + fldt

    # Output directory
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Projects"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_flp:
        out_flp_path = out_dir / "Dark_Cyber_Flamenco_Multitrack_Session_v18.flp"
    else:
        out_flp_path = Path(output_flp).expanduser().resolve()
        out_flp_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_flp_path, "wb") as f:
        f.write(flp_binary)

    # Export session JSON manifest
    manifest_path = out_flp_path.with_suffix(".json")
    manifest_data = {
        "project_title": project_title,
        "bpm": bpm,
        "ppq": DEFAULT_PPQ,
        "flp_file": str(out_flp_path),
        "file_size_bytes": len(flp_binary),
        "total_channels": num_ch,
        "channels": channels_meta
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return {
        "status": "SUCCESS",
        "project_title": project_title,
        "bpm": bpm,
        "total_stem_channels": num_ch,
        "flp_file": str(out_flp_path),
        "manifest_file": str(manifest_path),
        "file_size_bytes": len(flp_binary),
        "stems_linked": [c["sample_file"] for c in channels_meta]
    }


if __name__ == "__main__":
    res = compile_multitrack_stems_flp()
    print("Multitrack Stem FLP Compiler Output:", res)
