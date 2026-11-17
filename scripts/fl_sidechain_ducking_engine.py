#!/usr/bin/env python3
"""
Antigravity Logarithmic Sidechain Ducking Curve & Gross Beat Preset Engine
Computes click-free psychoacoustically optimized volume attenuation curves for 4/4 Kick
transients using a smooth raised-cosine pre-ducking attack ramp + logarithmic release.
"""

import json
import math
from pathlib import Path
from typing import List

WORKSPACE_DIR = Path(__file__).resolve().parent.parent


def generate_logarithmic_ducking_curve(
    num_points: int = 64,
    curve_exponent: float = 2.5,
    hold_ratio: float = 0.10,
    release_ratio: float = 0.65,
    attack_ratio: float = 0.06,
) -> List[float]:
    """
    Computes a click-free periodic logarithmic sidechain ducking curve
    (1.0 -> 0.0 raised-cosine attack ramp -> hold -> power-law recovery -> 1.0).
    """
    curve: List[float] = []
    denom = max(1, num_points - 1)
    att_r = max(0.02, min(0.20, attack_ratio))
    hold_end = min(0.85, att_r + hold_ratio)
    rel_end = min(0.99, hold_end + release_ratio)

    for i in range(num_points):
        phase = i / denom
        if phase < att_r:
            u = phase / att_r
            val = 0.5 * (1.0 + math.cos(math.pi * u))
        elif phase < hold_end:
            val = 0.0
        elif phase < rel_end:
            rel_phase = (phase - hold_end) / max(1e-6, rel_end - hold_end)
            val = math.pow(rel_phase, curve_exponent)
        else:
            val = 1.0
        curve.append(round(min(1.0, max(0.0, val)), 4))
    return curve


def export_ducking_curve_json(output_path: str) -> str:
    curve_data = {
        "engine": "Antigravity C5-REAL Logarithmic Sidechain (Zero-Click Ramp)",
        "resolution": 64,
        "curve": generate_logarithmic_ducking_curve(),
        "gross_beat_time_slot_map": {
            1: "Instant 1/4 Ducking (6% Raised-Cosine Ramp)",
            2: "Smooth 1/2 Logarithmic Ducking",
            3: "3/16 Dub Gate Stutter",
            4: "Reverse Scratch Drop",
        },
    }
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(curve_data, f, indent=2)

    print(f"[Sidechain Engine] Exported Logarithmic Ducking Curve -> {out}")
    return str(out)


if __name__ == "__main__":
    out_file = WORKSPACE_DIR / "scripts" / "logarithmic_sidechain_ducking.json"
    export_ducking_curve_json(str(out_file))
