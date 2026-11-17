#!/usr/bin/env python3
"""
Dark Cyber-Flamenco Headless Audio Synthesizer (v16.0 C5-REAL 48 kHz)
=====================================================================
Synthesizes a 16-bar 48 kHz Stereo PCM audio preview combining:
1. Phase-locked 808/Maceo kick (exact cumulative phase integral int f(t)dt at 0 rad).
2. Band-limited PolyBLEP rolling D Phrygian Dominant bassline with zero-crackle
   raised-cosine envelopes, +6 ms pocket, and LR4 140 Hz coupled multiband sidechain.
3. Flamenco palmas/clap transient cluster with -11 ms pre-snap flam & ghost hits.
4. Micro-strummed D Phrygian Dominant chords carved at 185 Hz HPF + 375 Hz notch,
   routed into a non-commutative 2800 Hz Basic Channel dub tape echo + Living Pre-Loop Gap.
5. Coherent mono-compatible shared studio room + -57 dBFS 1/f warm analog tape floor
   + 4x oversampled soft saturation + Lipshitz-Vanderkooy high-pass TPDF dither.
"""

from pathlib import Path
import numpy as np
from scipy import signal

try:
    from scripts.bounces_paths import resolve_bounces_dir
    from scripts.c5_dsp_core import (
        apply_coherent_shared_room,
        apply_noncommutative_dub_echo,
        apply_spectral_balance_eq,
        apply_wdf_warm_saturator,
        apply_zero_crackle_envelope,
        build_coupled_multiband_sidechain,
        carve_polyphonic_mud,
        enforce_low_end_mono,
        generate_warm_analog_tape_bed,
        lr4_zero_phase_crossover,
        make_time_axis,
        oversampled_soft_saturate,
        polyblep_saw,
        synthesize_analog_hihat_cymbal,
        synthesize_karplus_strong_pluck,
        synthesize_phase_locked_kick,
        synthesize_rhodes_electromechanical,
        synthesize_string_ensemble_pad,
        write_pcm_wav,
        zdf_moog_ladder_filter,
    )
    from scripts.c5_real_assets_bridge import get_round_robin_drum_pool, shape_velocity_sample
except ImportError:
    from bounces_paths import resolve_bounces_dir
    from c5_dsp_core import (
        apply_coherent_shared_room,
        apply_noncommutative_dub_echo,
        apply_spectral_balance_eq,
        apply_wdf_warm_saturator,
        apply_zero_crackle_envelope,
        build_coupled_multiband_sidechain,
        carve_polyphonic_mud,
        enforce_low_end_mono,
        generate_warm_analog_tape_bed,
        lr4_zero_phase_crossover,
        make_time_axis,
        oversampled_soft_saturate,
        polyblep_saw,
        synthesize_analog_hihat_cymbal,
        synthesize_karplus_strong_pluck,
        synthesize_phase_locked_kick,
        synthesize_rhodes_electromechanical,
        synthesize_string_ensemble_pad,
        write_pcm_wav,
        zdf_moog_ladder_filter,
    )
    from c5_real_assets_bridge import get_round_robin_drum_pool, shape_velocity_sample

SAMPLE_RATE = 48000
BPM = 112.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4.0
SIXTEENTH_DUR = BEAT_DUR / 4.0
TOTAL_BARS = 16
TOTAL_DURATION = BAR_DUR * TOTAL_BARS
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)


def synthesize_flamenco_clap(sample_rate: int = SAMPLE_RATE) -> tuple[np.ndarray, np.ndarray]:
    """Synthesizes stereo-coherent multi-tap flamenco palmas via modal palm resonances."""
    dur = int(sample_rate * 0.24)
    rng = np.random.default_rng(112240)
    t = make_time_axis(dur, sample_rate)

    # Three micro-staggered handbursts (0 ms, 8.5 ms, 17 ms) + exponential tail
    env = (
        0.55 * np.exp(-np.maximum(0.0, t) * 95.0)
        + 0.65 * np.exp(-np.maximum(0.0, t - 0.0085) * 85.0) * (t >= 0.0085)
        + 0.90 * np.exp(-np.maximum(0.0, t - 0.017) * 26.0) * (t >= 0.017)
    )
    noise_l = rng.standard_normal(dur)
    noise_r = 0.88 * noise_l + 0.12 * rng.standard_normal(dur)

    # Helmholtz cupped-palm formants (980 Hz + 1940 Hz) + >=5.4 kHz transient air sheen
    b_p1, a_p1 = signal.iirpeak(980.0, Q=6.2, fs=sample_rate)
    b_p2, a_p2 = signal.iirpeak(1940.0, Q=6.5, fs=sample_rate)
    nyq = 0.5 * sample_rate
    sos_air = signal.butter(3, min(0.85, 5400.0 / nyq), btype="high", output="sos")

    modal_body = (
        0.26 * np.sin(2.0 * np.pi * 218.0 * t) * np.exp(-t * 36.0)
        + 0.18 * np.sin(2.0 * np.pi * 980.0 * t + 0.3) * np.exp(-t * 44.0)
        + 0.14 * np.sin(2.0 * np.pi * 1560.0 * t + 0.7) * np.exp(-t * 56.0)
    )

    def _shape_palm(noise_vec: np.ndarray) -> np.ndarray:
        burst = noise_vec * env
        formant = (
            0.72 * signal.lfilter(b_p1, a_p1, burst)
            + 0.55 * signal.lfilter(b_p2, a_p2, burst)
            + 0.24 * signal.sosfilt(sos_air, burst)
        )
        return apply_zero_crackle_envelope(
            formant + modal_body,
            sample_rate=sample_rate,
            attack_ms=1.5,
            release_ms=12.0,
        )

    clap_l = _shape_palm(noise_l)
    clap_r = _shape_palm(noise_r)
    peak = max(float(np.max(np.abs(clap_l))), float(np.max(np.abs(clap_r))), 1e-6)
    scale = 0.72 / peak
    return clap_l * scale, clap_r * scale


_synthesize_flamenco_clap = synthesize_flamenco_clap


def _mix_stereo_hit(
    buf_l: np.ndarray,
    buf_r: np.ndarray,
    hit: np.ndarray,
    start_idx: int,
    gain: float = 1.0,
    pan: float = 0.0,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    """Safely mixes a mono or stereo hit into stereo accumulators with zero-crackle fades."""
    if start_idx >= len(buf_l) or hit.size == 0:
        return
    if hit.ndim == 1:
        hl = hit
        hr = hit
    else:
        hl = hit[:, 0]
        hr = hit[:, 1] if hit.shape[1] > 1 else hit[:, 0]
    if start_idx < 0:
        skip = -start_idx
        hl = hl[skip:]
        hr = hr[skip:]
        start_idx = 0
    dur = min(len(hl), len(buf_l) - start_idx)
    if dur <= 8:
        return
    fade_len = min(int(0.0025 * sample_rate), dur // 4)
    sl = apply_zero_crackle_envelope(
        np.array(hl[:dur], dtype=np.float64, copy=True),
        sample_rate=sample_rate,
        attack_ms=1.0,
        release_ms=max(2.0, (fade_len / sample_rate) * 1000.0),
    )
    sr_ch = apply_zero_crackle_envelope(
        np.array(hr[:dur], dtype=np.float64, copy=True),
        sample_rate=sample_rate,
        attack_ms=1.0,
        release_ms=max(2.0, (fade_len / sample_rate) * 1000.0),
    )
    pan_clamped = float(np.clip(pan, -0.92, 0.92))
    g_l = gain * (1.0 - max(0.0, pan_clamped) * 0.88)
    g_r = gain * (1.0 - max(0.0, -pan_clamped) * 0.88)
    buf_l[start_idx : start_idx + dur] += sl * g_l
    buf_r[start_idx : start_idx + dur] += sr_ch * g_r


def render_dark_cyber_flamenco_wav(output_path: Path, bit_depth: int = 16) -> Path:
    """Renders the 16-bar 48 kHz Dark Cyber-Flamenco preview WAV."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(1122026)

    kick_bus = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    bass_bus = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    perc_l = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    perc_r = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    hat_l = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    hat_r = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    chord_l = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    chord_r = np.zeros(TOTAL_SAMPLES, dtype=np.float64)

    nyq = 0.5 * SAMPLE_RATE

    # Load real studio ModeAudio round-robin drums (graceful physical fallback if absent)
    kick_pool = get_round_robin_drum_pool("kick", count=6, sample_rate=SAMPLE_RATE, max_sec=0.45)
    clap_pool = get_round_robin_drum_pool("clap", count=6, sample_rate=SAMPLE_RATE, max_sec=0.55)
    chat_pool = get_round_robin_drum_pool("closed_hat", count=8, sample_rate=SAMPLE_RATE, max_sec=0.35)
    ohat_pool = get_round_robin_drum_pool("open_hat", count=6, sample_rate=SAMPLE_RATE, max_sec=0.80)
    shaker_pool = get_round_robin_drum_pool("shaker", count=6, sample_rate=SAMPLE_RATE, max_sec=0.35)
    rim_pool = get_round_robin_drum_pool("rim", count=6, sample_rate=SAMPLE_RATE, max_sec=0.35)
    cymbal_pool = get_round_robin_drum_pool("cymbal", count=4, sample_rate=SAMPLE_RATE, max_sec=1.60)
    sos_kick_top = signal.butter(2, 95.0 / nyq, btype="high", output="sos")

    # 1. PHASE-LOCKED SUB KICK + ROUND-ROBIN ACOUSTIC TRANSIENT + A/A'/B/TURNAROUND PICKUPS
    kick_wave = synthesize_phase_locked_kick(
        sample_rate=SAMPLE_RATE,
        duration_sec=0.40,
        root_hz=48.0,
        punch_hz=158.0,
        click_hz=2950.0,
        drive_db=2.2,
    )
    kick_len = len(kick_wave)
    kick_triggers: list[int] = []
    for bar in range(TOTAL_BARS):
        if bar in (0, 8):
            # Atmospheric Flamenco intro (Bar 0) & full-bar dub breakdown release (Bar 8)
            beat_range: tuple[int, ...] = ()
        elif bar == 1:
            beat_range = (0, 2)  # Half-time pulse build
        elif bar == 9:
            beat_range = (2, 3)  # Half-bar re-entry tension
        elif bar in (3, 7, 11):
            beat_range = (0, 1, 2)  # Phrase turnaround breath before pickup
        elif bar == 15:
            beat_range = (0, 1)  # Outro turnaround release
        else:
            beat_range = (0, 1, 2, 3)
        for beat in beat_range:
            idx = int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE)
            if idx < TOTAL_SAMPLES:
                kick_triggers.append(idx)
                vel = 0.80 if beat in (0, 2) else 0.74
                end = min(TOTAL_SAMPLES, idx + kick_len)
                kick_bus[idx:end] += kick_wave[: end - idx] * (0.64 * vel)
                if kick_pool:
                    layer = shape_velocity_sample(
                        kick_pool[(bar * 4 + beat) % len(kick_pool)],
                        velocity=0.88 if beat == 0 else 0.76,
                        sample_rate=SAMPLE_RATE,
                    )
                    top_mono = 0.5 * (layer[:, 0] + layer[:, 1])
                    top_mono = signal.sosfilt(sos_kick_top, top_mono)
                    k_end = min(TOTAL_SAMPLES, idx + len(top_mono))
                    kick_bus[idx:k_end] += top_mono[: k_end - idx] * (0.34 * vel)

        if bar in (1, 3, 7, 11, 14):
            pickup_idx = int((bar * BAR_DUR + 14 * SIXTEENTH_DUR) * SAMPLE_RATE)
            if pickup_idx < TOTAL_SAMPLES:
                kick_triggers.append(pickup_idx)
                end_p = min(TOTAL_SAMPLES, pickup_idx + kick_len)
                kick_bus[pickup_idx:end_p] += kick_wave[: end_p - pickup_idx] * 0.46

    # 2. ZDF MOOG LADDER ROLLING BASSLINE (D Phrygian A->A'->B->Turnaround, +6ms pocket)
    bass_roots = [
        36.71, 43.65, 38.89, 46.25,  # D1 -> F1 -> Eb1 -> F#1 (intro + build)
        36.71, 49.00, 38.89, 55.00,  # D1 -> G1 -> Eb1 -> A1 (A groove)
        43.65, 51.91, 46.25, 58.27,  # F1 -> Ab1 -> F#1 -> Bb1 (B lift)
        49.00, 38.89, 55.00, 36.71,  # G1 -> Eb1 -> A1 -> D1 (Turnaround)
    ]
    pocket_samples = int(0.006 * SAMPLE_RATE)
    note_samples = int(SIXTEENTH_DUR * 0.78 * SAMPLE_RATE)
    bass_harm_bus = np.zeros(TOTAL_SAMPLES, dtype=np.float64)

    for bar in range(TOTAL_BARS):
        base_f = bass_roots[bar]
        phrase = bar % 4  # 0=A, 1=A', 2=B, 3=Turnaround
        sub_scale = 0.0 if bar in (0, 8) else (0.58 if bar == 1 else (0.72 if bar == 9 else (1.06 if 10 <= bar <= 14 else 0.92)))
        section_scale = 0.36 if bar == 0 else (0.56 if bar == 8 else (0.68 if bar in (1, 9) else (1.08 if 10 <= bar <= 14 else 0.96)))
        for step in range(16):
            if bar == 15 and step >= 10:
                continue  # Pre-loop tension breath
            if bar == 0 and step < 6:
                continue
            # Negative space & motif variation across 4-bar phrase
            if step == 0 or (phrase == 0 and step in (4, 8, 12)) or (phrase == 1 and step in (8, 12)):
                continue
            if bar in (8, 9) and step % 2 == 0:
                continue  # Offbeat dub arp bass during breakdown before full re-entry
            if phrase == 3 and step in (11, 12, 13):
                continue

            swing = int(((0.008 if step % 2 == 1 else 0.0) + float(rng.uniform(-0.002, 0.002))) * SAMPLE_RATE)
            start = int((bar * BAR_DUR + step * SIXTEENTH_DUR) * SAMPLE_RATE) + pocket_samples + swing
            if start >= TOTAL_SAMPLES:
                continue
            dur = min(note_samples, TOTAL_SAMPLES - start)
            if dur < int(0.020 * SAMPLE_RATE):
                continue

            is_octave = (step % 2 == 1)
            freq_mult = 2.0 if is_octave else 1.0
            if phrase == 2 and step in (10, 14):
                freq_mult = 1.5  # Phrygian 5th bounce in B-section
            elif phrase == 3 and step == 14:
                freq_mult = 1.06  # Tension turnaround semitone rub

            freq = base_f * freq_mult
            t_n = make_time_axis(dur, SAMPLE_RATE)
            sub_sine = np.sin(2.0 * np.pi * freq * t_n)
            saw = polyblep_saw(freq * 1.001, dur, sample_rate=SAMPLE_RATE)
            decay = np.exp(-t_n * (12.0 if is_octave else 8.2))
            accent = 1.16 if step in (2, 6, 10, 14) else 0.84
            vel = 0.24 * accent * section_scale * (1.0 + 0.08 * (bar / 15.0))
            sub_part = apply_zero_crackle_envelope(
                sub_sine * decay * (0.24 * accent * sub_scale * 0.44),
                sample_rate=SAMPLE_RATE,
                attack_ms=5.5,
                release_ms=11.0,
            )
            harm_part = apply_zero_crackle_envelope(
                saw * decay * (vel * 0.62),
                sample_rate=SAMPLE_RATE,
                attack_ms=4.5,
                release_ms=10.0,
            )
            bass_bus[start : start + dur] += sub_part
            bass_harm_bus[start : start + dur] += harm_part

    # Macro 16-bar filter curve through 4-pole ZDF Moog ladder (HPF>115Hz so sub doesn't double)
    t_all = make_time_axis(TOTAL_SAMPLES, SAMPLE_RATE)
    macro_cutoff = 520.0 + 1750.0 * (0.5 - 0.5 * np.cos(2.0 * np.pi * t_all / max(1.0, TOTAL_DURATION)))
    macro_cutoff = macro_cutoff + 360.0 * np.sin(2.0 * np.pi * t_all / (4.0 * BAR_DUR))
    macro_cutoff = np.clip(macro_cutoff, 480.0, 2600.0)
    bass_harm_filt = zdf_moog_ladder_filter(
        bass_harm_bus,
        cutoff_hz=macro_cutoff,
        resonance=0.30,
        drive=1.35,
        sample_rate=SAMPLE_RATE,
    )
    sos_bh_hp = signal.butter(2, 115.0 / nyq, btype="high", output="sos")
    bass_harm_clean = signal.sosfilt(sos_bh_hp, bass_harm_filt)
    bass_full = bass_bus + bass_harm_clean

    # Coupled Multiband Sidechain at 140 Hz (LR4 zero-phase)
    sc_sub, sc_mid = build_coupled_multiband_sidechain(
        TOTAL_SAMPLES, kick_triggers, sample_rate=SAMPLE_RATE, tau_body=0.20, sub_depth=0.92, high_depth=0.22
    )
    bass_low, bass_high = lr4_zero_phase_crossover(bass_full, 140.0, sample_rate=SAMPLE_RATE)
    bass_sculpted = bass_low * sc_sub + bass_high * sc_mid

    # 3. FLAMENCO CLAPS + MODEAUDIO ROUND-ROBIN HATS/SHAKERS/RIM + OPEN-CLOSED CHOKE + SWELL
    clap_l, clap_r = _synthesize_flamenco_clap(SAMPLE_RATE)
    flam_offset = int(0.011 * SAMPLE_RATE)

    for bar in range(TOTAL_BARS):
        phrase = bar % 4
        clap_beats: tuple[float, ...] = () if bar in (0, 8) else ((3.0,) if bar in (1, 9) else ((1.0, 2.5, 3.0, 3.5) if bar in (7, 14) else (1.0, 3.0)))
        for beat in clap_beats:
            if bar == 15 and beat >= 3.0:
                continue
            idx = max(0, int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE) - flam_offset)
            _mix_stereo_hit(perc_l, perc_r, np.column_stack((clap_l, clap_r)), idx, gain=0.34, pan=0.04)
            if clap_pool:
                c_hit = shape_velocity_sample(
                    clap_pool[int(bar * 4 + round(beat * 2)) % len(clap_pool)],
                    velocity=0.88 if beat == 3 else 0.78,
                    sample_rate=SAMPLE_RATE,
                )
                _mix_stereo_hit(perc_l, perc_r, c_hit, idx + flam_offset, gain=0.28, pan=-0.06)

        # Bulerías / organic micro-percussion rim & shaker accents (varies across A/A'/B/Turnaround)
        rim_steps = (7, 15) if phrase in (0, 2) else (3, 7, 13, 15)
        for r_i, g_step in enumerate(rim_steps):
            if bar == 15 and g_step >= 10:
                continue
            g_idx = int((bar * BAR_DUR + g_step * SIXTEENTH_DUR) * SAMPLE_RATE)
            vel = 0.45 if g_step in (3, 13) else 0.72
            if rim_pool:
                r_hit = shape_velocity_sample(rim_pool[(bar + r_i) % len(rim_pool)], velocity=vel, sample_rate=SAMPLE_RATE)
                _mix_stereo_hit(perc_l, perc_r, r_hit, g_idx, gain=0.19 * vel, pan=-0.34 if r_i % 2 == 0 else 0.36)
            else:
                _mix_stereo_hit(perc_l, perc_r, np.column_stack((clap_l, clap_r)), g_idx, gain=0.11 * vel, pan=0.18)

        # Hats + Choke group + Shakers on 16th grid with swing
        for step in range(16):
            if bar == 15 and step >= 10:
                continue
            if bar == 0 and step < 8:
                continue  # Organic entrance: hats breathe in after beat 2 of Bar 1
            swing_s = int(0.009 * SAMPLE_RATE) if step % 2 == 1 else 0
            h_idx = int((bar * BAR_DUR + step * SIXTEENTH_DUR) * SAMPLE_RATE) + swing_s
            if h_idx >= TOTAL_SAMPLES:
                continue

            if bar >= 2 and bar not in (8, 9) and step in (2, 10) and phrase in (1, 2, 3):
                # Open hi-hat offbeat
                h_vel = 0.78 if step == 10 else 0.68
                oh = (
                    shape_velocity_sample(ohat_pool[(bar + step) % len(ohat_pool)], velocity=h_vel, sample_rate=SAMPLE_RATE)
                    if ohat_pool
                    else synthesize_analog_hihat_cymbal(int(0.32 * SAMPLE_RATE), is_open=True, velocity=h_vel, sample_rate=SAMPLE_RATE, seed=900 + bar * 16 + step)
                )
                _mix_stereo_hit(hat_l, hat_r, oh, h_idx, gain=0.17, pan=-0.56)
            elif step % 2 == 0 or (phrase >= 1 and step in (7, 15)):
                # Closed hi-hat triggers choke fade on open hat tail
                choke_len = min(int(0.006 * SAMPLE_RATE), TOTAL_SAMPLES - h_idx)
                if choke_len > 8:
                    hat_l[h_idx : h_idx + choke_len] *= np.linspace(1.0, 0.0, choke_len)
                    hat_r[h_idx : h_idx + choke_len] *= np.linspace(1.0, 0.0, choke_len)
                    hat_l[h_idx + choke_len : min(TOTAL_SAMPLES, h_idx + int(0.18 * SAMPLE_RATE))] *= 0.08
                    hat_r[h_idx + choke_len : min(TOTAL_SAMPLES, h_idx + int(0.18 * SAMPLE_RATE))] *= 0.08

                h_vel = 0.86 if step % 4 == 2 else 0.56
                ch = (
                    shape_velocity_sample(chat_pool[(bar * 16 + step) % len(chat_pool)], velocity=h_vel, sample_rate=SAMPLE_RATE)
                    if chat_pool
                    else synthesize_analog_hihat_cymbal(int(0.08 * SAMPLE_RATE), is_open=False, velocity=h_vel, sample_rate=SAMPLE_RATE, seed=800 + bar * 16 + step)
                )
                _mix_stereo_hit(hat_l, hat_r, ch, h_idx, gain=0.19, pan=0.52)

            if shaker_pool and bar >= 4 and step % 4 in (1, 3):
                sh = shape_velocity_sample(
                    shaker_pool[(bar + step) % len(shaker_pool)],
                    velocity=0.62 if step % 4 == 1 else 0.78,
                    sample_rate=SAMPLE_RATE,
                )
                _mix_stereo_hit(perc_l, perc_r, sh, h_idx, gain=0.14, pan=-0.68 if step % 4 == 1 else 0.68)

    # Reverse crash turnaround swells into Bar 8 and end of Bar 15
    if cymbal_pool:
        sw = cymbal_pool[0]
        sw_rev = sw[::-1].copy()
        rev_len = len(sw_rev)
        ramp = np.linspace(0.0, 1.0, rev_len) ** 2.2
        sw_rev[:, 0] *= ramp
        sw_rev[:, 1] *= ramp
        for bar_anchor in (8, 15):
            a_idx = max(0, int(bar_anchor * BAR_DUR * SAMPLE_RATE) - rev_len)
            _mix_stereo_hit(perc_l, perc_r, sw_rev, a_idx, gain=0.22, pan=0.0)

    perc_l += hat_l
    perc_r += hat_r

    # 4. KARPLUS-STRONG FLAMENCO GUITAR + RHODES + SOLINA BBD AIR PAD (A/A'/B/Turnaround)
    chord_freqs = [
        [196.00, 233.08, 293.66, 349.23, 440.00],  # Gm9
        [174.61, 220.00, 261.63, 329.63, 392.00],  # Fmaj7
        [155.56, 196.00, 233.08, 293.66, 369.99],  # Ebmaj7(#11)
        [146.83, 185.00, 220.00, 261.63, 311.13],  # D7(b9)
    ]
    strum_step = int(0.015 * SAMPLE_RATE)

    for bar in range(TOTAL_BARS):
        phrase = bar % 4
        notes = list(chord_freqs[bar // 4])
        if phrase == 2:
            # Voice-led upper inversion in B-bar
            notes = [notes[0], notes[1] * 2.0, notes[2], notes[3], notes[4]]
        bar_start = int(bar * BAR_DUR * SAMPLE_RATE)

        if phrase == 0:
            stabs = ((0, 1.45, 0.24), (8, 0.85, 0.18))
        elif phrase == 1:
            stabs = ((0, 1.35, 0.23), (6, 0.72, 0.19), (12, 0.80, 0.20))
        elif phrase == 2:
            stabs = ((0, 1.40, 0.25), (5, 0.65, 0.19), (10, 0.75, 0.21))
        else:
            stabs = ((0, 1.25, 0.24), (6, 0.70, 0.18))  # Spacious turnaround

        for stab_i, (stab_step, stab_dur_s, stab_vel) in enumerate(stabs):
            if bar == 15 and stab_step >= 8:
                continue
            stab_base = bar_start + int(stab_step * SIXTEENTH_DUR * SAMPLE_RATE)
            iter_notes = list(reversed(notes)) if (phrase == 3 and stab_i > 0) else notes
            for n_i, freq in enumerate(iter_notes):
                n_start = stab_base + n_i * strum_step
                if n_start >= TOTAL_SAMPLES:
                    continue
                dur = min(int(stab_dur_s * SAMPLE_RATE), TOTAL_SAMPLES - n_start)
                if dur < int(0.030 * SAMPLE_RATE):
                    continue

                pan = (n_i / max(1, len(iter_notes) - 1)) * 1.48 - 0.74
                voice_weight = 1.15 if n_i == len(iter_notes) - 1 else (0.94 if n_i > 0 else 0.78)
                ks_voice = synthesize_karplus_strong_pluck(
                    freq_hz=freq,
                    n_samples=dur,
                    velocity=0.86 if n_i >= 3 else 0.74,
                    brightness=0.78 + 0.06 * (phrase == 2),
                    body_resonance=0.42,
                    sample_rate=SAMPLE_RATE,
                    seed=1995 + bar * 32 + stab_i * 8 + n_i,
                )
                rh_l, rh_r = synthesize_rhodes_electromechanical(
                    freq_hz=freq,
                    n_samples=dur,
                    velocity=0.80,
                    sample_rate=SAMPLE_RATE,
                    tremolo_hz=3.8,
                    tremolo_depth=0.20,
                    stereo_pan=pan * 0.88,
                    seed=1973 + bar * 32 + n_i,
                )
                v_l = apply_zero_crackle_envelope(
                    (ks_voice * 0.58 * (1.0 - max(0.0, pan) * 0.85) + rh_l * 0.48) * stab_vel * voice_weight,
                    sample_rate=SAMPLE_RATE,
                    attack_ms=5.0,
                    release_ms=18.0,
                )
                v_r = apply_zero_crackle_envelope(
                    (ks_voice * 0.58 * (1.0 - max(0.0, -pan) * 0.85) + rh_r * 0.48) * stab_vel * voice_weight,
                    sample_rate=SAMPLE_RATE,
                    attack_ms=5.0,
                    release_ms=18.0,
                )
                chord_l[n_start : n_start + dur] += v_l
                chord_r[n_start : n_start + dur] += v_r

        # Solina BBD string pad breath on Bars 4..15 (swells prominently during breakdown & climax)
        if bar >= 4 and bar != 15:
            pad_dur = min(int(BAR_DUR * 0.92 * SAMPLE_RATE), TOTAL_SAMPLES - bar_start)
            if pad_dur > int(0.25 * SAMPLE_RATE):
                pad_freqs = [notes[1], notes[2], notes[4] * (2.0 if (phrase == 2 or bar in (8, 9)) else 1.0)]
                cutoff_env = np.linspace(1800.0, 4600.0, pad_dur) if (phrase < 2 or bar == 8) else np.linspace(4100.0, 2100.0, pad_dur)
                sp_l, sp_r = synthesize_string_ensemble_pad(
                    pad_freqs,
                    pad_dur,
                    velocity=0.78 if bar in (8, 9, 12, 13, 14) else 0.70,
                    sample_rate=SAMPLE_RATE,
                    cutoff_curve=cutoff_env,
                    seed=1974 + bar,
                )
                pad_gain = 0.44 if bar in (8, 9) else (0.34 if 10 <= bar <= 14 else 0.24)
                sp_l = apply_zero_crackle_envelope(sp_l * pad_gain, sample_rate=SAMPLE_RATE, attack_ms=45.0, release_ms=65.0)
                sp_r = apply_zero_crackle_envelope(sp_r * pad_gain, sample_rate=SAMPLE_RATE, attack_ms=45.0, release_ms=65.0)
                chord_l[bar_start : bar_start + pad_dur] += sp_l
                chord_r[bar_start : bar_start + pad_dur] += sp_r

    chord_l, chord_r = carve_polyphonic_mud(chord_l, chord_r, sample_rate=SAMPLE_RATE)
    chord_l, chord_r = apply_noncommutative_dub_echo(
        chord_l,
        chord_r,
        delay_sec=SIXTEENTH_DUR * 3.0,
        feedback=0.38,
        lpf_hz=2800.0,
        wet=0.22,
        sample_rate=SAMPLE_RATE,
    )
    chord_l *= sc_mid
    chord_r *= sc_mid

    # 5. COHERENT REAL CONVOLUTION ROOM + WDF DIODE SATURATOR + SPECTRAL BALANCE EQ
    bus_l = kick_bus + bass_sculpted + perc_l + chord_l
    bus_r = kick_bus + bass_sculpted + perc_r + chord_r

    bus_l, bus_r = apply_coherent_shared_room(
        bus_l,
        bus_r,
        sample_rate=SAMPLE_RATE,
        rt60_sec=0.62,
        pre_delay_ms=16.0,
        wet=0.16,
        room_style="spring_dub",
        stereo_spread=0.52,
        use_real_ir=True,
    )
    bus_l, bus_r = apply_wdf_warm_saturator(
        bus_l, bus_r, sample_rate=SAMPLE_RATE, drive_db=2.2, tube_bias=0.07, mix=0.42
    )
    bus_l, bus_r = apply_spectral_balance_eq(
        bus_l,
        bus_r,
        sample_rate=SAMPLE_RATE,
        sub_gain_db=-2.2,
        mud_cut_db=-2.2,
        presence_gain_db=3.0,
        air_gain_db=2.8,
    )
    tape_l, tape_r = generate_warm_analog_tape_bed(
        TOTAL_SAMPLES, sample_rate=SAMPLE_RATE, level_dbfs=-57.0, seed=112
    )
    bus_l = oversampled_soft_saturate(bus_l + tape_l, drive_db=0.9, threshold_db=-2.2, asymmetry=0.01)
    bus_r = oversampled_soft_saturate(bus_r + tape_r, drive_db=0.9, threshold_db=-2.2, asymmetry=0.01)
    bus_l, bus_r = enforce_low_end_mono(
        bus_l, bus_r, cutoff_hz=120.0, sample_rate=SAMPLE_RATE
    )

    # Normalize cleanly to -0.8 dBFS preserving full dynamic Crest Factor (>= 10.5 dB)
    peak = max(float(np.max(np.abs(bus_l))), float(np.max(np.abs(bus_r))), 1e-9)
    target_peak = 10.0 ** (-0.8 / 20.0)
    bus_l *= target_peak / peak
    bus_r *= target_peak / peak

    # Smooth Living Exit fade over last 25 ms so loop boundary has zero discontinuity
    bus_l = apply_zero_crackle_envelope(bus_l, sample_rate=SAMPLE_RATE, attack_ms=5.0, release_ms=25.0)
    bus_r = apply_zero_crackle_envelope(bus_r, sample_rate=SAMPLE_RATE, attack_ms=5.0, release_ms=25.0)

    return write_pcm_wav(
        out_path, bus_l, bus_r, sample_rate=SAMPLE_RATE, bit_depth=bit_depth, dither=True
    )


if __name__ == "__main__":
    out_wav = resolve_bounces_dir() / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    render_dark_cyber_flamenco_wav(out_wav)
    print(f"Rendered 48kHz Headless Audio Preview: {out_wav} ({out_wav.stat().st_size / 1024:.1f} KB)")
