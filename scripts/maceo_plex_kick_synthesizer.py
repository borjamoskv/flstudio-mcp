#!/usr/bin/env python3
"""
C5-REAL Maceo Plex Kick Synthesizer & Audio DSP Engine (48 kHz / 24-bit SOTA)
Synthesizes phase-locked analog-modeled Maceo Plex kick drums using continuous
instantaneous phase integration, 4x oversampled soft saturation, and zero-crackle
raised-cosine boundary shaping (zero /tmp file I/O).
"""

import math
import sys
from pathlib import Path
from typing import List

import numpy as np

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from scripts.c5_dsp_core import (  # noqa: E402
    apply_zero_crackle_envelope,
    make_time_axis,
    oversampled_soft_saturate,
    synthesize_phase_locked_kick,
    write_pcm_wav,
)


def _synthesize_maceo_kick_array(
    sub_freq_hz: float = 50.0,
    pitch_start_hz: float = 3500.0,
    pitch_decay_ms: float = 12.0,
    body_decay_ms: float = 220.0,
    click_amount: float = 0.35,
    saturation_drive: float = 2.2,
    sample_rate: int = 48000,
) -> np.ndarray:
    """Synthesizes a phase-locked, 4x oversampled soft-saturated kick in float64."""
    duration_sec = max(0.08, (body_decay_ms / 1000.0) * 1.55)
    raw = synthesize_phase_locked_kick(
        sample_rate=sample_rate,
        duration_sec=duration_sec,
        root_hz=sub_freq_hz,
        punch_hz=max(sub_freq_hz * 2.4, 158.0),
        click_hz=pitch_start_hz,
        tau_click=max(0.002, pitch_decay_ms / 1000.0 * 0.35),
        tau_punch=max(0.015, pitch_decay_ms / 1000.0 * 2.5),
        tau_body=max(0.05, body_decay_ms / 1000.0),
        drive_db=20.0 * math.log10(max(1.0, saturation_drive)),
        pultec_sub_gain=0.18 + min(0.10, click_amount * 0.1),
    )
    driven = oversampled_soft_saturate(
        raw,
        drive_db=max(0.8, 12.0 * math.log10(max(1.0, saturation_drive))),
        threshold_db=-2.6,
        oversample=4,
    )
    return apply_zero_crackle_envelope(driven, sample_rate, attack_ms=0.35, release_ms=10.0)


def generate_maceo_plex_kick(
    output_path: str,
    sub_freq_hz: float = 50.0,
    pitch_start_hz: float = 3500.0,
    pitch_decay_ms: float = 12.0,
    body_decay_ms: float = 220.0,
    click_amount: float = 0.35,
    saturation_drive: float = 2.2,
    sample_rate: int = 48000,
) -> str:
    """
    Synthesizes a Maceo Plex signature kick drum WAV file (48 kHz / 24-bit):
    - Phase-locked continuous frequency integral anchored at 0 rad.
    - 4x oversampled hyperbolic tangent saturation (anti-aliased harmonics).
    - Zero-crackle raised-cosine tail fade-out.
    """
    kick_mono = _synthesize_maceo_kick_array(
        sub_freq_hz=sub_freq_hz,
        pitch_start_hz=pitch_start_hz,
        pitch_decay_ms=pitch_decay_ms,
        body_decay_ms=body_decay_ms,
        click_amount=click_amount,
        saturation_drive=saturation_drive,
        sample_rate=sample_rate,
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    peak = max(float(np.max(np.abs(kick_mono))), 1e-6)
    norm_kick = (kick_mono / peak) * 0.89
    write_pcm_wav(str(out), norm_kick, norm_kick, sample_rate=sample_rate, bit_depth=24, dither=False)
    print(f"[Maceo Plex Kick Synth] Generated 48kHz/24-bit Kick WAV -> {out}")
    return str(out)


def generate_maceo_plex_kick_pattern(
    output_path: str,
    fundamental_hz: float = 43.65,
    bpm: float = 124.0,
    length_bars: int = 4,
    sample_rate: int = 48000,
) -> str:
    """
    Generates a multi-bar Maceo Plex Melodic Techno kick drum + zero-crackle sub-rumble
    pattern in memory (zero /tmp disk I/O), saturated at 4x oversampling.
    """
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4.0
    total_sec = bar_sec * length_bars
    total_samples = int(total_sec * sample_rate)

    kick_mono = _synthesize_maceo_kick_array(
        sub_freq_hz=fundamental_hz,
        pitch_start_hz=3800.0,
        pitch_decay_ms=9.0,
        body_decay_ms=220.0,
        saturation_drive=2.6,
        sample_rate=sample_rate,
    )
    kick_len = len(kick_mono)

    rumble_samples = int(0.14 * sample_rate)
    t_r = make_time_axis(rumble_samples, sample_rate)
    raw_rumble = (
        np.sin(2.0 * math.pi * fundamental_hz * t_r)
        + 0.25 * np.sin(2.0 * math.pi * (fundamental_hz * 2.0) * t_r)
    ) * np.exp(-t_r * 16.5) * 0.24
    rumble_wave = apply_zero_crackle_envelope(raw_rumble, sample_rate, attack_ms=10.0, release_ms=18.0)

    out_buffer = np.zeros(total_samples, dtype=np.float64)

    for bar in range(length_bars):
        bar_start_s = bar * bar_sec
        is_turnaround = bar == length_bars - 1
        for beat in range(4):
            # Living Pre-Drop gap on beat 4 of final turnaround bar
            if is_turnaround and beat == 3:
                continue
            t_hit = bar_start_s + beat * beat_sec
            start_idx = int(t_hit * sample_rate)
            avail = min(kick_len, total_samples - start_idx)
            if avail > 0:
                accent = 1.0 if beat == 0 else (0.94 if beat == 2 else 0.90)
                out_buffer[start_idx : start_idx + avail] += kick_mono[:avail] * 0.88 * accent

            # Offbeat 16th industrial sub-rumble tuned to fundamental
            for step_sub, gain_mul in ((2, 1.0), (3, 0.72)):
                t_sub = t_hit + step_sub * (beat_sec / 4.0)
                sub_idx = int(t_sub * sample_rate)
                r_avail = min(rumble_samples, total_samples - sub_idx)
                if r_avail > 0:
                    out_buffer[sub_idx : sub_idx + r_avail] += rumble_wave[:r_avail] * gain_mul

    bus = oversampled_soft_saturate(out_buffer, drive_db=2.8, threshold_db=-2.4, oversample=4)
    bus = apply_zero_crackle_envelope(bus, sample_rate, attack_ms=0.5, release_ms=16.0)
    peak = max(float(np.max(np.abs(bus))), 1e-6)
    bus = (bus / peak) * 0.89

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_pcm_wav(str(out), bus, bus, sample_rate=sample_rate, bit_depth=24, dither=False)
    print(f"[Maceo Plex Kick Synth] Generated Pattern WAV -> {out}")
    return str(out)


def generate_maceo_plex_kick_pack() -> List[str]:
    """Generates a complete 3-sample Maceo Plex signature kick pack."""
    target_dir = WORKSPACE_DIR / "samples" / "maceo_plex"
    target_dir.mkdir(parents=True, exist_ok=True)

    return [
        generate_maceo_plex_kick(
            output_path=str(target_dir / "Maceo_Plex_Kick_Dark_Sub_A1.wav"),
            sub_freq_hz=55.0,
            pitch_start_hz=3800.0,
            pitch_decay_ms=10.0,
            body_decay_ms=230.0,
            saturation_drive=2.4,
        ),
        generate_maceo_plex_kick(
            output_path=str(target_dir / "Maceo_Plex_Kick_Punchy_Analog_F1.wav"),
            sub_freq_hz=43.65,
            pitch_start_hz=4200.0,
            pitch_decay_ms=8.5,
            body_decay_ms=200.0,
            saturation_drive=2.8,
        ),
        generate_maceo_plex_kick(
            output_path=str(target_dir / "Maceo_Plex_Kick_Electro_Hybrid_G1.wav"),
            sub_freq_hz=49.0,
            pitch_start_hz=3200.0,
            pitch_decay_ms=14.0,
            body_decay_ms=240.0,
            saturation_drive=2.0,
        ),
    ]


if __name__ == "__main__":
    generate_maceo_plex_kick_pack()
