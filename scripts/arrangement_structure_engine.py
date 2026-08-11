#!/usr/bin/env python3
"""
Antigravity Arrangement Structure Engine (v2.0 SOTA)
Generates complete song structures with intro, build-up, drop, breakdown,
second drop, and outro following professional House & Techno arrangement templates.
"""

import os
import math
import random
import mido
from typing import List, Dict, Optional

# Professional arrangement templates (in bars)
ARRANGEMENT_TEMPLATES = {
    "deep_house_classic": {
        "bpm": 122, "key": "Am",
        "sections": [
            {"name": "Intro (Kick + Percussion)", "bars": 16, "layers": ["kick", "hats", "shaker"]},
            {"name": "Build A (Add Bass)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc"]},
            {"name": "Main A (Full Energy)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc", "chords", "pad"]},
            {"name": "Breakdown (Strip Kick)", "bars": 8, "layers": ["pad", "chords", "vocal_chop"]},
            {"name": "Build B (Rising Filter)", "bars": 8, "layers": ["kick", "hats", "bass", "chords", "pad", "riser"]},
            {"name": "Drop / Main B (Peak)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc", "chords", "pad", "lead", "vocal_chop"]},
            {"name": "Breakdown 2", "bars": 8, "layers": ["pad", "chords", "delay_tail"]},
            {"name": "Main C (Final Push)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc", "chords", "pad"]},
            {"name": "Outro (Strip Layers)", "bars": 16, "layers": ["kick", "hats", "shaker"]},
        ]
    },
    "melodic_techno_maceo": {
        "bpm": 126, "key": "Bm",
        "sections": [
            {"name": "Intro (Atmosphere)", "bars": 16, "layers": ["kick", "noise_sweep"]},
            {"name": "Build (Add Acid)", "bars": 16, "layers": ["kick", "hats", "acid_bass", "perc"]},
            {"name": "Main A (Full Hypnotic)", "bars": 32, "layers": ["kick", "hats", "acid_bass", "perc", "locrian_pad", "arp"]},
            {"name": "Breakdown (Ethereal)", "bars": 16, "layers": ["locrian_pad", "arp", "reverb_wash"]},
            {"name": "Drop (Maximum Tension)", "bars": 32, "layers": ["kick", "hats", "acid_bass", "perc", "locrian_pad", "arp", "lead"]},
            {"name": "Outro (Deconstruct)", "bars": 16, "layers": ["kick", "acid_bass", "noise_sweep"]},
        ]
    },
    "air_moon_safari_dreampop": {
        "bpm": 88, "key": "Am",
        "sections": [
            {"name": "Intro (Rhodes Alone)", "bars": 8, "layers": ["rhodes"]},
            {"name": "Verse A (Add Bass + Strings)", "bars": 16, "layers": ["rhodes", "minimoog_bass", "strings"]},
            {"name": "Chorus (Full Ensemble)", "bars": 8, "layers": ["rhodes", "minimoog_bass", "strings", "vocal_melody", "drums_light"]},
            {"name": "Verse B", "bars": 16, "layers": ["rhodes", "minimoog_bass", "strings"]},
            {"name": "Chorus 2 (Peak)", "bars": 8, "layers": ["rhodes", "minimoog_bass", "strings", "vocal_melody", "drums_full", "synth_pad"]},
            {"name": "Bridge (Ambient)", "bars": 8, "layers": ["strings", "synth_pad", "rhodes"]},
            {"name": "Final Chorus", "bars": 8, "layers": ["rhodes", "minimoog_bass", "strings", "vocal_melody", "drums_full", "synth_pad"]},
            {"name": "Outro (Fade)", "bars": 8, "layers": ["rhodes", "strings"]},
        ]
    }
}

# Note pools per layer for MIDI generation
LAYER_NOTE_POOLS = {
    "kick": [36],
    "hats": [42, 44, 46],
    "shaker": [70],
    "perc": [39, 54, 56],
    "bass": [33, 36, 38, 40, 43, 45],
    "acid_bass": [35, 36, 38, 41],
    "chords": [60, 63, 67, 70, 74],
    "pad": [72, 76, 79, 84],
    "locrian_pad": [59, 62, 65, 68],
    "lead": [72, 74, 76, 79, 81, 84],
    "arp": [60, 64, 67, 72, 76],
    "rhodes": [60, 64, 67, 71],
    "minimoog_bass": [33, 40, 43],
    "strings": [76, 81],
    "vocal_chop": [60],
    "vocal_melody": [65, 67, 69, 72],
    "drums_light": [36, 38, 42],
    "drums_full": [36, 38, 42, 46, 49],
    "synth_pad": [60, 64, 67, 72],
    "riser": [84],
    "noise_sweep": [84],
    "reverb_wash": [72],
    "delay_tail": [60],
}

def generate_arrangement_midi(
    template_name: str = "deep_house_classic",
    output_path: Optional[str] = None,
    bpm_override: Optional[float] = None
) -> str:
    template = ARRANGEMENT_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(ARRANGEMENT_TEMPLATES.keys())}")

    bpm = bpm_override or template["bpm"]
    if not output_path:
        output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/samples/arrangement_{template_name}.mid")

    mid = mido.MidiFile(type=1)
    tpb = 480
    mid.ticks_per_beat = tpb

    # Tempo track
    t_tempo = mido.MidiTrack()
    mid.tracks.append(t_tempo)
    t_tempo.append(mido.MetaMessage('track_name', name=f'Arrangement: {template_name}'))
    t_tempo.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # Add section markers
    tick_offset = 0
    for section in template["sections"]:
        t_tempo.append(mido.MetaMessage('text', text=section["name"], time=tick_offset if tick_offset == 0 else section["bars"] * 4 * tpb))
        tick_offset += section["bars"] * 4 * tpb

    # Create one track per unique layer
    all_layers = set()
    for s in template["sections"]:
        all_layers.update(s["layers"])

    layer_tracks = {}
    for ch_idx, layer_name in enumerate(sorted(all_layers)):
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage('track_name', name=layer_name.replace("_", " ").title()))
        layer_tracks[layer_name] = (track, min(ch_idx, 15))

    # Generate notes per section
    for section in template["sections"]:
        bars = section["bars"]
        active_layers = set(section["layers"])

        for layer_name, (track, ch) in layer_tracks.items():
            if layer_name in active_layers:
                notes = LAYER_NOTE_POOLS.get(layer_name, [60])
                is_perc = layer_name in ("kick", "hats", "shaker", "perc", "drums_light", "drums_full")

                if is_perc:
                    # 16th-note grid
                    steps = bars * 16
                    step_ticks = tpb // 4
                    for step in range(steps):
                        if layer_name == "kick" and step % 4 != 0:
                            continue
                        if layer_name in ("hats", "drums_light", "drums_full") and step % 2 != 0:
                            continue
                        if layer_name == "shaker" and step % 2 == 0:
                            continue
                        n = random.choice(notes)
                        vel = random.randint(85, 115)
                        track.append(mido.Message('note_on', channel=ch, note=n, velocity=vel, time=step_ticks if step > 0 or len(track) > 1 else 0))
                        track.append(mido.Message('note_off', channel=ch, note=n, velocity=0, time=step_ticks // 2))
                else:
                    # Chord / melodic: one hit per bar
                    bar_ticks = 4 * tpb
                    for bar in range(bars):
                        for n in notes:
                            track.append(mido.Message('note_on', channel=ch, note=n, velocity=random.randint(75, 100), time=0 if n != notes[0] else (bar_ticks if bar > 0 or len(track) > 1 else 0)))
                        for i, n in enumerate(notes):
                            track.append(mido.Message('note_off', channel=ch, note=n, velocity=0, time=bar_ticks - 10 if i == 0 else 0))
            else:
                # Silent section: advance time pointer
                section_ticks = bars * 4 * tpb
                track.append(mido.Message('note_on', channel=ch, note=0, velocity=0, time=section_ticks))
                track.append(mido.Message('note_off', channel=ch, note=0, velocity=0, time=0))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    mid.save(output_path)
    print(f"[Arrangement Engine] Generated '{template_name}' ({sum(s['bars'] for s in template['sections'])} bars at {bpm} BPM) -> {output_path}")
    return output_path


if __name__ == "__main__":
    for name in ARRANGEMENT_TEMPLATES:
        generate_arrangement_midi(name)
