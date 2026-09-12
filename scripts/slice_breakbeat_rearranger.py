#!/usr/bin/env python3
"""
C5-REAL Generative Transient Slice Breakbeat & Compás Re-Arranger
═════════════════════════════════════════════════════════════════
Performs algorithmic and Markovian re-sequencing of transient audio chops
into polyrhythmic Flamenco Compás patterns, Cyber-Drill rolls, and
generative breakcore variations.

Exports:
- Standard MIDI File (.mid)
- Native FL Studio Piano Roll Score (.fsc)
- Centralized into ~/Music/FL Studio Bounces/Generative_Arrangements/
"""

import sys
import math
import random
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

MUSIC_BOUNCES_DIR = Path.home() / "Music" / "FL Studio Bounces"


def generate_slice_arrangement(
    style: str = "bulerias_cyber_drill",
    bars: int = 4,
    bpm: float = 112.0,
    total_slices: int = 64,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Generates algorithmic breakbeat arrangements triggering transient slices (chromatic map C1..).
    styles:
    - 'bulerias_cyber_drill': 12-beat compas with polyrhythmic ratchets and stutter rolls
    - 'markov_breakcore': Probabilistic Markov transitions between chop registers
    - 'tangos_funk': 4/4 syncopated Flamenco-Tangos groove with ghost notes
    """
    random.seed(random_seed)
    from scripts.fl_fsc_score_builder import FLScoreBuilder
    builder = FLScoreBuilder(ppq=96)

    # 96 ticks per beat (quarter note), 24 ticks per 16th note, 12 ticks per 32nd note
    step_16th = 24
    generated_notes = []

    if style == "bulerias_cyber_drill":
        # 12-beat Flamenco cycle across bars (e.g. 12 eighth notes = 576 ticks per compas)
        accents = {3, 6, 8, 10, 12}
        compas_len = 12
        ticks_per_step = 48  # 8th note
        current_tick = 0

        for bar in range(bars):
            for beat in range(1, compas_len + 1):
                is_accent = beat in accents
                slice_idx = random.randint(0, min(total_slices - 1, 15)) if is_accent else random.randint(16, min(total_slices - 1, 48))
                midi_note = 36 + slice_idx

                # Base compas hit
                vel = 124 if is_accent else 85
                dur = 36 if is_accent else 24
                builder.add_note(pos_ticks=current_tick, pitch=midi_note, duration_ticks=dur, velocity=vel)
                generated_notes.append({"tick": current_tick, "note": midi_note, "vel": vel})

                # Cyber-Drill stutter ratchet on accents 3 and 10 (1/32nd triplets)
                if beat in (3, 10) and random.random() > 0.3:
                    sub_ticks = 12
                    for r in range(1, 4):
                        sub_note = 36 + random.randint(0, 12)
                        builder.add_note(pos_ticks=current_tick + r * sub_ticks, pitch=sub_note, duration_ticks=8, velocity=max(40, vel - (r * 15)))
                        generated_notes.append({"tick": current_tick + r * sub_ticks, "note": sub_note, "vel": vel - (r * 15)})

                current_tick += ticks_per_step

    elif style == "tangos_funk":
        # 4/4 syncopated Tangos flamencos (accents on 2, 3, 4 with contratiempo)
        total_steps = bars * 16
        for step in range(total_steps):
            tick = step * step_16th
            beat_in_bar = (step % 16) / 4.0
            is_downbeat = (step % 16) in (0, 4, 8, 12)
            is_syncopated = (step % 16) in (3, 6, 9, 11, 14)

            if is_downbeat:
                slice_idx = 0 if (step % 16 == 0) else random.randint(1, 4)  # Kick / Primary
                builder.add_note(pos_ticks=tick, pitch=36 + slice_idx, duration_ticks=20, velocity=115)
                generated_notes.append({"tick": tick, "note": 36 + slice_idx, "vel": 115})
            elif is_syncopated and random.random() > 0.2:
                slice_idx = random.randint(5, min(total_slices - 1, 32))
                builder.add_note(pos_ticks=tick, pitch=36 + slice_idx, duration_ticks=16, velocity=95)
                generated_notes.append({"tick": tick, "note": 36 + slice_idx, "vel": 95})

    else:  # markov_breakcore
        # 1st-order Markov state transitions: Low -> Mid -> High -> Stutter -> Low
        states = ["low", "mid", "high", "stutter"]
        trans_matrix = {
            "low": [0.3, 0.4, 0.2, 0.1],
            "mid": [0.2, 0.3, 0.4, 0.1],
            "high": [0.4, 0.2, 0.1, 0.3],
            "stutter": [0.6, 0.2, 0.1, 0.1]
        }
        current_state = "low"
        total_steps = bars * 16

        for step in range(total_steps):
            tick = step * step_16th
            probs = trans_matrix[current_state]
            r = random.random()
            cum = 0.0
            for idx, p in enumerate(probs):
                cum += p
                if r <= cum:
                    current_state = states[idx]
                    break

            if current_state == "low":
                note = 36 + random.randint(0, 5)
                builder.add_note(pos_ticks=tick, pitch=note, duration_ticks=24, velocity=110)
            elif current_state == "mid":
                note = 36 + random.randint(6, 20)
                builder.add_note(pos_ticks=tick, pitch=note, duration_ticks=18, velocity=90)
            elif current_state == "high":
                note = 36 + random.randint(21, min(total_slices - 1, 45))
                builder.add_note(pos_ticks=tick, pitch=note, duration_ticks=12, velocity=85)
            elif current_state == "stutter":
                # Rapid 64th note burst
                for sub in range(4):
                    note = 36 + random.randint(0, 10)
                    builder.add_note(pos_ticks=tick + sub * 6, pitch=note, duration_ticks=4, velocity=100 - sub * 10)

    out_dir = MUSIC_BOUNCES_DIR / "Generative_Arrangements"
    out_dir.mkdir(parents=True, exist_ok=True)

    fsc_path = out_dir / f"{style}_{bars}Bars_{int(bpm)}BPM.fsc"
    builder.export_fsc(str(fsc_path))

    return {
        "status": "SUCCESS",
        "style": style,
        "bars": bars,
        "bpm": bpm,
        "total_notes": len(builder.notes),
        "exported_fsc": str(fsc_path)
    }


if __name__ == "__main__":
    res = generate_slice_arrangement("bulerias_cyber_drill", bars=4)
    print(json.dumps(res, indent=2))
