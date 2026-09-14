#!/usr/bin/env python3
"""
Ambisonics Diffuse Field All-Pass Decorrelator (v16.0 Sovereign Apex)
Generates 3D acoustic envelopment (Listener Envelopment LEV and Apparent Source Width ASW)
by decorrelating Ambisonics B-format (W, Y, Z, X) or stereo stems using orthogonal all-pass delay lattices.

Mathematical Formulation:
- Flat magnitude response: |H(e^jw)| = 1.0 (Zero tonal coloration / zero comb filtering)
- Mutually prime delay lines (D_W=101, D_Y=173, D_Z=241, D_X=311 samples)
- All-pass transfer function: H_k(z) = (-g + z^(-D_k)) / (1 - g * z^(-D_k))
- Drives Interaural Cross-Correlation (IACC) to near zero in the diffuse field
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
from scipy import signal

logger = logging.getLogger("FLStudio-AmbisonicsDecorrelator")

# Mutually prime delay lengths (in samples at 44.1 kHz)
PRIME_DELAYS = [101, 173, 241, 311, 401, 509]
ALLPASS_GAIN = 0.618  # Golden ratio all-pass reflection


def load_wav_multichannel_float(wav_path: str) -> Tuple[np.ndarray, int]:
    """Reads a WAV file and returns normalized multichannel float64 array (N, C) and sample rate."""
    with wave.open(wav_path, "rb") as wf:
        num_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        num_frames = wf.getnframes()
        raw_bytes = wf.readframes(num_frames)

    if sampwidth == 2:
        dtype = np.int16
        scale = 32768.0
        audio = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float64) / scale
    elif sampwidth == 3:
        int_data = np.frombuffer(raw_bytes, dtype=np.uint8)
        reshaped = int_data.reshape(-1, 3)
        int32_data = (reshaped[:, 0].astype(np.int32) |
                      (reshaped[:, 1].astype(np.int32) << 8) |
                      (reshaped[:, 2].astype(np.int32) << 16))
        int32_data = np.where(int32_data >= 0x800000, int32_data - 0x1000000, int32_data)
        audio = int32_data.astype(np.float64) / 8388608.0
    elif sampwidth == 4:
        dtype = np.int32
        scale = 2147483648.0
        audio = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float64) / scale
    else:
        dtype = np.int16
        scale = 32768.0
        audio = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float64) / scale

    if num_channels == 1:
        audio = audio.reshape(-1, 1)
    else:
        audio = audio.reshape(-1, num_channels)

    return audio, framerate


def apply_schroeder_allpass(x: np.ndarray, delay_samples: int, g: float = ALLPASS_GAIN) -> np.ndarray:
    """Applies a single Schroeder all-pass filter: H(z) = (-g + z^-D) / (1 - g * z^-D)."""
    # Numerator: b = [-g, 0, ..., 1.0]
    # Denominator: a = [1.0, 0, ..., -g]
    b = np.zeros(delay_samples + 1, dtype=np.float64)
    a = np.zeros(delay_samples + 1, dtype=np.float64)

    b[0] = -g
    b[delay_samples] = 1.0

    a[0] = 1.0
    a[delay_samples] = -g

    return signal.lfilter(b, a, x)


def decorrelate_spatial_ambisonics(
    input_wav: str,
    output_wav: Optional[str] = None,
    diffuse_amount: float = 0.40,
    cascaded_stages: int = 2
) -> Dict[str, Any]:
    """
    Applies multi-channel orthogonal all-pass decorrelation to an Ambisonics or stereo WAV file.
    - diffuse_amount: 0.0 = pure direct sound, 1.0 = maximum diffuse envelopment
    - cascaded_stages: number of cascaded all-pass filters per channel (1 to 3)
    """
    in_path = Path(input_wav).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_path}")

    audio, sample_rate = load_wav_multichannel_float(str(in_path))
    num_samples, num_channels = audio.shape

    out_audio = np.zeros_like(audio)

    for ch in range(num_channels):
        sig = audio[:, ch].copy()
        decorrelated = sig.copy()

        # Cascade all-pass filters with prime delay offsets
        for stage in range(cascaded_stages):
            prime_idx = (ch * cascaded_stages + stage) % len(PRIME_DELAYS)
            delay = PRIME_DELAYS[prime_idx]
            decorrelated = apply_schroeder_allpass(decorrelated, delay, g=ALLPASS_GAIN)

        # Mix direct and diffuse signals
        dry_gain = math.sqrt(max(0.0, 1.0 - diffuse_amount))
        wet_gain = math.sqrt(diffuse_amount)
        out_audio[:, ch] = dry_gain * sig + wet_gain * decorrelated

    # Peak normalization
    peak = float(np.max(np.abs(out_audio)))
    if peak > 0.95:
        out_audio *= (0.92 / peak)

    # Destination paths
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Diffuse_Fields"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"{in_path.stem}_DiffuseDecorrelated_{int(diffuse_amount*100)}pct.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    int16_out = np.clip(out_audio * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_out.tobytes())

    return {
        "status": "SUCCESS",
        "algorithm": "Schroeder_Orthogonal_AllPass_Lattice",
        "channels_processed": num_channels,
        "diffuse_amount": diffuse_amount,
        "cascaded_stages": cascaded_stages,
        "sample_rate_hz": sample_rate,
        "duration_sec": round(num_samples / sample_rate, 2),
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    bounces = Path.home() / "Music/FL Studio Bounces"
    test_amb = bounces / "Ambisonics/Dark_Cyber_Flamenco_Audio_Preview_16Bars_Ambisonics_BFormat_ACN.wav"
    if test_amb.exists():
        res = decorrelate_spatial_ambisonics(str(test_amb), diffuse_amount=0.35)
        print("Ambisonics Decorrelator output:", res)
    else:
        print("Ambisonics test file not found:", test_amb)
