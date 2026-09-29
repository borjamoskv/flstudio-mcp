#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.append("/Users/borjafernandezangulo/Music/WHATSAPP_VOICE_CLONES")
from voice_vault import VoiceVault

OUT_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/mitxu_videoclip")
OUT_DIR.mkdir(parents=True, exist_ok=True)

vault = VoiceVault()

lines = [
    ("m1", "mitxu", "Yola, mira qué mierda de música pincha el rata. House para guiris y progresivo de los noventa.", 401),
    ("m2", "mitxu", "Es tu cabeza. Jajajajaja.", 402),
    ("b1", "borja", "Eso le bajas cuarenta BPMs y pelotazo. Lo voy a hacer.", 403),
    ("m3", "mitxu", "Es que eso hace. Coge la chunga esa de progresivo y la baja de velocidad. Su novia debe ser piccicatera.", 404),
    ("b2", "borja", "¿Qué es eso?", 405),
    ("m4", "mitxu", "¿Y la de que es de estas de bar de lo viejo como para guiris? Estilo las chungas estas de Bob Sinclar para el verano.", 406),
    ("b3", "borja", "Pues ahí te va, Mitxu: ¡Katana a cien BPMs, puro trance ralentizado!", 407),
]

for lid, speaker, text, seed in lines:
    out_wav = OUT_DIR / f"{lid}_{speaker}.wav"
    print(f"[*] Sintetizando {lid} ({speaker})...")
    vault.synthesize(key=speaker, text=text, output_wav=out_wav, seed=seed)
    print(f"[✓] {out_wav} generado.")

print("\n[★] Todas las voces sintetizadas con éxito.")
