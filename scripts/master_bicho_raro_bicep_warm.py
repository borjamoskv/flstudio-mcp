#!/usr/bin/env python3
"""
WARM MASTER BICEP EDIT DSP ENGINE C5-REAL
==========================================
Re-calibración de balance tímbrico analógico cálido (Warm Dark Disco / BICEP style).
- Elimina el realce excesivo de agudos.
- Filtro de suavizado analógico Tape Damping (>12 kHz).
- Tails de Delay/Reverb cálidos con High-Cut en 4.5 kHz.
- Conserva el punch masivo de graves (20-250 Hz), el falso drop en 01:45 y el sidechaining BICEP.
- Target: -12.0 LUFS / -1.0 dBFS True Peak.
"""

import os
import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pln

INPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro.wav'
OUTPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro (WARM BICEP EDIT).wav'

def soft_clipper(x, threshold=0.85):
    """Saturación suave analógica tipo Mastering Soft Clipper."""
    abs_x = np.abs(x)
    return np.where(abs_x <= threshold, x,
                    np.sign(x) * (threshold + (1 - threshold) * np.tanh((abs_x - threshold) / (1 - threshold + 1e-12))))

def main():
    print(f"Cargando master original: {INPUT_PATH}")
    data, sr = sf.read(INPUT_PATH)
    num_samples, num_channels = data.shape

    mix = data.copy()

    # 1. SUAVIZADO DE AGUDOS (Tape High-Frequency Damping >12 kHz)
    print("\n[1/6] Aplicando suavizado analógico de agudos (Damping >12 kHz para sonido cálido)...")
    # Low pass suave a 12.5 kHz para mitigar estridencia y dar calidez de cinta
    sos_warm = signal.butter(2, 12500, btype='lowpass', fs=sr, output='sos')
    for ch in range(num_channels):
        mix[:, ch] = signal.sosfilt(sos_warm, mix[:, ch])

    # 2. FUNDAMENTAL FANTASMA SUAVE (300-700Hz)
    print("[2/6] Excitando armónicos de medios-graves cálidos (300-700Hz)...")
    sos_mid = signal.butter(4, [300, 700], btype='bandpass', fs=sr, output='sos')
    mid_b = np.zeros_like(data)
    for ch in range(num_channels):
        mid_b[:, ch] = signal.sosfilt(sos_mid, data[:, ch])
    mix += np.tanh(mid_b * 1.8) * 0.10

    # 3. TAPE DELAY BICEP CÁLIDO (High-Cut en 4.5 kHz en los tails)
    print("[3/6] Integrando Tape Delay BICEP con filtro cálido (High-Cut 4.5 kHz)...")
    sos_hp = signal.butter(4, [800, 4500], btype='bandpass', fs=sr, output='sos')
    send_sig = np.zeros_like(data)
    for ch in range(num_channels):
        send_sig[:, ch] = signal.sosfilt(sos_hp, mix[:, ch])

    quarter_note_sec = 60.0 / 97.51
    delay_samples = int(quarter_note_sec * 0.75 * sr)
    buf_len = delay_samples + 400
    buf_l, buf_r = np.zeros(buf_len), np.zeros(buf_len)
    ptr = 0
    t = np.arange(num_samples) / sr
    lfo_l = np.sin(2 * np.pi * 2.1 * t) * 12.0
    lfo_r = np.cos(2 * np.pi * 1.9 * t) * 12.0

    delay_bus = np.zeros_like(data)
    for i in range(num_samples):
        r_l = (ptr - (delay_samples + lfo_l[i])) % buf_len
        r_r = (ptr - (delay_samples + lfo_r[i])) % buf_len
        i_l, f_l = int(np.floor(r_l)), r_l - np.floor(r_l)
        i_r, f_r = int(np.floor(r_r)), r_r - np.floor(r_r)
        o_l = (1 - f_l) * buf_l[i_l] + f_l * buf_l[(i_l + 1) % buf_len]
        o_r = (1 - f_r) * buf_r[i_r] + f_r * buf_r[(i_r + 1) % buf_len]
        buf_l[ptr] = send_sig[i, 0] + o_r * 0.32
        buf_r[ptr] = send_sig[i, 1] + o_l * 0.32
        delay_bus[i, 0] = o_l
        delay_bus[i, 1] = o_r
        ptr = (ptr + 1) % buf_len

    # Sidechain Ducking del delay
    sos_lp = signal.butter(4, 150, btype='lowpass', fs=sr, output='sos')
    kick_env = np.abs(signal.sosfilt(sos_lp, np.mean(data, axis=1)))
    b_e, a_e = signal.butter(2, 8, btype='lowpass', fs=sr)
    kick_env = signal.lfilter(b_e, a_e, kick_env)
    kick_env = kick_env / (np.max(kick_env) + 1e-12)

    for ch in range(num_channels):
        delay_bus[:, ch] *= (1.0 - kick_env * 0.60)

    mix += delay_bus * 0.10

    # 4. TRATAMIENTO VOCAL CÁLIDO
    print("[4/6] Añadiendo textura vocal analógica cálida...")
    sos_voc = signal.butter(4, [400, 3000], btype='bandpass', fs=sr, output='sos')
    voc_b = np.zeros_like(data)
    for ch in range(num_channels):
        voc_b[:, ch] = signal.sosfilt(sos_voc, data[:, ch])
    voc_sat = np.tanh(voc_b * 1.8)

    d_l, d_r = int(0.011 * sr), int(0.017 * sr)
    voc_stereo = np.zeros_like(mix)
    voc_stereo[d_l:, 0] = voc_sat[:-d_l, 0] * 0.85
    voc_stereo[d_r:, 1] = voc_sat[:-d_r, 1] * 0.95

    mix += voc_stereo * 0.08

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

    # 6. MASTERING CEILING (-12.0 LUFS / -1.0 dBFS Peak)
    print("[6/6] Ajustando Soft-Clipper analógico y Peak Target -1.0 dBFS...")
    mix = soft_clipper(mix, threshold=0.85)

    meter = pln.Meter(sr)
    current_lufs = meter.integrated_loudness(mix)
    target_lufs = -12.00
    gain_db = target_lufs - current_lufs
    gain_linear = 10 ** (gain_db / 20.0)

    mix *= gain_linear

    peak = np.max(np.abs(mix))
    target_peak = 10 ** (-1.0 / 20.0)
    if peak > target_peak:
        mix = mix * (target_peak / peak)

    final_lufs = meter.integrated_loudness(mix)
    final_peak = 20 * np.log10(np.max(np.abs(mix)))

    print(f"\n==========================================")
    print(f"REMASTER CÁLIDO COMPLETADO CON ÉXITO:")
    print(f"Loudness Integrado Final : {final_lufs:.2f} LUFS")
    print(f"Pico Máximo Final       : {final_peak:.2f} dBFS")
    print(f"==========================================")

    sf.write(OUTPUT_PATH, mix, sr, subtype='PCM_24')
    print(f"Master cálido guardado en:\n{OUTPUT_PATH}")

if __name__ == '__main__':
    main()
