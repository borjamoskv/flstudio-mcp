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

VOICE_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_audio")
MUSIC_PATH = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/katana_100bpm.wav")
OUT_AUDIO_MP3 = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_master_audio.mp3")
OUT_AUDIO_WAV = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_master_audio.wav")
OUT_DATA_JSON = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_telemetry.json")

def load_clean(path, target_sr=SR):
    d, sr = sf.read(path)
    if len(d.shape) > 1:
        d = d[:, 0]
    if sr != target_sr:
        num = int(len(d) * target_sr / sr)
        d = signal.resample(d, num)
    # Butterworth 4-pole highpass at 85 Hz
    b_hp, a_hp = signal.butter(4, 85.0 / (target_sr / 2), btype='high')
    d = signal.lfilter(b_hp, a_hp, d)
    # Gentle high-shelf / de-ess at 13.5 kHz
    b_lp, a_lp = signal.butter(2, 13500.0 / (target_sr / 2), btype='low')
    d = signal.lfilter(b_lp, a_lp, d)
    # Normalize peak to 0.92
    d = d / (np.max(np.abs(d)) + 1e-6) * 0.92
    return d

# Dialogue structure
dialogue_defs = [
    {
        "id": "borja_pitch",
        "speaker": "borja",
        "file": "borja_ceutong_pitch.wav",
        "text": "A ver chavales, escuchadme bien. Lo de Ceuta amurallada es una ruina de cojones. ¡Hay que hacer CEUTONG! Desacoplamos la soberanía funcional, metemos un Hong Kong al 0% de impuestos con Tetuán, y en diez años los rascacielos tapan el Peñón de Gibraltar, ¡hostia!",
        "scene": "skyline"
    },
    {
        "id": "mitxu_rant",
        "speaker": "mitxu",
        "file": "mitxu_ceutong_rant.wav",
        "text": "¡Pero qué me estás contando, Borja! ¡La virgen! Si en Ceuta lo único que hay es el parking de los ferrys y viento de levante. ¡Como montes un Hong Kong ahí, a la que te descuides te ponen una gilda de cinco pisos y a cobrar el txakoli a diez euros!",
        "scene": "skyline"
    },
    {
        "id": "alain_negociodad",
        "speaker": "alain",
        "file": "alain_negociodad.wav",
        "text": "Negociodad : Ceutong. Y Villa Melilla, Ciudad Vacacional. ¡Esto lo petamos seguro con dos txakolis en el helipuerto!",
        "scene": "whatsapp_chat"
    },
    {
        "id": "chiquito_party",
        "speaker": "chiquito",
        "file": "chiquito_full.wav",
        "text": "¡¿Qué pasa, comor?! ¡No te digo trigo por no llamarte Rodrigor! ¡Siete caballos vienen de Bonanza a Ceutong! ¡Te das cuen! ¡Se me da usted un pelotazo! ¡Al ataquerl!",
        "scene": "party"
    },
    {
        "id": "echenique_cyber",
        "speaker": "echenique",
        "file": "echenique_cyber.wav",
        "text": "Compañeros, la plusvalía termodinámica de Ceutong es científicamente irrebatible. Pero por favor, asfaltad bien la recta del casino que a esta silla con alerón y leds le va a dar una taquicardia cuántica a ciento ochenta por hora.",
        "scene": "party"
    },
    {
        "id": "macgyver_hero",
        "speaker": "macgyver",
        "file": "macgyver_hero.wav",
        "text": "Tranquilos todos. Con un clip de oficina, un chicle de fresa y dos botellas de txakoli he hackeado la aduana del Estrecho. ¡Ceutong está al cien por cien de exergía!",
        "scene": "party"
    },
    {
        "id": "borja_drop_call",
        "speaker": "borja",
        "file": "borja_drop_intro.wav",
        "text": "¡Pues que empiece la fiesta en el helipuerto de Ceutong! ¡Soltad los bombos a cien BPMs!",
        "scene": "festival_mitxu"
    }
]

timeline_events = []
current_time = 0.5  # 0.5s pre-roll

for d in dialogue_defs:
    p = VOICE_DIR / d["file"]
    audio = load_clean(p)
    dur = len(audio) / SR
    start_s = current_time
    end_s = start_s + dur
    timeline_events.append({
        "id": d["id"],
        "speaker": d["speaker"],
        "text": d["text"],
        "scene": d["scene"],
        "start": start_s,
        "end": end_s,
        "audio": audio
    })
    pause = 0.35 if d["speaker"] in ["chiquito", "echenique"] else 0.45
    current_time = end_s + pause

drop_start_s = current_time + 0.15
DROP_DURATION = 24.0  # 24s of drop
TOTAL_DURATION = drop_start_s + DROP_DURATION
TOTAL_SAMPLES = int(TOTAL_DURATION * SR)

print(f"[*] Timeline total duration: {TOTAL_DURATION:.2f}s | Drop starts at: {drop_start_s:.2f}s")

# Load music track
music_raw, music_sr = sf.read(MUSIC_PATH)
if len(music_raw.shape) > 1:
    music_raw = music_raw[:, 0]
if music_sr != SR:
    num = int(len(music_raw) * SR / music_sr)
    music_raw = signal.resample(music_raw, num)

music_offset_s = 75.0
music_start_idx = int(music_offset_s * SR)
music_needed = TOTAL_SAMPLES

if music_start_idx + music_needed > len(music_raw):
    music_chunk = music_raw[:music_needed]
else:
    music_chunk = music_raw[music_start_idx:music_start_idx + music_needed].copy()

# Build ducking curve
duck_env = np.ones(TOTAL_SAMPLES, dtype=np.float32)
duck_vol = 0.18  # -15 dB during dialogue
transition_samples = int(0.20 * SR)

for ev in timeline_events:
    s_idx = max(0, int((ev["start"] - 0.10) * SR))
    e_idx = min(TOTAL_SAMPLES, int((ev["end"] + 0.15) * SR))
    
    # Ramp down
    r_down_start = max(0, s_idx - transition_samples)
    duck_env[r_down_start:s_idx] = np.linspace(1.0, duck_vol, s_idx - r_down_start)
    duck_env[s_idx:e_idx] = duck_vol
    # Ramp up
    r_up_end = min(TOTAL_SAMPLES, e_idx + transition_samples)
    duck_env[e_idx:r_up_end] = np.linspace(duck_vol, 1.0, r_up_end - e_idx)

# Drop build-up: cut music to silent for 0.4s right before drop, then EXPLODE
drop_hit_sample = int(drop_start_s * SR)
build_cut_start = max(0, drop_hit_sample - int(0.35 * SR))
duck_env[build_cut_start:drop_hit_sample] = np.linspace(duck_vol, 0.0, drop_hit_sample - build_cut_start)
duck_env[drop_hit_sample:] = 1.0

music_mixed = music_chunk * duck_env

# Vocal bus
vocals_bus = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
for ev in timeline_events:
    s_idx = int(ev["start"] * SR)
    e_idx = min(TOTAL_SAMPLES, s_idx + len(ev["audio"]))
    chunk = ev["audio"][:e_idx - s_idx]
    vocals_bus[s_idx:e_idx] += chunk * 0.95

# Master mix
master = music_mixed * 0.72 + vocals_bus * 0.90
max_val = np.max(np.abs(master))
if max_val > 0.96:
    master = master / max_val * 0.95

sf.write(OUT_AUDIO_WAV, master, SR)
cmd_mp3 = ["ffmpeg", "-y", "-i", str(OUT_AUDIO_WAV), "-b:a", "320k", str(OUT_AUDIO_MP3)]
subprocess.run(cmd_mp3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"✓ Master audio exported: {OUT_AUDIO_WAV} and {OUT_AUDIO_MP3}")

# Copy to Music
subprocess.run(["cp", "-f", str(OUT_AUDIO_WAV), "/Users/borjafernandezangulo/Music/CEUTONG_Audio_Master.wav"], check=True)
subprocess.run(["cp", "-f", str(OUT_AUDIO_MP3), "/Users/borjafernandezangulo/Music/CEUTONG_Audio_Master.mp3"], check=True)
print("✓ Centralized in ~/Music/")

# 3. FFT Spectrum & Lip-Sync Frame Telemetry
TOTAL_FRAMES = int(TOTAL_DURATION * FPS)
print(f"[*] Extracting frame telemetry ({TOTAL_FRAMES} frames @ {FPS} fps)...")

frames_data = []
samples_per_frame = int(SR / FPS)
fft_size = 2048
freqs = np.fft.rfftfreq(fft_size, 1.0 / SR)

sub_mask = (freqs >= 20) & (freqs < 120)
mid_mask = (freqs >= 300) & (freqs < 3000)
high_mask = (freqs >= 3000) & (freqs < 14000)

num_bands = 16
band_edges = np.logspace(np.log10(30), np.log10(14000), num_bands + 1)
band_masks = []
for i in range(num_bands):
    band_masks.append((freqs >= band_edges[i]) & (freqs < band_edges[i+1]))

for f in range(TOTAL_FRAMES):
    t_sec = f / FPS
    c_sample = int(t_sec * SR)
    
    # Active dialogue event
    active_ev = None
    for ev in timeline_events:
        if ev["start"] <= t_sec <= ev["end"]:
            active_ev = ev
            break
            
    speaker = active_ev["speaker"] if active_ev else "none"
    text = active_ev["text"] if active_ev else ""
    scene = active_ev["scene"] if active_ev else ("festival_mitxu" if t_sec >= drop_start_s else "skyline")
    
    # Lip sync / vocal amplitude
    vocal_window = vocals_bus[max(0, c_sample - 512):min(TOTAL_SAMPLES, c_sample + 512)]
    vocal_rms = float(np.sqrt(np.mean(vocal_window**2))) if len(vocal_window) > 0 else 0.0
    
    # Flap gap (0 to 38px)
    flap_gap = int(np.clip(vocal_rms * 165, 0, 38)) if active_ev and vocal_rms > 0.02 else 0
    
    # Audio window for FFT
    w_start = max(0, c_sample - fft_size // 2)
    w_end = min(TOTAL_SAMPLES, w_start + fft_size)
    window = master[w_start:w_end]
    if len(window) < fft_size:
        window = np.pad(window, (0, fft_size - len(window)))
        
    spec = np.abs(np.fft.rfft(window * np.hanning(fft_size)))
    rms = float(np.sqrt(np.mean(window**2)))
    sub_val = float(np.mean(spec[sub_mask])) if np.sum(sub_mask) > 0 else 0.0
    mid_val = float(np.mean(spec[mid_mask])) if np.sum(mid_mask) > 0 else 0.0
    high_val = float(np.mean(spec[high_mask])) if np.sum(high_mask) > 0 else 0.0
    
    bands_vals = []
    for m in band_masks:
        val = float(np.mean(spec[m])) if np.sum(m) > 0 else 0.0
        bands_vals.append(round(float(np.clip(val * 0.045, 0.0, 1.0)), 3))
        
    is_drop = t_sec >= drop_start_s
    
    frames_data.append({
        "frame": f,
        "time": round(t_sec, 3),
        "rms": round(float(np.clip(rms * 2.2, 0.0, 1.0)), 3),
        "sub": round(float(np.clip(sub_val * 0.045, 0.0, 1.0)), 3),
        "mid": round(float(np.clip(mid_val * 0.05, 0.0, 1.0)), 3),
        "high": round(float(np.clip(high_val * 0.05, 0.0, 1.0)), 3),
        "bands": bands_vals,
        "speaker": speaker,
        "text": text,
        "scene": scene,
        "borjaTalking": speaker == "borja" and flap_gap > 4,
        "mitxuTalking": speaker == "mitxu" and flap_gap > 4,
        "alainTalking": speaker == "alain" and flap_gap > 4,
        "chiquitoTalking": speaker == "chiquito" and flap_gap > 4,
        "echeniqueTalking": speaker == "echenique" and flap_gap > 4,
        "macgyverTalking": speaker == "macgyver" and flap_gap > 4,
        "flapGap": flap_gap,
        "isDrop": is_drop
    })

meta = {
    "totalDuration": round(TOTAL_DURATION, 2),
    "totalFrames": TOTAL_FRAMES,
    "dropFrame": int(drop_start_s * FPS),
    "dropStartSeconds": round(drop_start_s, 2),
    "fps": FPS
}

out_payload = {
    "metadata": meta,
    "events": [
        {"id": ev["id"], "speaker": ev["speaker"], "start": ev["start"], "end": ev["end"], "text": ev["text"], "scene": ev["scene"]}
        for ev in timeline_events
    ],
    "frames": frames_data
}

with open(OUT_DATA_JSON, "w", encoding="utf-8") as f:
    json.dump(out_payload, f, indent=2, ensure_ascii=False)

print(f"✓ Saved telemetry to {OUT_DATA_JSON} ({len(frames_data)} frames)")
print("=== PROCESAMIENTO DE AUDIO COMPLETO ===")
