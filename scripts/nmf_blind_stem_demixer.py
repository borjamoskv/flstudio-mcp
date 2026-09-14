#!/usr/bin/env python3
"""
Spectrogram NMF & Wiener Blind Stem Separator (v17.0 Hyper-Dimensional Omni)
Implements unsupervised blind audio source separation via Non-Negative Matrix Factorization (NMF)
and generalized soft Wiener ratio masking.

Architecture:
- STFT 2048-point Hann window, 75% overlap
- Multiplicative update rules (Lee & Seung, 2001) for V ~ W * H
- Energy-band clustering into 4 discrete production stems:
  1. Percussive / Drums (high spectral flux & transients)
  2. Sub / Bass (< 250 Hz fundamental resonances)
  3. Tonal / Lead / Harmonics (250 Hz - 4000 Hz pitched formants)
  4. Air / Highs / Atmosphere (> 4000 Hz cymbal & noise tails)
- Soft Wiener ratio masking with gamma=1.5
- Centralized WAV bounces to ~/Music/FL Studio Bounces/Demixed/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from scipy import signal

logger = logging.getLogger("FLStudio-NMFDemixer")


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


def run_nmf_multiplicative(V: np.ndarray, K: int = 6, max_iter: int = 30) -> Tuple[np.ndarray, np.ndarray]:
    """
    Executes Lee & Seung multiplicative update rules for Non-Negative Matrix Factorization:
    V ~ W * H, where V is (F, T), W is (F, K), H is (K, T).
    """
    F, T = V.shape
    eps = 1e-9

    np.random.seed(42)
    # Initialize positive matrices
    W = np.random.uniform(0.1, 1.0, (F, K)).astype(np.float64)
    H = np.random.uniform(0.1, 1.0, (K, T)).astype(np.float64)

    for it in range(max_iter):
        # Update H: H <- H * (W^T * (V / (W*H + eps))) / (W^T * 1 + eps)
        WH = np.dot(W, H) + eps
        ratio = V / WH
        numerator_H = np.dot(W.T, ratio)
        denominator_H = np.sum(W, axis=0, keepdims=True).T + eps
        H *= (numerator_H / denominator_H)

        # Update W: W <- W * ((V / (W*H + eps)) * H^T) / (1 * H^T + eps)
        WH = np.dot(W, H) + eps
        ratio = V / WH
        numerator_W = np.dot(ratio, H.T)
        denominator_W = np.sum(H, axis=1, keepdims=True).T + eps
        W *= (numerator_W / denominator_W)

    return W, H


def demix_multitrack_nmf_blind(
    input_wav: Optional[str] = None,
    output_dir: Optional[str] = None,
    num_components: int = 6,
    nmf_iterations: int = 25
) -> Dict[str, Any]:
    """
    Decomposes an audio mix into 4 discrete perceptual stems using NMF & Wiener ratio masking:
    - Percussive Drums
    - Sub Bass
    - Tonal Harmonics
    - Air / Atmosphere
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

    # STFT parameters
    nperseg = 2048
    noverlap = 1536
    hop_length = nperseg - noverlap

    freqs, times, Zxx = signal.stft(audio, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap)
    mag = np.abs(Zxx)
    phase = np.angle(Zxx)

    # Run NMF decomposition
    W, H = run_nmf_multiplicative(mag, K=num_components, max_iter=nmf_iterations)

    # Classify each component into 4 stem buckets based on spectral centroid and flux
    # Spectral Centroid of each W column:
    centroids = np.dot(freqs, W) / (np.sum(W, axis=0) + 1e-9)
    # Temporal flux (variance across time of H)
    flux = np.std(H, axis=1) / (np.mean(H, axis=1) + 1e-9)

    # Categories:
    # 1. Bass: lowest centroid (< 300 Hz)
    # 2. Drums: highest temporal flux / transient burst
    # 3. Air: highest centroid (> 3500 Hz)
    # 4. Tonal: intermediate centroid & sustained temporal profile
    component_categories = {}
    remaining = list(range(num_components))

    # Identify bass
    bass_idx = min(remaining, key=lambda idx: centroids[idx])
    component_categories[bass_idx] = "Bass"
    remaining.remove(bass_idx)

    # Identify air
    air_idx = max(remaining, key=lambda idx: centroids[idx])
    component_categories[air_idx] = "Air"
    remaining.remove(air_idx)

    # Identify drums (highest flux of remaining)
    drums_idx = max(remaining, key=lambda idx: flux[idx])
    component_categories[drums_idx] = "Drums"
    remaining.remove(drums_idx)

    # Remaining go to Tonal Harmonics
    for rem in remaining:
        component_categories[rem] = "Tonal"

    # Build 4 aggregate spectral models
    models = {
        "Drums": np.zeros_like(mag),
        "Bass": np.zeros_like(mag),
        "Tonal": np.zeros_like(mag),
        "Air": np.zeros_like(mag)
    }

    for k in range(num_components):
        cat = component_categories[k]
        recon_k = np.outer(W[:, k], H[k, :])
        models[cat] += recon_k

    # Wiener soft ratio masking: M_cat = S_cat^1.5 / (Sum S_j^1.5 + eps)
    gamma = 1.5
    denom = np.zeros_like(mag)
    for cat in models:
        models[cat] = np.maximum(1e-12, models[cat]) ** gamma
        denom += models[cat]
    denom = np.maximum(1e-12, denom)

    # Output directory
    if not output_dir:
        out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Demixed" / in_file.stem
    else:
        out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    separated_stems = {}
    energy_ratios = {}
    total_mix_energy = float(np.sum(audio ** 2)) + 1e-9

    for cat_name, powered_model in models.items():
        mask = powered_model / denom
        # Apply mask to original complex STFT
        masked_Zxx = Zxx * mask
        _, stem_audio = signal.istft(masked_Zxx, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap)

        # Match length
        if len(stem_audio) > len(audio):
            stem_audio = stem_audio[:len(audio)]
        elif len(stem_audio) < len(audio):
            stem_audio = np.pad(stem_audio, (0, len(audio) - len(stem_audio)))

        # Normalize and prevent clipping
        stem_energy = float(np.sum(stem_audio ** 2))
        energy_ratios[cat_name] = round(stem_energy / total_mix_energy, 4)

        peak = np.max(np.abs(stem_audio))
        if peak > 0.99:
            stem_audio = (stem_audio / peak) * 0.95

        out_path = out_dir / f"{in_file.stem}_{cat_name}_Stem.wav"
        int16_out = np.clip(stem_audio * 32767.0, -32768, 32767).astype(np.int16)
        with wave.open(str(out_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(int16_out.tobytes())

        separated_stems[cat_name] = str(out_path)

    return {
        "status": "SUCCESS",
        "input_mix": str(in_file),
        "num_nmf_components": num_components,
        "nmf_iterations": nmf_iterations,
        "separated_stems": separated_stems,
        "energy_ratios": energy_ratios,
        "output_directory": str(out_dir),
        "duration_sec": round(len(audio) / sr, 2)
    }


if __name__ == "__main__":
    res = demix_multitrack_nmf_blind(num_components=4, nmf_iterations=15)
    print("NMF Demixer Output:", res)
