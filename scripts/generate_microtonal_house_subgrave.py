#!/usr/bin/env python3
"""
Sovereign Microtonal House Synthesizer — C5-REAL Pure DSP Engine (v4.0 Full Masterpiece)
════════════════════════════════════════════════════════════════════════════════════════
Generates a complete, high-fidelity Organic / Afro-Melodic Microtonal Deep House track:
- Tempo: 124 BPM
- Subgrave Potente: 36.7Hz - 50Hz sub-bass with tanh saturation and kick sidechain ducking.
- Microtonal Scale: 24-EDO Maqam Bayati on D (featuring neutral 2nd @ 150 cents & neutral 6th @ 850 cents).
- Timbales: Afro-Latin membrane & shell cáscara synthesis with fills, rolls and syncopations.
- Xilófonos: Physical modeling of rosewood bar xylophones playing microtonal arpeggios.
- Pandeletas: Brass jingle tambourine groove with house shuffle swing and hand strikes on beats 2 & 4.
- House Drums: 909-style punch kick, offbeat open hats, claps, and organic shakers.
- PALMAS FLAMENCAS: Sordas (muffled 520Hz) and Secas (crisp 2.8kHz/4.8kHz) with bulería swing.
- ERUCTO DE ALAIN CON DUB DELAY: Esophageal guttural belch in Alain's tone + trailing 'la hostia tú' with ping-pong tape delay.
- VOZ DE MITXU (FLAMENCO & COROS): Quejío flamenco + cántico + coros "¡Michu, michu, michu, minuuuuu! ¡Olé!".
- Multitrack Stems: 10 discrete stems exported to ~/Music/Synthesized_Stems/Microtonal_House/.
- FL Studio Project (.flp): Compiled binary project with all 10 channel stem routings.
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
OUTPUT_WAV = MUSIC_DIR / "MICROTONAL_HOUSE_SUBGRAVE_TIMBALES_XILOFONOS.wav"
OUTPUT_MP3 = MUSIC_DIR / "MICROTONAL_HOUSE_SUBGRAVE_TIMBALES_XILOFONOS.mp3"
STEMS_DIR = MUSIC_DIR / "Synthesized_Stems" / "Microtonal_House"
PROJECTS_DIR = MUSIC_DIR / "FL Studio Bounces" / "Projects"
OUTPUT_FLP = PROJECTS_DIR / "Microtonal_House_Subgrave_Session.flp"

MITXU_QUEJIO_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Mitxu" / "cloned_generations" / "mitxu_flamenco_quejio_buleria.wav"
MITXU_CHANT_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Mitxu" / "cloned_generations" / "real_mitxu_acento_vasco" / "mitxu_vasco_lolololo_cantic.wav"
MITXU_MINU_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Mitxu" / "cloned_generations" / "mitxu_michu_minu_coros.wav"
ALAIN_ERUCTO_PATH = MUSIC_DIR / "LIBRARY" / "03-IA" / "Voice_Clones" / "WhatsApp" / "Alain" / "cloned_generations" / "alain_eructo_gutural_la_hostia.wav"

STEMS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100
BPM = 124.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4.0
SIXTEENTH_DUR = BEAT_DUR / 4.0
NUM_BARS = 64
TOTAL_DURATION = BAR_DUR * NUM_BARS
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

print(f"=== Synthesizing Microtonal House Masterpiece (10 Stems + Alain Eructo + Mitxu Minu) ===")
print(f"Duration: {TOTAL_DURATION:.2f}s ({NUM_BARS} bars @ {BPM} BPM)")
print(f"Total Samples: {TOTAL_SAMPLES} @ {SAMPLE_RATE} Hz")

ROOT_FREQ_D3 = 146.832
BAYATI_CENTS = [0.0, 150.0, 300.0, 500.0, 700.0, 850.0, 1000.0]

def cents_to_freq(root_freq, cents):
    return root_freq * (2.0 ** (cents / 1200.0))

SCALE_D3 = [cents_to_freq(ROOT_FREQ_D3, c) for c in BAYATI_CENTS]
SCALE_D4 = [f * 2.0 for f in SCALE_D3]
SCALE_D5 = [f * 4.0 for f in SCALE_D3]

def get_time(n_samples):
    return np.arange(n_samples, dtype=np.float32) / SAMPLE_RATE

# Stem Buffers (Left and Right)
stems = {
    "01_Kick_909": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "02_Subgrave_Potente": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "03_Pandeletas_House": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "04_Timbales_Latinos": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "05_Xilofonos_Bayati": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "06_Hats_Claps": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "07_Pads_Atmosphere": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "08_Voz_Mitxu_Flamenco": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "09_Palmas_Flamencas": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32)),
    "10_Eructo_Alain_Dub_Delay": (np.zeros(TOTAL_SAMPLES, dtype=np.float32), np.zeros(TOTAL_SAMPLES, dtype=np.float32))
}

# -------------------------------------------------------------
# 1. 909-STYLE PUNCH KICK (4-on-the-floor)
# -------------------------------------------------------------
print("-> Synthesizing 909 House Kick...")
kick_dur = 0.32
kick_samples = int(kick_dur * SAMPLE_RATE)
t_k = get_time(kick_samples)
f_k_start, f_k_end, k_sweep = 150.0, 46.0, 36.0
phase_k = 2.0 * np.pi * (f_k_end * t_k + ((f_k_start - f_k_end) / k_sweep) * (1.0 - np.exp(-k_sweep * t_k)))
env_k = np.exp(-t_k * 11.5)
click_k = 0.4 * np.sin(2.0 * np.pi * 1800.0 * t_k) * np.exp(-t_k * 140.0)
kick_waveform = np.tanh(1.8 * (np.sin(phase_k) + click_k)) * env_k * 0.85

kick_bars = [b for b in range(NUM_BARS) if not (b < 4 or (32 <= b < 40) or b >= 60)]
k_l, k_r = stems["01_Kick_909"]

for bar in kick_bars:
    for beat in range(4):
        start_idx = int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE)
        end_idx = min(start_idx + kick_samples, TOTAL_SAMPLES)
        length = end_idx - start_idx
        k_l[start_idx:end_idx] += kick_waveform[:length]
        k_r[start_idx:end_idx] += kick_waveform[:length]

# -------------------------------------------------------------
# 2. SUBGRAVE POTENTE (Deep House Sub-Bass with Sidechain)
# -------------------------------------------------------------
print("-> Synthesizing Potent Sub-Bass (36.7Hz - 50Hz) with Sidechain Ducking...")
SUB_ROOTS = {
    'D': 36.712,
    'E_hf': cents_to_freq(36.712, 150.0), # 40.03 Hz
    'F': cents_to_freq(36.712, 300.0),    # 43.65 Hz
    'G': cents_to_freq(36.712, 500.0),    # 48.99 Hz
    'C': cents_to_freq(36.712, 1000.0)    # 65.41 Hz
}

sub_pattern_A = [
    (0, 'D', 0.9, 1.8),
    (3, 'D', 0.8, 1.2),
    (6, 'E_hf', 0.85, 1.4),
    (10, 'F', 0.9, 1.5),
    (14, 'D', 0.75, 1.0)
]
sub_pattern_B = [
    (0, 'D', 0.9, 1.8),
    (3, 'G', 0.85, 1.2),
    (6, 'F', 0.85, 1.4),
    (10, 'E_hf', 0.9, 1.5),
    (13, 'C', 0.7, 1.0),
    (15, 'D', 0.8, 1.0)
]

sub_bars = [b for b in range(NUM_BARS) if (8 <= b < 32) or (36 <= b < 60)]
sub_l, sub_r = stems["02_Subgrave_Potente"]

for bar in sub_bars:
    pattern = sub_pattern_B if (bar % 4 == 3) else sub_pattern_A
    bridge_factor = 0.65 if (36 <= bar < 40) else 1.0
    
    for step, note_key, vel, dur_steps in pattern:
        f_sub = SUB_ROOTS[note_key]
        t_note_start = bar * BAR_DUR + step * SIXTEENTH_DUR
        dur_sec = dur_steps * SIXTEENTH_DUR * 1.05
        note_samples = int(dur_sec * SAMPLE_RATE)
        t_sub = get_time(note_samples)

        osc1 = np.sin(2.0 * np.pi * f_sub * t_sub)
        osc2 = 0.45 * np.sin(4.0 * np.pi * f_sub * t_sub)
        osc3 = 0.20 * np.sin(6.0 * np.pi * f_sub * t_sub)
        raw_sub = np.tanh(1.6 * (osc1 + osc2 + osc3))

        att = int(0.008 * SAMPLE_RATE)
        rel = int(0.04 * SAMPLE_RATE)
        env = np.ones(note_samples, dtype=np.float32)
        if att > 0 and att < note_samples:
            env[:att] = np.linspace(0.0, 1.0, att)
        if rel > 0 and rel < note_samples:
            env[-rel:] = np.linspace(1.0, 0.0, rel)

        sub_sig = raw_sub * env * vel * 0.62 * bridge_factor

        start_idx = int(t_note_start * SAMPLE_RATE)
        end_idx = min(start_idx + note_samples, TOTAL_SAMPLES)
        length = end_idx - start_idx

        sub_chunk = sub_sig[:length].copy()
        if not (32 <= bar < 40):
            for i_s in range(length):
                global_sample = start_idx + i_s
                sample_in_beat = global_sample % int(BEAT_DUR * SAMPLE_RATE)
                t_since_kick = sample_in_beat / SAMPLE_RATE
                if t_since_kick < 0.22:
                    duck = 1.0 - 0.88 * np.exp(-t_since_kick * 26.0)
                    sub_chunk[i_s] *= duck

        sub_l[start_idx:end_idx] += sub_chunk
        sub_r[start_idx:end_idx] += sub_chunk

# -------------------------------------------------------------
# 3. PANDELETAS (Tambourine / Jingles with House Swing)
# -------------------------------------------------------------
print("-> Synthesizing Brass Pandeletas (Tambourines with House Swing)...")
jingle_freqs = [4750.0, 6100.0, 7850.0, 9600.0, 11400.0, 13700.0]
pandeleta_dur = 0.16
p_samples = int(pandeleta_dur * SAMPLE_RATE)
t_p = get_time(p_samples)

jingle_osc = np.zeros(p_samples, dtype=np.float32)
for jf in jingle_freqs:
    jingle_osc += 0.16 * np.sin(2.0 * np.pi * jf * t_p)
noise_p = (np.random.rand(p_samples).astype(np.float32) * 2.0 - 1.0)
env_p_shake = np.exp(-t_p * 35.0) + 0.3 * np.exp(-t_p * 14.0)
pandeleta_shake = (noise_p * 0.6 + jingle_osc * 0.4) * env_p_shake * 0.32

env_p_hit = np.exp(-t_p * 22.0)
pandeleta_hit = (noise_p * 0.7 + jingle_osc * 0.5) * env_p_hit * 0.48

swing_offset = 0.015 * BEAT_DUR
pan_l_buf, pan_r_buf = stems["03_Pandeletas_House"]

for bar in range(NUM_BARS):
    if bar < 2 or (58 <= bar < 62):
        continue
    p_vol = 0.5 if (32 <= bar < 36) else 1.0
    
    for step in range(16):
        is_swing = (step % 2 == 1)
        step_time = bar * BAR_DUR + step * SIXTEENTH_DUR + (swing_offset if is_swing else 0.0)
        start_idx = int(step_time * SAMPLE_RATE)
        if start_idx >= TOTAL_SAMPLES:
            break
        
        if step in [4, 12]:
            sig = pandeleta_hit * p_vol
            pan_l, pan_r = 0.65, 0.35
        elif step % 4 == 2:
            sig = pandeleta_shake * 1.2 * p_vol
            pan_l, pan_r = 0.45, 0.55
        else:
            sig = pandeleta_shake * 0.6 * p_vol
            pan_l, pan_r = 0.5, 0.5

        end_idx = min(start_idx + p_samples, TOTAL_SAMPLES)
        length = end_idx - start_idx
        pan_l_buf[start_idx:end_idx] += sig[:length] * pan_l
        pan_r_buf[start_idx:end_idx] += sig[:length] * pan_r

# -------------------------------------------------------------
# 4. TIMBALES LATINOS (Membrane, Shell Cáscara & Fills)
# -------------------------------------------------------------
print("-> Synthesizing Latin Timbales (Membrane, Shell Cáscara & Fills)...")
timbal_modes = [1.0, 1.58, 2.14, 2.30, 2.92]

def synthesize_timbal_strike(f0, dur=0.28, is_rim=False):
    ns = int(dur * SAMPLE_RATE)
    t = get_time(ns)
    sig = np.zeros(ns, dtype=np.float32)
    for m_idx, m in enumerate(timbal_modes):
        mode_f = f0 * m
        if mode_f > 18000:
            continue
        decay = 18.0 + m_idx * 12.0
        amp = 1.0 / (m_idx + 1.0) ** 0.8
        sig += amp * np.sin(2.0 * np.pi * mode_f * t) * np.exp(-t * decay)
    if is_rim:
        noise = (np.random.rand(ns).astype(np.float32) * 2.0 - 1.0)
        stick = noise * np.exp(-t * 90.0) * 0.7
        sig = sig * 0.5 + stick
    return np.tanh(sig * 1.4) * np.exp(-t * 12.0)

timbal_macho = synthesize_timbal_strike(280.0, dur=0.25, is_rim=False)
timbal_hembra = synthesize_timbal_strike(195.0, dur=0.35, is_rim=False)
timbal_rim_macho = synthesize_timbal_strike(280.0, dur=0.18, is_rim=True)
timbal_rim_hembra = synthesize_timbal_strike(195.0, dur=0.22, is_rim=True)

cascara_samples = int(0.08 * SAMPLE_RATE)
t_cas = get_time(cascara_samples)
cascara_stick = (np.sin(2.0 * np.pi * 3200.0 * t_cas) * 0.4 +
                 np.sin(2.0 * np.pi * 1450.0 * t_cas) * 0.6) * np.exp(-t_cas * 85.0)

cascara_steps = [0, 2, 3, 6, 8, 10, 11, 14]
timbal_bars = [b for b in range(NUM_BARS) if (4 <= b < 32) or (36 <= b < 62)]
timb_l, timb_r = stems["04_Timbales_Latinos"]

for bar in timbal_bars:
    for step in cascara_steps:
        step_t = bar * BAR_DUR + step * SIXTEENTH_DUR
        start_idx = int(step_t * SAMPLE_RATE)
        end_idx = min(start_idx + cascara_samples, TOTAL_SAMPLES)
        length = end_idx - start_idx
        timb_l[start_idx:end_idx] += cascara_stick[:length] * 0.22
        timb_r[start_idx:end_idx] += cascara_stick[:length] * 0.28

    if bar % 2 == 1:
        accents = [
            (3, timbal_macho, 0.45, 0.4, 0.6),
            (6, timbal_hembra, 0.50, 0.6, 0.4),
            (11, timbal_rim_macho, 0.55, 0.3, 0.7),
            (14, timbal_hembra, 0.52, 0.6, 0.4)
        ]
        for step, sample_buf, vol, p_l, p_r in accents:
            t_acc = bar * BAR_DUR + step * SIXTEENTH_DUR
            start_idx = int(t_acc * SAMPLE_RATE)
            slen = len(sample_buf)
            end_idx = min(start_idx + slen, TOTAL_SAMPLES)
            length = end_idx - start_idx
            timb_l[start_idx:end_idx] += sample_buf[:length] * vol * p_l
            timb_r[start_idx:end_idx] += sample_buf[:length] * vol * p_r

    if bar == 39:
        for step in range(8, 16):
            t_roll = bar * BAR_DUR + step * (SIXTEENTH_DUR / 2.0)
            start_idx = int(t_roll * SAMPLE_RATE)
            if start_idx >= TOTAL_SAMPLES:
                break
            sample_buf = timbal_rim_macho if (step % 2 == 1) else timbal_macho
            crescendo = 0.3 + (step - 8) * 0.08
            slen = len(sample_buf)
            end_idx = min(start_idx + slen, TOTAL_SAMPLES)
            length = end_idx - start_idx
            timb_l[start_idx:end_idx] += sample_buf[:length] * crescendo * 0.5
            timb_r[start_idx:end_idx] += sample_buf[:length] * crescendo * 0.5

    elif bar % 4 == 3:
        fill_steps = [(12, timbal_macho), (13, timbal_rim_macho), (14, timbal_macho), (15, timbal_hembra)]
        for step, sample_buf in fill_steps:
            t_fill = bar * BAR_DUR + step * SIXTEENTH_DUR
            start_idx = int(t_fill * SAMPLE_RATE)
            slen = len(sample_buf)
            end_idx = min(start_idx + slen, TOTAL_SAMPLES)
            length = end_idx - start_idx
            timb_l[start_idx:end_idx] += sample_buf[:length] * 0.60 * 0.4
            timb_r[start_idx:end_idx] += sample_buf[:length] * 0.60 * 0.6

# -------------------------------------------------------------
# 5. XILÓFONOS (Rosewood Bar Physical Modeling in Microtonal Bayati)
# -------------------------------------------------------------
print("-> Synthesizing Microtonal Wooden Xylophones (Maqam Bayati with Neutral 2nd & 6th)...")
bar_modes = [1.0, 2.756, 5.404]

def synthesize_xylophone_bar(freq, dur=0.38):
    ns = int(dur * SAMPLE_RATE)
    t = get_time(ns)
    sig = np.zeros(ns, dtype=np.float32)
    mallet_noise = (np.random.rand(ns).astype(np.float32) * 2.0 - 1.0) * np.exp(-t * 110.0)
    for m_idx, m in enumerate(bar_modes):
        mf = freq * m
        if mf > 18000:
            continue
        damping = 16.0 + (mf / 300.0) * 12.0
        amp = 1.0 / (m_idx * 1.5 + 1.0)
        sig += amp * np.sin(2.0 * np.pi * mf * t) * np.exp(-t * damping)
    wood_body = 0.25 * np.sin(2.0 * np.pi * freq * t) * np.exp(-t * 9.0)
    xylo = sig * 0.75 + wood_body + mallet_noise * 0.3
    return np.tanh(xylo * 1.3) * 0.5

xylo_notes_D4 = [synthesize_xylophone_bar(f, 0.40) for f in SCALE_D4]
xylo_notes_D5 = [synthesize_xylophone_bar(f, 0.32) for f in SCALE_D5]

xylo_melody_A = [
    (0, 0, 4), (2, 1, 4), (4, 2, 4), (6, 4, 4),
    (8, 5, 4), (10, 4, 4), (12, 1, 4), (14, 0, 4)
]
xylo_melody_B = [
    (0, 4, 4), (2, 5, 4), (4, 0, 5), (6, 1, 5),
    (8, 2, 5), (10, 1, 5), (12, 0, 5), (14, 4, 4)
]

xylo_bars = [b for b in range(NUM_BARS) if (0 <= b < 32) or (32 <= b < 60)]
xyl_l, xyl_r = stems["05_Xilofonos_Bayati"]

for bar in xylo_bars:
    if (bar // 4) % 2 == 0:
        pattern = xylo_melody_A
    else:
        pattern = xylo_melody_B if (bar % 2 == 1) else xylo_melody_A
    
    vol_scale = 0.65 if (32 <= bar < 40) else 0.85
    
    for step, note_idx, oct_layer in pattern:
        buf = xylo_notes_D4[note_idx] if oct_layer == 4 else xylo_notes_D5[note_idx]
        t_xylo = bar * BAR_DUR + step * SIXTEENTH_DUR
        start_idx = int(t_xylo * SAMPLE_RATE)
        slen = len(buf)
        end_idx = min(start_idx + slen, TOTAL_SAMPLES)
        length = end_idx - start_idx
        
        p_l = 0.5 + 0.35 * math.sin(step * 0.785)
        p_r = 1.0 - p_l
        
        xyl_l[start_idx:end_idx] += buf[:length] * vol_scale * p_l
        xyl_r[start_idx:end_idx] += buf[:length] * vol_scale * p_r

# -------------------------------------------------------------
# 6. HOUSE DRUM ACCENTS (Open Hats & Claps)
# -------------------------------------------------------------
print("-> Synthesizing Offbeat Open Hats & Crisp Claps...")
oh_samples = int(0.24 * SAMPLE_RATE)
t_oh = get_time(oh_samples)
noise_oh = (np.random.rand(oh_samples).astype(np.float32) * 2.0 - 1.0)
metallic_oh = 0.3 * (np.sin(2.0 * np.pi * 7100.0 * t_oh) + np.sin(2.0 * np.pi * 9400.0 * t_oh))
open_hat = (noise_oh * 0.7 + metallic_oh) * np.exp(-t_oh * 17.0) * 0.28

clap_samples = int(0.22 * SAMPLE_RATE)
t_cl = get_time(clap_samples)
c_noise = (np.random.rand(clap_samples).astype(np.float32) * 2.0 - 1.0)
c_env = np.exp(-t_cl * 22.0)
for lag in [0.010, 0.022]:
    lag_s = int(lag * SAMPLE_RATE)
    if lag_s < clap_samples:
        c_env[lag_s:] += 0.5 * np.exp(-t_cl[:clap_samples - lag_s] * 40.0)
clap_sig = np.tanh(c_noise * c_env * 1.5) * 0.38

hat_bars = [b for b in range(NUM_BARS) if not (b < 2 or (32 <= b < 36) or b >= 62)]
hc_l, hc_r = stems["06_Hats_Claps"]

for bar in hat_bars:
    for beat in range(4):
        t_oh_start = bar * BAR_DUR + (beat + 0.5) * BEAT_DUR
        start_idx = int(t_oh_start * SAMPLE_RATE)
        end_idx = min(start_idx + oh_samples, TOTAL_SAMPLES)
        length = end_idx - start_idx
        hc_l[start_idx:end_idx] += open_hat[:length] * 0.45
        hc_r[start_idx:end_idx] += open_hat[:length] * 0.55

    if bar >= 4 and not (32 <= bar < 40):
        for beat in [1, 3]:
            t_cl_start = bar * BAR_DUR + beat * BEAT_DUR
            start_idx = int(t_cl_start * SAMPLE_RATE)
            end_idx = min(start_idx + clap_samples, TOTAL_SAMPLES)
            length = end_idx - start_idx
            hc_l[start_idx:end_idx] += clap_sig[:length] * 0.5
            hc_r[start_idx:end_idx] += clap_sig[:length] * 0.5

# -------------------------------------------------------------
# 7. MICROTONAL ANALOG ATMOSPHERIC PADS (Xenharmonic Wash)
# -------------------------------------------------------------
print("-> Synthesizing Microtonal Atmospheric Pads (Warm Xenharmonic Polyphony)...")
pad_chords = [
    [cents_to_freq(ROOT_FREQ_D3, 0.0), cents_to_freq(ROOT_FREQ_D3, 300.0), cents_to_freq(ROOT_FREQ_D3, 700.0), cents_to_freq(ROOT_FREQ_D3 * 2.0, 150.0)],
    [cents_to_freq(ROOT_FREQ_D3, 0.0), cents_to_freq(ROOT_FREQ_D3, 500.0), cents_to_freq(ROOT_FREQ_D3, 850.0), cents_to_freq(ROOT_FREQ_D3 * 2.0, 150.0)]
]

pad_bars = [b for b in range(NUM_BARS) if (0 <= b < 16) or (24 <= b < 48) or (56 <= b < 64)]
pad_l, pad_r = stems["07_Pads_Atmosphere"]

for bar in pad_bars:
    chord = pad_chords[(bar // 4) % 2]
    dur_pad = BAR_DUR
    ns_pad = int(dur_pad * SAMPLE_RATE)
    t_pad = get_time(ns_pad)
    
    pad_sig_l = np.zeros(ns_pad, dtype=np.float32)
    pad_sig_r = np.zeros(ns_pad, dtype=np.float32)
    
    for note_f in chord:
        f1 = note_f * 0.998
        f2 = note_f * 1.002
        osc_l = np.sin(2.0 * np.pi * f1 * t_pad) + 0.3 * np.sin(4.0 * np.pi * f1 * t_pad)
        osc_r = np.sin(2.0 * np.pi * f2 * t_pad) + 0.3 * np.sin(4.0 * np.pi * f2 * t_pad)
        pad_sig_l += osc_l * 0.06
        pad_sig_r += osc_r * 0.06

    env_pad = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.linspace(0.0, 1.0, ns_pad, dtype=np.float32)))
    
    start_idx = int(bar * BAR_DUR * SAMPLE_RATE)
    end_idx = min(start_idx + ns_pad, TOTAL_SAMPLES)
    length = end_idx - start_idx
    pad_l[start_idx:end_idx] += pad_sig_l[:length] * env_pad[:length]
    pad_r[start_idx:end_idx] += pad_sig_r[:length] * env_pad[:length]

# -------------------------------------------------------------
# 8. MITXU FLAMENCO VOCAL & COROS ("MICHU MICHU MICHU MINUUUUU")
# -------------------------------------------------------------
print("-> Processing Mitxu Flamenco Vocal & Coros for Bridge...")
voz_l, voz_r = stems["08_Voz_Mitxu_Flamenco"]

def load_and_resample(path: Path):
    d, s = sf.read(str(path))
    if d.ndim > 1:
        d = d[:, 0]
    ns = int(len(d) * SAMPLE_RATE / s)
    res = signal.resample(d, ns).astype(np.float32)
    # High-pass filter 110Hz
    b_hp, a_hp = signal.butter(2, 110.0 / (SAMPLE_RATE / 2.0), btype='highpass')
    f_res = signal.lfilter(b_hp, a_hp, res)
    return f_res / (np.max(np.abs(f_res)) + 1e-6)

v_quejio = load_and_resample(MITXU_QUEJIO_PATH)
v_chant = load_and_resample(MITXU_CHANT_PATH)
v_minu = load_and_resample(MITXU_MINU_PATH)

# Placement:
# 1. Quejío flamenco: Bar 32.5 (t = 62.90s)
t1 = 32.5 * BAR_DUR
i1 = int(t1 * SAMPLE_RATE)
l1 = min(len(v_quejio), TOTAL_SAMPLES - i1)
voz_l[i1:i1+l1] += v_quejio[:l1] * 0.78
voz_r[i1:i1+l1] += v_quejio[:l1] * 0.78

# 2. Cántico rítmico: Bar 35.75 (t = 69.19s)
t2 = 35.75 * BAR_DUR
i2 = int(t2 * SAMPLE_RATE)
l2 = min(len(v_chant), TOTAL_SAMPLES - i2)
voz_l[i2:i2+l2] += v_chant[:l2] * 0.74
voz_r[i2:i2+l2] += v_chant[:l2] * 0.74

# 3. Coros "Michu michu michu minuuuuu! Olé!": Bar 37.25 (t = 72.10s)
t3 = 37.25 * BAR_DUR
i3 = int(t3 * SAMPLE_RATE)
l3 = min(len(v_minu), TOTAL_SAMPLES - i3)
# Stereo chorus doubling
voz_l[i3:i3+l3] += v_minu[:l3] * 0.85
voz_r[i3:i3+l3] += v_minu[:l3] * 0.85
# And repeat right before drop climax (Bar 38.75)
t3_rep = 38.75 * BAR_DUR
i3_rep = int(t3_rep * SAMPLE_RATE)
l3_rep = min(len(v_minu), TOTAL_SAMPLES - i3_rep)
voz_l[i3_rep:i3_rep+l3_rep] += v_minu[:l3_rep] * 0.90 * 0.65
voz_r[i3_rep:i3_rep+l3_rep] += v_minu[:l3_rep] * 0.90 * 0.35

# Ping-Pong Tape Delay & Plate Reverb on Vocals
delay_samples = int(0.75 * BEAT_DUR * SAMPLE_RATE) # 362.9ms
delay_buf_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
delay_buf_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

for n in range(i1, min(i3_rep + int(4.0 * SAMPLE_RATE), TOTAL_SAMPLES)):
    if n - delay_samples >= 0:
        delay_buf_l[n] = voz_l[n] * 0.38 + delay_buf_r[n - delay_samples] * 0.38
        delay_buf_r[n] = voz_r[n] * 0.38 + delay_buf_l[n - delay_samples] * 0.38

b_lp, a_lp = signal.butter(2, 3800.0 / (SAMPLE_RATE / 2.0), btype='lowpass')
delay_buf_l = signal.lfilter(b_lp, a_lp, delay_buf_l)
delay_buf_r = signal.lfilter(b_lp, a_lp, delay_buf_r)

reverb_buf_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
reverb_buf_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
for cd in [int(0.029 * SAMPLE_RATE), int(0.037 * SAMPLE_RATE), int(0.043 * SAMPLE_RATE), int(0.051 * SAMPLE_RATE)]:
    reverb_buf_l[cd:] += delay_buf_l[:-cd] * 0.20
    reverb_buf_r[cd:] += delay_buf_r[:-cd] * 0.20

voz_l += delay_buf_l * 0.42 + reverb_buf_l * 0.32
voz_r += delay_buf_r * 0.42 + reverb_buf_r * 0.32
voz_l[:] = np.tanh(voz_l * 1.2) * 0.88
voz_r[:] = np.tanh(voz_r * 1.2) * 0.88

# -------------------------------------------------------------
# 9. PALMAS FLAMENCAS (Sordas & Secas con Bulería Swing)
# -------------------------------------------------------------
print("-> Synthesizing Palmas Flamencas (Sordas & Secas)...")
palmas_l, palmas_r = stems["09_Palmas_Flamencas"]

def synthesize_palma(is_seca=False):
    dur = 0.045 if is_seca else 0.075
    ns = int(dur * SAMPLE_RATE)
    t = get_time(ns)
    noise = (np.random.rand(ns) * 2 - 1).astype(np.float32)
    if is_seca:
        env = np.exp(-t * 110.0)
        b, a = signal.butter(2, [1800.0 / (SAMPLE_RATE/2), 5200.0 / (SAMPLE_RATE/2)], btype='bandpass')
        body = signal.lfilter(b, a, noise)
        snap = np.sin(2 * np.pi * 2800.0 * t) * np.exp(-t * 220.0) * 0.4
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

# Palmas active in Drop 1 (bars 16-31), Bridge (bars 34-39), and Drop 2 (bars 40-59)
palmas_bars = [b for b in range(NUM_BARS) if (16 <= b < 32) or (34 <= b < 40) or (40 <= b < 60)]

for bar in palmas_bars:
    # In bridge bars 37-39, intense palmas roll
    is_bridge_climax = (37 <= bar < 40)
    
    # 16-step palmas pattern: sordas on base, secas on syncopations and accents
    for step in range(16):
        is_swing = (step % 2 == 1)
        step_time = bar * BAR_DUR + step * SIXTEENTH_DUR + (swing_offset if is_swing else 0.0)
        start_idx = int(step_time * SAMPLE_RATE)
        if start_idx >= TOTAL_SAMPLES:
            break
        
        # Flamenco rumba / house syncopations (steps 2, 4, 7, 10, 12, 14)
        if step in [4, 12] or (is_bridge_climax and step in [2, 6, 10, 14]):
            p_buf = p_seca
            vol = 0.55 if not is_bridge_climax else 0.70
            p_l, p_r = 0.42, 0.58
        elif step % 2 == 0:
            p_buf = p_sorda
            vol = 0.38
            p_l, p_r = 0.55, 0.45
        else:
            continue

        end_idx = min(start_idx + len(p_buf), TOTAL_SAMPLES)
        length = end_idx - start_idx
        palmas_l[start_idx:end_idx] += p_buf[:length] * vol * p_l
        palmas_r[start_idx:end_idx] += p_buf[:length] * vol * p_r

# -------------------------------------------------------------
# 10. ERUCTO DE ALAIN CON DUB DELAY (Bar 35.0 Bridge & Outro)
# -------------------------------------------------------------
print("-> Processing Alain Guttural Eructo with Space Echo Dub Delay...")
eructo_l, eructo_r = stems["10_Eructo_Alain_Dub_Delay"]

alain_eructo_raw, a_sr = sf.read(str(ALAIN_ERUCTO_PATH))
if alain_eructo_raw.ndim > 1:
    alain_eructo_raw = alain_eructo_raw[:, 0]
num_s_e = int(len(alain_eructo_raw) * SAMPLE_RATE / a_sr)
eructo_res = signal.resample(alain_eructo_raw, num_s_e).astype(np.float32)
eructo_res /= (np.max(np.abs(eructo_res)) + 1e-6)

# Injection Points:
# 1. Main Bridge Hit: Bar 35.0 (t = 67.74s) — Right before Mitxu's chant & coros
t_e1 = 35.0 * BAR_DUR
i_e1 = int(t_e1 * SAMPLE_RATE)
l_e1 = min(len(eructo_res), TOTAL_SAMPLES - i_e1)
eructo_l[i_e1:i_e1+l_e1] += eructo_res[:l_e1] * 0.88 * 0.65
eructo_r[i_e1:i_e1+l_e1] += eructo_res[:l_e1] * 0.88 * 0.35

# 2. Outro Final Surprise Hit: Bar 60.5 (t = 117.10s)
t_e2 = 60.5 * BAR_DUR
i_e2 = int(t_e2 * SAMPLE_RATE)
l_e2 = min(len(eructo_res), TOTAL_SAMPLES - i_e2)
eructo_l[i_e2:i_e2+l_e2] += eructo_res[:l_e2] * 0.75 * 0.35
eructo_r[i_e2:i_e2+l_e2] += eructo_res[:l_e2] * 0.75 * 0.65

# Dedicated Roland Space Echo Dub Delay on Eructo
# Delay time: Dotted Eighth (362.9ms) with 50% feedback & tape low-pass (2600Hz)
d_samples = int(0.75 * BEAT_DUR * SAMPLE_RATE)
d_fb_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
d_fb_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

for n in range(i_e1, min(i_e1 + int(7.0 * SAMPLE_RATE), TOTAL_SAMPLES)):
    if n - d_samples >= 0:
        d_fb_l[n] = eructo_l[n] * 0.50 + d_fb_r[n - d_samples] * 0.48
        d_fb_r[n] = eructo_r[n] * 0.50 + d_fb_l[n - d_samples] * 0.48

for n in range(i_e2, min(i_e2 + int(6.0 * SAMPLE_RATE), TOTAL_SAMPLES)):
    if n - d_samples >= 0:
        d_fb_l[n] += eructo_l[n] * 0.45 + d_fb_r[n - d_samples] * 0.45
        d_fb_r[n] += eructo_r[n] * 0.45 + d_fb_l[n - d_samples] * 0.45

b_dub, a_dub = signal.butter(2, 2600.0 / (SAMPLE_RATE / 2.0), btype='lowpass')
d_fb_l = signal.lfilter(b_dub, a_dub, d_fb_l)
d_fb_r = signal.lfilter(b_dub, a_dub, d_fb_r)

# Sum delay into Alain's stem
eructo_l += d_fb_l * 0.55
eructo_r += d_fb_r * 0.55

# -------------------------------------------------------------
# WRITE DISCRETE STEMS (10 STEMS)
# -------------------------------------------------------------
print("-> Exporting 10 Discrete High-Fidelity WAV Stems...")
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

for stem_name, (sl, sr) in stems.items():
    stem_path = STEMS_DIR / f"{stem_name}.wav"
    write_stereo_wav(stem_path, sl, sr)
    print(f"   [Stem] {stem_path.name} written ({stem_path.stat().st_size / (1024*1024):.2f} MB)")

# -------------------------------------------------------------
# MASTER MIX & LIMITING
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
        project_title="Microtonal House Master Session (Alain Eructo + Mitxu Minu)",
        bpm=BPM,
        output_flp=str(OUTPUT_FLP)
    )
    print(f"✅ Native FLP Project Compiled: {OUTPUT_FLP} ({OUTPUT_FLP.stat().st_size / 1024:.1f} KB)")
except Exception as e:
    print(f"Notice: FLP compiler note: {e}")

print("=== All Production Assets Successfully Built and Centralized ===")
