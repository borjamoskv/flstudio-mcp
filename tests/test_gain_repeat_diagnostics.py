"""Diagnose repeat failures without trimming samples or relaxing acceptance."""

import json
import math
import os
from pathlib import Path
import shutil
import sys

import pytest

sys.path.insert(0, str(Path(__file__).absolute().parents[1]))
from scripts import real_io_verifier as verifier  # noqa: E402


@pytest.fixture
def signal():
    return next(verifier.stimuli())[1]


def test_tail_noise_remains_rejected_and_is_localized(signal):
    a = signal.copy()
    b = a.copy()
    b[192000:, :] = 0.005
    diag = verifier.diagnose_repeat(signal, a, b)
    assert diag["classification"] == "LATE_REPEAT_DIVERGENCE"
    assert diag["first_divergent_frame"] == 192000
    assert diag["last_divergent_frame"] == 239999
    assert diag["divergent_frames"] == 48000
    assert diag["input_zero_fraction_on_divergence"] == 1
    assert diag["regions"]["stable_window"]["max_abs_repeat_error"] == 0
    assert diag["regions"]["settled_tail"]["max_abs_repeat_error"] > 0.004
    assert diag["repeat_passed"] is False
    assert verifier.compare_case(signal, a, b)["passed"] is False


def test_active_divergence_is_not_relabelled_as_tail(signal):
    other = signal.copy()
    other[80000, 0] += 0.01
    diag = verifier.diagnose_repeat(signal, signal, other)
    assert diag["classification"] == "ACTIVE_REPEAT_DIVERGENCE"
    assert diag["first_divergent_frame"] == 80000
    assert diag["repeat_passed"] is False


def test_equal_repeats_do_not_claim_full_dsp_equivalence(signal):
    diag = verifier.diagnose_repeat(signal, signal, signal.copy())
    assert diag["classification"] == "REPEAT_MATCH"
    assert diag["repeat_passed"] is True
    assert diag["first_divergent_frame"] is None
    assert diag["cause_attribution"] == "NOT_INFERRED_FROM_WAVEFORM_ALONE"
    assert "license_status" not in diag


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_nonfinite_repeat_cannot_be_diagnosed_as_match(signal, bad):
    b = signal.copy()
    b[100, 1] = bad
    with pytest.raises(ValueError, match="NONFINITE"):
        verifier.diagnose_repeat(signal, signal, b)


def test_missing_frames_are_not_silently_dropped(signal):
    with pytest.raises(ValueError, match="SHAPE"):
        verifier.diagnose_repeat(signal, signal, signal[:-1])


def test_original_tolerances_are_unchanged():
    assert verifier.CONTRACT["max_abs_tolerance"] == 1e-6
    assert verifier.CONTRACT["repeat_max_abs_tolerance"] == 1e-7
    assert verifier.WINDOW == (60000, 132000)


@pytest.mark.skipif(
    not os.environ.get("GAIN_BASELINE_HISTORY"),
    reason="Needs original retained failure evidence",
)
def test_all_four_original_failed_cases_are_recomputed_and_stay_blocked():
    root = Path(os.environ["GAIN_BASELINE_HISTORY"])
    total = 0
    for session in ("sesion_01", "sesion_02"):
        report = json.loads((root / session / "report.json").read_text())
        for plugin in report["plugins"]:
            for case in plugin["cases"]:
                if case["real_verification"] or "gain" not in case["scope"]:
                    continue
                folder = root / session / plugin["target"]
                x = verifier.read_audio(
                    root / session / "inputs" / (case["stimulus"] + ".f32")
                )
                a = verifier.read_audio(folder / case["first_output"])
                b = verifier.read_audio(folder / case["second_output"])
                diag = verifier.diagnose_repeat(x, a, b)
                assert diag["classification"] == "LATE_REPEAT_DIVERGENCE"
                assert diag["repeat_passed"] is False
                assert (
                    diag["max_abs_repeat_error"]
                    == case["metrics"]["repeat_full_stream_max_abs_error"]
                )
                assert diag["first_divergent_frame"] in (143872, 192000)
                total += 1
    assert total == 4


@pytest.mark.skipif(
    not os.environ.get("GAIN_DIAGNOSTIC_EVIDENCE_DIR"),
    reason="Needs a retained run with recomputable repeat diagnostics",
)
@pytest.mark.parametrize("mutation", ["classification", "error"])
def test_fabricated_diagnostics_are_rejected_even_with_rehashed_report(
    tmp_path, mutation
):
    source = Path(os.environ["GAIN_DIAGNOSTIC_EVIDENCE_DIR"])

    def copy_artifact(src, dst):
        # JSON is copied before mutation. Large immutable audio files may be linked.
        return (
            shutil.copy2(src, dst) if str(src).endswith(".json") else os.link(src, dst)
        )

    root = tmp_path / "evidence"
    shutil.copytree(source, root, copy_function=copy_artifact)
    report = json.loads((root / "report.json").read_text())
    diag = report["plugins"][0]["cases"][0]["repeat_diagnostics"]
    if mutation == "classification":
        diag["classification"] = "UNSUPPORTED_ASSERTION"
    else:
        diag["max_abs_repeat_error"] += 0.1
    verifier.write_json(root / "report.json", report)
    verifier.write_json(root / "manifest.json", verifier.evidence_manifest(root))
    with pytest.raises(ValueError, match="REPEAT_DIAGNOSTICS_MISMATCH"):
        verifier.check_bundle(root)
