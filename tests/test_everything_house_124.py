"""
Tests de verificación C5-REAL para Everything In Its Right Place (House 124 BPM):
  - Tríada de entrega (Master WAV 48 kHz/24b, Stems discretos, MIDI SMF Tipo 1, .flp)
  - Falso Drop determinista en Compás 60 (pulsos 3-4 vacíos en kick/bajo, tape bed vivo)
  - Zero-Crackle Derivative Gate en subgrave y Rubin Acoustic Gate (EXERGÍA PURA)
  - Ruta híbrida con stem orgánico externo (time-stretch + resample 44.1 -> 48 kHz)
"""

import sys
import wave
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from scripts import c5_dsp_core, everything_in_its_right_place_house_124 as eiirp  # noqa: E402
from scripts.mastering_reverse_engine_fl import compute_rubin_metrics  # noqa: E402


def test_everything_house_124_64_bars_false_drop_and_rubin_gate(tmp_path: Path):
    res = eiirp.build_everything_house_124(
        profile_name="deep_house",
        total_bars=64,
        output_dir=str(tmp_path),
    )

    assert res["status"] == "SUCCESS"
    assert res["bpm"] == 124.0
    assert res["sample_rate_hz"] == 48000
    assert res["false_drop_bar"] == 60
    assert res["soul_classification"]["mode"] == "AUTÓMATA_SINTÉTICO_ESTRUCTURAL"
    assert res["zero_crackle_sub_audit"]["zero_crackle_passed"] is True

    master_path = Path(res["master_wav"])
    midi_path = Path(res["midi_file"])
    flp_path = Path(res["flp_file"])
    assert master_path.exists()
    assert midi_path.exists()
    assert flp_path.exists()
    assert len(res["stems"]) == 7

    with wave.open(str(master_path), "rb") as wf:
        assert wf.getframerate() == 48000
        assert wf.getsampwidth() == 3
        assert wf.getnchannels() == 2

    # Verificar Rubin Gate y techo True Peak
    rubin = res["mastering_metrics"]["rubin_audit_after"]
    assert rubin["is_pure_bone"] is True
    assert rubin["low_end_phase_coherence"] >= 0.95
    assert rubin["crest_factor_db"] >= 8.0
    assert rubin["spectral_flatness_sfm"] < 0.35
    assert res["mastering_metrics"]["true_peak_dbtp_after"] <= -0.45

    # Verificar auditoría de microvariaciones, síncopas, silencios y humanización RAE/Voss-Clarke
    hum = res["humanization_and_groove_audit"]
    assert hum["microtiming_offsets_ms"]["std_ms"] > 0.5
    assert hum["bass_laid_back_pocket_ms_range"][1] > hum["bass_laid_back_pocket_ms_range"][0]
    assert hum["prophet_strum_ms_range"][1] > hum["prophet_strum_ms_range"][0]
    assert hum["syncopated_turnaround_events"] > 0
    assert hum["offgrid_ghost_wood_perc_events"] > 0
    assert hum["avantgarde_spectral_bow_events"] >= 4
    silence_names = {s["name"] for s in hum["sculpted_living_silences"]}
    assert {
        "bar16_caesura_beat4",
        "bar32_pre_abyss_beats3_4",
        "bar48_pre_climax_vacuum",
        "bar60_c5_false_drop",
    }.issubset(silence_names)

    # Verificar Falso Drop en Compás 60 pulsos 3-4 y silencio estructural en Compás 48 pulsos 3-4 en MIDI
    mid = mido.MidiFile(str(midi_path))
    ppq = mid.ticks_per_beat
    track_names = {tr.name for tr in mid.tracks}
    assert "AvantGarde_Melodic_Techno" in track_names

    vacuum_windows = [
        (47 * 4 * ppq + 2 * ppq, 48 * 4 * ppq),  # Bar 48 beats 3-4
        (59 * 4 * ppq + 2 * ppq, 60 * 4 * ppq),  # Bar 60 beats 3-4 (Falso Drop)
    ]
    for tr in mid.tracks:
        if tr.name in ("Drums_Kick", "Drums_MPC_Perc", "SubBass_C_Phrygian"):
            acc = 0
            leaks = []
            vels = set()
            for msg in tr:
                acc += msg.time
                if msg.type == "note_on" and msg.velocity > 0:
                    vels.add(msg.velocity)
                    for w0, w1 in vacuum_windows:
                        if w0 <= acc < w1:
                            leaks.append((tr.name, acc))
            assert leaks == [], f"Se filtraron golpes en ventanas de silencio: {leaks}"
            assert len(vels) >= 4, f"Poca dinámica humana en {tr.name}: {vels}"

    # Verificar que en silencios estructurales (Bar 48 y Bar 60 beats 3-4) el tape bed + cola siguen vivos (no 0.0)
    beat_sec = 60.0 / 124.0
    master_audio, _ = sf.read(str(master_path))
    for b_idx in (47, 59):
        s0 = int(round((b_idx * 4.0 + 2.3) * beat_sec * 48000))
        s1 = int(round((b_idx * 4.0 + 3.8) * beat_sec * 48000))
        assert float(np.max(np.abs(master_audio[s0:s1]))) > 1e-4

    # Breakdown Abyss (Bars 33-40): cero golpes de Kick
    b_abyss0 = 32 * 4 * ppq
    b_abyss1 = 40 * 4 * ppq
    for tr in mid.tracks:
        if tr.name == "Drums_Kick":
            acc = 0
            for msg in tr:
                acc += msg.time
                if msg.type == "note_on" and msg.velocity > 0:
                    assert not (b_abyss0 <= acc < b_abyss1)

    # Todos los stems individuales deben mantener coherencia de subgrave >= 0.90;
    # los stems tonales/armónicos y de mezcla además pasan is_pure_bone estricto.
    for st_path in res["stems"]:
        st_data, st_sr = sf.read(st_path, always_2d=True)
        st_rubin = compute_rubin_metrics(st_data[:, 0], st_data[:, 1], sample_rate=int(st_sr))
        assert st_rubin["low_end_phase_coherence"] >= 0.90, f"Stem subgrave desfasado: {st_path} -> {st_rubin}"
        if "03_MPC_Percussion" not in st_path:
            assert st_rubin["is_pure_bone"] is True, f"Stem falló Rubin: {st_path} -> {st_rubin}"


def test_organic_vocal_stem_hybrid_stretch_and_gate(tmp_path: Path):
    # Crear un stem vocal orgánico simulado a 44.1 kHz / 105 BPM (sin dependencia externa)
    sr_in = 44100
    dur_sec = 10.0
    t = c5_dsp_core.make_time_axis(int(sr_in * dur_sec), sr_in)
    # Formantes tipo voz en C4/G4 modulados por envolvente respirada
    env = 0.5 * (1.0 - np.cos(2.0 * np.pi * (105.0 / 120.0) * t))
    vocal = (0.55 * np.sin(2.0 * np.pi * 261.63 * t) + 0.25 * np.sin(2.0 * np.pi * 523.25 * t)) * env * 0.45
    vocal_stereo = np.column_stack((vocal, vocal * 0.95))
    stem_in = tmp_path / "radiohead_vocal_44k.wav"
    sf.write(str(stem_in), vocal_stereo, sr_in, subtype="PCM_24")

    res = eiirp.build_everything_house_124(
        vocal_stem=str(stem_in),
        source_bpm_override=105.0,
        profile_name="deep_house",
        total_bars=8,
        output_dir=str(tmp_path / "out"),
    )
    assert res["status"] == "SUCCESS"
    assert res["soul_classification"]["mode"] == "TRANSDUCCION_ORGANICA_DEMUCS"
    assert res["soul_classification"]["estimated_source_bpm"]["vocals"] == 105.0
    assert len(res["stems"]) == 8
    assert res["mastering_metrics"]["rubin_audit_after"]["is_pure_bone"] is True
