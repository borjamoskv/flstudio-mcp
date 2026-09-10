#!/usr/bin/env python3
"""
WET BICEP EDIT DSP ENGINE C5-REAL ("MÁS HUMEDAD")
=================================================
Inyección de Humedad / Densidad Ambiental Líquida (Lush Wet Reverb & Delay Space):
- Generador de Reverb Hall Densidad Líquida (4.8s de decay, High-Cut en 3.8 kHz).
- Matriz M/S para expansión estéreo del tail húmedo (+35% Side Width).
- Sidechain Ducking agresivo (-85%) sobre la masa de humedad para mantener el Kick/Bass 100% seco y punzante.
- Mantiene la calidez tímbrica analógica (Tape Damping >12 kHz).
- Target: -12.0 LUFS / -1.0 dBFS True Peak.
"""

import os
import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pln

INPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro.wav'
OUTPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro (WET BICEP EDIT).wav'

def soft_clipper(x, threshold=0.85):
    abs_x = np.abs(x)
    return np.where(abs_x <= threshold, x,
                    np.sign(x) * (threshold + (1 - threshold) * np.tanh((abs_x - threshold) / (1 - threshold + 1e-12))))

def main():
    print(f"Cargando master original: {INPUT_PATH}")
    data, sr = sf.read(INPUT_PATH)
    num_samples, num_channels = data.shape

    mix = data.copy()

    # 1. SUAVIZADO TAPE DAMPING (>12 kHz)
    sos_warm = signal.butter(2, 12000, btype='lowpass', fs=sr, output='sos')
    for ch in range(num_channels):
        mix[:, ch] = signal.sosfilt(sos_warm, mix[:, ch])

    # 2. FUNDAMENTAL FANTASMA SUAVE (300-700Hz)
    sos_mid = signal.butter(4, [300, 700], btype='bandpass', fs=sr, output='sos')
    mid_b = np.zeros_like(data)
    for ch in range(num_channels):
        mid_b[:, ch] = signal.sosfilt(sos_mid, data[:, ch])
    mix += np.tanh(mid_b * 1.8) * 0.10

    # 3. GENERADOR DE "HUMEDAD" (LUSH WET AMBIENT REVERB - 4.8s Decay)
    print("\n[1/5] Inyectando Reverb Ambiental de Alta Densidad ('Humedad Líquida')...")
    sos_hp_rev = signal.butter(4, 500, btype='highpass', fs=sr, output='sos')
    rev_send = np.zeros_like(data)
    for ch in range(num_channels):
        rev_send[:, ch] = signal.sosfilt(sos_hp_rev, mix[:, ch])

    # Generar respuesta al impulso de Hall denso (4.8 segundos de decay)
    rev_len = int(4.8 * sr)
    t_rev = np.linspace(0, 4.8, rev_len)
    
    # Envolvente de difusión orgánica con difusión de fase
    env_rev = np.exp(-t_rev * 1.8)
    impulse_l = env_rev * np.random.randn(rev_len)
    impulse_r = env_rev * np.random.randn(rev_len)

    # Filtrar el tail de reverb para que la humedad sea cálida y no brillante (High-cut 3.8 kHz)
    sos_rev_lp = signal.butter(2, 3800, btype='lowpass', fs=sr, output='sos')
    impulse_l = signal.sosfilt(sos_rev_lp, impulse_l)
    impulse_r = signal.sosfilt(sos_rev_lp, impulse_r)

    # Convolución FFT para crear el Tail de Humedad
    wet_l = signal.fftconvolve(rev_send[:, 0], impulse_l, mode='same')
    wet_r = signal.fftconvolve(rev_send[:, 1], impulse_r, mode='same')
    wet_reverb = np.column_stack([wet_l, wet_r])

    # M/S Expansion en el bus de humedad (abrir Sides un +35%)
    wet_mid = (wet_reverb[:, 0] + wet_reverb[:, 1]) / 2.0
    wet_side = (wet_reverb[:, 0] - wet_reverb[:, 1]) / 2.0
    wet_side *= 1.35
    wet_reverb[:, 0] = wet_mid + wet_side
    wet_reverb[:, 1] = wet_mid - wet_side

    # 4. TAPE DELAY BICEP 3/16 MODULADO
    print("[2/5] Añadiendo Tape Delay modulado estilo BICEP...")
    sos_hp_del = signal.butter(4, [800, 4000], btype='bandpass', fs=sr, output='sos')
    send_sig = np.zeros_like(data)
    for ch in range(num_channels):
        send_sig[:, ch] = signal.sosfilt(sos_hp_del, mix[:, ch])

    quarter_note_sec = 60.0 / 97.51
    delay_samples = int(quarter_note_sec * 0.75 * sr)
    buf_len = delay_samples + 400
    buf_l, buf_r = np.zeros(buf_len), np.zeros(buf_len)
    ptr = 0
    t = np.arange(num_samples) / sr
    lfo_l = np.sin(2 * np.pi * 2.1 * t) * 14.0
    lfo_r = np.cos(2 * np.pi * 1.9 * t) * 14.0

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

    # 5. SIDECHAIN DUCKING MASIVO SOBRE LA HUMEDAD (REVERB + DELAY)
    print("[3/5] Aplicando Sidechain Ducking reactivo (-85%) sobre la masa de humedad...")
    sos_lp = signal.butter(4, 150, btype='lowpass', fs=sr, output='sos')
    kick_env = np.abs(signal.sosfilt(sos_lp, np.mean(data, axis=1)))
    b_e, a_e = signal.butter(2, 8, btype='lowpass', fs=sr)
    kick_env = signal.lfilter(b_e, a_e, kick_env)
    kick_env = kick_env / (np.max(kick_env) + 1e-12)

    # Ducking profundo
    duck_gain = 1.0 - (kick_env * 0.85)
    duck_gain = np.clip(duck_gain, 0.15, 1.0)

    for ch in range(num_channels):
        wet_reverb[:, ch] *= duck_gain
        delay_bus[:, ch] *= duck_gain

    # Sumar bus de humedad (Reverb 22% + Delay 12%)
    mix += (wet_reverb * 0.22) + (delay_bus * 0.12)

    # 6. AUTOMATIZACIÓN FALSO DROP (01:45 - 02:00)
    print("[4/5] Aplicando automatización de Falso Drop (01:45 - 02:00)...")
    i_s, i_e = int(105.0 * sr), int(120.0 * sr)
    sos_hpf = signal.butter(4, 120, btype='highpass', fs=sr, output='sos')
    hpf_seg = np.zeros_like(data[i_s:i_e])
    for ch in range(num_channels):
        hpf_seg[:, ch] = signal.sosfilt(sos_hpf, mix[i_s:i_e, ch])

    fade_l = int(1.5 * sr)
    env = np.ones(i_e - i_s)
    env[:fade_l] = np.linspace(1.0, 0.40, fade_l)
    env[-fade_l:] = np.linspace(0.40, 1.0, fade_l)
    env[fade_l:-fade_l] = 0.40
    for ch in range(num_channels):
        mix[i_s:i_e, ch] = mix[i_s:i_e, ch] * env + hpf_seg[:, ch] * (1 - env)

    # 7. MASTERING CEILING (-12.0 LUFS / -1.0 dBFS Peak)
    print("[5/5] Ajustando Soft-Clipper analógico y Target -12.0 LUFS...")
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
    print(f"REMASTER CON MÁS HUMEDAD COMPLETADO CON ÉXITO:")
    print(f"Loudness Integrado Final : {final_lufs:.2f} LUFS")
    print(f"Pico Máximo Final       : {final_peak:.2f} dBFS")
    print(f"==========================================")

    sf.write(OUTPUT_PATH, mix, sr, subtype='PCM_24')
    print(f"Master húmedo guardado en:\n{OUTPUT_PATH}")

if __name__ == '__main__':
    main()
