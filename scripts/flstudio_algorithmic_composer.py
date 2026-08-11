#!/usr/bin/env python3
"""
Antigravity Algorithmic Music & Signal Engine for FL Studio MCP
Generates harmonic progressions, basslines, reference song style matching, 100-agent polyrhythms, and sidechain automation curves.
"""

import math
import random
import os
import mido
from typing import List, Dict, Tuple, Optional

# Key Scale Definitions (Intervals in semitones)
SCALES = {
    "minor": [0, 2, 3, 5, 7, 8, 10],         # Natural Minor
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11], # Harmonic Minor
    "dorian": [0, 2, 3, 5, 7, 9, 10],         # Dorian
    "phrygian": [0, 1, 3, 5, 7, 8, 10],       # Phrygian
    "major": [0, 2, 4, 5, 7, 9, 11]          # Major
}

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Reference Song Style Profiles
REFERENCE_STYLES = {
    "satin_jackets": {
        "bpm": 116.0,
        "key_root": "C",
        "scale": "minor",
        "description": "Nu-Disco / Lush Chords / Penrose Stair progression (Abmaj7 -> Bb9 -> Cm9 -> Fm9)",
        "chords": [[56, 60, 63, 67, 72], [58, 62, 65, 68, 72], [60, 63, 67, 70, 74], [53, 60, 63, 67, 70]],
        "swing": 0.0,
        "vibe": "indie_disco"
    },
    "kerri_chandler": {
        "bpm": 122.0,
        "key_root": "F",
        "scale": "minor",
        "description": "Deep House Jersey Sound (MPC 62% swing, organ stabs, raw 909 syncopation)",
        "chords": [[53, 56, 60, 63, 67], [48, 51, 55, 58, 62], [51, 55, 58, 62, 65], [50, 53, 57, 60, 63]],
        "swing": 0.62,
        "vibe": "deep_house"
    },
    "frankie_knuckles": {
        "bpm": 120.0,
        "key_root": "C",
        "scale": "major",
        "description": "Chicago Soulful House (Emotional 7th chords, driving 707 bass, warm synth pads)",
        "chords": [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 65]],
        "swing": 0.54,
        "vibe": "chicago_house"
    },
    "ricardo_villalobos": {
        "bpm": 125.0,
        "key_root": "D",
        "scale": "phrygian",
        "description": "Microtonal Dub Techno / Minimal (24-TET Bayati microtonality, 3/16 echo, polyrhythms)",
        "chords": [[62, 65, 69, 72], [63, 67, 70, 74], [62, 65, 69, 72], [60, 64, 67, 70]],
        "swing": 0.52,
        "vibe": "dub_minimal"
    },
    "fred_again": {
        "bpm": 128.0,
        "key_root": "G",
        "scale": "minor",
        "description": "Emotional UK Garage / House (2-step garage swing, pitch chops, euphoric drop)",
        "chords": [[55, 58, 62, 65, 69], [51, 55, 58, 62, 65], [53, 57, 60, 64], [50, 53, 57, 60]],
        "swing": 0.58,
        "vibe": "uk_garage"
    },
    "air_moon_safari": {
        "bpm": 88.0,
        "key_root": "A",
        "scale": "minor",
        "description": "AIR Moon Safari (Vintage Fender Rhodes/Solina Space-Pop: Am9 -> D9 -> Fmaj7 -> E7#9)",
        "chords": [[45, 55, 60, 64, 71], [50, 54, 60, 64, 69], [41, 57, 60, 64, 67], [40, 56, 62, 67, 73]],
        "swing": 0.54,
        "vibe": "french_downtempo"
    },
    "maceo_plex": {
        "bpm": 124.0,
        "key_root": "A",
        "scale": "minor",
        "description": "Maceo Plex Melodic Techno (Dark analog sub-kick, 50Hz fundamental, 16th sub-rumble)",
        "chords": [[45, 57, 60, 64, 69], [43, 55, 58, 62, 67], [41, 53, 57, 60, 65], [40, 52, 56, 59, 64]],
        "swing": 0.52,
        "vibe": "melodic_techno"
    }
}



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
    progression: List[int] = [1, 7, 6, 5],
    octave: int = 4,
    bpm: float = 116.0,
    length_bars: int = 4
) -> str:
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
        
        voicing = [
            chord_root,
            chord_root + scale_intervals[(deg_idx + 2) % len(scale_intervals)] + (12 if deg_idx + 2 >= len(scale_intervals) else 0),
            chord_root + scale_intervals[(deg_idx + 4) % len(scale_intervals)] + (12 if deg_idx + 4 >= len(scale_intervals) else 0),
            chord_root + scale_intervals[(deg_idx + 6) % len(scale_intervals)] + (12 if deg_idx + 6 >= len(scale_intervals) else 0),
        ]

        first = True
        for n in voicing:
            vel = random.randint(78, 92)
            track.append(mido.Message('note_on', note=n, velocity=vel, time=0 if not first else ticks_per_chord // 8))
            first = False

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

        track.append(mido.Message('note_on', note=note_val, velocity=105, time=60))
        track.append(mido.Message('note_off', note=note_val, velocity=0, time=360))

        track.append(mido.Message('note_on', note=note_val, velocity=95, time=480))
        track.append(mido.Message('note_off', note=note_val, velocity=0, time=480))

        track.append(mido.Message('note_on', note=note_val + 12, velocity=85, time=240))
        track.append(mido.Message('note_off', note=note_val + 12, velocity=0, time=240))

    mid.save(output_path)
    return output_path


def generate_reference_style_midi(reference_name: str, output_path: str, bpm: Optional[float] = None) -> Dict:
    """
    Generates a MIDI file matching the signature harmonic, rhythmic, and arrangement style of a reference track.
    """
    ref_key = reference_name.lower().replace(" ", "_")
    profile = REFERENCE_STYLES.get(ref_key, REFERENCE_STYLES["satin_jackets"])
    
    target_bpm = bpm if bpm is not None else profile["bpm"]
    chords = profile["chords"]

    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('track_name', name=f'Reference Style - {reference_name}'))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(target_bpm)))

    ticks_per_chord = ticks_per_beat * 4  # 1 Bar per chord

    for chord in chords:
        for n in chord:
            track.append(mido.Message('note_on', note=n, velocity=random.randint(80, 95), time=0))
        for i, n in enumerate(chord):
            track.append(mido.Message('note_off', note=n, velocity=0, time=ticks_per_chord if i == 0 else 0))

    mid.save(output_path)
    return {
        "output_path": output_path,
        "style": profile["description"],
        "bpm": target_bpm,
        "key": profile["key_root"],
        "swing": profile["swing"]
    }


def generate_100_agents_polyrhythm_midi(output_path: str, bpm: float = 116.0) -> str:
    """
    Generates a 100-Agent polyrhythmic swarm matrix MIDI file.
    """
    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage('track_name', name='100-Agent Polyrhythmic Matrix'))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    total_ticks = ticks_per_beat * 16  # 4 Bars
    num_agents = 100
    scale_pitches = [36, 48, 51, 55, 60, 63, 67, 70, 72, 75, 79, 82, 84]

    events = []

    for agent_id in range(num_agents):
        divisions = [3, 4, 5, 7, 9, 11]
        div = divisions[agent_id % len(divisions)]
        pulse_period = total_ticks / (div * 4)
        pitch = scale_pitches[agent_id % len(scale_pitches)]
        phase_shift = int((agent_id * 17) % pulse_period)

        step = 0
        while True:
            note_time = int(step * pulse_period + phase_shift)
            if note_time >= total_ticks:
                break
            note_len = int(pulse_period * 0.45)
            vel_mod = int(40 + 70 * (0.5 + 0.4 * math.sin((agent_id * 0.1) + (step * 0.3))))
            
            events.append({"time": note_time, "type": "note_on", "pitch": pitch, "vel": max(30, min(127, vel_mod))})
            events.append({"time": note_time + note_len, "type": "note_off", "pitch": pitch, "vel": 0})
            step += 1

    events.sort(key=lambda x: x["time"])

    last_time = 0
    for ev in events:
        delta = ev["time"] - last_time
        track.append(mido.Message(ev["type"], note=ev["pitch"], velocity=ev["vel"], time=delta))
        last_time = ev["time"]

    mid.save(output_path)
    return output_path
