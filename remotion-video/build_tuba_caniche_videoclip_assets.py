#!/usr/bin/env python3
"""
build_tuba_caniche_videoclip_assets.py
Generates the frame-by-frame telemetry for Remotion video from the master audio:
"Tuba Menor, Pads y Caniche Feliz (Hola ¿Estás Sole?) feat. Alain"
"""

import json
import shutil
import numpy as np
import soundfile as sf
from pathlib import Path

SR = 44100
FPS = 30
BPM = 122.0
BEAT_SEC = 60.0 / BPM
BAR_SEC = BEAT_SEC * 4.0

AUDIO_SRC = Path("/Users/borjafernandezangulo/Music/Moskv-1_-_Tuba_Menor_Pads_y_Caniche_Feliz.wav")
MP3_SRC = Path("/Users/borjafernandezangulo/Music/Moskv-1_-_Tuba_Menor_Pads_y_Caniche_Feliz.mp3")

REMOTION_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video")
PUBLIC_DIR = REMOTION_DIR / "public"
OUT_JSON = PUBLIC_DIR / "tuba_caniche_telemetry.json"
OUT_MP3 = PUBLIC_DIR / "tuba_caniche_track.mp3"

# Copy audio into Remotion public directory
shutil.copy2(MP3_SRC, OUT_MP3)
print(f"[✓] Audio copiado a: {OUT_MP3}")

# Load WAV for analysis
data, sr = sf.read(AUDIO_SRC)
if data.ndim == 2:
    mono = np.mean(data, axis=1)
else:
    mono = data

dur_sec = len(mono) / sr
total_frames = int(dur_sec * FPS)

print(f"[*] Duración: {dur_sec:.2f} s | Total frames @ {FPS} FPS: {total_frames}")

# Frequency bands
band_edges = np.logspace(np.log10(30), np.log10(16000), 17)
fft_size = 2048
freqs = np.fft.rfftfreq(fft_size, 1.0 / sr)

# Libretto Event markers (Time in seconds)
events = [
    {"sec": 0.0, "section": "INTRO_QUEJIO", "speaker": "Cantaor Jondo", "text": "¡Ay!... (Quejío Ouroboros)"},
    {"sec": 4 * BAR_SEC + 1 * BEAT_SEC, "section": "VERSO_MARI_LUPE", "speaker": "Mari Lupe", "text": "¿Hola? ¿Estás Sole?"},
    {"sec": 6 * BAR_SEC + 1 * BEAT_SEC, "section": "VERSO_ALAIN", "speaker": "Alain (Sole)", "text": "Sí estoy Mari Lupe. Pero acompañade."},
    {"sec": 8 * BAR_SEC, "section": "GROOVE_START", "speaker": "Tuba & Pad Drums", "text": "[GROOVE 122 BPM · TUBA CON CHORUS]"},
    {"sec": 9 * BAR_SEC + 0.5 * BEAT_SEC, "section": "CANTICO_TUMBA", "speaker": "Alain", "text": "a tumba tumba, a tumba tumba..."},
    {"sec": 13 * BAR_SEC + 0.5 * BEAT_SEC, "section": "CANTICO_TUMBA_2", "speaker": "Alain", "text": "a tumba tumba, a tumba tumba..."},
    {"sec": 17 * BAR_SEC + 1.0 * BEAT_SEC, "section": "CANTICO_KETUMBAN", "speaker": "Alain", "text": "KETUMBAN BAN"},
    {"sec": 21 * BAR_SEC + 1.0 * BEAT_SEC, "section": "CANTICO_TEPETE", "speaker": "Alain", "text": "QUE TEPETE PETE"},
    {"sec": 25 * BAR_SEC + 0.5 * BEAT_SEC, "section": "CANTICO_DEJEBE", "speaker": "Alain", "text": "DEJEBE TU DEJEBERE"},
    {"sec": 29 * BAR_SEC + 0.5 * BEAT_SEC, "section": "CANTICO_URKULLU", "speaker": "Alain", "text": "Gora URKULLU (GORA GORA GORA)"},
    {"sec": 31 * BAR_SEC + 1.0 * BEAT_SEC, "section": "CANTICO_OLENTZERO", "speaker": "Alain", "text": "GURE OLENTZERO"},
    {"sec": 33 * BAR_SEC, "section": "NEGATIVE_HARMONY", "speaker": "Ernst Levy Polar", "text": "[PUENTE DE ARMONÍAS NEGATIVAS · POLAR REFLECTION]"},
    {"sec": 46 * BAR_SEC + 8 * (BAR_SEC / 16), "section": "CANICHE_COLLAPSE", "speaker": "Caniche Feliz", "text": "¡GUAU! (Colapso Tape Delay 3/16)"},
    {"sec": 52 * BAR_SEC, "section": "GROOVE_RETURN", "speaker": "Tuba & Ensamble", "text": "[RETORNO CATÁRTICO DEL GROOVE]"},
    {"sec": 65 * BAR_SEC, "section": "OUROBOROS_END", "speaker": "Cantaor Jondo", "text": "¡Ay!... (Quejío Final Ouroboros)"},
]

frames_telemetry = []

for f in range(total_frames):
    cur_sec = f / FPS
    start_sample = int(cur_sec * sr)
    end_sample = min(start_sample + fft_size, len(mono))
    
    chunk = mono[start_sample:end_sample]
    if len(chunk) < fft_size:
        pad = np.zeros(fft_size)
        pad[:len(chunk)] = chunk
        chunk_fft = pad
    else:
        chunk_fft = chunk
        
    rms = float(np.sqrt(np.mean(chunk_fft ** 2)))
    spec = np.abs(np.fft.rfft(chunk_fft * np.hanning(fft_size)))
    
    sub_mask = (freqs >= 30) & (freqs <= 95)
    sub = float(np.mean(spec[sub_mask])) if np.any(sub_mask) else 0.0
    
    mid_mask = (freqs >= 400) & (freqs <= 2500)
    mid = float(np.mean(spec[mid_mask])) if np.any(mid_mask) else 0.0
    
    high_mask = (freqs >= 5200) & (freqs <= 12000)
    high = float(np.mean(spec[high_mask])) if np.any(high_mask) else 0.0
    
    bands = []
    for b in range(16):
        b_mask = (freqs >= band_edges[b]) & (freqs < band_edges[b+1])
        b_val = float(np.mean(spec[b_mask])) if np.any(b_mask) else 0.0
        bands.append(round(min(b_val * 4.5, 1.0), 3))
        
    # Active libretto segment
    active_ev = events[0]
    for ev in events:
        if cur_sec >= ev["sec"]:
            active_ev = ev
        else:
            break
            
    bar_num = int(cur_sec / BAR_SEC)
    is_caniche = 46 <= bar_num < 52
    is_negative = 33 <= bar_num < 46
    is_ouroboros = bar_num < 4 or bar_num >= 65
    
    frames_telemetry.append({
        "frame": f,
        "time": round(cur_sec, 3),
        "bar": bar_num,
        "rms": round(rms, 4),
        "sub": round(min(sub * 5.5, 1.0), 4),
        "mid": round(min(mid * 6.0, 1.0), 4),
        "high": round(min(high * 9.0, 1.0), 4),
        "bands": bands,
        "section": active_ev["section"],
        "speaker": active_ev["speaker"],
        "text": active_ev["text"],
        "isCaniche": is_caniche,
        "isNegativeHarmony": is_negative,
        "isOuroboros": is_ouroboros,
        "headbob": round(np.sin(f * 2 * np.pi * (BPM / 60.0) / FPS), 3)
    })

payload = {
    "metadata": {
        "title": "Tuba Menor, Pads y Caniche Feliz (Hola ¿Estás Sole?) feat. Alain",
        "artist": "MOSKV-1 feat. Alain",
        "bpm": BPM,
        "fps": FPS,
        "totalBars": 68,
        "durationSec": dur_sec,
        "totalFrames": total_frames,
        "width": 1920,
        "height": 1080
    },
    "events": events,
    "frames": frames_telemetry
}

with open(OUT_JSON, "w") as jf:
    json.dump(payload, jf)

print(f"[✓] Telemetría guardada en: {OUT_JSON} ({len(frames_telemetry)} frames)")
