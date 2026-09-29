#!/usr/bin/env python3
import os
import json
import numpy as np
import scipy.signal as signal
import soundfile as sf
import subprocess
from pathlib import Path

SR = 44100
FPS = 30

VOICE_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/mitxu_videoclip")
MUSIC_PATH = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/katana_100bpm.wav")
OUT_AUDIO_MP3 = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/mitxu_videoclip_audio.mp3")
OUT_AUDIO_WAV = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/mitxu_videoclip_audio.wav")
OUT_DATA_JSON = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/mitxu_videoclip_data.json")

def load_clean(path, target_sr=SR):
    d, sr = sf.read(path)
    if len(d.shape) > 1:
        d = d[:, 0]
    if sr != target_sr:
        num = int(len(d) * target_sr / sr)
        d = signal.resample(d, num)
    # 4-pole highpass at 90 Hz
    b_hp, a_hp = signal.butter(4, 90.0 / (target_sr / 2), btype='high')
    d = signal.lfilter(b_hp, a_hp, d)
    # De-ess / smooth top end at 12 kHz
    b_lp, a_lp = signal.butter(2, 12000.0 / (target_sr / 2), btype='low')
    d = signal.lfilter(b_lp, a_lp, d)
    # Normalize peak to 0.95
    d = d / (np.max(np.abs(d)) + 1e-6) * 0.95
    return d

def get_audio_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(res.stdout.strip())

# Dialogue line definitions
dialogue_defs = [
    ("m1", "mitxu", "Yola, mira qué mierda de música pincha el rata. House para guiris y progresivo de los noventa."),
    ("m2", "mitxu", "¡Es tu cabeza! Jajajajaja."),
    ("b1", "borja", "Eso le bajas cuarenta BPMs y pelotazo. Lo voy a hacer."),
    ("m3", "mitxu", "Es que eso hace. Coge la chunga esa de progresivo y la baja de velocidad. Su novia debe ser piccicatera."),
    ("b2", "borja", "¿Qué es eso?"),
    ("m4", "mitxu", "¿Y la de que es de estas de bar de lo viejo como para guiris? Estilo las chungas estas de Bob Sinclar para el verano."),
    ("b3", "borja", "Pues ahí te va, Mitxu: ¡Katana a cien BPMs, puro trance ralentizado!")
]

timeline_events = []
current_time = 0.5  # 0.5s initial silence

for lid, speaker, text in dialogue_defs:
    wav_path = VOICE_DIR / f"{lid}_{speaker}_real.wav"
    audio = load_clean(wav_path)
    dur = len(audio) / SR
    start_s = current_time
    end_s = start_s + dur
    timeline_events.append({
        "id": lid,
        "speaker": speaker,
        "text": text,
        "start": start_s,
        "end": end_s,
        "audio": audio
    })
    # Natural conversational gap
    pause = 0.4 if speaker == "borja" else 0.45
    current_time = end_s + pause

drop_start_s = current_time + 0.2
DROP_DURATION = 24.0  # 24 seconds of massive 100 BPM drop
TOTAL_DURATION = drop_start_s + DROP_DURATION
TOTAL_SAMPLES = int(TOTAL_DURATION * SR)

print(f"[*] Timeline total duration: {TOTAL_DURATION:.2f}s | Drop at: {drop_start_s:.2f}s")

# Load music track
music_raw, music_sr = sf.read(MUSIC_PATH)
if len(music_raw.shape) > 1:
    music_raw = music_raw[:, 0]
if music_sr != SR:
    num = int(len(music_raw) * SR / music_sr)
    music_raw = signal.resample(music_raw, num)

# Find a high-energy section for the drop (e.g., around 1:30 or 2:00 of the slowed track)
# In Katana at 100 BPM, bar drop hits around 80s - 140s
music_offset_s = 75.0
music_start_idx = int(music_offset_s * SR)
music_needed = int(TOTAL_DURATION * SR)

if music_start_idx + music_needed > len(music_raw):
    music_chunk = music_raw[:music_needed]
else:
    music_chunk = music_raw[music_start_idx:music_start_idx + music_needed].copy()

# Create speech track
speech_track = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
for ev in timeline_events:
    s_idx = int(ev["start"] * SR)
    e_idx = min(s_idx + len(ev["audio"]), TOTAL_SAMPLES)
    valid_len = e_idx - s_idx
    speech_track[s_idx:e_idx] += ev["audio"][:valid_len]

# Create background music envelope:
# Ducked to 0.12 (-18dB) with lowpass filter during dialogue, ramping up to 0.85 at drop!
music_track = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
# Lowpass filtered version for background
b_duck, a_duck = signal.butter(2, 700.0 / (SR / 2), btype='low')
music_ducked = signal.lfilter(b_duck, a_duck, music_chunk) * 0.14

# Ramped music volume envelope
ramp_start_idx = int((drop_start_s - 1.5) * SR)
ramp_end_idx = int(drop_start_s * SR)

music_track[:ramp_start_idx] = music_ducked[:ramp_start_idx]
for i in range(ramp_start_idx, ramp_end_idx):
    alpha = (i - ramp_start_idx) / (ramp_end_idx - ramp_start_idx)
    # Crossfade from ducked filtered to full punch
    music_track[i] = (1.0 - alpha) * music_ducked[i] + alpha * (music_chunk[i] * 0.85)

music_track[ramp_end_idx:] = music_chunk[ramp_end_idx:] * 0.85

# Final mix
master_mix = speech_track + music_track
peak = np.max(np.abs(master_mix))
if peak > 0.95:
    master_mix = master_mix / peak * 0.95

sf.write(str(OUT_AUDIO_WAV), master_mix, SR)
print(f"[✓] WAV master exportado: {OUT_AUDIO_WAV}")

# Convert to 320k MP3
subprocess.run([
    "ffmpeg", "-y", "-i", str(OUT_AUDIO_WAV),
    "-b:a", "320k", str(OUT_AUDIO_MP3)
], check=True)
print(f"[✓] MP3 master exportado: {OUT_AUDIO_MP3}")

# Precompute frame-by-frame metadata for Remotion
total_frames = int(TOTAL_DURATION * FPS)
frames_data = []

samples_per_frame = int(SR / FPS)
fft_size = 1024

for f in range(total_frames):
    t_sec = f / FPS
    s_idx = f * samples_per_frame
    e_idx = min(s_idx + samples_per_frame, TOTAL_SAMPLES)
    
    chunk = master_mix[s_idx:e_idx]
    rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
    
    # Active dialogue check
    active_speaker = "none"
    active_text = ""
    active_msg_id = ""
    mitxu_talking = False
    borja_talking = False
    
    for ev in timeline_events:
        if ev["start"] <= t_sec <= ev["end"]:
            active_speaker = ev["speaker"]
            active_text = ev["text"]
            active_msg_id = ev["id"]
            if ev["speaker"] == "mitxu":
                mitxu_talking = True
            elif ev["speaker"] == "borja":
                borja_talking = True
            break
            
    # Spectral bands
    sub = 0.0
    mid = 0.0
    high = 0.0
    bands = [0.0] * 16
    
    if len(chunk) >= 256:
        # FFT
        windowed = chunk * np.hanning(len(chunk))
        spectrum = np.abs(np.fft.rfft(windowed, n=fft_size))
        freqs = np.fft.rfftfreq(fft_size, d=1.0/SR)
        
        # Sub: 30 - 150 Hz
        sub_idx = np.where((freqs >= 30) & (freqs <= 150))[0]
        if len(sub_idx) > 0:
            sub = float(np.mean(spectrum[sub_idx]) * 4.5)
            
        # Mid: 300 - 3000 Hz
        mid_idx = np.where((freqs >= 300) & (freqs <= 3000))[0]
        if len(mid_idx) > 0:
            mid = float(np.mean(spectrum[mid_idx]) * 5.0)
            
        # High: 4000 - 16000 Hz
        high_idx = np.where((freqs >= 4000) & (freqs <= 16000))[0]
        if len(high_idx) > 0:
            high = float(np.mean(spectrum[high_idx]) * 6.0)
            
        # 16 visualizer bands (log scale 40Hz to 16kHz)
        log_edges = np.logspace(np.log10(40), np.log10(16000), 17)
        for b in range(16):
            b_idx = np.where((freqs >= log_edges[b]) & (freqs < log_edges[b+1]))[0]
            if len(b_idx) > 0:
                val = float(np.mean(spectrum[b_idx]) * 4.8)
                bands[b] = min(1.0, val)
                
    sub = min(1.0, sub)
    mid = min(1.0, mid)
    high = min(1.0, high)
    
    # Jaw flap gap for talking animation
    flap_gap = 0
    if mitxu_talking or borja_talking:
        flap_gap = int(min(26, max(4, rms * 140)))
        
    is_drop = t_sec >= drop_start_s
    
    frames_data.append({
        "frame": f,
        "time": round(t_sec, 3),
        "rms": round(rms, 4),
        "sub": round(sub, 3),
        "mid": round(mid, 3),
        "high": round(high, 3),
        "bands": [round(b, 3) for b in bands],
        "speaker": active_speaker,
        "text": active_text,
        "msgId": active_msg_id,
        "mitxuTalking": mitxu_talking,
        "borjaTalking": borja_talking,
        "flapGap": flap_gap,
        "isDrop": is_drop
    })

meta = {
    "metadata": {
        "title": "Mitxu & Borja - Katana Silence 100BPM Videoclip",
        "fps": FPS,
        "totalFrames": total_frames,
        "totalDuration": round(TOTAL_DURATION, 2),
        "dropStart": round(drop_start_s, 2),
        "timeline": [
            {
                "id": ev["id"],
                "speaker": ev["speaker"],
                "text": ev["text"],
                "start": round(ev["start"], 2),
                "end": round(ev["end"], 2)
            } for ev in timeline_events
        ]
    },
    "frames": frames_data
}

with open(OUT_DATA_JSON, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)

print(f"[★] Metadatos guardados con éxito: {OUT_DATA_JSON} ({total_frames} frames)")
