#!/usr/bin/env python3
"""
SHARUR-3600: ENJAMBRE DE 100 AGENTES - TRILOGÍA DEFINITIVA DE ALMEIDA
====================================================================
Videoclip: «Almeida & Urquijo: The Club Trilogy (Sin Letras)»
Track: poc_euclidean_microtonal_club_master.wav (128 BPM, Build-up 128 -> Falso Drop -> Real Drop Dm House)
Metraje:
  1. El Chotis Nupcial (Boda) -> almeida_chotis_raw.mp4
  2. El Pelotazo de Rugby a Fotógrafo -> almeida_rugby_raw.mp4
  3. El Vuelo al Vacío en Cama Elástica -> almeida_cama_elastica_raw.mp4
Motor: 100 agentes concurrentes de render acelerado en Apple Silicon VideoToolbox
"""

import os
import sys
import time
import math
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

CWD = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video"
VIDEO_CHOTIS = os.path.join(CWD, "public/almeida_chotis_raw.mp4")
VIDEO_RUGBY = os.path.join(CWD, "public/almeida_rugby_raw.mp4")
VIDEO_TRAMP = os.path.join(CWD, "public/almeida_cama_elastica_raw.mp4")
AUDIO_SRC = os.path.join(CWD, "public/almeida_videoclip_audio.wav")

CHUNK_DIR = "/tmp/almeida_trilogy_100_chunks"
OUT_VIDEO = os.path.join(CWD, "out/almeida_trilogia_videoclip_master.mp4")

os.makedirs(CHUNK_DIR, exist_ok=True)
os.makedirs(os.path.join(CWD, "out"), exist_ok=True)

TOTAL_DURATION = 94.64
NUM_SWARM_AGENTS = 100
CHUNK_DURATION = TOTAL_DURATION / NUM_SWARM_AGENTS  # 0.9464 s por chunk

BEAT_DUR = 60.0 / 128.0  # 0.46875 s por beat

def get_chunk_spec(chunk_idx, start_t, end_t):
    """
    Determina la fuente de vídeo, el timestamp de origen y la cadena de filtros
    para cada uno de los 100 agentes del enjambre.
    """
    mid_t = (start_t + end_t) * 0.5
    dur = end_t - start_t
    filters = []

    # --------------------------------------------------------------------------
    # FASE 1: BUILD-UP INICIAL - EL CHOTIS NUPCIAL (00:00 - 00:29.34)
    # --------------------------------------------------------------------------
    if mid_t < 29.34:
        src_video = VIDEO_CHOTIS
        src_seek = 3.0 + mid_t * 0.85
        
        prog = mid_t / 29.34
        scale_val = 1.0 + 0.12 * prog + 0.02 * math.sin(mid_t * (2.0 * math.pi / BEAT_DUR))
        filters.append(f"scale=iw*{scale_val:.3f}:ih*{scale_val:.3f}")
        filters.append("crop=1920:1080")
        filters.append(f"eq=contrast={1.05 + 0.10*prog:.2f}:saturation={1.10 + 0.15*prog:.2f}:gamma=0.98")

    # --------------------------------------------------------------------------
    # FASE 2: BUILD-UP DE TENSIÓN - RUGBY & CHOTIS (00:29.34 - 00:59.00)
    # --------------------------------------------------------------------------
    elif 29.34 <= mid_t < 59.00:
        prog = (mid_t - 29.34) / (59.00 - 29.34)
        
        if mid_t < 54.00:
            # Alternancia rítmica cada 4 chunks (~3.78 s)
            pattern_idx = int((mid_t - 29.34) / (CHUNK_DURATION * 4)) % 4
            if pattern_idx == 0:
                # Rugby: Almeida colocando el balón
                src_video = VIDEO_RUGBY
                src_seek = 22.0 + (mid_t - 29.34) * 0.4
            elif pattern_idx == 1:
                # Chotis: Giro de pareja
                src_video = VIDEO_CHOTIS
                src_seek = 25.0 + (mid_t - 33.12) * 0.5
            elif pattern_idx == 2:
                # Rugby: Fotógrafos apuntando
                src_video = VIDEO_RUGBY
                src_seek = 26.5 + (mid_t - 36.90) * 0.3
            else:
                # Chotis: Sonrisa nupcial
                src_video = VIDEO_CHOTIS
                src_seek = 35.0 + (mid_t - 40.70) * 0.5
        else:
            # Clímax del redoble de 128 beats (54.0 - 59.0 s): Almeida toma carrerilla
            src_video = VIDEO_RUGBY
            src_seek = 28.0 + (mid_t - 54.00) * 0.4
            
        # Filtros de tensión creciente
        beat_pulse = 0.04 * math.sin(mid_t * (2.0 * math.pi / BEAT_DUR))
        scale_val = 1.05 + 0.15 * prog + beat_pulse
        filters.append(f"scale=iw*{scale_val:.3f}:ih*{scale_val:.3f}")
        filters.append("crop=1920:1080")
        filters.append(f"eq=contrast={1.12 + 0.15*prog:.2f}:saturation={1.15 + 0.20*prog:.2f}:gamma=0.96")

    # --------------------------------------------------------------------------
    # FASE 3: EL FALSO DROP - EL VUELO EN CAMA ELÁSTICA (00:59.00 - 01:03.50)
    # --------------------------------------------------------------------------
    elif 59.00 <= mid_t < 63.50:
        src_video = VIDEO_TRAMP
        # Exacto vuelo horizontal de Almeida en el aire
        src_seek = 40.8 + (mid_t - 59.00) * 0.35
        
        # Blanco y negro dramático + zoom hacia la caída al vacío
        filters.append("scale=iw*1.28:ih*1.28")
        filters.append("crop=1920:1080")
        filters.append("eq=saturation=0.0:contrast=1.45:gamma=0.90")

    # --------------------------------------------------------------------------
    # FASE 4: EL DROP REAL EN RE MENOR & HOUSE 4/4 (01:03.50 - 01:34.64)
    # --------------------------------------------------------------------------
    else:
        mid_t - 63.50
        
        if chunk_idx == 68:
            # ¡EL EXACTO PRIMER BOMBO DEL DROP REAL! -> EL PELOTAZO IMPACTA AL FOTÓGRAFO
            src_video = VIDEO_RUGBY
            src_seek = 30.5
            filters.append("scale=iw*1.22:ih*1.22")
            filters.append("crop=1920:1080")
            filters.append("curves=lighter")  # Flash estroboscópico blanco
            filters.append("eq=saturation=1.40:contrast=1.35:gamma=1.02")
        elif chunk_idx == 69:
            # BEAT 2 -> CAÍDA EN LA ESPUMA CON PIERNAS AL AIRE
            src_video = VIDEO_TRAMP
            src_seek = 42.6
            filters.append("scale=iw*1.15:ih*1.15")
            filters.append("crop=1920:1080")
            filters.append("eq=saturation=1.35:contrast=1.25:gamma=1.00")
        else:
            # CLÍMAX HOUSE: MONTAJE POLIRÍTMICO A 128 BPM
            # Cada 2 chunks (~1.89 s = 4 beats) conmuta de plano
            scene_cycle = (chunk_idx // 2) % 4
            if scene_cycle == 0:
                # Chotis nupcial en giros rápidos
                src_video = VIDEO_CHOTIS
                src_seek = 10.0 + (chunk_idx * 1.3) % 25.0
            elif scene_cycle == 1:
                # Pelotazo multi-ángulo al fotógrafo
                src_video = VIDEO_RUGBY
                src_seek = 30.2 + (chunk_idx * 0.3) % 2.0
            elif scene_cycle == 2:
                # Trampolín: aterrizaje y pies volando en espuma
                src_video = VIDEO_TRAMP
                src_seek = 41.8 + (chunk_idx * 0.4) % 2.5
            else:
                # Reacción y risas del público / novios
                src_video = VIDEO_RUGBY
                src_seek = 32.5 + (chunk_idx * 0.5) % 4.0

            # Zoom-punch balístico en cada kick (128 BPM)
            beat_phase = (mid_t % BEAT_DUR) / BEAT_DUR
            punch = math.exp(-beat_phase * 6.0)
            zoom_punch = 1.0 + 0.09 * punch
            filters.append(f"scale=iw*{zoom_punch:.3f}:ih*{zoom_punch:.3f}")
            filters.append("crop=1920:1080")
            
            # Saturación y contraste de club nocturno
            sat = 1.30 + 0.20 * punch
            contrast = 1.18 + 0.15 * punch
            filters.append(f"eq=saturation={sat:.2f}:contrast={contrast:.2f}:gamma=1.02")
            
            # Estrobo en claps (cada 2 beats)
            if (int(mid_t / BEAT_DUR) % 2 == 1) and punch > 0.5:
                filters.append("curves=lighter")

    # Viñeteado cinematográfico unificador
    filters.append("vignette=PI/5")
    
    return src_video, src_seek, dur, ",".join(filters)

# ------------------------------------------------------------------------------
# RENDERIZADO CONCURRENTE DEL ENJAMBRE (100 WORKERS)
# ------------------------------------------------------------------------------

def render_swarm_chunk(agent_idx):
    start_t = agent_idx * CHUNK_DURATION
    end_t = min(TOTAL_DURATION, (agent_idx + 1) * CHUNK_DURATION)
    
    src_video, src_seek, dur, vf_chain = get_chunk_spec(agent_idx, start_t, end_t)
    out_chunk = os.path.join(CHUNK_DIR, f"chunk_{agent_idx:03d}.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{src_seek:.4f}",
        "-t", f"{dur:.4f}",
        "-i", src_video,
        "-vf", vf_chain,
        "-r", "25",
        "-pix_fmt", "yuv420p",
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
    max_workers = 8
    print("=" * 80)
    print(f" SHARUR-3600: DESPLEGANDO ENJAMBRE DE {NUM_SWARM_AGENTS} AGENTES DE RENDER")
    print(" OBJETIVO: TRILOGÍA DE ALMEIDA (CHOTIS + RUGBY + CAMA ELÁSTICA)")
    print(f" Aceleración: Apple Silicon VideoToolbox ({max_workers} procesos en paralelo)")
    print("=" * 80)
    
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
    print(f"\n[+] Enjambre de {NUM_SWARM_AGENTS} agentes completado en {swarm_time:.2f} s ({TOTAL_DURATION / swarm_time:.1f}x tiempo real)!")

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
