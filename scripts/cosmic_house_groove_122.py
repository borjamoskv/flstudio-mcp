#!/usr/bin/env python3
"""
COSMIC HOUSE GROOVE (122 BPM · G Dorian / Gm9 -> C9 -> Ebmaj9 -> Dm7 · 48 kHz / 24-bit · 64 Bars)
==================================================================================================
Sovereign C5-REAL Production Engine integrating Satin Jackets warmth, Maceo Plex sub weight,
and AIR atmospheric expanse across the full arrangement arc:

  - Intro (Bars 1-16)     : Pulsating 4-on-the-floor kicks (49.0 Hz G1 anchor), syncopated
                            behind-the-beat analog bass (+6 ms pocket), retro-futuristic synth arps.
  - Verse 1 (Bars 17-24)  : Floats on airy electric keys (Rhodes micro-strum) and subtle pads.
  - Pre-Chorus 1 (25-32)  : Filtered disco guitars (waveguide funk strums + sweeping resonant
                            filter) accenting the build alongside rising synth arps & tension.
  - Drop 1 (Bars 33-44)   : Unleashes swirling phase-coherent analog leads and dynamic percussion
                            (ModeAudio round-robin + modal groove pocket) over cosmic groove.
  - Verse 2 (Bars 45-52)  : Airy keys and subtle cosmic pads with warm non-commutative dub tails.
  - Pre-Chorus 2 (53-60)  : Filtered disco guitars return + rising arp; Bar 60 beats 3-4 enforce
                            the deterministic False Drop vacuum (-57 dBFS tape bed + dub echo tail).
  - Drop 2 (Bars 61-64)   : Bold cosmic groove climax with swirling analog leads + full percussion,
                            terminating in Bar 64 with a calibrated RC Living Exit to exact 0.0.

Outputs (Bare-Metal Triad + FL Studio Native Assets):
  - Master WAV (48 kHz / 24-bit) + Premaster WAV + optional 320 kbps CBR MP3
  - 10 discrete 48 kHz / 24-bit multitrack stems in `stems/`
  - Multichannel SMF Type 1 MIDI (`480 PPQ`, zero cumulative delta drift, section markers)
  - Compiled native FL Studio project (`.flp`) via `flp_multitrack_stem_compiler`
  - Native FL Studio `.pyscript` (syntax-checked via `ast.parse`) + Scala tuning `.scl`
  - `production_receipt.json` with SHA-256 digests, Zero-Crackle & Rubin Gate audits.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import mido
import numpy as np
from scipy import signal

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.bounces_paths import resolve_bounces_dir, resolve_fl_user_dir  # noqa: E402
from scripts.c5_dsp_core import (  # noqa: E402
    SAMPLE_RATE as CORE_SR,
    apply_coherent_shared_room,
    apply_noncommutative_dub_echo,
    apply_zero_crackle_envelope,
    build_coupled_multiband_sidechain,
    carve_polyphonic_mud,
    check_zero_crackle_derivatives,
    enforce_low_end_mono,
    freeze_array,
    generate_warm_analog_tape_bed,
    lr4_zero_phase_crossover,
    make_time_axis,
    oversampled_soft_saturate,
    polyblep_pulse,
    polyblep_saw,
    synthesize_phase_locked_kick,
    write_pcm_wav,
)
from scripts.c5_real_assets_bridge import (  # noqa: E402
    get_real_room_ir,
    get_round_robin_drum_pool,
    shape_velocity_sample,
)
from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp  # noqa: E402
from scripts.mastering_reverse_engine_fl import (  # noqa: E402
    compute_rubin_metrics,
    load_wav_stereo,
    master_audio_reverse_engineered,
)

SAMPLE_RATE = CORE_SR  # 48000 Hz
DEFAULT_BPM = 122.0
DEFAULT_TOTAL_BARS = 64
RUBIN_LINTER_PATH = (
    Path.home()
    / ".gemini/config/skills/c5-rubin-acoustic-linter/scripts/audit_acoustic_exergy.py"
)

# G Dorian Cosmic Chord Cycle: Gm9 -> C9 -> Ebmaj9 -> Dm7(add11)
CHORD_PROGRESSION: Tuple[Dict[str, Any], ...] = (
    {
        "name": "Gm9",
        "bass_root": 31,  # G1 = 49.00 Hz (48-55 Hz club kick anchor)
        "bass_alt": 43,   # G2 = 98.00 Hz
        "keys": (55, 58, 62, 65, 69),
        "pad": (55, 62, 65, 69, 74),
        "guitar": (55, 58, 62, 65),
        "arp": (55, 58, 62, 65, 67, 69, 74),
    },
    {
        "name": "C9",
        "bass_root": 36,  # C2 = 65.41 Hz
        "bass_alt": 48,   # C3 = 130.81 Hz
        "keys": (52, 55, 58, 62, 69),
        "pad": (55, 60, 62, 67, 72),
        "guitar": (55, 58, 62, 64),
        "arp": (55, 58, 60, 62, 64, 67, 72),
    },
    {
        "name": "Ebmaj9",
        "bass_root": 39,  # Eb2 = 77.78 Hz
        "bass_alt": 51,   # Eb3 = 155.56 Hz
        "keys": (51, 55, 58, 62, 65),
        "pad": (51, 58, 62, 65, 70),
        "guitar": (55, 58, 62, 67),
        "arp": (55, 58, 62, 65, 67, 70, 74),
    },
    {
        "name": "Dm7add11",
        "bass_root": 38,  # D2 = 73.42 Hz
        "bass_alt": 50,   # D3 = 146.83 Hz
        "keys": (50, 53, 57, 60, 67),
        "pad": (50, 57, 60, 65, 69),
        "guitar": (53, 57, 60, 67),
        "arp": (53, 57, 60, 62, 65, 67, 72),
    },
)

SECTION_LAYOUT: Tuple[Dict[str, Any], ...] = (
    {"id": "intro", "name": "Intro (Kicks + Sync Bass + Retro Arps)", "start_bar": 0, "bars": 16},
    {"id": "verse_1", "name": "Verse 1 (Airy Keys + Subtle Pads)", "start_bar": 16, "bars": 8},
    {"id": "pre_chorus_1", "name": "Pre-Chorus 1 (Filtered Disco Guitars)", "start_bar": 24, "bars": 8},
    {"id": "drop_1", "name": "Drop 1 (Swirling Analog Leads + Dynamic Percussion)", "start_bar": 32, "bars": 12},
    {"id": "verse_2", "name": "Verse 2 (Airy Keys + Subtle Pads)", "start_bar": 44, "bars": 8},
    {"id": "pre_chorus_2", "name": "Pre-Chorus 2 (Filtered Disco Guitars + False Drop Bar 60)", "start_bar": 52, "bars": 8},
    {"id": "drop_2", "name": "Drop 2 (Cosmic Groove Climax + Living Exit)", "start_bar": 60, "bars": 4},
)


def midi_to_hz(note: float) -> float:
    """Converts MIDI note number (may be fractional) to Hz at A4 = 440 Hz."""
    return 440.0 * (2.0 ** ((float(note) - 69.0) / 12.0))


def _sha256_file(path: Path) -> str:
    """Computes SHA-256 hex digest for verifiable provenance."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _voss_clarke_1f_drift(n_points: int, seed: int = 1220) -> np.ndarray:
    """Generates smooth deterministic 1/f pink-noise timing/velocity drift in [-1, 1]."""
    rng = np.random.default_rng(seed)
    octaves = 5
    acc = np.zeros(n_points, dtype=np.float64)
    for k in range(octaves):
        step = max(1, n_points // (2 ** (k + 2)))
        knots = rng.uniform(-1.0, 1.0, max(2, step + 1))
        x_old = np.linspace(0.0, 1.0, len(knots), dtype=np.float64)
        x_new = np.linspace(0.0, 1.0, n_points, dtype=np.float64)
        acc += np.interp(x_new, x_old, knots) / (k + 1.0)
    peak = float(np.max(np.abs(acc)))
    out = acc / max(peak, 1e-9)
    return freeze_array(out)


def _morphing_resonant_filter(
    sig: np.ndarray,
    cutoff_hz: np.ndarray,
    band_edges: Sequence[float] = (280.0, 680.0, 1600.0, 3600.0, 7400.0),
    resonance_q: float = 1.8,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """
    Smooth, zipper-free, zero-crackle sweeping resonant lowpass filter via continuous
    crossfaded parallel 4-pole Butterworth bands with subtle analog resonance bump.
    """
    x = np.asarray(sig, dtype=np.float64)
    fc = np.asarray(cutoff_hz, dtype=np.float64)
    edges = np.asarray(band_edges, dtype=np.float64)
    nyq = 0.5 * float(sample_rate)

    bands: List[np.ndarray] = []
    for edge in edges:
        wn = float(np.clip(edge / nyq, 0.002, 0.94))
        sos_lp = signal.butter(4, wn, btype="low", output="sos")
        y_lp = signal.sosfilt(sos_lp, x)
        if resonance_q > 1.05:
            bw = float(np.clip(wn / max(resonance_q, 1.1), 0.002, 0.35))
            lo = float(np.clip(wn * 0.78, 0.002, 0.90))
            hi = float(np.clip(wn * 1.15 + bw * 0.25, lo + 0.004, 0.96))
            sos_bp = signal.butter(2, [lo, hi], btype="bandpass", output="sos")
            y_lp = y_lp + min(0.32, 0.14 * (resonance_q - 1.0)) * signal.sosfilt(sos_bp, x)
        bands.append(y_lp)

    fc_clipped = np.clip(fc, float(edges[0]), float(edges[-1]))
    pos = np.interp(fc_clipped, edges, np.arange(len(edges), dtype=np.float64))
    idx_lo = np.clip(np.floor(pos).astype(np.int64), 0, len(edges) - 2)
    frac = pos - idx_lo

    out = np.zeros_like(x)
    for b_idx in range(len(edges) - 1):
        mask = idx_lo == b_idx
        if np.any(mask):
            w = frac[mask]
            out[mask] = (1.0 - w) * bands[b_idx][mask] + w * bands[b_idx + 1][mask]
    return out


def _apply_smooth_gate_window(
    l_buf: np.ndarray,
    r_buf: np.ndarray,
    start_sample: int,
    end_sample: int,
    target_gain: float = 0.0,
    ramp_ms: float = 12.0,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """Applies a raised-cosine attenuation window cleanly without sample discontinuities."""
    n = len(l_buf)
    s0 = max(0, min(n, int(start_sample)))
    s1 = max(s0, min(n, int(end_sample)))
    if s1 <= s0:
        return l_buf, r_buf
    ramp = max(8, min((s1 - s0) // 3, int(round(ramp_ms * 0.001 * sample_rate))))
    gate = np.ones(s1 - s0, dtype=np.float64) * float(target_gain)
    t_in = np.linspace(0.0, math.pi, ramp, dtype=np.float64)
    ramp_down = 0.5 * (1.0 + np.cos(t_in)) * (1.0 - target_gain) + target_gain
    ramp_up = 0.5 * (1.0 - np.cos(t_in)) * (1.0 - target_gain) + target_gain
    gate[:ramp] = ramp_down
    gate[-ramp:] = ramp_up
    out_l = l_buf.copy()
    out_r = r_buf.copy()
    out_l[s0:s1] *= gate
    out_r[s0:s1] *= gate
    return out_l, out_r


def _apply_living_exit_rc(
    l_buf: np.ndarray,
    r_buf: np.ndarray,
    exit_start_sample: int,
    tau_sec: float = 0.52,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """Applies exponential RC capacitor discharge fade ending cleanly at exact 0.0."""
    n = len(l_buf)
    s0 = max(0, min(n - 1, int(exit_start_sample)))
    tail_len = n - s0
    if tail_len < 16:
        return l_buf, r_buf
    t_tail = make_time_axis(tail_len, sample_rate)
    rc_curve = np.exp(-t_tail / max(tau_sec, 0.05))
    # Smooth zero-crossing taper over final 65 ms so exact sample[-1] == 0.0
    zero_n = min(tail_len, int(0.065 * sample_rate))
    rc_curve[-zero_n:] *= 0.5 * (1.0 + np.cos(np.linspace(0.0, math.pi, zero_n, dtype=np.float64)))
    rc_curve[-1] = 0.0
    out_l = l_buf.copy()
    out_r = r_buf.copy()
    out_l[s0:] *= rc_curve
    out_r[s0:] *= rc_curve
    return out_l, out_r


def _safe_mix_add(dst: np.ndarray, start: int, src: np.ndarray, gain: float = 1.0) -> None:
    """Safely accumulates `src * gain` into `dst[start:start+len(src)]` without overflow."""
    if start >= len(dst) or len(src) == 0:
        return
    if start < 0:
        src = src[-start:]
        start = 0
    end = min(len(dst), start + len(src))
    if end <= start:
        return
    dst[start:end] += src[: end - start] * float(gain)


def _normalize_peak(l_buf: np.ndarray, r_buf: np.ndarray, target_peak: float) -> Tuple[np.ndarray, np.ndarray]:
    """Linearly scales a stereo buffer to a ceiling peak without soft/hard clipping."""
    peak = max(float(np.max(np.abs(l_buf))), float(np.max(np.abs(r_buf))), 1e-12)
    scale = float(target_peak) / peak
    return freeze_array(l_buf * scale), freeze_array(r_buf * scale)


def _bandlimit_for_zero_crackle(
    l_buf: np.ndarray,
    r_buf: np.ndarray,
    cutoff_hz: float,
    max_d1: float = 0.014,
    max_d2: float = 0.0046,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """Lowpasses gently and applies calibrated scalar headroom if needed for Zero-Crackle safety."""
    sos = signal.butter(4, min(0.45 * sample_rate, float(cutoff_hz)) / (0.5 * sample_rate), btype="low", output="sos")
    out_l = signal.sosfiltfilt(sos, l_buf)
    out_r = signal.sosfiltfilt(sos, r_buf)
    d1 = max(float(np.max(np.abs(np.diff(out_l)))), float(np.max(np.abs(np.diff(out_r)))))
    d2 = max(float(np.max(np.abs(np.diff(out_l, n=2)))), float(np.max(np.abs(np.diff(out_r, n=2)))))
    scale = min(
        1.0,
        (max_d1 / max(d1, 1e-9)),
        (max_d2 / max(d2, 1e-9)),
    )
    if scale < 1.0:
        out_l = out_l * scale
        out_r = out_r * scale
    return freeze_array(out_l), freeze_array(out_r)


def _synth_rhodes_airy_key(
    freq_hz: float,
    duration_sec: float,
    velocity: float = 0.85,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Synthesizes airy bell-tine electric piano (Rhodes) voice with organic harmonic bloom."""
    n = max(64, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    tw = 2.0 * math.pi * float(freq_hz)
    bell_mod = (0.35 + 0.75 * velocity) * np.exp(-t / 0.048) * np.sin(7.0 * tw * t)
    body = (
        0.64 * np.sin(tw * t + 0.16 * bell_mod) * np.exp(-t / 1.45)
        + 0.24 * np.sin(2.0 * tw * t) * np.exp(-t / 0.65)
        + 0.11 * np.sin(3.0 * tw * t) * np.exp(-t / 0.28)
        + 0.09 * np.sin(4.0 * tw * t) * np.exp(-t / 0.085)
    )
    return apply_zero_crackle_envelope(body, sample_rate=sample_rate, attack_ms=6.5, release_ms=28.0)


def _synth_karplus_guitar_note(
    freq_hz: float,
    duration_sec: float,
    brightness: float = 0.68,
    muted: bool = False,
    seed: int = 42,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """
    Synthesizes an authentic Nile-Rodgers-style electric guitar string via damped waveguide
    (Karplus-Strong comb decay + magnetic single-coil pickup formant).
    """
    n = max(64, int(round(duration_sec * sample_rate)))
    period = max(4, int(round(float(sample_rate) / max(float(freq_hz), 65.0))))
    rng = np.random.default_rng(seed)

    # Smooth bandlimited pick burst (avoids broadband white static in SFM audit)
    t_exc = make_time_axis(period, sample_rate)
    exc = (
        0.55 * np.sin(2.0 * math.pi * freq_hz * t_exc)
        + 0.30 * np.sin(4.0 * math.pi * freq_hz * t_exc + 0.4)
        + 0.15 * np.sin(6.0 * math.pi * freq_hz * t_exc)
        + 0.12 * rng.normal(0.0, 1.0, period)
    )
    exc = apply_zero_crackle_envelope(exc, sample_rate=sample_rate, attack_ms=1.5, release_ms=1.5)

    # Waveguide multi-cycle loop synthesized cleanly per period slice (fast in pure NumPy)
    damping = 0.72 if muted else float(np.clip(0.988 - 0.015 * (1.0 - brightness), 0.94, 0.992))
    out = np.zeros(n, dtype=np.float64)
    ring = exc.copy()
    pos = 0
    while pos < n:
        chunk = min(period, n - pos)
        out[pos : pos + chunk] = ring[:chunk]
        # Low-pass string nut reflection filter
        rolled = np.roll(ring, 1)
        ring = damping * ((0.55 + 0.25 * brightness) * ring + (0.45 - 0.25 * brightness) * rolled)
        pos += period

    t_all = make_time_axis(n, sample_rate)
    env_decay = np.exp(-t_all / (0.048 if muted else 0.34))
    out *= env_decay
    # Single-coil Strat position-4 notch resonance around 2.1 kHz, roll > 7.5 kHz
    sos_pick = signal.butter(2, [210.0 / (0.5 * sample_rate), 6800.0 / (0.5 * sample_rate)], btype="band", output="sos")
    out = signal.sosfilt(sos_pick, out)
    return apply_zero_crackle_envelope(out, sample_rate=sample_rate, attack_ms=4.5, release_ms=14.0)


def _synth_modal_percussion(
    kind: str,
    freq_hz: float,
    duration_sec: float,
    seed: int = 7,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """
    Synthesizes tonal modal percussion (`hat_closed`, `hat_open`, `clap`, `conga`, `rim`)
    focusing transient energy outside 500-5000 Hz broadband white noise so Bark SFM stays < 0.15.
    """
    n = max(48, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)
    rng = np.random.default_rng(seed)

    if kind in ("hat_closed", "hat_open"):
        # Roland TR-909 / CR-78 metallic inharmonic square/sine stack strictly > 6.2 kHz
        ratios = (1.0, 1.342, 1.483, 1.671, 2.043, 2.411)
        base = 6350.0
        sig = np.zeros(n, dtype=np.float64)
        for idx, ratio in enumerate(ratios):
            f = min(15800.0, base * ratio * (freq_hz / 6350.0 if freq_hz > 2000 else 1.0))
            sig += (1.0 / (1.0 + 0.25 * idx)) * np.sin(2.0 * math.pi * f * t + idx * 0.61)
        # Subtle high-shelf shimmer strictly > 6.8 kHz
        noise = rng.normal(0.0, 0.35, n)
        sos_hp = signal.butter(4, 6800.0 / (0.5 * sample_rate), btype="high", output="sos")
        sig = 0.68 * sig + 0.32 * signal.sosfilt(sos_hp, noise)
        tau = 0.028 if kind == "hat_closed" else 0.175
        sig *= np.exp(-t / tau)
        sig = signal.sosfilt(signal.butter(4, 5800.0 / (0.5 * sample_rate), btype="high", output="sos"), sig)
        return apply_zero_crackle_envelope(sig, sample_rate=sample_rate, attack_ms=1.8, release_ms=12.0)

    if kind == "clap":
        # Tight 3-microburst analog clap focused in narrow 1150 Hz + 2850 Hz body resonance
        sig = np.zeros(n, dtype=np.float64)
        offsets_ms = (0.0, 11.0, 23.0, 34.0)
        for b_idx, off_ms in enumerate(offsets_ms):
            s0 = int(round(off_ms * 0.001 * sample_rate))
            if s0 >= n:
                continue
            rem = n - s0
            t_b = make_time_axis(rem, sample_rate)
            tau_b = 0.011 if b_idx < 3 else 0.058
            burst = (
                0.55 * np.sin(2.0 * math.pi * 1180.0 * t_b + b_idx * 0.7)
                + 0.45 * np.sin(2.0 * math.pi * 2420.0 * t_b)
                + 0.25 * np.sin(2.0 * math.pi * 6450.0 * t_b)
                + 0.18 * rng.normal(0.0, 1.0, rem) * np.exp(-t_b / 0.006)
            )
            sig[s0:] += (0.75 if b_idx < 3 else 1.0) * burst * np.exp(-t_b / tau_b)
        sos_bp = signal.butter(2, [340.0 / (0.5 * sample_rate), 9500.0 / (0.5 * sample_rate)], btype="band", output="sos")
        sig = signal.sosfilt(sos_bp, sig)
        return apply_zero_crackle_envelope(sig, sample_rate=sample_rate, attack_ms=2.2, release_ms=18.0)

    if kind == "conga":
        # Expressive hand-drum membrane modes with subtle downward pitch bend
        f_inst = float(freq_hz) * (1.0 + 0.36 * np.exp(-t / 0.018))
        ph = 2.0 * math.pi * np.cumsum(f_inst) / float(sample_rate)
        sig = (
            0.78 * np.sin(ph) * np.exp(-t / 0.14)
            + 0.28 * np.sin(1.58 * ph + 0.3) * np.exp(-t / 0.075)
            + 0.14 * np.sin(2.14 * ph) * np.exp(-t / 0.032)
        )
        return apply_zero_crackle_envelope(sig, sample_rate=sample_rate, attack_ms=3.0, release_ms=16.0)

    # Default modal wood rim / clave tick
    sig = (
        0.72 * np.sin(2.0 * math.pi * freq_hz * t) * np.exp(-t / 0.022)
        + 0.34 * np.sin(2.0 * math.pi * freq_hz * 2.756 * t) * np.exp(-t / 0.009)
    )
    return apply_zero_crackle_envelope(sig, sample_rate=sample_rate, attack_ms=1.5, release_ms=10.0)


def _load_percussion_assets(sample_rate: int = SAMPLE_RATE) -> Dict[str, Tuple[np.ndarray, ...]]:
    """Loads optional ModeAudio round-robin drum pools via `c5_real_assets_bridge` safely."""
    pools: Dict[str, Tuple[np.ndarray, ...]] = {}
    for role in ("hat", "clap", "percussion"):
        try:
            loaded = get_round_robin_drum_pool(role=role, count=6, sample_rate=sample_rate, max_sec=0.45)
        except Exception:
            loaded = ()
        cleaned: List[np.ndarray] = []
        for s in loaded:
            if s is None or len(s) < 64:
                continue
            mono = 0.5 * (s[:, 0] + s[:, 1]) if s.ndim == 2 else s
            # Trim excess tail & clean >220 Hz to preserve modal Bark clarity
            if role == "hat":
                sos = signal.butter(4, 5800.0 / (0.5 * sample_rate), btype="high", output="sos")
            else:
                sos = signal.butter(2, [280.0 / (0.5 * sample_rate), 12800.0 / (0.5 * sample_rate)], btype="band", output="sos")
            shaped = signal.sosfilt(sos, mono)
            pk = float(np.max(np.abs(shaped)))
            if pk > 1e-6:
                cleaned.append(shaped / pk)
        pools[role] = tuple(cleaned)
    return pools


def _generate_syncopated_bass_stem(
    n_samples: int,
    bar_samples: int,
    beat_samples: int,
    step_samples: int,
    total_bars: int,
    kick_onsets: List[int],
    fd_start: int,
    fd_end: int,
    living_exit_start: int,
    drift: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Synthesizes behind-the-beat syncopated Minimoog/PolyBLEP cosmic bass + Bar 60 mute."""
    bass_mono = np.zeros(n_samples, dtype=np.float64)
    pocket_offset = int(round(0.006 * sample_rate))  # +6 ms laid-back cosmic pocket
    # Classic French/Cosmic House 16th-note syncopation (avoids beat 1 kick collision)
    pattern = (
        (2, False, 0.94),
        (3, True, 0.72),
        (6, False, 1.00),
        (7, False, 0.80),
        (10, True, 0.95),
        (11, False, 0.78),
        (14, False, 0.98),
        (15, True, 0.82),
    )

    for b in range(total_bars):
        # Active in Intro (0-15), subtle pulse on Pre-Chorus half-2 (28-31, 56-58), Drop 1 (32-43), Drop 2 (60-63)
        if b < 16:
            sec_gain = 0.65 + 0.35 * (b / 15.0)
        elif 28 <= b < 32:
            sec_gain = 0.55 + 0.35 * ((b - 28) / 3.0)
        elif 32 <= b < 44:
            sec_gain = 1.00
        elif 56 <= b < 60:
            sec_gain = 0.65 + 0.30 * ((b - 56) / 3.0)
        elif 60 <= b < 64:
            sec_gain = 1.02
        else:
            continue  # Verses float keyless of heavy bass

        chord = CHORD_PROGRESSION[b % len(CHORD_PROGRESSION)]
        root_hz = midi_to_hz(chord["bass_root"])
        alt_hz = midi_to_hz(chord["bass_alt"])
        bar_s = b * bar_samples

        for step, is_oct, accent in pattern:
            # Strip completely in Bar 60 beats 3-4 False Drop vacuum
            if b == 59 and step >= 8:
                continue
            swing_off = int(round(0.011 * sample_rate)) if step % 2 == 1 else 0
            jit_idx = (b * 16 + step) % len(drift)
            micro_ms = 0.002 * float(drift[jit_idx])
            t0 = max(0, bar_s + step * step_samples + pocket_offset + swing_off + int(micro_ms * sample_rate))
            dur = step_samples * (1.25 if step in (2, 6, 10, 14) else 0.72)
            n_note = max(128, int(round(dur)))
            if t0 >= n_samples:
                continue
            f_note = alt_hz if is_oct else root_hz
            saw = polyblep_saw(f_note, n_note, sample_rate=sample_rate)
            sine = np.sin(2.0 * math.pi * f_note * make_time_axis(n_note, sample_rate))
            voice = 0.60 * sine + 0.40 * saw
            t_v = make_time_axis(n_note, sample_rate)
            # Snappy analog filter VCA contour (low-passed cleanly)
            vca = np.exp(-t_v / 0.19)
            voice = apply_zero_crackle_envelope(voice * vca, sample_rate=sample_rate, attack_ms=6.0, release_ms=14.0)
            vel_scale = sec_gain * accent * (0.94 + 0.06 * float(drift[jit_idx]))
            _safe_mix_add(bass_mono, t0, voice, gain=vel_scale)

    # Dynamic morphing warm bass ladder filter + 49 Hz kick fundamental carve
    t_all = make_time_axis(n_samples, sample_rate)
    sweep_hz = 460.0 + 340.0 * (0.5 + 0.5 * np.sin(2.0 * math.pi * t_all / (4.0 * bar_samples / sample_rate)))
    bass_filt = _morphing_resonant_filter(
        bass_mono,
        sweep_hz,
        band_edges=(220.0, 420.0, 680.0, 1050.0, 1450.0),
        resonance_q=1.6,
        sample_rate=sample_rate,
    )
    # Bark-band subtle pocket notch at 49 Hz so kick body dominates fundamental
    b_n, a_n = signal.iirnotch(49.0, Q=3.2, fs=sample_rate)
    bass_filt = signal.filtfilt(b_n, a_n, bass_filt)

    # Multiband sidechain keyed to kicks
    sc_low, sc_hi = build_coupled_multiband_sidechain(
        n_samples, kick_onsets, sample_rate=sample_rate, tau_body=0.195, sub_depth=0.90, high_depth=0.35
    )
    b_l_low, b_l_hi = lr4_zero_phase_crossover(bass_filt, 160.0, sample_rate)
    bass_sc = b_l_low * sc_low + b_l_hi * sc_hi
    bass_sc = oversampled_soft_saturate(bass_sc, drive_db=1.6, threshold_db=-2.8, oversample=4)
    bass_sc, _ = _apply_smooth_gate_window(bass_sc, bass_sc, fd_start, fd_end, target_gain=0.0, ramp_ms=14.0)
    bass_sc, _ = _apply_living_exit_rc(bass_sc, bass_sc, living_exit_start, tau_sec=0.38)
    bass_sc, _ = _normalize_peak(bass_sc, bass_sc, 0.29)
    bass_sc, _ = _bandlimit_for_zero_crackle(bass_sc, bass_sc, cutoff_hz=1250.0)
    return bass_sc


def _generate_retro_arp_stem(
    n_samples: int,
    bar_samples: int,
    step_samples: int,
    total_bars: int,
    fd_start: int,
    fd_end: int,
    living_exit_start: int,
    drift: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """Synthesizes retro-futuristic PolyBLEP saw+pulse synth arpeggiator (Intro + Builds + Drops)."""
    arp_l = np.zeros(n_samples, dtype=np.float64)
    arp_r = np.zeros(n_samples, dtype=np.float64)

    for b in range(total_bars):
        # Opens track in Intro (0-15), accents Pre-Choruses (24-31, 52-59), supports Drops (32-43, 60-63)
        if b < 16:
            sec_gain = 0.85 if b < 8 else 0.95
        elif 24 <= b < 32:
            sec_gain = 0.45 + 0.55 * ((b - 24) / 7.0)
        elif 32 <= b < 44:
            sec_gain = 0.82
        elif 52 <= b < 60:
            sec_gain = 0.50 + 0.50 * ((b - 52) / 7.0)
        elif 60 <= b < 64:
            sec_gain = 0.88
        else:
            continue

        pool = CHORD_PROGRESSION[b % len(CHORD_PROGRESSION)]["arp"]
        bar_s = b * bar_samples
        for step in range(16):
            # Subtle breath on step 15 of turnaround bars, keep pre-drop tails airy in Bar 60
            if step == 15 and b % 4 == 3:
                continue
            if b == 59 and step >= 12:
                continue
            swing_off = int(round(0.011 * sample_rate)) if step % 2 == 1 else 0
            note = pool[(step + b * 2) % len(pool)]
            f_hz = midi_to_hz(note)
            t0 = bar_s + step * step_samples + swing_off
            n_note = max(128, int(round(step_samples * 0.78)))
            saw = polyblep_saw(f_hz * 1.003, n_note, sample_rate=sample_rate)
            pls = polyblep_pulse(f_hz * 0.997, n_note, duty=0.38, sample_rate=sample_rate)
            t_v = make_time_axis(n_note, sample_rate)
            vca = np.exp(-t_v / 0.115)
            voice = apply_zero_crackle_envelope((0.55 * saw + 0.45 * pls) * vca, sample_rate=sample_rate, attack_ms=4.5, release_ms=14.0)
            pan = 0.34 * math.sin(2.0 * math.pi * ((b * 16 + step) / 14.0))
            gain_v = sec_gain * (0.86 + 0.14 * float(drift[(b * 16 + step) % len(drift)]))
            _safe_mix_add(arp_l, t0, voice, gain=gain_v * (0.5 - 0.5 * pan + 0.25))
            _safe_mix_add(arp_r, t0, voice, gain=gain_v * (0.5 + 0.5 * pan + 0.25))

    t_all = make_time_axis(n_samples, sample_rate)
    # Sweeping cosmic filter contour across 8-bar waves
    lfo_cut = 1450.0 + 1850.0 * (0.5 - 0.5 * np.cos(2.0 * math.pi * t_all / (8.0 * bar_samples / sample_rate)))
    arp_l = _morphing_resonant_filter(arp_l, lfo_cut, band_edges=(520.0, 1100.0, 2100.0, 3800.0, 6500.0), resonance_q=2.1)
    arp_r = _morphing_resonant_filter(arp_r, lfo_cut * 1.04, band_edges=(520.0, 1100.0, 2100.0, 3800.0, 6500.0), resonance_q=2.1)
    arp_l, arp_r = carve_polyphonic_mud(arp_l, arp_r, sample_rate=sample_rate, hpf_hz=195.0, mud_hz=375.0, mud_cut_blend=0.42, air_lpf_hz=12500.0)
    arp_l, arp_r = _apply_smooth_gate_window(arp_l, arp_r, fd_start + int(0.08 * sample_rate), fd_end, target_gain=0.14, ramp_ms=25.0)
    arp_l, arp_r = _apply_living_exit_rc(arp_l, arp_r, living_exit_start, tau_sec=0.58)
    return _normalize_peak(arp_l, arp_r, 0.24)


def _generate_airy_keys_and_pads(
    n_samples: int,
    bar_samples: int,
    total_bars: int,
    fd_start: int,
    fd_end: int,
    living_exit_start: int,
    drift: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray]]:
    """
    Synthesizes floating Airy Rhodes Keys + Subtle Analog Cosmic Pads carrying
    Verses 1 & 2 (Bars 17-24, 45-52) and gentle harmonic support elsewhere.
    """
    keys_l = np.zeros(n_samples, dtype=np.float64)
    keys_r = np.zeros(n_samples, dtype=np.float64)
    pad_l = np.zeros(n_samples, dtype=np.float64)
    pad_r = np.zeros(n_samples, dtype=np.float64)
    bar_sec = bar_samples / float(sample_rate)

    for b in range(total_bars):
        chord = CHORD_PROGRESSION[b % len(CHORD_PROGRESSION)]
        bar_s = b * bar_samples

        # Verses (16..23, 44..51) highlight airy keys + subtle pads front-and-center
        in_verse = (16 <= b < 24) or (44 <= b < 52)
        in_pre = (24 <= b < 32) or (52 <= b < 60)
        in_drop = (32 <= b < 44) or (60 <= b < 64)

        if in_verse:
            key_gain, pad_gain = 1.00, 0.95
        elif in_pre:
            key_gain, pad_gain = 0.52, 0.72
        elif in_drop:
            key_gain, pad_gain = 0.34, 0.48
        else:  # Intro bars 8..15 pad swells gently underneath arps
            key_gain = 0.0
            pad_gain = 0.42 * max(0.0, (b - 7) / 8.0)

        # Airy Keys: micro-strummed Rhodes chord on bar beat 1 + airy offbeat grace voicing in Verses
        if key_gain > 0.0:
            key_notes = chord["keys"]
            # Bar hit micro-strum
            for v_idx, midi_n in enumerate(key_notes):
                is_top = v_idx == len(key_notes) - 1
                strum_s = int(round((0.011 * v_idx + 0.002 * drift[(b + v_idx) % len(drift)]) * sample_rate))
                voice = _synth_rhodes_airy_key(
                    midi_to_hz(midi_n),
                    duration_sec=bar_sec * (0.95 if in_verse else 0.72),
                    velocity=0.92 if is_top else 0.74,
                    sample_rate=sample_rate,
                )
                pan = -0.35 + 0.70 * (v_idx / max(1, len(key_notes) - 1))
                w = key_gain * (1.12 if is_top else 0.76)
                _safe_mix_add(keys_l, bar_s + strum_s, voice, gain=w * (0.72 - 0.35 * pan))
                _safe_mix_add(keys_r, bar_s + strum_s, voice, gain=w * (0.72 + 0.35 * pan))

            # Floating syncopated dotted-quarter chime answer in Verses
            if in_verse and not (b == 23 or b == 51):
                bell_s = bar_s + int(round(0.625 * bar_samples))
                top_note = key_notes[-1] + (12 if b % 2 == 1 else 0)
                bell_v = _synth_rhodes_airy_key(midi_to_hz(top_note), duration_sec=bar_sec * 0.42, velocity=0.88)
                _safe_mix_add(keys_l, bell_s, bell_v, gain=key_gain * 0.58)
                _safe_mix_add(keys_r, bell_s, bell_v, gain=key_gain * 0.85)

        # Subtle Analog Cosmic Pads: soft detuned ensemble saw+sine chord swell
        if pad_gain > 0.0:
            dur_pad = bar_sec * 1.04
            n_pad = int(round(dur_pad * sample_rate))
            pad_mix_l = np.zeros(n_pad, dtype=np.float64)
            pad_mix_r = np.zeros(n_pad, dtype=np.float64)
            for v_idx, midi_n in enumerate(chord["pad"]):
                f_c = midi_to_hz(midi_n)
                s_a = polyblep_saw(f_c * 0.9965, n_pad, sample_rate=sample_rate)
                s_b = polyblep_saw(f_c * 1.0038, n_pad, sample_rate=sample_rate)
                sine_c = np.sin(2.0 * math.pi * f_c * make_time_axis(n_pad, sample_rate))
                pan = -0.45 + 0.90 * (v_idx / max(1, len(chord["pad"]) - 1))
                pad_mix_l += (0.35 * s_a + 0.35 * s_b + 0.30 * sine_c) * (0.65 - 0.30 * pan)
                pad_mix_r += (0.35 * s_b + 0.35 * s_a + 0.30 * sine_c) * (0.65 + 0.30 * pan)
            pad_mix_l = apply_zero_crackle_envelope(pad_mix_l, sample_rate=sample_rate, attack_ms=95.0, release_ms=140.0)
            pad_mix_r = apply_zero_crackle_envelope(pad_mix_r, sample_rate=sample_rate, attack_ms=95.0, release_ms=140.0)
            _safe_mix_add(pad_l, bar_s, pad_mix_l, gain=pad_gain * 0.36)
            _safe_mix_add(pad_r, bar_s, pad_mix_r, gain=pad_gain * 0.36)

    # Smooth subtle pad filter (< 2.4 kHz for warm airy velvet glue without crowding leads)
    sos_pad = signal.butter(4, 2350.0 / (0.5 * sample_rate), btype="low", output="sos")
    pad_l = signal.sosfiltfilt(sos_pad, pad_l)
    pad_r = signal.sosfiltfilt(sos_pad, pad_r)

    keys_l, keys_r = carve_polyphonic_mud(keys_l, keys_r, sample_rate=sample_rate, hpf_hz=190.0, mud_hz=370.0, mud_cut_blend=0.45, air_lpf_hz=14000.0)
    pad_l, pad_r = carve_polyphonic_mud(pad_l, pad_r, sample_rate=sample_rate, hpf_hz=185.0, mud_hz=360.0, mud_cut_blend=0.48, air_lpf_hz=9500.0)

    # Bar 60 false drop soft breathe + Bar 64 Living Exit
    pad_l, pad_r = _apply_smooth_gate_window(pad_l, pad_r, fd_start + int(0.10 * sample_rate), fd_end, target_gain=0.22, ramp_ms=30.0)
    keys_l, keys_r = _apply_living_exit_rc(keys_l, keys_r, living_exit_start, tau_sec=0.72)
    pad_l, pad_r = _apply_living_exit_rc(pad_l, pad_r, living_exit_start, tau_sec=0.78)

    return _normalize_peak(keys_l, keys_r, 0.25), _normalize_peak(pad_l, pad_r, 0.21)


def _generate_filtered_disco_guitars(
    n_samples: int,
    bar_samples: int,
    step_samples: int,
    total_bars: int,
    fd_start: int,
    fd_end: int,
    living_exit_start: int,
    drift: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesizes Filtered Disco Guitars (waveguide Nile-Rodgers-style 16th funk strums
    swept by a resonant low-pass phaser filter) accenting Pre-Chorus 1 & Pre-Chorus 2.
    """
    gtr_l = np.zeros(n_samples, dtype=np.float64)
    gtr_r = np.zeros(n_samples, dtype=np.float64)

    # Pre-render waveguide chord bursts cached by (chord_idx, muted_flag)
    strum_cache: Dict[Tuple[int, bool], np.ndarray] = {}
    for c_idx, chord in enumerate(CHORD_PROGRESSION):
        for muted in (True, False):
            dur = 0.095 if muted else 0.30
            n_c = max(128, int(round(dur * sample_rate))) + 640
            chord_buf = np.zeros(n_c, dtype=np.float64)
            for s_idx, midi_n in enumerate(chord["guitar"]):
                # Upstroke / downstroke natural 4 ms inter-string strum stagger
                stagger = int(round((0.004 * s_idx) * sample_rate))
                str_w = _synth_karplus_guitar_note(
                    midi_to_hz(midi_n + 12),  # Sparkling upper-register disco skank octave
                    duration_sec=dur,
                    brightness=0.72,
                    muted=muted,
                    seed=700 + c_idx * 10 + s_idx,
                    sample_rate=sample_rate,
                )
                _safe_mix_add(chord_buf, stagger, str_w, gain=0.45)
            strum_cache[(c_idx, muted)] = freeze_array(chord_buf)

    # Classic 16th-note disco funk chop map: step -> (muted, accent)
    funk_pattern: Tuple[Tuple[int, bool, float], ...] = (
        (0, True, 0.42),
        (2, False, 1.00),
        (3, True, 0.45),
        (4, True, 0.38),
        (6, False, 0.94),
        (7, True, 0.44),
        (8, True, 0.40),
        (10, False, 0.98),
        (12, False, 0.88),
        (14, False, 1.00),
        (15, True, 0.50),
    )

    for b in range(total_bars):
        # Signature feature in Pre-Chorus 1 (24-31) and Pre-Chorus 2 (52-59), plus Drop 2 accent bar 60
        if 24 <= b < 32:
            sec_gain = 0.78 + 0.26 * ((b - 24) / 7.0)
        elif 52 <= b < 60:
            sec_gain = 0.82 + 0.24 * ((b - 52) / 7.0)
        elif b == 60:
            sec_gain = 0.72
        elif 32 <= b < 44 and (b % 4 == 3):
            sec_gain = 0.48  # Turnaround funky guitar accent inside Drop 1
        else:
            continue

        c_idx = b % len(CHORD_PROGRESSION)
        bar_s = b * bar_samples
        for step, muted, accent in funk_pattern:
            if b == 59 and step >= 10:
                continue  # Throw final guitar chop @ beat 3 into Pre-Drop dub echo
            swing_off = int(round(0.011 * sample_rate)) if step % 2 == 1 else 0
            jit_s = int(round(0.0015 * float(drift[(b * 16 + step) % len(drift)]) * sample_rate))
            t0 = bar_s + step * step_samples + swing_off + jit_s
            clip = strum_cache[(c_idx, muted)]
            pan = 0.38 * (1 if (step % 4) in (2, 10) else -1)
            gain_v = sec_gain * accent
            _safe_mix_add(gtr_l, t0, clip, gain=gain_v * (0.65 - 0.32 * pan))
            _safe_mix_add(gtr_r, t0, clip, gain=gain_v * (0.65 + 0.32 * pan))

    # Sweeping resonant disco filter ascending across Pre-Chorus 1 & Pre-Chorus 2!
    cutoff = np.full(n_samples, 2200.0, dtype=np.float64)
    for pc_start_bar in (24, 52):
        s_pc0 = pc_start_bar * bar_samples
        s_pc1 = min(n_samples, (pc_start_bar + 8) * bar_samples)
        if s_pc1 > s_pc0:
            ramp = np.linspace(0.0, 1.0, s_pc1 - s_pc0, dtype=np.float64)
            # Slow rising disco auto-filter + 16th-note funky wah shimmer
            t_seg = make_time_axis(s_pc1 - s_pc0, sample_rate)
            wah = 0.5 + 0.5 * np.sin(2.0 * math.pi * (DEFAULT_BPM / 60.0) * 2.0 * t_seg)
            cutoff[s_pc0:s_pc1] = 420.0 + 4800.0 * (ramp ** 1.35) + 950.0 * wah * (0.35 + 0.65 * ramp)

    gtr_l = _morphing_resonant_filter(gtr_l, cutoff, band_edges=(380.0, 950.0, 2100.0, 4200.0, 6800.0), resonance_q=2.4)
    gtr_r = _morphing_resonant_filter(gtr_r, cutoff * 1.05, band_edges=(380.0, 950.0, 2100.0, 4200.0, 6800.0), resonance_q=2.4)
    gtr_l, gtr_r = carve_polyphonic_mud(gtr_l, gtr_r, sample_rate=sample_rate, hpf_hz=215.0, mud_hz=385.0, mud_cut_blend=0.45, air_lpf_hz=13200.0)
    gtr_l, gtr_r = _normalize_peak(gtr_l, gtr_r, 0.85)
    gtr_l = oversampled_soft_saturate(gtr_l, drive_db=4.8, threshold_db=-6.5, oversample=4)
    gtr_r = oversampled_soft_saturate(gtr_r, drive_db=4.8, threshold_db=-6.5, oversample=4)
    gtr_l, gtr_r = _apply_living_exit_rc(gtr_l, gtr_r, living_exit_start, tau_sec=0.45)
    # Leave Bar 60 beats 3-4 tail untouched cleanly so its echo flows naturally into the vacuum!
    _ = (fd_start, fd_end)
    return _normalize_peak(gtr_l, gtr_r, 0.38)


def _generate_swirling_analog_lead_stem(
    n_samples: int,
    bar_samples: int,
    step_samples: int,
    total_bars: int,
    living_exit_start: int,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesizes the Swirling Analog Lead unleashed in Drops (Drop 1: Bars 33-44, Drop 2: Bars 61-64)
    with phase-coherent continuous waveguide legato pitch gliding (ZERO phase resets) + LFO swirl.
    Guarantees strict compliance with Zero-Crackle derivatives (`|Δx| <= 0.015`, `|Δ²x| <= 0.005`).
    """
    lead_l = np.zeros(n_samples, dtype=np.float64)
    lead_r = np.zeros(n_samples, dtype=np.float64)

    # 4-bar heroic G Dorian Cosmic Lead phrase (step_idx, len_steps, midi_note, gain)
    phrase_a = (
        (0, 5, 74, 0.92),   # D5 held
        (5, 3, 72, 0.84),   # C5
        (8, 4, 70, 0.90),   # Bb4
        (12, 4, 67, 0.88),  # G4
    )
    phrase_b = (
        (0, 4, 70, 0.90),   # Bb4
        (4, 4, 72, 0.95),   # C5
        (8, 5, 74, 1.00),   # D5 lift
        (13, 3, 77, 0.94),  # F5 cosmic peak
    )
    phrase_c = (
        (0, 6, 79, 1.00),   # G5 climax!
        (6, 2, 77, 0.88),   # F5
        (8, 4, 74, 0.92),   # D5
        (12, 4, 72, 0.84),  # C5
    )

    def render_drop_block(start_bar: int, end_bar: int, boost: float) -> None:
        s0 = start_bar * bar_samples
        s1 = min(n_samples, end_bar * bar_samples)
        blk_n = s1 - s0
        if blk_n <= 0:
            return

        # Build continuous frequency & amp contours across active Drop block (zero phase jumps!)
        freq_t = np.full(blk_n, midi_to_hz(74), dtype=np.float64)
        amp_t = np.zeros(blk_n, dtype=np.float64)
        for b in range(start_bar, end_bar):
            rel_b = b - start_bar
            phrase = phrase_a if (rel_b % 4 == 0) else (phrase_b if (rel_b % 4 in (1, 3)) else phrase_c)
            b_off = (b - start_bar) * bar_samples
            for step_i, dur_steps, note, g_val in phrase:
                n_s = b_off + step_i * step_samples
                n_e = min(blk_n, b_off + (step_i + dur_steps) * step_samples)
                if n_e <= n_s:
                    continue
                target_f = midi_to_hz(note + (12 if (boost > 1.0 and rel_b == 2 and step_i == 0) else 0))
                # Exponential analog portamento glide across first 45 ms of each note
                glide_n = min(n_e - n_s, int(round(0.045 * sample_rate)))
                prev_f = float(freq_t[max(0, n_s - 1)])
                freq_t[n_s : n_s + glide_n] = np.geomspace(max(prev_f, 80.0), target_f, glide_n)
                freq_t[n_s + glide_n : n_e] = target_f

                # Smooth legato note envelope (8 ms rise, gentle breath gap at end)
                note_len = n_e - n_s
                env = np.ones(note_len, dtype=np.float64) * g_val
                att = min(note_len // 3, int(round(0.010 * sample_rate)))
                rel = min(note_len // 3, int(round(0.022 * sample_rate)))
                if att > 2:
                    env[:att] *= 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, att)))
                if rel > 2:
                    env[-rel:] *= 0.5 * (1.0 + np.cos(np.linspace(0.0, math.pi, rel)))
                amp_t[n_s:n_e] = np.maximum(amp_t[n_s:n_e], env)

        t_blk = make_time_axis(blk_n, sample_rate)
        # Expressive delayed 5.2 Hz vibrato
        vib = 1.0 + 0.0048 * np.sin(2.0 * math.pi * 5.2 * t_blk)
        freq_inst = freq_t * vib

        # Continuous zero-phase-reset PolyBLEP-approximated additive analog oscillator stack
        # Sawtooth & rich triangle harmonics blended cleanly and phase-locked
        ph_main = (np.cumsum(freq_inst / float(sample_rate))) % 1.0
        osc_saw = (
            0.52 * np.sin(2.0 * math.pi * ph_main)
            + 0.25 * np.sin(4.0 * math.pi * ph_main + 0.15)
            + 0.13 * np.sin(6.0 * math.pi * ph_main + 0.30)
            + 0.06 * np.sin(8.0 * math.pi * ph_main)
        )
        osc_det = (
            0.52 * np.sin(2.0 * math.pi * ((ph_main * 1.0038) % 1.0))
            + 0.24 * np.sin(4.0 * math.pi * ((ph_main * 0.9965) % 1.0))
        )
        raw_lead = (0.64 * osc_saw + 0.36 * osc_det) * amp_t * boost

        # Swirling resonant analog filter + slow LFO stereo swirl
        fc_swirl = 1250.0 + 1350.0 * (0.5 + 0.5 * np.sin(2.0 * math.pi * 0.18 * t_blk))
        filt_lead = _morphing_resonant_filter(
            raw_lead, fc_swirl, band_edges=(680.0, 1250.0, 2100.0, 3200.0, 4400.0), resonance_q=2.0
        )
        pan_lfo = 0.46 * np.sin(2.0 * math.pi * 0.27 * t_blk)
        l_gain = np.sqrt(0.5 * (1.0 - pan_lfo))
        r_gain = np.sqrt(0.5 * (1.0 + pan_lfo))
        lead_l[s0:s1] += filt_lead * l_gain
        lead_r[s0:s1] += filt_lead * r_gain

    render_drop_block(32, 44, boost=1.00)
    render_drop_block(60, min(64, total_bars), boost=1.05)

    lead_l, lead_r = carve_polyphonic_mud(lead_l, lead_r, sample_rate=sample_rate, hpf_hz=185.0, mud_hz=375.0, mud_cut_blend=0.45, air_lpf_hz=12500.0)
    lead_l, lead_r = _apply_living_exit_rc(lead_l, lead_r, living_exit_start, tau_sec=0.62)
    lead_l, lead_r = _normalize_peak(lead_l, lead_r, 0.21)
    # Enforce strict Zero-Crackle discrete continuity on Swirling Analog Lead stem
    return _bandlimit_for_zero_crackle(lead_l, lead_r, cutoff_hz=2850.0, max_d1=0.0135, max_d2=0.0044)


def _generate_dynamic_percussion_stem(
    n_samples: int,
    bar_samples: int,
    beat_samples: int,
    step_samples: int,
    total_bars: int,
    fd_start: int,
    fd_end: int,
    living_exit_start: int,
    drift: np.ndarray,
    pools: Dict[str, Tuple[np.ndarray, ...]],
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesizes Dynamic Percussion (ModeAudio Round-Robin + Modal Congo/Rim/Clap/MPC Hats >6.2 kHz)
    breathing dynamically across Drops and Pre-Chorus builds, strictly muted in Bar 60 False Drop.
    """
    perc_l = np.zeros(n_samples, dtype=np.float64)
    perc_r = np.zeros(n_samples, dtype=np.float64)

    # Pre-synthesize deterministic modal percussion fallbacks
    hat_c_pool = [
        _synth_modal_percussion("hat_closed", 6350.0 + i * 95.0, 0.12, seed=100 + i)
        for i in range(4)
    ]
    hat_o_pool = [
        _synth_modal_percussion("hat_open", 6520.0 + i * 80.0, 0.34, seed=200 + i)
        for i in range(2)
    ]
    clap_pool = [
        _synth_modal_percussion("clap", 1200.0, 0.24, seed=300 + i)
        for i in range(3)
    ]
    conga_hi = _synth_modal_percussion("conga", 328.0, 0.30, seed=401)
    conga_lo = _synth_modal_percussion("conga", 242.0, 0.32, seed=402)
    rim_wood = _synth_modal_percussion("rim", 890.0, 0.10, seed=501)

    ext_hats = pools.get("hat", ())
    ext_claps = pools.get("clap", ())
    ext_perc = pools.get("percussion", ())

    flam_shift = int(round(0.008 * sample_rate))  # -8 ms pre-snap organic clap flam

    for b in range(total_bars):
        # Energy scaling across arrangement
        if 8 <= b < 16:
            mode = "light_intro"
            dyn = 0.32 + 0.18 * ((b - 8) / 7.0)
        elif 24 <= b < 32:
            mode = "build"
            dyn = 0.45 + 0.45 * ((b - 24) / 7.0)
        elif 32 <= b < 44:
            mode = "drop"
            dyn = 1.00
        elif 52 <= b < 60:
            mode = "build"
            dyn = 0.50 + 0.45 * ((b - 52) / 7.0)
        elif 60 <= b < 64:
            mode = "drop"
            dyn = 1.06
        else:
            continue

        bar_s = b * bar_samples
        is_turnaround = (b % 4 == 3) and b != 59

        for step in range(16):
            # Bar 60 beats 3-4 False Drop Vacuum: ZERO percussion hits
            if b == 59 and step >= 8:
                continue
            # Bar 64 beats 3-4 Living Exit clears out percussion
            if b == 63 and step >= 8:
                continue

            swing_off = int(round(0.0115 * sample_rate)) if step % 2 == 1 else 0  # 56.5% MPC swing
            jit_idx = (b * 16 + step) % len(drift)
            micro_off = int(round(0.0018 * float(drift[jit_idx]) * sample_rate))
            t0 = max(0, bar_s + step * step_samples + swing_off + micro_off)

            # 1) Swung Hats (> 6.2 kHz crisp shimmer)
            if step % 2 == 0 or (mode == "drop" and step in (3, 7, 11, 15)) or (is_turnaround and step >= 12):
                is_open = (step % 4 == 2) and mode in ("build", "drop")
                sample = (hat_o_pool if is_open else hat_c_pool)[(b + step) % (2 if is_open else 4)]
                if ext_hats and not is_open and (step % 4 != 2):
                    rr_h = shape_velocity_sample(ext_hats[(b + step) % len(ext_hats)], velocity=0.72)
                    sample = 0.72 * sample + 0.28 * rr_h[: len(sample)] if len(rr_h) >= len(sample) else sample
                vel = dyn * (0.85 if (step % 4 == 2) else 0.48) * (0.9 + 0.1 * float(drift[jit_idx]))
                _safe_mix_add(perc_l, t0, sample, gain=vel * 0.52)
                _safe_mix_add(perc_r, t0, sample, gain=vel * 0.62)

            # 2) Organic Clap on beats 2 & 4 (with -8 ms pre-snap flam)
            if step in (4, 12) and mode in ("build", "drop"):
                clap_s = clap_pool[(b + step) % len(clap_pool)]
                if ext_claps:
                    rr_c = shape_velocity_sample(ext_claps[(b + step) % len(ext_claps)], velocity=0.85)
                    n_c = min(len(clap_s), len(rr_c))
                    clap_s = clap_s.copy()
                    clap_s[:n_c] = 0.68 * clap_s[:n_c] + 0.32 * rr_c[:n_c]
                _safe_mix_add(perc_l, max(0, t0 - flam_shift), clap_s, gain=dyn * 0.85)
                _safe_mix_add(perc_r, max(0, t0 - flam_shift), clap_s, gain=dyn * 0.82)

            # 3) Dynamic Conga / Wood Groove in Drops & Turnarounds
            if mode == "drop":
                if step in (3, 14):
                    _safe_mix_add(perc_l, t0, conga_hi, gain=dyn * 0.56)
                    _safe_mix_add(perc_r, t0, conga_hi, gain=dyn * 0.38)
                elif step in (6, 11):
                    _safe_mix_add(perc_l, t0, conga_lo, gain=dyn * 0.38)
                    _safe_mix_add(perc_r, t0, conga_lo, gain=dyn * 0.58)
                elif step in (9, 15):
                    rim = rim_wood
                    if ext_perc:
                        rr_p = shape_velocity_sample(ext_perc[(b + step) % len(ext_perc)], velocity=0.76)
                        n_p = min(len(rim), len(rr_p))
                        rim = rim.copy()
                        rim[:n_p] = 0.65 * rim[:n_p] + 0.35 * rr_p[:n_p]
                    _safe_mix_add(perc_l, t0, rim, gain=dyn * 0.42)
                    _safe_mix_add(perc_r, t0, rim, gain=dyn * 0.55)

    # Hard sub-carve (< 195 Hz) and hard smooth gate on Bar 60 False Drop beats 3-4
    perc_l, perc_r = carve_polyphonic_mud(perc_l, perc_r, sample_rate=sample_rate, hpf_hz=195.0, mud_hz=380.0, mud_cut_blend=0.35, air_lpf_hz=14400.0)
    perc_l, perc_r = _apply_smooth_gate_window(perc_l, perc_r, fd_start, fd_end, target_gain=0.0, ramp_ms=10.0)
    perc_l, perc_r = _apply_living_exit_rc(perc_l, perc_r, living_exit_start, tau_sec=0.22)
    return _normalize_peak(perc_l, perc_r, 0.42)


def _generate_kick_stem(
    n_samples: int,
    bar_samples: int,
    beat_samples: int,
    total_bars: int,
    fd_start: int,
    fd_end: int,
    living_exit_start: int,
    drift: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, List[int]]:
    """Synthesizes pulsating phase-locked 49.0 Hz (G1) 4-on-the-floor kick track."""
    kick_mono = np.zeros(n_samples, dtype=np.float64)
    kick_onsets: List[int] = []
    # Small deterministic round-robin tonal micro-variants for organic pulsation
    kick_pool = [
        synthesize_phase_locked_kick(
            sample_rate=sample_rate,
            duration_sec=0.39,
            root_hz=49.0,  # Exact G1 harmonic anchor inside 48-55 Hz club window
            punch_hz=150.0 + idx * 2.5,
            click_hz=2850.0 + idx * 90.0,
            tau_body=0.205,
            drive_db=2.8,
            pultec_sub_gain=0.18,
            mud_notch_hz=195.0,
            beater_gain=0.23,
            beater_hz=2380.0,
        )
        for idx in range(4)
    ]

    for b in range(total_bars):
        # Opens track with pulsating kicks (0-15), rests in Verses (16-23, 44-51), builds in Pre-Choruses, slams Drops!
        if b < 16:
            sec_gain = 0.90 + 0.10 * math.sin(2.0 * math.pi * (b / 4.0))
        elif 24 <= b < 32:
            sec_gain = 0.56 + 0.42 * ((b - 24) / 7.0)
        elif 32 <= b < 44:
            sec_gain = 1.00
        elif 52 <= b < 60:
            sec_gain = 0.60 + 0.38 * ((b - 52) / 7.0)
        elif 60 <= b < 64:
            sec_gain = 1.04
        else:
            continue

        bar_s = b * bar_samples
        for beat in range(4):
            # Bar 60 beats 3-4 False Drop Vacuum: ZERO kicks
            if b == 59 and beat >= 2:
                continue
            # Bar 64 beats 3-4 Living Exit fade
            if b == 63 and beat >= 2:
                continue
            t0 = bar_s + beat * beat_samples
            kick_onsets.append(t0)
            vel_pulse = 1.00 if beat == 0 else (0.94 if beat == 2 else 0.89)
            k_wave = kick_pool[(b + beat) % len(kick_pool)]
            _safe_mix_add(kick_mono, t0, k_wave, gain=sec_gain * vel_pulse)

    kick_mono, _ = _apply_smooth_gate_window(kick_mono, kick_mono, fd_start, fd_end, target_gain=0.0, ramp_ms=10.0)
    kick_mono, _ = _apply_living_exit_rc(kick_mono, kick_mono, living_exit_start, tau_sec=0.22)
    kick_mono, _ = _normalize_peak(kick_mono, kick_mono, 0.56)
    return kick_mono, kick_onsets


def _build_cosmic_house_midi(bpm: float, total_bars: int, out_midi: Path) -> str:
    """Builds SMF Type 1 MIDI with strict 0-drift delta flushes, markers, and Bar 60 False Drop."""
    mid = mido.MidiFile(type=1)
    tpb = 480
    bar_ticks = 4 * tpb
    step_ticks = tpb // 4
    mid.ticks_per_beat = tpb

    # Conductor track
    t_cond = mido.MidiTrack()
    mid.tracks.append(t_cond)
    t_cond.append(mido.MetaMessage("track_name", name="Cosmic House 122 Conductor"))
    t_cond.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))
    t_cond.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, clocks_per_click=24, notated_32nd_notes_per_beat=8))
    cond_events: List[Tuple[int, int, Any]] = []
    for sec in SECTION_LAYOUT:
        if sec["start_bar"] < total_bars:
            cond_events.append((sec["start_bar"] * bar_ticks, 0, mido.MetaMessage("marker", text=sec["name"], time=0)))
    _sort_and_flush_midi(t_cond, cond_events)

    def add_track(name: str, ch: int) -> Tuple[mido.MidiTrack, List[Tuple[int, int, Any]]]:
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("track_name", name=name))
        return tr, []

    tr_kick, ev_kick = add_track("01_Kick_49Hz", 0)
    tr_bass, ev_bass = add_track("02_Syncopated_Bass", 1)
    tr_arp, ev_arp = add_track("03_Retro_Futuristic_Arp", 2)
    tr_keys, ev_keys = add_track("04_Airy_Keys_Rhodes", 3)
    tr_pad, ev_pad = add_track("05_Subtle_Cosmic_Pads", 4)
    tr_gtr, ev_gtr = add_track("06_Filtered_Disco_Guitars", 5)
    tr_lead, ev_lead = add_track("07_Swirling_Analog_Lead", 6)
    tr_perc, ev_perc = add_track("08_Dynamic_Percussion", 9)

    lead_phrase = ((0, 5, 74), (5, 3, 72), (8, 4, 70), (12, 4, 67))

    for b in range(total_bars):
        bt = b * bar_ticks
        chord = CHORD_PROGRESSION[b % len(CHORD_PROGRESSION)]

        # Kick (0-15, 24-43, 52-63; Bar 60 beats 3-4 silent)
        if b < 16 or (24 <= b < 44) or (52 <= b < 64):
            for beat in range(4):
                if (b == 59 or b == 63) and beat >= 2:
                    continue
                t0 = bt + beat * tpb
                ev_kick.append((t0, 1, mido.Message("note_on", channel=0, note=36, velocity=118 if beat == 0 else 108, time=0)))
                ev_kick.append((t0 + 220, 0, mido.Message("note_off", channel=0, note=36, velocity=0, time=0)))

        # Syncopated Bass
        if b < 16 or (28 <= b < 44) or (56 <= b < 64):
            for step, is_oct in ((2, False), (3, True), (6, False), (7, False), (10, True), (11, False), (14, False), (15, True)):
                if b == 59 and step >= 8:
                    continue
                n_b = chord["bass_alt"] if is_oct else chord["bass_root"]
                t0 = bt + step * step_ticks + 6
                ev_bass.append((t0, 1, mido.Message("note_on", channel=1, note=n_b, velocity=102, time=0)))
                ev_bass.append((t0 + step_ticks - 12, 0, mido.Message("note_off", channel=1, note=n_b, velocity=0, time=0)))

        # Retro Futuristic Arp
        if b < 16 or (24 <= b < 44) or (52 <= b < 64):
            for step in range(16):
                if (b == 59 and step >= 12) or (step == 15 and b % 4 == 3):
                    continue
                n_a = chord["arp"][(step + b * 2) % len(chord["arp"])]
                t0 = bt + step * step_ticks
                ev_arp.append((t0, 1, mido.Message("note_on", channel=2, note=n_a, velocity=94, time=0)))
                ev_arp.append((t0 + int(step_ticks * 0.75), 0, mido.Message("note_off", channel=2, note=n_a, velocity=0, time=0)))

        # Airy Keys & Subtle Pads (dominant in Verses 16-23, 44-51)
        if 16 <= b < 64:
            for idx, n_k in enumerate(chord["keys"]):
                t0 = bt + idx * 14
                ev_keys.append((t0, 1, mido.Message("note_on", channel=3, note=n_k, velocity=96 if idx == len(chord["keys"]) - 1 else 78, time=0)))
                ev_keys.append((bt + bar_ticks - 24, 0, mido.Message("note_off", channel=3, note=n_k, velocity=0, time=0)))
        if b >= 8:
            for n_p in chord["pad"]:
                ev_pad.append((bt, 1, mido.Message("note_on", channel=4, note=n_p, velocity=76, time=0)))
                ev_pad.append((bt + bar_ticks - 16, 0, mido.Message("note_off", channel=4, note=n_p, velocity=0, time=0)))

        # Filtered Disco Guitars (Pre-Choruses 24-31, 52-59 + accent Bar 60)
        if (24 <= b < 32) or (52 <= b < 61):
            cc_val = int(42 + 80 * (((b - 24) if b < 32 else max(0, b - 52)) / 7.0))
            ev_gtr.append((bt, 2, mido.Message("control_change", channel=5, control=74, value=min(127, cc_val), time=0)))
            for step in (2, 6, 10, 12, 14):
                if b == 59 and step >= 10:
                    continue
                for n_g in chord["guitar"]:
                    t0 = bt + step * step_ticks
                    ev_gtr.append((t0, 1, mido.Message("note_on", channel=5, note=n_g + 12, velocity=98, time=0)))
                    ev_gtr.append((t0 + step_ticks - 10, 0, mido.Message("note_off", channel=5, note=n_g + 12, velocity=0, time=0)))

        # Swirling Analog Lead (Drop 1: 32-43, Drop 2: 60-63)
        if (32 <= b < 44) or (60 <= b < 64):
            for step_i, dur_s, n_l in lead_phrase:
                t0 = bt + step_i * step_ticks
                ev_lead.append((t0, 1, mido.Message("note_on", channel=6, note=n_l, velocity=108, time=0)))
                ev_lead.append((t0 + dur_s * step_ticks - 16, 0, mido.Message("note_off", channel=6, note=n_l, velocity=0, time=0)))

        # Dynamic Percussion (Bar 60 beats 3-4 silent)
        if (8 <= b < 16) or (24 <= b < 44) or (52 <= b < 64):
            for step in range(16):
                if (b == 59 or b == 63) and step >= 8:
                    continue
                t0 = bt + step * step_ticks
                if step % 2 == 0:
                    ev_perc.append((t0, 1, mido.Message("note_on", channel=9, note=46 if step % 4 == 2 else 42, velocity=86, time=0)))
                    ev_perc.append((t0 + 80, 0, mido.Message("note_off", channel=9, note=46 if step % 4 == 2 else 42, velocity=0, time=0)))
                if step in (4, 12) and b >= 24:
                    ev_perc.append((t0, 1, mido.Message("note_on", channel=9, note=39, velocity=104, time=0)))
                    ev_perc.append((t0 + 100, 0, mido.Message("note_off", channel=9, note=39, velocity=0, time=0)))
                if step in (3, 11, 14) and ((32 <= b < 44) or (60 <= b < 64)):
                    ev_perc.append((t0, 1, mido.Message("note_on", channel=9, note=62 if step == 3 else 64, velocity=90, time=0)))
                    ev_perc.append((t0 + 90, 0, mido.Message("note_off", channel=9, note=62 if step == 3 else 64, velocity=0, time=0)))

    for tr, evs in (
        (tr_kick, ev_kick),
        (tr_bass, ev_bass),
        (tr_arp, ev_arp),
        (tr_keys, ev_keys),
        (tr_pad, ev_pad),
        (tr_gtr, ev_gtr),
        (tr_lead, ev_lead),
        (tr_perc, ev_perc),
    ):
        _sort_and_flush_midi(tr, evs)

    out_midi.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(out_midi))
    return str(out_midi)


def _sort_and_flush_midi(track: mido.MidiTrack, events: List[Tuple[int, int, Any]]) -> None:
    """Converts (abs_tick, order, msg) into strict non-negative delta-time events."""
    events.sort(key=lambda it: (it[0], it[1]))
    last_t = 0
    for abs_t, _ord, msg in events:
        clamped = max(last_t, int(abs_t))
        msg.time = clamped - last_t
        track.append(msg)
        last_t = clamped


def _build_fl_pyscript(out_pyscript: Path, bpm: float = DEFAULT_BPM) -> str:
    """Generates and AST-validates an authentic FL Studio Piano Roll script for Cosmic House."""
    src = f'''"""
Cosmic House Groove 122 BPM - Native FL Studio Piano Roll Script
Enforces +6 ms syncopated bass pocket, 56.5% swung percussion,
and deterministic Bar 60 beats 3-4 False Drop Vacuum.
"""
import flpianoroll as flp


def apply():
    ppq = flp.score.PPQ
    bar_ticks = ppq * 4
    six_ms_ticks = max(1, int(round(ppq * ({bpm:.1f} / 60.0) * 0.006)))
    fd_start = 59 * bar_ticks + 2 * ppq
    fd_end = 60 * bar_ticks
    kept = []
    for i in range(flp.score.noteCount):
        n = flp.score.getNote(i)
        if fd_start <= n.time < fd_end and n.number <= 48:
            continue
        if n.number <= 48 and (n.time % ppq) != 0:
            n.time = max(0, n.time + six_ms_ticks)
        kept.append(n)
    flp.score.clearNotes()
    for note in kept:
        flp.score.addNote(note)
'''
    ast.parse(src)
    out_pyscript.parent.mkdir(parents=True, exist_ok=True)
    out_pyscript.write_text(src, encoding="utf-8")
    return str(out_pyscript)


def _build_scala_tuning(out_scl: Path) -> str:
    """Generates G Cosmic Dorian 5-Limit Scala tuning file."""
    scl = """! G_Cosmic_Dorian_5Limit.scl
!
G Cosmic Dorian (5-Limit Just Intonation / Cosmic House 122 BPM)
 12
!
 16/15
 9/8
 6/5
 5/4
 4/3
 45/32
 3/2
 8/5
 5/3
 9/5
 15/8
 2/1
"""
    out_scl.parent.mkdir(parents=True, exist_ok=True)
    out_scl.write_text(scl, encoding="utf-8")
    return str(out_scl)


def _section_rms_dbfs(left: np.ndarray, right: np.ndarray, start: int, end: int) -> float:
    """Measures stereo RMS in dBFS over sample range `[start, end)` safely without mutation."""
    s0 = max(0, int(start))
    s1 = min(len(left), int(end))
    if s1 <= s0:
        return -120.0
    l_slice = np.array(left[s0:s1], dtype=np.float64, copy=True)
    r_slice = np.array(right[s0:s1], dtype=np.float64, copy=True)
    mono = 0.5 * (l_slice + r_slice)
    rms = math.sqrt(float(np.dot(mono, mono)) / float(len(mono)))
    return round(20.0 * math.log10(max(rms, 1e-9)), 2)


def _run_external_rubin_linter(master_wav: Path) -> Dict[str, Any]:
    """
    Runs external `audit_acoustic_exergy.py` linter in silicon if installed locally,
    evaluating its functions with read-only frozen arrays to guard against Python 3.14
    + NumPy 2.2 in-place temp-elision corruption.
    """
    if not RUBIN_LINTER_PATH.exists():
        return {"status": "SKIPPED_NOT_INSTALLED", "script": str(RUBIN_LINTER_PATH)}
    try:
        spec = importlib.util.spec_from_file_location("c5_rubin_auditor_ext", str(RUBIN_LINTER_PATH))
        if spec is None or spec.loader is None:
            return {"status": "ERROR", "error": "Unable to load external Rubin auditor spec"}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        stereo, sr = load_wav_stereo(str(master_wav))
        l_ro = freeze_array(np.array(stereo[:, 0], dtype=np.float64, copy=True))
        r_ro = freeze_array(np.array(stereo[:, 1], dtype=np.float64, copy=True))
        m_ro = freeze_array(0.5 * (l_ro + r_ro))

        cf = float(mod.compute_crest_factor(m_ro))
        sfm_mid = float(mod.compute_spectral_flatness_mid(m_ro, fs=sr))
        lpc = float(mod.compute_low_end_phase_coherence(l_ro, r_ro, fs=sr))
        tsi = float(mod.compute_temporal_smearing_index(m_ro, fs=sr))
        true_peak_dbfs = round(20.0 * math.log10(max(1e-6, float(np.max(np.abs(m_ro))))), 2)

        anomalies: List[str] = []
        if cf < 8.0:
            anomalies.append(f"Crest Factor {cf:.2f} dB < 8.0 dB")
        if sfm_mid > 0.35:
            anomalies.append(f"Wiener Spectral Flatness (500-5000Hz) {sfm_mid:.4f} > 0.35")
        if lpc < 0.85:
            anomalies.append(f"Low-End Phase Coherence {lpc:.3f} < 0.85")
        if tsi > 0.65:
            anomalies.append(f"Temporal Smearing Index {tsi:.3f} > 0.65")

        passed = len(anomalies) == 0
        proc = subprocess.run(
            [sys.executable, str(RUBIN_LINTER_PATH), str(master_wav)],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return {
            "status": "PASSED" if (passed and proc.returncode == 0) else "FAILED",
            "verdict": "EXERGÍA PURA (EL HUESO)" if passed else "NATA ACÚSTICA DETECTADA",
            "crest_factor_db": round(cf, 2),
            "wiener_sfm_500_5000hz": round(sfm_mid, 4),
            "low_end_phase_coherence": round(lpc, 4),
            "temporal_smearing_index": round(tsi, 3),
            "true_peak_dbfs": true_peak_dbfs,
            "anomalies": anomalies,
            "subprocess_returncode": proc.returncode,
            "subprocess_stdout": proc.stdout.strip(),
        }
    except Exception as exc:
        return {"status": "ERROR", "error": str(exc)}


def build_cosmic_house_122(
    total_bars: int = DEFAULT_TOTAL_BARS,
    bpm: float = DEFAULT_BPM,
    profile_name: str = "deep_house",
    output_dir: Optional[str] = None,
    deploy_fl_assets: bool = True,
) -> Dict[str, Any]:
    """
    Produces the complete 48 kHz / 24-bit COSMIC HOUSE track, multitrack stems,
    SMF Type 1 MIDI, binary .flp, .pyscript, .scl, and C5-REAL audit receipt.
    """
    if total_bars < 16:
        raise ValueError("total_bars must be >= 16")

    out_root = (
        Path(output_dir).expanduser().resolve()
        if output_dir
        else (resolve_bounces_dir() / "Cosmic_House_Groove_122")
    )
    stems_dir = out_root / "stems"
    out_root.mkdir(parents=True, exist_ok=True)
    stems_dir.mkdir(parents=True, exist_ok=True)

    beat_sec = 60.0 / float(bpm)
    beat_samples = int(round(beat_sec * SAMPLE_RATE))
    bar_samples = 4 * beat_samples
    step_samples = beat_samples // 4
    n_samples = total_bars * bar_samples

    # Deterministic False Drop Vacuum at Bar 60 beats 3-4 (or final pre-drop bar if <64 bars)
    fd_bar = 59 if total_bars >= 64 else max(4, total_bars - 5)
    fd_start = fd_bar * bar_samples + 2 * beat_samples
    fd_end = (fd_bar + 1) * bar_samples
    living_exit_start = (total_bars - 1) * bar_samples + int(round(0.25 * bar_samples))

    drift = _voss_clarke_1f_drift(max(2048, total_bars * 16), seed=1222026)
    pools = _load_percussion_assets(sample_rate=SAMPLE_RATE)

    # 1) Synthesize all stems cleanly
    kick_m, kick_onsets = _generate_kick_stem(
        n_samples, bar_samples, beat_samples, total_bars, fd_start, fd_end, living_exit_start, drift
    )
    bass_m = _generate_syncopated_bass_stem(
        n_samples, bar_samples, beat_samples, step_samples, total_bars, kick_onsets, fd_start, fd_end, living_exit_start, drift
    )
    arp_l, arp_r = _generate_retro_arp_stem(
        n_samples, bar_samples, step_samples, total_bars, fd_start, fd_end, living_exit_start, drift
    )
    (keys_l, keys_r), (pad_l, pad_r) = _generate_airy_keys_and_pads(
        n_samples, bar_samples, total_bars, fd_start, fd_end, living_exit_start, drift
    )
    gtr_l, gtr_r = _generate_filtered_disco_guitars(
        n_samples, bar_samples, step_samples, total_bars, fd_start, fd_end, living_exit_start, drift
    )
    lead_l, lead_r = _generate_swirling_analog_lead_stem(
        n_samples, bar_samples, step_samples, total_bars, living_exit_start
    )
    perc_l, perc_r = _generate_dynamic_percussion_stem(
        n_samples, bar_samples, beat_samples, step_samples, total_bars, fd_start, fd_end, living_exit_start, drift, pools
    )

    # 2) Non-commutative Pre-Filtered Recursive Dub Echo (disco guitars + swirling lead + arp)
    dub_src_l = 0.65 * gtr_l + 0.60 * lead_l + 0.35 * arp_l + 0.25 * keys_l
    dub_src_r = 0.65 * gtr_r + 0.60 * lead_r + 0.35 * arp_r + 0.25 * keys_r
    dub_l, dub_r = apply_noncommutative_dub_echo(
        dub_src_l,
        dub_src_r,
        sample_rate=SAMPLE_RATE,
        delay_sec=0.75 * beat_sec,  # dotted-8th hypnotic cosmic house echo
        feedback=0.38,
        lpf_hz=2800.0,
        hpf_hz=240.0,
        wet=0.28,
        taps=4,
    )
    # Subtract dry portion to keep Dub Echo stem discrete
    dub_l = dub_l - 0.72 * dub_src_l
    dub_r = dub_r - 0.72 * dub_src_r
    dub_l, dub_r = carve_polyphonic_mud(dub_l, dub_r, sample_rate=SAMPLE_RATE, hpf_hz=220.0, mud_hz=375.0, mud_cut_blend=0.35, air_lpf_hz=6800.0)
    dub_l, dub_r = _apply_living_exit_rc(dub_l, dub_r, living_exit_start, tau_sec=0.82)
    dub_l, dub_r = freeze_array(dub_l), freeze_array(dub_r)

    # 3) Active Warm Analog Tape Bed (-57.0 dBFS continuous floor)
    tape_l, tape_r = generate_warm_analog_tape_bed(n_samples, sample_rate=SAMPLE_RATE, level_dbfs=-57.0, seed=1999)
    tape_l, tape_r = _apply_living_exit_rc(tape_l, tape_r, n_samples - int(0.45 * SAMPLE_RATE), tau_sec=0.14)
    tape_l, tape_r = freeze_array(tape_l), freeze_array(tape_r)

    # 4) Coherent Shared Room on melodic & percussion tops
    room_in_l = 0.22 * keys_l + 0.25 * pad_l + 0.22 * gtr_l + 0.28 * lead_l + 0.16 * perc_l
    room_in_r = 0.22 * keys_r + 0.25 * pad_r + 0.22 * gtr_r + 0.28 * lead_r + 0.16 * perc_r
    real_ir = None
    ir_name = "c5_schroeder_coherent"
    try:
        loaded_ir = get_real_room_ir(style="chamber_warm", sample_rate=SAMPLE_RATE, max_sec=1.2)
        if loaded_ir is not None:
            real_ir, ir_name = loaded_ir
    except Exception:
        real_ir = None

    room_wet_l, room_wet_r = apply_coherent_shared_room(
        room_in_l, room_in_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, rt60_sec=1.22, wet=0.14
    )
    if real_ir is not None and real_ir.ndim == 2 and len(real_ir) > 64:
        conv_l = signal.fftconvolve(room_in_l, real_ir[:, 0], mode="full")[:n_samples] * 0.08
        conv_r = signal.fftconvolve(room_in_r, real_ir[:, 1], mode="full")[:n_samples] * 0.08
        room_wet_l = 0.65 * room_wet_l + 0.35 * conv_l
        room_wet_r = 0.65 * room_wet_r + 0.35 * conv_r
    room_wet_l, room_wet_r = carve_polyphonic_mud(room_wet_l, room_wet_r, sample_rate=SAMPLE_RATE, hpf_hz=210.0, mud_hz=375.0, mud_cut_blend=0.40, air_lpf_hz=11000.0)
    room_wet_l, room_wet_r = _apply_living_exit_rc(room_wet_l, room_wet_r, living_exit_start, tau_sec=0.72)
    room_wet_l, room_wet_r = freeze_array(room_wet_l), freeze_array(room_wet_r)

    # 5) Zero-Crackle Audits on Sub-Bass & Swirling Lead Stems
    bass_zc = check_zero_crackle_derivatives(bass_m, max_d1=0.015, max_d2=0.005)
    lead_zc = check_zero_crackle_derivatives(0.5 * (lead_l + lead_r), max_d1=0.015, max_d2=0.005)
    if not bass_zc["zero_crackle_passed"]:
        raise RuntimeError(f"Zero-Crackle failed on Syncopated Bass: {bass_zc}")
    if not lead_zc["zero_crackle_passed"]:
        raise RuntimeError(f"Zero-Crackle failed on Swirling Lead: {lead_zc}")

    # 6) Export 10 Multitrack 48 kHz / 24-bit WAV Stems
    stem_specs = (
        ("01_Kick_Cosmic_49Hz.wav", kick_m, kick_m),
        ("02_Syncopated_Cosmic_Bass.wav", bass_m, bass_m),
        ("03_Retro_Futuristic_Arp.wav", arp_l, arp_r),
        ("04_Airy_Keys_Rhodes.wav", keys_l, keys_r),
        ("05_Subtle_Cosmic_Pads.wav", pad_l, pad_r),
        ("06_Filtered_Disco_Guitars.wav", gtr_l, gtr_r),
        ("07_Swirling_Analog_Lead.wav", lead_l, lead_r),
        ("08_Dynamic_Percussion.wav", perc_l, perc_r),
        ("09_NonCommutative_Dub_Echo.wav", dub_l, dub_r),
        ("10_Analog_Tape_Bed.wav", tape_l, tape_r),
    )
    stem_paths: Dict[str, str] = {}
    for fname, sl, sr in stem_specs:
        p = stems_dir / fname
        write_pcm_wav(p, sl, sr, sample_rate=SAMPLE_RATE, bit_depth=24, dither=True)
        stem_paths[fname] = str(p)

    # 7) Sum & Calibrate Premaster Bus -> Reverse-Engineered Mastering
    mix_l = (
        1.00 * kick_m
        + 0.92 * bass_m
        + 0.64 * arp_l
        + 0.68 * keys_l
        + 0.56 * pad_l
        + 0.48 * gtr_l
        + 0.85 * lead_l
        + 0.72 * perc_l
        + 0.55 * dub_l
        + 0.42 * room_wet_l
        + 1.00 * tape_l
    )
    mix_r = (
        1.00 * kick_m
        + 0.92 * bass_m
        + 0.64 * arp_r
        + 0.68 * keys_r
        + 0.56 * pad_r
        + 0.48 * gtr_r
        + 0.85 * lead_r
        + 0.72 * perc_r
        + 0.55 * dub_r
        + 0.42 * room_wet_r
        + 1.00 * tape_r
    )
    mix_l, mix_r = enforce_low_end_mono(mix_l, mix_r, cutoff_hz=125.0, sample_rate=SAMPLE_RATE)
    mix_l, mix_r = _normalize_peak(mix_l, mix_r, 0.68)
    mix_l, mix_r = _apply_living_exit_rc(mix_l, mix_r, living_exit_start, tau_sec=0.68)

    premaster_wav = out_root / "Cosmic_House_Groove_122_Premaster.wav"
    master_wav = out_root / "Cosmic_House_Groove_122_Master.wav"
    write_pcm_wav(premaster_wav, mix_l, mix_r, sample_rate=SAMPLE_RATE, bit_depth=24, dither=False)

    master_res = master_audio_reverse_engineered(
        str(premaster_wav),
        output_wav=str(master_wav),
        profile_name=profile_name,
        bit_depth=24,
    )

    m_stereo, m_sr = load_wav_stereo(str(master_wav))
    rubin_master = compute_rubin_metrics(m_stereo[:, 0], m_stereo[:, 1], sample_rate=m_sr)
    if not rubin_master["is_pure_bone"]:
        raise RuntimeError(f"Rubin Acoustic Gate FAILED on master: {rubin_master}")

    rubin_ext = _run_external_rubin_linter(master_wav)
    if rubin_ext.get("status") == "FAILED":
        raise RuntimeError(f"External Rubin Linter FAILED: {rubin_ext}")

    # Optional 320 kbps CBR MP3
    master_mp3 = out_root / "Cosmic_House_Groove_122_Master.mp3"
    mp3_path_str: Optional[str] = None
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        try:
            proc_mp3 = subprocess.run(
                [ffmpeg_bin, "-y", "-i", str(master_wav), "-c:a", "libmp3lame", "-b:a", "320k", str(master_mp3)],
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            if proc_mp3.returncode == 0 and master_mp3.exists():
                mp3_path_str = str(master_mp3)
        except Exception:
            mp3_path_str = None

    # 8) MIDI + Binary .flp + .pyscript + .scl
    midi_path = out_root / "Cosmic_House_Groove_122.mid"
    flp_path = out_root / "Cosmic_House_Groove_122.flp"
    pyscript_path = out_root / "Cosmic_House_Groove_122_Groove.pyscript"
    scl_path = out_root / "G_Cosmic_Dorian_5Limit.scl"

    _build_cosmic_house_midi(bpm=bpm, total_bars=total_bars, out_midi=midi_path)
    compile_multitrack_stems_flp(
        stems_dir=str(stems_dir),
        project_title="Cosmic House Groove 122 BPM",
        bpm=bpm,
        output_flp=str(flp_path),
        total_bars=total_bars,
    )
    _build_fl_pyscript(pyscript_path, bpm=bpm)
    _build_scala_tuning(scl_path)

    deployed_assets: List[str] = []
    if deploy_fl_assets:
        fl_user = resolve_fl_user_dir()
        if fl_user.exists() and fl_user.is_dir():
            try:
                pr_dir = fl_user / "FL Studio" / "Settings" / "Piano roll scripts"
                tn_dir = fl_user / "FL Studio" / "Data" / "Patches" / "Scores" / "Tunings"
                pr_dir.mkdir(parents=True, exist_ok=True)
                tn_dir.mkdir(parents=True, exist_ok=True)
                dst_py = pr_dir / pyscript_path.name
                dst_scl = tn_dir / scl_path.name
                shutil.copy2(pyscript_path, dst_py)
                shutil.copy2(scl_path, dst_scl)
                deployed_assets.extend([str(dst_py), str(dst_scl)])
            except Exception:
                pass

    # 9) Section & False Drop Telemetry + Receipt
    fd_kick_rms = _section_rms_dbfs(kick_m, kick_m, fd_start + int(0.015 * SAMPLE_RATE), fd_end - int(0.015 * SAMPLE_RATE))
    fd_perc_rms = _section_rms_dbfs(perc_l, perc_r, fd_start + int(0.015 * SAMPLE_RATE), fd_end - int(0.015 * SAMPLE_RATE))
    fd_master_rms = _section_rms_dbfs(m_stereo[:, 0], m_stereo[:, 1], fd_start + int(0.015 * SAMPLE_RATE), fd_end - int(0.015 * SAMPLE_RATE))
    living_end_peak = float(np.max(np.abs(m_stereo[-8:])))

    hashes = {
        "master_wav_sha256": _sha256_file(master_wav),
        "premaster_wav_sha256": _sha256_file(premaster_wav),
        "midi_sha256": _sha256_file(midi_path),
        "flp_sha256": _sha256_file(flp_path),
        "pyscript_sha256": _sha256_file(pyscript_path),
        "scl_sha256": _sha256_file(scl_path),
    }

    receipt = {
        "status": "SUCCESS",
        "title": "Cosmic House Groove 122 BPM",
        "classification": "AUTÓMATA_SINTÉTICO_ESTRUCTURAL",
        "bpm": bpm,
        "key": "G Dorian / G Minor (49.00 Hz G1 Kick Anchor)",
        "sample_rate": SAMPLE_RATE,
        "bit_depth": 24,
        "total_bars": total_bars,
        "duration_sec": round(n_samples / float(SAMPLE_RATE), 3),
        "sections": [dict(sec) for sec in SECTION_LAYOUT],
        "output_dir": str(out_root),
        "master_wav": str(master_wav),
        "premaster_wav": str(premaster_wav),
        "master_mp3": mp3_path_str,
        "midi_file": str(midi_path),
        "flp_file": str(flp_path),
        "pyscript_file": str(pyscript_path),
        "scala_file": str(scl_path),
        "stems": stem_paths,
        "deployed_fl_assets": deployed_assets,
        "mastering": master_res,
        "rubin_gate": rubin_master,
        "rubin_external_linter": rubin_ext,
        "zero_crackle_audits": {
            "02_Syncopated_Cosmic_Bass": bass_zc,
            "07_Swirling_Analog_Lead": lead_zc,
        },
        "arrangement_telemetry": {
            "intro_kick_rms_dbfs": _section_rms_dbfs(kick_m, kick_m, 0, 16 * bar_samples),
            "verse_1_keys_rms_dbfs": _section_rms_dbfs(keys_l, keys_r, 16 * bar_samples, 24 * bar_samples),
            "pre_chorus_1_guitar_rms_dbfs": _section_rms_dbfs(gtr_l, gtr_r, 24 * bar_samples, 32 * bar_samples),
            "drop_1_lead_rms_dbfs": _section_rms_dbfs(lead_l, lead_r, 32 * bar_samples, 44 * bar_samples),
            "drop_1_perc_rms_dbfs": _section_rms_dbfs(perc_l, perc_r, 32 * bar_samples, 44 * bar_samples),
            "false_drop_bar60_kick_rms_dbfs": fd_kick_rms,
            "false_drop_bar60_perc_rms_dbfs": fd_perc_rms,
            "false_drop_bar60_master_rms_dbfs": fd_master_rms,
            "living_exit_end_peak": living_end_peak,
        },
        "assets_bridge_telemetry": {
            "room_ir": ir_name,
            "round_robin_pools_loaded": {k: len(v) for k, v in pools.items()},
        },
        "hashes": hashes,
    }
    receipt_path = out_root / "production_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    receipt["receipt_file"] = str(receipt_path)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Build C5-REAL Cosmic House Groove (122 BPM, 64 bars).")
    parser.add_argument("--bars", type=int, default=DEFAULT_TOTAL_BARS, help="Total bar count (default: 64)")
    parser.add_argument("--bpm", type=float, default=DEFAULT_BPM, help="Tempo in BPM (default: 122.0)")
    parser.add_argument("--profile", type=str, default="deep_house", help="Mastering profile (default: deep_house)")
    parser.add_argument("--output-dir", type=str, default=None, help="Optional output directory")
    parser.add_argument("--no-deploy", action="store_true", help="Skip copying .pyscript/.scl to FL User Dir")
    args = parser.parse_args()

    res = build_cosmic_house_122(
        total_bars=args.bars,
        bpm=args.bpm,
        profile_name=args.profile,
        output_dir=args.output_dir,
        deploy_fl_assets=not args.no_deploy,
    )
    print(json.dumps({"status": res["status"], "master_wav": res["master_wav"], "rubin_gate": res["rubin_gate"]}, indent=2))


if __name__ == "__main__":
    main()
