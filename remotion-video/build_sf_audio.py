import os
import subprocess
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

SR = 44100
TOTAL_SEC = 181
TOTAL_SAMPLES = int(SR * TOTAL_SEC)

TMP_DIR = Path("/tmp/sf_audio_parts")
TMP_DIR.mkdir(exist_ok=True)

# 1. Synthesize Dialogues with macOS say
dialogues = [
    # Announcer
    ("ann_r1", "Fred", "Round one! Fight!"),
    ("ann_r2", "Fred", "Round two! Fight!"),
    ("ann_dko1", "Fred", "Double K.O.! Berghain is closed!"),
    ("ann_dko2", "Fred", "Double K.O.! Panorama Bar is destroyed!"),
    
    # Conde Cero (Spanish Spain - Rocko / Eddy)
    ("cz_01", "Rocko (Español (España))", "¡Aupa ahí, aborto mal cerrao! ¿Qué vienes a asustar en Berghain, si pareces un calamar en oferta?"),
    ("cz_02", "Rocko (Español (España))", "¡Toma Hick Hack Asincopao, cagüendios! ¡Aprende compás!"),
    ("cz_03", "Rocko (Español (España))", "¡Aibalaostia! ¡Mírale el escupitajo! ¡Si parece la grasa de los macarrones tras tres días en la encimera!"),
    ("cz_04", "Rocko (Español (España))", "¡Se acabó la tontería! ¡Agárrate al fader que te voy a meter un Sidechain que te chupa hasta la pensión!"),
    ("cz_05", "Rocko (Español (España))", "¡Falso drop de CruEL Label! ¡Silencio sepulcral en Indautxu y a mamar bombo a ciento cuarenta decibelios!"),
    
    # Round 2 vs Nina
    ("cz_06", "Rocko (Español (España))", "¡Aupa Nina! ¡A mí con susurritos de siberiana friolera no me vengas, que en Bilbao los susurros se llaman martillazo neumático de Altos Hornos!"),
    ("cz_07", "Rocko (Español (España))", "¡Toma síncopa de Bilbao, a ver si cuadras a oído sin mirar la pantallita de Pioneer, siesa!"),
    ("cz_08", "Rocko (Español (España))", "¡Mucho postureo en la bañera, pero a las ocho de la mañana en Indautxu te habrías metido un pintxo de tortilla con txakoli en vez de tanto té matcha!"),
    ("cz_09", "Rocko (Español (España))", "¡Falso drop definitivo a máxima presión! ¡Aquí no hay after que valga, me cago en Dios!"),

    # Feto Infinito (will be passed through vocoder)
    ("feto_01", "Flo (Español (España))", "Matriz corrupta... siente el fluido primigenio..."),
    ("feto_02", "Flo (Español (España))", "Placenta ácida... disolución de tejidos..."),
    ("feto_03", "Flo (Español (España))", "Látigo nucleico... mutación en el darkroom..."),
    ("feto_04", "Flo (Español (España))", "Colapso total... moriremos en el cemento..."),

    # Niña Kravitz (Milena ru_RU / Russian English)
    ("nina_01", "Milena", "You don't understand underground, Conde. My 303 comes from Siberia. Spasiba."),
    ("nina_02", "Milena", "Ghetto Kraviz... hypnotic trip recordings... you are hypnotized..."),
    ("nina_03", "Milena", "Bathtub teleport! From Irkutsk with love! Spasiba, Bilbao!")
]

print("🎙️ Synthesizing speech lines with macOS engine...")
audio_clips = {}
for cid, voice, text in dialogues:
    aiff_path = TMP_DIR / f"{cid}.aiff"
    wav_path = TMP_DIR / f"{cid}.wav"
    subprocess.run(["say", "-v", voice, "-o", str(aiff_path), text], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(aiff_path), "-ar", str(SR), "-ac", "1", str(wav_path)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    d, sr = sf.read(str(wav_path))
    audio_clips[cid] = d

# 2. DSP Processing
def process_cz(sig):
    # Pitch down slightly (-15%) & add analog warmth
    # Resample to lower pitch
    resampled = signal.resample(sig, int(len(sig) * 1.15))
    # Bass boost at 120Hz
    b, a = signal.butter(2, [80 / (SR/2), 250 / (SR/2)], btype='bandpass')
    boost = signal.lfilter(b, a, resampled) * 1.5
    out = resampled + boost
    out = np.clip(out * 1.2, -0.95, 0.95)
    return out

def process_vocoder(sig):
    # Create alien robot carrier (65 Hz saw + 130 Hz square)
    t = np.arange(len(sig)) / SR
    carrier = 0.6 * signal.sawtooth(2 * np.pi * 68 * t) + 0.4 * signal.square(2 * np.pi * 136 * t)
    # Ring modulation + bandpass
    modulated = sig * carrier * 2.5
    # Resonant bandpass
    b, a = signal.butter(4, [400 / (SR/2), 3200 / (SR/2)], btype='bandpass')
    filtered = signal.lfilter(b, a, modulated)
    # Mix with sibilance noise
    noise = (np.random.rand(len(sig)) * 2 - 1) * np.abs(sig) * 0.15
    out = filtered + noise
    out = out / (np.max(np.abs(out)) + 1e-6) * 0.95
    return out

def process_nina(sig):
    # Add Space Echo tape delay + stereo touch
    delay_samples = int(0.18 * SR)
    echo = np.zeros(len(sig) + delay_samples)
    echo[:len(sig)] += sig
    echo[delay_samples:] += sig * 0.45
    return echo / (np.max(np.abs(echo)) + 1e-6) * 0.95

def process_announcer(sig):
    # Deep, cavernous arcade echo
    d1 = int(0.12 * SR)
    d2 = int(0.24 * SR)
    out = np.zeros(len(sig) + d2)
    out[:len(sig)] += sig
    out[d1:d1+len(sig)] += sig * 0.4
    out[d2:d2+len(sig)] += sig * 0.2
    return out / (np.max(np.abs(out)) + 1e-6) * 0.95

# 3. SFX Generators
def gen_punch_sfx():
    t = np.arange(int(0.25 * SR)) / SR
    kick = np.sin(2 * np.pi * (160 * np.exp(-t * 25)) * t) * np.exp(-t * 18)
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 22) * 0.4
    return (kick + noise) * 0.9

def gen_hickhack_sfx():
    t = np.arange(int(0.4 * SR)) / SR
    sfx = np.zeros(len(t))
    for i in range(5):
        st = int(i * 0.06 * SR)
        end = min(len(t), st + int(0.04 * SR))
        seg_t = t[:end-st]
        sfx[st:end] += signal.sawtooth(2 * np.pi * 3800 * seg_t) * np.exp(-seg_t * 50)
    return sfx * 0.8

def gen_sidechain_sfx():
    t = np.arange(int(0.8 * SR)) / SR
    sub = np.sin(2 * np.pi * (120 * np.exp(-t * 4)) * t) * np.exp(-t * 2.5)
    return sub * 0.95

def gen_acid_sfx():
    t = np.arange(int(0.6 * SR)) / SR
    # Corrosive noise
    noise = (np.random.rand(len(t)) * 2 - 1)
    b, a = signal.butter(4, [800 / (SR/2), 2400 / (SR/2)], btype='bandpass')
    f_noise = signal.lfilter(b, a, noise) * np.exp(-t * 3.5)
    return f_noise * 0.8

def gen_whip_sfx():
    t = np.arange(int(0.35 * SR)) / SR
    zap = signal.square(2 * np.pi * (3200 * np.exp(-t * 15)) * t) * np.exp(-t * 14)
    return zap * 0.85

def gen_tb303_sfx():
    t = np.arange(int(0.55 * SR)) / SR
    # Resonant acid sweep
    freq = 180 + 2600 * np.exp(-t * 6)
    acid = signal.sawtooth(2 * np.pi * freq * t) * np.exp(-t * 2.8)
    return acid * 0.8

def gen_explosion_sfx():
    t = np.arange(int(2.5 * SR)) / SR
    sub = np.sin(2 * np.pi * (90 * np.exp(-t * 1.5)) * t) * np.exp(-t * 0.8)
    noise = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 1.8)
    return (sub * 0.7 + noise * 0.5) * 0.95

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

print("🧩 Placing dialogue & battle sound effects on timeline...")

# --- ROUND 1 TIMELINE (0 - 90s) ---
place_audio(process_announcer(audio_clips["ann_r1"]), 1.0, vol=1.1)

place_audio(process_cz(audio_clips["cz_01"]), 5.0, vol=1.0, pan=-0.2)

# 14s: Hick Hack strike
place_audio(gen_hickhack_sfx(), 13.5, vol=0.85, pan=-0.1)
place_audio(gen_punch_sfx(), 14.0, vol=0.9, pan=0.3)
place_audio(process_cz(audio_clips["cz_02"]), 16.5, vol=1.0, pan=-0.2)

# 24s: Feto Vocoder
place_audio(process_vocoder(audio_clips["feto_01"]), 23.5, vol=1.1, pan=0.3)
place_audio(gen_acid_sfx(), 30.0, vol=0.9, pan=0.2)
place_audio(gen_punch_sfx(), 30.8, vol=0.85, pan=-0.2)

# 34s: CZ reaction
place_audio(process_cz(audio_clips["cz_03"]), 34.0, vol=1.0, pan=-0.2)

# 44s: Látigo Nucleico
place_audio(process_vocoder(audio_clips["feto_03"]), 43.5, vol=1.1, pan=0.3)
place_audio(gen_whip_sfx(), 49.0, vol=0.9, pan=0.1)
place_audio(gen_punch_sfx(), 49.3, vol=0.9, pan=-0.3)

# 55s: Sidechain CZ
place_audio(process_cz(audio_clips["cz_04"]), 54.0, vol=1.05, pan=-0.2)
place_audio(gen_sidechain_sfx(), 61.0, vol=1.1, pan=-0.1)
place_audio(gen_punch_sfx(), 61.6, vol=1.0, pan=0.3)

# 69s: Feto Colapso
place_audio(process_vocoder(audio_clips["feto_04"]), 68.0, vol=1.05, pan=0.3)

# 77s: Falso Drop CZ
place_audio(process_cz(audio_clips["cz_05"]), 76.0, vol=1.1, pan=-0.2)
place_audio(gen_explosion_sfx(), 83.5, vol=1.1)

# 86s: Double KO R1
place_audio(process_announcer(audio_clips["ann_dko1"]), 86.0, vol=1.15)


# --- ROUND 2 TIMELINE (90 - 180s) ---
place_audio(process_announcer(audio_clips["ann_r2"]), 91.0, vol=1.1)

place_audio(process_cz(audio_clips["cz_06"]), 94.0, vol=1.0, pan=-0.2)

# 105s: Nina 303 line
place_audio(process_nina(audio_clips["nina_01"]), 104.0, vol=1.1, pan=0.3)
place_audio(gen_tb303_sfx(), 111.0, vol=0.9, pan=0.3)
place_audio(gen_punch_sfx(), 111.5, vol=0.85, pan=-0.2)

# 116s: CZ Hick Hack counter
place_audio(process_cz(audio_clips["cz_07"]), 115.0, vol=1.0, pan=-0.2)
place_audio(gen_hickhack_sfx(), 122.0, vol=0.85, pan=-0.1)
place_audio(gen_punch_sfx(), 122.5, vol=0.85, pan=0.3)

# 127s: Nina Ghetto Whisper
place_audio(process_nina(audio_clips["nina_02"]), 126.5, vol=1.15, pan=0.35)
place_audio(gen_punch_sfx(), 133.0, vol=0.8, pan=-0.2)

# 137s: Nina Bathtub Teleport
place_audio(process_nina(audio_clips["nina_03"]), 136.5, vol=1.1, pan=0.3)
place_audio(gen_tb303_sfx(), 141.0, vol=0.85, pan=0.2)
place_audio(gen_punch_sfx(), 141.5, vol=0.9, pan=-0.3)

# 146s: CZ Bañera reaction
place_audio(process_cz(audio_clips["cz_08"]), 146.0, vol=1.05, pan=-0.2)

# 160s: CZ Final Falso Drop
place_audio(process_cz(audio_clips["cz_09"]), 159.0, vol=1.1, pan=-0.2)
place_audio(gen_explosion_sfx(), 168.0, vol=1.15)

# 173s: Double KO R2
place_audio(process_announcer(audio_clips["ann_dko2"]), 173.0, vol=1.2)


# 5. Load Original Music (Debussy Arabesque) as Background Track
print("🎵 Loading & ducking background track (Debussy Arabesque [CRU02])...")
bg_path = "/Users/borjafernandezangulo/Music/Conde_Cero_Debussy_Arabesque_CRU02.mp3"
bg_data, bg_sr = sf.read(bg_path)
if len(bg_data.shape) > 1:
    bg_l = bg_data[:, 0]
    bg_r = bg_data[:, 1]
else:
    bg_l = bg_data
    bg_r = bg_data

if bg_sr != SR:
    bg_l = signal.resample(bg_l, int(len(bg_l) * SR / bg_sr))
    bg_r = signal.resample(bg_r, int(len(bg_r) * SR / bg_sr))

# Trim or pad bg music to TOTAL_SAMPLES
if len(bg_l) < TOTAL_SAMPLES:
    bg_l = np.pad(bg_l, (0, TOTAL_SAMPLES - len(bg_l)))
    bg_r = np.pad(bg_r, (0, TOTAL_SAMPLES - len(bg_r)))
else:
    bg_l = bg_l[:TOTAL_SAMPLES]
    bg_r = bg_r[:TOTAL_SAMPLES]

# Background music level: -10 dB (factor 0.32) so voices & sound FX are punchy & crystal clear
bg_level = 0.32
final_left = master_left + bg_l * bg_level
final_right = master_right + bg_r * bg_level

# Master Soft Limiter
max_val = max(np.max(np.abs(final_left)), np.max(np.abs(final_right)))
if max_val > 0.98:
    final_left = final_left / max_val * 0.96
    final_right = final_right / max_val * 0.96

out_stereo = np.vstack([final_left, final_right]).T

out_wav = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/street_fighter_master_audio.wav"
out_mp3 = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/street_fighter_master_audio.mp3"

sf.write(out_wav, out_stereo, SR)
subprocess.run(["ffmpeg", "-y", "-i", out_wav, "-b:a", "320k", out_mp3],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# Also copy to ~/Music/
shutil_copy = f"/Users/borjafernandezangulo/Music/STREET_FIGHTER_MASTER_SOUNDTRACK.mp3"
subprocess.run(["cp", out_mp3, shutil_copy], check=True)

print(f"🎉 MASTER AUDIO COMPILED!")
print(f"📍 Location: {out_mp3}")
print(f"📍 Music library: {shutil_copy}")
