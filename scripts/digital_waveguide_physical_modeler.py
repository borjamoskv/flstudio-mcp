#!/usr/bin/env python3
"""
Digital Waveguide Physical Modeler (v17.0 Hyper-Dimensional Omni)
Implements Julius O. Smith III digital waveguide physical modeling synthesis
for acoustic non-linear wind and reed instruments (e.g. Flamenco Ney, Bamboo Flute).

Architecture:
- Fractional Delay Line with 1st-order Thiran All-Pass Interpolation
- Non-linear Bernoulli/cubic jet pressure exciter: f(x) = x - x^3 / 3
- One-pole reflective acoustic bore loss filter
- Breathing turbulence stochastic envelope and vibrato LFO
- Centralized WAV bounce to ~/Music/FL Studio Bounces/Physical_Modeling/
"""

import math
import wave
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("FLStudio-Waveguide")


def midi_to_freq(midi_pitch: float) -> float:
    """Converts MIDI pitch to frequency in Hz (A4 = 440 Hz)."""
    return 440.0 * (2.0 ** ((midi_pitch - 69.0) / 12.0))


class ThiranAllPassFractionalDelay:
    """1st-order Thiran All-Pass filter for exact fractional delay interpolation without amplitude loss."""
    def __init__(self, delta: float):
        # delta in [0, 1)
        self.delta = float(delta)
        # Coefficient for 1st order Thiran: a = (1 - D) / (1 + D)
        d = self.delta
        if d < 1e-4:
            self.a = 0.0
        else:
            self.a = (1.0 - d) / (1.0 + d)
        self.x1 = 0.0
        self.y1 = 0.0

    def process(self, x: float) -> float:
        y = self.a * x + self.x1 - self.a * self.y1
        self.x1 = x
        self.y1 = y
        return y


class DigitalWaveguideTube:
    """
    Physical model of an acoustic cylindrical bore with non-linear jet excitation.
    """
    def __init__(self, freq_hz: float, sample_rate: int = 44100, loss_decay: float = 0.985):
        self.fs = sample_rate
        self.freq = max(20.0, min(freq_hz, self.fs * 0.45))
        self.loss_factor = loss_decay

        # Nominal delay length: 2 * L = c / f => delay samples D = fs / f
        total_delay = self.fs / self.freq
        self.int_delay = int(math.floor(total_delay))
        self.frac_delay = total_delay - self.int_delay
        if self.int_delay < 2:
            self.int_delay = 2

        self.buffer = np.zeros(self.int_delay + 4, dtype=np.float64)
        self.write_ptr = 0
        self.interpolator = ThiranAllPassFractionalDelay(self.frac_delay)

        # 1-pole low-pass loss filter: y[n] = (1 - alpha)*x[n] + alpha*y[n-1]
        self.lp_alpha = 0.25
        self.lp_state = 0.0

    def process_sample(self, exciter_in: float) -> float:
        # Read from delay line with fractional interpolation
        read_ptr = (self.write_ptr - self.int_delay) % len(self.buffer)
        raw_delayed = self.buffer[read_ptr]
        delayed_sample = self.interpolator.process(raw_delayed)

        # Apply lowpass acoustic bore reflection loss
        self.lp_state = (1.0 - self.lp_alpha) * delayed_sample + self.lp_alpha * self.lp_state
        reflected = self.loss_factor * self.lp_state

        # Non-linear cubic jet scattering junction
        # delta_p = exciter_in - reflected
        delta_p = exciter_in - reflected
        # Non-linear function: f(p) = p - p^3 / 3 (clamped to [-1.2, 1.2])
        p_clamped = max(-1.2, min(1.2, delta_p))
        jet_flow = p_clamped - (p_clamped ** 3) / 3.0

        # Inject into bore
        next_sample = reflected + jet_flow * 0.5
        self.buffer[self.write_ptr] = next_sample
        self.write_ptr = (self.write_ptr + 1) % len(self.buffer)

        return next_sample


def synthesize_waveguide_flute(
    pitch_midi: int = 62,
    duration_sec: float = 2.5,
    breath_pressure: float = 0.85,
    vibrato_rate_hz: float = 5.2,
    vibrato_depth_cents: float = 25.0,
    output_wav: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesizes an acoustic instrument stem using digital waveguide physical modeling.
    - pitch_midi: MIDI pitch (e.g. 62 = D4, flamenco Ney root)
    - duration_sec: duration in seconds
    - breath_pressure: air jet excitation intensity (0.1 to 1.5)
    - vibrato_rate_hz: LFO rate in Hz
    - vibrato_depth_cents: pitch modulation depth in cents
    """
    sr = 44100
    total_samples = int(duration_sec * sr)
    base_freq = midi_to_freq(pitch_midi)

    # Instantiate waveguide
    tube = DigitalWaveguideTube(freq_hz=base_freq, sample_rate=sr, loss_decay=0.988)

    # Envelopes
    attack_samples = int(0.12 * sr)
    decay_samples = int(0.25 * sr)
    release_samples = int(0.35 * sr)
    sustain_samples = max(0, total_samples - attack_samples - decay_samples - release_samples)

    env = np.ones(total_samples, dtype=np.float64)
    # Attack: quadratic smooth ramp
    env[:attack_samples] = np.sin(np.linspace(0, np.pi / 2, attack_samples)) ** 2
    # Decay to sustain (0.85 of peak)
    if decay_samples > 0:
        env[attack_samples:attack_samples + decay_samples] = np.linspace(1.0, 0.85, decay_samples)
    # Sustain
    sustain_end = attack_samples + decay_samples + sustain_samples
    env[attack_samples + decay_samples:sustain_end] = 0.85
    # Release: cosine fade-out
    if release_samples > 0:
        env[sustain_end:] = 0.85 * np.cos(np.linspace(0, np.pi / 2, total_samples - sustain_end)) ** 2

    # LFO vibrato (delayed entry after attack)
    lfo_phase = 0.0
    lfo_inc = 2.0 * math.pi * vibrato_rate_hz / sr

    output_signal = np.zeros(total_samples, dtype=np.float64)

    # Audio synthesis loop
    for i in range(total_samples):
        # Breath turbulence noise
        noise = (random.random() * 2.0 - 1.0) * 0.12

        # Vibrato LFO envelope (fades in during sustain)
        vib_fade = min(1.0, max(0.0, (i - attack_samples) / (0.3 * sr)))
        lfo_val = math.sin(lfo_phase) * vib_fade
        lfo_phase += lfo_inc

        # Instantaneous breath pressure
        current_env = env[i] * breath_pressure
        exciter = (current_env + noise) * (1.0 + lfo_val * (vibrato_depth_cents / 1200.0))

        # Compute tube sample
        s = tube.process_sample(exciter)
        output_signal[i] = s

    # Remove DC offset and normalize
    output_signal = output_signal - np.mean(output_signal)
    peak = np.max(np.abs(output_signal))
    if peak > 1e-6:
        output_signal = (output_signal / peak) * 0.88

    # Apply soft clipping saturation
    output_signal = np.tanh(output_signal)

    # Centralized destination
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Physical_Modeling"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"Waveguide_Flute_MIDI{pitch_midi}_{base_freq:.1f}Hz.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    int16_audio = (output_signal * 32767.0).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_audio.tobytes())

    return {
        "status": "SUCCESS",
        "instrument": "Acoustic_Ney_Flute_Waveguide",
        "pitch_midi": pitch_midi,
        "base_freq_hz": round(base_freq, 2),
        "duration_sec": duration_sec,
        "breath_pressure": breath_pressure,
        "vibrato_rate_hz": vibrato_rate_hz,
        "total_samples": total_samples,
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = synthesize_waveguide_flute(pitch_midi=62, duration_sec=2.0)
    print("Waveguide synthesis output:", res)
