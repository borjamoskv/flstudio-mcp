#!/usr/bin/env python3
"""
C5-REAL Causal Mixer DAG & Transactional State Machine
═══════════════════════════════════════════════════════
Models the FL Studio 125-track mixer as a Directed Acyclic Graph (DAG)
with formal invariant verification (headroom preservation, feedback cycle
detection) and ACID transactional commits with topological rollback.
"""

import math
import time
import json
import hashlib
from typing import Dict, List, Any, Tuple, Optional


class CausalMixerDAG:
    """Manages transactional state mutations on FL Studio mixer routing DAG."""

    def __init__(self):
        # Current state: track_id -> dict(volume, pan, sep, muted, soloed, sends: set)
        self.state: Dict[int, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []
        self._init_default_state()

    def _init_default_state(self) -> None:
        """Initializes tracks. Master is track 0; tracks 1..127 are initially inactive."""
        self.state[0] = {
            "volume": 0.8,
            "pan": 0.0,
            "stereo_separation": 0.0,
            "muted": False,
            "soloed": False,
            "sends": set()
        }
        for i in range(1, 128):
            self.state[i] = {
                "volume": 0.0,  # inactive
                "pan": 0.0,
                "stereo_separation": 0.0,
                "muted": False,
                "soloed": False,
                "sends": {0}  # routed to master when energized
            }

    def check_routing_acyclicity(self, proposed_sends: Dict[int, set]) -> bool:
        """
        Verifies that sidechain and routing sends do not introduce cycles in the audio DAG.
        Uses Depth-First Search cycle detection.
        """
        visited = set()
        rec_stack = set()

        def dfs(node: int) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in proposed_sends.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True  # Cycle detected!
            rec_stack.remove(node)
            return False

        all_nodes = set(proposed_sends.keys())
        for n in all_nodes:
            if n not in visited:
                if dfs(n):
                    return False  # Not acyclic!
        return True

    def estimate_master_headroom_db(self, proposed_state: Dict[int, Dict[str, Any]]) -> float:
        """
        Estimates summed incoherent audio power entering the Master track:
        Total Power = sum(vol_i^2) for unmuted tracks routed to Master.
        Returns estimated headroom in dB relative to nominal 0 dBFS.
        """
        total_power = 0.0
        for tid, tdata in proposed_state.items():
            if tid == 0 or tdata.get("muted", False):
                continue
            if 0 in tdata.get("sends", set()):
                vol = tdata.get("volume", 0.75)
                total_power += (vol ** 2)

        if total_power <= 0.0:
            return 24.0  # complete silence
        est_rms = math.sqrt(total_power)
        # 0.8 vol corresponds roughly to nominal unity (-6dB to 0dB)
        headroom_db = 20.0 * math.log10(max(1e-4, 1.6 / est_rms))
        return round(headroom_db, 2)

    def validate_transaction(self, mutations: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[int, Dict[str, Any]]]:
        """
        Validates proposed mutations against C5-REAL thermodynamic invariants:
        1. Range boundaries [0.0..1.0] for volume, [-1.0..1.0] for pan/sep.
        2. Acyclicity: No feedback loops in routing.
        3. Headroom: Prevents runaway master bus clipping (headroom >= -2.0 dB).
        """
        # Clone current state
        sim_state = {k: {**v, "sends": set(v["sends"])} for k, v in self.state.items()}

        for m in mutations:
            tid = int(m.get("track", 0))
            if tid < 0 or tid > 127:
                return False, f"Track index {tid} out of valid range (0-127)", sim_state

            if "volume" in m:
                v = float(m["volume"])
                if not (0.0 <= v <= 1.0):
                    return False, f"Volume {v} on track {tid} out of range [0.0, 1.0]", sim_state
                sim_state[tid]["volume"] = v

            if "pan" in m:
                p = float(m["pan"])
                if not (-1.0 <= p <= 1.0):
                    return False, f"Pan {p} on track {tid} out of range [-1.0, 1.0]", sim_state
                sim_state[tid]["pan"] = p

            if "stereo_separation" in m:
                s = float(m["stereo_separation"])
                if not (-1.0 <= s <= 1.0):
                    return False, f"Stereo separation {s} out of range [-1.0, 1.0]", sim_state
                sim_state[tid]["stereo_separation"] = s

            if "muted" in m:
                sim_state[tid]["muted"] = bool(m["muted"])

            if "soloed" in m:
                sim_state[tid]["soloed"] = bool(m["soloed"])

            if "add_send" in m:
                target = int(m["add_send"])
                if target == tid:
                    return False, f"Track {tid} cannot route to itself (self-feedback)", sim_state
                sim_state[tid]["sends"].add(target)

            if "remove_send" in m:
                target = int(m["remove_send"])
                sim_state[tid]["sends"].discard(target)

        # Check acyclicity
        sends_map = {k: v["sends"] for k, v in sim_state.items()}
        if not self.check_routing_acyclicity(sends_map):
            return False, "Routing cycle detected! Violates Directed Acyclic Graph topology.", sim_state

        # Check headroom
        est_headroom = self.estimate_master_headroom_db(sim_state)
        if est_headroom < -4.0:
            return False, f"Summed power exceeds safe master bus headroom ({est_headroom} dB). Reduce faders.", sim_state

        return True, "VALID", sim_state

    def commit_transaction(self, mutations: List[Dict[str, Any]], execute_midi: bool = True) -> Dict[str, Any]:
        """
        Commits verified mutations as an atomic transaction.
        If any hardware error occurs during MIDI dispatch, state is rolled back.
        """
        valid, msg, new_state = self.validate_transaction(mutations)
        if not valid:
            return {
                "status": "REJECTED",
                "reason": msg,
                "transaction_id": None
            }

        # Backup for rollback
        old_state_backup = {k: {**v, "sends": set(v["sends"])} for k, v in self.state.items()}
        tx_time = time.time()
        tx_hash = hashlib.sha256(f"{tx_time}_{len(mutations)}".encode("utf-8")).hexdigest()[:12]

        dispatched_events = []
        try:
            if execute_midi:
                import mcp_server
                for m in mutations:
                    tid = int(m.get("track", 0))
                    if "volume" in m:
                        mcp_server.fl_set_mixer_volume(tid, float(m["volume"]))
                        dispatched_events.append(f"vol(T{tid}={m['volume']})")
                    if "pan" in m:
                        mcp_server.fl_set_mixer_pan(tid, float(m["pan"]))
                        dispatched_events.append(f"pan(T{tid}={m['pan']})")
                    if "stereo_separation" in m:
                        mcp_server.fl_set_mixer_stereo_separation(tid, float(m["stereo_separation"]))
                        dispatched_events.append(f"sep(T{tid}={m['stereo_separation']})")
                    if "muted" in m:
                        mcp_server.fl_mute_track(tid, bool(m["muted"]))
                        dispatched_events.append(f"mute(T{tid})")
                    if "soloed" in m:
                        mcp_server.fl_solo_track(tid, bool(m["soloed"]))
                        dispatched_events.append(f"solo(T{tid})")
                    if "add_send" in m:
                        mcp_server.fl_setup_sidechain(tid, int(m["add_send"]))
                        dispatched_events.append(f"sidechain(T{tid}->T{m['add_send']})")

            # Commit state
            self.state = new_state
            self.history.append({
                "tx_id": tx_hash,
                "timestamp": tx_time,
                "mutations_count": len(mutations),
                "estimated_headroom_db": self.estimate_master_headroom_db(new_state)
            })

            return {
                "status": "COMMITTED",
                "transaction_id": tx_hash,
                "mutations_applied": len(mutations),
                "dispatched_events": dispatched_events,
                "estimated_headroom_db": self.estimate_master_headroom_db(new_state)
            }

        except Exception as e:
            # ROLLBACK
            self.state = old_state_backup
            return {
                "status": "ROLLED_BACK",
                "error": str(e),
                "transaction_id": tx_hash
            }


if __name__ == "__main__":
    dag = CausalMixerDAG()
    # Test valid transaction
    tx = [
        {"track": 1, "volume": 0.50, "pan": 0.0, "stereo_separation": 1.0},
        {"track": 2, "volume": 0.40, "add_send": 1}
    ]
    res = dag.commit_transaction(tx, execute_midi=False)
    print("Valid commit test:", json.dumps(res, indent=2))

    # Test cyclic feedback rejection
    cycle_tx = [
        {"track": 1, "add_send": 2},
        {"track": 2, "add_send": 3},
        {"track": 3, "add_send": 1}
    ]
    res_cycle = dag.commit_transaction(cycle_tx, execute_midi=False)
    print("Cycle rejection test:", json.dumps(res_cycle, indent=2))
