#!/usr/bin/env python3
"""
Dark Cyber-Flamenco 7:20 Club de Culto Edition (Avant-Garde, Bailable, Palmas Protagonistas)
═════════════════════════════════════════════════════════════════════════════════════════════
Diseñado para Soundsystem de Club de Culto (Berghain / Tresor / Fabric / Dekmantel / Warp).
Cero comercial tech-house de Ibiza. Hipnosis polirrítmica bailable, peso pesado en 48 Hz,
palmas flamencas vivas con micro-swing de Jerez como motor rítmico central y diseño sonoro
avant-garde (TB-303 Devil Fish, guitarra de ciprés dub stabs, piano preparado y micro-glitch).

Métricas:
- Tempo: 130.0 BPM sólido de pista de baile.
- Duración: 440.0s (7:20 exactos).
- Polirritmia: Compás de Bulería (12 tiempos) sincronizado sobre rejilla hipnótica 4/4.
- Falso Drop a las 5:00 con vacío de cinta y palmas desnudas.
- Master Stereo PCM 24-bit 44.1kHz + 10 Stems + Proyecto FL Studio (.flp).
"""

import sys
import time
import numpy as np
import soundfile as sf
from pathlib import Path
import scipy.signal as signal

SAMPLE_RATE = 44100
DURATION_SEC = 440.0  # 7:20 exactos
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION_SEC)
BPM = 130.0
BEAT_SEC = 60.0 / BPM
SIXTEENTH_SEC = BEAT_SEC / 4.0

print("=== Compilando Versión Club de Culto (130 BPM, Avant-Garde, Palmas Protagonistas) ===")

# ── 1. MODELADO FÍSICO DE PALMAS FLAMENCAS (MOTOR RÍTMICO CENTRAL) ────
def synthesize_palma_flamenca_raw(seca=True, sr=SAMPLE_RATE):
    """Genera una muestra acústica individual de palma flamenca (piel contra piel)."""
    dur = 0.14 if seca else 0.22
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    # Excitación estocástica de choque palmar
    noise = np.random.uniform(-1.0, 1.0, n).astype(np.float32)
    
    if seca:
        # Palma seca: chasquido agudo, brillante, cortante (1400-2800 Hz)
        b, a = signal.iirpeak(1650.0, Q=3.5, fs=sr)
        filtered = signal.lfilter(b, a, noise)
        env = np.exp(-t * 52.0)
        # Rebote de dedos
        rebound = int(sr * 0.007)
        if rebound < n:
            env[rebound:] += 0.45 * np.exp(-t[:-rebound] * 68.0)
        return (filtered * env * 1.1).astype(np.float32)
    else:
        # Palma sorda: cuenco de la mano, grave, hueca, torácica (650-950 Hz)
        b, a = signal.iirpeak(780.0, Q=2.8, fs=sr)
        filtered = signal.lfilter(b, a, noise)
        env = np.exp(-t * 28.0)
        rebound = int(sr * 0.010)
        if rebound < n:
            env[rebound:] += 0.35 * np.exp(-t[:-rebound] * 42.0)
        return (filtered * env * 0.95).astype(np.float32)

# ── 2. BOMBO ANALÓGICO PESADO DE CLUB DE CULTO (48 HZ SEISMIC) ────────
def synthesize_club_kick(sr=SAMPLE_RATE):
    """Bombo analógico de hormigón: transitorio de madera + barrido sísmico a 48 Hz."""
    dur = 0.42
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    # Barrido de frecuencia exponencial (160 Hz -> 48 Hz)
    f_env = 48.0 + 115.0 * np.exp(-t * 32.0)
    phase = 2.0 * np.pi * np.cumsum(f_env) / sr
    click = 0.42 * np.sin(2.0 * np.pi * 1100.0 * t) * np.exp(-t * 180.0)
    body = (np.sin(phase) + click) * np.exp(-t * 8.5)
    # Saturación suave de transformador
    return np.tanh(body * 1.55).astype(np.float32)

# ── 3. CAJÓN FLAMENCO Y SUBGRAVE ROLLING ──────────────────────────────
def synthesize_cajon_hit(grave=True, sr=SAMPLE_RATE):
    dur = 0.28 if grave else 0.18
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    if grave:
        f_env = 75.0 * np.exp(-t * 16.0) + 44.0
        phase = 2.0 * np.pi * np.cumsum(f_env) / sr
        body = np.sin(phase) * np.exp(-t * 14.0)
        thump = 0.3 * np.random.uniform(-1, 1, n) * np.exp(-t * 90.0)
        return np.tanh((body + thump) * 1.3).astype(np.float32)
    else:
        noise = np.random.uniform(-1, 1, n).astype(np.float32)
        b, a = signal.iirpeak(3200.0, Q=3.8, fs=sr)
        snare = signal.lfilter(b, a, noise) * np.exp(-t * 30.0)
        click = np.sin(2.0 * np.pi * 1900.0 * t) * np.exp(-t * 140.0) * 0.4
        return np.tanh((snare + click) * 1.4).astype(np.float32)

def synthesize_rolling_sub_note(f0, duration, sr=SAMPLE_RATE):
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False, dtype=np.float32)
    fund = np.sin(2.0 * np.pi * f0 * t)
    h2 = 0.45 * np.sin(2.0 * np.pi * (f0 * 2.0) * t)
    env = np.exp(-t * 4.5)
    return (np.tanh((fund + h2) * 1.3) * env * 0.85).astype(np.float32)

# ── 4. TB-303 DEVIL FISH ACID BASS Y STABS DE GUITARRA ────────────────
def synthesize_acid_note(f0, dur, accent=False, slide=False, cutoff=900.0, res=0.82, sr=SAMPLE_RATE):
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    phase = 2.0 * np.pi * f0 * t
    saw = 2.0 * (phase / (2.0 * np.pi) - np.floor(phase / (2.0 * np.pi) + 0.5))
    tau = 0.08 if accent else 0.18
    env_f = np.exp(-t / tau)
    fc = np.clip(cutoff + (3000.0 if accent else 1200.0) * env_f, 60.0, sr * 0.42)
    b, a = signal.butter(4, min(np.mean(fc) / (sr * 0.5), 0.90), btype='low')
    filtered = signal.lfilter(b, a, saw)
    gain = 2.0 if accent else 1.3
    drive = np.tanh(filtered * (gain + res * 1.5))
    return (drive * np.exp(-t / (0.14 if accent else 0.28)) * (1.2 if accent else 0.85)).astype(np.float32)

def synthesize_guitar_dub_stab(chord_freqs, dur=0.35, sr=SAMPLE_RATE):
    """Guitarra de ciprés procesada como dub stab staccato para club de culto."""
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    stab = np.zeros(n, dtype=np.float32)
    for i, f in enumerate(chord_freqs):
        pluck = np.sin(2.0 * np.pi * f * t) * np.exp(-t * (18.0 + i * 2.0))
        stab += pluck
    # Paso-banda analógico y saturación
    b, a = signal.butter(2, [350.0 / (sr * 0.5), 3200.0 / (sr * 0.5)], btype='band')
    filtered = signal.lfilter(b, a, stab)
    return np.tanh(filtered * 1.4).astype(np.float32)

# ── 5. PREPARED PIANO INHARMÓNICO Y GLITCH MODULAR ────────────────────
def synthesize_prepared_piano_note(f0, dur=0.6, sr=SAMPLE_RATE):
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    partials = [1.0, 2.31, 3.84, 5.22]
    amps = [1.0, 0.65, 0.38, 0.20]
    out = np.zeros(n, dtype=np.float32)
    for p_f, p_a in zip(partials, amps):
        freq = f0 * p_f
        if freq < sr * 0.44:
            out += p_a * np.sin(2.0 * np.pi * freq * t) * np.exp(-t * (5.0 * p_f))
    hammer = np.sin(2.0 * np.pi * 180.0 * t) * np.exp(-t * 90.0) * 0.3
    return np.tanh((out + hammer) * 1.2).astype(np.float32)

def synthesize_afx_drill_click(sr=SAMPLE_RATE):
    dur = 0.012
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    f_sweep = 5200.0 * np.exp(-t * 400.0) + 60.0
    phase = 2.0 * np.pi * np.cumsum(f_sweep) / sr
    return (np.sin(phase) * np.exp(-t * 300.0)).astype(np.float32)

def synthesize_909_hat(open_hat=False, sr=SAMPLE_RATE):
    dur = 0.28 if open_hat else 0.06
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    noise = np.random.uniform(-1, 1, n).astype(np.float32)
    b, a = signal.butter(2, 6800.0 / (sr * 0.5), btype='high')
    decay = 14.0 if open_hat else 75.0
    return (signal.lfilter(b, a, noise) * np.exp(-t * decay)).astype(np.float32)

# ── 6. COMPILACIÓN PRINCIPAL DEL MASTER Y STEMS ────────────────────────
def render_dark_cyber_flamenco_club_culto():
    t0 = time.time()
    print("[1/5] Inicializando buffers de stems (7:20 @ 130.0 BPM)...")
    
    stem_kick = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_palmas_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_palmas_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_cajon = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_subbass = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_acid_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_acid_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_guitar_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_guitar_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_drill_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_drill_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_piano_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_piano_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_hats = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_drone_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_drone_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

    # Pre-renderizar elementos en memoria para velocidad ultra-rápida
    print("[2/5] Pre-renderizando bibliotecas de transitorios analógicos y palmas...")
    kick_sound = synthesize_club_kick(SAMPLE_RATE)
    cajon_g = synthesize_cajon_hit(grave=True, sr=SAMPLE_RATE)
    cajon_a = synthesize_cajon_hit(grave=False, sr=SAMPLE_RATE)
    palma_s = synthesize_palma_flamenca_raw(seca=True, sr=SAMPLE_RATE)
    palma_h = synthesize_palma_flamenca_raw(seca=False, sr=SAMPLE_RATE)
    hat_closed = synthesize_909_hat(open_hat=False, sr=SAMPLE_RATE)
    hat_open = synthesize_909_hat(open_hat=True, sr=SAMPLE_RATE)
    drill_click = synthesize_afx_drill_click(SAMPLE_RATE)
    
    # Acordes en Mi Frigio
    chords_freqs = {
        "Am": [110.0, 164.81, 220.0, 261.63],
        "G":  [98.0, 146.83, 196.0, 246.94],
        "F":  [87.31, 130.81, 174.61, 220.0],
        "E":  [82.41, 123.47, 164.81, 207.65]
    }
    chord_names = ["Am", "G", "F", "E"]
    acid_scale = [41.20, 82.41, 87.31, 103.83, 110.0, 123.47, 130.81, 164.81]
    piano_scale = [207.65, 246.94, 329.63, 415.30, 493.88, 659.25]

    total_beats = int(DURATION_SEC / BEAT_SEC)
    total_sixteenths = total_beats * 4
    print(f"[*] Total pulsos 130 BPM a secuenciar: {total_beats} beats ({total_sixteenths} semicorcheas)")

    # Micro-swing de Jerez para el compás de 12 (en ms)
    buleria_swing_ms = [0.0, 2.5, -3.5, 1.0, 3.0, -4.0, 1.5, -2.5, 2.0, -4.5, 1.0, -3.0]
    buleria_accents = {2, 5, 7, 9, 11} # 3, 6, 8, 10, 12

    print("[3/5] Ensamblando la polirritmia de 12 tiempos sobre el 4/4 bailable...")
    kick_indices = []

    # 1. LOOP PRINCIPAL DE TIEMPO (130 BPM GRID)
    for step in range(total_sixteenths):
        time_sec = step * SIXTEENTH_SEC
        if time_sec >= DURATION_SEC:
            break
        base_sample = int(time_sec * SAMPLE_RATE)
        
        is_downbeat_quarter = (step % 4 == 0)
        beat_idx = step // 4
        bar_idx = beat_idx // 4
        
        # Mapeo al ciclo de 12 tiempos de Bulería
        buleria_idx = step % 12
        is_buleria_accent = buleria_idx in buleria_accents
        
        # Secciones temporales de la pista
        in_intro = (time_sec < 45.0)
        in_fake_drop = (298.0 <= time_sec < 308.0)  # EL FALSO DROP (5:00)
        in_apex_climax = (time_sec >= 308.0)        # CLÍMAX APEX (5:08 - 7:20)
        
        # Jitter micro-swing de Jerez
        ms_jitter = buleria_swing_ms[buleria_idx]
        jitter_samp = int(SAMPLE_RATE * (ms_jitter / 1000.0))
        idx = max(0, min(TOTAL_SAMPLES - 1, base_sample + jitter_samp))

        # ─────────────────────────────────────────────────────────────
        # A. BOMBO DE CLUB (48 HZ SEISMIC)
        # ─────────────────────────────────────────────────────────────
        if not in_fake_drop and not in_intro:
            trig_kick = False
            # Bombo en 4/4 sólido para tracción bailable
            if is_downbeat_quarter:
                trig_kick = True
            # Bombos sincopados adicionales en los acentos de la bulería (Polirritmia bailable)
            elif in_apex_climax and (buleria_idx in (2, 7, 10)) and (step % 2 == 0):
                trig_kick = True
                
            if trig_kick:
                k_gain = 0.95 if in_apex_climax else (0.80 if time_sec < 75.0 else 0.90)
                rem = min(len(kick_sound), TOTAL_SAMPLES - idx)
                stem_kick[idx : idx + rem] += kick_sound[:rem] * k_gain
                kick_indices.append(idx)
        elif in_intro and time_sec >= 22.0 and is_downbeat_quarter:
            # Bombo filtrado en la intro para que el DJ mezcle
            rem = min(len(kick_sound), TOTAL_SAMPLES - idx)
            stem_kick[idx : idx + rem] += kick_sound[:rem] * 0.45

        # ─────────────────────────────────────────────────────────────
        # B. PALMAS FLAMENCAS (MOTOR RÍTMICO PROTAGONISTA)
        # ─────────────────────────────────────────────────────────────
        # Las palmas suenan SIEMPRE, incluso en el falso drop (palmas al descubierto)
        trig_palma = False
        palma_is_seca = False
        
        # Palmas sordas dan el soniquete continuo en semicorcheas sincopadas
        if step % 2 == 1 or buleria_idx in (1, 4, 6, 8):
            trig_palma = True
            palma_is_seca = False
        # Palmas secas azotan en los acentos 3, 6, 8, 10, 12 y cierres
        if is_buleria_accent or (in_apex_climax and buleria_idx == 11):
            trig_palma = True
            palma_is_seca = True
            
        if trig_palma:
            p_source = palma_s if palma_is_seca else palma_h
            rem = min(len(p_source), TOTAL_SAMPLES - idx)
            vol_p = (1.05 if palma_is_seca else 0.72) * (1.15 if in_fake_drop else 0.95)
            # Paneo estéreo de cuadro flamenco (dos palmeros enfrentados)
            stem_palmas_l[idx : idx + rem] += p_source[:rem] * vol_p * 0.95
            stem_palmas_r[idx : idx + rem] += p_source[:rem] * vol_p * 1.05

        # ─────────────────────────────────────────────────────────────
        # C. CAJÓN FLAMENCO Y HATS DE 909
        # ─────────────────────────────────────────────────────────────
        if not in_fake_drop:
            # Cajón grave reforzando el golpe 12 y contratiempos
            if buleria_idx == 11 and step % 2 == 0:
                rem = min(len(cajon_g), TOTAL_SAMPLES - idx)
                stem_cajon[idx : idx + rem] += cajon_g[:rem] * 0.88
            elif is_buleria_accent:
                rem = min(len(cajon_a), TOTAL_SAMPLES - idx)
                stem_cajon[idx : idx + rem] += cajon_a[:rem] * 0.75
                
            # Hi-hats 909 en los off-beats (clásico de club hipnótico)
            if step % 4 == 2 and time_sec >= 30.0:
                rem = min(len(hat_open), TOTAL_SAMPLES - idx)
                stem_hats[idx : idx + rem] += hat_open[:rem] * (0.65 if in_apex_climax else 0.45)
            elif step % 2 == 1 and time_sec >= 60.0:
                rem = min(len(hat_closed), TOTAL_SAMPLES - idx)
                stem_hats[idx : idx + rem] += hat_closed[:rem] * 0.35

        # ─────────────────────────────────────────────────────────────
        # D. SUBGRAVE ROLLING 130 BPM (PESO EN 41.2 HZ / MI FRIGIO)
        # ─────────────────────────────────────────────────────────────
        if not in_fake_drop and (time_sec >= 15.0):
            # Línea de bajo galopante en 16avas
            f_sub = 41.20 if (bar_idx % 4 == 3) else (43.65 if (bar_idx % 4 == 2) else 55.0)
            if step % 2 == 0:
                sub_note = synthesize_rolling_sub_note(f_sub, SIXTEENTH_SEC * 1.8, SAMPLE_RATE)
                rem = min(len(sub_note), TOTAL_SAMPLES - idx)
                sub_gain = 0.90 if in_apex_climax else 0.75
                stem_subbass[idx : idx + rem] += sub_note[:rem] * sub_gain

        # ─────────────────────────────────────────────────────────────
        # E. TB-303 DEVIL FISH ACID (RESONANCIA Y SLIDES)
        # ─────────────────────────────────────────────────────────────
        if not in_fake_drop and (time_sec >= 45.0):
            play_acid = is_buleria_accent or (in_apex_climax and step % 2 == 1)
            if play_acid:
                f_a = acid_scale[(bar_idx * 3 + buleria_idx) % len(acid_scale)]
                res_val = 0.88 if in_apex_climax else 0.70
                cut_base = (1400.0 if in_apex_climax else 700.0) + 600.0 * np.sin(step * 0.08) ** 2
                acid_h = synthesize_acid_note(
                    f_a, SIXTEENTH_SEC * 1.5,
                    accent=is_buleria_accent,
                    slide=(buleria_idx in (5, 9)),
                    cutoff=cut_base, res=res_val, sr=SAMPLE_RATE
                )
                rem = min(len(acid_h), TOTAL_SAMPLES - idx)
                gain_a = 0.75 if in_apex_climax else 0.55
                stem_acid_l[idx : idx + rem] += acid_h[:rem] * gain_a
                stem_acid_r[idx : idx + rem] += acid_h[:rem] * gain_a * 0.92

        # ─────────────────────────────────────────────────────────────
        # F. GUITARRA DE CIPRÉS (DUB STABS STACCATO)
        # ─────────────────────────────────────────────────────────────
        if in_fake_drop:
            # En el Falso Drop: Stabs solos y rasgueados desvergonzados
            if is_downbeat_quarter and (step % 8 == 0):
                c_curr = chord_names[bar_idx % 4]
                stab = synthesize_guitar_dub_stab(chords_freqs[c_curr], dur=0.55, sr=SAMPLE_RATE)
                rem = min(len(stab), TOTAL_SAMPLES - idx)
                stem_guitar_l[idx : idx + rem] += stab[:rem] * 1.10
                stem_guitar_r[idx : idx + rem] += stab[:rem] * 1.10
        elif not in_intro and (step % 8 == 4):
            # Dub stab en el contratiempo bailable
            c_curr = chord_names[bar_idx % 4]
            stab = synthesize_guitar_dub_stab(chords_freqs[c_curr], dur=0.35, sr=SAMPLE_RATE)
            rem = min(len(stab), TOTAL_SAMPLES - idx)
            stem_guitar_l[idx : idx + rem] += stab[:rem] * 0.75
            stem_guitar_r[idx : idx + rem] += stab[:rem] * 0.85

        # ─────────────────────────────────────────────────────────────
        # G. PREPARED PIANO AVANT-GARDE & AFX DRILL CLICKS
        # ─────────────────────────────────────────────────────────────
        if (time_sec >= 60.0 and buleria_idx in (3, 8)) or (in_fake_drop and buleria_idx in (1, 6, 10)):
            p_f = piano_scale[(step // 3) % len(piano_scale)]
            p_hit = synthesize_prepared_piano_note(p_f, dur=0.45, sr=SAMPLE_RATE)
            rem = min(len(p_hit), TOTAL_SAMPLES - idx)
            p_gain = 0.85 if in_fake_drop else 0.58
            stem_piano_l[idx : idx + rem] += p_hit[:rem] * p_gain * 0.8
            stem_piano_r[idx : idx + rem] += p_hit[:rem] * p_gain * 1.2

        if (time_sec >= 90.0 and step % 4 == 3) or (in_apex_climax and step % 2 == 1):
            rem = min(len(drill_click), TOTAL_SAMPLES - idx)
            pan = 1.0 if step % 2 == 0 else -1.0
            stem_drill_l[idx : idx + rem] += drill_click[:rem] * (1.0 - 0.3 * pan) * 0.60
            stem_drill_r[idx : idx + rem] += drill_click[:rem] * (1.0 + 0.3 * pan) * 0.60

    # ─────────────────────────────────────────────────────────────────
    # 2. CAPA DRONE DUB GRANULAR DE FONDO
    # ─────────────────────────────────────────────────────────────────
    print("[4/5] Sintetizando atmósfera dub granular y latidos somáticos...")
    t_full = np.linspace(0, DURATION_SEC, TOTAL_SAMPLES, endpoint=False, dtype=np.float32)
    # Acorde flotante Mi Frigio (E2, B2, E3, G#3)
    drone_f = [82.41, 123.47, 164.81, 207.65]
    for i, df in enumerate(drone_f):
        osc = np.sin(2.0 * np.pi * df * t_full) * 0.035
        lfo = 0.5 + 0.5 * np.sin(2.0 * np.pi * 0.05 * t_full + i)
        stem_drone_l += osc * lfo
        stem_drone_r += osc * (1.0 - lfo)

    # ─────────────────────────────────────────────────────────────────
    # 3. TAPE STOP EN 298.0s - 298.3s Y PULSOS SOMÁTICOS EN FALSO DROP
    # ─────────────────────────────────────────────────────────────────
    stop_idx = int(298.0 * SAMPLE_RATE)
    stop_len = int(0.28 * SAMPLE_RATE)
    t_stop = np.linspace(1.0, 0.0, stop_len, dtype=np.float32)
    for st in [stem_kick, stem_subbass, stem_acid_l, stem_acid_r, stem_hats, stem_cajon]:
        st[stop_idx : stop_idx + stop_len] *= t_stop
        st[stop_idx + stop_len : int(308.0 * SAMPLE_RATE)] = 0.0

    heartbeats = [299.5, 301.5, 303.5, 305.5, 307.2]
    for hb_t in heartbeats:
        h_idx = int(hb_t * SAMPLE_RATE)
        h_dur = 0.35
        h_len = int(h_dur * SAMPLE_RATE)
        t_h = np.linspace(0, h_dur, h_len, endpoint=False, dtype=np.float32)
        hb_sound = np.sin(2.0 * np.pi * 48.0 * t_h) * np.exp(-t_h * 16.0) * 0.85
        rem = min(h_len, TOTAL_SAMPLES - h_idx)
        stem_kick[h_idx : h_idx + rem] += hb_sound[:rem]

    # ─────────────────────────────────────────────────────────────────
    # 4. DUCKING SIDECHAIN CAUSAL DEL KICK A BAJOS Y DELAYS
    # ─────────────────────────────────────────────────────────────────
    duck_samples = int(SAMPLE_RATE * 0.042)
    duck_curve = np.linspace(0.18, 1.0, duck_samples, dtype=np.float32) ** 1.8
    for k_idx in kick_indices:
        rem = min(duck_samples, TOTAL_SAMPLES - k_idx)
        stem_subbass[k_idx : k_idx + rem] *= duck_curve[:rem]
        stem_acid_l[k_idx : k_idx + rem] *= duck_curve[:rem]
        stem_acid_r[k_idx : k_idx + rem] *= duck_curve[:rem]
        stem_drone_l[k_idx : k_idx + rem] *= duck_curve[:rem]
        stem_drone_r[k_idx : k_idx + rem] *= duck_curve[:rem]

    # ─────────────────────────────────────────────────────────────────
    # 5. MASTERIZACIÓN Y LIMITACIÓN TRUE-PEAK (-1.0 dBFS)
    # ─────────────────────────────────────────────────────────────────
    print("[5/5] Sumando stems a Master Stereo de 24 bits...")
    master_l = (
        stem_kick * 0.92 +
        stem_palmas_l * 0.95 +
        stem_cajon * 0.75 +
        stem_subbass * 0.88 +
        stem_acid_l * 0.70 +
        stem_guitar_l * 0.75 +
        stem_drill_l * 0.60 +
        stem_piano_l * 0.65 +
        stem_hats * 0.55 +
        stem_drone_l * 0.40
    )
    master_r = (
        stem_kick * 0.92 +
        stem_palmas_r * 0.95 +
        stem_cajon * 0.75 +
        stem_subbass * 0.88 +
        stem_acid_r * 0.70 +
        stem_guitar_r * 0.75 +
        stem_drill_r * 0.60 +
        stem_piano_r * 0.65 +
        stem_hats * 0.55 +
        stem_drone_r * 0.40
    )

    # Soft clipping analógico
    master_l = np.tanh(master_l * 0.80)
    master_r = np.tanh(master_r * 0.80)

    max_p = max(np.max(np.abs(master_l)), np.max(np.abs(master_r)))
    target_p = 0.891  # -1.0 dBFS
    if max_p > 0:
        gain = target_p / max_p
        master_l *= gain
        master_r *= gain

    stereo_master = np.vstack((master_l, master_r)).T

    # Directorios canónicos
    bounces_dir = Path("/Users/borjafernandezangulo/Music/LIBRARY/04-Stems/FL_Studio/Bounces")
    stems_dir = bounces_dir / "BORJA_MOSKV_Buleria_de_Chentsov_OMEGA_STEMS"
    stems_dir.mkdir(parents=True, exist_ok=True)
    projects_dir = bounces_dir / "Projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    master_path = bounces_dir / "BORJA MOSKV - Bulería de Chentsov Ω [7:20].wav"
    print(f"[*] Guardando Master Stereo Oficial en: {master_path}")
    sf.write(str(master_path), stereo_master, SAMPLE_RATE, subtype='PCM_24')

    # Guardar 10 discrete stems
    stems_dict = {
        "01_Kick_Club_Culto_48Hz.wav": np.vstack((stem_kick, stem_kick)).T,
        "02_Palmas_Flamencas_Secas_Sordas.wav": np.vstack((stem_palmas_l, stem_palmas_r)).T,
        "03_Cajon_Bulerias_Groove.wav": np.vstack((stem_cajon, stem_cajon)).T,
        "04_SubBass_Rolling_130BPM.wav": np.vstack((stem_subbass, stem_subbass)).T,
        "05_TB303_DevilFish_Acid_Rhythm.wav": np.vstack((stem_acid_l, stem_acid_r)).T,
        "06_Guitarra_Cipres_Dub_Stabs.wav": np.vstack((stem_guitar_l, stem_guitar_r)).T,
        "07_AFX_Drill_Glitch_Percussion.wav": np.vstack((stem_drill_l, stem_drill_r)).T,
        "08_Prepared_Piano_Arp_AvantGarde.wav": np.vstack((stem_piano_l, stem_piano_r)).T,
        "09_Modular_Clicks_Hats_909.wav": np.vstack((stem_hats, stem_hats)).T,
        "10_Granular_Drone_Dub_Chords.wav": np.vstack((stem_drone_l, stem_drone_r)).T
    }

    print(f"[*] Exportando 10 stems de club a: {stems_dir}")
    for fname, data in stems_dict.items():
        p_stem = stems_dir / fname
        peak_s = np.max(np.abs(data))
        if peak_s > 0.95:
            data = data * (0.891 / peak_s)
        sf.write(str(p_stem), data, SAMPLE_RATE, subtype='PCM_24')
        print(f"    ✓ {fname}")

    # Compilar proyecto FL Studio (.flp)
    flp_path = projects_dir / "BORJA_MOSKV_Buleria_de_Chentsov_OMEGA_720.flp"
    try:
        sys.path.insert(0, "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp")
        from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp
        print(f"[*] Compilando proyecto FL Studio en: {flp_path}")
        compile_multitrack_stems_flp(
            stems_dir=str(stems_dir),
            project_title="BORJA MOSKV - Buleria de Chentsov Omega [7:20]",
            bpm=130.0,
            output_flp=str(flp_path),
            total_bars=int(total_beats / 4)
        )
        print(f"[✓] FLP COMPILADO: {flp_path}")
    except Exception as e:
        print(f"[!] Aviso FLP: {e}")

    elapsed = time.time() - t0
    print("=" * 70)
    print(f"✨ VERSIÓN CLUB DE CULTO GENERADA CON ÉXITO EN {elapsed:.2f}s")
    print(f"Master: {master_path}")
    print(f"Stems:  {stems_dir}")
    print("=" * 70)
    return master_path, stems_dir, flp_path

if __name__ == "__main__":
    render_dark_cyber_flamenco_club_culto()
