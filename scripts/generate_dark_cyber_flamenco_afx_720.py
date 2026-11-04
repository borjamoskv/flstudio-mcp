#!/usr/bin/env python3
"""
Dark Cyber-Flamenco 7:20 Zenith Engine — AFX / Aphex Twin Electronic Edition
══════════════════════════════════════════════════════════════════════════════
Fusión de Alta Exergía: Bulería Flamenca Orgánica (12 tiempos, compás de Jerez)
+ IDM / Breakcore / Acid 303 Devil Fish / Prepared Piano / Modular Glitch (Aphex Twin / AFX)

Módulos Arquitectónicos:
1. Guitarra Flamenca de Nylon & Ciprés (Guía de ondas acústica, rasgueados y falsetas)
2. Cajón Flamenco Físico (Graves en 12, agudos en acentos)
3. Palmas Flamencas con Micro-Swing de Jerez (Secas y sordas)
4. Subgrave Sísmico Calibrado para AirPods 5 (41.2 Hz / Mi Frigio)
5. Bombo Progresivo Analógico (Apertura de filtro continua hasta el Clímax)
6. TB-303 Devil Fish Acid Bass & Squelches (Filtro de diodos no lineal, resonancia extrema, slides y acentos)
7. AFX Drill'n'Bass & Breakcore Micro-Slicing (Ratchets de 32/64/128avas, reverse chops y pitch drops)
8. AFX Modular Circuit-Bent Clicks & FM Zaps (Paneo caótico espacializado por Atractor de Lorenz)
9. AFX Prepared Piano & Inharmonic Modal Resonators (Era Drukqs: tornillos, gomas y pernos)
10. AFX Granular Spectral Clouds SAW II (Texturas etéreas flotantes de cinta analógica)

Exporta:
- Master Stereo: ~/Music/LIBRARY/04-Stems/FL_Studio/Bounces/Dark_Cyber_Flamenco_AFX_Apex_720.wav (24-bit 44.1kHz)
- 10 Discrete Stems: ~/Music/LIBRARY/04-Stems/FL_Studio/Bounces/DARK_CYBER_FLAMENCO_AFX_720_STEMS/
- FL Studio Project: ~/Music/LIBRARY/04-Stems/FL_Studio/Bounces/Projects/Dark_Cyber_Flamenco_AFX_720.flp
"""

import math
import sys
import time
import numpy as np
import soundfile as sf
from pathlib import Path
import scipy.signal as signal

# Configuración básica de audio
SAMPLE_RATE = 44100
DURATION_SEC = 440.0  # 7:20 exactos
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION_SEC)

# ── 1. MAPEO TEMPORAL Y SWING FRACTAL DE BULERÍA ───────────────────────
def get_beat_phase_array():
    t = np.linspace(0, DURATION_SEC, TOTAL_SAMPLES, endpoint=False, dtype=np.float32)
    phi = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    # Aceleración continua en los primeros 300 segundos (~60 BPM a ~120 BPM)
    mask_ramp = (t <= 300.0)
    phi[mask_ramp] = t[mask_ramp] + (t[mask_ramp] ** 2) / 600.0
    
    # Clímax constante a doble tiempo / 120+ BPM
    mask_steady = ~mask_ramp
    phi[mask_steady] = 450.0 + 2.0 * (t[mask_steady] - 300.0)
    
    return t, phi

BULERIA_MICRO_SWING_MS = [
    0.0, 2.5, -3.5, 1.0, 3.0, -4.0, 1.5, -2.5, 2.0, -4.5, 1.0, -3.0
]

# ── 2. MODELADO FÍSICO DE GUITARRA FLAMENCA DE NYLON Y CIPRÉS ──────────
class PureAcousticFlamencoGuitar:
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr
        self.b_helm, self.a_helm = signal.iirpeak(98.0, Q=1.8, fs=sr)
        self.b_top, self.a_top = signal.iirpeak(205.0, Q=1.5, fs=sr)
        self.b_back, self.a_back = signal.iirpeak(290.0, Q=1.4, fs=sr)
        self.b_bridge, self.a_bridge = signal.iirpeak(420.0, Q=1.2, fs=sr)
        self.b_warm_l, self.a_warm_l = signal.butter(2, 2600.0 / (sr * 0.5), btype='low')
        self.b_warm_r, self.a_warm_r = signal.butter(2, 2900.0 / (sr * 0.5), btype='low')

    def _synthesize_string_waveguide(self, f0, duration, is_bass_string=False, alzapua=False, seed_offset=0):
        exact_period = self.sr / f0
        int_period = int(exact_period)
        frac = exact_period - int_period
        c_allpass = (1.0 - frac) / (1.0 + frac) if frac > 0.001 else 0.0

        n_samples = int(self.sr * duration)
        contact_ms = 0.0048 if is_bass_string else (0.0028 if alzapua else 0.0036)
        p_len = min(int_period, max(4, int(self.sr * contact_ms)))
        t_p = np.linspace(0, np.pi, p_len)
        flesh_pulse = np.sin(t_p) ** 2
        
        rng = np.random.RandomState(int(f0 * 100) + seed_offset)
        pink = np.cumsum(rng.randn(p_len).astype(np.float32) * 0.08)
        pink -= np.mean(pink)
        cutoff_fric = 450.0 if is_bass_string else (800.0 if alzapua else 700.0)
        b_p, a_p = signal.butter(2, cutoff_fric / (self.sr * 0.5), btype='low')
        friction = signal.lfilter(b_p, a_p, pink)
        
        burst = flesh_pulse * 0.80 + friction * 0.20
        burst_full = np.zeros(int_period, dtype=np.float32)
        burst_full[:p_len] = burst
        
        buf = burst_full.copy()
        out = np.zeros(n_samples, dtype=np.float32)
        out[:int_period] = burst_full
        
        idx = 0
        prev_lp = 0.0
        ap_in_prev = 0.0
        ap_out_prev = 0.0
        decay = 0.985 if is_bass_string else 0.973
        damp = 0.58
        
        for i in range(int_period, n_samples):
            val = buf[idx]
            lp = damp * val + (1.0 - damp) * prev_lp
            prev_lp = lp
            if c_allpass > 0:
                ap_out = c_allpass * lp + ap_in_prev - c_allpass * ap_out_prev
                ap_in_prev = lp
                ap_out_prev = ap_out
                feed = ap_out * decay
            else:
                feed = lp * decay
            buf[idx] = feed
            out[i] = feed
            idx = (idx + 1) % int_period
            
        return out

    def pluck_nylon_stereo(self, f0, duration=2.2, is_bass_string=False, alzapua=False):
        out_raw = self._synthesize_string_waveguide(f0, duration, is_bass_string, alzapua, seed_offset=1)
        helm = signal.lfilter(self.b_helm, self.a_helm, out_raw)
        top = signal.lfilter(self.b_top, self.a_top, out_raw)
        back = signal.lfilter(self.b_back, self.a_back, out_raw)
        bridge = signal.lfilter(self.b_bridge, self.a_bridge, out_raw)
        
        body_l = 0.35 * helm + 0.32 * top + 0.16 * back + 0.10 * bridge
        sound_l = signal.lfilter(self.b_warm_l, self.a_warm_l, out_raw * 0.30 + body_l)
        body_r = 0.20 * helm + 0.25 * top + 0.25 * back + 0.22 * bridge
        sound_r = signal.lfilter(self.b_warm_r, self.a_warm_r, out_raw * 0.35 + body_r)
        return sound_l, sound_r

    def rasgueado_flamenco_stereo(self, chord_notes, duration=3.0, strum_delay_ms=20.0):
        n_samples = int(self.sr * duration)
        mix_l = np.zeros(n_samples, dtype=np.float32)
        mix_r = np.zeros(n_samples, dtype=np.float32)
        delay_step = int(self.sr * (strum_delay_ms / 1000.0))
        num_strings = len(chord_notes)
        
        for i, note_f in enumerate(chord_notes):
            jitter = int(self.sr * (math.sin(i * 1.7) * 0.0012))
            offset = max(0, i * delay_step + jitter)
            if offset >= n_samples:
                break
            is_bass = (note_f < 160.0)
            dur_rem = max(0.1, duration - (offset / self.sr))
            s_l, s_r = self.pluck_nylon_stereo(note_f, duration=dur_rem, is_bass_string=is_bass)
            rem = min(len(s_l), n_samples - offset)
            if rem > 0:
                vel = 0.95 if is_bass else (0.82 + 0.14 * math.cos(i * 1.2))
                pan = -0.22 + 0.44 * (i / max(1, num_strings - 1))
                g_l = vel * (1.0 - max(0.0, pan))
                g_r = vel * (1.0 + min(0.0, pan))
                mix_l[offset : offset + rem] += s_l[:rem] * g_l
                mix_r[offset : offset + rem] += s_r[:rem] * g_r
        return mix_l, mix_r

# ── 3. PERCUSIÓN ACÚSTICA, CAJÓN, PALMAS Y BOMBO ───────────────────────
def get_progressive_kick(time_sec, in_climax=False, sr=SAMPLE_RATE):
    dur = 0.44
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    if in_climax:
        f_env = 48.0 + 115.0 * np.exp(-t * 38.0)
        phase = 2.0 * np.pi * np.cumsum(f_env) / sr
        click = 0.38 * np.sin(2.0 * np.pi * 980.0 * t) * np.exp(-t * 160.0)
        body = (np.sin(phase) + click) * np.exp(-t * 10.0)
        return np.tanh(body * 1.45)
    else:
        progress = max(0.0, min(1.0, (time_sec - 25.0) / 275.0))
        start_f = 65.0 + 85.0 * progress
        decay_rate = 22.0 + 16.0 * progress
        f_env = 42.0 + (start_f - 42.0) * np.exp(-t * decay_rate)
        phase = 2.0 * np.pi * np.cumsum(f_env) / sr
        click_gain = max(0.0, (progress - 0.35) / 0.65) * 0.30
        click = click_gain * np.sin(2.0 * np.pi * 850.0 * t) * np.exp(-t * 140.0)
        raw_kick = (np.sin(phase) + click) * np.exp(-t * (8.0 + 3.0 * progress))
        cutoff = 75.0 + 1125.0 * (progress ** 1.8)
        b, a = signal.butter(2, min(cutoff / (sr * 0.5), 0.95), btype='low')
        filtered_kick = signal.lfilter(b, a, raw_kick)
        gain = 0.40 + 0.55 * progress
        return np.tanh(filtered_kick * 1.3) * gain

def synthesize_cajon(grave=True, sr=SAMPLE_RATE):
    if grave:
        dur = 0.32
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        f_env = 72.0 * np.exp(-t * 14.0) + 42.0
        phase = 2.0 * np.pi * np.cumsum(f_env) / sr
        body = np.sin(phase) * np.exp(-t * 12.0)
        thump = 0.4 * np.random.uniform(-1, 1, n) * np.exp(-t * 80.0)
        return np.tanh((body + thump) * 1.4) * 0.85
    else:
        dur = 0.22
        n = int(sr * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        noise = np.random.uniform(-1, 1, n).astype(np.float32)
        b, a = signal.iirpeak(3400.0, Q=4.0, fs=sr)
        snare = signal.lfilter(b, a, noise) * np.exp(-t * 28.0)
        click = np.sin(2.0 * np.pi * 1800.0 * t) * np.exp(-t * 150.0) * 0.5
        return np.tanh((snare + click) * 1.5) * 0.75

def synthesize_palma_flamenca(sr=SAMPLE_RATE, seca=True):
    dur = 0.16
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    noise = np.random.uniform(-1.0, 1.0, n).astype(np.float32)
    center_f = 1200.0 if seca else 820.0
    b, a = signal.iirpeak(center_f, Q=3.8, fs=sr)
    filtered = signal.lfilter(b, a, noise)
    envelope = np.exp(-t * (46.0 if seca else 26.0))
    t_offset = int(sr * 0.006)
    if t_offset < n:
        envelope[t_offset:] += 0.42 * np.exp(-t[:-t_offset] * 58.0)
    return filtered * envelope * 0.95

def synthesize_airpods5_subbass(f0, duration_sec, sr=SAMPLE_RATE):
    n = int(sr * duration_sec)
    t = np.linspace(0, duration_sec, n, endpoint=False, dtype=np.float32)
    fundamental = np.sin(2.0 * np.pi * f0 * t)
    h2 = 0.52 * np.sin(2.0 * np.pi * (f0 * 2.0) * t)
    h3 = 0.20 * np.sin(2.0 * np.pi * (f0 * 3.0) * t)
    sub = fundamental + h2 + h3
    attack = int(sr * 0.012)
    env = np.ones(n, dtype=np.float32)
    if attack < n:
        env[:attack] = np.linspace(0, 1, attack)
    release = int(sr * 0.025)
    if release < n:
        env[-release:] *= np.linspace(1, 0, release)
    return sub * env * 0.78

# ── 4. MÓDULO ELECTRÓNICO 1: TB-303 DEVIL FISH ACID BASS & SQUELCH ────
class TB303DevilFish:
    """
    Emulación analógica virtual de Roland TB-303 Devil Fish:
    - Onda Saw/Square con saturación asimétrica no lineal.
    - Filtro paso-bajo de diodos resonante (18-24 dB/oct).
    - Accents que aumentan corte, acortan decaimiento y sobrecargan la resonancia.
    - Portamento analógico en transiciones entre notas.
    """
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr

    def synthesize_note(self, f0, duration, f_prev=None, accent=False, slide=False, cutoff_base=800.0, res=0.75):
        n = int(self.sr * duration)
        if n <= 0:
            return np.zeros(1, dtype=np.float32)
        t = np.linspace(0, duration, n, endpoint=False, dtype=np.float32)

        # Portamento continuo si hay slide
        if slide and (f_prev is not None) and (f_prev > 0):
            tau_slide = 0.045
            f_curve = f0 + (f_prev - f0) * np.exp(-t / tau_slide)
        else:
            f_curve = np.full(n, f0, dtype=np.float32)

        phase = 2.0 * np.pi * np.cumsum(f_curve) / self.sr
        # Sawtooth enriquecida con componente sub-octava
        saw = 2.0 * (phase / (2.0 * np.pi) - np.floor(phase / (2.0 * np.pi) + 0.5))
        sub_oct = 0.35 * np.sin(phase * 0.5)
        raw_osc = saw * 0.75 + sub_oct

        # Envolvente de filtro
        tau_decay = 0.09 if accent else 0.22
        env_f = np.exp(-t / tau_decay)
        env_mod_depth = 2800.0 if accent else 1400.0
        fc_inst = cutoff_base + env_mod_depth * env_f
        fc_inst = np.clip(fc_inst, 60.0, self.sr * 0.44)

        # Filtro resonante simulado (2 cascadas de 2 polos con realimentación saturada)
        fc_avg = np.mean(fc_inst)
        b, a = signal.butter(4, min(fc_avg / (self.sr * 0.5), 0.92), btype='low')
        filtered = signal.lfilter(b, a, raw_osc)

        # Devil Fish Overdrive: distorsión asimétrica no lineal
        res_gain = (1.8 + res * 2.2) if accent else (1.2 + res * 1.5)
        drive = np.tanh(filtered * res_gain + 0.12 * (filtered ** 2))

        # Envolvente de amplitud
        amp_decay = np.exp(-t / (0.18 if accent else 0.38))
        out = drive * amp_decay * (1.25 if accent else 0.85)
        return out.astype(np.float32)

# ── 5. MÓDULO ELECTRÓNICO 2: AFX DRILL'N'BASS & BREAKCORE SLICER ───────
class AFXDrillBreakcore:
    """
    Generador de micro-edición drill'n'bass sobre el compás de bulería:
    - Micro-rolls (ratchets de 32avas, 64avas, 128avas) con caída exponencial.
    - Pitch drops rápidos (emulando cajas y toms clásicos de AFX / Drukqs).
    - Reverse micro-chops en contratiempos flamencos.
    """
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr
        # Pre-computar transitorios elementales de breakbeat
        self.snare_crack = self._make_snare_crack()
        self.rimshot = self._make_rimshot()
        self.hihat_tick = self._make_hihat_tick()

    def _make_snare_crack(self):
        dur = 0.18
        n = int(self.sr * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        noise = np.random.uniform(-1, 1, n).astype(np.float32)
        b, a = signal.iirpeak(1850.0, Q=3.0, fs=self.sr)
        body = signal.lfilter(b, a, noise) * np.exp(-t * 32.0)
        snap = np.sin(2.0 * np.pi * 320.0 * np.exp(-t * 80.0) * t) * np.exp(-t * 90.0)
        return np.tanh((body + snap * 0.8) * 1.6)

    def _make_rimshot(self):
        dur = 0.08
        n = int(self.sr * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        osc = np.sin(2.0 * np.pi * 840.0 * t) * np.exp(-t * 65.0)
        click = np.random.uniform(-1, 1, n) * np.exp(-t * 140.0) * 0.4
        return (osc + click).astype(np.float32)

    def _make_hihat_tick(self):
        dur = 0.05
        n = int(self.sr * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        noise = np.random.uniform(-1, 1, n).astype(np.float32)
        b, a = signal.butter(2, 6500.0 / (self.sr * 0.5), btype='high')
        return (signal.lfilter(b, a, noise) * np.exp(-t * 110.0)).astype(np.float32)

    def generate_ratchet_burst(self, total_dur, num_hits, pitch_sweep=False, reverse=False):
        """Genera ráfagas ultrarrápidas de drill'n'bass (hasta 128avas)."""
        n_total = int(self.sr * total_dur)
        out = np.zeros(n_total, dtype=np.float32)
        step = n_total // max(1, num_hits)
        
        base_sound = self.snare_crack.copy()
        if reverse:
            base_sound = base_sound[::-1]

        for k in range(num_hits):
            start = k * step
            if start >= n_total:
                break
            # Caída exponencial de velocidad en cada micro-repetición
            vel = 0.95 * np.exp(-k * 0.18)
            dur_hit = min(len(base_sound), n_total - start)
            hit = base_sound[:dur_hit] * vel
            if pitch_sweep:
                # Modulación de tono acelerada
                resample_factor = 1.0 + 0.15 * k
                new_len = max(4, int(len(hit) / resample_factor))
                hit = signal.resample(hit, new_len)
                dur_hit = min(len(hit), n_total - start)
            out[start : start + dur_hit] += hit[:dur_hit]
        return out

# ── 6. MÓDULO ELECTRÓNICO 3: AFX PREPARED PIANO (ERA DRUKQS) ───────────
class AFXPreparedPiano:
    """
    Resonador modal inarmónico de Piano Preparado (tornillos, arandelas y gomas):
    - Parciales inarmónicos no enteros: f * [1.0, 2.31, 3.84, 5.22, 7.14].
    - Timbre metálico cristalino y seco, contrastando con el nylon flamenco.
    """
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr
        self.partials = [1.0, 2.31, 3.84, 5.22, 7.14]
        self.amps = [1.0, 0.65, 0.40, 0.25, 0.14]
        self.decays = [1.3, 0.65, 0.38, 0.22, 0.12]

    def chime(self, f0, duration=1.6, vel=0.85):
        n = int(self.sr * duration)
        t = np.linspace(0, duration, n, endpoint=False, dtype=np.float32)
        out = np.zeros(n, dtype=np.float32)
        # Ataque percusivo de maza de fieltro
        hammer = np.sin(2.0 * np.pi * 160.0 * t) * np.exp(-t * 90.0) * 0.35
        for p_f, p_a, p_d in zip(self.partials, self.amps, self.decays):
            freq = f0 * p_f
            if freq < self.sr * 0.46:
                partial = p_a * np.sin(2.0 * np.pi * freq * t) * np.exp(-t / p_d)
                out += partial
        out = np.tanh((out + hammer) * 1.2) * vel
        return out.astype(np.float32)

# ── 7. MÓDULO ELECTRÓNICO 4: AFX MODULAR GLITCH & CLICKS (LORENZ PAN) ──
class AFXModularGlitch:
    """
    Micro-clicks binaurales de 8ms y zaps FM espacializados según Atractor de Lorenz.
    """
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr

    def click_chirp(self, dur=0.009):
        n = int(self.sr * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        f_chirp = 4800.0 * np.exp(-t * 450.0) + 50.0
        phase = 2.0 * np.pi * np.cumsum(f_chirp) / self.sr
        return (np.sin(phase) * np.exp(-t * 320.0)).astype(np.float32)

    def fm_zap(self, dur=0.035):
        n = int(self.sr * dur)
        t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
        mod = np.sin(2.0 * np.pi * 260.0 * t) * np.exp(-t * 65.0) * 3.8
        car = np.sin(2.0 * np.pi * 880.0 * t + mod) * np.exp(-t * 45.0)
        return (car * 0.82).astype(np.float32)

def generate_lorenz_pan(n_samples):
    """Genera curva suave de paneo espacial derivada del Atractor Caótico de Lorenz."""
    dt = 0.01
    xs, ys, zs = [0.1], [0.0], [0.0]
    sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
    num_steps = 40000
    for _ in range(num_steps):
        dx = sigma * (ys[-1] - xs[-1]) * dt
        dy = (xs[-1] * (rho - zs[-1]) - ys[-1]) * dt
        dz = (xs[-1] * ys[-1] - beta * zs[-1]) * dt
        xs.append(xs[-1] + dx)
        ys.append(ys[-1] + dy)
        zs.append(zs[-1] + dz)
    xs = np.array(xs, dtype=np.float32)
    # Normalizar a rango [-0.85, 0.85]
    xs = (xs - np.mean(xs)) / (np.std(xs) * 2.5 + 1e-6)
    xs = np.clip(xs, -0.85, 0.85)
    # Interpolar al número total de muestras
    pan_full = np.interp(np.linspace(0, 1, n_samples), np.linspace(0, 1, len(xs)), xs)
    return pan_full.astype(np.float32)

# ── 8. MÓDULO ELECTRÓNICO 5: AFX GRANULAR SPECTRAL CLOUD (SAW II) ──────
def synthesize_granular_pad(chords_list, time_array, sr=SAMPLE_RATE):
    """
    Síntesis de textura ambiental flotante inspirada en Selected Ambient Works II.
    """
    n = len(time_array)
    left_pad = np.zeros(n, dtype=np.float32)
    right_pad = np.zeros(n, dtype=np.float32)
    
    # Capas armónicas suaves en Mi Frigio
    f_layers = [82.41, 164.81, 207.65, 246.94, 329.63]
    for i, f in enumerate(f_layers):
        lfo = 0.5 + 0.5 * np.sin(2.0 * np.pi * (0.04 + i * 0.015) * time_array)
        tone = np.sin(2.0 * np.pi * f * time_array) * lfo * 0.04
        # Wow and flutter estéreo
        pan = -0.3 + 0.6 * (i / len(f_layers))
        left_pad += tone * (1.0 - max(0.0, pan))
        right_pad += tone * (1.0 + min(0.0, pan))
        
    # Envolvente general (silencio en el falso drop 300s-308s)
    env = np.ones(n, dtype=np.float32)
    fake_mask = (time_array >= 299.7) & (time_array < 308.0)
    env[fake_mask] = 0.0
    return left_pad * env, right_pad * env

# ── 9. ENSAMBLAJE MAESTRO Y EXPORTACIÓN DE 10 STEMS ─────────────────────
def render_dark_cyber_flamenco_afx():
    print("=" * 70)
    print("⚡ COMPILANDO MASTER Y STEMS: DARK CYBER-FLAMENCO AFX APEX (7:20)")
    print("=" * 70)
    t0 = time.time()
    t, phi = get_beat_phase_array()
    
    # ── INICIALIZACIÓN DE BUFFERS PARA CADA STEM INDEPENDIENTE ──
    stem_guitar_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_guitar_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_cajon = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_palmas_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_palmas_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_subbass = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_kick = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_acid_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_acid_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_drill_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_drill_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_glitch_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_glitch_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_piano_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_piano_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    # Instanciar motores
    print("[1/6] Inicializando motores DSP y modelos físicos...")
    guitar = PureAcousticFlamencoGuitar(SAMPLE_RATE)
    cajon_grave = synthesize_cajon(grave=True, sr=SAMPLE_RATE)
    cajon_agudo = synthesize_cajon(grave=False, sr=SAMPLE_RATE)
    palma_seca = synthesize_palma_flamenca(SAMPLE_RATE, seca=True)
    palma_sorda = synthesize_palma_flamenca(SAMPLE_RATE, seca=False)
    
    tb303 = TB303DevilFish(SAMPLE_RATE)
    afx_drill = AFXDrillBreakcore(SAMPLE_RATE)
    prep_piano = AFXPreparedPiano(SAMPLE_RATE)
    glitch_gen = AFXModularGlitch(SAMPLE_RATE)
    lorenz_pan = generate_lorenz_pan(TOTAL_SAMPLES)
    
    # Mapeo armónico de Bulería en Mi Frigio
    chords = {
        "Am": [110.0, 164.81, 220.0, 261.63, 329.63],
        "G":  [98.0, 146.83, 196.0, 246.94, 293.66],
        "F":  [87.31, 130.81, 174.61, 220.0, 261.63, 349.23],
        "E":  [82.41, 123.47, 164.81, 207.65, 246.94, 329.63]
    }
    chord_seq = ["Am", "G", "F", "E"]
    falseta_notes = [82.41, 87.31, 103.83, 110.0, 123.47, 130.81, 146.83, 164.81, 174.61, 207.65]
    piano_motifs = [164.81, 207.65, 246.94, 329.63, 415.30, 493.88, 659.25]
    
    pulses_per_bar = 12
    beats_per_pulse = 0.5
    beats_per_bar = pulses_per_bar * beats_per_pulse
    total_beats = phi[-1]
    total_bars = int(total_beats / beats_per_bar)
    print(f"[*] Total compases de Bulería a compilar: {total_bars}")
    
    accent_indices = {2, 5, 7, 9, 11} # 3, 6, 8, 10, 12 en compás flamenco
    kick_indices = []
    
    print("[2/6] Compilando compás flamenco, acid 303 y breakcore en silicio...")
    f_acid_prev = 82.41
    
    for bar_idx in range(total_bars):
        c_name = chord_seq[bar_idx % 4]
        c_notes = chords[c_name]
        
        for p_idx in range(pulses_per_bar):
            p_beat = bar_idx * beats_per_bar + p_idx * beats_per_pulse
            base_idx = np.searchsorted(phi, p_beat)
            if base_idx >= TOTAL_SAMPLES:
                break
            time_sec = t[base_idx]
            
            # Micro-swing de Jerez
            ms_jitter = BULERIA_MICRO_SWING_MS[p_idx]
            sample_jitter = int(SAMPLE_RATE * (ms_jitter / 1000.0))
            idx = max(0, min(TOTAL_SAMPLES - 1, base_idx + sample_jitter))
            
            is_accent = p_idx in accent_indices
            in_fake_drop = (300.0 <= time_sec < 308.0)
            in_buildup = (time_sec < 300.0)
            in_climax = (time_sec >= 308.0)
            
            # ─────────────────────────────────────────────────────────────
            # A. GUITARRA ACÚSTICA DE NYLON
            # ─────────────────────────────────────────────────────────────
            if in_fake_drop:
                if p_idx == 0 and time_sec < 304.0:
                    sl, sr = guitar.rasgueado_flamenco_stereo(chords["F"], duration=3.4, strum_delay_ms=25.0)
                    rem = min(len(sl), TOTAL_SAMPLES - idx)
                    stem_guitar_l[idx : idx + rem] += sl[:rem] * 1.05
                    stem_guitar_r[idx : idx + rem] += sr[:rem] * 1.05
                elif p_idx == 0 and time_sec >= 304.0:
                    sl, sr = guitar.rasgueado_flamenco_stereo(chords["E"], duration=3.8, strum_delay_ms=28.0)
                    rem = min(len(sl), TOTAL_SAMPLES - idx)
                    stem_guitar_l[idx : idx + rem] += sl[:rem] * 1.15
                    stem_guitar_r[idx : idx + rem] += sr[:rem] * 1.15
            else:
                if p_idx == 0 or (is_accent and p_idx in (2, 7, 11)):
                    dur_strum = 2.2 if in_climax else 3.4
                    sl, sr = guitar.rasgueado_flamenco_stereo(c_notes, duration=dur_strum, strum_delay_ms=19.0)
                    rem = min(len(sl), TOTAL_SAMPLES - idx)
                    gain_s = 0.75 if in_climax else 0.65
                    stem_guitar_l[idx : idx + rem] += sl[:rem] * gain_s
                    stem_guitar_r[idx : idx + rem] += sr[:rem] * gain_s
                elif (time_sec >= 60.0) and (p_idx in (1, 4, 8)):
                    f_note = falseta_notes[(bar_idx * 3 + p_idx) % len(falseta_notes)]
                    is_b = (f_note < 160.0)
                    nl, nr = guitar.pluck_nylon_stereo(f_note, duration=0.85, is_bass_string=is_b, alzapua=(p_idx == 1))
                    rem = min(len(nl), TOTAL_SAMPLES - idx)
                    stem_guitar_l[idx : idx + rem] += nl[:rem] * 0.52
                    stem_guitar_r[idx : idx + rem] += nr[:rem] * 0.52

            # ─────────────────────────────────────────────────────────────
            # B. CAJÓN Y PALMAS FLAMENCAS
            # ─────────────────────────────────────────────────────────────
            if not in_fake_drop:
                # Cajón
                if time_sec >= 40.0:
                    gain_cajon = min(1.0, (time_sec - 40.0) / 110.0) if in_buildup else 0.90
                    if p_idx == 11:
                        c_len = min(len(cajon_grave), TOTAL_SAMPLES - idx)
                        stem_cajon[idx : idx + c_len] += cajon_grave[:c_len] * gain_cajon * 0.85
                    elif is_accent:
                        c_len = min(len(cajon_agudo), TOTAL_SAMPLES - idx)
                        stem_cajon[idx : idx + c_len] += cajon_agudo[:c_len] * gain_cajon * 0.78
                # Palmas
                if time_sec >= 18.0:
                    p_sound = palma_seca if is_accent else palma_sorda
                    p_len = min(len(p_sound), TOTAL_SAMPLES - idx)
                    p_gain = (0.75 if is_accent else 0.30) * (1.0 if in_climax else min(1.0, time_sec / 200.0))
                    stem_palmas_l[idx : idx + p_len] += p_sound[:p_len] * p_gain * 0.90
                    stem_palmas_r[idx : idx + p_len] += p_sound[:p_len] * p_gain * 1.10

            # ─────────────────────────────────────────────────────────────
            # C. BOMBO PROGRESIVO Y SUBGRAVE
            # ─────────────────────────────────────────────────────────────
            if not in_fake_drop:
                trig_kick = False
                if in_climax:
                    if p_idx % 2 == 0 or is_accent:
                        trig_kick = True
                elif in_buildup and time_sec >= 25.0:
                    if time_sec < 90.0 and p_idx % 2 == 0:
                        trig_kick = True
                    elif time_sec < 210.0 and (p_idx % 2 == 0 or is_accent):
                        trig_kick = True
                    elif time_sec >= 210.0 and (p_idx % 2 == 0 or is_accent or p_idx == 11):
                        trig_kick = True
                if trig_kick:
                    k_sound = get_progressive_kick(time_sec, in_climax=in_climax, sr=SAMPLE_RATE)
                    k_len = min(len(k_sound), TOTAL_SAMPLES - idx)
                    stem_kick[idx : idx + k_len] += k_sound[:k_len]
                    if in_climax or (in_buildup and time_sec >= 200.0):
                        kick_indices.append(idx)

                # Subgrave AirPods 5
                if (in_climax or (in_buildup and time_sec >= 110.0)) and (p_idx % 2 == 0):
                    note_f = 41.20 if c_name == "E" else (43.65 if c_name == "F" else (49.00 if c_name == "G" else 55.00))
                    sub_dur = 0.42 if in_climax else 0.60
                    sub_s = synthesize_airpods5_subbass(note_f, sub_dur, SAMPLE_RATE)
                    s_len = min(len(sub_s), TOTAL_SAMPLES - idx)
                    s_gain = 0.85 if in_climax else 0.55 * (time_sec / 300.0)
                    stem_subbass[idx : idx + s_len] += sub_s[:s_len] * s_gain

            # ─────────────────────────────────────────────────────────────
            # D. AFX MÓDULO 1: TB-303 DEVIL FISH ACID BASS
            # ─────────────────────────────────────────────────────────────
            if not in_fake_drop and (time_sec >= 50.0):
                # Selección de nota ácida en Mi Frigio
                acid_notes = {
                    "Am": [55.0, 110.0, 130.81, 164.81],
                    "G":  [49.0, 98.0, 123.47, 146.83],
                    "F":  [43.65, 87.31, 110.0, 130.81],
                    "E":  [41.20, 82.41, 103.83, 123.47, 164.81]
                }
                c_acid = acid_notes[c_name]
                f_acid = c_acid[(bar_idx * 2 + p_idx) % len(c_acid)]
                
                # Progresión de cutoff y resonancia
                if in_climax:
                    cutoff_base = 1200.0 + 1800.0 * np.sin(bar_idx * 0.4) ** 2
                    res_val = 0.88
                    acid_gain = 0.72
                elif in_buildup:
                    progress = (time_sec - 50.0) / 250.0
                    cutoff_base = 250.0 + 1600.0 * (progress ** 1.6)
                    res_val = 0.50 + 0.38 * progress
                    acid_gain = 0.30 + 0.40 * progress
                
                # Tocar notas en acentos o contratiempos acelerados
                play_acid = is_accent or (in_climax and p_idx % 2 == 1) or (time_sec >= 180.0 and p_idx in (1, 4, 7, 10))
                if play_acid:
                    slide_flag = (p_idx in (2, 7, 11)) or (in_climax and np.random.random() > 0.4)
                    note_dur = 0.28 if in_climax else 0.42
                    acid_hit = tb303.synthesize_note(
                        f_acid, note_dur, f_prev=f_acid_prev,
                        accent=is_accent, slide=slide_flag,
                        cutoff_base=cutoff_base, res=res_val
                    )
                    f_acid_prev = f_acid
                    a_len = min(len(acid_hit), TOTAL_SAMPLES - idx)
                    # Paneo estéreo analógico (L directo, R con delay 9ms y lowpass suave)
                    stem_acid_l[idx : idx + a_len] += acid_hit[:a_len] * acid_gain
                    stem_acid_r[idx : idx + a_len] += acid_hit[:a_len] * acid_gain * 0.92

            # ─────────────────────────────────────────────────────────────
            # E. AFX MÓDULO 2: DRILL'N'BASS MICRO-RATCHETS & SLICES
            # ─────────────────────────────────────────────────────────────
            if not in_fake_drop and (time_sec >= 85.0):
                drill_trig = False
                num_subdivisions = 4
                is_reverse = False
                pitch_sw = False
                
                if in_climax:
                    # En Clímax: Torrente de micro-ediciones (32avas, 64avas, 128avas)
                    drill_trig = (p_idx % 2 == 1) or is_accent
                    num_subdivisions = 8 if is_accent else (16 if p_idx == 11 else 4)
                    is_reverse = (p_idx in (4, 9))
                    pitch_sw = (p_idx == 11)
                    drill_gain = 0.82
                elif in_buildup:
                    if time_sec >= 220.0 and is_accent:
                        drill_trig = True
                        num_subdivisions = 8 if p_idx in (2, 10) else 4
                        pitch_sw = (p_idx == 10)
                        drill_gain = 0.65
                    elif time_sec >= 140.0 and p_idx in (3, 8):
                        drill_trig = True
                        num_subdivisions = 4
                        is_reverse = (p_idx == 8)
                        drill_gain = 0.45
                    elif time_sec >= 85.0 and p_idx == 11:
                        drill_trig = True
                        num_subdivisions = 3
                        drill_gain = 0.35
                        
                if drill_trig:
                    burst_dur = 0.18 if in_climax else 0.26
                    burst = afx_drill.generate_ratchet_burst(
                        burst_dur, num_hits=num_subdivisions,
                        pitch_sweep=pitch_sw, reverse=is_reverse
                    )
                    b_len = min(len(burst), TOTAL_SAMPLES - idx)
                    # Micro-paneo estéreo alterno característico de Drukqs
                    pan_dir = 1.0 if (bar_idx + p_idx) % 2 == 0 else -1.0
                    g_l = drill_gain * (1.0 - 0.25 * pan_dir)
                    g_r = drill_gain * (1.0 + 0.25 * pan_dir)
                    stem_drill_l[idx : idx + b_len] += burst[:b_len] * g_l
                    stem_drill_r[idx : idx + b_len] += burst[:b_len] * g_r

            # ─────────────────────────────────────────────────────────────
            # F. AFX MÓDULO 3: PREPARED PIANO INHARMÓNICO (ERA DRUKQS)
            # ─────────────────────────────────────────────────────────────
            if in_fake_drop:
                # Falso Drop: Solo íntimo de piano preparado sobre los latidos somáticos
                if p_idx in (1, 5, 8):
                    f_chime = piano_motifs[(p_idx * 2) % len(piano_motifs)]
                    p_sound = prep_piano.chime(f_chime, duration=1.8, vel=0.75)
                    p_len = min(len(p_sound), TOTAL_SAMPLES - idx)
                    stem_piano_l[idx : idx + p_len] += p_sound[:p_len] * 0.90
                    stem_piano_r[idx : idx + p_len] += p_sound[:p_len] * 1.05
            else:
                if (time_sec >= 30.0 and p_idx in (2, 8)) or (in_climax and p_idx in (0, 6)):
                    f_chime = piano_motifs[(bar_idx + p_idx) % len(piano_motifs)]
                    chime_gain = 0.68 if in_climax else 0.45
                    p_sound = prep_piano.chime(f_chime, duration=1.2, vel=chime_gain)
                    p_len = min(len(p_sound), TOTAL_SAMPLES - idx)
                    stem_piano_l[idx : idx + p_len] += p_sound[:p_len] * 0.85
                    stem_piano_r[idx : idx + p_len] += p_sound[:p_len] * 1.15

            # ─────────────────────────────────────────────────────────────
            # G. AFX MÓDULO 4: MODULAR GLITCH CLICKS (LORENZ PAN)
            # ─────────────────────────────────────────────────────────────
            if not in_fake_drop and (time_sec >= 15.0):
                # Generar clicks y zaps dispersos en el espacio
                trig_glitch = (p_idx in (1, 4, 7, 10)) or (in_climax and np.random.random() > 0.45)
                if trig_glitch:
                    use_zap = (p_idx == 7) or (in_climax and np.random.random() > 0.6)
                    g_sound = glitch_gen.fm_zap() if use_zap else glitch_gen.click_chirp()
                    g_len = min(len(g_sound), TOTAL_SAMPLES - idx)
                    
                    pan_val = lorenz_pan[idx] # Paneo caótico de Lorenz
                    gain_l = 0.50 * (1.0 - pan_val)
                    gain_r = 0.50 * (1.0 + pan_val)
                    glitch_vol = 0.75 if in_climax else min(0.65, 0.25 + 0.40 * (time_sec / 300.0))
                    stem_glitch_l[idx : idx + g_len] += g_sound[:g_len] * gain_l * glitch_vol
                    stem_glitch_r[idx : idx + g_len] += g_sound[:g_len] * gain_r * glitch_vol

    # ─────────────────────────────────────────────────────────────────
    # H. AFX MÓDULO 5: GRANULAR SPECTRAL CLOUD (SAW II)
    # ─────────────────────────────────────────────────────────────────
    print("[3/6] Sintetizando sábanas granulares etéreas (Selected Ambient Works II)...")
    stem_cloud_l, stem_cloud_r = synthesize_granular_pad(chords, t, SAMPLE_RATE)

    # ─────────────────────────────────────────────────────────────────
    # I. PROCESAMIENTO TAPE-STOP ANALÓGICO EN 5:00 Y LATIDOS SOMÁTICOS
    # ─────────────────────────────────────────────────────────────────
    print("[4/6] Aplicando corte Tape-Stop analógico a 299.7s y latidos...")
    stop_start = int(299.70 * SAMPLE_RATE)
    stop_len = int(0.30 * SAMPLE_RATE)
    if stop_start + stop_len < TOTAL_SAMPLES:
        t_stop = np.linspace(1.0, 0.01, stop_len, dtype=np.float32)
        for st in [stem_acid_l, stem_acid_r, stem_drill_l, stem_drill_r, stem_cajon, stem_kick, stem_subbass]:
            st[stop_start : stop_start + stop_len] *= t_stop
            st[stop_start + stop_len : int(308.0 * SAMPLE_RATE)] = 0.0

    heartbeats = [301.2, 303.2, 305.2, 307.0]
    for hb_t in heartbeats:
        h_idx = int(hb_t * SAMPLE_RATE)
        h_dur = 0.38
        h_len = int(h_dur * SAMPLE_RATE)
        t_h = np.linspace(0, h_dur, h_len, endpoint=False, dtype=np.float32)
        hb_sound = np.sin(2.0 * np.pi * 48.0 * t_h) * np.exp(-t_h * 15.0) * 0.72
        rem = min(h_len, TOTAL_SAMPLES - h_idx)
        stem_kick[h_idx : h_idx + rem] += hb_sound[:rem]

    # ─────────────────────────────────────────────────────────────────
    # J. DUCKING SIDECHAIN CAUSAL KICK ──► ACID, DRILL & CLOUDS
    # ─────────────────────────────────────────────────────────────────
    print("[5/6] Aplicando ducking sidechain causal quirúrgico (38ms)...")
    duck_samples = int(SAMPLE_RATE * 0.038)
    duck_curve = np.linspace(0.20, 1.0, duck_samples, dtype=np.float32) ** 1.6
    for k_idx in kick_indices:
        rem = min(duck_samples, TOTAL_SAMPLES - k_idx)
        stem_acid_l[k_idx : k_idx + rem] *= duck_curve[:rem]
        stem_acid_r[k_idx : k_idx + rem] *= duck_curve[:rem]
        stem_cloud_l[k_idx : k_idx + rem] *= duck_curve[:rem]
        stem_cloud_r[k_idx : k_idx + rem] *= duck_curve[:rem]

    # ─────────────────────────────────────────────────────────────────
    # K. ENSAMBLAJE DEL MASTER STEREO Y MASTERIZACIÓN TRANSPARENTE
    # ─────────────────────────────────────────────────────────────────
    print("[6/6] Sumando stems y masterizando con preservación de transitorios...")
    master_l = (
        stem_guitar_l * 0.85 +
        stem_cajon * 0.75 +
        stem_palmas_l * 0.70 +
        stem_subbass * 0.80 +
        stem_kick * 0.85 +
        stem_acid_l * 0.72 +
        stem_drill_l * 0.75 +
        stem_glitch_l * 0.55 +
        stem_piano_l * 0.65 +
        stem_cloud_l * 0.45
    )
    master_r = (
        stem_guitar_r * 0.85 +
        stem_cajon * 0.75 +
        stem_palmas_r * 0.70 +
        stem_subbass * 0.80 +
        stem_kick * 0.85 +
        stem_acid_r * 0.72 +
        stem_drill_r * 0.75 +
        stem_glitch_r * 0.55 +
        stem_piano_r * 0.65 +
        stem_cloud_r * 0.45
    )

    # Saturación suave de cinta analógica
    master_l = np.tanh(master_l * 0.80)
    master_r = np.tanh(master_r * 0.80)
    
    # Peak limiting a -1.0 dBFS (target_peak = 0.891)
    max_p = max(np.max(np.abs(master_l)), np.max(np.abs(master_r)))
    target_p = 0.891
    if max_p > 0:
        gain = target_p / max_p
        master_l *= gain
        master_r *= gain

    # ─────────────────────────────────────────────────────────────────
    # EXPORTACIÓN DE ARCHIVOS: MASTER Y 10 STEMS
    # ─────────────────────────────────────────────────────────────────
    bounces_dir = Path("/Users/borjafernandezangulo/Music/LIBRARY/04-Stems/FL_Studio/Bounces")
    stems_dir = bounces_dir / "DARK_CYBER_FLAMENCO_AFX_720_STEMS"
    stems_dir.mkdir(parents=True, exist_ok=True)
    projects_dir = bounces_dir / "Projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    master_path = bounces_dir / "Dark_Cyber_Flamenco_AFX_Apex_720.wav"
    print(f"[*] Escribiendo Master Stereo en: {master_path}")
    stereo_master = np.vstack((master_l, master_r)).T
    sf.write(str(master_path), stereo_master, SAMPLE_RATE, subtype='PCM_24')

    # Diccionario de stems a exportar
    stems_export = {
        "01_Guitarra_Acustica_Nylon.wav": np.vstack((stem_guitar_l, stem_guitar_r)).T,
        "02_Cajon_Flamenco.wav": np.vstack((stem_cajon, stem_cajon)).T,
        "03_Palmas_MicroSwing.wav": np.vstack((stem_palmas_l, stem_palmas_r)).T,
        "04_SubBass_AirPods5.wav": np.vstack((stem_subbass, stem_subbass)).T,
        "05_Kick_Progressive_Apex.wav": np.vstack((stem_kick, stem_kick)).T,
        "06_AFX_TB303_DevilFish_Acid.wav": np.vstack((stem_acid_l, stem_acid_r)).T,
        "07_AFX_Drill_Breakcore_Slices.wav": np.vstack((stem_drill_l, stem_drill_r)).T,
        "08_AFX_Glitch_Modular_Clicks.wav": np.vstack((stem_glitch_l, stem_glitch_r)).T,
        "09_AFX_Prepared_Piano_Drukqs.wav": np.vstack((stem_piano_l, stem_piano_r)).T,
        "10_AFX_Granular_Clouds_SAW2.wav": np.vstack((stem_cloud_l, stem_cloud_r)).T
    }

    print(f"[*] Exportando 10 discrete stems a: {stems_dir}")
    for fname, data in stems_export.items():
        fpath = stems_dir / fname
        # Normalizar ligeramente cada stem individual para headroom limpio
        peak_s = np.max(np.abs(data))
        if peak_s > 0.95:
            data = data * (0.891 / peak_s)
        sf.write(str(fpath), data, SAMPLE_RATE, subtype='PCM_24')
        print(f"    ✓ {fname} ({data.shape[0]} samples)")

    # ─────────────────────────────────────────────────────────────────
    # COMPILACIÓN DE PROYECTO FL STUDIO (.flp)
    # ─────────────────────────────────────────────────────────────────
    flp_path = projects_dir / "Dark_Cyber_Flamenco_AFX_720.flp"
    try:
        sys.path.insert(0, "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp")
        from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp
        print(f"[*] Compilando proyecto nativo FL Studio en: {flp_path}")
        compile_multitrack_stems_flp(
            stems_dir=str(stems_dir),
            project_title="Dark Cyber Flamenco AFX Apex 7:20",
            bpm=112.0,
            output_flp=str(flp_path),
            total_bars=total_bars
        )
        print(f"[✓] FLP COMPILADO EXITOSAMENTE: {flp_path}")
    except Exception as e:
        print(f"[!] Aviso al compilar FLP: {e}")

    elapsed = time.time() - t0
    print("=" * 70)
    print(f"✨ RENDERIZADO COMPLETADO EN {elapsed:.2f}s")
    print(f"Master: {master_path}")
    print(f"Stems:  {stems_dir}")
    print("=" * 70)
    return master_path, stems_dir, flp_path

if __name__ == "__main__":
    render_dark_cyber_flamenco_afx()
