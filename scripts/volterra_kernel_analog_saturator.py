#!/usr/bin/env python3
"""
Volterra Kernel Non-Linear Analog Saturator & Memory Modeler (v21.0 Hyper-Spatial Continuum)
═══════════════════════════════════════════════════════════════════════════════════════════
Implements discrete Volterra series expansion to model analog hardware with memory:
audio transformers, magnetic tape hysteresis, and non-linear vacuum tube circuits.

Mathematical Mechanics:
1. Truncated Multi-Order Volterra Series:
   y[n] = sum_{m} h1[m]*x[n-m] + alpha2 * sum_{m} h2[m]*(x[n-m])^2 + alpha3 * sum_{m} h3[m]*(x[n-m])^3
2. 1st-Order Kernel h1: Models linear frequency-dependent transformer impedance and low-end warmth.
3. 2nd-Order Kernel h2: Models asymmetrical even-harmonic dynamic memory (triode valve warmth).
4. 3rd-Order Kernel h3: Models symmetrical odd-harmonic compression and magnetic saturation (tape head).
5. Dynamic memory decay: Kernels decay exponentially, accurately simulating physical hysteresis.
6. Centralized WAV export to ~/Music/FL Studio Bounces/Volterra_Analog/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("FLStudio-Volterra")


def _load_wav_stereo(file_path: Path, max_sec: float = 6.0) -> Tuple[np.ndarray, int]:
    """Loads stereo/mono audio normalized to [-1.0, 1.0] float64."""
    with wave.open(str(file_path), "rb") as wf:
        n_ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        n_frames = min(wf.getnframes(), int(sr * max_sec))
        raw = wf.readframes(n_frames)

    if sw == 2:
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sw == 3:
        a8 = np.frombuffer(raw, dtype=np.uint8)
        a24 = (a8[0::3].astype(np.int32)) | (a8[1::3].astype(np.int32) << 8) | (a8[2::3].astype(np.int32) << 16)
        a24[a24 >= 0x800000] -= 0x1000000
        audio = a24.astype(np.float64) / 8388608.0
    elif sw == 4:
        audio = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        audio = np.frombuffer(raw, dtype=np.uint8).astype(np.float64) / 128.0 - 1.0

    if n_ch == 1:
        audio = np.column_stack([audio, audio])
    else:
        audio = audio.reshape(-1, n_ch)
        if audio.shape[1] > 2:
            audio = audio[:, :2]

    return audio, sr


def saturate_volterra_kernel_analog(
    input_wav: Optional[str] = None,
    drive_db: float = 4.5,
    transformer_iron: float = 0.60,
    triode_warmth: float = 0.40,
    tape_saturation: float = 0.50,
    mix_wet: float = 1.0,
    max_duration_sec: float = 4.0,
    output_wav: Optional[str] = None
) -> Dict[str, Any]:
    """
    Applies non-linear dynamic Volterra series saturation with acoustic/circuit memory.
    """
    target_path = None
    if input_wav:
        p = Path(input_wav).expanduser().resolve()
        if p.exists():
            target_path = p

    bounces_dir = Path.home() / "Music" / "FL Studio Bounces"

    if not target_path:
        candidates = list(bounces_dir.glob("**/*.wav"))
        if candidates:
            target_path = candidates[0]

    if not target_path or not target_path.exists():
        sr = 44100
        t = np.linspace(0, max_duration_sec, int(max_duration_sec * sr), endpoint=False)
        sig = 0.6 * np.sin(2 * np.pi * 180.0 * t) + 0.2 * np.sin(2 * np.pi * 360.0 * t)
        audio = np.column_stack([sig, sig])
        filename_tag = "Synthetic_Harmonic_Bus"
    else:
        audio, sr = _load_wav_stereo(target_path, max_sec=max_duration_sec)
        filename_tag = target_path.stem

    num_samples, channels = audio.shape
    gain_linear = 10.0 ** (drive_db / 20.0)

    # Construct Volterra memory kernels
    # Kernel length M = 32 samples (~0.72 ms at 44.1 kHz, sufficient for magnetic/core memory)
    M = 32
    m_idx = np.arange(M)

    # 1st-order kernel h1: Transformer frequency tilt (low-mid resonance + mild damping)
    omega_core = 2.0 * np.pi * 80.0 / sr
    h1 = np.exp(-m_idx / 8.0) * np.cos(omega_core * m_idx)
    h1 = (1.0 - 0.3 * transformer_iron) * (m_idx == 0) + 0.3 * transformer_iron * (h1 / np.sum(np.abs(h1)))

    # 2nd-order kernel h2: Asymmetric even harmonic memory (triode valve)
    h2 = triode_warmth * 0.25 * np.exp(-m_idx / 6.0)
    h2 /= (np.sum(np.abs(h2)) + 1e-12)
    h2 *= triode_warmth * 0.25

    # 3rd-order kernel h3: Symmetrical odd harmonic memory (tape hysteresis / iron core)
    h3 = tape_saturation * 0.35 * np.exp(-m_idx / 10.0)
    h3 /= (np.sum(np.abs(h3)) + 1e-12)
    h3 *= tape_saturation * 0.35

    out_audio = np.zeros_like(audio)

    for ch in range(channels):
        in_ch = audio[:, ch] * gain_linear

        # 1st-order linear term: convolution with h1
        y1 = np.convolve(in_ch, h1, mode="same")

        # 2nd-order non-linear term: convolution of x^2 with h2
        y2 = np.convolve(in_ch ** 2, h2, mode="same")

        # 3rd-order non-linear term: convolution of x^3 with h3
        y3 = np.convolve(in_ch ** 3, h3, mode="same")

        # Composite Volterra response: y[n] = y1 + y2 - y3 (odd term provides natural compressive saturation)
        y_volterra = y1 + y2 - y3

        # Soft diode clip to guarantee physical stability
        y_saturated = np.tanh(y_volterra)

        # Wet / Dry mix
        out_ch = (1.0 - mix_wet) * audio[:, ch] + mix_wet * y_saturated
        out_audio[:, ch] = out_ch

    # Peak normalization
    peak = np.max(np.abs(out_audio))
    if peak > 1e-6:
        out_audio = (out_audio / peak) * 0.88

    # Centralized export
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Volterra_Analog"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"Volterra_{filename_tag}_{drive_db:.1f}dB_Iron{int(transformer_iron*100)}_Tape{int(tape_saturation*100)}.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    int16_out = np.clip(out_audio * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_out.tobytes())

    return {
        "status": "SUCCESS",
        "input_source": str(target_path) if target_path else "synthetic_reference",
        "drive_db": drive_db,
        "transformer_iron": transformer_iron,
        "triode_warmth": triode_warmth,
        "tape_saturation": tape_saturation,
        "volterra_kernel_length": M,
        "mix_wet": mix_wet,
        "duration_sec": round(num_samples / sr, 2),
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = saturate_volterra_kernel_analog(drive_db=5.0, transformer_iron=0.7)
    print("Volterra Saturator Output:", res)
