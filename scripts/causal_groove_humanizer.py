#!/usr/bin/env python3
"""
Causal Metric Groove & 1/f Pink Noise Humanizer (v16.0 Sovereign Apex)
Transforms mechanical rigid quantization into authentic human performance
using asymmetric metric Compás timing templates and 1/f fractal pink noise drift (Voss-Clarke model).

Groove Mechanics:
- 12-Beat Bulerías Compás Micro-Timing:
  - Metric accents on beats 3, 6, 8, 10, 12 receive velocity boost (+12 to +22) and early anticipation (-6 to -14 ticks)
  - Offbeat contratiempos receive laid-back pocket delay (+4 to +10 ticks)
- 1/f Fractal Noise Drift:
  - Voss-McCartney algorithm simulates human metabolic pulse fluctuation over long phrasing
- Full binary roundtrip: parses native .fsc scores, humanizes tick offsets & velocities, and serializes .fsc
"""

import math
import struct
import random
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from scripts.fl_fsc_score_builder import FLScoreBuilder, encode_varlen

logger = logging.getLogger("FLStudio-GrooveHumanizer")


def generate_pink_noise(n_samples: int) -> np.ndarray:
    """Generates 1/f pink noise via spectral filtering of white Gaussian noise."""
    if n_samples <= 0:
        return np.array([])
    white = np.random.normal(0.0, 1.0, n_samples)
    fft_white = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n_samples)
    freqs[0] = 1e-4  # Avoid division by zero at DC
    # Pink noise 1/sqrt(f) filter
    fft_pink = fft_white / np.sqrt(freqs)
    pink = np.fft.irfft(fft_pink, n=n_samples)
    # Normalize to zero mean, unit variance
    pink = (pink - np.mean(pink)) / (np.std(pink) + 1e-6)
    return pink


def parse_fsc_notes(fsc_path: str) -> List[Dict[str, int]]:
    """Parses raw note records from an FL Studio Score (.fsc) binary file."""
    p = Path(fsc_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"FSC score file not found: {p}")

    data = p.read_bytes()
    notes = []

    # Find Note Array Event 0xE0
    idx = data.find(b"\xE0")
    if idx == -1:
        # Fallback: scan for FLdt chunk
        idx = data.find(b"FLdt")
        if idx != -1:
            idx = data.find(b"\xE0", idx)

    if idx != -1:
        # Skip 0xE0 and varlen length
        ptr = idx + 1
        length = 0
        shift = 0
        while ptr < len(data):
            b = data[ptr]
            ptr += 1
            length |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7

        note_bytes = data[ptr:ptr + length]
        record_len = 20
        num_notes = len(note_bytes) // record_len

        for i in range(num_notes):
            chunk = note_bytes[i * record_len:(i + 1) * record_len]
            pos, flags, duration, pitch, pan, vel, rel, mod = struct.unpack("<IIIIBBBB", chunk)
            notes.append({
                "pos": pos,
                "flags": flags,
                "duration": duration,
                "pitch": pitch,
                "pan": pan,
                "vel": vel,
                "rel": rel,
                "mod": mod
            })

    return notes


def humanize_groove_causal(
    input_fsc: Optional[str] = None,
    output_fsc: Optional[str] = None,
    style: str = "bulerias_flamenco",
    groove_depth: float = 0.65,
    drift_amount: float = 0.40,
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Applies metric compás microtiming and 1/f fractal pink noise drift to note events.
    - style: 'bulerias_flamenco', 'cyber_dilla_swing', 'tangos_accelerando'
    - groove_depth: intensity of metric timing displacement (0.0 to 1.0)
    - drift_amount: intensity of 1/f tempo/velocity drift (0.0 to 1.0)
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    # If no input FSC is provided, find one in centralized bounces or generate baseline
    if not input_fsc:
        bounces = Path.home() / "Music" / "FL Studio Bounces" / "Scores"
        default_fsc = bounces / "Dark_Cyber_Flamenco_Score.fsc"
        if not default_fsc.exists():
            from scripts.fl_fsc_score_builder import generate_dark_cyber_flamenco_score
            generate_dark_cyber_flamenco_score()
        in_file = str(default_fsc)
    else:
        in_file = input_fsc

    notes = parse_fsc_notes(in_file)
    if not notes:
        raise ValueError(f"No notes could be extracted from {in_file}")

    total_notes = len(notes)
    pink_drift = generate_pink_noise(total_notes)

    ppq = 96
    ticks_per_beat = ppq

    # Bulerías 12-beat metric displacement map (in ticks relative to PPQ=96)
    # Accents: 3, 6, 8, 10, 12 (0-indexed beats: 2, 5, 7, 9, 11)
    bulerias_timing_map = {
        2: -10,  # Beat 3 rushed/pushed
        5: -8,   # Beat 6 rushed
        7: -12,  # Beat 8 strong accent anticipated
        9: -8,   # Beat 10
        11: -14  # Beat 12 resolution anticipated
    }
    bulerias_vel_map = {
        2: +18,
        5: +14,
        7: +22,
        9: +16,
        11: +24
    }

    builder = FLScoreBuilder(ppq=96, channels=5)

    humanized_notes = []
    for idx, n in enumerate(notes):
        orig_pos = n["pos"]
        orig_vel = n["vel"]

        # Calculate beat position within 12-beat compás cycle (cycle = 12 * 96 = 1152 ticks)
        beat_idx = int((orig_pos // ticks_per_beat) % 12)

        # 1. Metric systematic displacement
        if style == "bulerias_flamenco":
            metric_tick_offset = int(bulerias_timing_map.get(beat_idx, +5) * groove_depth)
            metric_vel_boost = int(bulerias_vel_map.get(beat_idx, -6) * groove_depth)
        elif style == "cyber_dilla_swing":
            # 16th note swing displacement
            sixteenth_idx = int((orig_pos // 24) % 4)
            metric_tick_offset = int((8 if sixteenth_idx % 2 == 1 else -3) * groove_depth)
            metric_vel_boost = int((6 if sixteenth_idx % 2 == 0 else -4) * groove_depth)
        else:
            metric_tick_offset = int(random.uniform(-4, 4) * groove_depth)
            metric_vel_boost = 0

        # 2. 1/f Pink Noise metabolic drift
        drift_tick = int(pink_drift[idx] * 6.0 * drift_amount)
        drift_vel = int(pink_drift[idx] * 8.0 * drift_amount)

        # Micro-jitter
        micro_jitter = random.randint(-2, 2)

        # Apply transformations
        new_pos = max(0, orig_pos + metric_tick_offset + drift_tick + micro_jitter)
        new_vel = max(1, min(127, orig_vel + metric_vel_boost + drift_vel))

        builder.add_note(
            pos_ticks=new_pos,
            pitch=n["pitch"],
            duration_ticks=n["duration"],
            velocity=new_vel,
            pan=n["pan"]
        )
        humanized_notes.append({"pitch": n["pitch"], "old_pos": orig_pos, "new_pos": new_pos, "vel": new_vel})

    # Export paths
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Groove_Humanized"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_fsc:
        in_stem = Path(in_file).stem
        out_fsc_path = out_dir / f"{in_stem}_Humanized_{style}.fsc"
    else:
        out_fsc_path = Path(output_fsc).expanduser().resolve()
        out_fsc_path.parent.mkdir(parents=True, exist_ok=True)

    builder.export_fsc(str(out_fsc_path))

    return {
        "status": "SUCCESS",
        "style": style,
        "input_score": str(in_file),
        "total_notes_humanized": len(humanized_notes),
        "groove_depth": groove_depth,
        "drift_amount": drift_amount,
        "output_fsc": str(out_fsc_path),
        "output_file": str(out_fsc_path),
        "file_size_bytes": out_fsc_path.stat().st_size
    }


if __name__ == "__main__":
    res = humanize_groove_causal()
    print("Groove Humanizer output:", res)
