#!/usr/bin/env python3
"""
MIRA NIÑITA (LOS JAIVAS) — C5-REAL Deep House 122 BPM Remix Engine (FL Studio 2025)
====================================================================================
Reinterpreta la obra icónica de Los Jaivas (1972, compás 6/8 sobre progresión F -> C -> G)
como un remix Deep House híbrido (Satin Jackets x Maceo Plex x AIR Moon Safari) a 122.0 BPM
en 48 kHz / 24-bit PCM:

  1. Armonía Deep House extendida: Fmaj9 -> Cmaj9 -> G6add9 -> Fmaj9/G sobre patrón
     polirrítmico 6/8-sobre-4/4 (hemiola 3+3+2 en corcheas) con micro-rasgueo Rhodes/Celesta.
  2. Motivos melódicos canónicos:
       - Quena / Flauta traversa andina (Intro: A-B-C-D-C-B-A / B-C-D-C-B-A-G / G-A-B-C-B-A-G)
       - Estribillo "Mira niñita..." (C5 x5 -> B4 -> A4 -> G4)
       - Charango en doble cuerda modal con repique sincopado 6/8 sobre 4/4.
  3. Base física Deep House:
       - Kick 909/Maceo anclado a fase 0 rad en G1 (49.0 Hz) con 5 variaciones round-robin.
       - Subgrave rolling F1/C2/G1 (+6 ms behind-the-beat, muesca Bark en 49 Hz, Zero-Crackle).
       - Swing Roger Linn MPC-60 (56.5%), hats limpios (>6.2 kHz), palmas orgánicas.
  4. Topología espacial y estructura de 64 compases:
       - Carving Bark (185 Hz HPF, 375 Hz mud cut, <14.2 kHz tape roll-off).
       - Lazo Dub No-Conmutativo Pre-Filtro (LPF 2800 Hz dentro del feedback).
       - Sala compartida coherente (18 ms pre-delay, 84% núcleo mono, LPC >= 0.96).
       - Falso Drop determinista en Compás 60 (pulsos 3-4 vacíos con lecho analógico -57 dBFS
         y eco dub de la melodía flotando en estéreo) + Living Exit RC en Compás 64.
  5. Modo Dual Honesto (INV_C5_ACOUSTIC_GATE):
       - Sin audio fuente: exporta Master 48 kHz/24-bit, 8 Stems, MIDI Tipo 1, .flp, .pyscript
         y .scl bajo clasificación AUTÓMATA_SINTÉTICO_ESTRUCTURAL.
       - Con --source-audio o --vocal-stem: separa vía Demucs conservando solo capas
         orgánicas (vocals/other), descarta percusión residual (§10), corrige deriva de afinación
         vintage (~431-455 Hz) y tiempo, y compila el remix híbrido TRANSDUCCION_ORGANICA_DEMUCS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
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
    from scripts.bounces_paths import resolve_bounces_dir, resolve_fl_user_dir
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
    from bounces_paths import resolve_bounces_dir, resolve_fl_user_dir
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
BPM = 122.0
PPQ = 480
TOTAL_BARS = 64
KICK_ROOT_HZ = 49.00  # G1 (48-55 Hz club impact anchor; V of C / 9th of Fmaj9)
MPC_SWING = 0.565
BASS_BEHIND_BEAT_SEC = 0.006

RUBIN_LINTER_PATH = Path(
    "/Users/borjafernandezangulo/.gemini/config/skills/"
    "c5-rubin-acoustic-linter/scripts/audit_acoustic_exergy.py"
)

# Ciclo armónico de "Mira Niñita" (F -> C -> G) en voicings Deep House (Satin/AIR)
# (bass_root_midi, bass_octave_midi, rhodes_chord_midi, pad_chord_midi, chord_label)
HARMONIC_CYCLE: List[Tuple[int, int, List[int], List[int], str]] = [
    (29, 41, [53, 57, 60, 64, 67], [57, 60, 64, 67], "Fmaj9"),
    (36, 48, [48, 55, 60, 62, 64], [55, 60, 62, 64], "Cmaj9"),
    (31, 43, [55, 59, 62, 64, 69], [59, 62, 64, 69], "G6add9"),
    (31, 40, [53, 57, 60, 62, 67], [57, 60, 62, 67], "Fmaj9/G -> G13sus4"),
]

# Hemiola andina 6/8 (3+3+2 en corcheas) proyectada sobre bloque de 4 compases (32 corcheas)
CHORD_HEMIOLA_EIGHTHS = [0, 3, 6, 8, 11, 14, 16, 19, 22, 24, 27, 30]

# Repique de charango en semicorcheas por compás (patrón sincopado 6/8 sobre 4/4)
CHARANGO_REPIQUE_STEPS = [0, 3, 6, 9, 12, 14]

# Motivo introductorio de Quena / Flauta (A-B-C-D-C-B-A / B-C-D-C-B-A-G) en tiempos de negra
QUENA_INTRO_PHRASE_A: List[Tuple[float, int, float]] = [
    (0.00, 69, 0.42),  # A4
    (0.75, 71, 0.36),  # B4
    (1.50, 72, 0.42),  # C5
    (2.25, 74, 0.56),  # D5
    (3.25, 72, 0.36),  # C5
    (4.00, 71, 0.40),  # B4
    (4.75, 69, 0.82),  # A4
]

QUENA_INTRO_PHRASE_B: List[Tuple[float, int, float]] = [
    (0.00, 71, 0.40),  # B4
    (0.75, 72, 0.36),  # C5
    (1.50, 74, 0.52),  # D5
    (2.25, 72, 0.38),  # C5
    (3.00, 71, 0.36),  # B4
    (3.75, 69, 0.38),  # A4
    (4.50, 67, 1.00),  # G4
]

QUENA_CHORUS_REFRAIN: List[Tuple[float, int, float]] = [
    (0.00, 72, 0.30),  # C5 ("Mi-")
    (0.50, 72, 0.30),  # C5 ("-ra")
    (1.00, 72, 0.30),  # C5 ("ni-")
    (1.50, 72, 0.30),  # C5 ("-ñi-")
    (2.00, 72, 0.52),  # C5 ("-ta")
    (3.00, 71, 0.44),  # B4
    (3.75, 69, 0.44),  # A4
    (4.50, 67, 1.25),  # G4
]

QUENA_FALSE_DROP_CALL: List[Tuple[float, int, float]] = [
    (0.00, 72, 0.28),  # C5
    (0.50, 72, 0.28),  # C5
    (1.00, 72, 0.30),  # C5
    (1.50, 71, 0.28),  # B4
    (2.00, 69, 0.32),  # A4
    (2.50, 67, 0.85),  # G4 flotando en eco dub sobre el Falso Drop (pulsos 3-4)
]

JUST_INTONATION_C_SCL = """! mira_ninita_just_c_maj.scl
Entonación Justa 5-Limit en Do Mayor (Calidez Acústica Los Jaivas - Mira Niñita)
 12
!
 111.73129
 203.91000
 315.64129
 386.31371
 498.04500
 590.22371
 701.95500
 813.68629
 884.35871
 996.09000
 1088.26871
 2/1
"""


def midi_to_hz(midi_note: float, detune_cents: float = 0.0) -> float:
    return 440.0 * (2.0 ** (((midi_note - 69.0) + (detune_cents / 100.0)) / 12.0))


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
    if sixteenth_idx % 2 == 1:
        return (MPC_SWING - 0.5) * 2.0 * sixteenth_sec
    return 0.0


def _apply_smooth_gate_window(
    buf: np.ndarray,
    start_idx: int,
    end_idx: int,
    fade_ms: float = 14.0,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    """Silencia suavemente una ventana [start_idx, end_idx) mediante rampa raised-cosine."""
    n = len(buf)
    s0 = max(0, start_idx)
    s1 = min(n, end_idx)
    if s1 <= s0:
        return
    f_len = min((s1 - s0) // 2, max(8, int(round((fade_ms / 1000.0) * sample_rate))))
    w = np.zeros(s1 - s0, dtype=np.float64)
    w[:f_len] = 0.5 * (1.0 + np.cos(np.pi * np.arange(f_len) / max(1, f_len - 1)))
    w[-f_len:] = 0.5 * (1.0 - np.cos(np.pi * np.arange(f_len) / max(1, f_len - 1)))
    w.flags.writeable = False
    buf[s0:s1] *= w


def render_rhodes_celesta_chord(
    notes_midi: Sequence[int],
    duration_sec: float,
    cutoff_peak_hz: float = 1850.0,
    velocity: float = 0.85,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """Fender Rhodes 73 con destello sutil de celesta y micro-rasgueo humano (9 ms/voz)."""
    n = max(64, int(round(duration_sec * sample_rate)))
    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)

    strum_step = int(round(0.009 * sample_rate))
    nyq = 0.5 * sample_rate

    for voice_idx, m_note in enumerate(notes_midi):
        delay_s = voice_idx * strum_step
        if delay_s >= n - 32:
            break
        v_len = n - delay_s
        tv = make_time_axis(v_len, sample_rate)
        f0 = midi_to_hz(float(m_note))

        # Cuerpo cálido de Rhodes + púa/celesta suave (2º y 4º armónico atenuados rápido)
        osc_a = polyblep_saw(
            f0 * (2.0 ** (-3.8 / 1200.0)), v_len, sample_rate, initial_phase=0.09 * voice_idx
        )
        osc_b = polyblep_pulse(
            f0 * (2.0 ** (3.8 / 1200.0)), v_len, sample_rate, duty=0.47, initial_phase=0.23 * voice_idx
        )
        tine = freeze_array(0.28 * np.sin(2.0 * math.pi * f0 * tv))
        celesta_bell = freeze_array(0.11 * np.sin(2.0 * math.pi * (2.0 * f0) * tv) * np.exp(-tv / 0.085))
        env_amp = freeze_array(np.exp(-tv / max(0.32, duration_sec * 0.78)))
        raw = freeze_array((0.38 * osc_a + 0.34 * osc_b + tine + celesta_bell) * env_amp)

        c_hi = min(0.85, cutoff_peak_hz / nyq)
        c_lo = min(0.55, max(320.0, cutoff_peak_hz * 0.36) / nyq)
        sos_hi = signal.butter(2, c_hi, btype="low", output="sos")
        sos_lo = signal.butter(2, c_lo, btype="low", output="sos")
        env_filt = freeze_array(np.exp(-tv / 0.28))
        bright = freeze_array(signal.sosfilt(sos_hi, raw))
        warm = freeze_array(signal.sosfilt(sos_lo, raw))
        filtered = env_filt * bright + (1.0 - env_filt) * warm

        voice_env = apply_zero_crackle_envelope(
            filtered, sample_rate=sample_rate, attack_ms=8.5, release_ms=18.0
        )
        pan = -0.32 + 0.64 * (voice_idx / max(1, len(notes_midi) - 1))
        gain_l = math.cos((pan + 1.0) * math.pi * 0.25)
        gain_r = math.sin((pan + 1.0) * math.pi * 0.25)
        left[delay_s:] += voice_env * gain_l
        right[delay_s:] += voice_env * gain_r

    norm = max(1.0, math.sqrt(len(notes_midi)))
    left = oversampled_soft_saturate((left / norm) * velocity * 0.85, drive_db=1.1, threshold_db=-3.5)
    right = oversampled_soft_saturate((right / norm) * velocity * 0.85, drive_db=1.1, threshold_db=-3.5)
    return (
        apply_zero_crackle_envelope(left, sample_rate=sample_rate, attack_ms=6.0, release_ms=14.0),
        apply_zero_crackle_envelope(right, sample_rate=sample_rate, attack_ms=6.0, release_ms=14.0),
    )


def render_andean_quena_note(
    midi_note: int,
    duration_sec: float,
    velocity: float = 0.80,
    sample_rate: int = SAMPLE_RATE,
    seed: int = 1972,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Flauta andina (Quena / Traversa) vectorizada a 48 kHz:
      - Embocadura inicial suave (-32 cents -> 0 cents en 48 ms).
      - Vibrato respirado tardío a 5.1 Hz tras 95 ms.
      - Turbulencia aérea filtrada de banda estrecha (700-2400 Hz, cero ruido blanco crudo).
      - Envolvente Zero-Crackle con derivadas acotadas.
    """
    n = max(64, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    f0 = midi_to_hz(float(midi_note))

    scoop_cents = -32.0 * np.exp(-t / 0.048)
    vib_gate = 1.0 - np.exp(-np.maximum(0.0, t - 0.095) / 0.090)
    vib_cents = 14.0 * vib_gate * np.sin(2.0 * math.pi * 5.1 * t)
    f_inst = freeze_array(f0 * (2.0 ** ((scoop_cents + vib_cents) / 1200.0)))
    phase = freeze_array(2.0 * math.pi * (np.cumsum(f_inst) - f_inst[0]) / float(sample_rate))

    # Timbre hueco de caña andina (fundamental dominante + 2º/3º armónicos suaves)
    bore = (
        0.78 * np.sin(phase)
        + 0.18 * np.sin(2.0 * phase + 0.15)
        + 0.04 * np.sin(3.0 * phase + 0.30)
    )

    # Soplo aéreo resonante estrecho alrededor de f0 y 2*f0 (mantiene SFM ultra bajo)
    rng = np.random.default_rng(seed + midi_note)
    air_raw = rng.normal(0.0, 1.0, n)
    nyq = 0.5 * sample_rate
    bp_lo = max(250.0, min(f0 * 0.85, 2200.0)) / nyq
    bp_hi = min(0.82, max(f0 * 2.1, 1750.0) / nyq)
    sos_air = signal.butter(2, [bp_lo, bp_hi], btype="band", output="sos")
    air_breath = freeze_array(signal.sosfilt(sos_air, air_raw) * (0.032 * np.exp(-t / 0.14) + 0.010))

    env_body = freeze_array((1.0 - np.exp(-t / 0.030)) * np.exp(-t / max(0.35, duration_sec * 1.15)))
    sig = (bore + air_breath) * env_body * velocity * 0.14
    sig = oversampled_soft_saturate(sig, drive_db=0.8, threshold_db=-4.0, asymmetry=0.025)
    sig = apply_zero_crackle_envelope(sig, sample_rate=sample_rate, attack_ms=16.0, release_ms=28.0)

    # Imagen estéreo orgánica ligeramente desplazada
    return sig * 0.96, sig * 0.88


def render_charango_pluck(
    midi_note: int,
    duration_sec: float = 0.34,
    velocity: float = 0.72,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Charango andino de órdenes dobles (±2.4 cents):
      - Parciales de cuerda de nailon con amortiguación dependiente de frecuencia (tau_k ~ 1/k^1.35).
      - Cuerpo de armadillo/madera filtrado < 3.6 kHz (calidez orgánica sin clics ni brillo plástico).
    """
    n = max(64, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    f0 = midi_to_hz(float(midi_note))

    course_l = np.zeros(n, dtype=np.float64)
    course_r = np.zeros(n, dtype=np.float64)
    f_a = f0 * (2.0 ** (-2.4 / 1200.0))
    f_b = f0 * (2.0 ** (2.4 / 1200.0))

    for k in range(1, 6):
        if k * f0 >= 3600.0:
            break
        amp_k = 1.0 / (k ** 1.45)
        tau_k = 0.28 / (k ** 1.30)
        dec_k = freeze_array(np.exp(-t / max(0.025, tau_k)) * amp_k)
        course_l += np.sin(2.0 * math.pi * (k * f_a) * t + 0.12 * k) * dec_k
        course_r += np.sin(2.0 * math.pi * (k * f_b) * t + 0.27 * k) * dec_k

    # Micro-resonancia de caja de madera (~420 Hz)
    wood_tap = freeze_array(0.12 * np.sin(2.0 * math.pi * 420.0 * t) * np.exp(-t / 0.012))
    nyq = 0.5 * sample_rate
    sos_body = signal.butter(2, [240.0 / nyq, 3600.0 / nyq], btype="band", output="sos")
    pl_l = signal.sosfilt(sos_body, course_l + wood_tap) * velocity * 0.11
    pl_r = signal.sosfilt(sos_body, course_r + wood_tap) * velocity * 0.11

    return (
        apply_zero_crackle_envelope(pl_l, sample_rate=sample_rate, attack_ms=6.0, release_ms=16.0),
        apply_zero_crackle_envelope(pl_r, sample_rate=sample_rate, attack_ms=6.0, release_ms=16.0),
    )


def render_air_solina_pad(
    notes_midi: Sequence[int],
    duration_sec: float,
    velocity: float = 0.55,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """Colchón AIR Solina String Ensemble cálido con modulación lenta coral."""
    n = max(64, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    pad_l = np.zeros(n, dtype=np.float64)
    pad_r = np.zeros(n, dtype=np.float64)

    lfo_a = freeze_array(1.0 + 0.0028 * np.sin(2.0 * math.pi * 0.42 * t))
    lfo_b = freeze_array(1.0 + 0.0028 * np.sin(2.0 * math.pi * 0.57 * t + 1.1))

    for idx, m_note in enumerate(notes_midi):
        f0 = midi_to_hz(float(m_note))
        v_a = polyblep_saw(f0 * lfo_a, n, sample_rate, initial_phase=0.11 * idx)
        v_b = polyblep_saw(f0 * lfo_b * (2.0 ** (4.0 / 1200.0)), n, sample_rate, initial_phase=0.37 * idx)
        pad_l += 0.60 * v_a + 0.40 * v_b
        pad_r += 0.40 * v_a + 0.60 * v_b

    norm = max(1.0, len(notes_midi))
    pad_l = (pad_l / norm) * velocity * 0.22
    pad_r = (pad_r / norm) * velocity * 0.22

    # Barrido cálido en medios sin brillo sintético
    nyq = 0.5 * sample_rate
    sos_lp = signal.butter(2, 3400.0 / nyq, btype="low", output="sos")
    pad_l = signal.sosfilt(sos_lp, pad_l)
    pad_r = signal.sosfilt(sos_lp, pad_r)

    return (
        apply_zero_crackle_envelope(pad_l, sample_rate=sample_rate, attack_ms=65.0, release_ms=95.0),
        apply_zero_crackle_envelope(pad_r, sample_rate=sample_rate, attack_ms=65.0, release_ms=95.0),
    )


def render_sub_bass_note(
    midi_note: int,
    duration_sec: float,
    velocity: float = 0.90,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Subgrave Deep House Zero-Crackle con muesca Bark sobre fundamental del kick (49 Hz)."""
    n = max(64, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    f0 = midi_to_hz(float(midi_note))

    fundamental = freeze_array(0.80 * np.sin(2.0 * math.pi * f0 * t))
    warm_saw = polyblep_saw(f0, n, sample_rate=sample_rate, initial_phase=0.0)
    sos_lp = signal.butter(2, 210.0 / (0.5 * sample_rate), btype="low", output="sos")
    harm = freeze_array(signal.sosfilt(sos_lp, 0.22 * warm_saw))

    env = freeze_array(np.exp(-t / max(0.18, duration_sec * 0.92)))
    raw = (fundamental + harm) * env * velocity * 0.52

    b_n, a_n = signal.iirnotch(KICK_ROOT_HZ, Q=2.3, fs=sample_rate)
    carved = 0.58 * signal.lfilter(b_n, a_n, raw) + 0.42 * raw
    carved = oversampled_soft_saturate(carved, drive_db=1.0, threshold_db=-4.5)
    return apply_zero_crackle_envelope(carved, sample_rate=sample_rate, attack_ms=8.0, release_ms=14.0)


def render_organic_clap(sample_rate: int = SAMPLE_RATE, variant: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(1700 + variant)
    n = int(round(0.18 * sample_rate))
    t = make_time_axis(n, sample_rate)
    bursts = freeze_array(
        np.exp(-t / 0.008)
        + 0.70 * np.exp(-np.maximum(0.0, t - 0.009) / 0.011) * (t >= 0.009)
        + 0.52 * np.exp(-np.maximum(0.0, t - 0.020) / 0.028) * (t >= 0.020)
    )
    tone_body = freeze_array(0.32 * np.sin(2.0 * math.pi * 620.0 * t) * np.exp(-t / 0.014))
    noise_l = rng.normal(0.0, 1.0, n)
    noise_r = 0.86 * noise_l + 0.14 * rng.normal(0.0, 1.0, n)
    sos_bp = signal.butter(2, [650.0 / (0.5 * sample_rate), 2500.0 / (0.5 * sample_rate)], btype="band", output="sos")
    cl_l = (signal.sosfilt(sos_bp, noise_l) + tone_body) * bursts * 0.12
    cl_r = (signal.sosfilt(sos_bp, noise_r) + tone_body) * bursts * 0.12
    return (
        apply_zero_crackle_envelope(cl_l, sample_rate=sample_rate, attack_ms=5.0, release_ms=12.0),
        apply_zero_crackle_envelope(cl_r, sample_rate=sample_rate, attack_ms=5.0, release_ms=12.0),
    )


def render_house_hat(
    open_hat: bool = False,
    sample_rate: int = SAMPLE_RATE,
    variant: int = 0,
) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng((1900 if open_hat else 1800) + variant)
    dur = 0.21 if open_hat else 0.058
    n = int(round(dur * sample_rate))
    t = make_time_axis(n, sample_rate)
    decay = freeze_array(np.exp(-t / (0.062 if open_hat else 0.014)))

    partials = sum(
        np.sin(2.0 * math.pi * f * t + 0.3 * i)
        for i, f in enumerate([6380.0, 8010.0, 9690.0, 11520.0])
    ) * 0.22
    n_l = rng.normal(0.0, 1.0, n) * 0.34 + partials
    n_r = (0.86 * n_l + 0.14 * rng.normal(0.0, 1.0, n)) * 0.96

    nyq = 0.5 * sample_rate
    sos_bp = signal.butter(2, [6200.0 / nyq, 13600.0 / nyq], btype="band", output="sos")
    h_l = signal.sosfilt(sos_bp, n_l) * decay * (0.11 if open_hat else 0.070)
    h_r = signal.sosfilt(sos_bp, n_r) * decay * (0.11 if open_hat else 0.070)
    return (
        apply_zero_crackle_envelope(h_l, sample_rate=sample_rate, attack_ms=5.0, release_ms=10.0),
        apply_zero_crackle_envelope(h_r, sample_rate=sample_rate, attack_ms=5.0, release_ms=10.0),
    )


def render_sub_drop_transition(sample_rate: int = SAMPLE_RATE) -> Tuple[np.ndarray, np.ndarray]:
    """Caída subgrave cálida 130 Hz -> 32 Hz en la entrada al breakdown."""
    dur = 1.65
    n = int(round(dur * sample_rate))
    t = make_time_axis(n, sample_rate)
    f_inst = freeze_array(32.0 + (130.0 - 32.0) * np.exp(-t / 0.42))
    phase = freeze_array(2.0 * math.pi * (np.cumsum(f_inst) - f_inst[0]) / float(sample_rate))
    sig = np.sin(phase) * np.exp(-t / 0.65) * 0.36
    sig = apply_zero_crackle_envelope(sig, sample_rate=sample_rate, attack_ms=12.0, release_ms=40.0)
    return sig, sig.copy()


def extract_organic_stems_with_demucs(
    source_audio: Path,
    work_dir: Path,
    keep_other: bool = False,
) -> Dict[str, Path]:
    """Separa audio legítimo con Demucs conservando solo vocals/other (descarta drums residuales)."""
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
    source_tuning_cents: Optional[float] = None,
) -> Tuple[np.ndarray, np.ndarray, float, float]:
    """
    Carga stem orgánico, estima BPM y deriva de afinación vintage (ej. cinta ~431-455 Hz),
    corrige pitch a A4=440 Hz si procede, ajusta tempo, remuestrea a 48 kHz y aplica Bark carving.
    """
    import librosa
    import soundfile as sf

    data, sr_in = sf.read(str(stem_path), always_2d=True)
    data = data.astype(np.float64)
    if data.shape[1] == 1:
        data = np.column_stack((data[:, 0], data[:, 0]))
    else:
        data = data[:, :2]

    mono_est = 0.5 * (data[:, 0] + data[:, 1])
    if source_bpm_override and source_bpm_override > 20.0:
        src_bpm = float(source_bpm_override)
    else:
        tempo_val, _ = librosa.beat.beat_track(y=mono_est, sr=sr_in)
        src_bpm = float(np.atleast_1d(tempo_val)[0])
        if src_bpm < 55.0:
            src_bpm *= 2.0
        elif src_bpm > 175.0:
            src_bpm *= 0.5

    if source_tuning_cents is not None:
        tuning_semitones = float(source_tuning_cents) / 100.0
    else:
        tuning_bins = float(librosa.estimate_tuning(y=mono_est, sr=sr_in))
        tuning_semitones = tuning_bins

    if sr_in != sample_rate:
        g = math.gcd(int(sample_rate), int(sr_in))
        data = signal.resample_poly(data, up=int(sample_rate) // g, down=int(sr_in) // g, axis=0)

    l_ch, r_ch = data[:, 0], data[:, 1]
    if abs(tuning_semitones) > 0.08:
        l_ch = librosa.effects.pitch_shift(l_ch, sr=sample_rate, n_steps=-tuning_semitones)
        r_ch = librosa.effects.pitch_shift(r_ch, sr=sample_rate, n_steps=-tuning_semitones)

    rate = float(np.clip(target_bpm / max(src_bpm, 40.0), 0.72, 1.45))
    if abs(rate - 1.0) > 0.004:
        l_st = librosa.effects.time_stretch(l_ch, rate=rate)
        r_st = librosa.effects.time_stretch(r_ch, rate=rate)
        n_st = min(len(l_st), len(r_st))
        l_ch, r_ch = l_st[:n_st], r_st[:n_st]

    out_l = np.zeros(target_samples, dtype=np.float64)
    out_r = np.zeros(target_samples, dtype=np.float64)
    copy_n = min(target_samples, len(l_ch))
    out_l[:copy_n] = apply_zero_crackle_envelope(l_ch[:copy_n], sample_rate=sample_rate, attack_ms=15.0, release_ms=40.0)
    out_r[:copy_n] = apply_zero_crackle_envelope(r_ch[:copy_n], sample_rate=sample_rate, attack_ms=15.0, release_ms=40.0)
    out_l, out_r = carve_polyphonic_mud(out_l, out_r, sample_rate=sample_rate, hpf_hz=190.0, mud_hz=360.0)
    return out_l, out_r, src_bpm, round(tuning_semitones * 100.0, 2)


def write_multichannel_midi(
    midi_path: Path,
    track_events: Dict[str, List[Tuple[int, int, int, int]]],
    quena_pitchbends: Optional[List[Tuple[int, int]]] = None,
    bpm: float = BPM,
) -> Path:
    """Escribe SMF Tipo 1 (480 PPQ) con cero deriva absoluta y pitchbends de expresión."""
    mid = mido.MidiFile(type=1, ticks_per_beat=PPQ)
    conductor = mido.MidiTrack()
    conductor.name = "Conductor_122BPM_MiraNinita"
    conductor.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))
    conductor.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))

    markers = [
        (0, "INTRO: Tape & Quena Whisper (Fmaj9 -> Cmaj9 -> G6)"),
        (8 * 4 * PPQ, "INTRO GROOVE: Warm 909 Kick & MPC 56.5% Hats"),
        (16 * 4 * PPQ, "GROOVE A: 6/8 Andean Hemiola over 4/4 Deep House"),
        (32 * 4 * PPQ, "BREAKDOWN: Sub Drop 130->32 Hz & Quena Refrain"),
        (40 * 4 * PPQ, "BUILD: Filter Sweep & Percussion Rise"),
        (48 * 4 * PPQ, "CLIMAX GROOVE B: Full Deep House Andean Drive"),
        (59 * 4 * PPQ + 2 * PPQ, "BAR 60: C5 False Drop Vacuum (Tape + Dub Quena)"),
        (60 * 4 * PPQ, "FINAL DROP: Full Impact"),
        (63 * 4 * PPQ, "LIVING EXIT: RC Exponential Decay"),
    ]
    last_t = 0
    for tick, txt in sorted(markers, key=lambda x: x[0]):
        conductor.append(mido.MetaMessage("marker", text=txt, time=max(0, tick - last_t)))
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

        if tr_name == "Andean_Quena_Lead" and quena_pitchbends:
            for pb_tick, pb_val in quena_pitchbends:
                raw_msgs.append((max(0, pb_tick), 2, mido.Message("pitchwheel", channel=channel, pitch=int(pb_val), time=0)))

        raw_msgs.sort(key=lambda item: (item[0], item[1]))
        prev_t = 0
        for t_abs, _, msg in raw_msgs:
            tr.append(msg.copy(time=max(0, t_abs - prev_t)))
            prev_t = t_abs
        if tr_name == "Andean_Quena_Lead":
            tr.append(mido.Message("pitchwheel", channel=channel, pitch=0, time=0))
        tr.append(mido.MetaMessage("end_of_track", time=0))
        mid.tracks.append(tr)

    midi_path.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(midi_path))
    return midi_path


def generate_piano_roll_pyscript(pyscript_path: Path) -> Path:
    """Genera script nativo de FL Studio 2025 (flpianoroll) para Mira Niñita Deep House."""
    content = '''# name = Mira Ninita (Los Jaivas) Deep House Hemiola & Quena
# author = Borja Fernandez Angulo / MOSKV-1
# description = Genera acordes Fmaj9-Cmaj9-G6add9 en hemiola 6/8-sobre-4/4, motivo de Quena con slides y bajo rolling.

import flpianoroll as flp


def createDialog():
    form = flp.ScriptDialog(
        "Mira Ninita — Deep House (122 BPM)",
        "Hemiola andina 6/8 sobre 4/4 (Fmaj9 -> Cmaj9 -> G6add9) y motivo de Quena con slides.",
    )
    form.AddInputCombo(
        "Capa a Generar",
        "Completa (Acordes + Quena + Bajo),Solo Acordes Rhodes/Charango,Solo Quena Melodia,Solo Subgrave Rolling",
        0,
    )
    form.AddInputKnob("Swing MPC (%)", 56.5, 50.0, 68.0)
    form.AddInputCheckbox("Slides Microtonales Quena", True)
    return form


def _add_note(score, number, time_480, len_480, vel, pitchoffset=0, slide=False, color=0, scale=1.0):
    n = flp.Note()
    n.number = int(number)
    n.time = max(0, int(round(time_480 * scale)))
    n.length = max(1, int(round(len_480 * scale)))
    n.velocity = float(vel)
    if hasattr(n, "pitchoffset"):
        n.pitchoffset = int(pitchoffset)
    if hasattr(n, "slide") and slide:
        n.slide = True
    if hasattr(n, "color"):
        n.color = int(color)
    score.addNote(n)


def apply(form):
    layer = form.GetInputValue("Capa a Generar")
    swing_pct = float(form.GetInputValue("Swing MPC (%)"))
    use_slides = bool(form.GetInputValue("Slides Microtonales Quena"))
    flp.score.clear()

    ppq = getattr(flp.score, "PPQ", 96)
    scale = ppq / 480.0
    swing_shift = int(round(((swing_pct - 50.0) / 50.0) * 120.0))

    chords = [
        (0, [53, 57, 60, 64, 67], 29),     # Fmaj9
        (1920, [48, 55, 60, 62, 64], 36),  # Cmaj9
        (3840, [55, 59, 62, 64, 69], 31),  # G6add9
        (5760, [53, 57, 60, 62, 67], 31),  # Fmaj9/G -> G13sus4
    ]

    if layer in (0, 1):
        hemiola = [0, 3, 6, 8, 11, 14, 16, 19, 22, 24, 27, 30]
        for idx, eighth_pos in enumerate(hemiola):
            c_idx = min(3, eighth_pos // 8)
            _, notes, _ = chords[c_idx]
            t0 = eighth_pos * 240
            for v_idx, p in enumerate(notes):
                _add_note(flp.score, p, t0 + v_idx * 14, 480, 0.78, color=0, scale=scale)

    if layer in (0, 2):
        # Frase A: A4 - B4 - C5 - D5 - C5 - B4 - A4 ; Frase B: B4 - C5 - D5 - C5 - B4 - A4 - G4
        quena_notes = [
            (0, 69, 280), (360, 71, 240), (720, 72, 280), (1080, 74, 380),
            (1560, 72, 240), (1920, 71, 260), (2280, 69, 520),
            (3840, 71, 260), (4200, 72, 240), (4560, 74, 340), (4920, 72, 240),
            (5280, 71, 240), (5640, 69, 240), (6000, 67, 640),
        ]
        for q_idx, (qt, qp, qdur) in enumerate(quena_notes):
            if use_slides and q_idx in (3, 9):
                _add_note(flp.score, qp - 2, qt, 90, 0.72, pitchoffset=-15, color=1, scale=scale)
                _add_note(flp.score, qp, qt + 45, qdur, 0.88, slide=True, color=1, scale=scale)
            else:
                _add_note(flp.score, qp, qt, qdur, 0.84, color=1, scale=scale)

    if layer in (0, 3):
        sub_beats = [360, 720 + swing_shift, 1320, 1680 + swing_shift]
        for bar_i, (_, _, root_p) in enumerate(chords):
            b0 = bar_i * 1920
            for sb_idx, sb in enumerate(sub_beats):
                pitch = root_p + (12 if sb_idx == 2 else 0)
                _add_note(flp.score, pitch, b0 + sb + 12, 210, 0.90, color=2, scale=scale)
'''
    pyscript_path.parent.mkdir(parents=True, exist_ok=True)
    pyscript_path.write_text(content, encoding="utf-8")
    return pyscript_path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_mira_ninita_deep_house_122(
    source_audio: Optional[str] = None,
    vocal_stem: Optional[str] = None,
    keep_other: bool = False,
    source_bpm_override: Optional[float] = None,
    source_tuning_cents: Optional[float] = None,
    profile_name: str = "deep_house",
    total_bars: int = TOTAL_BARS,
    output_dir: Optional[str] = None,
    deploy_fl_assets: bool = True,
) -> Dict[str, Any]:
    """Orquesta la compilación completa del remix Mira Niñita (Deep House 122 BPM)."""
    beat_sec = 60.0 / BPM
    bar_sec = 4.0 * beat_sec
    eighth_sec = 0.5 * beat_sec
    sixteenth_sec = 0.25 * beat_sec
    total_sec = total_bars * bar_sec
    n_samples = int(round(total_sec * SAMPLE_RATE))

    bounces_root = Path(output_dir).expanduser().resolve() if output_dir else resolve_bounces_dir()
    project_dir = bounces_root / "Mira_Ninita_Deep_House_122"
    stems_dir = project_dir / "stems"
    project_dir.mkdir(parents=True, exist_ok=True)
    stems_dir.mkdir(parents=True, exist_ok=True)

    # Buffers estéreo por stem
    kick_l = np.zeros(n_samples, dtype=np.float64)
    kick_r = np.zeros(n_samples, dtype=np.float64)
    bass_l = np.zeros(n_samples, dtype=np.float64)
    bass_r = np.zeros(n_samples, dtype=np.float64)
    perc_l = np.zeros(n_samples, dtype=np.float64)
    perc_r = np.zeros(n_samples, dtype=np.float64)
    chords_l = np.zeros(n_samples, dtype=np.float64)
    chords_r = np.zeros(n_samples, dtype=np.float64)
    quena_l = np.zeros(n_samples, dtype=np.float64)
    quena_r = np.zeros(n_samples, dtype=np.float64)
    charango_l = np.zeros(n_samples, dtype=np.float64)
    charango_r = np.zeros(n_samples, dtype=np.float64)
    pad_l = np.zeros(n_samples, dtype=np.float64)
    pad_r = np.zeros(n_samples, dtype=np.float64)
    dub_send_l = np.zeros(n_samples, dtype=np.float64)
    dub_send_r = np.zeros(n_samples, dtype=np.float64)

    # 5 variaciones round-robin de Kick cálido Deep House (49 Hz G1, LPF 1.35 kHz)
    sos_kick_warm = signal.butter(2, 1350.0 / (0.5 * SAMPLE_RATE), btype="low", output="sos")
    kicks_rr: List[np.ndarray] = []
    for i in range(5):
        k_raw = synthesize_phase_locked_kick(
            sample_rate=SAMPLE_RATE,
            duration_sec=0.38,
            root_hz=KICK_ROOT_HZ,
            punch_hz=134.0 + 2.0 * i,
            click_hz=1180.0,
            drive_db=1.6 + 0.10 * i,
        )
        k_warm = signal.sosfilt(sos_kick_warm, k_raw)
        k_warm = apply_zero_crackle_envelope(k_warm, sample_rate=SAMPLE_RATE, attack_ms=0.8, release_ms=12.0)
        k_pk = float(np.max(np.abs(k_warm)))
        if k_pk > 1e-6:
            k_warm = k_warm / k_pk
        kicks_rr.append(k_warm)

    claps_rr = [render_organic_clap(SAMPLE_RATE, variant=i) for i in range(5)]
    hats_c_rr = [render_house_hat(False, SAMPLE_RATE, variant=i) for i in range(5)]
    hats_o_rr = [render_house_hat(True, SAMPLE_RATE, variant=i) for i in range(5)]

    midi_tracks: Dict[str, List[Tuple[int, int, int, int]]] = {
        "Drums_Kick": [],
        "Drums_MPC_Perc": [],
        "SubBass_MiraNinita": [],
        "Rhodes_Hemiola_Chords": [],
        "Andean_Quena_Lead": [],
        "Charango_Repique": [],
        "AIR_Solina_Strings": [],
    }
    quena_pitchbends: List[Tuple[int, int]] = []
    kick_onsets: List[int] = []

    false_drop_bar = 59 if total_bars >= 64 else max(4, total_bars - 5)

    for bar_idx in range(total_bars):
        bar_t0 = bar_idx * bar_sec
        bar_tick0 = bar_idx * 4 * PPQ
        cycle_pos = bar_idx % 4
        bass_root, bass_oct, rhodes_notes, pad_notes, _ = HARMONIC_CYCLE[cycle_pos]

        in_intro_silent = bar_idx < 8
        in_intro_soft = 8 <= bar_idx < 16
        in_breakdown_vac = 32 <= bar_idx < 40
        in_breakdown_rise = 40 <= bar_idx < 48
        is_false_drop_bar = bar_idx == false_drop_bar
        is_exit_bar = bar_idx == (total_bars - 1)

        if bar_idx == 32:
            drop_l, drop_r = render_sub_drop_transition(SAMPLE_RATE)
            add_stereo(dub_send_l, dub_send_r, drop_l, drop_r, int(round(bar_t0 * SAMPLE_RATE)), gain=0.72)

        # 1. Kick & Percusión MPC 56.5%
        for beat in range(4):
            if is_false_drop_bar and beat >= 2:
                continue
            if is_exit_bar and beat >= 2:
                continue

            beat_t = bar_t0 + beat * beat_sec
            beat_s = int(round(beat_t * SAMPLE_RATE))
            beat_tick = bar_tick0 + beat * PPQ

            if not in_intro_silent and not in_breakdown_vac:
                k_gain = 0.36 if (in_intro_soft or in_breakdown_rise) else 0.64
                k_wave = kicks_rr[(bar_idx * 4 + beat) % 5]
                add_stereo(kick_l, kick_r, k_wave, k_wave, beat_s, gain=k_gain)
                kick_onsets.append(beat_s)
                midi_tracks["Drums_Kick"].append((beat_tick, beat_tick + 120, 36, int(112 * k_gain / 0.64)))

            if bar_idx >= 16 and not in_breakdown_vac and beat in (1, 3):
                c_l, c_r = claps_rr[(bar_idx + beat) % 5]
                c_gain = 0.62 if in_breakdown_rise else 0.90
                add_stereo(perc_l, perc_r, c_l, c_r, beat_s, gain=c_gain)
                midi_tracks["Drums_MPC_Perc"].append((beat_tick, beat_tick + 140, 39, int(94 * c_gain)))

            if bar_idx >= 8 and not in_breakdown_vac:
                oh_s = int(round((beat_t + 0.5 * beat_sec) * SAMPLE_RATE))
                oh_l, oh_r = hats_o_rr[(bar_idx + beat) % 5]
                oh_gain = 0.42 if (in_intro_soft or in_breakdown_rise) else 0.82
                add_stereo(perc_l, perc_r, oh_l, oh_r, oh_s, gain=oh_gain)
                midi_tracks["Drums_MPC_Perc"].append((beat_tick + PPQ // 2, beat_tick + PPQ // 2 + 100, 46, int(90 * oh_gain)))

                for step16 in range(4):
                    if step16 == 0:
                        continue
                    swing_dt = _compute_swing_offset_sec(step16, sixteenth_sec)
                    h_t = beat_t + step16 * sixteenth_sec + swing_dt
                    ch_l, ch_r = hats_c_rr[(bar_idx + beat + step16) % 5]
                    ch_gain = 0.46 if step16 == 2 else 0.32
                    add_stereo(perc_l, perc_r, ch_l, ch_r, int(round(h_t * SAMPLE_RATE)), gain=ch_gain)
                    sw_ticks = int(round((swing_dt / beat_sec) * PPQ))
                    t16 = beat_tick + step16 * (PPQ // 4) + sw_ticks
                    midi_tracks["Drums_MPC_Perc"].append((t16, t16 + 60, 42, 72 if step16 == 2 else 56))

        # 2. Subgrave Rolling (+6 ms behind-the-beat)
        if bar_idx >= 16 and not in_breakdown_vac:
            sub_positions = [0.75, 1.50, 2.75, 3.50]
            for idx_b, b_pos in enumerate(sub_positions):
                if is_false_drop_bar and b_pos >= 2.0:
                    continue
                if is_exit_bar and b_pos >= 2.0:
                    continue
                note_pitch = bass_oct if idx_b == 2 else bass_root
                note_t = bar_t0 + b_pos * beat_sec + BASS_BEHIND_BEAT_SEC
                note_dur = 0.32 if idx_b % 2 == 0 else 0.24
                vel = 0.70 if in_breakdown_rise else 0.92
                sub_wave = render_sub_bass_note(note_pitch, note_dur, velocity=vel, sample_rate=SAMPLE_RATE)
                add_stereo(bass_l, bass_r, sub_wave, sub_wave, int(round(note_t * SAMPLE_RATE)), gain=1.0)
                t_start = bar_tick0 + int(round(b_pos * PPQ))
                midi_tracks["SubBass_MiraNinita"].append((t_start, t_start + 220, note_pitch, int(106 * vel)))

        # 3. Charango Repique 6/8 sobre 4/4 (desde compás 8 hasta salida)
        if bar_idx >= 8 and not is_false_drop_bar:
            for ch_idx, step16 in enumerate(CHARANGO_REPIQUE_STEPS):
                if is_exit_bar and step16 >= 8:
                    continue
                swing_dt = _compute_swing_offset_sec(step16 % 4, sixteenth_sec)
                c_t = bar_t0 + step16 * sixteenth_sec + swing_dt
                c_note = rhodes_notes[(bar_idx + ch_idx) % len(rhodes_notes)] + 12
                c_vel = 0.56 if in_intro_soft else (0.76 if bar_idx >= 48 else 0.66)
                pl_l, pl_r = render_charango_pluck(c_note, duration_sec=0.34, velocity=c_vel, sample_rate=SAMPLE_RATE)
                add_stereo(charango_l, charango_r, pl_l, pl_r, int(round(c_t * SAMPLE_RATE)), gain=0.62)
                t_ch = bar_tick0 + step16 * (PPQ // 4)
                midi_tracks["Charango_Repique"].append((t_ch, t_ch + 160, c_note, int(92 * c_vel)))

        # 4. Solina Strings Pad cada 4 compases (entra suavemente en breakdown y clímax)
        if cycle_pos == 0 and (bar_idx >= 16):
            pad_dur = 3.85 * beat_sec
            for p_bar in range(4):
                abs_b = bar_idx + p_bar
                if abs_b >= total_bars:
                    break
                _, _, _, p_notes, _ = HARMONIC_CYCLE[p_bar]
                p_vel = 0.64 if (32 <= abs_b < 48 or abs_b >= 48) else 0.42
                p_l, p_r = render_air_solina_pad(p_notes, duration_sec=pad_dur, velocity=p_vel, sample_rate=SAMPLE_RATE)
                p_s = int(round(abs_b * bar_sec * SAMPLE_RATE))
                add_stereo(pad_l, pad_r, p_l, p_r, p_s, gain=0.82)
                t_p0 = abs_b * 4 * PPQ
                for pn in p_notes:
                    midi_tracks["AIR_Solina_Strings"].append((t_p0, t_p0 + 1800, pn, int(82 * p_vel)))

        # 5. Bloque polirrítmico cada 4 compases: Acordes Rhodes/Celesta 6/8 + Melodías de Quena
        if cycle_pos == 0:
            block_t0 = bar_t0
            block_tick0 = bar_tick0
            for m_idx, eighth_pos in enumerate(CHORD_HEMIOLA_EIGHTHS):
                bar_of_hit = bar_idx + (eighth_pos // 8)
                if bar_of_hit == false_drop_bar and (eighth_pos % 8) >= 4:
                    continue
                if bar_of_hit >= total_bars - 1 and (eighth_pos % 8) >= 4:
                    continue

                c_idx = min(3, eighth_pos // 8)
                _, _, c_notes, _, _ = HARMONIC_CYCLE[c_idx]
                next_pos = CHORD_HEMIOLA_EIGHTHS[m_idx + 1] if m_idx + 1 < len(CHORD_HEMIOLA_EIGHTHS) else 32
                hit_dur = max(0.35, (next_pos - eighth_pos) * eighth_sec * 0.92)
                vel = 0.78 + 0.06 * math.sin(m_idx * 1.1)
                cutoff_hz = 1180.0 + 780.0 * (bar_of_hit / float(total_bars))
                if 32 <= bar_of_hit < 48:
                    cutoff_hz *= 0.88

                c_l, c_r = render_rhodes_celesta_chord(
                    c_notes,
                    duration_sec=hit_dur,
                    cutoff_peak_hz=cutoff_hz,
                    velocity=vel,
                    sample_rate=SAMPLE_RATE,
                )
                hit_s = int(round((block_t0 + eighth_pos * eighth_sec) * SAMPLE_RATE))
                add_stereo(chords_l, chords_r, c_l, c_r, hit_s, gain=0.95)

                if (m_idx % 3 == 2) or (bar_of_hit in (false_drop_bar, 31, 32)):
                    add_stereo(dub_send_l, dub_send_r, c_l, c_r, hit_s, gain=0.68)

                t_c0 = block_tick0 + eighth_pos * (PPQ // 2)
                t_c1 = t_c0 + max(120, int(round((hit_dur / beat_sec) * PPQ)))
                for pitch in c_notes:
                    midi_tracks["Rhodes_Hemiola_Chords"].append((t_c0, t_c1, pitch, int(92 * vel)))

            # Motivo melódico de Quena según la sección
            if bar_idx < 16 or (16 <= bar_idx < 32):
                phrase_events = [(0.0, QUENA_INTRO_PHRASE_A), (8.0, QUENA_INTRO_PHRASE_B)]
                q_gain = 0.85 if bar_idx < 8 else 0.78
            elif 32 <= bar_idx < 48:
                phrase_events = [(0.0, QUENA_CHORUS_REFRAIN), (8.0, QUENA_INTRO_PHRASE_B)]
                q_gain = 0.94
            elif bar_idx == 56 and false_drop_bar == 59:
                # Bloque final 57-60: frase de entrada + llamada sobre Bar 60 Falso Drop
                phrase_events = [(0.0, QUENA_CHORUS_REFRAIN), (12.0, QUENA_FALSE_DROP_CALL)]
                q_gain = 1.0
            else:
                phrase_events = [(0.0, QUENA_CHORUS_REFRAIN), (8.0, QUENA_INTRO_PHRASE_A)]
                q_gain = 0.90

            for phrase_beat_off, notes_seq in phrase_events:
                for b_rel, q_pitch, q_dur_beats in notes_seq:
                    abs_beat = bar_idx * 4.0 + phrase_beat_off + b_rel
                    if abs_beat >= total_bars * 4.0 - 1.5:
                        continue
                    q_t = abs_beat * beat_sec
                    q_dur_s = max(0.18, q_dur_beats * beat_sec)
                    ql, qr = render_andean_quena_note(
                        q_pitch,
                        duration_sec=q_dur_s,
                        velocity=0.82 * q_gain,
                        sample_rate=SAMPLE_RATE,
                        seed=1972 + bar_idx,
                    )
                    q_s = int(round(q_t * SAMPLE_RATE))
                    add_stereo(quena_l, quena_r, ql, qr, q_s, gain=1.0)
                    # Enviar frase de Quena al lazo dub (especialmente en breakdown y antes del Falso Drop)
                    in_fd_window = abs(abs_beat - (false_drop_bar * 4.0 + 1.0)) <= 2.5
                    if (32 <= bar_idx < 40) or in_fd_window or (q_pitch in (67, 69) and q_dur_beats >= 0.75):
                        add_stereo(dub_send_l, dub_send_r, ql, qr, q_s, gain=0.95)

                    t_q0 = int(round(abs_beat * PPQ))
                    t_q1 = t_q0 + max(80, int(round(q_dur_beats * PPQ)))
                    midi_tracks["Andean_Quena_Lead"].append((t_q0, t_q1, q_pitch, int(98 * min(1.0, q_gain))))
                    quena_pitchbends.append((t_q0, -450))
                    quena_pitchbends.append((t_q0 + 36, 0))

    # Falso Drop determinista (Compás 60 pulsos 3-4)
    fd_start = int(round((false_drop_bar * bar_sec + 2.0 * beat_sec) * SAMPLE_RATE))
    fd_end = int(round(((false_drop_bar + 1) * bar_sec) * SAMPLE_RATE))
    for buf in (kick_l, kick_r, perc_l, perc_r, bass_l, bass_r):
        _apply_smooth_gate_window(buf, fd_start, fd_end, fade_ms=14.0, sample_rate=SAMPLE_RATE)

    # Living Exit (compás final): relajación exponencial RC hasta 0.0
    exit_start = int(round((total_bars - 1) * bar_sec * SAMPLE_RATE))
    if exit_start < n_samples:
        t_ex = make_time_axis(n_samples - exit_start, SAMPLE_RATE)
        rc_decay = np.exp(-t_ex / 0.85)
        n_end_fade = min(len(rc_decay), int(round(0.040 * SAMPLE_RATE)))
        rc_decay[-n_end_fade:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(n_end_fade) / max(1, n_end_fade - 1)))
        rc_decay[-1] = 0.0
        rc_decay.flags.writeable = False
        for buf in (
            kick_l, kick_r, perc_l, perc_r, bass_l, bass_r,
            chords_l, chords_r, quena_l, quena_r, charango_l, charango_r, pad_l, pad_r,
        ):
            buf[exit_start:] *= rc_decay

    # Bark Carving en pistas polifónicas
    chords_l, chords_r = carve_polyphonic_mud(chords_l, chords_r, sample_rate=SAMPLE_RATE, hpf_hz=185.0, mud_hz=375.0)
    pad_l, pad_r = carve_polyphonic_mud(
        pad_l, pad_r, sample_rate=SAMPLE_RATE, hpf_hz=210.0, mud_hz=380.0, air_lpf_hz=9200.0
    )
    quena_l, quena_r = carve_polyphonic_mud(
        quena_l, quena_r, sample_rate=SAMPLE_RATE, hpf_hz=210.0, mud_hz=390.0, mud_cut_blend=0.25, air_lpf_hz=9000.0
    )
    charango_l, charango_r = carve_polyphonic_mud(
        charango_l, charango_r, sample_rate=SAMPLE_RATE, hpf_hz=220.0, mud_hz=385.0, mud_cut_blend=0.25, air_lpf_hz=9000.0
    )

    # Lazo Dub No-Conmutativo Pre-Filtro (corchea con puntillo, LPF 2800 Hz en realimentación)
    dub_send_l.flags.writeable = False
    dub_send_r.flags.writeable = False
    dub_delay_sec = 0.75 * beat_sec
    dub_wet_l, dub_wet_r = apply_noncommutative_dub_echo(
        dub_send_l,
        dub_send_r,
        sample_rate=SAMPLE_RATE,
        delay_sec=dub_delay_sec,
        feedback=0.44,
        lpf_hz=2800.0,
        hpf_hz=240.0,
        wet=0.75,
        taps=5,
    )
    dub_l = (dub_wet_l - dub_send_l) * 1.25
    dub_r = (dub_wet_r - dub_send_r) * 1.25

    # Sidechain multibanda acoplado al decaimiento del Kick (Zero-Crackle)
    sc_sub, sc_mid = build_coupled_multiband_sidechain(
        n_samples,
        kick_onsets,
        sample_rate=SAMPLE_RATE,
        tau_body=0.205,
        sub_depth=0.90,
        high_depth=0.20,
        attack_ms=6.0,
        lookahead_ms=3.0,
    )
    bass_lo_l, bass_hi_l = lr4_zero_phase_crossover(bass_l, 140.0, SAMPLE_RATE)
    bass_lo_r, bass_hi_r = lr4_zero_phase_crossover(bass_r, 140.0, SAMPLE_RATE)
    bass_l = (bass_lo_l * sc_sub) + (bass_hi_l * sc_mid)
    bass_r = (bass_lo_r * sc_sub) + (bass_hi_r * sc_mid)

    chords_l *= sc_mid
    chords_r *= sc_mid
    charango_l *= sc_mid
    charango_r *= sc_mid
    pad_l *= sc_mid
    pad_r *= sc_mid

    # Sala compartida coherente (18 ms pre-delay, 84% núcleo mono)
    perc_l, perc_r = apply_coherent_shared_room(perc_l, perc_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.09)
    chords_l, chords_r = apply_coherent_shared_room(chords_l, chords_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.14)
    quena_l, quena_r = apply_coherent_shared_room(quena_l, quena_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.16)
    charango_l, charango_r = apply_coherent_shared_room(charango_l, charango_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.12)
    pad_l, pad_r = apply_coherent_shared_room(pad_l, pad_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.18)
    dub_l, dub_r = apply_coherent_shared_room(dub_l, dub_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.16)

    # Lecho de cinta analógica activa (-57 dBFS, cero silencio digital 0.0)
    tape_l, tape_r = generate_warm_analog_tape_bed(n_samples, sample_rate=SAMPLE_RATE, level_dbfs=-57.0)
    tape_l = apply_zero_crackle_envelope(tape_l, sample_rate=SAMPLE_RATE, attack_ms=20.0, release_ms=40.0)
    tape_r = apply_zero_crackle_envelope(tape_r, sample_rate=SAMPLE_RATE, attack_ms=20.0, release_ms=40.0)

    # Ingesta opcional de audio orgánico real (Demucs o stem vocal)
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
        est_tunings_cents: Dict[str, float] = {}
        for label, s_path in stems_extracted.items():
            sl, sr_st, est_bpm, est_cents = align_organic_stem_to_house(
                s_path,
                target_samples=n_samples,
                target_bpm=BPM,
                sample_rate=SAMPLE_RATE,
                source_bpm_override=source_bpm_override,
                source_tuning_cents=source_tuning_cents,
            )
            est_bpms[label] = round(est_bpm, 2)
            est_tunings_cents[label] = est_cents
            weight = 0.88 if label == "vocals" else 0.40
            org_l += sl * weight
            org_r += sr_st * weight

        org_l *= sc_mid
        org_r *= sc_mid
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
        org_l, org_r = apply_coherent_shared_room(
            org_dub_l, org_dub_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, wet=0.14
        )
        organic_info["mode"] = "TRANSDUCCION_ORGANICA_DEMUCS"
        organic_info["estimated_source_bpm"] = est_bpms
        organic_info["detected_tuning_offset_cents"] = est_tunings_cents

    # Gate Zero-Crackle en subgrave y melódico Quena/Charango
    bass_mono = 0.5 * (bass_l + bass_r)
    zero_crackle_sub = check_zero_crackle_derivatives(bass_mono, max_d1=0.015, max_d2=0.005)
    if not zero_crackle_sub["zero_crackle_passed"]:
        raise RuntimeError(f"Fallo Zero-Crackle Derivative Gate en subgrave: {zero_crackle_sub}")

    quena_mono = 0.5 * (quena_l + quena_r)
    zero_crackle_lead = check_zero_crackle_derivatives(quena_mono, max_d1=0.015, max_d2=0.005)
    if not zero_crackle_lead["zero_crackle_passed"]:
        raise RuntimeError(f"Fallo Zero-Crackle Derivative Gate en Quena: {zero_crackle_lead}")

    # Exportar stems individuales (48 kHz / 24-bit PCM)
    stem_specs: List[Tuple[str, np.ndarray, np.ndarray]] = [
        ("01_Kick_DeepHouse_49Hz.wav", kick_l, kick_r),
        ("02_SubBass_MiraNinita_BehindBeat.wav", bass_l, bass_r),
        ("03_MPC_Groove_Percussion.wav", perc_l, perc_r),
        ("04_Rhodes_Celesta_Hemiola_Chords.wav", chords_l, chords_r),
        ("05_Andean_Quena_Lead.wav", quena_l, quena_r),
        ("06_Charango_Andino_Hemiola.wav", charango_l, charango_r),
        ("07_AIR_Solina_Strings_Pad.wav", pad_l, pad_r),
        ("08_BasicChannel_Dub_Echo.wav", dub_l, dub_r),
        ("09_Analog_Tape_Bed.wav", tape_l, tape_r),
    ]
    if organic_info["mode"] == "TRANSDUCCION_ORGANICA_DEMUCS":
        stem_specs.append(("10_Mira_Ninita_Organic_Stems.wav", org_l, org_r))

    stem_paths: List[str] = []
    for filename, s_l, s_r in stem_specs:
        p = write_pcm_wav(stems_dir / filename, s_l, s_r, sample_rate=SAMPLE_RATE, bit_depth=24, dither=False)
        stem_paths.append(str(p))

    # Mezcla suma + consolidación mono < 120 Hz + pre-máster + máster
    mix_l = kick_l + bass_l + perc_l + chords_l + quena_l + charango_l + pad_l + dub_l + tape_l + org_l
    mix_r = kick_r + bass_r + perc_r + chords_r + quena_r + charango_r + pad_r + dub_r + tape_r + org_r
    mix_l, mix_r = enforce_low_end_mono(mix_l, mix_r, cutoff_hz=120.0, sample_rate=SAMPLE_RATE)

    premaster_path = project_dir / "Mira_Ninita_Los_Jaivas_Deep_House_122_PREMASTER.wav"
    master_path = project_dir / "Mira_Ninita_Los_Jaivas_Deep_House_122_MASTER_48k_24b.wav"
    write_pcm_wav(premaster_path, mix_l, mix_r, sample_rate=SAMPLE_RATE, bit_depth=24, dither=False)

    master_res = master_audio_reverse_engineered(
        input_wav=str(premaster_path),
        output_wav=str(master_path),
        profile_name=profile_name,
        bit_depth=24,
    )

    # Export promo 320 kbps CBR MP3 si ffmpeg está disponible
    mp3_path = project_dir / "Mira_Ninita_Los_Jaivas_Deep_House_122_PROMO_320k.mp3"
    mp3_exported: Optional[str] = None
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        ff_proc = subprocess.run(
            [ffmpeg_bin, "-y", "-i", str(master_path), "-b:a", "320k", "-ar", "48000", str(mp3_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if ff_proc.returncode == 0 and mp3_path.exists():
            mp3_exported = str(mp3_path)

    midi_path = project_dir / "Mira_Ninita_Los_Jaivas_Deep_House_122.mid"
    write_multichannel_midi(midi_path, midi_tracks, quena_pitchbends=quena_pitchbends, bpm=BPM)

    flp_path = project_dir / "Mira_Ninita_Los_Jaivas_Deep_House_122.flp"
    flp_res = compile_multitrack_stems_flp(
        stems_dir=str(stems_dir),
        project_title="Mira Ninita - Los Jaivas (C5 Deep House 122 BPM)",
        bpm=BPM,
        output_flp=str(flp_path),
        total_bars=total_bars,
    )

    # Exportar Piano Roll script nativo y escala Scala 5-Limit Just Intonation
    pyscript_local = generate_piano_roll_pyscript(project_dir / "Mira_Ninita_Deep_House_122.pyscript")
    scl_local = project_dir / "mira_ninita_just_c_maj.scl"
    scl_local.write_text(JUST_INTONATION_C_SCL, encoding="utf-8")

    deployed_assets: Dict[str, str] = {}
    if deploy_fl_assets:
        fl_user_dir = resolve_fl_user_dir()
        pr_target = fl_user_dir / "Settings" / "Piano roll scripts" / pyscript_local.name
        scl_target = fl_user_dir / "Settings" / "Tuning" / scl_local.name
        pr_target.parent.mkdir(parents=True, exist_ok=True)
        scl_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pyscript_local, pr_target)
        shutil.copy2(scl_local, scl_target)
        deployed_assets["piano_roll_script"] = str(pr_target)
        deployed_assets["scala_tuning"] = str(scl_target)

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
        if "NATA ACÚSTICA DETECTADA" in rubin_external_out:
            raise RuntimeError(f"Rubin Linter detectó NATA ACÚSTICA:\n{rubin_external_out}")

    # Auditoría interna final sobre el master escrito
    import soundfile as sf

    m_data, m_sr = sf.read(str(master_path), always_2d=True)
    rubin_internal = compute_rubin_metrics(m_data[:, 0], m_data[:, 1], sample_rate=int(m_sr))
    if not rubin_internal["is_pure_bone"]:
        raise RuntimeError(f"Master rechazado por INV_C5_ACOUSTIC_GATE: {rubin_internal}")

    receipt = {
        "status": "SUCCESS",
        "track": "Mira Ninita (Los Jaivas) — C5 Deep House Remix 122 BPM",
        "key": "C Major / Fmaj9 (Fmaj9 -> Cmaj9 -> G6add9 -> G13sus4)",
        "bpm": BPM,
        "sample_rate_hz": SAMPLE_RATE,
        "bit_depth": 24,
        "total_bars": total_bars,
        "false_drop_bar": false_drop_bar + 1,
        "soul_classification": organic_info,
        "zero_crackle_sub_audit": zero_crackle_sub,
        "zero_crackle_lead_audit": zero_crackle_lead,
        "master_wav": str(master_path),
        "master_sha256": _sha256_file(master_path),
        "premaster_wav": str(premaster_path),
        "promo_mp3_320k": mp3_exported,
        "stems_dir": str(stems_dir),
        "stems": stem_paths,
        "midi_file": str(midi_path),
        "flp_file": flp_res["flp_file"],
        "flp_manifest": flp_res["manifest_file"],
        "piano_roll_script": str(pyscript_local),
        "scala_tuning": str(scl_local),
        "deployed_fl_assets": deployed_assets,
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
    parser = argparse.ArgumentParser(description="Mira Niñita (Los Jaivas) — C5-REAL Deep House 122 BPM Remix")
    parser.add_argument("--source-audio", type=str, default=None, help="Ruta a WAV/FLAC/MP3 legítimo para separar con Demucs")
    parser.add_argument("--vocal-stem", type=str, default=None, help="Ruta directa a stem vocal WAV ya separado")
    parser.add_argument("--keep-other", action="store_true", help="Conservar también el stem 'other' de Demucs junto con 'vocals'")
    parser.add_argument("--source-bpm", type=float, default=None, help="BPM manual del audio fuente (opcional)")
    parser.add_argument("--source-tuning-cents", type=float, default=None, help="Desviación de afinación fuente en cents respecto a A4=440 Hz")
    parser.add_argument("--profile", type=str, default="deep_house", help="Perfil de masterización (deep_house, club_c5, streaming_sota)")
    parser.add_argument("--bars", type=int, default=TOTAL_BARS, help="Número de compases (por defecto 64)")
    parser.add_argument("--output-dir", type=str, default=None, help="Directorio de salida raíz (opcional)")
    parser.add_argument("--no-deploy", action="store_true", help="No copiar .pyscript/.scl al directorio de usuario de FL Studio")
    args = parser.parse_args()

    res = build_mira_ninita_deep_house_122(
        source_audio=args.source_audio,
        vocal_stem=args.vocal_stem,
        keep_other=args.keep_other,
        source_bpm_override=args.source_bpm,
        source_tuning_cents=args.source_tuning_cents,
        profile_name=args.profile,
        total_bars=args.bars,
        output_dir=args.output_dir,
        deploy_fl_assets=not args.no_deploy,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
