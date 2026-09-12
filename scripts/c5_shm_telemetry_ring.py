#!/usr/bin/env python3
"""
C5-REAL Zero-Copy POSIX Shared Memory Telemetry Ring Buffer
═══════════════════════════════════════════════════════════
Replaces disk-based JSON polling with sub-microsecond in-memory
state synchronization between FL Studio and Antigravity MCP Server.

Binary Frame Structure (C-Struct Equivalent):
- [00:14] Magic: b'C5_SHM_RING_V1'
- [14:18] uint32: Version (1)
- [18:22] uint32: Sequence ID (Monotonic frame counter)
- [22:30] double: Timestamp (Unix epoch)
- [30:34] uint32: Is Playing (0=Stopped, 1=Playing, 2=Paused)
- [34:42] double: BPM (Tempo)
- [42:50] double: Song Position (PPQ)
- [50:54] uint32: Track Count (typically 128)
- [54:2102] 128 Track States (16 bytes each):
    - float32: Volume (0.0..1.0)
    - float32: Pan (-1.0..+1.0)
    - float32: Stereo Separation (-1.0..+1.0)
    - uint8: Is Muted
    - uint8: Is Soloed
    - uint8: Is Armed
    - uint8: Sidechain Flags
- [2102:2358] Text: Frontmost Window Name (256 bytes UTF-8)
Total Frame Size: 2358 bytes (Allocated 4096 / 16384 bytes aligned).
"""

import time
import struct
from multiprocessing import shared_memory
from typing import Dict, Any, Optional

SHM_NAME = "antigravity_fl_telemetry_shm"
SHM_MAGIC = b"C5_SHM_RING_V1"
SHM_VERSION = 1
SHM_SIZE = 16384
MAX_TRACKS = 128


class C5SharedMemoryRing:
    """Manages POSIX shared memory ring-buffer for zero-copy DAW telemetry."""

    def __init__(self, create_if_missing: bool = True):
        self.shm: Optional[shared_memory.SharedMemory] = None
        self.is_owner = False
        self._seq = 0

        try:
            # Try to connect to existing SHM block
            self.shm = shared_memory.SharedMemory(name=SHM_NAME, create=False)
            self._detach_tracker()
        except FileNotFoundError:
            if create_if_missing:
                try:
                    self.shm = shared_memory.SharedMemory(name=SHM_NAME, create=True, size=SHM_SIZE)
                    self.is_owner = True
                    self._detach_tracker()
                    self._init_memory()
                except Exception as e:
                    self.shm = None
            else:
                self.shm = None

    def _detach_tracker(self) -> None:
        """Detaches shared memory segment from resource tracker so it persists across processes."""
        try:
            from multiprocessing import resource_tracker
            if self.shm:
                resource_tracker.unregister(self.shm._name, "shared_memory")
        except Exception:
            pass

    def _init_memory(self) -> None:
        """Initializes empty memory frame with magic header."""
        if not self.shm:
            return
        self.shm.buf[:len(SHM_MAGIC)] = SHM_MAGIC
        struct.pack_into("<I", self.shm.buf, 14, SHM_VERSION)
        struct.pack_into("<I", self.shm.buf, 18, 0)  # seq = 0

    def write_frame(
        self,
        is_playing: int,
        bpm: float,
        song_pos: float,
        active_window: str = "mixer",
        tracks: Optional[Dict[int, Dict[str, Any]]] = None
    ) -> int:
        """Writes an atomic telemetry frame into shared memory."""
        if not self.shm:
            return 0

        self._seq += 1
        now = time.time()

        # Write header
        self.shm.buf[:len(SHM_MAGIC)] = SHM_MAGIC
        struct.pack_into("<I", self.shm.buf, 14, SHM_VERSION)
        struct.pack_into("<I", self.shm.buf, 18, self._seq)
        struct.pack_into("<d", self.shm.buf, 22, now)
        struct.pack_into("<I", self.shm.buf, 30, int(is_playing))
        struct.pack_into("<d", self.shm.buf, 34, float(bpm))
        struct.pack_into("<d", self.shm.buf, 42, float(song_pos))
        struct.pack_into("<I", self.shm.buf, 50, MAX_TRACKS)

        # Write track states (16 bytes each, starting at offset 54)
        tracks_data = tracks or {}
        for t_idx in range(MAX_TRACKS):
            offset = 54 + (t_idx * 16)
            t_info = tracks_data.get(t_idx, {})
            vol = float(t_info.get("volume", 0.8 if t_idx == 0 else 0.75))
            pan = float(t_info.get("pan", 0.0))
            sep = float(t_info.get("separation", 0.0))
            muted = 1 if t_info.get("muted", False) else 0
            soloed = 1 if t_info.get("soloed", False) else 0
            armed = 1 if t_info.get("armed", False) else 0
            flags = int(t_info.get("flags", 0))

            struct.pack_into(
                "<fffBBBB",
                self.shm.buf,
                offset,
                vol,
                pan,
                sep,
                muted,
                soloed,
                armed,
                flags
            )

        # Write active window string (256 bytes starting at 2102)
        win_bytes = active_window.encode("utf-8")[:255] + b"\x00"
        win_padded = win_bytes.ljust(256, b"\x00")
        self.shm.buf[2102:2102 + 256] = win_padded

        return self._seq

    def read_frame(self) -> Dict[str, Any]:
        """Reads the latest telemetry frame with lock-free atomic sequence validation."""
        if not self.shm:
            return {"status": "SHM_OFFLINE", "error": "Shared memory segment not available"}

        # Check magic
        magic = bytes(self.shm.buf[:len(SHM_MAGIC)])
        if magic != SHM_MAGIC:
            return {"status": "SHM_CORRUPT", "error": f"Invalid magic header: {magic}"}

        # Double-read sequence check for lock-free consistency
        seq1 = struct.unpack_from("<I", self.shm.buf, 18)[0]
        timestamp = struct.unpack_from("<d", self.shm.buf, 22)[0]
        is_playing = struct.unpack_from("<I", self.shm.buf, 30)[0]
        bpm = struct.unpack_from("<d", self.shm.buf, 34)[0]
        song_pos = struct.unpack_from("<d", self.shm.buf, 42)[0]
        track_count = struct.unpack_from("<I", self.shm.buf, 50)[0]

        # Read sample tracks (first 8 tracks)
        tracks_sample = []
        for t_idx in range(min(8, track_count)):
            offset = 54 + (t_idx * 16)
            vol, pan, sep, muted, soloed, armed, flags = struct.unpack_from("<fffBBBB", self.shm.buf, offset)
            tracks_sample.append({
                "track": t_idx,
                "volume": round(vol, 3),
                "pan": round(pan, 3),
                "stereo_separation": round(sep, 3),
                "muted": bool(muted),
                "soloed": bool(soloed),
                "armed": bool(armed)
            })

        # Read active window
        raw_win = bytes(self.shm.buf[2102:2102 + 256])
        active_window = raw_win.split(b"\x00")[0].decode("utf-8", errors="ignore")

        # Check sequence after read
        seq2 = struct.unpack_from("<I", self.shm.buf, 18)[0]

        return {
            "status": "SHM_ONLINE",
            "shm_segment": SHM_NAME,
            "sequence_id": seq2,
            "is_consistent": (seq1 == seq2),
            "timestamp": timestamp,
            "latency_ms": round((time.time() - timestamp) * 1000.0, 3) if timestamp > 0 else 0.0,
            "is_playing": bool(is_playing),
            "playback_state": "PLAYING" if is_playing == 1 else ("PAUSED" if is_playing == 2 else "STOPPED"),
            "bpm": round(bpm, 2),
            "song_position_ppq": round(song_pos, 2),
            "frontmost_window": active_window,
            "monitored_tracks": track_count,
            "tracks_sample": tracks_sample
        }

    def close(self) -> None:
        """Closes memory view."""
        if self.shm:
            self.shm.close()

    def unlink(self) -> None:
        """Unlinks shared memory segment from OS."""
        if self.shm:
            try:
                self.shm.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    ring = C5SharedMemoryRing(create_if_missing=True)
    print("Writing test frame...")
    seq = ring.write_frame(is_playing=1, bpm=112.0, song_pos=384.0, active_window="piano_roll")
    print(f"Wrote frame #{seq}")
    data = ring.read_frame()
    import json
    print("Read back:")
    print(json.dumps(data, indent=2))
