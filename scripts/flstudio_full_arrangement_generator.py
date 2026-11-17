#!/usr/bin/env python3
"""
Full Arrangement Generator for 'No Lo Entiende' (116 BPM, C minor) — C5-REAL Fixed Timing
Uses exact absolute-tick scheduling so swing never accumulates tempo drift, vocal triggers
land on exact 4-bar boundaries (Bars 1, 5, 9, 13), and 24-TET pitchwheel resets cleanly.
"""

from pathlib import Path
from typing import Any, List, Tuple

import mido

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_DIR / "scripts" / "arrangement"


def _flush_abs_events(track: mido.MidiTrack, events: List[Tuple[int, int, Any]]) -> None:
    events.sort(key=lambda item: (item[0], item[1]))
    last_tick = 0
    for abs_tick, _order, msg in events:
        clamped = max(last_tick, int(abs_tick))
        msg.time = clamped - last_tick
        track.append(msg)
        last_tick = clamped


def generate_full_arrangement() -> bool:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpm = 116.0
    ticks_per_beat = 480
    bar_ticks = 4 * ticks_per_beat
    step_ticks = ticks_per_beat // 4  # 120 ticks per 16th

    # 1. Generate Intro Rhythm MIDI (exact 32 bars, zero cumulative swing drift)
    mid_intro = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    track_intro = mido.MidiTrack()
    mid_intro.tracks.append(track_intro)
    track_intro.append(mido.MetaMessage("track_name", name="Intro Shakers & Top Loop"))
    track_intro.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

    intro_events: List[Tuple[int, int, Any]] = []
    for bar in range(32):
        bar_base = bar * bar_ticks
        is_false_drop_bar = bar == 31
        for step in range(16):
            if is_false_drop_bar and step >= 8:
                continue  # Living Pre-Drop strip in beats 3-4 before Verse enters
            swing_offset = 12 if (step % 2 == 1) else 0
            t_on = bar_base + step * step_ticks + swing_offset
            t_off = t_on + (step_ticks // 2)
            note = 70 if step in (4, 12) else 69
            vel = (108 if step in (4, 12) else 96) if step % 2 == 0 else 74
            intro_events.append((t_on, 1, mido.Message("note_on", note=note, velocity=vel, time=0)))
            intro_events.append((t_off, 0, mido.Message("note_off", note=note, velocity=0, time=0)))
    _flush_abs_events(track_intro, intro_events)

    intro_path = OUTPUT_DIR / "01_intro_groove_32bars.mid"
    mid_intro.save(str(intro_path))
    print(f"[Arrangement] Saved Intro Groove MIDI -> {intro_path}")

    # 2. Generate Vocal Call-and-Response Trigger MIDI (Exact Bars 1, 5, 9, 13 = bars 0, 4, 8, 12)
    mid_vocal = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    track_vocal = mido.MidiTrack()
    mid_vocal.tracks.append(track_vocal)
    track_vocal.append(mido.MetaMessage("track_name", name="Teddy Pendergrass & Vocal Triggers"))
    track_vocal.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

    vocal_events: List[Tuple[int, int, Any]] = []
    for bar in range(0, 16, 4):
        t_on = bar * bar_ticks
        t_off = t_on + ticks_per_beat * 2
        vel = 108 if bar < 12 else 96
        vocal_events.append((t_on, 1, mido.Message("note_on", note=60, velocity=vel, time=0)))
        vocal_events.append((t_off, 0, mido.Message("note_off", note=60, velocity=0, time=0)))
    _flush_abs_events(track_vocal, vocal_events)

    vocal_path = OUTPUT_DIR / "02_vocal_triggers_16bars.mid"
    mid_vocal.save(str(vocal_path))
    print(f"[Arrangement] Saved Vocal Triggers MIDI -> {vocal_path}")

    # 3. Generate 24-TET Dub Breakdown MIDI (Exact bar spacing + clean Pitchwheel 0 reset)
    mid_dub = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    track_dub = mido.MidiTrack()
    mid_dub.tracks.append(track_dub)
    track_dub.append(mido.MetaMessage("track_name", name="24-TET Dub Synth Breakdown"))
    track_dub.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

    dub_notes = [60, 61, 63, 65, 67, 68, 70]
    dub_events: List[Tuple[int, int, Any]] = []
    for bar in range(32):
        note = dub_notes[bar % len(dub_notes)]
        chan = bar % 8
        pb_val = 2048 if bar % 2 == 1 else 0
        t_on = bar * bar_ticks
        t_off = t_on + ticks_per_beat * 3  # leaves 1 beat dub echo tail space per bar
        vel = 96 if bar < 30 else int(96 * (1.0 - 0.25 * (bar - 29)))
        dub_events.append((t_on, 0, mido.Message("pitchwheel", channel=chan, pitch=pb_val, time=0)))
        dub_events.append((t_on, 1, mido.Message("note_on", channel=chan, note=note, velocity=vel, time=0)))
        dub_events.append((t_off, 2, mido.Message("note_off", channel=chan, note=note, velocity=0, time=0)))
        dub_events.append((t_off + 24, 3, mido.Message("pitchwheel", channel=chan, pitch=0, time=0)))
    _flush_abs_events(track_dub, dub_events)

    dub_path = OUTPUT_DIR / "03_dub_breakdown_24tet_32bars.mid"
    mid_dub.save(str(dub_path))
    print(f"[Arrangement] Saved 24-TET Dub Breakdown MIDI -> {dub_path}")

    print("\n[Arrangement] Full 128-Bar House Producers Arrangement Suite Generated Successfully!")
    return True


if __name__ == "__main__":
    generate_full_arrangement()
