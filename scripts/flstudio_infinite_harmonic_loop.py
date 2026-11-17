#!/usr/bin/env python3
"""
Infinite Harmonic Loop Generator ('Satin Jackets / What a Girl to Do' Effect)
=============================================================================
Implements an 8-bar Penrose Stair chord progression in C minor with real structural
expressivity:
  VImaj7 (Abmaj7) -> VII9 (Bb9) -> i9 (Cm9 penultimate tonic) -> iv9 (Fm9)
  + Bar 8 Beat 3-4 False Drop / Picardy Third Turnaround (Cmaj9) + Micro-Strumming
  + Top-Note Melody Emphasis + Filter Brightness CC#74 Breath Envelope.
"""

from pathlib import Path
from typing import Any, List, Tuple

import mido

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = str(WORKSPACE_DIR / "scripts" / "satin_jackets_infinite_loop.mid")


def _flush_abs_events(track: mido.MidiTrack, events: List[Tuple[int, int, Any]]) -> None:
    """Converts (abs_tick, order_key, mido_message) tuples into exact non-negative delta track."""
    events.sort(key=lambda item: (item[0], item[1]))
    last_tick = 0
    for abs_tick, _order, msg in events:
        clamped = max(last_tick, int(abs_tick))
        msg.time = clamped - last_tick
        track.append(msg)
        last_tick = clamped


def generate_satin_jackets_infinite_loop(output_path: str = OUTPUT_PATH, bpm: float = 116.0) -> str:
    ticks_per_beat = 480
    mid = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)

    track_cond = mido.MidiTrack()
    mid.tracks.append(track_cond)
    track_cond.append(mido.MetaMessage("track_name", name="Satin Jackets Infinite Loop Conductor"))
    track_cond.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

    track_chords = mido.MidiTrack()
    mid.tracks.append(track_chords)
    track_chords.append(mido.MetaMessage("track_name", name="Infinite Harmonic Chords (Strummed)"))

    # Progression in C minor (8 Bars = 32 Beats):
    # Bars 1-2: Abmaj9, Bars 3-4: Bb9, Bars 5-6: Cm9 (penultimate tonic),
    # Bar 7-8.5: Fm9, Bar 8 Beats 3-4: Cmaj9 Picardy Third turnaround into Abmaj9!
    chord_sequence = [
        ("Abmaj9 (VImaj9)", [56, 60, 63, 67, 72], 0, 8 * ticks_per_beat, 86, False),
        ("Bb9 (VII9)", [58, 62, 65, 68, 72], 8 * ticks_per_beat, 8 * ticks_per_beat, 88, False),
        ("Cm9 (i9 Penultimate Tonic)", [60, 63, 67, 70, 74], 16 * ticks_per_beat, 8 * ticks_per_beat, 94, False),
        ("Fm9 (iv9 Unresolved Susp)", [53, 60, 63, 67, 70], 24 * ticks_per_beat, 6 * ticks_per_beat, 90, False),
        ("Cmaj9 (Picardy False Drop Turnaround)", [60, 64, 67, 71, 74], 30 * ticks_per_beat, 2 * ticks_per_beat, 98, True),
    ]

    events: List[Tuple[int, int, Any]] = []
    strum_step_ticks = 10  # ~10.8 ms at 116 BPM / 480 TPB

    for _name, notes, start_tick, dur_ticks, base_vel, is_turnaround in chord_sequence:
        n_voices = len(notes)
        for idx, note in enumerate(notes):
            is_top = idx == n_voices - 1
            t_on = start_tick + idx * strum_step_ticks
            t_off = max(t_on + 24, start_tick + dur_ticks - 18)
            vel = min(127, base_vel + idx * 3 + (16 if is_top else 0) + (4 if is_turnaround else 0))
            events.append((t_on, 1, mido.Message("note_on", channel=0, note=note, velocity=vel, time=0)))
            events.append((t_off, 0, mido.Message("note_off", channel=0, note=note, velocity=0, time=0)))

        # Velocity-coupled brightness breath (CC#74) + expression swell (CC#11)
        steps = max(2, dur_ticks // 240)
        for s in range(steps):
            t_cc = start_tick + s * 240
            frac = s / max(1, steps - 1)
            cutoff_val = int(76 + 34 * (1.0 - frac) if is_turnaround else 68 + 38 * frac)
            expr_val = int(112 - 22 * (frac ** 1.4)) if is_turnaround else 112
            events.append((t_cc, 2, mido.Message("control_change", channel=0, control=74, value=max(30, min(127, cutoff_val)), time=0)))
            events.append((t_cc, 3, mido.Message("control_change", channel=0, control=11, value=max(40, min(127, expr_val)), time=0)))

    _flush_abs_events(track_chords, events)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(out))
    print(f"[Infinite Harmonic Loop] Saved 'Satin Jackets' Penrose Stair MIDI -> {out}")
    return str(out)


if __name__ == "__main__":
    generate_satin_jackets_infinite_loop()
