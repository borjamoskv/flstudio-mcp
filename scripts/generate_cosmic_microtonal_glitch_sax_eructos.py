#!/usr/bin/env python3
"""
Cosmic Microtonal Glitch & Duende Synthesizer — C5-REAL Pure DSP Engine
═════════════════════════════════════════════════════════════════════════════════
Extended 96-Bar Masterpiece (192.0s @ 120.0 BPM):
- Saxophone completely PURGED.
- 11-Limit Xenharmonic Just Tuning on E (Natural 7th 7/4 & 11th 11/8 harmonics).
- Alain Vocoder Italo Dark: Alain's authentic voice modulating a 16-band filter bank
  with a polyphonic detuned sawtooth carrier in E negative harmony & Moroder rolling 16th bassline.
- Palmas Flamencas con Duende: Physical modeling of acoustic sordas & secas in bulería swing.
- Mitxu Flamenco Quejío & Negative Harmony Choir (Ernst Levy polar reflection axis).
- THE FAKE DROP (El Falso Drop): Extreme tension build (bars 52-59.5) -> Sudden vacuum cut (bars 60-63.5)
  with dry Alain whisper and lonely space delay eructo -> MONSTER APOTHEOTIC REAL DROP at Bar 64!
- 11 Discrete High-Fidelity WAV Stems, Master WAV, Master MP3, and Native FL Studio Project (.flp)
  centralized into canonical ~/Music/
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

MUSIC_DIR = Path.home() / "Music"
OUTPUT_WAV = MUSIC_DIR / "COSMIC_MICROTONAL_GLITCH_SAX_ERUCTOS.wav"
OUTPUT_MP3 = MUSIC_DIR / "COSMIC_MICROTONAL_GLITCH_SAX_ERUCTOS.mp3"
STEMS_DIR = MUSIC_DIR / "Synthesized_Stems" / "Cosmic_Microtonal_Sax_Eructos"
PROJECTS_DIR = MUSIC_DIR / "FL Studio Bounces" / "Projects"
OUTPUT_FLP = PROJECTS_DIR / "Cosmic_Microtonal_Glitch_Sax_Eructos_Session.flp"

# Canonical Voice Clones
ALAIN_ERUCTO_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Alain" / "cloned_generations" / "alain_eructo_gutural_la_hostia.wav"
ALAIN_HOSTIA_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Alain" / "cloned_generations" / "real_alain_acento_vasco" / "alain_vasco_1_la_ostia.wav"
ALAIN_BOMBO_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Alain" / "cloned_generations" / "real_alain_acento_vasco" / "alain_vasco_4_hacienda_bombo.wav"
ALAIN_EXERGIA_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Alain" / "cloned_generations" / "real_alain_v9_privado_elvio" / "alain_v9_1_exergia_entropia.wav"

MITXU_QUEJIO_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Mitxu" / "cloned_generations" / "mitxu_flamenco_quejio_buleria.wav"
MITXU_CANTIC_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Mitxu" / "cloned_generations" / "real_mitxu_acento_vasco" / "mitxu_vasco_lolololo_cantic.wav"
MITXU_MINU_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Mitxu" / "cloned_generations" / "mitxu_michu_minu_coros.wav"
MITXU_PAPARA_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Mitxu" / "cloned_generations" / "real_mitxu_acento_vasco" / "mitxu_vasco_paparapapa_cantic.wav"

STEMS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100
BPM = 120.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4.0
SIXTEENTH_DUR = BEAT_DUR / 4.0
NUM_BARS = 96
TOTAL_DURATION = BAR_DUR * NUM_BARS
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

print(f"=== Synthesizing Cosmic Microtonal Glitch & Duende Masterpiece (Extended) ===")
print(f"Duration: {TOTAL_DURATION:.2f}s ({NUM_BARS} bars @ {BPM} BPM)")
print(f"Total Samples: {TOTAL_SAMPLES} @ {SAMPLE_RATE} Hz")

def get_time(n_samples):
    return np.arange(n_samples, dtype=np.float32) / SAMPLE_RATE

# 11-Limit Xenharmonic Tuning on E (E1 = 41.203 Hz, E3 = 164.814 Hz)
ROOT_E3 = 164.8138
HARMONIC_RATIOS = [1.0, 9.0/8.0, 5.0/4.0, 11.0/8.0, 3.0/2.0, 7.0/4.0]
SCALE_E3 = [ROOT_E3 * r for r in HARMONIC_RATIOS]
SCALE_E4 = [f * 2.0 for f in SCALE_E3]
SCALE_E5 = [f * 4.0 for f in SCALE_E3]

# 11 Stems
stems = {
    "01_Cosmic_Kick_Sub": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "02_Polyrhythmic_Percussion": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "03_Glitch_Buffer_Stutter": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "04_Cosmic_Bells_Chimes": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "05_Cosmic_Pads_Drone": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "06_HiHats_Shakers_Groove": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "07_Palmas_Flamencas_Duende": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "08_Voces_Coros_Negative_Harmony": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "09_Eructos_Dub_Delay_Barrage": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "10_Atmospheric_Cosmic_Textures": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "11_Alain_Vocoder_Italo_Dark": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32))
}

# -------------------------------------------------------------
# 1. COSMIC KICK & DEEP SUB (E0/E1 41.2Hz)
# -------------------------------------------------------------
print("-> Synthesizing Cosmic 808/909 Sub-Kick...")
k_dur = 0.38
k_samples = int(k_dur * SAMPLE_RATE)
t_k = get_time(k_samples)
phase_k = 2.0 * np.pi * (41.2 * t_k + (88.8 / 32.0) * (1.0 - np.exp(-32.0 * t_k)))
env_k = np.exp(-t_k * 9.5)
click = 0.35 * np.sin(2.0 * np.pi * 1400.0 * t_k) * np.exp(-t_k * 130.0)
kick_wf = np.tanh(1.7 * (np.sin(phase_k) + click)) * env_k * 0.88

# Kick Active:
# Drop 1: Bars 16 to 44
# Real Drop 2: Bars 64 to 88
# SILENT in: Intro (0-16), Breakdown (44-52), Build-up & FAKE DROP (52-64), Outro (88-96)
kick_bars = [b for b in range(NUM_BARS) if (16 <= b < 44) or (64 <= b < 88)]
kl, kr = stems["01_Cosmic_Kick_Sub"]

sub_freq = 41.203
sub_t = get_time(TOTAL_SAMPLES)
sub_drone = np.sin(2.0 * np.pi * sub_freq * sub_t) + 0.35 * np.sin(4.0 * np.pi * sub_freq * sub_t)
sub_drone = np.tanh(1.5 * sub_drone) * 0.42

for b in kick_bars:
    for beat in range(4):
        t_hit = b * BAR_DUR + beat * BEAT_DUR
        s_idx = int(t_hit * SAMPLE_RATE)
        e_idx = min(s_idx + k_samples, TOTAL_SAMPLES)
        slen = e_idx - s_idx
        kl[s_idx:e_idx] += kick_wf[:slen]
        kr[s_idx:e_idx] += kick_wf[:slen]
        
    s_b = int(b * BAR_DUR * SAMPLE_RATE)
    e_b = min(s_b + int(BAR_DUR * SAMPLE_RATE), TOTAL_SAMPLES)
    kl[s_b:e_b] += sub_drone[s_b:e_b] * 0.30
    kr[s_b:e_b] += sub_drone[s_b:e_b] * 0.30

# -------------------------------------------------------------
# 2. POLYRHYTHMIC PERCUSSION (5:4 Cross-Rhythms & Syncopated Woodblocks)
# -------------------------------------------------------------
print("-> Synthesizing Polyrhythmic Percussion (5:4 cross-rhythms)...")
perc_l, perc_r = stems["02_Polyrhythmic_Percussion"]

def synth_wood(freq, decay=35.0):
    dur = 0.08
    ns = int(dur * SAMPLE_RATE)
    t = get_time(ns)
    noise = (np.random.rand(ns) * 2 - 1).astype(np.float32) * 0.35
    sig = np.sin(2.0 * np.pi * freq * t) + noise
    sig *= np.exp(-t * decay)
    return np.tanh(1.4 * sig) * 0.45

wood_low = synth_wood(320.0, 40.0)
wood_mid = synth_wood(480.0, 50.0)
wood_high = synth_wood(720.0, 65.0)

# Active during Drop 1 (16-44) and Real Drop 2 (64-88)
for bar in range(NUM_BARS):
    if not ((16 <= bar < 44) or (64 <= bar < 88)):
        continue
    # 5 hits over 4 beats
    for hit in range(5):
        t_hit = bar * BAR_DUR + (hit * (BAR_DUR / 5.0))
        s_idx = int(t_hit * SAMPLE_RATE)
        buf = wood_mid if hit % 2 == 0 else wood_high
        e_idx = min(s_idx + len(buf), TOTAL_SAMPLES)
        slen = e_idx - s_idx
        pan = 0.3 if hit % 2 == 0 else 0.7
        perc_l[s_idx:e_idx] += buf[:slen] * (1.0 - pan)
        perc_r[s_idx:e_idx] += buf[:slen] * pan
        
    for hit3 in range(3):
        t_hit3 = bar * BAR_DUR + (hit3 * (BAR_DUR / 3.0)) + 0.12
        s_idx = int(t_hit3 * SAMPLE_RATE)
        e_idx = min(s_idx + len(wood_low), TOTAL_SAMPLES)
        slen = e_idx - s_idx
        perc_l[s_idx:e_idx] += wood_low[:slen] * 0.6
        perc_r[s_idx:e_idx] += wood_low[:slen] * 0.4

# -------------------------------------------------------------
# 3. IDM GLITCHES, BUFFER STUTTERS & BIT-DECIMATION
# -------------------------------------------------------------
print("-> Synthesizing IDM Glitches & Risers...")
gl_l, gl_r = stems["03_Glitch_Buffer_Stutter"]

for b in range(NUM_BARS):
    # Stutter fills at phrase ends
    if b in [15, 31, 43, 51, 58, 59, 83, 87]:
        t_stutter = b * BAR_DUR + 2.0 * BEAT_DUR
        s_idx = int(t_stutter * SAMPLE_RATE)
        st_len = int(2.0 * BEAT_DUR * SAMPLE_RATE)
        t_st = get_time(st_len)
        glitch_burst = np.sin(2.0 * np.pi * (440.0 + 800.0 * t_st**2) * t_st)
        glitch_burst = np.round(glitch_burst * 4.0) / 4.0 # 4-bit reduction
        e_idx = min(s_idx + st_len, TOTAL_SAMPLES)
        slen = e_idx - s_idx
        gl_l[s_idx:e_idx] += glitch_burst[:slen] * 0.35
        gl_r[s_idx:e_idx] += glitch_burst[:slen] * 0.45
    
    # Tension Riser in Bars 56-59 (leading into FAKE DROP)
    if 56 <= b < 60:
        t_rise = b * BAR_DUR
        s_r = int(t_rise * SAMPLE_RATE)
        r_len = int(BAR_DUR * SAMPLE_RATE)
        t_rz = get_time(r_len)
        prog = (b - 56 + t_rz / BAR_DUR) / 4.0
        sn_rate = 4.0 + 24.0 * prog # Rapid snare roll
        sn_click = (np.sin(2.0 * np.pi * sn_rate * t_rz) > 0.8).astype(np.float32)
        noise_rise = (np.random.rand(r_len) * 2 - 1).astype(np.float32) * (prog ** 1.5) * 0.30
        riser_sig = (sn_click * 0.25 + noise_rise) * prog
        e_r = min(s_r + r_len, TOTAL_SAMPLES)
        sl_r = e_r - s_r
        gl_l[s_r:e_r] += riser_sig[:sl_r] * 0.6
        gl_r[s_r:e_r] += riser_sig[:sl_r] * 0.6

# -------------------------------------------------------------
# 4. COSMIC INHARMONIC BELLS (Modal 11-Limit Chimes)
# -------------------------------------------------------------
print("-> Synthesizing Cosmic Inharmonic Bells (Modal 11-Limit Chimes)...")
bell_l, bell_r = stems["04_Cosmic_Bells_Chimes"]

def synth_bell(freq, dur=4.5):
    ns = int(dur * SAMPLE_RATE)
    t = get_time(ns)
    modes = [1.0, 2.76, 5.40, 8.93, 11.34] # Inharmonic modal ratios of tuned bar
    weights = [0.45, 0.28, 0.16, 0.08, 0.03]
    decays = [1.2, 2.4, 4.2, 6.8, 9.5]
    sig = np.zeros(ns, dtype=np.float32)
    for m, w, d in zip(modes, weights, decays):
        sig += w * np.sin(2.0 * np.pi * freq * m * t) * np.exp(-t * d)
    return sig * np.exp(-t * 0.4)

bells_E4 = [synth_bell(f) for f in SCALE_E4]
bells_E5 = [synth_bell(f) for f in SCALE_E5]

bell_bars = [b for b in range(NUM_BARS) if not ((44 <= b < 52) or (60 <= b < 64) or b >= 92)]
for bar in bell_bars:
    for hit in [0, 2, 3]:
        n_idx = (bar * 3 + hit) % len(SCALE_E4)
        oct_v = 4 if hit < 2 else 5
        t_hit = bar * BAR_DUR + hit * 1.333 * BEAT_DUR
        s_idx = int(t_hit * SAMPLE_RATE)
        if s_idx < TOTAL_SAMPLES:
            buf = bells_E4[n_idx] if oct_v == 4 else bells_E5[n_idx]
            e_idx = min(s_idx + len(buf), TOTAL_SAMPLES)
            slen = e_idx - s_idx
            p_l = 0.5 + 0.4 * math.sin(t_hit * 0.8)
            bell_l[s_idx:e_idx] += buf[:slen] * p_l * 0.75
            bell_r[s_idx:e_idx] += buf[:slen] * (1.0 - p_l) * 0.75

# -------------------------------------------------------------
# 5. COSMIC PADS & ANALOG SPACE DRONE
# -------------------------------------------------------------
print("-> Synthesizing Cosmic Pads & Analog Space Drones...")
pad_l, pad_r = stems["05_Cosmic_Pads_Drone"]

pad_chords = [
    [SCALE_E3[0], SCALE_E3[2], SCALE_E3[4], SCALE_E3[5]],
    [SCALE_E3[0], SCALE_E3[3], SCALE_E3[4], SCALE_E4[0]]
]

for bar in range(NUM_BARS):
    # Pads provide cosmic warmth throughout, including bridge and fake drop
    if (bar < 16) or (32 <= bar < 64) or (76 <= bar < 96):
        chord = pad_chords[(bar // 4) % 2]
        ns_pad = int(BAR_DUR * SAMPLE_RATE)
        t_pad = get_time(ns_pad)
        p_sig_l = np.zeros(ns_pad, dtype=np.float32)
        p_sig_r = np.zeros(ns_pad, dtype=np.float32)
        for note_f in chord:
            f1, f2 = note_f * 0.997, note_f * 1.003
            p_sig_l += (np.sin(2 * np.pi * f1 * t_pad) + 0.25 * np.sin(4 * np.pi * f1 * t_pad)) * 0.05
            p_sig_r += (np.sin(2 * np.pi * f2 * t_pad) + 0.25 * np.sin(4 * np.pi * f2 * t_pad)) * 0.05
        env_pad = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.linspace(0.0, 1.0, ns_pad, dtype=np.float32)))
        s_idx = int(bar * BAR_DUR * SAMPLE_RATE)
        e_idx = min(s_idx + ns_pad, TOTAL_SAMPLES)
        slen = e_idx - s_idx
        pad_l[s_idx:e_idx] += p_sig_l[:slen] * env_pad[:slen]
        pad_r[s_idx:e_idx] += p_sig_r[:slen] * env_pad[:slen]

# -------------------------------------------------------------
# 6. HI-HATS & SHAKERS GROOVE
# -------------------------------------------------------------
print("-> Synthesizing Offbeat Hats & Cosmic Shakers...")
hh_l, hh_r = stems["06_HiHats_Shakers_Groove"]

oh_len = int(0.22 * SAMPLE_RATE)
t_oh = get_time(oh_len)
oh_sig = (np.random.rand(oh_len) * 2 - 1).astype(np.float32) * np.exp(-t_oh * 18.0) * 0.25
sh_len = int(0.07 * SAMPLE_RATE)
t_sh = get_time(sh_len)
sh_sig = (np.random.rand(sh_len) * 2 - 1).astype(np.float32) * np.exp(-t_sh * 45.0) * 0.18

for bar in range(NUM_BARS):
    # Silent during Intro (0-12), Bridge (44-52), FAKE DROP (60-64), and final Outro (92-96)
    if bar < 12 or (44 <= bar < 52) or (60 <= bar < 64) or bar >= 92:
        continue
    for beat in range(4):
        t_oh_hit = bar * BAR_DUR + (beat + 0.5) * BEAT_DUR
        s_idx = int(t_oh_hit * SAMPLE_RATE)
        e_idx = min(s_idx + oh_len, TOTAL_SAMPLES)
        slen = e_idx - s_idx
        hh_l[s_idx:e_idx] += oh_sig[:slen] * 0.45
        hh_r[s_idx:e_idx] += oh_sig[:slen] * 0.55
        
        for st in range(4):
            t_sh_hit = bar * BAR_DUR + (beat + st * 0.25) * BEAT_DUR
            s_sh = int(t_sh_hit * SAMPLE_RATE)
            e_sh = min(s_sh + sh_len, TOTAL_SAMPLES)
            sl_sh = e_sh - s_sh
            hh_l[s_sh:e_sh] += sh_sig[:sl_sh] * 0.35
            hh_r[s_sh:e_sh] += sh_sig[:sl_sh] * 0.35

# -------------------------------------------------------------
# 7. PALMAS FLAMENCAS CON DUENDE (Sordas & Secas en Bulería Compás)
# -------------------------------------------------------------
print("-> Synthesizing Palmas Flamencas con Duende (Sordas & Secas)...")
palmas_l, palmas_r = stems["07_Palmas_Flamencas_Duende"]

def synthesize_palma(is_seca=False):
    dur = 0.045 if is_seca else 0.075
    ns = int(dur * SAMPLE_RATE)
    t = get_time(ns)
    noise = (np.random.rand(ns) * 2 - 1).astype(np.float32)
    if is_seca:
        env = np.exp(-t * 110.0)
        b, a = signal.butter(2, [1800.0 / (SAMPLE_RATE/2), 5200.0 / (SAMPLE_RATE/2)], btype='bandpass')
        body = signal.lfilter(b, a, noise)
        snap = np.sin(2 * np.pi * 2800.0 * t) * np.exp(-t * 220.0) * 0.45
        palma = (body * 0.8 + snap) * env
    else:
        env = np.exp(-t * 55.0)
        b, a = signal.butter(2, [400.0 / (SAMPLE_RATE/2), 850.0 / (SAMPLE_RATE/2)], btype='bandpass')
        body = signal.lfilter(b, a, noise)
        pop = np.sin(2 * np.pi * 520.0 * t) * np.exp(-t * 90.0) * 0.6
        palma = (body * 0.5 + pop) * env
    palma = np.tanh(palma * 2.2)
    return palma / (np.max(np.abs(palma)) + 1e-6)

p_seca = synthesize_palma(is_seca=True)
p_sorda = synthesize_palma(is_seca=False)

# Palmas active during:
# Section 2 (Bars 32-44)
# Build-up (Bars 52-59.5)
# REAL APOTHEOTIC DROP (Bars 64-84)
palmas_bars = [b for b in range(NUM_BARS) if (32 <= b < 44) or (52 <= b < 60) or (64 <= b < 84)]

for bar in palmas_bars:
    is_climax = (56 <= bar < 60) or (64 <= bar < 80)
    for step in range(16):
        # Bulería swing offset
        swing_offset = 0.012 if (step % 2 == 1) else 0.0
        step_time = bar * BAR_DUR + step * SIXTEENTH_DUR + swing_offset
        start_idx = int(step_time * SAMPLE_RATE)
        if start_idx >= TOTAL_SAMPLES:
            continue
        
        # Bulería accent points (steps 0, 4, 7, 10, 13)
        if step in [0, 4, 7, 10, 13]:
            p_buf = p_seca
            vol = 0.85 if is_climax else 0.70
            pan = 0.65
        elif step % 2 == 0:
            p_buf = p_sorda
            vol = 0.65 if is_climax else 0.50
            pan = 0.35
        elif is_climax:
            p_buf = p_sorda
            vol = 0.45
            pan = 0.50
        else:
            continue
            
        end_idx = min(start_idx + len(p_buf), TOTAL_SAMPLES)
        slen = end_idx - start_idx
        palmas_l[start_idx:end_idx] += p_buf[:slen] * vol * (1.0 - pan)
        palmas_r[start_idx:end_idx] += p_buf[:slen] * vol * pan

# -------------------------------------------------------------
# 8. VOCES & COROS EN ARMONIA NEGATIVA (Mitxu Quejío & Ernst Levy Axis)
# -------------------------------------------------------------
print("-> Synthesizing Negative Harmony Vocal Choruses & Flamenco Quejío...")
vx_l, vx_r = stems["08_Voces_Coros_Negative_Harmony"]

def prep_vocal(path):
    if not path.exists():
        return None
    raw, sr = sf.read(str(path))
    if raw.ndim > 1:
        raw = raw[:, 0]
    num_s = int(len(raw) * SAMPLE_RATE / sr)
    res = signal.resample(raw, num_s).astype(np.float32)
    b_hp, a_hp = signal.butter(2, 140.0 / (SAMPLE_RATE / 2.0), btype='highpass')
    res = signal.lfilter(b_hp, a_hp, res)
    return res / (np.max(np.abs(res)) + 1e-6)

v_quejio = prep_vocal(MITXU_QUEJIO_PATH)
v_minu = prep_vocal(MITXU_MINU_PATH)
v_cantic = prep_vocal(MITXU_CANTIC_PATH)
v_papara = prep_vocal(MITXU_PAPARA_PATH)

def synth_negative_choir(vocal_sig):
    if vocal_sig is None:
        return np.zeros(100, dtype=np.float32), np.zeros(100, dtype=np.float32)
    choir_ratios = [
        (1.0, 0.75, 0.50),         # Lead E
        (1.5, 0.60, 0.15),         # Negative 5th (B)
        (1.20, 0.60, 0.85),        # Negative minor 3rd (G)
        (4.0/3.0, 0.50, 0.30),     # Negative 4th (A)
        (12.0/11.0, 0.45, 0.70)    # Negative undecimal (12/11)
    ]
    max_len = int(len(vocal_sig) * 1.5)
    ch_l = np.zeros(max_len, dtype=np.float32)
    ch_r = np.zeros(max_len, dtype=np.float32)
    for r, gain, pan in choir_ratios:
        target_len = max(10, int(len(vocal_sig) / r))
        shifted = signal.resample(vocal_sig, target_len).astype(np.float32)
        slen = min(len(shifted), max_len)
        ch_l[:slen] += shifted[:slen] * gain * (1.0 - pan)
        ch_r[:slen] += shifted[:slen] * gain * pan
    b_ch, a_ch = signal.butter(2, [200.0 / (SAMPLE_RATE/2), 6500.0 / (SAMPLE_RATE/2)], btype='bandpass')
    ch_l = signal.lfilter(b_ch, a_ch, ch_l)
    ch_r = signal.lfilter(b_ch, a_ch, ch_r)
    pk = max(np.max(np.abs(ch_l)), np.max(np.abs(ch_r))) + 1e-6
    return ch_l / pk, ch_r / pk

ch_quejio_l, ch_quejio_r = synth_negative_choir(v_quejio)
ch_cantic_l, ch_cantic_r = synth_negative_choir(v_cantic)
ch_minu_l, ch_minu_r = synth_negative_choir(v_minu)
ch_papara_l, ch_papara_r = synth_negative_choir(v_papara)

choir_schedule = [
    (18.0 * BAR_DUR, ch_minu_l, ch_minu_r, 0.65),
    (26.0 * BAR_DUR, ch_cantic_l, ch_cantic_r, 0.70),
    (34.0 * BAR_DUR, ch_papara_l, ch_papara_r, 0.75),
    # Duende Breakdown (Bars 44-52): Mitxu Flamenco Quejío Centerpiece
    (44.5 * BAR_DUR, ch_quejio_l, ch_quejio_r, 0.95),
    (48.5 * BAR_DUR, ch_cantic_l, ch_cantic_r, 0.85),
    # REAL DROP APOTHEOSIS (Bars 64-84)
    (64.0 * BAR_DUR, ch_quejio_l, ch_quejio_r, 1.00),
    (70.0 * BAR_DUR, ch_minu_l, ch_minu_r, 0.85),
    (76.0 * BAR_DUR, ch_papara_l, ch_papara_r, 0.80),
    (84.0 * BAR_DUR, ch_cantic_l, ch_cantic_r, 0.70)
]

for t_hit, cl, cr, vol in choir_schedule:
    s_idx = int(t_hit * SAMPLE_RATE)
    if s_idx >= TOTAL_SAMPLES:
        continue
    e_idx = min(s_idx + len(cl), TOTAL_SAMPLES)
    slen = e_idx - s_idx
    vx_l[s_idx:e_idx] += cl[:slen] * vol
    vx_r[s_idx:e_idx] += cr[:slen] * vol

# Roland Space Echo Delay on Vocals
vx_del_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
vx_del_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
d_vx_samples = int(0.75 * BEAT_DUR * SAMPLE_RATE) # 375ms

for n in range(TOTAL_SAMPLES):
    if n - d_vx_samples >= 0:
        vx_del_l[n] = vx_l[n] * 0.40 + vx_del_r[n - d_vx_samples] * 0.48
        vx_del_r[n] = vx_r[n] * 0.40 + vx_del_l[n - d_vx_samples] * 0.48

b_vxd, a_vxd = signal.butter(2, 3000.0 / (SAMPLE_RATE / 2.0), btype='lowpass')
vx_del_l = signal.lfilter(b_vxd, a_vxd, vx_del_l)
vx_del_r = signal.lfilter(b_vxd, a_vxd, vx_del_r)
vx_l += vx_del_l * 0.55
vx_r += vx_del_r * 0.55

# -------------------------------------------------------------
# 9. ERUCTOS DE ALAIN CON DUB DELAY BARRAGE (Including the Fake-Drop Marker!)
# -------------------------------------------------------------
print("-> Synthesizing Alain Eructos Dub Delay Barrage...")
er_l, er_r = stems["09_Eructos_Dub_Delay_Barrage"]

alain_eructo_raw, a_sr = sf.read(str(ALAIN_ERUCTO_PATH))
if alain_eructo_raw.ndim > 1:
    alain_eructo_raw = alain_eructo_raw[:, 0]
alain_res = signal.resample(alain_eructo_raw, int(len(alain_eructo_raw) * SAMPLE_RATE / a_sr)).astype(np.float32)
alain_res /= (np.max(np.abs(alain_res)) + 1e-6)

def synth_burp(pitch_hz, dur, seed=123):
    ns = int(dur * SAMPLE_RATE)
    t = get_time(ns)
    np.random.seed(seed)
    train = np.zeros(ns, dtype=np.float32)
    cur = 100
    while cur < ns - 200:
        per = int(SAMPLE_RATE / np.random.uniform(pitch_hz * 0.8, pitch_hz * 1.2))
        p_len = min(int(0.010 * SAMPLE_RATE), ns - cur)
        pt = np.arange(p_len) / SAMPLE_RATE
        pop = np.sin(2 * np.pi * pitch_hz * pt) * np.exp(-pt * 300.0)
        click = (np.random.rand(p_len) * 2 - 1) * np.exp(-pt * 500.0) * 0.6
        train[cur:cur+p_len] += pop + click
        cur += per
    env = np.exp(-t * (4.0 / dur))
    b, a = signal.butter(2, [350.0 / (SAMPLE_RATE/2), 1600.0 / (SAMPLE_RATE/2)], btype='bandpass')
    sig = signal.lfilter(b, a, train * env)
    return np.tanh(2.5 * sig) / (np.max(np.abs(sig)) + 1e-6)

burp_short = synth_burp(55.0, 0.35, 101)
burp_deep = synth_burp(38.0, 0.85, 202)
burp_high = synth_burp(75.0, 0.50, 303)

# Eructo Placement including the critical FAKE DROP lonely belch at Bar 61!
burp_schedule = [
    (8, 2.5, burp_short, 0.70, 0.2),
    (14, 3.5, burp_deep, 0.80, 0.8),
    (20, 1.0, burp_high, 0.65, 0.4),
    (28, 3.75, alain_res, 0.90, 0.6),
    (38, 2.0, burp_short, 0.75, 0.7),
    (42, 3.0, burp_deep, 0.85, 0.3),
    (50, 2.5, alain_res, 0.95, 0.5), # Pre-build marker
    # ─── EL FALSO DROP MARKER (BAR 61: Total Silence Except This Subterranean Belch!) ───
    (61, 1.0, alain_res, 1.00, 0.5), # Lonely dub delay belch in zero-G
    (63, 3.0, burp_short, 0.80, 0.5), # Pre-real-drop trigger
    # Real Drop Barrage
    (68, 2.5, burp_deep, 0.90, 0.2),
    (74, 1.5, burp_high, 0.85, 0.8),
    (80, 3.0, alain_res, 0.95, 0.5),
    (86, 2.0, burp_deep, 0.85, 0.4),
    (92, 1.0, alain_res, 0.80, 0.5)  # Outro farewell
]

for b_num, b_beat, b_buf, vol, pan in burp_schedule:
    t_start = b_num * BAR_DUR + b_beat * BEAT_DUR
    s_idx = int(t_start * SAMPLE_RATE)
    if s_idx >= TOTAL_SAMPLES:
        continue
    e_idx = min(s_idx + len(b_buf), TOTAL_SAMPLES)
    slen = e_idx - s_idx
    er_l[s_idx:e_idx] += b_buf[:slen] * vol * (1.0 - pan)
    er_r[s_idx:e_idx] += b_buf[:slen] * vol * pan

# Roland Space Echo Dub Delay on Eructos
d_samples = int(0.75 * BEAT_DUR * SAMPLE_RATE) # 375ms
er_del_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
er_del_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

for n in range(TOTAL_SAMPLES):
    if n - d_samples >= 0:
        er_del_l[n] = er_l[n] * 0.45 + er_del_r[n - d_samples] * 0.55
        er_del_r[n] = er_r[n] * 0.45 + er_del_l[n - d_samples] * 0.55

b_lp, a_lp = signal.butter(2, 2800.0 / (SAMPLE_RATE / 2.0), btype='lowpass')
er_del_l = signal.lfilter(b_lp, a_lp, er_del_l)
er_del_r = signal.lfilter(b_lp, a_lp, er_del_r)
er_l += er_del_l * 0.70
er_r += er_del_r * 0.70

# -------------------------------------------------------------
# 10. ATMOSPHERIC COSMIC TEXTURES & STELLAR NOISE
# -------------------------------------------------------------
print("-> Synthesizing Stellar Wind & Cosmic Textures...")
tx_l, tx_r = stems["10_Atmospheric_Cosmic_Textures"]

stellar_noise = (np.random.rand(TOTAL_SAMPLES) * 2 - 1).astype(np.float32)
b_tx, a_tx = signal.butter(2, [30.0 / (SAMPLE_RATE/2), 220.0 / (SAMPLE_RATE/2)], btype='bandpass')
rumble = signal.lfilter(b_tx, a_tx, stellar_noise) * 0.12
b_sh, a_sh = signal.butter(2, [6000.0 / (SAMPLE_RATE/2), 12000.0 / (SAMPLE_RATE/2)], btype='bandpass')
shimmer = signal.lfilter(b_sh, a_sh, stellar_noise) * 0.04
tx_l[:] = rumble + shimmer * 0.8
tx_r[:] = rumble + shimmer * 1.2

# -------------------------------------------------------------
# 11. ALAIN VOCODER ITALO DARK (Alain Voice Modulator + 16-Band Filter Bank + Rolling Saw Bass)
# -------------------------------------------------------------
print("-> Synthesizing Alain Italo Dark Vocoder (Alain Voice Modulator & Moroder Rolling Bass)...")
voc_l, voc_r = stems["11_Alain_Vocoder_Italo_Dark"]

# A. Rolling 16th-Note Moroder / Italo Dark Bassline (Bars 0-16, Bars 32-44, Bars 64-88)
italo_bass_len = int(0.125 * SAMPLE_RATE)
t_ib = get_time(italo_bass_len)
env_ib = np.exp(-t_ib * 22.0)

bass_active_bars = [b for b in range(NUM_BARS) if (b < 16) or (32 <= b < 44) or (64 <= b < 88)]
for b in bass_active_bars:
    for s16 in range(16):
        t_hit = b * BAR_DUR + s16 * SIXTEENTH_DUR
        s_idx = int(t_hit * SAMPLE_RATE)
        e_idx = min(s_idx + italo_bass_len, TOTAL_SAMPLES)
        slen = e_idx - s_idx
        if s16 % 4 == 0:
            f_bass = 41.203 # E1
        elif s16 % 4 == 2:
            f_bass = 82.407 # E2
        elif s16 % 4 == 1:
            f_bass = 61.735 # B1
        else:
            f_bass = 48.999 # G1
        saw_raw = (2.0 * (t_ib[:slen] * f_bass - np.floor(t_ib[:slen] * f_bass + 0.5))).astype(np.float32)
        fc_sweep = 380.0 + ((b % 8) / 8.0) * 1100.0
        b_ib, a_ib = signal.butter(2, min(0.48, fc_sweep / (SAMPLE_RATE / 2.0)), btype='lowpass')
        bass_note = signal.lfilter(b_ib, a_ib, saw_raw * env_ib[:slen]) * 0.48
        voc_l[s_idx:e_idx] += bass_note * 0.5
        voc_r[s_idx:e_idx] += bass_note * 0.5

# B. Alain 16-Band Vocoder Engine
def vocode_audio_segment(speech_sig, dur_s, chord_freqs):
    ns = int(dur_s * SAMPLE_RATE)
    t = get_time(ns)
    modulator = signal.resample(speech_sig, ns).astype(np.float32)
    modulator /= (np.max(np.abs(modulator)) + 1e-6)
    
    # Carrier: Detuned Saw Chords in E Negative Harmony
    carrier = np.zeros(ns, dtype=np.float32)
    for f in chord_freqs:
        for det in [0.995, 1.0, 1.005]:
            phase = 2.0 * np.pi * (f * det) * t
            for h in range(1, 15):
                carrier += (1.0 / h) * np.sin(h * phase) * 0.04
                
    bands = np.geomspace(160, 5600, 17)
    v_out_l = np.zeros(ns, dtype=np.float32)
    v_out_r = np.zeros(ns, dtype=np.float32)
    b_env, a_env = signal.butter(1, 38.0 / (SAMPLE_RATE/2), btype='lowpass')
    
    for i in range(16):
        f_low, f_high = bands[i], bands[i+1]
        b_bk, a_bk = signal.butter(2, [f_low / (SAMPLE_RATE/2), f_high / (SAMPLE_RATE/2)], btype='bandpass')
        m_band = signal.lfilter(b_bk, a_bk, modulator)
        m_env = signal.lfilter(b_env, a_env, np.abs(m_band))
        c_band = signal.lfilter(b_bk, a_bk, carrier)
        pan = i / 15.0
        v_out_l += c_band * m_env * (1.1 - pan * 0.5)
        v_out_r += c_band * m_env * (0.6 + pan * 0.5)
        
    pk = max(np.max(np.abs(v_out_l)), np.max(np.abs(v_out_r))) + 1e-6
    return (v_out_l / pk) * 0.85, (v_out_r / pk) * 0.85

v_alain_hostia = prep_vocal(ALAIN_HOSTIA_PATH)
v_alain_bombo = prep_vocal(ALAIN_BOMBO_PATH)
v_alain_exergia = prep_vocal(ALAIN_EXERGIA_PATH)

# Synthesize Alain Vocoded Phrases
# Chords in E Negative Harmony: E2, B2, G3, D4, C4
ch_e_neg = [82.41, 123.47, 164.81, 196.00, 261.63]
ch_c_neg = [65.41, 98.00, 130.81, 164.81, 196.00]

voc_hostia_l, voc_hostia_r = vocode_audio_segment(v_alain_hostia, 7.0, ch_e_neg)
voc_bombo_l, voc_bombo_r = vocode_audio_segment(v_alain_bombo, 8.5, ch_c_neg)
voc_exergia_l, voc_exergia_r = vocode_audio_segment(v_alain_exergia, 9.0, ch_e_neg)

# Placement of Alain Vocoder throughout the 96-bar structure
alain_voc_schedule = [
    # 1. Intro (Bars 2 to 9): Alain introduces the cosmic Italo track
    (2.0 * BAR_DUR, voc_hostia_l, voc_hostia_r, 0.90),
    (9.0 * BAR_DUR, voc_exergia_l, voc_exergia_r, 0.85),
    # 2. Section 2 Duende (Bars 34 to 42): Alain talks about the bombo & stems
    (34.0 * BAR_DUR, voc_bombo_l, voc_bombo_r, 0.90),
    # 3. Pre-Drop Build-up (Bars 53 to 59): "¡Se viene la hostia!"
    (53.0 * BAR_DUR, voc_hostia_l, voc_hostia_r, 1.00),
    # 4. FAKE DROP WHISPER (Bar 60.5): Alain whispers in the zero-gravity void!
    (60.2 * BAR_DUR, voc_exergia_l[:int(3.0 * SAMPLE_RATE)], voc_exergia_r[:int(3.0 * SAMPLE_RATE)], 0.70),
    # 5. REAL APOTHEOTIC DROP (Bars 64 to 73): Alain shouting in the real drop!
    (64.0 * BAR_DUR, voc_bombo_l, voc_bombo_r, 1.00),
    (74.0 * BAR_DUR, voc_hostia_l, voc_hostia_r, 0.95),
    # 6. Outro (Bars 86 to 94): Farewell transmission
    (86.0 * BAR_DUR, voc_exergia_l, voc_exergia_r, 0.80)
]

for t_hit, vl, vr, vol in alain_voc_schedule:
    s_idx = int(t_hit * SAMPLE_RATE)
    if s_idx >= TOTAL_SAMPLES:
        continue
    e_idx = min(s_idx + len(vl), TOTAL_SAMPLES)
    slen = e_idx - s_idx
    voc_l[s_idx:e_idx] += vl[:slen] * vol
    voc_r[s_idx:e_idx] += vr[:slen] * vol

# Ping-Pong Space Delay on Alain Vocoder
d_voc_samples = int(0.375 * SAMPLE_RATE) # Dotted 8th
voc_del_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
voc_del_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

for n in range(TOTAL_SAMPLES):
    if n - d_voc_samples >= 0:
        voc_del_l[n] = voc_l[n] * 0.35 + voc_del_r[n - d_voc_samples] * 0.45
        voc_del_r[n] = voc_r[n] * 0.35 + voc_del_l[n - d_voc_samples] * 0.45

b_vlp, a_vlp = signal.butter(2, 3200.0 / (SAMPLE_RATE / 2.0), btype='lowpass')
voc_del_l = signal.lfilter(b_vlp, a_vlp, voc_del_l)
voc_del_r = signal.lfilter(b_vlp, a_vlp, voc_del_r)
voc_l += voc_del_l * 0.50
voc_r += voc_del_r * 0.50

# -------------------------------------------------------------
# WRITE DISCRETE STEMS (11 STEMS)
# -------------------------------------------------------------
print("-> Exporting 11 Discrete High-Fidelity WAV Stems...")
def write_stereo_wav(filepath: Path, l_arr: np.ndarray, r_arr: np.ndarray):
    interleaved = np.empty((TOTAL_SAMPLES * 2,), dtype=np.int16)
    l_16 = np.clip(l_arr * 32767.0, -32768.0, 32767.0).astype(np.int16)
    r_16 = np.clip(r_arr * 32767.0, -32768.0, 32767.0).astype(np.int16)
    interleaved[0::2] = l_16
    interleaved[1::2] = r_16
    with wave.open(str(filepath), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(interleaved.tobytes())

# Clean directory first
for old_f in STEMS_DIR.glob("*.wav"):
    old_f.unlink()

for stem_name, (sl, sr) in stems.items():
    stem_path = STEMS_DIR / f"{stem_name}.wav"
    write_stereo_wav(stem_path, sl, sr)
    print(f"   [Stem] {stem_path.name} written ({stem_path.stat().st_size / (1024*1024):.2f} MB)")

# -------------------------------------------------------------
# MASTER MIX & SOVEREIGN LIMITING
# -------------------------------------------------------------
print("-> Summing Full Multitrack Mix & Applying Sovereign Mastering...")
master_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
master_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

for stem_name, (sl, sr) in stems.items():
    master_l += sl
    master_r += sr

peak_l = np.max(np.abs(master_l))
peak_r = np.max(np.abs(master_r))
max_peak = max(peak_l, peak_r)
print(f"Pre-master peak level: {max_peak:.3f}")

if max_peak > 0.001:
    drive = 1.05 / max_peak
    master_l = np.tanh(master_l * drive) * 0.96
    master_r = np.tanh(master_r * drive) * 0.96

write_stereo_wav(OUTPUT_WAV, master_l, master_r)
print(f"✅ WAV Master successfully generated: {OUTPUT_WAV} ({OUTPUT_WAV.stat().st_size / (1024*1024):.2f} MB)")

# Encode MP3
print("-> Encoding MP3 (320 kbps CBR)...")
try:
    subprocess.run([
        'ffmpeg', '-y', '-i', str(OUTPUT_WAV),
        '-codec:a', 'libmp3lame', '-b:a', '320k',
        str(OUTPUT_MP3)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✅ MP3 Exported: {OUTPUT_MP3} ({OUTPUT_MP3.stat().st_size / (1024*1024):.2f} MB)")
except Exception as e:
    print(f"Notice: MP3 encoding skipped: {e}")

# -------------------------------------------------------------
# COMPILE NATIVE FL STUDIO PROJECT (.flp)
# -------------------------------------------------------------
print("-> Compiling Native FL Studio Project (.flp)...")
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    res = compile_multitrack_stems_flp(
        stems_dir=str(STEMS_DIR),
        project_title="Cosmic Microtonal Glitch & Duende Session (Extended Alain Vocoder)",
        bpm=BPM,
        output_flp=str(OUTPUT_FLP)
    )
    print(f"✅ Native FLP Project Compiled: {OUTPUT_FLP} ({OUTPUT_FLP.stat().st_size / 1024:.1f} KB)")
except Exception as e:
    print(f"Notice: FLP compiler note: {e}")

print("=== All Extended Cosmic Production Assets Successfully Built and Centralized ===")
