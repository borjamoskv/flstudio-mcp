#!/usr/bin/env python3
"""Bounded local I/O verification of installed software, with retained evidence.

Positive claims cover only preregistered cases. A local evidence bundle is not a
hardware attestation, a DSP reconstruction, or proof of untested software.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import plistlib
import re
import subprocess
import sys
import time

import numpy as np

SOURCE = Path(__file__).with_name("native") / "au_probe.c"
SANDBOX = "(version 1)(allow default)(deny network*)"
SAMPLE_RATE = 48000
WINDOW = (60000, 132000)  # 1.25..2.75 s, fixed before the confirmation run.
CONTRACT = {
    "schema_version": 1,
    "mode": "real_installed_io",
    "sample_rate": SAMPLE_RATE,
    "channels": 2,
    "frames": 240000,
    "block_frames": 256,
    "signal_interval_frames": [48000, 144000],
    "comparison_window_frames": list(WINDOW),
    "max_abs_tolerance": 1e-6,
    "repeat_max_abs_tolerance": 1e-7,
    "gain_parameter": {
        "id": 1,
        "baseline_normalized": 0.5,
        "test_normalized": 0.45,
        "expected_db": -2.4,
    },
    "target_profiles": {
        "mvibratomb_au": {
            "parameter_2_name": "Width (Globals)",
            "parameter_2_value": 1.0,
        },
        "mflangermb_au": {
            "parameter_2_name": "Saturation (Globals)",
            "parameter_2_value": 0.0,
        },
    },
    "gain_reference": "baseline plugin output * 10 ** (-2.4 / 20)",
    "bypass_reference": "original input, no alignment or fitted gain",
    "full_stream_equality_claimed": False,
    "limitations": [
        "STEADY_WINDOW_ONLY",
        "AUDIO_UNIT_VARIANT_ONLY",
        "NO_RECONSTRUCTED_DSP_EQUIVALENCE",
        "NO_HARDWARE_ATTESTATION",
    ],
}
TARGETS = [
    {
        "id": "mvibratomb_au",
        "bundle": "/Library/Audio/Plug-Ins/Components/MVibratoMB.component",
        "type": "aumf",
        "subtype": "MmVi",
        "manufacturer": "Meld",
    },
    {
        "id": "mflangermb_au",
        "bundle": "/Library/Audio/Plug-Ins/Components/MFlangerMB.component",
        "type": "aumf",
        "subtype": "MMBF",
        "manufacturer": "Meld",
    },
]
GROK_PATH = Path.home() / ".grok/downloads/grok-macos-aarch64"
GROK_EXPECTED = "grok 0.2.39 (55a20b703aa)\n"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def run_command(argv, directory, label, timeout=45):
    """No shell, bounded process and explicit raw logs for every invocation."""
    argv = [str(a) for a in argv]
    start = time.monotonic()
    try:
        process = subprocess.run(
            argv, cwd=directory, capture_output=True, timeout=timeout
        )
        record = {"argv": argv, "exit_code": process.returncode, "timed_out": False}
        stdout, stderr = process.stdout, process.stderr
    except subprocess.TimeoutExpired as exc:
        record = {"argv": argv, "exit_code": None, "timed_out": True}
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
    record["elapsed_sec"] = time.monotonic() - start
    record["cwd"] = str(directory)
    for kind, data in [("stdout", stdout), ("stderr", stderr)]:
        filename = f"{label}.{kind}.txt"
        (directory / filename).write_bytes(data)
        record[kind + "_file"] = filename
        record[kind + "_sha256"] = digest(directory / filename)
    write_json(directory / f"{label}.command.json", record)
    if record["exit_code"] != 0:
        raise RuntimeError(
            f"{label}: process failed or timed out; see retained command/log files"
        )
    return stdout.decode("utf-8", errors="replace")


def parse_log(text):
    result = {"images": [], "sets": {}, "labels": {}, "parameters": {}}
    for row in text.splitlines():
        fields = row.split("\t")
        if fields[0] == "IMAGE" and len(fields) == 2:
            result["images"].append(fields[1])
        elif fields[0] == "SET" and len(fields) == 4:
            result["sets"][fields[1]] = {
                "requested": float(fields[2]),
                "readback": float(fields[3]),
            }
        elif fields[0] == "LABEL" and len(fields) == 3:
            result["labels"][fields[1]] = fields[2]
        elif fields[0] == "PARAM" and len(fields) == 9:
            result["parameters"][fields[1]] = fields[2:]
        elif fields[0] in (
            "COMPONENT",
            "VERSION",
            "BYPASS",
            "OFFLINE_STATUS",
            "LATENCY",
        ):
            result[fields[0].lower()] = fields[1:]
    return result


def installed_identity(target):
    bundle = Path(target["bundle"]).resolve(strict=True)
    metadata_path = bundle / "Contents/Info.plist"
    metadata = plistlib.loads(metadata_path.read_bytes())
    matches = [
        component
        for component in metadata.get("AudioComponents", [])
        if all(
            component.get(k) == target[k] for k in ("type", "subtype", "manufacturer")
        )
    ]
    if len(matches) != 1:
        raise ValueError("COMPONENT_IDENTITY_MISMATCH")
    binary = (bundle / "Contents/MacOS" / metadata["CFBundleExecutable"]).resolve(
        strict=True
    )
    return {
        "bundle": str(bundle),
        "binary": str(binary),
        "binary_sha256": digest(binary),
        "plist_sha256": digest(metadata_path),
        "bundle_id": metadata["CFBundleIdentifier"],
        "version": metadata.get("CFBundleVersion"),
        "component": matches[0],
    }


def stimuli():
    """Independent, deterministic float32 test vectors, identical for every target."""
    from scipy.signal import chirp

    total = CONTRACT["frames"]
    n = 96000
    t = np.arange(n, dtype=np.float64) / SAMPLE_RATE
    vectors = {
        "multitone": np.column_stack(
            (
                0.12 * np.sin(2 * np.pi * 220 * t) + 0.03 * np.sin(2 * np.pi * 997 * t),
                0.10 * np.sin(2 * np.pi * 330 * t)
                + 0.02 * np.sin(2 * np.pi * 1703 * t),
            )
        ),
        "sweep": np.column_stack(
            (
                0.12 * chirp(t, 40, 2, 12000, method="logarithmic"),
                0.09 * chirp(t, 70, 2, 9000, method="logarithmic", phi=90),
            )
        ),
        "noise": np.random.default_rng(20261021).uniform(-0.12, 0.12, (n, 2)),
    }
    for name, body in vectors.items():
        value = np.zeros((total, 2), dtype="<f4")
        value[48000:144000] = body
        yield name, value


def read_audio(path):
    value = np.fromfile(path, dtype="<f4")
    if value.size != CONTRACT["frames"] * 2:
        raise ValueError("MISSING_OR_TRUNCATED_AUDIO_EVIDENCE")
    value = value.reshape(-1, 2)
    if not np.isfinite(value).all():
        raise ValueError("NONFINITE_AUDIO")
    return value


def audio_telemetry(value):
    segment = value[WINDOW[0] : WINDOW[1]].astype(np.float64)
    spectrum = np.abs(np.fft.rfft(segment, axis=0)) ** 2
    frequencies = np.fft.rfftfreq(len(segment), 1 / SAMPLE_RATE)
    total = float(spectrum.sum())
    return {
        "frames": len(value),
        "channels": 2,
        "sample_rate": SAMPLE_RATE,
        "finite": bool(np.isfinite(value).all()),
        "peak": float(np.max(np.abs(value))),
        "clipped_samples": int(np.sum(np.abs(value) >= 1)),
        "window_rms": float(np.sqrt(np.mean(segment**2))),
        "window_spectral_centroid_hz": float(
            (spectrum * frequencies[:, None]).sum() / total
        )
        if total
        else 0.0,
    }


def compare_case(
    reference, first, second, *, expected_db=0.0, tolerance=1e-6, repeat_tolerance=1e-7
):
    """Fixed sample alignment, fixed gain, fixed window. No fitting to observations."""
    if (
        reference.shape != (CONTRACT["frames"], 2)
        or first.shape != reference.shape
        or second.shape != reference.shape
    ):
        raise ValueError("INVALID_AUDIO_SHAPE")
    if not all(np.isfinite(v).all() for v in (reference, first, second)):
        raise ValueError("NONFINITE_AUDIO")
    if not math.isfinite(expected_db) or tolerance <= 0 or repeat_tolerance <= 0:
        raise ValueError("INVALID_COMPARISON_CONTRACT")
    start, end = WINDOW
    reference = reference.astype(np.float64)
    first = first.astype(np.float64)
    second = second.astype(np.float64)
    expected = reference * (10 ** (expected_db / 20))
    error = first[start:end] - expected[start:end]
    repeat = np.max(np.abs(first - second))
    rms = float(np.sqrt(np.mean(reference[start:end] ** 2)))
    result = {
        "window_max_abs_error": float(np.max(np.abs(error))),
        "window_rms_error": float(np.sqrt(np.mean(error**2))),
        "full_stream_max_abs_error": float(np.max(np.abs(first - expected))),
        "repeat_full_stream_max_abs_error": float(repeat),
        "reference_window_rms": rms,
        "expected_gain_db": expected_db,
        "sample_alignment": 0,
        "window_frames": [start, end],
        "tolerance": tolerance,
        "repeat_tolerance": repeat_tolerance,
        "finite": True,
        "clipped_samples": int(
            np.sum(np.abs(first) >= 1) + np.sum(np.abs(second) >= 1)
        ),
        "full_stream_identity_verified": False,
    }
    result["passed"] = bool(
        result["window_max_abs_error"] <= tolerance
        and repeat <= repeat_tolerance
        and rms > 1e-4
        and result["clipped_samples"] == 0
    )
    return result


def diagnose_repeat(input_audio, first, second):
    """Explain failed repeats without modifying samples, windows, or tolerances.

    This locates the observable defect. Waveform statistics alone do not identify
    licensing state, vendor internals, or an error in the host.
    """
    shape = (CONTRACT["frames"], 2)
    if any(value.shape != shape for value in (input_audio, first, second)):
        raise ValueError("INVALID_AUDIO_SHAPE")
    if not all(np.isfinite(value).all() for value in (input_audio, first, second)):
        raise ValueError("NONFINITE_AUDIO")
    a, b = first.astype(np.float64), second.astype(np.float64)
    error = np.max(np.abs(a - b), axis=1)
    tolerance = CONTRACT["repeat_max_abs_tolerance"]
    indices = np.flatnonzero(error > tolerance)
    first_frame = int(indices[0]) if len(indices) else None
    last_frame = int(indices[-1]) if len(indices) else None
    if not len(indices):
        classification = "REPEAT_MATCH"
    elif np.any((indices >= WINDOW[0]) & (indices < WINDOW[1])):
        classification = "ACTIVE_REPEAT_DIVERGENCE"
    elif first_frame >= WINDOW[1]:
        classification = "LATE_REPEAT_DIVERGENCE"
    else:
        classification = "LEADING_OR_TRANSIENT_REPEAT_DIVERGENCE"

    def stats(value):
        return {
            "min": float(value.min()),
            "max": float(value.max()),
            "mean": float(value.mean()),
            "std": float(value.std()),
            "rms": float(np.sqrt(np.mean(value**2))),
        }

    regions = {}
    for name, start, end in [
        ("leading_silence", 0, 48000),
        ("signal", 48000, 144000),
        ("stable_window", WINDOW[0], WINDOW[1]),
        ("trailing_silence", 144000, 240000),
        ("settled_tail", 192000, 240000),
    ]:
        regions[name] = {
            "frames": [start, end],
            "max_abs_repeat_error": float(error[start:end].max()),
            "first_output": stats(a[start:end]),
            "second_output": stats(b[start:end]),
            "input_peak": float(np.max(np.abs(input_audio[start:end]))),
        }
    return {
        "schema_version": 1,
        "classification": classification,
        "repeat_passed": bool(float(error.max()) <= tolerance),
        "tolerance": tolerance,
        "max_abs_repeat_error": float(error.max()),
        "first_divergent_frame": first_frame,
        "last_divergent_frame": last_frame,
        "divergent_frames": len(indices),
        "input_zero_fraction_on_divergence": float(
            np.mean(np.all(input_audio[indices] == 0, axis=1))
        )
        if len(indices)
        else None,
        "regions": regions,
        "cause_attribution": "NOT_INFERRED_FROM_WAVEFORM_ALONE",
    }


def validate_host_log(parsed, target, identity, bypass, output_parameter):
    if identity["binary"] not in parsed["images"]:
        raise ValueError("REQUESTED_PLUGIN_BINARY_NOT_LOADED")
    for key, wanted in [
        ("0", 0.0),
        ("1", output_parameter),
        ("2", CONTRACT["target_profiles"][target["id"]]["parameter_2_value"]),
    ]:
        if (
            key not in parsed["sets"]
            or not math.isfinite(parsed["sets"][key]["readback"])
            or abs(parsed["sets"][key]["readback"] - wanted) > 1e-6
        ):
            raise ValueError("PARAMETER_READBACK_MISMATCH")
    if parsed.get("bypass") != [str(bypass)] or parsed.get("offline_status") != ["0"]:
        raise ValueError("RENDER_MODE_NOT_CONFIRMED")
    expected_label = -2.4 if output_parameter == 0.45 else 0.0
    label = parsed["labels"].get("1", "")
    if (
        not re.fullmatch(r"[-+]?\d+(?:\.\d+)? dB", label)
        or abs(float(label.split()[0]) - expected_label) > 0.001
    ):
        raise ValueError("GAIN_PARAMETER_LABEL_DOES_NOT_MATCH_CONTRACT")


def render(
    host,
    target,
    identity,
    input_path,
    folder,
    name,
    bypass,
    output_parameter,
    state=None,
):
    output = folder / f"{name}.f32"
    args = [
        host,
        target["type"],
        target["subtype"],
        target["manufacturer"],
        "render",
        input_path,
        output,
        str(bypass),
        "0=0",
        f"1={output_parameter}",
        f"2={CONTRACT['target_profiles'][target['id']]['parameter_2_value']}",
    ]
    if state:
        args.append(f"--state={state}")
    text = run_command(["/usr/bin/sandbox-exec", "-p", SANDBOX, *args], folder, name)
    parsed = parse_log(text)
    validate_host_log(parsed, target, identity, bypass, output_parameter)
    audio = read_audio(output)
    telemetry = audio_telemetry(audio)
    write_json(
        folder / f"{name}.metadata.json",
        {"host_log": parsed, "audio_telemetry": telemetry},
    )
    # WAVE is saved only after clipping/spectral telemetry has been computed.
    import soundfile as sf

    sf.write(folder / f"{name}.wav", audio, SAMPLE_RATE, subtype="FLOAT")
    return audio


def verify_plugin(host, target, folder, inputs):
    folder.mkdir()
    identity = installed_identity(target)
    write_json(folder / "identity.json", identity)
    # Same parameter numbers can mean something different on another plugin.
    info = parse_log(
        run_command(
            [
                "/usr/bin/sandbox-exec",
                "-p",
                SANDBOX,
                host,
                target["type"],
                target["subtype"],
                target["manufacturer"],
                "info",
            ],
            folder,
            "inspect",
        )
    )
    for key, name in [
        ("0", "Dry/wet (Globals)"),
        ("1", "Output (Globals)"),
        ("2", CONTRACT["target_profiles"][target["id"]]["parameter_2_name"]),
    ]:
        if info["parameters"].get(key, [None])[0] != name:
            raise ValueError("UNSUPPORTED_PARAMETER_SCHEMA")
    cases = []
    for stimulus, input_path in inputs.items():
        print(f"{target['id']}: {stimulus}", file=sys.stderr, flush=True)
        reference = read_audio(input_path)
        base_a = render(
            host, target, identity, input_path, folder, stimulus + "_base_a", 0, 0.5
        )
        state = folder / f"{stimulus}_base_a.f32.state.plist"
        base_b = render(
            host,
            target,
            identity,
            input_path,
            folder,
            stimulus + "_base_b",
            0,
            0.5,
            state,
        )
        gain_a = render(
            host,
            target,
            identity,
            input_path,
            folder,
            stimulus + "_gain_a",
            0,
            0.45,
            state,
        )
        gain_b = render(
            host,
            target,
            identity,
            input_path,
            folder,
            stimulus + "_gain_b",
            0,
            0.45,
            state,
        )
        bypass_a = render(
            host,
            target,
            identity,
            input_path,
            folder,
            stimulus + "_bypass_a",
            1,
            0.5,
            state,
        )
        bypass_b = render(
            host,
            target,
            identity,
            input_path,
            folder,
            stimulus + "_bypass_b",
            1,
            0.5,
            state,
        )
        baseline_repeat_window = float(
            np.max(
                np.abs(
                    base_a[WINDOW[0] : WINDOW[1]].astype(np.float64)
                    - base_b[WINDOW[0] : WINDOW[1]].astype(np.float64)
                )
            )
        )
        gain = compare_case(
            base_a,
            gain_a,
            gain_b,
            expected_db=CONTRACT["gain_parameter"]["expected_db"],
        )
        bypass = compare_case(reference, bypass_a, bypass_b)
        # Deliberately wrong or missing evidence must never produce a pass.
        negative_wrong_gain = compare_case(base_a, gain_a, gain_b, expected_db=-6.0)
        negative_wrong_reference = compare_case(
            np.roll(reference, 1000, axis=0), bypass_a, bypass_b
        )
        controls = {
            "wrong_gain_rejected": not negative_wrong_gain["passed"],
            "wrong_input_rejected": not negative_wrong_reference["passed"],
        }
        for scope, metrics, reference_name, stem in [
            (
                "output_gain_minus_2_4_db_steady_window",
                gain,
                f"{stimulus}_base_a.f32",
                f"{stimulus}_gain",
            ),
            (
                "bypass_identity_steady_window",
                bypass,
                str(input_path.relative_to(folder.parent)),
                f"{stimulus}_bypass",
            ),
        ]:
            reference_reproduced = (
                scope == "bypass_identity_steady_window"
                or baseline_repeat_window <= CONTRACT["repeat_max_abs_tolerance"]
            )
            passed = bool(
                metrics["passed"] and all(controls.values()) and reference_reproduced
            )
            cases.append(
                {
                    "scope": scope,
                    "stimulus": stimulus,
                    "status": "VERIFIED_SCOPE" if passed else "BLOCKED",
                    "real_verification": passed,
                    "metrics": metrics,
                    "negative_controls": controls,
                    "repeat_diagnostics": diagnose_repeat(
                        reference,
                        gain_a if scope.startswith("output_gain") else bypass_a,
                        gain_b if scope.startswith("output_gain") else bypass_b,
                    ),
                    "reference_repeat_window_max_abs_error": baseline_repeat_window
                    if scope.startswith("output_gain")
                    else 0.0,
                    "reference": reference_name,
                    "first_output": stem + "_a.f32",
                    "second_output": stem + "_b.f32",
                }
            )
    after = installed_identity(target)
    if identity != after:
        raise ValueError("INSTALLED_BINARY_CHANGED_DURING_VERIFICATION")
    return {
        "target": target["id"],
        "identity": identity,
        "cases": cases,
        "verified_scopes": sum(c["real_verification"] for c in cases),
        "full_algorithm_verified": False,
        "catalog_variant_verified": False,
        "status": "PARTIAL_REAL_IO"
        if any(c["real_verification"] for c in cases)
        else "BLOCKED",
        "unverified": [
            "FULL_SIGNAL_TRANSIENTS",
            "VIBRATO_OR_FLANGER_ALGORITHM_EQUIVALENCE",
            "VST3_VARIANT",
            "FL_STUDIO_INTERNAL_PLUGINS",
        ],
    }


def verify_grok(folder, binary=GROK_PATH):
    folder.mkdir()
    binary = Path(binary).resolve(strict=True)
    before = digest(binary)
    outputs = []
    for idx in range(2):
        outputs.append(
            run_command(
                ["/usr/bin/sandbox-exec", "-p", SANDBOX, binary, "--version"],
                folder,
                f"version_{idx + 1}",
                timeout=15,
            )
        )
    passed = outputs == [GROK_EXPECTED, GROK_EXPECTED] and before == digest(binary)
    return {
        "target": "grok_local_cli",
        "binary": str(binary),
        "binary_sha256": before,
        "scope": "local_version_stdout_only",
        "arguments": ["--version"],
        "expected_stdout": GROK_EXPECTED,
        "observed_stdout": outputs,
        "status": "VERIFIED_SCOPE" if passed else "BLOCKED",
        "real_verification": passed,
        "unverified": [
            "GROK_BOT_APP",
            "INTERNAL_MODEL",
            "REMOTE_SERVICE",
            "AGENT_COUNT",
            "SEMANTIC_VERIFIER",
        ],
    }


def evidence_manifest(root):
    return {
        str(p.relative_to(root)): {"sha256": digest(p), "bytes": p.stat().st_size}
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name not in ("manifest.json", "validation.json")
    }


def check_bundle(root):
    """Recompute hashes, process records and numeric comparisons, not passed flags."""
    root = Path(root).resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text())
    if not manifest or not isinstance(manifest, dict):
        raise ValueError("MISSING_MANIFEST")

    def artifact(relative):
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts or str(rel) not in manifest:
            raise ValueError("UNSAFE_OR_UNMANIFESTED_EVIDENCE_PATH")
        path = (root / rel).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError("UNSAFE_EVIDENCE_PATH")
        return path

    for relative, info in manifest.items():
        path = artifact(relative)
        if path.stat().st_size != info["bytes"] or digest(path) != info["sha256"]:
            raise ValueError("EVIDENCE_HASH_OR_PATH_MISMATCH: " + relative)
    report = json.loads(artifact("report.json").read_text())
    contract = json.loads(artifact("contract.json").read_text())
    if contract != CONTRACT or report.get("mode") != "real_installed_io":
        raise ValueError("UNSUPPORTED_OR_SIMULATED_CONTRACT")
    if report.get("full_algorithms_verified") != 0:
        raise ValueError("UNSUPPORTED_FULL_ALGORITHM_CLAIM")

    def process_record(folder, stem):
        record = json.loads(
            artifact(str(Path(folder) / (stem + ".command.json"))).read_text()
        )
        if record.get("exit_code") != 0 or record.get("timed_out") is not False:
            raise ValueError("PROCESS_NOT_SUCCESSFUL")
        for kind in ("stdout", "stderr"):
            filename = record[kind + "_file"]
            if filename != stem + "." + kind + ".txt":
                raise ValueError("INVALID_PROCESS_LOG_REFERENCE")
            path = artifact(str(Path(folder) / filename))
            if digest(path) != record[kind + "_sha256"]:
                raise ValueError("PROCESS_LOG_HASH_MISMATCH")
        return record

    if any("cases" in plugin for plugin in report.get("plugins", [])):
        for stimulus, expected in stimuli():
            observed = read_audio(artifact(f"inputs/{stimulus}.f32"))
            if not np.array_equal(observed, expected):
                raise ValueError("INPUT_VECTOR_DIFFERS_FROM_CONTRACT")
    recomputed = []
    seen = set()
    for plugin in report.get("plugins", []):
        target = next((t for t in TARGETS if t["id"] == plugin.get("target")), None)
        if target is None or target["id"] in seen:
            raise ValueError("UNKNOWN_OR_DUPLICATE_TARGET")
        seen.add(target["id"])
        if "cases" not in plugin:
            if plugin.get("real_verification") or plugin.get("status") != "BLOCKED":
                raise ValueError("MISSING_CASE_EVIDENCE")
            continue
        if (
            plugin.get("full_algorithm_verified") is not False
            or plugin.get("catalog_variant_verified") is not False
        ):
            raise ValueError("UNSUPPORTED_VARIANT_OR_ALGORITHM_CLAIM")
        if plugin["identity"] != installed_identity(target):
            raise ValueError("CURRENT_INSTALLATION_DIFFERS_FROM_EVIDENCE")
        if (
            json.loads(artifact(target["id"] + "/identity.json").read_text())
            != plugin["identity"]
        ):
            raise ValueError("IDENTITY_RECORD_MISMATCH")
        artifact("au_probe")
        if artifact("au_probe.c").read_bytes() != SOURCE.read_bytes():
            raise ValueError("UNRECOGNIZED_HOST_SOURCE")
        process_record(".", "compile")
        local_count = 0
        case_keys = set()
        for case in plugin["cases"]:
            stimulus = case["stimulus"]
            if stimulus not in {"multitone", "sweep", "noise"}:
                raise ValueError("UNKNOWN_STIMULUS")
            scope = case["scope"]
            key = (stimulus, scope)
            if key in case_keys:
                raise ValueError("DUPLICATE_VERIFICATION_CASE")
            case_keys.add(key)
            if scope == "output_gain_minus_2_4_db_steady_window":
                expected_db, variant, bypass = -2.4, "gain", 0
                reference_rel = f"{target['id']}/{stimulus}_base_a.f32"
                if case["reference"] != f"{stimulus}_base_a.f32":
                    raise ValueError("WRONG_REFERENCE")
            elif scope == "bypass_identity_steady_window":
                expected_db, variant, bypass = 0.0, "bypass", 1
                reference_rel = f"inputs/{stimulus}.f32"
                if case["reference"] != reference_rel:
                    raise ValueError("WRONG_REFERENCE")
            else:
                raise ValueError("UNSUPPORTED_VERIFICATION_SCOPE")
            outputs = []
            for suffix in ("a", "b"):
                stem = f"{stimulus}_{variant}_{suffix}"
                if (
                    case["first_output" if suffix == "a" else "second_output"]
                    != stem + ".f32"
                ):
                    raise ValueError("WRONG_OUTPUT_REFERENCE")
                folder = target["id"]
                record = process_record(folder, stem)
                argv = record["argv"]
                if (
                    argv[:3] != ["/usr/bin/sandbox-exec", "-p", SANDBOX]
                    or Path(argv[3]).name != "au_probe"
                    or argv[4:8]
                    != [
                        target["type"],
                        target["subtype"],
                        target["manufacturer"],
                        "render",
                    ]
                    or Path(argv[8]).name != stimulus + ".f32"
                    or Path(argv[9]).name != stem + ".f32"
                    or argv[10] != str(bypass)
                ):
                    raise ValueError("PROCESS_ARGUMENT_MISMATCH")
                log = parse_log(
                    artifact(folder + "/" + stem + ".stdout.txt").read_text()
                )
                validate_host_log(
                    log,
                    target,
                    plugin["identity"],
                    bypass,
                    0.45 if variant == "gain" else 0.5,
                )
                artifact(folder + "/" + stem + ".f32.state.plist")
                outputs.append(read_audio(artifact(folder + "/" + stem + ".f32")))
            reference = read_audio(artifact(reference_rel))
            metrics = compare_case(
                reference, outputs[0], outputs[1], expected_db=expected_db
            )
            if metrics != case["metrics"]:
                raise ValueError("COMPARISON_RESULT_MISMATCH")
            baseline_a = read_audio(artifact(f"{target['id']}/{stimulus}_base_a.f32"))
            baseline_b = read_audio(artifact(f"{target['id']}/{stimulus}_base_b.f32"))
            repeat_window = float(
                np.max(
                    np.abs(
                        baseline_a[WINDOW[0] : WINDOW[1]].astype(np.float64)
                        - baseline_b[WINDOW[0] : WINDOW[1]].astype(np.float64)
                    )
                )
            )
            reference_reproduced = (
                variant == "bypass"
                or repeat_window <= CONTRACT["repeat_max_abs_tolerance"]
            )
            original_input = read_audio(artifact(f"inputs/{stimulus}.f32"))
            if "repeat_diagnostics" in case and case[
                "repeat_diagnostics"
            ] != diagnose_repeat(original_input, outputs[0], outputs[1]):
                raise ValueError("REPEAT_DIAGNOSTICS_MISMATCH")
            bypass_a = read_audio(artifact(f"{target['id']}/{stimulus}_bypass_a.f32"))
            bypass_b = read_audio(artifact(f"{target['id']}/{stimulus}_bypass_b.f32"))
            gain_a = read_audio(artifact(f"{target['id']}/{stimulus}_gain_a.f32"))
            gain_b = read_audio(artifact(f"{target['id']}/{stimulus}_gain_b.f32"))
            controls = {
                "wrong_gain_rejected": not compare_case(
                    baseline_a, gain_a, gain_b, expected_db=-6
                )["passed"],
                "wrong_input_rejected": not compare_case(
                    np.roll(original_input, 1000, axis=0), bypass_a, bypass_b
                )["passed"],
            }
            if controls != case["negative_controls"]:
                raise ValueError("NEGATIVE_CONTROL_MISMATCH")
            passed = bool(
                metrics["passed"] and reference_reproduced and all(controls.values())
            )
            if case["real_verification"] is not passed or case["status"] != (
                "VERIFIED_SCOPE" if passed else "BLOCKED"
            ):
                raise ValueError("FALSE_POSITIVE_CASE")
            recomputed.append(passed)
            local_count += passed
        if len(case_keys) != 6 or plugin["verified_scopes"] != local_count:
            raise ValueError("MISSING_OR_MISCOUNTED_CASES")
    app_count = 0
    applications = report.get("applications", [])
    if len(applications) > 1:
        raise ValueError("DUPLICATE_APPLICATION")
    for app in applications:
        if not app.get("real_verification"):
            if app.get("status") != "BLOCKED":
                raise ValueError("INVALID_APPLICATION_STATUS")
            continue
        if (
            app.get("target") != "grok_local_cli"
            or app.get("scope") != "local_version_stdout_only"
            or Path(app["binary"]).resolve() != GROK_PATH.resolve()
            or digest(app["binary"]) != app["binary_sha256"]
        ):
            raise ValueError("APPLICATION_IDENTITY_MISMATCH")
        observations = []
        for idx in (1, 2):
            stem = f"version_{idx}"
            record = process_record("grok_local_cli", stem)
            if record["argv"] != [
                "/usr/bin/sandbox-exec",
                "-p",
                SANDBOX,
                app["binary"],
                "--version",
            ]:
                raise ValueError("APPLICATION_ARGUMENT_MISMATCH")
            observations.append(
                artifact(f"grok_local_cli/{stem}.stdout.txt").read_text()
            )
        if (
            observations != [GROK_EXPECTED] * 2
            or app["observed_stdout"] != observations
            or app["expected_stdout"] != GROK_EXPECTED
        ):
            raise ValueError("APPLICATION_EVIDENCE_MISMATCH")
        app_count += 1
    if report["verified_scoped_cases"] != sum(recomputed) + app_count:
        raise ValueError("MISCOUNTED_VERIFICATION_CLAIMS")
    return {
        "status": "EVIDENCE_INTEGRITY_AND_COMPARISONS_CHECKED",
        "cases_recomputed": len(recomputed),
        "verified_plugin_cases": sum(recomputed),
        "verified_application_cases": app_count,
        "verified_cases": sum(recomputed) + app_count,
        "full_algorithms_verified": 0,
        "note": "Local retained evidence, not hardware attestation or protection against a fabricated entire bundle.",
    }


def compare_sessions(bundle_paths):
    """Conservative intersection: a failure in any retained session stays blocked."""
    if len(bundle_paths) < 2:
        raise ValueError("TWO_INDEPENDENT_SESSIONS_REQUIRED")
    roots = [Path(p).resolve(strict=True) for p in bundle_paths]
    if len(set(roots)) != len(roots):
        raise ValueError("DUPLICATE_SESSION")
    maps = []
    evidence = []
    for root in roots:
        check_bundle(root)
        report = json.loads((root / "report.json").read_text())
        session = {}
        for plugin in report["plugins"]:
            for case in plugin.get("cases", []):
                key = (plugin["target"], case["scope"], case["stimulus"])
                session[key] = case["real_verification"]
        for app in report["applications"]:
            key = (
                app["target"],
                app.get("scope", "local_version_stdout_only"),
                "--version",
            )
            session[key] = bool(app.get("real_verification"))
        maps.append(session)
        evidence.append(
            {
                "bundle": str(root),
                "report_sha256": digest(root / "report.json"),
                "manifest_sha256": digest(root / "manifest.json"),
            }
        )
    if len({item["report_sha256"] for item in evidence}) != len(evidence):
        raise ValueError("DUPLICATE_RUN_EVIDENCE")
    keys = sorted(set().union(*(mapping.keys() for mapping in maps)))
    cases = []
    for key in keys:
        observations = [mapping.get(key, False) for mapping in maps]
        passed = all(observations)
        cases.append(
            {
                "target": key[0],
                "scope": key[1],
                "stimulus": key[2],
                "session_results": observations,
                "status": "VERIFIED_SCOPE" if passed else "BLOCKED",
                "real_verification": passed,
            }
        )
    return {
        "mode": "real_io_cross_session_intersection",
        "sessions": evidence,
        "cases": cases,
        "verified_scoped_cases": sum(c["real_verification"] for c in cases),
        "requested_cases_passed": bool(cases)
        and all(c["real_verification"] for c in cases),
        "full_algorithms_verified": 0,
        "status": "PARTIAL_REAL_VERIFICATION"
        if any(c["real_verification"] for c in cases)
        else "BLOCKED",
    }


def check_evidence_path(root):
    """Accept a single run or conservatively check all retained sesion_* children."""
    root = Path(root).resolve(strict=True)
    sessions = sorted(
        p for p in root.iterdir() if p.is_dir() and p.name.startswith("sesion_")
    )
    if sessions:
        result = compare_sessions(sessions)
        plugin_count = sum(
            c["real_verification"]
            for c in result["cases"]
            if c["target"] != "grok_local_cli"
        )
        app_count = sum(
            c["real_verification"]
            for c in result["cases"]
            if c["target"] == "grok_local_cli"
        )
        result.update(
            verified_plugin_cases=plugin_count,
            verified_application_cases=app_count,
            verified_cases=plugin_count + app_count,
            policy="INTERSECTION_OF_ALL_RETAINED_SESSIONS",
        )
        return result
    return check_bundle(root)


def installed_inventory():
    """Metadata discovery is kept separate from process/audio verification."""
    result = {
        "applications": [],
        "audio_units": [],
        "vst3_bundles": [],
        "fl_native": {},
    }
    for name in (
        "FL Studio 2026.app",
        "DJ.Studio.app",
        "Grok Bot.app",
        "BABYLON60.app",
    ):
        bundle = Path("/Applications") / name
        try:
            metadata = plistlib.loads((bundle / "Contents/Info.plist").read_bytes())
            result["applications"].append(
                {
                    "bundle": str(bundle),
                    "bundle_id": metadata.get("CFBundleIdentifier"),
                    "version": metadata.get("CFBundleVersion"),
                    "functional_status": "BLOCKED_NO_ISOLATED_IO_ADAPTER",
                }
            )
        except (OSError, plistlib.InvalidFileException):
            result["applications"].append(
                {"bundle": str(bundle), "functional_status": "BLOCKED_NOT_DISCOVERED"}
            )
    for metadata_file in sorted(
        Path("/Library/Audio/Plug-Ins/Components").glob(
            "*.component/Contents/Info.plist"
        )
    ):
        metadata = plistlib.loads(metadata_file.read_bytes())
        result["audio_units"].append(
            {
                "bundle": str(metadata_file.parents[1]),
                "bundle_id": metadata.get("CFBundleIdentifier"),
                "version": metadata.get("CFBundleVersion"),
                "components": metadata.get("AudioComponents", []),
                "discovery_only": True,
            }
        )
    result["vst3_bundles"] = [
        str(p) for p in sorted(Path("/Library/Audio/Plug-Ins/VST3").rglob("*.vst3"))
    ]
    try:
        from scripts.fl_native_plugin_reverse_engine import scan_native_fl_plugins

        report = scan_native_fl_plugins(
            False,
            plugins_root="/Applications/FL Studio 2026.app/Contents/Resources/FL/Plugins/Fruity",
        )
        result["fl_native"] = {
            k: report[k]
            for k in (
                "detected_plugins",
                "catalog_coverage_percent",
                "algorithms_verified",
                "verified",
                "inventory_status",
                "missing_effects",
                "missing_generators",
            )
        }
    except ImportError:
        # Direct script execution has scripts/ on sys.path, not the project root.
        import fl_native_plugin_reverse_engine as plugins

        report = plugins.scan_native_fl_plugins(
            False,
            plugins_root="/Applications/FL Studio 2026.app/Contents/Resources/FL/Plugins/Fruity",
        )
        result["fl_native"] = {
            k: report[k]
            for k in (
                "detected_plugins",
                "catalog_coverage_percent",
                "algorithms_verified",
                "verified",
                "inventory_status",
                "missing_effects",
                "missing_generators",
            )
        }
    return result


def run_suite(output_dir, *, plugins=True, applications=True):
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=False)  # Never reuse stale audio as new evidence.
    write_json(root / "contract.json", CONTRACT)  # Written before running any target.
    write_json(root / "inventory.json", installed_inventory())
    report = {
        "mode": "real_installed_io",
        "started_unix": time.time(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
        },
        "plugins": [],
        "applications": [],
        "full_algorithms_verified": 0,
        "blocked": [
            "147_PLUGIN_ALGORITHM_EQUIVALENCE",
            "AOT_HARDWARE_CONFINEMENT",
            "SWARM_AUTONOMOUS_AGENTS_AND_DISTRIBUTED_BFT",
            "GROK_INTERNAL_INFRASTRUCTURE",
            "DJ_STUDIO_END_TO_END",
            "FL_STUDIO_NATIVE_PLUGIN_DSP",
        ],
    }
    if platform.system() != "Darwin" or not Path("/usr/bin/sandbox-exec").exists():
        report["blocked"].append("MACOS_AUDIO_UNIT_HOST_UNAVAILABLE")
        plugins = applications = False
    if applications:
        try:
            report["applications"].append(verify_grok(root / "grok_local_cli"))
        except Exception as exc:
            report["applications"].append(
                {
                    "target": "grok_local_cli",
                    "status": "BLOCKED",
                    "real_verification": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    if plugins:
        try:
            source = root / "au_probe.c"
            source.write_bytes(SOURCE.read_bytes())
            host = root / "au_probe"
            run_command(
                [
                    "xcrun",
                    "clang",
                    "-O2",
                    "-Wall",
                    "-Wextra",
                    "-Wno-unused-parameter",
                    source,
                    "-framework",
                    "AudioToolbox",
                    "-framework",
                    "CoreFoundation",
                    "-o",
                    host,
                ],
                root,
                "compile",
            )
            input_dir = root / "inputs"
            input_dir.mkdir()
            inputs = {}
            import soundfile as sf

            for name, value in stimuli():
                path = input_dir / f"{name}.f32"
                value.tofile(path)
                write_json(input_dir / f"{name}.telemetry.json", audio_telemetry(value))
                sf.write(input_dir / f"{name}.wav", value, SAMPLE_RATE, subtype="FLOAT")
                inputs[name] = path
            for target in TARGETS:
                try:
                    result = verify_plugin(host, target, root / target["id"], inputs)
                except Exception as exc:
                    result = {
                        "target": target["id"],
                        "status": "BLOCKED",
                        "real_verification": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                report["plugins"].append(result)
        except Exception as exc:
            report["blocked"].append(
                f"HOST_OR_INPUT_FAILURE: {type(exc).__name__}: {exc}"
            )
    count = sum(p.get("verified_scopes", 0) for p in report["plugins"]) + sum(
        a.get("real_verification", False) for a in report["applications"]
    )
    requested_cases_passed = bool(count) and (
        (
            not plugins
            or (
                len(report["plugins"]) == len(TARGETS)
                and all(p.get("verified_scopes") == 6 for p in report["plugins"])
            )
        )
        and (
            not applications
            or (
                len(report["applications"]) == 1
                and all(a.get("real_verification") for a in report["applications"])
            )
        )
    )
    report.update(
        requested_cases_passed=requested_cases_passed,
        verified_scoped_cases=count,
        status="PARTIAL_REAL_VERIFICATION" if count else "BLOCKED",
        finished_unix=time.time(),
    )
    write_json(root / "report.json", report)
    write_json(root / "manifest.json", evidence_manifest(root))
    validation = check_bundle(root)
    write_json(root / "validation.json", validation)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compare-bundles",
        nargs="+",
        type=Path,
        help="Keep a case blocked if any retained session fails",
    )
    parser.add_argument(
        "--output", type=Path, help="New directory for retained evidence"
    )
    parser.add_argument(
        "--check-bundle",
        type=Path,
        help="Recompute existing evidence without rendering",
    )
    parser.add_argument(
        "--only", choices=["plugins", "applications", "all"], default="all"
    )
    args = parser.parse_args(argv)
    try:
        if args.compare_bundles:
            result = compare_sessions(args.compare_bundles)
        elif args.check_bundle:
            result = check_evidence_path(args.check_bundle)
        elif args.output:
            result = run_suite(
                args.output,
                plugins=args.only != "applications",
                applications=args.only != "plugins",
            )
        else:
            parser.error("--output or --check-bundle is required")
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        if args.check_bundle:
            return 0  # Integrity/recalculation succeeded, not a claim that every case passed.
        return 0 if result.get("requested_cases_passed") else 1
    except Exception as exc:
        print(
            json.dumps({"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"})
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
