#!/usr/bin/env python3
"""
Wave Digital Filter (WDF) Analog Saturator & Tone Stack (v17.0 Hyper-Dimensional Omni)
Implements Alfred Fettweis Wave Digital Filter formalism for non-linear analog tube/diode
saturation and classic 3-band passive RC tone stack emulation with anti-aliased oversampling.

Architecture:
- Incident and reflected wave decomposition: a = v + R0*i, b = v - R0*i
- Non-linear diode/triode junction resolved via fast Newton-Raphson root finding
- 4x polyphase oversampling for anti-aliasing protection
- Analog 3-band passive tone stack (Bass 100Hz, Mid 800Hz, Treble 3.2kHz)
- Centralized WAV export to ~/Music/FL Studio Bounces/Analog_WDF/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import signal

logger = logging.getLogger("FLStudio-WDF")


def load_wav_as_mono_float(wav_path: str) -> Tuple[np.ndarray, int]:
    """Reads a WAV file and returns normalized mono float64 array and sample rate."""
    with wave.open(wav_path, "rb") as wf:
        num_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        num_frames = wf.getnframes()
        raw_bytes = wf.readframes(num_frames)

    if sampwidth == 2:
        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float64) / 32768.0
    elif sampwidth == 3:
        int_data = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3)
        int32 = (int_data[:, 0].astype(np.int32) |
                 (int_data[:, 1].astype(np.int32) << 8) |
                 (int_data[:, 2].astype(np.int32) << 16))
        int32 = np.where(int32 >= 0x800000, int32 - 0x1000000, int32)
        audio = int32.astype(np.float64) / 8388608.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float64) / 2147483648.0
    else:
        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float64) / 32768.0

    if num_channels > 1:
        audio = audio.reshape(-1, num_channels).mean(axis=1)
    return audio, framerate


def solve_wdf_diode_pair(a: np.ndarray, R0: float = 1000.0, Is: float = 2.5e-9, Vt: float = 0.026) -> np.ndarray:
    """
    Vectorized Newton-Raphson solver for antiparallel diode pair in WDF domain:
    f(b) = b - a + 2 * R0 * Is * sinh((a + b) / (2 * Vt)) = 0
    Converges in 4 iterations.
    """
    b = np.copy(a) * 0.5  # Initial guess
    two_R0_Is = 2.0 * R0 * Is
    inv_2Vt = 1.0 / (2.0 * Vt)

    for _ in range(4):
        v = (a + b) * inv_2Vt
        v_clipped = np.clip(v, -30.0, 30.0)
        sinh_v = np.sinh(v_clipped)
        cosh_v = np.cosh(v_clipped)

        f = b - a + two_R0_Is * sinh_v
        df = 1.0 + two_R0_Is * inv_2Vt * cosh_v
        b -= f / df

    return b


def apply_analog_tone_stack(
    x: np.ndarray,
    sr: int,
    bass_norm: float = 0.5,
    mid_norm: float = 0.5,
    treble_norm: float = 0.5
) -> np.ndarray:
    """
    Models passive 3-band analog tone stack (Bass, Mid, Treble).
    - bass_norm: 0.0 to 1.0 (100 Hz shelf, +/- 10 dB)
    - mid_norm: 0.0 to 1.0 (800 Hz peak, +/- 8 dB)
    - treble_norm: 0.0 to 1.0 (3.2 kHz shelf, +/- 10 dB)
    """
    y = np.copy(x)

    # Bass shelf at 100 Hz
    bass_gain_db = (bass_norm - 0.5) * 20.0
    if abs(bass_gain_db) > 0.5:
        sos_bass = signal.iirfilter(2, 100.0 / (sr / 2.0), btype="lowpass", output="sos")
        bass_component = signal.sosfilt(sos_bass, y)
        scale = 10.0 ** (bass_gain_db / 20.0) - 1.0
        y += bass_component * scale

    # Mid peak at 800 Hz
    mid_gain_db = (mid_norm - 0.5) * 16.0
    if abs(mid_gain_db) > 0.5:
        sos_mid = signal.iirfilter(2, [600.0 / (sr / 2.0), 1100.0 / (sr / 2.0)], btype="bandpass", output="sos")
        mid_component = signal.sosfilt(sos_mid, y)
        scale = 10.0 ** (mid_gain_db / 20.0) - 1.0
        y += mid_component * scale

    # Treble shelf at 3200 Hz
    treble_gain_db = (treble_norm - 0.5) * 20.0
    if abs(treble_gain_db) > 0.5:
        sos_treble = signal.iirfilter(2, 3200.0 / (sr / 2.0), btype="highpass", output="sos")
        treble_component = signal.sosfilt(sos_treble, y)
        scale = 10.0 ** (treble_gain_db / 20.0) - 1.0
        y += treble_component * scale

    return y


def saturate_audio_wdf_analog(
    input_wav: Optional[str] = None,
    output_wav: Optional[str] = None,
    drive_db: float = 6.0,
    tube_bias: float = 0.20,
    tone_bass: float = 0.55,
    tone_mid: float = 0.45,
    tone_treble: float = 0.60,
    mix_wet: float = 0.65
) -> Dict[str, Any]:
    """
    Applies Wave Digital Filter (WDF) analog diode/triode saturation with 4x anti-aliasing
    oversampling and passive 3-band analog tone stack.
    - drive_db: input preamp drive gain (+0 to +24 dB)
    - tube_bias: DC offset asymmetry inducing second-harmonic warmth (0.0 to 0.5)
    - tone_bass, tone_mid, tone_treble: 0.0 to 1.0
    - mix_wet: dry/wet blend ratio (0.0 to 1.0)
    """
    if not input_wav:
        bounces_dir = Path.home() / "Music" / "FL Studio Bounces"
        default_wav = bounces_dir / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
        if not default_wav.exists():
            from scripts.fl_headless_audio_synthesizer import render_headless_dark_cyber_flamenco
            render_headless_dark_cyber_flamenco()
        in_file = default_wav
    else:
        in_file = Path(input_wav).expanduser().resolve()

    if not in_file.exists():
        raise FileNotFoundError(f"Input WAV not found: {in_file}")

    audio, sr = load_wav_as_mono_float(str(in_file))

    # Pre-gain drive
    drive_gain = 10.0 ** (drive_db / 20.0)
    driven_audio = audio * drive_gain + tube_bias

    # 4x Oversampling via SciPy resample_poly
    up_factor = 4
    audio_up = signal.resample_poly(driven_audio, up_factor, 1)

    # WDF Non-Linearity: Voltage to wave variable a
    # a = 2 * v_in
    a_waves = audio_up * 2.0
    # Solve reflected wave b
    b_waves = solve_wdf_diode_pair(a_waves, R0=1200.0, Is=2.0e-9, Vt=0.026)
    # Output voltage v_out = (a + b) / 2
    v_out_up = (a_waves + b_waves) * 0.5

    # 4x Decimation back to base sample rate
    v_out = signal.resample_poly(v_out_up, 1, up_factor)

    # Match length
    if len(v_out) > len(audio):
        v_out = v_out[:len(audio)]
    elif len(v_out) < len(audio):
        v_out = np.pad(v_out, (0, len(audio) - len(v_out)))

    # Remove DC bias offset
    v_out = v_out - np.mean(v_out)

    # Apply 3-band analog tone stack
    v_toned = apply_analog_tone_stack(v_out, sr=sr, bass_norm=tone_bass, mid_norm=tone_mid, treble_norm=tone_treble)

    # Dry/Wet blend
    blended = (1.0 - mix_wet) * audio + mix_wet * v_toned

    # Peak normalization
    peak = np.max(np.abs(blended))
    if peak > 0.99:
        blended = (blended / peak) * 0.95

    # Output directory
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Analog_WDF"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not output_wav:
        out_file = out_dir / f"{in_file.stem}_WDF_AnalogSaturated_{int(drive_db)}dB.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    int16_audio = (blended * 32767.0).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_audio.tobytes())

    return {
        "status": "SUCCESS",
        "input_file": str(in_file),
        "drive_db": drive_db,
        "tube_bias": tube_bias,
        "oversampling_factor": up_factor,
        "tone_stack": {
            "bass": tone_bass,
            "mid": tone_mid,
            "treble": tone_treble
        },
        "mix_wet": mix_wet,
        "duration_sec": round(len(audio) / sr, 2),
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = saturate_audio_wdf_analog(drive_db=8.0, tube_bias=0.25)
    print("WDF Saturator Output:", res)
