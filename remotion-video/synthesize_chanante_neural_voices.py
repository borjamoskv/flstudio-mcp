#!/opt/homebrew/Caskroom/miniconda/base/envs/audio/bin/python
"""
synthesize_chanante_neural_voices.py
Síntesis batch Flow-Matching F5-TTS sobre Metal MPS para los 11 parlamentos de
La Hora Chanante (Cuadrilla Nexus): Unai, Mitxu, Patxi, Alain, Lander y Borja.
"""

import gc
import re
import json
import time
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
from scipy.io import wavfile
from f5_tts.api import F5TTS

ROOT_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video")
PUB_DIR = ROOT_DIR / "public"
STEMS_DIR = PUB_DIR / "chanante_neural_stems"
STEMS_DIR.mkdir(parents=True, exist_ok=True)

VAULT_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/cuadrilla-neural-vault")
LANDER_WAV = Path("/Users/borjafernandezangulo/Music/WHATSAPP_VOICE_CLONES/Lander/references/lander_ref_clean.wav")

CHARACTER_REFS = {
    "unai": {
        "ref_audio": str(VAULT_DIR / "voices/references/unai/ref_1.wav"),
        "ref_text": "Paya la nada que estoy en Bilbao que me venía a ver a la Treti o el desastre que han pasado a hacer algo en ese vídeo Y nada de trabajo a lunes, pero bueno, igual es dar una vuelta con Bilbao y tomar algo así",
        "speed": 1.10,
        "cfg_strength": 1.75,
        "nfe_step": 24,
    },
    "mitxu": {
        "ref_audio": str(VAULT_DIR / "voices/references/mitxu/ref_1.wav"),
        "ref_text": "Te voy a apimiento verde, le puedes echar un chorrín de tomatefrito de este orlando y nada, si es que eso no tiene mucho misterio, vamos, es hacer la putas al salos de los chipirones.",
        "speed": 1.15,
        "cfg_strength": 1.80,
        "nfe_step": 24,
    },
    "patxi": {
        "ref_audio": str(VAULT_DIR / "voices/references/patxi/ref_1.wav"),
        "ref_text": "Sí, eso lo he habido yo también, pues eso es lo que me explica con estas cosas es que luego es que es poca agua que esto que lo otro, que cuando todo es prácticamente agua, y siempre voy a llevar un ciclo cerrado, tío, la otra cosa.",
        "speed": 1.22,
        "cfg_strength": 1.80,
        "nfe_step": 24,
    },
    "alain": {
        "ref_audio": str(VAULT_DIR / "voices/references/alain_electro/ref_1.wav"),
        "ref_text": "Boscate esto y míratelo, míratelo, porque a ver no es lo que bueno, yo creo que hay sal de contenta, se lo juraría y lo hay ahí.",
        "speed": 1.15,
        "cfg_strength": 1.80,
        "nfe_step": 24,
    },
    "lander": {
        "ref_audio": str(LANDER_WAV),
        "ref_text": "Me voy a implantar un chip para poder limpiar la casa sin esfuerzo. Y aquí en la nave de Zorroza no llega ni la señal de Hacienda.",
        "speed": 1.12,
        "cfg_strength": 1.70,
        "nfe_step": 24,
    },
    "borja": {
        "ref_audio": str(VAULT_DIR / "voices/references/borja/ref_1.wav"),
        "ref_text": "y se han querido irme porque que no se, en qué momento, junto a gente no me mola y ya está tío, o sea, pues eso, que me aburro, tío, no, no se qué decirte, qué quieres que te diga.",
        "speed": 1.15,
        "cfg_strength": 1.80,
        "nfe_step": 24,
    },
}

DIALOGUE = [
    ("unai", "alain", "Hola, zagales, soy David Lynch. He montao una piscinilla desmontable de plástico en La Rioja con cuatro hierros y después de salir de esto me he venido unos días a flotar con manguitos."),
    ("unai", "borja", "He subido un tema de noise a SoundCloud en privado con clave de cuarenta dígitos. Si la gente lo escucha, se me desmagnetiza el cardado. Ahora voy a Bilbao a ver qué desastre hay."),
    ("mitxu", "unai", "¡Míralo, qué tontaco! Al pimiento verde se le echa un chorrín generoso de Orlando, sal gorda y a correr, ¡que eso no tiene ningún puto misterio!"),
    ("mitxu", "alain", "Y dejad de odiar al que tiene dinero, copón, que tener billetes es hermosísimo. Te plantas tus gafas de soldador a las tres de la mañana y a campeonar en el Juanma."),
    ("patxi", "mitxu", "¡Mitxu, no enciendas la freidora que tengo el bar en ciclo cerrado! El cuerpo humano es setenta por ciento agua: te plantas en el andén de Metro Uribarri con bañador rojo y eres una pila viviente."),
    ("patxi", "lander", "Lo que pasa es que a las eléctricas no les interesa que la peña tenga energía libre inalámbrica por el aire, ¡pero yo he hecho experimentos en el portal y funciona!"),
    ("alain", "patxi", "¡Cuidado con el Bot de Hacienda! ¡Que los revienta, los mata, los masacra! He comprado una caja de ritmos en Róterdam a ciento dieciocho bombos y el algoritmo me ha bloqueao la cuenta."),
    ("alain", "borja", "Toma, Borja, escúchate este audio de quince minutos y treinta y tres segundos a un x donde te explico el artículo catorce de la ley del IVA."),
    ("lander", "alain", "Vengo de la nave de Zorroza... Andaba buscando cobertura cero ge de Vodafone y me he caído en el alcantarillado. En mi nave no hay luz ni WhatsApp: la luz del sol es de flojos."),
    ("lander", "mitxu", "Dos Technics descalibrados encima de cajas de Kas y cuatro mil vinilos llenos de polvo. Landerground en el silicio hasta la tumba."),
    ("borja", "lander", "¡Hijo de puta, hay que ver el videoclip! Fin del asalto chanante."),
]

NUM_MAP = {
    "0": "cero", "1": "uno", "2": "dos", "3": "tres", "4": "cuatro",
    "5": "cinco", "6": "seis", "7": "siete", "8": "ocho", "9": "nueve",
    "10": "diez", "14": "catorce", "15": "quince", "20": "veinte",
    "30": "treinta", "33": "treinta y tres", "40": "cuarenta",
    "50": "cincuenta", "70": "setenta", "100": "cien", "118": "ciento dieciocho",
    "4000": "cuatro mil", "IVA": "I V A", "AEAT": "A E A T",
    "1x": "un equis", "0G": "cero ge"
}

def clean_prosody_text(text: str) -> str:
    t = text
    for k, v in sorted(NUM_MAP.items(), key=lambda x: -len(x[0])):
        t = re.sub(r"\b" + re.escape(k) + r"\b", v, t)
    t = re.sub(r"\.{3,}", " — ", t)
    t = re.sub(r"\.{2}", ", ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def postprocess_stem(raw_wav: Path, target_wav: Path):
    cmd = [
        "ffmpeg", "-y", "-i", str(raw_wav),
        "-af", (
            "highpass=f=60,lowpass=f=7800,"
            "equalizer=f=180:t=q:w=1.2:g=1.5,"
            "equalizer=f=3200:t=q:w=1.0:g=1.8,"
            "loudnorm=I=-14:TP=-1.5:LRA=7"
        ),
        "-ar", "44100", "-ac", "2",
        str(target_wav)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def main():
    print("="*70)
    print("⚡ BATCH VOCES NEURONALES CLONADAS (F5-TTS) · LA HORA CHANANTE")
    print("="*70)

    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    gc.collect()

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[*] Inicializando motor F5-TTS en silicio: {device}")
    t_start_all = time.time()
    f5 = F5TTS(device=device)

    generated_stems = []

    for idx, (speaker, guest, text) in enumerate(DIALOGUE):
        stem_name = f"scene_{idx+1:03d}_{speaker}"
        target_wav = STEMS_DIR / f"{stem_name}_master.wav"
        raw_wav = STEMS_DIR / f"{stem_name}_raw.wav"

        cfg = CHARACTER_REFS.get(speaker, CHARACTER_REFS["borja"])
        clean_text = clean_prosody_text(text)

        print(f"\n[{idx+1}/{len(DIALOGUE)}] Sintetizando {speaker.upper()} ➔ «{clean_text[:45]}...»")

        if target_wav.exists() and target_wav.stat().st_size > 10000:
            print(f"  ⏩ Reutilizando stem preexistente: {target_wav.name}")
            generated_stems.append(target_wav)
            continue

        t0 = time.time()
        wav, sr, _ = f5.infer(
            ref_file=cfg["ref_audio"],
            ref_text=cfg["ref_text"],
            gen_text=clean_text,
            speed=cfg["speed"],
            cfg_strength=cfg["cfg_strength"],
            nfe_step=cfg["nfe_step"],
            seed=42
        )
        sf.write(str(raw_wav), wav, sr)
        postprocess_stem(raw_wav, target_wav)
        dt = time.time() - t0
        print(f"  ✅ Generado en {dt:.1f}s ➔ {target_wav.name}")
        generated_stems.append(target_wav)

    # Concatenate all stems with 0.4s micro-pause between scenes
    print("\n🎚️  Concatenando stems y masterizando pista final...")
    concat_list = STEMS_DIR / "concat_list.txt"
    with open(concat_list, "w") as f:
        for stem in generated_stems:
            f.write(f"file '{stem.resolve()}'\n")

    master_wav = PUB_DIR / "universal_video_master.wav"
    master_mp3 = PUB_DIR / "universal_video_master.mp3"

    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:a", "pcm_s16le", str(master_wav)
    ]
    subprocess.run(cmd_concat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    cmd_mp3 = [
        "ffmpeg", "-y", "-i", str(master_wav),
        "-b:a", "320k", str(master_mp3)
    ]
    subprocess.run(cmd_mp3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Compute FFT telemetry
    print("📊 Extrayendo telemetría FFT de 8 bandas y gap South Park...")
    sr, data = wavfile.read(str(master_wav))
    if data.ndim > 1:
        mono = data.mean(axis=1)
    else:
        mono = data
    mono = mono / (np.max(np.abs(mono)) + 1e-9)

    fps = 30
    total_frames = int(len(mono) / sr * fps)
    samples_per_frame = sr / fps

    # Scene frame bounds
    scenes_meta = []
    current_sample = 0
    for idx, (spk, gst, txt) in enumerate(DIALOGUE):
        stem_wav = generated_stems[idx]
        s_sr, s_data = wavfile.read(str(stem_wav))
        s_len = len(s_data)
        start_f = int(current_sample / sr * fps)
        end_f = int((current_sample + s_len) / sr * fps) - 1
        current_sample += s_len

        scenes_meta.append({
            "id": idx + 1,
            "speaker": spk,
            "guest": gst,
            "text": txt,
            "badge": f"🎭 {spk.upper()} // CHANANTE REAL",
            "color": "#a855f7" if spk == "unai" else ("#c084fc" if spk == "mitxu" else ("#0284c7" if spk == "patxi" else ("#00ffcc" if spk == "alain" else "#38bdf8"))),
            "slide": "bar.jpg",
            "startFrame": start_f,
            "endFrame": end_f
        })

    frames_data = []
    for f in range(total_frames):
        s_start = int(f * samples_per_frame)
        s_end = int(s_start + samples_per_frame)
        chunk = mono[s_start:s_end]
        rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0

        if len(chunk) >= 256:
            fft_vals = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk)), n=256))[:128]
            b_size = 16
            bands = []
            for b in range(8):
                b_val = float(np.mean(fft_vals[b*b_size:(b+1)*b_size]))
                bands.append(round(min(1.0, b_val * 3.8), 2))
        else:
            bands = [0.0] * 8

        is_talking = rms > 0.020
        flap_gap = round(min(28.0, rms * 155.0), 1) if is_talking else 0.0

        frames_data.append({
            "r": round(rms, 3),
            "g": flap_gap,
            "t": 1 if is_talking else 0,
            "b": bands
        })

    payload = {
        "metadata": {
            "title": "LA HORA CHANANTE // CUADRILLA NEXUS",
            "subtitle": "VOCES NEURONALES CLONADAS (F5-TTS) · 11 ESCENAS",
            "totalScenes": len(DIALOGUE),
            "totalDuration": round(len(mono) / sr, 2),
            "totalFrames": total_frames,
            "fps": fps,
            "width": 1920,
            "height": 1080,
            "audioFile": "universal_video_master.mp3"
        },
        "scenes": scenes_meta,
        "frames": frames_data
    }

    telemetry_path = PUB_DIR / "universal_video_telemetry.json"
    with open(telemetry_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    total_time = time.time() - t_start_all
    print("\n" + "="*70)
    print(f"🎉 BATCH COMPLETADO EN {total_time/60:.1f} MINUTOS!")
    print(f"📍 Master Audio WAV: {master_wav} ({payload['metadata']['totalDuration']}s)")
    print(f"📍 Master Audio MP3: {master_mp3}")
    print(f"📍 Telemetría FFT: {telemetry_path} ({total_frames} frames)")
    print("="*70)

if __name__ == "__main__":
    main()
