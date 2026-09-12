#!/usr/bin/env python3
"""
Antigravity Euclidean Polyrhythm & Microtonal Groove Generator (v9.0 SOTA)
Implements the Bjorklund E(k, n) algorithm with humanized velocity dynamics,
MPC groove swing, and flam accents for percussion and rhythmic synth lines.
"""

import math
from pathlib import Path
from typing import List, Dict, Any
import mido


def bjorklund(k: int, n: int) -> List[int]:
    """Distributes k pulses as evenly as possible over n steps using Bjorklund's algorithm."""
    if k <= 0:
        return [0] * n
    if k >= n:
        return [1] * n

    pattern = [[1]] * k + [[0]] * (n - k)
    while True:
        num_zeros = len(pattern) - k
        if num_zeros <= 1:
            break
        num_distribute = min(k, num_zeros)
        new_pattern = []
        for i in range(num_distribute):
            new_pattern.append(pattern[i] + pattern[-num_distribute + i])
        new_pattern.extend(pattern[num_distribute:-num_distribute])
        pattern = new_pattern
        k = num_distribute

    flat = [item for sublist in pattern for item in sublist]
    return flat


def generate_euclidean_midi_clip(
    pulses: int = 5,
    steps: int = 8,
    bars: int = 4,
    bpm: float = 112.0,
    note_number: int = 60,
    swing_percent: float = 58.0,
    output_path: Path = None,
    track_name: str = "Euclidean Groove"
) -> Path:
    if output_path is None:
        output_path = Path.home() / f"Music/FL Studio Bounces/Euclidean_E_{pulses}_{steps}_{int(bpm)}BPM.mid"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pattern = bjorklund(pulses, steps)
    ppq = 480
    step_ticks = (ppq * 4) // steps
    swing_offset = int((swing_percent - 50.0) / 100.0 * step_ticks)

    mid = mido.MidiFile(type=1, ticks_per_beat=ppq)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    track.append(mido.MetaMessage('track_name', name=f"{track_name} E({pulses},{steps})", time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))

    events = []
    for bar in range(bars):
        bar_start = bar * (ppq * 4)
        for s_idx, is_pulse in enumerate(pattern):
            if is_pulse:
                t = bar_start + (s_idx * step_ticks)
                if s_idx % 2 == 1:
                    t += swing_offset
                
                # Velocity accent curves
                if s_idx == 0:
                    vel = 120  # Downbeat accent
                elif s_idx == steps // 2:
                    vel = 105  # Midpoint accent
                else:
                    vel = 88 + (s_idx % 3) * 6

                dur = int(step_ticks * 0.70)
                events.append((t, 'note_on', note_number, vel))
                events.append((t + dur, 'note_off', note_number, 0))

    # Sort and compute deltas
    events.sort(key=lambda x: (x[0], 0 if x[1] == 'note_off' else 1))
    last_t = 0
    for t, mtype, note, vel in events:
        delta = max(0, t - last_t)
        track.append(mido.Message(mtype, channel=9 if note_number in [36, 38, 42] else 0, note=note, velocity=vel, time=delta))
        last_t = t

    track.append(mido.MetaMessage('end_of_track', time=0))
    mid.save(str(output_path))
    return output_path


if __name__ == "__main__":
    out = Path.home() / "Music/FL Studio Bounces/Euclidean_E_7_12_Bulerias.mid"
    generate_euclidean_midi_clip(pulses=7, steps=12, bars=8, bpm=112.0, note_number=69, swing_percent=62.0, output_path=out, track_name="Palmas Bulerías")
    print(f"✅ Generated Euclidean MIDI: {out}")
