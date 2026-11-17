#!/usr/bin/env python3
"""
headless_audio_dsp.py - C5-REAL 48 kHz Band-Limited Offline Synthesis Engine.
Renders warm, zero-crackle WAV audio buffers directly when FL Studio CoreMIDI ports are offline.
"""

from pathlib import Path
import numpy as np
from scipy import signal

try:
    from scripts.c5_dsp_core import (
        SAMPLE_RATE as DEFAULT_SR,
        apply_highpass_tpdf_dither,
        apply_zero_crackle_envelope,
        make_time_axis,
        oversampled_soft_saturate,
        polyblep_saw,
        write_pcm_wav,
    )
except ImportError:
    from c5_dsp_core import (
        SAMPLE_RATE as DEFAULT_SR,
        apply_highpass_tpdf_dither,
        apply_zero_crackle_envelope,
        make_time_axis,
        oversampled_soft_saturate,
        polyblep_saw,
        write_pcm_wav,
    )


def generate_microtonal_sine_wave(
    freq_hz: float,
    duration_s: float,
    sample_rate: int = DEFAULT_SR,
) -> bytes:
    """
    Synthesizes a warm, band-limited microtonal tone (fundamental + 2nd harmonic +
    filtered PolyBLEP body) with warm-bus low-shelf saturation and zero-crackle
    raised-cosine boundaries, returning little-endian 16-bit PCM bytes.
    """
    num_samples = max(16, int(sample_rate * duration_s))
    t = make_time_axis(num_samples, sample_rate)

    # Phase-coherent fundamental + warm octave + gentle PolyBLEP harmonic warmth
    fundamental = 0.62 * np.sin(2.0 * np.pi * freq_hz * t)
    octave = 0.18 * np.sin(4.0 * np.pi * freq_hz * t)
    saw_body = 0.14 * polyblep_saw(freq_hz, num_samples, sample_rate=sample_rate)

    raw = fundamental + octave + saw_body

    # Warm-bus analog tape LPF at 4.4 kHz + sub-warmth shelf around 240 Hz
    nyq = 0.5 * sample_rate
    sos_lpf = signal.butter(2, min(4400.0 / nyq, 0.95), btype="low", output="sos")
    warmed = signal.sosfilt(sos_lpf, raw)

    # Zero-crackle raised-cosine attack (8 ms) & release (16 ms)
    warmed = apply_zero_crackle_envelope(
        warmed, sample_rate=sample_rate, attack_ms=8.0, release_ms=16.0
    )
    warmed = oversampled_soft_saturate(warmed, drive_db=1.2, threshold_db=-2.4, asymmetry=0.015)

    # Lipshitz-Vanderkooy high-pass TPDF dither before 16-bit quantization
    dithered = apply_highpass_tpdf_dither(warmed * 0.88, bit_depth=16, seed=48000)
    pcm_i16 = np.clip(np.round(dithered * 32767.0), -32768, 32767).astype("<i2")
    return pcm_i16.tobytes()


def render_fallback_harmonic_loop(
    output_path: Path,
    note_freq: float = 130.81,
    sample_rate: int = DEFAULT_SR,
) -> Path:
    """Renders a 2.0s warm stereo 48 kHz fallback harmonic loop to `output_path`."""
    out = Path(output_path)
    pcm_bytes = generate_microtonal_sine_wave(note_freq, duration_s=2.0, sample_rate=sample_rate)
    mono = np.frombuffer(pcm_bytes, dtype="<i2").astype(np.float64) / 32768.0
    write_pcm_wav(out, mono, mono, sample_rate=sample_rate, bit_depth=16, dither=False)
    return out


if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent / "fallback_harmonic.wav"
    render_fallback_harmonic_loop(out_file)
    print(f"[OK] Headless Audio DSP 48kHz Rendered: {out_file}")
