#!/usr/bin/env python3
"""
Tests for Cosmic House 122 BPM DSP Engine, Arrangement Structure,
Bar 60 False Drop, Living Exit, Zero-Crackle & Rubin Acoustic Gates, and MCP tool.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import shutil
import wave
from pathlib import Path
from typing import Any, Dict, Iterator

import mido
import numpy as np
import pytest

import mcp_server
from scripts.arrangement_structure_engine import ARRANGEMENT_TEMPLATES
from scripts.cosmic_house_groove_122 import DEFAULT_BPM, SAMPLE_RATE, build_cosmic_house_122
from scripts.mastering_reverse_engine_fl import load_wav_stereo


@pytest.fixture(scope="module")
def cosmic_house_artifacts(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Dict[str, Any]]:
    out_dir = tmp_path_factory.mktemp("cosmic_house_122")
    try:
        yield build_cosmic_house_122(
            total_bars=64,
            bpm=DEFAULT_BPM,
            profile_name="deep_house",
            output_dir=str(out_dir),
            deploy_fl_assets=False,
        )
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def _abs_ticks_per_track(mid: mido.MidiFile) -> Dict[str, list]:
    tracks: Dict[str, list] = {}
    for tr in mid.tracks:
        name = tr.name or "unnamed"
        t = 0
        evs = []
        for msg in tr:
            assert msg.time >= 0, f"Negative delta tick in {name}: {msg}"
            t += msg.time
            evs.append((t, msg))
        tracks[name] = evs
    return tracks


def _rms_dbfs(stereo: np.ndarray, start_s: int, end_s: int) -> float:
    seg = stereo[start_s:end_s]
    mono = 0.5 * (seg[:, 0] + seg[:, 1])
    rms = math.sqrt(float(np.dot(mono, mono)) / max(1, len(mono)))
    return 20.0 * math.log10(max(rms, 1e-9))


def test_bare_metal_triad_and_assets_created(cosmic_house_artifacts: Dict[str, Any]) -> None:
    res = cosmic_house_artifacts
    assert res["status"] == "SUCCESS"
    assert res["classification"] == "AUTÓMATA_SINTÉTICO_ESTRUCTURAL"

    master = Path(res["master_wav"])
    premaster = Path(res["premaster_wav"])
    midi_p = Path(res["midi_file"])
    flp_p = Path(res["flp_file"])
    py_p = Path(res["pyscript_file"])
    scl_p = Path(res["scala_file"])
    receipt_p = Path(res["receipt_file"])

    for p in (master, premaster, midi_p, flp_p, py_p, scl_p, receipt_p):
        assert p.exists(), f"Missing deliverable: {p}"

    with wave.open(str(master), "rb") as wf:
        assert wf.getnchannels() == 2
        assert wf.getsampwidth() == 3  # 24-bit PCM
        assert wf.getframerate() == SAMPLE_RATE
        assert wf.getnframes() > SAMPLE_RATE * 120

    assert len(res["stems"]) == 10
    for stem_path in res["stems"].values():
        sp = Path(stem_path)
        assert sp.exists()
        with wave.open(str(sp), "rb") as wf:
            assert wf.getframerate() == SAMPLE_RATE
            assert wf.getsampwidth() == 3

    # Verify native .flp header & AST-valid .pyscript & valid .scl
    assert flp_p.read_bytes()[:4] == b"FLhd"
    ast.parse(py_p.read_text(encoding="utf-8"))
    scl_text = scl_p.read_text(encoding="utf-8")
    assert "12" in scl_text and "2/1" in scl_text

    # Verify SHA-256 hash in receipt matches master on disk
    receipt = json.loads(receipt_p.read_text(encoding="utf-8"))
    digest = hashlib.sha256(master.read_bytes()).hexdigest()
    assert receipt["hashes"]["master_wav_sha256"] == digest


def test_arrangement_sections_and_timbral_contrast(cosmic_house_artifacts: Dict[str, Any]) -> None:
    res = cosmic_house_artifacts
    stems = res["stems"]

    beat_s = int(round((60.0 / DEFAULT_BPM) * SAMPLE_RATE))
    bar_s = 4 * beat_s

    kick, _ = load_wav_stereo(stems["01_Kick_Cosmic_49Hz.wav"])
    bass, _ = load_wav_stereo(stems["02_Syncopated_Cosmic_Bass.wav"])
    arp, _ = load_wav_stereo(stems["03_Retro_Futuristic_Arp.wav"])
    keys, _ = load_wav_stereo(stems["04_Airy_Keys_Rhodes.wav"])
    pads, _ = load_wav_stereo(stems["05_Subtle_Cosmic_Pads.wav"])
    gtr, _ = load_wav_stereo(stems["06_Filtered_Disco_Guitars.wav"])
    lead, _ = load_wav_stereo(stems["07_Swirling_Analog_Lead.wav"])
    perc, _ = load_wav_stereo(stems["08_Dynamic_Percussion.wav"])

    # 1) Opens with pulsating 4-on-the-floor kicks, syncopated bass, retro synth arps (Bars 1-16)
    assert _rms_dbfs(kick, 0, 16 * bar_s) > -24.0
    assert _rms_dbfs(bass, 0, 16 * bar_s) > -26.0
    assert _rms_dbfs(arp, 0, 16 * bar_s) > -30.0

    # 2) Verses float on airy keys and subtle pads (Bars 17-24, 45-52) with kick stripped out
    assert _rms_dbfs(keys, 16 * bar_s, 24 * bar_s) > -30.0
    assert _rms_dbfs(pads, 16 * bar_s, 24 * bar_s) > -32.0
    assert _rms_dbfs(kick, 16 * bar_s + 1000, 24 * bar_s - 1000) < -70.0
    assert _rms_dbfs(keys, 44 * bar_s, 52 * bar_s) > -30.0

    # 3) Filtered disco guitars accent Pre-Chorus 1 & Pre-Chorus 2
    assert _rms_dbfs(gtr, 24 * bar_s, 32 * bar_s) > -33.0
    assert _rms_dbfs(gtr, 52 * bar_s, 60 * bar_s) > -33.0
    assert _rms_dbfs(gtr, 24 * bar_s, 32 * bar_s) > _rms_dbfs(gtr, 16 * bar_s + 2000, 24 * bar_s - 2000) + 25.0

    # 4) Drops unleash swirling analog leads and dynamic percussion
    assert _rms_dbfs(lead, 32 * bar_s, 44 * bar_s) > -31.5
    assert _rms_dbfs(perc, 32 * bar_s, 44 * bar_s) > -28.0
    assert _rms_dbfs(lead, 60 * bar_s, 63 * bar_s) > -31.5
    assert _rms_dbfs(lead, 16 * bar_s + 2000, 24 * bar_s - 2000) < -70.0


def test_midi_structure_and_false_drop_bar60(cosmic_house_artifacts: Dict[str, Any]) -> None:
    res = cosmic_house_artifacts
    mid = mido.MidiFile(res["midi_file"])
    assert mid.type == 1
    assert mid.ticks_per_beat == 480

    tracks = _abs_ticks_per_track(mid)
    markers = [msg.text for _t, msg in tracks["Cosmic House 122 Conductor"] if msg.type == "marker"]
    assert len(markers) == 7

    # Bar 60 beats 3-4 exact tick window
    bar_ticks = 4 * 480
    fd_t0 = 59 * bar_ticks + 2 * 480
    fd_t1 = 60 * bar_ticks

    for drum_bass_track in ("01_Kick_49Hz", "02_Syncopated_Bass", "08_Dynamic_Percussion"):
        note_ons = [
            t
            for t, msg in tracks[drum_bass_track]
            if msg.type == "note_on" and msg.velocity > 0 and fd_t0 <= t < fd_t1
        ]
        assert note_ons == [], f"Expected zero note_on events in Bar 60 beats 3-4 for {drum_bass_track}"

    # Verify Lead track enters Drops cleanly (Bars 33..44 and Bars 61..64)
    lead_note_ticks = [t for t, msg in tracks["07_Swirling_Analog_Lead"] if msg.type == "note_on" and msg.velocity > 0]
    assert any(32 * bar_ticks <= t < 44 * bar_ticks for t in lead_note_ticks)
    assert any(60 * bar_ticks <= t < 64 * bar_ticks for t in lead_note_ticks)


def test_false_drop_audio_living_exit_zero_crackle_and_rubin_gate(cosmic_house_artifacts: Dict[str, Any]) -> None:
    res = cosmic_house_artifacts
    beat_s = int(round((60.0 / DEFAULT_BPM) * SAMPLE_RATE))
    bar_s = 4 * beat_s

    kick, _ = load_wav_stereo(res["stems"]["01_Kick_Cosmic_49Hz.wav"])
    perc, _ = load_wav_stereo(res["stems"]["08_Dynamic_Percussion.wav"])
    master, _ = load_wav_stereo(res["master_wav"])

    # Bar 60 beats 3-4 interior window (allow 20 ms ramp tolerance)
    w0 = 59 * bar_s + 2 * beat_s + int(0.02 * SAMPLE_RATE)
    w1 = 60 * bar_s - int(0.02 * SAMPLE_RATE)
    assert _rms_dbfs(kick, w0, w1) < -60.0
    assert _rms_dbfs(perc, w0, w1) < -60.0
    assert _rms_dbfs(master, w0, w1) > -62.0  # Analog tape bed + dub echo remains alive!

    # Living Exit terminates smoothly at zero (zero rectangular cut)
    assert float(np.max(np.abs(master[-4:]))) < 1e-4

    # Zero-Crackle Audits
    for key in ("02_Syncopated_Cosmic_Bass", "07_Swirling_Analog_Lead"):
        zc = res["zero_crackle_audits"][key]
        assert zc["zero_crackle_passed"] is True
        assert zc["max_abs_d1"] <= 0.015
        assert zc["max_abs_d2"] <= 0.005

    # Rubin Acoustic Gate
    rg = res["rubin_gate"]
    assert rg["is_pure_bone"] is True
    assert rg["crest_factor_db"] >= 8.5
    assert rg["spectral_flatness_sfm"] < 0.15
    assert rg["low_end_phase_coherence"] >= 0.95
    assert res["mastering"]["true_peak_dbtp_after"] <= -0.45

    if res["rubin_external_linter"].get("status") not in ("SKIPPED_NOT_INSTALLED",):
        assert res["rubin_external_linter"]["status"] == "PASSED"
        assert res["rubin_external_linter"]["wiener_sfm_500_5000hz"] < 0.35

    # Ensure Python 3.14 temp-elision did not attenuate stems in memory before WAV/telemetry
    telemetry = res["arrangement_telemetry"]
    assert telemetry["verse_1_keys_rms_dbfs"] > -30.0
    assert telemetry["pre_chorus_1_guitar_rms_dbfs"] > -33.0
    assert telemetry["drop_1_lead_rms_dbfs"] > -31.5
    assert telemetry["drop_1_perc_rms_dbfs"] > -28.0


def test_arrangement_template_and_mcp_tool(tmp_path: Path) -> None:
    assert "cosmic_house_64" in ARRANGEMENT_TEMPLATES
    tpl = ARRANGEMENT_TEMPLATES["cosmic_house_64"]
    assert sum(s["bars"] for s in tpl["sections"]) == 64

    mcp_dir = tmp_path / "mcp_cosmic"
    try:
        res = mcp_server.fl_produce_cosmic_house_122(
            total_bars=16,
            bpm=122.0,
            output_dir=str(mcp_dir),
            deploy_fl_assets=False,
        )
        assert res["status"] == "SUCCESS"
        assert Path(res["master_wav"]).exists()
        assert res["rubin_gate"]["is_pure_bone"] is True
    finally:
        shutil.rmtree(mcp_dir, ignore_errors=True)
