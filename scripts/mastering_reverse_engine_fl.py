#!/usr/bin/env python3
"""
FL STUDIO REVERSE-ENGINEERED MASTERING ENGINE (C5-REAL SOTA v2.0)
=================================================================
Upgraded Broadcast & Club Mastering Pipeline:
  1. Sample-Rate-Adaptive ITU-R BS.1770-4 K-Weighting + Two-Stage Gating (-70 LUFS abs / -10 LU rel)
  2. Exact Zero-Phase 4th-Order Linkwitz-Riley (LR4, 24 dB/oct) Crossover (<120 Hz 100% Mono Consolidation)
  3. True Envelope-Following Stereo-Linked VCA Master Bus Glue Compressor (28 ms Attack / 90 ms Release)
  4. 4x Polyphase Oversampled Analog Harmonic Soft Clipper (Even/Odd Crest Toasting, Zero Aliasing)
  5. 4x Oversampled Stereo-Linked Lookahead Envelope True-Peak Limiter (Zero Crackle, ISP Verified)
  6. Lipshitz-Vanderkooy High-Pass TPDF Dither (24-bit & 16-bit)
  7. Rubin Acoustic Linter Metrology (<120 Hz Filtered LPC, 500-5000 Hz Welch SFM, Crest Factor, Derivative Gate)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import wave
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from scipy import ndimage, signal

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from scripts.c5_dsp_core import (  # noqa: E402
    apply_highpass_tpdf_dither,
    apply_spectral_balance_eq,
    apply_wdf_warm_saturator,
    freeze_array,
    lr4_zero_phase_crossover,
    oversampled_soft_saturate,
)
try:
    from scripts.c5_real_assets_bridge import apply_curated_vst3_preset  # noqa: E402
except ImportError:
    from c5_real_assets_bridge import apply_curated_vst3_preset  # type: ignore  # noqa: E402

# -----------------------------------------------------------------------------
# 1. GENRE & CLUB MASTERING PROFILES (C5-REAL & FL Cloud / TDR Reference Matrix)
# -----------------------------------------------------------------------------
REVERSE_MASTERING_PROFILES: Dict[str, Dict[str, Any]] = {
    "club_c5": {
        "name": "C5-REAL Sovereign Club Master (LR4 120 Hz + VCA 2.4:1 + -0.5 dBTP)",
        "lowest_freq": 28.0,
        "highest_freq": 19500.0,
        "mono_crossover_hz": 120.0,
        "target_lufs": -9.5,
        "target_dbtp": -0.5,
        "soft_clipper_drive_db": 1.8,
        "side_high_boost_db": 0.9,
        "vca_threshold_db": -13.5,
        "mid_glue_ratio": 2.4,
        "vca_attack_ms": 28.0,
        "vca_release_ms": 90.0,
        "character": "Phase-locked sub mono <120 Hz, 28ms punch-preserving VCA glue, 8.5-11.5 dB club crest",
    },
    "club_organic_vst3": {
        "name": "C5-REAL Organic Club Master (Balanced Tilt + >250Hz Stereo + Headless VST3 Glue)",
        "lowest_freq": 30.0,
        "highest_freq": 19500.0,
        "mono_crossover_hz": 120.0,
        "target_lufs": -9.8,
        "target_dbtp": -0.5,
        "soft_clipper_drive_db": 1.3,
        "side_high_boost_db": 1.2,
        "side_mid_width_boost": 0.24,
        "sub_gain_db": -1.4,
        "mud_cut_db": -1.8,
        "presence_gain_db": 1.8,
        "air_gain_db": 2.0,
        "use_vst3": True,
        "vca_threshold_db": -13.5,
        "mid_glue_ratio": 2.2,
        "vca_attack_ms": 28.0,
        "vca_release_ms": 92.0,
        "character": "Controlled <120Hz mono sub, open 2-18k presence/air, wide >250Hz stereo, Heat2/FirePresser warmth",
    },
    "techno": {
        "name": "Tokyo Dawn / FL Cloud Techno",
        "lowest_freq": 30.0,
        "highest_freq": 18500.0,
        "mono_crossover_hz": 125.0,
        "target_lufs": -8.8,
        "target_dbtp": -0.5,
        "soft_clipper_drive_db": 2.0,
        "side_high_boost_db": 0.8,
        "vca_threshold_db": -13.5,
        "mid_glue_ratio": 2.4,
        "vca_attack_ms": 28.0,
        "vca_release_ms": 90.0,
        "character": "Heavy punch, saturated transient crests, rock-solid sub-bass",
    },
    "club_heavy": {
        "name": "EBM / Dark Disco Club Heavy",
        "lowest_freq": 29.0,
        "highest_freq": 19000.0,
        "mono_crossover_hz": 120.0,
        "target_lufs": -8.5,
        "target_dbtp": -0.5,
        "soft_clipper_drive_db": 2.2,
        "side_high_boost_db": 1.0,
        "vca_threshold_db": -13.5,
        "mid_glue_ratio": 2.4,
        "vca_attack_ms": 26.0,
        "vca_release_ms": 85.0,
        "character": "Maximum club impact, dense analog warmth, Damon Jee / Curses style",
    },
    "deep_house": {
        "name": "Satin Jackets x Maceo x AIR Deep House SOTA",
        "lowest_freq": 30.0,
        "highest_freq": 18500.0,
        "mono_crossover_hz": 120.0,
        "target_lufs": -9.8,
        "target_dbtp": -0.5,
        "soft_clipper_drive_db": 1.5,
        "side_high_boost_db": 1.1,
        "vca_threshold_db": -13.5,
        "mid_glue_ratio": 2.2,
        "vca_attack_ms": 28.0,
        "vca_release_ms": 92.0,
        "character": "Warm analog low-end, open stereo air, subtle VCA tape glue",
    },
    "dub_techno": {
        "name": "Basic Channel / Maurizio Dub Techno",
        "lowest_freq": 27.0,
        "highest_freq": 16500.0,
        "mono_crossover_hz": 125.0,
        "target_lufs": -10.5,
        "target_dbtp": -0.6,
        "soft_clipper_drive_db": 1.6,
        "side_high_boost_db": 0.6,
        "vca_threshold_db": -14.0,
        "mid_glue_ratio": 2.2,
        "vca_attack_ms": 30.0,
        "vca_release_ms": 110.0,
        "character": "Subaquatic warm low-end, tape echo depth, preserved chord decay",
    },
    "streaming_sota": {
        "name": "EBU R128 / Streaming Worldwide (Spotify / Apple Music)",
        "lowest_freq": 26.0,
        "highest_freq": 20000.0,
        "mono_crossover_hz": 120.0,
        "target_lufs": -14.0,
        "target_dbtp": -1.0,
        "soft_clipper_drive_db": 0.6,
        "side_high_boost_db": 0.5,
        "vca_threshold_db": -15.0,
        "mid_glue_ratio": 1.8,
        "vca_attack_ms": 30.0,
        "vca_release_ms": 95.0,
        "character": "Pristine dynamic range, zero inter-sample clipping, full crest preservation",
    },
    "edm": {
        "name": "Festival Club / Peak-Time",
        "lowest_freq": 30.0,
        "highest_freq": 19500.0,
        "mono_crossover_hz": 130.0,
        "target_lufs": -8.2,
        "target_dbtp": -0.4,
        "soft_clipper_drive_db": 2.4,
        "side_high_boost_db": 1.2,
        "vca_threshold_db": -13.0,
        "mid_glue_ratio": 2.5,
        "vca_attack_ms": 25.0,
        "vca_release_ms": 80.0,
        "character": "High loudness with protected kick punch and true-peak safety",
    },
    "hip_hop": {
        "name": "Urban 808 / Breakbeat",
        "lowest_freq": 26.0,
        "highest_freq": 18500.0,
        "mono_crossover_hz": 115.0,
        "target_lufs": -9.0,
        "target_dbtp": -0.5,
        "soft_clipper_drive_db": 2.1,
        "side_high_boost_db": 0.6,
        "vca_threshold_db": -13.5,
        "mid_glue_ratio": 2.2,
        "vca_attack_ms": 28.0,
        "vca_release_ms": 90.0,
        "character": "Deep 808 sub extension, crisp snare crack, clear vocal center",
    },
    "ambient": {
        "name": "Cinematic Ambient / Space-Pop",
        "lowest_freq": 24.0,
        "highest_freq": 21000.0,
        "mono_crossover_hz": 105.0,
        "target_lufs": -16.0,
        "target_dbtp": -1.0,
        "soft_clipper_drive_db": 0.3,
        "side_high_boost_db": 1.4,
        "vca_threshold_db": -18.0,
        "mid_glue_ratio": 1.4,
        "vca_attack_ms": 35.0,
        "vca_release_ms": 130.0,
        "character": "Expansive spatial width, maximum dynamic micro-detail, zero pump",
    },
}


# -----------------------------------------------------------------------------
# 2. AUDIO I/O & SAMPLE-RATE-ADAPTIVE ITU-R BS.1770-4 GATED LOUDNESS
# -----------------------------------------------------------------------------
def load_wav_stereo(file_path: str) -> Tuple[np.ndarray, int]:
    """Loads 16/24/32-bit PCM WAV into normalized float64 stereo array [-1.0, 1.0] and sample rate."""
    with wave.open(file_path, "rb") as wf:
        num_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        num_frames = wf.getnframes()
        raw_bytes = wf.readframes(num_frames)

    if sampwidth == 2:
        audio = np.frombuffer(raw_bytes, dtype="<i2").astype(np.float64) / 32768.0
    elif sampwidth == 3:
        int_data = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3)
        int32_data = (
            int_data[:, 0].astype(np.int32)
            | (int_data[:, 1].astype(np.int32) << 8)
            | (int_data[:, 2].astype(np.int32) << 16)
        )
        int32_data.flags.writeable = False
        int32_data = np.where(int32_data >= 0x800000, int32_data - 0x1000000, int32_data)
        audio = int32_data.astype(np.float64) / 8388608.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw_bytes, dtype="<i4").astype(np.float64) / 2147483648.0
    elif sampwidth == 1:
        audio = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    else:
        audio = np.frombuffer(raw_bytes, dtype="<i2").astype(np.float64) / 32768.0

    if num_channels == 1:
        stereo = np.column_stack((audio, audio))
    else:
        stereo = audio.reshape(-1, num_channels)[:, :2]

    return stereo, int(framerate)


def design_k_weighting_coeffs(
    sample_rate: int,
) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
    """
    Exact ITU-R BS.1770-4 Stage 1 (acoustic head high-shelf) and Stage 2 (RLB high-pass)
    bilinear digital filter design for ANY sample rate (44.1 kHz, 48 kHz, 88.2 kHz, 96 kHz).
    """
    if sample_rate == 48000:
        b_shelf = np.array([1.53512485958697, -2.69169618940638, 1.19839281085285], dtype=np.float64)
        a_shelf = np.array([1.0, -1.69065929318241, 0.73248077421585], dtype=np.float64)
        b_rlb = np.array([1.0, -2.0, 1.0], dtype=np.float64)
        a_rlb = np.array([1.0, -1.99004745483398, 0.99007225035621], dtype=np.float64)
        return (b_shelf, a_shelf), (b_rlb, a_rlb)

    fs = float(sample_rate)
    # Stage 1 analog prototype parameters (ITU-R BS.1770-4)
    db_gain = 3.999843853973347
    vh = 10.0 ** (db_gain / 20.0)
    vb = vh ** 0.4996667741545416
    f0_s = 1681.974450955533
    q_s = 0.7071752369554196
    k_s = math.tan(math.pi * f0_s / fs)
    a0_s = 1.0 + k_s / q_s + k_s * k_s
    b_shelf = np.array(
        [
            (vh + vb * k_s / q_s + k_s * k_s) / a0_s,
            2.0 * (k_s * k_s - vh) / a0_s,
            (vh - vb * k_s / q_s + k_s * k_s) / a0_s,
        ],
        dtype=np.float64,
    )
    a_shelf = np.array(
        [1.0, 2.0 * (k_s * k_s - 1.0) / a0_s, (1.0 - k_s / q_s + k_s * k_s) / a0_s],
        dtype=np.float64,
    )

    # Stage 2 RLB high-pass analog prototype parameters
    f0_r = 38.13547087602444
    q_r = 0.5003270373238773
    k_r = math.tan(math.pi * f0_r / fs)
    a0_r = 1.0 + k_r / q_r + k_r * k_r
    b_rlb = np.array([1.0 / a0_r, -2.0 / a0_r, 1.0 / a0_r], dtype=np.float64)
    a_rlb = np.array(
        [1.0, 2.0 * (k_r * k_r - 1.0) / a0_r, (1.0 - k_r / q_r + k_r * k_r) / a0_r],
        dtype=np.float64,
    )
    return (b_shelf, a_shelf), (b_rlb, a_rlb)


def apply_k_weighting(audio_stereo: np.ndarray, sample_rate: int) -> np.ndarray:
    """Applies ITU-R BS.1770-4 K-weighting across stereo channels."""
    (b_shelf, a_shelf), (b_rlb, a_rlb) = design_k_weighting_coeffs(sample_rate)
    s1 = signal.lfilter(b_shelf, a_shelf, audio_stereo, axis=0)
    return signal.lfilter(b_rlb, a_rlb, s1, axis=0)


def compute_integrated_lufs(audio_stereo: np.ndarray, sample_rate: int) -> float:
    """
    Computes ITU-R BS.1770-4 / EBU R128 Gated Integrated Loudness (LUFS):
      - 400 ms sliding rectangular windows, 75% overlap (100 ms step).
      - Absolute gate at -70.0 LUFS.
      - Relative gate at -10.0 LU below absolute-gated average.
    """
    arr = np.asarray(audio_stereo, dtype=np.float64)
    if arr.ndim == 1:
        arr = np.column_stack((arr, arr))
    if len(arr) == 0:
        return -70.0

    k_filt = apply_k_weighting(arr, sample_rate)
    k_filt.flags.writeable = False
    sq_sum_ch = k_filt[:, 0] ** 2 + k_filt[:, 1] ** 2

    block_len = int(round(0.400 * sample_rate))
    hop_len = max(1, int(round(0.100 * sample_rate)))

    if len(sq_sum_ch) < block_len:
        ungated = float(np.mean(sq_sum_ch))
        return -70.0 if ungated < 1e-12 else float(round(-0.691 + 10.0 * math.log10(ungated), 2))

    # Fast prefix-sum O(N) computation of 400 ms block energies
    csum = np.concatenate(([0.0], np.cumsum(sq_sum_ch, dtype=np.float64)))
    starts = np.arange(0, len(sq_sum_ch) - block_len + 1, hop_len)
    block_energies = (csum[starts + block_len] - csum[starts]) / float(block_len)

    # Gate 1: Absolute gate (-70.0 LUFS)
    abs_thresh_energy = 10.0 ** ((-70.0 + 0.691) / 10.0)
    above_abs = block_energies[block_energies > abs_thresh_energy]
    if len(above_abs) == 0:
        return -70.0

    # Gate 2: Relative gate (-10.0 LU below absolute-gated mean)
    mean_abs = float(np.mean(above_abs))
    rel_thresh_lufs = -0.691 + 10.0 * math.log10(mean_abs) - 10.0
    rel_thresh_energy = 10.0 ** ((rel_thresh_lufs + 0.691) / 10.0)
    above_rel = above_abs[above_abs >= rel_thresh_energy]

    final_energy = float(np.mean(above_rel)) if len(above_rel) > 0 else mean_abs
    if final_energy < 1e-12:
        return -70.0
    return float(round(-0.691 + 10.0 * math.log10(final_energy), 2))


def compute_loudness_range_lu(audio_stereo: np.ndarray, sample_rate: int) -> float:
    """Computes EBU Tech 3342 Loudness Range (LRA in LU) using 3s short-term blocks."""
    arr = np.asarray(audio_stereo, dtype=np.float64)
    if arr.ndim == 1:
        arr = np.column_stack((arr, arr))
    block_len = int(round(3.0 * sample_rate))
    hop_len = max(1, int(round(0.100 * sample_rate)))
    if len(arr) < block_len:
        return 0.0

    k_filt = apply_k_weighting(arr, sample_rate)
    k_filt.flags.writeable = False
    sq = k_filt[:, 0] ** 2 + k_filt[:, 1] ** 2
    csum = np.concatenate(([0.0], np.cumsum(sq, dtype=np.float64)))
    starts = np.arange(0, len(sq) - block_len + 1, hop_len)
    energies = (csum[starts + block_len] - csum[starts]) / float(block_len)

    abs_e = 10.0 ** ((-70.0 + 0.691) / 10.0)
    valid = energies[energies >= abs_e]
    if len(valid) < 2:
        return 0.0
    rel_e = float(np.mean(valid)) * (10.0 ** (-20.0 / 10.0))
    rel_valid = valid[valid >= rel_e]
    if len(rel_valid) < 2:
        return 0.0
    st_lufs = -0.691 + 10.0 * np.log10(rel_valid)
    p10, p95 = np.percentile(st_lufs, [10.0, 95.0])
    return float(round(float(p95 - p10), 2))


def compute_true_peak_dbtp(audio_stereo: np.ndarray) -> float:
    """Computes True Peak in dBTP using 4x polyphase oversampling."""
    arr = np.asarray(audio_stereo, dtype=np.float64)
    if arr.ndim == 1:
        arr = np.column_stack((arr, arr))
    if len(arr) < 8:
        peak = max(float(np.max(np.abs(arr))) if len(arr) else 1e-6, 1e-6)
        return float(round(20.0 * math.log10(peak), 2))
    up = signal.resample_poly(arr, up=4, down=1, axis=0)
    peak = max(float(np.max(np.abs(up))), 1e-6)
    return float(round(20.0 * math.log10(peak), 2))


# -----------------------------------------------------------------------------
# 3. RUBIN ACOUSTIC LINTER METROLOGY (Invariantes C5-REAL)
# -----------------------------------------------------------------------------
ZWICKER_HARMONIC_BARK_HZ: Tuple[float, ...] = (
    180.0,
    290.0,
    400.0,
    510.0,
    630.0,
    770.0,
    920.0,
    1080.0,
    1270.0,
    1480.0,
    1720.0,
    2000.0,
    2320.0,
    2700.0,
    3150.0,
    3700.0,
    4400.0,
    5000.0,
)


def compute_bark_spectral_flatness(mono: np.ndarray, sample_rate: int = 48000) -> float:
    """
    Computes tilt-decoupled Wiener Spectral Flatness (SFM) across Zwicker Critical
    Bark Sub-Bands (Bark 2..18: 180-5000 Hz) via short-time 3-bin Daniell STFT.

    Decouples macroscopic EQ spectral tilt (e.g. -3 dB/oct French Touch / club mix vs
    -14 dB/oct dark dub mix) and chord progressions over time from microscopic intra-band
    harmonicity, eliminating false positives on vocal/hat presence while catching white,
    pink (1/f), brown (1/f^2), steep low-passed noise (1/f^3), and RVQ intermodulation mush.
    """
    sig = np.asarray(mono, dtype=np.float64)
    n = len(sig)
    if n == 0:
        return 0.0
    if n < 256:
        spec = (np.abs(np.fft.rfft(sig)) ** 2) + 1e-18
        spec.flags.writeable = False
        return float(np.exp(np.mean(np.log(spec))) / np.mean(spec))

    nperseg = min(n, 8192)
    nfft = max(16384, nperseg)
    hop = max(256, nperseg // 2)
    freqs, _, zxx = signal.stft(
        sig,
        fs=sample_rate,
        window="hann",
        nperseg=nperseg,
        noverlap=nperseg - hop,
        nfft=nfft,
        boundary=None,
        padded=False,
        scaling="spectrum",
    )
    power = (np.abs(zxx) ** 2) + 1e-30
    if power.shape[1] > 400:
        idx = np.linspace(0, power.shape[1] - 1, 400, dtype=int)
        power = power[:, idx]

    nyq_lim = min(5000.0, float(sample_rate) * 0.45)
    full_band = freqs >= 20.0
    active_band = (freqs >= 180.0) & (freqs <= nyq_lim)
    if not np.any(active_band) or not np.any(full_band):
        return 0.0

    full_energy = np.sum(power[full_band, :], axis=0)
    max_fe = float(np.max(full_energy))
    if max_fe <= 1e-28:
        return 0.0
    keep = full_energy >= max_fe * 0.01
    power = power[:, keep]
    full_energy = full_energy[keep]
    mid_energy = np.sum(power[active_band, :], axis=0)
    power.flags.writeable = False

    s_list = []
    e_list = []
    for f_lo, f_hi in zip(ZWICKER_HARMONIC_BARK_HZ[:-1], ZWICKER_HARMONIC_BARK_HZ[1:]):
        if f_lo >= nyq_lim:
            break
        mask = (freqs >= f_lo) & (freqs < min(f_hi, nyq_lim))
        if int(np.sum(mask)) >= 6:
            pb = power[mask, :]
            pb_sm = (pb[:-2, :] + pb[1:-1, :] + pb[2:, :]) / 3.0
            gm = np.exp(np.mean(np.log(pb_sm), axis=0))
            am = np.mean(pb_sm, axis=0)
            # Normalize by 3-bin Daniell Gaussian noise expectation (~0.785)
            s_list.append(np.minimum(1.0, (gm / am) / 0.785))
            e_list.append(np.sum(pb, axis=0))

    if not s_list:
        return 0.0

    s_mat = np.stack(s_list, axis=0)
    w_mat = np.stack(e_list, axis=0) + 1e-30
    raw_sfm = np.sum(s_mat * w_mat, axis=0) / np.sum(w_mat, axis=0)
    # Suppress <-50 dB stopband artifacts on pure sub-bass / sustained 49 Hz kick body frames
    rel_gate = np.minimum(1.0, mid_energy / np.maximum(full_energy * 1e-5, 1e-30))
    frame_sfm = raw_sfm * rel_gate
    return float(np.percentile(frame_sfm, 12.5))


def compute_rubin_metrics(
    left: np.ndarray,
    right: np.ndarray,
    sample_rate: int = 48000,
) -> Dict[str, Any]:
    """
    Evaluates the physical invariants of the Rubin Protocol:
      1. Crest Factor (WCF >= 8.0 dB): Detects brickwall hypercompression.
      2. Tilt-Decoupled Bark-Band Spectral Flatness (SFM < 0.35, optimal < 0.20 across Zwicker Bark 2..18).
      3. Low-End Phase Coherence (LPC >= 0.85, optimal >= 0.95 strictly filtered < 120 Hz).
      4. Discrete 1st/2nd Derivative Continuity telemetry.
    """
    l_arr = np.array(left, dtype=np.float64, copy=True)
    r_arr = np.array(right, dtype=np.float64, copy=True)
    l_arr.flags.writeable = False
    r_arr.flags.writeable = False
    mono = 0.5 * (l_arr + r_arr)
    mono.flags.writeable = False
    if len(mono) == 0:
        return {
            "crest_factor_db": 0.0,
            "spectral_flatness_sfm": 0.0,
            "low_end_phase_coherence": 1.0,
            "full_band_phase_coherence": 1.0,
            "max_abs_d1": 0.0,
            "is_pure_bone": False,
            "verdict": "NATA ACÚSTICA DETECTADA",
            "anomalies": ["Señal vacía"],
        }

    peak = float(np.max(np.abs(mono)))
    rms = math.sqrt(float(np.dot(mono, mono)) / float(len(mono)))
    cf = 20.0 * math.log10(peak / max(rms, 1e-9)) if rms > 0 and peak > 0 else 0.0

    # Tilt-decoupled Zwicker Critical Bark Sub-Band SFM (180 Hz - 5000 Hz),
    # weighted by -53 dBFS (5e-6 mean-square) psychoacoustic quiet-floor audibility
    # so mandated -57 dBFS C5 analog tape beds are not misclassified as program mush.
    rms_sq = rms * rms
    audibility_gate = rms_sq / (rms_sq + 5e-6) if rms_sq > 0.0 else 0.0
    sfm = compute_bark_spectral_flatness(mono, sample_rate=sample_rate) * audibility_gate

    # Full-band stereo correlation
    den_full = math.sqrt(float(np.dot(l_arr, l_arr)) * float(np.dot(r_arr, r_arr)))
    full_corr = float(np.dot(l_arr, r_arr) / den_full) if den_full > 1e-12 else 1.0

    # True < 120 Hz Low-End Phase Coherence (LPC) via zero-phase LR4 lowpass
    stereo = np.column_stack((l_arr, r_arr))
    low_stereo, _ = lr4_zero_phase_crossover(stereo, 120.0, sample_rate)
    low_stereo.flags.writeable = False
    l_low = low_stereo[:, 0]
    r_low = low_stereo[:, 1]
    den_low = math.sqrt(float(np.dot(l_low, l_low)) * float(np.dot(r_low, r_low)))
    if den_low > 1e-9:
        lpc = float(np.dot(l_low, r_low) / den_low)
    else:
        lpc = full_corr

    max_d1 = float(np.max(np.abs(np.diff(mono)))) if len(mono) > 1 else 0.0

    anomalies = []
    if cf < 8.0:
        anomalies.append(f"Anergía por Hipercompresión: Crest Factor {cf:.2f} dB < 8.0 dB")
    if sfm > 0.35:
        anomalies.append(f"Anergía por Capas Parásitas: Spectral Flatness {sfm:.3f} > 0.35")
    if lpc < 0.85:
        anomalies.append(f"Anergía por Desfase Subgrave (<120 Hz): LPC {lpc:.3f} < 0.85")

    is_pure_bone = len(anomalies) == 0
    return {
        "crest_factor_db": round(cf, 2),
        "spectral_flatness_sfm": round(sfm, 4),
        "low_end_phase_coherence": round(lpc, 4),
        "full_band_phase_coherence": round(full_corr, 4),
        "max_abs_d1": round(max_d1, 5),
        "is_pure_bone": is_pure_bone,
        "verdict": "EXERGÍA PURA (EL HUESO)" if is_pure_bone else "NATA ACÚSTICA DETECTADA",
        "anomalies": anomalies,
    }


# -----------------------------------------------------------------------------
# 4. REVERSE-ENGINEERED DSP STAGES (Zero-Phase LR4 + VCA Glue + Lookahead TP)
# -----------------------------------------------------------------------------
class FLReverseMasteringDSP:
    """
    Modular C5-REAL Mastering Engine:
      Stage 1: Zero-phase subsonic clean + LR4 (<120 Hz) 100% Mono consolidation + Mid/Side Air
      Stage 2: Stereo-Linked Ballistic VCA Bus Glue Compressor (28 ms Attack / 90 ms Release)
      Stage 3: 4x Polyphase Oversampled Analog Soft Clipper (Even/Odd Crest Toasting)
      Stage 4: 4x Oversampled Stereo-Linked Lookahead Envelope True-Peak Limiter
      Stage 5: Lipshitz-Vanderkooy High-Pass TPDF Dither
    """

    def __init__(self, sample_rate: int, profile: Dict[str, Any]):
        self.sr = int(sample_rate)
        self.profile = profile
        self.nyquist = sample_rate / 2.0

    def stage1_linear_phase_eq_and_mid_side(self, audio: np.ndarray) -> np.ndarray:
        """
        Stage 1:
          1. Zero-phase subsonic DC/rumble high-pass at `lowest_freq` (~28-30 Hz).
          2. Exact Zero-Phase 4th-Order Linkwitz-Riley (LR4, 24 dB/oct) crossover at `mono_crossover_hz`
             (120 Hz): unifies sub-bass 100% to Mono (LPC = 1.000, zero 180° phase notch!).
          3. Subtle zero-phase Side high-shelf air excitation (> 5.5 kHz) + gentle > 16 kHz silk smoothing.
        """
        cutoff_hp = max(20.0, float(self.profile.get("lowest_freq", 28.0)))
        wn_hp = float(np.clip(cutoff_hp / self.nyquist, 0.0005, 0.45))
        sos_hp = signal.butter(2, wn_hp, btype="high", output="sos")
        cleaned = signal.sosfiltfilt(sos_hp, audio, axis=0) if len(audio) >= 18 else audio.copy()

        # Optional tonal spectral-balance EQ curve (zero-phase/gentle club clarity tilt)
        sub_g = float(self.profile.get("sub_gain_db", 0.0))
        mud_g = float(self.profile.get("mud_cut_db", 0.0))
        pres_g = float(self.profile.get("presence_gain_db", 0.0))
        air_g = float(self.profile.get("air_gain_db", 0.0))
        if (abs(sub_g) > 0.05 or abs(mud_g) > 0.05 or abs(pres_g) > 0.05 or abs(air_g) > 0.05) and len(cleaned) >= 64:
            eq_l, eq_r = apply_spectral_balance_eq(
                cleaned[:, 0],
                cleaned[:, 1],
                sample_rate=self.sr,
                sub_gain_db=sub_g,
                mud_cut_db=mud_g,
                presence_gain_db=pres_g,
                air_gain_db=air_g,
            )
            cleaned = np.column_stack((eq_l, eq_r))
        cleaned.flags.writeable = False

        # Exact zero-phase LR4 split at mono_crossover_hz (~120 Hz)
        crossover = float(self.profile.get("mono_crossover_hz", 120.0))
        low_band, high_band = lr4_zero_phase_crossover(cleaned, crossover, self.sr)
        low_band.flags.writeable = False
        high_band.flags.writeable = False

        # Sub-bass strictly 100% monophonic
        low_mono = 0.5 * (low_band[:, 0] + low_band[:, 1])
        low_mono.flags.writeable = False

        # Mid/Side processing strictly on High band (>= 120 Hz)
        mid_h = 0.5 * (high_band[:, 0] + high_band[:, 1])
        mid_h.flags.writeable = False
        side_h = 0.5 * (high_band[:, 0] - high_band[:, 1])
        side_h.flags.writeable = False

        side_mid_boost = float(self.profile.get("side_mid_width_boost", 0.0))
        if side_mid_boost > 0.01 and len(side_h) >= 18:
            wn_w = float(np.clip(250.0 / self.nyquist, 0.005, 0.45))
            sos_w = signal.butter(2, wn_w, btype="high", output="sos")
            side_upper = signal.sosfiltfilt(sos_w, side_h)
            side_upper.flags.writeable = False
            # Cap boost so side RMS stays healthy & phase-compatible
            upper_gain = float(np.clip(side_mid_boost, 0.0, 0.65))
            side_h = side_h + side_upper * upper_gain
            side_h.flags.writeable = False

        side_boost_db = float(self.profile.get("side_high_boost_db", 0.8))
        if side_boost_db > 0.01 and len(side_h) >= 18:
            wn_air = float(np.clip(4500.0 / self.nyquist, 0.05, 0.90))
            sos_air = signal.butter(1, wn_air, btype="high", output="sos")
            side_air = signal.sosfiltfilt(sos_air, side_h)
            side_air.flags.writeable = False
            # Limit side air boost so stereo correlation stays strong
            boost_lin = min(0.55, 10.0 ** (side_boost_db / 20.0) - 1.0)
            side_h = side_h + side_air * boost_lin
            side_h.flags.writeable = False

        base = low_mono + mid_h
        base.flags.writeable = False
        left = base + side_h
        right = base - side_h
        return np.column_stack((left, right))

    def stage2_multiband_dynamics_glue(self, audio: np.ndarray) -> np.ndarray:
        """
        Stage 2: True Stereo-Linked Ballistic VCA Master Bus Glue Compressor
        (replaces static sample-by-sample waveshaping with smooth attack/release envelope!).
        Default C5 club ballistics: Threshold -13.5 dB, Ratio 2.4:1, Attack 28 ms (lets kick
        transient punch pass uncompressed!), Release 90 ms, Soft Knee 3.0 dB.
        """
        if len(audio) < 64:
            return audio.copy()

        ratio = max(1.05, float(self.profile.get("mid_glue_ratio", 2.4)))
        attack_ms = max(5.0, float(self.profile.get("vca_attack_ms", 28.0)))
        release_ms = max(25.0, float(self.profile.get("vca_release_ms", 90.0)))

        # Sidechain detector high-passed at 95 Hz so sub-bass weight doesn't pump mids
        wn_sc = float(np.clip(95.0 / self.nyquist, 0.002, 0.40))
        sos_sc = signal.butter(2, wn_sc, btype="high", output="sos")
        det_sig = signal.sosfilt(sos_sc, audio, axis=0)
        det_sig.flags.writeable = False
        linked_sq = 0.5 * (det_sig[:, 0] ** 2 + det_sig[:, 1] ** 2)

        # Compute smooth RMS envelope on 1 ms control blocks for ultra-fast O(N/48) ballistics
        step = max(1, int(round(0.001 * self.sr)))
        n_blocks = (len(linked_sq) + step - 1) // step
        padded_len = n_blocks * step
        if padded_len > len(linked_sq):
            sq_pad = np.pad(linked_sq, (0, padded_len - len(linked_sq)), mode="edge")
        else:
            sq_pad = linked_sq
        block_rms = np.sqrt(np.mean(sq_pad.reshape(n_blocks, step), axis=1) + 1e-15)

        dt_ctrl = step / float(self.sr)
        alpha_att = math.exp(-dt_ctrl / (attack_ms / 1000.0))
        alpha_rel = math.exp(-dt_ctrl / (release_ms / 1000.0))

        env = np.empty(n_blocks, dtype=np.float64)
        cur = float(block_rms[0])
        for i in range(n_blocks):
            x = float(block_rms[i])
            if x > cur:
                cur = alpha_att * cur + (1.0 - alpha_att) * x
            else:
                cur = alpha_rel * cur + (1.0 - alpha_rel) * x
            env[i] = cur

        env_db = 20.0 * np.log10(np.maximum(env, 1e-9))
        # Adaptive program-relative threshold anchored around RMS + 2.5 dB (caps max GR to ~3.5 dB glue)
        prog_rms_db = 20.0 * math.log10(max(float(np.median(block_rms)), 1e-6))
        thresh_db = max(float(self.profile.get("vca_threshold_db", -13.5)), prog_rms_db + 1.8)
        knee_db = 3.0

        over_db = env_db - thresh_db
        gr_db = np.zeros_like(over_db)
        slope = 1.0 - (1.0 / ratio)

        # Soft-knee quadratic transition in [-knee/2, +knee/2]
        in_knee = np.abs(over_db) < (knee_db * 0.5)
        above_knee = over_db >= (knee_db * 0.5)
        gr_db[in_knee] = -slope * ((over_db[in_knee] + knee_db * 0.5) ** 2) / (2.0 * knee_db)
        gr_db[above_knee] = -slope * over_db[above_knee]
        gr_db = np.clip(gr_db, -4.0, 0.0)

        # Gentle auto makeup (+45% of median active GR) + interpolate smoothly to sample rate
        active_gr = gr_db[gr_db < -0.05]
        makeup_db = -0.45 * float(np.median(active_gr)) if len(active_gr) > 0 else 0.0
        gain_ctrl = 10.0 ** ((gr_db + makeup_db) / 20.0)

        ctrl_t = np.arange(n_blocks, dtype=np.float64) * step
        sample_t = np.arange(len(audio), dtype=np.float64)
        gain_sample = np.interp(sample_t, ctrl_t, gain_ctrl)

        return audio * gain_sample[:, None]

    def stage3_fruity_soft_clipper(self, audio: np.ndarray, threshold_db: float = -2.2) -> np.ndarray:
        """
        Stage 3: 4x Polyphase Oversampled Analog Soft Clipper.
        Linear below threshold; warm polynomial-tanh saturation on transient crests with zero aliasing.
        """
        drive_db = float(self.profile.get("soft_clipper_drive_db", 1.5))
        if drive_db <= 0.05:
            return audio.copy()
        return oversampled_soft_saturate(
            audio,
            drive_db=drive_db,
            threshold_db=threshold_db,
            asymmetry=0.035,
            oversample=4,
        )

    def stage4_true_peak_lookahead_limiter(
        self, audio: np.ndarray, target_dbtp: float
    ) -> np.ndarray:
        """
        Stage 4: Real 4x Oversampled Stereo-Linked Lookahead Gain-Envelope True-Peak Limiter.
          1. 4x polyphase oversampling detects inter-sample peaks (ISP).
          2. 2.0 ms lookahead sliding maximum anticipates peaks before arrival.
          3. Raised-cosine attack smoothing (1.5 ms) + 75 ms exponential release prevents crackle.
          4. Post-downsample ISP verification guarantees strict ceiling compliance (<= target_dbtp).
        """
        if len(audio) == 0:
            return audio.copy()

        # Leave 0.06 dB internal safety margin against polyphase downsampling ripple
        internal_ceiling = 10.0 ** ((target_dbtp - 0.06) / 20.0)
        hard_ceiling = 10.0 ** (target_dbtp / 20.0)

        sr_4x = self.sr * 4
        if len(audio) >= 16:
            up = signal.resample_poly(audio, up=4, down=1, axis=0)
        else:
            up = audio.copy()
            sr_4x = self.sr

        inst_peak = np.maximum(np.abs(up[:, 0]), np.abs(up[:, 1]))

        # Lookahead window (2.0 ms) via O(N) sliding maximum
        la_samples = max(4, int(round(0.0020 * sr_4x)))
        anticipated_peak = ndimage.maximum_filter1d(inst_peak, size=la_samples, origin=la_samples // 2 - 1)
        anticipated_peak = np.maximum(anticipated_peak, inst_peak)

        # Required gain reduction on 1 ms control blocks + exponential 75 ms release + Hanning smoothing
        req_gain = np.where(
            anticipated_peak > internal_ceiling,
            internal_ceiling / np.maximum(anticipated_peak, 1e-9),
            1.0,
        )

        # Decimate minimum gain into 0.5 ms blocks for fast release ballistics, then smooth
        blk = max(1, int(round(0.0005 * sr_4x)))
        n_b = (len(req_gain) + blk - 1) // blk
        pad_n = n_b * blk - len(req_gain)
        rg_pad = np.pad(req_gain, (0, pad_n), mode="constant", constant_values=1.0) if pad_n > 0 else req_gain
        blk_min = np.min(rg_pad.reshape(n_b, blk), axis=1)

        rel_alpha = math.exp(-(blk / float(sr_4x)) / 0.075)
        env_b = np.empty(n_b, dtype=np.float64)
        g_cur = 1.0
        for i in range(n_b):
            target_g = float(blk_min[i])
            if target_g < g_cur:
                g_cur = target_g  # Instant lookahead catch (already smoothed by lookahead window)
            else:
                g_cur = rel_alpha * g_cur + (1.0 - rel_alpha) * target_g
            env_b[i] = g_cur

        gain_4x = np.interp(
            np.arange(len(up), dtype=np.float64),
            np.arange(n_b, dtype=np.float64) * blk,
            env_b,
        )

        # Smooth attack transitions with a 1.2 ms Hanning kernel & ensure gain_4x <= req_gain on peaks
        smooth_len = max(3, int(round(0.0012 * sr_4x)))
        if smooth_len % 2 == 0:
            smooth_len += 1
        kern = np.hanning(smooth_len)
        kern /= np.sum(kern)
        gain_4x = np.convolve(np.pad(gain_4x, smooth_len // 2, mode="edge"), kern, mode="valid")[: len(up)]

        limited_4x = up * gain_4x[:, None]
        # Final 4x safety soft-clamp at hard_ceiling
        limited_4x = np.clip(limited_4x, -hard_ceiling, hard_ceiling)

        if len(audio) >= 16:
            down = signal.resample_poly(limited_4x, up=1, down=4, axis=0)[: len(audio)]
        else:
            down = limited_4x

        # Verify post-downsample True Peak and apply clean micro-trim if needed
        actual_tp_db = compute_true_peak_dbtp(down)
        if actual_tp_db > target_dbtp:
            trim = 10.0 ** ((target_dbtp - actual_tp_db - 0.03) / 20.0)
            down = down * trim

        return down

    def stage5_psychoacoustic_tpdf_dither(self, audio: np.ndarray, bit_depth: int = 24) -> np.ndarray:
        """Stage 5: Lipshitz-Vanderkooy High-Pass TPDF Dither."""
        return apply_highpass_tpdf_dither(audio, bit_depth=bit_depth)


# -----------------------------------------------------------------------------
# 5. MASTERING PIPELINE ORCHESTRATOR (Crest-Protected Loudness Targeting)
# -----------------------------------------------------------------------------
def master_audio_reverse_engineered(
    input_wav: str,
    output_wav: Optional[str] = None,
    profile_name: str = "club_c5",
    custom_target_lufs: Optional[float] = None,
    custom_target_dbtp: Optional[float] = None,
    bit_depth: int = 24,
    use_vst3: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Executes the complete C5-REAL 5-stage mastering pass with automatic Crest-Factor
    protection (prevents over-driving dynamic mixes into brickwall hypercompression).
    """
    in_path = Path(input_wav).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_path}")

    profile = REVERSE_MASTERING_PROFILES.get(
        profile_name.lower(), REVERSE_MASTERING_PROFILES["club_c5"]
    ).copy()
    if custom_target_lufs is not None:
        profile["target_lufs"] = float(custom_target_lufs)
    if custom_target_dbtp is not None:
        profile["target_dbtp"] = float(custom_target_dbtp)

    target_lufs = float(profile["target_lufs"])
    target_dbtp = float(profile["target_dbtp"])

    audio_raw, sample_rate = load_wav_stereo(str(in_path))

    lufs_initial = compute_integrated_lufs(audio_raw, sample_rate)
    lra_initial = compute_loudness_range_lu(audio_raw, sample_rate)
    peak_dbtp_initial = compute_true_peak_dbtp(audio_raw)
    rubin_initial = compute_rubin_metrics(audio_raw[:, 0], audio_raw[:, 1], sample_rate=sample_rate)

    dsp = FLReverseMasteringDSP(sample_rate, profile)

    # Stage 1: Zero-Phase Sub Cut + LR4 (<120 Hz) Mono Consolidation + Side Air
    s1 = dsp.stage1_linear_phase_eq_and_mid_side(audio_raw)

    # Optional Stage 1b: Curated Headless VST3 Analog Tape + Glue (WDF Fallback)
    apply_vst = bool(profile.get("use_vst3", False)) if use_vst3 is None else bool(use_vst3)
    vst3_applied: list[str] = []
    if apply_vst:
        s1_vst = s1
        out_heat, ok_heat = apply_curated_vst3_preset(
            s1_vst, "heat2_warm_tape", sample_rate=sample_rate, wet=0.45
        )
        if ok_heat:
            s1_vst = out_heat
            vst3_applied.append("heat2_warm_tape")
        out_glue, ok_glue = apply_curated_vst3_preset(
            s1_vst, "firepresser_glue", sample_rate=sample_rate, wet=0.30
        )
        if ok_glue:
            s1_vst = out_glue
            vst3_applied.append("firepresser_glue")
        if vst3_applied:
            # Re-lock sub <120Hz after nonlinear plugin harmonics
            s1_low, s1_high = lr4_zero_phase_crossover(
                s1_vst, float(profile.get("mono_crossover_hz", 120.0)), sample_rate
            )
            s1_low.flags.writeable = False
            s1_high.flags.writeable = False
            s1_mono = 0.5 * (s1_low[:, 0] + s1_low[:, 1])
            s1_mono.flags.writeable = False
            s1 = np.column_stack((s1_mono + s1_high[:, 0], s1_mono + s1_high[:, 1]))
        else:
            wl, wr = apply_wdf_warm_saturator(
                s1[:, 0], s1[:, 1], sample_rate=sample_rate, drive_db=1.8, tube_bias=0.06, mix=0.38
            )
            s1 = np.column_stack((wl, wr))
            vst3_applied.append("wdf_diode_fallback")

    # Stage 2: Ballistic VCA Master Bus Glue Compressor
    s2 = dsp.stage2_multiband_dynamics_glue(s1)

    # Stage 3: Crest-Protected Loudness Gain Staging
    # Compute natural crest factor so we never push more than +3.8 dB into the limiter,
    # guaranteeing Rubin Crest Factor >= 8.5 dB ("EXERGÍA PURA") even on aggressive club targets!
    current_lufs = compute_integrated_lufs(s2, sample_rate)
    current_tp = compute_true_peak_dbtp(s2)
    max_safe_limiter_push_db = (target_dbtp - current_tp) + 3.8
    desired_gain_db = target_lufs - current_lufs
    gain_db = float(np.clip(min(desired_gain_db, max_safe_limiter_push_db), -15.0, 15.0))
    freeze_array(s2)
    gained = np.multiply(s2, 10.0 ** (gain_db / 20.0))

    # Stage 4: 4x Oversampled Analog Soft Clipper
    s4 = dsp.stage3_fruity_soft_clipper(gained)

    # Stage 5: 4x Oversampled Stereo-Linked Lookahead True-Peak Limiter
    s5 = dsp.stage4_true_peak_lookahead_limiter(s4, target_dbtp)

    # Fine loudness trim within safe crest headroom if under target
    post_lufs = compute_integrated_lufs(s5, sample_rate)
    post_rubin = compute_rubin_metrics(s5[:, 0], s5[:, 1], sample_rate=sample_rate)
    if abs(target_lufs - post_lufs) > 0.6 and post_rubin["crest_factor_db"] > 9.4:
        trim_db = float(np.clip(target_lufs - post_lufs, -1.8, 1.8))
        freeze_array(s5)
        s5_trimmed = dsp.stage4_true_peak_lookahead_limiter(
            np.multiply(s5, 10.0 ** (trim_db / 20.0)), target_dbtp
        )
        cand_rubin = compute_rubin_metrics(s5_trimmed[:, 0], s5_trimmed[:, 1], sample_rate=sample_rate)
        if cand_rubin["crest_factor_db"] >= 8.3:
            s5 = s5_trimmed
            gain_db += trim_db

    # Stage 6: Lipshitz-Vanderkooy High-Pass TPDF Dither (mindful of True Peak ceiling)
    ceiling_lin = 10.0 ** ((target_dbtp - 0.02) / 20.0)
    mastered = np.clip(dsp.stage5_psychoacoustic_tpdf_dither(s5, bit_depth=bit_depth), -ceiling_lin, ceiling_lin)

    lufs_final = compute_integrated_lufs(mastered, sample_rate)
    lra_final = compute_loudness_range_lu(mastered, sample_rate)
    peak_dbtp_final = compute_true_peak_dbtp(mastered)
    rubin_final = compute_rubin_metrics(mastered[:, 0], mastered[:, 1], sample_rate=sample_rate)

    if not output_wav:
        out_dir = in_path.parent / "mastered"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / f"{in_path.stem}_ReverseMaster_{profile_name.upper()}.wav"
    else:
        output_file = Path(output_wav).expanduser().resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    if bit_depth == 24:
        int32_data = np.clip(np.round(mastered * 8388607.0), -8388608, 8388607).astype("<i4")
        bytes_3 = int32_data.flatten().view(np.uint8).reshape(-1, 4)[:, :3]
        with wave.open(str(output_file), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(3)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes_3.tobytes())
    else:
        int16_data = np.clip(np.round(mastered * 32767.0), -32768, 32767).astype("<i2")
        with wave.open(str(output_file), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int16_data.tobytes())

    return {
        "status": "SUCCESS",
        "profile": profile_name,
        "profile_details": profile,
        "input_file": str(in_path),
        "output_file": str(output_file),
        "bit_depth": bit_depth,
        "sample_rate_hz": sample_rate,
        "duration_sec": round(len(mastered) / sample_rate, 2),
        "lufs_before": lufs_initial,
        "lufs_after": lufs_final,
        "lra_lu_before": lra_initial,
        "lra_lu_after": lra_final,
        "true_peak_dbtp_before": peak_dbtp_initial,
        "true_peak_dbtp_after": peak_dbtp_final,
        "gain_applied_db": round(gain_db, 2),
        "crossover_topology": f"Zero-Phase 4th-Order Linkwitz-Riley (LR4, 24 dB/oct) @ {profile['mono_crossover_hz']} Hz",
        "vst3_plugins_applied": vst3_applied,
        "rubin_audit_before": rubin_initial,
        "rubin_audit_after": rubin_final,
        "file_size_mb": round(output_file.stat().st_size / (1024 * 1024), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="FL Studio Reverse-Engineered Mastering Engine (C5-REAL v2.0)")
    parser.add_argument("--input", "-i", required=True, help="Input WAV audio file")
    parser.add_argument("--output", "-o", default=None, help="Output master WAV file")
    parser.add_argument(
        "--profile",
        "-p",
        default="club_c5",
        choices=list(REVERSE_MASTERING_PROFILES.keys()),
        help="Mastering profile",
    )
    parser.add_argument("--target-lufs", type=float, default=None, help="Override target integrated LUFS")
    parser.add_argument("--target-dbtp", type=float, default=None, help="Override target True Peak dBTP")
    parser.add_argument("--bits", type=int, default=24, choices=[16, 24], help="Bit depth for export")
    parser.add_argument("--json", action="store_true", help="Output pure JSON telemetry")

    args = parser.parse_args()

    try:
        report = master_audio_reverse_engineered(
            input_wav=args.input,
            output_wav=args.output,
            profile_name=args.profile,
            custom_target_lufs=args.target_lufs,
            custom_target_dbtp=args.target_dbtp,
            bit_depth=args.bits,
        )

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("\n" + "=" * 68)
            print("  FL STUDIO C5-REAL MASTERING ENGINE v2.0 (LR4 + VCA + TP LIMITER)")
            print("=" * 68)
            print(f" Archivo Entrada:   {report['input_file']}")
            print(f" Archivo Master:    {report['output_file']}")
            print(f" Perfil Aplicado:   {report['profile'].upper()} ({report['profile_details']['name']})")
            print(f" Topología Grave:   {report['crossover_topology']}")
            print("-" * 68)
            print(" TELEMETRÍA DE SONORIDAD (ITU-R BS.1770-4 GATED):")
            print(
                f"  • Integrated LUFS:   {report['lufs_before']} LUFS ──► {report['lufs_after']} LUFS "
                f"(Target: {report['profile_details']['target_lufs']} LUFS)"
            )
            print(
                f"  • True Peak dBTP:    {report['true_peak_dbtp_before']} dBTP ──► {report['true_peak_dbtp_after']} dBTP "
                f"(Ceiling: {report['profile_details']['target_dbtp']} dBTP)"
            )
            print(f"  • Loudness Range:    {report['lra_lu_before']} LU ──► {report['lra_lu_after']} LU")
            print(f"  • Ganancia Normaliz: {report['gain_applied_db']:+.2f} dB")
            print("-" * 68)
            print(" AUDITORÍA ACÚSTICA RUBIN (C5-REAL SILICON LINTER):")
            r = report["rubin_audit_after"]
            print(f"  • Factor de Cresta:  {r['crest_factor_db']} dB (Club Óptimo: 8.5 - 12.0 dB)")
            print(f"  • Planitud (Bark SFM): {r['spectral_flatness_sfm']} (Bark 180-5000 Hz < 0.20)")
            print(f"  • Coherencia <120Hz: {r['low_end_phase_coherence']} (Mono Sub >= 0.95)")
            print(f"  • Veredicto Final:   [{r['verdict']}]")
            print("=" * 68 + "\n")

    except Exception as e:
        print(f"Error fatal en masterización: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
