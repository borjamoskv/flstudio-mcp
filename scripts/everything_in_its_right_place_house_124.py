#!/usr/bin/env python3
"""
EVERYTHING IN ITS RIGHT PLACE — C5-REAL House 124 BPM Architecture (FL Studio 2025)
===================================================================================
Adapta la armonía y polirritmia de C Frigio (10/4 -> 4/4 a 124.0 BPM) sobre el stack
nativo `flstudio-mcp` (48 kHz / 24-bit PCM):
  - En modo estructural (sin --source-audio): genera la base House completa, stems,
    MIDI multicanal y proyecto .flp compilado (etiquetado AUTÓMATA_SINTÉTICO_ESTRUCTURAL).
  - Con --source-audio <WAV|FLAC> o --vocal-stem <WAV>: extrae con Demucs únicamente
    capas orgánicas (vocals/other), descarta batería residual (§10), ajusta a 124 BPM,
    aplica carving Bark + sidechain raised-cosine y compila el remix híbrido completo.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import mido
import numpy as np
from scipy import signal

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

try:
    from scripts.bounces_paths import resolve_bounces_dir
    from scripts.c5_dsp_core import (
        apply_coherent_shared_room,
        apply_noncommutative_dub_echo,
        apply_zero_crackle_envelope,
        build_coupled_multiband_sidechain,
        carve_polyphonic_mud,
        check_zero_crackle_derivatives,
        enforce_low_end_mono,
        freeze_array,
        generate_warm_analog_tape_bed,
        lr4_zero_phase_crossover,
        make_time_axis,
        oversampled_soft_saturate,
        polyblep_pulse,
        polyblep_saw,
        synthesize_phase_locked_kick,
        write_pcm_wav,
    )
    from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    from scripts.mastering_reverse_engine_fl import (
        compute_rubin_metrics,
        master_audio_reverse_engineered,
    )
except ImportError:
    from bounces_paths import resolve_bounces_dir
    from c5_dsp_core import (
        apply_coherent_shared_room,
        apply_noncommutative_dub_echo,
        apply_zero_crackle_envelope,
        build_coupled_multiband_sidechain,
        carve_polyphonic_mud,
        check_zero_crackle_derivatives,
        enforce_low_end_mono,
        freeze_array,
        generate_warm_analog_tape_bed,
        lr4_zero_phase_crossover,
        make_time_axis,
        oversampled_soft_saturate,
        polyblep_pulse,
        polyblep_saw,
        synthesize_phase_locked_kick,
        write_pcm_wav,
    )
    from flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    from mastering_reverse_engine_fl import (
        compute_rubin_metrics,
        master_audio_reverse_engineered,
    )

SAMPLE_RATE = 48000
BPM = 124.0
PPQ = 480
TOTAL_BARS = 64
KICK_ROOT_HZ = 49.00  # G1 (quinta justa de Do, zona de impacto 48-55 Hz)
MPC_SWING = 0.565
BASS_BEHIND_BEAT_SEC = 0.006

RUBIN_LINTER_PATH = Path(
    "/Users/borjafernandezangulo/.gemini/config/skills/"
    "c5-rubin-acoustic-linter/scripts/audit_acoustic_exergy.py"
)

# Progresión característica en C Frigio / pedal Do:
# Ciclo de 4 compases con agrupaciones polirrítmicas 3+3+2+2 en corcheas sobre 4/4
PHRYGIAN_CYCLE: List[Tuple[int, List[int], str]] = [
    (36, [48, 55, 60, 62, 67], "Csus2/C5"),       # C2 bass + C3 G3 C4 D4 G4
    (37, [49, 56, 60, 65, 68], "Dbmaj7"),         # Db2 bass + Db3 Ab3 C4 F4 Ab4
    (39, [51, 58, 60, 63, 67], "Eb6"),            # Eb2 bass + Eb3 Bb3 C4 Eb4 G4
    (41, [48, 53, 56, 60, 63], "Fm7/C"),          # F2 bass + C3 F3 Ab3 C4 Eb4
]

# Variaciones B (tensiones frigias y colores superiores para segundas vueltas de 8 compases)
PHRYGIAN_VARIATIONS_B: List[List[int]] = [
    [48, 55, 60, 62, 63, 67],  # Cm9/addb9 color sobre pedal Do
    [49, 56, 60, 65, 67],      # Dbmaj7#11 (resonancia G4)
    [51, 58, 60, 62, 67],      # Eb6/9 abierto
    [48, 53, 56, 60, 63, 67],  # Fm9/C
]

# Posiciones en corcheas dentro de un bloque de 4 compases (32 corcheas):
# superpone el pulso 3+3+2+2 (10 corcheas) sobre el grid 4/4 resolviendo en el ciclo
POLYRHYTHM_EIGHTHS = [0, 3, 6, 8, 10, 13, 16, 18, 20, 23, 26, 28]


def generate_voss_clarke_curve(length: int, seed: int = 124) -> np.ndarray:
    """
    Genera una curva fractal correlacionada 1/f (ruido rosa Voss-Clarke determinista)
    normalizada en [-1.0, 1.0] para modular fraseo, filtro y micro-bolsillo sin ruido blanco ciego.
    """
    n = max(16, int(length))
    rng = np.random.default_rng(seed)
    white = rng.normal(0.0, 1.0, n)
    spec = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n)
    freqs[0] = max(1e-3, freqs[1] * 0.5 if len(freqs) > 1 else 1e-3)
    pink = np.fft.irfft(spec / np.sqrt(freqs), n=n)
    pink = (pink - float(np.mean(pink))) / (float(np.std(pink)) + 1e-8)
    return np.tanh(pink * 0.55) / math.tanh(1.25)


def compute_phrase_rubato_sec(bar_idx: int, false_drop_bar: int) -> float:
    """
    Micro-modulación fraseológica determinista (±3.4 ms): empuja hacia mitad/cierre de
    hipercompás de 8 compases y aterriza en 0.0 exacto en los inicios de frase y en el Falso Drop.
    """
    if bar_idx in (false_drop_bar, false_drop_bar + 1) or (bar_idx % 8 == 0):
        return 0.0
    phase = 2.0 * math.pi * float(bar_idx % 8) / 8.0
    return -0.0034 * math.sin(phase)


def midi_to_hz(midi_note: float) -> float:
    return 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))


def add_stereo(
    buf_l: np.ndarray,
    buf_r: np.ndarray,
    clip_l: np.ndarray,
    clip_r: np.ndarray,
    start_idx: int,
    gain: float = 1.0,
) -> None:
    if start_idx >= len(buf_l) or len(clip_l) == 0:
        return
    src_start = max(0, -start_idx)
    dst_start = max(0, start_idx)
    avail = min(len(clip_l) - src_start, len(buf_l) - dst_start)
    if avail <= 0:
        return
    buf_l[dst_start : dst_start + avail] += clip_l[src_start : src_start + avail] * gain
    buf_r[dst_start : dst_start + avail] += clip_r[src_start : src_start + avail] * gain


def _compute_swing_offset_sec(sixteenth_idx: int, sixteenth_sec: float) -> float:
    """Desplaza las semicorcheas pares según swing Roger Linn MPC (56.5%)."""
    if sixteenth_idx % 2 == 1:
        return (MPC_SWING - 0.5) * 2.0 * sixteenth_sec
    return 0.0


def render_prophet_chord_event(
    notes_midi: Sequence[int],
    duration_sec: float,
    cutoff_peak_hz: float = 1750.0,
    velocity: float = 0.85,
    sample_rate: int = SAMPLE_RATE,
    strum_ms: float = 8.5,
    detune_bias_cents: float = 0.0,
    seed: int = 0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Síntesis cálida estilo Prophet-5 / Rhodes con micro-strumming variable y deriva térmica 1/f."""
    n = max(64, int(round(duration_sec * sample_rate)))
    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)

    base_strum = max(0.004, min(0.018, strum_ms / 1000.0))
    n_voices = len(notes_midi)
    for voice_idx, m_note in enumerate(notes_midi):
        # Ligero empuje orgánico por voz sin desordenar el arpegio ascendente
        voice_curve = 0.12 * math.sin(seed * 0.7 + voice_idx * 1.4)
        delay_s = max(0, int(round(voice_idx * base_strum * (1.0 + voice_curve) * sample_rate)))
        if delay_s >= n - 32:
            break
        v_len = n - delay_s
        tv = make_time_axis(v_len, sample_rate)
        f0 = midi_to_hz(float(m_note)) * (2.0 ** (detune_bias_cents / 1200.0))
        # Voces extremas (bajo del acorde y voz melódica superior) destacan sobre las internas
        voice_weight = 1.10 if voice_idx in (0, n_voices - 1) else 0.90
        # Dos VCOs analógicos con deriva térmica + sub sinusoidal
        osc_a = polyblep_saw(f0 * (2.0 ** (-4.2 / 1200.0)), v_len, sample_rate, initial_phase=0.07 * voice_idx)
        osc_b = polyblep_pulse(f0 * (2.0 ** (4.2 / 1200.0)), v_len, sample_rate, duty=0.46, initial_phase=0.19 * voice_idx)
        sub_sine = 0.30 * np.sin(2.0 * math.pi * f0 * tv)
        env_amp = freeze_array(np.exp(-tv / max(0.28, duration_sec * 0.72)))
        raw = (0.42 * osc_a + 0.36 * osc_b + sub_sine) * env_amp * voice_weight

        # Filtro paso-bajo de envolvente en dos bandas acoplado a velocidad (mayor velocity -> apertura más brillante)
        nyq = 0.5 * sample_rate
        vel_brightness = 0.76 + 0.34 * float(np.clip(velocity, 0.25, 1.15))
        c_hi = min(0.85, (cutoff_peak_hz * vel_brightness) / nyq)
        c_lo = min(0.60, max(280.0, cutoff_peak_hz * 0.34) / nyq)
        sos_hi = signal.butter(2, c_hi, btype="low", output="sos")
        sos_lo = signal.butter(2, c_lo, btype="low", output="sos")
        env_filt = freeze_array(np.exp(-tv / 0.24))
        bright = signal.sosfilt(sos_hi, raw)
        warm = signal.sosfilt(sos_lo, raw)
        filtered = env_filt * bright + (1.0 - env_filt) * warm

        voice_env = apply_zero_crackle_envelope(filtered, sample_rate=sample_rate, attack_ms=8.0, release_ms=18.0)
        pan = -0.28 + 0.56 * (voice_idx / max(1, n_voices - 1))
        gain_l = math.cos((pan + 1.0) * math.pi * 0.25)
        gain_r = math.sin((pan + 1.0) * math.pi * 0.25)
        left[delay_s:] += voice_env * gain_l
        right[delay_s:] += voice_env * gain_r

    norm = max(1.0, math.sqrt(max(1, n_voices)))
    left = oversampled_soft_saturate((left / norm) * velocity * 0.92, drive_db=1.2, threshold_db=-3.5)
    right = oversampled_soft_saturate((right / norm) * velocity * 0.92, drive_db=1.2, threshold_db=-3.5)
    return (
        apply_zero_crackle_envelope(left, sample_rate=sample_rate, attack_ms=6.0, release_ms=14.0),
        apply_zero_crackle_envelope(right, sample_rate=sample_rate, attack_ms=6.0, release_ms=14.0),
    )


def render_sub_bass_note(
    midi_note: int,
    duration_sec: float,
    velocity: float = 0.9,
    sample_rate: int = SAMPLE_RATE,
    accent_slide_cents: float = 0.0,
) -> np.ndarray:
    """Subgrave C Frigio Zero-Crackle con muesca Bark (49 Hz) y micro-inflexión expresiva."""
    n = max(64, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    f0 = midi_to_hz(float(midi_note))

    if abs(accent_slide_cents) > 0.1:
        f_inst = f0 * (2.0 ** ((accent_slide_cents * np.exp(-t / 0.045)) / 1200.0))
        phase = freeze_array(2.0 * math.pi * (np.cumsum(f_inst) - f_inst[0]) / float(sample_rate))
        fundamental = 0.78 * np.sin(phase)
    else:
        fundamental = 0.78 * np.sin(2.0 * math.pi * f0 * t)

    warm_saw = 0.24 * polyblep_saw(f0, n, sample_rate=sample_rate, initial_phase=0.0)
    sos_lp = signal.butter(2, 220.0 / (0.5 * sample_rate), btype="low", output="sos")
    harm = signal.sosfilt(sos_lp, warm_saw)

    env = freeze_array(np.exp(-t / max(0.14, duration_sec * 0.95)))
    raw = freeze_array((fundamental + harm) * env * velocity * 0.56)

    # Muesca paramétrica en la fundamental del bombo (49 Hz, -3.8 dB)
    b_n, a_n = signal.iirnotch(KICK_ROOT_HZ, Q=2.3, fs=sample_rate)
    carved = 0.58 * signal.lfilter(b_n, a_n, raw) + 0.42 * raw
    carved = oversampled_soft_saturate(carved, drive_db=1.1, threshold_db=-4.5)
    return apply_zero_crackle_envelope(carved, sample_rate=sample_rate, attack_ms=8.0, release_ms=14.0)


def render_organic_clap(sample_rate: int = SAMPLE_RATE, variant: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(700 + variant)
    n = int(round(0.18 * sample_rate))
    t = make_time_axis(n, sample_rate)
    d2 = 0.0085 + 0.0012 * (variant % 3)
    d3 = 0.019 + 0.002 * (variant % 4)
    bursts = freeze_array(
        np.exp(-t / 0.008)
        + 0.72 * np.exp(-np.maximum(0.0, t - d2) / 0.011) * (t >= d2)
        + 0.55 * np.exp(-np.maximum(0.0, t - d3) / (0.026 + 0.003 * (variant % 3))) * (t >= d3)
    )
    tone_body = 0.35 * np.sin(2.0 * math.pi * (625.0 + 18.0 * (variant % 5)) * t) * np.exp(-t / 0.014)
    noise_l = freeze_array(rng.normal(0.0, 1.0, n))
    noise_r = 0.86 * noise_l + 0.14 * rng.normal(0.0, 1.0, n)
    sos_bp = signal.butter(2, [650.0 / (0.5 * sample_rate), 2600.0 / (0.5 * sample_rate)], btype="band", output="sos")
    cl_l = (signal.sosfilt(sos_bp, noise_l) + tone_body) * bursts * 0.13
    cl_r = (signal.sosfilt(sos_bp, noise_r) + tone_body) * bursts * 0.13
    return (
        apply_zero_crackle_envelope(cl_l, sample_rate=sample_rate, attack_ms=5.0, release_ms=12.0),
        apply_zero_crackle_envelope(cl_r, sample_rate=sample_rate, attack_ms=5.0, release_ms=12.0),
    )


def render_house_hat(
    open_hat: bool = False,
    sample_rate: int = SAMPLE_RATE,
    variant: int = 0,
    decay_sec: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng((900 if open_hat else 800) + variant)
    tau = decay_sec if decay_sec is not None else (0.065 if open_hat else 0.015)
    dur = max(0.048, min(0.28, tau * 3.8))
    n = int(round(dur * sample_rate))
    t = make_time_axis(n, sample_rate)
    decay = freeze_array(np.exp(-t / max(0.008, tau)))

    # Parciales metálicos agudos + aire limpio entre 6.2 kHz y 13.8 kHz (fuera de banda media vocal)
    partials = sum(
        np.sin(2.0 * math.pi * (f + 45.0 * (variant % 4)) * t + 0.3 * i)
        for i, f in enumerate([6320.0, 7940.0, 9610.0, 11420.0])
    ) * 0.22
    n_l = freeze_array(rng.normal(0.0, 1.0, n) * 0.35 + partials)
    n_r = (0.86 * n_l + 0.14 * rng.normal(0.0, 1.0, n)) * 0.96

    nyq = 0.5 * sample_rate
    sos_bp = signal.butter(2, [6200.0 / nyq, 13800.0 / nyq], btype="band", output="sos")
    level = 0.115 if open_hat else 0.072
    h_l = signal.sosfilt(sos_bp, n_l) * decay * level
    h_r = signal.sosfilt(sos_bp, n_r) * decay * level
    return (
        apply_zero_crackle_envelope(h_l, sample_rate=sample_rate, attack_ms=5.0, release_ms=10.0),
        apply_zero_crackle_envelope(h_r, sample_rate=sample_rate, attack_ms=5.0, release_ms=10.0),
    )


def render_ghost_wood_perc(
    sample_rate: int = SAMPLE_RATE,
    variant: int = 0,
    freq_hz: float = 720.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Micro-percusión orgánica tipo woodblock/rim amortiguado (Slicex off-grid RAE Ley 8).
    Cuerpo resonante acotado bajo 1.5 kHz para añadir síncopa viva sin ensuciar la SFM media.
    """
    rng = np.random.default_rng(1100 + variant)
    n = int(round(0.065 * sample_rate))
    t = make_time_axis(n, sample_rate)
    f_body = freq_hz * (1.0 + 0.12 * np.exp(-t / 0.004))
    phase = freeze_array(2.0 * math.pi * (np.cumsum(f_body) - f_body[0]) / float(sample_rate))
    modal = (
        0.72 * np.sin(phase) * np.exp(-t / 0.011)
        + 0.28 * np.sin(2.38 * phase + 0.4) * np.exp(-t / 0.006)
    )
    brush = signal.sosfilt(
        signal.butter(2, [380.0 / (0.5 * sample_rate), 1450.0 / (0.5 * sample_rate)], btype="band", output="sos"),
        rng.normal(0.0, 1.0, n),
    ) * np.exp(-t / 0.009) * 0.22
    raw = freeze_array((modal + brush) * 0.11)
    pan = -0.35 + 0.70 * ((variant % 5) / 4.0)
    gl = math.cos((pan + 1.0) * math.pi * 0.25)
    gr = math.sin((pan + 1.0) * math.pi * 0.25)
    return (
        apply_zero_crackle_envelope(raw * gl, sample_rate=sample_rate, attack_ms=4.0, release_ms=10.0),
        apply_zero_crackle_envelope(raw * gr, sample_rate=sample_rate, attack_ms=4.0, release_ms=10.0),
    )


def render_melodic_techno_arp_note(
    midi_note: float,
    duration_sec: float,
    cutoff_hz: float = 1950.0,
    velocity: float = 0.78,
    pan: float = 0.0,
    vibrato_delay_sec: float = 0.14,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Voz analógica modular para Melodic Techno avant-garde: PolyBLEP saw + sub-triángulo,
    mordida FM exponencial solo en el transitorio (<= 22 ms), inflexión microtonal frigia b2
    y vibrato retardado RAE Ley 13 tras vibrato_delay_sec.
    """
    n = max(64, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    # Inflexión gravitacional sobre b2 (Db) y semitonos tensos del modo Frigio
    pc = int(round(midi_note)) % 12
    bend_cents = (-12.0 * np.exp(-t / 0.055)) if pc == 1 else np.zeros_like(t)
    vib_onset = np.clip((t - vibrato_delay_sec) / 0.18, 0.0, 1.0)
    vib_cents = 8.5 * vib_onset * np.sin(2.0 * math.pi * 5.2 * t)
    f_base = midi_to_hz(float(midi_note))
    f_inst = f_base * (2.0 ** ((bend_cents + vib_cents) / 1200.0))
    phase = freeze_array(2.0 * math.pi * (np.cumsum(f_inst) - f_inst[0]) / float(sample_rate))

    saw = polyblep_saw(f_base, n, sample_rate=sample_rate, initial_phase=0.11)
    # Modular FM bite limitado a 22 ms para preservar calidez sin estridencia en 2-5 kHz
    fm_index = freeze_array(0.32 * np.exp(-t / 0.022))
    core_osc = freeze_array(
        0.52 * np.sin(phase + fm_index * np.sin(2.0 * phase))
        + 0.30 * saw
        + 0.24 * np.sin(0.5 * phase)
    )
    env_amp = freeze_array((1.0 - np.exp(-t / 0.006)) * np.exp(-t / max(0.08, duration_sec * 0.62)))
    raw = core_osc * env_amp

    nyq = 0.5 * sample_rate
    vel_open = 0.72 + 0.42 * float(np.clip(velocity, 0.25, 1.15))
    c_hi = min(0.82, max(450.0, cutoff_hz * vel_open) / nyq)
    c_lo = min(0.50, max(240.0, cutoff_hz * 0.30) / nyq)
    bright = signal.sosfilt(signal.butter(2, c_hi, btype="low", output="sos"), raw)
    warm = signal.sosfilt(signal.butter(2, c_lo, btype="low", output="sos"), raw)
    f_env = freeze_array(np.exp(-t / 0.11))
    tone = oversampled_soft_saturate(
        (f_env * bright + (1.0 - f_env) * warm) * velocity * 0.44,
        drive_db=1.35,
        threshold_db=-4.0,
    )
    shaped = freeze_array(apply_zero_crackle_envelope(tone, sample_rate=sample_rate, attack_ms=5.5, release_ms=16.0))
    p = float(np.clip(pan, -0.65, 0.65))
    gl = math.cos((p + 1.0) * math.pi * 0.25)
    gr = math.sin((p + 1.0) * math.pi * 0.25)
    return shaped * gl, shaped * gr


def render_avantgarde_spectral_bow(
    notes_midi: Sequence[float] = (60.0, 67.0, 73.0, 77.0),
    duration_sec: float = 3.2,
    gain: float = 0.18,
    seed: int = 0,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Arco espectral micro-desafinado para silencios vivos, breakdown y transiciones avant-garde:
    parciales armónicos puros con respiración lenta (bajo SFM, alta coherencia estéreo).
    """
    n = max(256, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    swell = freeze_array(0.5 * (1.0 - np.cos(2.0 * math.pi * np.clip(t / max(0.1, duration_sec), 0.0, 1.0))))
    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)

    for idx, m_note in enumerate(notes_midi):
        f0 = midi_to_hz(float(m_note))
        # Deriva lenta tipo Ondes Martenot (±14 cents) en núcleo coherente en fase + respiración panorámica
        drift_c = 14.0 * np.sin(2.0 * math.pi * (0.28 + 0.06 * idx) * t + seed * 0.5)
        ph_c = 2.0 * math.pi * np.cumsum(f0 * (2.0 ** (drift_c / 1200.0))) / float(sample_rate)
        w = 1.0 / (1.0 + 0.45 * idx)
        sig_c = freeze_array((0.76 * np.sin(ph_c) + 0.24 * np.sin(2.0 * ph_c + 0.2)) * swell * w)
        pan_base = -0.18 + 0.36 * (idx / max(1, len(notes_midi) - 1))
        pan_t = pan_base + 0.14 * np.sin(2.0 * math.pi * (0.19 + 0.04 * idx) * t + seed * 0.3)
        angle = freeze_array((pan_t + 1.0) * math.pi * 0.25)
        left += sig_c * np.cos(angle)
        right += sig_c * np.sin(angle)

    sos_lp = signal.butter(2, 3100.0 / (0.5 * sample_rate), btype="low", output="sos")
    left = signal.sosfilt(sos_lp, left) * gain
    right = signal.sosfilt(sos_lp, right) * gain
    return (
        apply_zero_crackle_envelope(left, sample_rate=sample_rate, attack_ms=25.0, release_ms=45.0),
        apply_zero_crackle_envelope(right, sample_rate=sample_rate, attack_ms=25.0, release_ms=45.0),
    )


def render_sub_drop_transition(sample_rate: int = SAMPLE_RATE) -> Tuple[np.ndarray, np.ndarray]:
    """Caída de frecuencia subgrave 130 Hz -> 32 Hz en la entrada al breakdown (§2.3)."""
    dur = 1.65
    n = int(round(dur * sample_rate))
    t = make_time_axis(n, sample_rate)
    f_inst = 32.0 + (130.0 - 32.0) * np.exp(-t / 0.42)
    phase = 2.0 * math.pi * (np.cumsum(f_inst) - f_inst[0]) / float(sample_rate)
    sig = np.sin(phase) * np.exp(-t / 0.65) * 0.38
    sig = apply_zero_crackle_envelope(sig, sample_rate=sample_rate, attack_ms=12.0, release_ms=40.0)
    return sig, sig.copy()


def _apply_smooth_gate_window(
    buf: np.ndarray,
    start_idx: int,
    end_idx: int,
    fade_ms: float = 14.0,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    """Silencia suavemente una ventana [start_idx, end_idx) con rampas raised-cosine."""
    n = len(buf)
    s0 = max(0, start_idx)
    s1 = min(n, end_idx)
    if s1 <= s0:
        return
    f_len = min((s1 - s0) // 2, max(8, int(round((fade_ms / 1000.0) * sample_rate))))
    w = np.zeros(s1 - s0, dtype=np.float64)
    w[:f_len] = 0.5 * (1.0 + np.cos(np.pi * np.arange(f_len) / max(1, f_len - 1)))
    w[-f_len:] = 0.5 * (1.0 - np.cos(np.pi * np.arange(f_len) / max(1, f_len - 1)))
    buf[s0:s1] *= w


def extract_organic_stems_with_demucs(
    source_audio: Path,
    work_dir: Path,
    keep_other: bool = False,
) -> Dict[str, Path]:
    """
    Separa audio fuente legítimo con Demucs conservando solo capas orgánicas
    (vocals y opcionalmente other) y descartando siempre drums residuales (§10).
    """
    out_root = work_dir / "demucs_separated"
    out_root.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "demucs.separate",
        "-n",
        "htdemucs",
        "-o",
        str(out_root),
    ]
    if not keep_other:
        cmd.extend(["--two-stems", "vocals"])
    cmd.append(str(source_audio))

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Demucs falló (exit {proc.returncode}): {proc.stderr[-600:]}")

    stem_dir = out_root / "htdemucs" / source_audio.stem
    vocals = stem_dir / "vocals.wav"
    if not vocals.exists():
        raise FileNotFoundError(f"Demucs no generó vocals.wav esperado en {stem_dir}")

    result = {"vocals": vocals}
    other = stem_dir / "other.wav"
    if keep_other and other.exists():
        result["other"] = other
    return result


def align_organic_stem_to_house(
    stem_path: Path,
    target_samples: int,
    target_bpm: float = BPM,
    sample_rate: int = SAMPLE_RATE,
    source_bpm_override: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Carga stem orgánico, estima BPM (o usa override), ajusta con time-stretch,
    remuestrea exactamente a 48 kHz con resample_poly y aplica Bark carving.
    """
    import librosa
    import soundfile as sf

    data, sr_in = sf.read(str(stem_path), always_2d=True)
    data = data.astype(np.float64)
    if data.shape[1] == 1:
        data = np.column_stack((data[:, 0], data[:, 0]))
    else:
        data = data[:, :2]

    if source_bpm_override and source_bpm_override > 20.0:
        src_bpm = float(source_bpm_override)
    else:
        mono_est = 0.5 * (data[:, 0] + data[:, 1])
        tempo_val, _ = librosa.beat.beat_track(y=mono_est, sr=sr_in)
        src_bpm = float(np.atleast_1d(tempo_val)[0])
        if src_bpm < 55.0:
            src_bpm *= 2.0
        elif src_bpm > 175.0:
            src_bpm *= 0.5

    if sr_in != sample_rate:
        g = math.gcd(int(sample_rate), int(sr_in))
        data = signal.resample_poly(data, up=int(sample_rate) // g, down=int(sr_in) // g, axis=0)

    rate = float(np.clip(target_bpm / max(src_bpm, 40.0), 0.72, 1.45))
    if abs(rate - 1.0) > 0.004:
        l_st = librosa.effects.time_stretch(data[:, 0], rate=rate)
        r_st = librosa.effects.time_stretch(data[:, 1], rate=rate)
        n_st = min(len(l_st), len(r_st))
        l_ch, r_ch = l_st[:n_st], r_st[:n_st]
    else:
        l_ch, r_ch = data[:, 0], data[:, 1]

    out_l = np.zeros(target_samples, dtype=np.float64)
    out_r = np.zeros(target_samples, dtype=np.float64)
    copy_n = min(target_samples, len(l_ch))
    out_l[:copy_n] = apply_zero_crackle_envelope(l_ch[:copy_n], sample_rate=sample_rate, attack_ms=15.0, release_ms=40.0)
    out_r[:copy_n] = apply_zero_crackle_envelope(r_ch[:copy_n], sample_rate=sample_rate, attack_ms=15.0, release_ms=40.0)
    out_l, out_r = carve_polyphonic_mud(out_l, out_r, sample_rate=sample_rate, hpf_hz=190.0, mud_hz=360.0)
    return out_l, out_r, src_bpm


def write_multichannel_midi(
    midi_path: Path,
    track_events: Dict[str, List[Tuple[int, int, int, int]]],
    bpm: float = BPM,
) -> Path:
    """Escribe SMF Tipo 1 (480 PPQ) con cero deriva absoluta."""
    mid = mido.MidiFile(type=1, ticks_per_beat=PPQ)
    conductor = mido.MidiTrack()
    conductor.name = "Conductor_124BPM"
    conductor.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    conductor.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))

    markers = [
        (0, "PRELUDE: Tape Bed, Spectral Bow & Dark Prophet"),
        (8 * 4 * PPQ, "EMERGENCE: Breathing Hats & Ghost Rim Syncopation"),
        (15 * 4 * PPQ + 3 * PPQ, "BAR 16 CAESURA: Living Silence Before Act I"),
        (16 * 4 * PPQ, "ACT I GROOVE: 3+3+2+2 Polyrhythm & Phrygian Syncopation"),
        (24 * 4 * PPQ, "ACT I B: Polymetric 5/16 Melodic Techno Arp Enters"),
        (31 * 4 * PPQ + 2 * PPQ, "BAR 32 CAESURA: Pre-Abyss Negative Space"),
        (32 * 4 * PPQ, "ABYSS BREAKDOWN: Sub Drop 130->32 Hz & Spectral Canyon"),
        (40 * 4 * PPQ, "ASCENSION: Hat Decay Swell & Filter Opening"),
        (47 * 4 * PPQ + 2 * PPQ, "BAR 48 VACUUM: Pre-Climax Sculpted Silence"),
        (48 * 4 * PPQ, "ACT II CLIMAX: Avant-Garde Melodic Techno Drive"),
        (59 * 4 * PPQ + 2 * PPQ, "BAR 60: C5 False Drop Vacuum (Tape + Dub Tail)"),
        (60 * 4 * PPQ, "FINAL DROP: Apex Impact"),
        (63 * 4 * PPQ, "LIVING EXIT: RC Exponential Decay"),
    ]
    abs_evs: List[Tuple[int, mido.MetaMessage]] = [(t, mido.MetaMessage("marker", text=txt, time=0)) for t, txt in markers]
    last_t = 0
    for tick, msg in sorted(abs_evs, key=lambda x: x[0]):
        conductor.append(msg.copy(time=max(0, tick - last_t)))
        last_t = tick
    conductor.append(mido.MetaMessage("end_of_track", time=0))
    mid.tracks.append(conductor)

    for ch_idx, (tr_name, notes) in enumerate(track_events.items()):
        tr = mido.MidiTrack()
        tr.name = tr_name
        raw_msgs: List[Tuple[int, int, mido.Message]] = []
        channel = 9 if "drums" in tr_name.lower() or "kick" in tr_name.lower() else (ch_idx % 8)
        for t0, t1, pitch, vel in notes:
            p = int(np.clip(pitch, 0, 127))
            v = int(np.clip(vel, 1, 127))
            raw_msgs.append((max(0, t0), 1, mido.Message("note_on", channel=channel, note=p, velocity=v, time=0)))
            raw_msgs.append((max(t0 + 10, t1), 0, mido.Message("note_off", channel=channel, note=p, velocity=0, time=0)))

        raw_msgs.sort(key=lambda item: (item[0], item[1]))
        prev_t = 0
        for t_abs, _, msg in raw_msgs:
            tr.append(msg.copy(time=max(0, t_abs - prev_t)))
            prev_t = t_abs
        tr.append(mido.MetaMessage("end_of_track", time=0))
        mid.tracks.append(tr)

    midi_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(midi_path))
    return midi_path


def build_everything_house_124(
    source_audio: Optional[str] = None,
    vocal_stem: Optional[str] = None,
    keep_other: bool = False,
    source_bpm_override: Optional[float] = None,
    profile_name: str = "deep_house",
    total_bars: int = TOTAL_BARS,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Orquesta la compilación completa (Master + Stems + MIDI + FLP + Rubin Gate)."""
    beat_sec = 60.0 / BPM
    bar_sec = 4.0 * beat_sec
    eighth_sec = 0.5 * beat_sec
    sixteenth_sec = 0.25 * beat_sec
    total_sec = total_bars * bar_sec
    n_samples = int(round(total_sec * SAMPLE_RATE))

    bounces_root = Path(output_dir).expanduser().resolve() if output_dir else resolve_bounces_dir()
    project_dir = bounces_root / "Everything_In_Its_Right_Place_House_124"
    stems_dir = project_dir / "stems"
    project_dir.mkdir(parents=True, exist_ok=True)
    stems_dir.mkdir(parents=True, exist_ok=True)
    for stale_wav in stems_dir.glob("*.wav"):
        stale_wav.unlink()

    # Buffers estéreo por stem (7 stems base + 8.º stem orgánico si hay --source-audio/--vocal-stem)
    kick_l = np.zeros(n_samples, dtype=np.float64)
    kick_r = np.zeros(n_samples, dtype=np.float64)
    perc_l = np.zeros(n_samples, dtype=np.float64)
    perc_r = np.zeros(n_samples, dtype=np.float64)
    bass_l = np.zeros(n_samples, dtype=np.float64)
    bass_r = np.zeros(n_samples, dtype=np.float64)
    chords_l = np.zeros(n_samples, dtype=np.float64)
    chords_r = np.zeros(n_samples, dtype=np.float64)
    avant_l = np.zeros(n_samples, dtype=np.float64)
    avant_r = np.zeros(n_samples, dtype=np.float64)
    dub_send_l = np.zeros(n_samples, dtype=np.float64)
    dub_send_r = np.zeros(n_samples, dtype=np.float64)

    # Curvas fractales Voss-Clarke 1/f deterministas (micro-groove correlacionado, sin ruido blanco ciego)
    pink_bar = generate_voss_clarke_curve(max(16, total_bars), seed=124)
    pink_step = generate_voss_clarke_curve(max(64, total_bars * 16), seed=224)

    # Bancos round-robin de 8 articulaciones (erradicación efecto metralleta + respiración RAE Ley 9)
    sos_kick_warm = signal.butter(2, 1350.0 / (0.5 * SAMPLE_RATE), btype="low", output="sos")
    kicks_rr: List[np.ndarray] = []
    ghost_kicks_rr: List[np.ndarray] = []
    sos_ghost_k = signal.butter(2, [60.0 / (0.5 * SAMPLE_RATE), 960.0 / (0.5 * SAMPLE_RATE)], btype="band", output="sos")
    for i in range(8):
        k_raw = synthesize_phase_locked_kick(
            sample_rate=SAMPLE_RATE,
            duration_sec=0.38,
            root_hz=KICK_ROOT_HZ,
            punch_hz=135.0 + 1.5 * i,
            click_hz=1220.0 + 18.0 * (i % 4),
            drive_db=1.65 + 0.06 * i,
        )
        k_warm = signal.sosfilt(sos_kick_warm, k_raw)
        k_warm = apply_zero_crackle_envelope(k_warm, sample_rate=SAMPLE_RATE, attack_ms=0.8, release_ms=12.0)
        k_pk = float(np.max(np.abs(k_warm)))
        if k_pk > 1e-6:
            k_warm = k_warm / k_pk
        kicks_rr.append(k_warm)
        if i < 4:
            gk = signal.sosfilt(sos_ghost_k, k_warm[: int(round(0.16 * SAMPLE_RATE))])
            gk = apply_zero_crackle_envelope(gk, sample_rate=SAMPLE_RATE, attack_ms=2.0, release_ms=16.0)
            g_pk = float(np.max(np.abs(gk)))
            ghost_kicks_rr.append(gk / g_pk if g_pk > 1e-6 else gk)

    claps_rr = [render_organic_clap(SAMPLE_RATE, variant=i) for i in range(8)]
    # Hi-hat decay breathing: 11 ms -> 32 ms (cerrados) y 48 ms -> 88 ms (abiertos)
    hats_c_rr = [
        render_house_hat(False, SAMPLE_RATE, variant=i, decay_sec=0.011 + 0.003 * i)
        for i in range(8)
    ]
    hats_o_rr = [
        render_house_hat(True, SAMPLE_RATE, variant=i, decay_sec=0.048 + 0.0057 * i)
        for i in range(8)
    ]
    wood_freqs = [640.0, 710.0, 790.0, 860.0, 680.0, 745.0, 825.0, 910.0]
    wood_rr = [
        render_ghost_wood_perc(SAMPLE_RATE, variant=i, freq_hz=wood_freqs[i])
        for i in range(8)
    ]

    midi_tracks: Dict[str, List[Tuple[int, int, int, int]]] = {
        "Drums_Kick": [],
        "Drums_MPC_Perc": [],
        "SubBass_C_Phrygian": [],
        "Prophet_Rhodes_Motif": [],
        "AvantGarde_Melodic_Techno": [],
    }
    kick_onsets: List[int] = []

    false_drop_bar = 59 if total_bars >= 64 else max(4, total_bars - 5)

    timing_offsets_ms: List[float] = []
    strum_ms_values: List[float] = []
    bass_pocket_values_ms: List[float] = []
    syncopated_turnaround_events = 0
    ghost_perc_events = 0
    spectral_bow_events = 0

    def _is_rhythm_muted(b_i: int, b_pos: float) -> bool:
        if b_i == false_drop_bar and b_pos >= 2.0:
            return True
        if b_i == (total_bars - 1) and b_pos >= 2.0:
            return True
        if total_bars >= 32 and b_i == 15 and b_pos >= 3.0:  # Bar 16 Beat 4 Caesura Silence
            return True
        if total_bars >= 48 and b_i == 31 and b_pos >= 2.0:  # Bar 32 Beats 3-4 Pre-Abyss Silence
            return True
        if total_bars >= 56 and b_i == 47 and b_pos >= 2.0:  # Bar 48 Beats 3-4 Pre-Climax Vacuum
            return True
        return False

    beat_vel_weights = [1.00, 0.93, 0.98, 0.95]
    arp_step_idx = 0
    arp_cell_a = [72.0, 73.0, 79.0, 75.0, 74.0]  # C5 Db5 G5 Eb5 D5 (motivo C Frigio)
    arp_cell_b = [72.0, 68.0, 70.0, 75.0, 79.0]  # C5 Ab4 Bb4 Eb5 G5 (tensión Acto II)

    for bar_idx in range(total_bars):
        bar_t0 = bar_idx * bar_sec
        bar_tick0 = bar_idx * 4 * PPQ
        cycle_pos = bar_idx % 4
        bass_midi, _, _ = PHRYGIAN_CYCLE[cycle_pos]
        next_bass_midi = PHRYGIAN_CYCLE[(bar_idx + 1) % 4][0]

        in_intro_silent = bar_idx < 8
        in_intro_soft = 8 <= bar_idx < 16
        in_breakdown_vac = 32 <= bar_idx < 40
        in_breakdown_rise = 40 <= bar_idx < 48
        is_false_drop_bar = bar_idx == false_drop_bar
        is_b_cycle = ((bar_idx // 4) % 2 == 1) and (bar_idx >= 8)

        rubato_sec = compute_phrase_rubato_sec(bar_idx, false_drop_bar)
        u_phrase = (bar_idx % 4) / 3.0
        hat_breath_idx = int(round(u_phrase * 7.0))

        # Transición Breakdown Cavern (compás 33) + Arcos Espectrales Avant-Garde en silencios vivos
        if bar_idx == 32:
            drop_l, drop_r = render_sub_drop_transition(SAMPLE_RATE)
            add_stereo(dub_send_l, dub_send_r, drop_l, drop_r, int(round(bar_t0 * SAMPLE_RATE)), gain=0.72)

        spectral_trigger = None
        if bar_idx in (0, 4):
            spectral_trigger = (0.0, (60.0, 67.0, 73.0, 77.0), 3.6, 0.16, 0.45)
        elif bar_idx in (32, 36):
            spectral_trigger = (0.25, (60.0, 63.0, 67.0, 74.0), 4.0, 0.20, 0.62)
        elif total_bars >= 56 and bar_idx == 47:
            spectral_trigger = (1.75, (60.0, 67.0, 75.0, 79.0), 2.1, 0.15, 0.55)
        elif is_false_drop_bar:
            spectral_trigger = (1.75, (60.0, 68.0, 73.0, 79.0), 1.85, 0.14, 0.65)

        if spectral_trigger is not None:
            sp_beat, sp_notes, sp_dur, sp_gain, sp_dub = spectral_trigger
            sp_l, sp_r = render_avantgarde_spectral_bow(
                notes_midi=sp_notes,
                duration_sec=sp_dur,
                gain=sp_gain,
                seed=bar_idx + 17,
                sample_rate=SAMPLE_RATE,
            )
            sp_s = int(round((bar_t0 + sp_beat * beat_sec) * SAMPLE_RATE))
            add_stereo(avant_l, avant_r, sp_l, sp_r, sp_s, gain=1.0)
            add_stereo(dub_send_l, dub_send_r, sp_l, sp_r, sp_s, gain=sp_dub)
            sp_t0 = bar_tick0 + int(round(sp_beat * PPQ))
            sp_t1 = sp_t0 + int(round((sp_dur / beat_sec) * PPQ))
            for sp_n in sp_notes:
                midi_tracks["AvantGarde_Melodic_Techno"].append((sp_t0, sp_t1, int(round(sp_n)), 54))
            spectral_bow_events += 1

        # 1. Kick & Percusión Sincopada + Ghost Wood-Rim + Hats Respirados
        for beat in range(4):
            beat_t_nom = bar_t0 + beat * beat_sec
            beat_tick_nom = bar_tick0 + beat * PPQ
            muted_here = _is_rhythm_muted(bar_idx, float(beat))

            # Kick principal (anclado < 0.4 ms, pesos humanos por pulso + 1/f)
            if not muted_here and not in_intro_silent and not in_breakdown_vac:
                k_step_idx = (bar_idx * 16 + beat * 4) % len(pink_step)
                k_jit = 0.00035 * float(pink_step[k_step_idx])
                timing_offsets_ms.append(k_jit * 1000.0)
                k_t = max(0.0, beat_t_nom + rubato_sec + k_jit)
                k_s = int(round(k_t * SAMPLE_RATE))
                base_k_gain = 0.38 if (in_intro_soft or in_breakdown_rise) else 0.65
                k_vel_w = beat_vel_weights[beat] * (1.0 + 0.025 * float(pink_bar[bar_idx]))
                k_gain = base_k_gain * k_vel_w
                k_wave = kicks_rr[(bar_idx * 4 + beat) % len(kicks_rr)]
                add_stereo(kick_l, kick_r, k_wave, k_wave, k_s, gain=k_gain)
                kick_onsets.append(k_s)
                k_tick = beat_tick_nom + int(round(((rubato_sec + k_jit) / beat_sec) * PPQ))
                midi_tracks["Drums_Kick"].append((k_tick, k_tick + 120, 36, int(np.clip(115 * k_gain / 0.65, 42, 127))))

                # Pickup Kick sincopado en cierres de hipercompás (beat 3.75)
                if beat == 3 and (bar_idx % 8 == 3) and bar_idx >= 16 and bar_idx != (false_drop_bar - 1):
                    sw_kick = _compute_swing_offset_sec(3, sixteenth_sec)
                    pk_pos = 3.75
                    if not _is_rhythm_muted(bar_idx, pk_pos):
                        pk_t = bar_t0 + pk_pos * beat_sec + rubato_sec + sw_kick
                        pk_wave = ghost_kicks_rr[bar_idx % len(ghost_kicks_rr)]
                        add_stereo(kick_l, kick_r, pk_wave, pk_wave, int(round(pk_t * SAMPLE_RATE)), gain=0.28)
                        pk_tick = bar_tick0 + int(round((pk_pos + (rubato_sec + sw_kick) / beat_sec) * PPQ))
                        midi_tracks["Drums_Kick"].append((pk_tick, pk_tick + 80, 36, 58))
                        syncopated_turnaround_events += 1

            # Clap con bolsillo push/pull + pre-flam fantasma en cierres
            if not muted_here and bar_idx >= 16 and not in_breakdown_vac and beat in (1, 3):
                c_shift = rubato_sec + (0.0028 if beat == 1 else -0.0022) * (0.6 + 0.4 * float(pink_bar[bar_idx]))
                timing_offsets_ms.append(c_shift * 1000.0)
                c_t = max(0.0, beat_t_nom + c_shift)
                c_l, c_r = claps_rr[(bar_idx + beat) % len(claps_rr)]
                c_gain = (0.65 if in_breakdown_rise else 0.92) * (1.0 + 0.05 * float(pink_bar[bar_idx]))
                add_stereo(perc_l, perc_r, c_l, c_r, int(round(c_t * SAMPLE_RATE)), gain=c_gain)
                c_tick = beat_tick_nom + int(round((c_shift / beat_sec) * PPQ))
                midi_tracks["Drums_MPC_Perc"].append((c_tick, c_tick + 140, 39, int(np.clip(96 * c_gain, 40, 122))))

                if ((bar_idx % 4 == 3 and beat == 3) or (bar_idx % 8 == 5 and beat == 1)) and c_t > 0.02:
                    fl_l, fl_r = claps_rr[(bar_idx + beat + 3) % len(claps_rr)]
                    fl_t = c_t - 0.013
                    add_stereo(perc_l, perc_r, fl_l, fl_r, int(round(fl_t * SAMPLE_RATE)), gain=0.32 * c_gain)
                    midi_tracks["Drums_MPC_Perc"].append((max(0, c_tick - 12), c_tick + 30, 39, 44))

            # Open Hat (decay respirado + empuje 1/f) & Closed Hats (MPC 56.5% + espacios silenciosos)
            if bar_idx >= 8 and not in_breakdown_vac:
                oh_pos = beat + 0.5
                if not _is_rhythm_muted(bar_idx, oh_pos):
                    oh_step_i = (bar_idx * 16 + beat * 4 + 2) % len(pink_step)
                    oh_shift = rubato_sec + 0.0032 * float(pink_step[oh_step_i])
                    timing_offsets_ms.append(oh_shift * 1000.0)
                    oh_t = max(0.0, beat_t_nom + 0.5 * beat_sec + oh_shift)
                    oh_idx = int(np.clip(hat_breath_idx + (beat % 2), 0, 7))
                    oh_l, oh_r = hats_o_rr[oh_idx]
                    oh_gain = (0.45 if (in_intro_soft or in_breakdown_rise) else 0.85) * (0.94 + 0.10 * float(pink_step[oh_step_i]))
                    add_stereo(perc_l, perc_r, oh_l, oh_r, int(round(oh_t * SAMPLE_RATE)), gain=oh_gain)
                    oh_tick = beat_tick_nom + PPQ // 2 + int(round((oh_shift / beat_sec) * PPQ))
                    midi_tracks["Drums_MPC_Perc"].append((oh_tick, oh_tick + 100, 46, int(np.clip(92 * oh_gain, 36, 118))))

                for step16 in range(1, 4):
                    s_pos = beat + step16 * 0.25
                    if _is_rhythm_muted(bar_idx, s_pos):
                        continue
                    # Respeto por el silencio: omitir ciertas semicorcheas débiles para que respire el groove
                    if step16 == 1 and (bar_idx % 2 == 0) and beat in (0, 2):
                        continue
                    if step16 == 3 and (bar_idx % 4 == 3) and beat == 2:
                        continue
                    s_idx = (bar_idx * 16 + beat * 4 + step16) % len(pink_step)
                    swing_dt = _compute_swing_offset_sec(step16, sixteenth_sec)
                    h_shift = rubato_sec + 0.0018 * float(pink_step[s_idx])
                    timing_offsets_ms.append(h_shift * 1000.0)
                    h_t = max(0.0, beat_t_nom + step16 * sixteenth_sec + swing_dt + h_shift)
                    ch_l, ch_r = hats_c_rr[int(np.clip(hat_breath_idx + (step16 % 2), 0, 7))]
                    base_ch = 0.48 if step16 == 2 else (0.37 if step16 == 3 else 0.24)
                    ch_gain = base_ch * (0.88 + 0.16 * float(pink_step[s_idx]))
                    add_stereo(perc_l, perc_r, ch_l, ch_r, int(round(h_t * SAMPLE_RATE)), gain=ch_gain)
                    sw_ticks = int(round(((swing_dt + h_shift) / beat_sec) * PPQ))
                    t16 = beat_tick_nom + step16 * (PPQ // 4) + sw_ticks
                    vel_h = int(np.clip((76 if step16 == 2 else (60 if step16 == 3 else 44)) + 8 * float(pink_step[s_idx]), 28, 108))
                    midi_tracks["Drums_MPC_Perc"].append((t16, t16 + 60, 42, vel_h))

        # 1B. Micro-Percusión Wood-Rim Orgánica Off-Grid Sincopada (RAE Ley 8)
        if bar_idx >= 12 and not in_breakdown_vac:
            wood_steps = [3, 6, 11, 14] if (bar_idx % 2 == 0) else [2, 7, 11, 13]
            for ws in wood_steps:
                w_pos = ws * 0.25
                if _is_rhythm_muted(bar_idx, w_pos):
                    continue
                ws_idx = (bar_idx * 16 + ws) % len(pink_step)
                offgrid_sec = rubato_sec + 0.0095 * float(pink_step[ws_idx])
                timing_offsets_ms.append(offgrid_sec * 1000.0)
                w_t = max(0.0, bar_t0 + ws * sixteenth_sec + offgrid_sec)
                wl, wr = wood_rr[(bar_idx + ws) % len(wood_rr)]
                w_gain = (0.48 if (in_intro_soft or in_breakdown_rise) else 0.68) * (0.82 + 0.24 * float(pink_step[ws_idx]))
                add_stereo(perc_l, perc_r, wl, wr, int(round(w_t * SAMPLE_RATE)), gain=w_gain)
                w_tick = bar_tick0 + ws * (PPQ // 4) + int(round((offgrid_sec / beat_sec) * PPQ))
                midi_tracks["Drums_MPC_Perc"].append((w_tick, w_tick + 70, 76 if ws in (3, 11) else 37, int(np.clip(74 * w_gain, 32, 98))))
                ghost_perc_events += 1

        # 2. Subgrave Rolling C Frigio Sincopado (+5.5..+9.0 ms laid-back + saltos octava/anticipación)
        if bar_idx >= 16 and not in_breakdown_vac:
            pocket_sec = 0.0055 + 0.0035 * (0.5 + 0.5 * float(pink_bar[bar_idx]))
            bass_pocket_values_ms.append(pocket_sec * 1000.0)
            if cycle_pos == 0:
                sub_score = [
                    (0.75, bass_midi, 0.30, 0.94, 0.0),
                    (1.50, bass_midi, 0.23, 0.84, 0.0),
                    (2.75, bass_midi, 0.31, 0.95, 0.0),
                    (3.50, bass_midi, 0.22, 0.80, 0.0),
                ]
            elif cycle_pos == 1:
                sub_score = [
                    (0.75, bass_midi, 0.29, 0.95, 0.0),
                    (1.50, bass_midi, 0.22, 0.84, 0.0),
                    (1.75, bass_midi + 12, 0.14, 0.64, 5.0),
                    (2.75, bass_midi, 0.30, 0.96, 0.0),
                    (3.50, bass_midi, 0.22, 0.82, 0.0),
                ]
            elif cycle_pos == 2:
                sub_score = [
                    (0.75, bass_midi, 0.30, 0.94, 0.0),
                    (1.50, bass_midi, 0.22, 0.82, 0.0),
                    (2.25, bass_midi + 12, 0.14, 0.60, -4.0),
                    (2.75, bass_midi, 0.30, 0.96, 0.0),
                    (3.50, bass_midi, 0.22, 0.82, 0.0),
                ]
            else:
                sub_score = [
                    (0.75, bass_midi, 0.28, 0.94, 0.0),
                    (1.50, bass_midi, 0.21, 0.82, 0.0),
                    (2.50, bass_midi + 7, 0.17, 0.72, 4.0),
                    (3.25, bass_midi, 0.19, 0.86, 0.0),
                    (3.75, next_bass_midi, 0.115, 0.68, -6.0),
                ]

            for b_pos, pitch_b, note_dur, v_mul, slide_c in sub_score:
                if _is_rhythm_muted(bar_idx, b_pos):
                    continue
                step16_sub = int(round(b_pos * 4.0))
                sw_bass = _compute_swing_offset_sec(step16_sub, sixteenth_sec) if (step16_sub % 2 == 1) else 0.0
                note_t = bar_t0 + b_pos * beat_sec + pocket_sec + rubato_sec + sw_bass
                timing_offsets_ms.append((pocket_sec + rubato_sec + sw_bass) * 1000.0)
                vel = (0.72 if in_breakdown_rise else 0.94) * v_mul
                sub_wave = render_sub_bass_note(
                    pitch_b,
                    note_dur,
                    velocity=vel,
                    sample_rate=SAMPLE_RATE,
                    accent_slide_cents=slide_c,
                )
                add_stereo(bass_l, bass_r, sub_wave, sub_wave, int(round(note_t * SAMPLE_RATE)), gain=1.0)
                t_start = bar_tick0 + int(round((b_pos + (pocket_sec + rubato_sec + sw_bass) / beat_sec) * PPQ))
                t_dur_ticks = max(70, int(round((note_dur / beat_sec) * PPQ)))
                midi_tracks["SubBass_C_Phrygian"].append((t_start, t_start + t_dur_ticks, pitch_b, int(np.clip(112 * vel, 38, 124))))
                if b_pos in (1.75, 2.25, 3.75):
                    syncopated_turnaround_events += 1

        # 3. Acordes Prophet/Rhodes (3+3+2+2 con colores Cycle B, anticipación sincopada, ghost stabs y silencio en Breakdown)
        if cycle_pos == 0:
            block_t0 = bar_t0
            block_tick0 = bar_tick0
            block_hits: List[Tuple[float, int, float, bool]] = []
            for m_idx, eighth_pos in enumerate(POLYRHYTHM_EIGHTHS):
                if in_breakdown_vac and eighth_pos not in (0, 16):
                    continue  # Breakdown Cavern: silencio amplio (~2.9s) entre pulsos armónicos
                eff_eighth = float(eighth_pos)
                if is_b_cycle and not in_breakdown_vac and m_idx in (4, 8):
                    eff_eighth -= 0.5  # Anticipación sincopada en semicorchea (-1/16) sobre hits clave de Ciclo B
                next_pos = POLYRHYTHM_EIGHTHS[m_idx + 1] if m_idx + 1 < len(POLYRHYTHM_EIGHTHS) else 32
                hit_dur = max(0.32, (next_pos - eff_eighth) * eighth_sec * (1.28 if in_breakdown_vac else 0.92))
                block_hits.append((eff_eighth, min(3, eighth_pos // 8), hit_dur, False))
                # Ghost stab armónico sincopado entre silencios de Ciclo B fuera del breakdown
                if is_b_cycle and not in_breakdown_vac and m_idx in (5, 10):
                    block_hits.append((eff_eighth + 1.5, min(3, eighth_pos // 8), 0.36, True))

            for hit_i, (eff_eighth, chord_idx, hit_dur, is_ghost) in enumerate(block_hits):
                bar_of_hit = bar_idx + int(eff_eighth // 8.0)
                if bar_of_hit >= total_bars:
                    continue
                beat_in_bar = (eff_eighth % 8.0) * 0.5
                if _is_rhythm_muted(bar_of_hit, beat_in_bar):
                    continue

                if is_b_cycle:
                    c_notes = PHRYGIAN_VARIATIONS_B[chord_idx]
                else:
                    _, c_notes, _ = PHRYGIAN_CYCLE[chord_idx]

                step16_chord = int(round((eff_eighth * 2.0))) % 16
                sw_c = _compute_swing_offset_sec(step16_chord, sixteenth_sec) if abs(eff_eighth * 2.0 - round(eff_eighth * 2.0)) < 1e-3 and (step16_chord % 2 == 1) else 0.0
                c_step_pink = float(pink_step[(bar_of_hit * 16 + step16_chord) % len(pink_step)])
                c_rubato = compute_phrase_rubato_sec(bar_of_hit, false_drop_bar)
                c_shift = c_rubato + sw_c + 0.0045 * c_step_pink
                timing_offsets_ms.append(c_shift * 1000.0)

                vel = (0.44 if is_ghost else (0.76 + 0.08 * math.sin(hit_i * 1.1))) * (0.94 + 0.08 * c_step_pink)
                strum_ms = 13.5 if is_ghost else float(np.clip(7.8 + (1.0 - vel) * 13.5, 7.2, 14.5))
                strum_ms_values.append(strum_ms)
                detune_cents = 2.2 * c_step_pink

                cutoff_hz = 1120.0 + 740.0 * (bar_of_hit / float(max(1, total_bars))) + 140.0 * c_step_pink
                if in_breakdown_vac or in_breakdown_rise:
                    cutoff_hz *= 0.80
                if is_ghost:
                    cutoff_hz *= 0.68

                c_l, c_r = render_prophet_chord_event(
                    c_notes,
                    duration_sec=hit_dur,
                    cutoff_peak_hz=cutoff_hz,
                    velocity=vel,
                    sample_rate=SAMPLE_RATE,
                    strum_ms=strum_ms,
                    detune_bias_cents=detune_cents,
                    seed=bar_of_hit * 31 + hit_i,
                )
                hit_t = block_t0 + eff_eighth * eighth_sec + c_shift
                hit_s = int(round(hit_t * SAMPLE_RATE))
                add_stereo(chords_l, chords_r, c_l, c_r, hit_s, gain=0.95)

                if is_ghost or (hit_i % 3 == 2) or (bar_of_hit in (false_drop_bar, 31, 32, 47)):
                    add_stereo(dub_send_l, dub_send_r, c_l, c_r, hit_s, gain=(0.82 if is_ghost else 0.72))

                strum_ticks = max(1, int(round((strum_ms / 1000.0 / beat_sec) * PPQ)))
                base_c0 = block_tick0 + int(round((eff_eighth * 0.5 + c_shift / beat_sec) * PPQ))
                t_len_c = max(100, int(round((hit_dur / beat_sec) * PPQ)))
                for v_i, pitch in enumerate(c_notes):
                    t_v0 = max(0, base_c0 + v_i * strum_ticks)
                    v_em = 1.08 if v_i in (0, len(c_notes) - 1) else 0.90
                    midi_tracks["Prophet_Rhodes_Motif"].append((t_v0, t_v0 + t_len_c, pitch, int(np.clip(92 * vel * v_em, 28, 122))))

        # 4. Stem Experimental Avant-Garde / Melodic Techno (Ostinato Polimétrico 5/16)
        arp_mask: List[int] = []
        if 24 <= bar_idx < 32:
            arp_mask = [0, 6, 11, 14]
        elif 40 <= bar_idx < 48:
            arp_mask = [0, 6, 11, 14]
        elif (48 <= bar_idx < false_drop_bar) or (false_drop_bar < bar_idx < total_bars - 1):
            arp_mask = [0, 3, 6, 9, 11, 14]

        if arp_mask:
            active_cell = arp_cell_b if bar_idx >= 48 else arp_cell_a
            progress = max(0.0, (bar_idx - 24) / float(max(1, total_bars - 24)))
            for s16 in arp_mask:
                a_pos = s16 * 0.25
                if _is_rhythm_muted(bar_idx, a_pos):
                    continue
                sw_a = _compute_swing_offset_sec(s16, sixteenth_sec)
                a_idx_pink = (bar_idx * 16 + s16) % len(pink_step)
                a_shift = rubato_sec + sw_a + 0.0040 * float(pink_step[a_idx_pink])
                timing_offsets_ms.append(a_shift * 1000.0)
                a_t = max(0.0, bar_t0 + s16 * sixteenth_sec + a_shift)

                note_pitch = active_cell[arp_step_idx % len(active_cell)]
                if (arp_step_idx % 11 == 10) and bar_idx >= 48:
                    note_pitch += 12.0  # Salto de octava avant-garde en clímax de frase
                arp_step_idx += 1

                a_dur = 0.36 if s16 == 14 else 0.19
                a_vel = (0.56 + 0.22 * progress) * (0.88 + 0.16 * float(pink_step[a_idx_pink]))
                if in_breakdown_rise:
                    a_vel *= 0.78
                a_cutoff = 1180.0 + 1350.0 * progress + 220.0 * float(pink_step[a_idx_pink])
                a_pan = 0.38 * math.sin(arp_step_idx * 0.85)
                al, ar = render_melodic_techno_arp_note(
                    midi_note=note_pitch,
                    duration_sec=a_dur,
                    cutoff_hz=a_cutoff,
                    velocity=a_vel,
                    pan=a_pan,
                    vibrato_delay_sec=0.12 if s16 == 14 else 0.16,
                    sample_rate=SAMPLE_RATE,
                )
                a_s = int(round(a_t * SAMPLE_RATE))
                add_stereo(avant_l, avant_r, al, ar, a_s, gain=0.82)
                if s16 in (6, 14):
                    add_stereo(dub_send_l, dub_send_r, al, ar, a_s, gain=0.48)
                a_tick = bar_tick0 + s16 * (PPQ // 4) + int(round((a_shift / beat_sec) * PPQ))
                midi_tracks["AvantGarde_Melodic_Techno"].append((max(0, a_tick), max(0, a_tick) + int(round((a_dur / beat_sec) * PPQ)), int(round(note_pitch)), int(np.clip(88 * a_vel, 32, 118))))

    # Ventanas raised-cosine limpias para los silencios estructurales y el Falso Drop (Compás 60 pulsos 3-4)
    silence_windows_sec: List[Tuple[str, float, float]] = []
    if total_bars >= 32:
        silence_windows_sec.append(("bar16_caesura_beat4", 15.0 * bar_sec + 3.0 * beat_sec, 16.0 * bar_sec))
    if total_bars >= 48:
        silence_windows_sec.append(("bar32_pre_abyss_beats3_4", 31.0 * bar_sec + 2.0 * beat_sec, 32.0 * bar_sec))
    if total_bars >= 56:
        silence_windows_sec.append(("bar48_pre_climax_vacuum", 47.0 * bar_sec + 2.0 * beat_sec, 48.0 * bar_sec))
    silence_windows_sec.append(("bar60_c5_false_drop", false_drop_bar * bar_sec + 2.0 * beat_sec, (false_drop_bar + 1) * bar_sec))

    for _, ws_sec, we_sec in silence_windows_sec:
        ws_idx = int(round(ws_sec * SAMPLE_RATE))
        we_idx = int(round(we_sec * SAMPLE_RATE))
        for buf in (kick_l, kick_r, perc_l, perc_r, bass_l, bass_r):
            _apply_smooth_gate_window(buf, ws_idx, we_idx, fade_ms=14.0, sample_rate=SAMPLE_RATE)

    # Living Exit (compás final): disolución exponencial RC hasta silencio limpio
    exit_start = int(round((total_bars - 1) * bar_sec * SAMPLE_RATE))
    if exit_start < n_samples:
        t_ex = make_time_axis(n_samples - exit_start, SAMPLE_RATE)
        rc_decay = np.exp(-t_ex / 0.85)
        n_end_fade = min(len(rc_decay), int(round(0.040 * SAMPLE_RATE)))
        rc_decay[-n_end_fade:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(n_end_fade) / max(1, n_end_fade - 1)))
        rc_decay[-1] = 0.0
        rc_decay.flags.writeable = False
        for buf in (kick_l, kick_r, perc_l, perc_r, bass_l, bass_r, chords_l, chords_r, avant_l, avant_r):
            buf[exit_start:] *= rc_decay

    # Bark Carving en acordes y sinte avant-garde + Lazo Dub No-Conmutativo Pre-Filtro (corchea con puntillo)
    chords_l, chords_r = carve_polyphonic_mud(chords_l, chords_r, sample_rate=SAMPLE_RATE, hpf_hz=185.0, mud_hz=375.0)
    avant_l, avant_r = carve_polyphonic_mud(avant_l, avant_r, sample_rate=SAMPLE_RATE, hpf_hz=210.0, mud_hz=375.0)
    dub_send_l.flags.writeable = False
    dub_send_r.flags.writeable = False
    dub_delay_sec = 0.75 * beat_sec
    dub_wet_l, dub_wet_r = apply_noncommutative_dub_echo(
        dub_send_l,
        dub_send_r,
        sample_rate=SAMPLE_RATE,
        delay_sec=dub_delay_sec,
        feedback=0.45,
        lpf_hz=2800.0,
        hpf_hz=240.0,
        wet=0.74,
        taps=6,
    )
    # Quitar señal seca del stem de envío Dub para conservar solo la cola espacial orgánica
    dub_l = (dub_wet_l - dub_send_l) * 1.35
    dub_r = (dub_wet_r - dub_send_r) * 1.35

    # Sidechain multibanda acoplado al decaimiento del Kick (Zero-Crackle)
    sc_sub, sc_mid = build_coupled_multiband_sidechain(
        n_samples,
        kick_onsets,
        sample_rate=SAMPLE_RATE,
        tau_body=0.205,
        sub_depth=0.90,
        high_depth=0.22,
        attack_ms=6.0,
        lookahead_ms=3.0,
    )
    bass_lo_l, bass_hi_l = lr4_zero_phase_crossover(bass_l, 140.0, SAMPLE_RATE)
    bass_lo_r, bass_hi_r = lr4_zero_phase_crossover(bass_r, 140.0, SAMPLE_RATE)
    bass_l = (bass_lo_l * sc_sub) + (bass_hi_l * sc_mid)
    bass_r = (bass_lo_r * sc_sub) + (bass_hi_r * sc_mid)

    chords_l *= sc_mid
    chords_r *= sc_mid
    avant_l *= sc_mid
    avant_r *= sc_mid

    # Sala compartida coherente (18 ms pre-delay, 84% núcleo mono) + consolidación mono < 135 Hz por stem
    perc_l, perc_r = apply_coherent_shared_room(perc_l, perc_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.10)
    perc_l, perc_r = enforce_low_end_mono(perc_l, perc_r, cutoff_hz=135.0, sample_rate=SAMPLE_RATE)
    chords_l, chords_r = apply_coherent_shared_room(chords_l, chords_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.14)
    chords_l, chords_r = enforce_low_end_mono(chords_l, chords_r, cutoff_hz=135.0, sample_rate=SAMPLE_RATE)
    avant_l, avant_r = apply_coherent_shared_room(avant_l, avant_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.18)
    avant_l, avant_r = enforce_low_end_mono(avant_l, avant_r, cutoff_hz=135.0, sample_rate=SAMPLE_RATE)
    dub_l, dub_r = apply_coherent_shared_room(dub_l, dub_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.18)
    dub_l, dub_r = enforce_low_end_mono(dub_l, dub_r, cutoff_hz=135.0, sample_rate=SAMPLE_RATE)

    # Lecho de cinta analógica activa (-57 dBFS, cero silencio digital 0.0)
    tape_l, tape_r = generate_warm_analog_tape_bed(n_samples, sample_rate=SAMPLE_RATE, level_dbfs=-57.0)
    tape_l = apply_zero_crackle_envelope(tape_l, sample_rate=SAMPLE_RATE, attack_ms=20.0, release_ms=40.0)
    tape_r = apply_zero_crackle_envelope(tape_r, sample_rate=SAMPLE_RATE, attack_ms=20.0, release_ms=40.0)

    # Ingesta opcional de audio real legítimo (Demucs o stem vocal)
    organic_info: Dict[str, Any] = {"mode": "AUTÓMATA_SINTÉTICO_ESTRUCTURAL", "source_audio": None}
    org_l = np.zeros(n_samples, dtype=np.float64)
    org_r = np.zeros(n_samples, dtype=np.float64)

    if vocal_stem or source_audio:
        if vocal_stem:
            v_path = Path(vocal_stem).expanduser().resolve()
            if not v_path.exists():
                raise FileNotFoundError(f"Stem vocal no encontrado: {v_path}")
            stems_extracted = {"vocals": v_path}
            organic_info["source_audio"] = str(v_path)
        else:
            src_path = Path(str(source_audio)).expanduser().resolve()
            if not src_path.exists():
                raise FileNotFoundError(f"Audio fuente no encontrado: {src_path}")
            stems_extracted = extract_organic_stems_with_demucs(src_path, project_dir, keep_other=keep_other)
            organic_info["source_audio"] = str(src_path)

        est_bpms: Dict[str, float] = {}
        for label, s_path in stems_extracted.items():
            sl, sr_st, est_bpm = align_organic_stem_to_house(
                s_path,
                target_samples=n_samples,
                target_bpm=BPM,
                sample_rate=SAMPLE_RATE,
                source_bpm_override=source_bpm_override,
            )
            est_bpms[label] = round(est_bpm, 2)
            weight = 0.88 if label == "vocals" else 0.42
            org_l += sl * weight
            org_r += sr_st * weight

        org_l *= sc_mid
        org_r *= sc_mid
        # Durante el Falso Drop del Compás 60 la voz real flota con eco dub filtrado
        org_dub_l, org_dub_r = apply_noncommutative_dub_echo(
            org_l,
            org_r,
            sample_rate=SAMPLE_RATE,
            delay_sec=dub_delay_sec,
            feedback=0.38,
            lpf_hz=2800.0,
            hpf_hz=260.0,
            wet=0.28,
            taps=4,
        )
        org_l, org_r = apply_coherent_shared_room(org_dub_l, org_dub_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.14)
        org_l, org_r = enforce_low_end_mono(org_l, org_r, cutoff_hz=120.0, sample_rate=SAMPLE_RATE)
        organic_info["mode"] = "TRANSDUCCION_ORGANICA_DEMUCS"
        organic_info["estimated_source_bpm"] = est_bpms

    # Verificación Zero-Crackle en subgrave antes de mezclar
    bass_mono = 0.5 * (bass_l + bass_r)
    zero_crackle_audit = check_zero_crackle_derivatives(bass_mono, max_d1=0.015, max_d2=0.005)
    if not zero_crackle_audit["zero_crackle_passed"]:
        raise RuntimeError(f"Fallo Zero-Crackle Derivative Gate en subgrave: {zero_crackle_audit}")

    # Exportar stems individuales (48 kHz / 24-bit PCM)
    stem_specs: List[Tuple[str, np.ndarray, np.ndarray]] = [
        ("01_Kick_C5_49Hz.wav", kick_l, kick_r),
        ("02_SubBass_C_Phrygian.wav", bass_l, bass_r),
        ("03_MPC_Percussion.wav", perc_l, perc_r),
        ("04_Prophet_Rhodes_Motif.wav", chords_l, chords_r),
        ("05_AvantGarde_Melodic_Techno.wav", avant_l, avant_r),
        ("06_BasicChannel_Dub_Echo.wav", dub_l, dub_r),
        ("07_Analog_Tape_Bed.wav", tape_l, tape_r),
    ]
    if organic_info["mode"] == "TRANSDUCCION_ORGANICA_DEMUCS":
        stem_specs.append(("08_Radiohead_Organic_Stems.wav", org_l, org_r))

    stem_paths: List[str] = []
    for filename, s_l, s_r in stem_specs:
        p = write_pcm_wav(stems_dir / filename, s_l, s_r, sample_rate=SAMPLE_RATE, bit_depth=24, dither=False)
        stem_paths.append(str(p))

    # Mezcla suma + consolidación mono < 120 Hz + pre-máster
    mix_l = kick_l + bass_l + perc_l + chords_l + avant_l + dub_l + tape_l + org_l
    mix_r = kick_r + bass_r + perc_r + chords_r + avant_r + dub_r + tape_r + org_r
    mix_l, mix_r = enforce_low_end_mono(mix_l, mix_r, cutoff_hz=120.0, sample_rate=SAMPLE_RATE)

    premaster_path = project_dir / "Everything_In_Its_Right_Place_C5_House_124_PREMASTER.wav"
    master_path = project_dir / "Everything_In_Its_Right_Place_C5_House_124_MASTER_48k_24b.wav"
    write_pcm_wav(premaster_path, mix_l, mix_r, sample_rate=SAMPLE_RATE, bit_depth=24, dither=False)

    master_res = master_audio_reverse_engineered(
        input_wav=str(premaster_path),
        output_wav=str(master_path),
        profile_name=profile_name,
        bit_depth=24,
    )

    midi_path = project_dir / "Everything_In_Its_Right_Place_C5_House_124.mid"
    write_multichannel_midi(midi_path, midi_tracks, bpm=BPM)

    flp_path = project_dir / "Everything_In_Its_Right_Place_C5_House_124.flp"
    flp_res = compile_multitrack_stems_flp(
        stems_dir=str(stems_dir),
        project_title="Everything In Its Right Place (C5 Melodic Techno/House 124 BPM)",
        bpm=BPM,
        output_flp=str(flp_path),
        total_bars=total_bars,
    )

    # Gate Acústico Rubin externo obligatorio (INV_C5_ACOUSTIC_GATE)
    rubin_external_out = ""
    if RUBIN_LINTER_PATH.exists():
        proc = subprocess.run(
            [sys.executable, str(RUBIN_LINTER_PATH), str(master_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        rubin_external_out = proc.stdout.strip()
        if proc.returncode != 0:
            raise RuntimeError(f"Rubin Linter externo abortó ({proc.returncode}): {proc.stderr or proc.stdout}")

    # Auditoría interna final sobre el master escrito
    import soundfile as sf

    m_data, m_sr = sf.read(str(master_path), always_2d=True)
    rubin_internal = compute_rubin_metrics(m_data[:, 0], m_data[:, 1], sample_rate=int(m_sr))
    if not rubin_internal["is_pure_bone"]:
        raise RuntimeError(f"Master rechazado por INV_C5_ACOUSTIC_GATE: {rubin_internal}")

    humanization_audit = {
        "voss_clarke_1f_curves": {"bar_seed": 124, "step_seed": 224},
        "microtiming_offsets_ms": {
            "count": len(timing_offsets_ms),
            "min_ms": round(min(timing_offsets_ms), 2) if timing_offsets_ms else 0.0,
            "max_ms": round(max(timing_offsets_ms), 2) if timing_offsets_ms else 0.0,
            "std_ms": round(float(np.std(timing_offsets_ms)), 2) if timing_offsets_ms else 0.0,
        },
        "bass_laid_back_pocket_ms_range": [
            round(min(bass_pocket_values_ms), 2) if bass_pocket_values_ms else 0.0,
            round(max(bass_pocket_values_ms), 2) if bass_pocket_values_ms else 0.0,
        ],
        "prophet_strum_ms_range": [
            round(min(strum_ms_values), 2) if strum_ms_values else 0.0,
            round(max(strum_ms_values), 2) if strum_ms_values else 0.0,
        ],
        "hihat_decay_breathing_ms": {"closed": [11.0, 32.0], "open": [48.0, 88.0]},
        "syncopated_turnaround_events": syncopated_turnaround_events,
        "offgrid_ghost_wood_perc_events": ghost_perc_events,
        "avantgarde_spectral_bow_events": spectral_bow_events,
        "sculpted_living_silences": [
            {"name": name, "start_sec": round(s, 3), "end_sec": round(e, 3)}
            for name, s, e in silence_windows_sec
        ],
    }

    receipt = {
        "status": "SUCCESS",
        "track": "Everything In Its Right Place (C Phrygian Avant-Garde Melodic Techno / House 124 BPM)",
        "bpm": BPM,
        "sample_rate_hz": SAMPLE_RATE,
        "bit_depth": 24,
        "total_bars": total_bars,
        "false_drop_bar": false_drop_bar + 1,
        "soul_classification": organic_info,
        "humanization_and_groove_audit": humanization_audit,
        "zero_crackle_sub_audit": zero_crackle_audit,
        "master_wav": str(master_path),
        "premaster_wav": str(premaster_path),
        "stems_dir": str(stems_dir),
        "stems": stem_paths,
        "midi_file": str(midi_path),
        "flp_file": flp_res["flp_file"],
        "flp_manifest": flp_res["manifest_file"],
        "mastering_metrics": {
            "lufs_after": master_res["lufs_after"],
            "lra_lu_after": master_res["lra_lu_after"],
            "true_peak_dbtp_after": master_res["true_peak_dbtp_after"],
            "rubin_audit_after": rubin_internal,
        },
        "rubin_external_report": rubin_external_out,
    }
    receipt_path = project_dir / "production_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Everything In Its Right Place — C5-REAL House 124 BPM Pipeline")
    parser.add_argument("--source-audio", type=str, default=None, help="Ruta a archivo WAV/FLAC legítimo para separar con Demucs")
    parser.add_argument("--vocal-stem", type=str, default=None, help="Ruta directa a stem vocal WAV ya separado")
    parser.add_argument("--keep-other", action="store_true", help="Conservar también el stem 'other' de Demucs junto con 'vocals'")
    parser.add_argument("--source-bpm", type=float, default=None, help="BPM manual del audio fuente (opcional)")
    parser.add_argument("--profile", type=str, default="deep_house", help="Perfil de masterización (deep_house, club_c5, streaming_sota)")
    parser.add_argument("--bars", type=int, default=TOTAL_BARS, help="Número de compases (por defecto 64)")
    parser.add_argument("--output-dir", type=str, default=None, help="Directorio de salida raíz (opcional)")
    args = parser.parse_args()

    res = build_everything_house_124(
        source_audio=args.source_audio,
        vocal_stem=args.vocal_stem,
        keep_other=args.keep_other,
        source_bpm_override=args.source_bpm,
        profile_name=args.profile,
        total_bars=args.bars,
        output_dir=args.output_dir,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
