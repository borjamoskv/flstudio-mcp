"""Pruebas estructurales y DSP para el generador SIKAH-128 (3/2 -> 6/4 -> 12/8)."""

from __future__ import annotations

import ast
import json
import sys
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import mido
import numpy as np

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from scripts.generate_sikah128_triptych import (  # noqa: E402
    BAR_DURATION_SEC,
    BAR_TICKS,
    PPQ,
    SAMPLE_RATE,
    SECTIONS_CLUB_64,
    SECTIONS_PLAN,
    _render_continuous_legato_lead,
    cents_to_pitchwheel,
    export_fl_assets,
    render_verification_maquette,
)


def _decode_pcm24_stereo(wav_path: Path) -> Tuple[int, np.ndarray]:
    """Decodifica un WAV estéreo de 24 bits con sign-extension exacto."""
    with wave.open(str(wav_path), "rb") as wf:
        sr = wf.getframerate()
        n_ch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    assert n_ch == 2
    assert sampwidth == 3
    bytes_u8 = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
    vals = (
        bytes_u8[:, 0].astype(np.int32)
        | (bytes_u8[:, 1].astype(np.int32) << 8)
        | (bytes_u8[:, 2].astype(np.int32) << 16)
    )
    vals.flags.writeable = False
    vals = np.where((vals & 0x800000) != 0, vals - 0x1000000, vals)
    return sr, (vals.astype(np.float64) / 8388608.0).reshape(-1, 2)


def test_export_fl_assets_and_symbolic_invariants(tmp_path: Path) -> None:
    bounces_dir = tmp_path / "bounces"
    fl_user_dir = tmp_path / "fl_user"
    assets = export_fl_assets(bounces_dir=bounces_dir, fl_user_dir=fl_user_dir)

    assert assets["midi_path"].exists()
    assert assets["scl_path"].exists()
    assert assets["kbm_path"].exists()
    assert assets["pyscript_path"].exists()

    # 1. Validar Scala .scl (12 grados cerrando en 2/1)
    scl_lines = [
        ln.strip()
        for ln in assets["scl_path"].read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("!")
    ]
    assert scl_lines[1] == "12"
    assert scl_lines[-1] == "2/1"
    assert len(scl_lines) == 14  # descripción + count(12) + 12 intervalos

    # 2. Validar sintaxis y puntos de entrada de FL Studio .pyscript
    tree = ast.parse(assets["pyscript_path"].read_text(encoding="utf-8"))
    fn_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {"createDialog", "apply", "createScore"}.issubset(fn_names)

    # 3. Validar modulación métrica isócrona 3/2 -> 6/4 -> 12/8 en SMF Tipo 1
    mid = mido.MidiFile(str(assets["midi_path"]))
    assert mid.type == 1
    assert mid.ticks_per_beat == PPQ

    conductor = mid.tracks[0]
    tempo_msgs = [m for m in conductor if m.type == "set_tempo"]
    assert len(tempo_msgs) == 1
    assert abs(mido.tempo2bpm(tempo_msgs[0].tempo) - 115.2) < 1e-3

    time_sigs: List[Tuple[str, int]] = []
    abs_tick = 0
    for msg in conductor:
        abs_tick += msg.time
        if msg.type == "time_signature":
            time_sigs.append((f"{msg.numerator}/{msg.denominator}", abs_tick))

    assert time_sigs == [
        ("3/2", 0),
        ("6/4", 4 * BAR_TICKS),
        ("12/8", 8 * BAR_TICKS),
    ]

    # 4. Validar que en cada compás del estribillo la Tónica D4 (62, 0c) sea anteúltima
    lead_tracks = [
        tr
        for tr in mid.tracks
        if any(m.type == "track_name" and m.name == "Estribillo_Tonic_Penultimate" for m in tr)
    ]
    assert len(lead_tracks) == 1
    lead_track = lead_tracks[0]

    bars_notes: Dict[int, List[Tuple[int, int, int]]] = {}
    abs_t = 0
    cur_pitch = 0
    for msg in lead_track:
        abs_t += msg.time
        if msg.type == "pitchwheel":
            cur_pitch = msg.pitch
        elif msg.type == "note_on" and msg.velocity > 0:
            bar_idx = abs_t // BAR_TICKS
            bars_notes.setdefault(bar_idx, []).append((abs_t, msg.note, cur_pitch))

    assert len(bars_notes) == 16
    expected_sikah_pitch = cents_to_pitchwheel(-50.0)
    for bar_idx in range(16):
        notes = bars_notes[bar_idx]
        if bar_idx == 7:
            assert len(notes) == 2
        else:
            assert len(notes) == 8
        assert notes[-2][1] == 62  # D4 Tónica anteúltima
        assert notes[-2][2] == 0
        assert notes[-1][1] == 64  # E_half-flat4 cierre suspendido (+150c)
        assert notes[-1][2] == expected_sikah_pitch


def test_render_verification_maquette_short_triptych(tmp_path: Path) -> None:
    short_sections = [("3/2", 3, 2, 1), ("6/4", 6, 4, 1), ("12/8", 12, 8, 1)]
    summary = render_verification_maquette(
        bounces_dir=tmp_path / "bounces",
        sections=short_sections,
        profile_name="dub_techno",
        run_mastering=True,
        run_linter_subprocess=False,
    )

    assert summary["engine_version"] == "analog_waveguide_v3"
    assert summary["classification"] == "AUTÓMATA_SINTÉTICO_ESTRUCTURAL"
    pre_wav = Path(summary["premaster_wav"])
    mast_wav = Path(summary["mastered_wav"])
    audit_json = Path(summary["audit_json"])

    assert pre_wav.exists()
    assert mast_wav.exists()
    assert audit_json.exists()
    assert len(summary["stems"]) == 6
    for stem_path in summary["stems"].values():
        assert Path(stem_path).exists()

    parsed_audit = json.loads(audit_json.read_text(encoding="utf-8"))
    assert parsed_audit["engine_version"] == "analog_waveguide_v3"
    assert parsed_audit["mix_revision"] == "organic_v3.1_tempo_0.60x"
    assert parsed_audit["quarter_bpm"] == 115.2
    assert parsed_audit["climax_12_8_bpm"] == 76.8
    assert parsed_audit["classification"] == "AUTÓMATA_SINTÉTICO_ESTRUCTURAL"
    assert isinstance(parsed_audit["rubin_premaster"], dict)
    assert isinstance(parsed_audit["master_report"], dict)
    assert parsed_audit["crackle_check_premaster"]["zero_crackle_passed"] is True
    assert parsed_audit["crackle_check_sub_bass"]["zero_crackle_passed"] is True
    assert parsed_audit["rubin_premaster"]["low_end_phase_coherence"] >= 0.90
    rubin_after = parsed_audit["master_report"]["rubin_audit_after"]
    assert rubin_after["low_end_phase_coherence"] >= 0.85
    assert rubin_after["crest_factor_db"] >= 8.0
    assert rubin_after["spectral_flatness_sfm"] < 0.35
    assert set(parsed_audit["per_stem_stats"].keys()) == {
        "kick",
        "rumble_bass",
        "trombones",
        "lead_estribillo",
        "castanets",
    }

    sr_pre, pcm_pre = _decode_pcm24_stereo(pre_wav)
    sr_mast, pcm_mast = _decode_pcm24_stereo(mast_wav)
    assert sr_pre == 48000
    assert sr_mast == 48000
    assert pcm_pre.shape[0] > 48000 * 5
    assert pcm_mast.shape[0] > 48000 * 5
    assert np.all(np.isfinite(pcm_pre))
    assert np.all(np.isfinite(pcm_mast))
    assert float(np.max(np.abs(pcm_pre))) <= 1.0
    assert float(np.max(np.abs(pcm_mast))) <= 1.0

    # Verificar lecho continuo analógico en el tramo de vacío Living Pre-Drop (compás 6/4)
    _, pcm_tape = _decode_pcm24_stereo(Path(summary["stems"]["tape_bed"]))
    mid_slice = pcm_tape[len(pcm_tape) // 2 - 4800 : len(pcm_tape) // 2 + 4800]
    assert float(np.sqrt(np.mean(mid_slice**2))) > 0.0


def test_anti_midi_phrasing_and_call_response() -> None:
    """Verifica que el solista continuo NO repita un loop ringtone en los 16 compases."""
    total_bars = sum(nb for _, _, _, nb in SECTIONS_PLAN)
    n_total = int(round((total_bars * BAR_DURATION_SEC + 2.0) * SAMPLE_RATE))
    lead_l, lead_r = _render_continuous_legato_lead(
        sections=SECTIONS_PLAN, n_total=n_total, sample_rate=SAMPLE_RATE
    )
    mono = 0.5 * (lead_l + lead_r)
    bar_samps = int(round(BAR_DURATION_SEC * SAMPLE_RATE))

    # Acto I (compases 0..3) deja respirar la caverna (> 6 dB por debajo del Clímax 12/8)
    rms_act1 = float(np.sqrt(np.mean(mono[: 4 * bar_samps] ** 2) + 1e-18))
    rms_act3 = float(np.sqrt(np.mean(mono[8 * bar_samps : 16 * bar_samps] ** 2) + 1e-18))
    diff_act_db = 20.0 * np.log10(rms_act3 / rms_act1)
    assert diff_act_db >= 6.0

    # Compás 0 (caverna desnuda) prácticamente en silencio frente a Compás 8 (entrada Clímax)
    rms_bar0 = float(np.sqrt(np.mean(mono[0:bar_samps] ** 2) + 1e-18))
    rms_bar8 = float(np.sqrt(np.mean(mono[8 * bar_samps : 9 * bar_samps] ** 2) + 1e-18))
    assert rms_bar0 < rms_bar8 * 0.10

    # Call & Response real entre compás 8 (Call completo) y compás 9 (Respuesta espacial)
    rms_bar9 = float(np.sqrt(np.mean(mono[9 * bar_samps : 10 * bar_samps] ** 2) + 1e-18))
    call_resp_db = 20.0 * np.log10(rms_bar8 / rms_bar9)
    assert call_resp_db >= 1.5


def test_club64_arrangement_symbolic_and_living_exit(tmp_path: Path) -> None:
    """Valida los 4 actos (64 compases), el vacío Pre-Drop (c.31) y el Living Exit (c.56..63)."""
    bounces_dir = tmp_path / "bounces_club64"
    fl_user_dir = tmp_path / "fl_user_club64"
    assets = export_fl_assets(
        bounces_dir=bounces_dir, fl_user_dir=fl_user_dir, sections=SECTIONS_CLUB_64
    )
    club_mid_path = bounces_dir / "SIKAH_128_Club64_3_2_6_4_12_8.mid"
    assert club_mid_path.exists()
    assert assets["midi_path"].exists()

    mid = mido.MidiFile(str(club_mid_path))
    conductor = mid.tracks[0]
    time_sigs: List[Tuple[str, int]] = []
    markers: List[Tuple[str, int]] = []
    abs_tick = 0
    for msg in conductor:
        abs_tick += msg.time
        if msg.type == "time_signature":
            time_sigs.append((f"{msg.numerator}/{msg.denominator}", abs_tick))
        elif msg.type == "marker":
            markers.append((msg.text, abs_tick))

    assert time_sigs == [
        ("3/2", 0),
        ("6/4", 16 * BAR_TICKS),
        ("12/8", 32 * BAR_TICKS),
    ]
    assert markers == [
        ("Acto_I_Intro_Hipnotica_3_2", 0),
        ("Acto_II_Breakdown_Hemiola_6_4", 16 * BAR_TICKS),
        ("Pre_Drop_Vacuum", 31 * BAR_TICKS),
        ("Acto_III_Climax_Call_Response_12_8", 32 * BAR_TICKS),
        ("Acto_IV_Living_Exit_Analogico", 56 * BAR_TICKS),
    ]

    lead_track = next(
        tr
        for tr in mid.tracks
        if any(m.type == "track_name" and m.name == "Estribillo_Tonic_Penultimate" for m in tr)
    )
    bars_notes: Dict[int, List[Tuple[int, int, int]]] = {}
    abs_t = 0
    cur_pitch = 0
    for msg in lead_track:
        abs_t += msg.time
        if msg.type == "pitchwheel":
            cur_pitch = msg.pitch
        elif msg.type == "note_on" and msg.velocity > 0:
            bar_idx = abs_t // BAR_TICKS
            bars_notes.setdefault(bar_idx, []).append((abs_t, msg.note, cur_pitch))

    expected_sikah_pitch = cents_to_pitchwheel(-50.0)
    # Compases 0..7 (apertura hipnótica) y 59..63 (Living Exit final) sin notas secas de lead
    for silent_b in list(range(0, 8)) + list(range(59, 64)):
        assert silent_b not in bars_notes
    # Compás 31 (Pre-Drop Vacuum) tiene únicamente las 2 notas desnudas D4 -> Eb_sikah4
    assert len(bars_notes[31]) == 2
    for active_b, notes in bars_notes.items():
        assert len(notes) >= 2
        assert notes[-2][1] == 62 and notes[-2][2] == 0
        assert notes[-1][1] == 64 and notes[-1][2] == expected_sikah_pitch

    # Verificar el arco DSP de 64 compases (204.0 s) del solista continuo
    n_total = int(round((64 * BAR_DURATION_SEC + 4.0) * SAMPLE_RATE))
    lead_l, lead_r = _render_continuous_legato_lead(
        sections=SECTIONS_CLUB_64, n_total=n_total, sample_rate=SAMPLE_RATE
    )
    mono = 0.5 * (lead_l + lead_r)
    bar_samps = int(round(BAR_DURATION_SEC * SAMPLE_RATE))

    rms_intro_open = float(np.sqrt(np.mean(mono[: 8 * bar_samps] ** 2)))
    rms_act1 = float(np.sqrt(np.mean(mono[: 16 * bar_samps] ** 2) + 1e-18))
    rms_climax = float(np.sqrt(np.mean(mono[32 * bar_samps : 56 * bar_samps] ** 2) + 1e-18))
    rms_exit_fade = float(np.sqrt(np.mean(mono[59 * bar_samps : 64 * bar_samps] ** 2) + 1e-18))
    rms_exit_silent = float(np.sqrt(np.mean(mono[60 * bar_samps : 64 * bar_samps] ** 2)))

    assert rms_intro_open < 1e-5
    assert 20.0 * np.log10(rms_climax / rms_act1) >= 8.0
    assert rms_exit_fade < rms_climax * 0.10  # Cola ligada de c.58 -> c.59 (-22 dB)
    assert rms_exit_silent < 1e-5  # Retirada vocal completa en c.60..63
