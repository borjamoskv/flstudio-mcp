#!/usr/bin/env python3
"""
Spectral Freeze & Phase-Vocoder Drone Synthesizer (v18.0 Demiurgic Nexus)
Implements STFT spectral freezing and stochastic phase-vocoder re-synthesis
for infinite ambient drones, harmonic textures, and shimmer pads.

Architecture:
- STFT 4096-point Hann window with 87.5% overlap
- Freeze time slice extraction: extracts magnitude spectrum |X(f)| at target timestamp
- Stochastic Phase Randomization: Delta phi(t, f) = 2*pi*f*H / fs + N(0, sigma^2)
  eliminating static metallic phasing artifacts
- Dual LFO octave/fifth shimmer envelope modulation
- Centralized WAV export to ~/Music/FL Studio Bounces/Drones_Freeze/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import signal

logger = logging.getLogger("FLStudio-SpectralFreeze")


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


def synthesize_spectral_freeze_drone(
    input_wav: Optional[str] = None,
    freeze_time_sec: float = 2.5,
    output_duration_sec: float = 6.0,
    output_wav: Optional[str] = None,
    shimmer_depth: float = 0.35,
    phase_diffusion: float = 0.20
) -> Dict[str, Any]:
    """
    Freezes a spectral frame from input_wav and re-synthesizes an evolving ambient drone.
    - freeze_time_sec: timestamp from source audio to freeze (seconds)
    - output_duration_sec: duration of generated drone
    - shimmer_depth: depth of octave/fifth harmonic shimmer modulation (0.0 to 1.0)
    - phase_diffusion: stochastic phase jitter variance preventing metallic comb filtering
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

    # STFT configuration
    nperseg = 4096
    hop = 512
    noverlap = nperseg - hop

    # Find the target frame index
    target_sample = int(min(len(audio) - nperseg - 1, max(0, freeze_time_sec * sr)))
    frame = audio[target_sample:target_sample + nperseg] * signal.windows.hann(nperseg)
    spectrum = np.fft.rfft(frame)
    frozen_mag = np.abs(spectrum)

    num_bins = len(frozen_mag)
    bin_freqs = np.fft.rfftfreq(nperseg, 1.0 / sr)

    # Number of output synthesis frames
    total_out_samples = int(output_duration_sec * sr)
    num_out_frames = int(math.ceil(total_out_samples / hop)) + 4

    # Pre-allocate STFT synthesis matrix
    synth_stft = np.zeros((num_bins, num_out_frames), dtype=np.complex128)

    # Initialize phase accumulator
    current_phase = np.random.uniform(-np.pi, np.pi, num_bins)
    phase_inc = 2.0 * np.pi * bin_freqs * (hop / sr)

    np.random.seed(42)

    for f_idx in range(num_out_frames):
        t_sec = (f_idx * hop) / sr

        # Shimmer harmonic modulation (slow dual LFOs)
        lfo1 = 0.5 * (1.0 + math.sin(2.0 * math.pi * 0.25 * t_sec))
        lfo2 = 0.5 * (1.0 + math.sin(2.0 * math.pi * 0.11 * t_sec))

        # Modulate magnitude curve with gentle spectral tilt/shimmer
        mag_t = np.copy(frozen_mag)
        if shimmer_depth > 0.0:
            shimmer_filter = 1.0 + shimmer_depth * (
                0.6 * lfo1 * np.sin(np.linspace(0, 4 * np.pi, num_bins)) +
                0.4 * lfo2 * np.cos(np.linspace(0, 2 * np.pi, num_bins))
            )
            mag_t = mag_t * np.maximum(0.2, shimmer_filter)

        # Update phases with fundamental increment + stochastic diffusion
        jitter = np.random.normal(0.0, phase_diffusion, num_bins)
        current_phase += phase_inc + jitter
        current_phase = (current_phase + np.pi) % (2.0 * np.pi) - np.pi

        synth_stft[:, f_idx] = mag_t * np.exp(1j * current_phase)

    # Invert STFT to time domain
    _, drone_audio = signal.istft(synth_stft, fs=sr, window="hann", nperseg=nperseg, noverlap=noverlap)

    # Trim to exact requested length
    drone_audio = drone_audio[:total_out_samples]

    # Smooth attack and release envelope (1.0s fade-in, 1.5s fade-out)
    fade_in_len = int(min(sr * 1.0, len(drone_audio) // 3))
    fade_out_len = int(min(sr * 1.5, len(drone_audio) // 3))

    if fade_in_len > 0:
        drone_audio[:fade_in_len] *= np.linspace(0.0, 1.0, fade_in_len) ** 2
    if fade_out_len > 0:
        drone_audio[-fade_out_len:] *= np.linspace(1.0, 0.0, fade_out_len) ** 2

    # Peak normalization
    peak = np.max(np.abs(drone_audio))
    if peak > 1e-6:
        drone_audio = (drone_audio / peak) * 0.88

    # Output directory
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Drones_Freeze"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"{in_file.stem}_SpectralFreeze_t{int(freeze_time_sec)}s_{int(output_duration_sec)}sDrone.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    int16_audio = (drone_audio * 32767.0).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_audio.tobytes())

    return {
        "status": "SUCCESS",
        "input_file": str(in_file),
        "freeze_time_sec": freeze_time_sec,
        "output_duration_sec": output_duration_sec,
        "fft_window_size": nperseg,
        "shimmer_depth": shimmer_depth,
        "phase_diffusion": phase_diffusion,
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = synthesize_spectral_freeze_drone(freeze_time_sec=2.0, output_duration_sec=4.0)
    print("Spectral Freeze Drone Output:", res)
