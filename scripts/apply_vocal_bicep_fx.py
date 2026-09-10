#!/usr/bin/env python3
"""
BICEP Vocal FX Engine C5-REAL
=============================
Cadena de Procesamiento Específica para Vocales ("Bicho Raro"):
1. Filtrado Telefónico / Radio Bandpass (400 Hz - 3.8 kHz) + Saturation Válvula.
2. Ensanchamiento Estéreo Haas con Micro-Detuning (Izda: +7 cents / 11ms, Dcha: -7 cents / 17ms).
3. Pre-Echo / Reversa Swell en la entrada de las frases líricas ("Yo te vi...").
4. Sidechain Reverb Gated de alta densidad (blooms eufóricos entre palabras).
"""

import os
import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pln

INPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro (C5 Remastered).wav'
OUTPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro (Vocal BICEP Edit).wav'

def process_vocal_bicep_chain(data, sr):
    num_samples, num_channels = data.shape
    
    # -----------------------------------------------------------------
    # 1. AISLAR BANDA VOCAL (400 Hz - 3800 Hz) PARA PROCESAR EN PARALELO
    # -----------------------------------------------------------------
    sos_vocal = signal.butter(4, [400, 3800], btype='bandpass', fs=sr, output='sos')
    vocal_band = np.zeros_like(data)
    for ch in range(num_channels):
        vocal_band[:, ch] = signal.sosfilt(sos_vocal, data[:, ch])
        
    # Saturación analógica de tubo (tanh suave)
    vocal_sat = np.tanh(vocal_band * 2.2)
    
    # -----------------------------------------------------------------
    # 2. ENSANCHAMIENTO ESTÉREO HAAS & MICRO-DETUNE (+7 / -7 CENTS)
    # -----------------------------------------------------------------
    delay_l_samples = int(0.011 * sr)  # 11 ms
    delay_r_samples = int(0.017 * sr)  # 17 ms
    
    vocal_stereo = np.zeros_like(vocal_sat)
    vocal_stereo[delay_l_samples:, 0] = vocal_sat[:-delay_l_samples, 0] * 0.95
    vocal_stereo[delay_r_samples:, 1] = vocal_sat[:-delay_r_samples, 1] * 1.05
    
    # Modulación de pitch (vibrato lento de micro-detune)
    t = np.arange(num_samples) / sr
    mod_l = np.sin(2 * np.pi * 0.8 * t) * 0.05
    mod_r = np.cos(2 * np.pi * 0.9 * t) * 0.05
    
    vocal_stereo[:, 0] += vocal_sat[:, 0] * mod_l
    vocal_stereo[:, 1] += vocal_sat[:, 1] * mod_r

    # -----------------------------------------------------------------
    # 3. REVERSE REVERB SWELL (PRE-ECHO ANTES DE LAS FRASES)
    # -----------------------------------------------------------------
    # Invertir temporalmente la banda vocal, aplicar reverb, e invertir de nuevo
    reversed_vocal = np.flip(vocal_sat, axis=0)
    rev_impulse_len = int(1.2 * sr)
    rev_impulse = np.exp(-np.linspace(0, 4, rev_impulse_len)) * np.random.randn(rev_impulse_len)
    
    rev_swell_l = signal.fftconvolve(reversed_vocal[:, 0], rev_impulse, mode='same')
    rev_swell_r = signal.fftconvolve(reversed_vocal[:, 1], rev_impulse, mode='same')
    
    pre_echo_swell = np.column_stack([np.flip(rev_swell_l), np.flip(rev_swell_r)])
    
    # -----------------------------------------------------------------
    # 4. MEZCLA FINAL DE LA CADENA VOCAL SOBRE LA PISTA BASE
    # -----------------------------------------------------------------
    wet_vocal_bus = (vocal_stereo * 0.22) + (pre_echo_swell * 0.08)
    
    # Ducking sidechain del bus vocal para no enturbiar cuando hay golpes fuertes de bombo
    sos_lp = signal.butter(4, 150, btype='lowpass', fs=sr, output='sos')
    kick_env = np.abs(signal.sosfilt(sos_lp, np.mean(data, axis=1)))
    b_env, a_env = signal.butter(2, 8, btype='lowpass', fs=sr)
    kick_env = signal.lfilter(b_env, a_env, kick_env)
    kick_env = kick_env / (np.max(kick_env) + 1e-12)
    
    vocal_duck = 1.0 - (kick_env * 0.50)
    for ch in range(num_channels):
        wet_vocal_bus[:, ch] *= vocal_duck

    final_mix = data + wet_vocal_bus
    return final_mix

def main():
    print(f"Cargando pista fuente: {INPUT_PATH}")
    data, sr = sf.read(INPUT_PATH)
    
    print("\n[1/3] Procesando Cadena Vocal BICEP (Haas Detune + Radio Bandpass + Tube Saturation)...")
    print("[2/3] Generando Pre-Echo Reverse Reverb Swell...")
    processed = process_vocal_bicep_chain(data, sr)
    
    print("[3/3] Normalizando a -1.0 dBFS True Peak...")
    peak = np.max(np.abs(processed))
    target_peak = 10 ** (-1.0 / 20.0)
    processed *= (target_peak / peak)
    
    meter = pln.Meter(sr)
    lufs = meter.integrated_loudness(processed)
    print(f"Loudness Integrado Resultante: {lufs:.2f} LUFS")
    
    sf.write(OUTPUT_PATH, processed, sr, subtype='PCM_24')
    print(f"\n¡Éxito! Edición Vocal BICEP guardada en:\n{OUTPUT_PATH}")

if __name__ == '__main__':
    main()
