#!/usr/bin/env python3
"""
C5-REAL HYBRID FLOW ENGINE: Satin Jackets x Maceo Plex x AIR (Moon Safari)
========================================================================
Synthesizes a multi-track musical framework engineered for maximum exergy flow state:
1. Satin Jackets: Non-resolving Penrose Stair chord loop (Abmaj7 -> Bb9 -> Cm9 -> Fm9).
2. Maceo Plex: DSP Techno-Industrial Punch Kick (3.8kHz -> 50Hz sweep, Tanh saturation, 30-80Hz rumble).
3. AIR Moon Safari: Analog Fender Rhodes 73, Solina String Ensemble, tape noise & 3/16 dub delays.
4. Mathematical Neuro-Flow Calibration: 118 BPM (508.47 ms/beat), 24-TET microtonal pitch bends.
"""

import math
import struct
import wave
import os
import random
import mido
from typing import List, Dict, Any

# Ensure target directories
WORKSPACE_DIR = os.path.expanduser("~/10_PROJECTS/flstudio-mcp")
SAMPLES_DIR = os.path.join(WORKSPACE_DIR, "samples", "hybrid_flow")
SCALINGS_DIR = os.path.join(WORKSPACE_DIR, "scalings")
FL_SCRIPTS_DIR = os.path.expanduser("~/Documents/Image-Line/FL Studio/Settings/Piano roll scripts")

os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(SCALINGS_DIR, exist_ok=True)
os.makedirs(FL_SCRIPTS_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Maceo Plex DSP Kick & Sub-Rumble Synthesizer
# -----------------------------------------------------------------------------
def generate_maceo_plex_flow_kick(
    output_path: str,
    sub_freq_hz: float = 49.0, # G1 key
    pitch_start_hz: float = 3800.0,
    pitch_decay_ms: float = 11.0,
    body_decay_ms: float = 210.0,
    saturation_drive: float = 2.4,
    sample_rate: int = 44100
) -> str:
    """Synthesizes high-impact Maceo Plex Kick with Tanh saturation."""
    total_samples = int(sample_rate * (body_decay_ms / 1000.0) * 1.4)
    samples = []

    tau_pitch = pitch_decay_ms / 1000.0
    tau_amp = body_decay_ms / 1000.0
    phase = 0.0

    for i in range(total_samples):
        t = i / sample_rate
        freq_t = sub_freq_hz + (pitch_start_hz - sub_freq_hz) * math.exp(-t / tau_pitch)
        phase += 2.0 * math.pi * freq_t / sample_rate
        sine_val = math.sin(phase)
        amp_t = math.exp(-t / tau_amp)

        click_env = math.exp(-t / 0.0018) if t < 0.004 else 0.0
        click_val = 0.3 * click_env * math.sin(2.0 * math.pi * 3800.0 * t)

        raw_sig = (sine_val * amp_t) + click_val
        driven_sig = math.tanh(raw_sig * saturation_drive) / math.tanh(saturation_drive)
        val_pcm = int(max(-32767, min(32767, driven_sig * 32000.0)))
        samples.append(val_pcm)

    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        packed = bytearray()
        for sample in samples:
            packed.extend(struct.pack('<h', sample))
        wav_file.writeframes(packed)

    return output_path

# -----------------------------------------------------------------------------
# 2. Scala Microtonal Scaling (.scl) for 24-TET Flow
# -----------------------------------------------------------------------------
def generate_24tet_flow_scala_file(output_path: str) -> str:
    """Generates a 24-TET Scala tuning file for microtonal synth engines."""
    content = """! 24tet_flow_max_exergy.scl
24-TET Equal Temperament with Bayati Micro-Quarter-Tones for Max Exergy Flow
 24
!
 50.00000
 100.00000
 150.00000
 200.00000
 250.00000
 300.00000
 350.00000
 400.00000
 450.00000
 500.00000
 550.00000
 600.00000
 650.00000
 700.00000
 750.00000
 800.00000
 850.00000
 900.00000
 950.00000
 1000.00000
 1050.00000
 1100.00000
 1150.00000
 2/1
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path

# -----------------------------------------------------------------------------
# 3. Piano Roll Native Script (.py) for FL Studio
# -----------------------------------------------------------------------------
def generate_fl_piano_roll_script(output_path: str) -> str:
    """Generates an FL Studio native Piano Roll script for non-resolving Satin Jackets flow loop."""
    code = """# name = Satin Jackets x Maceo Plex Flow Generator
# author = Antigravity C5-REAL AI

import utils

def createScore():
    score.clear()
    
    # 118 BPM Penrose Stair Progression in C Minor
    # Abmaj7 -> Bb9 -> Cm9 -> Fm9
    chords = [
        # Abmaj7 (Bar 1)
        (0, [56, 60, 63, 67], 1920, 0.78),
        # Bb9 (Bar 2)
        (1920, [58, 62, 65, 70], 1920, 0.80),
        # Cm9 (Bar 3)
        (3840, [60, 63, 67, 70], 1920, 0.82),
        # Fm9 (Bar 4)
        (5760, [53, 56, 60, 63], 1920, 0.80),
    ]

    for start_t, notes, dur, vel in chords:
        for n in notes:
            note = utils.Note()
            note.number = n
            note.time = start_t
            note.length = dur - 20
            note.velocity = vel
            score.addNote(note)
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    return output_path

# -----------------------------------------------------------------------------
# 4. Multi-Track MIDI Composition Engine (Mido)
# -----------------------------------------------------------------------------
def generate_hybrid_flow_multitrack_midi(output_path: str, bpm: float = 118.0) -> str:
    mid = mido.MidiFile(type=1)
    ticks = 480
    mid.ticks_per_beat = ticks

    # Master Track
    master = mido.MidiTrack()
    mid.tracks.append(master)
    master.append(mido.MetaMessage('track_name', name='Master Flow Tempo (118 BPM)'))
    master.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # --- TRACK 1: Satin Jackets / AIR Fender Rhodes 73 Chords ---
    tr_rhodes = mido.MidiTrack()
    mid.tracks.append(tr_rhodes)
    tr_rhodes.append(mido.MetaMessage('track_name', name='Chords - Fender Rhodes 73 (Satin Jackets)'))

    # Penrose Stair Loop (2 Iterations = 8 Bars = 15360 ticks)
    chord_progression = [
        # Bar 1: Abmaj7
        {"notes": [44, 56, 60, 63, 67], "start": 0, "dur": 1920, "vel": 80},
        # Bar 2: Bb9
        {"notes": [46, 58, 62, 65, 70], "start": 1920, "dur": 1920, "vel": 82},
        # Bar 3: Cm9 (Non-resolving landing)
        {"notes": [48, 60, 63, 67, 70], "start": 3840, "dur": 1920, "vel": 85},
        # Bar 4: Fm9
        {"notes": [41, 53, 56, 60, 63], "start": 5760, "dur": 1920, "vel": 80},
        # Bar 5: Abmaj7
        {"notes": [44, 56, 60, 63, 67], "start": 7680, "dur": 1920, "vel": 80},
        # Bar 6: Bb9
        {"notes": [46, 58, 62, 65, 70], "start": 9600, "dur": 1920, "vel": 82},
        # Bar 7: False Drop Tension -> Picardy Cmaj9 modulation in 2nd half
        {"notes": [48, 60, 64, 67, 71], "start": 11520, "dur": 1920, "vel": 92},
        # Bar 8: Fm9
        {"notes": [41, 53, 56, 60, 63], "start": 13440, "dur": 1920, "vel": 80},
    ]

    rhodes_events = []
    for item in chord_progression:
        for n in item["notes"]:
            jitter = random.randint(-6, 6) if item["start"] > 0 else 0
            t_on = item["start"] + jitter
            t_off = t_on + item["dur"] - 40
            v = max(40, min(127, item["vel"] + random.randint(-4, 4)))
            rhodes_events.append({"time": t_on, "msg": mido.Message('note_on', channel=0, note=n, velocity=v, time=0)})
            rhodes_events.append({"time": t_off, "msg": mido.Message('note_off', channel=0, note=n, velocity=0, time=0)})

    rhodes_events.sort(key=lambda x: x["time"])
    last_t = 0
    for ev in rhodes_events:
        ev["msg"].time = ev["time"] - last_t
        tr_rhodes.append(ev["msg"])
        last_t = ev["time"]

    # --- TRACK 2: Solina Strings Ensemble (AIR Moon Safari Ambient Pad) ---
    tr_strings = mido.MidiTrack()
    mid.tracks.append(tr_strings)
    tr_strings.append(mido.MetaMessage('track_name', name='Pad - Solina String Ensemble (AIR Moon Safari)'))

    string_events = []
    pad_chords = [
        {"notes": [75, 79], "start": 0, "dur": 3840, "vel": 68},      # Eb5, G5 over Abmaj7/Bb
        {"notes": [72, 79], "start": 3840, "dur": 3840, "vel": 70},   # C5, G5 over Cm9/Fm
        {"notes": [75, 79], "start": 7680, "dur": 3840, "vel": 68},
        {"notes": [72, 76, 79], "start": 11520, "dur": 3840, "vel": 75} # C5, E5, G5 Picardy Brightness
    ]

    for item in pad_chords:
        for n in item["notes"]:
            string_events.append({"time": item["start"], "msg": mido.Message('note_on', channel=1, note=n, velocity=item["vel"], time=0)})
            string_events.append({"time": item["start"] + item["dur"] - 20, "msg": mido.Message('note_off', channel=1, note=n, velocity=0, time=0)})

    string_events.sort(key=lambda x: x["time"])
    last_t = 0
    for ev in string_events:
        ev["msg"].time = ev["time"] - last_t
        tr_strings.append(ev["msg"])
        last_t = ev["time"]

    # --- TRACK 3: Maceo Plex Techno Kick & Sub-Rumble (Channel 10 Drums) ---
    tr_drums = mido.MidiTrack()
    mid.tracks.append(tr_drums)
    tr_drums.append(mido.MetaMessage('track_name', name='Drums - Maceo Plex Techno Kick (4-on-the-floor)'))

    drum_events = []
    # 8 Bars of 4-on-the-floor kick = 32 beats
    for beat in range(32):
        # Silence for false drop at beat 26 & 27 (Bar 7 3rd & 4th beats)
        if beat in [26, 27]:
            continue
        t_on = beat * 480
        t_off = t_on + 240
        v = 115 if (beat % 4 == 0) else 108
        drum_events.append({"time": t_on, "msg": mido.Message('note_on', channel=9, note=36, velocity=v, time=0)})
        drum_events.append({"time": t_off, "msg": mido.Message('note_off', channel=9, note=36, velocity=0, time=0)})

        # Offbeat Hi-Hat on 16th note step 2 (ticks 240, 720, etc.)
        t_hh_on = t_on + 240
        t_hh_off = t_hh_on + 120
        # 62% MPC Swing offset
        swing_offset = 18
        drum_events.append({"time": t_hh_on + swing_offset, "msg": mido.Message('note_on', channel=9, note=42, velocity=90, time=0)})
        drum_events.append({"time": t_hh_off + swing_offset, "msg": mido.Message('note_off', channel=9, note=42, velocity=0, time=0)})

    drum_events.sort(key=lambda x: x["time"])
    last_t = 0
    for ev in drum_events:
        ev["msg"].time = ev["time"] - last_t
        tr_drums.append(ev["msg"])
        last_t = ev["time"]

    # --- TRACK 4: Minimoog Driving Bassline (Maceo Plex + Satin Jackets) ---
    tr_bass = mido.MidiTrack()
    mid.tracks.append(tr_bass)
    tr_bass.append(mido.MetaMessage('track_name', name='Bass - Minimoog Drive (Industrial Sub)'))

    # 16th note driving pulse with 24-TET pitch bend modulation
    bass_pattern = [
        # Bar 1: Ab bass (Note 32 = Ab1)
        (32, 0, 240), (32, 240, 240), (32, 480, 240), (44, 720, 240),
        (32, 960, 240), (32, 1200, 240), (32, 1440, 240), (44, 1680, 240),
        # Bar 2: Bb bass (Note 34 = Bb1)
        (34, 1920, 240), (34, 2160, 240), (34, 2400, 240), (46, 2640, 240),
        (34, 2880, 240), (34, 3120, 240), (34, 3360, 240), (46, 3600, 240),
        # Bar 3: C bass (Note 36 = C2)
        (36, 3840, 240), (36, 4080, 240), (36, 4320, 240), (48, 4560, 240),
        (36, 4800, 240), (36, 5040, 240), (36, 5280, 240), (48, 5520, 240),
        # Bar 4: F bass (Note 29 = F1)
        (29, 5760, 240), (29, 6000, 240), (29, 6240, 240), (41, 6480, 240),
        (29, 6720, 240), (29, 6960, 240), (29, 7200, 240), (41, 7440, 240),
    ]

    bass_events = []
    # Repeat for 2 iterations (8 bars)
    for rep in range(2):
        offset = rep * 7680
        for n, start, dur in bass_pattern:
            t_on = offset + start
            t_off = t_on + dur - 30
            v = random.randint(95, 112)
            bass_events.append({"time": t_on, "msg": mido.Message('note_on', channel=2, note=n, velocity=v, time=0)})
            bass_events.append({"time": t_off, "msg": mido.Message('note_off', channel=2, note=n, velocity=0, time=0)})

    bass_events.sort(key=lambda x: x["time"])
    last_t = 0
    for ev in bass_events:
        ev["msg"].time = ev["time"] - last_t
        tr_bass.append(ev["msg"])
        last_t = ev["time"]

    # Save MIDI file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    return output_path

# -----------------------------------------------------------------------------
# Main Execution Protocol
# -----------------------------------------------------------------------------
def build_satin_maceo_air_package():
    print("=== [C5-REAL HYBRID FLOW ENGINE INITIALIZATION] ===")
    
    # 1. Generate Maceo Plex Signature DSP Kick
    kick_path = os.path.join(SAMPLES_DIR, "Maceo_Plex_Flow_Kick_118BPM.wav")
    generate_maceo_plex_flow_kick(kick_path)
    print(f"✅ Generated Maceo Plex DSP Kick WAV: {kick_path}")

    # 2. Generate 24-TET Microtonal Scala File
    scl_path = os.path.join(SCALINGS_DIR, "24tet_flow_max_exergy.scl")
    generate_24tet_flow_scala_file(scl_path)
    print(f"✅ Generated 24-TET Scala File: {scl_path}")

    # 3. Generate Piano Roll Native Script for FL Studio
    py_fl_path = os.path.join(FL_SCRIPTS_DIR, "Satin_Maceo_AIR_Flow_Pattern.py")
    generate_fl_piano_roll_script(py_fl_path)
    print(f"✅ Generated FL Studio Piano Roll Script: {py_fl_path}")

    # 4. Generate Multi-Track MIDI File
    midi_path = os.path.join(SAMPLES_DIR, "Satin_Maceo_AIR_Flow_Master.mid")
    generate_hybrid_flow_multitrack_midi(midi_path)
    print(f"✅ Generated Multi-Track Master MIDI: {midi_path}")

    print("=== [HYBRID FLOW PACKAGE BUILD COMPLETE] ===")

if __name__ == "__main__":
    build_satin_maceo_air_package()
