#!/usr/bin/env python3
"""
2D Kirchhoff-Love Modal Plate & Gong Resonator Physical Modeler (v20.0 Sovereign Transcendence)
════════════════════════════════════════════════════════════════════════════════════════════════
Synthesizes physical 2D plate vibrations (Chladni eigenmodes) using modal acoustic synthesis.
Accurately models metallic inharmonic dispersion, modal damping, and spatial stereo pickups.

Acoustic Physics:
1. Kirchhoff-Love Plate Equation:
   rho * h * d^2 w / dt^2 + D * nabla^4 w + 2 * d1 * dw / dt = f(x, y, t)
   where bending stiffness D = E * h^3 / (12 * (1 - nu^2)).
2. Eigenmode Frequencies:
   f_{m,n} = (pi / 2) * sqrt(D / (rho * h)) * [(m / Lx)^2 + (n / Ly)^2]
   Yields physical inharmonic overtone spacing characteristic of gongs, cymbals, and metal plates.
3. Modal Spatial Eigenfunctions (Simply Supported):
   Phi_{m,n}(x, y) = sin(m * pi * x / Lx) * sin(n * pi * y / Ly)
4. Dual Stereo Pickups:
   Pickup L at (x_L, y_L) and Pickup R at (x_R, y_R) capturing rich spatial stereo phase dispersion.
5. Frequency-dependent damping:
   tau_{m,n} = 1.0 / (d1 + d2 * (f_{m,n} / 1000)^1.5)
6. Centralized WAV export to ~/Music/FL Studio Bounces/Modal_Plates/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("FLStudio-ModalPlate")

# Material Physical Constants (Steel / Bronze / Aluminum)
MATERIALS = {
    "steel": {"E": 200e9, "rho": 7850.0, "nu": 0.30, "d1": 1.2, "d2": 0.08},
    "bronze": {"E": 105e9, "rho": 8500.0, "nu": 0.34, "d1": 0.8, "d2": 0.05},
    "aluminum": {"E": 69e9, "rho": 2700.0, "nu": 0.33, "d1": 1.8, "d2": 0.12},
    "cajon_wood": {"E": 12e9, "rho": 650.0, "nu": 0.25, "d1": 4.5, "d2": 0.35}
}


def synthesize_modal_plate_resonator(
    material: str = "bronze",
    length_m: float = 0.75,
    width_m: float = 0.55,
    thickness_mm: float = 1.8,
    strike_pos: Tuple[float, float] = (0.42, 0.38),
    strike_force: float = 0.85,
    duration_sec: float = 3.5,
    max_modes: int = 48,
    output_wav: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesizes a physical 2D vibrating plate strike with stereo spatial pickups.
    """
    mat_key = material.lower().strip()
    if mat_key not in MATERIALS:
        mat_key = "bronze"

    props = MATERIALS[mat_key]
    E = props["E"]
    rho = props["rho"]
    nu = props["nu"]
    d1 = props["d1"]
    d2 = props["d2"]

    h = thickness_mm * 1e-3
    Lx = max(0.1, float(length_m))
    Ly = max(0.1, float(width_m))

    # Bending stiffness D
    D = (E * (h ** 3)) / (12.0 * (1.0 - nu ** 2))
    stiffness_factor = (np.pi / 2.0) * np.sqrt(D / (rho * h))

    sr = 44100
    total_samples = int(duration_sec * sr)
    t = np.linspace(0.0, duration_sec, total_samples, endpoint=False)

    # Pickup positions (normalized coordinates [0, 1] across Lx, Ly)
    pos_L = (0.28, 0.32)
    pos_R = (0.72, 0.68)

    sx, sy = strike_pos
    sx = np.clip(sx, 0.05, 0.95)
    sy = np.clip(sy, 0.05, 0.95)

    # Calculate modal parameters
    modes = []
    for m in range(1, 15):
        for n in range(1, 15):
            # Frequency
            f_mn = stiffness_factor * (((m / Lx) ** 2) + ((n / Ly) ** 2))
            if 20.0 <= f_mn <= 18000.0:
                # Mode shapes
                phi_strike = np.sin(m * np.pi * sx) * np.sin(n * np.pi * sy)
                phi_L = np.sin(m * np.pi * pos_L[0]) * np.sin(n * np.pi * pos_L[1])
                phi_R = np.sin(m * np.pi * pos_R[0]) * np.sin(n * np.pi * pos_R[1])

                # Decay time constant
                decay_rate = d1 + d2 * ((f_mn / 1000.0) ** 1.3)
                tau = 1.0 / max(0.1, decay_rate)

                # Amplitude weighting: lower modes and modes aligned with strike point
                amp = (strike_force * phi_strike) / (1.0 + (f_mn / 2000.0) ** 0.8)

                modes.append({
                    "m": m,
                    "n": n,
                    "freq": f_mn,
                    "amp_L": amp * phi_L,
                    "amp_R": amp * phi_R,
                    "tau": tau
                })

    # Sort by perceptual prominence and prune to max_modes
    modes.sort(key=lambda x: abs(x["amp_L"]) + abs(x["amp_R"]), reverse=True)
    active_modes = modes[:max_modes]

    # Synthesize modal sum
    left_chan = np.zeros(total_samples, dtype=np.float64)
    right_chan = np.zeros(total_samples, dtype=np.float64)

    for mode in active_modes:
        freq = mode["freq"]
        tau = mode["tau"]
        env = np.exp(-t / tau)
        # Random initial phase micro-dispersion
        phi0 = np.random.uniform(0, 2 * np.pi)
        osc = np.sin(2.0 * np.pi * freq * t + phi0) * env

        left_chan += osc * mode["amp_L"]
        right_chan += osc * mode["amp_R"]

    # Natural non-linear strike transient (broadband hammer impact burst 5ms)
    strike_len = int(0.005 * sr)
    strike_env = np.hanning(strike_len * 2)[:strike_len]
    hammer_noise = np.random.normal(0.0, 0.15 * strike_force, strike_len) * strike_env
    left_chan[:strike_len] += hammer_noise
    right_chan[:strike_len] += hammer_noise

    # Peak normalization
    peak = max(np.max(np.abs(left_chan)), np.max(np.abs(right_chan)))
    if peak > 1e-6:
        left_chan = (left_chan / peak) * 0.88
        right_chan = (right_chan / peak) * 0.88

    # Centralized export
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Modal_Plates"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"Modal_Plate_{mat_key}_{int(Lx*100)}x{int(Ly*100)}cm_{thickness_mm}mm_{int(duration_sec)}s.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    stereo_audio = np.stack([left_chan, right_chan], axis=1)
    int16_out = np.clip(stereo_audio * 32767.0, -32768, 32767).astype(np.int16)

    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_out.tobytes())

    return {
        "status": "SUCCESS",
        "material": mat_key,
        "dimensions_m": [Lx, Ly],
        "thickness_mm": thickness_mm,
        "bending_stiffness_D": round(float(D), 2),
        "fundamental_freq_hz": round(float(active_modes[0]["freq"]), 1) if active_modes else 0.0,
        "total_modes_synthesized": len(active_modes),
        "duration_sec": duration_sec,
        "strike_position": [round(float(sx), 2), round(float(sy), 2)],
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = synthesize_modal_plate_resonator(material="bronze", duration_sec=3.0)
    print("Modal Plate Resonator Output:", res)
