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


def generate_maceo_plex_kick_pattern(
    output_path: str,
    fundamental_hz: float = 43.65,
    bpm: float = 124.0,
    length_bars: int = 4,
    sample_rate: int = 44100
) -> str:
    """
    Generates a full multi-bar Maceo Plex Melodic Techno kick drum + sub-rumble pattern.
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    total_sec = bar_sec * length_bars
    total_samples = int(total_sec * sample_rate)

    # 1. Synthesize single single kick sample
    temp_kick_path = "/tmp/maceo_temp_kick.wav"
    generate_maceo_plex_kick(
        output_path=temp_kick_path,
        sub_freq_hz=fundamental_hz,
        pitch_start_hz=3800.0,
        pitch_decay_ms=9.0,
        body_decay_ms=220.0,
        saturation_drive=2.6,
        sample_rate=sample_rate
    )
    
    with wave.open(temp_kick_path, 'r') as wf:
        kick_frames = wf.readframes(wf.getnframes())
        kick_data = list(struct.unpack(f"<{len(kick_frames)//2}h", kick_frames))

    out_buffer = [0.0] * total_samples

    # Place 4-on-the-floor kicks + sub rumble on 16ths
    for bar in range(length_bars):
        bar_start_s = bar * bar_sec
        for beat in range(4):
            t_hit = bar_start_s + beat * beat_sec
            start_idx = int(t_hit * sample_rate)
            for j, val in enumerate(kick_data):
                if start_idx + j < total_samples:
                    out_buffer[start_idx + j] += (val / 32768.0) * 0.95

            # Sub-rumble offbeat on 16th (step 2 and 3 of beat)
            for step_sub in [2, 3]:
                t_sub = t_hit + step_sub * (beat_sec / 4.0)
                sub_idx = int(t_sub * sample_rate)
                # rumble is low-pass filtered delayed tail
                for j in range(int(0.12 * sample_rate)):
                    if sub_idx + j < total_samples:
                        t_r = j / sample_rate
                        sub_wave = math.sin(2.0 * math.pi * fundamental_hz * t_r) * math.exp(-t_r * 18.0) * 0.28
                        out_buffer[sub_idx + j] += sub_wave

    # Soft clip master pattern
    samples = []
    for s in out_buffer:
        driven = math.tanh(s * 1.5) / math.tanh(1.5)
        pcm = int(max(-32767, min(32767, driven * 32000.0)))
        samples.append(pcm)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        packed_data = bytearray()
        for sample in samples:
            packed_data.extend(struct.pack('<h', sample))
        wav_file.writeframes(packed_data)

    print(f"[Maceo Plex Kick Synth] Generated Pattern WAV -> {output_path}")
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

