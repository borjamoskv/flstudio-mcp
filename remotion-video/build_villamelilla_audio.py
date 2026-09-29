#!/usr/bin/env python3
"""
build_villamelilla_audio.py
Compiles 100% REAL AUDIO RECORDINGS for Capítulo 3:
VILLA MELILLA — CIUDAD VACACIONAL
- Alain Electro (alain_real_hacienda: "el bot en el ordenador de Hacienda los revienta")
- Borja Moskv (msg23700: "voy super feliz a 120" + msg23686: "la vez que más cerca he mirado a la muerte")
- Mitxu Luchador (Derrick May & guiris en el yate)
- Chiquito de la Calzada (Authentic analog soundbites)
- Echenique Cyber-Racer (Marina cuántica y ruletas de Bitcoin)
- Drop 100 BPM Katana en el superyate de Villa Melilla
"""

import os
import json
import numpy as np
import scipy.signal as signal
import soundfile as sf
import subprocess
from pathlib import Path

SR = 44100
FPS = 30

VOICE_FILES = {
    "alain_hacienda": "/Users/borjafernandezangulo/Music/LIBRARY/06-Audiovisual/VISUALES/cortex-remotion/public/nexus/alain_real_hacienda.wav",
    "borja_feliz_120": "/Users/borjafernandezangulo/Music/El_Serio/wav_48k_24bit/2026-09-24_15-01-12_Borja_5s_msg23700.wav",
    "borja_coche_muerte": "/Users/borjafernandezangulo/Music/El_Serio/wav_48k_24bit/2026-09-24_14-57-17_Borja_17s_msg23686.wav",
    "borja_chuleton": "/Users/borjafernandezangulo/Music/LIBRARY/06-Audiovisual/VISUALES/cortex-remotion/public/nexus/borja_voice.wav",
    "mitxu_derrick": "/Users/borjafernandezangulo/Music/WHATSAPP_VOICE_CLONES/Mitxu/audios_originales_destacados/03_Mitxu_Original_Derrick_May_Guiris_Rockstar_Cibiu_40s.wav",
    "mitxu_bombos": "/Users/borjafernandezangulo/Music/LIBRARY/06-Audiovisual/VISUALES/cortex-remotion/public/nexus/mitxu_bombos.wav",
    "chiquito_full": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_audio/chiquito_full.wav",
    "echenique_cyber": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_audio/echenique_cyber.wav",
    "lander_vodafone": "/Users/borjafernandezangulo/Music/LIBRARY/06-Audiovisual/VISUALES/cortex-remotion/public/nexus/lander_real_vodafone.wav"
}

MUSIC_PATH = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/katana_100bpm.wav")
OUT_AUDIO_MP3 = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/villamelilla_master_audio.mp3")
OUT_AUDIO_WAV = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/villamelilla_master_audio.wav")
OUT_DATA_JSON = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/villamelilla_telemetry.json")

def load_clean(path, target_sr=SR):
    d, sr = sf.read(path)
    if len(d.shape) > 1:
        d = np.mean(d, axis=1)
    if sr != target_sr:
        num = int(len(d) * target_sr / sr)
        d = signal.resample(d, num)
    # 4-pole highpass at 75 Hz
    b_hp, a_hp = signal.butter(4, 75.0 / (target_sr / 2), btype='high')
    d = signal.lfilter(b_hp, a_hp, d)
    # Gentle de-ess at 13.5 kHz
    b_lp, a_lp = signal.butter(2, 13500.0 / (target_sr / 2), btype='low')
    d = signal.lfilter(b_lp, a_lp, d)
    max_val = np.max(np.abs(d))
    if max_val > 1e-4:
        d = d / max_val * 0.94
    return d

print("[1/5] Cargando y filtrando audios reales de Villa Melilla...")

# Alain introducing Villa Melilla & Hacienda Bot
alain_h = load_clean(VOICE_FILES["alain_hacienda"])

# Borja: 120kmh + muerte en coche
b_120 = load_clean(VOICE_FILES["borja_feliz_120"])
b_coche = load_clean(VOICE_FILES["borja_coche_muerte"])
silence_03 = np.zeros(int(0.35 * SR))
borja_melilla = np.concatenate([b_120, silence_03, b_coche])

# Mitxu: Derrick May / guiris en el yate + bombos
m_derrick = load_clean(VOICE_FILES["mitxu_derrick"])
m_bombos = load_clean(VOICE_FILES["mitxu_bombos"])
mitxu_melilla = np.concatenate([m_derrick, silence_03, m_bombos])

# Chiquito: original soundbites
chiquito_audio = load_clean(VOICE_FILES["chiquito_full"])

# Echenique: cyber tuned
echenique_audio = load_clean(VOICE_FILES["echenique_cyber"])

# Lander: vodafone chip
lander_audio = load_clean(VOICE_FILES["lander_vodafone"])

# Borja final cue: chuleton
borja_chuleton = load_clean(VOICE_FILES["borja_chuleton"])

dialogue_defs = [
    {
        "id": "alain_intro_melilla",
        "speaker": "alain",
        "audio": alain_h,
        "text": "¡El bot en el ordenador de un inspector de Hacienda, los revienta, los vuelve locos, los mata, los masacra y hace de todo! ¡Y ahora montamos Villa Melilla, Ciudad Vacacional al 0% de impuestos!",
        "scene": "resort"
    },
    {
        "id": "borja_velocidad",
        "speaker": "borja",
        "audio": borja_melilla,
        "text": "Fíjate que no te lo he comentado, yo, tío, desde el viaje ahora voy super feliz a 120 tíos, te lo juro, eh. La vez que más cerca he mirado a la muerte ha sido en tu coche, ¡y ahora atracamos el yate en Villa Melilla!",
        "scene": "resort"
    },
    {
        "id": "chiquito_yacht",
        "speaker": "chiquito",
        "audio": chiquito_audio,
        "text": "¡¿Qué pasa, comor?! ¡No te digo trigo por no llamarte Rodrigor! ¡Siete caballos vienen de Bonanza a Villa Melilla! ¡Te das cuen! ¡Se me da usted un pelotazo! ¡Al ataquerl!",
        "scene": "yacht_party"
    },
    {
        "id": "echenique_casino",
        "speaker": "echenique",
        "audio": echenique_audio,
        "text": "Compañeros, la plusvalía termodinámica de Villa Melilla es científicamente irrebatible. La marina cuántica y el casino flotante minan Bitcoin con cero fricción a ciento ochenta por hora.",
        "scene": "yacht_party"
    },
    {
        "id": "lander_suite",
        "speaker": "macgyver",
        "audio": lander_audio,
        "text": "Información de Vodafone, línea suspendida. Me voy a implantar un chip para poder limpiar la casa sin esfuerzo. Y aquí en la nave de Zorroza no llega ni la señal de Hacienda.",
        "scene": "yacht_party"
    },
    {
        "id": "mitxu_guiris",
        "speaker": "mitxu",
        "audio": mitxu_melilla,
        "text": "La noticia es que a mí qué me importan, que si en el año 99 pincha este con Derrick May... Yo no he pinchado con ningún guiri, con ningún guiri ni he pinchado con ningún nacional así potente... pero bueno, yo no voy traumado. ¡Pásale los bombos y vamos a meterle caña a esto!",
        "scene": "festival_yacht"
    },
    {
        "id": "borja_chuleton_melilla",
        "speaker": "borja",
        "audio": borja_chuleton,
        "text": "¡Yo ya no existo como unidad! ¡El 25 aparco el microchip y nos comemos ese chuletón en Villa Melilla!",
        "scene": "festival_yacht"
    }
]

print("[2/5] Ensamblando timeline con pausas orgánicas...")
PAUSE_BETWEEN = 0.40
current_time = 0.50

events = []
dialogue_timeline = []

for d in dialogue_defs:
    dur = len(d["audio"]) / SR
    start_t = current_time
    end_t = start_t + dur
    events.append({
        "id": d["id"],
        "speaker": d["speaker"],
        "start": start_t,
        "end": end_t,
        "text": d["text"],
        "scene": d["scene"]
    })
    dialogue_timeline.append({
        "data": d["audio"],
        "start_samp": int(start_t * SR),
        "end_samp": int(end_t * SR),
        "speaker": d["speaker"],
        "text": d["text"],
        "scene": d["scene"]
    })
    current_time = end_t + PAUSE_BETWEEN

DROP_START = current_time
DROP_DUR = 28.0
TOTAL_DUR = DROP_START + DROP_DUR
TOTAL_SAMPLES = int(TOTAL_DUR * SR)
TOTAL_FRAMES = int(TOTAL_DUR * FPS)
DROP_FRAME = int(DROP_START * FPS)

print(f"Duración total: {TOTAL_DUR:.2f}s | Fotogramas: {TOTAL_FRAMES} | Drop en: {DROP_START:.2f}s (Frame {DROP_FRAME})")

master_audio = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

print("[3/5] Inyectando pistas vocales...")
for item in dialogue_timeline:
    st = item["start_samp"]
    en = item["end_samp"]
    spk = item["speaker"]
    sig = item["data"]
    sig_len = min(len(sig), en - st, TOTAL_SAMPLES - st)
    
    pan = 0.50
    if spk == "borja": pan = 0.45
    elif spk == "mitxu": pan = 0.55
    elif spk == "alain": pan = 0.48
    elif spk == "chiquito": pan = 0.52
    elif spk == "echenique": pan = 0.44
    elif spk == "macgyver": pan = 0.56
    
    master_audio[st:st+sig_len, 0] += sig[:sig_len] * (1.0 - pan) * 1.30
    master_audio[st:st+sig_len, 1] += sig[:sig_len] * pan * 1.30

print("[4/5] Inyectando beat Katana...")
if MUSIC_PATH.exists():
    music_raw, m_sr = sf.read(MUSIC_PATH)
    if len(music_raw.shape) > 1:
        music_raw = np.mean(music_raw, axis=1)
    if m_sr != SR:
        num = int(len(music_raw) * SR / m_sr)
        music_raw = signal.resample(music_raw, num)
        
    b_lp_bg, a_lp_bg = signal.butter(2, 900.0 / (SR / 2), btype='low')
    bg_m = signal.lfilter(b_lp_bg, a_lp_bg, music_raw) * 0.16
    
    idx = 0
    drop_samp = int(DROP_START * SR)
    while idx < drop_samp:
        chunk = min(len(bg_m), drop_samp - idx)
        master_audio[idx:idx+chunk, 0] += bg_m[:chunk]
        master_audio[idx:idx+chunk, 1] += bg_m[:chunk]
        idx += chunk
        
    drop_m = music_raw * 0.88
    idx = drop_samp
    while idx < TOTAL_SAMPLES:
        chunk = min(len(drop_m), TOTAL_SAMPLES - idx)
        master_audio[idx:idx+chunk, 0] += drop_m[:chunk]
        master_audio[idx:idx+chunk, 1] += drop_m[:chunk]
        idx += chunk

print("[5/5] Normalizando master audio...")
peak = np.max(np.abs(master_audio))
if peak > 0.96:
    master_audio = master_audio / peak * 0.96

sf.write(OUT_AUDIO_WAV, master_audio, SR)
subprocess.run(["ffmpeg", "-y", "-i", str(OUT_AUDIO_WAV), "-c:a", "libmp3lame", "-b:a", "320k", str(OUT_AUDIO_MP3)], check=True)

import shutil
shutil.copy2(OUT_AUDIO_WAV, "/Users/borjafernandezangulo/Music/VILLA_MELILLA_Audio_Master.wav")
shutil.copy2(OUT_AUDIO_MP3, "/Users/borjafernandezangulo/Music/VILLA_MELILLA_Audio_Master.mp3")

# Compute Telemetry JSON
print("Computando telemetría FFT y flapGap...")
frames_data = []
SAMPLES_PER_FRAME = int(SR / FPS)
fft_size = 2048

mono = np.mean(master_audio, axis=1)

for f in range(TOTAL_FRAMES):
    st = f * SAMPLES_PER_FRAME
    en = st + SAMPLES_PER_FRAME
    t_sec = f / FPS
    
    chunk = mono[st:en] if en <= len(mono) else mono[st:]
    if len(chunk) == 0:
        chunk = np.zeros(SAMPLES_PER_FRAME)
        
    rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
    
    fft_chunk = mono[st:st+fft_size] if st+fft_size <= len(mono) else np.pad(mono[st:], (0, fft_size - len(mono[st:])))
    spec = np.abs(np.fft.rfft(fft_chunk * np.hanning(len(fft_chunk))))
    spec_bins = len(spec)
    
    bands = []
    edges = np.logspace(np.log10(1), np.log10(spec_bins - 1), 17).astype(int)
    for b in range(16):
        b_st = edges[b]
        b_en = max(edges[b+1], b_st + 1)
        val = float(np.mean(spec[b_st:b_en]))
        bands.append(min(1.0, val * 3.5))
        
    sub = float(np.mean(bands[0:2]))
    mid = float(np.mean(bands[3:8]))
    high = float(np.mean(bands[9:16]))
    
    cur_speaker = "none"
    cur_text = ""
    cur_scene = "resort"
    for ev in events:
        if ev["start"] <= t_sec <= ev["end"]:
            cur_speaker = ev["speaker"]
            cur_text = ev["text"]
            cur_scene = ev["scene"]
            break
            
    is_drop = t_sec >= DROP_START
    if is_drop and cur_speaker == "none":
        cur_scene = "festival_yacht"
        
    flap_gap = 0
    if cur_speaker != "none":
        v_energy = mid * 24 + rms * 20
        flap_gap = int(min(32, max(0, v_energy * (0.6 + 0.4 * np.sin(f * 1.8)))))
        
    frames_data.append({
        "frame": f,
        "time": round(t_sec, 3),
        "rms": round(rms, 4),
        "sub": round(sub, 4),
        "mid": round(mid, 4),
        "high": round(high, 4),
        "bands": [round(b, 4) for b in bands],
        "speaker": cur_speaker,
        "text": cur_text,
        "scene": cur_scene,
        "borjaTalking": cur_speaker == "borja",
        "mitxuTalking": cur_speaker == "mitxu",
        "alainTalking": cur_speaker == "alain",
        "chiquitoTalking": cur_speaker == "chiquito",
        "echeniqueTalking": cur_speaker == "echenique",
        "macgyverTalking": cur_speaker == "macgyver",
        "flapGap": flap_gap,
        "isDrop": is_drop
    })

telemetry = {
    "metadata": {
        "totalDuration": round(TOTAL_DUR, 2),
        "totalFrames": TOTAL_FRAMES,
        "dropFrame": DROP_FRAME,
        "dropStartSeconds": round(DROP_START, 2),
        "fps": FPS
    },
    "events": events,
    "frames": frames_data
}

with open(OUT_DATA_JSON, "w", encoding="utf-8") as f:
    json.dump(telemetry, f, indent=2)

print(f"Telemetría guardada en {OUT_DATA_JSON} ({len(frames_data)} frames)")
print("=== AUDIO MASTER VILLA MELILLA GENERADO CON ÉXITO ===")
EOF
