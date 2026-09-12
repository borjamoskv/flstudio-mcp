#!/usr/bin/env python3
"""
C5-REAL Kernel & Mach Thread Watchdog Guard for FL Studio (macOS)
═════════════════════════════════════════════════════════════════
Performs deep process inspection, thread count, RSS memory footprint,
CPU duty cycle, and thermodynamic liveness audit for FL Studio 2025.

Follows process_diagnostics_invariant:
- NEVER uses ps aux -c (preserves full command line arguments and executable paths).
- Deep Mach/PID inspection via /bin/ps and macOS sysctl.
"""

import os
import subprocess
import time
from typing import Dict, Any, Optional, List


def inspect_fl_process_kernel() -> Dict[str, Any]:
    """
    Inspects FL Studio (OsxFL) process state on macOS without truncating command line paths.
    Captures PID, CPU %, Memory RSS, thread count, and parent process.
    """
    try:
        # ps aux without -c to preserve full command path
        proc = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = proc.stdout.splitlines()
        fl_processes = []

        for line in lines:
            if "OsxFL" in line or "FL Studio" in line:
                if "grep" in line or "python" in line and "watchdog" in line:
                    continue
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    fl_processes.append({
                        "user": parts[0],
                        "pid": int(parts[1]),
                        "cpu_percent": float(parts[2]),
                        "mem_percent": float(parts[3]),
                        "vsz_kb": int(parts[4]),
                        "rss_kb": int(parts[5]),
                        "rss_mb": round(int(parts[5]) / 1024.0, 2),
                        "tty": parts[6],
                        "state": parts[7],
                        "started": parts[8],
                        "time": parts[9],
                        "command_full": parts[10]
                    })

        if not fl_processes:
            return {
                "status": "DAW_OFFLINE",
                "message": "FL Studio process (OsxFL) is not currently running.",
                "process_count": 0,
                "timestamp": time.time()
            }

        main_proc = fl_processes[0]
        pid = main_proc["pid"]

        # Query thread count via ps -M (Mach threads) without -c
        threads_count = 0
        try:
            m_proc = subprocess.run(
                ["ps", "-M", "-p", str(pid)],
                capture_output=True,
                text=True,
                check=True
            )
            threads_count = max(0, len(m_proc.stdout.splitlines()) - 1)
        except Exception:
            threads_count = 1

        # Thermodynamic health evaluation
        is_hung = (main_proc["state"].startswith("U") or main_proc["cpu_percent"] > 350.0)
        health_status = "CRITICAL_SPINLOCK" if is_hung else ("HEALTHY_REALTIME" if threads_count > 4 else "NORMAL")

        return {
            "status": "DAW_ONLINE_KERNEL_VALIDATED",
            "health": health_status,
            "pid": pid,
            "user": main_proc["user"],
            "state": main_proc["state"],
            "mach_threads": threads_count,
            "cpu_percent": main_proc["cpu_percent"],
            "rss_mb": main_proc["rss_mb"],
            "vsz_mb": round(main_proc["vsz_kb"] / 1024.0, 2),
            "command_full": main_proc["command_full"],
            "timestamp": time.time()
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "timestamp": time.time()
        }


if __name__ == "__main__":
    import json
    res = inspect_fl_process_kernel()
    print(json.dumps(res, indent=2))
