#!/usr/bin/env python3
"""
Demucs Isolated Orchestrator:
Runs Demucs chunks in isolated sub-processes, freeing memory at Ring-0 between chunks.
Stitches the final stems using equal-power crossfading.
"""

import sys
import time
import subprocess
import logging
from pathlib import Path
import numpy as np
import scipy.io.wavfile as wav

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IsolatedDemucsOrchestrator")

PYTHON_EXE = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3"


def orchestrate_demucs(input_wav: str, final_out_dir: str, chunk_s: float = 75.0, overlap_s: float = 4.0):
    in_path = Path(input_wav).resolve()
    final_out = Path(final_out_dir).resolve()
    final_out.mkdir(parents=True, exist_ok=True)

    chunks_dir = final_out / "raw_chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    sr, full_data = wav.read(str(in_path))
    total_samples = full_data.shape[0]
    total_s = total_samples / sr
    logger.info(f"Target: {in_path.name} | Duration: {total_s:.2f}s ({total_samples} samples) | Sample Rate: {sr} Hz")

    step_s = chunk_s - overlap_s
    worker_script = Path(__file__).parent / "demucs_isolated_chunk_worker.py"

    # 1. Compute intervals
    intervals = []
    start_s = 0.0
    idx = 0
    while start_s < total_s:
        end_s = min(start_s + chunk_s, total_s)
        intervals.append((idx, start_s, end_s))
        start_s += step_s
        idx += 1

    logger.info(f"Generated {len(intervals)} isolated chunk tasks (each ~{chunk_s}s with {overlap_s}s overlap).")
    t0 = time.time()

    # 2. Execute each chunk in a fresh OS sub-process
    for chunk_idx, st_s, en_s in intervals:
        chunk_out_dir = chunks_dir / f"chunk_{chunk_idx:02d}"
        # Check if already processed
        if (chunk_out_dir / "drums.wav").exists() and (chunk_out_dir / "bass.wav").exists():
            logger.info(f"Chunk {chunk_idx + 1}/{len(intervals)} already exists on disk. Skipping.")
            continue

        logger.info(f"Launching isolated worker for Chunk {chunk_idx + 1}/{len(intervals)} ({st_s:.1f}s - {en_s:.1f}s)...")
        cmd = [
            PYTHON_EXE,
            str(worker_script),
            str(in_path),
            str(chunk_idx),
            f"{st_s:.2f}",
            f"{en_s:.2f}",
            str(chunks_dir)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            logger.error(f"Worker failed for chunk {chunk_idx}:\n{res.stderr}")
            sys.exit(res.returncode)
        logger.info(f"Chunk {chunk_idx + 1}/{len(intervals)} complete.")

    logger.info(f"All {len(intervals)} chunks extracted in {time.time() - t0:.2f}s! Now stitching with equal-power crossfade...")

    # 3. Stitch stems
    sources = ["drums", "bass", "other", "vocals"]
    overlap_samples = int(overlap_s * sr)

    fade_in = np.sin(0.5 * np.pi * np.linspace(0.0, 1.0, overlap_samples, dtype=np.float32)) ** 2
    fade_out = np.cos(0.5 * np.pi * np.linspace(0.0, 1.0, overlap_samples, dtype=np.float32)) ** 2

    for s in sources:
        logger.info(f"Stitching source '{s}' across all {len(intervals)} chunks...")
        stem_accum = np.zeros((total_samples, 2), dtype=np.float32)
        weight_accum = np.zeros(total_samples, dtype=np.float32)

        for chunk_idx, st_s, en_s in intervals:
            c_file = chunks_dir / f"chunk_{chunk_idx:02d}" / f"{s}.wav"
            c_sr, c_data = wav.read(str(c_file))
            c_float = c_data.astype(np.float32) / 32768.0

            st_samp = int(st_s * sr)
            cur_len = c_float.shape[0]
            en_samp = st_samp + cur_len

            w_chunk = np.ones(cur_len, dtype=np.float32)
            if chunk_idx > 0 and cur_len >= overlap_samples:
                w_chunk[:overlap_samples] = fade_in
            if chunk_idx < len(intervals) - 1 and cur_len >= overlap_samples:
                w_chunk[-overlap_samples:] = fade_out

            stem_accum[st_samp:en_samp] += c_float * w_chunk[:, None]
            weight_accum[st_samp:en_samp] += w_chunk

        # Normalize by weights
        weight_accum = np.maximum(weight_accum, 1e-6)
        stem_final = stem_accum / weight_accum[:, None]
        stem_final = np.clip(stem_final, -1.0, 1.0)
        stem_i16 = (stem_final * 32767.0).astype(np.int16)

        final_file = final_out / f"{s}.wav"
        wav.write(str(final_file), sr, stem_i16)
        logger.info(f"Saved final stem: {final_file}")

    logger.info(f"Complete separation pipeline successfully concluded in {time.time() - t0:.2f}s!")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: demucs_isolated_orchestrator.py <input_wav> <final_out_dir>")
        sys.exit(1)
    orchestrate_demucs(sys.argv[1], sys.argv[2])
