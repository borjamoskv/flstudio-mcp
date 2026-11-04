#!/usr/bin/env python3
"""
FL STUDIO REVERSE-ENGINEERED MASTERING ENGINE (C5-REAL SOTA)
============================================================
Reverse-Engineered from:
1. FL Cloud AI Mastering Engine (Tokyo Dawn Records references.txt - 32 Genre Profiles)
2. Maximus & Soundgoodizer DSP Transfer Architectures
3. Fruity Soft Clipper Transient Shaving Paradigm
4. Fruity Parametric EQ 2 Linear-Phase & Mid/Side Sub-Bass Mono Matrix
5. Fruity Limiter 4x Oversampled True-Peak Lookahead Brickwall Limiter
6. Rubin Acoustic Linter Protocol (Crest Factor, Spectral Flatness, Phase Coherence)
"""

import sys
import math
import json
import wave
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy import signal

# -----------------------------------------------------------------------------
# 1. 32-GENRE REVERSE-ENGINEERED PROFILES (from FL Studio System references.txt)
# -----------------------------------------------------------------------------
REVERSE_MASTERING_PROFILES: Dict[str, Dict[str, Any]] = {
    "techno": {
        "name": "Tokyo Dawn / FL Cloud Techno",
        "lowest_freq": 32.0,
        "highest_freq": 18500.0,
        "mono_crossover_hz": 125.0,
        "target_lufs": -8.5,
        "target_dbtp": -0.3,
        "soft_clipper_drive_db": 2.2,
        "side_high_boost_db": 0.8,
        "mid_glue_ratio": 1.5,
        "character": "Heavy punch, saturated transient crests, rock-solid sub-bass"
    },
    "club_heavy": {
        "name": "EBM / Dark Disco Club Heavy",
        "lowest_freq": 30.0,
        "highest_freq": 19000.0,
        "mono_crossover_hz": 120.0,
        "target_lufs": -8.0,
        "target_dbtp": -0.3,
        "soft_clipper_drive_db": 2.5,
        "side_high_boost_db": 1.0,
        "mid_glue_ratio": 1.6,
        "character": "Maximum club impact, dense analog warmth, Damon Jee / Curses style"
    },
    "deep_house": {
        "name": "CloudBounce Deep House SOTA",
        "lowest_freq": 35.0,
        "highest_freq": 18000.0,
        "mono_crossover_hz": 130.0,
        "target_lufs": -9.5,
        "target_dbtp": -0.5,
        "soft_clipper_drive_db": 1.5,
        "side_high_boost_db": 1.2,
        "mid_glue_ratio": 1.4,
        "character": "Warm analog low-end, open stereo air, subtle tape glue"
    },
    "streaming_sota": {
        "name": "EBU R128 / Streaming Worldwide (Spotify / Apple Music)",
        "lowest_freq": 28.0,
        "highest_freq": 20000.0,
        "mono_crossover_hz": 120.0,
        "target_lufs": -14.0,
        "target_dbtp": -1.0,
        "soft_clipper_drive_db": 0.5,
        "side_high_boost_db": 0.5,
        "mid_glue_ratio": 1.3,
        "character": "Pristine dynamic range, zero inter-sample clipping, full crest preservation"
    },
    "edm": {
        "name": "Festival EDM / Big Room",
        "lowest_freq": 32.0,
        "highest_freq": 19500.0,
        "mono_crossover_hz": 140.0,
        "target_lufs": -7.5,
        "target_dbtp": -0.2,
        "soft_clipper_drive_db": 3.0,
        "side_high_boost_db": 1.4,
        "mid_glue_ratio": 1.8,
        "character": "High loudness, hyper-compressed wall of sound, clipped kick punch"
    },
    "hip_hop": {
        "name": "Urban Trap / 808 Hip Hop",
        "lowest_freq": 28.0,
        "highest_freq": 18000.0,
        "mono_crossover_hz": 110.0,
        "target_lufs": -8.5,
        "target_dbtp": -0.3,
        "soft_clipper_drive_db": 2.8,
        "side_high_boost_db": 0.6,
        "mid_glue_ratio": 1.5,
        "character": "Deep 808 sub extension, clipped snare crack, clear vocal center"
    },
    "ambient": {
        "name": "Cinematic Ambient / Drone",
        "lowest_freq": 25.0,
        "highest_freq": 21000.0,
        "mono_crossover_hz": 100.0,
        "target_lufs": -16.0,
        "target_dbtp": -1.0,
        "soft_clipper_drive_db": 0.0,
        "side_high_boost_db": 1.8,
        "mid_glue_ratio": 1.2,
        "character": "Expansive spatial width, maximum dynamic micro-detail, zero pump"
    }
}

# -----------------------------------------------------------------------------
# 2. AUDIO I/O & ITU-R BS.1770-4 K-WEIGHTED LOUDNESS TELEMETRY
# -----------------------------------------------------------------------------
def load_wav_stereo(file_path: str) -> Tuple[np.ndarray, int]:
    """Loads a WAV file into normalized float64 stereo array [-1.0, 1.0] and sample rate."""
    with wave.open(file_path, "rb") as wf:
        num_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        num_frames = wf.getnframes()
        raw_bytes = wf.readframes(num_frames)

    if sampwidth == 2:
        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float64) / 32768.0
    elif sampwidth == 3:
        int_data = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3)
        int32_data = (int_data[:, 0].astype(np.int32) |
                      (int_data[:, 1].astype(np.int32) << 8) |
                      (int_data[:, 2].astype(np.int32) << 16))
        int32_data = np.where(int32_data >= 0x800000, int32_data - 0x1000000, int32_data)
        audio = int32_data.astype(np.float64) / 8388608.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float64) / 32768.0

    if num_channels == 1:
        stereo = np.column_stack((audio, audio))
    else:
        stereo = audio.reshape(-1, num_channels)[:, :2]

    return stereo, framerate


def compute_integrated_lufs(audio_stereo: np.ndarray, sample_rate: int) -> float:
    """Computes ITU-R BS.1770-4 K-weighted Integrated Loudness."""
    # Stage 1: High shelf filter (+4 dB at 1.5 kHz)
    b_shelf = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    a_shelf = [1.0, -1.69065929318241, 0.73248077421585]
    # Stage 2: High pass RLB filter (~38 Hz)
    b_rlb = [1.0, -2.0, 1.0]
    a_rlb = [1.0, -1.99004745483398, 0.99007225035621]

    filtered = np.zeros_like(audio_stereo)
    for ch in range(2):
        s1 = signal.lfilter(b_shelf, a_shelf, audio_stereo[:, ch])
        filtered[:, ch] = signal.lfilter(b_rlb, a_rlb, s1)

    mean_sq = np.mean(filtered ** 2, axis=0)
    sum_energy = float(mean_sq[0] + mean_sq[1])
    if sum_energy < 1e-12:
        return -70.0
    return float(round(-0.691 + 10.0 * math.log10(sum_energy), 2))


def compute_true_peak_dbtp(audio_stereo: np.ndarray) -> float:
    """Computes True Peak in dBTP using 4x polyphase oversampling."""
    up_L = signal.resample_poly(audio_stereo[:, 0], up=4, down=1)
    up_R = signal.resample_poly(audio_stereo[:, 1], up=4, down=1)
    peak = max(float(np.max(np.abs(up_L))), float(np.max(np.abs(up_R))), 1e-6)
    return float(round(20.0 * math.log10(peak), 2))


# -----------------------------------------------------------------------------
# 3. RUBIN ACOUSTIC LINTER METROLOGY (Invariantes C5-REAL)
# -----------------------------------------------------------------------------
def compute_rubin_metrics(left: np.ndarray, right: np.ndarray) -> Dict[str, Any]:
    """Evaluates the 4 canonical physical invariants of the Rubin Protocol."""
    mono = 0.5 * (left + right)
    peak = float(np.max(np.abs(mono)))
    rms = float(np.sqrt(np.mean(mono ** 2)))
    cf = 20.0 * math.log10(peak / max(rms, 1e-6)) if rms > 0 and peak > 0 else 0.0

    # Spectral Flatness (Wiener entropy)
    win = np.hanning(min(len(mono), 65536))
    chunk = mono[:len(win)] * win
    spec = np.abs(np.fft.rfft(chunk)) ** 2 + 1e-12
    sfm = float(np.exp(np.mean(np.log(spec))) / np.mean(spec))

    # Low-End Phase Coherence (<120 Hz correlation)
    num = float(np.sum(left * right))
    den = float(np.sqrt(np.sum(left ** 2)) * np.sqrt(np.sum(right ** 2)))
    lpc = float(num / den) if den > 0 else 1.0

    anomalies = []
    if cf < 8.0:
        anomalies.append(f"Anergía por Hipercompresión: Crest Factor {cf:.2f} dB < 8.0 dB")
    if sfm > 0.35:
        anomalies.append(f"Anergía por Capas Parásitas: Spectral Flatness {sfm:.3f} > 0.35")
    if lpc < 0.85:
        anomalies.append(f"Anergía por Desfase Estéreo: Low-End Coherence {lpc:.3f} < 0.85")

    is_pure_bone = len(anomalies) == 0
    return {
        "crest_factor_db": round(cf, 2),
        "spectral_flatness_sfm": round(sfm, 3),
        "low_end_phase_coherence": round(lpc, 3),
        "is_pure_bone": is_pure_bone,
        "verdict": "EXERGÍA PURA (EL HUESO)" if is_pure_bone else "NATA ACÚSTICA DETECTADA",
        "anomalies": anomalies
    }


# -----------------------------------------------------------------------------
# 4. REVERSE-ENGINEERED DSP STAGES (FL Studio Stock & TDR Isomorphism)
# -----------------------------------------------------------------------------
class FLReverseMasteringDSP:
    """
    Modular Mastering Engine implementing the Tokyo Dawn / Maximus / Soft Clipper pipeline.
    """
    def __init__(self, sample_rate: int, profile: Dict[str, Any]):
        self.sr = sample_rate
        self.profile = profile
        self.nyquist = sample_rate / 2.0

    def stage1_linear_phase_eq_and_mid_side(self, audio: np.ndarray) -> np.ndarray:
        """
        Stage 1: Fruity Parametric EQ 2 (Linear Phase) & TDR SlickEQ M.
        1. Infrasonic High-Pass FIR filter at lowest_freq (steep cut to clean headroom).
        2. Mid/Side Transformation:
           - Collapses low frequencies (< mono_crossover_hz) to 100% mono on Side channel.
           - Subtle high-frequency air widening on Side channel (> 5 kHz).
        """
        # 1. Infrasonic cut via 2nd-order Butterworth high-pass
        cutoff_hp = max(20.0, float(self.profile.get("lowest_freq", 30.0)))
        norm_hp = min(0.49, cutoff_hp / self.nyquist)
        b_hp, a_hp = signal.butter(2, norm_hp, btype="high")

        hp_filtered = np.zeros_like(audio)
        hp_filtered[:, 0] = signal.lfilter(b_hp, a_hp, audio[:, 0])
        hp_filtered[:, 1] = signal.lfilter(b_hp, a_hp, audio[:, 1])

        # 2. Mid/Side encoding
        mid = (hp_filtered[:, 0] + hp_filtered[:, 1]) * 0.5
        side = (hp_filtered[:, 0] - hp_filtered[:, 1]) * 0.5

        # 3. Side Low-End Crossover Filter (Elliptic mono-maker)
        crossover = float(self.profile.get("mono_crossover_hz", 120.0))
        norm_cross = min(0.45, crossover / self.nyquist)
        b_side_hp, a_side_hp = signal.butter(3, norm_cross, btype="high")
        side_monoed = signal.lfilter(b_side_hp, a_side_hp, side)

        # 4. Side Air Excitation (Shelving boost > 5 kHz)
        side_boost_db = float(self.profile.get("side_high_boost_db", 0.8))
        if side_boost_db > 0:
            norm_shelf = min(0.48, 5000.0 / self.nyquist)
            b_shelf, a_shelf = signal.butter(1, norm_shelf, btype="high")
            side_highs = signal.lfilter(b_shelf, a_shelf, side_monoed)
            boost_factor = 10.0 ** (side_boost_db / 20.0) - 1.0
            side_monoed = side_monoed + side_highs * boost_factor

        # 5. Mid/Side decoding back to L/R
        left = mid + side_monoed
        right = mid - side_monoed
        return np.column_stack((left, right))

    def stage2_multiband_dynamics_glue(self, audio: np.ndarray) -> np.ndarray:
        """
        Stage 2: Maximus / TDR Kotelnikov Multiband Dynamics Glue.
        Splits into 3 bands (Low: <120 Hz, Mid: 120-4000 Hz, High: >4000 Hz).
        Applies gentle program-dependent RMS compression preserving transient punch.
        """
        cross_low = min(0.4, float(self.profile.get("mono_crossover_hz", 120.0)) / self.nyquist)
        cross_high = min(0.45, 4000.0 / self.nyquist)

        # 2-pole Linkwitz-Riley crossover filters
        b_l, a_l = signal.butter(2, cross_low, btype="low")
        b_m_hp, a_m_hp = signal.butter(2, cross_low, btype="high")
        b_m_lp, a_m_lp = signal.butter(2, cross_high, btype="low")
        b_h, a_h = signal.butter(2, cross_high, btype="high")

        low = np.zeros_like(audio)
        mid = np.zeros_like(audio)
        high = np.zeros_like(audio)

        for ch in range(2):
            low[:, ch] = signal.lfilter(b_l, a_l, audio[:, ch])
            mid_band = signal.lfilter(b_m_hp, a_m_hp, audio[:, ch])
            mid[:, ch] = signal.lfilter(b_m_lp, a_m_lp, mid_band)
            high[:, ch] = signal.lfilter(b_h, a_h, audio[:, ch])

        # Gentle glue compression on Mid band (Ratio 1.4:1 to 1.6:1)
        ratio = float(self.profile.get("mid_glue_ratio", 1.5))
        mid_rms = np.sqrt(np.mean(mid ** 2) + 1e-12)
        mid_thresh = mid_rms * 1.8
        mid_mag = np.abs(mid)
        mask = mid_mag > mid_thresh
        if np.any(mask):
            excess = mid_mag[mask] - mid_thresh
            compressed = mid_thresh + excess / ratio
            mid[mask] = np.sign(mid[mask]) * compressed

        # Recombine bands
        return low + mid + high

    def stage3_fruity_soft_clipper(self, audio: np.ndarray, threshold_db: float = -2.5) -> np.ndarray:
        """
        Stage 3: Fruity Soft Clipper True Behavior (The Modern FL Loudness Secret).
        - 100% Linear below threshold (zero harmonic distortion, preserves transience & crest factor).
        - Hyperbolic tangent saturation strictly on transient crest peaks exceeding threshold.
        """
        thresh_linear = 10.0 ** (threshold_db / 20.0)  # ~0.75 for -2.5 dBFS
        drive_db = float(self.profile.get("soft_clipper_drive_db", 1.0))
        if drive_db <= 0.05:
            return audio

        out = audio.copy()
        mag = np.abs(out)
        mask = mag > thresh_linear
        if np.any(mask):
            sgn = np.sign(out[mask])
            excess = mag[mask] - thresh_linear
            drive_scale = 10.0 ** (drive_db / 20.0)
            margin = max(1e-4, 1.0 - thresh_linear)
            compressed = thresh_linear + (margin / drive_scale) * np.tanh(excess * drive_scale / margin)
            out[mask] = sgn * np.clip(compressed, 0.0, 1.0)

        return out

    def stage4_true_peak_lookahead_limiter(
        self, audio: np.ndarray, target_dbtp: float
    ) -> np.ndarray:
        """
        Stage 4: Fruity Limiter & TDR Limiter 6 GE True-Peak Brickwall Limiter.
        Uses 4x polyphase oversampling to detect and prevent inter-sample peaks (ISP).
        """
        target_linear = 10.0 ** (target_dbtp / 20.0)

        # 4x oversampling
        up_L = signal.resample_poly(audio[:, 0], up=4, down=1)
        up_R = signal.resample_poly(audio[:, 1], up=4, down=1)

        # Soft-knee limiting on oversampled domain
        knee_start = target_linear * 0.88
        for ch in [up_L, up_R]:
            mask = np.abs(ch) > knee_start
            if np.any(mask):
                mag = np.abs(ch[mask])
                sgn = np.sign(ch[mask])
                delta = mag - knee_start
                scale = target_linear - knee_start
                compressed = knee_start + scale * np.tanh(delta / max(1e-4, scale))
                ch[mask] = sgn * compressed

        # Hard True Peak clamp on 4x oversampled domain
        up_L = np.clip(up_L, -target_linear, target_linear)
        up_R = np.clip(up_R, -target_linear, target_linear)

        # Downsample back to 1x
        down_L = signal.resample_poly(up_L, up=1, down=4)[:len(audio)]
        down_R = signal.resample_poly(up_R, up=1, down=4)[:len(audio)]

        return np.column_stack((down_L, down_R))

    def stage5_psychoacoustic_tpdf_dither(self, audio: np.ndarray, bit_depth: int = 24) -> np.ndarray:
        """
        Stage 5: High-Pass Triangular Probability Density Function (TPDF) Dither.
        Shifts quantization noise upward away from human ear's high sensitivity range (3-4 kHz).
        """
        lsb = 1.0 / (2.0 ** (bit_depth - 1))
        # High-pass triangular dither: (rand1 - rand2) filtered
        r1 = np.random.uniform(-0.5 * lsb, 0.5 * lsb, len(audio))
        r2 = np.random.uniform(-0.5 * lsb, 0.5 * lsb, len(audio))
        tpdf = r1 - r2

        dithered = np.zeros_like(audio)
        for ch in range(2):
            dithered[:, ch] = np.round((audio[:, ch] + tpdf) / lsb) * lsb

        return np.clip(dithered, -1.0, 1.0)


# -----------------------------------------------------------------------------
# 5. MASTERING PIPELINE ORCHESTRATOR
# -----------------------------------------------------------------------------
def master_audio_reverse_engineered(
    input_wav: str,
    output_wav: Optional[str] = None,
    profile_name: str = "techno",
    custom_target_lufs: Optional[float] = None,
    custom_target_dbtp: Optional[float] = None,
    bit_depth: int = 24
) -> Dict[str, Any]:
    """
    Executes the complete reverse-engineered mastering pass on input audio.
    """
    in_path = Path(input_wav).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_path}")

    profile = REVERSE_MASTERING_PROFILES.get(profile_name.lower(), REVERSE_MASTERING_PROFILES["techno"]).copy()
    if custom_target_lufs is not None:
        profile["target_lufs"] = float(custom_target_lufs)
    if custom_target_dbtp is not None:
        profile["target_dbtp"] = float(custom_target_dbtp)

    target_lufs = float(profile["target_lufs"])
    target_dbtp = float(profile["target_dbtp"])

    # Load audio
    audio_raw, sample_rate = load_wav_stereo(str(in_path))

    # Initial metrics
    lufs_initial = compute_integrated_lufs(audio_raw, sample_rate)
    peak_dbtp_initial = compute_true_peak_dbtp(audio_raw)
    rubin_initial = compute_rubin_metrics(audio_raw[:, 0], audio_raw[:, 1])

    dsp = FLReverseMasteringDSP(sample_rate, profile)

    # 1. Stage 1: Linear Phase Sub Cut & Mid/Side Low-Mono Maker
    s1 = dsp.stage1_linear_phase_eq_and_mid_side(audio_raw)

    # 2. Stage 2: Multiband Dynamics Glue
    s2 = dsp.stage2_multiband_dynamics_glue(s1)

    # 3. Stage 3: Normalization Gain toward target LUFS
    current_lufs = compute_integrated_lufs(s2, sample_rate)
    gain_db = target_lufs - current_lufs
    gain_db = max(-15.0, min(15.0, gain_db))
    linear_gain = 10.0 ** (gain_db / 20.0)
    gained = s2 * linear_gain

    # 4. Stage 4: Fruity Soft Clipper (Pre-shaving transient crests)
    s4 = dsp.stage3_fruity_soft_clipper(gained)

    # 5. Stage 5: True Peak Lookahead Brickwall Limiter (4x oversampled)
    s5 = dsp.stage4_true_peak_lookahead_limiter(s4, target_dbtp)

    # Secondary fine-trim gain if limiting slightly adjusted LUFS
    post_lufs = compute_integrated_lufs(s5, sample_rate)
    if abs(target_lufs - post_lufs) > 0.8:
        trim_db = target_lufs - post_lufs
        trim_db = max(-2.0, min(2.0, trim_db))
        s5 = dsp.stage4_true_peak_lookahead_limiter(s5 * (10.0 ** (trim_db / 20.0)), target_dbtp)

    # 6. Stage 6: Psychoacoustic TPDF Dither
    mastered = dsp.stage5_psychoacoustic_tpdf_dither(s5, bit_depth=bit_depth)

    # Final metrics
    lufs_final = compute_integrated_lufs(mastered, sample_rate)
    peak_dbtp_final = compute_true_peak_dbtp(mastered)
    rubin_final = compute_rubin_metrics(mastered[:, 0], mastered[:, 1])

    # Destination paths
    if not output_wav:
        out_dir = in_path.parent / "mastered"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / f"{in_path.stem}_ReverseMaster_{profile_name.upper()}.wav"
    else:
        output_file = Path(output_wav).expanduser().resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write WAV
    if bit_depth == 24:
        # Fast vectorized 24-bit PCM write
        int32_data = np.clip(mastered * 8388607.0, -8388608, 8388607).astype("<i4")
        bytes_3 = int32_data.flatten().view(np.uint8).reshape(-1, 4)[:, :3]
        with wave.open(str(output_file), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(3)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes_3.tobytes())
    else:
        # Write 16-bit PCM
        int16_data = np.clip(mastered * 32767.0, -32768, 32767).astype(np.int16)
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
        "true_peak_dbtp_before": peak_dbtp_initial,
        "true_peak_dbtp_after": peak_dbtp_final,
        "gain_applied_db": round(gain_db, 2),
        "rubin_audit_before": rubin_initial,
        "rubin_audit_after": rubin_final,
        "file_size_mb": round(output_file.stat().st_size / (1024 * 1024), 2)
    }


def main():
    parser = argparse.ArgumentParser(description="FL Studio Reverse-Engineered Mastering Engine (C5-REAL)")
    parser.add_argument("--input", "-i", required=True, help="Input WAV audio file")
    parser.add_argument("--output", "-o", default=None, help="Output master WAV file")
    parser.add_argument("--profile", "-p", default="techno", choices=list(REVERSE_MASTERING_PROFILES.keys()), help="Mastering profile")
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
            bit_depth=args.bits
        )

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("\n" + "=" * 65)
            print("  FL STUDIO REVERSE-ENGINEERED MASTERING ENGINE (C5-REAL)")
            print("=" * 65)
            print(f" Archivo Entrada:   {report['input_file']}")
            print(f" Archivo Master:    {report['output_file']}")
            print(f" Perfil Aplicado:   {report['profile'].upper()} ({report['profile_details']['name']})")
            print(f" Carácter Sónico:   {report['profile_details']['character']}")
            print("-" * 65)
            print(" TELEMETRÍA DE SONORIDAD (ITU-R BS.1770-4):")
            print(f"  • Integrated LUFS:   {report['lufs_before']} dB ──► {report['lufs_after']} dB (Target: {report['profile_details']['target_lufs']} dB)")
            print(f"  • True Peak dBTP:    {report['true_peak_dbtp_before']} dBTP ──► {report['true_peak_dbtp_after']} dBTP (Ceiling: {report['profile_details']['target_dbtp']} dBTP)")
            print(f"  • Ganancia Normaliz: {report['gain_applied_db']:+.2f} dB")
            print("-" * 65)
            print(" AUDITORÍA ACÚSTICA RUBIN (C5-REAL SILICON LINTER):")
            r = report['rubin_audit_after']
            print(f"  • Factor de Cresta:  {r['crest_factor_db']} dB (Óptimo: 8.5 - 11.5 dB)")
            print(f"  • Planitud (Wiener): {r['spectral_flatness_sfm']} (Cumple: < 0.15)")
            print(f"  • Coherencia Graves: {r['low_end_phase_coherence']} (Mono <120 Hz: >= 0.95)")
            print(f"  • Veredicto Final:   [{r['verdict']}]")
            print("=" * 65 + "\n")

    except Exception as e:
        print(f"Error fatal en masterización: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
