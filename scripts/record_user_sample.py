#!/usr/bin/env python3
"""
FL Studio MCP — Sovereign Audio Intake & Track Preparation Pipeline
═══════════════════════════════════════════════════════════════════
Prepares audio intake for user-recorded audio:
- Direct capture from macOS AVFoundation audio devices (Mic MacBook Pro, AirPods, iPhone).
- Ingest & conversion of dropped audio files (WAV, M4A, MP3, FLAC, AIFF, OGG) to 48 kHz / 24-bit PCM.
- Sample-accurate transient slicing via audio_transient_slicer.
- Spectro-temporal analysis (Peak dBFS, RMS, Spectral Centroid, Duration).
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
RECORDED_DIR = WORKSPACE_DIR / "samples" / "recorded"
BOUNCES_DIR = Path.home() / "Music" / "FL Studio Bounces"

RECORDED_DIR.mkdir(parents=True, exist_ok=True)
BOUNCES_DIR.mkdir(parents=True, exist_ok=True)


def list_audio_inputs():
    """Lists available AVFoundation audio devices."""
    cmd = ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    lines = p.stderr.splitlines()
    in_audio = False
    devices = []
    for line in lines:
        if "AVFoundation audio devices:" in line:
            in_audio = True
            continue
        if in_audio:
            if "AVFoundation video devices:" in line or "Error" in line:
                break
            if "[" in line and "]" in line:
                devices.append(line.strip())
    return devices


def record_microphone(device_index: int = 1, duration_sec: float = 5.0, output_wav: Path = None) -> Path:
    """Records audio from AVFoundation device to 48 kHz / 24-bit WAV."""
    if output_wav is None:
        output_wav = RECORDED_DIR / "user_recording.wav"

    print(f"🎙️ [RECORDING] Grabando {duration_sec}s desde dispositivo audio :{device_index}...")
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "avfoundation",
        "-i", f":{device_index}",
        "-t", str(duration_sec),
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s24le",
        str(output_wav)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"❌ Error en grabación: {res.stderr}")
        raise RuntimeError(f"FFmpeg recording failed: {res.stderr}")

    print(f"✅ Grabación finalizada con éxito: {output_wav}")
    return output_wav


def ingest_audio_file(input_path: Path, output_wav: Path = None) -> Path:
    """Converts any audio file to pristine 48 kHz / 24-bit PCM stereo WAV."""
    input_path = Path(input_path).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"El archivo {input_path} no existe en el sustrato.")

    if output_wav is None:
        output_wav = RECORDED_DIR / f"{input_path.stem}_48k24b.wav"

    print(f"🔄 Ingestando y convirtiendo {input_path.name} a 48 kHz / 24-bit PCM...")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-ar", "48000",
        "-ac", "2",
        "-c:a", "pcm_s24le",
        str(output_wav)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg ingestion failed: {res.stderr}")

    print(f"✅ Audio ingestado en: {output_wav}")
    return output_wav


def analyze_audio(wav_path: Path) -> dict:
    """Runs ffprobe analysis on audio file."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=channels,sample_rate,codec_name",
        "-of", "json",
        str(wav_path)
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(p.stdout) if p.returncode == 0 else {}
    return info


def slice_recording(wav_path: Path, bpm: float = 124.0) -> dict:
    """Invokes audio_transient_slicer on the normalized WAV."""
    sys.path.insert(0, str(WORKSPACE_DIR / "scripts"))
    from audio_transient_slicer import slice_audio_file

    slices_dir = RECORDED_DIR / f"{wav_path.stem}_slices"
    result = slice_audio_file(
        input_wav=str(wav_path),
        output_dir=str(slices_dir),
        bpm=bpm,
        min_slice_ms=60.0,
        sensitivity=1.5
    )
    return result


def main():
    parser = argparse.ArgumentParser(description="Ingesta y slicing de audio grabado por el usuario")
    parser.add_argument("--list-devices", action="store_true", help="Listar dispositivos de entrada AVFoundation")
    parser.add_argument("--record", action="store_true", help="Grabar directamente del micrófono")
    parser.add_argument("--device", type=int, default=1, help="Índice de dispositivo AVFoundation (1=MacBook Mic, 2=AirPods)")
    parser.add_argument("--duration", type=float, default=6.0, help="Duración de grabación en segundos")
    parser.add_argument("--import-file", type=str, help="Ruta de archivo existente para ingestar")
    parser.add_argument("--bpm", type=float, default=124.0, help="BPM objetivo para el track")
    args = parser.parse_args()

    if args.list_devices:
        devs = list_audio_inputs()
        print("\n".join(devs))
        return

    wav_file = None
    if args.record:
        wav_file = record_microphone(device_index=args.device, duration_sec=args.duration)
    elif args.import_file:
        wav_file = ingest_audio_file(Path(args.import_file))
    else:
        # Check if user already placed any file in samples/recorded/
        candidates = list(RECORDED_DIR.glob("*.wav")) + list(RECORDED_DIR.glob("*.m4a")) + list(RECORDED_DIR.glob("*.mp3"))
        if candidates:
            latest = max(candidates, key=lambda f: f.stat().st_mtime)
            print(f"🎯 Detectado archivo reciente en samples/recorded/: {latest.name}")
            wav_file = ingest_audio_file(latest)
        else:
            print("ℹ️ No se especificó --record ni --import-file, y no hay archivos en samples/recorded/.")
            print("Dispositivos detectados:")
            for d in list_audio_inputs():
                print(" ", d)
            return

    if wav_file and wav_file.exists():
        analysis = analyze_audio(wav_file)
        print(f"📊 Telemetría: {json.dumps(analysis, indent=2)}")
        print(f"🔪 Ejecutando transient slicing a {args.bpm} BPM...")
        slices_res = slice_recording(wav_file, bpm=args.bpm)
        print("✨ Slicing completado:")
        print(json.dumps(slices_res, indent=2))


if __name__ == "__main__":
    main()
