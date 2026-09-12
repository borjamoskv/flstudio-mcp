#!/usr/bin/env python3
"""
Antigravity Multitrack Stem Pack Synthesis Engine (v9.0 SOTA)
Synthesizes discrete broadcast WAV stems (44.1kHz, 16-bit Stereo PCM)
and an orchestration manifest into ~/Music/FL Studio Bounces/Stems/Dark_Cyber_Flamenco_Stems_16Bars/.
"""

import math
import struct
import wave
import json
import time
from pathlib import Path
from typing import Dict, Any, List

SAMPLE_RATE = 44100
BPM = 112.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4
SIXTEENTH_DUR = BEAT_DUR / 4.0
TOTAL_BARS = 16
TOTAL_DURATION = BAR_DUR * TOTAL_BARS
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)


def write_stereo_wav(file_path: Path, left_buf: List[float], right_buf: List[float], normalize: bool = True):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    n_samples = len(left_buf)
    
    if normalize:
        peak = 0.0001
        for i in range(n_samples):
            peak = max(peak, abs(left_buf[i]), abs(right_buf[i]))
        target = 0.944  # -0.5 dB
        gain = target / peak if peak > target else 1.0
    else:
        gain = 1.0

    raw = bytearray()
    for i in range(n_samples):
        l = math.tanh(left_buf[i] * gain)
        r = math.tanh(right_buf[i] * gain)
        raw.extend(struct.pack('<hh', int(l * 32767.0), int(r * 32767.0)))

    with wave.open(str(file_path), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw)


def render_multitrack_stems(output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    # Buffers
    kick_l, kick_r = [0.0] * TOTAL_SAMPLES, [0.0] * TOTAL_SAMPLES
    snare_l, snare_r = [0.0] * TOTAL_SAMPLES, [0.0] * TOTAL_SAMPLES
    bass_l, bass_r = [0.0] * TOTAL_SAMPLES, [0.0] * TOTAL_SAMPLES
    chords_l, chords_r = [0.0] * TOTAL_SAMPLES, [0.0] * TOTAL_SAMPLES
    master_l, master_r = [0.0] * TOTAL_SAMPLES, [0.0] * TOTAL_SAMPLES

    # 1. KICK STEM (Linndrum / 808 Pitch Drop)
    kick_samples = int(SAMPLE_RATE * 0.45)
    kick_single = []
    for i in range(kick_samples):
        t = i / SAMPLE_RATE
        freq = 48.0 + 112.0 * math.exp(-t * 32.0)
        amp = math.exp(-t * 9.0)
        click = 0.3 * math.sin(2.0 * math.pi * 900.0 * t) * math.exp(-t * 120.0)
        kick_single.append((math.sin(2.0 * math.pi * freq * t) + click) * amp)

    for bar in range(TOTAL_BARS):
        for beat in range(4):
            idx = int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE)
            for k in range(min(kick_samples, TOTAL_SAMPLES - idx)):
                kick_l[idx + k] += kick_single[k] * 0.85
                kick_r[idx + k] += kick_single[k] * 0.85

    # 2. SNARE / CLAP STEM (Beats 2 and 4)
    clap_samples = int(SAMPLE_RATE * 0.3)
    clap_single = []
    rng = 987654321
    def noise():
        nonlocal rng
        rng = (1103515245 * rng + 12345) & 0x7fffffff
        return (rng / 1073741824.0) - 1.0

    for i in range(clap_samples):
        t = i / SAMPLE_RATE
        clap_single.append((noise() * 0.8 + math.sin(2 * math.pi * 220.0 * t) * 0.3) * math.exp(-t * 16.0))

    for bar in range(TOTAL_BARS):
        for beat in [1, 3]:
            idx = int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE)
            for c in range(min(clap_samples, TOTAL_SAMPLES - idx)):
                snare_l[idx + c] += clap_single[c] * 0.85
                snare_r[idx + c] += clap_single[c] * 0.95

    # 3. ROLLING CYBER SUB-BASS STEM
    bass_roots = [
        36.71, 36.71, 36.71, 36.71,
        38.89, 38.89, 38.89, 38.89,
        46.25, 46.25, 48.99, 55.00,
        36.71, 36.71, 36.71, 36.71
    ]
    sixteenth_samples = int(SAMPLE_RATE * SIXTEENTH_DUR)
    for bar in range(TOTAL_BARS):
        base_f = bass_roots[bar]
        for step in range(16):
            idx = int((bar * BAR_DUR + step * SIXTEENTH_DUR) * SAMPLE_RATE)
            is_oct = (step % 2 == 1)
            freq = base_f * (2.0 if is_oct else 1.0)
            dur = sixteenth_samples * 0.75
            for n in range(min(int(dur), TOTAL_SAMPLES - idx)):
                t = n / SAMPLE_RATE
                env = math.exp(-t * 14.0)
                osc = (math.sin(2 * math.pi * freq * t) +
                       0.5 * math.sin(4 * math.pi * freq * t) +
                       0.25 * math.sin(6 * math.pi * freq * t))
                s = osc * env * 0.40
                bass_l[idx + n] += s
                bass_r[idx + n] += s

    # 4. FLAMENCO ARPEGGIATED CHORDS STEM
    chord_freqs = [
        [196.0, 233.08, 293.66, 349.23, 440.0],  # Gm9
        [174.61, 220.0, 261.63, 329.63, 392.0],  # Fmaj7
        [155.56, 196.0, 233.08, 293.66, 369.99], # Ebmaj7(#11)
        [146.83, 185.0, 220.0, 261.63, 311.13]   # D7(b9)
    ]
    for bar in range(TOTAL_BARS):
        notes = chord_freqs[bar // 4]
        bar_start = int(bar * BAR_DUR * SAMPLE_RATE)
        for n_i, freq in enumerate(notes):
            n_start = bar_start + int(n_i * (BAR_DUR / len(notes)) * SAMPLE_RATE)
            pan = (n_i / (len(notes) - 1)) * 0.8 - 0.4
            for s_i in range(min(int(SAMPLE_RATE * 1.8), TOTAL_SAMPLES - n_start)):
                t = s_i / SAMPLE_RATE
                env = (1.0 - math.exp(-t * 8.0)) * math.exp(-t * 2.2)
                synth = (math.sin(2 * math.pi * freq * t) * 0.5 +
                         math.sin(2 * math.pi * (freq * 1.003) * t) * 0.3 +
                         math.sin(2 * math.pi * (freq * 2.0) * t) * 0.15)
                val = synth * env * 0.35
                chords_l[n_start + s_i] += val * (0.5 - pan)
                chords_r[n_start + s_i] += val * (0.5 + pan)

    # 5. MASTER MIXDOWN (Sum with relative mix balance)
    for i in range(TOTAL_SAMPLES):
        master_l[i] = kick_l[i] * 0.70 + snare_l[i] * 0.65 + bass_l[i] * 0.65 + chords_l[i] * 0.55
        master_r[i] = kick_r[i] * 0.70 + snare_r[i] * 0.65 + bass_r[i] * 0.65 + chords_r[i] * 0.55

    # Export individual stems
    stems = [
        ("01_Kick_4onTheFloor.wav", kick_l, kick_r),
        ("02_Snare_Clap_Flamenco.wav", snare_l, snare_r),
        ("03_Rolling_Cyber_Bass.wav", bass_l, bass_r),
        ("04_Flamenco_Arp_Chords.wav", chords_l, chords_r),
        ("05_Master_Mix.wav", master_l, master_r),
    ]

    manifest_stems = []
    for fname, l_buf, r_buf in stems:
        path = output_dir / fname
        write_stereo_wav(path, l_buf, r_buf)
        manifest_stems.append({
            "name": fname,
            "path": str(path),
            "size_kb": round(path.stat().st_size / 1024.0, 1),
            "duration_sec": round(TOTAL_DURATION, 2)
        })

    # Write Manifest JSON
    manifest = {
        "pack_name": "Dark Cyber-Flamenco Multitrack Stems (16 Bars)",
        "version": "9.0-SOTA",
        "bpm": BPM,
        "key": "D Phrygian Dominant",
        "time_signature": "4/4",
        "bars": TOTAL_BARS,
        "sample_rate_hz": SAMPLE_RATE,
        "bit_depth": 16,
        "channels": 2,
        "total_stems": len(manifest_stems),
        "stems": manifest_stems,
        "elapsed_render_sec": round(time.time() - t_start, 2)
    }

    manifest_path = output_dir / "stems_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    out = Path.home() / "Music/FL Studio Bounces/Stems/Dark_Cyber_Flamenco_Stems_16Bars"
    res = render_multitrack_stems(out)
    print(f"✅ Exported Multitrack Stems ({res['total_stems']} stems) in {res['elapsed_render_sec']}s -> {out}")
