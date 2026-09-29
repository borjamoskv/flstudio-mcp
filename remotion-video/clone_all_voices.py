#!/usr/bin/env python3
import os, gc, time, subprocess, torch, soundfile as sf
from f5_tts.api import F5TTS

print("=== INICIALIZANDO F5-TTS SOTA ENGINE ===")
if torch.backends.mps.is_available():
    torch.mps.empty_cache()
gc.collect()

ckpt = os.path.expanduser("~/.cache/f5-tts-es/model_1250000.safetensors")
vocab = os.path.expanduser("~/.cache/f5-tts-es/vocab.txt")
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Device: {device}")

kwargs = {"device": device}
if os.path.exists(ckpt) and os.path.exists(vocab):
    kwargs["ckpt_file"] = ckpt
    kwargs["vocab_file"] = vocab
    print(f"Using checkpoint: {ckpt}")

f5 = F5TTS(**kwargs)
print("F5TTS model loaded successfully.\n")

# Directories
PUB_DIR = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voice_clones"
MUSIC_DIR = "/Users/borjafernandezangulo/Music/Voice_Clones_Nexus"
os.makedirs(PUB_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# Voice profiles
VOICES = [
    {
        "id": "borja_moskv",
        "name": "Borja Moskv (Yo)",
        "ref_file": f"{PUB_DIR}/ref_borja_clean.wav",
        "ref_text": "porque la clave de esto es voz humana, lo tengo súper calibrado, la gente no quiere voz rebótica, la mínima pasa.",
        "lines": [
            {
                "tag": "borja_id",
                "text": "A ver chavales, lo tengo clarísimo. Si la clave de esto es la voz humana real de la cuadrilla, aquí no entra ni una gota de nata ni voces robóticas. Katana a cien BPMs y nos forramos en YouTube.",
                "speed": 1.12
            },
            {
                "tag": "borja_remix",
                "text": "Eso le bajas cuarenta BPMs y pelotazo, te lo juro por Dios, lo voy a reventar.",
                "speed": 1.15
            }
        ]
    },
    {
        "id": "mitxu",
        "name": "Mitxu (Mikel Cristóbal)",
        "ref_file": f"{PUB_DIR}/ref_mitxu_3.wav",
        "ref_text": "Mira, tío. Es que ahora es cuando se muestra que el nacionalismo es el gran timo de este país.",
        "lines": [
            {
                "tag": "mitxu_id",
                "text": "¡Yola tío! Menuda mierda de música pincha el rata, house para guiris y progresivo de los noventa. Y ponme la capucha de Kenny bien puesta que me entra biruji en la calva.",
                "speed": 1.12
            },
            {
                "tag": "mitxu_piccicatera",
                "text": "¡Mitxu piccicatera! A ver qué cojones hacéis ahora con el bombo y la gilda espía.",
                "speed": 1.14
            }
        ]
    },
    {
        "id": "alain",
        "name": "Alain Ballesteros",
        "ref_file": f"{PUB_DIR}/ref_alain.wav",
        "ref_text": "Pues nada que no hayamos visto anteriormente, pero la verdad que hacía falta otros sitios de estos sitios pequeños, una programación de pop, de rock, de gas, acojonante.",
        "lines": [
            {
                "tag": "alain_id",
                "text": "Pues la verdad que hacía falta algo así en el Casco Viejo. Le metemos un buen bombo a cien BPMs, un par de txakolis, y esto lo petamos seguro chavales.",
                "speed": 1.12
            },
            {
                "tag": "alain_podcast",
                "text": "Hombre, si es que nos van a llover las demandas pero nos vamos a reír por los cuatro costados.",
                "speed": 1.12
            }
        ]
    }
]

generated_files = []

for v in VOICES:
    print(f"\n==========================================")
    print(f"CLONANDO VOZ: {v['name']} ({v['id']})")
    print(f"Ref: {v['ref_file']}")
    print(f"==========================================")
    
    for item in v["lines"]:
        tag = item["tag"]
        text = item["text"]
        speed = item["speed"]
        
        # Clean text: no ...
        text_clean = text.replace("...", ",").replace("..", ",")
        
        print(f"\n➔ Generando [{tag}]: \"{text_clean}\" (speed={speed})...")
        t0 = time.time()
        
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
        gc.collect()
        
        wav, sr, _ = f5.infer(
            ref_file=v["ref_file"],
            ref_text=v["ref_text"],
            gen_text=text_clean,
            nfe_step=64,
            cfg_strength=1.35,
            speed=speed,
            seed=808
        )
        
        dt = time.time() - t0
        dur = len(wav) / sr
        print(f"✓ Síntesis completada en {dt:.2f}s (Audio: {dur:.2f}s, SR: {sr}Hz)")
        
        # Raw WAV paths
        raw_pub_wav = os.path.join(PUB_DIR, f"{tag}.wav")
        raw_mus_wav = os.path.join(MUSIC_DIR, f"{tag}.wav")
        sf.write(raw_pub_wav, wav, sr)
        sf.write(raw_mus_wav, wav, sr)
        
        # Mastered OPUS paths (EBU R128 Loudnorm + VOIP)
        out_pub_opus = os.path.join(PUB_DIR, f"{tag}.opus")
        out_mus_opus = os.path.join(MUSIC_DIR, f"{tag}.opus")
        
        cmd_opus = [
            "ffmpeg", "-y", "-i", raw_pub_wav,
            "-af", "highpass=f=45,lowpass=f=6000,loudnorm=I=-16:TP=-1.0:LRA=9",
            "-c:a", "libopus", "-b:a", "24k", "-application", "voip",
            out_pub_opus
        ]
        subprocess.run(cmd_opus, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        # Copy to Music
        subprocess.run(["cp", "-f", out_pub_opus, out_mus_opus], check=True)
        
        print(f"✓ Masterizado Opus VOIP -> {out_mus_opus}")
        generated_files.append((v["name"], tag, raw_mus_wav, out_mus_opus, dur))

print("\n==========================================")
print("RESUMEN DE SÍNTESIS Y CLONACIÓN COMPLETA:")
print("==========================================")
for name, tag, wav_p, opus_p, dur in generated_files:
    print(f"- {name} [{tag}]: {dur:.1f}s | {wav_p} | {opus_p}")

