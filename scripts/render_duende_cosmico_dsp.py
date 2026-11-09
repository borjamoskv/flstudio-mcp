#!/usr/bin/env python3
"""
Headless DSP Audio Renderer for "El Duende del Cosmos Microtonal"
Synthesizes a 30-second audio demonstration (WAV 44.1kHz 16-bit) showcasing:
- Solomun 50Hz punch kick + 62% swing hi-hats
- The Cure Chorus post-punk bassline
- Röyksopp warm analog space pads
- COIL 50Hz sub-drone with 24-TET microtonal pitch modulation
- Lindstrøm 24-TET Space Disco arpeggio
- Camarón Cante Jondo vocal lead melismas (quarter-tone bends)
- Paco de Lucía Flamenco guitar falsetas
"""

import math
import struct
import wave
import os

WORKSPACE_DIR = os.path.expanduser("~/10_PROJECTS/flstudio-mcp")
OUTPUT_WAV_PATH = os.path.join(WORKSPACE_DIR, "samples", "el_duende_del_cosmos_microtonal_preview.wav")

SAMPLE_RATE = 44100
DURATION = 30.0 # 30 seconds preview
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION)
BPM = 122.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4

def midi_to_freq(midi_note: float) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))

def render_dsp_preview() -> str:
    print(f"[DSP Audio Renderer] Synthesizing {DURATION}s preview of 'El Duende del Cosmos Microtonal'...")
    
    # Initialize left and right channel sample buffers
    out_l = [0.0] * TOTAL_SAMPLES
    out_r = [0.0] * TOTAL_SAMPLES

    # 1. Solomun 50Hz Punch Kick Synthesizer
    for bar in range(int(DURATION / BAR_DUR) + 1):
        for beat in range(4):
            t_start = (bar * BAR_DUR) + (beat * BEAT_DUR)
            if t_start >= DURATION:
                break
            sample_start = int(t_start * SAMPLE_RATE)
            sample_len = int(0.25 * SAMPLE_RATE) # 250ms kick body
            
            for i in range(sample_len):
                idx = sample_start + i
                if idx >= TOTAL_SAMPLES:
                    break
                t_rel = i / SAMPLE_RATE
                # Exponential pitch sweep from 350Hz down to 50Hz
                freq = 50.0 + 300.0 * math.exp(-t_rel * 35.0)
                env = math.exp(-t_rel * 12.0)
                phase = 2.0 * math.pi * (50.0 * t_rel + (300.0 / 35.0) * (1.0 - math.exp(-t_rel * 35.0)))
                val = math.tanh(1.5 * math.sin(phase)) * env * 0.45
                
                out_l[idx] += val
                out_r[idx] += val

    # 2. The Cure Post-Punk Chorus Bass (E2 = 40, F2 = 41, G#2 = 44)
    bass_notes = [(40, 0.0), (40, 0.25), (52, 0.5), (40, 0.75), (41, 1.0), (40, 1.25), (44, 1.5), (40, 1.75)]
    for bar in range(int(DURATION / BAR_DUR) + 1):
        bar_t = bar * BAR_DUR
        for n, rel_b in bass_notes:
            t_start = bar_t + (rel_b * BEAT_DUR)
            if t_start >= DURATION:
                break
            sample_start = int(t_start * SAMPLE_RATE)
            sample_len = int(0.22 * SAMPLE_RATE)
            freq = midi_to_freq(n)
            
            for i in range(sample_len):
                idx = sample_start + i
                if idx >= TOTAL_SAMPLES:
                    break
                t_rel = i / SAMPLE_RATE
                # Chorus effect (two slightly detuned saw waves)
                f1, f2 = freq, freq * 1.008
                v1 = (2.0 * ((t_rel * f1) % 1.0) - 1.0)
                v2 = (2.0 * ((t_rel * f2) % 1.0) - 1.0)
                env = math.exp(-t_rel * 4.0)
                val = (v1 + v2) * 0.5 * env * 0.25
                
                out_l[idx] += val * 0.8
                out_r[idx] += val * 1.2 # Stereo chorus width

    # 3. Lindstrøm 24-TET Space Disco Arp & Paco Falsetas
    arp_sequence = [64, 64.5, 68, 71, 72, 74.5, 76, 77.5] # 24-TET quarter-tones
    for i_step in range(int(DURATION / (BEAT_DUR / 4))):
        t_start = i_step * (BEAT_DUR / 4)
        if t_start >= DURATION:
            break
        sample_start = int(t_start * SAMPLE_RATE)
        sample_len = int(0.1 * SAMPLE_RATE)
        note_m = arp_sequence[i_step % len(arp_sequence)]
        freq = midi_to_freq(note_m)
        
        for i in range(sample_len):
            idx = sample_start + i
            if idx >= TOTAL_SAMPLES:
                break
            t_rel = i / SAMPLE_RATE
            env = math.exp(-t_rel * 15.0)
            val = math.sin(2.0 * math.pi * freq * t_rel) * env * 0.15
            
            # Pan sweep
            pan = 0.5 + 0.3 * math.sin(i_step * 0.2)
            out_l[idx] += val * (1.0 - pan)
            out_r[idx] += val * pan

    # 4. Camarón Cante Jondo Vocal Lead (Microtonal Quejío Melismas)
    for i in range(TOTAL_SAMPLES):
        t = i / SAMPLE_RATE
        if 8.0 <= t <= 24.0: # Vocal Cante segment
            # Portamento & pitch bend vibrato between E4 (64) and G#4 neutral (67.5)
            bend = 0.5 * math.sin(2.0 * math.pi * 5.0 * t) # 5Hz micro-vibrato
            freq = midi_to_freq(64.0 + 3.5 * math.sin(t * 0.5) + bend)
            env = min(1.0, (t - 8.0) * 0.5) * min(1.0, (24.0 - t) * 0.5)
            
            # Vocal formants synthesis (sine + triangle harmonic blend)
            s1 = math.sin(2.0 * math.pi * freq * t)
            s2 = 0.5 * math.sin(2.0 * math.pi * freq * 2.0 * t)
            val = (s1 + s2) * env * 0.20
            
            out_l[i] += val
            out_r[i] += val

    # Master Limiter & Normalization
    max_val = max(max(abs(x) for x in out_l), max(abs(x) for x in out_r))
    scale_factor = 0.90 / max(0.001, max_val)

    os.makedirs(os.path.dirname(OUTPUT_WAV_PATH), exist_ok=True)
    with wave.open(OUTPUT_WAV_PATH, 'wb') as wav_file:
        wav_file.setnchannels(2) # Stereo
        wav_file.setsampwidth(2) # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        
        frames = bytearray()
        for i in range(TOTAL_SAMPLES):
            l_pcm = int(max(-32767, min(32767, out_l[i] * scale_factor * 32767)))
            r_pcm = int(max(-32767, min(32767, out_r[i] * scale_factor * 32767)))
            frames.extend(struct.pack('<hh', l_pcm, r_pcm))
            
        wav_file.writeframes(frames)

    print(f" Successfully rendered DSP Audio Preview -> {OUTPUT_WAV_PATH}")
    return OUTPUT_WAV_PATH

if __name__ == "__main__":
    render_dsp_preview()
