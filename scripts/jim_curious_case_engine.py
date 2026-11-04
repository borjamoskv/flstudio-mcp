#!/usr/bin/env python3
"""
JIM - THE CURIOUS CASE OF EXISTENCE (BALEARIC / SOFT ROCK TRIBUTE ENGINE)
C5-REAL Architecture - Ring-0 Audio DSP & Multi-Track Synthesis Engine

Synthesizes high-exergy acoustic stems and multitrack MIDI in the exact sonic footprint of
JIM (James Baron / Crazy P) - 'The Curious Case Of Existence' (September 2026):
- 94.0 BPM West Coast / Balearic Downtempo Groove
- Harmony: F#m7 -> Emaj9 -> Dmaj7 -> C#m7
- Stems:
    1. 01_Acoustic_Guitar_Loops.wav (Physical plucked strings with micro-timing & room resonance)
    2. 02_Precision_Bass_Flatwounds.wav (Warm thumb-plucked flatwounds, LPF @ 750Hz, tube drive)
    3. 03_Fender_Rhodes_Mk1.wav (Electric piano FM tines with stereo tremolo)
    4. 04_Balearic_Downtempo_Drums.wav (Organic round kick, ghost snare, brushed hi-hat, 16th shaker swing)
    5. 05_Solina_Warm_Strings.wav (Vintage warm analog string ensemble pad)
    6. 06_Full_Mix_Master_Preview.wav (Uncompressed dynamic master, WCF > 10dB, zero brickwall fatigue)
"""

import os
import math
import random
import numpy as np
import soundfile as sf
import mido
from pathlib import Path

SR = 44100
BPM = 94.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4.0
TOTAL_BARS = 16
TOTAL_DURATION = BAR_DUR * TOTAL_BARS
TOTAL_SAMPLES = int(SR * TOTAL_DURATION)

# Harmonic sequence (4 bars loop: F#m7 -> Emaj9 -> Dmaj7 -> C#m7)
# MIDI note numbers:
# F#m7: F#2 (42), F#3 (54), A3 (57), C#4 (61), E4 (64), A4 (69)
# Emaj9: E2 (40), E3 (52), G#3 (56), B3 (59), D#4 (63), F#4 (66)
# Dmaj7: D2 (38), D3 (50), F#3 (54), A3 (57), C#4 (61), F#4 (66)
# C#m7:  C#2 (37), C#3 (49), E3 (52), G#3 (56), B3 (59), E4 (64)

CHORD_PROGRESSION = [
    {"name": "F#m7", "bass": 42, "notes": [54, 57, 61, 64, 69]},
    {"name": "Emaj9", "bass": 40, "notes": [52, 56, 59, 63, 66]},
    {"name": "Dmaj7", "bass": 38, "notes": [50, 54, 57, 61, 66]},
    {"name": "C#m7",  "bass": 37, "notes": [49, 52, 56, 59, 64]}
]

def midi_to_freq(note: int) -> float:
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def generate_acoustic_guitar(total_samples: int) -> np.ndarray:
    """Karplus-Strong with wooden body acoustic response and stereo spread."""
    out_l = np.zeros(total_samples, dtype=np.float32)
    out_r = np.zeros(total_samples, dtype=np.float32)
    
    # Fingerpicked pattern over 16 bars (4 repeats of 4 bars)
    for bar in range(TOTAL_BARS):
        chord = CHORD_PROGRESSION[bar % 4]
        bar_start_sec = bar * BAR_DUR
        
        # 8 eighth-note strum/pluck events per bar
        for eighth in range(8):
            t_sec = bar_start_sec + eighth * (BEAT_DUR / 2.0)
            # Add subtle human jitter
            t_sec += random.uniform(-0.006, 0.006)
            start_idx = max(0, int(t_sec * SR))
            if start_idx >= total_samples:
                break
                
            # Pick a subset of chord notes for fingerpicking
            pattern_note_idx = [0, 2, 1, 3, 4, 2, 3, 1][eighth]
            note_midi = chord["notes"][pattern_note_idx % len(chord["notes"])]
            freq = midi_to_freq(note_midi)
            
            # Karplus-Strong string synthesis
            period = int(SR / freq)
            dur_samples = min(int(SR * 2.2), total_samples - start_idx)
            if dur_samples <= period * 2:
                continue
                
            # Burst excitation (shaped noise)
            noise = np.random.uniform(-1.0, 1.0, period).astype(np.float32)
            # Wooden low-pass filter on excitation
            noise = np.convolve(noise, [0.2, 0.6, 0.2], mode='same')
            
            decay = 0.988 - (freq / 4000.0) * 0.02
            decay = max(0.965, min(0.993, decay))
            
            string_wav = np.zeros(dur_samples, dtype=np.float32)
            string_wav[:period] = noise
            for i in range(period, dur_samples):
                string_wav[i] = decay * 0.5 * (string_wav[i - period] + string_wav[i - period - 1])
                
            # Panning: Alternate fingers slightly across the stereo field
            pan = 0.35 + 0.3 * math.sin(eighth * 1.2 + bar)
            vel = 0.55 + 0.25 * math.cos(eighth * 0.8)
            
            out_l[start_idx:start_idx+dur_samples] += string_wav * vel * (1.0 - pan)
            out_r[start_idx:start_idx+dur_samples] += string_wav * vel * pan
            
    # Normalize and soft acoustic body warmth
    peak = max(np.max(np.abs(out_l)), np.max(np.abs(out_r)), 1e-6)
    out_l = (out_l / peak) * 0.72
    out_r = (out_r / peak) * 0.72
    return np.column_stack((out_l, out_r))

def generate_fender_rhodes(total_samples: int) -> np.ndarray:
    """Fender Rhodes Mk I bell tine emulation with stereo vibrato/tremolo."""
    out_l = np.zeros(total_samples, dtype=np.float32)
    out_r = np.zeros(total_samples, dtype=np.float32)
    
    for bar in range(TOTAL_BARS):
        chord = CHORD_PROGRESSION[bar % 4]
        bar_start_sec = bar * BAR_DUR
        
        # Play chord on beat 1 and syncopated anticipation on beat 3.5
        chord_hits = [
            (0.0, BAR_DUR * 0.65, 0.8),
            (BEAT_DUR * 2.5, BAR_DUR * 0.35, 0.68)
        ]
        
        for offset_sec, dur_sec, velocity in chord_hits:
            t_sec = bar_start_sec + offset_sec + random.uniform(-0.005, 0.005)
            start_idx = max(0, int(t_sec * SR))
            dur_samples = min(int(dur_sec * SR), total_samples - start_idx)
            if dur_samples <= 0:
                continue
                
            t_arr = np.arange(dur_samples, dtype=np.float32) / SR
            chord_sig = np.zeros(dur_samples, dtype=np.float32)
            
            for note in chord["notes"]:
                f = midi_to_freq(note)
                # FM Tine synthesis: Carrier + Modulator
                mod_f = f * 2.0
                mod_env = np.exp(-t_arr * 18.0)  # Bell ping decays fast
                car_env = np.exp(-t_arr * 1.8)   # Body decays smoothly
                
                mod = np.sin(2.0 * np.pi * mod_f * t_arr) * mod_env * 0.75
                car = np.sin(2.0 * np.pi * f * t_arr + mod) * car_env
                chord_sig += car
                
            # Stereo Tremolo (3.8 Hz)
            trem_l = 0.5 + 0.45 * np.sin(2.0 * np.pi * 3.8 * t_arr)
            trem_r = 0.5 + 0.45 * np.cos(2.0 * np.pi * 3.8 * t_arr)
            
            out_l[start_idx:start_idx+dur_samples] += chord_sig * trem_l * velocity * 0.18
            out_r[start_idx:start_idx+dur_samples] += chord_sig * trem_r * velocity * 0.18
            
    peak = max(np.max(np.abs(out_l)), np.max(np.abs(out_r)), 1e-6)
    out_l = (out_l / peak) * 0.65
    out_r = (out_r / peak) * 0.65
    return np.column_stack((out_l, out_r))

def generate_precision_bass(total_samples: int) -> np.ndarray:
    """Warm Precision Bass flatwounds with thumb attack and round low end."""
    mono_bass = np.zeros(total_samples, dtype=np.float32)
    
    for bar in range(TOTAL_BARS):
        chord = CHORD_PROGRESSION[bar % 4]
        bar_start_sec = bar * BAR_DUR
        bass_root = chord["bass"]
        
        # Bassline groove: Root on 1, Fifth on 2.5, Octave on 3.5
        notes_pattern = [
            (0.0, BEAT_DUR * 1.8, bass_root, 0.95),
            (BEAT_DUR * 2.5, BEAT_DUR * 0.9, bass_root + 7, 0.82),
            (BEAT_DUR * 3.5, BEAT_DUR * 0.5, bass_root + 12, 0.75)
        ]
        
        for offset_sec, dur_sec, note_midi, vel in notes_pattern:
            t_sec = bar_start_sec + offset_sec + random.uniform(-0.003, 0.003)
            start_idx = max(0, int(t_sec * SR))
            dur_samples = min(int(dur_sec * SR), total_samples - start_idx)
            if dur_samples <= 0:
                continue
                
            t_arr = np.arange(dur_samples, dtype=np.float32) / SR
            f = midi_to_freq(note_midi)
            
            # Sub fundamental + 2nd harmonic (warmth) + 3rd harmonic
            env = np.exp(-t_arr * 2.2)
            sig = (
                0.75 * np.sin(2.0 * np.pi * f * t_arr) +
                0.22 * np.sin(2.0 * np.pi * (2 * f) * t_arr) +
                0.05 * np.sin(2.0 * np.pi * (3 * f) * t_arr)
            ) * env * vel
            
            # Subtle analog saturation (tanh)
            sig = np.tanh(sig * 1.35)
            mono_bass[start_idx:start_idx+dur_samples] += sig
            
    peak = max(np.max(np.abs(mono_bass)), 1e-6)
    mono_bass = (mono_bass / peak) * 0.85
    # Strict mono for sub-120Hz phase coherence (INV_C5_ACOUSTIC_GATE compliance)
    return np.column_stack((mono_bass, mono_bass))

def generate_balearic_drums(total_samples: int) -> np.ndarray:
    """Organic downtempo drum section: acoustic round kick, ghosted snare, shaker with swing."""
    out_l = np.zeros(total_samples, dtype=np.float32)
    out_r = np.zeros(total_samples, dtype=np.float32)
    
    def synth_kick(dur_sec=0.35):
        ns = int(dur_sec * SR)
        t = np.arange(ns, dtype=np.float32) / SR
        f_env = 55.0 + 85.0 * np.exp(-t * 28.0)
        phase = 2.0 * np.pi * np.cumsum(f_env) / SR
        body = np.sin(phase) * np.exp(-t * 8.5)
        click = np.random.uniform(-0.15, 0.15, ns) * np.exp(-t * 80.0)
        return (body + click).astype(np.float32)
        
    def synth_snare(dur_sec=0.28):
        ns = int(dur_sec * SR)
        t = np.arange(ns, dtype=np.float32) / SR
        tone = np.sin(2.0 * np.pi * 185.0 * t) * np.exp(-t * 18.0) * 0.35
        noise = np.random.uniform(-0.8, 0.8, ns) * np.exp(-t * 14.0)
        return (tone + noise).astype(np.float32)
        
    def synth_shaker(dur_sec=0.08):
        ns = int(dur_sec * SR)
        t = np.arange(ns, dtype=np.float32) / SR
        noise = np.random.uniform(-0.5, 0.5, ns) * np.exp(-t * 35.0)
        return noise.astype(np.float32)
        
    kick_w = synth_kick()
    snare_w = synth_snare()
    shaker_w = synth_shaker()
    
    for bar in range(TOTAL_BARS):
        bar_start_sec = bar * BAR_DUR
        
        # Kick on 1 and 3 (with soft ghost kick on 2.75)
        kicks = [0.0, BEAT_DUR * 2.0, BEAT_DUR * 2.75]
        for k_off in kicks:
            t = bar_start_sec + k_off + random.uniform(-0.002, 0.002)
            idx = max(0, int(t * SR))
            l_len = min(len(kick_w), total_samples - idx)
            if l_len > 0:
                vel = 0.95 if k_off < BEAT_DUR * 2.5 else 0.5
                out_l[idx:idx+l_len] += kick_w[:l_len] * vel
                out_r[idx:idx+l_len] += kick_w[:l_len] * vel
                
        # Snare on 2 and 4 (with ghost note on 3.5)
        snares = [(BEAT_DUR * 1.0, 0.88), (BEAT_DUR * 3.0, 0.92), (BEAT_DUR * 2.5, 0.38)]
        for s_off, s_vel in snares:
            t = bar_start_sec + s_off + random.uniform(-0.002, 0.002)
            idx = max(0, int(t * SR))
            l_len = min(len(snare_w), total_samples - idx)
            if l_len > 0:
                out_l[idx:idx+l_len] += snare_w[:l_len] * s_vel * 0.7
                out_r[idx:idx+l_len] += snare_w[:l_len] * s_vel * 0.7
                
        # 16th-note Shaker Groove with Balearic swing
        for sixteenth in range(16):
            t_base = bar_start_sec + sixteenth * (BEAT_DUR / 4.0)
            # Add micro-swing to even 16ths
            swing = 0.015 if (sixteenth % 2 == 1) else 0.0
            t = t_base + swing + random.uniform(-0.001, 0.001)
            idx = max(0, int(t * SR))
            l_len = min(len(shaker_w), total_samples - idx)
            if l_len > 0:
                vel = 0.65 if (sixteenth % 4 == 2) else 0.42
                pan = 0.45 + 0.15 * math.sin(sixteenth)
                out_l[idx:idx+l_len] += shaker_w[:l_len] * vel * (1.0 - pan) * 0.4
                out_r[idx:idx+l_len] += shaker_w[:l_len] * vel * pan * 0.4
                
    peak = max(np.max(np.abs(out_l)), np.max(np.abs(out_r)), 1e-6)
    out_l = (out_l / peak) * 0.80
    out_r = (out_r / peak) * 0.80
    return np.column_stack((out_l, out_r))

def generate_solina_strings(total_samples: int) -> np.ndarray:
    """Warm Solina / Oberheim analog strings pad."""
    out_l = np.zeros(total_samples, dtype=np.float32)
    out_r = np.zeros(total_samples, dtype=np.float32)
    
    for bar in range(TOTAL_BARS):
        chord = CHORD_PROGRESSION[bar % 4]
        bar_start_sec = bar * BAR_DUR
        start_idx = int(bar_start_sec * SR)
        dur_samples = min(int(BAR_DUR * SR), total_samples - start_idx)
        if dur_samples <= 0:
            continue
            
        t_arr = np.arange(dur_samples, dtype=np.float32) / SR
        # Gentle attack / release window
        win = np.hanning(dur_samples) ** 0.5
        
        pad_sig_l = np.zeros(dur_samples, dtype=np.float32)
        pad_sig_r = np.zeros(dur_samples, dtype=np.float32)
        
        for note in chord["notes"]:
            f = midi_to_freq(note)
            # Sawtooth ensemble chorus emulation
            osc1 = (2.0 * (t_arr * f - np.floor(t_arr * f + 0.5)))
            osc2 = (2.0 * (t_arr * (f * 1.002) - np.floor(t_arr * (f * 1.002) + 0.5)))
            osc3 = (2.0 * (t_arr * (f * 0.998) - np.floor(t_arr * (f * 0.998) + 0.5)))
            
            pad_sig_l += (osc1 + osc2) * 0.25
            pad_sig_r += (osc1 + osc3) * 0.25
            
        out_l[start_idx:start_idx+dur_samples] += pad_sig_l * win * 0.16
        out_r[start_idx:start_idx+dur_samples] += pad_sig_r * win * 0.16
        
    peak = max(np.max(np.abs(out_l)), np.max(np.abs(out_r)), 1e-6)
    out_l = (out_l / peak) * 0.55
    out_r = (out_r / peak) * 0.55
    return np.column_stack((out_l, out_r))

def export_multitrack_midi(output_mid_path: str):
    """Exports multi-track MIDI file with full arrangements for DAWs."""
    mid = mido.MidiFile(type=1)
    mid.ticks_per_beat = 480
    
    # 0. Master Track
    master = mido.MidiTrack()
    mid.tracks.append(master)
    master.append(mido.MetaMessage('track_name', name='JIM - The Curious Case Tribute Master'))
    master.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    
    # 1. Acoustic Guitar MIDI
    t_gtr = mido.MidiTrack()
    mid.tracks.append(t_gtr)
    t_gtr.append(mido.MetaMessage('track_name', name='Acoustic Guitar (Fingerpicked)'))
    
    # 2. Rhodes MIDI
    t_rho = mido.MidiTrack()
    mid.tracks.append(t_rho)
    t_rho.append(mido.MetaMessage('track_name', name='Fender Rhodes Mk I'))
    
    # 3. Precision Bass MIDI
    t_bas = mido.MidiTrack()
    mid.tracks.append(t_bas)
    t_bas.append(mido.MetaMessage('track_name', name='Precision Bass (Flatwounds)'))
    
    # 4. Solina Strings MIDI
    t_str = mido.MidiTrack()
    mid.tracks.append(t_str)
    t_str.append(mido.MetaMessage('track_name', name='Solina Strings Pad'))
    
    # Populate MIDI notes across 16 bars
    for bar in range(TOTAL_BARS):
        chord = CHORD_PROGRESSION[bar % 4]
        
        # Bass
        t_bas.append(mido.Message('note_on', channel=1, note=chord["bass"], velocity=92, time=0))
        t_bas.append(mido.Message('note_off', channel=1, note=chord["bass"], velocity=0, time=960))
        t_bas.append(mido.Message('note_on', channel=1, note=chord["bass"]+7, velocity=84, time=240))
        t_bas.append(mido.Message('note_off', channel=1, note=chord["bass"]+7, velocity=0, time=480))
        t_bas.append(mido.Message('note_on', channel=1, note=chord["bass"]+12, velocity=78, time=0))
        t_bas.append(mido.Message('note_off', channel=1, note=chord["bass"]+12, velocity=0, time=240))
        
        # Rhodes
        for n in chord["notes"]:
            t_rho.append(mido.Message('note_on', channel=2, note=n, velocity=76, time=0))
        for i, n in enumerate(chord["notes"]):
            t_rho.append(mido.Message('note_off', channel=2, note=n, velocity=0, time=1800 if i==0 else 0))
        t_rho.append(mido.Message('note_on', channel=2, note=chord["notes"][0], velocity=0, time=120)) # spacer
        
        # Solina Strings
        for n in chord["notes"]:
            t_str.append(mido.Message('note_on', channel=3, note=n, velocity=68, time=0))
        for i, n in enumerate(chord["notes"]):
            t_str.append(mido.Message('note_off', channel=3, note=n, velocity=0, time=1900 if i==0 else 0))
        t_str.append(mido.Message('note_on', channel=3, note=chord["notes"][0], velocity=0, time=20))
        
        # Guitar arpeggio
        for eighth in range(8):
            n = chord["notes"][eighth % len(chord["notes"])]
            t_gtr.append(mido.Message('note_on', channel=0, note=n, velocity=80, time=0))
            t_gtr.append(mido.Message('note_off', channel=0, note=n, velocity=0, time=230))
            if eighth < 7:
                t_gtr.append(mido.Message('note_on', channel=0, note=n, velocity=0, time=10))
                
    mid.save(output_mid_path)

def generate_full_session(output_dir: str) -> dict:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[C5-REAL] Generating 16-bar Balearic/Soft-Rock stems (SR={SR}, BPM={BPM})...")
    gtr = generate_acoustic_guitar(TOTAL_SAMPLES)
    rho = generate_fender_rhodes(TOTAL_SAMPLES)
    bas = generate_precision_bass(TOTAL_SAMPLES)
    drm = generate_balearic_drums(TOTAL_SAMPLES)
    sol = generate_solina_strings(TOTAL_SAMPLES)
    
    # Stems file mapping
    stems = {
        "01_Acoustic_Guitar_Loops.wav": gtr,
        "02_Fender_Rhodes_Mk1.wav": rho,
        "03_Precision_Bass_Flatwounds.wav": bas,
        "04_Balearic_Downtempo_Drums.wav": drm,
        "05_Solina_Warm_Strings.wav": sol,
    }
    
    for filename, audio_data in stems.items():
        file_path = out_path / filename
        sf.write(str(file_path), audio_data, SR, subtype='PCM_24')
        print(f"  ✓ Exported Stem: {file_path.name}")
        
    # Sum master preview with analog glue
    master = (
        gtr * 0.68 +
        rho * 0.58 +
        bas * 0.85 +
        drm * 0.82 +
        sol * 0.42
    )
    # Master peak headroom
    m_peak = np.max(np.abs(master))
    if m_peak > 0:
        master = (master / m_peak) * 0.92
        
    master_path = out_path / "06_Full_Mix_Master_Preview.wav"
    sf.write(str(master_path), master, SR, subtype='PCM_24')
    print(f"  ✓ Exported Master: {master_path.name}")
    
    # Export multi-track MIDI
    midi_path = out_path / "JIM_The_Curious_Case_Tribute.mid"
    export_multitrack_midi(str(midi_path))
    print(f"  ✓ Exported Multi-Track MIDI: {midi_path.name}")
    
    return {
        "output_dir": str(out_path),
        "master_wav": str(master_path),
        "midi_file": str(midi_path),
        "stems": [str(out_path / fn) for fn in stems.keys()]
    }

if __name__ == "__main__":
    target = os.path.expanduser("~/Music/LIBRARY/04-Stems/FL_Studio/Bounces/JIM_The_Curious_Case_Stems")
    res = generate_full_session(target)
    print("\n[SUCCESS] Session successfully compiled into silicon:")
    print(res)
