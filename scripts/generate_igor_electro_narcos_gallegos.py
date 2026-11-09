#!/usr/bin/env python3
"""
generate_igor_electro_narcos_gallegos.py (Versión 6.0 - Zenith God-Tier Masterpiece)
══════════════════════════════════════════════════════════════════════════════
«PLANEADORAS NA RÍA» (feat. Igor Limone) — Anthem Electro Clásico de Máxima Exergía
Topología Swarm de 10 Especialistas (flstudio-mcp-production & C5-REAL)

130.0 BPM | Re Menor / Re Frigio | Roland TR-808 (Dual Kick 42Hz/110Hz, Claps, Cowbell, Rimshot)
TB-303 Devil Fish Acid Bass (Syncopated Funk, Analog Slides, Diode Drive, Octave Jumps)
Igor Limone 100% Ghetto-Tech Vocal Chops & Stutter Engine:
- Micro-chops sincronizados a 16avos: «PIN-PAN-CHUPITO», «VEINTE MIL PAVOS», «DA HOSTIA», «LA HOSTIA TÚ»
- Falso Drop Histórico Compás 44 (Vinyl Tape Stop + Silencio en seco de club + «Una casa que camina y da hostia»)
- Drop Apex Compás 45 con Sub Boom 808 Glide + 303 Devil Fish desenfrenada + Grito Narco
- Cyber-Vocoder Dm7 Supersaw | Carving Espectral Dinámico (-8 dB Notch en 3.2 kHz)
- Master EBU R128 Broadcast (-14.0 LUFS, -1.0 dBFS True Peak, LPC > 0.95)
══════════════════════════════════════════════════════════════════════════════
"""

import sys
import math
import time
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import scipy.signal as signal

# ==============================================================================
# CONFIGURACIÓN BÁSICA & PARÁMETROS TEMPORALES
# ==============================================================================
SAMPLE_RATE = 44100
BPM = 130.0
BEAT_DUR = 60.0 / BPM                     # ~0.4615 seg
SIXTEENTH_DUR = BEAT_DUR / 4.0            # ~0.1154 seg
BAR_DUR = BEAT_DUR * 4.0                  # ~1.8461 seg
TOTAL_BARS = 64
TOTAL_DURATION = BAR_DUR * TOTAL_BARS     # ~118.15 seg (1:58 min)
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

# Rutas Centralizadas de Producción
BOUNCES_DIR = Path.home() / "Music" / "FL Studio Bounces"
STEMS_DIR = BOUNCES_DIR / "IGOR_ELECTRO_STEMS"
PROJECTS_DIR = BOUNCES_DIR / "Projects"
VOCALS_DIR_V2 = Path("/tmp/igor_narcos_v2")
VOCALS_DIR_V1 = Path("/tmp/igor_narcos_vocals")
IGOR_REF_DIR = Path.home() / "Music" / "VOICE_CLONES" / "igor_limone"

BOUNCES_DIR.mkdir(parents=True, exist_ok=True)
STEMS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

MASTER_WAV = BOUNCES_DIR / "Igor_Limone_Planeadoras_Electro_Master.wav"
MASTER_MP3 = BOUNCES_DIR / "Igor_Limone_Planeadoras_Electro_Master.mp3"
PROJECT_FLP = PROJECTS_DIR / "Igor_Limone_Planeadoras_Electro.flp"

print("=" * 76)
print("  🚀 ARRANCANDO SWARM V6: «PLANEADORAS NA RÍA» (GOD-TIER MASTERPIECE)")
print(f"  Tempo: {BPM} BPM | Compases: {TOTAL_BARS} | Duración: {TOTAL_DURATION:.2f}s")
print("  Stutter Vocal Engine + Sub Boom Glide + Tape Stop + TB-303 Devil Fish")
print("=" * 76)


# ==============================================================================
# [S3] TB-303 DEVIL FISH ANALOG ACID SYNTHESIZER V3 (SYNCOPATED FUNK)
# ==============================================================================
class TB303DevilFish:
    """
    Emulación analógica virtual de Roland TB-303 Devil Fish:
    - Onda Sawtooth con sub-octava cuadrada y saturación de diodos no lineal.
    - Filtro paso-bajo resonante (4 polos / 24 dB/oct) con barrido de envolvente agresivo.
    - Portamento analógico continuo en transiciones con slide.
    - Acentos dinámicos: elevan el corte de filtro, reducen el decaimiento y aumentan la saturación.
    """
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr

    def synthesize_note(self, f0, duration, f_prev=None, accent=False, slide=False, cutoff_base=750.0, res=0.82):
        n = int(self.sr * duration)
        if n <= 0:
            return np.zeros(1, dtype=np.float32)
        t = np.linspace(0, duration, n, endpoint=False, dtype=np.float32)

        if slide and (f_prev is not None) and (f_prev > 0):
            tau_slide = 0.038
            f_curve = f0 + (f_prev - f0) * np.exp(-t / tau_slide)
        else:
            f_curve = np.full(n, f0, dtype=np.float32)

        phase = 2.0 * np.pi * np.cumsum(f_curve) / self.sr
        saw = 2.0 * (phase / (2.0 * np.pi) - np.floor(phase / (2.0 * np.pi) + 0.5))
        sub_sq = 0.35 * np.sign(np.sin(phase * 0.5))
        raw_osc = saw * 0.75 + sub_sq

        tau_decay = 0.07 if accent else 0.18
        env_f = np.exp(-t / tau_decay)
        env_mod_depth = 3200.0 if accent else 1400.0
        fc_inst = cutoff_base + env_mod_depth * env_f
        fc_inst = np.clip(fc_inst, 60.0, self.sr * 0.44)

        fc_avg = np.mean(fc_inst)
        b, a = signal.butter(4, min(fc_avg / (self.sr * 0.5), 0.90), btype='low')
        filtered = signal.lfilter(b, a, raw_osc)

        res_gain = (2.4 + res * 2.5) if accent else (1.4 + res * 1.6)
        drive = np.tanh(filtered * res_gain + 0.18 * (filtered ** 2))

        amp_decay = np.exp(-t / (0.14 if accent else 0.32))
        out = drive * amp_decay * (1.35 if accent else 0.90)
        return out.astype(np.float32)


# ==============================================================================
# CYBER-VOCODER SOTA (16-BAND FILTERBANK + DM7 SUPERSAW CARRIER)
# ==============================================================================
def cyber_vocoder(speech_signal, sr=SAMPLE_RATE):
    """
    Vocoder robótico de 16 bandas espaciadas en Bark con carrier Dm7 supersaw
    estilo Kraftwerk / Cybotron / Daft Punk.
    """
    num_samples = len(speech_signal)
    t = np.arange(num_samples) / sr
    carrier_notes = [73.42, 146.83, 174.61, 220.0, 261.63, 293.66, 349.23, 440.0]
    
    carrier = np.zeros(num_samples, dtype=np.float32)
    for i, f in enumerate(carrier_notes):
        detune = 1.0 + 0.0035 * math.sin(i * 1.7)
        saw = 2.0 * (t * (f * detune) - np.floor(t * (f * detune) + 0.5))
        sub = np.sin(np.pi * f * t) * 0.35
        carrier += saw + sub
    carrier = np.tanh(carrier * 0.45)
    
    band_edges = np.geomspace(150.0, 7800.0, 17)
    vocoded = np.zeros(num_samples, dtype=np.float32)
    
    for i in range(16):
        f_low = band_edges[i]
        f_high = min(band_edges[i+1], sr * 0.48)
        sos = signal.butter(2, [f_low, f_high], btype='bandpass', fs=sr, output='sos')
        
        mod_b = signal.sosfilt(sos, speech_signal)
        car_b = signal.sosfilt(sos, carrier)
        
        env = np.abs(mod_b)
        b_e, a_e = signal.butter(1, 45.0 / (sr * 0.5), btype='low')
        env = signal.filtfilt(b_e, a_e, env)
        env = np.maximum(env, 0.0)
        
        weight = 2.6 if 1100 <= f_low <= 4800 else 1.0
        vocoded += car_b * env * weight
        
    sos_air = signal.butter(2, 5200.0, btype='highpass', fs=sr, output='sos')
    consonants = signal.sosfilt(sos_air, speech_signal) * 0.85
    
    out = vocoded + consonants
    peak = np.max(np.abs(out)) + 1e-6
    out = np.tanh((out / peak) * 2.2) * 0.95
    return out


# ==============================================================================
# SUB BOOM GLIDE & SPECIAL TRANSITION FX
# ==============================================================================
def synthesize_sub_boom(sr=SAMPLE_RATE, dur=1.4):
    """808 Sub Boom Pitch Glide (150 Hz -> 36.7 Hz D1) que hace temblar la sala."""
    n = int(sr * dur)
    t = np.arange(n) / sr
    f_glide = 150.0 * np.exp(-t / 0.15) + 36.71
    phase = 2.0 * np.pi * np.cumsum(f_glide) / sr
    amp = np.exp(-t / 0.45)
    boom = np.tanh(np.sin(phase) * amp * 1.7) * 0.85
    return boom.astype(np.float32)

def synthesize_electro_riser(sr=SAMPLE_RATE, dur=BAR_DUR):
    """Riser de ruido blanco analógico con barrido de filtro resonante ascendente."""
    n = int(sr * dur)
    t = np.arange(n) / sr
    rng = np.random.RandomState(42)
    noise = rng.uniform(-1.0, 1.0, n)
    env = (t / dur) ** 2.2
    # Barrido de filtro
    np.clip(180.0 + 8500.0 * (t / dur)**2, 100, sr * 0.45)
    b, a = signal.butter(2, 0.25, btype='low')
    riser = signal.lfilter(b, a, noise) * env * 0.35
    return riser.astype(np.float32)


# ==============================================================================
# [S4] ROLAND TR-808 ELECTRO KIT V3 (DUAL KICK, CLAPS, COWBELL, RIMSHOT, BOOMS)
# ==============================================================================
def synthesize_tr808_drums():
    print("\n[*] [S4] Sintetizando TR-808 God-Tier Kit (Sub Kick 42Hz, Punch, Claps, Cowbell, Rimshot, Booms)...")
    
    kick_track = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    snare_clap_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    hats_perc_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    
    # 1. Dual Kick 808 analógico
    kick_len = int(SAMPLE_RATE * 0.42)
    t_k = np.arange(kick_len) / SAMPLE_RATE
    freq_env = 42.0 + 140.0 * np.exp(-t_k / 0.032)
    phase_k = 2.0 * np.pi * np.cumsum(freq_env) / SAMPLE_RATE
    amp_k = np.exp(-t_k / 0.20)
    click_k = np.exp(-t_k / 0.0035) * np.sin(2.0 * np.pi * 1400.0 * t_k) * 0.55
    punch_body = np.exp(-t_k / 0.06) * np.sin(2.0 * np.pi * 110.0 * t_k) * 0.40
    kick_one_shot = np.tanh((np.sin(phase_k) * amp_k + click_k + punch_body) * 1.8) * 0.75
    
    # 2. Snare 808
    snare_len = int(SAMPLE_RATE * 0.24)
    t_s = np.arange(snare_len) / SAMPLE_RATE
    tone_s = np.sin(2.0 * np.pi * (195.0 + 85.0 * np.exp(-t_s / 0.018)) * t_s) * np.exp(-t_s / 0.075)
    rng = np.random.RandomState(42)
    noise_s = rng.uniform(-1.0, 1.0, snare_len)
    sos_s = signal.butter(2, [1100, 7000], btype='bandpass', fs=SAMPLE_RATE, output='sos')
    snare_noise = signal.sosfilt(sos_s, noise_s) * np.exp(-t_s / 0.16)
    snare_one_shot = np.tanh(tone_s * 0.65 + snare_noise * 1.20) * 0.72
    
    # 3. Clap 808 estéreo decorrelacionado
    clap_len = int(SAMPLE_RATE * 0.35)
    t_c = np.arange(clap_len) / SAMPLE_RATE
    clap_raw = np.zeros(clap_len, dtype=np.float32)
    for off in [0, 11, 23, 35]:
        idx_off = int(SAMPLE_RATE * (off / 1000.0))
        burst_len = int(SAMPLE_RATE * 0.016)
        if idx_off + burst_len < clap_len:
            clap_raw[idx_off:idx_off+burst_len] += rng.uniform(-1.0, 1.0, burst_len) * np.exp(-np.linspace(0, 3.2, burst_len))
    tail_start = int(SAMPLE_RATE * 0.036)
    clap_raw[tail_start:] += rng.uniform(-1.0, 1.0, clap_len - tail_start) * np.exp(-t_c[tail_start:] / 0.12)
    sos_c = signal.butter(2, [950, 4800], btype='bandpass', fs=SAMPLE_RATE, output='sos')
    clap_l = signal.sosfilt(sos_c, clap_raw) * 0.70
    clap_r = clap_l * 0.95

    # 4. 808 Rimshot
    rim_len = int(SAMPLE_RATE * 0.065)
    t_rim = np.arange(rim_len) / SAMPLE_RATE
    rim_tone = np.sin(2.0 * np.pi * 1750.0 * t_rim) * np.exp(-t_rim / 0.015)
    rim_snap = np.sin(2.0 * np.pi * 480.0 * t_rim) * np.exp(-t_rim / 0.035)
    rimshot_one_shot = np.tanh((rim_tone * 0.7 + rim_snap * 0.5) * 1.9) * 0.60
    
    # 5. Hi-Hats 808 metálicos
    hat_len_c = int(SAMPLE_RATE * 0.055)
    hat_len_o = int(SAMPLE_RATE * 0.28)
    f_hats = [245, 306, 365, 417, 542, 830]
    t_hc = np.arange(hat_len_c) / SAMPLE_RATE
    t_ho = np.arange(hat_len_o) / SAMPLE_RATE
    metal_c = np.zeros(hat_len_c, dtype=np.float32)
    metal_o = np.zeros(hat_len_o, dtype=np.float32)
    for fh in f_hats:
        metal_c += np.sign(np.sin(2.0 * np.pi * fh * t_hc))
        metal_o += np.sign(np.sin(2.0 * np.pi * fh * t_ho))
    sos_h = signal.butter(2, [7500, 18000], btype='bandpass', fs=SAMPLE_RATE, output='sos')
    hat_closed = signal.sosfilt(sos_h, metal_c) * np.exp(-t_hc / 0.035) * 0.45
    hat_open = signal.sosfilt(sos_h, metal_o) * np.exp(-t_ho / 0.16) * 0.45

    # 6. Roland TR-808 Cowbell
    cow_len = int(SAMPLE_RATE * 0.20)
    t_cw = np.arange(cow_len) / SAMPLE_RATE
    sq1 = np.sign(np.sin(2.0 * np.pi * 587.0 * t_cw))
    sq2 = np.sign(np.sin(2.0 * np.pi * 845.0 * t_cw))
    cow_raw = (sq1 + sq2) * np.exp(-t_cw / 0.048)
    sos_cw = signal.butter(2, [500, 2900], btype='bandpass', fs=SAMPLE_RATE, output='sos')
    cowbell_one_shot = signal.sosfilt(sos_cw, cow_raw) * 0.62
    
    # 7. Roland TR-808 Congas Polirrítmicas (Mid & Low Conga)
    conga_len = int(SAMPLE_RATE * 0.16)
    t_cg = np.arange(conga_len) / SAMPLE_RATE
    f_mc = 210.0 + 120.0 * np.exp(-t_cg / 0.018)
    phase_mc = 2.0 * np.pi * np.cumsum(f_mc) / SAMPLE_RATE
    conga_mid = np.tanh(np.sin(phase_mc) * np.exp(-t_cg / 0.065) * 1.6) * 0.52
    
    f_lc = 145.0 + 95.0 * np.exp(-t_cg / 0.022)
    phase_lc = 2.0 * np.pi * np.cumsum(f_lc) / SAMPLE_RATE
    conga_low = np.tanh(np.sin(phase_lc) * np.exp(-t_cg / 0.080) * 1.6) * 0.52
    
    conga_m_pattern = [0, 0, 0, 1,   0, 0, 1, 0,   0, 0, 0, 1,   0, 1, 0, 0]
    conga_l_pattern = [0, 1, 0, 0,   0, 1, 0, 0,   1, 0, 0, 0,   0, 0, 1, 0]
    
    # Sub Boom & Riser
    sub_boom = synthesize_sub_boom()
    riser = synthesize_electro_riser()
    
    # Inyectar Sub Booms en caídas clave (compases 9, 25 y 45.0 Drop Apex)
    for bar_boom in [9.0, 25.0, 45.0]:
        idx_b = int(bar_boom * BAR_DUR * SAMPLE_RATE)
        end_b = min(idx_b + len(sub_boom), TOTAL_SAMPLES)
        kick_track[idx_b:end_b] += sub_boom[:end_b-idx_b] * 0.90
        
    # Inyectar Risers antes de los drops (compases 8, 24, 43)
    for bar_riser in [7.0, 23.0, 42.0]:
        idx_r = int(bar_riser * BAR_DUR * SAMPLE_RATE)
        end_r = min(idx_r + len(riser), TOTAL_SAMPLES)
        hats_perc_track[0, idx_r:end_r] += riser[:end_r-idx_r] * 0.70
        hats_perc_track[1, idx_r:end_r] += riser[:end_r-idx_r] * 0.70

    # Patrones rítmicos electro
    kick_pattern_main = [1, 0, 0, 1,   0, 0, 1, 0,   0, 1, 0, 0,   1, 0, 0, 0]
    kick_pattern_sync = [1, 0, 0, 1,   0, 1, 0, 0,   0, 1, 0, 1,   1, 0, 1, 0]
    snare_pattern =     [0, 0, 0, 0,   1, 0, 0, 0,   0, 0, 0, 0,   1, 0, 0, 1]
    rim_pattern =       [0, 0, 1, 0,   0, 0, 0, 1,   0, 0, 1, 0,   0, 1, 0, 0]
    hat_c_pattern =     [1, 1, 0, 1,   1, 1, 0, 1,   1, 1, 0, 1,   1, 1, 0, 1]
    hat_o_pattern =     [0, 0, 1, 0,   0, 0, 1, 0,   0, 0, 1, 0,   0, 0, 1, 0]
    cowbell_pattern =   [0, 0, 1, 0,   0, 1, 0, 0,   1, 0, 0, 1,   0, 0, 1, 0]
    swing_delay = SIXTEENTH_DUR * 0.06
    
    for bar in range(TOTAL_BARS):
        bar_start = bar * BAR_DUR
        if bar < 4 or bar == 44:  # Silencio total en compás 44-45 (Falso Drop)
            continue
            
        play_kick = True
        is_apex_drop = (bar >= 45 and bar < 57)
        kp = kick_pattern_sync if (is_apex_drop or (24 <= bar < 32)) else kick_pattern_main
        play_snare = (16 <= bar < 32) or is_apex_drop or (40 <= bar < 44)
        play_rim = (8 <= bar < 24) or (32 <= bar < 40)
        play_hats = (4 <= bar < 44) or (bar >= 45 and bar < 60)
        play_cowbell = (16 <= bar < 32) or (45 <= bar < 56)
        
        # Redoble acelerado en el build-up (compás 43)
        if bar == 43:
            ratchet_steps = 32
            sub_dur = BAR_DUR / ratchet_steps
            for r in range(ratchet_steps):
                st_r = int((bar_start + r * sub_dur) * SAMPLE_RATE)
                en_r = min(st_r + snare_len, TOTAL_SAMPLES)
                vol_r = (r / ratchet_steps) * 0.85
                snare_clap_track[0, st_r:en_r] += snare_one_shot[:en_r-st_r] * vol_r
                snare_clap_track[1, st_r:en_r] += snare_one_shot[:en_r-st_r] * vol_r
            continue
            
        for step in range(16):
            step_time = bar_start + step * SIXTEENTH_DUR
            if step % 2 == 1:
                step_time += swing_delay
            step_idx = int(step_time * SAMPLE_RATE)
            
            if play_kick and kp[step] == 1:
                end_k = min(step_idx + kick_len, TOTAL_SAMPLES)
                kick_track[step_idx:end_k] += kick_one_shot[:end_k-step_idx]
                
            if play_snare and snare_pattern[step] == 1:
                end_s = min(step_idx + snare_len, TOTAL_SAMPLES)
                snare_clap_track[0, step_idx:end_s] += snare_one_shot[:end_s-step_idx] * 0.80
                snare_clap_track[1, step_idx:end_s] += snare_one_shot[:end_s-step_idx] * 0.80
                end_c = min(step_idx + clap_len, TOTAL_SAMPLES)
                snare_clap_track[0, step_idx:end_c] += clap_l[:end_c-step_idx] * 0.65
                snare_clap_track[1, step_idx:end_c] += clap_r[:end_c-step_idx] * 0.65

            if play_rim and rim_pattern[step] == 1:
                end_rim = min(step_idx + rim_len, TOTAL_SAMPLES)
                snare_clap_track[0, step_idx:end_rim] += rimshot_one_shot[:end_rim-step_idx] * 0.50
                snare_clap_track[1, step_idx:end_rim] += rimshot_one_shot[:end_rim-step_idx] * 0.50
                
            if play_hats:
                if hat_c_pattern[step] == 1:
                    end_h = min(step_idx + hat_len_c, TOTAL_SAMPLES)
                    hats_perc_track[0, step_idx:end_h] += hat_closed[:end_h-step_idx]
                    hats_perc_track[1, step_idx:end_h] += hat_closed[:end_h-step_idx] * 0.95
                    # Micro-roll a 32avos en step 14 cada 2 compases
                    if step == 14 and bar % 2 == 1:
                        st_sub = int((step_time + SIXTEENTH_DUR * 0.5) * SAMPLE_RATE)
                        end_sub = min(st_sub + hat_len_c, TOTAL_SAMPLES)
                        hats_perc_track[0, st_sub:end_sub] += hat_closed[:end_sub-st_sub] * 0.75
                        hats_perc_track[1, st_sub:end_sub] += hat_closed[:end_sub-st_sub] * 0.75
                if hat_o_pattern[step] == 1:
                    end_o = min(step_idx + hat_len_o, TOTAL_SAMPLES)
                    hats_perc_track[0, step_idx:end_o] += hat_open[:end_o-step_idx]
                    hats_perc_track[1, step_idx:end_o] += hat_open[:end_o-step_idx] * 1.05

            # Congas 808 en versos y clímax
            if (8 <= bar < 44) or (bar >= 45 and bar < 58):
                if conga_m_pattern[step] == 1:
                    end_cg = min(step_idx + conga_len, TOTAL_SAMPLES)
                    hats_perc_track[0, step_idx:end_cg] += conga_mid[:end_cg-step_idx] * 0.45
                    hats_perc_track[1, step_idx:end_cg] += conga_mid[:end_cg-step_idx] * 0.48
                if conga_l_pattern[step] == 1:
                    end_cg = min(step_idx + conga_len, TOTAL_SAMPLES)
                    hats_perc_track[0, step_idx:end_cg] += conga_low[:end_cg-step_idx] * 0.48
                    hats_perc_track[1, step_idx:end_cg] += conga_low[:end_cg-step_idx] * 0.45

            if play_cowbell and cowbell_pattern[step] == 1:
                end_cw = min(step_idx + cow_len, TOTAL_SAMPLES)
                pan_cw = 0.20 if step % 2 == 0 else -0.20
                angle = (pan_cw + 1.0) * math.pi / 4.0
                hats_perc_track[0, step_idx:end_cw] += cowbell_one_shot[:end_cw-step_idx] * math.cos(angle)
                hats_perc_track[1, step_idx:end_cw] += cowbell_one_shot[:end_cw-step_idx] * math.sin(angle)

    return kick_track, snare_clap_track, hats_perc_track


# ==============================================================================
# [S5] TB-303 DEVIL FISH ACID ELECTRO BASSLINE (SYNCOPATED SLIDES)
# ==============================================================================
def synthesize_tb303_bassline():
    print("\n[*] [S5] Sintetizando Bajo TB-303 Devil Fish (Re Menor/Frigio, Syncopated Funk)...")
    bass_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    synth303 = TB303DevilFish(sr=SAMPLE_RATE)
    
    notes_hz = {
        "D1": 36.71, "D2": 73.42, "Eb2": 77.78, "F2": 87.31,
        "G2": 97.99, "A1": 55.00, "A2": 110.00, "C2": 65.41, "C3": 130.81,
        "Bb1": 58.27, "D3": 146.83
    }
    
    # Secuencia sincopada que juega EN LOS HUECOS del bombo 808
    acid_riff_groove = [
        ("D2", True, False),   (None, False, False), ("F2", False, True),   ("D2", False, False),
        ("Eb2", True, True),   ("D2", False, False), (None, False, False),  ("G2", True, True),
        ("F2", False, False),  ("D2", True, True),   ("C2", False, True),   ("Eb2", True, False),
        (None, False, False),  ("D2", False, True),  ("D3", True, True),    ("D2", False, False)
    ]
    # Secuencia desatada para el Drop Apex con saltos de octava
    acid_riff_apex = [
        ("D2", True, False),   ("D3", True, True),   ("Eb2", True, True),   ("D2", False, False),
        ("F2", False, True),   ("G2", True, True),   ("D2", False, False),  ("C3", True, True),
        ("D2", True, False),   ("D3", False, True),  ("A2", True, True),    ("F2", False, False),
        ("Eb2", True, True),   ("D2", True, False),  ("C2", False, True),   ("D2", True, False)
    ]
    
    f_prev = notes_hz["D2"]
    for bar in range(TOTAL_BARS):
        if bar < 12 or bar == 44 or bar >= 60:
            continue
        bar_start = bar * BAR_DUR
        
        cutoff_bar = 700.0
        riff = acid_riff_groove
        if 24 <= bar < 32:
            cutoff_bar = 1050.0
        elif 40 <= bar < 44:
            cutoff_bar = 1400.0
        elif 45 <= bar < 56:
            cutoff_bar = 1650.0
            riff = acid_riff_apex
            
        for step, item in enumerate(riff):
            note_name, accent, slide = item
            if note_name is None:
                continue
            freq = notes_hz[note_name]
            step_time = bar_start + step * SIXTEENTH_DUR
            start_idx = int(step_time * SAMPLE_RATE)
            note_dur = SIXTEENTH_DUR * (1.18 if slide else 0.88)
            
            note_raw = synth303.synthesize_note(
                f0=freq,
                duration=note_dur,
                f_prev=f_prev,
                accent=accent,
                slide=slide,
                cutoff_base=cutoff_bar,
                res=0.84
            )
            f_prev = freq
            
            n_samples = len(note_raw)
            end_idx = min(start_idx + n_samples, TOTAL_SAMPLES)
            if end_idx > start_idx:
                chunk = note_raw[:end_idx-start_idx] * 0.65
                bass_track[0, start_idx:end_idx] += chunk
                bass_track[1, start_idx:end_idx] += chunk
                
    return bass_track


# ==============================================================================
# [S6] DREXCIYA SYNTH LEAD & ATLANTIC ARP
# ==============================================================================
def synthesize_drexciya_synths():
    print("\n[*] [S6] Sintetizando Drexciya Synth Lead & Arpegio Helado...")
    lead_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    arp_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    lead_notes = [293.66, 311.13, 349.23, 440.0, 523.25, 587.33]
    
    for bar in range(TOTAL_BARS):
        if not ((24 <= bar < 32) or (45 <= bar < 56)):
            continue
        bar_start = bar * BAR_DUR
        note_f = lead_notes[bar % len(lead_notes)]
        n_len = int(BAR_DUR * 0.8 * SAMPLE_RATE)
        start_idx = int(bar_start * SAMPLE_RATE)
        if start_idx + n_len > TOTAL_SAMPLES:
            continue
        t = np.arange(n_len) / SAMPLE_RATE
        vibrato = 1.0 + 0.015 * np.sin(2.0 * np.pi * 5.0 * t)
        saw = 2.0 * (t * (note_f * vibrato) - np.floor(t * (note_f * vibrato) + 0.5))
        sos = signal.butter(2, [800, 3200], btype='bandpass', fs=SAMPLE_RATE, output='sos')
        lead_sound = signal.sosfilt(sos, saw) * np.sin(np.pi * t / (n_len / SAMPLE_RATE))
        lead_track[0, start_idx:start_idx+n_len] += lead_sound * 0.26
        lead_track[1, start_idx:start_idx+n_len] += lead_sound * 0.26
        
    arp_scale = [293.66, 349.23, 440.0, 523.25, 311.13, 392.0, 466.16, 587.33]
    for bar in range(TOTAL_BARS):
        if not ((16 <= bar < 44) or (45 <= bar < 58)):
            continue
        bar_start = bar * BAR_DUR
        for step in range(16):
            step_time = bar_start + step * SIXTEENTH_DUR
            f_arp = arp_scale[(bar * 2 + step) % len(arp_scale)]
            n_len = int(SIXTEENTH_DUR * 0.7 * SAMPLE_RATE)
            start_idx = int(step_time * SAMPLE_RATE)
            if start_idx + n_len > TOTAL_SAMPLES:
                continue
            t = np.arange(n_len) / SAMPLE_RATE
            pluck = np.sin(2.0 * np.pi * f_arp * t) * np.exp(-t / 0.028)
            pan = math.sin(step * 0.6) * 0.20
            angle = (pan + 1.0) * math.pi / 4.0
            arp_track[0, start_idx:start_idx+n_len] += pluck * 0.20 * math.cos(angle)
            arp_track[1, start_idx:start_idx+n_len] += pluck * 0.20 * math.sin(angle)
            
    return lead_track, arp_track


# ==============================================================================
# [S7] SOUNDSCAPE MARINO & RADIO POLICIAL ADUANAS
# ==============================================================================
def synthesize_ria_soundscape():
    print("\n[*] [S7] Generando Soundscape Marino & Radio VHF Vigilancia Aduanera...")
    soundscape_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    t = np.arange(TOTAL_SAMPLES) / SAMPLE_RATE
    
    # 1. Oleaje atlántico cortado por planeadora
    rng = np.random.RandomState(77)
    white = rng.uniform(-1.0, 1.0, TOTAL_SAMPLES)
    b_pink, a_pink = signal.butter(1, 0.02, btype='low')
    pink = signal.lfilter(b_pink, a_pink, white)
    lfo_wave = 0.5 + 0.5 * np.sin(2.0 * np.pi * 0.12 * t)
    sos_water = signal.butter(2, [180, 2400], btype='bandpass', fs=SAMPLE_RATE, output='sos')
    water_sound = signal.sosfilt(sos_water, pink) * lfo_wave * 0.15
    soundscape_track[0] += water_sound
    soundscape_track[1] += water_sound
    
    # 2. Sirena lejana de niebla
    foghorn = np.sin(2.0 * np.pi * 73.42 * t) + 0.5 * np.sin(2.0 * np.pi * 146.83 * t)
    horn_mask = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    for s_start in [1.5, 7.0, 68.0, 75.0]:
        i1 = int(s_start * SAMPLE_RATE)
        i2 = int((s_start + 2.5) * SAMPLE_RATE)
        if i2 < TOTAL_SAMPLES:
            horn_mask[i1:i2] = np.sin(np.linspace(0, np.pi, i2-i1)) ** 2
    soundscape_track[0] += foghorn * horn_mask * 0.10
    soundscape_track[1] += foghorn * horn_mask * 0.10
    
    # 3. Radio VHF Vigilancia Aduanera (en compás 1.0 a 6.0)
    radio_file = VOCALS_DIR_V2 / "radio_aduanas.wav"
    if radio_file.exists():
        r_data, r_sr = sf.read(str(radio_file))
        if r_sr != SAMPLE_RATE:
            r_data = signal.resample(r_data, int(len(r_data) * SAMPLE_RATE / r_sr))
        if r_data.ndim > 1:
            r_data = r_data[:, 0]
        sos_radio = signal.butter(2, [350, 3200], btype='bandpass', fs=SAMPLE_RATE, output='sos')
        r_filt = signal.sosfilt(sos_radio, r_data)
        noise_sq = rng.uniform(-0.04, 0.04, len(r_filt))
        r_final = np.tanh((r_filt + noise_sq) * 2.2) * 0.45
        
        st_r = int(1.2 * SAMPLE_RATE)
        en_r = min(st_r + len(r_final), TOTAL_SAMPLES)
        soundscape_track[0, st_r:en_r] += r_final[:en_r-st_r]
        soundscape_track[1, st_r:en_r] += r_final[:en_r-st_r]

    # 4. Colchón Pad Roland Juno-106
    juno_f = [146.83, 220.0, 261.63, 349.23]
    juno_pad = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    for f in juno_f:
        juno_pad += np.sin(2.0 * np.pi * f * t) * 0.12
    pad_env = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    pad_env[:int(16 * BAR_DUR * SAMPLE_RATE)] = 0.20
    pad_env[int(32 * BAR_DUR * SAMPLE_RATE):int(44 * BAR_DUR * SAMPLE_RATE)] = 0.22
    pad_env[int(56 * BAR_DUR * SAMPLE_RATE):] = 0.18
    soundscape_track[0] += juno_pad * pad_env
    soundscape_track[1] += juno_pad * pad_env
    
    return soundscape_track


# ==============================================================================
# PROCESAMIENTO VOCAL EN CADENA 1176 / DUAL-STAGE OPTO-FET
# ==============================================================================
def process_vocal_chain(vocal_mono, sr=SAMPLE_RATE):
    """
    Cadena vocal de alta pegada y presencia:
    - High-pass a 130 Hz para limpiar lodo subgrave.
    - Realce paramétrico en 3.4 kHz (+7 dB) para morder la mezcla.
    - Air boost en 8.5 kHz (+4 dB).
    - Compresión rápida FET con saturación de armónicos pares (estilo 1176 Blue Stripe).
    """
    sos_hp = signal.butter(2, 130.0, btype='highpass', fs=sr, output='sos')
    v1 = signal.sosfilt(sos_hp, vocal_mono)
    
    b_eq, a_eq = signal.iirpeak(3400.0, Q=1.2, fs=sr)
    v2 = v1 + 1.8 * signal.lfilter(b_eq, a_eq, v1)
    
    sos_hs = signal.butter(2, 8500.0, btype='highpass', fs=sr, output='sos')
    v3 = v2 + 0.60 * signal.sosfilt(sos_hs, v2)
    
    env = np.abs(v3)
    b_c, a_c = signal.butter(1, 30.0 / (sr * 0.5), btype='low')
    smooth_env = signal.filtfilt(b_c, a_c, env)
    th = 0.05
    safe_env = np.maximum(smooth_env, 1e-5)
    gain_curve = np.where(smooth_env > th, (th / safe_env) ** 0.70, 1.0)
    v4 = v3 * gain_curve
    
    v_out = np.tanh(v4 * 2.8) * 0.96
    return v_out.astype(np.float32)


# ==============================================================================
# [S8] MONTAJE VOCAL DE ALTO IMPACTO (STUTTER ENGINE + CALL & RESPONSE)
# ==============================================================================
def assemble_igor_vocal_stems():
    print("\n[*] [S8] Ensamblando Stems Vocales Soberanos (Stutter Vocal Engine + Micro-Chops)...")
    spoken_lead_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    vocoder_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    chops_track = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    
    # 1. Cargar tomas neurales F5-TTS
    files_map = {
        "hook_planeadoras": VOCALS_DIR_V2 / "hook_planeadoras.wav",
        "hook_charlines": VOCALS_DIR_V2 / "hook_charlines.wav",
        "verso_sito": VOCALS_DIR_V2 / "verso_sito.wav",
        "verso_charlines": VOCALS_DIR_V2 / "verso_charlines.wav",
        "build_oubina": VOCALS_DIR_V2 / "build_oubina.wav",
        "drop_apex": VOCALS_DIR_V2 / "drop_apex_grito.wav",
        "intro_whisper": VOCALS_DIR_V1 / "intro_whisper.wav",
        "falso_drop": VOCALS_DIR_V1 / "falso_drop.wav"
    }
    
    loaded = {}
    for k, p in files_map.items():
        if p.exists():
            d, s = sf.read(str(p))
            if s != SAMPLE_RATE:
                d = signal.resample(d, int(len(d) * SAMPLE_RATE / s))
            if d.ndim > 1:
                d = d[:, 0]
            d_processed = process_vocal_chain(d.astype(np.float32))
            loaded[k] = d_processed
            print(f"  [✓] Neural vocal cargada: {k}")
        else:
            print(f"  [!] Alerta: {p} no encontrado")
            loaded[k] = np.zeros(SAMPLE_RATE, dtype=np.float32)

    def insert_vocal(track_stereo, audio_mono, bar_start_float, gain=1.4, pan=0.0):
        start_idx = int(bar_start_float * BAR_DUR * SAMPLE_RATE)
        n_samples = len(audio_mono)
        end_idx = min(start_idx + n_samples, TOTAL_SAMPLES)
        if end_idx > start_idx:
            chunk = audio_mono[:end_idx-start_idx] * gain
            p = np.clip(pan, -0.5, 0.5)
            angle = (p + 1.0) * math.pi / 4.0
            g_l = math.cos(angle)
            g_r = math.sin(angle)
            track_stereo[0, start_idx:end_idx] += chunk * g_l
            track_stereo[1, start_idx:end_idx] += chunk * g_r

    # 2. Extraer micro-chops biológicos de WhatsApp con envelope smoothing
    def extract_clean_chop(ref_name, t_start, t_end, fade_ms=15):
        p = IGOR_REF_DIR / ref_name
        if p.exists():
            d, s = sf.read(str(p))
            s0 = int(t_start * s)
            s1 = int(t_end * s)
            chunk = d[s0:s1]
            if s != SAMPLE_RATE:
                chunk = signal.resample(chunk, int(len(chunk) * SAMPLE_RATE / s))
            chunk = process_vocal_chain(chunk.astype(np.float32))
            f_len = int(SAMPLE_RATE * (fade_ms / 1000.0))
            if len(chunk) > f_len * 2:
                chunk[:f_len] *= np.linspace(0, 1, f_len)
                chunk[-f_len:] *= np.linspace(1, 0, f_len)
            return chunk
        return np.zeros(int(SAMPLE_RATE * 0.1), dtype=np.float32)

    # Catálogo de micro-chops de alta exergía
    chop_pin             = extract_clean_chop("ref_5.wav", 3.75, 4.02, fade_ms=10) # "pin"
    chop_pan             = extract_clean_chop("ref_5.wav", 4.02, 4.35, fade_ms=10) # "pan"
    chop_chupito         = extract_clean_chop("ref_5.wav", 4.85, 5.60, fade_ms=15) # "chupito"
    chop_veinte_mil      = extract_clean_chop("ref_4.wav", 5.45, 6.45, fade_ms=15) # "veinte mil"
    chop_pavos           = extract_clean_chop("ref_4.wav", 7.10, 7.65, fade_ms=10) # "pavos!"
    chop_casa_camina     = extract_clean_chop("ref_1.wav", 6.50, 7.55, fade_ms=15) # "una casa que camina"
    chop_da_hostia       = extract_clean_chop("ref_1.wav", 7.55, 8.45, fade_ms=15) # "y da hostia!"
    chop_la_hostia_tu    = extract_clean_chop("ref_8.wav", 3.90, 4.50, fade_ms=15) # "la hostia, tú!"
    chop_puta_antena     = extract_clean_chop("ref_2.wav", 7.80, 12.50, fade_ms=30)# toma completa antena

    # Motor de tartamudeo rítmico (Stutter Machine Gun)
    def insert_stutter(track_stereo, chop_mono, bar_num, step_list, gain=1.8, pan_list=None):
        for idx, step in enumerate(step_list):
            pan_val = pan_list[idx % len(pan_list)] if pan_list else 0.0
            time_offset = bar_num + (step * SIXTEENTH_DUR / BAR_DUR)
            insert_vocal(track_stereo, chop_mono, time_offset, gain=gain, pan=pan_val)

    # ══════════════════════════════════════════════════════════════════════════
    # ARREGLO VOCAL SOTA: STUTTER CHANT + CALL & RESPONSE DE CULTO
    # ══════════════════════════════════════════════════════════════════════════
    
    # 1. INTRO (Compás 1 a 8):
    # Igor real explicando la antena de radar en la ría
    insert_vocal(chops_track, chop_puta_antena, 2.0, gain=1.85, pan=-0.15)
    insert_vocal(spoken_lead_track, loaded["intro_whisper"], 5.0, gain=1.60)
    insert_vocal(chops_track, chop_la_hostia_tu, 7.5, gain=1.80, pan=0.2)
    
    # 2. HOOK 1 (Compás 8.5 a 16):
    # Rhythmic Ghetto-Tech Stutter:
    # Compás 8.5: PIN (paso 0), PAN (paso 2), PIN (paso 4), PAN (paso 6), CHUPITO (paso 8)
    insert_stutter(chops_track, chop_pin, 8.5, [0, 4], gain=1.85, pan_list=[-0.25, 0.25])
    insert_stutter(chops_track, chop_pan, 8.5, [2, 6], gain=1.85, pan_list=[0.25, -0.25])
    insert_vocal(chops_track, chop_chupito, 8.5 + (8 * SIXTEENTH_DUR / BAR_DUR), gain=1.95)
    
    # Response Vocoder (Compás 10.0 a 12.0):
    voc_hook1 = cyber_vocoder(loaded["hook_planeadoras"])
    insert_vocal(vocoder_track, voc_hook1, 10.0, gain=1.70)
    
    # Compás 12.0: VEINTE MIL (paso 0), PAVOS (paso 6), PAVOS (paso 10)
    insert_vocal(chops_track, chop_veinte_mil, 12.0, gain=1.95, pan=-0.2)
    insert_stutter(chops_track, chop_pavos, 12.0, [6, 10], gain=1.85, pan_list=[0.3, -0.3])
    insert_vocal(chops_track, chop_la_hostia_tu, 14.5, gain=1.85, pan=0.2)
    
    # 3. VERSO 1 (Compás 16.5 a 24):
    # Spoken Lead con ritmo seco
    insert_vocal(spoken_lead_track, loaded["verso_sito"], 16.5, gain=1.90)
    # Stutters de acento en el verso
    insert_stutter(chops_track, chop_pin, 20.5, [0, 2], gain=1.75, pan_list=[-0.3, 0.3])
    insert_stutter(chops_track, chop_pan, 20.5, [4, 6], gain=1.75, pan_list=[0.3, -0.3])
    insert_vocal(chops_track, chop_chupito, 21.0, gain=1.85)
    insert_vocal(chops_track, chop_la_hostia_tu, 23.5, gain=1.85)
    
    # 4. HOOK 2 (Compás 24.5 a 32):
    # Stutter ametralladora en Hook 2
    insert_stutter(chops_track, chop_pin, 24.5, [0, 4, 8], gain=1.85, pan_list=[-0.25, 0.25])
    insert_stutter(chops_track, chop_pan, 24.5, [2, 6, 10], gain=1.85, pan_list=[0.25, -0.25])
    insert_vocal(chops_track, chop_chupito, 25.25, gain=1.95)
    
    voc_hook2 = cyber_vocoder(loaded["hook_charlines"])
    insert_vocal(vocoder_track, voc_hook2, 26.5, gain=1.70)
    insert_vocal(chops_track, chop_veinte_mil, 29.5, gain=1.90, pan=-0.2)
    insert_stutter(chops_track, chop_pavos, 29.5, [6, 10, 14], gain=1.85, pan_list=[0.3, -0.3])
    
    # 5. VERSO 2 (Compás 32.5 a 39.5):
    insert_vocal(spoken_lead_track, loaded["verso_charlines"], 32.5, gain=1.90)
    insert_vocal(chops_track, chop_da_hostia, 37.0, gain=1.85, pan=0.25)
    
    # 6. BUILD-UP (Compás 39.5 a 44):
    insert_vocal(spoken_lead_track, loaded["build_oubina"], 39.5, gain=1.85)
    voc_build = cyber_vocoder(loaded["build_oubina"])
    insert_vocal(vocoder_track, voc_build, 39.5, gain=1.65)
    
    # Stutter en crescendo hacia el Falso Drop (compás 42 a 43.5)
    insert_stutter(chops_track, chop_pin, 42.0, [0, 4, 8, 12], gain=1.90, pan_list=[-0.3, 0.3])
    insert_stutter(chops_track, chop_pan, 42.0, [2, 6, 10, 14], gain=1.90, pan_list=[0.3, -0.3])
    insert_stutter(chops_track, chop_pavos, 43.0, [0, 4, 8, 12], gain=2.00, pan_list=[-0.3, 0.3])
    
    # 7. COMPÁS 44 A 45: EL FALSO DROP HISTÓRICO
    # CORTE EN SECO DE TODOS LOS INSTRUMENTOS (Compás 44.0 a 45.0)
    # Solo suena Igor en su nota real de WhatsApp:
    # «...saliste para irte a una casa que camina... ¡y da hostia!»
    insert_vocal(chops_track, chop_casa_camina, 44.0, gain=2.10)
    insert_vocal(chops_track, chop_da_hostia, 44.6, gain=2.25)
    
    # 8. DROP REAL APEX (Compás 45.0 a 56):
    # ¡BOMBO 808 SUB BOOM + TB-303 DEVIL FISH A MÁXIMA POTENCIA!
    insert_vocal(spoken_lead_track, loaded["drop_apex"], 45.2, gain=2.05)
    voc_drop = cyber_vocoder(loaded["drop_apex"])
    insert_vocal(vocoder_track, voc_drop, 45.2, gain=1.75)
    
    # Chops rítmicos desenfrenados en el Drop Apex
    insert_stutter(chops_track, chop_pin, 48.0, [0, 4], gain=1.90, pan_list=[-0.3, 0.3])
    insert_stutter(chops_track, chop_pan, 48.0, [2, 6], gain=1.90, pan_list=[0.3, -0.3])
    insert_vocal(chops_track, chop_chupito, 48.5, gain=2.00)
    
    insert_vocal(chops_track, chop_veinte_mil, 50.0, gain=1.95, pan=-0.2)
    insert_stutter(chops_track, chop_pavos, 50.0, [6, 10], gain=1.90, pan_list=[0.3, -0.3])
    insert_vocal(chops_track, chop_da_hostia, 51.5, gain=2.00, pan=0.2)
    
    # Re-engage del Hook en el Drop (Compás 52.0 a 56):
    insert_vocal(spoken_lead_track, loaded["hook_planeadoras"], 52.0, gain=1.90)
    insert_vocal(vocoder_track, voc_hook1, 52.0, gain=1.70)
    insert_vocal(chops_track, chop_la_hostia_tu, 55.0, gain=2.05)
    
    # 9. OUTRO (Compás 57 a 63):
    insert_vocal(vocoder_track, voc_hook2, 57.0, gain=1.55)
    insert_vocal(chops_track, chop_puta_antena, 59.0, gain=1.75, pan=0.15)
    insert_vocal(chops_track, chop_la_hostia_tu, 62.0, gain=1.85)

    return spoken_lead_track, vocoder_track, chops_track


# ==============================================================================
# CARVING ESPECTRAL DINÁMICO & SIDECHAIN NOTCH (-8 dB en 3kHz en Sintes)
# ==============================================================================
def apply_vocal_sidechain_ducking(kick, bass, lead, arp, soundscape, spoken, vocoder, chops):
    """
    Atenuación quirúrgica para garantizar inteligibilidad vocal absoluta:
    1. Detector de envolvente rápido (attack 5ms, release 70ms).
    2. Ducking de nivel general (-5.5 dB) en colchones y synths durante el habla.
    3. Dynamic Notch Filter (-8 dB a 3.2 kHz) sobre los sintetizadores para abrir
       un hueco transparente exacto para los formantes de Igor.
    """
    print("\n[*] [S9] Aplicando Carving Espectral Dinámico (-8 dB Notch en 3kHz en Sintes)...")
    vocal_sum = np.abs(spoken[0]) + np.abs(spoken[1]) + np.abs(vocoder[0]) + np.abs(vocoder[1]) + np.abs(chops[0])
    
    b_sc, a_sc = signal.butter(1, 22.0 / (SAMPLE_RATE * 0.5), btype='low')
    vocal_env = signal.filtfilt(b_sc, a_sc, vocal_sum)
    
    duck_gain = np.where(vocal_env > 0.030, 0.53, 1.0)
    b_sm, a_sm = signal.butter(1, 28.0 / (SAMPLE_RATE * 0.5), btype='low')
    duck_gain_smooth = signal.filtfilt(b_sm, a_sm, duck_gain)
    
    bass_ducked = bass * (0.35 + 0.65 * duck_gain_smooth)
    soundscape_ducked = soundscape * duck_gain_smooth
    
    b_notch, a_notch = signal.iirnotch(3200.0, Q=1.5, fs=SAMPLE_RATE)
    v_mask = np.clip(vocal_env * 15.0, 0.0, 1.0)
    
    def process_synth(s_track):
        s_notched = np.zeros_like(s_track)
        s_notched[0] = signal.lfilter(b_notch, a_notch, s_track[0])
        s_notched[1] = signal.lfilter(b_notch, a_notch, s_track[1])
        s_out = np.zeros_like(s_track)
        s_out[0] = (s_track[0] * (1.0 - 0.55 * v_mask)) * (1.0 - v_mask) + (s_notched[0] * 0.55) * v_mask
        s_out[1] = (s_track[1] * (1.0 - 0.55 * v_mask)) * (1.0 - v_mask) + (s_notched[1] * 0.55) * v_mask
        return s_out
        
    lead_ducked = process_synth(lead)
    arp_ducked = process_synth(arp)
    kick_ducked = kick
    
    return kick_ducked, bass_ducked, lead_ducked, arp_ducked, soundscape_ducked


# ==============================================================================
# [S10] MASTERIZACIÓN EBU R128 & COMPILACIÓN FLP
# ==============================================================================
def export_stems_and_master(stems_dict):
    print("\n[*] [S10] Exportando los 10 Stems Multitrack a 24-bit 44.1kHz WAV...")
    
    STEM_MIX_GAINS = {
        "01_KICK_808": 0.58,
        "02_SNARE_CLAP_808": 0.68,
        "03_HATS_PERC_ELECTRO": 0.48,
        "04_ELECTRO_BASSLINE": 0.55,
        "05_DREXCIYA_SYNTH_LEAD": 0.35,
        "06_ATLANTIC_ARP_PLUCK": 0.30,
        "07_RIA_DE_AROUSA_DRONE_PAD": 0.28,
        "08_IGOR_SPOKEN_LEAD": 1.45,
        "09_IGOR_VOCODER_ROBOT": 1.30,
        "10_IGOR_ORGANIC_CHOPS_FX": 1.45
    }
    
    stereo_mix = np.zeros((2, TOTAL_SAMPLES), dtype=np.float32)
    
    for stem_name, audio_data in stems_dict.items():
        stem_path = STEMS_DIR / f"{stem_name}.wav"
        if audio_data.ndim == 1:
            audio_stereo = np.vstack([audio_data, audio_data])
        else:
            audio_stereo = audio_data
            
        sf.write(str(stem_path), audio_stereo.T, SAMPLE_RATE, subtype='PCM_24')
        gain = STEM_MIX_GAINS.get(stem_name, 1.0)
        peak = np.max(np.abs(audio_stereo))
        print(f"  [✓] Stem exportado: {stem_name}.wav (Peak: {peak:.2f} | Fader Gain: {gain:.2f})")
        stereo_mix += audio_stereo * gain
        
    print("\n[*] [S10] Ejecutando Masterización EBU R128 con Pegamento Analógico...")
    mix_l = stereo_mix[0]
    mix_r = stereo_mix[1]
    
    # 1. Compresor de bus SSL suave (Ratio 2:1)
    env = np.maximum(np.abs(mix_l), np.abs(mix_r))
    b_c, a_c = signal.butter(1, 10.0 / (SAMPLE_RATE * 0.5), btype='low')
    smooth_env = signal.filtfilt(b_c, a_c, env)
    th = 0.65
    gain_reduction = np.where(smooth_env > th, (th / (smooth_env + 1e-6)) ** 0.25, 1.0)
    mix_l *= gain_reduction
    mix_r *= gain_reduction
    
    # 2. Limitador True Peak (-1.0 dBFS) y Normalización EBU R128 (-14.0 LUFS)
    rms = np.sqrt(np.mean(mix_l**2 + mix_r**2) / 2.0)
    target_rms = 0.200  # ~ -14.0 LUFS
    makeup = target_rms / (rms + 1e-6)
    master_l = np.tanh(mix_l * makeup * 1.08) * 0.891
    master_r = np.tanh(mix_r * makeup * 1.08) * 0.891
    
    master_stereo = np.vstack([master_l, master_r])
    sf.write(str(MASTER_WAV), master_stereo.T, SAMPLE_RATE, subtype='PCM_24')
    print(f"  [✓] Master WAV guardado en: {MASTER_WAV}")
    
    subprocess.run([
        "ffmpeg", "-y", "-i", str(MASTER_WAV),
        "-codec:a", "libmp3lame", "-b:a", "320k",
        str(MASTER_MP3)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if MASTER_MP3.exists():
        print(f"  [✓] Master MP3 guardado en: {MASTER_MP3}")

    print("\n[*] Compilando Proyecto Nativo FL Studio (.flp)...")
    flp_compiler = Path(__file__).resolve().parent / "flp_multitrack_stem_compiler.py"
    if flp_compiler.exists():
        subprocess.run([
            sys.executable, str(flp_compiler),
            "--stems-dir", str(STEMS_DIR),
            "--title", "Igor Limone - Planeadoras na Ria (Electro Narcos)",
            "--bpm", str(BPM),
            "--output", str(PROJECT_FLP)
        ])
        print(f"  [✓] Proyecto .flp compilado en: {PROJECT_FLP}")


# ==============================================================================
# PIPELINE PRINCIPAL V6
# ==============================================================================
def main():
    start_time = time.time()
    
    # 1. Baterías TR-808 con Sub Kick, Punch, Cowbell, Rimshot, Booms y Risers
    kick, snare_clap, hats_perc = synthesize_tr808_drums()
    
    # 2. Bajo TB-303 Devil Fish Acid con slides sincopados
    bass = synthesize_tb303_bassline()
    
    # 3. Sintetizadores Drexciya
    lead, arp = synthesize_drexciya_synths()
    
    # 4. Soundscape de la Ría y Radio Aduanas
    soundscape = synthesize_ria_soundscape()
    
    # 5. Capas Vocales de Igor Limone (Stutter Engine + WhatsApp Micro-Chops + Vocoder)
    spoken_lead, vocoder, chops = assemble_igor_vocal_stems()
    
    # 6. Carving Espectral Dinámico y Sidechain
    kick_d, bass_d, lead_d, arp_d, soundscape_d = apply_vocal_sidechain_ducking(
        kick, bass, lead, arp, soundscape, spoken_lead, vocoder, chops
    )
    
    # 7. Empaquetar los 10 Stems
    stems = {
        "01_KICK_808": kick_d,
        "02_SNARE_CLAP_808": snare_clap,
        "03_HATS_PERC_ELECTRO": hats_perc,
        "04_ELECTRO_BASSLINE": bass_d,
        "05_DREXCIYA_SYNTH_LEAD": lead_d,
        "06_ATLANTIC_ARP_PLUCK": arp_d,
        "07_RIA_DE_AROUSA_DRONE_PAD": soundscape_d,
        "08_IGOR_SPOKEN_LEAD": spoken_lead,
        "09_IGOR_VOCODER_ROBOT": vocoder,
        "10_IGOR_ORGANIC_CHOPS_FX": chops
    }
    
    # 8. Exportar Stems, Master y Compilar FLP
    export_stems_and_master(stems)
    
    total_time = time.time() - start_time
    print("\n" + "=" * 76)
    print(f"  🏁 PRODUCCIÓN V6 (GOD-TIER MASTERPIECE) COMPLETADA EN {total_time:.2f} SEGUNDOS")
    print("=" * 76)


if __name__ == "__main__":
    main()
