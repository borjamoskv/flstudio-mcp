#!/usr/bin/env python3
"""
BICEP Signature Effect DSP Engine C5-REAL
==========================================
Aplica las firmas sonoras de BICEP (Glue / Atlas / Water):
1. Ping-Pong Delay de 3/16 con LFO Tape Pitch-Warble (LFO Flutter en 2.5 Hz).
2. Sidechain Ducking reactivo sobre el bus del delay (efecto "respiración BICEP").
3. Shimmer Reverb Swell en la transición del breakdown (01:40 - 02:00).
"""

import os
import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pln

INPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro (C5 Remastered).wav'
OUTPUT_PATH = '/Users/borjafernandezangulo/99_CUARENTENA_TERMICA/25_BOCETOS/audio/01_borja_moskv_releases/reworks_and_edits/Borja Moskv - Bicho Raro (BICEP Edit).wav'

def apply_bicep_tape_delay(data, sr, bpm=97.51, wet=0.18):
    """
    Simula el Tape Delay estéreo modulado estilo BICEP (3/16 note delay con pitch flutter)
    y sidechain automático activado por los picos del kick.
    """
    num_samples, num_channels = data.shape
    quarter_note_sec = 60.0 / bpm
    delay_sec = quarter_note_sec * 0.75  # 3/16 delay (~461.5 ms)
    delay_samples_base = int(delay_sec * sr)

    # Extraer banda superior (>1 kHz) para enviar al delay (vocal / synth lead)
    sos_hp = signal.butter(4, 1000, btype='highpass', fs=sr, output='sos')
    send_signal = np.zeros_like(data)
    for ch in range(num_channels):
        send_signal[:, ch] = signal.sosfilt(sos_hp, data[:, ch])

    # LFO de Pitch Modulation (Tape Warble a 2.5 Hz)
    t = np.arange(num_samples) / sr
    lfo_left = np.sin(2 * np.pi * 2.5 * t) * 18.0   # ±18 muestras de flutter
    lfo_right = np.cos(2 * np.pi * 2.1 * t) * 18.0  # Fase cruzada estéreo

    delay_out = np.zeros_like(data)

    # Buffer circular para el delay modulado
    buf_len = delay_samples_base + 500
    buf_l = np.zeros(buf_len)
    buf_r = np.zeros(buf_len)
    ptr = 0

    feedback = 0.42

    for i in range(num_samples):
        # Muestra actual de envío
        in_l = send_signal[i, 0]
        in_r = send_signal[i, 1]

        # Lectura con interpolación lineal (Pitch Warble)
        r_idx_l = (ptr - (delay_samples_base + lfo_left[i])) % buf_len
        r_idx_r = (ptr - (delay_samples_base + lfo_right[i])) % buf_len

        i0_l, frac_l = int(np.floor(r_idx_l)), r_idx_l - np.floor(r_idx_l)
        i0_r, frac_r = int(np.floor(r_idx_r)), r_idx_r - np.floor(r_idx_r)

        out_l = (1 - frac_l) * buf_l[i0_l] + frac_l * buf_l[(i0_l + 1) % buf_len]
        out_r = (1 - frac_r) * buf_r[i0_r] + frac_r * buf_r[(i0_r + 1) % buf_len]

        # Ping-Pong feedback cruzado
        buf_l[ptr] = in_l + out_r * feedback
        buf_r[ptr] = in_r + out_l * feedback

        delay_out[i, 0] = out_l
        delay_out[i, 1] = out_r

        ptr = (ptr + 1) % buf_len

    # Sidechain Ducking automático por envolvente de graves (Kick Envelope)
    sos_lp = signal.butter(4, 150, btype='lowpass', fs=sr, output='sos')
    low_env = np.abs(signal.sosfilt(sos_lp, np.mean(data, axis=1)))
    # Suavizar envolvente
    b_env, a_env = signal.butter(2, 10, btype='lowpass', fs=sr)
    low_env = signal.lfilter(b_env, a_env, low_env)
    low_env = low_env / (np.max(low_env) + 1e-12)

    # Ducking: reducir delay cuando el kick está presente
    duck_gain = 1.0 - (low_env * 0.70)
    duck_gain = np.clip(duck_gain, 0.30, 1.0)

    for ch in range(num_channels):
        delay_out[:, ch] *= duck_gain

    return data + delay_out * wet

def apply_bicep_breakdown_shimmer(data, sr, t_start=95.0, t_end=120.0):
    """Crea una atmósfera euforica Shimmer Riser en el breakdown (01:35 - 02:00)."""
    idx_start = int(t_start * sr)
    idx_end = int(t_end * sr)
    segment_len = idx_end - idx_start

    # Transposición octava arriba (+12 semitono) simulada mediante interpolación rápida
    sos_bp = signal.butter(4, [800, 4000], btype='bandpass', fs=sr, output='sos')
    bp_sig = signal.sosfilt(sos_bp, np.mean(data[idx_start:idx_end], axis=1))

    # Shimmer reverb tail largo
    reverb_tail_len = int(2.0 * sr)
    impulse = np.exp(-np.linspace(0, 5, reverb_tail_len)) * np.random.randn(reverb_tail_len)
    shimmer = signal.fftconvolve(bp_sig, impulse, mode='same')

    # Envolvente exponencial de riser
    riser_env = np.linspace(0, 1, segment_len) ** 2.5
    shimmer_stereo = np.column_stack([shimmer * riser_env, np.roll(shimmer, 200) * riser_env])

    output = data.copy()
    output[idx_start:idx_end] += shimmer_stereo * 0.15
    return output

def main():
    print(f"Cargando audio remasterizado: {INPUT_PATH}")
    data, sr = sf.read(INPUT_PATH)

    print("\n[1/3] Generando Tape Delay Modulado BICEP (3/16 Ping-Pong + Pitch Flutter)...")
    with_delay = apply_bicep_tape_delay(data, sr)

    print("[2/3] Construyendo Shimmer Riser Eufórico en Breakdown (01:35 - 02:00)...")
    final_edit = apply_bicep_breakdown_shimmer(with_delay, sr)

    print("[3/3] Normalizando a True Peak -1.0 dBFS...")
    peak = np.max(np.abs(final_edit))
    target_peak = 10 ** (-1.0 / 20.0)
    final_edit *= (target_peak / peak)

    meter = pln.Meter(sr)
    lufs = meter.integrated_loudness(final_edit)
    print(f"Loudness Resultante: {lufs:.2f} LUFS")

    sf.write(OUTPUT_PATH, final_edit, sr, subtype='PCM_24')
    print(f"\n¡Éxito! BICEP Edit generado en:\n{OUTPUT_PATH}")

if __name__ == '__main__':
    main()
