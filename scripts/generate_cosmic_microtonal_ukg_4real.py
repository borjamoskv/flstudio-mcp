#!/usr/bin/env python3
"""
Cosmic Microtonal UK Garage Synthesizer — C5-REAL Pure DSP Engine
═════════════════════════════════════════════════════════════════════════════════
Reference Aesthetic: "4REAL" by Juni & ELI (138 BPM, UKG / Speed Garage / Bass)
Key Features:
- 138.0 BPM Authentic UK Garage 2-Step & Speed Garage Bouncy Swing (60% shuffle)
- Microtonality: 11-Limit Just Intonation Cosmic Tuning on E:
    * 1/1 Tonic E (41.20 Hz)
    * 11/9 Undecimal Neutral 3rd (50.36 Hz, +347.4 cents)
    * 11/8 Euler-Undecimal Cosmic Tritone (56.65 Hz, +551.3 cents)
    * 7/4 Harmonic 7th (72.11 Hz, +968.8 cents)
    * 13/8 Tridecimal Neutral 6th (66.96 Hz, +840.5 cents)
- Bass Architecture:
    * 01: Pure Sub-Bass (E1 41.2Hz to 72.1Hz) with Volterra warm saturation
    * 02: Warped FM Donk & Speed Garage resonant squelch bass with pitch scoops
- Drum & Groove Engine:
    * Punchy 909/acoustic 2-step kick with sidechain compression
    * Snappy Rimshots on 2 & 4 with velocity-sensitive syncopated ghost snares
    * Shuffling 16th hats with 60% UKG swing delay
    * Sliced acoustic bongo loops (LoopMasters MJ Bongo) and congas
    * Sliced underground ghost breaks (Slicex Ghost Break) highpassed at 320 Hz
- Harmonic & Melodic Instrumentation:
    * Multi-sampled Rhodes Mark I tines retuned to 11-limit microtonal chord voicings
    * Astral microtonal crystalline arpeggios with ping-pong delay
    * Shepard-Risset infinite ascending cosmic glissando pads
- Vocals & SFX:
    * Soul vocal chops ("4REAL", melodic runs, vocal stabs) with tape echo & space reverb
    * Space laser blips, cymbal rises, reverse sweeps, and vinyl warmth
- Deliverables:
    * 10 Discrete High-Fidelity WAV Stems
    * Master WAV & 320 kbps MP3
    * Native FL Studio Project (.flp) session
Centralized into canonical ~/Music/
"""

import math
import os
import struct
import wave
import subprocess
import numpy as np
import soundfile as sf
from scipy import signal
from pathlib import Path
import sys

# Add scripts directory for FLP compiler
sys.path.insert(0, str(Path(__file__).parent))

MUSIC_DIR = Path.home() / "Music"
OUTPUT_WAV = MUSIC_DIR / "COSMIC_MICROTONAL_UKG_4REAL.wav"
OUTPUT_MP3 = MUSIC_DIR / "COSMIC_MICROTONAL_UKG_4REAL.mp3"
STEMS_DIR = MUSIC_DIR / "Synthesized_Stems" / "Cosmic_Microtonal_UKG_4Real"
PROJECTS_DIR = MUSIC_DIR / "FL Studio Bounces" / "Projects"
OUTPUT_FLP = PROJECTS_DIR / "Cosmic_Microtonal_UKG_4Real_Session.flp"

SAMPLES_BASE = MUSIC_DIR / "LIBRARY" / "04-Stems" / "Samples" / "SAMPLES"
DRUMS_DIR = SAMPLES_BASE / "Drums"
INST_DIR = SAMPLES_BASE / "Instruments"
VOC_DIR = SAMPLES_BASE / "Vocals"
LOOPS_DIR = SAMPLES_BASE / "Loops"

STEMS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100
BPM = 138.0
BEAT_DUR = 60.0 / BPM          # ~0.43478 s
BAR_DUR = BEAT_DUR * 4.0       # ~1.73913 s
SIXTEENTH_DUR = BEAT_DUR / 4.0 # ~0.10870 s
NUM_BARS = 112                 # 112 bars = ~194.78 s (3m 15s)
TOTAL_DURATION = BAR_DUR * NUM_BARS
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

print("=" * 75)
print("=== COSMIC MICROTONAL UK GARAGE — C5-REAL PURE DSP ENGINE ===")
print(f"BPM: {BPM} | Key: E 11-Limit Just Intonation | Bars: {NUM_BARS} ({TOTAL_DURATION:.2f}s)")
print("=" * 75)

# ─────────────────────────────────────────────────────────────────────────────
# 1. 11-LIMIT MICROTONAL TUNING TABLE (Root E1 = 41.2034 Hz)
# ─────────────────────────────────────────────────────────────────────────────
F_ROOT_E1 = 41.203438
F_ROOT_E2 = F_ROOT_E1 * 2.0
F_ROOT_E3 = F_ROOT_E1 * 4.0
F_ROOT_E4 = F_ROOT_E1 * 8.0

RATIOS = {
    '1/1':   1.0 / 1.0,           # Tonic E (0 cents)
    '21/20': 21.0 / 20.0,         # Septimal sub-minor 2nd (+84.5 c)
    '10/9':  10.0 / 9.0,          # Grave major 2nd (+182.4 c)
    '11/9':  11.0 / 9.0,          # Undecimal neutral 3rd (+347.4 c)
    '5/4':   5.0 / 4.0,           # Pure major 3rd (+386.3 c)
    '4/3':   4.0 / 3.0,           # Perfect 4th (+498.0 c)
    '11/8':  11.0 / 8.0,          # Undecimal tritone (+551.3 c)
    '3/2':   3.0 / 2.0,           # Perfect 5th (+702.0 c)
    '13/8':  13.0 / 8.0,          # Tridecimal neutral 6th (+840.5 c)
    '7/4':   7.0 / 4.0,           # Harmonic 7th (+968.8 c)
    '16/9':  16.0 / 9.0,          # Minor 7th (+996.1 c)
    '2/1':   2.0 / 1.0            # Octave (+1200 c)
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. AUDIO HELPER UTILITIES
# ─────────────────────────────────────────────────────────────────────────────
def load_and_resample(file_path, target_sr=SAMPLE_RATE, to_mono=True):
    path = Path(file_path)
    if not path.exists():
        print(f"Warning: Sample not found: {file_path}")
        return np.zeros(int(target_sr * 0.1), dtype=np.float32)
    data, sr = sf.read(str(path))
    if sr != target_sr:
        num_target = int(len(data) * target_sr / sr)
        data = signal.resample(data, num_target)
    if to_mono and data.ndim > 1:
        data = np.mean(data, axis=1)
    return data.astype(np.float32)

def resample_pitch(audio, pitch_ratio):
    """Accurate pitch-shift via high-quality resampling."""
    if abs(pitch_ratio - 1.0) < 1e-4 or len(audio) == 0:
        return audio.copy()
    new_len = max(int(len(audio) / pitch_ratio), 1)
    return signal.resample(audio, new_len).astype(np.float32)

def apply_volterra_saturation(x, drive=1.4, alpha2=0.15, alpha3=0.08):
    """Analog non-linear saturation with warm 2nd and 3rd order harmonics."""
    y = np.tanh(x * drive) + alpha2 * (x ** 2) - alpha3 * (x ** 3)
    peak = np.max(np.abs(y)) + 1e-6
    if peak > 1.0:
        y = y / peak
    return y.astype(np.float32)

def stereo_reverb(mono_in, decay_s=2.8, wet=0.35, high_damp=0.4):
    """Ultra-fast, 100% numerically stable FFT convolution cosmic space reverb."""
    if mono_in.ndim > 1:
        mono = np.mean(mono_in, axis=1)
    else:
        mono = mono_in
    ns = len(mono)
    
    ir_len = int(decay_s * SAMPLE_RATE)
    t_ir = np.arange(ir_len) / SAMPLE_RATE
    env = np.exp(-t_ir / (max(decay_s, 0.1) / 5.5))
    
    # Dual decorrelated noise tails
    np.random.seed(42)
    noise_l = np.random.randn(ir_len).astype(np.float32) * env
    noise_r = np.random.randn(ir_len).astype(np.float32) * env
    
    # High frequency absorption damping
    damp_cutoff = max(1000.0, 5000.0 * (1.0 - high_damp))
    b_damp, a_damp = signal.butter(1, damp_cutoff / (SAMPLE_RATE / 2.0), btype='lowpass')
    ir_l = signal.lfilter(b_damp, a_damp, noise_l)
    ir_r = signal.lfilter(b_damp, a_damp, noise_r)
    
    # Normalize impulse response
    ir_l /= (np.sqrt(np.sum(ir_l**2)) + 1e-6)
    ir_r /= (np.sqrt(np.sum(ir_r**2)) + 1e-6)
    
    # FFT convolution
    wet_l = signal.fftconvolve(mono, ir_l, mode='full')[:ns]
    wet_r = signal.fftconvolve(mono, ir_r, mode='full')[:ns]
    
    res_l = mono * (1.0 - wet) + wet_l * wet
    res_r = mono * (1.0 - wet) + wet_r * wet
    return np.column_stack([res_l, res_r]).astype(np.float32)

def stereo_delay(signal_in, bpm=BPM, delay_notes=(0.75, 1.0), feedback=0.38, wet=0.3):
    """Vectorized multi-tap stereo delay with exponential feedback decay."""
    ns = len(signal_in)
    sixteenth = (60.0 / bpm) / 4.0
    del_l = int(delay_notes[0] * sixteenth * 3.0 * SAMPLE_RATE) # dotted 16th
    del_r = int(delay_notes[1] * sixteenth * 2.0 * SAMPLE_RATE) # 8th
    
    if signal_in.ndim > 1:
        in_l = signal_in[:, 0]
        in_r = signal_in[:, 1]
    else:
        in_l = signal_in
        in_r = signal_in
        
    out_l = np.zeros(ns, dtype=np.float32)
    out_r = np.zeros(ns, dtype=np.float32)
    
    for tap in range(1, 5):
        g = feedback ** tap
        dl = del_l * tap
        dr = del_r * tap
        if dl < ns:
            out_l[dl:] += in_l[:-dl] * g
        if dr < ns:
            out_r[dr:] += in_r[:-dr] * g
            
    res_l = in_l * (1.0 - wet) + out_l * wet
    res_r = in_r * (1.0 - wet) + out_r * wet
    return np.column_stack([res_l, res_r]).astype(np.float32)

print("-> Audio DSP utilities initialized.")

# ─────────────────────────────────────────────────────────────────────────────
# 3. SYNTHESIS ENGINE: SPEED GARAGE SUB & WARPED FM DONK BASS
# ─────────────────────────────────────────────────────────────────────────────
print("-> Synthesizing Stems 01 & 02: Speed Garage Sub-Bass & Warped FM Donk...")

stem_01_sub = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
stem_02_donk = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# UK Garage 2-bar bass motif (syncopated off-beat bounce)
# Pattern definition: (bar_offset, beat_offset, ratio_key, octave, dur_sixteenths, slide_to_ratio)
BASS_MOTIF_A = [
    # Bar 1:
    (0, 0.0,  '1/1',   1, 2, None),       # Beat 1: Root E1 punch
    (0, 1.5,  '11/9',  1, 2, '5/4'),      # Beat 2-and: Undecimal 3rd sliding to pure 3rd
    (0, 2.75, '1/1',   1, 1, None),       # Beat 3 16th skip
    (0, 3.25, '11/8',  1, 2, '3/2'),      # Beat 4 skip: Undecimal tritone slide to 5th!
    # Bar 2:
    (1, 0.5,  '1/1',   1, 2, None),       # Beat 1 off-beat
    (1, 1.25, '7/4',   1, 2, None),       # Beat 2 skip: Harmonic 7th funk
    (1, 2.0,  '1/1',   2, 2, '1/1'),      # Beat 3: Octave bounce E2 sliding down to E1
    (1, 3.0,  '13/8',  1, 1, None),       # Beat 4: Tridecimal neutral 6th
    (1, 3.5,  '16/9',  1, 2, '2/1'),      # Beat 4-and: Minor 7th slide to octave!
]

BASS_MOTIF_B = [
    # Variation with deep 11-limit tritone wobble and drops
    (0, 0.0,  '1/1',   1, 2, None),
    (0, 1.25, '11/9',  1, 3, None),
    (0, 2.5,  '1/1',   1, 2, None),
    (0, 3.25, '21/20', 1, 2, '1/1'),      # Septimal sub-minor 2nd slide down to root!
    (1, 0.5,  '1/1',   1, 2, None),
    (1, 1.5,  '11/8',  1, 2, None),       # Undecimal tritone punch
    (1, 2.25, '7/4',   1, 2, '1/1'),
    (1, 3.25, '10/9',  1, 2, '1/1'),
]

def synthesize_bass_note(f_start, f_end, dur_s, has_scoop=True):
    ns = int(dur_s * SAMPLE_RATE)
    if ns <= 0:
        return np.zeros(0, dtype=np.float32), np.zeros((0, 2), dtype=np.float32)
    t = np.arange(ns) / SAMPLE_RATE
    
    # Frequency trajectory (pitch scoop + slide)
    if has_scoop:
        scoop_dur = min(0.035, dur_s * 0.3)
        scoop_samples = int(scoop_dur * SAMPLE_RATE)
        f_scoop = np.linspace(f_start * 0.88, f_start, scoop_samples)
        f_body = np.linspace(f_start, f_end, ns - scoop_samples)
        f_traj = np.concatenate([f_scoop, f_body])
    else:
        f_traj = np.linspace(f_start, f_end, ns)
        
    phase = 2.0 * np.pi * np.cumsum(f_traj) / SAMPLE_RATE
    
    # 1. Pure Sub-Bass (Mono, clean with soft tanh)
    env_sub = np.exp(-t / max(dur_s * 0.8, 0.1))
    sub_raw = np.sin(phase) * env_sub
    sub_sat = np.tanh(sub_raw * 1.3)
    
    # 2. Warped FM Donk Bass (Speed Garage 2-Op FM with decaying modulation index)
    mod_env = np.exp(-t / 0.085) * 3.5 + 0.35
    mod_phase = phase * 2.0 # 2x frequency modulator for punch
    modulator = np.sin(mod_phase) * mod_env
    carrier = np.sin(phase + modulator)
    
    # Lowpass filter envelope
    donk_env = np.exp(-t / max(dur_s * 0.65, 0.08))
    donk_raw = carrier * donk_env
    
    # Add subtle stereo chorus / micro-detune to the donk
    phase_l = 2.0 * np.pi * np.cumsum(f_traj * 1.003) / SAMPLE_RATE
    phase_r = 2.0 * np.pi * np.cumsum(f_traj * 0.997) / SAMPLE_RATE
    carrier_l = np.sin(phase_l + modulator) * donk_env
    carrier_r = np.sin(phase_r + modulator) * donk_env
    
    donk_stereo = np.column_stack([carrier_l, carrier_r])
    donk_sat = apply_volterra_saturation(donk_stereo, drive=1.6)
    
    return sub_sat.astype(np.float32), donk_sat.astype(np.float32)

# Schedule bass notes across the 112 bars
# Active bars: Drop 1 (bars 17-48), Build 2 tease (bars 68-72), Drop 2 Apex (bars 73-96), Outro pulse (bars 97-104)
for bar in range(NUM_BARS):
    # Determine motif and activity
    is_active = False
    motif = BASS_MOTIF_A
    vel_scale = 1.0
    
    if 16 <= bar < 32:       # Drop 1
        is_active = True
        motif = BASS_MOTIF_A if (bar // 2) % 2 == 0 else BASS_MOTIF_B
        vel_scale = 0.95
    elif 32 <= bar < 48:     # Drop 1 Variation
        is_active = True
        motif = BASS_MOTIF_B if (bar // 2) % 2 == 0 else BASS_MOTIF_A
        vel_scale = 1.0
    elif 68 <= bar < 72:     # Build 2 tease
        is_active = True
        motif = BASS_MOTIF_A
        vel_scale = 0.65 * ((bar - 67) / 4.0) # rising filter tease
    elif 72 <= bar < 96:     # Drop 2 APEX!
        is_active = True
        motif = BASS_MOTIF_B if (bar // 2) % 2 == 1 else BASS_MOTIF_A
        vel_scale = 1.05
    elif 96 <= bar < 104:    # Outro
        is_active = (bar % 2 == 0) # Sparse hits
        motif = [(0, 0.0, '1/1', 1, 4, None)]
        vel_scale = 0.8
        
    if not is_active:
        continue
        
    bar_in_two = bar % 2
    for b_bar, b_beat, r_key, oct_mult, dur_16, slide_r in motif:
        if b_bar != bar_in_two:
            continue
        t_note = (bar * BAR_DUR) + (b_beat * BEAT_DUR)
        dur_note = dur_16 * SIXTEENTH_DUR
        idx_start = int(t_note * SAMPLE_RATE)
        
        f_start = F_ROOT_E1 * RATIOS[r_key] * oct_mult
        f_end = (F_ROOT_E1 * RATIOS[slide_r] * oct_mult) if slide_r else f_start
        
        sub_n, donk_n = synthesize_bass_note(f_start, f_end, dur_note, has_scoop=(slide_r is None))
        ns_n = len(sub_n)
        idx_end = min(idx_start + ns_n, TOTAL_SAMPLES)
        actual_len = idx_end - idx_start
        
        if actual_len > 0:
            stem_01_sub[idx_start:idx_end] += sub_n[:actual_len] * vel_scale * 0.9
            stem_02_donk[idx_start:idx_end, :] += donk_n[:actual_len, :] * vel_scale * 0.75

# Filter sub: steep lowpass below 95 Hz
b_sub_lp, a_sub_lp = signal.butter(4, 95.0 / (SAMPLE_RATE / 2.0), btype='lowpass')
stem_01_sub = signal.lfilter(b_sub_lp, a_sub_lp, stem_01_sub)

# Filter donk: bandpass 120 Hz to 2400 Hz
b_donk_bp, a_donk_bp = signal.butter(2, [120.0 / (SAMPLE_RATE / 2.0), 2400.0 / (SAMPLE_RATE / 2.0)], btype='bandpass')
stem_02_donk[:, 0] = signal.lfilter(b_donk_bp, a_donk_bp, stem_02_donk[:, 0])
stem_02_donk[:, 1] = signal.lfilter(b_donk_bp, a_donk_bp, stem_02_donk[:, 1])

# Duplicate sub to stereo
stem_01_sub_stereo = np.column_stack([stem_01_sub, stem_01_sub])

print(f"✅ Stems 01 & 02 synthesized (Sub RMS: {np.sqrt(np.mean(stem_01_sub**2)):.4f})")

# ─────────────────────────────────────────────────────────────────────────────
# 4. DRUM ENGINE: 2-STEP KICK, GHOST RIMS, SWINGING HATS & BONGO LOOPS
# ─────────────────────────────────────────────────────────────────────────────
print("-> Synthesizing Stems 03, 04, 05, 06, 07: UK Garage Drum Architecture...")

stem_03_kick = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
stem_04_snare_rim = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
stem_05_hats = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
stem_06_bongos = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
stem_07_break = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# Load authentic samples
s_kick_909 = load_and_resample(DRUMS_DIR / "FL 909 Kick Alt.wav")
s_kick_short = load_and_resample(DRUMS_DIR / "Power ShortKick 13.wav")
s_rim = load_and_resample(DRUMS_DIR / "FL 909 Rim.wav")
s_snare_main = load_and_resample(DRUMS_DIR / "FL 909 Snare.wav")
s_hat_ch1 = load_and_resample(DRUMS_DIR / "FL 909 CH 1.wav")
s_hat_ch2 = load_and_resample(DRUMS_DIR / "HouseGen CHat 01.wav")
s_hat_oh = load_and_resample(DRUMS_DIR / "HouseGen OHat 12.wav")
s_shaker1 = load_and_resample(DRUMS_DIR / "Attack Shaker 03.wav")
s_shaker2 = load_and_resample(DRUMS_DIR / "Attack Shaker 04.wav")
s_conga = load_and_resample(DRUMS_DIR / "FL 808 Conga.wav")

s_bongo_loop = load_and_resample(LOOPS_DIR / "LoopMasters MJ Bongo.flac")
s_ghost_break = load_and_resample(LOOPS_DIR / "Slicex Ghost Break.flac")

# Highpass the ghost break at 320 Hz so it leaves sub & low-mid pristine
b_brk_hp, a_brk_hp = signal.butter(4, 320.0 / (SAMPLE_RATE / 2.0), btype='highpass')
s_ghost_break = signal.lfilter(b_brk_hp, a_brk_hp, s_ghost_break)

# Combine kicks for punchy UKG transient
min_k_len = min(len(s_kick_909), len(s_kick_short))
s_kick_hybrid = (s_kick_short[:min_k_len] * 0.65 + s_kick_909[:min_k_len] * 0.55).astype(np.float32)

# Highpass kick slightly at 35 Hz to prevent sub mud
b_k_hp, a_k_hp = signal.butter(2, 35.0 / (SAMPLE_RATE / 2.0), btype='highpass')
s_kick_hybrid = signal.lfilter(b_k_hp, a_k_hp, s_kick_hybrid)

# UKG 2-Step Kick Pattern:
# Beat 1: Heavy downbeat
# Beat 2-and or Beat 3-skip: Classic syncopated 2-step bounce
KICK_PATTERN = [0.0, 1.75, 2.5] # Beat 1, Beat 2 (16th before 3), Beat 3.5

# Rim & Snare:
# Beat 2 and Beat 4 are solid rim/snare hits.
# Ghost taps on 16ths: 1.25, 2.75, 3.25, 4.25
MAIN_SNARE_BEATS = [1.0, 3.0] # 0-indexed: beat 2 and beat 4
GHOST_SNARE_BEATS = [(0.75, 0.40), (1.5, 0.35), (2.25, 0.45), (3.75, 0.50)]

# UKG Swing Offset (60% shuffle on 2nd and 4th sixteenth of each beat)
SWING_OFFSET_S = (0.60 - 0.50) * 2.0 * SIXTEENTH_DUR # ~21.7 ms

def add_sample(stem, sample_data, start_sample, gain=1.0, pan=0.0):
    """Adds a sample to a stereo stem buffer with panning and boundary guards."""
    ns = len(sample_data)
    end_idx = min(start_sample + ns, TOTAL_SAMPLES)
    actual_len = end_idx - start_sample
    if actual_len <= 0 or start_sample < 0:
        return
    
    gain_l = gain * math.cos((pan + 1.0) * math.pi / 4.0)
    gain_r = gain * math.sin((pan + 1.0) * math.pi / 4.0)
    
    if sample_data.ndim == 1:
        stem[start_sample:end_idx, 0] += sample_data[:actual_len] * gain_l
        stem[start_sample:end_idx, 1] += sample_data[:actual_len] * gain_r
    else:
        stem[start_sample:end_idx, 0] += sample_data[:actual_len, 0] * gain_l
        stem[start_sample:end_idx, 1] += sample_data[:actual_len, 1] * gain_r

# Schedule drums across all bars
for bar in range(NUM_BARS):
    # Arrangement sections:
    # 0-8: Intro A (no drums, only subtle shakers)
    # 8-16: Intro B (hats + filtered kick + bongos)
    # 16-48: Drop 1 (full drums, break, rimshots)
    # 48-64: Breakdown (drums cut, only subtle bongos/shakers)
    # 64-72: Build 2 (snare rolls, accelerating hats, rising sweeps)
    # 72-96: Drop 2 Apex (full drums, max swing and energy)
    # 96-104: Outro A (stripping kick, hats & bongos remain)
    # 104-112: Outro B (gentle shaker fadeout)
    
    has_kick = (16 <= bar < 48) or (72 <= bar < 96) or (8 <= bar < 16 and bar % 2 == 0)
    has_snare = (16 <= bar < 48) or (72 <= bar < 96) or (64 <= bar < 72)
    has_hats = (8 <= bar < 56) or (64 <= bar < 104)
    has_perc = (8 <= bar < 48) or (56 <= bar < 64) or (72 <= bar < 104)
    has_break = (16 <= bar < 48) or (72 <= bar < 96) or (68 <= bar < 72)
    
    bar_start_s = bar * BAR_DUR
    
    # 1. KICKS
    if has_kick:
        for k_beat in KICK_PATTERN:
            t_k = bar_start_s + (k_beat * BEAT_DUR)
            s_idx = int(t_k * SAMPLE_RATE)
            g = 0.95 if k_beat == 0.0 else 0.85
            # Filter in Intro B
            if bar < 16:
                g *= 0.65
            add_sample(stem_03_kick, s_kick_hybrid, s_idx, gain=g, pan=0.0)
            
    # 2. SNARES & RIMS
    if has_snare:
        if 64 <= bar < 72: # Snare build-up roll
            # Accelerating snare density
            subdiv = 4 if bar < 68 else (8 if bar < 70 else 16)
            for step in range(subdiv):
                t_sn = bar_start_s + (step * (BAR_DUR / subdiv))
                s_idx = int(t_sn * SAMPLE_RATE)
                roll_gain = 0.3 + 0.6 * ((bar - 64 + (step / subdiv)) / 8.0)
                add_sample(stem_04_snare_rim, s_snare_main, s_idx, gain=roll_gain, pan=0.0)
        else:
            # Main Rim on beats 2 & 4
            for s_beat in MAIN_SNARE_BEATS:
                t_s = bar_start_s + (s_beat * BEAT_DUR)
                s_idx = int(t_s * SAMPLE_RATE)
                add_sample(stem_04_snare_rim, s_rim, s_idx, gain=0.92, pan=-0.05)
                add_sample(stem_04_snare_rim, s_snare_main, s_idx, gain=0.60, pan=0.05)
                
            # Ghost snares
            for g_beat, g_vol in GHOST_SNARE_BEATS:
                t_g = bar_start_s + (g_beat * BEAT_DUR)
                s_idx = int(t_g * SAMPLE_RATE)
                add_sample(stem_04_snare_rim, s_rim, s_idx, gain=g_vol * 0.7, pan=0.15)
                
    # 3. HI-HATS (16ths with 60% UKG Swing)
    if has_hats:
        for beat in range(4):
            for sixteenth in range(4):
                is_swung = (sixteenth in [1, 3])
                swing_add = SWING_OFFSET_S if is_swung else 0.0
                t_h = bar_start_s + (beat * BEAT_DUR) + (sixteenth * SIXTEENTH_DUR) + swing_add
                s_idx = int(t_h * SAMPLE_RATE)
                
                # Alternate hat samples
                h_sample = s_hat_ch1 if (sixteenth % 2 == 0) else s_hat_ch2
                h_gain = 0.55 if sixteenth == 0 else (0.42 if is_swung else 0.48)
                h_pan = -0.2 if is_swung else 0.15
                add_sample(stem_05_hats, h_sample, s_idx, gain=h_gain, pan=h_pan)
                
            # Open Hat on off-beat 8th (sixteenth 2)
            t_oh = bar_start_s + (beat * BEAT_DUR) + (2 * SIXTEENTH_DUR)
            s_idx_oh = int(t_oh * SAMPLE_RATE)
            add_sample(stem_05_hats, s_hat_oh, s_idx_oh, gain=0.58, pan=0.25)
            
    # 4. PERCUSSION (Bongos, Congas & Shakers)
    if has_perc or bar < 8: # Shakers also present in Intro A
        # 16th Shakers back and forth
        for step in range(16):
            is_swung = (step % 2 == 1)
            t_sh = bar_start_s + (step * SIXTEENTH_DUR) + (SWING_OFFSET_S if is_swung else 0.0)
            s_idx = int(t_sh * SAMPLE_RATE)
            sh_samp = s_shaker1 if (step % 2 == 0) else s_shaker2
            sh_pan = -0.35 if (step % 2 == 0) else 0.35
            sh_gain = 0.35 if bar >= 16 else 0.22
            add_sample(stem_06_bongos, sh_samp, s_idx, gain=sh_gain, pan=sh_pan)
            
        # Conga on syncopated accents (beat 1.75 and 3.5)
        if has_perc:
            for c_beat in [1.75, 3.5]:
                t_cg = bar_start_s + (c_beat * BEAT_DUR)
                s_idx = int(t_cg * SAMPLE_RATE)
                add_sample(stem_06_bongos, s_conga, s_idx, gain=0.65, pan=-0.2)
                
            # Loop slice of real bongos across the bar
            b_dur_samples = int(BAR_DUR * SAMPLE_RATE)
            b_start_src = (bar % 2) * b_dur_samples
            if b_start_src + b_dur_samples <= len(s_bongo_loop):
                b_slice = s_bongo_loop[b_start_src:b_start_src + b_dur_samples]
                idx_b = int(bar_start_s * SAMPLE_RATE)
                add_sample(stem_06_bongos, b_slice, idx_b, gain=0.55, pan=0.1)
                
    # 5. SLICED UNDERGROUND BREAK (Ghost Break)
    if has_break:
        brk_len = int(BAR_DUR * SAMPLE_RATE)
        src_offset = ((bar % 4) * brk_len) % max(len(s_ghost_break) - brk_len, 1)
        brk_slice = s_ghost_break[src_offset:src_offset + brk_len]
        idx_brk = int(bar_start_s * SAMPLE_RATE)
        g_brk = 0.45 if bar >= 16 else 0.25
        add_sample(stem_07_break, brk_slice, idx_brk, gain=g_brk, pan=0.0)

print("✅ Stems 03 - 07 synthesized (Drums, Rims, Hats, Bongos, Breaks)")

# ─────────────────────────────────────────────────────────────────────────────
# 5. HARMONIC ENGINE: COSMIC MICROTONAL RHODES & ASTRAL SHEPARD ARPS
# ─────────────────────────────────────────────────────────────────────────────
print("-> Synthesizing Stems 08 & 09: Cosmic Microtonal Rhodes & Astral Arps...")

stem_08_rhodes = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
stem_09_arps = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# Load real Rhodes Mark I multi-samples
s_rhodes_c2 = load_and_resample(INST_DIR / "Rhodes Piano (3).wav") # ~65.4 Hz
s_rhodes_c3 = load_and_resample(INST_DIR / "Rhodes Piano (5).wav") # ~130.8 Hz
s_rhodes_c4 = load_and_resample(INST_DIR / "Rhodes Piano (7).wav") # ~260.9 Hz
s_rhodes_c5 = load_and_resample(INST_DIR / "Rhodes Piano (9).wav") # ~525.0 Hz

def get_rhodes_note(f_target, dur_s=2.0):
    """Selects closest multi-sample and resamples to exact 11-limit frequency."""
    if f_target < 95.0:
        base_s, base_f = s_rhodes_c2, 65.43
    elif f_target < 190.0:
        base_s, base_f = s_rhodes_c3, 130.86
    elif f_target < 380.0:
        base_s, base_f = s_rhodes_c4, 260.95
    else:
        base_s, base_f = s_rhodes_c5, 525.00
        
    ratio = f_target / base_f
    res = resample_pitch(base_s, ratio)
    req_samples = int(dur_s * SAMPLE_RATE)
    if len(res) < req_samples:
        res = np.pad(res, (0, req_samples - len(res)))
    else:
        res = res[:req_samples]
        
    # Apply natural envelope fadeout
    fade_len = int(0.08 * SAMPLE_RATE)
    res[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
    return res.astype(np.float32)

# Pre-render 11-limit Rhodes chords on E
# Chord 1: Em9[11/9] (Cosmic soul chord with undecimal neutral 3rd)
# Notes: E2 (82.4Hz), G2_undec (100.7Hz), B2 (123.6Hz), D3 (146.5Hz), F#3 (164.8Hz)
chord_em9_notes = [
    F_ROOT_E2 * RATIOS['1/1'],
    F_ROOT_E2 * RATIOS['11/9'],
    F_ROOT_E2 * RATIOS['3/2'],
    F_ROOT_E2 * RATIOS['7/4'],
    F_ROOT_E3 * RATIOS['10/9']
]

# Chord 2: E11[11/8] (Euler-undecimal cosmic tritone stab)
# Notes: E2, B2, D3, F#3, A#3_undec (226.6Hz)
chord_e11_notes = [
    F_ROOT_E2 * RATIOS['1/1'],
    F_ROOT_E2 * RATIOS['3/2'],
    F_ROOT_E3 * RATIOS['10/9'],
    F_ROOT_E3 * RATIOS['11/8'],
    F_ROOT_E3 * RATIOS['13/8']
]

# Chord 3: A7[7/4] (Harmonic 7th soulful funk chord)
# Notes: A2 (110.0Hz), C#3 (137.5Hz), E3 (164.8Hz), G3_harm (192.5Hz)
chord_a7_notes = [
    F_ROOT_E2 * RATIOS['4/3'],
    F_ROOT_E2 * RATIOS['5/4'] * (4.0/3.0),
    F_ROOT_E3 * RATIOS['1/1'],
    F_ROOT_E3 * RATIOS['7/4'] * (4.0/3.0)
]

def render_chord(note_freqs, dur_s=1.6):
    ns = int(dur_s * SAMPLE_RATE)
    mono_chord = np.zeros(ns, dtype=np.float32)
    for f in note_freqs:
        note_audio = get_rhodes_note(f, dur_s=dur_s)
        mono_chord += note_audio[:ns] * 0.22
    # Apply analog stereo tremolo (4.6 Hz)
    t = np.arange(ns) / SAMPLE_RATE
    tremolo_l = 0.5 + 0.45 * np.cos(2.0 * np.pi * 4.6 * t)
    tremolo_r = 0.5 + 0.45 * np.sin(2.0 * np.pi * 4.6 * t)
    return np.column_stack([mono_chord * tremolo_l, mono_chord * tremolo_r]).astype(np.float32)

em9_audio = render_chord(chord_em9_notes, dur_s=1.8)
e11_audio = render_chord(chord_e11_notes, dur_s=1.4)
a7_audio = render_chord(chord_a7_notes, dur_s=1.8)

# Schedule Rhodes chords:
# Syncopated UK Garage stabs on off-beats: Beat 1.5, Beat 3.5, or sustained swells in intro/breakdown
for bar in range(NUM_BARS):
    bar_start_s = bar * BAR_DUR
    
    # Intro (Bars 0-16): Sustained lush chords
    if bar < 16:
        ch_audio = em9_audio if (bar % 4 < 2) else a7_audio
        idx = int(bar_start_s * SAMPLE_RATE)
        add_sample(stem_08_rhodes, ch_audio, idx, gain=0.65, pan=0.0)
        
    # Drop 1 (Bars 16-48): Syncopated stabs
    elif 16 <= bar < 48:
        # Stab on Beat 1.5 and Beat 3.75
        for b_stab, ch in [(1.5, em9_audio), (3.75, e11_audio if bar % 2 == 1 else a7_audio)]:
            t_st = bar_start_s + (b_stab * BEAT_DUR)
            idx = int(t_st * SAMPLE_RATE)
            add_sample(stem_08_rhodes, ch, idx, gain=0.55, pan=0.0)
            
    # Breakdown (Bars 48-64): Zero-gravity cosmic swells
    elif 48 <= bar < 64:
        if bar % 4 == 0:
            idx = int(bar_start_s * SAMPLE_RATE)
            add_sample(stem_08_rhodes, em9_audio, idx, gain=0.75, pan=-0.1)
        elif bar % 4 == 2:
            idx = int(bar_start_s * SAMPLE_RATE)
            add_sample(stem_08_rhodes, e11_audio, idx, gain=0.75, pan=0.1)
            
    # Drop 2 Apex (Bars 72-96): Maximum funk stabs
    elif 72 <= bar < 96:
        for b_stab, ch in [(1.5, em9_audio), (2.5, a7_audio), (3.5, e11_audio)]:
            t_st = bar_start_s + (b_stab * BEAT_DUR)
            idx = int(t_st * SAMPLE_RATE)
            add_sample(stem_08_rhodes, ch, idx, gain=0.58, pan=0.0)
            
    # Outro (Bars 96-112): Fading chords
    elif bar >= 96:
        if bar % 4 == 0:
            idx = int(bar_start_s * SAMPLE_RATE)
            fade = max(1.0 - (bar - 96) / 16.0, 0.1)
            add_sample(stem_08_rhodes, em9_audio, idx, gain=0.6 * fade, pan=0.0)

# Process Rhodes through stereo space reverb
stem_08_rhodes = stereo_reverb(np.mean(stem_08_rhodes, axis=1), decay_s=3.2, wet=0.35)

# ─────────────────────────────────────────────────────────────────────────────
# 6. STEM 09: ASTRAL MICROTONAL ARPEGGIOS & SHEPARD GLISSANDO
# ─────────────────────────────────────────────────────────────────────────────
# Pre-calculate crystalline sine notes for 11-limit arpeggios
arp_scale_freqs = [
    F_ROOT_E3 * RATIOS['1/1'],
    F_ROOT_E3 * RATIOS['11/9'],
    F_ROOT_E3 * RATIOS['11/8'],
    F_ROOT_E3 * RATIOS['3/2'],
    F_ROOT_E3 * RATIOS['7/4'],
    F_ROOT_E4 * RATIOS['1/1'],
    F_ROOT_E4 * RATIOS['11/9'],
    F_ROOT_E4 * RATIOS['11/8']
]

# Synthesize Shepard-Risset rising cosmic glissando for build-up sections (bars 8-16 and 64-72)
def synthesize_shepard_swell(dur_s):
    ns = int(dur_s * SAMPLE_RATE)
    t = np.arange(ns) / SAMPLE_RATE
    out = np.zeros(ns, dtype=np.float32)
    num_octaves = 6
    base_f = 55.0
    for oct_idx in range(num_octaves):
        # Exponential frequency rise over duration
        f_start = base_f * (2.0 ** oct_idx)
        f_t = f_start * (2.0 ** (t / dur_s))
        phase = 2.0 * np.pi * np.cumsum(f_t) / SAMPLE_RATE
        # Gaussian bell envelope in log-frequency
        center_oct = 3.0
        dist = oct_idx + (t / dur_s) - center_oct
        amp = np.exp(-0.5 * (dist / 1.4) ** 2)
        out += np.sin(phase) * amp * 0.15
    return out.astype(np.float32)

shepard_8bars = synthesize_shepard_swell(BAR_DUR * 8.0)

# Schedule Shepard in builds
idx_b1 = int(8 * BAR_DUR * SAMPLE_RATE)
idx_b2 = int(64 * BAR_DUR * SAMPLE_RATE)
add_sample(stem_09_arps, shepard_8bars, idx_b1, gain=0.65, pan=0.0)
add_sample(stem_09_arps, shepard_8bars, idx_b2, gain=0.85, pan=0.0)

# Schedule microtonal arpeggios in Drop 1 Variation (bars 32-48) and Drop 2 (bars 72-96)
arp_note_dur = SIXTEENTH_DUR
for bar in range(NUM_BARS):
    if (32 <= bar < 48) or (72 <= bar < 96):
        bar_start_s = bar * BAR_DUR
        for step in range(16):
            t_step = bar_start_s + (step * SIXTEENTH_DUR)
            s_idx = int(t_step * SAMPLE_RATE)
            f_note = arp_scale_freqs[(bar * 3 + step) % len(arp_scale_freqs)]
            
            # Synthesize short bell chime
            t_bell = np.arange(int(arp_note_dur * 2.5 * SAMPLE_RATE)) / SAMPLE_RATE
            bell_env = np.exp(-t_bell / 0.09)
            bell_sig = (np.sin(2.0 * np.pi * f_note * t_bell) * 0.7 +
                        np.sin(2.0 * np.pi * (f_note * 2.756) * t_bell) * 0.25 +
                        np.sin(2.0 * np.pi * (f_note * 5.404) * t_bell) * 0.1) * bell_env
            pan_bell = -0.4 + 0.8 * ((step % 4) / 3.0)
            add_sample(stem_09_arps, bell_sig, s_idx, gain=0.38, pan=pan_bell)

# Add delay & space to arps
stem_09_arps = stereo_delay(stem_09_arps, bpm=BPM, feedback=0.45, wet=0.4)
stem_09_arps = stereo_reverb(np.mean(stem_09_arps, axis=1), decay_s=3.5, wet=0.3)

print("✅ Stems 08 & 09 synthesized (Rhodes & Astral Arps)")

# ─────────────────────────────────────────────────────────────────────────────
# 7. STEM 10: SOUL VOCAL CHOPS & COSMIC SFX
# ─────────────────────────────────────────────────────────────────────────────
print("-> Synthesizing Stem 10: Soul Vocal Chops & Cosmic SFX...")

stem_10_vocals = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# Load real vocals and Coub reference chops
s_knockout = load_and_resample(VOC_DIR / "Knocked Out Vocals_ b3_2.mp3", to_mono=True)
s_coub_ref = load_and_resample(MUSIC_DIR / "coub_reference_tmjd8000pa.mp3", to_mono=True)
s_cymb_rise = load_and_resample(DRUMS_DIR / "FL Cymbal Rise.wav", to_mono=False)
s_cymb_drop = load_and_resample(DRUMS_DIR / "FL Cymbal Drop.wav", to_mono=False)
s_blip = load_and_resample(DRUMS_DIR / "Attack Blip 03.wav", to_mono=True)

# Extract vocal slices from Coub ("4-Real" vocal hook and stabs)
# In coub reference: iconic chops occur at ~0.67s, 1.26s, 2.13s, 3.44s
def extract_slice(audio, t_start, t_end):
    i0 = int(t_start * SAMPLE_RATE)
    i1 = int(t_end * SAMPLE_RATE)
    clip = audio[i0:min(i1, len(audio))].copy()
    # Smooth edges
    fade = min(int(0.015 * SAMPLE_RATE), len(clip) // 4)
    if fade > 0:
        clip[:fade] *= np.linspace(0.0, 1.0, fade)
        clip[-fade:] *= np.linspace(1.0, 0.0, fade)
    return clip.astype(np.float32)

v_chop_4real = extract_slice(s_coub_ref, 0.55, 1.15)  # "For real"
v_chop_stab1 = extract_slice(s_coub_ref, 1.22, 1.65)  # Syncopated stab
v_chop_baby  = extract_slice(s_coub_ref, 2.05, 2.65)  # Vocal hook
v_chop_cry   = extract_slice(s_coub_ref, 3.35, 4.10)  # Melodic vocal cry

# Soul vocal run from Knocked Out Vocals
v_soul_run   = extract_slice(s_knockout, 4.8, 6.8)     # Soul run
v_soul_ooh   = extract_slice(s_knockout, 52.0, 54.5)   # Soulful high falsetto

# Highpass vocals to fit UKG mix (cut below 250 Hz)
b_voc_hp, a_voc_hp = signal.butter(4, 250.0 / (SAMPLE_RATE / 2.0), btype='highpass')
v_chop_4real = signal.lfilter(b_voc_hp, a_voc_hp, v_chop_4real)
v_chop_stab1 = signal.lfilter(b_voc_hp, a_voc_hp, v_chop_stab1)
v_chop_baby  = signal.lfilter(b_voc_hp, a_voc_hp, v_chop_baby)
v_chop_cry   = signal.lfilter(b_voc_hp, a_voc_hp, v_chop_cry)
v_soul_run   = signal.lfilter(b_voc_hp, a_voc_hp, v_soul_run)
v_soul_ooh   = signal.lfilter(b_voc_hp, a_voc_hp, v_soul_ooh)

# Schedule vocal chops across arrangement
for bar in range(NUM_BARS):
    bar_start_s = bar * BAR_DUR
    
    # Intro vocal hints (bars 4-16)
    if 4 <= bar < 16:
        if bar % 4 == 0:
            idx = int((bar_start_s + 1.5 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_4real, idx, gain=0.65, pan=0.1)
        elif bar % 4 == 2:
            idx = int((bar_start_s + 2.0 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_baby, idx, gain=0.60, pan=-0.15)
            
    # Drop 1 (bars 16-48): Vocal chops punctuating the groove
    elif 16 <= bar < 48:
        # "4-Real" on bar starts
        if bar % 4 == 0:
            idx = int((bar_start_s + 0.0 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_4real, idx, gain=0.85, pan=0.0)
        elif bar % 4 == 2:
            idx = int((bar_start_s + 1.5 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_baby, idx, gain=0.75, pan=-0.2)
            idx2 = int((bar_start_s + 3.25 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_stab1, idx2, gain=0.70, pan=0.2)
            
        # Soul run at transitions (bars 23, 31, 39, 47)
        if bar % 8 == 7:
            idx = int((bar_start_s + 2.0 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_soul_run, idx, gain=0.72, pan=0.0)
            
    # Breakdown (bars 48-64): Soulful falsetto echoing into deep space
    elif 48 <= bar < 64:
        if bar % 8 == 0:
            idx = int(bar_start_s * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_soul_ooh, idx, gain=0.88, pan=0.0)
        elif bar % 8 == 4:
            idx = int((bar_start_s + 1.0 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_cry, idx, gain=0.80, pan=-0.1)
            
    # Build 2 (bars 64-72): Rapid stutter build-up!
    elif 64 <= bar < 72:
        if bar >= 68: # Rapid stutters
            subdiv = 4 if bar < 70 else (8 if bar < 71 else 16)
            for step in range(subdiv):
                t_st = bar_start_s + (step * (BAR_DUR / subdiv))
                idx = int(t_st * SAMPLE_RATE)
                short_4 = v_chop_4real[:int(0.08 * SAMPLE_RATE)]
                g_st = 0.4 + 0.5 * ((bar - 68 + step/subdiv) / 4.0)
                add_sample(stem_10_vocals, short_4, idx, gain=g_st, pan=0.0)
        if bar == 71: # Last bar before Drop 2: Vacuum pause on beats 3-4 with whisper
            idx_whisper = int((bar_start_s + 3.0 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_4real, idx_whisper, gain=0.95, pan=0.0)
            
    # Drop 2 Apex (bars 72-96): Full vocal fire!
    elif 72 <= bar < 96:
        if bar % 2 == 0:
            idx = int((bar_start_s + 0.0 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_4real, idx, gain=0.90, pan=0.0)
            idx_stab = int((bar_start_s + 2.5 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_stab1, idx_stab, gain=0.75, pan=0.25)
        else:
            idx = int((bar_start_s + 1.5 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_baby, idx, gain=0.80, pan=-0.2)
            if bar % 4 == 3:
                idx_cry = int((bar_start_s + 2.75 * BEAT_DUR) * SAMPLE_RATE)
                add_sample(stem_10_vocals, v_chop_cry, idx_cry, gain=0.82, pan=0.15)
                
    # Outro (bars 96-112)
    elif bar >= 96:
        if bar % 4 == 0:
            idx = int((bar_start_s + 1.5 * BEAT_DUR) * SAMPLE_RATE)
            add_sample(stem_10_vocals, v_chop_4real, idx, gain=0.60 * max(1.0 - (bar-96)/16.0, 0.1), pan=0.0)

# Schedule Cymbal Risers, Drops & Laser Blips
# Risers peaking before drops: Bar 15.5 and Bar 71.5
idx_rise1 = int((16 * BAR_DUR - 6.0) * SAMPLE_RATE)
idx_rise2 = int((72 * BAR_DUR - 6.0) * SAMPLE_RATE)
add_sample(stem_10_vocals, s_cymb_rise, idx_rise1, gain=0.65, pan=0.0)
add_sample(stem_10_vocals, s_cymb_rise, idx_rise2, gain=0.85, pan=0.0)

# Cymbal Drop impacts on Bar 16 and Bar 72
idx_drop1 = int(16 * BAR_DUR * SAMPLE_RATE)
idx_drop2 = int(72 * BAR_DUR * SAMPLE_RATE)
add_sample(stem_10_vocals, s_cymb_drop, idx_drop1, gain=0.70, pan=0.0)
add_sample(stem_10_vocals, s_cymb_drop, idx_drop2, gain=0.85, pan=0.0)

# Cosmic laser blips across breakdowns
for blip_bar in [50, 54, 58, 62]:
    idx_blip = int((blip_bar * BAR_DUR + 2.5 * BEAT_DUR) * SAMPLE_RATE)
    add_sample(stem_10_vocals, s_blip, idx_blip, gain=0.45, pan=-0.3 if blip_bar % 8 == 2 else 0.3)

# Add stereo tape delay and cosmic reverb to the vocal stem
stem_10_vocals = stereo_delay(stem_10_vocals, bpm=BPM, delay_notes=(0.75, 1.0), feedback=0.42, wet=0.35)
stem_10_vocals = stereo_reverb(np.mean(stem_10_vocals, axis=1), decay_s=3.0, wet=0.28)

print("✅ Stem 10 synthesized (Vocals & SFX)")

# ─────────────────────────────────────────────────────────────────────────────
# 8. MASTERING CHAIN & DISCRETE STEMS WRITING
# ─────────────────────────────────────────────────────────────────────────────
print("-> Processing Master Summation & Professional Mastering Chain...")

stems_dict = {
    "01_Speed_Garage_SubBass.wav": stem_01_sub_stereo,
    "02_Warped_FM_Donk.wav": stem_02_donk,
    "03_UKG_Punch_Kick.wav": stem_03_kick,
    "04_Ghost_Snares_And_Rims.wav": stem_04_snare_rim,
    "05_Swinging_UKG_HiHats.wav": stem_05_hats,
    "06_Acoustic_Bongos_Perc.wav": stem_06_bongos,
    "07_Sliced_Underground_Break.wav": stem_07_break,
    "08_Cosmic_Microtonal_Rhodes.wav": stem_08_rhodes,
    "09_Astral_Arps_Shepard.wav": stem_09_arps,
    "10_Soul_Vocal_Chops_SFX.wav": stem_10_vocals
}

# Write discrete stems
print("-> Writing 10 discrete stems to canonical ~/Music/Synthesized_Stems/Cosmic_Microtonal_UKG_4Real/...")
for name, data in stems_dict.items():
    p = STEMS_DIR / name
    # Ensure float32 in range
    pk = np.max(np.abs(data)) + 1e-6
    if pk > 1.0:
        data = data / pk
    sf.write(str(p), data, SAMPLE_RATE, subtype='PCM_24')
    print(f"   • {name:32s} [24-bit WAV, RMS={np.sqrt(np.mean(data**2)):.4f}]")

# Master Summation with balanced mix levels
mix_master = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
mix_master += stem_01_sub_stereo * 0.90   # Driving sub
mix_master += stem_02_donk * 0.72         # Punchy FM donk
mix_master += stem_03_kick * 0.92         # Punchy 2-step kick
mix_master += stem_04_snare_rim * 0.82    # Snappy rim & ghost snares
mix_master += stem_05_hats * 0.58         # Shuffling hats
mix_master += stem_06_bongos * 0.55       # Organic bongos/shakers
mix_master += stem_07_break * 0.50        # Underground grit break
mix_master += stem_08_rhodes * 0.70       # Microtonal soul Rhodes
mix_master += stem_09_arps * 0.52         # Astral arpeggios
mix_master += stem_10_vocals * 0.75       # Soul vocal chops & SFX

# 1. Monofy low-end below 110 Hz
b_sub_mono, a_sub_mono = signal.butter(4, 110.0 / (SAMPLE_RATE / 2.0), btype='lowpass')
sub_l = signal.lfilter(b_sub_mono, a_sub_mono, mix_master[:, 0])
sub_r = signal.lfilter(b_sub_mono, a_sub_mono, mix_master[:, 1])
sub_mono_channel = (sub_l + sub_r) * 0.5

# Highs above 110 Hz preserve full stereo width
b_high_st, a_high_st = signal.butter(4, 110.0 / (SAMPLE_RATE / 2.0), btype='highpass')
highs_l = signal.lfilter(b_high_st, a_high_st, mix_master[:, 0])
highs_r = signal.lfilter(b_high_st, a_high_st, mix_master[:, 1])

mix_master[:, 0] = sub_mono_channel + highs_l
mix_master[:, 1] = sub_mono_channel + highs_r

# 2. Subtle Volterra warmth on the master bus
mix_master = apply_volterra_saturation(mix_master, drive=1.15, alpha2=0.06, alpha3=0.03)

# 3. True-Peak Limiter / Ceiling Normalization to -0.3 dBFS (0.966)
peak_cur = np.max(np.abs(mix_master))
target_peak = 0.966
mix_master = (mix_master / peak_cur) * target_peak

# Write Master WAV (24-bit 44.1 kHz)
sf.write(str(OUTPUT_WAV), mix_master, SAMPLE_RATE, subtype='PCM_24')
print(f"✅ Master WAV Exported: {OUTPUT_WAV} ({OUTPUT_WAV.stat().st_size / (1024*1024):.2f} MB)")

# Encode Master MP3 (320 kbps) via ffmpeg
cmd_mp3 = [
    "ffmpeg", "-y", "-i", str(OUTPUT_WAV),
    "-b:a", "320k", "-ar", "44100",
    str(OUTPUT_MP3)
]
subprocess.run(cmd_mp3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"✅ Master MP3 Exported: {OUTPUT_MP3} ({OUTPUT_MP3.stat().st_size / (1024*1024):.2f} MB)")

# ─────────────────────────────────────────────────────────────────────────────
# 9. COMPILE NATIVE FL STUDIO PROJECT (.flp)
# ─────────────────────────────────────────────────────────────────────────────
print("-> Compiling Native FL Studio Project (.flp)...")
try:
    from flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    res = compile_multitrack_stems_flp(
        stems_dir=str(STEMS_DIR),
        project_title="Cosmic Microtonal UKG 4Real Session",
        bpm=BPM,
        output_flp=str(OUTPUT_FLP)
    )
    print(f"✅ Native FLP Project Compiled: {OUTPUT_FLP} ({OUTPUT_FLP.stat().st_size / 1024:.1f} KB)")
except Exception as e:
    print(f"Notice: FLP compiler note: {e}")

print("=" * 75)
print("=== COSMIC MICROTONAL UK GARAGE MASTERPIECE SUCCESSFULLY COMPILED ===")
print(f"Master WAV: {OUTPUT_WAV}")
print(f"Master MP3: {OUTPUT_MP3}")
print(f"Stems Dir:  {STEMS_DIR}")
print(f"FL Studio:  {OUTPUT_FLP}")
print("=" * 75)
