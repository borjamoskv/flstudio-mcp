import os
import gc
import torch
import soundfile as sf
import subprocess
import numpy as np
from f5_tts.api import F5TTS

ckpt = os.path.expanduser("~/.cache/f5-tts-es/model_1250000.safetensors")
vocab = os.path.expanduser("~/.cache/f5-tts-es/vocab.txt")
ref_file = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/voices/ref_otegui_9s.wav"
ref_text = "porque me mandas unos textos de 300 mil letras que no lo leo y cuando lo leo"

print("🔥 Inicializando F5-TTS en silicio Apple Silicon (MPS)...")
f5 = F5TTS(model="F5TTS_Base", device="mps", ckpt_file=ckpt, vocab_file=vocab)

# Sintetizar frase por frase limpiando MPS cache
lines = [
    "Aupa Borja, me dice Mario que me habéis metido a pelear en un Street Fighter contra Escohotado.",
    "Pero a ver, qué coño me estás contando, si yo estoy aquí liado con los albaranes de Busca Records!",
    "Y el calor de Praga me va a doblar los vinilos de ciento ochenta gramos, cagüendios!"
]

pieces = []
sample_rate = 24000

for i, line in enumerate(lines):
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    gc.collect()
    
    print(f"🎙️ Sintetizando línea {i+1}/{len(lines)}: '{line}'")
    wav, sr, _ = f5.infer(
        ref_file=ref_file,
        ref_text=ref_text,
        gen_text=line,
        nfe_step=32,
        cfg_strength=1.35,
        speed=1.12,
        seed=808 + i
    )
    sample_rate = sr
    pieces.append(wav)
    # 0.3s pause between lines
    pieces.append(np.zeros(int(0.3 * sr)))

combined_wav = np.concatenate(pieces)
raw_wav = "/tmp/ote_clon_raw.wav"
sf.write(raw_wav, combined_wav, sample_rate)
print(f"✅ Audio en crudo guardado ({len(combined_wav)/sample_rate:.1f}s)")

# Masterización EBU R128 y compresión VOIP Opus
out_opus = "/Users/borjafernandezangulo/Music/OTE_CLON_VOZ_WHATSAPP.opus"
out_mp3 = "/Users/borjafernandezangulo/Music/OTE_CLON_VOZ_WHATSAPP.mp3"

cmd_opus = [
    "ffmpeg", "-y", "-i", raw_wav,
    "-af", "highpass=f=45,lowpass=f=6500,loudnorm=I=-16:TP=-1.0:LRA=9",
    "-c:a", "libopus", "-b:a", "32k", "-application", "voip",
    out_opus
]
subprocess.run(cmd_opus, check=True)

cmd_mp3 = [
    "ffmpeg", "-y", "-i", raw_wav,
    "-af", "highpass=f=45,lowpass=f=6500,loudnorm=I=-16:TP=-1.0:LRA=9",
    "-b:a", "192k",
    out_mp3
]
subprocess.run(cmd_mp3, check=True)

# Copiar ruta y archivo al portapapeles de macOS
subprocess.run(["osascript", "-e", f'set the clipboard to POSIX file "{out_opus}"'], check=True)
subprocess.run(f'echo "{out_opus}" | pbcopy', shell=True, check=True)

print(f"🎉 CLON VOCAL DE OTE TERMINADO:")
print(f"   -> {out_opus}")
print(f"   -> {out_mp3}")
print("📋 Copiado al portapapeles listo para enviar por WhatsApp!")
EOF
