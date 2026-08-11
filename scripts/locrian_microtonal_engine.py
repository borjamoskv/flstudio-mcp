#!/usr/bin/env python3
"""
Antigravity SOTA Locrian & Xenharmonic Techno Engine
Implements 24-TET Quarter-Tone Neutral Locrian, Locrian Natural 6, and Super-Locrian (Altered Scale) multi-layer patterns.
"""

import math
import random
import os
import mido

def generate_locrian_sota_suite(output_path: str, bpm: float = 125.0) -> str:
    """
    Generates a 3-track SOTA Locrian Techno MIDI arrangement:
    1. Acid Sub-Tritone Riff (Locrian b5 Drive)
    2. 24-TET Neutral-2nd Arpeggiator (Exotic Sci-Fi Tension)
    3. Super-Locrian Altered Stab Chords
    """
    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    # Track 1: Acid Sub-Tritone Bassline (Channel 0)
    track_bass = mido.MidiTrack()
    mid.tracks.append(track_bass)
    track_bass.append(mido.MetaMessage('track_name', name='Acid Locrian Bass (b5 Tritone)'))
    track_bass.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # Locrian Acid Riff (16th-notes)
    # B (35), C (36), D (38), F (41 - b5 tritone accent)
    bass_pattern = [
        (35, 120, 110), (35, 120, 85), (36, 120, 95), (41, 120, 120),  # Bar 1 beat 1
        (35, 120, 100), (38, 120, 90), (41, 120, 115), (36, 120, 85),
        (35, 120, 110), (41, 120, 125), (38, 120, 90), (35, 120, 100),
        (36, 120, 95), (41, 120, 120), (38, 120, 90), (35, 120, 80)
    ]

    last_t = 0
    total_t = 0
    for bar in range(2):  # 2 Bars loop
        for note_val, dur, vel in bass_pattern:
            delta = total_t - last_t
            track_bass.append(mido.Message('note_on', channel=0, note=note_val, velocity=vel, time=delta))
            track_bass.append(mido.Message('note_off', channel=0, note=note_val, velocity=0, time=dur - 15))
            last_t = total_t + (dur - 15)
            total_t += dur

    # Track 2: 24-TET Neutral-2nd Arp (Channel 1)
    track_arp = mido.MidiTrack()
    mid.tracks.append(track_arp)
    track_arp.append(mido.MetaMessage('track_name', name='24-TET Neutral Locrian Arp'))

    # Arp pattern using sub-cent pitch wheel for neutral 2nd
    arp_notes = [59, 60, 62, 65, 67, 71, 74, 77]
    total_t = 0
    last_t = 0

    for i in range(32):  # 32 8th-note steps
        n = arp_notes[i % len(arp_notes)]
        # Apply 24-TET neutral offset (-50 cents on C / minor 2nd)
        pb_val = -2048 if n == 60 else 0
        
        delta = total_t - last_t
        track_arp.append(mido.Message('pitchwheel', channel=1, pitch=pb_val, time=delta))
        track_arp.append(mido.Message('note_on', channel=1, note=n, velocity=random.randint(85, 105), time=0))
        track_arp.append(mido.Message('note_off', channel=1, note=n, velocity=0, time=220))
        
        last_t = total_t + 220
        total_t += 240

    # Track 3: Super-Locrian Altered Stabs (Channel 2)
    track_stabs = mido.MidiTrack()
    mid.tracks.append(track_stabs)
    track_stabs.append(mido.MetaMessage('track_name', name='Super-Locrian Altered Stabs'))

    stab_chords = [
        {"notes": [59, 62, 65, 68], "t_on": 480},   # Bm7b5
        {"notes": [60, 64, 67, 71], "t_on": 1440},  # Cmaj7
        {"notes": [59, 63, 65, 68], "t_on": 2400},  # B7alt (Super-Locrian)
        {"notes": [57, 60, 64, 67], "t_on": 3360}   # Am7
    ]

    last_t = 0
    for s in stab_chords:
        t_on = s["t_on"]
        delta = t_on - last_t
        for n in s["notes"]:
            track_stabs.append(mido.Message('note_on', channel=2, note=n, velocity=100, time=delta if n == s["notes"][0] else 0))
        for n in s["notes"]:
            track_stabs.append(mido.Message('note_off', channel=2, note=n, velocity=0, time=180 if n == s["notes"][0] else 0))
        last_t = t_on + 180

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    print(f"[Locrian SOTA Engine] Generated Multi-Track MIDI -> {output_path}")
    return output_path

if __name__ == "__main__":
    out_file = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/locrian_sota_techno_suite.mid")
    generate_locrian_sota_suite(out_file)
