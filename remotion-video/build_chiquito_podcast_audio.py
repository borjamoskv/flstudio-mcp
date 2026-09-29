#!/usr/bin/env python3
"""
Build Complete Two-Speaker South Park Podcast Audio & Frame Metadata:
ALAIN ELEKTRONISCHE (Sensaciones Reales) vs. BORJA MOSKV (Modo South Park / Chiquito de la Calzada - Explicaciones Científicas C5-REAL)
"""
import os
import json
import numpy as np
import scipy.signal as signal
import soundfile as sf
import subprocess

SR = 44100
FPS = 30

def load_clean(path, target_sr=SR):
    d, sr = sf.read(path)
    if len(d.shape) > 1:
        d = d[:, 0]
    if sr != target_sr:
        num = int(len(d) * target_sr / sr)
        d = signal.resample(d, num)
    # Butterworth 4-pole highpass at 95 Hz
    b_hp, a_hp = signal.butter(4, 95.0 / (target_sr / 2), btype='high')
    d = signal.lfilter(b_hp, a_hp, d)
    # De-ess / smooth top end at 12 kHz
    b_lp, a_lp = signal.butter(2, 12000.0 / (target_sr / 2), btype='low')
    d = signal.lfilter(b_lp, a_lp, d)
    # Normalize peak to 0.90
    d = d / (np.max(np.abs(d)) + 1e-6) * 0.90
    return d

def get_slice(arr, start_s, end_s, fade_ms=25):
    s_idx = int(start_s * SR)
    e_idx = min(int(end_s * SR), len(arr))
    chunk = arr[s_idx:e_idx].copy()
    fl = int((fade_ms / 1000.0) * SR)
    if len(chunk) > fl * 2:
        chunk[:fl] *= np.linspace(0, 1, fl)
        chunk[-fl:] *= np.linspace(1, 0, fl)
    return chunk

# 1. Load Alain's original audio files
v_sol = load_clean('/tmp/alain_japan/sol.wav')
v_kremlin = load_clean('/tmp/alain_japan/kremlin.wav')
v_moon = load_clean('/tmp/alain_japan/moon.wav')
v_roque = load_clean('/tmp/alain_japan/roque.wav')

# Slices of Alain
a_sol = get_slice(v_sol, 0.0, 9.1)
a_concerta = get_slice(v_kremlin, 1.8, 5.8)
a_tiracres = get_slice(v_kremlin, 26.2, 31.0)
# Moonwalk and combination
a_comb1 = get_slice(v_moon, 0.0, 7.5)
a_comb2 = get_slice(v_moon, 27.5, 34.5)
gap_short = np.zeros(int(0.3 * SR), dtype=np.float32)
a_combinacion = np.concatenate([a_comb1, gap_short, a_comb2])

a_mw1 = get_slice(v_moon, 34.8, 41.2)
a_mw2 = get_slice(v_moon, 42.5, 45.0)
a_moonwalk = np.concatenate([a_mw1, gap_short, a_mw2])

a_birr1 = get_slice(v_roque, 0.0, 6.5)
a_birr2 = get_slice(v_roque, 11.8, 14.2)
a_birras = np.concatenate([a_birr1, gap_short, a_birr2])

a_roq1 = get_slice(v_roque, 16.2, 20.2)
a_roq2 = get_slice(v_roque, 21.0, 25.8)
a_roque = np.concatenate([a_roq1, gap_short, a_roq2])

# 2. Load Borja's Chiquito explanations
b1 = load_clean('/tmp/alain_japan/borja_b1.mp3')
b2 = load_clean('/tmp/alain_japan/borja_b2.mp3')
b3 = load_clean('/tmp/alain_japan/borja_b3.mp3')
b4 = load_clean('/tmp/alain_japan/borja_b4.mp3')
b5 = load_clean('/tmp/alain_japan/borja_b5.mp3')
b6 = load_clean('/tmp/alain_japan/borja_b6.mp3')
b7 = load_clean('/tmp/alain_japan/borja_b7.mp3')

# Sequence definition: (speaker, chunk, text)
dialogue = [
    # Round 1
    ("alain", a_sol, "¿Quién coño fue el viajero secreto a la ciudad, al país del Sol Naciente?"),
    ("borja", b1, "¡¿Cómoooor?! ¡¿Quién va a ser, cobarde de la pradera?! ¡Un servidor en misión diplomática de alta exergía! ¡Siete caballos vienen de Bonanza con el billete a Tokio en la mano, te das cuen!"),
    
    # Round 2
    ("alain", a_concerta, "Una concerta, estoy a punto... de comerme la otra..."),
    ("borja", b2, "¡No te comas la otra, pecadorr! ¡Quietoooorl! ¡Que el metilfenidato OROS te bloquea el transportador DAT y te deja el lóbulo frontal más tenso que la cuerda de un funambulista!"),
    
    # Round 3
    ("alain", a_tiracres, "Y luego ya en el Kremlin según llegué me metí dos tiracres..."),
    ("borja", b3, "¡Al ataquerl! ¡Llegas a Dos de Mayo y le metes dos tiracres de sulfato de la calzada! ¡Eso no es juerga, Alain, eso es fisión nuclear en San Francisco sin barras de grafito!"),
    
    # Round 4
    ("alain", a_combinacion, "Pero creo que la combinación concerta tiraco de spiz es acojonante... Sensación de anfeta de verdad totalmente, sin necesidad..."),
    ("borja", b4, "¡Pues claro que es acojonante, fistro duodenal! ¡La concerta te cierra la compuerta de salida y el spiz te vacía las vesículas a chorro! ¡Tenías el estriado dorsal a diez mil revoluciones por minuto! ¡Jarl!"),
    
    # Round 5
    ("alain", a_moonwalk, "¡Los discos me los ponía haciendo el moonwalk a las 6 de la mañana! ¡Así como estaba, cabrón!"),
    ("borja", b5, "¡Haciendo el moonwalk a las seis de la mañana en la baldosa del Kremlin, te das cuen! ¡Eso es Aforismo cinco puro: el cerebelo patinando hacia atrás porque la masa no asimilaba semejante aceleración motriz! ¡No te puédor!"),
    
    # Round 6
    ("alain", a_birras, "5 birras al final compaginé... birra chupito y muy bien... O sea llegué a casa 8 de la mañana..."),
    ("borja", b6, "¡Cinco birras de refrigeración líquida y chupito de boro para que el corazón no se te saliera por la boca! ¡Aterrizaje forzoso a las ocho de la mañana con el tren de aterrizaje echando chispas!"),
    
    # Round 7
    ("alain", a_roque, "Roque, roque hasta las 5 o 6 de la tarde... Pero fantástico vamos... ¡todavía hago loopy a la mañana!"),
    ("borja", b7, "¡Diez horas de roque roque criogénico, hasta luego Lucas! ¡Y el sistema vestibular haciendo loopy a ciento veintiséis BPM porque los canales del oído van desfasados! ¡Estás vivo de milagro, monstruo de la pista!")
]

# Calculate timeline
current_time = 0.8  # Start with 0.8s pre-roll
segments = []

for speaker, chunk, text in dialogue:
    dur = len(chunk) / SR
    start_s = current_time
    end_s = start_s + dur
    segments.append({
        "speaker": speaker,
        "start": start_s,
        "end": end_s,
        "chunk": chunk,
        "text": text
    })
    # Add a conversational pause between speakers (0.45s)
    current_time = end_s + 0.45

# Add 2.0s outro pause
TOTAL_DURATION = current_time + 1.5
TOTAL_SAMPLES = int(TOTAL_DURATION * SR)
print(f"Total Podcast Duration: {TOTAL_DURATION:.2f}s ({TOTAL_DURATION/60:.2f} min), Frames: {int(TOTAL_DURATION * FPS)}")

master_audio = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
cues = []

for seg in segments:
    start_idx = int(seg["start"] * SR)
    chunk = seg["chunk"]
    end_idx = min(start_idx + len(chunk), TOTAL_SAMPLES)
    valid_len = end_idx - start_idx
    if valid_len > 0:
        master_audio[start_idx:end_idx] += chunk[:valid_len]
        cues.append({
            "speaker": seg["speaker"],
            "speakerName": "ALAIN" if seg["speaker"] == "alain" else "BORJA",
            "startFrame": int(seg["start"] * FPS),
            "endFrame": int(seg["end"] * FPS),
            "text": seg["text"]
        })

# Gentle master compression
threshold = 0.28
compressed = np.copy(master_audio)
mask = np.abs(master_audio) > threshold
compressed[mask] = np.sign(master_audio[mask]) * (threshold + (np.abs(master_audio[mask]) - threshold) * 0.45)
# Normalize peak to -0.8 dBFS (~0.91)
compressed = (compressed / (np.max(np.abs(compressed)) + 1e-6)) * 0.91

PUB = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public"
WAV_PATH = os.path.join(PUB, "chiquito_podcast_audio.wav")
MP3_PATH = os.path.join(PUB, "chiquito_podcast_audio.mp3")

sf.write(WAV_PATH, compressed, SR, subtype='PCM_16')
subprocess.run(['ffmpeg', '-y', '-i', WAV_PATH, '-codec:a', 'libmp3lame', '-b:a', '192k', MP3_PATH], check=True, stderr=subprocess.DEVNULL)
print(f"Master MP3 written: {MP3_PATH}")

# Precompute per-frame talking state and mouth flapping gap for BOTH speakers
frame_len = int(SR / FPS)
total_frames = int(TOTAL_DURATION * FPS)
frames_data = []

for f in range(total_frames):
    s_idx = f * frame_len
    e_idx = min(s_idx + frame_len, TOTAL_SAMPLES)
    chunk = compressed[s_idx:e_idx]
    rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
    
    # Active cue check
    active_cue = None
    for cue in cues:
        if cue["startFrame"] <= f <= cue["endFrame"]:
            active_cue = cue
            break
            
    active_speaker = active_cue["speaker"] if active_cue else "none"
    curr_text = active_cue["text"] if active_cue else ""
    curr_speaker_name = active_cue["speakerName"] if active_cue else ""
    
    is_talking = rms > 0.035 and active_speaker != "none"
    flap_cycle = np.sin((f * 0.85) * np.pi) ** 2 if is_talking else 0.0
    gap = int(np.clip(rms * 130.0 * flap_cycle, 0, 36)) if is_talking else 0
    
    alain_gap = gap if active_speaker == "alain" else 0
    borja_gap = gap if active_speaker == "borja" else 0
    
    frames_data.append({
        "frame": f,
        "rms": round(rms, 4),
        "activeSpeaker": active_speaker,
        "speakerName": curr_speaker_name,
        "alainTalking": active_speaker == "alain" and is_talking,
        "alainFlapGap": alain_gap,
        "borjaTalking": active_speaker == "borja" and is_talking,
        "borjaFlapGap": borja_gap,
        "text": curr_text
    })

meta = {
    "metadata": {
        "title": "CORTEZAS Y CONCERTAS: CHIQUITO & SOUTH PARK EDITION",
        "subtitle": "Alain Elektronische vs. Borja Moskv (Explicaciones Científicas C5-REAL)",
        "totalFrames": total_frames,
        "fps": FPS,
        "durationSec": round(TOTAL_DURATION, 2),
        "width": 1920,
        "height": 1080
    },
    "cues": cues,
    "frames": frames_data
}

JSON_PATH = os.path.join(PUB, "chiquito_podcast_data.json")
with open(JSON_PATH, "w") as f:
    json.dump(meta, f, indent=2)

print(f"Precomputed frame metadata saved: {JSON_PATH} ({len(frames_data)} frames)")
