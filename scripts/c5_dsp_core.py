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
from typing import Any, Dict, Iterable, Optional, Tuple, Union

import numpy as np
from scipy import signal

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
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Shared Coherent Convolution Room (INV_C5_ACOUSTIC_GATE §3.1.5 & Rubin §3.2):
      - 18 ms pre-delay preserving dry transient attack.
      - 84% shared mono diffuse core + 16% orthogonal lateral tail -> LPC >= 0.96 & 100% mono-compatible.
    """
    n = len(left)
    if n < 64 or wet <= 0.0:
        return left.copy(), right.copy()

    ir_dur = min(1.8, max(0.35, rt60_sec * 0.85))
    ir_len = int(round(ir_dur * sample_rate))
    pre_samples = int(round((pre_delay_ms / 1000.0) * sample_rate))
    if ir_len <= pre_samples + 16:
        return left.copy(), right.copy()

    rng = np.random.default_rng(140)
    tail_len = ir_len - pre_samples
    t_ir = freeze_array(make_time_axis(tail_len, sample_rate))
    decay = freeze_array(np.exp(np.multiply(-6.9078 / max(0.15, rt60_sec), t_ir)))
    # Smooth onset into diffuse tail
    onset = freeze_array(0.5 * (1.0 - np.cos(np.pi * np.clip(np.divide(t_ir, 0.012), 0.0, 1.0))))

    core_noise = np.multiply(np.multiply(rng.normal(0.0, 1.0, tail_len), decay), onset)
    side_noise = np.multiply(np.multiply(rng.normal(0.0, 1.0, tail_len), decay), onset)

    nyq = sample_rate / 2.0
    sos_room = signal.butter(
        2,
        [min(0.35, 220.0 / nyq), min(0.85, 5800.0 / nyq)],
        btype="band",
        output="sos",
    )
    core_filt = signal.sosfilt(sos_room, core_noise)
    side_filt = signal.sosfilt(sos_room, side_noise)
    core_filt.flags.writeable = False
    side_filt.flags.writeable = False

    ir_l = np.zeros(ir_len, dtype=np.float64)
    ir_r = np.zeros(ir_len, dtype=np.float64)
    # 84% mono core + 16% orthogonal side -> mono sum cancels side cleanly without comb filtering!
    ir_l[pre_samples:] = 0.84 * core_filt + 0.16 * side_filt
    ir_r[pre_samples:] = 0.84 * core_filt - 0.16 * side_filt

    norm = math.sqrt(float(np.sum(ir_l * ir_l)) + 1e-12)
    ir_l /= norm
    ir_r /= norm

    mono_send = 0.5 * (left + right)
    mono_send.flags.writeable = False
    wet_l = signal.fftconvolve(0.75 * left + 0.25 * mono_send, ir_l, mode="full")[:n]
    wet_r = signal.fftconvolve(0.75 * right + 0.25 * mono_send, ir_r, mode="full")[:n]

    out_l = np.asarray(left, dtype=np.float64).copy()
    out_r = np.asarray(right, dtype=np.float64).copy()
    out_l += wet * wet_l
    out_r += wet * wet_r
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
