#!/usr/bin/env python3
"""
Non-Linear Chaotic Attractor Sound Design Synthesizer (v21.0 Hyper-Spatial Continuum)
═════════════════════════════════════════════════════════════════════════════════════
Synthesizes non-linear deterministic chaos using 4th-order Runge-Kutta (RK4) numerical integration.
Models strange attractors and bifurcations for raw cyber-textures, sub-bass drones, and organic instability.

Dynamical Systems:
1. Duffing Oscillator (Double-well potential):
   x'' + delta * x' + alpha * x + beta * x^3 = gamma * cos(omega * t)
   Generates period-doubling routes to chaos, metallic resonances, and catastrophic jumps.
2. Van der Pol Oscillator (Non-linear relaxation):
   x'' - mu * (1 - x^2) * x' + omega0^2 * x = 0
   Produces organic, self-oscillating limit cycles characteristic of analog circuits.
3. Lorenz Strange Attractor (3D butterfly manifold):
   dx/dt = sigma * (y - x)
   dy/dt = x * (rho - z) - y
   dz/dt = x * y - beta * z
   Mapped to audio rates with 2D spatial stereo phase projection.
4. Centralized WAV export to ~/Music/FL Studio Bounces/Chaotic_Attractors/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("FLStudio-Chaos")


def synthesize_chaotic_attractor_oscillator(
    attractor_type: str = "duffing",
    base_frequency_hz: float = 110.0,  # A2
    chaos_parameter: float = 0.40,     # Driving / non-linearity depth
    duration_sec: float = 3.5,
    stereo_spread: float = 0.50,
    output_wav: Optional[str] = None
) -> Dict[str, Any]:
    """
    Synthesizes a chaotic attractor oscillator via Runge-Kutta 4 (RK4) integration.
    - attractor_type: 'duffing', 'vanderpol', 'lorenz'
    - chaos_parameter: controls non-linear drive / bifurcation point
    """
    kind = attractor_type.lower().strip()
    if kind not in {"duffing", "vanderpol", "lorenz"}:
        kind = "duffing"

    sr = 44100
    total_samples = int(duration_sec * sr)
    dt = 1.0 / sr

    left_chan = np.zeros(total_samples, dtype=np.float64)
    right_chan = np.zeros(total_samples, dtype=np.float64)

    if kind == "duffing":
        # Double well: alpha = -1.0, beta = 1.0
        alpha = -1.0
        beta = 1.0
        delta = 0.25
        gamma = 0.20 + 0.35 * chaos_parameter  # Chaos onset ~0.35
        omega = 2.0 * np.pi * base_frequency_hz

        x = 0.1
        v = 0.0

        for n in range(total_samples):
            t_curr = n * dt

            def f_duff(x_val, v_val, t_val):
                return gamma * math.cos(omega * t_val) - delta * v_val - alpha * x_val - beta * (x_val ** 3)

            # RK4 Integration
            k1_x = v
            k1_v = f_duff(x, v, t_curr)

            k2_x = v + 0.5 * dt * k1_v
            k2_v = f_duff(x + 0.5 * dt * k1_x, v + 0.5 * dt * k1_v, t_curr + 0.5 * dt)

            k3_x = v + 0.5 * dt * k2_v
            k3_v = f_duff(x + 0.5 * dt * k2_x, v + 0.5 * dt * k2_v, t_curr + 0.5 * dt)

            k4_x = v + dt * k3_v
            k4_v = f_duff(x + dt * k3_x, v + dt * k3_v, t_curr + dt)

            x += (dt / 6.0) * (k1_x + 2.0 * k2_x + 2.0 * k3_x + k4_x)
            v += (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)

            left_chan[n] = x
            right_chan[n] = v / max(1.0, omega * 0.1)

    elif kind == "vanderpol":
        mu = 0.5 + 4.5 * chaos_parameter
        omega0 = 2.0 * np.pi * base_frequency_hz

        x = 0.5
        v = 0.0

        for n in range(total_samples):
            def f_vdp(x_val, v_val):
                return mu * (1.0 - x_val ** 2) * v_val - (omega0 ** 2) * x_val

            k1_x = v
            k1_v = f_vdp(x, v)

            k2_x = v + 0.5 * dt * k1_v
            k2_v = f_vdp(x + 0.5 * dt * k1_x, v + 0.5 * dt * k1_v)

            k3_x = v + 0.5 * dt * k2_v
            k3_v = f_vdp(x + 0.5 * dt * k2_x, v + 0.5 * dt * k2_v)

            k4_x = v + dt * k3_v
            k4_v = f_vdp(x + dt * k3_x, v + dt * k3_v)

            x += (dt / 6.0) * (k1_x + 2.0 * k2_x + 2.0 * k3_x + k4_x)
            v += (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)

            left_chan[n] = x
            right_chan[n] = v / max(1.0, omega0 * 0.1)

    elif kind == "lorenz":
        sigma = 10.0
        rho = 28.0 + 15.0 * chaos_parameter
        beta = 8.0 / 3.0
        # Time dilation to bring Lorenz dynamics into audible range
        time_warp = base_frequency_hz * 0.15

        x, y, z = 0.1, 0.0, 0.0

        for n in range(total_samples):
            def f_lorenz(xv, yv, zv):
                dx = sigma * (yv - xv) * time_warp
                dy = (xv * (rho - zv) - yv) * time_warp
                dz = (xv * yv - beta * zv) * time_warp
                return dx, dy, dz

            k1_x, k1_y, k1_z = f_lorenz(x, y, z)
            k2_x, k2_y, k2_z = f_lorenz(x + 0.5 * dt * k1_x, y + 0.5 * dt * k1_y, z + 0.5 * dt * k1_z)
            k3_x, k3_y, k3_z = f_lorenz(x + 0.5 * dt * k2_x, y + 0.5 * dt * k2_y, z + 0.5 * dt * k2_z)
            k4_x, k4_y, k4_z = f_lorenz(x + dt * k3_x, y + dt * k3_y, z + dt * k3_z)

            x += (dt / 6.0) * (k1_x + 2.0 * k2_x + 2.0 * k3_x + k4_x)
            y += (dt / 6.0) * (k1_y + 2.0 * k2_y + 2.0 * k3_y + k4_y)
            z += (dt / 6.0) * (k1_z + 2.0 * k2_z + 2.0 * k3_z + k4_z)

            left_chan[n] = x
            right_chan[n] = y

    # Stereo widening / pan matrix
    mid = 0.5 * (left_chan + right_chan)
    side = 0.5 * (left_chan - right_chan)
    left_chan = mid + side * (1.0 + stereo_spread)
    right_chan = mid - side * (1.0 + stereo_spread)

    # Fade in / out
    fade_len = int(0.04 * sr)
    if fade_len > 0:
        ramp = np.linspace(0.0, 1.0, fade_len)
        left_chan[:fade_len] *= ramp
        right_chan[:fade_len] *= ramp
        left_chan[-fade_len:] *= ramp[::-1]
        right_chan[-fade_len:] *= ramp[::-1]

    # Peak normalization
    peak = max(np.max(np.abs(left_chan)), np.max(np.abs(right_chan)))
    if peak > 1e-6:
        left_chan = (left_chan / peak) * 0.88
        right_chan = (right_chan / peak) * 0.88

    # Centralized export
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Chaotic_Attractors"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"Chaos_{kind.capitalize()}_{int(base_frequency_hz)}Hz_drive{int(chaos_parameter*100)}_{int(duration_sec)}s.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    stereo_out = np.stack([left_chan, right_chan], axis=1)
    int16_out = np.clip(stereo_out * 32767.0, -32768, 32767).astype(np.int16)

    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_out.tobytes())

    return {
        "status": "SUCCESS",
        "attractor_type": kind,
        "base_frequency_hz": base_frequency_hz,
        "chaos_parameter": chaos_parameter,
        "duration_sec": duration_sec,
        "stereo_spread": stereo_spread,
        "numerical_integrator": "Runge-Kutta 4th Order (RK4)",
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = synthesize_chaotic_attractor_oscillator(attractor_type="duffing", base_frequency_hz=110.0, duration_sec=3.0)
    print("Chaos Oscillator Output:", res)
