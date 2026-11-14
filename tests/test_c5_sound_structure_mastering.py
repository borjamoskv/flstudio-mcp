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
