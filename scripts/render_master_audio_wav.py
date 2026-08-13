#!/usr/bin/env python3
"""
Synthesizes a full 8-bar audio WAV for Satin_Maceo_AIR_Flow_Master.wav
"""

import math
import struct
import wave
import os

def render_master_audio_wav(output_path, sample_rate=44100, bpm=118.0):
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4
    total_sec = bar_sec * 8  # ~16.27s
    total_samples = int(sample_rate * total_sec)
    
    samples = []
    
    # Penrose Chord frequencies (Abmaj7, Bb9, Cm9, Fm9)
    chords_freqs = [
        [207.65, 261.63, 311.13, 392.00],  # Abmaj7
        [233.08, 293.66, 349.23, 440.00],  # Bb9
        [261.63, 311.13, 392.00, 466.16],  # Cm9
        [174.61, 207.65, 261.63, 311.13],  # Fm9
    ]
    
    phase_chords = [0.0] * 4
    phase_kick = 0.0
    
    for i in range(total_samples):
        t = i / sample_rate
        bar_idx = int(t / bar_sec) % 8
        chord_idx = (bar_idx // 2) % 4
        current_chords = chords_freqs[chord_idx]
        
        # 1. Rhodes / Pad Chords (Satin / AIR)
        chord_sig = 0.0
        for idx, freq in enumerate(current_chords):
            phase_chords[idx] += 2.0 * math.pi * freq / sample_rate
            sine_val = math.sin(phase_chords[idx]) + 0.3 * math.sin(phase_chords[idx] * 2)
            chord_sig += sine_val * 0.15
            
        # 2. Maceo Plex DSP Kick (4-on-the-floor)
        t_beat = (t % beat_sec)
        beat_idx = int(t / beat_sec)
        kick_sig = 0.0
        # False drop silence on beats 26 & 27 (bar 7, 3rd & 4th beats)
        if not (beat_idx in [26, 27]):
            if t_beat < 0.2:
                kick_pitch = 49.0 + (3800.0 - 49.0) * math.exp(-t_beat / 0.011)
                phase_kick += 2.0 * math.pi * kick_pitch / sample_rate
                kick_env = math.exp(-t_beat / 0.15)
                raw_kick = math.sin(phase_kick) * kick_env
                kick_sig = math.tanh(raw_kick * 2.5) * 0.4
                
        mix = chord_sig + kick_sig
        pcm_val = int(max(-32767, min(32767, mix * 28000.0)))
        samples.append(pcm_val)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with wave.open(output_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        packed = bytearray()
        for sample in samples:
            packed.extend(struct.pack('<h', sample))
        wav_file.writeframes(packed)
        
    print(f"✅ Generated Master Audio WAV ({total_sec:.2f}s): {output_path}")

if __name__ == "__main__":
    out_wav = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/Satin_Maceo_AIR_Flow_Master.wav"
    render_master_audio_wav(out_wav)
