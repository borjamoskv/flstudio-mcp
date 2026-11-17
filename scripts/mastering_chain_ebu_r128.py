#!/usr/bin/env python3
"""
EBU R128 / ITU-R BS.1770-4 Mastering Chain & True-Peak Limiter (v16.0 C5-REAL)
==============================================================================
Broadcast & Club mastering suite upgraded with:
  1. Sample-rate-adaptive ITU-R BS.1770-4 K-weighting + two-stage EBU R128 gating (-70 LUFS / -10 LU)
  2. Exact Zero-Phase 4th-Order Linkwitz-Riley (LR4, 24 dB/oct) crossover (<120 Hz 100% Mono, zero phase notch)
  3. Stereo-linked VCA glue compression (28 ms attack / 90 ms release) + 4x oversampled soft saturation
  4. 4x oversampled stereo-linked lookahead gain-envelope True-Peak limiter (ISP-verified)
  5. Lipshitz-Vanderkooy high-pass TPDF dithering (24-bit & 16-bit export) + Rubin metrology
"""

from __future__ import annotations

import logging
import sys
import wave
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from scripts.bounces_paths import resolve_bounces_dir  # noqa: E402
from scripts.mastering_reverse_engine_fl import (  # noqa: E402
    FLReverseMasteringDSP,
    apply_k_weighting,
    compute_integrated_lufs,
    compute_loudness_range_lu,
    compute_rubin_metrics,
    compute_true_peak_dbtp,
    load_wav_stereo,
)

logger = logging.getLogger("FLStudio-MasteringChain")


def load_wav_stereo_float(wav_path: str) -> Tuple[np.ndarray, int]:
    """Reads a 16/24/32-bit WAV file and returns normalized stereo float64 array (N, 2) and sample rate."""
    return load_wav_stereo(wav_path)


def apply_k_weighting_filter(audio_stereo: np.ndarray, sample_rate: int) -> np.ndarray:
    """Applies sample-rate-adaptive ITU-R BS.1770-4 Stage 1 High-Shelf and Stage 2 RLB High-Pass filters."""
    return apply_k_weighting(audio_stereo, sample_rate)


def calculate_integrated_lufs(audio_stereo: np.ndarray, sample_rate: int) -> float:
    """Computes ITU-R BS.1770-4 / EBU R128 Gated Integrated Loudness (LUFS/LKFS)."""
    return compute_integrated_lufs(audio_stereo, sample_rate)


def calculate_true_peak_dbtp(audio_stereo: np.ndarray) -> float:
    """Calculates True Peak in dBTP via 4x polyphase oversampling."""
    return compute_true_peak_dbtp(audio_stereo)


def master_audio_ebu_r128(
    input_wav: str,
    output_wav: Optional[str] = None,
    target_lufs: float = -14.0,
    target_true_peak_dbtp: float = -1.0,
    bass_mono_crossover_hz: float = 120.0,
    bit_depth: int = 24,
) -> Dict[str, Any]:
    """
    Executes a complete EBU R128 / C5-REAL mastering pass on input audio:
      1. Zero-phase LR4 mono-maker crossover below `bass_mono_crossover_hz` (120 Hz, zero phase hole)
      2. Gentle VCA bus glue (28 ms attack / 90 ms release) preserving transient punch
      3. ITU-R BS.1770-4 gated loudness normalization with crest-factor protection
      4. 4x oversampled lookahead envelope True-Peak brickwall limiting + high-pass TPDF dither
    """
    in_path = Path(input_wav).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_path}")

    audio_stereo, sample_rate = load_wav_stereo_float(str(in_path))

    lufs_before = calculate_integrated_lufs(audio_stereo, sample_rate)
    peak_dbtp_before = calculate_true_peak_dbtp(audio_stereo)
    lra_before = compute_loudness_range_lu(audio_stereo, sample_rate)

    is_club_loudness = target_lufs > -11.5
    profile = {
        "lowest_freq": 28.0,
        "mono_crossover_hz": float(bass_mono_crossover_hz),
        "side_high_boost_db": 0.8 if is_club_loudness else 0.5,
        "vca_threshold_db": -13.5 if is_club_loudness else -15.5,
        "mid_glue_ratio": 2.4 if is_club_loudness else 1.8,
        "vca_attack_ms": 28.0,
        "vca_release_ms": 90.0,
        "soft_clipper_drive_db": 1.6 if is_club_loudness else 0.6,
    }

    dsp = FLReverseMasteringDSP(sample_rate, profile)

    # 1. Zero-phase subsonic clean + LR4 (<120 Hz) mono consolidation + M/S air
    s1 = dsp.stage1_linear_phase_eq_and_mid_side(audio_stereo)

    # 2. VCA Master Bus Glue Compressor
    s2 = dsp.stage2_multiband_dynamics_glue(s1)

    # 3. Gated Loudness Normalization with Crest-Factor protection
    lufs_current = calculate_integrated_lufs(s2, sample_rate)
    tp_current = calculate_true_peak_dbtp(s2)
    max_safe_push = (target_true_peak_dbtp - tp_current) + 3.8
    gain_db = float(np.clip(min(target_lufs - lufs_current, max_safe_push), -14.0, 14.0))
    gained_audio = s2 * (10.0 ** (gain_db / 20.0))

    # 4. 4x Oversampled Soft Clipper + 4x Lookahead Envelope True-Peak Limiter
    s3 = dsp.stage3_fruity_soft_clipper(gained_audio)
    s4 = dsp.stage4_true_peak_lookahead_limiter(s3, target_true_peak_dbtp)

    # Fine loudness trim if headroom permits
    post_lufs = calculate_integrated_lufs(s4, sample_rate)
    post_rubin = compute_rubin_metrics(s4[:, 0], s4[:, 1], sample_rate=sample_rate)
    if abs(target_lufs - post_lufs) > 0.6 and post_rubin["crest_factor_db"] > 9.4:
        trim_db = float(np.clip(target_lufs - post_lufs, -1.8, 1.8))
        cand = dsp.stage4_true_peak_lookahead_limiter(
            s4 * (10.0 ** (trim_db / 20.0)), target_true_peak_dbtp
        )
        if compute_rubin_metrics(cand[:, 0], cand[:, 1], sample_rate=sample_rate)["crest_factor_db"] >= 8.3:
            s4 = cand
            gain_db += trim_db

    # 5. High-Pass TPDF Dithering bounded strictly inside True Peak ceiling
    ceiling_lin = 10.0 ** ((target_true_peak_dbtp - 0.02) / 20.0)
    mastered_stereo = np.clip(
        dsp.stage5_psychoacoustic_tpdf_dither(s4, bit_depth=bit_depth),
        -ceiling_lin,
        ceiling_lin,
    )

    lufs_after = calculate_integrated_lufs(mastered_stereo, sample_rate)
    peak_dbtp_after = calculate_true_peak_dbtp(mastered_stereo)
    lra_after = compute_loudness_range_lu(mastered_stereo, sample_rate)
    rubin_after = compute_rubin_metrics(
        mastered_stereo[:, 0], mastered_stereo[:, 1], sample_rate=sample_rate
    )

    out_dir = resolve_bounces_dir() / "Master"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        stem_name = in_path.stem
        output_file = out_dir / f"{stem_name}_Mastered_EBUR128.wav"
    else:
        output_file = Path(output_wav).expanduser().resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(output_file), "wb") as wf:
        wf.setnchannels(2)
        wf.setframerate(sample_rate)
        if bit_depth == 24:
            wf.setsampwidth(3)
            i32 = np.clip(np.round(mastered_stereo * 8388607.0), -8388608, 8388607).astype("<i4")
            b24 = i32.flatten().view(np.uint8).reshape(-1, 4)[:, :3]
            wf.writeframes(b24.tobytes())
        else:
            wf.setsampwidth(2)
            i16 = np.clip(np.round(mastered_stereo * 32767.0), -32768, 32767).astype("<i2")
            wf.writeframes(i16.tobytes())

    return {
        "status": "SUCCESS",
        "standard": "EBU_R128_ITU_R_BS1770_4_GATED_LR4",
        "input_file": str(in_path),
        "target_integrated_lufs": target_lufs,
        "target_true_peak_dbtp": target_true_peak_dbtp,
        "lufs_before": lufs_before,
        "lufs_after": lufs_after,
        "lra_lu_before": lra_before,
        "lra_lu_after": lra_after,
        "true_peak_dbtp_before": peak_dbtp_before,
        "true_peak_dbtp_after": peak_dbtp_after,
        "gain_applied_db": round(gain_db, 2),
        "bass_mono_crossover_hz": bass_mono_crossover_hz,
        "crossover_topology": "Zero-Phase LR4 (24 dB/oct)",
        "bit_depth": bit_depth,
        "sample_rate_hz": sample_rate,
        "duration_sec": round(len(mastered_stereo) / sample_rate, 2),
        "rubin_audit": rubin_after,
        "output_file": str(output_file),
        "file_size_kb": round(output_file.stat().st_size / 1024, 1),
    }


if __name__ == "__main__":
    test_in = resolve_bounces_dir() / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    if test_in.exists():
        res = master_audio_ebu_r128(str(test_in))
        print("Mastering Suite output:", res)
    else:
        print("Test file not found:", test_in)
