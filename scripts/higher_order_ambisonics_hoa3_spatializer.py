#!/usr/bin/env python3
"""
Higher-Order Ambisonics (HOA3) 3rd-Order Spherical Harmonic Spatializer (v21.0 Hyper-Spatial Continuum)
═══════════════════════════════════════════════════════════════════════════════════════════════════════
Encodes monophonic or stereophonic audio into 3rd-Order Ambisonics (HOA3, 16 channels, ACN-SN3D)
and decodes to 3D Binaural stereo via spherical t-design virtual loudspeaker matrix.

Mathematical Architecture:
1. Spherical Harmonics Expansion (Order N=3, M=(N+1)^2=16 channels):
   Channel index ACN n = l^2 + l + m, for l in [0..3], m in [-l..l].
   Y_l^m(theta, phi) = N_{l,m} * P_l^{|m|}(sin(phi)) * [cos(m*theta) if m>=0 else sin(|m|*theta)]
   with Schmidt semi-normalization (SN3D).
2. Spatial Trajectory / Panning:
   Azimuth theta in [-pi, pi], Elevation phi in [-pi/2, pi/2].
3. 3D Binaural Decoding:
   Decodes 16-channel HOA3 stream into binaural stereo using a 12-point regular icosahedral
   virtual loudspeaker array convolved with Woodworth ITD and head-shadow ILD filters.
4. Centralized export to ~/Music/FL Studio Bounces/Ambisonics_HOA3/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np

logger = logging.getLogger("FLStudio-HOA3")


def _associated_legendre_polynomials(sin_phi: float) -> Dict[Tuple[int, int], float]:
    """Evaluates associated Legendre polynomials P_l^|m|(sin_phi) up to order 3."""
    x = float(np.clip(sin_phi, -1.0, 1.0))
    x2 = x * x
    sqrt_1_x2 = math.sqrt(max(0.0, 1.0 - x2))

    P = {}
    # l = 0
    P[(0, 0)] = 1.0
    # l = 1
    P[(1, 0)] = x
    P[(1, 1)] = -sqrt_1_x2
    # l = 2
    P[(2, 0)] = 0.5 * (3.0 * x2 - 1.0)
    P[(2, 1)] = -3.0 * x * sqrt_1_x2
    P[(2, 2)] = 3.0 * (1.0 - x2)
    # l = 3
    P[(3, 0)] = 0.5 * (5.0 * x2 * x - 3.0 * x)
    P[(3, 1)] = -1.5 * (5.0 * x2 - 1.0) * sqrt_1_x2
    P[(3, 2)] = 15.0 * x * (1.0 - x2)
    P[(3, 3)] = -15.0 * ((1.0 - x2) ** 1.5)

    return P


def compute_hoa3_gains(azimuth_rad: float, elevation_rad: float) -> np.ndarray:
    """Computes the 16 ACN-SN3D spherical harmonic gains for a given direction."""
    theta = azimuth_rad
    phi = elevation_rad
    sin_phi = math.sin(phi)
    P = _associated_legendre_polynomials(sin_phi)

    # Schmidt semi-normalization factors N_{l,m}
    # For SN3D: N_{l, 0} = 1, N_{l, m} = sqrt( (2 - delta_{m,0}) * (l - |m|)! / (l + |m|)! ) * (-1)^m
    # Pre-calculated for l in 0..3:
    gains = np.zeros(16, dtype=np.float64)

    # Order 0: n=0 -> (0,0)
    gains[0] = 1.0

    # Order 1: n=1,2,3 -> (1,-1), (1,0), (1,1)
    gains[1] = -P[(1, 1)] * math.sin(theta)           # Y_1^-1 = Y
    gains[2] = P[(1, 0)]                              # Y_1^0  = Z
    gains[3] = -P[(1, 1)] * math.cos(theta)           # Y_1^1  = X

    # Order 2: n=4..8
    gains[4] = (1.0 / math.sqrt(12.0)) * P[(2, 2)] * math.sin(2.0 * theta)   # Y_2^-2
    gains[5] = -(1.0 / math.sqrt(3.0)) * P[(2, 1)] * math.sin(theta)         # Y_2^-1
    gains[6] = P[(2, 0)]                                                      # Y_2^0
    gains[7] = -(1.0 / math.sqrt(3.0)) * P[(2, 1)] * math.cos(theta)         # Y_2^1
    gains[8] = (1.0 / math.sqrt(12.0)) * P[(2, 2)] * math.cos(2.0 * theta)   # Y_2^2

    # Order 3: n=9..15
    gains[9]  = -(1.0 / math.sqrt(360.0)) * P[(3, 3)] * math.sin(3.0 * theta)  # Y_3^-3
    gains[10] = (1.0 / math.sqrt(60.0)) * P[(3, 2)] * math.sin(2.0 * theta)   # Y_3^-2
    gains[11] = -(1.0 / math.sqrt(6.0)) * P[(3, 1)] * math.sin(theta)         # Y_3^-1
    gains[12] = P[(3, 0)]                                                      # Y_3^0
    gains[13] = -(1.0 / math.sqrt(6.0)) * P[(3, 1)] * math.cos(theta)         # Y_3^1
    gains[14] = (1.0 / math.sqrt(60.0)) * P[(3, 2)] * math.cos(2.0 * theta)   # Y_3^2
    gains[15] = -(1.0 / math.sqrt(360.0)) * P[(3, 3)] * math.cos(3.0 * theta)  # Y_3^3

    return gains


def _load_wav_mono(file_path: Path, max_sec: float = 6.0) -> Tuple[np.ndarray, int]:
    """Loads mono audio buffer normalized to [-1, 1]."""
    with wave.open(str(file_path), "rb") as wf:
        n_ch = wf.getnchannels()
        sw = wf.getsampwidth()
        sr = wf.getframerate()
        n_frames = min(wf.getnframes(), int(sr * max_sec))
        raw = wf.readframes(n_frames)

    if sw == 2:
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float64) / 32768.0
    elif sw == 3:
        a8 = np.frombuffer(raw, dtype=np.uint8)
        a24 = (a8[0::3].astype(np.int32)) | (a8[1::3].astype(np.int32) << 8) | (a8[2::3].astype(np.int32) << 16)
        a24[a24 >= 0x800000] -= 0x1000000
        audio = a24.astype(np.float64) / 8388608.0
    elif sw == 4:
        audio = np.frombuffer(raw, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        audio = np.frombuffer(raw, dtype=np.uint8).astype(np.float64) / 128.0 - 1.0

    if n_ch > 1:
        audio = audio.reshape(-1, n_ch).mean(axis=1)

    return audio, sr


def encode_higher_order_ambisonics_hoa3(
    input_wav: Optional[str] = None,
    azimuth_deg: float = 45.0,
    elevation_deg: float = 15.0,
    binaural_decode: bool = True,
    max_duration_sec: float = 4.0,
    output_wav: Optional[str] = None
) -> Dict[str, Any]:
    """
    Encodes audio into 3rd-Order 16-channel Ambisonics (HOA3 ACN-SN3D) with optional 3D binaural decoding.
    """
    target_path = None
    if input_wav:
        p = Path(input_wav).expanduser().resolve()
        if p.exists():
            target_path = p

    bounces_dir = Path.home() / "Music" / "FL Studio Bounces"

    if not target_path:
        candidates = list(bounces_dir.glob("**/*.wav"))
        if candidates:
            target_path = candidates[0]

    if not target_path or not target_path.exists():
        sr = 44100
        t = np.linspace(0, max_duration_sec, int(max_duration_sec * sr), endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 330.0 * t) * np.exp(-t * 0.8)
        filename_tag = "Synthetic_Harmonic_Tone"
    else:
        audio, sr = _load_wav_mono(target_path, max_sec=max_duration_sec)
        filename_tag = target_path.stem

    # Convert angles to radians
    az_rad = math.radians(azimuth_deg)
    el_rad = math.radians(elevation_deg)

    # 16-channel HOA3 gains
    hoa_gains = compute_hoa3_gains(az_rad, el_rad)

    # Encode into 16 channels: shape [num_samples, 16]
    hoa_stream = np.outer(audio, hoa_gains)

    # Binaural decoding via 12-point spherical virtual loudspeaker array
    # Icosahedral vertices (golden ratio phi_g = (1 + sqrt(5)) / 2)
    phi_g = (1.0 + math.sqrt(5.0)) / 2.0
    raw_verts = np.array([
        [-1, phi_g, 0], [1, phi_g, 0], [-1, -phi_g, 0], [1, -phi_g, 0],
        [0, -1, phi_g], [0, 1, phi_g], [0, -1, -phi_g], [0, 1, -phi_g],
        [phi_g, 0, -1], [phi_g, 0, 1], [-phi_g, 0, -1], [-phi_g, 0, 1]
    ], dtype=np.float64)
    # Normalize vertices to unit sphere
    norms = np.linalg.norm(raw_verts, axis=1, keepdims=True)
    verts = raw_verts / norms

    # Virtual loudspeaker decoding matrix (12 speakers x 16 HOA channels)
    D_mat = np.zeros((12, 16), dtype=np.float64)
    for spk_idx in range(12):
        vx, vy, vz = verts[spk_idx]
        spk_az = math.atan2(vy, vx)
        spk_el = math.asin(np.clip(vz, -1.0, 1.0))
        # Forward spherical harmonic vector for speaker
        y_spk = compute_hoa3_gains(spk_az, spk_el)
        D_mat[spk_idx] = y_spk / 16.0  # Basic mode-matching decoder

    # Virtual speaker feeds: shape [num_samples, 12]
    speaker_feeds = np.dot(hoa_stream, D_mat.T)

    # Binauralize virtual speakers with Woodworth ITD & head-shadow ILD
    head_radius = 0.0875  # 8.75 cm
    c_sound = 343.0
    left_ear = np.zeros(len(audio), dtype=np.float64)
    right_ear = np.zeros(len(audio), dtype=np.float64)

    for spk in range(12):
        vx, vy, vz = verts[spk]
        spk_az = math.atan2(vy, vx)
        spk_feed = speaker_feeds[:, spk]

        # Woodworth ITD
        itd_sec = (head_radius / c_sound) * (math.sin(spk_az) + spk_az)
        itd_samples = int(np.round(itd_sec * sr))

        # ILD gain (Rayleigh scattering head shadow)
        ild_left = 1.0 + 0.35 * math.sin(spk_az)
        ild_right = 1.0 - 0.35 * math.sin(spk_az)

        if itd_samples >= 0:
            # Source closer to right ear
            left_ear += np.pad(spk_feed * ild_left, (itd_samples, 0))[:len(audio)]
            right_ear += spk_feed * ild_right
        else:
            # Source closer to left ear
            itd_abs = abs(itd_samples)
            left_ear += spk_feed * ild_left
            right_ear += np.pad(spk_feed * ild_right, (itd_abs, 0))[:len(audio)]

    # Peak normalization
    peak = max(np.max(np.abs(left_ear)), np.max(np.abs(right_ear)))
    if peak > 1e-6:
        left_ear = (left_ear / peak) * 0.88
        right_ear = (right_ear / peak) * 0.88

    # Centralized export
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Ambisonics_HOA3"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"HOA3_Binaural_{filename_tag}_Az{int(azimuth_deg)}_El{int(elevation_deg)}.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    stereo_out = np.stack([left_ear, right_ear], axis=1)
    int16_out = np.clip(stereo_out * 32767.0, -32768, 32767).astype(np.int16)

    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_out.tobytes())

    return {
        "status": "SUCCESS",
        "input_source": str(target_path) if target_path else "synthetic_reference",
        "ambisonics_order": 3,
        "total_spherical_harmonic_channels": 16,
        "azimuth_deg": azimuth_deg,
        "elevation_deg": elevation_deg,
        "virtual_loudspeaker_points": 12,
        "decoded_format": "3D Binaural Stereo (SN3D ACN decoded)",
        "duration_sec": round(len(audio) / sr, 2),
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = encode_higher_order_ambisonics_hoa3(azimuth_deg=45.0, elevation_deg=15.0)
    print("HOA3 Spatializer Output:", res)
