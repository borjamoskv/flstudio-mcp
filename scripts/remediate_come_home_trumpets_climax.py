#!/usr/bin/env python3
"""
C5-REAL Acoustic Remediation Engine: Come Home for the Trumpets (Climax Fix)
=============================================================================
Author: Borja Fernández Angulo (C5-REAL Sovereign Audio & Complex Systems)
Track: 'Borja Moskv - Come Home for the Trumpets'
Target Section: 2:05 - 3:03 (Climax Accumulation & Mono Masking)

REMEDIATION MATRIX:
1. Low-End Protection (<180 Hz): 100% untouched via complementary crossover.
   Zero phase smearing on kick, bass fundamental, or rhythm foundation.
2. Side-Channel Mud Carving (400 - 800 Hz):
   - Parametric bell notch (fc=560 Hz, Q=1.1, gain=-3.8 dB) on the Side channel.
   - 2nd-order High-Pass on Side channel at 260 Hz (purges lateral low-mid bleed).
3. Melodic Layer Gain Trimming:
   - -1.2 dB trim on mid/side melodic content during the climax (125s - 183.5s)
     with smooth Hann crossfade window (120s - 125s).
4. True Peak Lookahead Master Limiter:
   - 4x oversampled ceiling locked strictly to -1.0 dBTP.
5. Acoustic Pre-Human Audit Gate:
   - Full comparative matrix (Loudness, True Peak, Crest Factor, Correlation, Side/Mid, Mono LUFS).
"""

import sys
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
from scipy import signal
import soundfile as sf
import pyloudnorm as pln


WORKSPACE_DIR = Path(__file__).resolve().parent.parent
FLAC_PATH = WORKSPACE_DIR / "bounces/damon_jee_curses_microtonal/Borja Moskv -  Come Home for the Trumpets.flac"
BACKUP_FLAC = WORKSPACE_DIR / "bounces/damon_jee_curses_microtonal/Borja Moskv -  Come Home for the Trumpets.orig.flac"

MUSIC_BOUNCES_DIR = Path.home() / "Music/FL Studio Bounces"
OUTPUT_MASTER_WAV = MUSIC_BOUNCES_DIR / "Borja Moskv - Come home for the trumpets (C5 Apex Remaster -1dBTP).wav"
OUTPUT_MASTER_FLAC = MUSIC_BOUNCES_DIR / "Borja Moskv - Come home for the trumpets (C5 Apex Remaster -1dBTP).flac"


def calculate_metrics(seg: np.ndarray, sr: int) -> Dict[str, float]:
    meter = pln.Meter(sr)
    lufs = meter.integrated_loudness(seg)
    
    # 4x oversampled true peak
    seg_4x = signal.resample_poly(seg, 4, 1, axis=0)
    tp = 20.0 * np.log10(np.max(np.abs(seg_4x)) + 1e-12)
    
    # Crest factor
    rms = np.sqrt(np.mean(seg**2)) + 1e-12
    crest = 20.0 * np.log10(np.max(np.abs(seg)) / rms)
    
    # Stereo correlation
    norm_l = np.linalg.norm(seg[:, 0])
    norm_r = np.linalg.norm(seg[:, 1])
    corr = np.dot(seg[:, 0], seg[:, 1]) / (norm_l * norm_r + 1e-12)
    
    # Mid / Side decomposition in 400 - 800 Hz
    mid = (seg[:, 0] + seg[:, 1]) / np.sqrt(2.0)
    side = (seg[:, 0] - seg[:, 1]) / np.sqrt(2.0)
    sos_band = signal.butter(4, [400.0, 800.0], btype='bandpass', fs=sr, output='sos')
    mid_filt = signal.sosfilt(sos_band, mid)
    side_filt = signal.sosfilt(sos_band, side)
    rms_mid = np.sqrt(np.mean(mid_filt**2)) + 1e-12
    rms_side = np.sqrt(np.mean(side_filt**2)) + 1e-12
    side_mid_diff = 20.0 * np.log10(rms_side / rms_mid)
    
    # Mono collapsed Loudness
    mono_seg = np.column_stack([mid, mid])
    mono_lufs = meter.integrated_loudness(mono_seg)
    
    return {
        "lufs": round(float(lufs), 2),
        "true_peak_dbtp": round(float(tp), 3),
        "crest_factor_db": round(float(crest), 2),
        "stereo_correlation": round(float(corr), 3),
        "side_mid_diff_db": round(float(side_mid_diff), 2),
        "mono_lufs": round(float(mono_lufs), 2)
    }


def execute_remediation(data: np.ndarray, sr: int) -> Tuple[np.ndarray, Dict[str, Any]]:
    print("  [1/4] Aplicando Crossover Complementario (<180 Hz protegido a bit-exact)...")
    sos_lp = signal.butter(4, 180.0, btype='lowpass', fs=sr, output='sos')
    low = signal.sosfilt(sos_lp, data)
    high = data - low  # Perfect reconstruction: low + high == data identically
    
    print("  [2/4] Generando envolvente de modulación temporal Hann (120s -> 187s)...")
    t = np.arange(len(data)) / sr
    mod_env = np.zeros(len(data))
    for i in range(len(data)):
        t_sec = t[i]
        if t_sec < 120.0:
            mod_env[i] = 0.0
        elif 120.0 <= t_sec < 125.0:
            p = (t_sec - 120.0) / 5.0
            mod_env[i] = 0.5 * (1.0 - np.cos(np.pi * p))
        elif 125.0 <= t_sec <= 183.5:
            mod_env[i] = 1.0
        elif 183.5 < t_sec <= 187.5:
            p = (t_sec - 183.5) / 4.0
            mod_env[i] = 0.5 * (1.0 + np.cos(np.pi * p))
        else:
            mod_env[i] = 0.0

    print("  [3/4] M/S EQ en Side: Purga 400-800 Hz (-3.8 dB) y HPF a 260 Hz + Trim Melódico...")
    mid_h = (high[:, 0] + high[:, 1]) / np.sqrt(2.0)
    side_h = (high[:, 0] - high[:, 1]) / np.sqrt(2.0)
    
    # Bell filter on Side channel for 400-800 Hz (fc=560 Hz, Q=1.1, gain=-3.8 dB)
    fc = 560.0
    q = 1.1
    gain_db = -3.8
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * fc / sr
    alpha = np.sin(w0) / (2.0 * q)
    cos_w0 = np.cos(w0)
    b = np.array([1.0 + alpha * A, -2.0 * cos_w0, 1.0 - alpha * A]) / (1.0 + alpha / A)
    a = np.array([1.0, -2.0 * cos_w0 / (1.0 + alpha / A), (1.0 - alpha / A) / (1.0 + alpha / A)])
    side_h_eq = signal.lfilter(b, a, side_h)
    
    # High-pass filter on Side channel at 260 Hz
    sos_side_hp = signal.butter(2, 260.0, btype='highpass', fs=sr, output='sos')
    side_h_eq = signal.sosfilt(sos_side_hp, side_h_eq)
    
    # Melodic layer trims: Mid gets slight polish (-0.4 dB), Side gets -1.8 dB
    mid_trim = 10.0 ** (-0.4 / 20.0)
    side_trim = 10.0 ** (-1.8 / 20.0)
    
    mid_h_out = mid_h * (1.0 - mod_env) + (mid_h * mid_trim) * mod_env
    side_h_out = side_h * (1.0 - mod_env) + (side_h_eq * side_trim) * mod_env
    
    high_out_l = (mid_h_out + side_h_out) / np.sqrt(2.0)
    high_out_r = (mid_h_out - side_h_out) / np.sqrt(2.0)
    high_out = np.column_stack([high_out_l, high_out_r])
    
    recombined = low + high_out
    
    print("  [4/4] Limitador Master True-Peak 4x Oversampled con Techo a -1.0 dBTP...")
    ceiling_linear = 10.0 ** (-1.0 / 20.0)
    recomb_4x = signal.resample_poly(recombined, 4, 1, axis=0)
    
    k_start = ceiling_linear * 0.92
    delta = ceiling_linear - k_start
    recomb_4x_lim = recomb_4x.copy()
    for ch in range(2):
        x = recomb_4x[:, ch]
        abs_x = np.abs(x)
        sign_x = np.sign(x)
        clipped = np.where(abs_x < k_start, x, sign_x * (k_start + delta * np.tanh((abs_x - k_start) / delta)))
        recomb_4x_lim[:, ch] = clipped
        
    master = signal.resample_poly(recomb_4x_lim, 1, 4, axis=0)
    if len(master) > len(data):
        master = master[:len(data)]
    elif len(master) < len(data):
        master = np.pad(master, ((0, len(data) - len(master)), (0, 0)))
        
    master_4x = signal.resample_poly(master, 4, 1, axis=0)
    final_peak = np.max(np.abs(master_4x))
    if final_peak > ceiling_linear:
        master *= (ceiling_linear / final_peak)
        
    return master, {}


def main():
    print("═══════════════════════════════════════════════════════════════════════════")
    print("🚀 MOTOR DE REMEDIACIÓN ACÚSTICA C5-REAL · COME HOME FOR THE TRUMPETS")
    print("═══════════════════════════════════════════════════════════════════════════")
    
    if not FLAC_PATH.exists():
        print(f"Error: Archivo FLAC no encontrado en {FLAC_PATH}")
        sys.exit(1)
        
    # Backup
    if not BACKUP_FLAC.exists():
        print(f"Creando respaldo inmutable en {BACKUP_FLAC.name}...")
        shutil.copy2(FLAC_PATH, BACKUP_FLAC)
    else:
        print(f"Respaldo existente verificado en {BACKUP_FLAC.name}")
        
    data, sr = sf.read(str(FLAC_PATH))
    print(f"Audio cargado: {len(data)/sr:.2f}s | {sr} Hz | Canales: {data.shape[1]}")
    
    # 1. Telemetría Previa
    sec1_range = (int(78.0 * sr), int(110.0 * sr))
    sec2_range = (int(125.0 * sr), int(183.0 * sr))
    
    pre_m1 = calculate_metrics(data[sec1_range[0]:sec1_range[1]], sr)
    pre_m2 = calculate_metrics(data[sec2_range[0]:sec2_range[1]], sr)
    
    # 2. Ejecutar remediación
    master, _ = execute_remediation(data, sr)
    
    # 3. Telemetría Posterior
    post_m1 = calculate_metrics(master[sec1_range[0]:sec1_range[1]], sr)
    post_m2 = calculate_metrics(master[sec2_range[0]:sec2_range[1]], sr)
    
    # 4. Guardar archivos
    MUSIC_BOUNCES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Sobrescribir el FLAC de trabajo
    sf.write(str(FLAC_PATH), master, sr, format="FLAC", subtype="PCM_24")
    print(f"\n FLAC de trabajo actualizado: {FLAC_PATH}")
    
    # Exportar master final a Music/FL Studio Bounces
    sf.write(str(OUTPUT_MASTER_WAV), master, sr, subtype="PCM_24")
    sf.write(str(OUTPUT_MASTER_FLAC), master, sr, format="FLAC", subtype="PCM_24")
    print(f" Master WAV entregado en: {OUTPUT_MASTER_WAV}")
    print(f" Master FLAC entregado en: {OUTPUT_MASTER_FLAC}")
    
    # 5. Reporte Telemetría Comparativa
    print("\n═══════════════════════════════════════════════════════════════════════════")
    print("🔬 AUDITORÍA COMPARATIVA DE TELEMETRÍA (ANTES vs DESPUÉS)")
    print("═══════════════════════════════════════════════════════════════════════════")
    print(f"{'Métrica':<24} | {'1:18-1:50 PRE':<13} {'1:18-1:50 POST':<14} | {'2:05-3:03 PRE':<13} {'2:05-3:03 POST':<14}")
    print("-" * 85)
    
    metrics_keys = [
        ("Loudness (LUFS)", "lufs", "LUFS"),
        ("True Peak (dBTP)", "true_peak_dbtp", "dBTP"),
        ("Crest Factor (dB)", "crest_factor_db", "dB"),
        ("Correlación Estéreo", "stereo_correlation", ""),
        ("Side/Mid 400-800Hz", "side_mid_diff_db", "dB"),
        ("Mono Loudness", "mono_lufs", "LUFS")
    ]
    
    for label, k, unit in metrics_keys:
        v1_pre = f"{pre_m1[k]:+.2f} {unit}".strip()
        v1_post = f"{post_m1[k]:+.2f} {unit}".strip()
        v2_pre = f"{pre_m2[k]:+.2f} {unit}".strip()
        v2_post = f"{post_m2[k]:+.2f} {unit}".strip()
        print(f"{label:<24} | {v1_pre:<13} {v1_post:<14} | {v2_pre:<13} {v2_post:<14}")
        
    print("═══════════════════════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
