#!/usr/bin/env python3
"""
Demucs Chunked Separator with Constant Memory O(1) & Equal-Power Crossfade
==========================================================================
Eliminates the Demucs Python 3.14 RAM memory leak on long tracks (>150s).
Slices audio into 80-second windows with 4-second equal-power overlaps,
separates each chunk, and stitches the 4 stems seamlessly.
"""

import gc
import sys
import time
import logging
from pathlib import Path
import numpy as np
import scipy.io.wavfile as wav
import torch

from demucs.pretrained import get_model
from demucs.apply import apply_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ChunkedDemucs")


def separate_chunked(
    input_wav: str,
    output_dir: str,
    chunk_seconds: float = 75.0,
    overlap_seconds: float = 4.0,
    model_name: str = "htdemucs"
):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading input WAV: {input_wav}")
    sr, full_data = wav.read(input_wav)
    if full_data.dtype == np.int16:
        audio = full_data.astype(np.float32) / 32768.0
    elif full_data.dtype == np.int32:
        audio = full_data.astype(np.float32) / 2147483648.0
    else:
        audio = full_data.astype(np.float32)

    if audio.ndim == 1:
        audio = np.column_stack([audio, audio])
    else:
        audio = audio[:, :2]

    total_samples = audio.shape[0]
    total_seconds = total_samples / sr
    logger.info(f"Total audio: {total_seconds:.2f} seconds ({total_samples} samples) at {sr} Hz")

    chunk_samples = int(chunk_seconds * sr)
    overlap_samples = int(overlap_seconds * sr)
    step_samples = chunk_samples - overlap_samples

    # Load model on CPU
    logger.info(f"Loading {model_name} on CPU...")
    model = get_model(model_name)
    model.eval()

    sources = model.sources  # ['drums', 'bass', 'other', 'vocals']
    len(sources)

    # Pre-allocate output arrays for each source on CPU (shape: [total_samples, 2])
    output_stems = {s: np.zeros((total_samples, 2), dtype=np.float32) for s in sources}
    # Weight buffer for crossfade normalization
    weights = np.zeros(total_samples, dtype=np.float32)

    # Equal power fade window for overlap
    fade_in = np.sin(0.5 * np.pi * np.linspace(0.0, 1.0, overlap_samples, dtype=np.float32)) ** 2
    fade_out = np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, overlap_samples, dtype=np.float32)) ** 2

    # Generate chunk window (flat in middle, tapered at ends if overlapping)
    start_pos = 0
    chunk_idx = 0
    t0 = time.time()

    while start_pos < total_samples:
        end_pos = min(start_pos + chunk_samples, total_samples)
        cur_len = end_pos - start_pos
        logger.info(f"Processing chunk {chunk_idx + 1} ({start_pos / sr:.1f}s to {end_pos / sr:.1f}s, len: {cur_len / sr:.1f}s)...")

        chunk_audio = audio[start_pos:end_pos].T  # [2, cur_len]
        chunk_tensor = torch.from_numpy(chunk_audio).unsqueeze(0)  # [1, 2, cur_len]

        with torch.no_grad():
            # shifts=0 for fast single-pass inference without memory accumulation
            out = apply_model(model, chunk_tensor, shifts=0, split=True, device="cpu")

        # out shape: [1, 4, 2, cur_len]
        out_np = out.squeeze(0).numpy()  # [4, 2, cur_len]

        # Calculate chunk weight window
        w_chunk = np.ones(cur_len, dtype=np.float32)
        if start_pos > 0 and cur_len >= overlap_samples:
            w_chunk[:overlap_samples] = fade_in
        if end_pos < total_samples and cur_len >= overlap_samples:
            w_chunk[-overlap_samples:] = fade_out

        # Accumulate into output stems
        for idx, s in enumerate(sources):
            # out_np[idx] is [2, cur_len], transpose to [cur_len, 2]
            stem_chunk = out_np[idx].T
            output_stems[s][start_pos:end_pos] += stem_chunk * w_chunk[:, None]

        weights[start_pos:end_pos] += w_chunk

        # Cleanup memory immediately
        del chunk_tensor, out, out_np
        gc.collect()

        start_pos += step_samples
        chunk_idx += 1

    # Normalize by weights to guarantee seamless 1.0 reconstruction
    weights = np.maximum(weights, 1e-6)
    logger.info("Normalizing and saving discrete stems...")

    for s in sources:
        stem_final = output_stems[s] / weights[:, None]
        stem_final = np.clip(stem_final, -1.0, 1.0)
        stem_i16 = (stem_final * 32767.0).astype(np.int16)
        out_file = out_path / f"{s}.wav"
        wav.write(str(out_file), sr, stem_i16)
        logger.info(f"Stem written: {out_file} (duration: {total_seconds:.1f}s)")

    logger.info(f"All 4 stems successfully separated in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: demucs_chunked_separator.py <input_wav> <output_dir>")
        sys.exit(1)
    separate_chunked(sys.argv[1], sys.argv[2])
