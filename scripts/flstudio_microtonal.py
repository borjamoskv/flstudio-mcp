#!/usr/bin/env python3
"""
Antigravity Microtonal & Xenharmonic Engine for FL Studio MCP
Computes sub-cent pitch bend matrices, MPE polyphonic channels, and Xenharmonic scales.
Supports 24-TET (Quarter-tones / Makam), 19-TET, 31-TET, Just Intonation, and Bohlen-Pierce.
"""

import math
import os
import random
import mido
from typing import List, Dict, Tuple, Optional

# Microtonal Scale Systems (Frequency ratios or Cents offsets relative to 12-TET root)
MICROTONAL_SYSTEMS = {
    "24tet": {
        "description": "24 Equal Temperament (Quarter-tone system, 50 cents per step)",
        "cents": [i * 50.0 for i in range(24)]
    },
    "19tet": {
        "description": "19 Equal Temperament (63.16 cents per step - Pure 3rds & 6ths)",
        "cents": [i * (1200.0 / 19.0) for i in range(19)]
    },
    "31tet": {
        "description": "31 Equal Temperament (38.71 cents per step - Meantone & Just Intonation approx)",
        "cents": [i * (1200.0 / 31.0) for i in range(31)]
    },
    "just_intonation": {
        "description": "Just Intonation 7-limit (Pure integer frequency ratios)",
        "cents": [
            0.0,      # 1:1 Unison
            111.73,   # 16:15 Minor 2nd
            203.91,   # 9:8 Major 2nd
            315.64,   # 6:5 Minor 3rd
            386.31,   # 5:4 Major 3rd
            498.04,   # 4:3 Perfect 4th
            582.51,   # 7:5 Tritone / Subminor 5th
            701.96,   # 3:2 Perfect 5th
            813.69,   # 8:5 Minor 6th
            884.36,   # 5:3 Major 6th
            968.83,   # 7:4 Harmonic 7th
            1088.27   # 15:8 Major 7th
        ]
    },
    "bohlen_pierce": {
        "description": "Bohlen-Pierce Non-Octave Scale (Tritave 3:1 divided into 13 steps)",
        "cents": [i * (1901.955 / 13.0) for i in range(13)]  # 1901.955 cents = 3:1 ratio
    },
    "makam_bayati": {
        "description": "Arabian Makam Bayati (Featuring D neutral 2nd ~ half-flat, ~150 cents)",
        "cents": [0.0, 150.0, 300.0, 500.0, 700.0, 850.0, 1000.0]
    },
    "makam_rast": {
        "description": "Arabian Makam Rast (Featuring E neutral 3rd & B neutral 7th ~ half-flats)",
        "cents": [0.0, 200.0, 350.0, 500.0, 700.0, 900.0, 1050.0]
    },
    "slendro": {
        "description": "Indonesian Gamelan Slendro (5-tone quasi-equidistant pentatonic scale)",
        "cents": [0.0, 240.0, 480.0, 720.0, 960.0]
    },
    "pelog": {
        "description": "Indonesian Gamelan Pelog Selisir (7-tone heptatonic scale with narrow 2nds)",
        "cents": [0.0, 120.0, 270.0, 540.0, 670.0, 780.0, 950.0]
    },
    "wendy_carlos_alpha": {
        "description": "Wendy Carlos Alpha Scale (78.0 cents per step - 15.385 steps per octave)",
        "cents": [i * 78.0 for i in range(15)]
    },
    "partch_43": {
        "description": "Harry Partch 43-Tone Just Intonation Monophonic Fabric",
        "cents": [
            0.0, 21.51, 62.96, 105.0, 150.64, 182.4, 203.91, 231.17, 266.87, 294.13, 315.64,
            347.41, 386.31, 417.51, 435.08, 470.78, 498.04, 519.55, 551.32, 582.51, 617.49,
            648.68, 680.45, 701.96, 729.22, 764.92, 782.49, 813.69, 852.59, 884.36, 905.87,
            933.13, 968.83, 996.09, 1017.6, 1049.36, 1094.92, 1126.69, 1149.36, 1178.49
        ]
    }
}


def cents_to_pitch_bend(cents_offset: float, semitone_range: float = 2.0) -> int:
    """
    Converts a pitch offset in cents (-200 to +200) to a 14-bit MIDI Pitch Bend value (-8192 to +8191).
    Default semitone_range is 2.0 semitones (+/- 200 cents).
    Resolution: ~0.0244 cents per MIDI step.
    """
    max_cents = semitone_range * 100.0
    normalized = max(-1.0, min(1.0, cents_offset / max_cents))
    return int(round(normalized * 8191.0))


def generate_microtonal_midi(
    output_path: str,
    system_name: str = "24tet",
    scale_steps: List[int] = [0, 3, 7, 10, 14, 17, 21],
    bpm: float = 116.0,
    length_bars: int = 4,
    semitone_range: float = 2.0,
    polyphonic: bool = True
) -> str:
    """
    Generates an MPE-compliant Multi-Channel Microtonal MIDI file.
    Each polyphonic note is assigned to a separate MIDI channel with sub-cent Pitch Bend tuning.
    """
    if system_name not in MICROTONAL_SYSTEMS:
        system_name = "24tet"

    sys_info = MICROTONAL_SYSTEMS[system_name]
    cents_list = sys_info["cents"]

    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    # Create Conductor Track
    track_cond = mido.MidiTrack()
    mid.tracks.append(track_cond)
    track_cond.append(mido.MetaMessage('track_name', name=f'Microtonal {system_name} Conductor'))
    track_cond.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # Create MPE Note Track
    track_notes = mido.MidiTrack()
    mid.tracks.append(track_notes)
    track_notes.append(mido.MetaMessage('track_name', name=f'Microtonal Notes ({system_name})'))

    ticks_per_step = ticks_per_beat // 2  # 8th note steps
    total_steps = length_bars * 8

    channel_idx = 0

    for i in range(total_steps):
        step_idx = scale_steps[i % len(scale_steps)]
        
        # Calculate total cents from root
        total_cents = cents_list[step_idx % len(cents_list)] + 1200.0 * (step_idx // len(cents_list))
        
        # Split into nearest 12-TET MIDI semitone + microtonal cent offset
        base_midi_note = 60 + int(round(total_cents / 100.0))
        cent_offset = total_cents - ((base_midi_note - 60) * 100.0)

        # Calculate exact 14-bit pitch bend
        pb_val = cents_to_pitch_bend(cent_offset, semitone_range=semitone_range)
        cur_chan = (channel_idx % 14) if polyphonic else 0  # MPE Channels 0..13

        # Send Pitch Bend message on specific channel before note_on
        track_notes.append(mido.Message('pitchwheel', channel=cur_chan, pitch=pb_val, time=0 if i > 0 else ticks_per_step))
        
        # Send Note On
        vel = random.randint(85, 110)
        track_notes.append(mido.Message('note_on', channel=cur_chan, note=base_midi_note, velocity=vel, time=ticks_per_step if i > 0 else 0))
        
        # Send Note Off
        track_notes.append(mido.Message('note_off', channel=cur_chan, note=base_midi_note, velocity=0, time=ticks_per_step // 2))

        channel_idx += 1

    mid.save(output_path)
    print(f"[Microtonal Generator] Saved MPE Microtonal MIDI ({system_name}) -> {output_path}")
    return output_path


def export_scala_scl_file(system_name: str, output_path: str) -> str:
    """
    Exports a Scala (.scl) microtonal tuning file compatible with FL Studio native plugins (Sytrus, Harmor, FLEX).
    """
    if system_name not in MICROTONAL_SYSTEMS:
        system_name = "24tet"

    cents_list = MICROTONAL_SYSTEMS[system_name]["cents"][1:]  # Exclude unison 0.0
    desc = MICROTONAL_SYSTEMS[system_name]["description"]

    lines = [
        f"! {system_name}.scl",
        f"! Created by Antigravity FL Studio MCP Microtonal Engine",
        f"{desc}",
        f"{len(cents_list)}"
    ]

    for c in cents_list:
        lines.append(f" {c:.4f}")

    content = "\n".join(lines) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[Scala Exporter] Saved Scala Tuning File (.scl) -> {output_path}")
    return output_path


def export_scala_kbm_file(output_path: str, middle_note: int = 60, ref_note: int = 69, ref_freq: float = 440.0) -> str:
    """
    Exports a Scala Keyboard Mapping (.kbm) file for exact note-to-frequency mapping in plugins.
    """
    lines = [
        "! Default Keyboard Mapping",
        "! Map size:",
        "0",
        "! First MIDI note number to retune:",
        "0",
        "! Last MIDI note number to retune:",
        "127",
        "! Middle note where 1/1 ratio is located:",
        f"{middle_note}",
        "! Reference note for given frequency:",
        f"{ref_note}",
        "! Reference frequency in Hz:",
        f"{ref_freq:.4f}",
        "! Scale degree for formal octave:",
        "0"
    ]
    content = "\n".join(lines) + "\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[Scala KBM Exporter] Saved Scala Keyboard Mapping (.kbm) -> {output_path}")
    return output_path

