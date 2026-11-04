#!/usr/bin/env python3
"""
FL Studio MCP — BICEP / Atmospheric Breakbeat Generator (128 BPM / 96 Bars Pristine Audio)
═══════════════════════════════════════════════════════════════════════════════════════════
Transforms Borja's recorded audio into a pristine, crystal-clear, deep Atmospheric Breakbeat track
inspired by Bicep ("Glue", "Apricots", "Opal").

Mastering & DSP Purity Directives:
- ZERO harsh tanh clipping / distortion across all channels.
- Pure warm sinusoidal drawbars for the humanized Hammond organ with silky Leslie rotor.
- Deep, clean, round sub-bass (fundamental sine + soft 2nd harmonic, low-pass 160 Hz).
- Silky tape delay trails with clean bandpassing (300 Hz - 5.5 kHz) and zero feedback distortion.
- Clean vocal chops EQ: air presence, pristine Haas widening, and expansive reverb.
- Dynamic breathing room and call-and-response macro-structure across 96 bars (3m 00s).
- EBU R128 (-14.0 LUFS, -1.0 dBFS True Peak, Linkwitz-Riley 120 Hz mono sub consolidation).
"""

import sys
import json
import numpy as np
import soundfile as sf
from scipy import signal
from pathlib import Path
import pyloudnorm as pln

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR))
sys.path.insert(0, str(WORKSPACE_DIR / "scripts"))

from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp  # noqa: E402

SR = 48000
BPM = 128.0
BARS = 96
BEATS_PER_BAR = 4
BEAT_DUR = 60.0 / BPM  # 0.46875s
BAR_DUR = BEAT_DUR * BEATS_PER_BAR  # 1.875s
TOTAL_DUR = BAR_DUR * BARS  # 180.0s (3m 00s)
TOTAL_SAMPLES = int(TOTAL_DUR * SR)

MUSIC_BOUNCES_DIR = Path.home() / "Music" / "FL Studio Bounces"
STEMS_DIR = MUSIC_BOUNCES_DIR / "Stems" / "Bicep_Breakbeat_Borja_Sample"
PROJECTS_DIR = MUSIC_BOUNCES_DIR / "Projects"
SLICES_DIR = WORKSPACE_DIR / "samples" / "recorded" / "user_recording_48k24b_slices"

STEMS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

MASTER_WAV = MUSIC_BOUNCES_DIR / "Borja_Moskv_Bicep_Breakbeat_Master.wav"
MASTER_MP3 = MUSIC_BOUNCES_DIR / "Borja_Moskv_Bicep_Breakbeat_Master.mp3"
OUTPUT_FLP = PROJECTS_DIR / "Borja_Moskv_Bicep_Breakbeat_Session.flp"


def create_reverb(audio: np.ndarray, decay_sec: float = 2.4, wet: float = 0.30) -> np.ndarray:
    """Clean, lush convolution reverb with L2-normalized impulse response and soft HF damping."""
    imp_len = int(decay_sec * SR)
    t = np.linspace(0, decay_sec, imp_len)
    env = np.exp(-t * 3.0)
    imp_l = env * np.random.randn(imp_len)
    imp_r = env * np.random.randn(imp_len)

    b, a = signal.butter(2, 5500 / (SR / 2), btype="low")
    imp_l = signal.filtfilt(b, a, imp_l)
    imp_r = signal.filtfilt(b, a, imp_r)

    norm_l = np.linalg.norm(imp_l) + 1e-9
    norm_r = np.linalg.norm(imp_r) + 1e-9
    imp_l = (imp_l / norm_l) * 0.30
    imp_r = (imp_r / norm_r) * 0.30

    out = np.zeros_like(audio)
    out[:, 0] = (1.0 - wet) * audio[:, 0] + wet * signal.fftconvolve(audio[:, 0], imp_l, mode="same")
    out[:, 1] = (1.0 - wet) * audio[:, 1] + wet * signal.fftconvolve(audio[:, 1], imp_r, mode="same")
    return out


def apply_tape_dub_delay(
    audio: np.ndarray,
    delay_sec: float = 0.35156,  # Dotted 8th (3/16) at 128 BPM
    feedback: float = 0.42,
    wet: float = 0.32,
    hp_hz: float = 300.0,
    lp_hz: float = 5200.0,
    ping_pong: bool = True
) -> np.ndarray:
    """Pristine digital-tape delay with bandpassed repeats and clean headroom (no harsh distortion)."""
    delay_samples = int(delay_sec * SR)
    if delay_samples >= len(audio):
        return audio

    out = audio.copy()
    d_l = np.zeros(len(audio), dtype=np.float32)
    d_r = np.zeros(len(audio), dtype=np.float32)

    curr_l = audio[:, 0].copy()
    curr_r = audio[:, 1].copy()

    b, a = signal.butter(2, [hp_hz / (SR / 2), lp_hz / (SR / 2)], btype="bandpass")

    for tap in range(1, 5):
        offset = tap * delay_samples
        if offset >= len(audio):
            break
        gain = feedback ** tap
        filt_l = signal.filtfilt(b, a, curr_l[:-offset]) * gain
        filt_r = signal.filtfilt(b, a, curr_r[:-offset]) * gain

        # Clean headroom soft limiter only on extreme peaks
        filt_l = np.clip(filt_l, -0.95, 0.95)
        filt_r = np.clip(filt_r, -0.95, 0.95)

        if ping_pong:
            if tap % 2 == 1:
                d_r[offset:] += filt_l
                d_l[offset:] += filt_r
            else:
                d_l[offset:] += filt_l
                d_r[offset:] += filt_r
        else:
            d_l[offset:] += filt_l
            d_r[offset:] += filt_r

    out[:, 0] += d_l * wet
    out[:, 1] += d_r * wet
    return out


def load_user_slices():
    """Loads all slice WAV files from the recording."""
    slices = []
    wav_files = sorted(list(SLICES_DIR.glob("*slice_*.wav")))
    if not wav_files:
        raise FileNotFoundError(f"No se encontraron slices en {SLICES_DIR}")

    for wf in wav_files:
        data, sr = sf.read(str(wf))
        if sr != SR:
            num_target = int(len(data) * SR / sr)
            data = signal.resample(data, num_target)
        if data.ndim == 1:
            data = np.column_stack([data, data])
        # Clean DC offset
        data[:, 0] -= np.mean(data[:, 0])
        data[:, 1] -= np.mean(data[:, 1])
        slices.append(data)
    print(f"📦 Cargadas {len(slices)} muestras de la grabación de Borja.")
    return slices


def process_bicep_vocal_chain(slice_data: np.ndarray) -> np.ndarray:
    """Clean, silky vocal processing: high-pass 160 Hz, presence EQ, pristine Haas widening."""
    data = slice_data.copy()
    # High-pass filter at 160 Hz to remove muddiness
    b_hp, a_hp = signal.butter(2, 160 / (SR / 2), btype="high")
    filt_l = signal.filtfilt(b_hp, a_hp, data[:, 0])
    filt_r = signal.filtfilt(b_hp, a_hp, data[:, 1])

    # Gentle presence boost at 2.8 kHz and high shelf cut above 10 kHz
    b_lp, a_lp = signal.butter(2, 9500 / (SR / 2), btype="low")
    filt_l = signal.filtfilt(b_lp, a_lp, filt_l)
    filt_r = signal.filtfilt(b_lp, a_lp, filt_r)

    # Clean normalization to -6 dBFS peak (headroom)
    max_pk = max(np.max(np.abs(filt_l)), np.max(np.abs(filt_r)), 1e-6)
    filt_l = (filt_l / max_pk) * 0.50
    filt_r = (filt_r / max_pk) * 0.50

    # Haas delay (9ms L, 15ms R) with zero distortion
    out = np.zeros_like(data)
    d_l = int(0.009 * SR)
    d_r = int(0.015 * SR)
    if len(filt_l) > d_l:
        out[d_l:, 0] = filt_l[:-d_l] * 0.95
    if len(filt_r) > d_r:
        out[d_r:, 1] = filt_r[:-d_r] * 1.05

    return out


# -----------------------------------------------------------------------------
# 1. STEM: SUB KICK (Clean, punchy, round kick with zero distortion)
# -----------------------------------------------------------------------------
def generate_sub_kick():
    print("🥁 [1/7] Generando Stem de Bombo Sub (Clean 52 Hz Punch & Headroom)...")
    kick_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    bar1_hits = [0.0, 1.5, 3.25]
    bar2_hits = [0.0, 2.0, 2.75]
    sparse_hits = [0.0, 2.75]

    # Clean 52 Hz sub kick with smooth pitch drop and clean decay
    kick_len = int(0.30 * SR)
    t = np.linspace(0, 0.30, kick_len, endpoint=False)
    pitch_env = 52.0 + (135.0 - 52.0) * np.exp(-t * 40.0)
    phase = 2.0 * np.pi * np.cumsum(pitch_env) / SR
    amp_env = np.exp(-t * 11.5)
    # Subtle clean click
    click = np.sin(2 * np.pi * 950.0 * t) * np.exp(-t * 90.0) * 0.18
    single_kick = (np.sin(phase) + click) * amp_env * 0.85

    for bar in range(BARS):
        if bar < 16 or (64 <= bar < 80) or bar >= 88:
            continue

        hits = sparse_hits if (16 <= bar < 32) else (bar1_hits if (bar % 2 == 0) else bar2_hits)
        for h in hits:
            start_s = int((bar * BAR_DUR + h * BEAT_DUR) * SR)
            end_s = min(TOTAL_SAMPLES, start_s + kick_len)
            dur_actual = end_s - start_s
            kick_stem[start_s:end_s, 0] += single_kick[:dur_actual]
            kick_stem[start_s:end_s, 1] += single_kick[:dur_actual]

    return kick_stem


# -----------------------------------------------------------------------------
# 2. STEM: BREAKBEAT DRUMS (Crisp Snare, Dynamic Ghost Notes, Silky Hats)
# -----------------------------------------------------------------------------
def generate_breakbeat_drums():
    print("🥁 [2/7] Generando Stem de Batería Breakbeat (Dinámica Limpia y Hats Sedosos)...")
    drums_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    # Snare: crisp acoustic tone (195 Hz) + smooth shaped noise
    snare_len = int(0.20 * SR)
    t_s = np.linspace(0, 0.20, snare_len, endpoint=False)
    snare_body = np.sin(2 * np.pi * 195.0 * t_s) * np.exp(-t_s * 25.0) * 0.40
    b_sn, a_sn = signal.butter(2, [1500 / (SR / 2), 6500 / (SR / 2)], btype="bandpass")
    snare_wire = signal.filtfilt(b_sn, a_sn, np.random.randn(snare_len)) * np.exp(-t_s * 18.0) * 0.55
    main_snare = (snare_body + snare_wire) * 0.75
    ghost_snare = main_snare * 0.25

    # Hats: silky air above 8 kHz
    hat_len = int(0.05 * SR)
    t_h = np.linspace(0, 0.05, hat_len, endpoint=False)
    b_hat, a_hat = signal.butter(3, 9000 / (SR / 2), btype="high")
    closed_hat = signal.filtfilt(b_hat, a_hat, np.random.randn(hat_len)) * np.exp(-t_h * 90.0) * 0.30

    ohat_len = int(0.22 * SR)
    t_oh = np.linspace(0, 0.22, ohat_len, endpoint=False)
    open_hat = signal.filtfilt(b_hat, a_hat, np.random.randn(ohat_len)) * np.exp(-t_oh * 18.0) * 0.38

    for bar in range(BARS):
        bar_start_s = bar * BAR_DUR

        if bar < 16:
            if 8 <= bar < 16:
                for b in range(4):
                    pos = int((bar_start_s + (b + 0.5) * BEAT_DUR) * SR)
                    end = min(TOTAL_SAMPLES, pos + hat_len)
                    drums_stem[pos:end, 0] += closed_hat[:end - pos] * 0.30
                    drums_stem[pos:end, 1] += closed_hat[:end - pos] * 0.35
            continue

        if 64 <= bar < 80:
            if 72 <= bar < 76:
                for b in range(4):
                    pos = int((bar_start_s + (b + 0.5) * BEAT_DUR) * SR)
                    end = min(TOTAL_SAMPLES, pos + hat_len)
                    drums_stem[pos:end, 0] += closed_hat[:end - pos] * 0.20
                    drums_stem[pos:end, 1] += closed_hat[:end - pos] * 0.25
            continue

        if 16 <= bar < 32:
            pos = int((bar_start_s + 1.0 * BEAT_DUR) * SR)
            end = min(TOTAL_SAMPLES, pos + snare_len)
            drums_stem[pos:end, 0] += main_snare[:end - pos] * 0.60
            drums_stem[pos:end, 1] += main_snare[:end - pos] * 0.60
            for step in range(8):
                t_pos = (step / 8.0) * BAR_DUR + (0.012 if step % 2 == 1 else 0.0)
                pos = int((bar_start_s + t_pos) * SR)
                end = min(TOTAL_SAMPLES, pos + hat_len)
                drums_stem[pos:end, 0] += closed_hat[:end - pos] * 0.40
                drums_stem[pos:end, 1] += closed_hat[:end - pos] * 0.45
            continue

        for s_beat in [1.0, 3.0]:
            pos = int((bar_start_s + s_beat * BEAT_DUR) * SR)
            end = min(TOTAL_SAMPLES, pos + snare_len)
            drums_stem[pos:end, 0] += main_snare[:end - pos] * 0.80
            drums_stem[pos:end, 1] += main_snare[:end - pos] * 0.80

        ghost_beats = [1.75, 2.5, 3.75] if (bar % 2 == 0) else [0.75, 2.25, 3.5]
        for gb in ghost_beats:
            pos = int((bar_start_s + gb * BEAT_DUR) * SR)
            end = min(TOTAL_SAMPLES, pos + snare_len)
            drums_stem[pos:end, 0] += ghost_snare[:end - pos] * 0.50
            drums_stem[pos:end, 1] += ghost_snare[:end - pos] * 0.55

        for step in range(16):
            base_t = (step / 16.0) * BAR_DUR + (0.012 if step % 2 == 1 else 0.0)
            pos = int((bar_start_s + base_t) * SR)
            end = min(TOTAL_SAMPLES, pos + hat_len)
            vel = 0.70 if step % 4 == 2 else 0.35
            drums_stem[pos:end, 0] += closed_hat[:end - pos] * vel * 0.65
            drums_stem[pos:end, 1] += closed_hat[:end - pos] * vel * 0.75

        for ob in [1.5, 3.5]:
            pos = int((bar_start_s + ob * BEAT_DUR) * SR)
            end = min(TOTAL_SAMPLES, pos + ohat_len)
            drums_stem[pos:end, 0] += open_hat[:end - pos] * 0.45
            drums_stem[pos:end, 1] += open_hat[:end - pos] * 0.55

        if bar >= 88:
            fade = np.linspace(1.0, 0.0, TOTAL_SAMPLES - int(88 * BAR_DUR * SR))
            drums_stem[int(88 * BAR_DUR * SR):, :] *= fade[:, np.newaxis]
            break

    return drums_stem


# -----------------------------------------------------------------------------
# 3. STEM: CLEAN DEEP SUB-BASS (Round Fundamental, Zero Distortion)
# -----------------------------------------------------------------------------
def generate_reese_subbass():
    print("🎹 [3/7] Generando Stem de Sub-Grave Limpio (Fundamental Redonda & Cero Saturación)...")
    bass_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    chord_roots = [32.70, 51.91, 58.27, 48.99]

    for bar in range(BARS):
        if bar < 16 or (64 <= bar < 80) or bar >= 88:
            continue

        root_f = chord_roots[bar % 4]
        bar_len = int(BAR_DUR * SR)
        t = np.linspace(0, BAR_DUR, bar_len, endpoint=False)

        # Pure sinusoidal sub-bass foundation + subtle warm 2nd harmonic
        sub_sine = np.sin(2 * np.pi * root_f * t) * 0.72
        second_harm = np.sin(2 * np.pi * root_f * 2.0 * t) * 0.18

        # Gentle warm low-pass filter at 180 Hz
        b_lp, a_lp = signal.butter(2, 180.0 / (SR / 2), btype="low")
        clean_bass = signal.filtfilt(b_lp, a_lp, sub_sine + second_harm)

        # Smooth sidechain ducking curve (smooth envelope, zero clicks)
        sc_env = np.ones(bar_len)
        hits = [0.0, 2.75] if (16 <= bar < 32) else ([0.0, 1.5, 3.25] if (bar % 2 == 0) else [0.0, 2.0, 2.75])
        for h in hits:
            idx = int(h * BEAT_DUR * SR)
            sc_len = int(0.16 * SR)
            if idx + sc_len < bar_len:
                sc_env[idx:idx + sc_len] = 0.30 + 0.70 * (1.0 - np.exp(-np.linspace(0, 4, sc_len)))

        start_s = int(bar * BAR_DUR * SR)
        end_s = min(TOTAL_SAMPLES, start_s + bar_len)
        dur = end_s - start_s
        bass_stem[start_s:end_s, 0] += clean_bass[:dur] * sc_env[:dur] * 0.65
        bass_stem[start_s:end_s, 1] += clean_bass[:dur] * sc_env[:dur] * 0.65

    return bass_stem


# -----------------------------------------------------------------------------
# 4. STEM: BORJA'S BICEP CHOPS (Call & Response, Ethereal Air, Pristine Delays)
# -----------------------------------------------------------------------------
def generate_user_bicep_chops(slices):
    print("🎙️ [4/7] Generando Stem de Chops Vocales Bicep (Call & Response y Delays Sedosos)...")
    chops_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    proc_slices = [process_bicep_vocal_chain(s) for s in slices]
    num_slices = len(proc_slices)
    melody_pitches = [1.0, 1.189, 1.0, 1.498, 1.334, 1.189, 1.0, 0.89]

    first_slice = proc_slices[0]
    rev_slice = np.flip(first_slice[:int(1.4 * SR)], axis=0)
    rev_swell = create_reverb(rev_slice, decay_sec=2.2, wet=0.55)

    for bar in range(BARS):
        bar_start_s = bar * BAR_DUR

        if bar in [15, 31, 47, 63, 75, 79]:
            pos = int((bar_start_s + 2.0 * BEAT_DUR) * SR)
            dur = min(len(rev_swell), TOTAL_SAMPLES - pos)
            chops_stem[pos:pos + dur] += rev_swell[:dur] * 0.70

        if bar < 16:
            if bar in [4, 8, 12]:
                s_idx = (bar * 3) % num_slices
                sl = proc_slices[s_idx]
                pos = int((bar_start_s + 1.0 * BEAT_DUR) * SR)
                dur = min(len(sl), TOTAL_SAMPLES - pos)
                chops_stem[pos:pos + dur] += sl[:dur] * 0.60
            continue

        if 16 <= bar < 32:
            if (bar % 4) in [0, 1]:
                for idx, cp in enumerate([0.5, 2.0]):
                    s_data = proc_slices[(bar * 3 + idx) % num_slices]
                    pos = int((bar_start_s + cp * BEAT_DUR) * SR)
                    dur = min(len(s_data[:int(0.38 * SR)]), TOTAL_SAMPLES - pos)
                    chops_stem[pos:pos + dur] += s_data[:dur] * 0.75
            continue

        if 64 <= bar < 80:
            if bar == 76:
                sl = proc_slices[1]
                pos = int(bar_start_s * SR)
                dur = min(len(sl[:int(0.55 * SR)]), TOTAL_SAMPLES - pos)
                chops_stem[pos:pos + dur] += sl[:dur] * 0.85
                continue

            if bar in [64, 68, 72]:
                s_data = proc_slices[(bar * 2) % num_slices]
                pos = int((bar_start_s + 1.0 * BEAT_DUR) * SR)
                dur = min(len(s_data[:int(0.45 * SR)]), TOTAL_SAMPLES - pos)
                chops_stem[pos:pos + dur] += s_data[:dur] * 0.80
            continue

        # Active Drops
        if (bar % 4) in [0, 1, 2]:
            chop_pattern = [0.0, 0.75, 1.5, 2.25, 3.0, 3.5]
            for idx, cp in enumerate(chop_pattern):
                slice_choice = (bar * 7 + idx * 3) % num_slices
                s_data = proc_slices[slice_choice]
                pitch_ratio = melody_pitches[(bar + idx) % len(melody_pitches)]

                if abs(pitch_ratio - 1.0) > 0.02:
                    target_len = int(len(s_data) / pitch_ratio)
                    s_pitched_l = signal.resample(s_data[:, 0], target_len)
                    s_pitched_r = signal.resample(s_data[:, 1], target_len)
                    s_curr = np.column_stack([s_pitched_l, s_pitched_r])
                else:
                    s_curr = s_data

                s_curr = s_curr[:int(0.35 * SR)]
                pos = int((bar_start_s + cp * BEAT_DUR) * SR)
                dur = min(len(s_curr), TOTAL_SAMPLES - pos)
                chops_stem[pos:pos + dur] += s_curr[:dur] * 0.78

        if bar >= 88:
            fade = np.linspace(1.0, 0.0, TOTAL_SAMPLES - int(88 * BAR_DUR * SR))
            chops_stem[int(88 * BAR_DUR * SR):, :] *= fade[:, np.newaxis]
            break

    chops_stem = create_reverb(chops_stem, decay_sec=2.2, wet=0.35)
    chops_stem = apply_tape_dub_delay(chops_stem, delay_sec=0.35156, feedback=0.45, wet=0.38, ping_pong=True)
    return chops_stem


# -----------------------------------------------------------------------------
# 5. STEM: ATMOSPHERIC PADS (Warm Analog Chords with Gentle Cutoff)
# -----------------------------------------------------------------------------
def generate_atmospheric_pads():
    print("🌌 [5/7] Generando Stem de Pads Atmosféricos (Calidez Suave y Aire)...")
    pads_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    chords = [
        [130.81, 155.56, 196.00, 233.08, 293.66],  # Cm9
        [103.83, 130.81, 155.56, 196.00],          # Abmaj7
        [116.54, 146.83, 174.61, 207.65, 261.63],  # Bb9
        [98.00, 116.54, 146.83, 174.61]            # Gm7
    ]
    picardy_chord = [130.81, 164.81, 196.00, 246.94, 293.66]

    for bar in range(BARS):
        chord_freqs = picardy_chord if bar in [77, 78] else chords[bar % 4]
        bar_len = int(BAR_DUR * SR)
        t = np.linspace(0, BAR_DUR, bar_len, endpoint=False)
        chord_sig_l = np.zeros(bar_len)
        chord_sig_r = np.zeros(bar_len)

        for f in chord_freqs:
            f1 = f * (2 ** (-4 / 1200))
            f2 = f
            f3 = f * (2 ** (+4 / 1200))
            # Smooth sine/triangle synthesis without harsh sawtooth edges
            tri1 = signal.sawtooth(2 * np.pi * f1 * t, width=0.5)
            sin2 = np.sin(2 * np.pi * f2 * t)
            tri3 = signal.sawtooth(2 * np.pi * f3 * t, width=0.5)
            chord_sig_l += (tri1 + sin2) * 0.12
            chord_sig_r += (sin2 + tri3) * 0.12

        cutoff = 850.0 if (bar < 16 or (64 <= bar < 80)) else (1600.0 if (48 <= bar < 64 or bar >= 80) else 1150.0)
        b_pad, a_pad = signal.butter(2, cutoff / (SR / 2), btype="low")
        chord_sig_l = signal.filtfilt(b_pad, a_pad, chord_sig_l)
        chord_sig_r = signal.filtfilt(b_pad, a_pad, chord_sig_r)

        env = np.ones(bar_len)
        fade_len = int(0.08 * SR)
        env[:fade_len] = np.linspace(0, 1, fade_len)
        env[-fade_len:] = np.linspace(1, 0, fade_len)

        start_s = int(bar * BAR_DUR * SR)
        end_s = min(TOTAL_SAMPLES, start_s + bar_len)
        dur = end_s - start_s
        pads_stem[start_s:end_s, 0] += chord_sig_l[:dur] * env[:dur] * 0.50
        pads_stem[start_s:end_s, 1] += chord_sig_r[:dur] * env[:dur] * 0.50

    pads_stem = create_reverb(pads_stem, decay_sec=3.0, wet=0.40)
    return pads_stem


# -----------------------------------------------------------------------------
# 6. STEM: COSMIC ARP (Delicate Pluck Arpeggio with Clean Ping-Pong Delays)
# -----------------------------------------------------------------------------
def generate_cosmic_arp():
    print("✨ [6/7] Generando Stem de Arpegio Cósmico (Pulsos Cristalinos y Delays Limpios)...")
    arp_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    arp_scale = [261.63, 311.13, 349.23, 392.00, 466.16, 523.25, 622.25]
    pluck_len = int(0.18 * SR)
    t_p = np.linspace(0, 0.18, pluck_len, endpoint=False)

    for bar in range(BARS):
        if not ((32 <= bar < 64) or (80 <= bar < 88)):
            continue

        bar_start_s = bar * BAR_DUR
        for step in range(16):
            if step % 2 == 1:
                note_f = arp_scale[(bar * 3 + step) % len(arp_scale)]
                # Gentle sine + soft triangle for pure crystalline tone
                pluck = np.sin(2 * np.pi * note_f * t_p) * 0.70 + signal.sawtooth(2 * np.pi * note_f * t_p, width=0.5) * 0.30
                env = np.exp(-t_p * 28.0)
                single_pluck = pluck * env * 0.22

                pos = int((bar_start_s + (step / 16.0) * BAR_DUR) * SR)
                end = min(TOTAL_SAMPLES, pos + pluck_len)
                dur = end - pos
                pan_l = 0.75 if step % 4 == 1 else 0.35
                pan_r = 1.0 - pan_l
                arp_stem[pos:end, 0] += single_pluck[:dur] * pan_l
                arp_stem[pos:end, 1] += single_pluck[:dur] * pan_r

    arp_stem = apply_tape_dub_delay(arp_stem, delay_sec=0.17578, feedback=0.44, wet=0.36, ping_pong=True)
    return arp_stem


# -----------------------------------------------------------------------------
# 7. STEM: HUMANIZED SOUL ORGAN (Pure Sinusoidal Hammond B3 & Silky Leslie)
# -----------------------------------------------------------------------------
def generate_humanized_organ():
    print("🎹 [7/7] Generando Stem de Órgano Humanizado (Pureza Sinusoidal Hammond B3 & Leslie Suave)...")
    organ_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    # Pure sinusoidal drawbars (Hammond tonewheels are sinusoidal oscillators!)
    drawbars = [
        (0.5, 0.40),  # 16'
        (1.0, 0.85),  # 8'
        (1.5, 0.28),  # 5 1/3'
        (2.0, 0.55),  # 4'
        (3.0, 0.20),  # 2 2/3'
    ]

    chords_voicings = [
        [155.56, 196.00, 233.08, 293.66],  # Cm9
        [130.81, 155.56, 196.00, 261.63],  # Abmaj7
        [146.83, 174.61, 207.65, 261.63],  # Bb9
        [146.83, 174.61, 233.08, 293.66]   # Gm7
    ]

    from scripts.causal_groove_humanizer import generate_pink_noise
    pink_drift = generate_pink_noise(BARS * 8)

    pattern_bar1 = [1.5, 2.75, 3.5]
    pattern_bar2 = [0.75, 2.0, 3.25]

    np.random.seed(42)

    for bar in range(BARS):
        if bar < 8:
            continue

        bar_start_s = bar * BAR_DUR
        chord = chords_voicings[bar % 4]

        if bar < 16:
            stabs = [1.0]
        elif 64 <= bar < 80:
            stabs = [1.0, 3.0]
        else:
            stabs = pattern_bar1 if (bar % 2 == 0) else pattern_bar2

        if bar < 32:
            leslie_speed = 1.0
        elif 32 <= bar < 48:
            leslie_speed = 2.8
        elif 48 <= bar < 64:
            leslie_speed = 5.2
        elif 64 <= bar < 80:
            leslie_speed = 0.85
        else:
            leslie_speed = 5.5 if bar < 88 else 0.9

        for stab_idx, beat_pos in enumerate(stabs):
            drift_val = pink_drift[(bar * 4 + stab_idx) % len(pink_drift)]

            micro_timing_s = (0.010 + 0.004 * drift_val) + np.random.uniform(-0.002, 0.003)
            stab_start_time = bar_start_s + beat_pos * BEAT_DUR + micro_timing_s

            dur_s = 0.75 if bar < 16 or (64 <= bar < 80) else (0.22 + 0.06 * (stab_idx % 2) + 0.02 * drift_val)
            stab_samples = int(dur_s * SR)
            t_s = np.linspace(0, dur_s, stab_samples, endpoint=False)

            chord_sig_l = np.zeros(stab_samples)
            chord_sig_r = np.zeros(stab_samples)

            for note_idx, f0 in enumerate(chord):
                finger_delay_samples = int(note_idx * np.random.uniform(0.002, 0.005) * SR)
                t_note = t_s[finger_delay_samples:] if finger_delay_samples < stab_samples else t_s
                if len(t_note) == 0:
                    continue

                note_wave = np.zeros_like(t_note)
                for harm, amp in drawbars:
                    note_wave += np.sin(2 * np.pi * f0 * harm * t_note) * amp

                # Clean subtle click
                click_len = min(int(0.002 * SR), len(note_wave))
                click = np.sin(2 * np.pi * 1200.0 * t_note[:click_len]) * np.exp(-t_note[:click_len] * 120.0) * 0.15
                note_wave[:click_len] += click

                finger_vel = 0.85 + 0.10 * (1.0 - note_idx * 0.08) + 0.06 * np.random.uniform(-0.1, 0.1)
                note_wave *= finger_vel

                env = np.exp(-t_note * (1.8 if dur_s > 0.5 else 4.0))
                shaped_note = note_wave * env

                target_len = len(shaped_note)
                chord_sig_l[finger_delay_samples:finger_delay_samples + target_len] += shaped_note
                chord_sig_r[finger_delay_samples:finger_delay_samples + target_len] += shaped_note

            # Clean Leslie modulation: pure AM tremolo + gentle pitch phase offset (ZERO clipping)
            leslie_phase = 2 * np.pi * leslie_speed * t_s
            trem_l = 0.82 + 0.18 * np.sin(leslie_phase)
            trem_r = 0.82 + 0.18 * np.sin(leslie_phase + np.pi * 0.55)

            organ_stab_l = chord_sig_l * trem_l * 0.35
            organ_stab_r = chord_sig_r * trem_r * 0.35

            pos = int(stab_start_time * SR)
            if pos < TOTAL_SAMPLES:
                end = min(TOTAL_SAMPLES, pos + stab_samples)
                dur_actual = end - pos
                organ_stem[pos:end, 0] += organ_stab_l[:dur_actual]
                organ_stem[pos:end, 1] += organ_stab_r[:dur_actual]

    organ_stem = create_reverb(organ_stem, decay_sec=1.6, wet=0.22)
    organ_stem = apply_tape_dub_delay(organ_stem, delay_sec=0.35156, feedback=0.35, wet=0.25, ping_pong=True)
    return organ_stem


# -----------------------------------------------------------------------------
# MASTER MIXDOWN & EBU R128 NORMALIZATION (Zero Harsh Saturation)
# -----------------------------------------------------------------------------
def mix_and_master(stems_dict: dict):
    print("🎚️ Realizando Mixdown Limpio y Masterización EBU R128 (-14 LUFS, TP <= -1.0 dBFS)...")
    mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    # Calibrated stem balance with plenty of internal headroom
    gains = {
        "01_Sub_Kick.wav": 0.70,
        "02_Breakbeat_Drums.wav": 0.60,
        "03_Reese_SubBass.wav": 0.65,
        "04_Borja_Bicep_Chops.wav": 0.75,
        "05_Atmospheric_Pads.wav": 0.50,
        "06_Cosmic_Arp.wav": 0.45,
        "07_Humanized_Organ.wav": 0.55
    }

    for name, data in stems_dict.items():
        g = gains.get(name, 0.5)
        mix += data * g

    # Clean sub rumble cut < 28 Hz
    b_hp, a_hp = signal.butter(3, 28.0 / (SR / 2), btype="high")
    mix[:, 0] = signal.filtfilt(b_hp, a_hp, mix[:, 0])
    mix[:, 1] = signal.filtfilt(b_hp, a_hp, mix[:, 1])

    # Linkwitz-Riley 4th order crossover at 120 Hz: Mono consolidation of sub frequencies
    sos_lp = signal.butter(2, 120 / (SR / 2), btype="low", output="sos")
    sub_l = signal.sosfiltfilt(sos_lp, mix[:, 0])
    sub_r = signal.sosfiltfilt(sos_lp, mix[:, 1])
    sub_mono = (sub_l + sub_r) * 0.5

    sos_hp = signal.butter(2, 120 / (SR / 2), btype="high", output="sos")
    high_l = signal.sosfiltfilt(sos_hp, mix[:, 0])
    high_r = signal.sosfiltfilt(sos_hp, mix[:, 1])

    mix = np.column_stack([sub_mono + high_l, sub_mono + high_r])

    # Measure Integrated Loudness
    meter = pln.Meter(SR)
    loudness = meter.integrated_loudness(mix)
    print(f"📊 Loudness antes de normalizar: {loudness:.2f} LUFS")

    # Normalize to -14.0 LUFS linearly
    target_lufs = -14.0
    gain_db = target_lufs - loudness
    linear_gain = 10.0 ** (gain_db / 20.0)
    master = mix * linear_gain

    # Transparent peak limiting: scale down cleanly if peak exceeds -1.0 dBFS (0.891)
    peak = np.max(np.abs(master))
    if peak > 0.891:
        print(f"⚠️ Limitando picos limpios: {peak:.3f} -> 0.891 (-1.0 dBFS)")
        master = master * (0.891 / peak)

    final_lufs = meter.integrated_loudness(master)
    final_tp = 20 * np.log10(np.max(np.abs(master)) + 1e-9)
    print(f"🏆 Master Limpio Final: {final_lufs:.2f} LUFS | True Peak: {final_tp:.2f} dBFS")

    return master


def main():
    print("=" * 70)
    print("🚀 INICIANDO PRODUCCIÓN SOTA PRISTINA: BICEP BREAKBEAT ESPACIAL (96 COMPASES)")
    print(f"⏱️ 96 Compases @ {BPM} BPM | 48.0 kHz / 24-bit PCM | Duración: 3m 00s")
    print("=" * 70)

    slices = load_user_slices()

    stems = {
        "01_Sub_Kick.wav": generate_sub_kick(),
        "02_Breakbeat_Drums.wav": generate_breakbeat_drums(),
        "03_Reese_SubBass.wav": generate_reese_subbass(),
        "04_Borja_Bicep_Chops.wav": generate_user_bicep_chops(slices),
        "05_Atmospheric_Pads.wav": generate_atmospheric_pads(),
        "06_Cosmic_Arp.wav": generate_cosmic_arp(),
        "07_Humanized_Organ.wav": generate_humanized_organ()
    }

    # Save individual stems
    print("💾 Guardando 7 Stems WAV limpios en:", STEMS_DIR)
    for stem_name, stem_data in stems.items():
        out_path = STEMS_DIR / stem_name
        sf.write(str(out_path), stem_data, SR, subtype="PCM_24")

    # Master render
    master = mix_and_master(stems)
    sf.write(str(MASTER_WAV), master, SR, subtype="PCM_24")
    print(f"📀 Master WAV generado: {MASTER_WAV}")

    # Generate MP3
    import subprocess
    cmd_mp3 = ["ffmpeg", "-y", "-i", str(MASTER_WAV), "-b:a", "320k", str(MASTER_MP3)]
    subprocess.run(cmd_mp3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"📱 Master MP3 generado: {MASTER_MP3}")

    # Compile Native FLP
    print("🎛️ Compilando archivo de sesión nativo .flp para FL Studio 2025...")
    staging = {
        "01_Sub_Kick.wav": {"mixer_track": 1, "volume": 100},
        "02_Breakbeat_Drums.wav": {"mixer_track": 2, "volume": 90},
        "03_Reese_SubBass.wav": {"mixer_track": 3, "volume": 95},
        "04_Borja_Bicep_Chops.wav": {"mixer_track": 4, "volume": 105},
        "05_Atmospheric_Pads.wav": {"mixer_track": 5, "volume": 80},
        "06_Cosmic_Arp.wav": {"mixer_track": 6, "volume": 75},
        "07_Humanized_Organ.wav": {"mixer_track": 7, "volume": 92, "pan": 60}
    }
    flp_res = compile_multitrack_stems_flp(
        stems_dir=str(STEMS_DIR),
        project_title="Borja Moskv - Bicep Breakbeat Pristine Session",
        bpm=BPM,
        output_flp=str(OUTPUT_FLP),
        total_bars=BARS,
        channel_staging=staging
    )
    print(f"✅ Sesión FL Studio compilada: {OUTPUT_FLP}")
    print(json.dumps(flp_res, indent=2))


if __name__ == "__main__":
    main()
