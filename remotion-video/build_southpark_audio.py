#!/usr/bin/env python3
"""
Build 100% Clean Voice-Only Audio for South Park Podcast (Zero Music, Zero Muddy Bass)
"""
import os
import json
import numpy as np
import scipy.signal as signal
import soundfile as sf
import subprocess

SR = 44100
FPS = 30

def load_clean(p):
    d, sr = sf.read(p)
    if len(d.shape) > 1:
        d = d[:, 0]
    if sr != SR:
        num = int(len(d) * SR / sr)
        d = signal.resample(d, num)
    # Highpass at 100Hz (butterworth 4-pole) to completely kill rumble
    b_hp, a_hp = signal.butter(4, 100.0 / (SR / 2), btype='high')
    d = signal.lfilter(b_hp, a_hp, d)
    # De-ess / smooth top end
    b_lp, a_lp = signal.butter(2, 12000.0 / (SR / 2), btype='low')
    d = signal.lfilter(b_lp, a_lp, d)
    # Normalize peak to 0.90
    d = d / (np.max(np.abs(d)) + 1e-6) * 0.90
    return d

v_sol = load_clean('/tmp/alain_japan/sol.wav')
v_kremlin = load_clean('/tmp/alain_japan/kremlin.wav')
v_moon = load_clean('/tmp/alain_japan/moon.wav')
v_roque = load_clean('/tmp/alain_japan/roque.wav')

def get_slice(arr, start_s, end_s, fade_ms=30):
    s_idx = int(start_s * SR)
    e_idx = min(int(end_s * SR), len(arr))
    chunk = arr[s_idx:e_idx].copy()
    fl = int((fade_ms / 1000.0) * SR)
    if len(chunk) > fl * 2:
        chunk[:fl] *= np.linspace(0, 1, fl)
        chunk[-fl:] *= np.linspace(1, 0, fl)
    return chunk

# Dialogue segments
segments = [
    # 0.5s - 9.5s
    (0.8, get_slice(v_sol, 0.0, 9.1), "¿Quién coño fue el viajero secreto a la ciudad, al país del Sol Naciente?"),
    
    # 10.5s - 15.0s
    (10.5, get_slice(v_kremlin, 1.8, 5.8), "Una concerta, estoy a punto... de comerme la otra..."),
    
    # 15.8s - 21.0s
    (15.8, get_slice(v_kremlin, 26.2, 31.0), "Y luego ya en el Kremlin según llegué me metí dos tiracres..."),
    
    # 22.0s - 29.5s
    (22.0, get_slice(v_moon, 0.0, 7.5), "Pero creo que la combinación concerta tiraco de spiz es acojonante..."),
    
    # 30.5s - 37.0s
    (30.5, get_slice(v_moon, 27.5, 34.5), "Sensación de anfeta de verdad totalmente, sin necesidad..."),
    
    # 37.8s - 44.0s
    (37.8, get_slice(v_moon, 34.8, 41.2), "¡Los discos me los ponía haciendo el moonwalk a las 6 de la mañana!"),
    
    # 44.5s - 47.0s
    (44.5, get_slice(v_moon, 42.5, 45.0), "¡Así como estaba, cabrón!"),
    
    # 48.0s - 54.0s
    (48.0, get_slice(v_roque, 0.0, 6.5), "5 birras al final compaginé... birra chupito y muy bien..."),
    
    # 54.8s - 57.0s
    (54.8, get_slice(v_roque, 11.8, 14.2), "O sea llegué a casa 8 de la mañana..."),
    
    # 57.5s - 61.5s
    (57.5, get_slice(v_roque, 16.2, 20.2), "Roque, roque hasta las 5 o 6 de la tarde..."),
    
    # 62.2s - 66.5s
    (62.2, get_slice(v_roque, 21.0, 25.8), "Pero fantástico vamos... ¡todavía hago loopy a la mañana!")
]

TOTAL_DURATION = 68.0  # 68 seconds = 2040 frames
TOTAL_SAMPLES = int(TOTAL_DURATION * SR)
speech = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

cues = []
for start_s, chunk, txt in segments:
    start_idx = int(start_s * SR)
    end_idx = min(start_idx + len(chunk), TOTAL_SAMPLES)
    valid_len = end_idx - start_idx
    if valid_len > 0:
        speech[start_idx:end_idx] += chunk[:valid_len]
        cues.append({
            "startFrame": int(start_s * FPS),
            "endFrame": int((start_s + len(chunk)/SR) * FPS),
            "text": txt
        })

# Pure speech mastering: Broadcast compression & normalization
threshold = 0.20
compressed = np.copy(speech)
mask = np.abs(speech) > threshold
compressed[mask] = np.sign(speech[mask]) * (threshold + (np.abs(speech[mask]) - threshold) * 0.35)
# Normalize to -0.5 dBFS peak (~0.95)
compressed = (compressed / (np.max(np.abs(compressed)) + 1e-6)) * 0.95

OUT_DIR = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public"
RAW_WAV = os.path.join(OUT_DIR, "southpark_audio_raw.wav")
WAV_PATH = os.path.join(OUT_DIR, "southpark_audio.wav")
MP3_PATH = os.path.join(OUT_DIR, "southpark_audio.mp3")

sf.write(RAW_WAV, compressed, SR, subtype='PCM_16')
# Master with loudnorm to -13 LUFS for maximum phone/WhatsApp speaker punch
cmd_norm = [
    'ffmpeg', '-y', '-i', RAW_WAV,
    '-af', 'loudnorm=I=-13.0:LRA=7.0:TP=-0.5',
    '-c:a', 'pcm_s16le', WAV_PATH
]
subprocess.run(cmd_norm, check=True, stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg', '-y', '-i', WAV_PATH, '-codec:a', 'libmp3lame', '-b:a', '256k', MP3_PATH], check=True, stderr=subprocess.DEVNULL)
print(f"Generated broadcast-mastered audio: {MP3_PATH} ({TOTAL_DURATION}s, ZERO MUSIC)")

# Reload mastered audio for accurate RMS per frame
mastered_audio, _ = sf.read(WAV_PATH)
if len(mastered_audio.shape) > 1:
    mastered_audio = mastered_audio[:, 0]

# Precompute speech loudness envelope and mouth flapping gap per frame
frame_len = int(SR / FPS)
frames_data = []

for f in range(int(TOTAL_DURATION * FPS)):
    s_idx = f * frame_len
    e_idx = min(s_idx + frame_len, len(mastered_audio))
    chunk = mastered_audio[s_idx:e_idx]
    rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
    
    # Active text
    curr_txt = ""
    for cue in cues:
        if cue["startFrame"] <= f <= cue["endFrame"]:
            curr_txt = cue["text"]
            break
            
    # Flap gap in pixels: 0 when quiet, up to 32px when loud
    is_talking = rms > 0.04
    # Alternate flap cycle when talking
    flap_cycle = np.sin((f * 0.85) * np.pi) ** 2 if is_talking else 0.0
    flap_gap = int(np.clip(rms * 120.0 * flap_cycle, 0, 36)) if is_talking else 0
    
    frames_data.append({
        "frame": f,
        "rms": float(rms),
        "isTalking": bool(is_talking),
        "flapGap": flap_gap,
        "text": curr_txt
    })

meta = {
    "metadata": {
        "title": "CORTEZAS Y CONCERTAS: SOUTH PARK EDITION",
        "totalFrames": int(TOTAL_DURATION * FPS),
        "fps": FPS,
        "durationSec": TOTAL_DURATION,
        "width": 1920,
        "height": 1080
    },
    "cues": cues,
    "frames": frames_data
}

JSON_PATH = os.path.join(OUT_DIR, "southpark_data.json")
with open(JSON_PATH, "w") as f:
    json.dump(meta, f, indent=2)

print(f"Saved South Park frame metadata: {JSON_PATH}")
