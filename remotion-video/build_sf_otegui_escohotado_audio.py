import os
import gc
import subprocess
import asyncio
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

SR = 44100
# 50 seconds fight timeline
TOTAL_SEC = 50
TOTAL_SAMPLES = int(SR * TOTAL_SEC)

TMP_DIR = Path("/tmp/sf_otegui_audio_parts")
TMP_DIR.mkdir(exist_ok=True, parents=True)

# 1. Synthesize Dialogues
async def synth_edge_voices():
    import edge_tts
    
    edge_lines = [
        # Announcer
        ("ann_intro", "en-US-ChristopherNeural", "-6Hz", "-2%", "Round one! Fight!"),
        ("ann_shuriken", "en-US-ChristopherNeural", "-6Hz", "-2%", "Vinyl Shuriken!"),
        ("ann_counter", "en-US-ChristopherNeural", "-6Hz", "-2%", "Empirical Reversal!"),
        ("ann_super", "en-US-ChristopherNeural", "-6Hz", "-2%", "Super Combo Finish!"),
        ("ann_ko", "en-US-ChristopherNeural", "-8Hz", "-4%", "Double K.O.!"),
        
        # Antonio Escohotado (calm, gravelly, slow philosophical punch)
        ("esco_intro", "es-ES-AlvaroNeural", "-10Hz", "-18%", "Gorka, querido amigo... el comercio no tiene enemigos; el miedo es la única prisión."),
        ("esco_atk1", "es-ES-AlvaroNeural", "-10Hz", "-16%", "¡Siente la gravedad del Tomo Tres de la Historia de las Drogas!"),
        ("esco_atk2", "es-ES-AlvaroNeural", "-10Hz", "-16%", "¡Rayo de empirismo puro! Cero dogma, cien por cien principio activo."),
        ("esco_super", "es-ES-AlvaroNeural", "-10Hz", "-16%", "¡El comercio libre entre hombres despiertos jamás será vencido por un berrinche de almacén!")
    ]
    
    print("🎙️ Sintetizando voces de Escohotado y Announcer con Edge-TTS...")
    for cid, voice, pitch, rate, text in edge_lines:
        out_mp3 = TMP_DIR / f"{cid}.mp3"
        out_wav = TMP_DIR / f"{cid}.wav"
        communicate = edge_tts.Communicate(text, voice, pitch=pitch, rate=rate)
        await communicate.save(str(out_mp3))
        subprocess.run(["ffmpeg", "-y", "-i", str(out_mp3), "-ar", str(SR), "-ac", "1", str(out_wav)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

asyncio.run(synth_edge_voices())

# 2. Synthesize Otegui lines with F5-TTS
print("🎙️ Sintetizando líneas de OTE con F5-TTS...")
import torch
from f5_tts.api import F5TTS

if torch.backends.mps.is_available():
    torch.mps.empty_cache()
gc.collect()

ckpt = os.path.expanduser("~/.cache/f5-tts-es/model_1250000.safetensors")
vocab = os.path.expanduser("~/.cache/f5-tts-es/vocab.txt")
ref_file = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voices/ref_otegui_9s.wav"
ref_text = "porque me mandas unos textos de 300 mil letras que no lo leo y cuando lo leo"

f5 = F5TTS(model="F5TTS_Base", device="mps", ckpt_file=ckpt, vocab_file=vocab)

ote_lines = [
    ("ote_intro", "Escohotado, deja de filosofar, que el calor de Praga me está doblando los vinilos de ciento ochenta gramos!"),
    ("ote_atk1", "Toma prensaje sin compresión de Spotify, filósofo de sofá!"),
    ("ote_atk2", "Te meto una macro de Excel en el lomo con error de referencia circular!"),
    ("ote_super", "Se acabó la teoría! Disipación térmica y a mamar vinilo a cuarenta grados!")
]

for cid, text in ote_lines:
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    gc.collect()
    print(f"  -> Inferencia F5-TTS: {cid}...")
    wav, sr, _ = f5.infer(
        ref_file=ref_file,
        ref_text=ref_text,
        gen_text=text,
        nfe_step=32,
        cfg_strength=1.35,
        speed=1.12,
        seed=808
    )
    raw_wav = TMP_DIR / f"{cid}_raw.wav"
    sf.write(str(raw_wav), wav, sr)
    # Resample to SR (44100)
    out_wav = TMP_DIR / f"{cid}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", str(raw_wav), "-ar", str(SR), "-ac", "1", str(out_wav)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# 3. SFX Generators via NumPy & SciPy
def gen_punch_sfx():
    t = np.arange(int(0.25 * SR)) / SR
    kick = np.sin(2 * np.pi * (180 * np.exp(-t * 26)) * t) * np.exp(-t * 18)
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 24) * 0.4
    return (kick + noise) * 0.95

def gen_vinyl_shuriken():
    t = np.arange(int(0.55 * SR)) / SR
    # Needle scratch and aerodynamic whoosh
    freq = 600 + 1800 * np.sin(2 * np.pi * 12 * t)
    scratch = signal.sawtooth(2 * np.pi * freq * t) * np.exp(-t * 5)
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 4) * 0.35
    return (scratch * 0.7 + noise * 0.3) * 0.9

def gen_book_slam():
    t = np.arange(int(0.65 * SR)) / SR
    # Deep heavy paper/wood impact
    sub = np.sin(2 * np.pi * (95 * np.exp(-t * 10)) * t) * np.exp(-t * 7)
    thud = signal.square(2 * np.pi * 65 * t) * np.exp(-t * 12) * 0.4
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 15) * 0.3
    return (sub + thud + noise) * 0.95

def gen_excel_zap():
    t = np.arange(int(0.4 * SR)) / SR
    # 8-bit digital macro cascade
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
    # Resonant empirical laser sweep
    freq = 2800 * np.exp(-t * 4) + 240
    laser = np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.5)
    b, a = signal.butter(4, [400 / (SR/2), 3500 / (SR/2)], btype='bandpass')
    f_laser = signal.lfilter(b, a, laser)
    return f_laser * 0.9

def gen_super_explosion():
    t = np.arange(int(2.2 * SR)) / SR
    sub = np.sin(2 * np.pi * (75 * np.exp(-t * 1.8)) * t) * np.exp(-t * 1.2)
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 1.6)
    return (sub * 0.75 + noise * 0.5) * 0.95

# 4. Generate Driving Arcade Techno Beat (135 BPM)
def gen_arcade_bgm(total_sec):
    bpm = 135
    beat_sec = 60.0 / bpm
    total_samples = int(total_sec * SR)
    bgm = np.zeros(total_samples)
    
    t_beat = np.arange(int(beat_sec * SR)) / SR
    # Punchy kick drum
    kick = np.sin(2 * np.pi * (140 * np.exp(-t_beat * 32)) * t_beat) * np.exp(-t_beat * 16)
    
    # Bass synth note
    t_16th = np.arange(int((beat_sec / 4) * SR)) / SR
    bass_note = signal.sawtooth(2 * np.pi * 55 * t_16th) * np.exp(-t_16th * 8) * 0.3
    
    # Snare on 2 and 4
    snare = (np.random.rand(len(t_beat)) * 2 - 1) * np.exp(-t_beat * 18) * 0.35
    
    num_beats = int(total_sec / beat_sec)
    for b in range(num_beats):
        st = int(b * beat_sec * SR)
        # Kick
        end_k = min(total_samples, st + len(kick))
        bgm[st:end_k] += kick[:end_k-st] * 0.65
        
        # Snare on beats 1 and 3 (0-indexed)
        if b % 2 == 1:
            end_s = min(total_samples, st + len(snare))
            bgm[st:end_s] += snare[:end_s-st] * 0.5
            
        # 16th bassline pattern
        for s in range(4):
            st_b = st + int(s * (beat_sec / 4) * SR)
            end_b = min(total_samples, st_b + len(bass_note))
            if st_b < total_samples:
                bgm[st_b:end_b] += bass_note[:end_b-st_b] * 0.45

    # Lowpass filter on BGM so dialogue sits crystal clear on top
    b, a = signal.butter(4, 3800 / (SR/2), btype='lowpass')
    filtered_bgm = signal.lfilter(b, a, bgm)
    return filtered_bgm * 0.42

# 5. Mix Master Timeline (50 seconds)
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

# Add arcade background music
bgm = gen_arcade_bgm(TOTAL_SEC)
master_left += bgm
master_right += bgm

# Load all voice clips
clips = {}
all_cids = [
    "ann_intro", "ann_shuriken", "ann_counter", "ann_super", "ann_ko",
    "esco_intro", "esco_atk1", "esco_atk2", "esco_super",
    "ote_intro", "ote_atk1", "ote_atk2", "ote_super"
]
for cid in all_cids:
    d, _ = sf.read(str(TMP_DIR / f"{cid}.wav"))
    clips[cid] = d

# TIMELINE SCHEDULE:
# 0.5s: Announcer: Round One! Fight!
place_audio(clips["ann_intro"], 0.8, vol=1.15)

# 2.5s: Otegui Intro Line
place_audio(clips["ote_intro"], 2.8, vol=1.1, pan=-0.25)

# 8.0s: Escohotado Intro Line
place_audio(clips["esco_intro"], 8.0, vol=1.1, pan=0.25)

# 14.5s: Otegui Vinyl Shuriken Attack
place_audio(clips["ote_atk1"], 14.5, vol=1.1, pan=-0.2)
place_audio(gen_vinyl_shuriken(), 17.5, vol=0.9, pan=-0.1)
place_audio(clips["ann_shuriken"], 18.0, vol=1.0)
place_audio(gen_punch_sfx(), 18.6, vol=1.0, pan=0.3)

# 21.0s: Escohotado Counter: Tomo Tres Historia de las Drogas
place_audio(clips["esco_atk1"], 21.0, vol=1.1, pan=0.2)
place_audio(gen_book_slam(), 24.5, vol=1.1, pan=0.1)
place_audio(clips["ann_counter"], 25.0, vol=1.0)
place_audio(gen_punch_sfx(), 25.3, vol=1.0, pan=-0.3)

# 28.0s: Otegui Macro de Excel Asesina
place_audio(clips["ote_atk2"], 28.0, vol=1.1, pan=-0.2)
place_audio(gen_excel_zap(), 31.5, vol=0.95, pan=-0.1)
place_audio(gen_punch_sfx(), 32.2, vol=1.0, pan=0.3)

# 35.0s: Escohotado Rayo de Empirismo Puro
place_audio(clips["esco_atk2"], 35.0, vol=1.1, pan=0.2)
place_audio(gen_laser_beam(), 38.0, vol=1.0, pan=0.1)
place_audio(gen_punch_sfx(), 38.8, vol=1.0, pan=-0.3)

# 41.0s: FINAL CLASH: Otegui Super Furia Landauer vs Escohotado Enemigos del Comercio
place_audio(clips["ote_super"], 40.5, vol=1.1, pan=-0.2)
place_audio(clips["esco_super"], 42.0, vol=1.1, pan=0.2)
place_audio(clips["ann_super"], 44.5, vol=1.2)

# 45.8s: Nuclear Double Collision Explosion
place_audio(gen_super_explosion(), 45.8, vol=1.2)

# 47.0s: Double K.O. Announcer
place_audio(clips["ann_ko"], 47.2, vol=1.25)

# Limiter & Master Export
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

# Also copy to ~/Music/ canonical directory
music_master = "/Users/borjafernandezangulo/Music/StreetFighter_Otegui_vs_Escohotado_Master.mp3"
subprocess.run(["cp", out_master_mp3, music_master], check=True)

print("🎯 Master Audio compilado con éxito:")
print(f"   -> {out_master_wav}")
print(f"   -> {out_master_mp3}")
print(f"   -> {music_master}")
EOF
