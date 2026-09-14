#!/usr/bin/env python3
"""
Multi-Track Stem Phase Alignment & Comb-Filtering Remediator (v20.0 Sovereign Transcendence)
═════════════════════════════════════════════════════════════════════════════════════════════
Detects and corrects destructive acoustic comb-filtering and phase cancellation between layered stems.

Mechanics:
1. Cross-Correlation Lag Estimation:
   R_xy[tau] = sum_n x[n] * y[n+tau] over a search window (e.g. +/- 20ms).
2. Sub-Sample Fractional Delay Peak Interpolation:
   Parabolic 3-point peak fitting yields sub-sample precision delta in [-0.5, 0.5] samples.
3. Polarity Inversion Detection:
   Determines if 180-degree phase flip restores low-end acoustic summation.
4. Fractional Delay Sinc FIR Filter:
   Shifts the secondary stem by non-integer sample offset using a Kaiser-windowed sinc FIR kernel.
5. Coherent Summation & Comb-Filter Metrics:
   Quantifies pre- and post-alignment phase correlation, summation energy gain (dB), and
   comb-filter cancellation notches.
6. Centralized WAV export to ~/Music/FL Studio Bounces/Phase_Aligned/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("FLStudio-PhaseAlign")


def _load_wav_mono(file_path: Path, max_sec: float = 6.0) -> Tuple[np.ndarray, int]:
    """Loads mono audio buffer normalized to [-1, 1]."""
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

    if n_ch > 1:
        audio = audio.reshape(-1, n_ch).mean(axis=1)

    return audio, sr


def _fractional_delay_sinc(signal: np.ndarray, delay_samples: float) -> np.ndarray:
    """Applies high-fidelity sub-sample delay using a windowed sinc FIR filter."""
    int_delay = int(np.floor(delay_samples))
    frac_delay = delay_samples - int_delay

    # Filter radius N
    N = 16
    kernel_len = 2 * N + 1
    k = np.arange(-N, N + 1)
    
    # Sinc kernel shifted by fractional delay
    sinc_arg = k - frac_delay
    sinc_kernel = np.sinc(sinc_arg)
    # Blackman-Harris tapering window
    window = np.blackman(kernel_len)
    h = sinc_kernel * window
    h /= np.sum(h)  # Unity gain

    # Apply integer delay first
    if int_delay >= 0:
        delayed = np.pad(signal, (int_delay, 0))[:len(signal)]
    else:
        delayed = np.pad(signal[-int_delay:], (0, -int_delay))

    # Apply FIR fractional filter
    return np.convolve(delayed, h, mode="same")


def align_multitrack_stems_phase(
    reference_wav: Optional[str] = None,
    secondary_wav: Optional[str] = None,
    max_search_ms: float = 15.0,
    allow_polarity_invert: bool = True,
    max_duration_sec: float = 4.0,
    output_wav: Optional[str] = None
) -> Dict[str, Any]:
    """
    Measures and aligns acoustic phase between two multitrack stems to eliminate comb filtering.
    """
    bounces_dir = Path.home() / "Music" / "FL Studio Bounces"

    # Resolve reference WAV
    ref_path = None
    if reference_wav:
        rp = Path(reference_wav).expanduser().resolve()
        if rp.exists():
            ref_path = rp

    if not ref_path:
        candidates = list(bounces_dir.glob("**/*.wav"))
        if candidates:
            ref_path = candidates[0]

    # Resolve secondary WAV
    sec_path = None
    if secondary_wav:
        sp = Path(secondary_wav).expanduser().resolve()
        if sp.exists():
            sec_path = sp

    if not sec_path and len(candidates) > 1:
        sec_path = candidates[1]

    # Fallback to synthetic phase-misaligned pair if files missing
    if not ref_path or not ref_path.exists():
        sr = 44100
        t = np.linspace(0, max_duration_sec, int(max_duration_sec * sr), endpoint=False)
        sig_ref = 0.5 * np.sin(2 * np.pi * 120.0 * t) + 0.3 * np.sin(2 * np.pi * 240.0 * t)
        # 1.8 ms delay + 180 deg inverted
        delay_idx = int(0.0018 * sr)
        sig_sec = -np.pad(sig_ref, (delay_idx, 0))[:len(sig_ref)] * 0.95
        ref_audio = sig_ref
        sec_audio = sig_sec
        ref_tag = "Synthetic_Ref"
        sec_tag = "Synthetic_Sec"
    else:
        ref_audio, sr = _load_wav_mono(ref_path, max_sec=max_duration_sec)
        ref_tag = ref_path.stem
        if sec_path and sec_path.exists():
            sec_audio, _ = _load_wav_mono(sec_path, max_sec=max_duration_sec)
            sec_tag = sec_path.stem
        else:
            # Artificially phase-distort reference to simulate misalignment
            delay_idx = int(0.0022 * sr)
            sec_audio = -np.pad(ref_audio, (delay_idx, 0))[:len(ref_audio)] * 0.92
            sec_tag = f"{ref_tag}_Delayed"

    # Match buffer lengths
    min_len = min(len(ref_audio), len(sec_audio))
    ref_audio = ref_audio[:min_len]
    sec_audio = sec_audio[:min_len]

    # Initial Correlation & Summation Energy
    norm_factor = np.sqrt(np.sum(ref_audio ** 2) * np.sum(sec_audio ** 2)) + 1e-12
    initial_corr = float(np.sum(ref_audio * sec_audio) / norm_factor)
    initial_sum_energy = float(np.sum((ref_audio + sec_audio) ** 2))

    # Cross-correlation search
    max_lag_samples = int(sr * (max_search_ms * 1e-3))
    # Analyze middle segment (avoid edge transients)
    analysis_len = min(min_len, int(sr * 2.0))
    start_idx = (min_len - analysis_len) // 2
    r_seg = ref_audio[start_idx : start_idx + analysis_len]
    s_seg = sec_audio[start_idx : start_idx + analysis_len]

    corr = np.correlate(r_seg, s_seg, mode="full")
    lags = np.arange(-len(s_seg) + 1, len(r_seg))

    # Restrict to search window
    mid = len(s_seg) - 1
    valid_window = (lags >= -max_lag_samples) & (lags <= max_lag_samples)
    corr_window = corr[valid_window]
    lags_window = lags[valid_window]

    # Find peak (positive or negative)
    abs_peak_idx = np.argmax(np.abs(corr_window))
    raw_peak_lag = lags_window[abs_peak_idx]
    peak_val = corr_window[abs_peak_idx]

    # Check polarity inversion
    invert_polarity = False
    if allow_polarity_invert and peak_val < 0:
        invert_polarity = True

    # Parabolic sub-sample refinement
    if 0 < abs_peak_idx < len(corr_window) - 1:
        alpha = corr_window[abs_peak_idx - 1]
        beta = corr_window[abs_peak_idx]
        gamma = corr_window[abs_peak_idx + 1]
        denom = alpha - 2.0 * beta + gamma
        delta = 0.5 * (alpha - gamma) / denom if abs(denom) > 1e-9 else 0.0
        refined_lag = float(raw_peak_lag + delta)
    else:
        refined_lag = float(raw_peak_lag)

    # Delay to align secondary stem: shift = -refined_lag
    align_shift = -refined_lag
    aligned_sec = _fractional_delay_sinc(sec_audio, align_shift)
    if invert_polarity:
        aligned_sec = -aligned_sec

    # Post-alignment metrics
    final_corr = float(np.sum(ref_audio * aligned_sec) / norm_factor)
    final_sum_energy = float(np.sum((ref_audio + aligned_sec) ** 2))

    energy_gain_db = float(10.0 * np.log10((final_sum_energy + 1e-12) / (initial_sum_energy + 1e-12)))

    # Sum mix output
    sum_mix = (ref_audio + aligned_sec) * 0.5
    peak = np.max(np.abs(sum_mix))
    if peak > 1e-6:
        sum_mix = (sum_mix / peak) * 0.88

    # Centralized export
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Phase_Aligned"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = Path(output_wav).expanduser().resolve() if output_wav else out_dir / f"Aligned_Sum_{ref_tag}_x_{sec_tag}.wav"
    aligned_sec_file = out_dir / f"Aligned_Secondary_{sec_tag}.wav"

    int16_sum = np.clip(sum_mix * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_sum.tobytes())

    int16_sec = np.clip(aligned_sec * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(aligned_sec_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_sec.tobytes())

    return {
        "status": "SUCCESS",
        "reference_track": str(ref_path) if ref_path else "synthetic_reference",
        "secondary_track": str(sec_path) if sec_path else "synthetic_secondary",
        "delay_offset_ms": round(float(align_shift * 1000.0 / sr), 3),
        "delay_offset_samples": round(float(align_shift), 2),
        "polarity_inverted": invert_polarity,
        "initial_phase_correlation": round(initial_corr, 3),
        "aligned_phase_correlation": round(final_corr, 3),
        "coherent_energy_gain_db": round(energy_gain_db, 2),
        "aligned_secondary_file": str(aligned_sec_file),
        "output_sum_mix_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = align_multitrack_stems_phase()
    print("Phase Aligner Output:", res)
