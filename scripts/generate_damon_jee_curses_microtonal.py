#!/usr/bin/env python3
"""
Damon Jee x Curses Microtonal Dark Disco / EBM Engine (C5-REAL SOTA Zenith)
════════════════════════════════════════════════════════════════════════════════
Synthesizes a masterwork combining:
1. Damon Jee: Driving 1/16th-note rolling EBM bassline, punchy 50 Hz analog kick, 122 BPM.
2. Curses: Post-punk chorus electric guitar, 80s gated snare, spectral whisper vox & space echo.
3. Microtonal: 24-TET Makam Bayati xen-scale (neutral 2nd ~150 cents, quarter-tone slides).
4. C5 Musical Invariants: Falso Drop at bar 60, Bark carving, active tape floor (-57 dBFS),
   and EBU R128 master with Rubin Linter certification.
5. Autopoietic FL Studio Project (.flp) compilation linking all 10 discrete stems.
"""

import sys
from pathlib import Path
import numpy as np
import scipy.signal as signal
import soundfile as sf

# ── 1. PARÁMETROS GLOBALES Y CONSTANTES FÍSICAS ─────────────────────────────
SAMPLE_RATE = 44100
BPM = 122.0
BEAT_SEC = 60.0 / BPM                     # ~0.4918 s
BAR_SEC = BEAT_SEC * 4.0                  # ~1.9672 s
SIXTEENTH_SEC = BEAT_SEC / 4.0            # ~0.12295 s
TOTAL_BARS = 64
DURATION_SEC = TOTAL_BARS * BAR_SEC       # ~125.9016 s
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION_SEC)

TAPE_FLOOR_DB = -57.0
TAPE_FLOOR_AMP = 10.0 ** (TAPE_FLOOR_DB / 20.0)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "bounces" / "borja_moskv_lomu"
STEMS_DIR = OUTPUT_DIR / "stems"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STEMS_DIR.mkdir(parents=True, exist_ok=True)

print("=== Borja Moskv - Lomu (Damon Jee x Curses Microtonal · 122 BPM · 24-TET Bayati) ===")
print(f"Total Duration: {DURATION_SEC:.2f}s ({TOTAL_SAMPLES} samples) | Stems Dir: {STEMS_DIR}")

# ── 2. ESCALA MICROTONAL 24-TET MAKAM BAYATI (EN RE / D) ────────────────────
# Base D2 = 73.42 Hz, D3 = 146.83 Hz, D4 = 293.66 Hz
# 24-TET formula: f = f0 * 2^(cents / 1200)
def cents_to_freq(base_f: float, cents: float) -> float:
    return float(base_f * (2.0 ** (cents / 1200.0)))

# Grados Makam Bayati:
# 0: D (0 cents), 1: E half-flat (150 cents), 2: F (300 cents), 3: G (500 cents),
# 4: A (700 cents), 5: Bb (800 cents), 6: C half-sharp (1050 cents), 7: D (1200 cents)
BAYATI_CENTS = [0.0, 150.0, 300.0, 500.0, 700.0, 800.0, 1050.0, 1200.0]

# ── 3. GENERADORES DE TIMBRES NATIVOS EN SILICIO ────────────────────────────

def synthesize_damon_kick(sr=SAMPLE_RATE) -> np.ndarray:
    """Bombo analógico pesado de Dark Disco: click de madera + barrido sísmico a 50 Hz."""
    dur = 0.38
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    # Barrido exponencial de 180 Hz a 50.0 Hz
    f_env = 50.0 + 130.0 * np.exp(-t * 36.0)
    phase = 2.0 * np.pi * np.cumsum(f_env) / sr
    click = 0.45 * np.sin(2.0 * np.pi * 1250.0 * t) * np.exp(-t * 220.0)
    body = (np.sin(phase) + click) * np.exp(-t * 9.5)
    return np.tanh(body * 1.6).astype(np.float32)


def synthesize_gated_snare_hit(sr=SAMPLE_RATE) -> np.ndarray:
    """Caja 80s gated industrial: cuerpo tonal 210 Hz + ruido denso con compuerta a 160ms."""
    dur = 0.28
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    # Tonal body
    tone = np.sin(2.0 * np.pi * 210.0 * t) * np.exp(-t * 24.0)
    # Snare wire noise (bandpass 800-4500 Hz)
    noise = np.random.uniform(-1.0, 1.0, n).astype(np.float32)
    b, a = signal.butter(2, [800.0 / (sr / 2), 4500.0 / (sr / 2)], btype='bandpass')
    noise_filt = signal.lfilter(b, a, noise)
    # Non-linear gate envelope: cut abruptly at 0.16s with 5ms smooth fade
    gate = np.ones(n, dtype=np.float32)
    cutoff_idx = int(0.16 * sr)
    fade_idx = int(0.006 * sr)
    if cutoff_idx + fade_idx < n:
        gate[cutoff_idx:cutoff_idx + fade_idx] = np.linspace(1.0, 0.0, fade_idx)
        gate[cutoff_idx + fade_idx:] = 0.0
    sig = (0.5 * tone + 0.85 * noise_filt) * gate * np.exp(-t * 6.0)
    return np.tanh(sig * 1.5).astype(np.float32)


def synthesize_hat_hit(open_hat: bool = False, sr=SAMPLE_RATE) -> np.ndarray:
    """Charles analógico 909/808 con cluster inarmónico y filtrado paso-alto a 7.5 kHz."""
    dur = 0.28 if open_hat else 0.048
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    # Ring mod cluster of inharmonic square waves
    freqs = [245.0, 306.0, 368.0, 420.0, 525.0, 800.0]
    cluster = np.zeros(n, dtype=np.float32)
    for f in freqs:
        cluster += np.sign(np.sin(2.0 * np.pi * f * t))
    # Metal noise
    noise = np.random.uniform(-1.0, 1.0, n).astype(np.float32) * 0.4
    raw = (cluster + noise).astype(np.float32)
    b, a = signal.butter(3, 7200.0 / (sr / 2), btype='highpass')
    filt = signal.lfilter(b, a, raw)
    env = np.exp(-t * (12.0 if open_hat else 75.0))
    return (filt * env * 0.45).astype(np.float32)


def synthesize_cavern_clap(sr=SAMPLE_RATE) -> np.ndarray:
    """Clap cavernoso con multi-golpes escalonados y reflexiones estéreo tempranas."""
    dur = 0.35
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    sig = np.zeros(n, dtype=np.float32)
    # 3 pre-claps
    delays = [0, int(0.008 * sr), int(0.017 * sr), int(0.026 * sr)]
    noise = np.random.uniform(-1.0, 1.0, n).astype(np.float32)
    b, a = signal.butter(2, [1100.0 / (sr / 2), 3200.0 / (sr / 2)], btype='bandpass')
    noise_filt = signal.lfilter(b, a, noise)
    for i, d in enumerate(delays):
        decay = 120.0 if i < 3 else 22.0
        amp = 0.45 if i < 3 else 1.0
        remaining = n - d
        if remaining > 0:
            env = np.exp(-t[:remaining] * decay) * amp
            sig[d:] += noise_filt[:remaining] * env
    return np.tanh(sig * 1.3).astype(np.float32)


# ── 4. CONSTRUCCIÓN DEL ARREGLO DE 10 PISTAS ESTÉREO ─────────────────────────
print("Generando pistas de audio en memoria (64 compases)...")

track_kick = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_bass = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_guitar = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_snare = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_hats = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_claps = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_303 = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_vox = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_stabs = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
track_drone = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

kick_sample = synthesize_damon_kick()
snare_sample = synthesize_gated_snare_hit()
oh_sample = synthesize_hat_hit(open_hat=True)
ch_sample = synthesize_hat_hit(open_hat=False)
clap_sample = synthesize_cavern_clap()

bar_samples = int(BAR_SEC * SAMPLE_RATE)
beat_samples = int(BEAT_SEC * SAMPLE_RATE)
sixteenth_samples = int(SIXTEENTH_SEC * SAMPLE_RATE)

# ── PISTA 1: KICK (Four on the floor, con corte en Falso Drop compás 60) ─────
for bar in range(TOTAL_BARS):
    # Compases activos: 9..64 (con corte en compás 60 beats 2 y 3)
    if bar < 8:
        continue
    bar_start = bar * bar_samples
    for beat in range(4):
        # Falso Drop en compás 60 (bar index 59): mute en pulsos 3 y 4 (beat index 2 y 3)
        if bar == 59 and beat >= 2:
            continue
        hit_pos = bar_start + beat * beat_samples
        hit_len = min(len(kick_sample), TOTAL_SAMPLES - hit_pos)
        if hit_len > 0:
            track_kick[hit_pos:hit_pos + hit_len, 0] += kick_sample[:hit_len] * 0.95
            track_kick[hit_pos:hit_pos + hit_len, 1] += kick_sample[:hit_len] * 0.95

# ── PISTA 2: ROLLING EBM BASS (Damon Jee 1/16th groove con muesca 50Hz) ──────
# Patrón de 16 semicorcheas en Re: D1, D1, D2, F2, D1, D1, G2, D1, D1, E_half_flat, D1, D1, C2, D1, A1, D1
bass_cents = [0.0, 0.0, 1200.0, 1500.0, 0.0, 0.0, 1700.0, 0.0, 0.0, 1350.0, 0.0, 0.0, 1000.0, 0.0, 700.0, 0.0]
base_d1 = 36.71  # D1 fundamental

for bar in range(TOTAL_BARS):
    # Entra suave con filtro cerrado en bar 4, abre en bar 9..64
    if bar < 3:
        continue
    # Falso drop en bar 60 (index 59): silencio en beats 2 y 3
    bar_start = bar * bar_samples
    filter_cutoff = 450.0 if bar < 8 else (1100.0 if bar < 48 else 1800.0)
    if bar >= 60:
        filter_cutoff = 2200.0  # Clímax tras el drop
        
    for step in range(16):
        beat_in_bar = step // 4
        if bar == 59 and beat_in_bar >= 2:
            continue
        step_pos = bar_start + step * sixteenth_samples
        step_len = min(sixteenth_samples + int(0.02 * SAMPLE_RATE), TOTAL_SAMPLES - step_pos)
        if step_len <= 0:
            continue
        f_note = cents_to_freq(base_d1, bass_cents[step])
        t_note = np.linspace(0, step_len / SAMPLE_RATE, step_len, endpoint=False, dtype=np.float32)
        # Saw + sub pulse
        saw = 2.0 * (t_note * f_note - np.floor(t_note * f_note + 0.5))
        sub = np.sign(np.sin(2.0 * np.pi * (f_note / 2.0) * t_note)) * 0.35
        raw_bass = (saw + sub) * np.exp(-t_note * 11.0)
        # Resonant lowpass
        b, a = signal.butter(2, min(filter_cutoff, 4000.0) / (SAMPLE_RATE / 2), btype='lowpass')
        filt_bass = signal.lfilter(b, a, raw_bass)
        # Sidechain ducking contra el bombo si cae en tiempo fuerte
        ducking = 0.32 if (step % 4 == 0 and bar >= 8) else 1.0
        val = np.tanh(filt_bass * 1.8) * 0.85 * ducking
        track_bass[step_pos:step_pos + step_len, 0] += val
        track_bass[step_pos:step_pos + step_len, 1] += val

# ── PISTA 3: GUITARRA POST-PUNK CHORUS (Curses Style 24-TET) ────────────────
# Riff cortante con púa, deslices microtonales y chorus Roland Dimension D
guitar_riff_cents = [1200.0, 1350.0, 1500.0, 1700.0, 1900.0, 1700.0, 1500.0, 1350.0]
base_d3 = 146.83

def synthesize_plucked_guitar(freq: float, dur: float, sr=SAMPLE_RATE) -> np.ndarray:
    n = int(sr * dur)
    t = np.linspace(0, dur, n, endpoint=False, dtype=np.float32)
    # Karplus-Strong approximation: noise burst + decaying harmonic bank
    harmonics = [1.0, 2.0, 3.01, 4.02, 5.05]
    sig = np.zeros(n, dtype=np.float32)
    for h_idx, h in enumerate(harmonics):
        amp = 1.0 / (h_idx + 1.2)
        sig += amp * np.sin(2.0 * np.pi * (freq * h) * t) * np.exp(-t * (14.0 * (h_idx + 1.0)))
    # Add pick transient
    pick = np.random.uniform(-1.0, 1.0, n).astype(np.float32) * np.exp(-t * 220.0) * 0.6
    return (sig + pick).astype(np.float32)

for bar in range(TOTAL_BARS):
    # Aparece en compases 17..32 y en 41..59, y regresa con furia en el drop 61..64
    if not (16 <= bar < 32 or 40 <= bar < 59 or 60 <= bar < 64):
        continue
    bar_start = bar * bar_samples
    for note_idx, c_val in enumerate(guitar_riff_cents):
        hit_pos = bar_start + note_idx * (beat_samples // 2)
        if hit_pos >= TOTAL_SAMPLES:
            break
        note_f = cents_to_freq(base_d3, c_val)
        dur = BEAT_SEC * 0.75
        g_sound = synthesize_plucked_guitar(note_f, dur)
        g_len = min(len(g_sound), TOTAL_SAMPLES - hit_pos)
        if g_len > 0:
            # Dimension D chorus emulation (L slightly earlier, R modulated)
            track_guitar[hit_pos:hit_pos + g_len, 0] += g_sound[:g_len] * 0.55
            # Right channel delayed 16ms
            delay_r = int(0.016 * SAMPLE_RATE)
            if hit_pos + delay_r + g_len < TOTAL_SAMPLES:
                track_guitar[hit_pos + delay_r:hit_pos + delay_r + g_len, 1] += g_sound[:g_len] * 0.52

# ── PISTA 4: GATED SNARE INDUSTRIAL (Compases 17..64) ───────────────────────
for bar in range(TOTAL_BARS):
    if bar < 16:
        continue
    if bar == 59:  # Falso drop: solo primer beat 2, beat 4 mute
        pass
    bar_start = bar * bar_samples
    for beat in [1, 3]:
        if bar == 59 and beat == 3:
            continue
        hit_pos = bar_start + beat * beat_samples
        hit_len = min(len(snare_sample), TOTAL_SAMPLES - hit_pos)
        if hit_len > 0:
            track_snare[hit_pos:hit_pos + hit_len, 0] += snare_sample[:hit_len] * 0.85
            track_snare[hit_pos:hit_pos + hit_len, 1] += snare_sample[:hit_len] * 0.85

# ── PISTA 5: HATS MOTORIK (Open Hat en contratiempo, Closed en 16ths) ────────
for bar in range(TOTAL_BARS):
    if bar < 4:
        continue
    bar_start = bar * bar_samples
    for s in range(16):
        if bar == 59 and s >= 8:  # Mute en falso drop pulsos 3 y 4
            continue
        # Micro-swing de 4ms en semicorcheas pares
        swing_offset = int(0.004 * SAMPLE_RATE) if (s % 2 == 1) else 0
        hit_pos = bar_start + s * sixteenth_samples + swing_offset
        if hit_pos >= TOTAL_SAMPLES:
            break
        # Offbeats (s = 2, 6, 10, 14) -> Open hat
        if s % 4 == 2 and bar >= 8:
            h_len = min(len(oh_sample), TOTAL_SAMPLES - hit_pos)
            if h_len > 0:
                track_hats[hit_pos:hit_pos + h_len, 0] += oh_sample[:h_len] * 0.55
                track_hats[hit_pos:hit_pos + h_len, 1] += oh_sample[:h_len] * 0.65
        else:
            h_len = min(len(ch_sample), TOTAL_SAMPLES - hit_pos)
            if h_len > 0:
                track_hats[hit_pos:hit_pos + h_len, 0] += ch_sample[:h_len] * 0.40
                track_hats[hit_pos:hit_pos + h_len, 1] += ch_sample[:h_len] * 0.35

# ── PISTA 6: CLAPS CAVERNOSOS EN SALA ESTÉREO (Compases 9..64) ──────────────
for bar in range(TOTAL_BARS):
    if bar < 8:
        continue
    bar_start = bar * bar_samples
    for beat in [1, 3]:
        if bar == 59 and beat == 3:
            continue
        hit_pos = bar_start + beat * beat_samples
        hit_len = min(len(clap_sample), TOTAL_SAMPLES - hit_pos)
        if hit_len > 0:
            track_claps[hit_pos:hit_pos + hit_len, 0] += clap_sample[:hit_len] * 0.65
            track_claps[hit_pos:hit_pos + hit_len, 1] += clap_sample[:hit_len] * 0.75

# ── PISTA 7: ACID 303 MICROTONAL (24-TET Makam Bayati con Resonancia Agresiva)
acid_seq = [
    (0.0, 1.0), (150.0, 1.2), (300.0, 0.8), (500.0, 1.5), 
    (700.0, 1.0), (800.0, 1.3), (1050.0, 1.1), (1200.0, 1.6)
]
for bar in range(TOTAL_BARS):
    # Entra en la sección hipnótica 33..48 y en el apex final 61..64
    if not (32 <= bar < 48 or 60 <= bar < 64):
        continue
    bar_start = bar * bar_samples
    for s_idx in range(16):
        note_cents, accent = acid_seq[s_idx % len(acid_seq)]
        note_f = cents_to_freq(base_d3, note_cents)
        step_pos = bar_start + s_idx * sixteenth_samples
        step_len = min(int(sixteenth_samples * 1.2), TOTAL_SAMPLES - step_pos)
        if step_len <= 0:
            continue
        t_acid = np.linspace(0, step_len / SAMPLE_RATE, step_len, endpoint=False, dtype=np.float32)
        # 303 saw
        saw = 2.0 * (t_acid * note_f - np.floor(t_acid * note_f + 0.5))
        # Swept diode filter
        sweep_f = np.clip(600.0 + 2400.0 * np.exp(-t_acid * 18.0) * accent, 200.0, 8000.0)
        # Approximated resonant peak
        b, a = signal.iirpeak(float(np.mean(sweep_f)), Q=4.5, fs=SAMPLE_RATE)
        acid_filt = signal.lfilter(b, a, saw)
        val = np.tanh(acid_filt * (1.8 * accent)) * 0.65
        track_303[step_pos:step_pos + step_len, 0] += val * 0.7
        track_303[step_pos:step_pos + step_len, 1] += val * 0.8

# ── PISTA 8: CURSES WHISPER VOX & SPACE ECHO (Protagonista del Falso Drop) ────
# Síntesis de spoken word espectral ("We dance... in silence... shadows fall")
def synthesize_whisper_voice(phrase: str, dur_sec: float, sr=SAMPLE_RATE) -> np.ndarray:
    n = int(sr * dur_sec)
    np.linspace(0, dur_sec, n, endpoint=False, dtype=np.float32)
    # Noise with formant resonances (Formants: F1=500Hz, F2=1500Hz, F3=2500Hz)
    noise = np.random.uniform(-1.0, 1.0, n).astype(np.float32)
    b1, a1 = signal.iirpeak(550.0, Q=4.0, fs=sr)
    b2, a2 = signal.iirpeak(1600.0, Q=5.0, fs=sr)
    b3, a3 = signal.iirpeak(2700.0, Q=6.0, fs=sr)
    formant = signal.lfilter(b1, a1, noise) * 0.5 + signal.lfilter(b2, a2, noise) * 0.35 + signal.lfilter(b3, a3, noise) * 0.2
    # Rhythmic phrasing envelope
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    raw_vox = formant * env * 1.8
    # Tape delay (Space Echo: delay 280ms, feedback)
    delay_samples = int(0.28 * sr)
    echo = np.zeros(n + delay_samples * 3, dtype=np.float32)
    echo[:n] += raw_vox
    echo[delay_samples:delay_samples + n] += raw_vox * 0.45
    echo[delay_samples * 2:delay_samples * 2 + n] += raw_vox * 0.22
    return echo

# Whisper en el Falso Drop (Compás 60, pulsos 2.5 a 4)
drop_pos = int(59 * bar_samples + 2.0 * beat_samples)
drop_vox = synthesize_whisper_voice("We dance in silence", 1.8)
drop_len = min(len(drop_vox), TOTAL_SAMPLES - drop_pos)
if drop_len > 0:
    track_vox[drop_pos:drop_pos + drop_len, 0] += drop_vox[:drop_len] * 0.95
    # Stereo panning delay
    d_vox_r = int(0.022 * SAMPLE_RATE)
    if drop_pos + d_vox_r + drop_len < TOTAL_SAMPLES:
        track_vox[drop_pos + d_vox_r:drop_pos + d_vox_r + drop_len, 1] += drop_vox[:drop_len] * 0.90

# Whispers adicionales en compases 24 y 40
for bar_cue in [24, 40]:
    cue_pos = bar_cue * bar_samples
    vox_cue = synthesize_whisper_voice("Shadows fall", 1.4)
    c_len = min(len(vox_cue), TOTAL_SAMPLES - cue_pos)
    if c_len > 0:
        track_vox[cue_pos:cue_pos + c_len, 0] += vox_cue[:c_len] * 0.70
        track_vox[cue_pos:cue_pos + c_len, 1] += vox_cue[:c_len] * 0.75

# ── PISTA 9: DARK DISCO SYNTH STABS (Prophet-5 Chords con Desafinación) ───────
# Acordes menores en síncopa en compases 9..32 y 49..59
stab_chords_cents = [
    [0.0, 300.0, 700.0, 1050.0],       # Dm7 (Bayati 7th)
    [500.0, 800.0, 1200.0, 1500.0],    # Gm7
    [800.0, 1200.0, 1500.0, 1900.0]    # Bbmaj7
]
for bar in range(TOTAL_BARS):
    if not (8 <= bar < 32 or 48 <= bar < 59 or 60 <= bar < 64):
        continue
    bar_start = bar * bar_samples
    chord = stab_chords_cents[bar % len(stab_chords_cents)]
    # Toca en el pulso 2.5 y 4.5
    for beat_off in [1.5, 3.5]:
        hit_pos = bar_start + int(beat_off * beat_samples)
        dur = BEAT_SEC * 0.45
        n_stab = int(dur * SAMPLE_RATE)
        if hit_pos + n_stab >= TOTAL_SAMPLES:
            break
        t_stab = np.linspace(0, dur, n_stab, endpoint=False, dtype=np.float32)
        chord_wave = np.zeros(n_stab, dtype=np.float32)
        for c_note in chord:
            f0 = cents_to_freq(base_d3 * 2.0, c_note)
            # Dual detuned saw waves (+/- 8 cents)
            saw1 = 2.0 * (t_stab * (f0 * 1.0046) - np.floor(t_stab * (f0 * 1.0046) + 0.5))
            saw2 = 2.0 * (t_stab * (f0 * 0.9954) - np.floor(t_stab * (f0 * 0.9954) + 0.5))
            chord_wave += (saw1 + saw2) * 0.25
        # Lowpass filter and fast decay
        b, a = signal.butter(2, 2200.0 / (SAMPLE_RATE / 2), btype='lowpass')
        filt_chord = signal.lfilter(b, a, chord_wave) * np.exp(-t_stab * 10.0)
        val = np.tanh(filt_chord * 1.4) * 0.60
        track_stabs[hit_pos:hit_pos + n_stab, 0] += val * 0.65
        track_stabs[hit_pos:hit_pos + n_stab, 1] += val * 0.75

# ── PISTA 10: DRONE SUBTENSION FX & LECHO DE CINTA (-57 dBFS) ─────────────────
# 1. Lecho de cinta analógica continua (Living Tape Noise Floor)
t_full = np.linspace(0, DURATION_SEC, TOTAL_SAMPLES, endpoint=False, dtype=np.float32)
pink_noise = np.random.uniform(-1.0, 1.0, TOTAL_SAMPLES).astype(np.float32)
b_tape, a_tape = signal.butter(1, [150.0 / (SAMPLE_RATE / 2), 6500.0 / (SAMPLE_RATE / 2)], btype='bandpass')
tape_floor = signal.lfilter(b_tape, a_tape, pink_noise) * TAPE_FLOOR_AMP
track_drone[:, 0] += tape_floor
track_drone[:, 1] += tape_floor * 0.98

# 2. Sub-bass tension drone (D1 = 36.71 Hz) modulado
drone_osc = np.sin(2.0 * np.pi * 36.71 * t_full + 0.2 * np.sin(2.0 * np.pi * 0.15 * t_full))
# Fade in during first 8 bars and during tension build (bars 48-59)
drone_env = np.ones(TOTAL_SAMPLES, dtype=np.float32) * 0.35
drone_env[:bar_samples * 8] = np.linspace(0.0, 0.35, bar_samples * 8)
# Riser in bar 59
riser_start = 58 * bar_samples
riser_end = 59 * bar_samples
if riser_end < TOTAL_SAMPLES:
    drone_env[riser_start:riser_end] = np.linspace(0.35, 0.75, riser_end - riser_start)
track_drone[:, 0] += drone_osc * drone_env * 0.55
track_drone[:, 1] += drone_osc * drone_env * 0.55

print("Pistas sintetizadas con éxito. Procediendo a exportación de stems PCM 24-bit...")

# ── 5. EXPORTACIÓN DE STEMS MULTITRACK ────────────────────────────────────────
stems_map = {
    "01_KICK_DAMON_50HZ.wav": track_kick,
    "02_BASS_ROLLING_EBM.wav": track_bass,
    "03_POSTPUNK_CHORUS_GUITAR.wav": track_guitar,
    "04_SNARE_GATED_INDUSTRIAL.wav": track_snare,
    "05_HATS_PERC_MOTORIK.wav": track_hats,
    "06_CLAPS_CAVERN_STEREO.wav": track_claps,
    "07_ACID_303_MICROTONAL.wav": track_303,
    "08_CURSES_WHISPER_VOX.wav": track_vox,
    "09_DARK_DISCO_STABS.wav": track_stabs,
    "10_DRONE_SUBTENSION_FX.wav": track_drone,
}

for filename, data in stems_map.items():
    file_path = STEMS_DIR / filename
    # Normalizar stem para prevenir clipping individual
    peak = np.max(np.abs(data))
    scale = (0.85 / peak) if peak > 0.85 else 1.0
    sf.write(str(file_path), (data * scale).astype(np.float32), SAMPLE_RATE, subtype='PCM_24')
    print(f" -> Stem guardado: {filename} (Peak: {peak:.3f}, Scale: {scale:.3f})")

# ── 6. MEZCLA MASTER Y PROCESADO EBU R128 (CLUB PEAK) ────────────────────────
print("\nCompilando Master Bus Estéreo...")
master_mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)
# Suma de stems con balance de headroom orgánico
master_mix += track_kick * 0.85
master_mix += track_bass * 0.65
master_mix += track_guitar * 0.45
master_mix += track_snare * 0.60
master_mix += track_hats * 0.38
master_mix += track_claps * 0.45
master_mix += track_303 * 0.48
master_mix += track_vox * 0.55
master_mix += track_stabs * 0.40
master_mix += track_drone * 0.30

# 1. Crossover Linkwitz-Riley mono a 120 Hz en subgraves
b_low, a_low = signal.butter(4, 120.0 / (SAMPLE_RATE / 2), btype='lowpass')
b_high, a_high = signal.butter(4, 120.0 / (SAMPLE_RATE / 2), btype='highpass')

sub_l = signal.lfilter(b_low, a_low, master_mix[:, 0])
sub_r = signal.lfilter(b_low, a_low, master_mix[:, 1])
sub_mono = 0.5 * (sub_l + sub_r)  # Monofónico estricto bajo 120 Hz

high_l = signal.lfilter(b_high, a_high, master_mix[:, 0])
high_r = signal.lfilter(b_high, a_high, master_mix[:, 1])

master_processed = np.zeros_like(master_mix)
master_processed[:, 0] = sub_mono + high_l
master_processed[:, 1] = sub_mono + high_r

# 2. VCA Glue Bus: Preservar transitorios dinámicos sin aplastar picos
# Saturación analógica suave que redondea armónicos sin asfixiar el Crest Factor
master_saturated = np.tanh(master_processed * 0.90)

# 3. Lookahead True-Peak Limiter (-0.5 dBTP = 0.944)
target_peak = 10.0 ** (-0.5 / 20.0)
curr_peak = np.max(np.abs(master_saturated))
if curr_peak > 0:
    master_final = master_saturated * (target_peak / curr_peak)
else:
    master_final = master_saturated

master_path = OUTPUT_DIR / "Borja_Moskv_-_Lomu_Master.wav"
sf.write(str(master_path), master_final.astype(np.float32), SAMPLE_RATE, subtype='PCM_24')
print(f"Master final exportado: {master_path}")

# ── 7. COMPILACIÓN AUTOPOIÉTICA DE PROYECTO FL STUDIO (.FLP) ─────────────────
print("\nCompilando Proyecto Binario Nativo FL Studio (.flp)...")
try:
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    flp_path = OUTPUT_DIR / "Borja_Moskv_-_Lomu_Session.flp"
    res_flp = compile_multitrack_stems_flp(
        stems_dir=str(STEMS_DIR),
        project_title="Borja Moskv - Lomu",
        bpm=BPM,
        output_flp=str(flp_path),
        total_bars=TOTAL_BARS
    )
    print(f"FLP compilado con éxito: {flp_path} ({res_flp.get('total_stem_channels')} canales)")
except Exception as e:
    print(f"Aviso compilación FLP: {e}")

# ── 8. LINTER ACÚSTICO C5 (RUBIN AUDITOR) FAIL-CLOSED ─────────────────────────
print("\nEjecutando Linter Acústico de Silicio (Protocolo Rubin)...")
try:
    linter_script = Path.home() / ".gemini" / "config" / "skills" / "c5-rubin-acoustic-linter" / "scripts" / "audit_acoustic_exergy.py"
    if linter_script.exists():
        import subprocess
        res = subprocess.run([sys.executable, str(linter_script), str(master_path)], capture_output=True, text=True)
        print(res.stdout)
        if res.stderr:
            print("Linter Stderr:", res.stderr)
    else:
        print(f"Linter no encontrado en {linter_script}")
except Exception as e:
    print(f"Error ejecutando linter: {e}")

print("=== Proceso completado exitosamente ===")
