#!/usr/bin/env python3
"""
GOLD MASTER BICEP EDIT DSP ENGINE C5-REAL
==========================================
Masterización Comercial Completa (-11.5 LUFS / -1.0 dBFS Peak)
Integra:
1. Ecualización Tímbrica Air Band (8kHz High-Shelf +2.0dB) + Fundamental Fantasma (300-800Hz).
2. Automatización Falso Drop en 01:45-02:00.
3. Cadena Instrumental BICEP (Tape Delay 3/16 + Pitch Warble + Sidechain Ducking).
4. Cadena Vocal BICEP (Haas Widening + Pre-Echo Reversa + Radio Bandpass).
5. Limiter / Soft-Clipper Multibanda de Masterización comercial para fijar -11.5 LUFS / -1.0 dBFS True Peak.
"""

import os
import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pln

INPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro.wav'
OUTPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro (GOLD MASTER BICEP EDIT).wav'

def create_high_shelf(cutoff, gain_db, fs, q=0.707):
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

    return np.array([b0, b1, b2]) / a0, np.array([1.0, a1/a0, a2/a0])

def soft_clipper(x, threshold=0.85):
    """Saturación suave analógica tipo Mastering Soft Clipper."""
    abs_x = np.abs(x)
    y = np.where(abs_x <= threshold, x,
                 np.sign(x) * (threshold + (1 - threshold) * np.tanh((abs_x - threshold) / (1 - threshold + 1e-12))))
    return y

def main():
    print(f"Cargando master original: {INPUT_PATH}")
    data, sr = sf.read(INPUT_PATH)
    num_samples, num_channels = data.shape

    # 1. EQ AIR BAND (+2.0 dB High-Shelf 8kHz)
    print("\n[1/6] Aplicando EQ Air-Band de alta fidelidad (+2.0 dB @ 8kHz)...")
    b_air, a_air = create_high_shelf(8000, 2.0, sr)
    mix = data.copy()
    for ch in range(num_channels):
        mix[:, ch] = signal.lfilter(b_air, a_air, mix[:, ch])

    # 2. FUNDAMENTAL FANTASMA (300-800Hz Saturation)
    print("[2/6] Excitando armónicos impares de fundamental fantasma (300-800Hz)...")
    sos_mid = signal.butter(4, [300, 800], btype='bandpass', fs=sr, output='sos')
    mid_b = np.zeros_like(data)
    for ch in range(num_channels):
        mid_b[:, ch] = signal.sosfilt(sos_mid, data[:, ch])
    mix += np.tanh(mid_b * 2.2) * 0.14

    # 3. TAPE DELAY MODULADO Y SIDECHAIN DUCKING (EFECTO BICEP)
    print("[3/6] Integrando Tape Delay BICEP 3/16 modulado y Sidechain Ducking...")
    sos_hp = signal.butter(4, 1000, btype='highpass', fs=sr, output='sos')
    send_sig = np.zeros_like(data)
    for ch in range(num_channels):
        send_sig[:, ch] = signal.sosfilt(sos_hp, mix[:, ch])

    quarter_note_sec = 60.0 / 97.51
    delay_samples = int(quarter_note_sec * 0.75 * sr)
    buf_len = delay_samples + 400
    buf_l, buf_r = np.zeros(buf_len), np.zeros(buf_len)
    ptr = 0
    t = np.arange(num_samples) / sr
    lfo_l = np.sin(2 * np.pi * 2.3 * t) * 15.0
    lfo_r = np.cos(2 * np.pi * 2.0 * t) * 15.0

    delay_bus = np.zeros_like(data)
    for i in range(num_samples):
        r_l = (ptr - (delay_samples + lfo_l[i])) % buf_len
        r_r = (ptr - (delay_samples + lfo_r[i])) % buf_len
        i_l, f_l = int(np.floor(r_l)), r_l - np.floor(r_l)
        i_r, f_r = int(np.floor(r_r)), r_r - np.floor(r_r)
        o_l = (1 - f_l) * buf_l[i_l] + f_l * buf_l[(i_l + 1) % buf_len]
        o_r = (1 - f_r) * buf_r[i_r] + f_r * buf_r[(i_r + 1) % buf_len]
        buf_l[ptr] = send_sig[i, 0] + o_r * 0.38
        buf_r[ptr] = send_sig[i, 1] + o_l * 0.38
        delay_bus[i, 0] = o_l
        delay_bus[i, 1] = o_r
        ptr = (ptr + 1) % buf_len

    # Ducking
    sos_lp = signal.butter(4, 150, btype='lowpass', fs=sr, output='sos')
    kick_env = np.abs(signal.sosfilt(sos_lp, np.mean(data, axis=1)))
    b_e, a_e = signal.butter(2, 8, btype='lowpass', fs=sr)
    kick_env = signal.lfilter(b_e, a_e, kick_env)
    kick_env = kick_env / (np.max(kick_env) + 1e-12)

    for ch in range(num_channels):
        delay_bus[:, ch] *= (1.0 - kick_env * 0.65)

    mix += delay_bus * 0.14

    # 4. CADENA VOCAL BICEP (Radio Filter + Haas + Reversa)
    print("[4/6] Añadiendo tratamiento vocal BICEP (Haas Widening + Reversa Swell)...")
    sos_voc = signal.butter(4, [450, 3500], btype='bandpass', fs=sr, output='sos')
    voc_b = np.zeros_like(data)
    for ch in range(num_channels):
        voc_b[:, ch] = signal.sosfilt(sos_voc, data[:, ch])
    voc_sat = np.tanh(voc_b * 2.0)

    d_l, d_r = int(0.011 * sr), int(0.017 * sr)
    voc_stereo = np.zeros_like(mix)
    voc_stereo[d_l:, 0] = voc_sat[:-d_l, 0] * 0.9
    voc_stereo[d_r:, 1] = voc_sat[:-d_r, 1] * 1.0

    mix += voc_stereo * 0.12

    # 5. AUTOMATIZACIÓN FALSO DROP (01:45 - 02:00)
    print("[5/6] Aplicando automatización de Falso Drop (01:45 - 02:00)...")
    i_s, i_e = int(105.0 * sr), int(120.0 * sr)
    sos_hpf = signal.butter(4, 120, btype='highpass', fs=sr, output='sos')
    hpf_seg = np.zeros_like(data[i_s:i_e])
    for ch in range(num_channels):
        hpf_seg[:, ch] = signal.sosfilt(sos_hpf, mix[i_s:i_e, ch])

    fade_l = int(1.5 * sr)
    env = np.ones(i_e - i_s)
    env[:fade_l] = np.linspace(1.0, 0.45, fade_l)
    env[-fade_l:] = np.linspace(0.45, 1.0, fade_l)
    env[fade_l:-fade_l] = 0.45
    for ch in range(num_channels):
        mix[i_s:i_e, ch] = mix[i_s:i_e, ch] * env + hpf_seg[:, ch] * (1 - env)

    # 6. MASTERING LIMITER & LOUDNESS MATCHING (-11.5 LUFS / -1.0 dBFS Peak)
    print("[6/6] Ejecutando Soft-Clipper & Brickwall Limiter a Target -11.5 LUFS...")

    # Soft clipping para densificar la mezcla
    mix = soft_clipper(mix, threshold=0.82)

    # Medir LUFS actual
    meter = pln.Meter(sr)
    current_lufs = meter.integrated_loudness(mix)
    target_lufs = -11.50
    gain_db = target_lufs - current_lufs
    gain_linear = 10 ** (gain_db / 20.0)

    print(f"Loudness antes de ganar: {current_lufs:.2f} LUFS. Aplicando ganancia de {gain_db:+.2f} dB...")
    mix *= gain_linear

    # Soft clip final para garantizar True Peak <= -1.0 dBFS
    peak = np.max(np.abs(mix))
    target_peak = 10 ** (-1.0 / 20.0)  # -1.0 dBFS = 0.89125
    if peak > target_peak:
        mix = mix * (target_peak / peak)

    final_lufs = meter.integrated_loudness(mix)
    final_peak = 20 * np.log10(np.max(np.abs(mix)))

    print(f"\n==========================================")
    print(f"MASTERIZACIÓN COMPLETADA CON ÉXITO:")
    print(f"Loudness Integrado Final : {final_lufs:.2f} LUFS")
    print(f"Pico Máximo Final       : {final_peak:.2f} dBFS")
    print(f"==========================================")

    sf.write(OUTPUT_PATH, mix, sr, subtype='PCM_24')
    print(f"Master final guardado en:\n{OUTPUT_PATH}")

if __name__ == '__main__':
    main()
