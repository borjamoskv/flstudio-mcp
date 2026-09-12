#!/usr/bin/env python3
"""
Spectral Harmonic-Percussive Sound Separation (HPSS) Engine (v14.0 Continuum)
Implements FitzGerald / Ono median-filtering STFT separation in pure Python + SciPy
to dissect composite audio stems into pure continuous harmonic tones and transient percussive bursts.

Algorithm:
1. STFT with 2048-point Hann window (46 ms resolution)
2. Horizontal 1D median filtering along time axis -> Harmonic spectrogram H
3. Vertical 1D median filtering along frequency axis -> Percussive spectrogram P
4. Soft Wiener power-masking (p=2) ensuring phase conservation
5. Inverse STFT synthesis into discrete broadcast 16-bit PCM WAV stems
"""

import wave
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy import signal, ndimage

logger = logging.getLogger("FLStudio-HPSS")


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


def separate_harmonic_percussive(
    input_wav: str,
    output_dir: Optional[str] = None,
    time_kernel_frames: int = 31,
    freq_kernel_bins: int = 17,
    mask_power: float = 2.0
) -> Dict[str, Any]:
    """
    Separates input WAV into Harmonic and Percussive components via 2D STFT median filtering.
    - time_kernel_frames: horizontal kernel width (~0.2s for harmonic sustain)
    - freq_kernel_bins: vertical kernel height (~360Hz for percussive transients)
    - mask_power: Wiener mask exponent (typically 2.0)
    """
    in_path = Path(input_wav).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_path}")

    audio, sample_rate = load_wav_as_mono_float(str(in_path))

    # STFT parameters
    nperseg = 2048
    noverlap = 1536  # 75% overlap for artifact-free ISTFT
    f, t, Zxx = signal.stft(audio, fs=sample_rate, window="hann", nperseg=nperseg, noverlap=noverlap)

    mag = np.abs(Zxx)

    # Ensure odd kernel sizes for median filter
    k_time = time_kernel_frames if time_kernel_frames % 2 == 1 else time_kernel_frames + 1
    k_freq = freq_kernel_bins if freq_kernel_bins % 2 == 1 else freq_kernel_bins + 1

    # 1D Horizontal median filter along time (axis 1) -> Harmonic emphasis
    H_mag = ndimage.median_filter(mag, size=(1, k_time))

    # 1D Vertical median filter along frequency (axis 0) -> Percussive emphasis
    P_mag = ndimage.median_filter(mag, size=(k_freq, 1))

    # Soft Wiener power masks
    eps = 1e-9
    H_pow = H_mag ** mask_power
    P_pow = P_mag ** mask_power
    sum_pow = H_pow + P_pow + eps

    mask_H = H_pow / sum_pow
    mask_P = P_pow / sum_pow

    # Apply masks to original complex STFT
    Zxx_H = Zxx * mask_H
    Zxx_P = Zxx * mask_P

    # Inverse STFT
    _, audio_H = signal.istft(Zxx_H, fs=sample_rate, window="hann", nperseg=nperseg, noverlap=noverlap)
    _, audio_P = signal.istft(Zxx_P, fs=sample_rate, window="hann", nperseg=nperseg, noverlap=noverlap)

    # Match length to original audio
    min_len = min(len(audio), len(audio_H), len(audio_P))
    audio_H = audio_H[:min_len]
    audio_P = audio_P[:min_len]

    # Energy calculations
    energy_total = float(np.sum(audio[:min_len]**2) + eps)
    energy_H = float(np.sum(audio_H**2))
    energy_P = float(np.sum(audio_P**2))

    ratio_H = round(energy_H / energy_total, 3)
    ratio_P = round(energy_P / energy_total, 3)

    # Output paths
    if not output_dir:
        out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Demixed"
    else:
        out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    stem_base = in_path.stem
    path_H = out_dir / f"{stem_base}_Harmonic.wav"
    path_P = out_dir / f"{stem_base}_Percussive.wav"

    # Write 16-bit PCM WAVs
    for out_path, sig_data in [(path_H, audio_H), (path_P, audio_P)]:
        peak = np.max(np.abs(sig_data))
        if peak > 0.98:
            sig_data = sig_data * (0.95 / peak)
        int16_sig = np.clip(sig_data * 32767.0, -32768, 32767).astype(np.int16)
        with wave.open(str(out_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int16_sig.tobytes())

    return {
        "status": "SUCCESS",
        "demix_algorithm": "FitzGerald_STFT_2D_Median_Filter",
        "input_file": str(in_path),
        "harmonic_stem": str(path_H),
        "percussive_stem": str(path_P),
        "energy_ratio_harmonic": ratio_H,
        "energy_ratio_percussive": ratio_P,
        "sample_rate_hz": sample_rate,
        "duration_sec": round(min_len / sample_rate, 2),
        "harmonic_size_kb": round(path_H.stat().st_size / 1024, 1),
        "percussive_size_kb": round(path_P.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    test_in = Path.home() / "Music/FL Studio Bounces/Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    if test_in.exists():
        res = separate_harmonic_percussive(str(test_in))
        print("HPSS Demixer output:", res)
    else:
        print("Test file not found:", test_in)
