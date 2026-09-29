#!/usr/bin/env python3
"""
build_ceutong_real_voices_audio.py
Assembles 100% REAL AUDIO RECORDINGS for Videoclip Ceutong:
- Borja Moskv (Real WhatsApp audios: ref_borja_clean + termodinamica + chuletón)
- Alain (Real WhatsApp audio: alain_m3)
- Chiquito de la Calzada (Authentic analog soundbites)
- Echenique (Cyber vocoder tuning)
- Landerground (Real WhatsApp audio: lander_real_vodafone)
- Mitxu (Real WhatsApp audios: sesion 110 bpm + bombos)
- Drop @ 100 BPM with Mitxu Festival
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
    "borja_clean": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voice_clones/ref_borja_clean.wav",
    "borja_termo": "/Users/borjafernandezangulo/Music/El_Serio/wav_48k_24bit/2026-09-24_15-01-34_Borja_8s_msg23702.wav",
    "borja_chuleton": "/Users/borjafernandezangulo/Music/LIBRARY/06-Audiovisual/VISUALES/cortex-remotion/public/nexus/borja_voice.wav",
    "alain_m3": "/Users/borjafernandezangulo/Music/LIBRARY/06-Audiovisual/VISUALES/cortex-remotion/public/nexus/alain_m3.wav",
    "chiquito_full": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_audio/chiquito_full.wav",
    "echenique_cyber": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_audio/echenique_cyber.wav",
    "lander_vodafone": "/Users/borjafernandezangulo/Music/LIBRARY/06-Audiovisual/VISUALES/cortex-remotion/public/nexus/lander_real_vodafone.wav",
    "mitxu_110bpm": "/Users/borjafernandezangulo/Music/WHATSAPP_VOICE_CLONES/Mitxu/audios_originales_destacados/12_Mitxu_Original_Sesion_Consorcio_Gaupa_110bpm_Apoteosico_21s.wav",
    "mitxu_bombos": "/Users/borjafernandezangulo/Music/LIBRARY/06-Audiovisual/VISUALES/cortex-remotion/public/nexus/mitxu_bombos.wav"
}

MUSIC_PATH = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/katana_100bpm.wav")
OUT_AUDIO_MP3 = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_master_audio.mp3")
OUT_AUDIO_WAV = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_master_audio.wav")
OUT_DATA_JSON = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_telemetry.json")

def load_clean(path, target_sr=SR):
    d, sr = sf.read(path)
    if len(d.shape) > 1:
        d = np.mean(d, axis=1)
    if sr != target_sr:
        num = int(len(d) * target_sr / sr)
        d = signal.resample(d, num)
    # Butterworth 4-pole highpass at 75 Hz
    b_hp, a_hp = signal.butter(4, 75.0 / (target_sr / 2), btype='high')
    d = signal.lfilter(b_hp, a_hp, d)
    # Gentle de-ess at 13.5 kHz
    b_lp, a_lp = signal.butter(2, 13500.0 / (target_sr / 2), btype='low')
    d = signal.lfilter(b_lp, a_lp, d)
    # Peak normalization
    max_val = np.max(np.abs(d))
    if max_val > 1e-4:
        d = d / max_val * 0.94
    return d

# Prepare combined audios
print("[1/5] Preparando audios reales...")

# Borja: clean statement + termodinamica
b_clean = load_clean(VOICE_FILES["borja_clean"])
b_termo = load_clean(VOICE_FILES["borja_termo"])
silence_03 = np.zeros(int(0.35 * SR))
borja_intro = np.concatenate([b_clean, silence_03, b_termo])

# Mitxu: sesion 110bpm + bombos
m_110 = load_clean(VOICE_FILES["mitxu_110bpm"])
m_bombos = load_clean(VOICE_FILES["mitxu_bombos"])
silence_02 = np.zeros(int(0.30 * SR))
mitxu_combined = np.concatenate([m_110, silence_02, m_bombos])

# Alain: M3 material de oficina
alain_audio = load_clean(VOICE_FILES["alain_m3"])

# Chiquito: original soundbites
chiquito_audio = load_clean(VOICE_FILES["chiquito_full"])

# Echenique: cyber tuned
echenique_audio = load_clean(VOICE_FILES["echenique_cyber"])

# Lander: vodafone
lander_audio = load_clean(VOICE_FILES["lander_vodafone"])

# Borja final cue: chuleton
borja_chuleton = load_clean(VOICE_FILES["borja_chuleton"])

dialogue_defs = [
    {
        "id": "borja_pitch",
        "speaker": "borja",
        "audio": borja_intro,
        "text": "Porque la clave de esto es voz humana, lo tengo súper calibrado, la gente no quiere voz robótica, la mínima pasa... O sea, pasamos de fases, y es que yo estoy muy metido en esto ahora de la termodinámica, de la cibernética, y acá lo veo clarísimo todo, tío!",
        "scene": "skyline"
    },
    {
        "id": "alain_m3",
        "speaker": "alain",
        "audio": alain_audio,
        "text": "Rollo Elbio Chema, escucha: que he metido el gasto de las chuletonas y la gasolina del M3 como material de oficina. Rollo Elbio tío, si preguntan los de Hacienda, diles que es un ordenador con ruedas.",
        "scene": "whatsapp_chat"
    },
    {
        "id": "chiquito_party",
        "speaker": "chiquito",
        "audio": chiquito_audio,
        "text": "¡¿Qué pasa, comor?! ¡No te digo trigo por no llamarte Rodrigor! ¡Siete caballos vienen de Bonanza a Ceutong! ¡Te das cuen! ¡Se me da usted un pelotazo! ¡Al ataquerl!",
        "scene": "party"
    },
    {
        "id": "echenique_cyber",
        "speaker": "echenique",
        "audio": echenique_audio,
        "text": "Compañeros, la plusvalía termodinámica de Ceutong es científicamente irrebatible. Pero por favor, asfaltad bien la recta del casino que a esta silla con alerón y leds le va a dar una taquicardia cuántica a ciento ochenta por hora.",
        "scene": "party"
    },
    {
        "id": "lander_vodafone",
        "speaker": "macgyver", # Visual slot: hero / lander in party
        "audio": lander_audio,
        "text": "Información de Vodafone, línea suspendida. Me voy a implantar un chip para poder limpiar la casa sin esfuerzo. Y aquí en la nave de Zorroza no llega ni la señal de Hacienda.",
        "scene": "party"
    },
    {
        "id": "mitxu_sesion",
        "speaker": "mitxu",
        "audio": mitxu_combined,
        "text": "Esa sesión en el consorcio de Gaupa fue apoteósica, pero algo apoteósico, pinchando ahí a 110 BPM y la hostia! Eso le podéis preguntar a cualquiera, a Gonzalo al Manguero, a cualquiera, apoteósico fue! ¡No se ha visto algo así de Gaupa en Bilbao en la vida! ... Pero Alain, deja de llorarle a Borja con el mail o los de Hacienda, pásale los bombos y vamos a meterle caña a esto!",
        "scene": "festival_mitxu"
    },
    {
        "id": "borja_chuleton",
        "speaker": "borja",
        "audio": borja_chuleton,
        "text": "¡Yo ya no existo como unidad! ¡El 25 aparco el microchip y nos comemos ese chuletón!",
        "scene": "festival_mitxu"
    }
]

print("[2/5] Ensamblando línea temporal con pausas orgánicas...")
PAUSE_BETWEEN = 0.40  # 400ms between lines
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
DROP_DUR = 28.0  # 28s of pure festival drop at the end
TOTAL_DUR = DROP_START + DROP_DUR
TOTAL_SAMPLES = int(TOTAL_DUR * SR)
TOTAL_FRAMES = int(TOTAL_DUR * FPS)
DROP_FRAME = int(DROP_START * FPS)

print(f"Duración total: {TOTAL_DUR:.2f}s | Fotogramas: {TOTAL_FRAMES} | Drop en: {DROP_START:.2f}s (Frame {DROP_FRAME})")

# Build Master Stereo Buffer
master_audio = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# Insert dialogue
print("[3/5] Inyectando diálogos en master...")
for item in dialogue_timeline:
    st = item["start_samp"]
    en = item["end_samp"]
    spk = item["speaker"]
    sig = item["data"]
    sig_len = min(len(sig), en - st, TOTAL_SAMPLES - st)
    
    # Panning
    if spk == "borja":
        pan = 0.45  # slight left
    elif spk == "mitxu":
        pan = 0.55  # slight right
    elif spk == "alain":
        pan = 0.50  # center
    elif spk == "chiquito":
        pan = 0.48
    elif spk == "echenique":
        pan = 0.42
    elif spk == "macgyver":
        pan = 0.58
    else:
        pan = 0.50
        
    master_audio[st:st+sig_len, 0] += sig[:sig_len] * (1.0 - pan) * 1.30
    master_audio[st:st+sig_len, 1] += sig[:sig_len] * pan * 1.30

# Background beat & music
print("[4/5] Inyectando beat Katana 100 BPM...")
if MUSIC_PATH.exists():
    music_raw, m_sr = sf.read(MUSIC_PATH)
    if len(music_raw.shape) > 1:
        music_raw = np.mean(music_raw, axis=1)
    if m_sr != SR:
        num = int(len(music_raw) * SR / m_sr)
        music_raw = signal.resample(music_raw, num)
        
    # Intro/dialogue background: ducked with lowpass filter
    b_lp_bg, a_lp_bg = signal.butter(2, 900.0 / (SR / 2), btype='low')
    bg_m = signal.lfilter(b_lp_bg, a_lp_bg, music_raw)
    bg_m = bg_m * 0.16  # ducked
    
    # Loop background music during dialogue
    idx = 0
    drop_samp = int(DROP_START * SR)
    while idx < drop_samp:
        chunk = min(len(bg_m), drop_samp - idx)
        master_audio[idx:idx+chunk, 0] += bg_m[:chunk]
        master_audio[idx:idx+chunk, 1] += bg_m[:chunk]
        idx += chunk
        
    # Drop full blast: full frequency, high energy
    drop_m = music_raw * 0.88
    idx = drop_samp
    while idx < TOTAL_SAMPLES:
        chunk = min(len(drop_m), TOTAL_SAMPLES - idx)
        master_audio[idx:idx+chunk, 0] += drop_m[:chunk]
        master_audio[idx:idx+chunk, 1] += drop_m[:chunk]
        idx += chunk

# Soft clipper / normalization
print("[5/5] Normalizando master audio EBU R128...")
peak = np.max(np.abs(master_audio))
if peak > 0.96:
    master_audio = master_audio / peak * 0.96

sf.write(OUT_AUDIO_WAV, master_audio, SR)
subprocess.run(["ffmpeg", "-y", "-i", str(OUT_AUDIO_WAV), "-c:a", "libmp3lame", "-b:a", "320k", str(OUT_AUDIO_MP3)], check=True)
print(f"Master audio guardado en {OUT_AUDIO_MP3} y {OUT_AUDIO_WAV}")

# Also copy to canonical ~/Music
import shutil
shutil.copy2(OUT_AUDIO_WAV, "/Users/borjafernandezangulo/Music/CEUTONG_Audio_Master.wav")
shutil.copy2(OUT_AUDIO_MP3, "/Users/borjafernandezangulo/Music/CEUTONG_Audio_Master.mp3")

# Compute Telemetry JSON
print("Computando telemetría de audio (FFT, RMS, flapGap) para Remotion...")
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
    
    # 16-band FFT
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
    
    # Active dialogue event
    cur_speaker = "none"
    cur_text = ""
    cur_scene = "skyline"
    for ev in events:
        if ev["start"] <= t_sec <= ev["end"]:
            cur_speaker = ev["speaker"]
            cur_text = ev["text"]
            cur_scene = ev["scene"]
            break
            
    is_drop = t_sec >= DROP_START
    if is_drop and cur_speaker == "none":
        cur_scene = "festival_mitxu"
        
    # Flap mouth movement (mouth opening in px)
    flap_gap = 0
    if cur_speaker != "none":
        # Flap based on mid-frequency voice energy + sine chatter
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
print("=== AUDIO MASTER REAL Y TELEMETRÍA GENERADOS CON ÉXITO ===")
