#!/usr/bin/env python3
"""
Antigravity AIR Moon Safari Space-Pop Multi-Track Engine
Generates a complete multi-track MIDI arrangement featuring:
1. Fender Rhodes Chords (Am9 -> D9 -> Fmaj7 -> E7#9) with humanized micro-timing.
2. Minimoog Melodic Bassline (Counterpoint, staccato + legato).
3. Solina String Ensemble (High ethereal pad).
"""

import math
import random
import os
import mido

def generate_air_moon_safari_multitrack(output_path: str, bpm: float = 88.0) -> str:
    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    # Master Track
    track_master = mido.MidiTrack()
    mid.tracks.append(track_master)
    track_master.append(mido.MetaMessage('track_name', name='AIR Moon Safari Master'))
    track_master.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # --- TRACK 1: Fender Rhodes Chords ---
    track_rhodes = mido.MidiTrack()
    mid.tracks.append(track_rhodes)
    track_rhodes.append(mido.MetaMessage('track_name', name='Fender Rhodes (Chords)'))
    
    chords = [
        {"notes": [45, 55, 60, 64, 71], "time_start": 0, "duration": 1920, "vel": 82},     # Am9
        {"notes": [50, 54, 60, 64, 69], "time_start": 1920, "duration": 1920, "vel": 80},  # D9
        {"notes": [41, 57, 60, 64, 67], "time_start": 3840, "duration": 1920, "vel": 84},  # Fmaj7
        {"notes": [40, 56, 62, 67, 73], "time_start": 5760, "duration": 1920, "vel": 86}   # E7(#9)
    ]

    rhodes_events = []
    for c in chords:
        for n in c["notes"]:
            jitter = random.randint(-8, 8) if c["time_start"] > 0 else 0
            t_on = c["time_start"] + jitter
            t_off = t_on + c["duration"] - 60
            v = max(40, min(127, c["vel"] + random.randint(-5, 5)))
            rhodes_events.append({"time": t_on, "msg": mido.Message('note_on', channel=0, note=n, velocity=v, time=0)})
            rhodes_events.append({"time": t_off, "msg": mido.Message('note_off', channel=0, note=n, velocity=0, time=0)})

    rhodes_events.sort(key=lambda x: x["time"])
    last_t = 0
    for ev in rhodes_events:
        delta = ev["time"] - last_t
        ev["msg"].time = delta
        track_rhodes.append(ev["msg"])
        last_t = ev["time"]

    # --- TRACK 2: Minimoog Bassline ---
    track_bass = mido.MidiTrack()
    mid.tracks.append(track_bass)
    track_bass.append(mido.MetaMessage('track_name', name='Minimoog (Bass)'))

    bass_notes = [
        # Am9 -> A walkup
        {"note": 33, "t_on": 0, "dur": 480}, {"note": 40, "t_on": 960, "dur": 240}, {"note": 43, "t_on": 1440, "dur": 240},
        # D9 -> D bounce
        {"note": 38, "t_on": 1920, "dur": 480}, {"note": 45, "t_on": 2880, "dur": 240}, {"note": 42, "t_on": 3360, "dur": 240},
        # Fmaj7 -> F pedal
        {"note": 29, "t_on": 3840, "dur": 960}, {"note": 36, "t_on": 4800, "dur": 480},
        # E7(#9) -> E tension walkdown
        {"note": 28, "t_on": 5760, "dur": 480}, {"note": 40, "t_on": 6720, "dur": 240}, {"note": 38, "t_on": 7200, "dur": 240}
    ]

    bass_events = []
    for b in bass_notes:
        v = random.randint(95, 110)
        bass_events.append({"time": b["t_on"], "msg": mido.Message('note_on', channel=1, note=b["note"], velocity=v, time=0)})
        bass_events.append({"time": b["t_on"] + b["dur"] - 30, "msg": mido.Message('note_off', channel=1, note=b["note"], velocity=0, time=0)})

    bass_events.sort(key=lambda x: x["time"])
    last_t = 0
    for ev in bass_events:
        delta = ev["time"] - last_t
        ev["msg"].time = delta
        track_bass.append(ev["msg"])
        last_t = ev["time"]

    # --- TRACK 3: Solina String Ensemble (High Pads) ---
    track_strings = mido.MidiTrack()
    mid.tracks.append(track_strings)
    track_strings.append(mido.MetaMessage('track_name', name='Solina Strings (Pad)'))

    string_chords = [
        {"notes": [76, 81], "t_on": 0, "dur": 1920},     # E5, A5
        {"notes": [74, 81], "t_on": 1920, "dur": 1920},  # D5, A5
        {"notes": [77, 84], "t_on": 3840, "dur": 1920},  # F5, C6
        {"notes": [73, 80], "t_on": 5760, "dur": 1920}   # C#5, G#5
    ]

    string_events = []
    for s in string_chords:
        for n in s["notes"]:
            string_events.append({"time": s["t_on"], "msg": mido.Message('note_on', channel=2, note=n, velocity=65, time=0)})
            string_events.append({"time": s["t_on"] + s["dur"] - 10, "msg": mido.Message('note_off', channel=2, note=n, velocity=0, time=0)})

    string_events.sort(key=lambda x: x["time"])
    last_t = 0
    for ev in string_events:
        delta = ev["time"] - last_t
        ev["msg"].time = delta
        track_strings.append(ev["msg"])
        last_t = ev["time"]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    print(f"[AIR Moon Safari Engine] Generated Multi-Track MIDI -> {output_path}")
    return output_path

if __name__ == "__main__":
    out_file = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/air_moon_safari_multitrack.mid")
    generate_air_moon_safari_multitrack(out_file)
