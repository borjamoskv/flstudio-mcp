#!/usr/bin/env python3
"""
Multiband Transient & Tonal Envelope Shaper (v18.0 Demiurgic Nexus)
Implements a 3-band Linkwitz-Riley (LR4) crossover network and dual-envelope
ballistic differential detection for independent transient attack and sustain shaping.

Architecture:
- 3-band Linkwitz-Riley crossover (Low < 200Hz, Mid 200-3000Hz, High > 3000Hz)
  guaranteeing zero phase distortion and unity magnitude sum.
- Dual leaky integrator envelope follower:
  Fast ballistic (attack 2ms, release 15ms) vs. Slow ballistic (attack 20ms, release 120ms)
- Algebraic transient/sustain decomposition per frequency band
- Independent dB gain offsets for transient punch and sustain body
- Centralized WAV export to ~/Music/FL Studio Bounces/Transient_Shaper/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import signal

logger = logging.getLogger("FLStudio-TransientShaper")


def load_wav_as_mono_float(wav_path: str) -> Tuple[np.ndarray, int]:
    """Reads a WAV file and returns normalized mono float64 array and sample rate."""
    with wave.open(wav_path, "rb") as wf:
        num_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        num_frames = wf.getnframes()
        raw_bytes = wf.readframes(num_frames)

    if sampwidth == 2:
        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float64) / 32768.0
    elif sampwidth == 3:
        int_data = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3)
        int32 = (int_data[:, 0].astype(np.int32) |
                 (int_data[:, 1].astype(np.int32) << 8) |
                 (int_data[:, 2].astype(np.int32) << 16))
        int32 = np.where(int32 >= 0x800000, int32 - 0x1000000, int32)
        audio = int32.astype(np.float64) / 8388608.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float64) / 32768.0

    if num_channels > 1:
        audio = audio.reshape(-1, num_channels).mean(axis=1)
    return audio, framerate


def split_3band_linkwitz_riley(x: np.ndarray, sr: int, f_low: float = 200.0, f_high: float = 3000.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Splits audio into 3 bands using cascaded 2nd-order Butterworth filters (LR4 24 dB/octave).
    """
    nyq = sr / 2.0
    w_low = min(0.48, f_low / nyq)
    w_high = min(0.48, f_high / nyq)

    # Low-pass LR4 at f_low (two cascaded 2nd order Butterworth)
    sos_lp = signal.butter(2, w_low, btype="lowpass", output="sos")
    low_band = signal.sosfilt(sos_lp, signal.sosfilt(sos_lp, x))

    # High-pass LR4 at f_high
    sos_hp = signal.butter(2, w_high, btype="highpass", output="sos")
    high_band = signal.sosfilt(sos_hp, signal.sosfilt(sos_hp, x))

    # Mid band is residual to preserve perfect reconstruction
    mid_band = x - low_band - high_band
    return low_band, mid_band, high_band


def extract_transient_and_sustain(
    band_audio: np.ndarray,
    sr: int,
    fast_att_ms: float = 2.0,
    fast_rel_ms: float = 15.0,
    slow_att_ms: float = 20.0,
    slow_rel_ms: float = 120.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Decomposes a single band into transient attack and sustained decay components.
    """
    abs_x = np.abs(band_audio)

    # Ballistic filter coefficients: alpha = exp(-1 / (tau * fs))
    a_fast_att = math.exp(-1.0 / (fast_att_ms * 1e-3 * sr))
    a_fast_rel = math.exp(-1.0 / (fast_rel_ms * 1e-3 * sr))
    a_slow_att = math.exp(-1.0 / (slow_att_ms * 1e-3 * sr))
    a_slow_rel = math.exp(-1.0 / (slow_rel_ms * 1e-3 * sr))

    # Envelope follower
    n = len(band_audio)
    env_fast = np.zeros(n, dtype=np.float64)
    env_slow = np.zeros(n, dtype=np.float64)

    f_curr = 0.0
    s_curr = 0.0
    for i in range(n):
        val = abs_x[i]
        # Fast tracker
        if val > f_curr:
            f_curr = a_fast_att * f_curr + (1.0 - a_fast_att) * val
        else:
            f_curr = a_fast_rel * f_curr + (1.0 - a_fast_rel) * val
        env_fast[i] = f_curr

        # Slow tracker
        if val > s_curr:
            s_curr = a_slow_att * s_curr + (1.0 - a_slow_att) * val
        else:
            s_curr = a_slow_rel * s_curr + (1.0 - a_slow_rel) * val
        env_slow[i] = s_curr

    # Differential ratio: transient weight in [0, 1]
    eps = 1e-9
    diff = np.maximum(0.0, env_fast - env_slow)
    transient_ratio = np.clip(diff / (env_fast + eps), 0.0, 1.0)

    transient = band_audio * transient_ratio
    sustain = band_audio - transient
    return transient, sustain


def shape_multiband_transients(
    input_wav: Optional[str] = None,
    output_wav: Optional[str] = None,
    low_transient_db: float = 0.0,
    low_sustain_db: float = 2.0,
    mid_transient_db: float = 1.5,
    mid_sustain_db: float = 0.0,
    high_transient_db: float = 3.0,
    high_sustain_db: float = -1.0
) -> Dict[str, Any]:
    """
    Applies 3-band transient vs. sustain envelope shaping:
    - low: < 200 Hz (e.g. sub weight vs kick click)
    - mid: 200 - 3000 Hz (e.g. snare body vs attack)
    - high: > 3000 Hz (e.g. hi-hat crack vs cymbal wash)
    """
    if not input_wav:
        bounces_dir = Path.home() / "Music" / "FL Studio Bounces"
        default_wav = bounces_dir / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
        if not default_wav.exists():
            from scripts.fl_headless_audio_synthesizer import render_headless_dark_cyber_flamenco
            render_headless_dark_cyber_flamenco()
        in_file = default_wav
    else:
        in_file = Path(input_wav).expanduser().resolve()

    if not in_file.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_file}")

    audio, sr = load_wav_as_mono_float(str(in_file))

    # Split into 3 Linkwitz-Riley bands
    low_band, mid_band, high_band = split_3band_linkwitz_riley(audio, sr, f_low=200.0, f_high=3000.0)

    # Process each band
    t_low, s_low = extract_transient_and_sustain(low_band, sr)
    t_mid, s_mid = extract_transient_and_sustain(mid_band, sr)
    t_high, s_high = extract_transient_and_sustain(high_band, sr)

    # Apply dB gains
    g_t_low = 10.0 ** (low_transient_db / 20.0)
    g_s_low = 10.0 ** (low_sustain_db / 20.0)

    g_t_mid = 10.0 ** (mid_transient_db / 20.0)
    g_s_mid = 10.0 ** (mid_sustain_db / 20.0)

    g_t_high = 10.0 ** (high_transient_db / 20.0)
    g_s_high = 10.0 ** (high_sustain_db / 20.0)

    proc_low = t_low * g_t_low + s_low * g_s_low
    proc_mid = t_mid * g_t_mid + s_mid * g_s_mid
    proc_high = t_high * g_t_high + s_high * g_s_high

    recombined = proc_low + proc_mid + proc_high

    # Peak normalization
    peak = np.max(np.abs(recombined))
    if peak > 0.98:
        recombined = (recombined / peak) * 0.95

    # Export to centralized vault
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Transient_Shaper"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"{in_file.stem}_MultibandShaped.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    int16_audio = (recombined * 32767.0).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_audio.tobytes())

    return {
        "status": "SUCCESS",
        "input_file": str(in_file),
        "gains_applied_db": {
            "low_transient": low_transient_db,
            "low_sustain": low_sustain_db,
            "mid_transient": mid_transient_db,
            "mid_sustain": mid_sustain_db,
            "high_transient": high_transient_db,
            "high_sustain": high_sustain_db
        },
        "crossover_frequencies_hz": [200.0, 3000.0],
        "duration_sec": round(len(audio) / sr, 2),
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = shape_multiband_transients(high_transient_db=3.0, low_sustain_db=2.0)
    print("Multiband Transient Shaper Output:", res)
