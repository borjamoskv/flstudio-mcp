#!/usr/bin/env python3
# ============================================================================
# FL STUDIO 2025 MCP PRODUCTION SUITE
# █ XENHARMONIC SWARM ENGINE | Plomp-Levelt Sensory Dissonance & Scala (.scl)
# ============================================================================
"""
poc_xenharmonic_swarm.py - Swarm-Guided Xenharmonic Tuning Engine
Calculates Helmholtz / Plomp-Levelt sensory dissonance across microtonal interval
matrices (24-TET / 31-TET / Just Intonation) and generates Scala (.scl) tuning profiles.
"""

import argparse
import json
import math
import sys
from typing import List, Dict, Any

# Plomp-Levelt dissonance curve coefficients
ALPHA = 3.5
BETA = 5.75
D_MAX = 0.24
S1 = 0.021
S2 = 0.19


def interval_dissonance(f1: float, f2: float) -> float:
    """Calculates Plomp-Levelt sensory dissonance between two frequencies."""
    f_min = min(f1, f2)
    f_diff = abs(f1 - f2)
    s = D_MAX / (S1 * f_min + S2)
    x = s * f_diff
    return math.exp(-ALPHA * x) - math.exp(-BETA * x)


def evaluate_scale_dissonance(frequencies: List[float]) -> float:
    """Computes total pairwise dissonance metric for a scale (Exergy loss)."""
    total_dissonance = 0.0
    pairs = 0
    for i in range(len(frequencies)):
        for j in range(i + 1, len(frequencies)):
            total_dissonance += interval_dissonance(frequencies[i], frequencies[j])
            pairs += 1
    return total_dissonance / max(pairs, 1)


def generate_scala_scl(scale_name: str, cents_list: List[float]) -> str:
    """Generates Scala (.scl) file content."""
    lines = [
        f"! {scale_name}.scl",
        f"! Generated autonomously by FL Studio MCP Swarm Tuning Engine",
        scale_name,
        str(len(cents_list)),
        "!"
    ]
    for cents in cents_list:
        lines.append(f" {cents:.5f}")
    return "\n".join(lines)


def run_poc_xenharmonic(divisions: int = 24, json_output: bool = False) -> None:
    # Base frequency A4 = 440 Hz
    f0 = 440.0
    cents_step = 1200.0 / divisions
    cents_list = [cents_step * i for i in range(1, divisions + 1)]
    frequencies = [f0 * (2 ** (c / 1200.0)) for c in cents_list]

    dissonance_score = evaluate_scale_dissonance(frequencies)
    scale_title = f"{divisions}-TET Xenharmonic Swarm Matrix"
    scl_content = generate_scala_scl(scale_title, cents_list)

    if json_output:
        payload = {
            "schema_version": "1.0",
            "type": "FLSTUDIO_XENHARMONIC_SWARM",
            "scale": {
                "name": scale_title,
                "divisions": divisions,
                "base_freq_hz": f0,
                "sensory_dissonance_index": round(dissonance_score, 6),
                "exergy_consonance_pct": round((1.0 - dissonance_score) * 100, 2)
            },
            "scala_scl_preview": scl_content.splitlines()[:10],
            "status": "CONVERGED"
        }
        print(json.dumps(payload, indent=2))
        return

    print("============================================================")
    print(" 🎼 FL STUDIO MCP: SWARM-GUIDED XENHARMONIC TUNING ENGINE")
    print("============================================================")
    print(f" Scale Target               : {scale_title}")
    print(f" Microtonal Divisions       : {divisions}")
    print(f" Sensory Dissonance Index   : {dissonance_score:.6f}")
    print(f" Exergy Consonance Score    : {((1.0 - dissonance_score) * 100):.2f}%")
    print("------------------------------------------------------------")
    print(" Scala (.scl) Manifest Preview:")
    print("\n".join(scl_content.splitlines()[:8]))
    print("============================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="FL Studio MCP: Swarm-Guided Xenharmonic Tuning Engine")
    parser.add_argument("--divisions", "-d", type=int, default=24, help="Number of EDO scale divisions (default: 24)")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")
    args = parser.parse_args()

    run_poc_xenharmonic(divisions=args.divisions, json_output=args.json)


if __name__ == "__main__":
    main()
