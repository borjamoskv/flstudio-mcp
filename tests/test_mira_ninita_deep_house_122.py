"""
Tests de verificación C5-REAL para Mira Niñita (Los Jaivas) — Deep House 122 BPM:
  - Tríada de entrega (Master WAV 48 kHz/24b, 8 Stems discretos, MIDI SMF Tipo 1, .flp, .pyscript, .scl)
  - Falso Drop determinista en Compás 60 (pulsos 3-4 vacíos en kick/bajo, lecho de cinta vivo)
  - Zero-Crackle Derivative Gate en subgrave y Quena/Charango + Rubin Acoustic Gate (EXERGÍA PURA)
  - Ruta híbrida con stem orgánico externo con deriva de afinación vintage y time-stretch
  - Interfaz FastMCP fl_remix_mira_ninita_deep_house
"""

import ast
import sys
import wave
from pathlib import Path

import mido
import numpy as np
import soundfile as sf

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

import mcp_server  # noqa: E402
from scripts import c5_dsp_core, mira_ninita_deep_house_122 as mira  # noqa: E402


def test_mira_ninita_deep_house_122_64_bars_false_drop_and_rubin_gate(tmp_path: Path):
    res = mira.build_mira_ninita_deep_house_122(
        profile_name="deep_house",
        total_bars=64,
        output_dir=str(tmp_path),
        deploy_fl_assets=False,
    )

    assert res["status"] == "SUCCESS"
    assert res["bpm"] == 122.0
    assert res["sample_rate_hz"] == 48000
    assert res["bit_depth"] == 24
    assert res["false_drop_bar"] == 60
    assert res["soul_classification"]["mode"] == "AUTÓMATA_SINTÉTICO_ESTRUCTURAL"
    assert res["zero_crackle_sub_audit"]["zero_crackle_passed"] is True
    assert res["zero_crackle_lead_audit"]["zero_crackle_passed"] is True

    master_path = Path(res["master_wav"])
    midi_path = Path(res["midi_file"])
    flp_path = Path(res["flp_file"])
    pyscript_path = Path(res["piano_roll_script"])
    scl_path = Path(res["scala_tuning"])
    assert master_path.exists()
    assert midi_path.exists()
    assert flp_path.exists()
    assert pyscript_path.exists()
    assert scl_path.exists()
    assert len(res["stems"]) == 9
    assert len(res["master_sha256"]) == 64

    # Validar sintaxis AST del Piano Roll script generado
    ast.parse(pyscript_path.read_text(encoding="utf-8"))

    with wave.open(str(master_path), "rb") as wf:
        assert wf.getframerate() == 48000
        assert wf.getsampwidth() == 3
        assert wf.getnchannels() == 2

    rubin = res["mastering_metrics"]["rubin_audit_after"]
    assert rubin["is_pure_bone"] is True
    assert rubin["low_end_phase_coherence"] >= 0.95
    assert rubin["crest_factor_db"] >= 8.5
    assert rubin["spectral_flatness_sfm"] < 0.15
    assert res["mastering_metrics"]["true_peak_dbtp_after"] <= -0.45

    # Verificar Falso Drop en Compás 60 pulsos 3-4 en MIDI y audio
    mid = mido.MidiFile(str(midi_path))
    ppq = mid.ticks_per_beat
    vacuum_start = 59 * 4 * ppq + 2 * ppq
    vacuum_end = 60 * 4 * ppq
    for tr in mid.tracks:
        if tr.name == "Drums_Kick":
            acc = 0
            leaks = []
            for msg in tr:
                acc += msg.time
                if msg.type == "note_on" and msg.velocity > 0 and vacuum_start <= acc < vacuum_end:
                    leaks.append(acc)
            assert leaks == [], f"Kick filtró golpes dentro del Falso Drop Bar 60: {leaks}"
        if tr.name == "Andean_Quena_Lead":
            pws = [m.pitch for m in tr if m.type == "pitchwheel"]
            assert pws and pws[-1] == 0

    beat_sec = 60.0 / 122.0
    s0 = int(round((59 * 4.0 + 2.35) * beat_sec * 48000))
    s1 = int(round((59 * 4.0 + 3.85) * beat_sec * 48000))
    master_audio, _ = sf.read(str(master_path))
    assert float(np.max(np.abs(master_audio[s0:s1]))) > 1e-4


def test_mira_ninita_organic_vocal_hybrid_tuning_and_mcp(tmp_path: Path):
    sr_in = 44100
    dur_sec = 10.0
    t = c5_dsp_core.make_time_axis(int(sr_in * dur_sec), sr_in)
    # Simular voz a 44.1 kHz, 93 BPM (6/8 original) y deriva vintage +45 cents
    drift_ratio = 2.0 ** (45.0 / 1200.0)
    env = 0.5 * (1.0 - np.cos(2.0 * np.pi * (93.0 / 120.0) * t))
    vocal = (
        0.52 * np.sin(2.0 * np.pi * (523.25 * drift_ratio) * t)
        + 0.24 * np.sin(2.0 * np.pi * (392.00 * drift_ratio) * t)
    ) * env * 0.40
    vocal_stereo = np.column_stack((vocal, vocal * 0.94))
    stem_in = tmp_path / "mira_ninita_vocal_vintage_44k.wav"
    sf.write(str(stem_in), vocal_stereo, sr_in, subtype="PCM_24")

    res = mcp_server.fl_remix_mira_ninita_deep_house(
        vocal_stem=str(stem_in),
        source_bpm_override=93.0,
        source_tuning_cents=45.0,
        profile_name="deep_house",
        total_bars=8,
        output_dir=str(tmp_path / "out"),
        deploy_fl_assets=False,
    )

    assert res["status"] == "SUCCESS"
    assert res["soul_classification"]["mode"] == "TRANSDUCCION_ORGANICA_DEMUCS"
    assert res["soul_classification"]["estimated_source_bpm"]["vocals"] == 93.0
    assert res["soul_classification"]["detected_tuning_offset_cents"]["vocals"] == 45.0
    assert len(res["stems"]) == 10
    assert res["mastering_metrics"]["rubin_audit_after"]["is_pure_bone"] is True
