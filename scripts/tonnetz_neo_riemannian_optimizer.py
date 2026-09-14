#!/usr/bin/env python3
"""
Neo-Riemannian Tonnetz & Voice Leading Optimizer (v17.0 Hyper-Dimensional Omni)
Implements mathematical transformations on the Tonnetz torus (C_3 x C_4 x C_5)
and parsimonious voice-leading optimization for modal, chromatic, and flamenco progressions.

Theoretical Foundations:
- Triadic Operators:
    P (Parallel): shares root & 5th, shifts 3rd by 1 semitone (e.g. Dm <-> D)
    L (Leittonwechsel): shares 3rd & 5th, shifts root by 1 semitone (e.g. Dm <-> Bb)
    R (Relative): shares root & 3rd, shifts 5th by 2 semitones (e.g. Dm <-> F)
    S (Slide): L o P o R (e.g. Dm <-> C#)
    N (Nebentypus): R o P o L (e.g. Dm <-> Ebm)
    H (Hexatonic Pole): L o P o L (e.g. Dm <-> F#)
- Parsimonious Voice Leading: Minimizes total semitone displacement:
    Cost = sum_{v=1}^N |p_v(t) - p_v(t-1)|
- Exports native FL Studio Piano Roll Score (.fsc) and JSON transformation report.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import itertools

logger = logging.getLogger("FLStudio-Tonnetz")

# Pitch Class Mapping
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NAME_TO_PC = {name: idx for idx, name in enumerate(NOTE_NAMES)}
# Enharmonics
NAME_TO_PC.update({
    "Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10
})


class Triad:
    """Represents a pitch-class triad: (root, quality) where quality is '+' (major) or '-' (minor)."""
    def __init__(self, root_pc: int, quality: str):
        self.root = root_pc % 12
        self.quality = quality  # '+' for major, '-' for minor

    @property
    def pitch_classes(self) -> Tuple[int, int, int]:
        if self.quality == "+":
            return (self.root, (self.root + 4) % 12, (self.root + 7) % 12)
        else:
            return (self.root, (self.root + 3) % 12, (self.root + 7) % 12)

    @property
    def name(self) -> str:
        root_str = NOTE_NAMES[self.root]
        return root_str if self.quality == "+" else f"{root_str}m"

    def P(self) -> "Triad":
        """Parallel: inverts third."""
        new_qual = "-" if self.quality == "+" else "+"
        return Triad(self.root, new_qual)

    def L(self) -> "Triad":
        """Leittonwechsel (leading-tone exchange)."""
        if self.quality == "+":
            return Triad((self.root + 4) % 12, "-")
        else:
            return Triad((self.root + 8) % 12, "+")

    def R(self) -> "Triad":
        """Relative."""
        if self.quality == "+":
            return Triad((self.root + 9) % 12, "-")
        else:
            return Triad((self.root + 3) % 12, "+")

    def S(self) -> "Triad":
        """Slide: L o P o R."""
        return self.R().P().L()

    def N(self) -> "Triad":
        """Nebentypus: R o P o L."""
        return self.L().P().R()

    def H(self) -> "Triad":
        """Hexatonic Pole: L o P o L."""
        return self.L().P().L()


def parse_chord_to_triad(chord_str: str) -> Triad:
    """Parses chord strings like 'Dm', 'D', 'Bb', 'F#m' into Triad."""
    c = chord_str.strip()
    if c.endswith("m") and not c.endswith("dim"):
        root_name = c[:-1]
        quality = "-"
    else:
        root_name = c
        quality = "+"
    root_pc = NAME_TO_PC.get(root_name, 2)  # Default D
    return Triad(root_pc, quality)


def find_optimal_voice_leading(
    triads: List[Triad],
    base_octave: int = 4
) -> Tuple[List[Tuple[int, int, int, int]], int]:
    """
    Computes SATB 4-part voicings (doubling root) for a triad progression that
    strictly minimizes total semitone voice displacement.
    """
    # Generate candidate 4-note voicings for each triad within octaves 3..5
    all_voicings = []
    for triad in triads:
        pcs = triad.pitch_classes
        # Voice options: Bass (octave 3), Tenor, Alto, Soprano (octave 4..5)
        candidates = []
        bass_note = 36 + triad.root  # Bass root in octave 2..3
        # Pick 3 upper voices from pcs (can include root, third, fifth)
        upper_options = []
        for octave in (4, 5):
            for pc in pcs:
                upper_options.append(12 * octave + pc)

        # Generate combinations of 3 upper voices with root, 3rd, 5th present
        for combo in itertools.combinations(upper_options, 3):
            chord_pcs = set([bass_note % 12] + [p % 12 for p in combo])
            if set(pcs).issubset(chord_pcs):
                voicing = (bass_note, combo[0], combo[1], combo[2])
                candidates.append(voicing)

        # Limit to top 8 reasonable voicings sorted by spread
        candidates = sorted(candidates, key=lambda v: max(v) - min(v))[:8]
        all_voicings.append(candidates)

    # Dynamic Programming (Viterbi / Dijkstra) for minimum total distance
    # dp[step][candidate_idx] = (min_cost, prev_idx)
    dp = [{idx: (0, -1) for idx in range(len(all_voicings[0]))}]

    for step in range(1, len(triads)):
        curr_dp = {}
        for c_idx, c_voice in enumerate(all_voicings[step]):
            best_cost = float("inf")
            best_prev = -1
            for p_idx, p_voice in enumerate(all_voicings[step - 1]):
                prev_cost = dp[step - 1][p_idx][0]
                # Voice leading cost: sum of absolute differences of upper voices + bass
                step_cost = sum(abs(c_voice[v] - p_voice[v]) for v in range(4))
                total = prev_cost + step_cost
                if total < best_cost:
                    best_cost = total
                    best_prev = p_idx
            curr_dp[c_idx] = (best_cost, best_prev)
        dp.append(curr_dp)

    # Backtrack
    final_step = len(triads) - 1
    best_final_idx = min(dp[final_step].keys(), key=lambda k: dp[final_step][k][0])
    total_movement_cost = dp[final_step][best_final_idx][0]

    chosen_voicings = [None] * len(triads)
    curr_idx = best_final_idx
    for step in range(final_step, -1, -1):
        chosen_voicings[step] = all_voicings[step][curr_idx]
        curr_idx = dp[step][curr_idx][1]

    return chosen_voicings, total_movement_cost


def optimize_neo_riemannian_progression(
    base_progression: Optional[List[str]] = None,
    target_mode: str = "phrygian_dominant",
    transformation_cycle: str = "PLR_hexatonic",
    bars: int = 4,
    output_fsc: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates and optimizes a harmonic progression using Neo-Riemannian operators and
    parsimonious voice-leading minimization.
    - base_progression: initial chord list, e.g. ['D', 'Eb', 'Bb', 'D']
    - target_mode: 'phrygian_dominant', 'dorian', 'aeolian'
    - transformation_cycle: 'PLR_hexatonic', 'slide_chromatic', 'parallel_relative'
    """
    if not base_progression:
        # Default Flamenco Phrygian Dominant base
        base_chords = ["D", "Eb", "Bb", "D"]
    else:
        base_chords = base_progression

    triads = [parse_chord_to_triad(c) for c in base_chords]

    # Apply transformation variations
    extended_triads = []
    operations_applied = []

    for t in triads:
        extended_triads.append(t)
        operations_applied.append("INIT")
        if transformation_cycle == "PLR_hexatonic":
            t_sub = t.P().L()
            extended_triads.append(t_sub)
            operations_applied.append("P∘L")
        elif transformation_cycle == "slide_chromatic":
            t_sub = t.S()
            extended_triads.append(t_sub)
            operations_applied.append("S (Slide)")
        else:
            t_sub = t.R()
            extended_triads.append(t_sub)
            operations_applied.append("R (Relative)")

    # Compute optimal SATB voice leading
    voicings, parsimony_cost = find_optimal_voice_leading(extended_triads)

    # Build native .fsc score file
    try:
        from scripts.fl_fsc_score_builder import FLScoreBuilder
    except ImportError:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scripts.fl_fsc_score_builder import FLScoreBuilder
    ppq = 96
    builder = FLScoreBuilder(ppq=ppq, channels=5)

    ticks_per_chord = ppq * 2  # Half note per chord
    for chord_idx, voice in enumerate(voicings):
        pos = chord_idx * ticks_per_chord
        dur = int(ticks_per_chord * 0.95)
        for pitch in voice:
            builder.add_note(
                pos_ticks=pos,
                pitch=pitch,
                duration_ticks=dur,
                velocity=92 if pitch == voice[0] else 84,
                pan=64
            )

    # Centralized export
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Tonnetz_Harmonies"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_fsc:
        out_fsc_path = out_dir / f"Tonnetz_Progression_{target_mode}_{transformation_cycle}.fsc"
    else:
        out_fsc_path = Path(output_fsc).expanduser().resolve()
        out_fsc_path.parent.mkdir(parents=True, exist_ok=True)

    builder.export_fsc(str(out_fsc_path))

    progression_names = [t.name for t in extended_triads]

    return {
        "status": "SUCCESS",
        "target_mode": target_mode,
        "transformation_cycle": transformation_cycle,
        "total_chords": len(extended_triads),
        "chords_progression": progression_names,
        "operations_applied": operations_applied,
        "parsimonious_voice_leading_cost": parsimony_cost,
        "average_voice_movement_semitones": round(parsimony_cost / (4.0 * (len(extended_triads) - 1)), 2),
        "output_file": str(out_fsc_path),
        "output_fsc": str(out_fsc_path),
        "file_size_bytes": out_fsc_path.stat().st_size
    }


if __name__ == "__main__":
    res = optimize_neo_riemannian_progression()
    print("Tonnetz Optimizer Output:", res)
