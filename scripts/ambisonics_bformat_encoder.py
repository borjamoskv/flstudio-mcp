#!/usr/bin/env python3
"""
Ambisonics B-Format 3D Spherical Encoder (v14.0 Continuum)
Encodes audio stems into 1st-Order Ambisonics (FOA) B-format (ambiX / ACN-SN3D)
with full SO(3) Euler head-tracking rotation and spherical coordinates (theta, phi, r).

B-Format Channels:
- Channel 0: W (Omnidirectional pressure, order 0)
- Channel 1: Y (Left-Right dipole, order 1, degree -1)
- Channel 2: Z (Up-Down dipole, order 1, degree 0)
- Channel 3: X (Front-Back dipole, order 1, degree 1)
"""

import math
import wave
import struct
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np

logger = logging.getLogger("FLStudio-Ambisonics")


def euler_rotation_so3(yaw: float, pitch: float, roll: float, x: float, y: float, z: float) -> Tuple[float, float, float]:
    """
    Rotates 3D coordinates via SO(3) rotation matrix R_z(yaw) * R_y(pitch) * R_x(roll).
    Angles in radians for dynamic head-tracking compensation.
    """
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)

    x_rot = (cy * cp) * x + (cy * sp * sr - sy * cr) * y + (cy * sp * cr + sy * sr) * z
    y_rot = (sy * cp) * x + (sy * sp * sr + cy * cr) * y + (sy * sp * cr - cy * sr) * z
    z_rot = (-sp) * x + (cp * sr) * y + (cp * cr) * z

    return x_rot, y_rot, z_rot


def load_wav_as_mono_float(wav_path: str) -> Tuple[np.ndarray, int]:
    """Reads a WAV file and returns normalized mono float64 array (-1.0 to +1.0) and sample rate."""
    with wave.open(wav_path, "rb") as wf:
        num_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        num_frames = wf.getnframes()
        raw_bytes = wf.readframes(num_frames)

    if sampwidth == 2:
        dtype = np.int16
        scale = 32768.0
    elif sampwidth == 3:
        # 24-bit PCM unpack
        int_data = np.frombuffer(raw_bytes, dtype=np.uint8)
        reshaped = int_data.reshape(-1, 3)
        # Sign extend 24-bit to 32-bit
        int32_data = (reshaped[:, 0].astype(np.int32) |
                      (reshaped[:, 1].astype(np.int32) << 8) |
                      (reshaped[:, 2].astype(np.int32) << 16))
        int32_data = np.where(int32_data >= 0x800000, int32_data - 0x1000000, int32_data)
        audio = int32_data.astype(np.float64) / 8388608.0
        if num_channels > 1:
            audio = audio.reshape(-1, num_channels).mean(axis=1)
        return audio, framerate
    elif sampwidth == 4:
        dtype = np.int32
        scale = 2147483648.0
    else:
        dtype = np.int16
        scale = 32768.0

    audio = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float64) / scale
    if num_channels > 1:
        audio = audio.reshape(-1, num_channels).mean(axis=1)
    return audio, framerate


def encode_to_ambisonics_bformat(
    input_wav: str,
    output_wav: Optional[str] = None,
    azimuth_deg: float = 45.0,
    elevation_deg: float = 0.0,
    distance_m: float = 2.0,
    rotate_yaw_deg: float = 0.0,
    rotate_pitch_deg: float = 0.0,
    rotate_roll_deg: float = 0.0,
) -> Dict[str, Any]:
    """
    Encodes mono/stereo WAV into 4-channel Ambisonics B-Format (ambiX ACN-SN3D standard).
    Channels: 0=W, 1=Y, 2=Z, 3=X.
    """
    in_path = Path(input_wav).expanduser().resolve()
    if not in_path.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_path}")

    audio, sample_rate = load_wav_as_mono_float(str(in_path))

    # Spherical coordinates to Cartesian unit vector
    theta_rad = math.radians(azimuth_deg)
    phi_rad = math.radians(elevation_deg)

    x0 = math.cos(theta_rad) * math.cos(phi_rad)
    y0 = math.sin(theta_rad) * math.cos(phi_rad)
    z0 = math.sin(phi_rad)

    # Apply head-tracking rotation in SO(3)
    yaw_rad = math.radians(rotate_yaw_deg)
    pitch_rad = math.radians(rotate_pitch_deg)
    roll_rad = math.radians(rotate_roll_deg)

    x_rot, y_rot, z_rot = euler_rotation_so3(yaw_rad, pitch_rad, roll_rad, x0, y0, z0)

    # Distance attenuation (inverse distance law)
    dist = max(1.0, distance_m)
    gain = 1.0 / dist
    source_signal = audio * gain

    # ambiX ACN / SN3D Encoding
    # ACN 0 (W, 0,0)  = 1.0 * S
    # ACN 1 (Y, 1,-1) = y * S
    # ACN 2 (Z, 1,0)  = z * S
    # ACN 3 (X, 1,1)  = x * S
    num_samples = len(source_signal)
    bformat = np.zeros((num_samples, 4), dtype=np.float32)
    bformat[:, 0] = (source_signal * 1.0).astype(np.float32)       # W
    bformat[:, 1] = (source_signal * y_rot).astype(np.float32)     # Y
    bformat[:, 2] = (source_signal * z_rot).astype(np.float32)     # Z
    bformat[:, 3] = (source_signal * x_rot).astype(np.float32)     # X

    # Target path setup
    if not output_wav:
        out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Ambisonics"
        out_dir.mkdir(parents=True, exist_ok=True)
        stem_name = in_path.stem
        output_file = out_dir / f"{stem_name}_Ambisonics_BFormat_ACN.wav"
    else:
        output_file = Path(output_wav).expanduser().resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write 4-channel 16-bit PCM WAV
    int16_data = np.clip(bformat * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(output_file), "wb") as wf:
        wf.setnchannels(4)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_data.tobytes())

    return {
        "status": "SUCCESS",
        "format": "ambiX_ACN_SN3D_4CH",
        "channels": ["W (Omni)", "Y (Left-Right)", "Z (Up-Down)", "X (Front-Back)"],
        "azimuth_deg": azimuth_deg,
        "elevation_deg": elevation_deg,
        "distance_m": distance_m,
        "head_tracking_rotation": {
            "yaw_deg": rotate_yaw_deg,
            "pitch_deg": rotate_pitch_deg,
            "roll_deg": rotate_roll_deg
        },
        "sample_rate_hz": sample_rate,
        "duration_sec": round(num_samples / sample_rate, 2),
        "output_file": str(output_file),
        "file_size_kb": round(output_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    import sys
    test_in = Path.home() / "Music/FL Studio Bounces/Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    if test_in.exists():
        res = encode_to_ambisonics_bformat(str(test_in), azimuth_deg=45.0, elevation_deg=15.0)
        print("Ambisonics B-Format Encoder output:", res)
    else:
        print("Test file not found:", test_in)
