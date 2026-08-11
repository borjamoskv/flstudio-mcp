#!/usr/bin/env python3
"""
Antigravity Algorithmic Music & Signal Engine for FL Studio MCP
Generates harmonic progressions, basslines, spectral analysis, and sidechain automation curves.
"""

import math
import random
import os
import mido
from typing import List, Dict, Tuple

# Key Scale Definitions (Intervals in semitones)
SCALES = {
    "minor": [0, 2, 3, 5, 7, 8, 10],         # Natural Minor
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11], # Harmonic Minor
    "dorian": [0, 2, 3, 5, 7, 9, 10],         # Dorian
    "phrygian": [0, 1, 3, 5, 7, 8, 10],       # Phrygian
    "major": [0, 2, 4, 5, 7, 9, 11]          # Major
}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def note_name_to_midi(name: str, octave: int = 4) -> int:
    name_clean = name.strip().capitalize()
    if name_clean in NOTE_NAMES:
        idx = NOTE_NAMES.index(name_clean)
        return (octave + 1) * 12 + idx
    return 60  # C4 default

def generate_chord_progression_midi(
    output_path: str,
    key_root: str = "C",
    scale_type: str = "minor",
    progression: List[int] = [1, 7, 6, 5],  # i - VII - VI - v (e.g., Cm - Bb - Ab - Gm)
    octave: int = 4,
    bpm: float = 116.0,
    length_bars: int = 4
) -> str:
    """
    Generates a MIDI file containing sophisticated 7th/9th chord voicings for the given progression.
    """
    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('track_name', name=f'Chords {key_root} {scale_type}'))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    root_midi = note_name_to_midi(key_root, octave)
    scale_intervals = SCALES.get(scale_type, SCALES["minor"])

    ticks_per_bar = ticks_per_beat * 4
    ticks_per_chord = (ticks_per_bar * length_bars) // len(progression)

    for degree in progression:
        deg_idx = (degree - 1) % len(scale_intervals)
        chord_root = root_midi + scale_intervals[deg_idx]
        
        # Build 7th/9th Voicing (Root, 3rd, 5th, 7th, 9th)
        voicing = [
            chord_root,
            chord_root + scale_intervals[(deg_idx + 2) % len(scale_intervals)] + (12 if deg_idx + 2 >= len(scale_intervals) else 0),
            chord_root + scale_intervals[(deg_idx + 4) % len(scale_intervals)] + (12 if deg_idx + 4 >= len(scale_intervals) else 0),
            chord_root + scale_intervals[(deg_idx + 6) % len(scale_intervals)] + (12 if deg_idx + 6 >= len(scale_intervals) else 0),
        ]

        # Add note_ons
        first = True
        for n in voicing:
            vel = random.randint(78, 92)
            track.append(mido.Message('note_on', note=n, velocity=vel, time=0 if not first else ticks_per_chord // 8))
            first = False

        # Add note_offs
        first = True
        for n in voicing:
            track.append(mido.Message('note_off', note=n, velocity=0, time=0 if not first else (ticks_per_chord * 7) // 8))
            first = False

    mid.save(output_path)
    return output_path

def generate_sub_bassline_midi(
    output_path: str,
    key_root: str = "C",
    scale_type: str = "minor",
    progression: List[int] = [1, 7, 6, 5],
    octave: int = 1,
    bpm: float = 116.0
) -> str:
    """
    Generates a syncopated Minimal/Dub sub bassline MIDI file aligned with the chord progression.
    """
    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('track_name', name=f'Sub Bass {key_root}'))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    root_midi = note_name_to_midi(key_root, octave)
    scale_intervals = SCALES.get(scale_type, SCALES["minor"])

    for degree in progression:
        deg_idx = (degree - 1) % len(scale_intervals)
        note_val = root_midi + scale_intervals[deg_idx]

        # Syncopated rhythm: Onbeat + Offbeat pulse
        # Note on 1 (quarter note)
        track.append(mido.Message('note_on', note=note_val, velocity=105, time=60))
        track.append(mido.Message('note_off', note=note_val, velocity=0, time=360))

        # Offbeat syncopation (and of 2)
        track.append(mido.Message('note_on', note=note_val, velocity=95, time=480))
        track.append(mido.Message('note_off', note=note_val, velocity=0, time=480))

        # Octave jump on beat 4
        track.append(mido.Message('note_on', note=note_val + 12, velocity=85, time=240))
        track.append(mido.Message('note_off', note=note_val + 12, velocity=0, time=240))

    mid.save(output_path)
    return output_path
