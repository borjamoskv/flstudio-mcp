"""Isolated evidence controls: no DAW, MIDI or production artifact writes."""

import math
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).absolute().parents[1]))
from scripts import fl_native_plugin_reverse_engine as plugins
from swarm1000.council.bft_1000_consensus import Bft1000ConsensusEngine


@pytest.mark.parametrize("empty", [False, True])
def test_absent_or_empty_installation_is_not_full_coverage(
    tmp_path, monkeypatch, empty
):
    root = tmp_path / "plugins"
    if empty:
        (root / "Generators").mkdir(parents=True)
        (root / "Effects").mkdir()
    monkeypatch.setattr(plugins, "FL_APP_PATH", str(root))
    report = plugins.scan_native_fl_plugins(write_artifacts=False)
    assert report["coverage_percent"] != 100
    assert report["verified"] is False
    assert report["inventory_status"] == "UNAVAILABLE"


def test_plugin_catalog_match_is_only_inventory(tmp_path):
    (tmp_path / "Generators" / next(iter(plugins.GENERATORS_RAE_SPEC))).mkdir(
        parents=True
    )
    (tmp_path / "Effects" / next(iter(plugins.EFFECTS_RAE_SPEC))).mkdir(parents=True)
    report = plugins.scan_native_fl_plugins(False, plugins_root=str(tmp_path))
    assert report["catalog_coverage_percent"] == 100
    assert report["verified"] is False
    assert report["algorithms_verified"] == 0
    assert report["coverage_percent"] is None


def test_unknown_plugin_reduces_catalog_coverage(tmp_path):
    (tmp_path / "Generators" / next(iter(plugins.GENERATORS_RAE_SPEC))).mkdir(
        parents=True
    )
    (tmp_path / "Effects" / "UNLISTED").mkdir(parents=True)
    report = plugins.scan_native_fl_plugins(False, plugins_root=str(tmp_path))
    assert report["catalog_coverage_percent"] == 50
    assert report["missing_effects"] == ["UNLISTED"]
    assert report["verified"] is False


def test_catalog_simulation_has_no_detected_plugins():
    report = plugins.scan_native_fl_plugins(False, simulation=True)
    assert report["mode"] == "simulation"
    assert report["detected_plugins"] == 0
    assert report["verified"] is False


def test_duplicate_identity_cannot_trigger_a_veto():
    engine = Bft1000ConsensusEngine()
    vote = engine.simulate_1000_agent_votes(0.65, 16, True)[600]
    with pytest.raises(ValueError):
        engine.resolve_consensus([vote] * 130, simulation=True)


@pytest.mark.parametrize(
    "corruption", ["missing", "duplicate", "division", "nan", "unknown_action"]
)
def test_invalid_votes_fail_closed(corruption):
    engine = Bft1000ConsensusEngine()
    votes = engine.simulate_1000_agent_votes(0.65, 16, True)
    if corruption == "missing":
        votes.pop()
    elif corruption == "duplicate":
        votes[-1] = votes[0]
    elif corruption == "division":
        votes[0] = replace(votes[0], division_id=4)
    elif corruption == "nan":
        votes[0] = replace(votes[0], confidence=math.nan)
    else:
        votes[0] = replace(votes[0], proposed_action=999)
    with pytest.raises(ValueError):
        engine.resolve_consensus(votes, simulation=True)


def test_simulated_votes_stay_simulated():
    engine = Bft1000ConsensusEngine()
    _, report = engine.resolve_consensus(
        engine.simulate_1000_agent_votes(0.65, 16, True), simulation=True
    )
    assert report["mode"] == "simulation"
    assert report["real_verification"] is False
    assert report["verified_agents"] == 0


def good_metrics():
    return dict(
        avg_write_ns=100,
        avg_read_ns=100,
        avg_consensus_ms=0.5,
        p99_consensus_ms=1,
        dsp_processing_ms=100,
        phase_coherence=0.99,
        readback_matches=True,
        audio_finite=True,
    )


@pytest.mark.parametrize(
    "field,bad",
    [
        ("avg_write_ns", 500),
        ("avg_read_ns", 500),
        ("avg_consensus_ms", 2),
        ("p99_consensus_ms", 2),
        ("dsp_processing_ms", 10000),
        ("phase_coherence", -0.1826),
        ("phase_coherence", 0.95),
        ("phase_coherence", 1.1),
        ("readback_matches", False),
        ("audio_finite", False),
    ],
)
def test_benchmark_thresholds_fail(field, bad):
    from swarm1000.benchmarks.benchmark_1000_agents import evaluate_metrics

    metrics = good_metrics()
    assert evaluate_metrics(metrics)["passed"] is True
    metrics[field] = bad
    assert evaluate_metrics(metrics)["passed"] is False


@pytest.mark.parametrize("bad", [None, math.nan, math.inf, -1, "100", True])
def test_bad_measurements_fail(bad):
    from swarm1000.benchmarks.benchmark_1000_agents import evaluate_metrics

    metrics = good_metrics()
    metrics["avg_read_ns"] = bad
    assert evaluate_metrics(metrics)["passed"] is False


def test_missing_metrics_and_real_benchmark_evidence_fail():
    from swarm1000.benchmarks.benchmark_1000_agents import (
        evaluate_metrics,
        run_benchmark,
    )

    assert evaluate_metrics({})["passed"] is False
    report = run_benchmark()
    assert report["passed"] is False
    assert report["status"] == "FAIL_MISSING_EVIDENCE"
    assert report["real_verification"] is False


def test_dsp_regression_is_failed_not_certified():
    from swarm1000.benchmarks.benchmark_1000_agents import run_benchmark

    report = run_benchmark(simulation=True)
    assert report["metrics"]["phase_coherence"] < 0.95
    assert report["checks"]["phase_coherence"] is False
    assert report["status"] == "SIMULATION_FAILED"
    assert report["real_verification"] is False
    assert report["verified_agents"] == 0


def test_plugin_exports_preserve_failure(tmp_path, monkeypatch):
    import json

    monkeypatch.setattr(plugins, "OUTPUT_JSON_PATH", str(tmp_path / "result.json"))
    monkeypatch.setattr(plugins, "OUTPUT_MD_PATH", str(tmp_path / "result.md"))
    report = plugins.scan_native_fl_plugins(
        True, plugins_root=str(tmp_path / "missing")
    )
    exported = json.loads((tmp_path / "result.json").read_text())
    assert exported["status"] == "FAIL_MISSING_EVIDENCE"
    assert exported["verified"] is False
    assert "algoritmos verificados: 0" in (tmp_path / "result.md").read_text()
    assert report["coverage_percent"] is None


def test_plugin_cli_scope_and_failure(tmp_path, capsys):
    assert plugins.main(["--plugins-root", str(tmp_path)]) == 1
    assert plugins.main(["--plugins-root", str(tmp_path), "--inventory-only"]) == 1
    (tmp_path / "Generators" / next(iter(plugins.GENERATORS_RAE_SPEC))).mkdir(
        parents=True
    )
    (tmp_path / "Effects" / next(iter(plugins.EFFECTS_RAE_SPEC))).mkdir(parents=True)
    assert plugins.main(["--plugins-root", str(tmp_path)]) == 1
    assert plugins.main(["--plugins-root", str(tmp_path), "--inventory-only"]) == 0
    capsys.readouterr()


def test_swarm_cli_missing_evidence_exits_nonzero(tmp_path):
    import json
    import subprocess

    script = (
        Path(__file__).absolute().parents[1]
        / "swarm1000/benchmarks/benchmark_1000_agents.py"
    )
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["status"] == "FAIL_MISSING_EVIDENCE"
    assert not list(tmp_path.iterdir())


def test_non_simulated_votes_do_not_establish_agents():
    engine = Bft1000ConsensusEngine()
    votes = [
        replace(v, source="claimed_real")
        for v in engine.simulate_1000_agent_votes(0.9, 1, False)
    ]
    with pytest.raises(ValueError, match="MISSING_EVIDENCE"):
        engine.resolve_consensus(votes)


def test_generated_votes_also_require_explicit_simulation():
    engine = Bft1000ConsensusEngine()
    votes = engine.simulate_1000_agent_votes(0.9, 1, False)
    with pytest.raises(ValueError, match="MISSING_EVIDENCE"):
        engine.resolve_consensus(votes)
