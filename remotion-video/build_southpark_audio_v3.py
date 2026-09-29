#!/usr/bin/env python3
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
    # Highpass at 90Hz to kill any rumble
    b_hp, a_hp = signal.butter(4, 90.0 / (SR / 2), btype='high')
    d = signal.lfilter(b_hp, a_hp, d)
    # De-ess / smooth top end
    b_lp, a_lp = signal.butter(2, 12000.0 / (SR / 2), btype='low')
    d = signal.lfilter(b_lp, a_lp, d)
    # Normalize peak to 0.90
    d = d / (np.max(np.abs(d)) + 1e-6) * 0.90
    return d

v_diana_intro = load_clean('/tmp/diana_voice.wav')
v_borja = load_clean('/tmp/borja_voice.wav')
v_diana_outro = load_clean('/tmp/diana_outro.wav')

v_sol = load_clean('/tmp/alain_japan/sol.wav')
v_kremlin = load_clean('/tmp/alain_japan/kremlin.wav')
v_moon = load_clean('/tmp/alain_japan/moon.wav')
v_roque = load_clean('/tmp/alain_japan/roque.wav')

def get_slice(arr, start_s, end_s, fade_ms=25):
    s_idx = int(start_s * SR)
    e_idx = min(int(end_s * SR), len(arr))
    chunk = arr[s_idx:e_idx].copy()
    fl = int((fade_ms / 1000.0) * SR)
    if len(chunk) > fl * 2:
        chunk[:fl] *= np.linspace(0, 1, fl)
        chunk[-fl:] *= np.linspace(1, 0, fl)
    return chunk

# Dialogue timeline: Diana -> Borja -> Alain -> Borja -> Alain -> Diana -> Borja
timeline = [
    # 1. Diana opening (0.5s - 8.6s)
    (0.5, "diana", v_diana_intro, "Miedo y Asco en Japan .... ¡OLE OLE! No todos con las puertas abiertas, ¡ole ole guau guau!"),
    
    # 2. Borja deadpan (9.2s - 11.2s)
    (9.2, "borja", v_borja, "Pura entropía."),
    
    # 3. Alain: Japan secret trip (11.8s - 20.8s)
    (11.8, "alain", get_slice(v_sol, 0.0, 9.0), "¿Quién coño fue el viajero secreto a la ciudad, al país del Sol Naciente?"),
    
    # 4. Alain: Concerta (21.4s - 25.4s)
    (21.4, "alain", get_slice(v_kremlin, 1.8, 5.8), "Una concerta, estoy a punto... de comerme la otra..."),
    
    # 5. Alain: Kremlin tiracres (26.0s - 30.8s)
    (26.0, "alain", get_slice(v_kremlin, 26.2, 31.0), "Y luego ya en el Kremlin según llegué me metí dos tiracres..."),
    
    # 6. Alain: Speed + concerta (31.5s - 39.0s)
    (31.5, "alain", get_slice(v_moon, 0.0, 7.5), "Pero creo que la combinación concerta tiraco de spiz es acojonante..."),
    
    # 7. Alain: Moonwalk (39.6s - 46.0s)
    (39.6, "alain", get_slice(v_moon, 34.8, 41.2), "¡Los discos me los ponía haciendo el moonwalk a las 6 de la mañana!"),
    
    # 8. Borja reaction (46.8s - 48.8s)
    (46.8, "borja", v_borja, "Pura entropía."),
    
    # 9. Alain: Birras y chupito (49.4s - 55.4s)
    (49.4, "alain", get_slice(v_roque, 0.0, 6.0), "5 birras al final compaginé... birra chupito y muy bien..."),
    
    # 10. Alain: Roque hasta las 6 (56.0s - 63.5s)
    (56.0, "alain", get_slice(v_roque, 11.8, 19.3), "O sea llegué a casa 8 de la mañana... Roque, roque hasta las 6 de la tarde..."),
    
    # 11. Alain: Loopy (64.0s - 68.5s)
    (64.0, "alain", get_slice(v_roque, 21.0, 25.5), "Pero fantástico vamos... ¡todavía hago loopy a la mañana!"),
    
    # 12. Diana Outro (69.2s - 71.5s)
    (69.2, "diana", v_diana_outro, "¡OLE OLE, GUAU GUAU!"),
    
    # 13. Borja Final Punch (72.2s - 74.2s)
    (72.2, "borja", v_borja, "Pura entropía.")
]

TOTAL_DURATION = 75.0  # 75 seconds = 2250 frames
TOTAL_SAMPLES = int(TOTAL_DURATION * SR)
speech = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

cues = []
for start_s, speaker, chunk, txt in timeline:
    start_idx = int(start_s * SR)
    end_idx = min(start_idx + len(chunk), TOTAL_SAMPLES)
    valid_len = end_idx - start_idx
    if valid_len > 0:
        speech[start_idx:end_idx] += chunk[:valid_len]
        cues.append({
            "speaker": speaker,
            "startFrame": int(start_s * FPS),
            "endFrame": int((start_s + len(chunk)/SR) * FPS),
            "text": txt
        })

# Broadcast speech mastering
threshold = 0.20
compressed = np.copy(speech)
mask = np.abs(speech) > threshold
compressed[mask] = np.sign(speech[mask]) * (threshold + (np.abs(speech[mask]) - threshold) * 0.35)
compressed = (compressed / (np.max(np.abs(compressed)) + 1e-6)) * 0.95

OUT_DIR = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public"
RAW_WAV = os.path.join(OUT_DIR, "southpark_audio_raw.wav")
WAV_PATH = os.path.join(OUT_DIR, "southpark_audio.wav")
MP3_PATH = os.path.join(OUT_DIR, "southpark_audio.mp3")

sf.write(RAW_WAV, compressed, SR, subtype='PCM_16')
cmd_norm = [
    'ffmpeg', '-y', '-i', RAW_WAV,
    '-af', 'loudnorm=I=-13.0:LRA=7.0:TP=-0.5',
    '-ar', str(SR), '-c:a', 'pcm_s16le', WAV_PATH
]
subprocess.run(cmd_norm, check=True, stderr=subprocess.DEVNULL)
subprocess.run(['ffmpeg', '-y', '-i', WAV_PATH, '-codec:a', 'libmp3lame', '-b:a', '256k', MP3_PATH], check=True, stderr=subprocess.DEVNULL)
print(f"Generated broadcast-mastered audio: {MP3_PATH} ({TOTAL_DURATION}s, ZERO MUSIC)")

# Reload mastered audio for accurate RMS per frame
mastered_audio, _ = sf.read(WAV_PATH)
if len(mastered_audio.shape) > 1:
    mastered_audio = mastered_audio[:, 0]

frame_len = int(SR / FPS)
frames_data = []

for f in range(int(TOTAL_DURATION * FPS)):
    s_idx = f * frame_len
    e_idx = min(s_idx + frame_len, len(mastered_audio))
    chunk = mastered_audio[s_idx:e_idx]
    rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
    
    # Active cue & speaker
    curr_speaker = "none"
    curr_txt = ""
    for cue in cues:
        if cue["startFrame"] <= f <= cue["endFrame"]:
            curr_speaker = cue["speaker"]
            curr_txt = cue["text"]
            break
            
    is_talking = rms > 0.03 and curr_speaker != "none"
    
    # Flap gap for Alain
    is_alain_talking = is_talking and curr_speaker == "alain"
    flap_cycle = np.sin((f * 0.85) * np.pi) ** 2 if is_alain_talking else 0.0
    flap_gap = int(np.clip(rms * 120.0 * flap_cycle, 0, 36)) if is_alain_talking else 0
    
    # Mouth scale for Diana and Borja
    diana_talking = bool(is_talking and curr_speaker == "diana")
    borja_talking = bool(is_talking and curr_speaker == "borja")
    
    frames_data.append({
        "frame": f,
        "speaker": curr_speaker,
        "rms": float(rms),
        "isTalking": bool(is_talking),
        "flapGap": flap_gap,
        "dianaTalking": diana_talking,
        "borjaTalking": borja_talking,
        "text": curr_txt
    })

meta = {
    "metadata": {
        "title": "CORTEZAS Y CONCERTAS: SOUTH PARK V3",
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

print(f"Saved South Park frame metadata: {JSON_PATH} ({len(frames_data)} frames)")
