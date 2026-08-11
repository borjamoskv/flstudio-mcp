#!/usr/bin/env python3
"""
FL Studio Binary & Audio Signal Reverse Engineering Engine
Inspects FL Studio .flp project binaries, .fst preset binaries, and RIFF .wav audio headers.
"""

import sys
import os
import struct

def inspect_wav_binary(file_path):
    with open(file_path, 'rb') as f:
        data = f.read(100)

    if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        return {"error": "Not a valid RIFF/WAVE binary"}

    chunk_size = struct.unpack('<I', data[4:8])[0]
    fmt_id = data[12:16]
    fmt_size = struct.unpack('<I', header_offset := data[16:20])[0]
    audio_format, channels, sample_rate, byte_rate, block_align, bits_per_sample = struct.unpack('<HHIIHH', data[20:36])

    duration_sec = (chunk_size - 36) / byte_rate if byte_rate > 0 else 0

    return {
        "file_type": "RIFF WAVE Audio",
        "audio_format": "PCM Uncompressed" if audio_format == 1 else "IEEE Float",
        "channels": channels,
        "sample_rate_hz": sample_rate,
        "bits_per_sample": bits_per_sample,
        "byte_rate_bytes_per_sec": byte_rate,
        "total_file_bytes": chunk_size + 8,
        "audio_duration_sec": round(duration_sec, 2),
        "bars_at_116bpm": round((duration_sec / 60.0) * (116.0 / 4), 1)
    }

def inspect_fl_binary(file_path):
    with open(file_path, 'rb') as f:
        data = f.read(256)

    if data[:4] != b'FLhd':
        return {"error": "Not a valid FL Studio FLhd binary"}

    hdr_len = struct.unpack('<I', data[4:8])[0]
    fmt_type, channels, ppq = struct.unpack('<HHH', data[8:14])
    chunk_type = data[14:18].decode('ascii', errors='ignore')

    return {
        "file_type": "FL Studio Binary",
        "magic_header": "FLhd",
        "format_type": fmt_type,
        "channel_count": channels,
        "ppq_resolution": ppq,
        "data_chunk_header": chunk_type,
        "raw_hex_head": data[:32].hex()
    }

if __name__ == "__main__":
    wav_file = os.path.expanduser("~/10_PROJECTS/No_Lo_Entiende_Stems/01_kick_selections.wav")
    if os.path.exists(wav_file):
        print("=== WAV BINARY REVERSE ENGINEERING ===")
        print(json_str := inspect_wav_binary(wav_file))
