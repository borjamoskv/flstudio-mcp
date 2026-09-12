#!/usr/bin/env python3
"""
Binaural Woodworth 3D Spatializer (v14.0 Continuum)
Implements physical spherical head acoustics (Woodworth ITD model + Brown & Duda ILD head-shadow filter)
to spatialize audio stems into fully exteriorized 3D Binaural sound (anti in-head localization).

Acoustic Parameters:
- Head radius a = 0.0875 m (average human head)
- Speed of sound c = 343 m/s
- Woodworth ITD: tau(theta) = (a / c) * (sin|theta| + |theta|)
- Head-shadow ILD filter: 1st-order continuous s-domain pole-zero mapped via bilinear transform
- Pinna notch elevation filter: comb filter reflection simulating vertical pinna dispersion
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy import signal

logger = logging.getLogger("FLStudio-Binaural3D")

HEAD_RADIUS_M = 0.0875   # 8.75 cm
SPEED_OF_SOUND = 343.0   # m/s


def load_wav_as_mono_float(wav_path: str) -> Tuple[np.ndarray, int]:
    """Reads a WAV file and returns normalized mono float64 array and sample rate."""
    with wave.open(wav_path, "rb") as wf:
        num_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        num_frames = wf.getnframes()
        raw_bytes = wf.readframes(num_frames)

    if sampwidth == 2:
        dtype = np.int16
        scale = 32768.0
    elif sampwidth == 3:
        int_data = np.frombuffer(raw_bytes, dtype=np.uint8)
        reshaped = int_data.reshape(-1, 3)
        int32_data = (reshaped[:, 0].astype(np.int32) |
                      (reshaped[:, 1].astype(np.int32) << 8) |
                      (reshaped[:, 2].astype(np.int32) << 16))
        int32_data = np.where(int32_data >= 0x800000, int32_data - 0x1000000, int32_data)
        audio = int32_data.astype(np.float64) / 8388608.0
        if num_channels > 1:
            audio = audio.reshape(-1, num_channels).mean(axis=1)
        return audio, framerate
    elif sampwidth == 4:
        dtype = np.int32
        scale = 2147483648.0
    else:
        dtype = np.int16
        scale = 32768.0

    audio = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float64) / scale
    if num_channels > 1:
        audio = audio.reshape(-1, num_channels).mean(axis=1)
    return audio, framerate


def design_head_shadow_filter(theta_ear_rad: float, sample_rate: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Designs a 1st-order head-shadow filter for the ear at angle theta_ear_rad (0 = directly facing source).
    Uses Brown & Duda's structural model for frequency-dependent ILD attenuation.
    """
    theta = abs(theta_ear_rad)
    alpha_min = 0.15  # Maximum high-frequency attenuation (~ -16 dB)
    alpha = 1.0 + ((alpha_min - 1.0) / 2.0) * (1.0 - math.cos(theta))

    # Characteristic head frequency f0 ~ c / (2 * pi * a) ~ 624 Hz
    w0 = SPEED_OF_SOUND / HEAD_RADIUS_M  # ~ 3920 rad/s

    # Analog pole-zero: H(s) = (alpha * s / w0 + 1) / (s / w0 + 1)
    b_analog = [alpha / w0, 1.0]
    a_analog = [1.0 / w0, 1.0]

    # Bilinear transform to digital IIR filter
    b_d, a_d = signal.bilinear(b_analog, a_analog, fs=sample_rate)
    return b_d, a_d


def apply_fractional_delay(audio: np.ndarray, delay_samples: float) -> np.ndarray:
    """Applies high-fidelity linear interpolated sample delay."""
    if delay_samples <= 0.001:
        return audio.copy()

    int_delay = int(math.floor(delay_samples))
    frac_delay = delay_samples - int_delay

    out = np.zeros_like(audio)
    if int_delay + 1 < len(audio):
        out[int_delay:] = (1.0 - frac_delay) * audio[:len(audio) - int_delay]
        out[int_delay + 1:] += frac_delay * audio[:len(audio) - int_delay - 1]
    return out


def spatialize_binaural_woodworth(
    input_wav: str,
    output_wav: Optional[str] = None,
    azimuth_deg: float = 30.0,
    elevation_deg: float = 10.0,
    distance_m: float = 1.8
) -> Dict[str, Any]:
    """
    Spatialize mono/stereo WAV into 3D Binaural audio using Woodworth ITD + Brown-Duda ILD.
    azimuth_deg: -180 to +180 deg (0 = front, +90 = left, -90 = right, 180 = behind).
    elevation_deg: -90 to +90 deg (0 = horizon, +90 = top zenith, -90 = bottom nadir).
    distance_m: source distance in meters (controls inverse-distance attenuation).
    """
    in_path = Path(input_wav).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_path}")

    audio, sample_rate = load_wav_as_mono_float(str(in_path))

    # Normalize azimuth to [-pi, pi]
    azimuth_rad = math.radians(azimuth_deg)
    elevation_rad = math.radians(elevation_deg)

    # Relative angle to Left Ear (+pi/2) and Right Ear (-pi/2)
    # Left ear: theta_L = azimuth - pi/2
    # Right ear: theta_R = azimuth + pi/2
    theta_L = math.atan2(math.sin(azimuth_rad - math.pi / 2.0), math.cos(azimuth_rad - math.pi / 2.0))
    theta_R = math.atan2(math.sin(azimuth_rad + math.pi / 2.0), math.cos(azimuth_rad + math.pi / 2.0))

    # Woodworth ITD calculation
    # Path delay from center of head:
    # If ear is facing source (angle < pi/2): delay = -a * cos(angle) / c
    # If ear is shadowed (angle >= pi/2): delay = a * (angle - pi/2) / c
    def ear_itd_seconds(angle: float) -> float:
        ang = abs(angle)
        if ang < math.pi / 2.0:
            return (HEAD_RADIUS_M / SPEED_OF_SOUND) * (1.0 - math.cos(math.pi / 2.0 - ang))
        else:
            return (HEAD_RADIUS_M / SPEED_OF_SOUND) * (1.0 + (ang - math.pi / 2.0))

    itd_L_sec = ear_itd_seconds(theta_L)
    itd_R_sec = ear_itd_seconds(theta_R)

    # Normalize ITD so minimum delay is 0
    min_itd = min(itd_L_sec, itd_R_sec)
    itd_L_sec -= min_itd
    itd_R_sec -= min_itd

    delay_samples_L = itd_L_sec * sample_rate
    delay_samples_R = itd_R_sec * sample_rate

    # Head shadow filters (ILD)
    b_L, a_L = design_head_shadow_filter(theta_L, sample_rate)
    b_R, a_R = design_head_shadow_filter(theta_R, sample_rate)

    filt_L = signal.lfilter(b_L, a_L, audio)
    filt_R = signal.lfilter(b_R, a_R, audio)

    # Apply ITD delays
    bin_L = apply_fractional_delay(filt_L, delay_samples_L)
    bin_R = apply_fractional_delay(filt_R, delay_samples_R)

    # Pinna notch elevation cue (subtle comb reflection at 6-10 kHz)
    # Elevation from -pi/2 to +pi/2
    pinna_delay_sec = 0.000100 * (1.0 - math.sin(elevation_rad))  # 0 to 200 microseconds
    pinna_samples = pinna_delay_sec * sample_rate
    if pinna_samples > 0.1:
        pinna_refl_L = apply_fractional_delay(bin_L, pinna_samples) * 0.35
        pinna_refl_R = apply_fractional_delay(bin_R, pinna_samples) * 0.35
        bin_L = bin_L - pinna_refl_L
        bin_R = bin_R - pinna_refl_R

    # Distance attenuation (1/r)
    dist = max(0.5, distance_m)
    dist_gain = 1.0 / dist
    bin_L *= dist_gain
    bin_R *= dist_gain

    # Interaural Cross-Correlation (IACC) estimation
    corr = np.correlate(bin_L[:10000], bin_R[:10000], mode="full")
    norm_factor = np.sqrt(np.sum(bin_L[:10000]**2) * np.sum(bin_R[:10000]**2) + 1e-9)
    iacc_peak = float(np.max(np.abs(corr)) / norm_factor)

    # Interleave into stereo 16-bit PCM WAV
    stereo = np.zeros((len(bin_L), 2), dtype=np.float32)
    stereo[:, 0] = bin_L
    stereo[:, 1] = bin_R

    peak = np.max(np.abs(stereo))
    if peak > 0.98:
        stereo = stereo * (0.95 / peak)

    int16_stereo = np.clip(stereo * 32767.0, -32768, 32767).astype(np.int16)

    if not output_wav:
        out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Binaural_3D"
        out_dir.mkdir(parents=True, exist_ok=True)
        stem_name = in_path.stem
        output_file = out_dir / f"{stem_name}_Binaural3D_Az{int(azimuth_deg)}_El{int(elevation_deg)}.wav"
    else:
        output_file = Path(output_wav).expanduser().resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(output_file), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_stereo.tobytes())

    return {
        "status": "SUCCESS",
        "spatial_model": "Woodworth_Spherical_Head_ITD_ILD",
        "azimuth_deg": azimuth_deg,
        "elevation_deg": elevation_deg,
        "distance_m": distance_m,
        "itd_left_usec": round(itd_L_sec * 1e6, 1),
        "itd_right_usec": round(itd_R_sec * 1e6, 1),
        "iacc_inter_aural_correlation": round(iacc_peak, 4),
        "sample_rate_hz": sample_rate,
        "duration_sec": round(len(bin_L) / sample_rate, 2),
        "output_file": str(output_file),
        "file_size_kb": round(output_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    test_in = Path.home() / "Music/FL Studio Bounces/Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    if test_in.exists():
        res = spatialize_binaural_woodworth(str(test_in), azimuth_deg=45.0, elevation_deg=20.0, distance_m=1.5)
        print("Binaural 3D Spatializer output:", res)
    else:
        print("Test file not found:", test_in)
