#!/usr/bin/env python3
import os, gc, time, subprocess, torch
import soundfile as sf
import numpy as np
import scipy.signal as signal
from f5_tts.api import F5TTS

OUT_DIR = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_audio"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. CHIQUITO DE LA CALZADA AUTHENTIC CLIPS
print("=== [1/4] EXTRAYENDO FRASES ORIGINALES DE CHIQUITO DE LA CALZADA ===")
raw_chiquito = "/tmp/chiquito_sounds.mp3"

chiquito_slices = [
    ("chiquito_comor.wav", 170.0, 172.0),
    ("chiquito_bonanza.wav", 36.0, 39.0),
    ("chiquito_pelotazo.wav", 217.0, 219.2),
    ("chiquito_ataquer.wav", 8.0, 10.2),
    ("chiquito_rodrigor.wav", 265.0, 268.0),
    ("chiquito_cuen.wav", 270.0, 271.5),
    ("chiquito_fistro.wav", 121.0, 123.0)
]

for out_name, start_s, end_s in chiquito_slices:
    dst = os.path.join(OUT_DIR, out_name)
    dur = end_s - start_s
    cmd = [
        "ffmpeg", "-y", "-ss", str(start_s), "-i", raw_chiquito,
        "-t", str(dur), "-ar", "44100", "-ac", "1", dst
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  ✓ {out_name} ({dur:.1f}s)")

# Concatenate Chiquito master monologue
c_parts = ["chiquito_comor.wav", "chiquito_rodrigor.wav", "chiquito_bonanza.wav", "chiquito_pelotazo.wav", "chiquito_ataquer.wav"]
c_audio = []
for p in c_parts:
    d, sr = sf.read(os.path.join(OUT_DIR, p))
    c_audio.append(d)
    c_audio.append(np.zeros(int(sr * 0.15))) # short pause
full_chiquito = np.concatenate(c_audio)
sf.write(os.path.join(OUT_DIR, "chiquito_full.wav"), full_chiquito, 44100)
print(f"  ✓ Chiquito master clip: {len(full_chiquito)/44100:.2f}s")


# 2. ECHENIQUE ROBOTIC HIGH-TECH VOICE
print("\n=== [2/4] SINTETIZANDO VOZ ROBÓTICA DE ECHENIQUE ===")
echenique_text = "Compañeros, la plusvalía termodinámica de Ceutong es científicamente irrebatible. Pero por favor, asfaltad bien la recta del casino que a esta silla con alerón y leds le va a dar una taquicardia cuántica a ciento ochenta por hora."
raw_ech = os.path.join(OUT_DIR, "echenique_raw.aiff")
dst_ech = os.path.join(OUT_DIR, "echenique_cyber.wav")

# Use macOS native synth with robot ring-modulator
subprocess.run(["say", "-v", "Eddy (Español (España))", "-r", "165", "-o", raw_ech, echenique_text], check=True)

# Apply Cyber Vocoder / Robotic Ring-Modulation in Python
d_ech, sr_ech = sf.read(raw_ech)
if len(d_ech.shape) > 1:
    d_ech = d_ech[:, 0]
t = np.arange(len(d_ech)) / sr_ech
# Carrier 65 Hz robot drone
mod = 0.65 + 0.35 * np.sin(2 * np.pi * 65.0 * t)
robotic_ech = d_ech * mod
# Add robotic flanger / metallic slap
delay_samples = int(0.012 * sr_ech)
robotic_ech[delay_samples:] += 0.4 * d_ech[:-delay_samples]
robotic_ech = robotic_ech / np.max(np.abs(robotic_ech)) * 0.95
sf.write(dst_ech, robotic_ech, sr_ech)
print(f"  ✓ Echenique cyber voice: {len(robotic_ech)/sr_ech:.2f}s")


# 3. MACGYVER 80s ACTION VOICE
print("\n=== [3/4] SINTETIZANDO VOZ DE MACGYVER ===")
macgyver_text = "Tranquilos todos. Con un clip de oficina, un chicle de fresa y dos botellas de txakoli he hackeado la aduana del Estrecho. Ceutong está al cien por cien de exergía."
raw_mac = os.path.join(OUT_DIR, "macgyver_raw.aiff")
dst_mac = os.path.join(OUT_DIR, "macgyver_hero.wav")
subprocess.run(["say", "-v", "Rocko (Español (España))", "-r", "175", "-o", raw_mac, macgyver_text], check=True)
# Add 80s radio broadcast warmth
cmd_mac = [
    "ffmpeg", "-y", "-i", raw_mac,
    "-af", "highpass=f=120,equalizer=f=3000:t=q:w=1:g=4,aecho=0.8:0.6:25:0.25",
    "-ar", "44100", dst_mac
]
subprocess.run(cmd_mac, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"  ✓ MacGyver hero voice generated")


# 4. BORJA MOSKV, MITXU & ALAIN WITH F5-TTS (SOTA MPS)
print("\n=== [4/4] SINTETIZANDO BORJA MOSKV, MITXU Y ALAIN CON F5-TTS ===")
if torch.backends.mps.is_available():
    torch.mps.empty_cache()
gc.collect()

ckpt = os.path.expanduser("~/.cache/f5-tts-es/model_1250000.safetensors")
vocab = os.path.expanduser("~/.cache/f5-tts-es/vocab.txt")
kwargs = {"device": "mps" if torch.backends.mps.is_available() else "cpu"}
if os.path.exists(ckpt) and os.path.exists(vocab):
    kwargs["ckpt_file"] = ckpt
    kwargs["vocab_file"] = vocab

f5 = F5TTS(**kwargs)
print("F5TTS model initialized on MPS.")

f5_lines = [
    {
        "id": "borja_ceutong_pitch",
        "speaker": "Borja Moskv",
        "ref_file": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voice_clones/ref_borja_clean.wav",
        "ref_text": "porque la clave de esto es voz humana, lo tengo súper calibrado, la gente no quiere voz rebótica, la mínima pasa.",
        "gen_text": "A ver chavales, escuchadme bien. Lo de Ceuta amurallada es una ruina de cojones. Hay que hacer CEUTONG. Desacoplamos la soberanía funcional, metemos un Hong Kong al cero por ciento de impuestos con Tetuán, y en diez años los rascacielos tapan el Peñón de Gibraltar, hostia.",
        "speed": 1.14
    },
    {
        "id": "mitxu_ceutong_rant",
        "speaker": "Mitxu",
        "ref_file": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voice_clones/ref_mitxu_3.wav",
        "ref_text": "Mira, tío. Es que ahora es cuando se muestra que el nacionalismo es el gran timo de este país.",
        "gen_text": "Pero qué me estás contando, Borja. La virgen. Si en Ceuta lo único que hay es el parking de los ferrys y viento de levante. Como montes un Hong Kong ahí, a la que te descuides te ponen una gilda de cinco pisos y a cobrar el txakoli a diez euros.",
        "speed": 1.14
    },
    {
        "id": "alain_negociodad",
        "speaker": "Alain Electro",
        "ref_file": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voice_clones/ref_alain.wav",
        "ref_text": "Pues nada que no hayamos visto anteriormente, pero la verdad que hacía falta otros sitios de estos sitios pequeños, una programación de pop, de rock, de gas, acojonante.",
        "gen_text": "Negociodad Ceutong. Y Villa Melilla, Ciudad Vacacional. Esto lo petamos seguro con dos txakolis en el helipuerto.",
        "speed": 1.12
    },
    {
        "id": "borja_drop_intro",
        "speaker": "Borja Moskv",
        "ref_file": "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voice_clones/ref_borja_clean.wav",
        "ref_text": "porque la clave de esto es voz humana, lo tengo súper calibrado, la gente no quiere voz rebótica, la mínima pasa.",
        "gen_text": "Pues que empiece la fiesta en el helipuerto de Ceutong. Soltad los bombos a cien BPMs.",
        "speed": 1.15
    }
]

for item in f5_lines:
    tag = item["id"]
    text = item["gen_text"]
    print(f"\n➔ F5-TTS [{item['speaker']}]: \"{text}\"...")
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    gc.collect()
    
    wav, sr, _ = f5.infer(
        ref_file=item["ref_file"],
        ref_text=item["ref_text"],
        gen_text=text,
        nfe_step=48,
        cfg_strength=1.85,
        speed=item["speed"],
        seed=808
    )
    p = os.path.join(OUT_DIR, f"{tag}.wav")
    sf.write(p, wav, sr)
    print(f"  ✓ Guardado: {p} ({len(wav)/sr:.2f}s)")

print("\n=== TODAS LAS VOCES DE CEUTONG GENERADAS CON ÉXITO ===")
