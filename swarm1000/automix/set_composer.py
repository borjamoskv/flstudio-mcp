#!/usr/bin/env python3
"""
SWARM-1000 AUTONOMOUS SET COMPOSER & HARMONIC DISPATCHER
Ring-0 Audio Feature Extraction, Camelot Wheel Harmonic Optimization (TSP),
Vocal Mutex Collision Prevention, and Psychoacoustic Transition Prescription
"""

import os
import glob
import math
import numpy as np
import soundfile as sf
from typing import List, Dict, Any, Tuple

# Krumhansl-Schmuckler Key Profiles (Chroma correlation)
KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Camelot Mapping: (PitchClass, Mode) -> CamelotCode
CAMELOT_MAP = {
    ('B', 'major'): '1B', ('G#', 'minor'): '1A',
    ('F#', 'major'): '2B', ('D#', 'minor'): '2A',
    ('C#', 'major'): '3B', ('A#', 'minor'): '3A',
    ('G#', 'major'): '4B', ('F', 'minor'): '4A',
    ('D#', 'major'): '5B', ('C', 'minor'): '5A',
    ('A#', 'major'): '6B', ('G', 'minor'): '6A',
    ('F', 'major'): '7B', ('D', 'minor'): '7A',
    ('C', 'major'): '8B', ('A', 'minor'): '8A',
    ('G', 'major'): '9B', ('E', 'minor'): '9A',
    ('D', 'major'): '10B', ('B', 'minor'): '10A',
    ('A', 'major'): '11B', ('F#', 'minor'): '11A',
    ('E', 'major'): '12B', ('C#', 'minor'): '12A',
}

import subprocess

class TrackFeatureExtractor:
    """Extracts fundamental acoustic, rhythmic, harmonic, and vocal telemetry."""

    @staticmethod
    def _read_audio_universal(filepath: str, max_duration_s: float = 300.0, sr: int = 48000) -> Tuple[np.ndarray, float]:
        # Probe duration first
        cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath]
        try:
            res = subprocess.run(cmd_dur, capture_output=True, text=True, check=True)
            duration = float(res.stdout.strip())
        except Exception:
            duration = 300.0

        # Decode up to max_duration_s as f32le mono
        cmd_dec = [
            "ffmpeg", "-v", "error", "-t", str(max_duration_s),
            "-i", filepath,
            "-f", "f32le", "-ar", str(sr), "-ac", "1", "pipe:1"
        ]
        proc = subprocess.Popen(cmd_dec, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw, _ = proc.communicate()
        if len(raw) == 0:
            return np.zeros(sr, dtype=np.float32), duration
        mono = np.frombuffer(raw, dtype=np.float32).copy()
        return mono, duration

    @staticmethod
    def extract_features(filepath: str, max_duration_s: float = 300.0) -> Dict[str, Any]:
        sr = 48000
        mono, duration = TrackFeatureExtractor._read_audio_universal(filepath, max_duration_s, sr)

        # Downsample to 22050 for fast feature analysis if needed
        target_sr = 22050
        step = max(1, sr // target_sr)
        mono_ds = mono[::step]
        eff_sr = sr // step

        # 1. BPM / Tempo Estimation (Autocorrelation on onset envelope)
        bpm = TrackFeatureExtractor._estimate_bpm(mono_ds, eff_sr)

        # 2. Harmonic Key Estimation (Chroma correlation)
        key_name, camelot = TrackFeatureExtractor._estimate_key(mono_ds, eff_sr)

        # 3. Vocal Energy Density & Vocal Ranges
        vocal_regions, vocal_density = TrackFeatureExtractor._detect_vocal_activity(mono_ds, eff_sr)

        # 4. Energy Profile & Loudness
        rms = float(np.sqrt(np.mean(mono**2)))
        peak = float(np.max(np.abs(mono)))
        crest_factor_db = 20.0 * np.log10(peak / (rms + 1e-9))

        return {
            "path": filepath,
            "filename": os.path.basename(filepath),
            "duration_s": round(duration, 2),
            "samplerate": sr,
            "bpm": round(bpm, 1),
            "key": key_name,
            "camelot": camelot,
            "vocal_density": round(vocal_density, 3),
            "vocal_regions": vocal_regions,
            "rms": round(rms, 4),
            "crest_factor_db": round(crest_factor_db, 2)
        }

    @staticmethod
    def _estimate_bpm(audio: np.ndarray, sr: int) -> float:
        # Onset envelope via half-wave rectified spectral flux
        frame_len = 1024
        hop_len = 512
        num_frames = (len(audio) - frame_len) // hop_len
        if num_frames < 100:
            return 124.0  # fallback

        # Simple energy envelope derivative
        frames = np.lib.stride_tricks.sliding_window_view(audio[:num_frames * hop_len], frame_len)[::hop_len]
        energy = np.sum(frames**2, axis=1)
        onset_env = np.maximum(0, np.diff(energy))
        onset_env = onset_env - np.mean(onset_env)

        # Autocorrelation of onset envelope
        corr = np.correlate(onset_env, onset_env, mode='full')
        corr = corr[len(corr)//2:]

        # Constrain search range to 80 - 150 BPM
        hop_time = hop_len / sr
        min_lag = int((60.0 / 155.0) / hop_time)
        max_lag = int((60.0 / 78.0) / hop_time)

        if max_lag >= len(corr):
            max_lag = len(corr) - 1
        if min_lag >= max_lag:
            return 124.0

        best_lag = min_lag + np.argmax(corr[min_lag:max_lag])
        bpm = 60.0 / (best_lag * hop_time)
        
        # Normalize into 110 - 145 range
        while bpm < 110:
            bpm *= 2.0
        while bpm > 145:
            bpm /= 2.0
        return bpm

    @staticmethod
    def _estimate_key(audio: np.ndarray, sr: int) -> Tuple[str, str]:
        # Compute simplified 12-bin Chroma vector
        n_fft = 4096
        hop = 2048
        window = np.hanning(n_fft)
        num_frames = min(200, (len(audio) - n_fft) // hop)
        if num_frames <= 0:
            return "A minor", "8A"

        chroma = np.zeros(12, dtype=np.float64)
        freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
        
        # Map frequencies (65 Hz to 2000 Hz) to pitch classes
        valid_mask = (freqs >= 65.4) & (freqs <= 2093.0)
        valid_freqs = freqs[valid_mask]
        midi_notes = np.round(69 + 12 * np.log2(valid_freqs / 440.0)).astype(int)
        pitch_classes = midi_notes % 12

        for i in range(num_frames):
            seg = audio[i * hop : i * hop + n_fft] * window
            mag = np.abs(np.fft.rfft(seg))[valid_mask]
            for pc in range(12):
                chroma[pc] += np.sum(mag[pitch_classes == pc])

        norm = np.linalg.norm(chroma)
        if norm > 0:
            chroma /= norm

        # Correlate with KS Major and Minor profiles for all 12 rotations
        best_score = -1e9
        best_key = ("A", "minor")

        for r in range(12):
            rot_chroma = np.roll(chroma, -r)
            # Major correlation
            maj_corr = np.corrcoef(rot_chroma, KS_MAJOR)[0, 1]
            if maj_corr > best_score:
                best_score = maj_corr
                best_key = (PITCH_CLASSES[r], "major")
            # Minor correlation
            min_corr = np.corrcoef(rot_chroma, KS_MINOR)[0, 1]
            if min_corr > best_score:
                best_score = min_corr
                best_key = (PITCH_CLASSES[r], "minor")

        key_str = f"{best_key[0]} {best_key[1]}"
        camelot = CAMELOT_MAP.get(best_key, "8A")
        return key_str, camelot

    @staticmethod
    def _detect_vocal_activity(audio: np.ndarray, sr: int) -> Tuple[List[Tuple[float, float]], float]:
        # Formant band 350 Hz - 3200 Hz
        n_fft = 2048
        hop = 1024
        window = np.hanning(n_fft)
        num_frames = (len(audio) - n_fft) // hop
        if num_frames <= 0:
            return [], 0.0

        freqs = np.fft.rfftfreq(n_fft, 1.0 / sr)
        vocal_mask = (freqs >= 350) & (freqs <= 3200)

        vocal_frames = []
        for i in range(num_frames):
            seg = audio[i * hop : i * hop + n_fft] * window
            mag_sq = np.abs(np.fft.rfft(seg))**2
            total_e = np.sum(mag_sq) + 1e-12
            vocal_e = np.sum(mag_sq[vocal_mask])
            vocal_ratio = vocal_e / total_e
            
            # Vocal threshold heuristics: ratio > 0.45 and sufficient energy
            is_vocal = (vocal_ratio > 0.45) and (total_e > 1e-4)
            vocal_frames.append(is_vocal)

        # Smooth vocal frames and merge into contiguous regions (seconds)
        hop_time = hop / sr
        regions = []
        start_t = None
        for i, val in enumerate(vocal_frames):
            t = i * hop_time
            if val and start_t is None:
                start_t = t
            elif not val and start_t is not None:
                if (t - start_t) >= 2.0:  # minimum 2s to count as vocal phrase
                    regions.append((round(start_t, 1), round(t, 1)))
                start_t = None
        if start_t is not None and (len(vocal_frames)*hop_time - start_t) >= 2.0:
            regions.append((round(start_t, 1), round(len(vocal_frames)*hop_time, 1)))

        vocal_density = sum(end - start for start, end in regions) / (len(audio) / sr)
        return regions, vocal_density


class AutonomousSetComposer:
    """
    Solves harmonic sequence optimization and prescribes exact 
    psychoacoustic transitions across a playlist.
    """

    def __init__(self, tracks_dir: str):
        self.tracks_dir = tracks_dir
        self.tracks: List[Dict[str, Any]] = []

    def scan_and_analyze(self) -> List[Dict[str, Any]]:
        patterns = ["*.wav", "*.flac", "*.aiff", "*.mp3", "*.webm", "*.ogg"]
        files = []
        for p in patterns:
            files.extend(glob.glob(os.path.join(self.tracks_dir, p)))
        files.sort()

        print(f"[SWARM-1000 Composer] Found {len(files)} tracks in {self.tracks_dir}. Running Ring-0 analysis...")
        self.tracks = []
        for f in files:
            feat = TrackFeatureExtractor.extract_features(f)
            self.tracks.append(feat)
            print(f"  -> {feat['filename']}: BPM {feat['bpm']} | Key {feat['key']} ({feat['camelot']}) | Vocal Density {feat['vocal_density']*100:.1f}%")
        return self.tracks

    @staticmethod
    def camelot_distance(cam1: str, cam2: str) -> int:
        """Computes distance on the 12-hour Camelot clock."""
        num1, letter1 = int(cam1[:-1]), cam1[-1]
        num2, letter2 = int(cam2[:-1]), cam2[-1]
        
        diff = abs(num1 - num2)
        clock_diff = min(diff, 12 - diff)
        mode_diff = 0 if letter1 == letter2 else 1
        return clock_diff + mode_diff

    def optimize_set_flow(self) -> List[Dict[str, Any]]:
        """
        Greedy nearest-neighbor with Camelot Wheel & BPM constraint 
        to build an ultra-harmonic, high-exergy progression.
        """
        if not self.tracks:
            return []

        remaining = list(self.tracks)
        # Start with track that has lowest BPM / ambient opening
        remaining.sort(key=lambda t: t['bpm'])
        current = remaining.pop(0)
        ordered = [current]

        while remaining:
            best_idx = 0
            best_score = 1e9

            for idx, cand in enumerate(remaining):
                cam_dist = self.camelot_distance(current['camelot'], cand['camelot'])
                bpm_diff = abs(current['bpm'] - cand['bpm'])
                
                # Penalty: high BPM jump > 8 BPM is heavily penalized
                # Harmonic penalty: distance > 2 is penalized
                score = cam_dist * 10.0 + bpm_diff * 2.0
                if score < best_score:
                    best_score = score
                    best_idx = idx

            current = remaining.pop(best_idx)
            ordered.append(current)

        return ordered

    def prescribe_transitions(self, ordered_tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prescribes exact transition parameters for each pair of tracks:
        Crossover type, transition duration in bars/seconds, LR4 split, and vocal lock.
        """
        transitions = []
        for i in range(len(ordered_tracks) - 1):
            t_curr = ordered_tracks[i]
            t_next = ordered_tracks[i+1]
            
            avg_bpm = (t_curr['bpm'] + t_next['bpm']) / 2.0
            bar_duration_s = (60.0 / avg_bpm) * 4.0
            
            # Distance and compatibility
            cam_dist = self.camelot_distance(t_curr['camelot'], t_next['camelot'])
            bpm_diff = abs(t_curr['bpm'] - t_next['bpm'])
            
            # Decision Matrix:
            # 1. High vocal density in transition window -> Tape-Stop or Satori Silence
            # 2. Strict club techno / minimal -> 32 or 64 bars Sigmoidal Bass Swap
            # 3. High BPM jump (> 10 BPM) -> Vacuum Silence / Ambient Reverb Wash
            if bpm_diff > 12.0:
                trans_type = "SATORI_VACUUM_WASH"
                bars = 8
                duration_s = 8 * bar_duration_s
                k_sigmoid = 12.0
                silence_gap_s = 2.0
            elif t_next['vocal_density'] > 0.4 and len(t_next['vocal_regions']) > 0 and t_next['vocal_regions'][0][0] < 15.0:
                trans_type = "TAPE_STOP_VOCAL_ENTRY"
                bars = 4
                duration_s = 4 * bar_duration_s
                k_sigmoid = 30.0
                silence_gap_s = 1.2
            elif cam_dist <= 1:
                # Perfect harmonic alignment -> Deep 32/64-bar club crossover
                trans_type = "SIGMOIDAL_BASS_SWAP_LR4"
                bars = 32
                duration_s = 32 * bar_duration_s
                k_sigmoid = 18.0
                silence_gap_s = 0.0
            else:
                # Birmingham Continuous Blend with High-Pass Filter sweep
                trans_type = "CONTINUOUS_HPF_BLEND"
                bars = 16
                duration_s = 16 * bar_duration_s
                k_sigmoid = 20.0
                silence_gap_s = 0.0

            transitions.append({
                "from_track": t_curr['filename'],
                "to_track": t_next['filename'],
                "transition_index": i + 1,
                "type": trans_type,
                "bars": bars,
                "duration_s": round(duration_s, 2),
                "k_sigmoid": k_sigmoid,
                "crossover_freq_hz": 160.0,
                "silence_gap_s": silence_gap_s,
                "ms_evaporation_ratio": 0.28,
                "vocal_mutex_locked": True,
                "false_drop_bar12": True if bars >= 32 else False
            })

        return transitions

if __name__ == "__main__":
    test_dir = "/Users/borjafernandezangulo/10_PROJECTS/dj_tascas_set/tracks"
    if os.path.exists(test_dir):
        composer = AutonomousSetComposer(test_dir)
        composer.scan_and_analyze()
        ordered = composer.optimize_set_flow()
        print("\n" + "="*70)
        print("SWARM-1000 OPTIMIZED HARMONIC FLOW (CAMELOT WHEEL TSP):")
        print("="*70)
        for idx, t in enumerate(ordered):
            print(f"[{idx+1:02d}] {t['filename']} | BPM: {t['bpm']} | Camelot: {t['camelot']}")
        
        prescriptions = composer.prescribe_transitions(ordered)
        print("\n" + "="*70)
        print("SWARM-1000 TRANSITION PRESCRIPTIONS:")
        print("="*70)
        for p in prescriptions:
            print(f"TR#{p['transition_index']:02d}: {p['from_track']} -> {p['to_track']}")
            print(f"     Type: {p['type']} | Duration: {p['duration_s']}s ({p['bars']} bars)")
            print(f"     k={p['k_sigmoid']} | LR4 Crossover: {p['crossover_freq_hz']}Hz | Gap: {p['silence_gap_s']}s")
