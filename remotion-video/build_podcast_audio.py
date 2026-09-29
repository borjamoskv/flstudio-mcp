#!/usr/bin/env python3
"""
Build Podcast Audio & Transcript Timeline for Remotion
Show: CORTEZAS Y CONCERTAS (Alain Elektrocaniche Edition)
"""
import os
import json
import numpy as np
import scipy.signal as signal
import soundfile as sf
import subprocess

SR = 44100
FPS = 30

# 1. Load clean vocal slices
def load_wav(p):
    d, sr = sf.read(p)
    if len(d.shape) > 1:
        d = d[:, 0]
    if sr != SR:
        num = int(len(d) * SR / sr)
        d = signal.resample(d, num)
    d = d / (np.max(np.abs(d)) + 1e-6) * 0.95
    return d

v_sol = load_wav('/tmp/alain_japan/sol.wav')
v_kremlin = load_wav('/tmp/alain_japan/kremlin.wav')
v_moon = load_wav('/tmp/alain_japan/moon.wav')
v_roque = load_wav('/tmp/alain_japan/roque.wav')

def get_slice(arr, start_s, end_s, fade_ms=25):
    s_idx = int(start_s * SR)
    e_idx = min(int(end_s * SR), len(arr))
    chunk = arr[s_idx:e_idx].copy()
    fl = int((fade_ms / 1000.0) * SR)
    if len(chunk) > fl * 2:
        chunk[:fl] *= np.linspace(0, 1, fl)
        chunk[-fl:] *= np.linspace(1, 0, fl)
    return chunk

# Dialogue timeline cues: (start_s, duration_s, speaker, text, audio_chunk)
cues = [
    # 0.0 - 2.5: Jingle / Host Intro Bed
    # 2.5 - 11.5: Alain's mystery hook
    (2.5, get_slice(v_sol, 0.0, 9.1), "ALAIN", "¿Quién coño fue el viajero secreto a la ciudad, al país del Sol Naciente?"),
    
    # 12.5 - 17.5: Concerta y Kremlin
    (12.5, get_slice(v_kremlin, 1.8, 5.8), "ALAIN", "Una concerta, estoy a punto... de comerme la otra..."),
    (17.5, get_slice(v_kremlin, 26.2, 31.0), "ALAIN", "Y luego ya en el Kremlin según llegué me metí dos tiracres..."),
    
    # 23.5 - 38.5: The cocktail & Moonwalk
    (23.5, get_slice(v_moon, 0.0, 7.5), "ALAIN", "La combinación concerta con tiraco de spiz es acojonante..."),
    (31.5, get_slice(v_moon, 27.5, 34.5), "ALAIN", "Sensación de anfeta de verdad totalmente, sin necesidad..."),
    (39.0, get_slice(v_moon, 34.8, 41.2), "ALAIN", "¡Los discos me los ponía haciendo el moonwalk a las 6 de la mañana!"),
    (45.5, get_slice(v_moon, 42.5, 45.0), "ALAIN", "¡Así como estaba, cabrón!"),
    
    # 48.0 - 62.0: Roque y Loopy
    (48.5, get_slice(v_roque, 0.0, 6.5), "ALAIN", "5 birras, agua con gas, birra chupito y muy bien..."),
    (55.5, get_slice(v_roque, 11.8, 14.2), "ALAIN", "O sea llegué a casa 8 de la mañana..."),
    (58.5, get_slice(v_roque, 16.2, 20.2), "ALAIN", "Roque, roque hasta las 5 o 6 de la tarde..."),
    (63.5, get_slice(v_roque, 21.0, 25.8), "ALAIN", "Pero fantástico vamos... ¡todavía hago loopy a la mañana!")
]

TOTAL_DURATION = 72.0  # 72 seconds = 2160 frames at 30 fps
TOTAL_SAMPLES = int(TOTAL_DURATION * SR)

podcast_speech = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

transcript_cues = []
for start_s, chunk, spk, txt in cues:
    start_idx = int(start_s * SR)
    end_idx = min(start_idx + len(chunk), TOTAL_SAMPLES)
    valid_len = end_idx - start_idx
    if valid_len > 0:
        podcast_speech[start_idx:end_idx] += chunk[:valid_len] * 1.15
        transcript_cues.append({
            "startFrame": int(start_s * FPS),
            "endFrame": int((start_s + len(chunk)/SR) * FPS),
            "speaker": spk,
            "text": txt
        })

# Load background music from Electrocaniche track
bg_music_path = "/Users/borjafernandezangulo/Music/Electrocaniche_In_Japan_(Alain_Electro_Mix).wav"
bg_music, _ = sf.read(bg_music_path)
if len(bg_music.shape) > 1:
    bg_music_mono = (bg_music[:, 0] + bg_music[:, 1]) * 0.5
else:
    bg_music_mono = bg_music

# Slice first 72 seconds of music
bg_slice = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
mlen = min(len(bg_music_mono), TOTAL_SAMPLES)
bg_slice[:mlen] = bg_music_mono[:mlen]

# Ducking: compute envelope of speech and lower music by 12dB when speech is present
speech_env = np.abs(podcast_speech)
b_lp, a_lp = signal.butter(2, 4.0 / (SR / 2), btype='low')
speech_env_smooth = signal.lfilter(b_lp, a_lp, speech_env)
speech_env_smooth = np.clip(speech_env_smooth * 2.5, 0.0, 1.0)

# Ducking factor: 0.15 when speech active, 0.55 when quiet
duck_gain = 0.50 - 0.35 * speech_env_smooth
# Swell at intro (0 - 2.5s) and outro (68 - 72s)
duck_gain[:int(2.5 * SR)] = 0.70
duck_gain[int(68.0 * SR):] = np.linspace(0.40, 0.85, TOTAL_SAMPLES - int(68.0 * SR))

ducked_music = bg_slice * duck_gain

# Master mix
master = (podcast_speech * 0.90) + (ducked_music * 0.60)
master = np.tanh(master * 1.2) * 0.95

# Highpass sub at 35Hz
b_sub, a_sub = signal.butter(2, 35.0 / (SR / 2), btype='high')
master = signal.lfilter(b_sub, a_sub, master)

OUT_DIR = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public"
WAV_OUT = os.path.join(OUT_DIR, "podcast_alain.wav")
MP3_OUT = os.path.join(OUT_DIR, "podcast_alain.mp3")

sf.write(WAV_OUT, master, SR, subtype='PCM_16')
subprocess.run(['ffmpeg', '-y', '-i', WAV_OUT, '-codec:a', 'libmp3lame', '-b:a', '256k', MP3_OUT], check=True, stderr=subprocess.DEVNULL)
print(f"Generated podcast audio: {MP3_OUT} ({TOTAL_DURATION}s)")

# Compute frame-by-frame RMS and spectral bands for video reactivity
print("Computing audio reactivity frames for Remotion...")
frame_len = int(SR / FPS)
audio_frames = []

for f in range(int(TOTAL_DURATION * FPS)):
    s_idx = f * frame_len
    e_idx = min(s_idx + frame_len, TOTAL_SAMPLES)
    chunk = master[s_idx:e_idx]
    if len(chunk) == 0:
        chunk = np.zeros(frame_len)
    
    rms = float(np.sqrt(np.mean(chunk**2)))
    
    # FFT for frequency bands
    w = np.hanning(len(chunk))
    spec = np.abs(np.fft.rfft(chunk * w))
    freqs = np.fft.rfftfreq(len(chunk), 1.0 / SR)
    
    sub_band = float(np.mean(spec[(freqs >= 30) & (freqs <= 120)]) if np.any((freqs >= 30) & (freqs <= 120)) else 0.0)
    mid_band = float(np.mean(spec[(freqs >= 300) & (freqs <= 2500)]) if np.any((freqs >= 300) & (freqs <= 2500)) else 0.0)
    high_band = float(np.mean(spec[(freqs >= 4000) & (freqs <= 12000)]) if np.any((freqs >= 4000) & (freqs <= 12000)) else 0.0)
    
    # 16 visualizer bands
    bands_16 = []
    band_edges = np.logspace(np.log10(40), np.log10(14000), 17)
    for b in range(16):
        b_low, b_high = band_edges[b], band_edges[b+1]
        mask = (freqs >= b_low) & (freqs <= b_high)
        val = float(np.mean(spec[mask])) if np.any(mask) else 0.0
        bands_16.append(min(1.0, val * 0.08))
    
    # Active subtitle cue
    curr_text = ""
    curr_speaker = "ALAIN"
    for cue in transcript_cues:
        if cue["startFrame"] <= f <= cue["endFrame"]:
            curr_text = cue["text"]
            curr_speaker = cue["speaker"]
            break
            
    audio_frames.append({
        "frame": f,
        "rms": min(1.0, rms * 3.5),
        "sub": min(1.0, sub_band * 0.06),
        "mid": min(1.0, mid_band * 0.08),
        "high": min(1.0, high_band * 0.12),
        "bands": bands_16,
        "speaker": curr_speaker,
        "text": curr_text
    })

data_json = {
    "metadata": {
        "title": "CORTEZAS Y CONCERTAS: EL PODCAST",
        "episode": "EP 01: ELECTROCANICHE IN JAPAN",
        "totalFrames": int(TOTAL_DURATION * FPS),
        "fps": FPS,
        "durationSec": TOTAL_DURATION,
        "width": 1920,
        "height": 1080
    },
    "cues": transcript_cues,
    "frames": audio_frames
}

JSON_OUT = os.path.join(OUT_DIR, "podcast_data.json")
with open(JSON_OUT, "w") as f:
    json.dump(data_json, f, indent=2)

print(f"Podcast metadata & audio reactive frames written to: {JSON_OUT}")
print("=== AUDIO BUILD COMPLETE ===")
