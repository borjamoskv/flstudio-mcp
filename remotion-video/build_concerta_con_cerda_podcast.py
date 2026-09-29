#!/usr/bin/env python3
"""
build_concerta_con_cerda_podcast.py
Pipeline completo de audio, telemetría y renderizado Remotion para:
PODCAST "CONCERTA CON CERDA"
Personajes: Alain, Borja y Diana.
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
import numpy as np
import scipy.signal as signal
import soundfile as sf
import edge_tts

ROOT_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video")
PUB_DIR = ROOT_DIR / "public"
TMP_DIR = Path("/tmp/concerta_build")
TMP_DIR.mkdir(parents=True, exist_ok=True)

SR = 44100
FPS = 30

DIALOGUE = [
    {
        "speaker": "alain",
        "voice": "es-ES-AlvaroNeural",
        "rate": "+20%",
        "pitch": "+4Hz",
        "text": "¡Tíos, parad máquinas! Que es martes a mediodía y tengo una paranormal activity de cágate lorito. ¡Pim pam pim pam! La Concerta me la tomé el sábado por la tarde con una bolsa de cortezas de cerda y esto me ha hecho como la ayahuasca: ¡me ha reseteado los chakras de la productividad!"
    },
    {
        "speaker": "borja",
        "voice": "es-ES-AlvaroNeural",
        "rate": "+2%",
        "pitch": "-3Hz",
        "text": "Alain, aterriza. El metilfenidato tiene tres horas y media de semivida. El domingo a mediodía ya habías meado hasta la última molécula. Hoy martes tu sangre tiene cero coma cero cero. Estás químicamente virgen. Pura entropía."
    },
    {
        "speaker": "alain",
        "voice": "es-ES-AlvaroNeural",
        "rate": "+22%",
        "pitch": "+5Hz",
        "text": "¡¿Y por qué no tengo el bajón de siempre, Borja?! ¡Llevo seis horas sacando presupuestos atrasados y he pasado la mopa por detrás del frigorífico! ¡Eso es la liana sagrada con la cerda, me cago en diez!"
    },
    {
        "speaker": "diana",
        "voice": "es-ES-ElviraNeural",
        "rate": "-2%",
        "pitch": "+1Hz",
        "text": "Es conmovedora la urgencia del varón moderno por dotar de épica amazónica a su propia desidia cotidiana. Alain, has transformado una cápsula osmótica y unos torreznos en tu Odisea particular. Es el melodrama del burgués con déficit atencional elevado a cantar de gesta."
    },
    {
        "speaker": "borja",
        "voice": "es-ES-AlvaroNeural",
        "rate": "+3%",
        "pitch": "-3Hz",
        "text": "¡Que no hay liana, Alain! No tienes bajón hoy porque el sábado no te metiste catorce copas de ginebra. Tu milagro es simplemente haber dormido ocho horas. Pura entropía."
    },
    {
        "speaker": "alain",
        "voice": "es-ES-AlvaroNeural",
        "rate": "+16%",
        "pitch": "+3Hz",
        "text": "O sea... ¿que no he despertado el tercer ojo? ¿Solo soy un tío descansado comiendo cortezas de cerda?"
    },
    {
        "speaker": "diana",
        "voice": "es-ES-ElviraNeural",
        "rate": "-2%",
        "pitch": "+1Hz",
        "text": "Exacto, Alain. Descansado, alimentado de grasa saturada y clínicamente ordinario."
    },
    {
        "speaker": "borja",
        "voice": "es-ES-AlvaroNeural",
        "rate": "+2%",
        "pitch": "-3Hz",
        "text": "Fin del misterio. Apaga el incienso, cierra la cerda y ponte a currar."
    }
]

async def synthesize_all():
    print("[1/5] Sintetizando voces de Alain, Borja y Diana...")
    audio_clips = []
    for i, item in enumerate(DIALOGUE):
        raw_mp3 = TMP_DIR / f"line_{i:02d}_{item['speaker']}.mp3"
        raw_wav = TMP_DIR / f"line_{i:02d}_{item['speaker']}.wav"
        
        communicate = edge_tts.Communicate(
            text=item["text"],
            voice=item["voice"],
            rate=item["rate"],
            pitch=item["pitch"]
        )
        await communicate.save(str(raw_mp3))
        
        # Convert to 44.1kHz mono WAV
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_mp3),
            "-ar", str(SR), "-ac", "1",
            str(raw_wav)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # Load and filter
        d, sr = sf.read(str(raw_wav))
        # Highpass at 85Hz
        b_hp, a_hp = signal.butter(4, 85.0 / (SR / 2), btype='high')
        d = signal.lfilter(b_hp, a_hp, d)
        # Lowpass at 12kHz
        b_lp, a_lp = signal.butter(2, 12000.0 / (SR / 2), btype='low')
        d = signal.lfilter(b_lp, a_lp, d)
        d = d / (np.max(np.abs(d)) + 1e-6) * 0.92
        
        audio_clips.append((item["speaker"], d, item["text"]))
        print(f"  [✓] Línea {i+1}/{len(DIALOGUE)} ({item['speaker']}): {len(d)/SR:.2f}s")
        
    return audio_clips

def build_timeline(audio_clips):
    print("[2/5] Ensamblando timeline con pausas orgánicas...")
    pause_sec = 0.50
    current_time = 0.60
    
    events = []
    total_audio_samples = 0
    for speaker, audio, text in audio_clips:
        dur = len(audio) / SR
        events.append({
            "speaker": speaker,
            "start_s": current_time,
            "end_s": current_time + dur,
            "audio": audio,
            "text": text
        })
        current_time += dur + pause_sec
        
    total_duration = current_time + 1.2
    total_samples = int(total_duration * SR)
    master_speech = np.zeros(total_samples, dtype=np.float32)
    
    cues = []
    for ev in events:
        s_idx = int(ev["start_s"] * SR)
        e_idx = min(s_idx + len(ev["audio"]), total_samples)
        valid = e_idx - s_idx
        master_speech[s_idx:e_idx] += ev["audio"][:valid]
        cues.append({
            "speaker": ev["speaker"],
            "startFrame": int(ev["start_s"] * FPS),
            "endFrame": int(ev["end_s"] * FPS),
            "text": ev["text"]
        })
        
    return total_duration, master_speech, cues

def master_audio(total_duration, master_speech, cues):
    print("[3/5] Masterizando audio a estándar broadcast (-13 LUFS)...")
    # Soft limiter / compressor
    threshold = 0.22
    compressed = np.copy(master_speech)
    mask = np.abs(master_speech) > threshold
    compressed[mask] = np.sign(master_speech[mask]) * (threshold + (np.abs(master_speech[mask]) - threshold) * 0.35)
    compressed = (compressed / (np.max(np.abs(compressed)) + 1e-6)) * 0.95
    
    raw_wav = TMP_DIR / "southpark_audio_raw.wav"
    sf.write(str(raw_wav), compressed, SR, subtype='PCM_16')
    
    final_wav = PUB_DIR / "southpark_audio.wav"
    final_mp3 = PUB_DIR / "southpark_audio.mp3"
    
    cmd_norm = [
        "ffmpeg", "-y", "-i", str(raw_wav),
        "-af", "loudnorm=I=-13.0:LRA=7.0:TP=-0.5",
        "-ar", str(SR), "-c:a", "pcm_s16le", str(final_wav)
    ]
    subprocess.run(cmd_norm, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    cmd_mp3 = [
        "ffmpeg", "-y", "-i", str(final_wav),
        "-codec:a", "libmp3lame", "-b:a", "256k", str(final_mp3)
    ]
    subprocess.run(cmd_mp3, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"  [✓] Audio máster listo en {final_mp3} ({total_duration:.2f}s)")
    
    # Read back mastered audio for RMS telemetry
    norm_audio, _ = sf.read(str(final_wav))
    if norm_audio.ndim > 1:
        norm_audio = norm_audio[:, 0]
        
    frame_len = int(SR / FPS)
    total_frames = int(total_duration * FPS)
    frames_data = []
    
    for f in range(total_frames):
        s_idx = f * frame_len
        e_idx = min(s_idx + frame_len, len(norm_audio))
        chunk = norm_audio[s_idx:e_idx]
        rms = float(np.sqrt(np.mean(chunk**2))) if len(chunk) > 0 else 0.0
        
        curr_speaker = "none"
        curr_txt = ""
        for cue in cues:
            if cue["startFrame"] <= f <= cue["endFrame"]:
                curr_speaker = cue["speaker"]
                curr_txt = cue["text"]
                break
                
        is_talking = rms > 0.025 and curr_speaker != "none"
        
        is_alain_talking = is_talking and curr_speaker == "alain"
        flap_cycle = np.sin((f * 0.85) * np.pi) ** 2 if is_alain_talking else 0.0
        flap_gap = int(np.clip(rms * 125.0 * flap_cycle, 0, 36)) if is_alain_talking else 0
        
        diana_talking = bool(is_talking and curr_speaker == "diana")
        borja_talking = bool(is_talking and curr_speaker == "borja")
        
        frames_data.append({
            "frame": f,
            "speaker": curr_speaker,
            "rms": round(float(rms), 4),
            "isTalking": bool(is_talking),
            "flapGap": flap_gap,
            "dianaTalking": diana_talking,
            "borjaTalking": borja_talking,
            "text": curr_txt
        })
        
    json_path = PUB_DIR / "southpark_data.json"
    meta = {
        "metadata": {
            "title": "CONCERTA CON CERDA: EL PODCAST",
            "totalFrames": total_frames,
            "fps": FPS,
            "durationSec": round(total_duration, 2),
            "width": 1920,
            "height": 1080
        },
        "cues": cues,
        "frames": frames_data
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        
    print(f"  [✓] Telemetría JSON actualizada en {json_path} ({total_frames} frames)")
    return total_frames

def render_remotion(total_frames):
    print(f"[4/5] Renderizando vídeo con Remotion Engine ({total_frames} frames)...")
    temp_render = ROOT_DIR / "out" / "concerta_con_cerda_raw.mp4"
    temp_render.parent.mkdir(parents=True, exist_ok=True)
    
    cmd_render = [
        "npx", "remotion", "render",
        "src/index.ts", "PodcastSouthParkAlain",
        str(temp_render),
        "--pixel-format=yuv420p",
        "--concurrency=4",
        "--gl=angle"
    ]
    subprocess.run(cmd_render, cwd=str(ROOT_DIR), check=True)
    print(f"  [✓] Render crudo finalizado en {temp_render}")
    
    print("[5/5] Comprimiendo a estándar IDE/WhatsApp (< 20 MB)...")
    final_music_mp4 = Path("/Users/borjafernandezangulo/Music/Podcast_Concerta_Con_Cerda_Remotion_Master.mp4")
    brain_mp4 = Path("/Users/borjafernandezangulo/.gemini/antigravity/brain/50a84f4a-c6a7-4ade-a137-266725411083/Podcast_Concerta_Con_Cerda_Remotion_Master.mp4")
    
    cmd_compress = [
        "ffmpeg", "-y", "-i", str(temp_render),
        "-c:v", "libx264", "-b:v", "1800k", "-maxrate", "2500k", "-bufsize", "4000k",
        "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(final_music_mp4)
    ]
    subprocess.run(cmd_compress, check=True)
    
    # Copy to Brain
    brain_mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", str(final_music_mp4), str(brain_mp4)], check=True)
    
    sz_mb = os.path.getsize(final_music_mp4) / (1024 * 1024)
    print(f"  [✓] Vídeo final masterizado: {final_music_mp4} ({sz_mb:.2f} MB)")
    print(f"  [✓] Copia en Brain: {brain_mp4}")
    
    # Inject into macOS clipboard
    script = f'set the clipboard to POSIX file "{final_music_mp4}"'
    subprocess.run(["osascript", "-e", script], check=True)
    print("  [✓] Vídeo MP4 inyectado en el portapapeles de macOS (listo para Cmd+V en WhatsApp).")
    return final_music_mp4

async def main():
    clips = await synthesize_all()
    dur, speech, cues = build_timeline(clips)
    total_frames = master_audio(dur, speech, cues)
    render_remotion(total_frames)

if __name__ == "__main__":
    asyncio.run(main())
