#!/usr/bin/env python3
"""
False Drop & Major Scale Euphoric Expansion Generator ('Falso Drop' C minor -> Eb Major / C Major Shift)
Created for 'No Lo Entiende' (Unai Stems Remix at 116 BPM)

Harmonic Architecture:
- Bars 1-4: Tension Build in C minor (Cm9 -> Fm9)
- Bar 4 (Beats 3-4): FALSE DROP SILENCE - Kicks & Bass cut out, Vocal Delay Throws
- Bar 5-8: EUPHORIC MAJOR DROP - Modulation to Eb Major9 (Ebmaj9 -> F9 -> Gm7 -> Cmaj9 Picardy Peak)
  Provides intense emotional contrast between minor dark house tension and major euphoric release.
"""

import sys
import os
import mido

OUTPUT_PATH = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/false_drop_major_expansion.mid")

def generate_false_drop_major_expansion(output_path=OUTPUT_PATH, bpm=116.0):
    ticks_per_beat = 480
    mid = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)

    # Conductor track
    track_cond = mido.MidiTrack()
    mid.tracks.append(track_cond)
    track_cond.append(mido.MetaMessage('track_name', name='False Drop Conductor'))
    track_cond.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # Chord track
    track_chords = mido.MidiTrack()
    mid.tracks.append(track_chords)
    track_chords.append(mido.MetaMessage('track_name', name='False Drop & Major Chords'))

    # Progression (8 Bars = 32 Beats)
    # Section 1: Dark C minor Tension (Bars 1-4)
    # Section 2: False Drop Break (Bar 4 Beat 3-4) -> Muted
    # Section 3: Euphoric Major Expansion (Bars 5-8)

    SEQUENCE = [
        # (name, notes, beats, is_false_drop_break)
        ("Cm9 (Tension)",       [60, 63, 67, 70, 74], 7, False),   # C4, Eb4, G4, Bb4, D5
        ("Fm9 (Pre-Break)",     [53, 60, 63, 67, 70], 7, False),   # F3, C4, Eb4, G4, Bb4
        ("FALSE DROP BREAK",    [],                    2, True),   # SILENCE / Vocal Delay Throw
        ("Ebmaj9 (EUPHORIC MAJOR DROP)", [63, 67, 70, 74, 77], 8, False), # Eb4, G4, Bb4, D5, F5 (Relative Major!)
        ("Cmaj9 (Picardy Third Peak)",   [60, 64, 67, 71, 74], 8, False)  # C4, E4, G4, B4, D5  (Parallel Major Euphoria!)
    ]

    for name, chord_notes, beats, is_break in SEQUENCE:
        duration_ticks = ticks_per_beat * beats
        if is_break:
            # Silence time offset
            track_chords.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=duration_ticks))
        else:
            for idx, note in enumerate(chord_notes):
                time_offset = 0 if idx > 0 else 0
                track_chords.append(mido.Message('note_on', channel=0, note=note, velocity=95 + (idx*2), time=time_offset))
            
            for idx, note in enumerate(chord_notes):
                time_offset = duration_ticks if idx == 0 else 0
                track_chords.append(mido.Message('note_off', channel=0, note=note, velocity=0, time=time_offset))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    print(f"[False Drop Generator] Saved False Drop & Major Expansion MIDI -> {output_path}")
    return output_path

if __name__ == "__main__":
    generate_false_drop_major_expansion()
