import os
import subprocess
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

SR = 44100
TOTAL_SEC = 50
TOTAL_SAMPLES = int(SR * TOTAL_SEC)

TMP_DIR = Path("/tmp/sf_otegui_audio_parts")
TMP_DIR.mkdir(exist_ok=True, parents=True)

# 1. Extract sliced phrases from ote_clon_raw.wav
raw_ote = "/tmp/ote_clon_raw.wav"
d_raw, sr_raw = sf.read(raw_ote)

# Slice 1: Mario / Street Fighter intro (0.0 to 7.6s)
s1 = d_raw[int(0.0 * sr_raw):int(7.6 * sr_raw)]
sf.write(str(TMP_DIR / "ote_atk1_raw.wav"), s1, sr_raw)
subprocess.run(["ffmpeg", "-y", "-i", str(TMP_DIR / "ote_atk1_raw.wav"), "-ar", str(SR), "-ac", "1", str(TMP_DIR / "ote_atk1.wav")],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# Slice 2: Albaranes Busca Records (11.8 to 21.0s)
s2 = d_raw[int(11.8 * sr_raw):int(21.0 * sr_raw)]
sf.write(str(TMP_DIR / "ote_atk2_raw.wav"), s2, sr_raw)
subprocess.run(["ffmpeg", "-y", "-i", str(TMP_DIR / "ote_atk2_raw.wav"), "-ar", str(SR), "-ac", "1", str(TMP_DIR / "ote_atk2.wav")],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# Slice 3: Calor Praga vinilos 180g (21.2 to 31.0s)
s3 = d_raw[int(21.2 * sr_raw):int(31.0 * sr_raw)]
sf.write(str(TMP_DIR / "ote_super_raw.wav"), s3, sr_raw)
subprocess.run(["ffmpeg", "-y", "-i", str(TMP_DIR / "ote_super_raw.wav"), "-ar", str(SR), "-ac", "1", str(TMP_DIR / "ote_super.wav")],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# 2. SFX Generators via NumPy & SciPy
def gen_punch_sfx():
    t = np.arange(int(0.25 * SR)) / SR
    kick = np.sin(2 * np.pi * (180 * np.exp(-t * 26)) * t) * np.exp(-t * 18)
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 24) * 0.4
    return (kick + noise) * 0.95

def gen_vinyl_shuriken():
    t = np.arange(int(0.55 * SR)) / SR
    freq = 600 + 1800 * np.sin(2 * np.pi * 12 * t)
    scratch = signal.sawtooth(2 * np.pi * freq * t) * np.exp(-t * 5)
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 4) * 0.35
    return (scratch * 0.7 + noise * 0.3) * 0.9

def gen_book_slam():
    t = np.arange(int(0.65 * SR)) / SR
    sub = np.sin(2 * np.pi * (95 * np.exp(-t * 10)) * t) * np.exp(-t * 7)
    thud = signal.square(2 * np.pi * 65 * t) * np.exp(-t * 12) * 0.4
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 15) * 0.3
    return (sub + thud + noise) * 0.95

def gen_excel_zap():
    t = np.arange(int(0.4 * SR)) / SR
    sfx = np.zeros(len(t))
    for i in range(6):
        st = int(i * 0.05 * SR)
        end = min(len(t), st + int(0.04 * SR))
        seg_t = t[:end-st]
        freq = 1200 + i * 400
        sfx[st:end] += signal.square(2 * np.pi * freq * seg_t) * np.exp(-seg_t * 60)
    return sfx * 0.75

def gen_laser_beam():
    t = np.arange(int(0.8 * SR)) / SR
    freq = 2800 * np.exp(-t * 4) + 240
    laser = np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.5)
    b, a = signal.butter(4, [400 / (SR/2), 3500 / (SR/2)], btype='bandpass')
    f_laser = signal.lfilter(b, a, laser)
    return f_laser * 0.9

def gen_super_explosion():
    t = np.arange(int(2.5 * SR)) / SR
    sub = np.sin(2 * np.pi * (75 * np.exp(-t * 1.8)) * t) * np.exp(-t * 1.2)
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 1.6)
    return (sub * 0.75 + noise * 0.5) * 0.95

# 3. Driving Arcade Techno Beat (135 BPM)
def gen_arcade_bgm(total_sec):
    bpm = 135
    beat_sec = 60.0 / bpm
    total_samples = int(total_sec * SR)
    bgm = np.zeros(total_samples)
    
    t_beat = np.arange(int(beat_sec * SR)) / SR
    kick = np.sin(2 * np.pi * (140 * np.exp(-t_beat * 32)) * t_beat) * np.exp(-t_beat * 16)
    
    t_16th = np.arange(int((beat_sec / 4) * SR)) / SR
    bass_note = signal.sawtooth(2 * np.pi * 55 * t_16th) * np.exp(-t_16th * 8) * 0.35
    
    snare = (np.random.rand(len(t_beat)) * 2 - 1) * np.exp(-t_beat * 18) * 0.35
    
    num_beats = int(total_sec / beat_sec)
    for b in range(num_beats):
        st = int(b * beat_sec * SR)
        end_k = min(total_samples, st + len(kick))
        bgm[st:end_k] += kick[:end_k-st] * 0.65
        
        if b % 2 == 1:
            end_s = min(total_samples, st + len(snare))
            bgm[st:end_s] += snare[:end_s-st] * 0.5
            
        for s in range(4):
            st_b = st + int(s * (beat_sec / 4) * SR)
            end_b = min(total_samples, st_b + len(bass_note))
            if st_b < total_samples:
                bgm[st_b:end_b] += bass_note[:end_b-st_b] * 0.45

    b, a = signal.butter(4, 3800 / (SR/2), btype='lowpass')
    filtered_bgm = signal.lfilter(b, a, bgm)
    return filtered_bgm * 0.45

# 4. Mix Master Timeline
master_left = np.zeros(TOTAL_SAMPLES)
master_right = np.zeros(TOTAL_SAMPLES)

def place_audio(clip, time_sec, vol=1.0, pan=0.0):
    start = int(time_sec * SR)
    end = start + len(clip)
    if start >= TOTAL_SAMPLES: return
    if end > TOTAL_SAMPLES:
        clip = clip[:TOTAL_SAMPLES - start]
        end = TOTAL_SAMPLES
    l_vol = vol * (1.0 - max(0, pan))
    r_vol = vol * (1.0 + min(0, pan))
    master_left[start:end] += clip * l_vol
    master_right[start:end] += clip * r_vol

print("🧩 Montando master timeline...")
bgm = gen_arcade_bgm(TOTAL_SEC)
master_left += bgm
master_right += bgm

clips = {}
all_cids = [
    "ann_intro", "ann_shuriken", "ann_counter", "ann_super", "ann_ko",
    "esco_intro", "esco_atk1", "esco_atk2", "esco_super",
    "ote_intro", "ote_atk1", "ote_atk2", "ote_super"
]
for cid in all_cids:
    p = TMP_DIR / f"{cid}.wav"
    if p.exists():
        d, _ = sf.read(str(p))
        clips[cid] = d

# TIMELINE SCHEDULE:
# 0.8s: Announcer: Round One! Fight!
if "ann_intro" in clips:
    place_audio(clips["ann_intro"], 0.8, vol=1.2)

# 2.8s: Otegui Intro Line
if "ote_intro" in clips:
    place_audio(clips["ote_intro"], 2.8, vol=1.15, pan=-0.25)

# 8.0s: Escohotado Intro Line
if "esco_intro" in clips:
    place_audio(clips["esco_intro"], 8.0, vol=1.15, pan=0.25)

# 14.5s: Otegui Vinyl Shuriken Attack
if "ote_atk1" in clips:
    place_audio(clips["ote_atk1"], 14.5, vol=1.15, pan=-0.2)
place_audio(gen_vinyl_shuriken(), 17.5, vol=0.95, pan=-0.1)
if "ann_shuriken" in clips:
    place_audio(clips["ann_shuriken"], 18.0, vol=1.0)
place_audio(gen_punch_sfx(), 18.4, vol=1.05, pan=0.3)

# 21.0s: Escohotado Counter: Tomo Tres Historia de las Drogas
if "esco_atk1" in clips:
    place_audio(clips["esco_atk1"], 21.0, vol=1.15, pan=0.2)
place_audio(gen_book_slam(), 24.5, vol=1.1, pan=0.1)
if "ann_counter" in clips:
    place_audio(clips["ann_counter"], 25.0, vol=1.0)
place_audio(gen_punch_sfx(), 25.3, vol=1.05, pan=-0.3)

# 28.0s: Otegui Macro de Excel Asesina
if "ote_atk2" in clips:
    place_audio(clips["ote_atk2"], 28.0, vol=1.15, pan=-0.2)
place_audio(gen_excel_zap(), 31.5, vol=1.0, pan=-0.1)
place_audio(gen_punch_sfx(), 32.2, vol=1.05, pan=0.3)

# 35.0s: Escohotado Rayo de Empirismo Puro
if "esco_atk2" in clips:
    place_audio(clips["esco_atk2"], 35.0, vol=1.15, pan=0.2)
place_audio(gen_laser_beam(), 38.0, vol=1.05, pan=0.1)
place_audio(gen_punch_sfx(), 38.8, vol=1.05, pan=-0.3)

# 40.5s: Final Climax
if "ote_super" in clips:
    place_audio(clips["ote_super"], 40.2, vol=1.15, pan=-0.2)
if "esco_super" in clips:
    place_audio(clips["esco_super"], 42.0, vol=1.15, pan=0.2)
if "ann_super" in clips:
    place_audio(clips["ann_super"], 44.5, vol=1.2)

# 45.8s: Nuclear Collision Explosion
place_audio(gen_super_explosion(), 45.8, vol=1.25)

# 47.2s: Double K.O.
if "ann_ko" in clips:
    place_audio(clips["ann_ko"], 47.2, vol=1.3)

# Master Limiter
max_val = max(np.max(np.abs(master_left)), np.max(np.abs(master_right)))
if max_val > 0.98:
    master_left = (master_left / max_val) * 0.95
    master_right = (master_right / max_val) * 0.95

stereo_master = np.vstack([master_left, master_right]).T
out_master_wav = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/sf_otegui_escohotado_master.wav"
out_master_mp3 = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/sf_otegui_escohotado_master.mp3"

sf.write(out_master_wav, stereo_master, SR)
subprocess.run(["ffmpeg", "-y", "-i", out_master_wav, "-b:a", "256k", out_master_mp3],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

music_master = "/Users/borjafernandezangulo/Music/StreetFighter_Otegui_vs_Escohotado_Master.mp3"
subprocess.run(["cp", out_master_mp3, music_master], check=True)

print("🎯 Master Audio compilado con éxito:")
print(f"   -> {out_master_wav}")
print(f"   -> {out_master_mp3}")
print(f"   -> {music_master}")
