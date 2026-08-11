#!/usr/bin/env python3
"""
Infinite Harmonic Loop Generator ('Satin Jackets / What a Girl to Do' Effect)
Implements a non-resolving 8-bar Penrose Stair chord progression in C minor:
VImaj7 (Abmaj7) ---> VII9 (Bb9) ---> i9 (Cm9 - Second-to-last tonic) ---> iv9 (Fm9 - Unresolved suspension)

This creates the hypnotic, never-ending infinite cycle where the tonic note/chord lands on the penultimate bar,
forcing the ear into a continuous circular momentum.
"""

import sys
import os
import mido

OUTPUT_PATH = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/satin_jackets_infinite_loop.mid")

def generate_satin_jackets_infinite_loop(output_path=OUTPUT_PATH, bpm=116.0):
    ticks_per_beat = 480
    mid = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)

    # Conductor track
    track_cond = mido.MidiTrack()
    mid.tracks.append(track_cond)
    track_cond.append(mido.MetaMessage('track_name', name='Satin Jackets Infinite Loop Conductor'))
    track_cond.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # Chord track (Chords with 7th/9th extensions)
    track_chords = mido.MidiTrack()
    mid.tracks.append(track_chords)
    track_chords.append(mido.MetaMessage('track_name', name='Infinite Harmonic Chords'))

    # Progression in C minor (8 Bars = 32 Beats)
    # Chord 1: Abmaj7 (Bar 1-2, Beats 0-8)
    # Chord 2: Bb9    (Bar 3-4, Beats 8-16)
    # Chord 3: Cm9    (Bar 5-6, Beats 16-24) -> Penultimate Tonic Arrival!
    # Chord 4: Fm9    (Bar 7-8, Beats 24-32) -> Unresolved Suspension leading back to Abmaj7

    CHORD_SEQUENCE = [
        # (name, notes, duration_in_beats)
        ("Abmaj7 (VImaj7)", [56, 60, 63, 67, 72], 8),      # Ab3, C4, Eb4, G4, C5
        ("Bb9 (VII9)",      [58, 62, 65, 68, 72], 8),      # Bb3, D4, F4, Ab4, C5
        ("Cm9 (i9 Penultimate Tonic)", [60, 63, 67, 70, 74], 8), # C4, Eb4, G4, Bb4, D5 (Tonic on 2nd-to-last!)
        ("Fm9 (iv9 Unresolved Susp)",  [53, 60, 63, 67, 70], 8)  # F3, C4, Eb4, G4, Bb4
    ]

    for name, chord_notes, beats in CHORD_SEQUENCE:
        duration_ticks = ticks_per_beat * beats
        # Note On for all notes in chord
        for idx, note in enumerate(chord_notes):
            time_offset = 0 if idx > 0 else 0
            track_chords.append(mido.Message('note_on', channel=0, note=note, velocity=88 + (idx*3), time=time_offset))
        
        # Note Off for all notes at end of duration
        for idx, note in enumerate(chord_notes):
            time_offset = duration_ticks if idx == 0 else 0
            track_chords.append(mido.Message('note_off', channel=0, note=note, velocity=0, time=time_offset))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    print(f"[Infinite Harmonic Loop] Saved 'Satin Jackets' Penrose Stair MIDI -> {output_path}")
    return output_path

if __name__ == "__main__":
    generate_satin_jackets_infinite_loop()
