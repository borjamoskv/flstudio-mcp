#!/usr/bin/env python3
"""
21-Agent Parallel Remotion Renderer for Street Fighter: Conde Cero vs. Feto Infinito & Niña Kravitz
Full Dynamic Combat Animations with Spoken Voices, SFX & Debussy Arabesque Background Music.
Total 5,400 frames (3 minutes @ 30fps) partitioned across 21 parallel agent chunks.
"""
import os
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

CWD = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video"
OUT_DIR = "/tmp/sf_21_agents_chunks"
FINAL_VIDEO_PATH = "/Users/borjafernandezangulo/Music/STREET_FIGHTER_CONDE_CERO_VS_FETO_Y_KRAVITZ.mp4"
AUDIO_MASTER = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/street_fighter_master_audio.mp3"

# Clean out directory for fresh dynamic combat render
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)
os.makedirs(OUT_DIR, exist_ok=True)

TOTAL_FRAMES = 5400
NUM_AGENTS = 21

CHUNK_SIZE = TOTAL_FRAMES // NUM_AGENTS  # 257 frames
CHUNKS = []
for i in range(NUM_AGENTS):
    start_f = i * CHUNK_SIZE
    if i == NUM_AGENTS - 1:
        end_f = TOTAL_FRAMES - 1
    else:
        end_f = (i + 1) * CHUNK_SIZE - 1
    CHUNKS.append((i + 1, start_f, end_f))

def render_agent_chunk(chunk_info):
    agent_id, start_f, end_f = chunk_info
    out_file = os.path.join(OUT_DIR, f"agent_chunk_{agent_id:02d}.mp4")

    print(f"⚡ [AGENTE {agent_id:02d}/21] Renderizando combate frames {start_f}..{end_f} ({end_f - start_f + 1} frames)...")
    t0 = time.time()
    cmd = [
        "npx", "remotion", "render", "src/index.ts", "StreetFighterBerghain",
        out_file, f"--frames={start_f}-{end_f}", "--gl=angle", "--concurrency=4"
    ]
    res = subprocess.run(cmd, cwd=CWD, capture_output=True, text=True)
    dt = time.time() - t0

    if res.returncode != 0:
        print(f"❌ [AGENTE {agent_id:02d}/21] ERROR: {res.stderr[-300:]}")
        raise RuntimeError(f"Agente {agent_id} falló al renderizar")

    sz = os.path.getsize(out_file) / (1024 * 1024)
    print(f"✅ [AGENTE {agent_id:02d}/21] Completado en {dt:.1f}s ({sz:.2f} MB)")
    return agent_id, out_file, dt

def main():
    print(f"🚀 INICIANDO ENJAMBRE DE 21 AGENTES: COMBATE COMPLETO SOTA (ROLLO MITXU)...")
    print(f"📊 Composición: StreetFighterBerghain (5.400 frames / 180s @ 30fps)")
    print(f"👥 Total Agentes en Paralelo: 21")
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(render_agent_chunk, c): c for c in CHUNKS}
        for future in as_completed(futures):
            agent_id, out_file, dt = future.result()

    print("\n🎉 ¡LOS 21 AGENTES HAN COMPLETADO SUS CHUNKS!")
    print("📦 Ensamblando secuencia de vídeo con FFmpeg demuxer...")

    concat_txt = os.path.join(OUT_DIR, "agents_concat_list.txt")
    with open(concat_txt, "w") as f:
        for i in range(1, NUM_AGENTS + 1):
            p = os.path.join(OUT_DIR, f"agent_chunk_{i:02d}.mp4")
            f.write(f"file '{p}'\n")

    concat_video = os.path.join(OUT_DIR, "sf_full_video_stream.mp4")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt, "-c:v", "copy", "-an", concat_video
    ]
    subprocess.run(concat_cmd, check=True)

    print("\n🎧 Muxeando con pista máster vocal y banda sonora de Conde Cero...")
    mux_cmd = [
        "ffmpeg", "-y", "-i", concat_video, "-i", AUDIO_MASTER,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
        "-shortest", FINAL_VIDEO_PATH
    ]
    subprocess.run(mux_cmd, check=True)

    total_time = time.time() - t_start
    final_sz = os.path.getsize(FINAL_VIDEO_PATH) / (1024 * 1024)
    print(f"\n🏆 ¡RENDERIZADO SOTA DE COMBATE FINALIZADO!")
    print(f"⏱️ Tiempo total: {total_time:.1f}s ({total_time/60:.2f} min)")
    print(f"📍 Archivo final: {FINAL_VIDEO_PATH}")
    print(f"💾 Tamaño: {final_sz:.2f} MB")

    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size,bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1", FINAL_VIDEO_PATH
    ], capture_output=True, text=True)
    print("ffprobe datos:", probe.stdout.strip())

if __name__ == "__main__":
    main()
