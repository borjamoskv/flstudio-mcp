#!/usr/bin/env python3
"""
Antigravity Multitrack Stem Pack Synthesis Engine (v16.0 C5-REAL 48 kHz)
========================================================================
Synthesizes 5 discrete 48 kHz broadcast WAV stems + orchestration manifest:
  01_Kick_4onTheFloor.wav   (Phase-locked integral kick, Pultec sub, 195 Hz mud cut)
  02_Snare_Clap_Flamenco.wav (Band-passed palmas/clap with -11 ms flam & ghost hits)
  03_Rolling_Cyber_Bass.wav  (PolyBLEP + sub fundamental, zero-crackle RC envelope, coupled SC)
  04_Flamenco_Arp_Chords.wav (Strummed Phrygian chords, 185 Hz HPF + 375 Hz notch + 2800 Hz dub)
  05_Master_Mix.wav          (Coherent room glue, -57 dBFS tape floor, Rubin-verified master)
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Union

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
        check_zero_crackle_derivatives,
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
    from scripts.mastering_reverse_engine_fl import (
        compute_rubin_metrics,
        compute_true_peak_dbtp,
    )
    from scripts.render_synthwave_flamenco_audio_preview import (
        _mix_stereo_hit,
        synthesize_flamenco_clap,
    )
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
        check_zero_crackle_derivatives,
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
    from mastering_reverse_engine_fl import compute_rubin_metrics, compute_true_peak_dbtp
    from render_synthwave_flamenco_audio_preview import _mix_stereo_hit, synthesize_flamenco_clap

SAMPLE_RATE = 48000
BPM = 112.0
BEAT_DUR = 60.0 / BPM
BAR_DUR = BEAT_DUR * 4.0
SIXTEENTH_DUR = BEAT_DUR / 4.0
TOTAL_BARS = 16
TOTAL_DURATION = BAR_DUR * TOTAL_BARS
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)


def write_stereo_wav(
    file_path: Path,
    left_buf: Union[List[float], np.ndarray],
    right_buf: Union[List[float], np.ndarray],
    normalize: bool = True,
    target_dbfs: float = -1.0,
) -> Path:
    """Exports a 48 kHz 16-bit TPDF-dithered stereo WAV stem."""
    l_arr = np.asarray(left_buf, dtype=np.float64).copy()
    r_arr = np.asarray(right_buf, dtype=np.float64).copy()
    if normalize:
        peak = max(float(np.max(np.abs(l_arr))), float(np.max(np.abs(r_arr))), 1e-9)
        target = 10.0 ** (target_dbfs / 20.0)
        if peak > 1e-6:
            gain = min(target / peak, 3.0)
            l_arr *= gain
            r_arr *= gain
        tp_dbtp = compute_true_peak_dbtp(np.column_stack((l_arr, r_arr)))
        if tp_dbtp > target_dbfs:
            tp_scale = 10.0 ** ((target_dbfs - tp_dbtp) / 20.0)
            l_arr *= tp_scale
            r_arr *= tp_scale
    return write_pcm_wav(file_path, l_arr, r_arr, sample_rate=SAMPLE_RATE, bit_depth=16, dither=True)


def render_multitrack_stems(output_dir: Path) -> Dict[str, Any]:
    """Synthesizes all 5 discrete 48 kHz multitrack stems + Rubin-audited Master Mix."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    rng = np.random.default_rng(48162026)

    kick_l = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    kick_r = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    snare_l = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    snare_r = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    hat_l = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    hat_r = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    bass_l = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    bass_r = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    chords_l = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    chords_r = np.zeros(TOTAL_SAMPLES, dtype=np.float64)

    nyq = 0.5 * SAMPLE_RATE
    kick_pool = get_round_robin_drum_pool("kick", count=6, sample_rate=SAMPLE_RATE, max_sec=0.45)
    clap_pool = get_round_robin_drum_pool("clap", count=6, sample_rate=SAMPLE_RATE, max_sec=0.55)
    chat_pool = get_round_robin_drum_pool("closed_hat", count=8, sample_rate=SAMPLE_RATE, max_sec=0.35)
    ohat_pool = get_round_robin_drum_pool("open_hat", count=6, sample_rate=SAMPLE_RATE, max_sec=0.80)
    shaker_pool = get_round_robin_drum_pool("shaker", count=6, sample_rate=SAMPLE_RATE, max_sec=0.35)
    cymbal_pool = get_round_robin_drum_pool("cymbal", count=4, sample_rate=SAMPLE_RATE, max_sec=1.60)
    sos_kick_top = signal.butter(2, 95.0 / nyq, btype="high", output="sos")

    # 1. KICK STEM (Phase-locked integral sub + ModeAudio round-robin punch)
    kick_single = synthesize_phase_locked_kick(
        sample_rate=SAMPLE_RATE,
        duration_sec=0.40,
        root_hz=48.0,
        punch_hz=156.0,
        click_hz=2950.0,
        drive_db=2.2,
    )
    kick_len = len(kick_single)
    kick_triggers: List[int] = []
    for bar in range(TOTAL_BARS):
        if bar in (0, 8):
            beat_range: tuple[int, ...] = ()
        elif bar == 1:
            beat_range = (0, 2)
        elif bar == 9:
            beat_range = (2, 3)
        elif bar in (3, 7, 11):
            beat_range = (0, 1, 2)
        elif bar == 15:
            beat_range = (0, 1)
        else:
            beat_range = (0, 1, 2, 3)
        for beat in beat_range:
            idx = int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE)
            kick_triggers.append(idx)
            vel = 0.88 if beat in (0, 2) else 0.80
            end = min(TOTAL_SAMPLES, idx + kick_len)
            kick_l[idx:end] += kick_single[: end - idx] * (0.72 * vel)
            kick_r[idx:end] += kick_single[: end - idx] * (0.72 * vel)
            if kick_pool:
                layer = shape_velocity_sample(
                    kick_pool[(bar * 4 + beat) % len(kick_pool)],
                    velocity=0.85 if beat == 0 else 0.75,
                    sample_rate=SAMPLE_RATE,
                )
                top = signal.sosfilt(sos_kick_top, 0.5 * (layer[:, 0] + layer[:, 1]))
                k_end = min(TOTAL_SAMPLES, idx + len(top))
                kick_l[idx:k_end] += top[: k_end - idx] * (0.34 * vel)
                kick_r[idx:k_end] += top[: k_end - idx] * (0.34 * vel)
        if bar in (3, 7, 11, 14):
            p_idx = int((bar * BAR_DUR + 14 * SIXTEENTH_DUR) * SAMPLE_RATE)
            if p_idx < TOTAL_SAMPLES:
                kick_triggers.append(p_idx)
                p_end = min(TOTAL_SAMPLES, p_idx + kick_len)
                kick_l[p_idx:p_end] += kick_single[: p_end - p_idx] * 0.48
                kick_r[p_idx:p_end] += kick_single[: p_end - p_idx] * 0.48

    # 2. SNARE / CLAP / PERC STEM (Helmholtz palmas + ModeAudio claps + choked hats + turnaround swell)
    clap_wave_l, clap_wave_r = synthesize_flamenco_clap(SAMPLE_RATE)
    flam_samples = int(0.011 * SAMPLE_RATE)
    for bar in range(TOTAL_BARS):
        phrase = bar % 4
        clap_beats: tuple[float, ...] = () if bar in (0, 8) else ((3.0,) if bar in (1, 9) else ((1.0, 2.5, 3.0, 3.5) if bar in (7, 14) else (1.0, 3.0)))
        for beat in clap_beats:
            if bar == 15 and beat >= 3.0:
                continue
            idx = max(0, int((bar * BAR_DUR + beat * BEAT_DUR) * SAMPLE_RATE) - flam_samples)
            _mix_stereo_hit(
                snare_l, snare_r, np.column_stack((clap_wave_l, clap_wave_r)), idx, gain=0.56, pan=0.04, sample_rate=SAMPLE_RATE
            )
            if clap_pool:
                c_hit = shape_velocity_sample(
                    clap_pool[int(bar * 4 + round(beat * 2)) % len(clap_pool)],
                    velocity=0.88 if beat == 3 else 0.78,
                    sample_rate=SAMPLE_RATE,
                )
                _mix_stereo_hit(snare_l, snare_r, c_hit, idx + flam_samples, gain=0.40, pan=-0.06, sample_rate=SAMPLE_RATE)

        for step in range(16):
            if (bar == 15 and step >= 10) or (bar == 0 and step < 8):
                continue
            swing_s = int(0.0085 * SAMPLE_RATE) if step % 2 == 1 else 0
            h_idx = int((bar * BAR_DUR + step * SIXTEENTH_DUR) * SAMPLE_RATE) + swing_s
            if h_idx >= TOTAL_SAMPLES:
                continue
            if bar >= 2 and bar not in (8, 9) and step in (2, 10) and phrase in (1, 2, 3):
                h_vel = 0.78 if step == 10 else 0.68
                oh = (
                    shape_velocity_sample(ohat_pool[(bar + step) % len(ohat_pool)], velocity=h_vel, sample_rate=SAMPLE_RATE)
                    if ohat_pool
                    else synthesize_analog_hihat_cymbal(int(0.32 * SAMPLE_RATE), is_open=True, velocity=h_vel, sample_rate=SAMPLE_RATE, seed=910 + bar * 16 + step)
                )
                _mix_stereo_hit(hat_l, hat_r, oh, h_idx, gain=0.22, pan=-0.56, sample_rate=SAMPLE_RATE)
            elif step % 2 == 0 or (phrase >= 1 and step in (7, 15)):
                choke_len = min(int(0.006 * SAMPLE_RATE), TOTAL_SAMPLES - h_idx)
                if choke_len > 8:
                    hat_l[h_idx : h_idx + choke_len] *= np.linspace(1.0, 0.0, choke_len)
                    hat_r[h_idx : h_idx + choke_len] *= np.linspace(1.0, 0.0, choke_len)
                    hat_l[h_idx + choke_len : min(TOTAL_SAMPLES, h_idx + int(0.18 * SAMPLE_RATE))] *= 0.08
                    hat_r[h_idx + choke_len : min(TOTAL_SAMPLES, h_idx + int(0.18 * SAMPLE_RATE))] *= 0.08
                h_vel = 0.85 if step % 4 == 2 else 0.56
                ch = (
                    shape_velocity_sample(chat_pool[(bar * 16 + step) % len(chat_pool)], velocity=h_vel, sample_rate=SAMPLE_RATE)
                    if chat_pool
                    else synthesize_analog_hihat_cymbal(int(0.08 * SAMPLE_RATE), is_open=False, velocity=h_vel, sample_rate=SAMPLE_RATE, seed=810 + bar * 16 + step)
                )
                _mix_stereo_hit(hat_l, hat_r, ch, h_idx, gain=0.24, pan=0.52, sample_rate=SAMPLE_RATE)

            if shaker_pool and bar >= 4 and step % 4 in (1, 3):
                sh = shape_velocity_sample(
                    shaker_pool[(bar + step) % len(shaker_pool)],
                    velocity=0.64 if step % 4 == 1 else 0.80,
                    sample_rate=SAMPLE_RATE,
                )
                _mix_stereo_hit(snare_l, snare_r, sh, h_idx, gain=0.16, pan=-0.68 if step % 4 == 1 else 0.68, sample_rate=SAMPLE_RATE)

    if cymbal_pool:
        sw_rev = cymbal_pool[0][::-1].copy()
        rev_len = len(sw_rev)
        ramp = np.linspace(0.0, 1.0, rev_len) ** 2.2
        sw_rev[:, 0] *= ramp
        sw_rev[:, 1] *= ramp
        for bar_anchor in (8, 15):
            a_idx = max(0, int(bar_anchor * BAR_DUR * SAMPLE_RATE) - rev_len)
            _mix_stereo_hit(snare_l, snare_r, sw_rev, a_idx, gain=0.24, pan=0.0, sample_rate=SAMPLE_RATE)

    snare_l += hat_l
    snare_r += hat_r

    # 3. ROLLING CYBER SUB-BASS STEM (ZDF Moog Ladder + A/A'/B/Turnaround + Clean YIN Pitch)
    bass_roots = [
        73.42, 87.31, 77.78, 92.50,   # D2 -> F2 -> Eb2 -> F#2
        73.42, 98.00, 77.78, 110.00,  # D2 -> G2 -> Eb2 -> A2
        87.31, 103.83, 92.50, 116.54, # F2 -> Ab2 -> F#2 -> Bb2
        98.00, 77.78, 110.00, 73.42,  # G2 -> Eb2 -> A2 -> D2
    ]
    note_samples = int(SIXTEENTH_DUR * 0.78 * SAMPLE_RATE)
    pocket_samples = int(0.006 * SAMPLE_RATE)
    bass_mono = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    bass_harm = np.zeros(TOTAL_SAMPLES, dtype=np.float64)

    for bar in range(TOTAL_BARS):
        base_f = bass_roots[bar]
        phrase = bar % 4
        sub_scale = 0.0 if bar in (0, 8) else (0.58 if bar == 1 else (0.72 if bar == 9 else (1.06 if 10 <= bar <= 14 else 0.92)))
        section_scale = 0.36 if bar == 0 else (0.56 if bar == 8 else (0.68 if bar in (1, 9) else (1.08 if 10 <= bar <= 14 else 0.96)))
        for step in range(16):
            if bar == 15 and step >= 12:
                continue
            if bar == 0 and step < 6:
                continue
            if (phrase == 0 and step in (4, 8, 12)) or (phrase == 1 and step == 8) or (phrase == 3 and step in (12, 13)):
                continue
            if bar in (8, 9) and step % 2 == 0:
                continue
            swing = int(((0.007 if step % 2 == 1 else 0.0) + float(rng.uniform(-0.0015, 0.0015))) * SAMPLE_RATE)
            idx = int((bar * BAR_DUR + step * SIXTEENTH_DUR) * SAMPLE_RATE) + pocket_samples + swing
            if idx >= TOTAL_SAMPLES:
                continue
            dur = min(note_samples, TOTAL_SAMPLES - idx)
            if dur < int(0.025 * SAMPLE_RATE):
                continue
            is_oct = (step % 2 == 1)
            freq = base_f * (1.5 if step == 14 and phrase == 2 else (2.0 if is_oct else 1.0))
            t_n = make_time_axis(dur, SAMPLE_RATE)
            env = np.exp(-t_n * (8.2 if is_oct else 6.6))
            accent = 1.15 if step in (2, 6, 10, 14) else 0.85
            sub_p = apply_zero_crackle_envelope(
                np.sin(2.0 * np.pi * freq * t_n) * env * 0.24 * accent * sub_scale,
                sample_rate=SAMPLE_RATE,
                attack_ms=6.5,
                release_ms=14.0,
            )
            harm_p = apply_zero_crackle_envelope(
                polyblep_saw(freq, dur, sample_rate=SAMPLE_RATE) * env * 0.30 * accent * section_scale,
                sample_rate=SAMPLE_RATE,
                attack_ms=5.0,
                release_ms=12.0,
            )
            bass_mono[idx : idx + dur] += sub_p
            bass_harm[idx : idx + dur] += harm_p

    t_all = make_time_axis(TOTAL_SAMPLES, SAMPLE_RATE)
    cutoff_sweep = np.clip(
        500.0
        + 1650.0 * (0.5 - 0.5 * np.cos(2.0 * np.pi * t_all / max(1.0, TOTAL_DURATION)))
        + 320.0 * np.sin(2.0 * np.pi * t_all / (4.0 * BAR_DUR)),
        480.0,
        2450.0,
    )
    bass_harm_zdf = zdf_moog_ladder_filter(
        bass_harm, cutoff_hz=cutoff_sweep, resonance=0.30, drive=1.30, sample_rate=SAMPLE_RATE
    )
    sos_bh_hp = signal.butter(2, 115.0 / nyq, btype="high", output="sos")
    bass_full = bass_mono + signal.sosfilt(sos_bh_hp, bass_harm_zdf)

    sc_sub, sc_mid = build_coupled_multiband_sidechain(
        TOTAL_SAMPLES, kick_triggers, sample_rate=SAMPLE_RATE, tau_body=0.20, sub_depth=0.90, high_depth=0.22
    )
    b_low, b_high = lr4_zero_phase_crossover(bass_full, 140.0, sample_rate=SAMPLE_RATE)
    bass_sculpted = b_low * sc_sub + b_high * sc_mid
    bass_sculpted = apply_wdf_warm_saturator(
        bass_sculpted, sample_rate=SAMPLE_RATE, drive_db=1.8, tube_bias=0.06, mix=0.35
    )
    bass_l[:] = bass_sculpted
    bass_r[:] = bass_sculpted

    # 4. FLAMENCO ARPEGGIATED CHORDS STEM (Karplus-Strong + Rhodes + Solina BBD + 2800 Hz Dub)
    chord_freqs = [
        [196.00, 233.08, 293.66, 349.23, 440.00],  # Gm9
        [174.61, 220.00, 261.63, 329.63, 392.00],  # Fmaj7
        [155.56, 196.00, 233.08, 293.66, 369.99],  # Ebmaj7(#11)
        [146.83, 185.00, 220.00, 261.63, 311.13],  # D7(b9)
    ]
    for bar in range(TOTAL_BARS):
        phrase = bar % 4
        notes = list(chord_freqs[bar // 4])
        if phrase == 2:
            notes = [notes[0], notes[1] * 2.0, notes[2], notes[3], notes[4]]
        elif phrase == 3:
            notes = list(reversed(notes))
        bar_start = int(bar * BAR_DUR * SAMPLE_RATE)

        for n_i, freq in enumerate(notes):
            if phrase == 0 and n_i == 2:
                continue  # Negative space
            n_start = bar_start + int(n_i * (BAR_DUR / len(notes)) * SAMPLE_RATE)
            if n_start >= TOTAL_SAMPLES:
                continue
            dur = min(int(SAMPLE_RATE * 1.55), TOTAL_SAMPLES - n_start)
            if dur < int(0.030 * SAMPLE_RATE):
                continue
            pan = (n_i / max(1, len(notes) - 1)) * 1.48 - 0.74
            ks_v = synthesize_karplus_strong_pluck(
                freq_hz=freq,
                n_samples=dur,
                velocity=0.84,
                brightness=0.78 + 0.06 * (phrase == 2),
                body_resonance=0.40,
                sample_rate=SAMPLE_RATE,
                seed=2026 + bar * 16 + n_i,
            )
            rh_l, rh_r = synthesize_rhodes_electromechanical(
                freq_hz=freq,
                n_samples=dur,
                velocity=0.78,
                sample_rate=SAMPLE_RATE,
                tremolo_hz=3.6,
                tremolo_depth=0.22,
                stereo_pan=pan * 0.88,
                seed=2126 + bar * 16 + n_i,
            )
            vl = apply_zero_crackle_envelope(
                (ks_v * 0.56 * (1.0 - max(0.0, pan) * 0.85) + rh_l * 0.48) * 0.36,
                sample_rate=SAMPLE_RATE,
                attack_ms=6.0,
                release_ms=20.0,
            )
            vr = apply_zero_crackle_envelope(
                (ks_v * 0.56 * (1.0 - max(0.0, -pan) * 0.85) + rh_r * 0.48) * 0.36,
                sample_rate=SAMPLE_RATE,
                attack_ms=6.0,
                release_ms=20.0,
            )
            chords_l[n_start : n_start + dur] += vl
            chords_r[n_start : n_start + dur] += vr

        if bar >= 4 and bar != 15:
            pad_dur = min(int(BAR_DUR * 0.90 * SAMPLE_RATE), TOTAL_SAMPLES - bar_start)
            if pad_dur > int(0.25 * SAMPLE_RATE):
                sp_l, sp_r = synthesize_string_ensemble_pad(
                    [notes[1], notes[2], notes[-1] * (2.0 if bar in (8, 9) or phrase == 2 else 1.0)],
                    pad_dur,
                    velocity=0.78 if bar in (8, 9, 12, 13, 14) else 0.70,
                    sample_rate=SAMPLE_RATE,
                    cutoff_curve=np.linspace(1900.0, 4400.0, pad_dur),
                    seed=2226 + bar,
                )
                pad_gain = 0.42 if bar in (8, 9) else (0.32 if 10 <= bar <= 14 else 0.22)
                chords_l[bar_start : bar_start + pad_dur] += apply_zero_crackle_envelope(
                    sp_l * pad_gain, sample_rate=SAMPLE_RATE, attack_ms=40.0, release_ms=60.0
                )
                chords_r[bar_start : bar_start + pad_dur] += apply_zero_crackle_envelope(
                    sp_r * pad_gain, sample_rate=SAMPLE_RATE, attack_ms=40.0, release_ms=60.0
                )

    chords_l, chords_r = carve_polyphonic_mud(chords_l, chords_r, sample_rate=SAMPLE_RATE)
    chords_l, chords_r = apply_noncommutative_dub_echo(
        chords_l,
        chords_r,
        delay_sec=SIXTEENTH_DUR * 3.0,
        feedback=0.35,
        lpf_hz=2800.0,
        wet=0.20,
        sample_rate=SAMPLE_RATE,
    )
    chords_l *= sc_mid
    chords_r *= sc_mid

    # 5. MASTER MIXDOWN (Balanced headroom, real studio IR room, WDF warm saturation, Spectral Balance EQ)
    master_l = kick_l * 0.72 + snare_l * 0.62 + bass_l * 0.56 + chords_l * 0.60
    master_r = kick_r * 0.72 + snare_r * 0.62 + bass_r * 0.56 + chords_r * 0.60

    master_l, master_r = apply_coherent_shared_room(
        master_l,
        master_r,
        sample_rate=SAMPLE_RATE,
        rt60_sec=0.58,
        pre_delay_ms=16.0,
        wet=0.16,
        room_style="chamber_warm",
        stereo_spread=0.62,
        use_real_ir=True,
    )
    master_l, master_r = apply_wdf_warm_saturator(
        master_l, master_r, sample_rate=SAMPLE_RATE, drive_db=2.0, tube_bias=0.06, mix=0.40
    )
    master_l, master_r = apply_spectral_balance_eq(
        master_l,
        master_r,
        sample_rate=SAMPLE_RATE,
        sub_gain_db=-2.0,
        mud_cut_db=-2.2,
        presence_gain_db=2.8,
        air_gain_db=2.6,
    )
    tape_l, tape_r = generate_warm_analog_tape_bed(
        TOTAL_SAMPLES, sample_rate=SAMPLE_RATE, level_dbfs=-57.0, seed=4816
    )
    master_l = oversampled_soft_saturate(master_l + tape_l, drive_db=0.9, threshold_db=-2.2, asymmetry=0.01)
    master_r = oversampled_soft_saturate(master_r + tape_r, drive_db=0.9, threshold_db=-2.2, asymmetry=0.01)
    master_l, master_r = enforce_low_end_mono(
        master_l, master_r, cutoff_hz=120.0, sample_rate=SAMPLE_RATE
    )

    master_peak = max(float(np.max(np.abs(master_l))), float(np.max(np.abs(master_r))), 1e-9)
    master_gain = (10.0 ** (-0.8 / 20.0)) / master_peak
    master_l = apply_zero_crackle_envelope(
        master_l * master_gain, sample_rate=SAMPLE_RATE, attack_ms=5.0, release_ms=25.0
    )
    master_r = apply_zero_crackle_envelope(
        master_r * master_gain, sample_rate=SAMPLE_RATE, attack_ms=5.0, release_ms=25.0
    )

    rubin_master = compute_rubin_metrics(master_l, master_r, sample_rate=SAMPLE_RATE)
    bass_crackle = check_zero_crackle_derivatives(bass_l)

    stems = [
        ("01_Kick_4onTheFloor.wav", kick_l, kick_r, False),
        ("02_Snare_Clap_Flamenco.wav", snare_l, snare_r, True),
        ("03_Rolling_Cyber_Bass.wav", bass_l, bass_r, True),
        ("04_Flamenco_Arp_Chords.wav", chords_l, chords_r, True),
        ("05_Master_Mix.wav", master_l, master_r, False),
    ]

    manifest_stems = []
    for fname, l_buf, r_buf, norm_flag in stems:
        path = out_dir / fname
        write_stereo_wav(path, l_buf, r_buf, normalize=norm_flag, target_dbfs=-1.0)
        manifest_stems.append({
            "name": fname,
            "path": str(path),
            "size_kb": round(path.stat().st_size / 1024.0, 1),
            "duration_sec": round(TOTAL_DURATION, 2),
        })

    manifest = {
        "pack_name": "Dark Cyber-Flamenco Multitrack Stems (16 Bars)",
        "version": "16.0-C5-REAL-48KHZ",
        "bpm": BPM,
        "key": "D Phrygian Dominant",
        "time_signature": "4/4",
        "bars": TOTAL_BARS,
        "sample_rate_hz": SAMPLE_RATE,
        "bit_depth": 16,
        "channels": 2,
        "total_stems": len(manifest_stems),
        "stems": manifest_stems,
        "rubin_master_audit": rubin_master,
        "bass_zero_crackle_audit": bass_crackle,
        "elapsed_render_sec": round(time.time() - t_start, 2),
    }

    manifest_path = out_dir / "stems_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    out = resolve_bounces_dir() / "Stems" / "Dark_Cyber_Flamenco_Stems_16Bars"
    res = render_multitrack_stems(out)
    print(f"Exported 48kHz Multitrack Stems ({res['total_stems']} stems) in {res['elapsed_render_sec']}s -> {out}")
