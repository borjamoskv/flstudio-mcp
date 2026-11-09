"""Negative controls for evidence gates; numerical fixtures do not claim real execution."""

import copy
import json
import math
import os
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).absolute().parents[1]))
from scripts import real_io_verifier as verifier  # noqa: E402
from scripts import fl_native_plugin_reverse_engine as catalog  # noqa: E402


@pytest.fixture
def reference():
    return next(verifier.stimuli())[1]


def test_fixed_mathematical_gain_and_repeat(reference):
    output = (reference * 10 ** (-2.4 / 20)).astype("<f4")
    result = verifier.compare_case(reference, output, output.copy(), expected_db=-2.4)
    assert result["passed"]
    assert result["window_max_abs_error"] < 1e-6
    assert result["sample_alignment"] == 0
    assert result["full_stream_identity_verified"] is False


@pytest.mark.parametrize(
    "failure",
    ["wrong_gain", "wrong_input", "missing_repeat", "shift", "clipping", "zero_input"],
)
def test_wrong_or_missing_numerical_evidence_fails(reference, failure):
    output = reference.copy()
    second = output.copy()
    if failure == "wrong_gain":
        output *= 0.5
        second = output.copy()
    elif failure == "wrong_input":
        reference = np.roll(reference, 1000, axis=0)
    elif failure == "missing_repeat":
        second[80000, 0] += 0.01
    elif failure == "shift":
        output = np.roll(output, 24, axis=0)
        second = output.copy()
    elif failure == "clipping":
        output[0] = 1.1
        second = output.copy()
    else:
        reference[:] = 0
        output[:] = 0
        second[:] = 0
    assert verifier.compare_case(reference, output, second)["passed"] is False


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_nonfinite_output_cannot_be_verified(reference, bad):
    output = reference.copy()
    output[80000, 0] = bad
    with pytest.raises(ValueError, match="NONFINITE"):
        verifier.compare_case(reference, output, reference)


def test_transients_remain_outside_verified_claim(reference):
    output = reference.copy()
    output[48010, 0] += 0.01
    result = verifier.compare_case(reference, output, output)
    assert result["passed"] is True  # Only the preregistered stable window.
    assert result["full_stream_max_abs_error"] > 0.009
    assert result["full_stream_identity_verified"] is False


def test_truncated_or_absent_audio_is_rejected(tmp_path):
    path = tmp_path / "audio.f32"
    np.zeros((128, 2), dtype="<f4").tofile(path)
    with pytest.raises(ValueError, match="TRUNCATED"):
        verifier.read_audio(path)
    with pytest.raises(FileNotFoundError):
        verifier.read_audio(tmp_path / "missing.f32")


def minimal_bundle(root, report=None):
    root.mkdir()
    report = report or {
        "mode": "real_installed_io",
        "plugins": [],
        "applications": [],
        "full_algorithms_verified": 0,
        "verified_scoped_cases": 0,
    }
    verifier.write_json(root / "contract.json", verifier.CONTRACT)
    verifier.write_json(root / "report.json", report)
    verifier.write_json(root / "manifest.json", verifier.evidence_manifest(root))
    return root


def test_claimed_positive_count_without_evidence_is_rejected(tmp_path):
    root = minimal_bundle(tmp_path / "bundle")
    report = json.loads((root / "report.json").read_text())
    report["verified_scoped_cases"] = 1296000
    verifier.write_json(root / "report.json", report)
    verifier.write_json(root / "manifest.json", verifier.evidence_manifest(root))
    with pytest.raises(ValueError, match="MISCOUNTED"):
        verifier.check_bundle(root)


def test_metadata_alone_cannot_verify_application(tmp_path):
    root = minimal_bundle(
        tmp_path / "bundle",
        {
            "mode": "real_installed_io",
            "plugins": [],
            "full_algorithms_verified": 0,
            "verified_scoped_cases": 1,
            "applications": [
                {
                    "target": "grok_local_cli",
                    "real_verification": True,
                    "scope": "local_version_stdout_only",
                    "binary": "/not/a/real/application",
                    "binary_sha256": "0" * 64,
                    "observed_stdout": [verifier.GROK_EXPECTED] * 2,
                }
            ],
        },
    )
    with pytest.raises((ValueError, OSError)):
        verifier.check_bundle(root)


def test_hash_or_missing_artifact_invalidates_bundle(tmp_path):
    root = minimal_bundle(tmp_path / "bundle")
    (root / "report.json").write_text("{}")
    with pytest.raises(ValueError, match="HASH"):
        verifier.check_bundle(root)
    (root / "report.json").unlink()
    with pytest.raises(FileNotFoundError):
        verifier.check_bundle(root)


@pytest.mark.parametrize("mutation", ["simulation", "wide_scope", "different_window"])
def test_simulated_or_expanded_contract_rejected(tmp_path, mutation):
    root = minimal_bundle(tmp_path / "bundle")
    contract = copy.deepcopy(verifier.CONTRACT)
    if mutation == "simulation":
        report = json.loads((root / "report.json").read_text())
        report["mode"] = "simulation"
        verifier.write_json(root / "report.json", report)
    elif mutation == "wide_scope":
        contract["full_stream_equality_claimed"] = True
    else:
        contract["comparison_window_frames"] = [0, 1]
    verifier.write_json(root / "contract.json", contract)
    verifier.write_json(root / "manifest.json", verifier.evidence_manifest(root))
    with pytest.raises(ValueError, match="CONTRACT"):
        verifier.check_bundle(root)


def test_manifest_paths_cannot_escape_bundle(tmp_path):
    root = minimal_bundle(tmp_path / "bundle")
    verifier.write_json(
        root / "manifest.json", {"../secret": {"bytes": 0, "sha256": "0" * 64}}
    )
    with pytest.raises(ValueError, match="PATH"):
        verifier.check_bundle(root)


def test_existing_output_directory_is_never_reused(tmp_path):
    marker = tmp_path / "stale.wav"
    marker.write_bytes(b"old output")
    with pytest.raises(FileExistsError):
        verifier.run_suite(tmp_path)
    assert marker.read_bytes() == b"old output"


def test_failed_process_and_timeout_are_retained(tmp_path):
    with pytest.raises(RuntimeError):
        verifier.run_command(
            [sys.executable, "-c", "raise SystemExit(7)"], tmp_path, "failed"
        )
    assert json.loads((tmp_path / "failed.command.json").read_text())["exit_code"] == 7
    with pytest.raises(RuntimeError):
        verifier.run_command(
            [sys.executable, "-c", "import time; time.sleep(1)"],
            tmp_path,
            "timeout",
            timeout=0.01,
        )
    assert (
        json.loads((tmp_path / "timeout.command.json").read_text())["timed_out"] is True
    )


def test_missing_plugin_has_no_fallback():
    target = dict(verifier.TARGETS[0], bundle="/missing/plugin.component")
    with pytest.raises(FileNotFoundError):
        verifier.installed_identity(target)


def test_fake_host_log_cannot_attest_loaded_plugin():
    with pytest.raises(ValueError, match="NOT_LOADED"):
        verifier.validate_host_log(
            verifier.parse_log("COMPONENT\tMy plugin\n"),
            verifier.TARGETS[0],
            {"binary": "/real/plugin.bin"},
            0,
            0.5,
        )


def test_catalog_invalid_bundle_fails_without_promoting_algorithm(tmp_path):
    result = catalog.scan_native_fl_plugins(
        False, real_io_evidence_dir=str(tmp_path / "absent")
    )
    assert result["status"] == "FAIL_INVALID_IO_EVIDENCE"
    assert result["real_io_evidence"]["status"] == "BLOCKED"
    assert result["verified"] is False
    assert result["algorithms_verified"] == 0


@pytest.mark.skipif(
    not os.environ.get("REAL_IO_EVIDENCE_DIR"),
    reason="Requires retained original-plugin execution evidence",
)
def test_retained_real_bundle_and_catalog_are_scoped():
    root = Path(os.environ["REAL_IO_EVIDENCE_DIR"])
    result = verifier.check_bundle(root)
    assert result["verified_plugin_cases"] > 0
    assert result["verified_application_cases"] == 1
    assert result["full_algorithms_verified"] == 0
    catalog_result = catalog.scan_native_fl_plugins(
        False, real_io_evidence_dir=str(root)
    )
    assert catalog_result["verified"] is False
    assert catalog_result["algorithms_verified"] == 0
    assert (
        catalog_result["real_io_evidence"]["verified_cases"] == result["verified_cases"]
    )


def test_nonnumeric_parameter_readback_is_not_attestation():
    target = verifier.TARGETS[0]
    parsed = {
        "images": ["/plugin.bin"],
        "sets": {
            "0": {"readback": 0.0},
            "1": {"readback": math.nan},
            "2": {"readback": 1.0},
        },
        "labels": {"1": "0.00 dB"},
        "bypass": ["0"],
        "offline_status": ["0"],
    }
    with pytest.raises(ValueError, match="READBACK"):
        verifier.validate_host_log(parsed, target, {"binary": "/plugin.bin"}, 0, 0.5)


def test_session_intersection_never_clears_an_observed_failure(tmp_path, monkeypatch):
    # Only exercise aggregation policy; this mocked integrity check does not claim a real run.
    monkeypatch.setattr(verifier, "check_bundle", lambda _: {})
    paths = []
    for index, passed in enumerate([False, True]):
        root = tmp_path / str(index)
        root.mkdir()
        report = {
            "plugins": [
                {
                    "target": "plugin",
                    "cases": [
                        {
                            "scope": "gain",
                            "stimulus": "noise",
                            "real_verification": passed,
                        }
                    ],
                }
            ],
            "applications": [],
        }
        verifier.write_json(root / "report.json", report)
        verifier.write_json(root / "manifest.json", {})
        paths.append(root)
    result = verifier.compare_sessions(paths)
    assert result["cases"][0]["session_results"] == [False, True]
    assert result["cases"][0]["real_verification"] is False
    assert result["requested_cases_passed"] is False


def test_copied_bundle_cannot_count_as_second_independent_session(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(verifier, "check_bundle", lambda _: {})
    paths = [minimal_bundle(tmp_path / str(index)) for index in range(2)]
    with pytest.raises(ValueError, match="DUPLICATE_RUN_EVIDENCE"):
        verifier.compare_sessions(paths)
    with pytest.raises(ValueError, match="DUPLICATE_SESSION"):
        verifier.compare_sessions([paths[0], paths[0]])


def test_cli_missing_bundle_fails_and_help_is_available(tmp_path, capsys):
    assert verifier.main(["--check-bundle", str(tmp_path / "absent")]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"
    with pytest.raises(SystemExit) as help_exit:
        verifier.main(["--help"])
    assert help_exit.value.code == 0


def test_mcp_existing_directory_blocks_without_overwrite(tmp_path):
    import mcp_server

    marker = tmp_path / "preserve.txt"
    marker.write_text("original")
    result = mcp_server.fl_verify_installed_io(str(tmp_path))
    assert result["status"] == "BLOCKED"
    assert result["requested_cases_passed"] is False
    assert marker.read_text() == "original"


@pytest.mark.skipif(
    not os.environ.get("REAL_IO_HISTORY_DIR"),
    reason="Requires two retained original-plugin sessions",
)
def test_history_preserves_all_observed_failures():
    root = Path(os.environ["REAL_IO_HISTORY_DIR"])
    result = verifier.check_evidence_path(root)
    assert result["policy"] == "INTERSECTION_OF_ALL_RETAINED_SESSIONS"
    assert result["full_algorithms_verified"] == 0
    assert result["requested_cases_passed"] is False
    assert any(
        c["status"] == "BLOCKED" and any(c["session_results"]) for c in result["cases"]
    )
    report = catalog.scan_native_fl_plugins(False, real_io_evidence_dir=str(root))
    assert report["real_io_evidence"]["verified_cases"] == result["verified_cases"]
    assert report["algorithms_verified"] == 0
    assert report["verified"] is False
