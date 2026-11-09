#!/usr/bin/env python3
"""Local synthetic microbenchmark: serial slots, generated votes and noise DSP.

This does not verify autonomous agents, concurrent IPC, hardware atomics or BFT.
Real verification fails closed until an independent evidence path is implemented.
"""

import argparse
import json
import math
import platform
import sys
import tempfile
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Every threshold applies to a measured scalar, not to a claim of equivalence.
LIMITS = {
    "avg_write_ns": (0, 500),
    "avg_read_ns": (0, 500),
    "avg_consensus_ms": (0, 2),
    "p99_consensus_ms": (0, 2),
    "dsp_processing_ms": (0, 10000),
}


def evaluate_metrics(metrics):
    """Missing, nonfinite and out-of-range observations fail, including equality."""
    checks = {}
    for name, (low, high) in LIMITS.items():
        value = metrics.get(name)
        checks[name] = (
            type(value) in (int, float) and math.isfinite(value) and low <= value < high
        )
    phase = metrics.get("phase_coherence")
    checks["phase_coherence"] = (
        type(phase) in (int, float) and math.isfinite(phase) and 0.95 < phase <= 1.0
    )
    checks["readback_matches"] = metrics.get("readback_matches") is True
    checks["audio_finite"] = metrics.get("audio_finite") is True
    return {"checks": checks, "passed": all(checks.values())}


def run_benchmark(*, simulation=False):
    report = {
        "mode": "simulation" if simulation else "verification",
        "real_verification": False,
        "verified_agents": 0,
        "hardware_observed": {
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "limitations": [
            "NO_AUTONOMOUS_AGENT_EXECUTION",
            "NO_CONCURRENT_IPC_TEST",
            "NO_HARDWARE_ATTESTATION",
            "CENTRALIZED_TALLY_NOT_BFT",
        ],
        "metrics": {},
        "passed": False,
    }
    if not simulation:
        report.update(
            status="FAIL_MISSING_EVIDENCE",
            error="No real agent/runtime verifier is implemented",
        )
        return report

    import numpy as np
    from swarm1000.core.shm_seqlock_bus import ShmSeqlockBus
    from swarm1000.council.bft_1000_consensus import Bft1000ConsensusEngine
    from swarm1000.engine.psychoacoustic_matrix import (
        apply_lr4_crossover,
        apply_sigmoidal_bass_swap,
        apply_ms_peripheral_evaporation,
        calculate_phase_coherence,
    )

    # A unique file avoids touching any running telemetry bus.
    with tempfile.TemporaryDirectory(prefix="swarm-benchmark-") as scratch:
        bus = ShmSeqlockBus(is_master=True, path=str(Path(scratch) / "telemetry.raw"))
        try:
            t0 = time.perf_counter_ns()
            for agent_id in range(1000):
                bus.write_agent_state(
                    agent_id,
                    agent_id // 200 + 1,
                    126.0 + (agent_id % 4) * 0.5,
                    -12.5,
                    0.92,
                    1,
                    18.0,
                )
            write_ns = (time.perf_counter_ns() - t0) / 1000
            t0 = time.perf_counter_ns()
            states = [bus.read_agent_state(i) for i in range(1000)]
            read_ns = (time.perf_counter_ns() - t0) / 1000
            readback = all(
                s["agent_id"] == i
                and s["division_id"] == i // 200 + 1
                and s["bpm"] == 126.0 + (i % 4) * 0.5
                and s["lufs"] == -12.5
                and math.isclose(s["phase_coherence"], 0.92, abs_tol=1e-6)
                and s["action_code"] == 1
                and s["action_param"] == 18.0
                and s["timestamp_ns"] > 0
                for i, s in enumerate(states)
            )
        finally:
            bus.close()

    engine = Bft1000ConsensusEngine()
    latencies = []
    for idx in range(100):
        votes = engine.simulate_1000_agent_votes(
            0.65 if idx % 4 == 0 else 0.95, idx, idx % 16 == 0
        )
        t0 = time.perf_counter_ns()
        engine.resolve_consensus(votes, simulation=True)
        latencies.append((time.perf_counter_ns() - t0) / 1e6)

    # Retain the historical seed/data distribution for comparable DSP measurements.
    rng = np.random.RandomState(42)
    n = 480000
    track_a = rng.uniform(-0.5, 0.5, (n, 2)).astype(np.float32)
    track_b = rng.uniform(-0.5, 0.5, (n, 2)).astype(np.float32)
    tau = np.linspace(0.0, 1.0, n)[:, None].astype(np.float32)
    t0 = time.perf_counter_ns()
    low_a, high_a = apply_lr4_crossover(track_a, cutoff_hz=130.0)
    low_b, high_b = apply_lr4_crossover(track_b, cutoff_hz=130.0)
    mixed = (
        apply_sigmoidal_bass_swap(low_a, low_b, tau, k=18.0)
        + apply_ms_peripheral_evaporation(high_a, tau, side_boost=1.35)
        + high_b * tau
    )
    phase = float(calculate_phase_coherence(mixed, cutoff_hz=150.0))
    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6
    metrics = {
        "avg_write_ns": write_ns,
        "avg_read_ns": read_ns,
        "avg_consensus_ms": float(np.mean(latencies)),
        "p99_consensus_ms": float(np.percentile(latencies, 99)),
        "dsp_processing_ms": elapsed_ms,
        "phase_coherence": phase,
        "readback_matches": readback,
        "audio_finite": bool(np.isfinite(mixed).all()),
    }
    evaluated = evaluate_metrics(metrics)
    report.update(
        metrics=metrics,
        **evaluated,
        workload={
            "serial_slots": 1000,
            "simulated_votes_per_round": 1000,
            "rounds": 100,
            "audio_samples_per_track": n,
            "sample_rate": 48000,
        },
        status="SIMULATION_PASSED" if evaluated["passed"] else "SIMULATION_FAILED",
    )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--simulate", action="store_true", help="Explicit synthetic microbenchmark"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON result; no default artifact overwrite",
    )
    args = parser.parse_args(argv)
    try:
        report = run_benchmark(simulation=args.simulate)
    except Exception as exc:
        report = {
            "status": "ERROR",
            "passed": False,
            "real_verification": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    encoded = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(encoded + "\n")
    print(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
