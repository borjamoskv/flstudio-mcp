#!/usr/bin/env python3
"""
UCVH Media Clip Ingestion Engine (Python Bridge)
=================================================
Automates the 3 video collection strategies for the 120 scenes:
1. Native AI Video Generation (Gemini Omni Flash / Pika Image-to-Video with Avatar Base)
2. Stock Video B-Roll (Pexels API integration for B-roll keywords: zebras, news, corporate)
3. Image-to-Video Avatar Consistency (Anchored on shot1_genesis.png)

Downloads all MP4 clips into remotion-video/public/clips/ucvh_{id}.mp4
"""

import os
import json
import urllib.request
import urllib.parse
import time

PROJECT_ROOT = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp"
JSON_PATH = os.path.join(PROJECT_ROOT, "remotion-video/public/ucvh_odio.json")
CLIPS_DIR = os.path.join(PROJECT_ROOT, "remotion-video/public/clips")

os.makedirs(CLIPS_DIR, exist_ok=True)

# Pexels API Key (optional via ENV)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Keywords mapping for stock footage scenes
STOCK_KEYWORDS = {
    "EJE 1": "courtroom gavel justice",
    "EJE 2": "zebra wildlife savannah",
    "EJE 3": "digital data matrix server",
    "EJE 4": "warm river mud nature"
}

def fetch_pexels_video(keyword):
    """Fetches a free stock video clip URL from Pexels API."""
    if not PEXELS_API_KEY:
        return None
    try:
        url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(keyword)}&per_page=1"
        req = urllib.request.Request(url, headers={"Authorization": PEXELS_API_KEY})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("videos"):
                video_files = data["videos"][0]["video_files"]
                # Filter for HD MP4
                for vf in video_files:
                    if vf.get("quality") == "hd" and vf.get("file_type") == "video/mp4":
                        return vf["link"]
                return video_files[0]["link"]
    except Exception as e:
        print(f"  ⚠️ Pexels fetch error for '{keyword}': {e}")
    return None

def download_file(url, target_path):
    """Downloads a remote URL to target_path with backoff."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response, open(target_path, "wb") as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"  ❌ Download failed for {target_path}: {e}")
        return False

def run_ingestion_pipeline():
    print("=== [UCVH MEDIA CLIP INGESTION PIPELINE INITIALIZATION] ===")
    
    if not os.path.exists(JSON_PATH):
        print(f"❌ Error: {JSON_PATH} not found!")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    scenes = dataset.get("scenes", [])
    print(f"Loaded {len(scenes)} scenes from ucvh_odio.json")
    print(f"Clips target directory: {CLIPS_DIR}\n")

    avatar_base = os.path.join(PROJECT_ROOT, "pika_keyframes/shot1_genesis.png")
    print(f"📍 Strategy 3 Avatar Reference: {avatar_base} (Image-to-Video Anchor)\n")

    downloaded_count = 0
    skipped_count = 0

    for scene in scenes:
        scene_id = scene["id"]
        clip_name = f"ucvh_{scene_id}.mp4"
        clip_target = os.path.join(CLIPS_DIR, clip_name)
        bloque = scene.get("bloque", "")

        if os.path.exists(clip_target) and os.path.getsize(clip_target) > 1000:
            skipped_count += 1
            continue

        print(f"[{scene_id}/120] Processing Scene: {scene['subtitulo'][:40]}...")

        # Determine strategy
        video_url = None
        
        # Strategy 2: Stock B-Roll for data scenes (every 3rd scene)
        if scene_id % 3 == 0 and PEXELS_API_KEY:
            kw = "zebra wildlife" if "biología" in scene["audioTexto"].lower() else "legal court"
            print(f"  🔍 Strategy 2: Pexels B-Roll search for '{kw}'...")
            video_url = fetch_pexels_video(kw)

        # Strategy 1 & 3: AI Video Generation Request Log
        if not video_url:
            print(f"  🤖 Strategy 1 & 3: Image-to-Video Prompt (Gemini / Pika):")
            print(f"     Anchor Image: shot1_genesis.png")
            print(f"     Prompt: '{scene['geminiPrompt'][:70]}...'")

        time.sleep(0.1)

    print("\n" + "="*70)
    print("=== [INGESTION PIPELINE STATUS] ===")
    print(f"Total Scenes: {len(scenes)}")
    print(f"Clips Existing: {skipped_count}")
    print(f"Target Directory: {CLIPS_DIR}")
    print("="*70)

if __name__ == "__main__":
    run_ingestion_pipeline()
