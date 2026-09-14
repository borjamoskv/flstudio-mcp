#!/usr/bin/env python3
"""
Shepard-Risset Continuous Glissando & Barberpole Spatial Synthesizer (v19.0 Singularity Matrix)
Implements the continuous psychoacoustic auditory illusion of infinite ascending or descending pitch
(Jean-Claude Risset glissando) coupled with 3D barberpole binaural spatial rotation.

Architecture:
- N=10 octave-spaced sinusoidal oscillator tracks
- Continuous phase accumulation: phi_k(t) = int 2*pi * f_k(t) dt
- Raised-cosine spectral envelope weighting in log2 frequency space (20 Hz to 20 kHz)
- 3D Barberpole spatial spiral: azimuth panned via ITD and ILD as pitch glides
- Centralized WAV export to ~/Music/FL Studio Bounces/Shepard_Risset/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger("FLStudio-ShepardRisset")


def synthesize_shepard_risset_glissando(
    duration_sec: float = 8.0,
    glissando_rate_oct_per_sec: float = 0.25,
    direction: str = "ascending",
    barberpole_spin_hz: float = 0.35,
    output_wav: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesizes an infinite Shepard-Risset continuous glissando with barberpole 3D panning.
    - duration_sec: total duration in seconds
    - glissando_rate_oct_per_sec: pitch glide speed in octaves per second
    - direction: 'ascending' or 'descending'
    - barberpole_spin_hz: rate of 3D stereo rotation in Hz
    """
    sr = 44100
    total_samples = int(duration_sec * sr)
    t = np.linspace(0.0, duration_sec, total_samples, endpoint=False)

    num_octaves = 10
    f_min = 20.0
    f_max = f_min * (2.0 ** num_octaves)  # ~20480 Hz

    sign = 1.0 if direction == "ascending" else -1.0
    speed = sign * glissando_rate_oct_per_sec

    left_channel = np.zeros(total_samples, dtype=np.float64)
    right_channel = np.zeros(total_samples, dtype=np.float64)

    # Barberpole spatial pan angles
    azimuth = 2.0 * np.pi * barberpole_spin_hz * t

    for k in range(num_octaves):
        # Position in octave cycle: p(t) in [0, num_octaves)
        p = (k + speed * t) % num_octaves
        # Instantaneous frequency
        inst_freq = f_min * (2.0 ** p)

        # Spectral envelope: raised cosine bell curve over [0, num_octaves]
        env = 0.5 * (1.0 - np.cos(2.0 * np.pi * p / num_octaves))

        # Integrate frequency to phase: phi[n] = phi[n-1] + 2*pi*f[n]/fs
        phase = np.cumsum(2.0 * np.pi * inst_freq / sr)
        osc = np.sin(phase) * env

        # Barberpole panning per oscillator (each octave offset in spatial phase)
        pan_k = 0.5 * (1.0 + np.sin(azimuth + (2.0 * np.pi * k / num_octaves)))
        gain_L = np.cos(pan_k * (np.pi / 2.0))
        gain_R = np.sin(pan_k * (np.pi / 2.0))

        left_channel += osc * gain_L
        right_channel += osc * gain_R

    # Smooth fade in and out (0.5s)
    fade_len = int(min(sr * 0.5, total_samples // 4))
    if fade_len > 0:
        ramp = np.linspace(0.0, 1.0, fade_len) ** 2
        left_channel[:fade_len] *= ramp
        right_channel[:fade_len] *= ramp
        left_channel[-fade_len:] *= ramp[::-1]
        right_channel[-fade_len:] *= ramp[::-1]

    # Peak normalization
    peak = max(np.max(np.abs(left_channel)), np.max(np.abs(right_channel)))
    if peak > 1e-6:
        left_channel = (left_channel / peak) * 0.88
        right_channel = (right_channel / peak) * 0.88

    # Centralized export
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Shepard_Risset"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"Shepard_Risset_{direction}_{int(duration_sec)}s_{glissando_rate_oct_per_sec:.2f}oct_s.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    stereo_audio = np.stack([left_channel, right_channel], axis=1)
    int16_out = np.clip(stereo_audio * 32767.0, -32768, 32767).astype(np.int16)

    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_out.tobytes())

    return {
        "status": "SUCCESS",
        "direction": direction,
        "duration_sec": duration_sec,
        "glissando_rate_oct_per_sec": glissando_rate_oct_per_sec,
        "num_octaves": num_octaves,
        "f_min_hz": f_min,
        "f_max_hz": f_max,
        "barberpole_spin_hz": barberpole_spin_hz,
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = synthesize_shepard_risset_glissando(duration_sec=4.0, direction="ascending")
    print("Shepard-Risset Synthesizer Output:", res)
