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
    BAR_TICKS,
    PPQ,
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

    assert summary["engine_version"] == "organic_v2"
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
    assert parsed_audit["engine_version"] == "organic_v2"
    assert parsed_audit["classification"] == "AUTÓMATA_SINTÉTICO_ESTRUCTURAL"
    assert isinstance(parsed_audit["rubin_premaster"], dict)
    assert isinstance(parsed_audit["master_report"], dict)
    assert parsed_audit["crackle_check_premaster"]["zero_crackle_passed"] is True
    assert parsed_audit["crackle_check_sub_bass"]["zero_crackle_passed"] is True
    assert parsed_audit["rubin_premaster"]["low_end_phase_coherence"] >= 0.90
    rubin_after = parsed_audit["master_report"]["rubin_audit_after"]
    assert rubin_after["low_end_phase_coherence"] >= 0.85
    assert rubin_after["crest_factor_db"] >= 8.0
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
