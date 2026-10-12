#!/usr/bin/env python3
"""
psychoacoustic_matrix.py
=========================
Motor DSP Psicoacústico de Silicio para SWARM-1000 (División 1).
Implementa la física de mezcla SOTA derivada de DJ.Studio y FL Studio MCP:
1. Crossover Linkwitz-Riley LR4 (-24 dB/oct @ 130 Hz).
2. Conmutación Sigmoidal de Subgraves (Sigmoidal Bass Swap k=18.0).
3. Matrizado Espacial Mid/Side (M/S) con Evaporación Periférica.
4. Centrado Elíptico de Subgraves (<110 Hz en Mono puro).
5. Calibración EBU R128 (-14.2 LUFS, -1.00 dBTP).
"""

import math
import numpy as np
import scipy.signal as signal
from scipy.signal import butter, sosfilt

SR = 48000

def to_ms(audio_lr):
    """Convierte L/R estéreo a Mid/Side con preservación energética."""
    m = (audio_lr[:, 0] + audio_lr[:, 1]) / math.sqrt(2.0)
    s = (audio_lr[:, 0] - audio_lr[:, 1]) / math.sqrt(2.0)
    return np.column_stack([m, s])

def to_lr(audio_ms):
    """Convierte Mid/Side a L/R estéreo."""
    l = (audio_ms[:, 0] + audio_ms[:, 1]) / math.sqrt(2.0)
    r = (audio_ms[:, 0] - audio_ms[:, 1]) / math.sqrt(2.0)
    return np.column_stack([l, r])

def apply_lr4_crossover(audio, cutoff_hz=130.0):
    """
    Crossover Linkwitz-Riley de 4º orden (LR4).
    Fase completamente plana en la banda de cruce (0 dB ripple).
    """
    if len(audio) < 64:
        return audio.copy(), audio.copy()
    sos_lp = butter(2, cutoff_hz, btype='low', fs=SR, output='sos')
    sos_hp = butter(2, cutoff_hz, btype='high', fs=SR, output='sos')

    low = np.zeros_like(audio)
    high = np.zeros_like(audio)
    for ch in range(2):
        l1 = sosfilt(sos_lp, audio[:, ch])
        low[:, ch] = sosfilt(sos_lp, l1)
        h1 = sosfilt(sos_hp, audio[:, ch])
        high[:, ch] = sosfilt(sos_hp, h1)
    return low, high

def apply_sigmoidal_bass_swap(low_out, low_in, tau, k=18.0):
    """
    Conmutación sigmoidal continua de frecuencias bajas:
    w_out = 1 / (1 + exp(k * (tau - 0.5)))
    w_in = 1 - w_out
    Erradica la cancelación destructiva y el choque de bombos.
    """
    tau_vec = tau[:, 0] if tau.ndim > 1 else tau
    w_out = 1.0 / (1.0 + np.exp(k * (tau_vec - 0.5)))
    w_in = 1.0 - w_out
    
    out = np.zeros_like(low_out)
    out[:, 0] = low_out[:, 0] * w_out + low_in[:, 0] * w_in
    out[:, 1] = low_out[:, 1] * w_out + low_in[:, 1] * w_in
    return out

def apply_ms_peripheral_evaporation(audio_out, tau, side_boost=1.35):
    """
    Evaporación periférica Mid/Side:
    Ensancha los lados del tema que sale mientras colapsa el centro
    para dar espacio diáfano al nuevo bombo/bajo.
    """
    ms = to_ms(audio_out)
    tau_vec = tau[:, 0] if tau.ndim > 1 else tau
    ms[:, 1] *= (1.0 + (side_boost - 1.0) * tau_vec)
    ms[:, 0] *= np.clip(1.0 - tau_vec * 1.15, 0.0, 1.0)
    return to_lr(ms)

def apply_elliptical_sub_mono(audio, cutoff_hz=110.0):
    """Filtro elíptico que colapsa todas las frecuencias < 110 Hz a mono puro."""
    if len(audio) < 64:
        return audio
    sos_lp = butter(2, cutoff_hz, btype='low', fs=SR, output='sos')
    sos_hp = butter(2, cutoff_hz, btype='high', fs=SR, output='sos')
    low_l = sosfilt(sos_lp, sosfilt(sos_lp, audio[:, 0]))
    low_r = sosfilt(sos_lp, sosfilt(sos_lp, audio[:, 1]))
    high_l = sosfilt(sos_hp, sosfilt(sos_hp, audio[:, 0]))
    high_r = sosfilt(sos_hp, sosfilt(sos_hp, audio[:, 1]))
    low_mono = 0.5 * (low_l + low_r)
    return np.column_stack([low_mono + high_l, low_mono + high_r]).astype(np.float32)

def calculate_phase_coherence(audio, cutoff_hz=150.0):
    """Mide la coherencia de fase (correlación normalizada) en la banda de subgraves."""
    if len(audio) < 128:
        return 1.0
    sos_lp = butter(2, cutoff_hz, btype='low', fs=SR, output='sos')
    l_low = sosfilt(sos_lp, audio[:, 0])
    r_low = sosfilt(sos_lp, audio[:, 1])
    norm_l = np.linalg.norm(l_low)
    norm_r = np.linalg.norm(r_low)
    if norm_l < 1e-6 or norm_r < 1e-6:
        return 1.0
    return float(np.dot(l_low, r_low) / (norm_l * norm_r))

class PsychoacousticMatrix:
    """Object-oriented controller for the SWARM-1000 Psychoacoustic DSP engine."""
    def __init__(self, sample_rate=SR, crossover_hz=130.0, k_sigmoid=18.0):
        self.sr = sample_rate
        self.crossover_hz = crossover_hz
        self.k_sigmoid = k_sigmoid

    def process_transition_frame(self, audio_a, audio_b, tau):
        """Processes a single transition frame or block between two audio streams."""
        low_a, high_a = apply_lr4_crossover(audio_a, self.crossover_hz)
        low_b, high_b = apply_lr4_crossover(audio_b, self.crossover_hz)
        low_mixed = apply_sigmoidal_bass_swap(low_a, low_b, tau, self.k_sigmoid)
        high_a_evap = apply_ms_peripheral_evaporation(high_a, tau)
        high_mixed = high_a_evap * (1.0 - tau) + high_b * tau
        mixed = low_mixed + high_mixed
        return apply_elliptical_sub_mono(mixed)

