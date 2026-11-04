#!/usr/bin/env python3
"""
Demucs Isolated Chunk Worker: Runs 1 chunk in a standalone process and exits.
Guarantees 100% OS kernel memory reclamation on process termination.
"""

import sys
from pathlib import Path
import numpy as np
import scipy.io.wavfile as wav
import torch

from demucs.pretrained import get_model
from demucs.apply import apply_model


def run_worker(input_wav: str, chunk_idx: int, start_s: float, end_s: float, out_dir: str):
    out_path = Path(out_dir) / f"chunk_{chunk_idx:02d}"
    out_path.mkdir(parents=True, exist_ok=True)

    sr, full_data = wav.read(input_wav)
    start_samp = int(start_s * sr)
    end_samp = min(int(end_s * sr), full_data.shape[0])

    chunk_data = full_data[start_samp:end_samp]
    if chunk_data.dtype == np.int16:
        audio = chunk_data.astype(np.float32) / 32768.0
    elif chunk_data.dtype == np.int32:
        audio = chunk_data.astype(np.float32) / 2147483648.0
    else:
        audio = chunk_data.astype(np.float32)

    if audio.ndim == 1:
        audio = np.column_stack([audio, audio])
    else:
        audio = audio[:, :2]

    chunk_tensor = torch.from_numpy(audio.T).unsqueeze(0)  # [1, 2, N]

    model = get_model("htdemucs")
    model.eval()

    with torch.no_grad():
        out = apply_model(model, chunk_tensor, shifts=0, split=True, device="cpu")

    out_np = out.squeeze(0).numpy()  # [4, 2, N]
    sources = model.sources

    for idx, s in enumerate(sources):
        stem_audio = np.clip(out_np[idx].T, -1.0, 1.0)
        stem_i16 = (stem_audio * 32767.0).astype(np.int16)
        wav.write(str(out_path / f"{s}.wav"), sr, stem_i16)

    print(f"SUCCESS: chunk_{chunk_idx:02d} ({start_s:.1f}s - {end_s:.1f}s) written to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: demucs_isolated_chunk_worker.py <input_wav> <chunk_idx> <start_s> <end_s> <out_dir>")
        sys.exit(1)
    run_worker(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5])
