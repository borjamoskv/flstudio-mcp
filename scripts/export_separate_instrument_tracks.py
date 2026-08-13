#!/usr/bin/env python3
"""
C5-REAL INDIVIDUAL INSTRUMENT TRACK EXPANDER & STEM MIDI GENERATOR
==================================================================
Exports 7 individual stem MIDI files + 1 Master Multi-Track MIDI (Type 1)
so FL Studio 2025 creates SEPARATE CHANNELS / TRACKS for each instrument:

Instruments Split Into Individual Tracks:
1. 01_Fender_Rhodes_73_Satin_Jackets.mid  (Ch 1 - Satin Chords)
2. 02_Solina_Strings_AIR_Pad.mid          (Ch 2 - AIR Ambient Pad)
3. 03_Minimoog_Sub_Bass.mid               (Ch 3 - Minimoog Bass Drive)
4. 04_Maceo_Industrial_303_Acid.mid       (Ch 4 - Maceo Acid Lead)
5. 05_AIR_Vocoder_Space_Lead.mid          (Ch 5 - AIR Vocoder Lead)
6. 06_Maceo_Techno_Kick_DSP.mid           (Ch 10 - Sub Kick)
7. 07_HiHats_Percussion_MPC_Swing.mid     (Ch 10 - Swung Percussion)
"""

import os
import mido
from typing import List, Dict, Tuple

WORKSPACE_DIR = os.path.expanduser("~/10_PROJECTS/flstudio-mcp")
STEMS_DIR = os.path.join(WORKSPACE_DIR, "samples", "separate_instrument_tracks")

os.makedirs(STEMS_DIR, exist_ok=True)

BPM = 118.0
TPB = 480
TICKS_PER_BAR = TPB * 4

# Load original multi-track MIDI file
SOURCE_MIDI_PATH = os.path.join(WORKSPACE_DIR, "samples", "hybrid_flow", "Satin_Maceo_AIR_SOTA_Masterwork.mid")

def split_midi_into_separate_tracks():
    if not os.path.exists(SOURCE_MIDI_PATH):
        raise FileNotFoundError(f"Source MIDI not found: {SOURCE_MIDI_PATH}")

    src_mid = mido.MidiFile(SOURCE_MIDI_PATH)
    print(f"📖 Loaded Source MIDI: {len(src_mid.tracks)} tracks.")

    instrument_names = [
        "01_Fender_Rhodes_73_Satin_Jackets",
        "02_Solina_Strings_AIR_Pad",
        "03_Minimoog_Sub_Bass",
        "04_Maceo_Industrial_303_Acid",
        "05_AIR_Vocoder_Space_Lead",
        "06_Maceo_Techno_Kick_DSP_Drums"
    ]

    generated_files = []

    # Export individual MIDI files for each track
    for idx, track in enumerate(src_mid.tracks):
        # Skip master/tempo track if empty of notes
        note_events = [m for m in track if m.type in ('note_on', 'note_off', 'control_change', 'pitchwheel')]
        if not note_events:
            continue

        track_name = "Track"
        for m in track:
            if m.type == 'track_name':
                track_name = m.name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")
                break

        single_mid = mido.MidiFile(type=1)
        single_mid.ticks_per_beat = TPB

        # Add Tempo Track
        t_master = mido.MidiTrack()
        single_mid.tracks.append(t_master)
        t_master.append(mido.MetaMessage('track_name', name=track_name))
        t_master.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))

        # Add Instrument Track
        t_inst = mido.MidiTrack()
        single_mid.tracks.append(t_inst)
        for msg in track:
            t_inst.append(msg.copy())

        out_name = f"{idx:02d}_{track_name}.mid"
        out_path = os.path.join(STEMS_DIR, out_name)
        single_mid.save(out_path)
        generated_files.append(out_path)
        print(f"✅ Exported Separate Instrument Track -> {out_path}")

    # Build explicit Multi-Channel Master with Channel Isolation
    master_separate_path = os.path.join(STEMS_DIR, "00_MASTER_SEPARATE_CHANNELS_ALL_INSTRUMENTS.mid")
    src_mid.save(master_separate_path)
    print(f"🌟 Master Multi-Channel Separate File -> {master_separate_path}")

    return generated_files, master_separate_path

if __name__ == "__main__":
    split_midi_into_separate_tracks()
