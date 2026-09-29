#!/usr/bin/env python3
import os, gc, time, torch, soundfile as sf
from f5_tts.api import F5TTS

if torch.backends.mps.is_available():
    torch.mps.empty_cache()
gc.collect()

ckpt = os.path.expanduser("~/.cache/f5-tts-es/model_1250000.safetensors")
vocab = os.path.expanduser("~/.cache/f5-tts-es/vocab.txt")
device = "mps" if torch.backends.mps.is_available() else "cpu"

kwargs = {"device": device}
if os.path.exists(ckpt) and os.path.exists(vocab):
    kwargs["ckpt_file"] = ckpt
    kwargs["vocab_file"] = vocab

f5 = F5TTS(**kwargs)
print("F5TTS loaded for Mitxu real dialogue lines.")

ref_file = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voice_clones/ref_mitxu_3.wav"
ref_text = "Mira, tío. Es que ahora es cuando se muestra que el nacionalismo es el gran timo de este país."

lines = [
    ("m1_mitxu_real.wav", "Yola, mira qué mierda de música pincha el rata, house para guiris y progresivo de los noventa.", 1.14),
    ("m2_mitxu_real.wav", "¡Es tu cabeza! Jajajajaja.", 1.15),
    ("m3_mitxu_real.wav", "Es que eso hace, coge la chunga esa de progresivo y la baja de velocidad, su novia debe ser piccicatera.", 1.14),
    ("m4_mitxu_real.wav", "¿Y la de que es de estas de bar de lo viejo como para guiris? Estilo las chungas estas de Bob Sinclar para el verano.", 1.12),
]

out_dir = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/mitxu_videoclip"

for fname, text, speed in lines:
    print(f"Generating {fname}...")
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    gc.collect()
    
    wav, sr, _ = f5.infer(
        ref_file=ref_file,
        ref_text=ref_text,
        gen_text=text,
        nfe_step=64,
        cfg_strength=1.35,
        speed=speed,
        seed=808
    )
    p = os.path.join(out_dir, fname)
    sf.write(p, wav, sr)
    print(f"Saved {p} ({len(wav)/sr:.2f}s)")

print("All Mitxu real dialogue synthesized successfully!")
