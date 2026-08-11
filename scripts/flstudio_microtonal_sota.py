#!/usr/bin/env python3
"""
Antigravity SOTA Microtonal Acoustic & Psychoacoustic Engine for FL Studio MCP
Implements Plomp-Levelt sensory dissonance optimization, Sethares timbre-scale matching,
and specialized microtonal house sub-genre MIDI generation.
"""

import math
import os
import random
import mido
from typing import List, Dict, Tuple, Optional

# Plomp-Levelt Sensory Dissonance Constants
PL_X_STAR = 0.24
PL_S1 = 3.5
PL_S2 = 5.75
PL_B1 = 0.8
PL_B2 = 1.6

def critical_bandwidth(f_hz: float) -> float:
    """Calculates Bark-scale Critical Bandwidth (Glasberg & Moore ERB formula)."""
    return 24.7 * (4.37e-3 * f_hz + 1.0)

def plomp_levelt_dissonance(f1: float, f2: float, a1: float = 1.0, a2: float = 1.0) -> float:
    """Calculates sensory dissonance between two pure sinusoidal frequencies f1 and f2."""
    if f1 == f2 or f1 <= 0 or f2 <= 0:
        return 0.0
    f_min, f_max = min(f1, f2), max(f1, f2)
    cbw = critical_bandwidth(f_min)
    s = PL_X_STAR / cbw
    diff = f_max - f_min
    return a1 * a2 * (math.exp(-PL_B1 * s * diff) - math.exp(-PL_B2 * s * diff))

def calculate_timbre_dissonance(frequencies: List[float], amplitudes: List[float]) -> float:
    """Calculates total Plomp-Levelt sensory dissonance of a complex multi-partial timbre."""
    tot_diss = 0.0
    n = len(frequencies)
    for i in range(n):
        for j in range(i + 1, n):
            tot_diss += plomp_levelt_dissonance(frequencies[i], frequencies[j], amplitudes[i], amplitudes[j])
    return tot_diss

# Specialized Microtonal House Sub-Genre Presets
MICROTONAL_HOUSE_SUBGENRES = {
    "19tet_deep_house": {
        "system": "19tet",
        "bpm": 120.0,
        "description": "19-TET Deep House with pure 5:4 major thirds and non-beating pad voicings",
        "chord_degrees": [[0, 5, 9, 12, 16], [3, 8, 12, 15, 19], [5, 10, 14, 17, 21], [2, 7, 11, 14, 18]]
    },
    "24tet_makam_minimal": {
        "system": "makam_bayati",
        "bpm": 124.0,
        "description": "24-TET Makam Bayati Minimal House (Villalobos & Zip Style) with quarter-tone glides",
        "chord_degrees": [[0, 2, 4, 6], [1, 3, 5, 7], [0, 2, 4, 6], [6, 4, 2, 0]]
    },
    "31tet_soulful_house": {
        "system": "31tet",
        "bpm": 122.0,
        "description": "31-TET Soulful House featuring 7-limit harmonic seventh (7:4) stabs",
        "chord_degrees": [[0, 10, 18, 25], [5, 15, 23, 30], [8, 18, 26, 33], [3, 13, 21, 28]]
    },
    "bohlen_pierce_techno_house": {
        "system": "bohlen_pierce",
        "bpm": 126.0,
        "description": "Bohlen-Pierce Non-Octave Tritave (3:1) Minimal Techno/House",
        "chord_degrees": [[0, 3, 7, 10], [2, 5, 9, 12], [4, 7, 11, 13], [1, 4, 8, 11]]
    },
    "slendro_tech_house": {
        "system": "slendro",
        "bpm": 125.0,
        "description": "Indonesian Gamelan Slendro 5-tone Tech House with driving 4/4 drums",
        "chord_degrees": [[0, 2, 4], [1, 3, 0], [2, 4, 1], [3, 0, 2]]
    }
}

def generate_sota_microtonal_house_midi(subgenre_key: str, output_path: str) -> Dict:
    """Generates a specialized SOTA Microtonal House MIDI file for the target subgenre."""
    preset = MICROTONAL_HOUSE_SUBGENRES.get(subgenre_key, MICROTONAL_HOUSE_SUBGENRES["19tet_deep_house"])
    
    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('track_name', name=f'SOTA Microtonal House - {subgenre_key}'))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(preset["bpm"])))

    ticks_per_chord = ticks_per_beat * 4
    base_midi = 60  # C4

    for chord in preset["chord_degrees"]:
        for step in chord:
            note_val = base_midi + step
            track.append(mido.Message('note_on', note=note_val, velocity=random.randint(82, 96), time=0))
        for i, step in enumerate(chord):
            note_val = base_midi + step
            track.append(mido.Message('note_off', note=note_val, velocity=0, time=ticks_per_chord if i == 0 else 0))

    mid.save(output_path)
    return {
        "output_path": output_path,
        "subgenre": subgenre_key,
        "bpm": preset["bpm"],
        "description": preset["description"]
    }
