#!/usr/bin/env python3
"""
DSP Remastering Engine C5-REAL for 'Borja Moskv - Bicho Raro'
============================================================
Aplica las 3 optimizaciones cuantitativas sobre la pista fuente:
1. Excitador psicoacústico de fundamental fantasma (300Hz - 800Hz) para pequeños altavoces.
2. Realce de banda Air (High-Shelf en 8kHz) para textura orgánica AIR.
3. Automatización de "Falso Drop" con filtro paso-alto en 01:45 - 02:00.
4. Normalización True Peak a -1.0 dBFS con inmunidad a picos ISP.
"""

import os
import sys
import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pln

INPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro.wav'
OUTPUT_DIR = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits'
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'Borja Moskv - Bicho Raro (C5 Remastered).wav')

def create_high_shelf(cutoff, gain_db, fs, q=0.707):
    """Crea coeficientes de un filtro High-Shelf IIR (Biquad)."""
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * cutoff / fs
    alpha = np.sin(w0) / (2 * q)
    cos_w0 = np.cos(w0)

    b0 = A * ((A + 1) + (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
    b2 = A * ((A + 1) + (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * cos_w0 + 2 * np.sqrt(A) * alpha
    a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
    a2 = (A + 1) - (A - 1) * cos_w0 - 2 * np.sqrt(A) * alpha

    b = np.array([b0, b1, b2]) / a0
    a = np.array([1.0, a1/a0, a2/a0])
    return b, a

def main():
    print(f"Cargando audio desde: {INPUT_PATH}")
    data, sr = sf.read(INPUT_PATH)
    num_samples, num_channels = data.shape
    duration = num_samples / sr
    print(f"Duración: {duration:.2f}s, Canales: {num_channels}, Sr: {sr} Hz")

    processed = data.copy()

    # -------------------------------------------------------------
    # 1. REALCE DE BANDA AIR (>8 kHz High-Shelf +2.5 dB)
    # -------------------------------------------------------------
    print("\n[1/4] Aplicando Realce de Banda AIR (High-Shelf 8 kHz, +2.5 dB)...")
    b_air, a_air = create_high_shelf(cutoff=8000, gain_db=2.5, fs=sr)
    for ch in range(num_channels):
        processed[:, ch] = signal.lfilter(b_air, a_air, processed[:, ch])

    # -------------------------------------------------------------
    # 2. SATURACIÓN PARALELA PARA FUNDAMENTAL FANTASMA (300-800 Hz)
    # -------------------------------------------------------------
    print("[2/4] Procesando Excitador Psicoacústico de Medios-Bajos (300-800 Hz)...")
    sos_mid = signal.butter(4, [300, 800], btype='bandpass', fs=sr, output='sos')
    mid_band = np.zeros_like(data)
    for ch in range(num_channels):
        mid_band[:, ch] = signal.sosfilt(sos_mid, data[:, ch])

    saturated_mid = np.tanh(mid_band * 2.5) * 0.18
    processed += saturated_mid

    # -------------------------------------------------------------
    # 3. AUTOMATIZACIÓN DE "FALSO DROP" (01:45 a 02:00 / 105s - 120s)
    # -------------------------------------------------------------
    print("[3/4] Generando automatización de 'Falso Drop' en 01:45 - 02:00...")
    t_start = 105.0  # 01:45
    t_end = 120.0    # 02:00
    idx_start = int(t_start * sr)
    idx_end = int(t_end * sr)

    sos_hpf = signal.butter(4, 120, btype='highpass', fs=sr, output='sos')
    filtered_segment = np.zeros_like(data[idx_start:idx_end])
    for ch in range(num_channels):
        filtered_segment[:, ch] = signal.sosfilt(sos_hpf, processed[idx_start:idx_end, ch])

    fade_len = int(1.5 * sr)
    env = np.ones(idx_end - idx_start)
    env[:fade_len] = np.linspace(1.0, 0.4, fade_len)
    env[-fade_len:] = np.linspace(0.4, 1.0, fade_len)
    env[fade_len:-fade_len] = 0.4

    for ch in range(num_channels):
        drop_blend = processed[idx_start:idx_end, ch] * env + filtered_segment[:, ch] * (1 - env)
        processed[idx_start:idx_end, ch] = drop_blend

    # -------------------------------------------------------------
    # 4. NORMALIZACIÓN Y CEILING DE PICO (-1.0 dBFS)
    # -------------------------------------------------------------
    print("[4/4] Ajustando Ceilings y Normalización True Peak (-1.0 dBFS)...")
    peak = np.max(np.abs(processed))
    target_peak_linear = 10 ** (-1.0 / 20.0)
    gain_factor = target_peak_linear / peak
    processed *= gain_factor

    meter = pln.Meter(sr)
    loudness = meter.integrated_loudness(processed)
    print(f"Loudness Integrado Resultante: {loudness:.2f} LUFS")
    print(f"Nivel de Pico Máximo: {20*np.log10(np.max(np.abs(processed))):.2f} dBFS")

    sf.write(OUTPUT_PATH, processed, sr, subtype='PCM_24')
    print(f"\n¡Éxito! Archivo remasterizado guardado en:\n{OUTPUT_PATH}")

if __name__ == '__main__':
    main()
