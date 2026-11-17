#!/usr/bin/env python3
"""
C5-REAL AIR Moon Safari Space-Pop Multi-Track Engine
====================================================
Generates a multi-track MIDI arrangement with deterministic differential groove pocket,
chord micro-strumming, top-note voicing, and Living Exit phrasing:
1. Fender Rhodes 73 Chords (Am9 -> D9 -> Fmaj7 -> E7#9) with +14 tick strum & CC10 tremolo.
2. Minimoog Melodic Bassline (+10 tick laid-back pocket + legato/staccato contour).
3. Solina String Ensemble (ethereal upper counter-voicing + Bar 4 Living Exit decrescendo).
"""

from pathlib import Path
from typing import Any, List, Tuple

import mido

WORKSPACE_DIR = Path(__file__).resolve().parent.parent


def _flush_abs_events(track: mido.MidiTrack, events: List[Tuple[int, int, Any]]) -> None:
    """Flushes absolute-tick sorted MIDI events without cumulative drift."""
    events.sort(key=lambda item: (item[0], item[1]))
    last_tick = 0
    for abs_tick, _order, msg in events:
        clamped = max(last_tick, int(abs_tick))
        msg.time = clamped - last_tick
        track.append(msg)
        last_tick = clamped


def generate_air_moon_safari_multitrack(output_path: str, bpm: float = 88.0) -> str:
    ticks_per_beat = 480
    mid = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)

    track_master = mido.MidiTrack()
    mid.tracks.append(track_master)
    track_master.append(mido.MetaMessage("track_name", name="AIR Moon Safari Master"))
    track_master.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

    # --- TRACK 1: Fender Rhodes 73 Chords (Micro-Strum + Top-Note Voicing) ---
    track_rhodes = mido.MidiTrack()
    mid.tracks.append(track_rhodes)
    track_rhodes.append(mido.MetaMessage("track_name", name="Fender Rhodes 73 (Chords)"))

    chords = [
        {"notes": [45, 55, 60, 64, 71], "time_start": 0, "duration": 1920, "vel": 82},     # Am9
        {"notes": [50, 54, 60, 64, 69], "time_start": 1920, "duration": 1920, "vel": 80},  # D9
        {"notes": [41, 57, 60, 64, 67], "time_start": 3840, "duration": 1920, "vel": 86},  # Fmaj7
        {"notes": [40, 56, 62, 67, 73], "time_start": 5760, "duration": 1920, "vel": 88},  # E7(#9)
    ]

    rhodes_events: List[Tuple[int, int, Any]] = []
    strum_ticks = 14
    for bar_idx, chord in enumerate(chords):
        n_voices = len(chord["notes"])
        is_exit_bar = bar_idx == len(chords) - 1
        for v_idx, note in enumerate(chord["notes"]):
            is_top = v_idx == n_voices - 1
            t_on = chord["time_start"] + v_idx * strum_ticks
            t_off = max(t_on + 24, chord["time_start"] + chord["duration"] - 48)
            vel = min(127, chord["vel"] + v_idx * 3 + (14 if is_top else 0))
            rhodes_events.append((t_on, 1, mido.Message("note_on", channel=0, note=note, velocity=vel, time=0)))
            rhodes_events.append((t_off, 0, mido.Message("note_off", channel=0, note=note, velocity=0, time=0)))

        # Rhodes tremolo pan ripple (CC#10) & Living Exit RC decrescendo in Bar 4
        for step in range(4):
            t_cc = chord["time_start"] + step * 480
            pan = 64 + int(22 * ((-1) ** (bar_idx + step)))
            rhodes_events.append((t_cc, 2, mido.Message("control_change", channel=0, control=10, value=pan, time=0)))
            expr = int(115 - 32 * ((step / 3.0) ** 1.3)) if is_exit_bar else 112
            rhodes_events.append((t_cc, 3, mido.Message("control_change", channel=0, control=11, value=expr, time=0)))

    _flush_abs_events(track_rhodes, rhodes_events)

    # --- TRACK 2: Minimoog Bassline (Laid-Back Differential Pocket +10 ticks) ---
    track_bass = mido.MidiTrack()
    mid.tracks.append(track_bass)
    track_bass.append(mido.MetaMessage("track_name", name="Minimoog (Bass Laid-Back Pocket)"))

    bass_notes = [
        {"note": 33, "t_on": 0, "dur": 480, "vel": 106},
        {"note": 40, "t_on": 960, "dur": 240, "vel": 96},
        {"note": 43, "t_on": 1440, "dur": 240, "vel": 102},
        {"note": 38, "t_on": 1920, "dur": 480, "vel": 106},
        {"note": 45, "t_on": 2880, "dur": 240, "vel": 98},
        {"note": 42, "t_on": 3360, "dur": 240, "vel": 100},
        {"note": 29, "t_on": 3840, "dur": 960, "vel": 108},
        {"note": 36, "t_on": 4800, "dur": 480, "vel": 102},
        {"note": 28, "t_on": 5760, "dur": 480, "vel": 106},
        {"note": 40, "t_on": 6720, "dur": 240, "vel": 94},
        {"note": 38, "t_on": 7200, "dur": 240, "vel": 88},
    ]

    bass_events: List[Tuple[int, int, Any]] = []
    bass_pocket_ticks = 10
    for b in bass_notes:
        t_on = b["t_on"] + (bass_pocket_ticks if b["t_on"] > 0 else 0)
        t_off = t_on + b["dur"] - 24
        bass_events.append((t_on, 1, mido.Message("note_on", channel=1, note=b["note"], velocity=b["vel"], time=0)))
        bass_events.append((t_off, 0, mido.Message("note_off", channel=1, note=b["note"], velocity=0, time=0)))

    _flush_abs_events(track_bass, bass_events)

    # --- TRACK 3: Solina String Ensemble (Counter-Voicing + Turnaround Lift) ---
    track_strings = mido.MidiTrack()
    mid.tracks.append(track_strings)
    track_strings.append(mido.MetaMessage("track_name", name="Solina Strings (Pad)"))

    string_chords = [
        {"notes": [76, 81], "t_on": 0, "dur": 1920, "vel": 68},
        {"notes": [74, 81], "t_on": 1920, "dur": 1920, "vel": 72},
        {"notes": [77, 84], "t_on": 3840, "dur": 1920, "vel": 78},
        {"notes": [73, 80, 88], "t_on": 5760, "dur": 1880, "vel": 82},
    ]

    string_events: List[Tuple[int, int, Any]] = []
    for idx, sc in enumerate(string_chords):
        for v_i, note in enumerate(sc["notes"]):
            t_on = sc["t_on"] + v_i * 8
            t_off = sc["t_on"] + sc["dur"] - 16
            vel = min(127, sc["vel"] + (8 if v_i == len(sc["notes"]) - 1 else 0))
            string_events.append((t_on, 1, mido.Message("note_on", channel=2, note=note, velocity=vel, time=0)))
            string_events.append((t_off, 0, mido.Message("note_off", channel=2, note=note, velocity=0, time=0)))
        # Swell expression curve (CC#11) across each bar
        for step in range(4):
            t_cc = sc["t_on"] + step * 480
            expr = int(84 + 34 * (step / 3.0)) if idx < 3 else int(118 - 28 * (step / 3.0))
            string_events.append((t_cc, 2, mido.Message("control_change", channel=2, control=11, value=expr, time=0)))

    _flush_abs_events(track_strings, string_events)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(out))
    print(f"[AIR Moon Safari Engine] Generated Multi-Track MIDI -> {out}")
    return str(out)


if __name__ == "__main__":
    out_file = WORKSPACE_DIR / "samples" / "air_moon_safari_multitrack.mid"
    generate_air_moon_safari_multitrack(str(out_file))
