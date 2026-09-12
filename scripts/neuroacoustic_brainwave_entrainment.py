#!/usr/bin/env python3
"""
C5-REAL Neuroacoustic Brainwave Entrainment Synthesizer
═══════════════════════════════════════════════════════
Generates phase-coherent Binaural Beats and Isochronic Pulses
mathematically tuned to the musical key (D Phrygian / 112 BPM)
for cognitive focus (40 Hz Gamma) and meditative trance (6 Hz Theta).

Acoustic Physics:
- Carrier frequency f0 tuned to root harmonic (e.g. D2 = 73.42 Hz, D3 = 146.83 Hz)
- Left Channel: f_left = f0 - (delta_f / 2)
- Right Channel: f_right = f0 + (delta_f / 2)
- Brainwave Frequency: delta_f = |f_right - f_left| (40 Hz Gamma, 6 Hz Theta)
"""

import sys
import math
import wave
import struct
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

MUSIC_BOUNCES_DIR = Path.home() / "Music" / "FL Studio Bounces"


def synthesize_entrainment_stem(
    wave_type: str = "gamma_40hz",
    duration_sec: float = 34.29,  # 16 bars at 112 BPM
    carrier_freq_hz: float = 146.83,  # D3 root harmonic
    sample_rate: int = 44100,
    amplitude: float = 0.25
) -> Dict[str, Any]:
    """
    Synthesizes neuroacoustic entrainment audio track:
    - 'gamma_40hz': 40 Hz Gamma binaural beat (focus, analytical binding)
    - 'theta_6hz': 6 Hz Theta binaural beat (deep trance, meditative flow)
    - 'isochronic_gamma': 40 Hz Isochronic pulse with Hann amplitude modulation
    """
    if wave_type == "gamma_40hz":
        delta_f = 40.0
        mode = "binaural"
    elif wave_type == "theta_6hz":
        delta_f = 6.0
        mode = "binaural"
    elif wave_type == "isochronic_gamma":
        delta_f = 40.0
        mode = "isochronic"
    else:
        delta_f = 40.0
        mode = "binaural"

    f_left = carrier_freq_hz - (delta_f / 2.0)
    f_right = carrier_freq_hz + (delta_f / 2.0)

    total_frames = int(sample_rate * duration_sec)
    two_pi = 2.0 * math.pi
    raw_bytes = bytearray()

    fade_frames = int(sample_rate * 0.05)  # 50ms fade-in/out to prevent pop

    for i in range(total_frames):
        t = i / float(sample_rate)

        # Micro fade envelope
        env = 1.0
        if i < fade_frames:
            env = i / float(fade_frames)
        elif i > total_frames - fade_frames:
            env = (total_frames - i) / float(fade_frames)

        if mode == "binaural":
            s_l = amplitude * env * math.sin(two_pi * f_left * t)
            s_r = amplitude * env * math.sin(two_pi * f_right * t)
        else:  # isochronic
            mod = 0.5 * (1.0 + math.cos(two_pi * delta_f * t))  # Hann pulse
            carrier = math.sin(two_pi * carrier_freq_hz * t)
            s_l = amplitude * env * mod * carrier
            s_r = s_l

        # Clamping
        int_l = int(max(-32767, min(32767, s_l * 32767.0)))
        int_r = int(max(-32767, min(32767, s_r * 32767.0)))

        raw_bytes += struct.pack("<hh", int_l, int_r)

    out_dir = MUSIC_BOUNCES_DIR / "Neuroacoustics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_wav = out_dir / f"Neuroacoustic_{wave_type}_{int(carrier_freq_hz)}Hz_Carrier.wav"

    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_bytes)

    return {
        "status": "SUCCESS",
        "wave_type": wave_type,
        "entrainment_freq_hz": delta_f,
        "carrier_freq_hz": carrier_freq_hz,
        "duration_sec": duration_sec,
        "output_file": str(out_wav),
        "file_size_kb": round(out_wav.stat().st_size / 1024.0, 1)
    }


if __name__ == "__main__":
    res_gamma = synthesize_entrainment_stem("gamma_40hz")
    res_theta = synthesize_entrainment_stem("theta_6hz")
    print(f"Synthesized Gamma: {res_gamma['output_file']}")
    print(f"Synthesized Theta: {res_theta['output_file']}")
