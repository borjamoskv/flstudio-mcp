#!/usr/bin/env python3
"""
Parallel Multi-Worker Remotion Renderer for 20-Minute Delirio Podcast (36,000 Frames)
"""
import os
import shutil
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

CWD = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video"
OUT_DIR = "/tmp/delirio_chunks"
FINAL_MUSIC_PATH = "/Users/borjafernandezangulo/Music/Podcast_JARANA_CAST_20_MINUTOS_DELIRIO.mp4"
AUDIO_MASTER = os.path.join(CWD, "public/podcast_delirio_master.wav")

os.makedirs(OUT_DIR, exist_ok=True)

# Copy pre-rendered chunk 0 if exists
if os.path.exists("/tmp/test_chunk_0.mp4") and not os.path.exists(os.path.join(OUT_DIR, "chunk_0.mp4")):
    shutil.copy("/tmp/test_chunk_0.mp4", os.path.join(OUT_DIR, "chunk_0.mp4"))
    print("Reused pre-rendered chunk_0.mp4")

# Total 12 chunks of 3,000 frames each = 36,000 frames (20 minutes exact @ 30fps)
TOTAL_FRAMES = 36000
CHUNK_SIZE = 3000
CHUNKS = []
for i in range(12):
    start_f = i * CHUNK_SIZE
    end_f = (i + 1) * CHUNK_SIZE - 1
    CHUNKS.append((i, start_f, end_f))

def render_chunk(chunk_info):
    idx, start_f, end_f = chunk_info
    out_file = os.path.join(OUT_DIR, f"chunk_{idx}.mp4")
    
    # Check if already rendered and valid (> 10MB)
    if os.path.exists(out_file) and os.path.getsize(out_file) > 10 * 1024 * 1024:
        print(f"⏩ [CHUNK {idx:02d}/12] Already rendered ({os.path.getsize(out_file)/(1024*1024):.1f} MB). Skipping.")
        return idx, out_file, 0.0

    print(f"🎬 [CHUNK {idx:02d}/12] Rendering frames {start_f}..{end_f}...")
    t0 = time.time()
    cmd = [
        "npx", "remotion", "render", "src/index.ts", "PodcastSouthParkDelirio20Min",
        out_file, f"--frames={start_f}-{end_f}", "--concurrency=4", "--gl=angle"
    ]
    res = subprocess.run(cmd, cwd=CWD, capture_output=True, text=True)
    dt = time.time() - t0
    
    if res.returncode != 0:
        print(f"❌ [CHUNK {idx:02d}/12] FAILED: {res.stderr[-400:]}")
        raise RuntimeError(f"Chunk {idx} failed")
    
    sz = os.path.getsize(out_file) / (1024 * 1024)
    print(f"✅ [CHUNK {idx:02d}/12] Completed in {dt:.1f}s ({sz:.1f} MB)")
    return idx, out_file, dt

def main():
    print(f"🚀 Starting parallel render of 36,000 frames (20 minutes) across 12 chunks...")
    t_start = time.time()
    
    # 3 concurrent workers in parallel on Apple Silicon M3 Pro
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(render_chunk, c): c for c in CHUNKS}
        for future in as_completed(futures):
            idx, out_file, dt = future.result()
    
    print("\n📦 All 12 chunks rendered successfully! Starting FFmpeg concatenation...")
    
    # Create concat list
    concat_txt = os.path.join(OUT_DIR, "chunks_list.txt")
    with open(concat_txt, "w") as f:
        for i in range(12):
            chunk_p = os.path.join(OUT_DIR, f"chunk_{i}.mp4")
            f.write(f"file '{chunk_p}'\n")
    
    concat_video = os.path.join(OUT_DIR, "delirio_full_video_stream.mp4")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt, "-c:v", "copy", "-an", concat_video
    ]
    print("Running:", " ".join(concat_cmd))
    subprocess.run(concat_cmd, check=True)
    
    print("\n🎧 Muxing video stream with Broadcast-Mastered 20-minute audio track...")
    mux_cmd = [
        "ffmpeg", "-y", "-i", concat_video, "-i", AUDIO_MASTER,
        "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
        "-shortest", FINAL_MUSIC_PATH
    ]
    print("Running:", " ".join(mux_cmd))
    subprocess.run(mux_cmd, check=True)
    
    total_time = time.time() - t_start
    final_sz = os.path.getsize(FINAL_MUSIC_PATH) / (1024 * 1024)
    print(f"\n🎉 COMPLETED! 20-minute podcast video rendered in {total_time/60:.1f} minutes!")
    print(f"📍 Location: {FINAL_MUSIC_PATH}")
    print(f"📊 Final Size: {final_sz:.1f} MB")
    
    # Verify with ffprobe
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size,bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1", FINAL_MUSIC_PATH
    ], capture_output=True, text=True)
    print("ffprobe info:", probe.stdout.strip())

if __name__ == "__main__":
    main()
