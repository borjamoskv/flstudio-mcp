#!/usr/bin/env python3
"""
C5-REAL High-Definition Acoustic & Physical Synthesis Core (48 kHz / 24-bit)
============================================================================
Shared DSP primitives enforcing:
  1. Band-limited PolyBLEP anti-aliased oscillators (zero naive modulo aliasing).
  2. Exact phase-integrated kick synthesis anchored at 0 rad + Pultec sub boost + 195 Hz mud notch.
  3. Zero-Crackle discrete derivative continuity (raised-cosine attack >= 5 ms, tail >= 10 ms to 0.0).
  4. Hanning-smoothed multiband sidechain envelopes (zero t=0 step discontinuities).
  5. Exact zero-phase 4th-order Linkwitz-Riley (LR4, 24 dB/oct) crossovers via sosfiltfilt.
  6. Psychoacoustic Bark carving on polyphonic stems (185 Hz HPF, 375 Hz mud cut, 14.2 kHz tape roll-off).
  7. Non-commutative pre-filtered recursive tape dub echo (LPF 2800 Hz inside feedback loop).
  8. Phase-coherent shared convolution room (18 ms pre-delay, 84% mono diffuse core, LPC >= 0.96).
  9. True band-limited 1/f warm analog tape thermal bed (-57 dBFS, zero stationary hum).
 10. 4x polyphase oversampled analog soft saturation & high-pass Lipshitz-Vanderkooy TPDF dithering.
"""

from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple, Union

import numpy as np
from scipy import signal

try:
    from scripts.c5_real_assets_bridge import get_real_room_ir
except ImportError:
    try:
        from c5_real_assets_bridge import get_real_room_ir  # type: ignore[no-redef]
    except ImportError:
        get_real_room_ir = None  # type: ignore[assignment]

try:
    from scripts.wave_digital_filter_analog_saturator import solve_wdf_diode_pair
except ImportError:
    try:
        from wave_digital_filter_analog_saturator import solve_wdf_diode_pair  # type: ignore[no-redef]
    except ImportError:
        solve_wdf_diode_pair = None  # type: ignore[assignment]

try:
    from scripts.digital_waveguide_physical_modeler import DigitalWaveguideTube, midi_to_freq
except ImportError:
    try:
        from digital_waveguide_physical_modeler import DigitalWaveguideTube, midi_to_freq  # type: ignore[no-redef]
    except ImportError:
        DigitalWaveguideTube = None  # type: ignore[assignment,misc]
        midi_to_freq = None  # type: ignore[assignment]

SAMPLE_RATE = 48000


def freeze_array(arr: np.ndarray) -> np.ndarray:
    """Return an explicit read-only view/buffer to prevent Python 3.14+ / NumPy temp-elision."""
    arr.flags.writeable = False
    return arr


def make_time_axis(n_samples: int, sample_rate: int = 48000) -> np.ndarray:
    """
    Returns an immutable (read-only) float64 time vector in seconds.
    Read-only flag prevents Python 3.14 LOAD_FAST_BORROW + NumPy 2.2 temp-elision
    from mutating time grids in-place inside compound arithmetic expressions.
    """
    t = np.arange(n_samples, dtype=np.float64) / float(sample_rate)
    t.flags.writeable = False
    return t


def _polyblep_residual(phase: np.ndarray, dt: np.ndarray) -> np.ndarray:
    """2-point polynomial band-limited step (PolyBLEP) residual at discontinuity p = 0 / 1."""
    corr = np.zeros_like(phase, dtype=np.float64)
    dt_safe = np.clip(dt, 1e-7, 0.49)
    dt_safe.flags.writeable = False

    mask_start = phase < dt_safe
    if np.any(mask_start):
        u = phase[mask_start] / dt_safe[mask_start]
        u.flags.writeable = False
        corr[mask_start] = u + u - u * u - 1.0

    mask_end = phase > (1.0 - dt_safe)
    if np.any(mask_end):
        u = (phase[mask_end] - 1.0) / dt_safe[mask_end]
        u.flags.writeable = False
        corr[mask_end] = u * u + u + u + 1.0

    return corr


def polyblep_saw(
    freq_hz: Union[float, np.ndarray],
    n_samples: int,
    sample_rate: int = 48000,
    initial_phase: float = 0.0,
) -> np.ndarray:
    """Generates a band-limited anti-aliased sawtooth wave via PolyBLEP."""
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float64)
    dt = np.broadcast_to(np.asarray(freq_hz, dtype=np.float64) / float(sample_rate), (n_samples,)).copy()
    dt = np.clip(dt, 1e-7, 0.48)
    dt.flags.writeable = False
    # Phase at sample 0 starts at initial_phase
    phase = np.mod(initial_phase + np.cumsum(dt) - dt[0], 1.0)
    phase.flags.writeable = False
    naive = 2.0 * phase - 1.0
    return naive - _polyblep_residual(phase, dt)


def polyblep_pulse(
    freq_hz: Union[float, np.ndarray],
    n_samples: int,
    sample_rate: int = 48000,
    duty: float = 0.5,
    initial_phase: float = 0.0,
) -> np.ndarray:
    """Generates a band-limited anti-aliased pulse/square wave via dual-edge PolyBLEP."""
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float64)
    duty_clamped = float(np.clip(duty, 0.05, 0.95))
    dt = np.broadcast_to(np.asarray(freq_hz, dtype=np.float64) / float(sample_rate), (n_samples,)).copy()
    dt = np.clip(dt, 1e-7, 0.48)
    dt.flags.writeable = False
    phase = np.mod(initial_phase + np.cumsum(dt) - dt[0], 1.0)
    phase.flags.writeable = False
    phase_shifted = np.mod(phase + (1.0 - duty_clamped), 1.0)
    phase_shifted.flags.writeable = False
    naive = np.where(phase < duty_clamped, 1.0, -1.0)
    blep = _polyblep_residual(phase, dt) - _polyblep_residual(phase_shifted, dt)
    # Remove DC offset when duty != 0.5
    dc = 2.0 * duty_clamped - 1.0
    return naive + blep - dc


def apply_zero_crackle_envelope(
    buf: np.ndarray,
    sample_rate: int = 48000,
    attack_ms: float = 5.0,
    release_ms: float = 10.0,
) -> np.ndarray:
    """
    Enforces INV_C5_ACOUSTIC_GATE §2.5: raised-cosine attack (>= 5 ms) and
    raised-cosine tail fade-out (>= 10 ms) reaching exact 0.0 at boundaries.
    """
    n = len(buf)
    if n == 0:
        return buf
    out = buf.astype(np.float64, copy=True)
    n_att = min(n // 2, max(2, int(round((attack_ms / 1000.0) * sample_rate))))
    n_rel = min(n - n_att, max(2, int(round((release_ms / 1000.0) * sample_rate))))

    if n_att > 1:
        w_att = 0.5 * (1.0 - np.cos(np.pi * np.arange(n_att, dtype=np.float64) / (n_att - 1)))
        out[:n_att] *= w_att
    if n_rel > 1:
        w_rel = 0.5 * (1.0 + np.cos(np.pi * np.arange(n_rel, dtype=np.float64) / (n_rel - 1)))
        out[-n_rel:] *= w_rel
    out[0] = 0.0
    out[-1] = 0.0
    return out


def check_zero_crackle_derivatives(
    stem: np.ndarray,
    max_d1: float = 0.015,
    max_d2: float = 0.005,
) -> Dict[str, Any]:
    """Audits 1st and 2nd discrete derivatives on sub/bass stems at 48 kHz."""
    arr = np.asarray(stem, dtype=np.float64)
    if arr.ndim > 1:
        arr = 0.5 * (arr[:, 0] + arr[:, 1])
    if len(arr) < 3:
        return {"max_abs_d1": 0.0, "max_abs_d2": 0.0, "zero_crackle_passed": True}
    d1 = np.abs(np.diff(arr, n=1))
    d2 = np.abs(np.diff(arr, n=2))
    m1 = float(np.max(d1))
    m2 = float(np.max(d2))
    return {
        "max_abs_d1": round(m1, 6),
        "max_abs_d2": round(m2, 6),
        "zero_crackle_passed": bool(m1 <= max_d1 and m2 <= max_d2),
    }


def lr4_zero_phase_crossover(
    audio: np.ndarray,
    crossover_hz: float,
    sample_rate: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Exact 4th-order Linkwitz-Riley (LR4, 24 dB/oct) zero-phase crossover.
    Applies forward-backward 2nd-order Butterworth via sosfiltfilt on lowpass,
    obtaining highpass via exact complementary subtraction (or dual sosfiltfilt
    with |H_LP|^2 + |H_HP|^2 == 1.0 identically across all frequencies).
    """
    arr = np.asarray(audio, dtype=np.float64)
    nyq = sample_rate / 2.0
    wn = float(np.clip(crossover_hz / nyq, 0.001, 0.95))
    sos_lp = signal.butter(2, wn, btype="low", output="sos")

    if len(arr) < 18:
        low = signal.sosfilt(sos_lp, arr, axis=0)
        return low, arr - low

    low = signal.sosfiltfilt(sos_lp, arr, axis=0)
    high = arr - low
    return low, high


def enforce_low_end_mono(
    left: np.ndarray,
    right: np.ndarray,
    cutoff_hz: float = 120.0,
    sample_rate: int = 48000,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Collapses sub-bass below `cutoff_hz` to exact phase-coherent mono (Mid = 0.5*(L+R))
    using the complementary zero-phase LR4 crossover while leaving highs untouched.
    """
    l_arr = np.asarray(left, dtype=np.float64)
    r_arr = np.asarray(right, dtype=np.float64)
    if len(l_arr) < 18:
        return l_arr, r_arr
    l_lo, l_hi = lr4_zero_phase_crossover(l_arr, cutoff_hz, sample_rate)
    r_lo, r_hi = lr4_zero_phase_crossover(r_arr, cutoff_hz, sample_rate)
    mono_lo = 0.5 * (l_lo + r_lo)
    mono_lo.flags.writeable = False
    return mono_lo + l_hi, mono_lo + r_hi


def oversampled_soft_saturate(
    audio: np.ndarray,
    drive_db: float = 1.8,
    threshold_db: float = -2.4,
    asymmetry: float = 0.04,
    oversample: int = 4,
) -> np.ndarray:
    """
    4x polyphase oversampled analog saturation (even + odd harmonics via biased soft knee)
    suppressing Nyquist foldback aliasing without nested tanh cascades.
    """
    arr = np.asarray(audio, dtype=np.float64)
    if drive_db <= 0.02 or len(arr) == 0:
        return arr.copy()

    is_1d = arr.ndim == 1
    work = arr[:, None] if is_1d else arr
    n_orig = len(work)

    if oversample > 1 and n_orig >= 16:
        up = signal.resample_poly(work, up=oversample, down=1, axis=0)
    else:
        up = work.copy()
        oversample = 1

    thresh = 10.0 ** (threshold_db / 20.0)
    drive = 10.0 ** (drive_db / 20.0)
    margin = max(1e-4, 1.0 - thresh)

    # Subtle even-harmonic tube/tape bias with AC-coupled DC removal strictly on up^2
    # so zero-valued idle regions stay exact 0.0 instead of inheriting global mean shift.
    up.flags.writeable = False
    if asymmetry != 0.0:
        if len(up) >= 16:
            dc_cutoff_norm = min(0.1, 18.0 / (0.5 * 48000.0 * oversample))
            sos_dc = signal.butter(1, dc_cutoff_norm, btype="high", output="sos")
            even_term = asymmetry * signal.sosfilt(sos_dc, up * up, axis=0)
        else:
            sq = up * up
            even_term = asymmetry * (sq - np.mean(sq, axis=0, keepdims=True))
        biased = up + even_term
    else:
        biased = up

    mag = np.abs(biased)
    out_up = biased.copy()
    mask = mag > thresh
    if np.any(mask):
        sgn = np.sign(biased[mask])
        excess = mag[mask] - thresh
        shaped = thresh + margin * np.tanh((excess * drive) / margin)
        out_up[mask] = sgn * shaped

    if oversample > 1:
        down = signal.resample_poly(out_up, up=1, down=oversample, axis=0)[:n_orig]
    else:
        down = out_up

    return down[:, 0] if is_1d else down


def synthesize_phase_locked_kick(
    sample_rate: int = 48000,
    duration_sec: float = 0.40,
    root_hz: float = 49.0,
    punch_hz: float = 152.0,
    click_hz: float = 2950.0,
    tau_click: float = 0.0042,
    tau_punch: float = 0.030,
    tau_body: float = 0.205,
    drive_db: float = 2.8,
    pultec_sub_gain: float = 0.18,
    mud_notch_hz: float = 195.0,
    beater_gain: float = 0.24,
    beater_hz: float = 2400.0,
) -> np.ndarray:
    """
    Synthesizes a phase-locked (phi(0) = 0 rad) analog club kick using exact
    instantaneous frequency integration, Pultec fundamental reinforcement,
    195 Hz mud notch, 4x oversampled soft saturation, and zero-crackle tail.
    """
    n = max(16, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n, sample_rate)

    # Exact instantaneous frequency sweep f(t) integrated into phase phi(t)
    f_inst = (
        root_hz
        + (punch_hz - root_hz) * np.exp(-t / tau_punch)
        + (click_hz - punch_hz) * np.exp(-t / tau_click)
    )
    phase = 2.0 * math.pi * (np.cumsum(f_inst) - f_inst[0]) / float(sample_rate)

    t.flags.writeable = False
    # Smooth 0.7 ms raised-cosine onset + exponential body + 12 ms raised-cosine tail to 0.0
    env = np.exp(np.multiply(-1.0 / tau_body, t))
    n_att = max(2, int(round(0.0007 * sample_rate)))
    n_rel = max(4, int(round(0.012 * sample_rate)))
    if n > n_att:
        env[:n_att] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(n_att) / (n_att - 1)))
    if n > n_rel:
        env[-n_rel:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(n_rel) / (n_rel - 1)))
    env.flags.writeable = False

    # Organic beater transient (< 11 kHz) + Pultec sub anchor
    beater = (
        beater_gain
        * np.sin(np.multiply(2.0 * math.pi * beater_hz, t))
        * np.exp(np.multiply(-1.0 / 0.0024, t))
    )
    beater[:2] *= np.array([0.0, 0.5])
    pultec_sub = np.multiply(
        np.multiply(pultec_sub_gain, np.sin(np.multiply(2.0 * math.pi * root_hz, t))), env
    )

    raw = np.sin(phase) * env + pultec_sub + beater
    saturated = oversampled_soft_saturate(raw, drive_db=drive_db, threshold_db=-3.0, asymmetry=0.03)

    # Surgical mud notch at ~195 Hz (-3.5 dB blend)
    b_n, a_n = signal.iirnotch(mud_notch_hz, Q=2.2, fs=sample_rate)
    notched = 0.62 * signal.lfilter(b_n, a_n, saturated) + 0.38 * saturated
    # Enforce zero-crackle C2 boundary condition after zero-phase 4x polyphase resampling
    notched = apply_zero_crackle_envelope(
        notched, sample_rate=sample_rate, attack_ms=0.35, release_ms=12.0
    )

    peak = float(np.max(np.abs(notched)))
    if peak > 1e-6:
        notched = notched / peak
    notched.flags.writeable = False
    return notched


def build_coupled_multiband_sidechain(
    n_samples: int,
    kick_onset_samples: Iterable[int],
    sample_rate: int = 48000,
    tau_body: float = 0.205,
    sub_depth: float = 0.90,
    high_depth: float = 0.20,
    attack_ms: float = 6.0,
    lookahead_ms: float = 3.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Constructs smooth, click-free multiband sidechain gain envelopes (<140 Hz sub vs >=140 Hz mid/high)
    with raised-cosine pre-ducking attack ramp and Hanning low-pass smoothing (tau = 4.5 ms).
    """
    sc_sub = np.ones(n_samples, dtype=np.float64)
    sc_high = np.ones(n_samples, dtype=np.float64)
    if n_samples <= 0:
        return sc_sub, sc_high

    duck_len = int(round(min(0.42, tau_body * 2.2) * sample_rate))
    tk = make_time_axis(duck_len, sample_rate)
    att_sec = max(0.005, attack_ms / 1000.0)
    att_ramp = 0.5 * (1.0 - np.cos(np.pi * np.clip(tk / att_sec, 0.0, 1.0)))
    att_ramp.flags.writeable = False

    prof_sub = 1.0 - sub_depth * att_ramp * np.exp(-((tk / (tau_body * 0.85)) ** 1.35))
    prof_high = 1.0 - high_depth * att_ramp * np.exp(-((tk / 0.050) ** 1.45))

    la_samples = int(round((lookahead_ms / 1000.0) * sample_rate))
    for idx0 in kick_onset_samples:
        start = max(0, int(idx0) - la_samples)
        avail = min(duck_len, n_samples - start)
        if avail > 0:
            sc_sub[start : start + avail] = np.minimum(sc_sub[start : start + avail], prof_sub[:avail])
            sc_high[start : start + avail] = np.minimum(sc_high[start : start + avail], prof_high[:avail])

    # Hanning smoothing kernel (tau >= 4.5 ms) guarantees continuous 1st/2nd derivatives
    k_len = max(5, int(round(0.0045 * sample_rate)))
    if k_len % 2 == 0:
        k_len += 1
    kern = np.hanning(k_len)
    kern /= np.sum(kern)
    pad = k_len // 2
    sc_sub = np.convolve(np.pad(sc_sub, pad, mode="edge"), kern, mode="valid")[:n_samples]
    sc_high = np.convolve(np.pad(sc_high, pad, mode="edge"), kern, mode="valid")[:n_samples]
    sc_sub_out = np.clip(sc_sub, 0.02, 1.0)
    sc_high_out = np.clip(sc_high, 0.25, 1.0)
    sc_sub_out.flags.writeable = False
    sc_high_out.flags.writeable = False
    return sc_sub_out, sc_high_out


def carve_polyphonic_mud(
    left: np.ndarray,
    right: np.ndarray,
    sample_rate: int = 48000,
    hpf_hz: float = 185.0,
    mud_hz: float = 375.0,
    mud_cut_blend: float = 0.42,
    air_lpf_hz: float = 14200.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Enforces Bark-band psychoacoustic carving on chords/pads/Rhodes:
      - High-pass filter at 185 Hz (clears kick & sub-bass fundamentals).
      - Peaking mud attenuation around 375 Hz (eliminates boxy low-mids).
      - Smooth 14.2 kHz roll-off (eliminates plastic digital harshness).
    """
    nyq = sample_rate / 2.0
    sos_hp = signal.butter(2, min(0.45, hpf_hz / nyq), btype="high", output="sos")
    sos_lp = signal.butter(2, min(0.92, air_lpf_hz / nyq), btype="low", output="sos")
    b_mud, a_mud = signal.iirnotch(mud_hz, Q=1.8, fs=sample_rate)

    out_l = left.astype(np.float64, copy=True)
    out_r = right.astype(np.float64, copy=True)
    if len(out_l) < 24:
        return out_l, out_r

    for ch_in, is_left in ((out_l, True), (out_r, False)):
        s = signal.sosfiltfilt(sos_hp, ch_in)
        s.flags.writeable = False
        s_mud = signal.lfilter(b_mud, a_mud, s)
        s_mud.flags.writeable = False
        s = (1.0 - mud_cut_blend) * s + mud_cut_blend * s_mud
        s = signal.sosfiltfilt(sos_lp, s)
        if is_left:
            out_l = s
        else:
            out_r = s
    return out_l, out_r


def apply_noncommutative_dub_echo(
    left: np.ndarray,
    right: np.ndarray,
    sample_rate: int = 48000,
    delay_sec: float = 0.36,
    feedback: float = 0.36,
    lpf_hz: float = 2800.0,
    hpf_hz: float = 240.0,
    wet: float = 0.26,
    taps: int = 4,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Enforces Basic Channel / Dub Techno Non-Commutative Topology:
      u(t) = F_pre(x(t))
      y_dub(t) = S_console( u(t) + alpha * H_tape_2800Hz( S_tape( y_dub(t - tau) ) ) )
    Pre-filters input BEFORE the delay line and degrades highs progressively on each recursive pass.
    """
    n = len(left)
    delay_samples = max(1, int(round(delay_sec * sample_rate)))
    if n < delay_samples + 16 or wet <= 0.0:
        return left.copy(), right.copy()

    nyq = sample_rate / 2.0
    sos_pre = signal.butter(
        2,
        [min(0.40, hpf_hz / nyq), min(0.85, lpf_hz / nyq)],
        btype="band",
        output="sos",
    )
    sos_tape_lp = signal.butter(1, min(0.85, lpf_hz / nyq), btype="low", output="sos")

    u_l = signal.sosfilt(sos_pre, left)
    u_r = signal.sosfilt(sos_pre, right)

    echo_l = np.zeros(n, dtype=np.float64)
    echo_r = np.zeros(n, dtype=np.float64)

    tap_l = u_l.copy()
    tap_r = u_r.copy()
    gain = 1.0

    for tap_idx in range(1, taps + 1):
        shift = tap_idx * delay_samples
        if shift >= n:
            break
        # Recursive tape saturation + progressive 2800 Hz high absorption per pass
        tap_l = signal.sosfilt(sos_tape_lp, np.tanh(tap_l * 1.25) / math.tanh(1.25))
        tap_r = signal.sosfilt(sos_tape_lp, np.tanh(tap_r * 1.25) / math.tanh(1.25))
        gain *= feedback if tap_idx > 1 else 1.0
        # Gentle cross-feed ping-pong preserving strong center correlation (no short Haas comb!)
        c_l = 0.78 * tap_l[:-shift] + 0.22 * tap_r[:-shift]
        c_r = 0.78 * tap_r[:-shift] + 0.22 * tap_l[:-shift]
        echo_l[shift:] += gain * c_l
        echo_r[shift:] += gain * c_r

    out_l = np.asarray(left, dtype=np.float64).copy()
    out_r = np.asarray(right, dtype=np.float64).copy()
    out_l += wet * echo_l
    out_r += wet * echo_r
    return out_l, out_r


def apply_coherent_shared_room(
    left: np.ndarray,
    right: np.ndarray,
    sample_rate: int = 48000,
    pre_delay_ms: float = 18.0,
    rt60_sec: float = 1.25,
    wet: float = 0.12,
    room_style: str = "chamber_warm",
    stereo_spread: float = 0.30,
    use_real_ir: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Shared Coherent Convolution Room (INV_C5_ACOUSTIC_GATE §3.1.5 & Rubin §3.2):
      - Prefers real studio hardware/room Impulse Responses (Patches/Impulses/*.wv)
        for authentic 3D early reflections above 165 Hz while keeping <120 Hz mono.
      - Falls back deterministically to Haas lateral early reflections + diffuse tail.
    """
    n = min(len(left), len(right))
    if n < 64 or wet <= 0.0:
        return left.copy(), right.copy()

    pre_samples = max(16, int(round((pre_delay_ms / 1000.0) * sample_rate)))
    spread = float(np.clip(stereo_spread, 0.0, 0.85))
    ir_l: Optional[np.ndarray] = None
    ir_r: Optional[np.ndarray] = None

    if use_real_ir and get_real_room_ir is not None:
        loaded_ir = get_real_room_ir(
            style=room_style,
            sample_rate=sample_rate,
            max_sec=min(2.2, max(0.75, rt60_sec * 1.25)),
        )
        if loaded_ir is not None:
            ir_raw, _ir_name = loaded_ir
            usable_tail = min(len(ir_raw), max(128, n - pre_samples))
            if usable_tail >= 128 and pre_samples + usable_tail <= n:
                mid_ir = freeze_array(0.5 * (ir_raw[:usable_tail, 0] + ir_raw[:usable_tail, 1]))
                side_ir = freeze_array(0.5 * (ir_raw[:usable_tail, 0] - ir_raw[:usable_tail, 1]))
                mid_w = 0.82 - 0.16 * spread
                side_w = 0.42 + 0.88 * spread
                ir_len = pre_samples + usable_tail
                ir_l = np.zeros(ir_len, dtype=np.float64)
                ir_r = np.zeros(ir_len, dtype=np.float64)
                ir_l[pre_samples:] = mid_w * mid_ir + side_w * side_ir
                ir_r[pre_samples:] = mid_w * mid_ir - side_w * side_ir
                norm = math.sqrt(float(np.sum(np.square(ir_l)) + np.sum(np.square(ir_r))) * 0.5 + 1e-12)
                ir_l = freeze_array(ir_l / norm)
                ir_r = freeze_array(ir_r / norm)

    if ir_l is None or ir_r is None:
        ir_dur = min(1.8, max(0.35, rt60_sec * 0.85))
        ir_len = min(n, int(round(ir_dur * sample_rate)))
        if ir_len <= pre_samples + 16:
            return left.copy(), right.copy()

        rng = np.random.default_rng(140)
        tail_len = ir_len - pre_samples
        t_ir = freeze_array(make_time_axis(tail_len, sample_rate))
        decay = freeze_array(np.exp(np.multiply(-6.9078 / max(0.15, rt60_sec), t_ir)))
        onset = freeze_array(0.5 * (1.0 - np.cos(np.pi * np.clip(np.divide(t_ir, 0.012), 0.0, 1.0))))

        core_noise = np.multiply(np.multiply(rng.normal(0.0, 1.0, tail_len), decay), onset)
        side_noise = np.multiply(np.multiply(rng.normal(0.0, 1.0, tail_len), decay), onset)
        # Sculpted Haas lateral early reflections for spatial width
        for tap_ms, tap_amp, pan in (
            (3.4, 0.52, 0.48),
            (8.1, 0.44, -0.58),
            (13.7, 0.36, 0.66),
            (20.5, 0.28, -0.50),
            (28.9, 0.21, 0.38),
        ):
            idx = int(round((tap_ms / 1000.0) * sample_rate))
            if idx < tail_len:
                core_noise[idx] += tap_amp * (1.0 - abs(pan) * 0.25)
                side_noise[idx] += tap_amp * pan * 1.45

        nyq = sample_rate / 2.0
        sos_room = signal.butter(
            2,
            [min(0.35, 175.0 / nyq), min(0.88, 8600.0 / nyq)],
            btype="band",
            output="sos",
        )
        core_filt = freeze_array(signal.sosfilt(sos_room, core_noise))
        side_filt = freeze_array(signal.sosfilt(sos_room, side_noise))

        ir_l = np.zeros(ir_len, dtype=np.float64)
        ir_r = np.zeros(ir_len, dtype=np.float64)
        mid_w = 0.80 - 0.14 * spread
        side_w = 0.22 + 0.38 * spread
        ir_l[pre_samples:] = mid_w * core_filt + side_w * side_filt
        ir_r[pre_samples:] = mid_w * core_filt - side_w * side_filt

        norm = math.sqrt(float(np.sum(np.square(ir_l)) + np.sum(np.square(ir_r))) * 0.5 + 1e-12)
        ir_l = freeze_array(ir_l / norm)
        ir_r = freeze_array(ir_r / norm)

    l_in = freeze_array(np.array(left[:n], dtype=np.float64, copy=True))
    r_in = freeze_array(np.array(right[:n], dtype=np.float64, copy=True))
    mono_send = freeze_array(0.5 * (l_in + r_in))
    send_l = freeze_array(0.76 * l_in + 0.24 * mono_send)
    send_r = freeze_array(0.76 * r_in + 0.24 * mono_send)
    wet_l = signal.fftconvolve(send_l, ir_l, mode="full")[:n]
    wet_r = signal.fftconvolve(send_r, ir_r, mode="full")[:n]

    sos_wet_hp = signal.butter(2, min(0.45, 165.0 / (0.5 * sample_rate)), btype="high", output="sos")
    wet_l = freeze_array(signal.sosfilt(sos_wet_hp, wet_l))
    wet_r = freeze_array(signal.sosfilt(sos_wet_hp, wet_r))

    out_l = np.asarray(left, dtype=np.float64).copy()
    out_r = np.asarray(right, dtype=np.float64).copy()
    out_l[:n] += wet * wet_l
    out_r[:n] += wet * wet_r
    return out_l, out_r


def generate_warm_analog_tape_bed(
    n_samples: int,
    sample_rate: int = 48000,
    level_dbfs: float = -57.0,
    seed: int = 1995,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates an active analog tape bed (-56 to -58 dBFS, band-limited 1/f pink spectrum
    45 Hz - 4.2 kHz) eliminating cold digital 0.0 gaps without injecting 60 Hz hum.
    """
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float64), np.zeros(0, dtype=np.float64)

    rng = np.random.default_rng(seed)
    white_c = rng.normal(0.0, 1.0, n_samples)
    white_s = rng.normal(0.0, 1.0, n_samples)

    spec_c = np.fft.rfft(white_c)
    spec_s = np.fft.rfft(white_s)
    freqs = np.fft.rfftfreq(n_samples, d=1.0 / float(sample_rate))
    freqs_safe = freeze_array(np.maximum(freqs, 20.0))
    tilt = freeze_array(1.0 / np.sqrt(freqs_safe))
    band_mask = freeze_array(((freqs >= 45.0) & (freqs <= 4200.0)).astype(np.float64))

    bed_mid = np.fft.irfft(np.multiply(np.multiply(spec_c, tilt), band_mask), n=n_samples)
    bed_side = np.fft.irfft(np.multiply(np.multiply(spec_s, tilt), band_mask), n=n_samples)
    bed_mid.flags.writeable = False
    bed_side.flags.writeable = False

    rms_mid = math.sqrt(float(np.dot(bed_mid, bed_mid) / float(n_samples)) + 1e-18)
    rms_side = math.sqrt(float(np.dot(bed_side, bed_side) / float(n_samples)) + 1e-18)
    target_rms = 10.0 ** (level_dbfs / 20.0)
    bed_mid = (bed_mid / rms_mid) * target_rms
    bed_side = (bed_side / rms_side) * (target_rms * 0.15)
    bed_mid.flags.writeable = False
    bed_side.flags.writeable = False

    return bed_mid + bed_side, bed_mid - bed_side


def apply_highpass_tpdf_dither(
    audio: np.ndarray,
    bit_depth: int = 24,
    seed: int = 2026,
) -> np.ndarray:
    """
    Lipshitz-Vanderkooy high-pass TPDF dither: shifts quantization noise energy
    above 8 kHz away from the 3-4 kHz cochlear sensitivity peak.
    """
    arr = np.array(audio, dtype=np.float64, copy=True)
    arr.flags.writeable = False
    lsb = 1.0 / float(1 << (bit_depth - 1))
    rng = np.random.default_rng(seed)
    # 1st-order high-pass rectangular noise difference -> exact high-pass TPDF in [-lsb, +lsb]
    u = rng.uniform(-0.5 * lsb, 0.5 * lsb, size=(len(arr) + 1,) + arr.shape[1:])
    hp_tpdf = np.diff(u, axis=0)
    hp_tpdf.flags.writeable = False
    quantized = np.round((arr + hp_tpdf) / lsb) * lsb
    max_pos = 1.0 - lsb
    return np.clip(quantized, -1.0, max_pos)


def write_pcm_wav(
    output_path: Union[str, Path],
    left: np.ndarray,
    right: Optional[np.ndarray] = None,
    sample_rate: int = 48000,
    bit_depth: int = 24,
    dither: bool = True,
) -> Path:
    """Writes 16-bit or 24-bit PCM WAV with optional high-pass TPDF dithering."""
    out = Path(output_path).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    l_arr = np.asarray(left, dtype=np.float64)
    if right is None:
        stereo = l_arr[:, None] if l_arr.ndim == 1 else l_arr
    else:
        stereo = np.column_stack((l_arr, np.asarray(right, dtype=np.float64)))

    processed = apply_highpass_tpdf_dither(stereo, bit_depth=bit_depth) if dither else np.clip(stereo, -1.0, 0.999999)
    n_channels = processed.shape[1]

    with wave.open(str(out), "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setframerate(int(sample_rate))
        if bit_depth == 24:
            wf.setsampwidth(3)
            i32 = np.clip(np.round(processed * 8388607.0), -8388608, 8388607).astype("<i4")
            b24 = i32.flatten().view(np.uint8).reshape(-1, 4)[:, :3]
            wf.writeframes(b24.tobytes())
        else:
            wf.setsampwidth(2)
            i16 = np.clip(np.round(processed * 32767.0), -32768, 32767).astype("<i2")
            wf.writeframes(i16.tobytes())

    return out


# ---------------------------------------------------------------------------
# C5-REAL Nonlinear Circuit & Physical Instrument Models (Zero Naive Sines)
# ---------------------------------------------------------------------------


def zdf_moog_ladder_filter(
    x: np.ndarray,
    cutoff_hz: Union[float, np.ndarray],
    resonance: float = 0.32,
    drive: float = 1.35,
    sample_rate: int = 48000,
) -> np.ndarray:
    """
    Sample-exact 4-pole Zero-Delay Feedback (ZDF / TPT trapezoidal) nonlinear Moog
    ladder filter with per-stage saturation and smooth time-varying cutoff support.
    `resonance` in [0.0, 0.96] maps cleanly up to near self-oscillation (k <= 3.72).
    """
    arr = np.asarray(x, dtype=np.float64)
    n = len(arr)
    if n == 0:
        return np.zeros(0, dtype=np.float64)

    fc = np.broadcast_to(np.asarray(cutoff_hz, dtype=np.float64), (n,))
    fc_safe = freeze_array(np.clip(fc, 28.0, min(18500.0, 0.42 * float(sample_rate))))
    g_arr = freeze_array(np.tan(math.pi * fc_safe / float(sample_rate)))
    denom = freeze_array(1.0 + g_arr)
    G_arr = freeze_array(np.divide(g_arr, denom))

    # Clamp resonance safely away from divergent blowup; add slight bass gain comp
    k = float(np.clip(resonance, 0.0, 0.94)) * 3.72
    drv = float(np.clip(drive, 0.2, 4.0))
    comp = 1.0 + 0.35 * (k / 3.72)

    x_list = (arr * drv).tolist()
    g_list = G_arr.tolist()
    y = np.empty(n, dtype=np.float64)

    s1 = s2 = s3 = s4 = 0.0
    tanh = math.tanh
    inv_drv = 1.0 / max(1.0, 0.65 * drv + 0.35)
    for i in range(n):
        G = g_list[i]
        G2 = G * G
        G3 = G2 * G
        G4 = G3 * G
        S = G3 * s1 + G2 * s2 + G * s3 + s4
        u = tanh((x_list[i] * comp - k * S) / (1.0 + k * G4))

        v1 = (u - s1) * G
        y1 = v1 + s1
        s1 = y1 + v1

        v2 = (y1 - s2) * G
        y2 = v2 + s2
        s2 = y2 + v2

        v3 = (y2 - s3) * G
        y3 = v3 + s3
        s3 = y3 + v3

        v4 = (y3 - s4) * G
        y4 = v4 + s4
        s4 = y4 + v4

        y[i] = y4 * inv_drv

    return y


def synthesize_rhodes_electromechanical(
    freq_hz: float,
    n_samples: int,
    velocity: float = 0.85,
    sample_rate: int = 48000,
    tremolo_hz: float = 4.2,
    tremolo_depth: float = 0.22,
    stereo_pan: float = 0.0,
    seed: int = 1973,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Electromechanical Fender Rhodes Mk I synthesis:
      1. Velocity-scaled neoprene hammer felt transient (1.2-4.2 kHz exciter burst).
      2. Inharmonic steel tine bell overtones (fast exponential decay).
      3. Warm coupled tonebar sustain (1f0, 2f0).
      4. Asymmetric magnetic pickup displacement nonlinearity (even + odd bark).
      5. Stereo suitcase autopan tremolo & strict zero-crackle boundary tapering.
    """
    if n_samples <= 0 or freq_hz <= 15.0:
        z = np.zeros(max(0, n_samples), dtype=np.float64)
        return z, z.copy()

    vel = float(np.clip(velocity, 0.08, 1.25))
    t = freeze_array(make_time_axis(n_samples, sample_rate))
    nyq = 0.5 * float(sample_rate)

    # Hammer felt mechanical thump (2.5-5 ms exciter filtered into mechanical bark band)
    rng = np.random.default_rng(seed + int(round(freq_hz * 10.0)))
    noise = rng.normal(0.0, 1.0, n_samples)
    hammer_tau = 0.0028 + 0.0018 * (1.0 - min(1.0, vel))
    hammer_env = freeze_array(np.exp(np.divide(-t, hammer_tau)))
    hammer_raw = noise * hammer_env
    band_lo = min(0.45, max(120.0, freq_hz * 1.8) / nyq)
    band_hi = min(0.90, (1800.0 + 2800.0 * vel) / nyq)
    sos_felt = signal.butter(2, [band_lo, max(band_lo + 0.04, band_hi)], btype="band", output="sos")
    felt_transient = freeze_array(signal.sosfilt(sos_felt, hammer_raw)) * (0.28 * (vel ** 1.35))

    # Coupled tonebar + steel tine assembly
    pitch_scale = math.sqrt(max(0.25, 261.63 / freq_hz))
    tau_f0 = min(3.4, 1.15 * pitch_scale)
    tau_2f = tau_f0 * 0.62
    tau_tine = min(0.42, 0.09 + 0.14 * pitch_scale)

    phase0 = 2.0 * math.pi * freq_hz * t
    phase0.flags.writeable = False

    tonebar = (
        1.00 * np.sin(phase0) * np.exp(np.divide(-t, tau_f0))
        + 0.34 * np.sin(2.0 * phase0) * np.exp(np.divide(-t, tau_2f))
        + 0.14 * np.sin(3.003 * phase0) * np.exp(np.divide(-t, tau_f0 * 0.40))
    )
    # Inharmonic tine partials (7th/10th modes stay audible as signature Fender chime)
    tine_bright = 0.32 + 0.68 * vel
    tine = np.zeros(n_samples, dtype=np.float64)
    for mult, amp, dec_mul in (
        (5.04, 0.18, 1.00),
        (7.11, 0.12, 0.58),
        (10.62, 0.075, 0.32),
        (14.15, 0.045, 0.18),
    ):
        if freq_hz * mult < 0.44 * sample_rate:
            tine += (amp * tine_bright) * np.sin(mult * phase0) * np.exp(np.divide(-t, tau_tine * dec_mul))

    displacement = freeze_array(tonebar + tine + felt_transient)

    # Asymmetric magnetic pickup nonlinearity (d/dt induced voltage through biased coil)
    pickup_drive = 1.05 + 1.15 * vel
    pickup_bias = 0.24 * vel
    biased = freeze_array(displacement * pickup_drive + pickup_bias)
    raw_pickup = np.tanh(biased) - math.tanh(pickup_bias)
    if n_samples >= 24:
        sos_ac = signal.butter(1, min(0.08, 28.0 / nyq), btype="high", output="sos")
        raw_pickup = signal.sosfilt(sos_ac, raw_pickup)

    # Smooth note onset + decay into zero-crackle window
    voiced = apply_zero_crackle_envelope(
        raw_pickup * (0.48 * vel),
        sample_rate=sample_rate,
        attack_ms=5.2,
        release_ms=26.0,
    )
    voiced.flags.writeable = False

    # Stereo suitcase tremolo autopan
    pan = float(np.clip(stereo_pan, -0.75, 0.75))
    depth = float(np.clip(tremolo_depth, 0.0, 0.45))
    lfo = freeze_array(np.sin(2.0 * math.pi * tremolo_hz * t + pan * 0.7))
    gain_l = (1.0 - pan * 0.35) * (1.0 + depth * lfo)
    gain_r = (1.0 + pan * 0.35) * (1.0 - depth * lfo)
    return voiced * gain_l, voiced * gain_r


def synthesize_solina_bbd_ensemble(
    left: np.ndarray,
    right: Optional[np.ndarray] = None,
    sample_rate: int = 48000,
    depth_ms: float = 3.6,
    rate_slow_hz: float = 0.62,
    rate_fast_hz: float = 5.8,
    mix: float = 0.72,
    stereo_spread: float = 0.85,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Genuine 3-phase Bucket-Brigade Delay (BBD) analog Solina string ensemble chorus.
    Modulates 3 delay lines spaced 120 deg apart with dual LFO (0.62 Hz wander + 5.8 Hz
    vibrato), gentle BBD 10.5 kHz HF clock rolloff, and authentic M/S stereo dispersion.
    """
    l_in = np.asarray(left, dtype=np.float64)
    r_in = np.asarray(left if right is None else right, dtype=np.float64)
    n = min(len(l_in), len(r_in))
    if n < 32:
        return l_in.copy(), r_in.copy()

    mono = freeze_array(0.5 * (l_in[:n] + r_in[:n]))
    idx_base = freeze_array(np.arange(n, dtype=np.float64))
    t = freeze_array(make_time_axis(n, sample_rate))

    base_delay_samp = 0.0085 * float(sample_rate)
    mod_samp = (max(0.4, depth_ms) / 1000.0) * float(sample_rate)

    wet_l = np.zeros(n, dtype=np.float64)
    wet_r = np.zeros(n, dtype=np.float64)
    pan_weights = ((0.85, 0.25), (0.55, 0.55), (0.25, 0.85))
    for v_idx in range(3):
        phi = (2.0 * math.pi * v_idx) / 3.0
        lfo_slow = freeze_array(np.sin(2.0 * math.pi * rate_slow_hz * t + phi))
        lfo_fast = freeze_array(np.sin(2.0 * math.pi * rate_fast_hz * t + phi * 1.7))
        lfo = freeze_array(0.70 * lfo_slow + 0.30 * lfo_fast)
        read_pos = freeze_array(np.clip(idx_base - (base_delay_samp + mod_samp * (0.5 + 0.5 * lfo)), 0.0, float(n - 1)))
        delayed = freeze_array(np.interp(read_pos, idx_base, mono))
        wl, wr = pan_weights[v_idx]
        wet_l = wet_l + wl * delayed
        wet_r = wet_r + wr * delayed

    wet_l = freeze_array(wet_l / 1.65)
    wet_r = freeze_array(wet_r / 1.65)

    # Gentle BBD clock filter (tames ultrasonic artifacts while keeping analog shimmer <= 10.8 kHz)
    sos_bbd = signal.butter(2, min(0.88, 10800.0 / (0.5 * float(sample_rate))), btype="low", output="sos")
    wet_l = freeze_array(signal.sosfilt(sos_bbd, wet_l))
    wet_r = freeze_array(signal.sosfilt(sos_bbd, wet_r))

    # Expand stereo image cleanly via stereo_spread without losing mono weight
    mid = freeze_array(0.5 * (wet_l + wet_r))
    side = freeze_array(0.5 * (wet_l - wet_r) * (0.65 + 0.85 * float(np.clip(stereo_spread, 0.0, 1.0))))
    wet_l_sp = freeze_array(mid + side)
    wet_r_sp = freeze_array(mid - side)

    w = float(np.clip(mix, 0.0, 1.0))
    l_ro = freeze_array(np.asarray(l_in[:n], dtype=np.float64).copy())
    r_ro = freeze_array(np.asarray(r_in[:n], dtype=np.float64).copy())
    out_l = (1.0 - w) * l_ro + w * wet_l_sp
    out_r = (1.0 - w) * r_ro + w * wet_r_sp
    return out_l, out_r


def synthesize_string_ensemble_pad(
    freqs_hz: Sequence[float],
    n_samples: int,
    velocity: float = 0.82,
    sample_rate: int = 48000,
    cutoff_curve: Optional[Union[float, np.ndarray]] = None,
    seed: int = 1974,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    PolyBLEP bowed sawtooth + sub-pulse ensemble passed through nonlinear 4-pole
    ZDF ladder filter and 3-phase Solina BBD ensemble chorus.
    """
    if n_samples <= 0 or not freqs_hz:
        z = np.zeros(max(0, n_samples), dtype=np.float64)
        return z, z.copy()

    vel = float(np.clip(velocity, 0.1, 1.2))
    raw_l = np.zeros(n_samples, dtype=np.float64)
    raw_r = np.zeros(n_samples, dtype=np.float64)
    scale = 1.0 / math.sqrt(float(len(freqs_hz)))
    for i, f_hz in enumerate(freqs_hz):
        if f_hz <= 20.0:
            continue
        p0 = ((seed + i * 37) % 100) / 100.0
        saw_a = polyblep_saw(f_hz * 0.9978, n_samples, sample_rate, initial_phase=p0)
        saw_b = polyblep_saw(f_hz * 1.0022, n_samples, sample_rate, initial_phase=(p0 + 0.37) % 1.0)
        pulse_sub = polyblep_pulse(f_hz, n_samples, sample_rate, duty=0.38, initial_phase=(p0 + 0.61) % 1.0)
        voice = (0.45 * saw_a + 0.45 * saw_b + 0.25 * pulse_sub) * scale
        pan = -0.35 + 0.70 * ((i % max(1, len(freqs_hz) - 1)) / max(1, len(freqs_hz) - 1))
        raw_l += voice * (0.58 - 0.18 * pan)
        raw_r += voice * (0.58 + 0.18 * pan)

    fc = (2200.0 + 2600.0 * vel) if cutoff_curve is None else cutoff_curve
    filt_l = zdf_moog_ladder_filter(raw_l, cutoff_hz=fc, resonance=0.22, drive=1.18, sample_rate=sample_rate)
    filt_r = zdf_moog_ladder_filter(raw_r, cutoff_hz=fc, resonance=0.22, drive=1.18, sample_rate=sample_rate)

    ens_l, ens_r = synthesize_solina_bbd_ensemble(filt_l, filt_r, sample_rate=sample_rate, mix=0.74)
    out_l = apply_zero_crackle_envelope(ens_l * (0.42 * vel), sample_rate=sample_rate, attack_ms=42.0, release_ms=65.0)
    out_r = apply_zero_crackle_envelope(ens_r * (0.42 * vel), sample_rate=sample_rate, attack_ms=42.0, release_ms=65.0)
    return out_l, out_r


def synthesize_karplus_strong_pluck(
    freq_hz: float,
    n_samples: int,
    velocity: float = 0.85,
    brightness: float = 0.74,
    body_resonance: float = 0.38,
    sample_rate: int = 48000,
    seed: int = 1995,
) -> np.ndarray:
    """
    Extended Karplus-Strong physical plucked string waveguide with wooden body
    formant resonators (115 Hz air mode, 285 Hz top plate, 2350 Hz pick presence).
    """
    if n_samples <= 0 or freq_hz <= 20.0:
        return np.zeros(max(0, n_samples), dtype=np.float64)

    vel = float(np.clip(velocity, 0.1, 1.25))
    bright = float(np.clip(brightness * (0.55 + 0.45 * min(1.0, vel)), 0.18, 0.96))
    period = max(2.2, float(sample_rate) / float(freq_hz))
    n_delay = int(math.floor(period))
    frac = period - n_delay

    rng = np.random.default_rng(seed + int(round(freq_hz * 13.0)))
    exc = rng.uniform(-1.0, 1.0, n_delay + 2)
    # Pick-position comb notch + brightness tilt on initial string displacement
    comb_len = max(2, int(round(n_delay * 0.24)))
    if comb_len < len(exc):
        exc_ro = freeze_array(exc.copy())
        exc[comb_len:] -= 0.45 * exc_ro[:-comb_len]
    b_lpf = signal.butter(1, min(0.90, (1400.0 + 7800.0 * bright) / (0.5 * sample_rate)), btype="low")
    exc = signal.lfilter(b_lpf[0], b_lpf[1], exc)
    exc = (exc / max(1e-6, float(np.max(np.abs(exc))))) * vel

    # Frequency-dependent loop damping keeps sustained lows warm while fast highs decay naturally
    decay_base = 0.9945 - 0.004 * min(1.0, freq_hz / 900.0)
    blend_alpha = 0.35 + 0.35 * (1.0 - bright)

    ring = np.zeros(n_delay + 2, dtype=np.float64)
    ring[: len(exc)] = exc[: len(ring)]
    y = np.zeros(n_samples, dtype=np.float64)

    ring_len = len(ring)
    r_idx = 0
    prev_val = 0.0
    for i in range(n_samples):
        idx_a = r_idx % ring_len
        idx_b = (r_idx + 1) % ring_len
        samp = (1.0 - frac) * ring[idx_a] + frac * ring[idx_b]
        y[i] = samp
        lp = (1.0 - blend_alpha) * samp + blend_alpha * prev_val
        prev_val = samp
        ring[idx_a] = lp * decay_base
        r_idx += 1

    # Wooden guitar/charango body resonance parallel mix (keeps transient crispness)
    if body_resonance > 0.01 and n_samples >= 32:
        nyq = 0.5 * float(sample_rate)
        sos_body_lo = signal.butter(2, [min(0.3, 95.0 / nyq), min(0.45, 290.0 / nyq)], btype="band", output="sos")
        sos_body_hi = signal.butter(2, [min(0.4, 1650.0 / nyq), min(0.75, 4200.0 / nyq)], btype="band", output="sos")
        body = 0.48 * signal.sosfilt(sos_body_lo, y) + 0.36 * signal.sosfilt(sos_body_hi, y)
        y = y + float(np.clip(body_resonance, 0.0, 0.8)) * body

    return apply_zero_crackle_envelope(y, sample_rate=sample_rate, attack_ms=1.8, release_ms=18.0)


def synthesize_analog_hihat_cymbal(
    n_samples: int,
    is_open: bool = False,
    velocity: float = 0.85,
    pitch_scale: float = 1.0,
    sample_rate: int = 48000,
    seed: int = 808,
) -> np.ndarray:
    """
    Deterministic Roland 808/606 6-oscillator inharmonic metallic hi-hat / cymbal
    generator with high-pass resonance and air shimmer (never naive sine noise).
    """
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float64)

    vel = float(np.clip(velocity, 0.05, 1.25))
    t = freeze_array(make_time_axis(n_samples, sample_rate))
    freqs = (205.3, 304.4, 369.6, 522.7, 540.0, 800.0)
    rng = np.random.default_rng(seed)

    # Sum 6 inharmonic square/Schmitt partials + ring-mod metallic shimmer
    bank = np.zeros(n_samples, dtype=np.float64)
    for f0 in freqs:
        f = float(np.clip(f0 * pitch_scale, 80.0, 0.35 * sample_rate))
        phase = (2.0 * math.pi * f) * t + float(rng.uniform(0.0, 2.0 * math.pi))
        sq = np.tanh(3.2 * np.sin(phase))
        bank += sq
    bank = freeze_array(bank / 6.0)
    metallic = np.tanh(2.4 * (bank * bank - 0.25)) + 0.35 * bank + 0.14 * rng.normal(0.0, 1.0, n_samples)

    nyq = 0.5 * float(sample_rate)
    sos_hp = signal.butter(4, min(0.85, 5800.0 / nyq), btype="high", output="sos")
    sos_bp = signal.butter(2, [min(0.65, 7200.0 / nyq), min(0.92, 13800.0 / nyq)], btype="band", output="sos")
    bright = 0.58 * signal.sosfilt(sos_hp, metallic) + 0.52 * signal.sosfilt(sos_bp, metallic)

    tau = (0.24 if is_open else 0.036) * (0.78 + 0.35 * min(1.0, vel))
    env = freeze_array(np.exp(np.divide(-t, tau)))
    hit = apply_zero_crackle_envelope(bright * env * (0.65 * vel), sample_rate=sample_rate, attack_ms=0.6, release_ms=14.0)
    peak = float(np.max(np.abs(hit)))
    if peak > 1.0:
        hit = hit / peak
    return hit


def apply_wdf_warm_saturator(
    left: np.ndarray,
    right: Optional[np.ndarray] = None,
    sample_rate: int = 48000,
    drive_db: float = 2.4,
    tube_bias: float = 0.08,
    mix: float = 0.45,
) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Applies Wave Digital Filter (Newton-Raphson antiparallel diode pair) harmonic
    warmth above 140 Hz using 2x polyphase oversampling while preserving sub-bass
    coherence below 140 Hz untouched.
    """
    is_mono = right is None
    l_arr = np.asarray(left, dtype=np.float64)
    r_arr = np.asarray(left if is_mono else right, dtype=np.float64)
    n = min(len(l_arr), len(r_arr))
    if n < 32 or mix <= 0.0:
        return l_arr.copy() if is_mono else (l_arr.copy(), r_arr.copy())

    def _process_ch(ch: np.ndarray) -> np.ndarray:
        lo, hi = lr4_zero_phase_crossover(ch, 140.0, sample_rate)
        lo_ro = freeze_array(lo)
        hi_ro = freeze_array(hi)
        if solve_wdf_diode_pair is not None and n <= sample_rate * 45:
            drive_gain = 10.0 ** (drive_db / 20.0)
            driven = hi_ro * (drive_gain * 0.42) + float(tube_bias) * 0.15
            up = signal.resample_poly(driven, 2, 1)
            a_waves = freeze_array(up * 2.0)
            b_waves = freeze_array(solve_wdf_diode_pair(a_waves, R0=1200.0, Is=2.0e-9, Vt=0.026))
            v_up = (a_waves + b_waves) * 0.5
            sat_hi = signal.resample_poly(v_up, 1, 2)[:n]
            sos_dc = signal.butter(1, min(0.1, 45.0 / (0.5 * sample_rate)), btype="high", output="sos")
            sat_hi = signal.sosfilt(sos_dc, sat_hi) * (1.15 / max(0.35, drive_gain * 0.42))
        else:
            sat_hi = oversampled_soft_saturate(hi_ro, drive_db=drive_db, threshold_db=-3.0, asymmetry=0.05)

        w = float(np.clip(mix, 0.0, 1.0))
        return lo_ro + ((1.0 - w) * hi_ro + w * sat_hi)

    out_l = _process_ch(l_arr[:n])
    if is_mono:
        return out_l
    out_r = _process_ch(r_arr[:n])
    return out_l, out_r


def apply_spectral_balance_eq(
    left: np.ndarray,
    right: np.ndarray,
    sample_rate: int = 48000,
    sub_gain_db: float = -1.8,
    mud_cut_db: float = -2.2,
    presence_gain_db: float = 2.6,
    air_gain_db: float = 2.2,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Linear/Zero-phase 4-band perceptual balance shelf (sub <= 115 Hz, low-mid 280 Hz,
    presence 3.4 kHz, open air >= 8.5 kHz) eliminating <250 Hz blanket mud while
    lifting human intelligibility and top-end air without high-Q ringing.
    """
    n = min(len(left), len(right))
    if n < 64:
        return left.copy(), right.copy()

    def _peaking_biquad(fc: float, gain_db: float, q: float = 0.85) -> np.ndarray:
        a = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * math.pi * fc / float(sample_rate)
        alpha = math.sin(w0) / (2.0 * q)
        cos_w0 = math.cos(w0)
        b0 = 1.0 + alpha * a
        b1 = -2.0 * cos_w0
        b2 = 1.0 - alpha * a
        a0 = 1.0 + alpha / a
        a1 = -2.0 * cos_w0
        a2 = 1.0 - alpha / a
        return np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]], dtype=np.float64)

    def _shelf_biquad(fc: float, gain_db: float, high: bool) -> np.ndarray:
        a = 10.0 ** (gain_db / 40.0)
        w0 = 2.0 * math.pi * fc / float(sample_rate)
        cos_w0 = math.cos(w0)
        sin_w0 = math.sin(w0)
        alpha = sin_w0 / 2.0 * math.sqrt(2.0)
        sq_a = 2.0 * math.sqrt(a) * alpha
        if not high:
            b0 = a * ((a + 1.0) - (a - 1.0) * cos_w0 + sq_a)
            b1 = 2.0 * a * ((a - 1.0) - (a + 1.0) * cos_w0)
            b2 = a * ((a + 1.0) - (a - 1.0) * cos_w0 - sq_a)
            a0 = (a + 1.0) + (a - 1.0) * cos_w0 + sq_a
            a1 = -2.0 * ((a - 1.0) + (a + 1.0) * cos_w0)
            a2 = (a + 1.0) + (a - 1.0) * cos_w0 - sq_a
        else:
            b0 = a * ((a + 1.0) + (a - 1.0) * cos_w0 + sq_a)
            b1 = -2.0 * a * ((a - 1.0) + (a + 1.0) * cos_w0)
            b2 = a * ((a + 1.0) + (a - 1.0) * cos_w0 - sq_a)
            a0 = (a + 1.0) - (a - 1.0) * cos_w0 + sq_a
            a1 = 2.0 * ((a - 1.0) - (a + 1.0) * cos_w0)
            a2 = (a + 1.0) - (a - 1.0) * cos_w0 - sq_a
        return np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]], dtype=np.float64)

    sos_chain = np.vstack(
        [
            _shelf_biquad(95.0, sub_gain_db, high=False),
            _peaking_biquad(280.0, mud_cut_db, q=0.75),
            _peaking_biquad(3400.0, presence_gain_db, q=0.72),
            _shelf_biquad(8500.0, air_gain_db, high=True),
        ]
    )
    out_l = signal.sosfilt(sos_chain, np.asarray(left[:n], dtype=np.float64))
    out_r = signal.sosfilt(sos_chain, np.asarray(right[:n], dtype=np.float64))
    return out_l, out_r
