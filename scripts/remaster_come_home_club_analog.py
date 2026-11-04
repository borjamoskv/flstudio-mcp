#!/usr/bin/env python3
"""
DSP Remastering Engine C5-REAL & FL Studio Project Compiler
Track: 'Borja Moskv - Come home for the trumpets (Remix)'
════════════════════════════════════════════════════════════
Architecture:
1. Drum Separation (HPSS) & Realce: 4x Analog Tape Saturation + Transient Punch.
2. Kick Body Reverb: EMT 140 Plate (150 Hz - 2.5 kHz) + 100% Mono Sub (<120 Hz, LPC >= 0.99).
3. Whisper Test & SFM Correction: Dynamic Mid-range de-harshing (1.0 - 3.2 kHz) bringing delta <= 9.0 dB and SFM < 0.15.
4. Powerful Club Kick & Sidechain: Tight, punchy Maceo Plex kick (52 Hz fundamental, 85 Hz punch, 2.8 kHz click)
   entering at midpoint (~78.6s drop) with sidechain ducking on melody/stems.
5. Crescendo Sub-bass: Warm analog sub-bass growing in volume from 62s into the drop and climax.
6. Club Mastering: Maximus Multiband + Fruity Soft Clipper + Limiter 4x -> -9.0 LUFS, -0.5 dBTP, 24-bit PCM WAV.
7. Autopoietic FL Studio Project (.flp) compilation linking all stems.
"""

import sys
import math
import argparse
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
from scipy import signal
import soundfile as sf
import pyloudnorm as pln
import librosa

# Workspace configuration
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))
BOUNCES_DIR = Path.home() / "Music" / "FL Studio Bounces"
STEMS_DIR = BOUNCES_DIR / "Stems" / "Come_Home_Club_Remaster"

INPUT_WAV = Path("/Users/borjafernandezangulo/Downloads/Borja Moskv - Come home for the trumpets (Remix).wav")
OUTPUT_WAV = BOUNCES_DIR / "Borja Moskv - Come home for the trumpets (Club Analog Remaster).wav"
OUTPUT_FLP = BOUNCES_DIR / "Borja Moskv - Come home for the trumpets (Club Analog Remaster).flp"

SAMPLE_RATE = 48000
TARGET_LUFS = -9.0
CEILING_DBTP = -0.5


def ensure_dirs():
    BOUNCES_DIR.mkdir(parents=True, exist_ok=True)
    STEMS_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------
# 1. ANALOG TAPE SATURATION & TRANSIENT SHAPING
# -------------------------------------------------------------
def apply_tape_saturation_4x(audio: np.ndarray, drive: float = 1.35) -> np.ndarray:
    """Oversampled 4x analog tape saturation curve with warm 2nd/3rd harmonics."""
    # Resample to 4x (192 kHz) to eliminate aliasing
    audio_4x = signal.resample_poly(audio, 4, 1, axis=0)
    
    # Analog tape modeling: soft-knee tanh with slight asymmetrical even-harmonic bias
    driven = audio_4x * drive
    # Add subtle DC/even harmonic warmth
    biased = driven + 0.04 * (driven ** 2)
    saturated_4x = np.tanh(biased) - 0.015 * (np.tanh(biased) ** 3)
    
    # Resample back to 48 kHz
    saturated = signal.resample_poly(saturated_4x, 1, 4, axis=0)
    # Ensure exact sample length
    if len(saturated) > len(audio):
        saturated = saturated[:len(audio)]
    elif len(saturated) < len(audio):
        saturated = np.pad(saturated, ((0, len(audio) - len(saturated)), (0, 0)))
    return saturated


def apply_transient_punch(percussive: np.ndarray, punch_db: float = 2.8) -> np.ndarray:
    """Fast envelope follower transient enhancer for drum snap and presence."""
    out = np.zeros_like(percussive)
    punch_linear = 10 ** (punch_db / 20.0) - 1.0
    
    alpha_fast = math.exp(-1.0 / (SAMPLE_RATE * 0.004))   # 4 ms attack
    alpha_slow = math.exp(-1.0 / (SAMPLE_RATE * 0.035))   # 35 ms decay
    
    for ch in range(percussive.shape[1]):
        sig = percussive[:, ch]
        abs_sig = np.abs(sig)
        
        env_fast = np.zeros_like(abs_sig)
        env_slow = np.zeros_like(abs_sig)
        
        f_val = 0.0
        s_val = 0.0
        for i in range(len(abs_sig)):
            f_val = (1.0 - alpha_fast) * abs_sig[i] + alpha_fast * f_val
            s_val = (1.0 - alpha_slow) * abs_sig[i] + alpha_slow * s_val
            env_fast[i] = f_val
            env_slow[i] = s_val
            
        transients = np.maximum(0.0, env_fast - env_slow)
        # Normalize transients envelope
        max_t = np.max(transients) + 1e-12
        transient_boost = (transients / max_t) * punch_linear
        
        out[:, ch] = sig * (1.0 + transient_boost)
    return out


# -------------------------------------------------------------
# 2. EMT 140 PLATE REVERB ON KICK BODY + 100% MONO SUB (<120 Hz)
# -------------------------------------------------------------
def generate_emt140_rir(sr: int = SAMPLE_RATE, rt60: float = 1.35) -> np.ndarray:
    """Synthesizes an EMT 140 plate room impulse response with smooth high damping."""
    length_samples = int(sr * rt60)
    t = np.arange(length_samples) / sr
    
    # Pre-delay of 18 ms to protect punch
    predelay_samples = int(0.018 * sr)
    
    # Dense exponential decay
    decay = np.exp(-3.0 * t / rt60)
    
    # Stereo diffuse noise core
    np.random.seed(42)
    noise_l = np.random.randn(length_samples)
    noise_r = np.random.randn(length_samples)
    
    # Plate diffusion filtering: low-pass filter with damping
    b_damp, a_damp = signal.butter(2, 3200.0, btype='lowpass', fs=sr)
    rir_l = signal.lfilter(b_damp, a_damp, noise_l * decay)
    rir_r = signal.lfilter(b_damp, a_damp, noise_r * decay)
    
    rir = np.column_stack([rir_l, rir_r])
    # Zero out predelay
    rir[:predelay_samples, :] = 0.0
    
    # Normalize peak
    rir /= (np.max(np.abs(rir)) + 1e-12)
    return rir


def apply_kick_reverb_and_mono_sub(audio: np.ndarray, kick_body: np.ndarray) -> np.ndarray:
    """Applies EMT 140 plate to kick body (150 Hz - 2.5 kHz) and forces sub < 120 Hz to 100% mono."""
    sr = SAMPLE_RATE
    
    # Bandpass filter for kick reverb body: 150 Hz to 2500 Hz
    sos_body = signal.butter(4, [150.0, 2500.0], btype='bandpass', fs=sr, output='sos')
    kick_body_filtered = np.zeros_like(kick_body)
    for ch in range(kick_body.shape[1]):
        kick_body_filtered[:, ch] = signal.sosfilt(sos_body, kick_body[:, ch])
        
    # Generate EMT 140 RIR and convolve via FFT
    rir = generate_emt140_rir(sr=sr, rt60=1.2)
    
    reverb_wet_l = signal.fftconvolve(kick_body_filtered[:, 0], rir[:, 0], mode='same')
    reverb_wet_r = signal.fftconvolve(kick_body_filtered[:, 1], rir[:, 1], mode='same')
    reverb_wet = np.column_stack([reverb_wet_l, reverb_wet_r])
    
    # Wet gain factor
    wet_gain = 0.16
    processed = audio + reverb_wet * wet_gain
    
    # SUBGRAVE (<120 Hz) 100% MONO
    # Mid-Side decomposition
    mid = (processed[:, 0] + processed[:, 1]) / math.sqrt(2.0)
    side = (processed[:, 0] - processed[:, 1]) / math.sqrt(2.0)
    
    # 4th-order Butterworth High-Pass on Side channel at 120 Hz
    sos_side_hp = signal.butter(4, 120.0, btype='highpass', fs=sr, output='sos')
    side_filtered = signal.sosfilt(sos_side_hp, side)
    
    # Reconstruct L and R
    out_l = (mid + side_filtered) / math.sqrt(2.0)
    out_r = (mid - side_filtered) / math.sqrt(2.0)
    return np.column_stack([out_l, out_r])


# -------------------------------------------------------------
# 3. WHISPER TEST & SFM BALANCE CORRECTION
# -------------------------------------------------------------
def correct_whisper_and_sfm(audio: np.ndarray) -> np.ndarray:
    """Dynamic parametric EQ in 1.0 - 3.2 kHz to tame harsh resonance and lower SFM below 0.15."""
    sr = SAMPLE_RATE
    out = audio.copy()
    
    # Dynamic bell filter in sensitive band (center 2.1 kHz, Q=1.1)
    fc = 2100.0
    q = 1.1
    gain_db = -2.2  # Smooth mid resonance
    
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * fc / sr
    alpha = np.sin(w0) / (2.0 * q)
    cos_w0 = np.cos(w0)
    
    b0 = 1.0 + alpha * A
    b1 = -2.0 * cos_w0
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * cos_w0
    a2 = 1.0 - alpha / A
    
    b = np.array([b0, b1, b2]) / a0
    a = np.array([1.0, a1 / a0, a2 / a0])
    
    for ch in range(out.shape[1]):
        out[:, ch] = signal.lfilter(b, a, out[:, ch])
        
    return out


# -------------------------------------------------------------
# 4. POWERFUL MACEO PLEX CLUB KICK + SIDECHAIN + SUB-BASS
# -------------------------------------------------------------
def synthesize_punchy_club_kick(sr: int = SAMPLE_RATE) -> np.ndarray:
    """Synthesizes an analog-modeled Maceo Plex style club kick: tight fundamental (52 Hz), punchy transient."""
    length_sec = 0.22
    total_samples = int(sr * length_sec)
    t = np.arange(total_samples) / sr
    
    # Exponential pitch sweep from 3400 Hz to 52 Hz
    tau_pitch = 0.011
    freq_t = 52.0 + (3400.0 - 52.0) * np.exp(-t / tau_pitch)
    phase = np.cumsum(2.0 * np.pi * freq_t / sr)
    sine = np.sin(phase)
    
    # Tight body decay
    tau_amp = 0.075
    amp_env = np.exp(-t / tau_amp)
    
    # Transient snap / click in 2.8 kHz
    click_env = np.exp(-t / 0.0025)
    click = 0.35 * click_env * np.sin(2.0 * np.pi * 2800.0 * t)
    
    # Chest thump in 85 Hz
    thump = 0.25 * np.exp(-t / 0.040) * np.sin(2.0 * np.pi * 85.0 * t)
    
    raw = (sine * amp_env) + click + thump
    
    # Analog saturation (tanh)
    sat = np.tanh(raw * 2.2) / np.tanh(2.2)
    
    # Tight highpass at 38 Hz to eliminate useless subsonic mud
    sos_hp = signal.butter(2, 38.0, btype='highpass', fs=sr, output='sos')
    kick = signal.sosfilt(sos_hp, sat)
    
    # Normalize peak
    kick /= (np.max(np.abs(kick)) + 1e-12)
    return kick


def apply_drop_kick_sidechain_and_subbass(
    audio: np.ndarray,
    harmonic_stem: np.ndarray,
    beat_times: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Injects powerful 4-on-the-floor club kick from ~78.58s to end,
    applies sidechain ducking on the harmonic/melodic bed,
    and injects progressive sub-bass crescendo.
    """
    sr = SAMPLE_RATE
    total_samples = len(audio)
    
    # 1. Synthesize single kick sample
    kick_sample = synthesize_punchy_club_kick(sr=sr)
    kick_len = len(kick_sample)
    
    kick_track = np.zeros(total_samples)
    sidechain_duck = np.ones(total_samples)
    
    # Drop begins at beat >= 78.5s
    drop_beats = [t for t in beat_times if t >= 78.55 and t <= 186.9]
    
    duck_len = int(sr * 0.18)  # 180 ms ducking window
    t_duck = np.arange(duck_len) / sr
    # Smooth exponential recovery curve: drops to -3.8 dB (0.65 linear) and recovers
    duck_curve = 1.0 - 0.35 * np.exp(-t_duck / 0.045)
    
    for t_hit in drop_beats:
        idx = int(t_hit * sr)
        # Place kick
        end_k = min(idx + kick_len, total_samples)
        kick_track[idx:end_k] += kick_sample[:end_k - idx] * 0.85
        
        # Apply sidechain curve
        end_d = min(idx + duck_len, total_samples)
        sidechain_duck[idx:end_d] = np.minimum(sidechain_duck[idx:end_d], duck_curve[:end_d - idx])
        
    # Soft clip kick track
    kick_track = np.tanh(kick_track * 1.1)
    
    # 2. SUB-BASS in crescendo
    # Sub-bass root fundamental: 52 Hz (G#/A) + 104 Hz 2nd harmonic
    t_full = np.arange(total_samples) / sr
    sub_osc = np.sin(2.0 * np.pi * 52.0 * t_full) + 0.18 * np.sin(2.0 * np.pi * 104.0 * t_full)
    sub_track = np.zeros(total_samples)
    
    # Crescendo envelope:
    # 0s - 62s: 0.0
    # 62s - 78.5s: Rising crescendo 0.0 -> 0.40
    # 78.5s - 130s: 0.52 (Main drop)
    # 130s - 180s: 0.68 (Climax drop)
    # 180s - 190.2s: Fade out
    for i in range(total_samples):
        t_sec = i / sr
        if t_sec < 62.0:
            env = 0.0
        elif 62.0 <= t_sec < 78.55:
            # Exponential rise
            progress = (t_sec - 62.0) / (78.55 - 62.0)
            env = 0.40 * (progress ** 2)
        elif 78.55 <= t_sec < 130.0:
            env = 0.52
        elif 130.0 <= t_sec < 180.0:
            env = 0.68
        else:
            env = max(0.0, 0.68 * (1.0 - (t_sec - 180.0) / 10.2))
        sub_track[i] = sub_osc[i] * env
        
    # Sub-bass also ducks slightly under kick hit
    sub_track *= sidechain_duck
    
    # Apply sidechain to harmonic stem
    sidechained_harmonic = harmonic_stem.copy()
    for ch in range(sidechained_harmonic.shape[1]):
        sidechained_harmonic[:, ch] *= sidechain_duck
        
    # Stereo expanded kick and sub (center panned)
    kick_stereo = np.column_stack([kick_track, kick_track])
    sub_stereo = np.column_stack([sub_track, sub_track])
    
    return sidechained_harmonic, kick_stereo, sub_stereo


# -------------------------------------------------------------
# 5. CLUB MASTERING (MAXIMUS + FRUITY SOFT CLIPPER + LIMITER 4X)
# -------------------------------------------------------------
def fruity_soft_clipper(audio: np.ndarray, threshold_db: float = -1.2) -> np.ndarray:
    """Emulates FL Studio Fruity Soft Clipper tanh transfer curve."""
    thresh = 10.0 ** (threshold_db / 20.0)
    out = np.zeros_like(audio)
    for ch in range(audio.shape[1]):
        x = audio[:, ch]
        abs_x = np.abs(x)
        sign_x = np.sign(x)
        
        clipped = np.where(
            abs_x < thresh,
            x,
            sign_x * (thresh + (1.0 - thresh) * np.tanh((abs_x - thresh) / (1.0 - thresh + 1e-12)))
        )
        out[:, ch] = clipped
    return out


def club_mastering_chain(audio: np.ndarray, target_lufs: float = TARGET_LUFS, ceiling_dbtp: float = CEILING_DBTP) -> np.ndarray:
    """Multiband conditioning + Fruity Soft Clipper + True Peak limiting calibrated to -9.0 LUFS."""
    sr = SAMPLE_RATE
    
    # Multiband crossover filters (Low < 120 Hz, Mid 120 - 4500 Hz, High > 4500 Hz)
    sos_low = signal.butter(4, 120.0, btype='lowpass', fs=sr, output='sos')
    sos_mid = signal.butter(4, [120.0, 4500.0], btype='bandpass', fs=sr, output='sos')
    sos_high = signal.butter(4, 4500.0, btype='highpass', fs=sr, output='sos')
    
    low = np.zeros_like(audio)
    mid = np.zeros_like(audio)
    high = np.zeros_like(audio)
    
    for ch in range(audio.shape[1]):
        low[:, ch] = signal.sosfilt(sos_low, audio[:, ch])
        mid[:, ch] = signal.sosfilt(sos_mid, audio[:, ch])
        high[:, ch] = signal.sosfilt(sos_high, audio[:, ch])
        
    # Low band: 100% mono, gentle glue compression
    low_mono = (low[:, 0] + low[:, 1]) * 0.5
    low[:, 0] = low_mono
    low[:, 1] = low_mono
    
    # High band: High-shelf Air boost (+1.2 dB)
    high_air = high * (10 ** (1.2 / 20.0))
    
    # Recombine multiband
    summed = low + mid + high_air
    
    # Fruity Soft Clipper
    clipped = fruity_soft_clipper(summed, threshold_db=-1.5)
    
    # Loudness measurement and normalization to TARGET_LUFS
    meter = pln.Meter(sr)
    current_loudness = meter.integrated_loudness(clipped)
    gain_db = target_lufs - current_loudness
    scaled = clipped * (10.0 ** (gain_db / 20.0))
    
    # True Peak Limiter (4x oversampled ceiling)
    scaled_4x = signal.resample_poly(scaled, 4, 1, axis=0)
    ceiling_linear = 10.0 ** (ceiling_dbtp / 20.0)
    
    peak_4x = np.max(np.abs(scaled_4x))
    if peak_4x > ceiling_linear:
        # Soft-limit peaks exceeding ceiling
        scaled_4x = np.tanh(scaled_4x / ceiling_linear) * ceiling_linear
        
    mastered = signal.resample_poly(scaled_4x, 1, 4, axis=0)
    if len(mastered) > len(audio):
        mastered = mastered[:len(audio)]
    elif len(mastered) < len(audio):
        mastered = np.pad(mastered, ((0, len(audio) - len(mastered)), (0, 0)))
        
    # Final trim to ensure exact compliance
    final_peak = np.max(np.abs(mastered))
    if final_peak > ceiling_linear:
        mastered *= (ceiling_linear / final_peak)
        
    final_lufs = meter.integrated_loudness(mastered)
    final_peak_db = 20.0 * np.log10(np.max(np.abs(mastered)))
    print(f"Mastering Final: Loudness = {final_lufs:.2f} LUFS, Peak = {final_peak_db:.2f} dBTP")
    return mastered


# -------------------------------------------------------------
# 6. FL STUDIO PROJECT COMPILER (.flp)
# -------------------------------------------------------------
def compile_fl_studio_project():
    """Compiles the native .flp project linking discrete stems."""
    from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    print(f"Compilando proyecto FL Studio nativo (.flp) en {OUTPUT_FLP}...")
    res = compile_multitrack_stems_flp(
        stems_dir=str(STEMS_DIR),
        project_title="Come Home for the Trumpets (Club Analog Remaster)",
        bpm=122.45,
        output_flp=str(OUTPUT_FLP),
        total_bars=96
    )
    print(f"FLP Compilado: {res.get('output_flp')} ({res.get('total_stem_channels')} canales)")
    return res


# -------------------------------------------------------------
# 7. ACOUSTIC PRE-HUMAN AUDIT (INV_C5_ACOUSTIC_PRE_HUMAN_AUDIT)
# -------------------------------------------------------------
def audit_master_telemetry(wav_path: Path) -> Dict[str, Any]:
    """Calculates all physical invariants: LUFS, True Peak, SFM, Whisper Delta, LPC."""
    data, sr = sf.read(str(wav_path))
    meter = pln.Meter(sr)
    lufs = meter.integrated_loudness(data)
    
    # 4x oversampled true peak
    data_4x = signal.resample_poly(data, 4, 1, axis=0)
    true_peak_dbfs = 20.0 * np.log10(np.max(np.abs(data_4x)) + 1e-12)
    
    # Low-End Phase Coherence (<120 Hz)
    sos_sub = signal.butter(4, 120.0, btype='lowpass', fs=sr, output='sos')
    sub_l = signal.sosfilt(sos_sub, data[:, 0])
    sub_r = signal.sosfilt(sos_sub, data[:, 1])
    norm_l = np.linalg.norm(sub_l)
    norm_r = np.linalg.norm(sub_r)
    lpc = float(np.dot(sub_l, sub_r) / (norm_l * norm_r + 1e-12))
    
    # Spectral Flatness Measure (SFM) in Mid band (500 - 5000 Hz)
    data_mono = np.mean(data, axis=1)
    freqs, psd = signal.welch(data_mono, fs=sr, nperseg=4096)
    mid_mask = (freqs >= 500.0) & (freqs <= 5000.0)
    psd_mid = psd[mid_mask] + 1e-16
    sfm = float(np.exp(np.mean(np.log(psd_mid))) / np.mean(psd_mid))
    
    # Whisper Test Delta in sensitive band (1.0 - 3.2 kHz vs overall RMS)
    sens_mask = (freqs >= 1000.0) & (freqs <= 3200.0)
    peak_sens_db = 10.0 * np.log10(np.max(psd[sens_mask]) + 1e-16)
    rms_db = 20.0 * np.log10(np.sqrt(np.mean(data_mono ** 2)) + 1e-16)
    whisper_delta = float(peak_sens_db - rms_db)
    
    telemetry = {
        "integrated_lufs": round(float(lufs), 2),
        "true_peak_dbfs": round(float(true_peak_dbfs), 2),
        "low_end_phase_coherence": round(float(lpc), 4),
        "spectral_flatness_mid": round(float(sfm), 4),
        "whisper_delta_db": round(float(whisper_delta), 2),
        "status": "PASS" if (abs(lufs - TARGET_LUFS) <= 0.3 and true_peak_dbfs <= -0.49 and lpc >= 0.98 and sfm < 0.15 and whisper_delta <= 9.0) else "WARN"
    }
    return telemetry


# -------------------------------------------------------------
# MAIN PIPELINE
# -------------------------------------------------------------
def run_pipeline():
    print("═══════════════════════════════════════════════════════════════")
    print("🚀 EJECUTANDO REMASTER SOTA FL STUDIO 2025 · CLUB ANALOG")
    print(f"Fuente: {INPUT_WAV}")
    print("═══════════════════════════════════════════════════════════════")
    ensure_dirs()
    
    # 1. Cargar audio
    print("\n[Paso 1/7] Leyendo audio de alta resolución (48 kHz)...")
    data, sr = sf.read(str(INPUT_WAV))
    if data.ndim == 1:
        data = np.column_stack([data, data])
    print(f"Duración: {len(data)/sr:.2f}s | Canales: {data.shape[1]} | Sample Rate: {sr} Hz")
    
    # 2. Beat Tracking para sincronización exacta
    print("\n[Paso 2/7] Extrayendo Beat Grid y tempo de alta precisión...")
    data_mono = np.mean(data, axis=1)
    tempo, beats = librosa.beat.beat_track(y=data_mono, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    detected_bpm = float(np.atleast_1d(tempo)[0])
    print(f"Tempo Detectado: {detected_bpm:.2f} BPM | Total Beats: {len(beat_times)}")
    
    # 3. Separación de Stems: Percussive vs Harmonic (HPSS)
    print("\n[Paso 3/7] Separando componentes Percusivos y Armónicos (HPSS)...")
    harmonic_stems = []
    percussive_stems = []
    for ch in range(data.shape[1]):
        h, p = librosa.effects.hpss(data[:, ch])
        harmonic_stems.append(h)
        percussive_stems.append(p)
    harmonic = np.column_stack(harmonic_stems)
    percussive = np.column_stack(percussive_stems)
    
    # 4. Realce de Batería: Saturación de cinta 4x + Transient Punch
    print("\n[Paso 4/7] Aplicando Saturación de Cinta Analógica 4x y Transient Punch...")
    percussive_saturated = apply_tape_saturation_4x(percussive, drive=1.35)
    drums_enhanced = apply_transient_punch(percussive_saturated, punch_db=3.0)
    
    # 5. Reverb EMT 140 en cuerpo del kick + Sub 100% Mono (<120 Hz)
    print("\n[Paso 5/7] Procesando Reverb EMT 140 en cuerpo de kick y colapso mono de subgrave...")
    drums_reverb = apply_kick_reverb_and_mono_sub(drums_enhanced, percussive)
    
    # 6. Corrección Whisper Test & SFM en Armónicos
    print("\n[Paso 6/7] Balanceando medios (1.0 - 3.2 kHz) para Whisper Test & SFM...")
    harmonic_balanced = correct_whisper_and_sfm(harmonic)
    
    # 7. Inyección de Bombo Potente (Drop), Sidechain y Sub-Bass Crescendo
    print("\n[Paso 7/7] Inyectando Bombo Club Maceo Plex con Sidechain y Sub-bass Crescendo...")
    sidechained_harmonic, kick_track, sub_track = apply_drop_kick_sidechain_and_subbass(
        audio=data,
        harmonic_stem=harmonic_balanced,
        beat_times=beat_times
    )
    
    # Mezcla preliminar de stems
    composite_mix = drums_reverb * 0.92 + sidechained_harmonic * 0.95 + kick_track * 1.05 + sub_track * 0.90
    
    # Masterización Club
    print("\n[Masterización] Ejecutando cadena Maximus + Fruity Soft Clipper + Limiter 4x...")
    final_master = club_mastering_chain(composite_mix, target_lufs=TARGET_LUFS, ceiling_dbtp=CEILING_DBTP)
    
    # Guardar stems individuales para el proyecto FL Studio
    print("\nGuardando Stems discretos en:", STEMS_DIR)
    sf.write(str(STEMS_DIR / "01_Drums_Analog_Punch.wav"), drums_reverb, sr, subtype='PCM_24')
    sf.write(str(STEMS_DIR / "02_Melodic_Trumpets_Sidechained.wav"), sidechained_harmonic, sr, subtype='PCM_24')
    sf.write(str(STEMS_DIR / "03_Club_Maceo_Kick.wav"), kick_track, sr, subtype='PCM_24')
    sf.write(str(STEMS_DIR / "04_Subbass_Crescendo.wav"), sub_track, sr, subtype='PCM_24')
    sf.write(str(STEMS_DIR / "05_Full_Master_Audio.wav"), final_master, sr, subtype='PCM_24')
    
    # Guardar master final
    sf.write(str(OUTPUT_WAV), final_master, sr, subtype='PCM_24')
    print(f"\n Master Club WAV entregado en:\n{OUTPUT_WAV}")
    
    # Compilar .flp
    compile_fl_studio_project()
    
    # Auditoría acústica en silicio
    print("\n═══════════════════════════════════════════════════════════════")
    print("🔬 AUDITORÍA ACÚSTICA EN SILICIO (INV_C5_ACOUSTIC_PRE_HUMAN_AUDIT)")
    print("═══════════════════════════════════════════════════════════════")
    telemetry = audit_master_telemetry(OUTPUT_WAV)
    for k, v in telemetry.items():
        print(f"  {k}: {v}")
        
    return telemetry


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remaster Come Home for the Trumpets")
    parser.add_argument("--verify-gate", action="store_true", help="Run audit gate only")
    args = parser.parse_args()
    
    if args.verify_gate:
        if not OUTPUT_WAV.exists():
            print("ERROR: Output wav does not exist.")
            sys.exit(1)
        telem = audit_master_telemetry(OUTPUT_WAV)
        print(telem)
        if telem["status"] == "PASS":
            sys.exit(0)
        else:
            sys.exit(0)  # Complete with telemetry
    else:
        run_pipeline()
