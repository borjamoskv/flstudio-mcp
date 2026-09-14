#!/usr/bin/env python3
"""
Homomorphic Cepstral Deconvolver & Formant Transplant Engine (v20.0 Sovereign Transcendence)
═════════════════════════════════════════════════════════════════════════════════════════════
Implements Oppenheim & Schafer homomorphic signal processing to deconvolve source excitation
and acoustic vocal/body resonance filters in the quefrency domain.

Mechanics:
1. Real Cepstrum Transformation:
   c[n] = IFFT(ln |FFT(x[n])| + eps)
   Converts multiplicative convolution s(t) = e(t) * h(t) into additive quefrency components:
   c_s[n] = c_e[n] + c_h[n]
2. Low-Quefrency Liftering (Filter Extraction):
   Applies a smooth liftering window over quefrency index n < n_cutoff (~3ms) to isolate
   formant structure and acoustic instrument body resonances H(omega).
3. High-Quefrency Liftering (Pitch Excitation Extraction):
   Isolates fundamental frequency f0 impulse train c_e[n].
4. Acoustic Formant Transplant / Cross-Deconvolution:
   Impresses the deconvolved resonance envelope of a modulator source onto a target carrier,
   allowing acoustic flamenco body resonances or vocal formants to reshape electronic stems.
5. Centralized WAV export to ~/Music/FL Studio Bounces/Cepstral_Deconvolved/
"""

import math
import wave
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger("FLStudio-Cepstrum")


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


def deconvolve_homomorphic_cepstrum(
    input_wav: Optional[str] = None,
    resonance_source_wav: Optional[str] = None,
    quefrency_cutoff_ms: float = 2.8,
    formant_emphasis_db: float = 6.0,
    max_duration_sec: float = 4.0,
    output_wav: Optional[str] = None
) -> Dict[str, Any]:
    """
    Deconvolves source excitation from spectral envelope using homomorphic real cepstrum.
    If resonance_source_wav is provided, transplants its acoustic body resonance onto input_wav.
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
        audio = 0.5 * np.sin(2 * np.pi * 110.0 * t) + 0.3 * np.sin(2 * np.pi * 220.0 * t)
        filename_tag = "Synthetic_Carrier"
    else:
        audio, sr = _load_wav_mono(target_path, max_sec=max_duration_sec)
        filename_tag = target_path.stem

    # Resonance source audio
    res_path = None
    if resonance_source_wav:
        rp = Path(resonance_source_wav).expanduser().resolve()
        if rp.exists():
            res_path = rp

    if res_path:
        res_audio, _ = _load_wav_mono(res_path, max_sec=max_duration_sec)
    else:
        res_audio = audio

    # STFT Analysis Parameters
    n_fft = 2048
    hop = 512
    window = np.hanning(n_fft)
    cutoff_samples = int(sr * (quefrency_cutoff_ms * 1e-3))
    cutoff_samples = max(4, min(n_fft // 4, cutoff_samples))

    # Low-pass lifter window (half Hanning taper)
    lifter = np.zeros(n_fft, dtype=np.float64)
    lifter[:cutoff_samples] = 1.0
    taper_len = min(cutoff_samples // 2, 16)
    if taper_len > 0:
        lifter[cutoff_samples - taper_len : cutoff_samples] = np.hanning(taper_len * 2)[taper_len:]
    # Symmetric lifter for real cepstrum
    lifter[-cutoff_samples:] = lifter[:cutoff_samples][::-1]

    # Process STFT frames
    num_frames = (len(audio) - n_fft) // hop
    if num_frames < 1:
        audio = np.pad(audio, (0, n_fft * 2))
        num_frames = 2

    out_signal = np.zeros(len(audio), dtype=np.float64)
    window_sum = np.zeros(len(audio), dtype=np.float64)

    total_pitch_peaks_detected = 0

    for i in range(num_frames):
        start = i * hop
        frame_in = audio[start : start + n_fft] * window
        X_in = np.fft.fft(frame_in)
        mag_in = np.abs(X_in) + 1e-12
        phase_in = np.angle(X_in)

        # Real Cepstrum of carrier
        cep_in = np.real(np.fft.ifft(np.log(mag_in)))

        # Excitation part (high-quefrency)
        cep_excitation = cep_in * (1.0 - lifter)

        # Detect pitch peak in quefrency excitation
        search_region = cep_excitation[cutoff_samples : n_fft // 2]
        if len(search_region) > 0 and np.max(search_region) > 0.05:
            total_pitch_peaks_detected += 1

        # Resonance part from resonance source or self
        if res_path and i * hop + n_fft <= len(res_audio):
            frame_res = res_audio[start : start + n_fft] * window
            X_res = np.fft.fft(frame_res)
            mag_res = np.abs(X_res) + 1e-12
            cep_res = np.real(np.fft.ifft(np.log(mag_res)))
            cep_envelope = cep_res * lifter
        else:
            cep_envelope = cep_in * lifter

        # Recombine excitation + shaped envelope
        emphasis_scale = 10.0 ** (formant_emphasis_db / 20.0)
        recombined_cep = cep_excitation + cep_envelope * (1.0 + 0.1 * (emphasis_scale - 1.0))

        # Invert from cepstrum back to log-magnitude and spectrum
        recombined_log_mag = np.real(np.fft.fft(recombined_cep))
        new_mag = np.exp(recombined_log_mag)

        # Reconstruct complex spectrum with original phase
        X_out = new_mag * np.exp(1j * phase_in)
        frame_out = np.real(np.fft.ifft(X_out)) * window

        out_signal[start : start + n_fft] += frame_out
        window_sum[start : start + n_fft] += window ** 2

    # Overlap-add normalization
    valid = window_sum > 1e-4
    out_signal[valid] /= window_sum[valid]

    # Peak normalize
    peak = np.max(np.abs(out_signal))
    if peak > 1e-6:
        out_signal = (out_signal / peak) * 0.88

    # Centralized export
    out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Cepstral_Deconvolved"
    out_dir.mkdir(parents=True, exist_ok=True)

    mode_label = "Transplanted" if res_path else "Reshaped"
    if not output_wav:
        out_file = out_dir / f"Cepstral_{filename_tag}_{mode_label}_{quefrency_cutoff_ms:.1f}ms.wav"
    else:
        out_file = Path(output_wav).expanduser().resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

    int16_out = np.clip(out_signal * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(out_file), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(int16_out.tobytes())

    return {
        "status": "SUCCESS",
        "input_source": str(target_path) if target_path else "synthetic_reference",
        "resonance_source": str(res_path) if res_path else "self_deconvolution",
        "duration_sec": round(len(out_signal) / sr, 2),
        "quefrency_cutoff_ms": quefrency_cutoff_ms,
        "cutoff_samples": cutoff_samples,
        "formant_emphasis_db": formant_emphasis_db,
        "pitch_frames_tracked": total_pitch_peaks_detected,
        "output_file": str(out_file),
        "file_size_kb": round(out_file.stat().st_size / 1024, 1)
    }


if __name__ == "__main__":
    res = deconvolve_homomorphic_cepstrum(quefrency_cutoff_ms=2.8, formant_emphasis_db=6.0)
    print("Cepstral Deconvolver Output:", res)
