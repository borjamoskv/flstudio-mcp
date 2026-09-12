#!/usr/bin/env python3
"""
Dark Cyber-Flamenco Headless Audio Synthesizer (v8.0 SOTA)
Synthesizes a full 16-bar audio preview (WAV, 44.1kHz, 16-bit Stereo PCM)
using pure Python standard library DSP.
Combines Linndrum/808 kick transients, rolling 16th sub-bass, snare claps,
and D Phrygian Dominant flamenco harmony.
"""

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44100
BPM = 112.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4
SIXTEENTH_DUR = BEAT_DUR / 4.0
TOTAL_BARS = 16
TOTAL_DURATION = BAR_DUR * TOTAL_BARS
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)


def render_dark_cyber_flamenco_wav(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    left_channel = [0.0] * TOTAL_SAMPLES
    right_channel = [0.0] * TOTAL_SAMPLES

    # 1. LINNDRUM / 808 HYBRID KICK (4-on-the-floor)
    kick_samples = int(SAMPLE_RATE * 0.45)
    kick_buf = []
    for i in range(kick_samples):
        t = i / SAMPLE_RATE
        # Exponential pitch envelope from 160Hz down to 48Hz
        freq = 48.0 + 112.0 * math.exp(-t * 32.0)
        phase = 2.0 * math.pi * freq * t
        # Body sine + slight click transient
        amp = math.exp(-t * 9.0)
        click = 0.3 * math.sin(2.0 * math.pi * 900.0 * t) * math.exp(-t * 120.0)
        sample = (math.sin(phase) + click) * amp
        kick_buf.append(sample)

    for bar in range(TOTAL_BARS):
        for beat in range(4):
            start_idx = int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE)
            for k in range(min(kick_samples, TOTAL_SAMPLES - start_idx)):
                left_channel[start_idx + k] += kick_buf[k] * 0.70
                right_channel[start_idx + k] += kick_buf[k] * 0.70

    # 2. CYBERPUNK ROLLING 16TH BASSLINE (D Phrygian Dominant)
    # Roots: Bar 0-3: D1 (36.7Hz), Bar 4-7: Eb1 (38.9Hz), Bar 8-11: F#1 (46.2Hz), Bar 12-15: D1 (36.7Hz)
    bass_roots = [
        36.71, 36.71, 36.71, 36.71,  # D1
        38.89, 38.89, 38.89, 38.89,  # Eb1
        46.25, 46.25, 48.99, 55.00,  # F#1, F#1, G1, A1
        36.71, 36.71, 36.71, 36.71   # D1 Picardy resolution
    ]

    sixteenth_samples = int(SAMPLE_RATE * SIXTEENTH_DUR)
    for bar in range(TOTAL_BARS):
        base_f = bass_roots[bar]
        for step in range(16):
            start_idx = int((bar * BAR_DUR + step * SIXTEENTH_DUR) * SAMPLE_RATE)
            is_octave = (step % 2 == 1)
            freq = base_f * (2.0 if is_octave else 1.0)
            note_dur = sixteenth_samples * 0.75

            for n in range(min(int(note_dur), TOTAL_SAMPLES - start_idx)):
                t = n / SAMPLE_RATE
                env = math.exp(-t * 14.0)
                # Sawtooth approximation with first 4 harmonics
                osc = (math.sin(2 * math.pi * freq * t) +
                       0.5 * math.sin(4 * math.pi * freq * t) +
                       0.25 * math.sin(6 * math.pi * freq * t))
                s = osc * env * 0.28
                left_channel[start_idx + n] += s
                right_channel[start_idx + n] += s

    # 3. SYNTHWAVE CLAP / SNARE (Beats 2 and 4)
    clap_samples = int(SAMPLE_RATE * 0.3)
    clap_buf = []
    # Seeded pseudo-random noise burst
    rng_state = 123456789
    def quick_rand():
        nonlocal rng_state
        rng_state = (1103515245 * rng_state + 12345) & 0x7fffffff
        return (rng_state / 1073741824.0) - 1.0

    for i in range(clap_samples):
        t = i / SAMPLE_RATE
        noise = quick_rand()
        body = math.sin(2 * math.pi * 210.0 * t) * 0.3
        env = math.exp(-t * 16.0)
        clap_buf.append((noise + body) * env * 0.35)

    for bar in range(TOTAL_BARS):
        for beat in [1, 3]:  # Beats 2 & 4 (0-indexed 1 and 3)
            start_idx = int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE)
            for c in range(min(clap_samples, TOTAL_SAMPLES - start_idx)):
                left_channel[start_idx + c] += clap_buf[c] * 0.85
                right_channel[start_idx + c] += clap_buf[c] * 0.95

    # 4. FLAMENCO ARPEGGIATED CHORDS (Pad / Brass Layer)
    # Chords: Gm9 (bar 0-3), Fmaj7 (4-7), Ebmaj7 (8-11), D7b9 (12-15)
    chord_freqs = [
        [196.0, 233.08, 293.66, 349.23, 440.0],  # G, Bb, D, F, A (Gm9)
        [174.61, 220.0, 261.63, 329.63, 392.0],  # F, A, C, E, G (Fmaj7)
        [155.56, 196.0, 233.08, 293.66, 369.99], # Eb, G, Bb, D, F# (Ebmaj7#11)
        [146.83, 185.0, 220.0, 261.63, 311.13]   # D, F#, A, C, Eb (D7b9)
    ]

    for bar in range(TOTAL_BARS):
        c_idx = bar // 4
        notes = chord_freqs[c_idx]
        bar_start = int((bar * BAR_DUR) * SAMPLE_RATE)
        bar_samples = int(BAR_DUR * SAMPLE_RATE)

        # Arpeggiate notes across the bar
        for n_i, freq in enumerate(notes):
            n_start = bar_start + int(n_i * (BAR_DUR / len(notes)) * SAMPLE_RATE)
            pan = (n_i / (len(notes) - 1)) * 0.8 - 0.4  # -0.4 to +0.4
            pan_l = 0.5 - pan
            pan_r = 0.5 + pan

            for s_i in range(min(int(SAMPLE_RATE * 1.8), TOTAL_SAMPLES - n_start)):
                t = s_i / SAMPLE_RATE
                env = (1.0 - math.exp(-t * 8.0)) * math.exp(-t * 2.2)
                # Lush warm saw/tri synth
                synth = (math.sin(2 * math.pi * freq * t) * 0.5 +
                         math.sin(2 * math.pi * (freq * 1.003) * t) * 0.3 +  # Detuned chorus
                         math.sin(2 * math.pi * (freq * 2.0) * t) * 0.15)
                val = synth * env * 0.18
                left_channel[n_start + s_i] += val * pan_l
                right_channel[n_start + s_i] += val * pan_r

    # 5. SOFT CLIPPING & MASTERING NORMALIZATION
    max_peak = 0.0001
    for i in range(TOTAL_SAMPLES):
        max_peak = max(max_peak, abs(left_channel[i]), abs(right_channel[i]))

    # Target -0.5 dB True Peak
    target_peak = 0.944
    gain = target_peak / max_peak if max_peak > target_peak else 1.0

    raw_frames = bytearray()
    for i in range(TOTAL_SAMPLES):
        # Apply tanh saturation soft clipping
        l = math.tanh(left_channel[i] * gain)
        r = math.tanh(right_channel[i] * gain)
        int_l = int(max(-32768, min(32767, l * 32767.0)))
        int_r = int(max(-32768, min(32767, r * 32767.0)))
        raw_frames.extend(struct.pack('<hh', int_l, int_r))

    with wave.open(str(output_path), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw_frames)

    return output_path


if __name__ == "__main__":
    bounces_dir = Path.home() / "Music/FL Studio Bounces"
    out_wav = bounces_dir / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    render_dark_cyber_flamenco_wav(out_wav)
    print(f"✅ Rendered Headless Audio Preview: {out_wav} ({out_wav.stat().st_size / 1024:.1f} KB)")
