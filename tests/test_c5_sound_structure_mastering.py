"""
C5-REAL Regression & Acoustic Verification Suite:
1. Anti-aliased 48 kHz DSP primitives (PolyBLEP, phase-locked kick, LR4 unity crossover, zero-crackle fades)
2. Arrangement, sequencing, False Drop Bar 60 vacuum, Living Exits, and zero-drift absolute-tick MIDI
3. 5-stage Reverse Mastering Club C5 & Rubin Pre-Human Acoustic Gate verification
"""

import sys
from pathlib import Path

import mido
import numpy as np
from scipy import signal

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

import mcp_server  # noqa: E402
from scripts import (  # noqa: E402
    air_moon_safari_engine,
    arrangement_structure_engine,
    c5_dsp_core,
    fl_playlist_arranger,
    fl_sidechain_ducking_engine,
    flstudio_full_arrangement_generator,
    flstudio_infinite_harmonic_loop,
    maceo_plex_kick_synthesizer,
    midi_cc_automation_generator,
)


def test_polyblep_suppresses_aliasing_above_12khz():
    sr = 48000
    n = 48000
    freq = 1760.0
    t = np.arange(n, dtype=np.float64) / sr
    naive_saw = 2.0 * ((t * freq) % 1.0) - 1.0
    blep_saw = c5_dsp_core.polyblep_saw(freq, n, sample_rate=sr)

    freqs, p_naive = signal.welch(naive_saw, fs=sr, nperseg=4096)
    _, p_blep = signal.welch(blep_saw, fs=sr, nperseg=4096)

    # Measure non-harmonic aliasing noise floor between 16 kHz and 23.5 kHz
    # (excluding legitimate integer harmonics k * 1760 Hz of the 1760 Hz sawtooth)
    hi_mask = (freqs >= 16000.0) & (freqs <= 23500.0)
    for k in range(9, 15):
        hi_mask &= np.abs(freqs - k * freq) > 250.0
    naive_hi_db = 10.0 * np.log10(float(np.mean(p_naive[hi_mask])) + 1e-18)
    blep_hi_db = 10.0 * np.log10(float(np.mean(p_blep[hi_mask])) + 1e-18)
    assert blep_hi_db < naive_hi_db - 12.0


def test_lr4_zero_phase_crossover_perfect_reconstruction_and_kick_bounds():
    sr = 48000
    t = np.arange(sr, dtype=np.float64) / sr
    composite = 0.6 * np.sin(2.0 * np.pi * 55.0 * t) + 0.4 * np.sin(2.0 * np.pi * 880.0 * t)
    low, high = c5_dsp_core.lr4_zero_phase_crossover(composite, 140.0, sr)
    err = float(np.max(np.abs(composite - (low + high))))
    assert err < 1e-10

    kick = c5_dsp_core.synthesize_phase_locked_kick(sample_rate=sr, duration_sec=0.40, root_hz=49.0)
    assert abs(float(kick[0])) < 1e-4
    assert abs(float(kick[-1])) < 1e-4


def test_zero_crackle_envelope_on_sub_bass_note():
    sr = 48000
    n = int(0.5 * sr)
    t = np.arange(n, dtype=np.float64) / sr
    sub = 0.55 * np.sin(2.0 * np.pi * 49.0 * t)
    shaped = c5_dsp_core.apply_zero_crackle_envelope(sub, sample_rate=sr, attack_ms=6.0, release_ms=12.0)
    audit = c5_dsp_core.check_zero_crackle_derivatives(shaped, max_d1=0.015, max_d2=0.005)
    assert audit["zero_crackle_passed"] is True
    assert abs(float(shaped[0])) < 1e-9
    assert abs(float(shaped[-1])) < 1e-9


def test_maceo_kick_pattern_48khz_no_tmp_dependency(tmp_path: Path):
    out_wav = tmp_path / "maceo_48k.wav"
    res = maceo_plex_kick_synthesizer.generate_maceo_plex_kick_pattern(
        output_path=str(out_wav), fundamental_hz=49.0, bpm=122.0, length_bars=2
    )
    assert Path(res).exists()
    # Read only header via wave module (no binary content in LLM context)
    import wave

    with wave.open(res, "rb") as wf:
        assert wf.getframerate() == 48000
        assert wf.getsampwidth() == 3
        assert wf.getnchannels() == 2


def test_arrangement_templates_zero_drift_and_false_drop_bar60(tmp_path: Path):
    tpb = 480
    bar_ticks = 4 * tpb
    for name, tpl in arrangement_structure_engine.ARRANGEMENT_TEMPLATES.items():
        mid_path = tmp_path / f"{name}.mid"
        out = arrangement_structure_engine.generate_arrangement_midi(name, output_path=str(mid_path))
        mid = mido.MidiFile(out)
        expected_bars = sum(int(s["bars"]) for s in tpl["sections"])
        max_ticks = expected_bars * bar_ticks

        for track in mid.tracks:
            abs_tick = 0
            for msg in track:
                assert msg.time >= 0
                abs_tick += msg.time
            assert abs_tick <= max_ticks + tpb

        if expected_bars >= 64:
            # Verify Bar 60 beats 3-4 False Drop gap on Kick track (if present)
            for track in mid.tracks:
                if track.name == "kick":
                    abs_tick = 0
                    vacuum_start = 59 * bar_ticks + 2 * tpb
                    vacuum_end = 60 * bar_ticks
                    hits_in_vacuum = []
                    for msg in track:
                        abs_tick += msg.time
                        if msg.type == "note_on" and msg.velocity > 0 and vacuum_start <= abs_tick < vacuum_end:
                            hits_in_vacuum.append(abs_tick)
                    assert hits_in_vacuum == [], f"{name} leaked kick during Bar 60 False Drop: {hits_in_vacuum}"


def test_playlist_arranger_and_loop_generators_zero_drift(tmp_path: Path, monkeypatch):
    # Playlist FLP compiler
    flp_out = tmp_path / "arranged.flp"
    res = fl_playlist_arranger.compile_playlist_song_arrangement(bpm=112.0, output_path=str(flp_out))
    assert res["status"] == "SUCCESS"
    assert res["total_bars"] == 64
    assert res["total_notes"] > 500
    assert Path(res["json_manifest_file"]).exists()

    # Penrose stair loop with Picardy turnaround
    sj_mid = tmp_path / "penrose.mid"
    flstudio_infinite_harmonic_loop.generate_satin_jackets_infinite_loop(str(sj_mid), bpm=116.0)
    mid_sj = mido.MidiFile(str(sj_mid))
    assert abs(sum(m.time for m in mid_sj.tracks[1]) - 32 * 480) < 40

    # AIR Moon Safari deterministically humanized
    air_mid = tmp_path / "air.mid"
    air_moon_safari_engine.generate_air_moon_safari_multitrack(str(air_mid), bpm=88.0)
    mid_air = mido.MidiFile(str(air_mid))
    assert len(mid_air.tracks) == 4

    # Full arrangement generator (no workspace pollution)
    monkeypatch.setattr(flstudio_full_arrangement_generator, "OUTPUT_DIR", tmp_path)
    assert flstudio_full_arrangement_generator.generate_full_arrangement() is True
    mid_intro = mido.MidiFile(str(tmp_path / "01_intro_groove_32bars.mid"))
    assert sum(m.time for m in mid_intro.tracks[0]) <= 32 * 4 * 480
    mid_vocal = mido.MidiFile(str(tmp_path / "02_vocal_triggers_16bars.mid"))
    vocal_on_ticks = []
    acc = 0
    for m in mid_vocal.tracks[0]:
        acc += m.time
        if m.type == "note_on" and m.velocity > 0:
            vocal_on_ticks.append(acc)
    assert vocal_on_ticks == [0, 4 * 1920, 8 * 1920, 12 * 1920]

    mid_dub = mido.MidiFile(str(tmp_path / "03_dub_breakdown_24tet_32bars.mid"))
    final_pws = [m.pitch for m in mid_dub.tracks[0] if m.type == "pitchwheel"]
    assert final_pws[-1] == 0


def test_sidechain_and_vibrato_cc_click_free():
    curve = fl_sidechain_ducking_engine.generate_logarithmic_ducking_curve()
    assert curve[0] == 1.0
    assert curve[-1] == 1.0
    assert min(curve) == 0.0

    vb = midi_cc_automation_generator.generate_flamenco_vibrato_bend(bars=2, bpm=112.0)
    assert vb[-1][1] == bytes([0xE0, 0x00, 0x40])

    sc = midi_cc_automation_generator.generate_sidechain_ducking_curve(bars=2, bpm=112.0)
    assert sc[0][1][2] == 127  # smooth ramp starts from 127 instead of sudden jump to 0


def test_mcp_club_c5_mastering_and_structured_arrangement_tools(tmp_path: Path):
    sr = 48000
    duration_sec = 4.0
    n = int(sr * duration_sec)
    kick_single = c5_dsp_core.synthesize_phase_locked_kick(sample_rate=sr, duration_sec=0.38, root_hz=49.0)

    kick_bus = np.zeros(n, dtype=np.float64)
    bass_bus = np.zeros(n, dtype=np.float64)
    chord_l = np.zeros(n, dtype=np.float64)
    chord_r = np.zeros(n, dtype=np.float64)

    beat_sec = 60.0 / 122.0
    kick_triggers = []
    for beat in range(8):
        idx = int(beat * beat_sec * sr)
        if idx + len(kick_single) <= n:
            kick_triggers.append(idx)
            kick_bus[idx : idx + len(kick_single)] += kick_single * 0.72

    # PolyBLEP rolling bass + chord harmonic warmth
    for beat in range(8):
        for sub_i in (1, 2, 3):
            idx = int((beat + sub_i * 0.25) * beat_sec * sr)
            dur = int(0.11 * sr)
            if idx + dur <= n:
                t_b = np.arange(dur, dtype=np.float64) / sr
                freq = 49.0 * (2.0 if sub_i == 2 else 1.0)
                note = (
                    0.7 * np.sin(2.0 * np.pi * freq * t_b)
                    + 0.3 * c5_dsp_core.polyblep_saw(freq, dur, sr)
                ) * np.exp(-t_b * 7.5) * 0.42
                bass_bus[idx : idx + dur] += c5_dsp_core.apply_zero_crackle_envelope(note, sr, 5.0, 10.0)

    t_all = np.arange(n, dtype=np.float64) / sr
    pad = (
        0.5 * np.sin(2.0 * np.pi * 196.0 * t_all)
        + 0.3 * np.sin(2.0 * np.pi * 233.08 * t_all)
        + 0.2 * np.sin(2.0 * np.pi * 293.66 * t_all)
    ) * 0.14
    chord_l += pad * 0.56
    chord_r += pad * 0.44
    chord_l, chord_r = c5_dsp_core.carve_polyphonic_mud(chord_l, chord_r, sample_rate=sr)

    sc_sub, sc_mid = c5_dsp_core.build_coupled_multiband_sidechain(n, kick_triggers, sample_rate=sr)
    b_lo, b_hi = c5_dsp_core.lr4_zero_phase_crossover(bass_bus, 140.0, sr)
    bass_sc = b_lo * sc_sub + b_hi * sc_mid

    left = kick_bus + bass_sc + chord_l * sc_mid
    right = kick_bus + bass_sc + chord_r * sc_mid
    left, right = c5_dsp_core.apply_coherent_shared_room(left, right, sample_rate=sr, wet=0.08)

    premaster = tmp_path / "premaster_48k.wav"
    mastered = tmp_path / "mastered_club_c5.wav"
    c5_dsp_core.write_pcm_wav(premaster, left, right, sample_rate=sr, bit_depth=24, dither=False)

    res = mcp_server.fl_master_audio_club_c5(
        input_wav=str(premaster),
        output_wav=str(mastered),
        profile_name="club_c5",
        bit_depth=24,
    )
    assert res["status"] == "SUCCESS"
    assert res["true_peak_dbtp_after"] <= -0.45
    assert res["rubin_audit_after"]["low_end_phase_coherence"] >= 0.95
    assert res["rubin_audit_after"]["crest_factor_db"] >= 8.0
    assert res["rubin_audit_after"]["spectral_flatness_sfm"] < 0.35
    assert res["rubin_audit_after"]["is_pure_bone"] is True

    arr = mcp_server.fl_generate_structured_arrangement(
        template_name="satin_maceo_air_hybrid_64",
        output_path=str(tmp_path / "hybrid_64.mid"),
    )
    assert arr["status"] == "SUCCESS"
    assert arr["total_bars"] == 64
    assert Path(arr["midi_file"]).exists()


def test_bark_spectral_flatness_tilt_invariance_and_slop_rejection():
    from scripts.mastering_reverse_engine_fl import (
        compute_bark_spectral_flatness,
        compute_rubin_metrics,
    )

    sr = 48000
    t = np.arange(sr * 4, dtype=np.float64) / sr
    rng = np.random.default_rng(2026)

    # 1. French-Touch bright harmonic chord + 16th hi-hat transients (healthy -3 dB/oct presence)
    chord = sum(
        (1.0 / k) * np.sin(2.0 * np.pi * f0 * k * t)
        for f0 in (130.81, 155.56, 196.00, 233.08, 293.66)
        for k in range(1, 16)
    )
    chord = 0.35 * chord / np.max(np.abs(chord))
    hats = np.exp(-((t % 0.125) / 0.012)) * rng.normal(0.0, 0.14, len(t))
    kick_env = np.exp(-((t % 0.5) / 0.065)) * np.sin(2.0 * np.pi * 52.0 * t) * 0.55
    bright_club_mix = kick_env + chord + hats

    rubin_bright = compute_rubin_metrics(bright_club_mix, bright_club_mix, sample_rate=sr)
    assert rubin_bright["spectral_flatness_sfm"] < 0.25
    assert rubin_bright["is_pure_bone"] is True

    # 2. White, Pink (1/f), and Steep Low-Passed Noise (1/f^3) must ALL be caught (no tilt cheat)
    white = rng.normal(0.0, 0.3, len(t))
    w_fft = np.fft.rfft(white)
    f_ax = np.maximum(np.fft.rfftfreq(len(white), d=1.0 / sr), 1.0)
    pink = np.fft.irfft(w_fft / np.sqrt(f_ax), n=len(white))
    steep_noise = np.fft.irfft(w_fft / (f_ax**1.5), n=len(white))

    assert compute_bark_spectral_flatness(white, sample_rate=sr) > 0.75
    assert compute_bark_spectral_flatness(pink, sample_rate=sr) > 0.75
    assert compute_bark_spectral_flatness(steep_noise, sample_rate=sr) > 0.70

    # 3. Clean 50 Hz sub-sine + midband intermodulation pink noise mush must fail Rubin Gate
    sos_hp = signal.butter(4, 500.0 / (sr / 2.0), btype="high", output="sos")
    mid_mush = signal.sosfilt(sos_hp, pink / np.max(np.abs(pink)) * 0.25)
    sub_plus_mush = 0.5 * np.sin(2.0 * np.pi * 50.0 * t) + mid_mush
    rubin_mush = compute_rubin_metrics(sub_plus_mush, sub_plus_mush, sample_rate=sr)
    assert rubin_mush["spectral_flatness_sfm"] > 0.70
    assert rubin_mush["is_pure_bone"] is False

    # 4. Isolated 49 Hz club kick stem & mandated -57 dBFS analog tape bed must pass Rubin Gate
    kick_single = c5_dsp_core.synthesize_phase_locked_kick(sample_rate=sr, duration_sec=0.40, root_hz=49.0)
    kick_stem = np.zeros(len(t), dtype=np.float64)
    for beat_i in range(8):
        idx = int(beat_i * 0.5 * sr)
        kick_stem[idx : idx + len(kick_single)] += kick_single * 0.75
    rubin_kick = compute_rubin_metrics(kick_stem, kick_stem, sample_rate=sr)
    assert rubin_kick["spectral_flatness_sfm"] < 0.05
    assert rubin_kick["is_pure_bone"] is True

    tape_l, tape_r = c5_dsp_core.generate_warm_analog_tape_bed(len(t), sample_rate=sr, level_dbfs=-57.0)
    rubin_tape = compute_rubin_metrics(tape_l, tape_r, sample_rate=sr)
    assert rubin_tape["is_pure_bone"] is True


def test_real_assets_bridge_round_robin_velocity_and_fallback(tmp_path: Path, monkeypatch):
    from scripts import c5_real_assets_bridge

    # Graceful fallback on missing asset root (clear LRU cache around patched candidates)
    monkeypatch.setattr(c5_real_assets_bridge, "FL_PATCHES_CANDIDATES", (tmp_path,))
    c5_real_assets_bridge.get_round_robin_drum_pool.cache_clear()
    c5_real_assets_bridge.get_real_room_ir.cache_clear()
    try:
        assert c5_real_assets_bridge.get_round_robin_drum_pool("kick", count=6) == ()
        assert c5_real_assets_bridge.get_real_room_ir("chamber_warm") is None
    finally:
        monkeypatch.undo()
        c5_real_assets_bridge.get_round_robin_drum_pool.cache_clear()
        c5_real_assets_bridge.get_real_room_ir.cache_clear()

    # Physical velocity-to-cutoff darkening
    sr = 48000
    t = np.arange(int(0.25 * sr), dtype=np.float64) / sr
    env = np.exp(-t * 12.0)
    tone = np.sin(2.0 * np.pi * 6000.0 * t) * env
    bright_hit = np.column_stack((tone, tone))
    soft_shaped = c5_real_assets_bridge.shape_velocity_sample(bright_hit, velocity=0.25, sample_rate=sr)
    hard_shaped = c5_real_assets_bridge.shape_velocity_sample(bright_hit, velocity=0.95, sample_rate=sr)
    assert np.all(np.isfinite(soft_shaped)) and np.all(np.isfinite(hard_shaped))
    assert float(np.sqrt(np.mean(soft_shaped**2))) < float(np.sqrt(np.mean(hard_shaped**2)))

    # Real local studio assets verification (skip assertion on pool length only if assets aren't present)
    pool = c5_real_assets_bridge.get_round_robin_drum_pool("closed_hat", count=6, sample_rate=sr)
    if pool:
        assert len(pool) >= 5
        assert pool[0].ndim == 2 and pool[0].shape[1] == 2
        assert np.all(np.isfinite(pool[0]))


def test_nonlinear_physical_engines_quality_and_zero_warning():
    import warnings

    sr = 48000
    dur_n = int(1.0 * sr)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)

        saw = c5_dsp_core.polyblep_saw(110.0, dur_n, sample_rate=sr)
        sweep = np.linspace(380.0, 2600.0, dur_n)
        zdf_out = c5_dsp_core.zdf_moog_ladder_filter(saw, cutoff_hz=sweep, resonance=0.35, drive=1.4, sample_rate=sr)
        assert zdf_out.shape == (dur_n,) and np.all(np.isfinite(zdf_out))
        assert float(np.sqrt(np.mean(zdf_out**2))) > 0.05

        rh_l, rh_r = c5_dsp_core.synthesize_rhodes_electromechanical(
            293.66, dur_n, velocity=0.84, sample_rate=sr, stereo_pan=0.35
        )
        assert np.all(np.isfinite(rh_l)) and np.all(np.isfinite(rh_r))
        assert not np.allclose(rh_l, rh_r)  # stereo tremolo + pan

        sol_l, sol_r = c5_dsp_core.synthesize_solina_bbd_ensemble(rh_l, rh_r, sample_rate=sr)
        assert np.all(np.isfinite(sol_l)) and np.all(np.isfinite(sol_r))
        assert float(np.max(np.abs(sol_l - sol_r))) > 1e-3

        ks = c5_dsp_core.synthesize_karplus_strong_pluck(196.0, dur_n, velocity=0.88, sample_rate=sr)
        assert np.all(np.isfinite(ks))
        early_rms = float(np.sqrt(np.mean(ks[: dur_n // 4] ** 2)))
        late_rms = float(np.sqrt(np.mean(ks[-dur_n // 6 :] ** 2)))
        assert early_rms > late_rms * 2.5

        hh_closed = c5_dsp_core.synthesize_analog_hihat_cymbal(int(0.12 * sr), is_open=False, sample_rate=sr)
        hh_open = c5_dsp_core.synthesize_analog_hihat_cymbal(int(0.35 * sr), is_open=True, sample_rate=sr)
        assert float(np.sqrt(np.mean(hh_closed**2))) > 0.01 and float(np.sqrt(np.mean(hh_open**2))) > 0.01

        wl, wr = c5_dsp_core.apply_wdf_warm_saturator(rh_l, rh_r, sample_rate=sr, drive_db=2.2, mix=0.45)
        el, er = c5_dsp_core.apply_spectral_balance_eq(
            wl, wr, sample_rate=sr, sub_gain_db=-2.0, mud_cut_db=-2.0, presence_gain_db=3.0, air_gain_db=3.0
        )
        assert np.all(np.isfinite(el)) and np.all(np.isfinite(er))


def test_club_organic_vst3_mastering_and_antigoodhart_auditor(tmp_path: Path):
    from scripts.mastering_reverse_engine_fl import master_audio_reverse_engineered
    from scripts.spectral_audio_auditor import analyze_audio_spectrum

    sr = 48000
    bpm = 124.0
    bar_s = int(sr * 4.0 * 60.0 / bpm)
    n_slop = bar_s * 4
    t_bar = np.arange(bar_s, dtype=np.float64) / sr
    one_bar = (
        0.72 * np.sin(2.0 * np.pi * 52.0 * t_bar)
        + 0.08 * np.sin(2.0 * np.pi * 196.0 * t_bar)
    )
    slop_mono = np.tile(one_bar, 4)[:n_slop]
    slop_wav = tmp_path / "ia_slop_124bpm.wav"
    c5_dsp_core.write_pcm_wav(slop_wav, slop_mono, slop_mono, sample_rate=sr, bit_depth=24, dither=False)

    slop_rep = analyze_audio_spectrum(slop_wav, bpm=bpm)
    assert slop_rep["perceptual_warnings"]["is_low_end_bloated"] is True
    assert slop_rep["perceptual_warnings"]["is_mono_tunnel"] is True
    assert slop_rep["perceptual_warnings"]["is_presence_deficient"] is True
    assert slop_rep["perceptual_warnings"]["is_robot_loop_cloning"] is True
    assert slop_rep["exergy_rating_21000"] < 15000

    # Rich, stereo, dynamic 4-bar test premaster mastered cleanly with club_organic_vst3 (both fallback and VST3)
    beat_s = int(sr * 60.0 / bpm)
    kick_wave = c5_dsp_core.synthesize_phase_locked_kick(sample_rate=sr, duration_sec=0.38, root_hz=50.0)
    mix_l = np.zeros(n_slop, dtype=np.float64)
    mix_r = np.zeros(n_slop, dtype=np.float64)
    roots = [146.83, 164.81, 196.00, 130.81]
    for b_idx in range(4):
        root = roots[b_idx]
        b_start = b_idx * bar_s
        for beat in range(4):
            if b_idx == 3 and beat == 3:
                continue
            k_pos = b_start + beat * beat_s
            end = min(n_slop, k_pos + len(kick_wave))
            mix_l[k_pos:end] += kick_wave[: end - k_pos] * 0.55
            mix_r[k_pos:end] += kick_wave[: end - k_pos] * 0.55
            # 8th/16th bright analog hi-hat spread stereo so fixture exercises real high-air band
            for sub in (beat_s // 4, beat_s // 2, (3 * beat_s) // 4):
                h_pos = k_pos + sub
                hh = c5_dsp_core.synthesize_analog_hihat_cymbal(
                    int(0.14 * sr), is_open=(sub == beat_s // 2 and beat == 1), sample_rate=sr, seed=b_idx * 40 + beat * 4 + sub
                )
                h_end = min(n_slop, h_pos + len(hh))
                amp = 1.38 if sub == beat_s // 2 else 0.90
                mix_l[h_pos:h_end] += hh[: h_end - h_pos] * (amp if beat % 2 == 0 else amp * 0.25)
                mix_r[h_pos:h_end] += hh[: h_end - h_pos] * (amp * 0.25 if beat % 2 == 0 else amp)
        dur = min(bar_s, n_slop - b_start)
        rl, rr = c5_dsp_core.synthesize_rhodes_electromechanical(root * 2.0, dur, sample_rate=sr, stereo_pan=0.65 if b_idx % 2 == 0 else -0.65)
        ks = c5_dsp_core.synthesize_karplus_strong_pluck(root * 4.0, dur, sample_rate=sr, brightness=0.92, seed=500 + b_idx)
        sp_l, sp_r = c5_dsp_core.synthesize_string_ensemble_pad([root * 4.0, root * 6.0], dur, velocity=0.88, sample_rate=sr, cutoff_curve=7500.0)
        mix_l[b_start : b_start + dur] += rl * 0.30 + ks * 0.34 + sp_l * 0.28
        mix_r[b_start : b_start + dur] += rr * 0.30 + ks * 0.08 + sp_r * 0.28

    pre_wav = tmp_path / "organic_pre_124bpm.wav"
    mast_fb = tmp_path / "organic_master_fallback.wav"
    c5_dsp_core.write_pcm_wav(pre_wav, mix_l, mix_r, sample_rate=sr, bit_depth=24, dither=False)

    res_fb = master_audio_reverse_engineered(
        input_wav=str(pre_wav),
        output_wav=str(mast_fb),
        profile_name="club_organic_vst3",
        use_vst3=False,
    )
    assert res_fb["status"] == "SUCCESS"
    assert res_fb["true_peak_dbtp_after"] <= -0.45
    assert res_fb["rubin_audit_after"]["is_pure_bone"] is True
    assert res_fb["rubin_audit_after"]["low_end_phase_coherence"] >= 0.95
    assert res_fb["vst3_plugins_applied"] == []

    mast_vst = tmp_path / "organic_master_vst3.wav"
    res_vst = master_audio_reverse_engineered(
        input_wav=str(pre_wav),
        output_wav=str(mast_vst),
        profile_name="club_organic_vst3",
        use_vst3=True,
    )
    assert res_vst["status"] == "SUCCESS"
    assert res_vst["rubin_audit_after"]["is_pure_bone"] is True
    assert len(res_vst["vst3_plugins_applied"]) >= 1

    aud = analyze_audio_spectrum(mast_vst, bpm=bpm)
    assert aud["band_balance_pct"]["sub_lt120"] < 68.0
    assert aud["band_balance_pct"]["presence_2k_6k"] >= 1.5
    assert aud["band_balance_pct"]["air_6k_18k"] >= 1.2
    assert aud["stereo_width_s_m"]["sub_lt120"] <= 0.02
    assert aud["stereo_width_s_m"]["presence_2k_6k"] >= 0.20


def test_arrangement_macro_phrasing_breaks_loop_cloning(tmp_path: Path):
    out_mid = tmp_path / "macro_phrased.mid"
    res_path = arrangement_structure_engine.generate_arrangement_midi("satin_maceo_air_hybrid_64", out_mid)
    assert Path(res_path).exists()
    mid = mido.MidiFile(str(out_mid))
    tpb = mid.ticks_per_beat
    bar_ticks = 4 * tpb
    chord_track = next(t for t in mid.tracks if t.name == "chords")

    bar_notes: dict[int, list[int]] = {}
    cc74_vals: list[int] = []
    acc = 0
    for msg in chord_track:
        acc += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            bar_idx = acc // bar_ticks
            bar_notes.setdefault(bar_idx, []).append(msg.note)
        elif msg.type == "control_change" and msg.control == 74:
            cc74_vals.append(msg.value)

    # Active phrasing bars must exhibit changing voice-led pitch sets (not cloned bars)
    active_voicings = [
        tuple(sorted(set(notes)))
        for _, notes in sorted(bar_notes.items())
        if notes
    ][:12]
    assert len(set(active_voicings)) >= 3
    if cc74_vals:
        assert max(cc74_vals) - min(cc74_vals) >= 15


