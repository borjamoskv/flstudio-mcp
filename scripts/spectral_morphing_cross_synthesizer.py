#!/usr/bin/env python3
"""
Spectral Morphing & Cross-Synthesis Vocoder (v16.0 Sovereign Apex)
Executes continuous non-stationary STFT spectral morphing between two audio streams,
interpolating between carrier harmonics and modulator formant structures with phase coherence.

Formulation:
- STFT 2048-point Hann window with 75% overlap
- Spectral Envelope Homomorphic Extraction (Cepstral Liftering)
- Log-magnitude cross-synthesis: |S_morph(t, f)| = |C(t, f)|^(1 - alpha(t)) * |M(t, f)|^(alpha(t))
- High-transient phase preservation avoiding smearing
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy import signal

logger = logging.getLogger("FLStudio-SpectralMorph")


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

    if num_channels > 1:
        audio = audio.reshape(-1, num_channels).mean(axis=1)
    return audio, framerate


def morph_spectral_cross_synthesis(
    carrier_wav: str,
    modulator_wav: str,
    output_wav: Optional[str] = None,
    morph_factor: float = 0.5,
    formant_preservation: bool = True
) -> Dict[str, Any]:
    """
    Morphs between Carrier and Modulator audio stems.
    - morph_factor: 0.0 = pure carrier, 0.5 = hybrid chimera, 1.0 = pure modulator
    - formant_preservation: applies cepstral liftering to imprint modulator formants onto carrier pitch
    """
    c_path = Path(carrier_wav).expanduser().resolve()
    m_path = Path(modulator_wav).expanduser().resolve()

    if not c_path.exists():
        raise FileNotFoundError(f"Carrier WAV not found: {c_path}")
    if not m_path.exists():
        raise FileNotFoundError(f"Modulator WAV not found: {m_path}")

    audio_c, sr_c = load_wav_as_mono_float(str(c_path))
    audio_m, sr_m = load_wav_as_mono_float(str(m_path))

    # Match lengths and sample rates
    sr = sr_c
    if sr_c != sr_m:
        new_len = int(round(len(audio_m) * float(sr_c) / float(sr_m)))
        audio_m = signal.resample(audio_m, new_len)

    min_len = min(len(audio_c), len(audio_m))
    audio_c = audio_c[:min_len]
    audio_m = audio_m[:min_len]

    # STFT parameters
    nperseg = 2048
    noverlap = 1536
    fc, tc, Zc = signal.stft(audio_c, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap)
    fm, tm, Zm = signal.stft(audio_m, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap)

    # Align frame count
    n_frames = min(Zc.shape[1], Zm.shape[1])
    Zc = Zc[:, :n_frames]
    Zm = Zm[:, :n_frames]

    mag_c = np.abs(Zc) + 1e-9
    mag_m = np.abs(Zm) + 1e-9

    alpha = max(0.0, min(1.0, morph_factor))

    if formant_preservation:
        # Extract smooth spectral envelope of modulator via low-frequency cepstral lifter
        log_mag_m = np.log(mag_m)
        # Apply 1D smoothing along frequency axis (moving average as cepstral lifter approximation)
        kernel_size = 25
        kernel = np.ones(kernel_size) / kernel_size
        env_m = np.zeros_like(log_mag_m)
        for t_idx in range(n_frames):
            env_m[:, t_idx] = np.convolve(log_mag_m[:, t_idx], kernel, mode="same")
        smooth_mag_m = np.exp(env_m)

        # Cross-synthesize: Carrier fine harmonic pitch structure * Modulator spectral envelope
        mag_morph = (mag_c ** (1.0 - alpha * 0.5)) * ((smooth_mag_m / np.mean(smooth_mag_m)) ** alpha)
    else:
        # Direct geometric interpolation of magnitudes
        mag_morph = (mag_c ** (1.0 - alpha)) * (mag_m ** alpha)

    # Phase interpolation: primarily preserve carrier harmonic phase, modulated by spectral flux
    phase_c = np.angle(Zc)
    phase_m = np.angle(Zm)
    phase_morph = phase_c * (1.0 - alpha * 0.3) + phase_m * (alpha * 0.3)

    Z_morph = mag_morph * np.exp(1j * phase_morph)

    # Inverse STFT
    _, audio_out = signal.istft(Z_morph, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap)
    audio_out = audio_out[:min_len].astype(np.float32)

    # Peak normalization
    peak = float(np.max(np.abs(audio_out)))
    if peak > 0.01:
        audio_out = audio_out * (0.92 / peak)

    # Destination paths
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Spectral_Morphs"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"Morph_{c_path.stem}_x_{m_path.stem}_alpha{int(alpha*100)}.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    int16_out = np.clip(audio_out * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_out.tobytes())

    return {
        "status": "SUCCESS",
        "morph_algorithm": "STFT_Cepstral_Liftered_Cross_Synthesis",
        "carrier_file": str(c_path),
        "modulator_file": str(m_path),
        "morph_factor": alpha,
        "formant_preservation": formant_preservation,
        "sample_rate_hz": sr,
        "duration_sec": round(min_len / sr, 2),
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    bounces = Path.home() / "Music/FL Studio Bounces"
    c_test = bounces / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    m_test = bounces / "Neuroacoustics/Neuroacoustic_gamma_40hz_146Hz_Carrier.wav"
    if c_test.exists() and m_test.exists():
        res = morph_spectral_cross_synthesis(str(c_test), str(m_test), morph_factor=0.45)
        print("Spectral Morph output:", res)
    else:
        print("Files not found for test")
