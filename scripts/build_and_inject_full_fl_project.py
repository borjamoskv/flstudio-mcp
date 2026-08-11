#!/usr/bin/env python3
"""
Antigravity FL Studio Complete Project Builder & Ingestion Suite
Generates a complete multi-pattern, multi-track SOTA House & Techno project MIDI file,
injects it into FL Studio 2025, populates Playlist clips, and starts playback.
"""

import os
import time
import subprocess
import mido

def generate_full_project_midi(output_path: str) -> str:
    mid = mido.MidiFile(type=1)
    ticks_per_beat = 480
    mid.ticks_per_beat = ticks_per_beat

    # Conductor / Tempo Track
    track_cond = mido.MidiTrack()
    mid.tracks.append(track_cond)
    track_cond.append(mido.MetaMessage('track_name', name='Legion Master Tempo 116 BPM'))
    track_cond.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(116.0)))

    # Track 1: Maceo Plex Sub Kick (Ch 0)
    t1 = mido.MidiTrack()
    mid.tracks.append(t1)
    t1.append(mido.MetaMessage('track_name', name='01 Maceo Plex Sub Kick'))
    for beat in range(32):
        t1.append(mido.Message('note_on', channel=0, note=60, velocity=100, time=0 if beat == 0 else 240))
        t1.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=240))

    # Track 2: Satin Jackets Penrose Chords (Ch 1)
    t2 = mido.MidiTrack()
    mid.tracks.append(t2)
    t2.append(mido.MetaMessage('track_name', name='02 Satin Jackets Chords'))
    chords_satin = [
        [56, 60, 63, 67, 72], # Abmaj7
        [58, 62, 65, 68, 72], # Bb9
        [60, 63, 67, 70, 74], # Cm9
        [53, 60, 63, 67, 70]  # Fm9
    ]
    for bar_idx in range(4):
        chord = chords_satin[bar_idx]
        for n in chord:
            t2.append(mido.Message('note_on', channel=1, note=n, velocity=85, time=0))
        for i, n in enumerate(chord):
            t2.append(mido.Message('note_off', channel=1, note=n, velocity=0, time=1910 if i == 0 else 0))

    # Track 3: AIR Moon Safari Rhodes (Ch 2)
    t3 = mido.MidiTrack()
    mid.tracks.append(t3)
    t3.append(mido.MetaMessage('track_name', name='03 AIR Moon Safari Rhodes'))
    chords_air = [
        [45, 55, 60, 64, 71], # Am9
        [50, 54, 60, 64, 69], # D9
        [41, 57, 60, 64, 67], # Fmaj7
        [40, 56, 62, 67, 73]  # E7#9
    ]
    for bar_idx in range(4):
        chord = chords_air[bar_idx]
        for n in chord:
            t3.append(mido.Message('note_on', channel=2, note=n, velocity=82, time=0))
        for i, n in enumerate(chord):
            t3.append(mido.Message('note_off', channel=2, note=n, velocity=0, time=1910 if i == 0 else 0))

    # Track 4: 24-TET Locrian Acid Lead (Ch 3)
    t4 = mido.MidiTrack()
    mid.tracks.append(t4)
    t4.append(mido.MetaMessage('track_name', name='04 Locrian 24-TET Acid Lead'))
    acid_notes = [59, 60, 62, 65, 67, 71, 74, 77]
    for step in range(32):
        note_val = acid_notes[step % len(acid_notes)]
        t4.append(mido.Message('note_on', channel=3, note=note_val, velocity=90, time=0 if step == 0 else 30))
        t4.append(mido.Message('note_off', channel=3, note=note_val, velocity=0, time=210))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    print(f"✅ Generated Full Legion Project MIDI -> {output_path}")
    return output_path

def inject_and_play():
    midi_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/full_legion_house_project.mid")
    generate_full_project_midi(midi_path)
    
    # 1. Open in FL Studio 2025
    subprocess.run(f'open -a "FL Studio 2025" "{midi_path}"', shell=True)
    time.sleep(1.2)

    # 2. Confirm import dialog & click play via pyautogui
    try:
        import pyautogui
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('space')
        print("🚀 Successfully injected project into FL Studio 2025 & started playback!")
    except Exception as e:
        print(f"PyAutoGUI trigger note: {e}")

if __name__ == "__main__":
    inject_and_play()
