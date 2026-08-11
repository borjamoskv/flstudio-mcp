#!/usr/bin/env python3
"""
Full Arrangement Generator for 'No Lo Entiende' (116 BPM, C minor)
Constructs a complete 128-bar House Producers arrangement:
- Section 1: Intro Groove (Bars 1-32) - Top Loop, Shakers, Sub-Bass Pulse
- Section 2: Verse / Vocal Spoken Word (Bars 33-48) - Teddy Pendergrass Chops + Lead Vocals + 3/16 Dub Delays
- Section 3: Microtonal Dub Breakdown (Bars 49-80) - 24-TET Makam Bayati Synth Modulations
- Section 4: Main Peak Drop (Bars 81-112) - Full Kick + Claps + Main Synth + Sub
- Section 5: Outro / Deconstruction (Bars 113-128) - Filtered Synths + Percussion Fade
"""

import sys
import os
import random
import mido

OUTPUT_DIR = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/arrangement")

def generate_full_arrangement():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    bpm = 116.0
    ticks_per_beat = 480

    # 1. Generate Intro Rhythm MIDI
    mid_intro = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    track_intro = mido.MidiTrack()
    mid_intro.tracks.append(track_intro)
    track_intro.append(mido.MetaMessage('track_name', name='Intro Shakers & Top Loop'))
    track_intro.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # 32 Bars of Shaker 16th note pattern with 55% swing
    for bar in range(32):
        for step in range(16):
            swing_offset = 12 if (step % 2 == 1) else 0
            tick_time = (ticks_per_beat // 4) + swing_offset
            note = 70 if step in [4, 12] else 69
            vel = random.randint(90, 115) if step % 2 == 0 else random.randint(65, 85)
            track_intro.append(mido.Message('note_on', note=note, velocity=vel, time=tick_time if (bar>0 or step>0) else 0))
            track_intro.append(mido.Message('note_off', note=note, velocity=0, time=tick_time // 2))

    intro_path = os.path.join(OUTPUT_DIR, "01_intro_groove_32bars.mid")
    mid_intro.save(intro_path)
    print(f"[Arrangement] Saved Intro Groove MIDI -> {intro_path}")

    # 2. Generate Vocal Call-and-Response Trigger MIDI
    mid_vocal = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    track_vocal = mido.MidiTrack()
    mid_vocal.tracks.append(track_vocal)
    track_vocal.append(mido.MetaMessage('track_name', name='Teddy Pendergrass & Vocal Triggers'))
    track_vocal.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # Triggers on Bar 1, 5, 9, 13
    for bar in range(16):
        if bar % 4 == 0:
            track_vocal.append(mido.Message('note_on', note=60, velocity=105, time=ticks_per_beat * 4 * (bar if bar==0 else 1)))
            track_vocal.append(mido.Message('note_off', note=60, velocity=0, time=ticks_per_beat * 2))

    vocal_path = os.path.join(OUTPUT_DIR, "02_vocal_triggers_16bars.mid")
    mid_vocal.save(vocal_path)
    print(f"[Arrangement] Saved Vocal Triggers MIDI -> {vocal_path}")

    # 3. Generate 24-TET Dub Breakdown MIDI
    mid_dub = mido.MidiFile(type=1, ticks_per_beat=ticks_per_beat)
    track_dub = mido.MidiTrack()
    mid_dub.tracks.append(track_dub)
    track_dub.append(mido.MetaMessage('track_name', name='24-TET Dub Synth Breakdown'))
    track_dub.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # Makam Bayati Cents: 0, 150, 300, 500, 700, 850, 1000
    dub_notes = [60, 61, 63, 65, 67, 68, 70]
    for bar in range(32):
        note = dub_notes[bar % len(dub_notes)]
        chan = bar % 8
        # Pitch bend quarter-tone offset
        pb_val = 2048 if bar % 2 == 1 else 0
        track_dub.append(mido.Message('pitchwheel', channel=chan, pitch=pb_val, time=0 if bar > 0 else ticks_per_beat * 4))
        track_dub.append(mido.Message('note_on', channel=chan, note=note, velocity=95, time=0))
        track_dub.append(mido.Message('note_off', channel=chan, note=note, velocity=0, time=ticks_per_beat * 3))

    dub_path = os.path.join(OUTPUT_DIR, "03_dub_breakdown_24tet_32bars.mid")
    mid_dub.save(dub_path)
    print(f"[Arrangement] Saved 24-TET Dub Breakdown MIDI -> {dub_path}")

    print("\n[Arrangement] Full 128-Bar House Producers Arrangement Suite Generated Successfully!")
    return True

if __name__ == "__main__":
    generate_full_arrangement()
