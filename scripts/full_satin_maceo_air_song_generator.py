#!/usr/bin/env python3
"""
C5-REAL FULL SONG ARRANGEMENT GENERATOR (v3.0 SOTA)
===================================================
Generates a complete 144-bar (4m 52s at 118 BPM) structured song:
Satin Jackets (Synthwave) x Maceo Plex (Techno-Industrial) x AIR (Moon Safari Ambient)

Song Structure (144 Bars Total):
--------------------------------
1.  Intro (Atmospheric Ambient AIR)            : Bars 1-16   (16 bars)
2.  Verse A (Satin Jackets Synthwave Pulse)   : Bars 17-32  (16 bars)
3.  Build-Up A (Industrial Ingress Maceo)     : Bars 33-48  (16 bars)
4.  Main Drop / Peak Flow Apex 1               : Bars 49-80  (32 bars)
5.  Breakdown / Ambient Bridge (AIR Space-Pop) : Bars 81-96  (16 bars)
6.  False Drop & Picardy Modulation Shift     : Bars 97-104 (8 bars)
7.  Peak Flow Apex 2 (Final Maximum Drop)     : Bars 105-128(24 bars)
8.  Outro / Deconstruction                      : Bars 129-144(16 bars)
"""

import math
import struct
import wave
import os
import random
import mido
from typing import List, Dict, Any

WORKSPACE_DIR = os.path.expanduser("~/10_PROJECTS/flstudio-mcp")
SAMPLES_DIR = os.path.join(WORKSPACE_DIR, "samples", "hybrid_flow")
FL_SCRIPTS_DIR = os.path.expanduser("~/Documents/Image-Line/FL Studio/Settings/Piano roll scripts")

os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(FL_SCRIPTS_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Song Structure Definition
# -----------------------------------------------------------------------------
BPM = 118.0
TICKS_PER_BEAT = 480
BEATS_PER_BAR = 4
TICKS_PER_BAR = TICKS_PER_BEAT * BEATS_PER_BAR # 1920 ticks

SECTIONS = [
    {"name": "1. Intro (AIR Ambient Space)", "bars": 16, "kick": False, "bass": False, "rhodes": True, "strings": True, "arp": False, "hats": False},
    {"name": "2. Verse A (Satin Jackets Pulse)", "bars": 16, "kick": False, "bass": True, "rhodes": True, "strings": True, "arp": False, "hats": True},
    {"name": "3. Build-Up A (Maceo Ingress)", "bars": 16, "kick": True, "bass": True, "rhodes": True, "strings": False, "arp": True, "hats": True},
    {"name": "4. Main Drop (Peak Flow Apex 1)", "bars": 32, "kick": True, "bass": True, "rhodes": True, "strings": True, "arp": True, "hats": True},
    {"name": "5. Ambient Bridge (AIR Space-Pop)", "bars": 16, "kick": False, "bass": False, "rhodes": True, "strings": True, "arp": False, "hats": False},
    {"name": "6. False Drop & Picardy Shift", "bars": 8,  "kick": False, "bass": False, "rhodes": True, "strings": True, "arp": True, "hats": False},
    {"name": "7. Peak Flow Apex 2 (Final Drop)", "bars": 24, "kick": True, "bass": True, "rhodes": True, "strings": True, "arp": True, "hats": True},
    {"name": "8. Outro (Deconstruction)", "bars": 16, "kick": False, "bass": True, "rhodes": True, "strings": True, "arp": False, "hats": False},
]

# Chords (Penrose Stair non-resolving loop in C Minor + Picardy Modulation)
PENROSE_CHORDS = [
    # Bar 1: Abmaj7
    [44, 56, 60, 63, 67],
    # Bar 2: Bb9
    [46, 58, 62, 65, 70],
    # Bar 3: Cm9 (Landing)
    [48, 60, 63, 67, 70],
    # Bar 4: Fm9
    [41, 53, 56, 60, 63],
]

PICARDY_CHORDS = [
    # Cmaj9 (Picardy 3rd Euphoria)
    [48, 60, 64, 67, 71],
    # Fmaj9
    [41, 53, 57, 60, 64],
]

# -----------------------------------------------------------------------------
# MIDI Generation Engine
# -----------------------------------------------------------------------------
def generate_full_song_midi(output_path: str) -> str:
    mid = mido.MidiFile(type=1)
    mid.ticks_per_beat = TICKS_PER_BEAT

    # --- Master Track & Section Markers ---
    master = mido.MidiTrack()
    mid.tracks.append(master)
    master.append(mido.MetaMessage('track_name', name='Master Tempo & Structure (118 BPM)'))
    master.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))

    current_tick = 0
    for sec in SECTIONS:
        master.append(mido.MetaMessage('marker', text=sec["name"], time=current_tick if current_tick == 0 else 0))
        current_tick = sec["bars"] * TICKS_PER_BAR

    # --- TRACK 1: Fender Rhodes 73 (Satin Jackets Chords) ---
    tr_rhodes = mido.MidiTrack()
    mid.tracks.append(tr_rhodes)
    tr_rhodes.append(mido.MetaMessage('track_name', name='Rhodes 73 (Satin Jackets Chords)'))

    # --- TRACK 2: Solina Strings Ensemble (AIR Ambient Pad) ---
    tr_strings = mido.MidiTrack()
    mid.tracks.append(tr_strings)
    tr_strings.append(mido.MetaMessage('track_name', name='Solina Strings (AIR Ambient Pad)'))

    # --- TRACK 3: Minimoog Driving Bassline (Maceo + Satin Jackets) ---
    tr_bass = mido.MidiTrack()
    mid.tracks.append(tr_bass)
    tr_bass.append(mido.MetaMessage('track_name', name='Minimoog Bassline (Drive)'))

    # --- TRACK 4: Maceo Plex FM Arp / Metallic Lead ---
    tr_arp = mido.MidiTrack()
    mid.tracks.append(tr_arp)
    tr_arp.append(mido.MetaMessage('track_name', name='FM Arpeggio (Maceo Industrial)'))

    # --- TRACK 5: Drums (Maceo Kick + 62% MPC Swing Hi-Hats) ---
    tr_drums = mido.MidiTrack()
    mid.tracks.append(tr_drums)
    tr_drums.append(mido.MetaMessage('track_name', name='Drums (Kick + Swung Hats)'))

    # --- Event Accumulators ---
    rhodes_events = []
    strings_events = []
    bass_events = []
    arp_events = []
    drums_events = []

    bar_offset = 0

    for sec_idx, sec in enumerate(SECTIONS):
        bars = sec["bars"]

        for b in range(bars):
            global_bar = bar_offset + b
            bar_tick = global_bar * TICKS_PER_BAR

            # 1. Fender Rhodes Chords
            if sec["rhodes"]:
                # Check for False Drop section (Picardy modulation)
                if sec_idx == 5: # False drop section
                    chord_notes = PICARDY_CHORDS[b % len(PICARDY_CHORDS)]
                    vel = 92
                else:
                    chord_notes = PENROSE_CHORDS[b % len(PENROSE_CHORDS)]
                    vel = 78 if not sec["kick"] else 84

                for n in chord_notes:
                    jitter = random.randint(-5, 5) if global_bar > 0 else 0
                    t_on = bar_tick + jitter
                    t_off = t_on + TICKS_PER_BAR - 40
                    rhodes_events.append({"time": t_on, "msg": mido.Message('note_on', channel=0, note=n, velocity=vel + random.randint(-3, 3), time=0)})
                    rhodes_events.append({"time": t_off, "msg": mido.Message('note_off', channel=0, note=n, velocity=0, time=0)})

            # 2. Solina Strings Pad
            if sec["strings"]:
                pad_notes = [72, 75, 79] if (global_bar % 4 in [0, 1]) else [70, 74, 77]
                if sec_idx == 5: # Picardy euphoria
                    pad_notes = [72, 76, 79]
                for n in pad_notes:
                    t_on = bar_tick
                    t_off = t_on + TICKS_PER_BAR - 20
                    strings_events.append({"time": t_on, "msg": mido.Message('note_on', channel=1, note=n, velocity=68, time=0)})
                    strings_events.append({"time": t_off, "msg": mido.Message('note_off', channel=1, note=n, velocity=0, time=0)})

            # 3. Minimoog Driving Bass
            if sec["bass"]:
                # Root note mapping based on Penrose chords
                root_map = [32, 34, 36, 29] # Ab1, Bb1, C2, F1
                root = root_map[b % 4]
                
                # 16th note pattern
                for step in range(16):
                    step_tick = bar_tick + (step * 120)
                    dur = 100
                    # Octave jump on step 3, 7, 11, 15
                    n = root + 12 if (step in [3, 7, 11, 15]) else root
                    v = random.randint(92, 108)
                    bass_events.append({"time": step_tick, "msg": mido.Message('note_on', channel=2, note=n, velocity=v, time=0)})
                    bass_events.append({"time": step_tick + dur, "msg": mido.Message('note_off', channel=2, note=n, velocity=0, time=0)})

            # 4. Maceo Industrial FM Arp
            if sec["arp"]:
                arp_scale = [60, 63, 67, 70, 72, 75] # Cm pentatonic/minor
                for step in range(16):
                    if step % 2 == 0:
                        step_tick = bar_tick + (step * 120)
                        n = arp_scale[(step + b) % len(arp_scale)]
                        dur = 90
                        arp_events.append({"time": step_tick, "msg": mido.Message('note_on', channel=3, note=n, velocity=88, time=0)})
                        arp_events.append({"time": step_tick + dur, "msg": mido.Message('note_off', channel=3, note=n, velocity=0, time=0)})

            # 5. Drums (Maceo Kick + MPC Swing Hats)
            if sec["kick"]:
                # 4-on-the-floor kick
                for beat in range(4):
                    # Check for false drop silence on last 2 beats of section 6
                    if sec_idx == 5 and b == 7 and beat in [2, 3]:
                        continue
                    t_on = bar_tick + (beat * 480)
                    drums_events.append({"time": t_on, "msg": mido.Message('note_on', channel=9, note=36, velocity=115, time=0)})
                    drums_events.append({"time": t_on + 220, "msg": mido.Message('note_off', channel=9, note=36, velocity=0, time=0)})

            if sec["hats"]:
                # Offbeat 16th hats with 62% swing
                for step in range(16):
                    if step % 2 == 1:
                        swing = 18 if step in [3, 7, 11, 15] else 0
                        t_on = bar_tick + (step * 120) + swing
                        drums_events.append({"time": t_on, "msg": mido.Message('note_on', channel=9, note=42, velocity=90, time=0)})
                        drums_events.append({"time": t_on + 60, "msg": mido.Message('note_off', channel=9, note=42, velocity=0, time=0)})

        bar_offset += bars

    # Sort & process tracks into delta-time sequences
    def add_events_to_track(events: List[Dict], track: mido.MidiTrack):
        events.sort(key=lambda x: x["time"])
        last_t = 0
        for ev in events:
            ev["msg"].time = ev["time"] - last_t
            track.append(ev["msg"])
            last_t = ev["time"]

    add_events_to_track(rhodes_events, tr_rhodes)
    add_events_to_track(strings_events, tr_strings)
    add_events_to_track(bass_events, tr_bass)
    add_events_to_track(arp_events, tr_arp)
    add_events_to_track(drums_events, tr_drums)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    total_bars = sum(s["bars"] for s in SECTIONS)
    total_sec = (total_bars * 4 * (60.0 / BPM))
    print(f"[Full Song Engine] Generated '{output_path}': {total_bars} Bars ({int(total_sec // 60)}m {int(total_sec % 60)}s at {BPM} BPM)")
    return output_path

# -----------------------------------------------------------------------------
# FL Studio Full Song Piano Roll Script Generator
# -----------------------------------------------------------------------------
def generate_fl_full_song_piano_roll_script(output_path: str) -> str:
    code = """# name = Full Song Master Generator (Satin x Maceo x AIR)
# author = Antigravity C5-REAL AI

import utils

def createScore():
    score.clear()
    
    # 144-Bar Structured Composition Engine
    # Penrose Stair Chords: Abmaj7 -> Bb9 -> Cm9 -> Fm9
    penrose_chords = [
        [56, 60, 63, 67], # Abmaj7
        [58, 62, 65, 70], # Bb9
        [60, 63, 67, 70], # Cm9
        [53, 56, 60, 63], # Fm9
    ]
    
    picardy_chords = [
        [60, 64, 67, 71], # Cmaj9
        [53, 57, 60, 64], # Fmaj9
    ]

    # Generate 144 Bars of full progression score
    total_bars = 144
    ticks_per_bar = 1920

    for bar in range(total_bars):
        start_tick = bar * ticks_per_bar
        
        # Section 6 (Bars 96 to 103): False Drop Picardy Shift
        if 96 <= bar < 104:
            notes = picardy_chords[bar % len(picardy_chords)]
            vel = 0.90
        else:
            notes = penrose_chords[bar % len(penrose_chords)]
            vel = 0.78 if (bar < 32 or (80 <= bar < 96)) else 0.86

        for n in notes:
            note = utils.Note()
            note.number = n
            note.time = start_tick
            note.length = ticks_per_bar - 30
            note.velocity = vel
            score.addNote(note)
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    return output_path

if __name__ == "__main__":
    out_midi = os.path.join(SAMPLES_DIR, "Satin_Maceo_AIR_Full_Song_Master.mid")
    generate_full_song_midi(out_midi)
    
    out_fl_script = os.path.join(FL_SCRIPTS_DIR, "Full_Song_Satin_Maceo_AIR.py")
    generate_fl_full_song_piano_roll_script(out_fl_script)
