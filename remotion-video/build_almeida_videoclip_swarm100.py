#!/usr/bin/env python3
"""
SHARUR-3600: 100-SWARM PARALLEL RENDER PIPELINE
================================================
Videoclip: «Almeida & Teresa Urquijo - Chotis Club Remix (Sin Letras)»
Audio: poc_euclidean_microtonal_club_master.wav (Build-Up 128 + Falso Drop + House 4/4)
Video Source: almeida_chotis_raw.mp4 (1920x1080 @ 25fps)
Rendering Engine: 100-Agent Concurrent Chunk Swarm via Apple Silicon VideoToolbox
"""

import os
import sys
import time
import math
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

CWD = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video"
VIDEO_SRC = os.path.join(CWD, "public/almeida_chotis_raw.mp4")
AUDIO_SRC = os.path.join(CWD, "public/almeida_videoclip_audio.wav")
CHUNK_DIR = "/tmp/almeida_swarm_100_chunks"
OUT_VIDEO = os.path.join(CWD, "out/almeida_chotis_videoclip_master.mp4")

os.makedirs(CHUNK_DIR, exist_ok=True)
os.makedirs(os.path.join(CWD, "out"), exist_ok=True)

# Duración total: 94.64 s
TOTAL_DURATION = 94.64
NUM_SWARM_AGENTS = 100
CHUNK_DURATION = TOTAL_DURATION / NUM_SWARM_AGENTS  # ~0.9464 s por agente

print("=" * 80)
print(f" SHARUR-3600: DESPLEGANDO ENJAMBRE DE {NUM_SWARM_AGENTS} AGENTES DE RENDER")
print("=" * 80)
print(f"[*] Vídeo Origen: {VIDEO_SRC}")
print(f"[*] Audio Master: {AUDIO_SRC}")
print(f"[*] Segmentos del Enjambre: {NUM_SWARM_AGENTS} chunks de {CHUNK_DURATION:.3f} s cada uno")

# ------------------------------------------------------------------------------
# DEFINICIÓN DE TRANSFORMACIONES PSICOACÚSTICAS (SIN LETRAS)
# ------------------------------------------------------------------------------
# 128 BPM -> Beat dur = 60 / 128 = 0.46875 s
BEAT_DUR = 60.0 / 128.0

def get_chunk_filter(chunk_idx, start_t, end_t):
    """
    Construye el filtergraph de FFmpeg según la fase del tema:
    - 00:00 - 00:59 (Chunks 0-62): Build-up de 128 beats (zoom progresivo, color vintage)
    - 00:59 - 01:03.5 (Chunks 63-67): EL FALSO DROP (cámara lenta 0.25x, blanco y negro dramático)
    - 01:03.5 - 01:34.6 (Chunks 68-99): DROP REAL & CLÍMAX HOUSE (zoom-punch 4/4, saturación viva, stutter)
    """
    filters = []
    mid_t = (start_t + end_t) * 0.5
    
    if mid_t < 59.0:
        # FASE 1: BUILD-UP DE 128 BEATS
        # Zoom sutil creciente + pulso suave en cada compás
        prog = mid_t / 59.0
        scale_val = 1.0 + 0.12 * prog + 0.03 * math.sin(mid_t * (2.0 * math.pi / BEAT_DUR))
        filters.append(f"scale=iw*{scale_val:.3f}:ih*{scale_val:.3f}")
        filters.append("crop=1920:1080")
        # Color analógico cinematográfico suave
        filters.append(f"eq=contrast={1.05 + 0.1*prog:.2f}:saturation={1.1 + 0.15*prog:.2f}:gamma=0.98")
        
    elif 59.0 <= mid_t < 63.5:
        # FASE 2: EL FALSO DROP (Tensión absoluta / Silencio en pista)
        # Zoom directo a Almeida + desaturación / alto contraste cinematográfico
        filters.append("scale=iw*1.28:ih*1.28")
        filters.append("crop=1920:1080")
        # Blanco y negro dramático y contraste cinematográfico
        filters.append("eq=saturation=0.15:contrast=1.35:gamma=0.92")
        
    else:
        # FASE 3: DROP REAL EN RE MENOR & HOUSE 4/4 (Estallido de club)
        # Punch percusivo en cada beat de bombo (128 BPM)
        beat_phase = (mid_t % BEAT_DUR) / BEAT_DUR
        punch = math.exp(-beat_phase * 5.0)  # Caída balística de transitorio
        zoom_punch = 1.0 + 0.08 * punch
        
        filters.append(f"scale=iw*{zoom_punch:.3f}:ih*{zoom_punch:.3f}")
        filters.append("crop=1920:1080")
        
        # Color dinámico de club (saturación viva + contraste agresivo)
        sat = 1.25 + 0.20 * punch
        contrast = 1.15 + 0.15 * punch
        filters.append(f"eq=saturation={sat:.2f}:contrast={contrast:.2f}:gamma=1.02")
        
        # Efecto estroboscópico sutil en claps (cada 2 beats)
        if (int(mid_t / BEAT_DUR) % 2 == 1) and punch > 0.6:
            filters.append("curves=lighter")
            
    # Viñeteado cinematográfico permanente
    filters.append("vignette=PI/5")
    return ",".join(filters)

# ------------------------------------------------------------------------------
# RENDERIZADO CONCURRENTE DEL ENJAMBRE (100 WORKERS)
# ------------------------------------------------------------------------------

def render_swarm_chunk(agent_idx):
    start_t = agent_idx * CHUNK_DURATION
    end_t = min(TOTAL_DURATION, (agent_idx + 1) * CHUNK_DURATION)
    dur = end_t - start_t
    out_chunk = os.path.join(CHUNK_DIR, f"chunk_{agent_idx:03d}.mp4")
    
    # Filtro específico
    vf_chain = get_chunk_filter(agent_idx, start_t, end_t)
    
    # Renderizado acelerado por hardware con h264_videotoolbox en Apple Silicon
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_t:.4f}",
        "-t", f"{dur:.4f}",
        "-i", VIDEO_SRC,
        "-vf", vf_chain,
        "-c:v", "h264_videotoolbox",
        "-b:v", "14M",
        "-an",
        out_chunk
    ]
    
    t0 = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    dt = time.perf_counter() - t0
    
    if res.returncode != 0:
        return agent_idx, False, res.stderr[-200:], dt
    return agent_idx, True, out_chunk, dt

def main():
    t_start = time.perf_counter()
    # Usar 8 workers simultáneos en M3 Pro
    max_workers = 8
    print(f"[*] Lanzando {NUM_SWARM_AGENTS} agentes a través de {max_workers} núcleos concurrentes (Apple Silicon M3 Pro)...")
    
    completed = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(render_swarm_chunk, i): i for i in range(NUM_SWARM_AGENTS)}
        for future in as_completed(futures):
            idx, success, info, dt = future.result()
            if not success:
                print(f"[!] Agente SHARUR_{idx:03d} falló: {info}")
                sys.exit(1)
            completed += 1
            if completed % 20 == 0 or completed == NUM_SWARM_AGENTS:
                print(f"  • Progreso Enjambre: [{completed:03d}/{NUM_SWARM_AGENTS}] chunks completados (último en {dt:.2f} s)")
                
    swarm_time = time.perf_counter() - t_start
    print(f"\n[+] Enjambre de 100 agentes completado en {swarm_time:.2f} s ({TOTAL_DURATION / swarm_time:.1f}x tiempo real)!")

    # --------------------------------------------------------------------------
    # CONCATENACIÓN ATÓMICA Y MUXING DE AUDIO MASTER
    # --------------------------------------------------------------------------
    print("[*] Concatenando los 100 chunks y ensamblando el audio master...")
    concat_list_file = os.path.join(CHUNK_DIR, "chunks_concat.txt")
    with open(concat_list_file, "w") as f:
        for i in range(NUM_SWARM_AGENTS):
            chunk_file = os.path.join(CHUNK_DIR, f"chunk_{i:03d}.mp4")
            f.write(f"file '{chunk_file}'\n")
            
    concat_video_only = os.path.join(CHUNK_DIR, "video_stream_combined.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        concat_video_only
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Mux final con el audio master de 48 kHz
    print("[*] Muxing final con almeida_videoclip_audio.wav...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", concat_video_only,
        "-i", AUDIO_SRC,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        OUT_VIDEO
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    final_sz_mb = os.path.getsize(OUT_VIDEO) / (1024 * 1024)
    print("=" * 80)
    print(f" VIDEOCLIP MASTER COMPLETADO: {OUT_VIDEO}")
    print(f" Tamaño: {final_sz_mb:.2f} MB | Duración: {TOTAL_DURATION} s | 1080p @ 25fps")
    print(f" Tiempo Total de Producción: {time.perf_counter() - t_start:.2f} s")
    print("=" * 80)

if __name__ == "__main__":
    main()
