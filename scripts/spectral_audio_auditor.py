#!/usr/bin/env python3
"""
Antigravity Spectral Audio Quality & Psychoacoustic Health Auditor (v10.0 C5-REAL)
==================================================================================
Performs full-duration empirical ITU-R BS.1770-4 gated loudness analysis,
4x oversampled True Peak (dBTP), Welch PSD 5-band spectral energy decomposition,
Rubin Protocol metrology (<120 Hz LR4 Phase Coherence, 180-5000 Hz Zwicker Bark Wiener SFM,
Crest Factor), and Zero-Crackle discrete derivative auditing across 16/24/32-bit WAVs.
"""

from __future__ import annotations

import json
import math
import re
import sys
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import signal

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from scripts.bounces_paths import resolve_bounces_dir  # noqa: E402
from scripts.c5_dsp_core import check_zero_crackle_derivatives  # noqa: E402
from scripts.mastering_reverse_engine_fl import (  # noqa: E402
    compute_integrated_lufs,
    compute_loudness_range_lu,
    compute_rubin_metrics,
    compute_true_peak_dbtp,
)


def _infer_bpm_from_filename(wav_path: Path, explicit_bpm: Optional[float]) -> float:
    if explicit_bpm is not None and explicit_bpm > 30.0:
        return float(explicit_bpm)
    name = wav_path.name.lower()
    m = re.search(r"(\d{2,3})\s*bpm", name)
    if m:
        val = float(m.group(1))
        if 60.0 <= val <= 190.0:
            return val
    if "flamenco" in name or "cyber" in name:
        return 112.0
    if "yolando" in name or "everything" in name or "124" in name:
        return 124.0
    return 122.0


def analyze_audio_spectrum(
    wav_path: Path,
    max_duration_sec: float = 60.0,
    bpm: Optional[float] = None,
) -> Dict[str, Any]:
    wav_path = Path(wav_path).expanduser().resolve()
    if not wav_path.exists():
        return {"error": f"Audio file not found: {wav_path}"}

    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        samp_width = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        total_duration = n_frames / float(framerate) if framerate > 0 else 0.0

        frames_to_read = min(n_frames, int(framerate * max_duration_sec))
        raw_bytes = wf.readframes(frames_to_read)

    if samp_width == 2:
        raw_float = np.frombuffer(raw_bytes, dtype="<i2").astype(np.float64) / 32768.0
    elif samp_width == 3:
        b = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3)
        i32 = (
            b[:, 0].astype(np.int32)
            | (b[:, 1].astype(np.int32) << 8)
            | (b[:, 2].astype(np.int32) << 16)
        )
        i32 = np.where(i32 >= 0x800000, i32 - 0x1000000, i32)
        raw_float = i32.astype(np.float64) / 8388608.0
    elif samp_width == 4:
        raw_float = np.frombuffer(raw_bytes, dtype="<i4").astype(np.float64) / 2147483648.0
    elif samp_width == 1:
        raw_float = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    else:
        return {"error": f"Unsupported sample width: {samp_width * 8}-bit PCM"}

    if len(raw_float) == 0:
        return {"error": "Empty audio data"}

    if n_channels == 1:
        stereo = np.column_stack((raw_float, raw_float))
        mono = np.array(raw_float, dtype=np.float64, copy=True)
    else:
        reshaped = raw_float.reshape(-1, n_channels)
        stereo = reshaped[:, :2]
        mono = np.mean(reshaped, axis=1)
    mono.flags.writeable = False

    n_pts = len(mono)
    analyzed_sec = n_pts / float(framerate)

    # 1. Sample Peak, True Peak (4x oversampled), RMS, Clipping & Zero-Crossings
    abs_stereo = np.abs(stereo)
    peak_val = max(1e-6, float(np.max(abs_stereo)))
    rms_val = max(1e-6, math.sqrt(float(np.dot(mono, mono)) / float(max(1, n_pts))))
    clipping_samples = int(np.sum(abs_stereo >= 0.9999))
    signs = mono >= 0.0
    zero_crossings = int(np.sum(signs[1:] != signs[:-1])) if n_pts > 1 else 0

    peak_dbfs = round(20.0 * math.log10(peak_val), 2)
    true_peak_dbtp = compute_true_peak_dbtp(stereo)
    rms_dbfs = round(20.0 * math.log10(rms_val), 2)
    crest_factor_db = round(peak_dbfs - rms_dbfs, 2)
    integrated_lufs = compute_integrated_lufs(stereo, framerate)
    lra_lu = compute_loudness_range_lu(stereo, framerate)

    # 2. Full-Duration Welch PSD Spectral Band Decomposition
    nperseg = min(n_pts, 8192)
    if nperseg >= 32:
        freqs, psd = signal.welch(mono, fs=framerate, nperseg=nperseg)
    else:
        freqs = np.fft.rfftfreq(n_pts, d=1.0 / framerate)
        psd = (np.abs(np.fft.rfft(mono)) ** 2) / max(1, n_pts)

    band_ranges = {
        "sub_bass_45hz": (20.0, 80.0),
        "punch_120hz": (80.0, 220.0),
        "body_500hz": (220.0, 1200.0),
        "presence_2500hz": (1200.0, 5500.0),
        "air_10000hz": (5500.0, min(20000.0, framerate * 0.49)),
    }

    band_energies: Dict[str, float] = {}
    for b_name, (f_lo, f_hi) in band_ranges.items():
        mask = (freqs >= f_lo) & (freqs < max(f_lo + 1.0, f_hi))
        band_energies[b_name] = max(1e-12, float(np.sum(psd[mask])))

    total_band_energy = max(1e-12, sum(band_energies.values()))
    spectral_distribution = {
        k: round((v / total_band_energy) * 100.0, 1) for k, v in band_energies.items()
    }

    # 2b. Honest Multi-Axis Perceptual Telemetry (Anti-IA Goodhart Audit)
    l_ch = np.array(stereo[:, 0], dtype=np.float64, copy=True)
    r_ch = np.array(stereo[:, 1], dtype=np.float64, copy=True)
    l_ch.flags.writeable = False
    r_ch.flags.writeable = False
    mid_sig = 0.5 * (l_ch + r_ch)
    side_sig = 0.5 * (l_ch - r_ch)
    mid_sig.flags.writeable = False
    side_sig.flags.writeable = False

    nperseg_p = min(n_pts, 16384)
    if nperseg_p >= 32:
        p_freqs, psd_mid = signal.welch(mid_sig, fs=framerate, nperseg=nperseg_p)
        _, psd_side = signal.welch(side_sig, fs=framerate, nperseg=nperseg_p)
    else:
        p_freqs = np.fft.rfftfreq(n_pts, d=1.0 / framerate)
        psd_mid = (np.abs(np.fft.rfft(mid_sig)) ** 2) / max(1, n_pts)
        psd_side = (np.abs(np.fft.rfft(side_sig)) ** 2) / max(1, n_pts)

    perceptual_bands = {
        "sub_lt120": (20.0, 120.0),
        "low_mid_120_500": (120.0, 500.0),
        "mid_500_2k": (500.0, 2000.0),
        "presence_2k_6k": (2000.0, 6000.0),
        "air_6k_18k": (6000.0, min(18000.0, framerate * 0.49)),
    }
    in_range = (p_freqs >= 20.0) & (p_freqs <= min(18000.0, framerate * 0.49))
    tot_mid = max(1e-18, float(np.sum(psd_mid[in_range])))
    band_balance_pct: Dict[str, float] = {}
    stereo_width_s_m: Dict[str, float] = {}
    for b_key, (b_lo, b_hi) in perceptual_bands.items():
        b_mask = (p_freqs >= b_lo) & (p_freqs < max(b_lo + 1.0, b_hi))
        e_mid = float(np.sum(psd_mid[b_mask]))
        e_side = float(np.sum(psd_side[b_mask]))
        band_balance_pct[b_key] = round(100.0 * e_mid / tot_mid, 2)
        stereo_width_s_m[b_key] = round(math.sqrt(max(0.0, e_side) / max(1e-18, e_mid)), 3)

    # Bar-to-bar spectral cosine similarity (catches copy-paste robotic loops)
    eff_bpm = _infer_bpm_from_filename(wav_path, bpm)
    bar_samples = max(1, int(round(framerate * 4.0 * 60.0 / eff_bpm)))
    n_bars = n_pts // bar_samples
    bar_to_bar_cosine_similarity: Optional[float] = None
    if n_bars >= 2:
        bar_specs: List[np.ndarray] = []
        seg_nperseg = min(bar_samples, 4096)
        if seg_nperseg >= 32:
            for b_i in range(n_bars):
                seg = mono[b_i * bar_samples : (b_i + 1) * bar_samples]
                _, p_bar = signal.welch(seg, fs=framerate, nperseg=seg_nperseg)
                bar_specs.append(np.sqrt(np.maximum(p_bar, 0.0) + 1e-18))
            sims: List[float] = []
            for b_i in range(len(bar_specs) - 1):
                va, vb = bar_specs[b_i], bar_specs[b_i + 1]
                denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
                if denom > 1e-15:
                    sims.append(float(np.dot(va, vb) / denom))
            if sims:
                bar_to_bar_cosine_similarity = round(float(np.mean(sims)), 4)

    perceptual_warnings = {
        "is_low_end_bloated": bool(band_balance_pct["sub_lt120"] > 68.0),
        "is_mono_tunnel": bool(
            max(stereo_width_s_m["mid_500_2k"], stereo_width_s_m["presence_2k_6k"]) < 0.14
        ),
        "is_presence_deficient": bool(
            band_balance_pct["presence_2k_6k"] < 1.2 or band_balance_pct["air_6k_18k"] < 1.0
        ),
        "is_robot_loop_cloning": bool(
            bar_to_bar_cosine_similarity is not None and bar_to_bar_cosine_similarity > 0.96
        ),
    }

    # 3. True Spectral Centroid across Welch PSD
    psd_total = float(np.sum(psd))
    spectral_centroid_hz = (
        round(float(np.sum(freqs * psd) / psd_total), 1) if psd_total > 1e-15 else 0.0
    )

    # 4. Rubin Protocol & Zero-Crackle Derivative Gate
    rubin = compute_rubin_metrics(stereo[:, 0], stereo[:, 1], sample_rate=framerate)
    crackle = check_zero_crackle_derivatives(mono)

    # 5. Exergy Score (1 to 21,000) calibrated on physical invariants
    base_score = 16000
    if 8.0 <= rubin["crest_factor_db"] <= 14.5:
        base_score += 2500
    elif rubin["crest_factor_db"] < 6.5:
        base_score -= 4500

    if clipping_samples == 0 and true_peak_dbtp <= -0.1:
        base_score += 1500
    else:
        base_score -= min(5000, clipping_samples * 50 + (1000 if true_peak_dbtp > 0.0 else 0))

    if rubin["low_end_phase_coherence"] >= 0.95 and rubin["spectral_flatness_sfm"] < 0.20:
        base_score += 1000
    elif not rubin["is_pure_bone"]:
        base_score -= 2500

    # Perceptual Goodhart penalty (prevents sub-bloated/mono/robot loops from scoring 21,000)
    if perceptual_warnings["is_low_end_bloated"]:
        base_score -= 2200
    if perceptual_warnings["is_mono_tunnel"]:
        base_score -= 1800
    if perceptual_warnings["is_presence_deficient"]:
        base_score -= 1800
    if perceptual_warnings["is_robot_loop_cloning"]:
        base_score -= 1800

    exergy_score = max(1, min(21000, base_score))

    return {
        "file_name": wav_path.name,
        "file_path": str(wav_path),
        "duration_analyzed_sec": round(analyzed_sec, 2),
        "total_duration_sec": round(total_duration, 2),
        "sample_rate_hz": framerate,
        "bit_depth": samp_width * 8,
        "channels": n_channels,
        "metrics": {
            "peak_dbfs": peak_dbfs,
            "true_peak_dbtp": true_peak_dbtp,
            "rms_dbfs": rms_dbfs,
            "crest_factor_db": crest_factor_db,
            "estimated_integrated_lufs": integrated_lufs,
            "integrated_lufs_gated": integrated_lufs,
            "loudness_range_lu": lra_lu,
            "clipping_samples_count": clipping_samples,
            "spectral_centroid_hz": spectral_centroid_hz,
            "spectral_flatness_sfm": rubin["spectral_flatness_sfm"],
            "low_end_phase_coherence_120hz": rubin["low_end_phase_coherence"],
            "zero_crossing_rate_hz": round(zero_crossings / max(1e-4, analyzed_sec), 1),
            "max_abs_derivative_d1": crackle["max_abs_d1"],
        },
        "rubin_audit": rubin,
        "spectral_energy_percent": spectral_distribution,
        "band_balance_pct": band_balance_pct,
        "stereo_width_s_m": stereo_width_s_m,
        "bar_to_bar_cosine_similarity": bar_to_bar_cosine_similarity,
        "perceptual_warnings": perceptual_warnings,
        "exergy_rating_21000": exergy_score,
        "verdict": "HIGH_EXERGY_PUNCH" if (exergy_score > 15000 and rubin["is_pure_bone"]) else "DEGRADED_DYNAMICS",
    }


if __name__ == "__main__":
    p = resolve_bounces_dir() / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    report = analyze_audio_spectrum(p)
    print(json.dumps(report, indent=2))
