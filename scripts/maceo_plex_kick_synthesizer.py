#!/usr/bin/env python3
"""
Antigravity Maceo Plex Kick Synthesizer & Audio DSP Engine
Synthesizes SOTA analog-modeled Maceo Plex kick drums (Sub fundamental, 14-bit pitch sweep, saturation harmonics).
"""

import math
import struct
import wave
import os
from typing import List, Tuple

def generate_maceo_plex_kick(
    output_path: str,
    sub_freq_hz: float = 50.0,
    pitch_start_hz: float = 3500.0,
    pitch_decay_ms: float = 12.0,
    body_decay_ms: float = 220.0,
    click_amount: float = 0.35,
    saturation_drive: float = 2.2,
    sample_rate: int = 44100
) -> str:
    """
    Synthesizes a Maceo Plex signature kick drum WAV file using pure mathematical DSP:
    - Pitch sweep: Exponential drop from pitch_start_hz down to sub_freq_hz.
    - Amplitude envelope: Fast attack, exponential decay (body_decay_ms).
    - Saturation: Hyperbolic tangent (tanh) soft-clipping for 2nd/3rd order analog harmonics.
    - Transient click: High-frequency transient burst.
    """
    total_samples = int(sample_rate * (body_decay_ms / 1000.0) * 1.5)
    samples = []

    tau_pitch = pitch_decay_ms / 1000.0
    tau_amp = body_decay_ms / 1000.0

    phase = 0.0

    for i in range(total_samples):
        t = i / sample_rate

        # 1. Exponential Pitch Sweep Envelope
        freq_t = sub_freq_hz + (pitch_start_hz - sub_freq_hz) * math.exp(-t / tau_pitch)
        
        # Advance phase
        phase += 2.0 * math.pi * freq_t / sample_rate
        
        # Fundamental sine wave
        sine_val = math.sin(phase)

        # 2. Amplitude Envelope
        amp_t = math.exp(-t / tau_amp)

        # 3. High-frequency transient click
        click_env = math.exp(-t / 0.002) if t < 0.005 else 0.0
        click_val = click_amount * click_env * (math.sin(2.0 * math.pi * 4000.0 * t))

        # Raw composite signal
        raw_sig = (sine_val * amp_t) + click_val

        # 4. Analog Saturation (Tanh soft clipping)
        driven_sig = math.tanh(raw_sig * saturation_drive) / math.tanh(saturation_drive)

        # Peak normalization & conversion to 16-bit PCM
        val_pcm = int(max(-32767, min(32767, driven_sig * 32000.0)))
        samples.append(val_pcm)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write WAV file
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit PCM
        wav_file.setframerate(sample_rate)
        packed_data = bytearray()
        for sample in samples:
            packed_data.extend(struct.pack('<h', sample))
        wav_file.writeframes(packed_data)

    print(f"[Maceo Plex Kick Synth] Generated Kick WAV -> {output_path}")
    return output_path


def generate_maceo_plex_kick_pack() -> List[str]:
    """Generates a complete 3-sample Maceo Plex signature kick pack."""
    target_dir = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/maceo_plex")
    os.makedirs(target_dir, exist_ok=True)

    pack = [
        generate_maceo_plex_kick(
            output_path=os.path.join(target_dir, "Maceo_Plex_Kick_Dark_Sub_A1.wav"),
            sub_freq_hz=55.0,  # A1
            pitch_start_hz=3800.0,
            pitch_decay_ms=10.0,
            body_decay_ms=230.0,
            saturation_drive=2.4
        ),
        generate_maceo_plex_kick(
            output_path=os.path.join(target_dir, "Maceo_Plex_Kick_Punchy_Analog_F1.wav"),
            sub_freq_hz=43.65,  # F1
            pitch_start_hz=4200.0,
            pitch_decay_ms=8.5,
            body_decay_ms=200.0,
            saturation_drive=2.8
        ),
        generate_maceo_plex_kick(
            output_path=os.path.join(target_dir, "Maceo_Plex_Kick_Electro_Hybrid_G1.wav"),
            sub_freq_hz=49.0,  # G1
            pitch_start_hz=3200.0,
            pitch_decay_ms=14.0,
            body_decay_ms=240.0,
            saturation_drive=2.0
        )
    ]
    return pack

if __name__ == "__main__":
    generate_maceo_plex_kick_pack()
