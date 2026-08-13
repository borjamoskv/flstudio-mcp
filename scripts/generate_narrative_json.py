#!/usr/bin/env python3
"""
Narrative JSON Generator for 20-Minute Cyber-Epistemology Video
================================================================
Generates a structured, data-driven narrative JSON for Remotion rendering.
"""

import json
import os

BPM = 118
FPS = 30
BEAT_SEC = 60.0 / BPM  # ~0.50847s
BAR_SEC = BEAT_SEC * 4   # ~2.0339s
LOOP_BARS = 8
LOOP_SEC = BAR_SEC * LOOP_BARS  # ~16.2712s

TARGET_MINUTES = 20
TOTAL_TARGET_SEC = TARGET_MINUTES * 60  # 1200s
NUM_LOOPS = round(TOTAL_TARGET_SEC / LOOP_SEC)  # 74 loops -> ~1204s

ACTS = [
    {
        "name": "ACT I — GENESIS & PENROSE STAIR",
        "description": "Exploración de la estructura armónica Abmaj7 -> Bb9 -> Cm9 -> Fm9 con Rhodes de cristal en ingravidez.",
        "colorToken": "magentaNeon",
        "hex": "#E01882"
    },
    {
        "name": "ACT II — INDUSTRIAL TECHNO IMPACT",
        "description": "Golpe de bombo DSP Maceo Plex (3.8kHz -> 50Hz) y deformación magnética de ferrofluido.",
        "colorToken": "purpleIndustrial",
        "hex": "#5B2C6F"
    },
    {
        "name": "ACT III — XENHARMONIC ASCENSION",
        "description": "Cúpula observatorio retro-futurista con anillos armónicos giran en afinación 24-TET.",
        "colorToken": "cyanDeep",
        "hex": "#00CED1"
    },
    {
        "name": "ACT IV — FALSE DROP & PICARDY SUNBURST",
        "description": "Silencio de transitorios en el compás 7 seguido de modulación brillante Picardy Cmaj9.",
        "colorToken": "goldenPicardy",
        "hex": "#FFB347"
    }
]

def build_20min_json(output_path):
    scenes = []
    
    for i in range(NUM_LOOPS):
        act_info = ACTS[i % len(ACTS)]
        scene = {
            "id": i + 1,
            "loopIndex": i,
            "act": act_info["name"],
            "description": act_info["description"],
            "startSeconds": round(i * LOOP_SEC, 3),
            "durationSeconds": round(LOOP_SEC, 3),
            "startFrame": round(i * LOOP_SEC * FPS),
            "durationFrames": round(LOOP_SEC * FPS),
            "colorToken": act_info["colorToken"],
            "colorHex": act_info["hex"],
            "keyframeImage": f"shot{(i % 4)*2 + 1}_keyframe.png",
            "audioTrack": "Satin_Maceo_AIR_Flow_Master.wav",
            "typography": {
                "title": f"SCENE {i+1:02d} // {act_info['name']}",
                "subtitle": f"Loop {i+1}/{NUM_LOOPS} • 118 BPM 24-TET",
                "font": "Inter"
            }
        }
        scenes.append(scene)

    narrative = {
        "metadata": {
            "title": "Satin x Maceo x AIR: 20-Minute Cyber-Epistemology",
            "bpm": BPM,
            "fps": FPS,
            "width": 1920,
            "height": 1080,
            "loopDurationSeconds": round(LOOP_SEC, 4),
            "totalDurationSeconds": round(NUM_LOOPS * LOOP_SEC, 2),
            "totalFrames": round(NUM_LOOPS * LOOP_SEC * FPS),
            "totalScenes": NUM_LOOPS
        },
        "colorPalette": {
            "obsidianBase": "#0A0A0F",
            "magentaNeon": "#E01882",
            "cyanDeep": "#00CED1",
            "goldenPicardy": "#FFB347",
            "purpleIndustrial": "#5B2C6F"
        },
        "scenes": scenes
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(narrative, f, indent=2)
    return output_path

if __name__ == "__main__":
    out_file = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/narrative_20min.json"
    build_20min_json(out_file)
    print(f"✅ Generated 20-minute Data-Driven Narrative JSON: {out_file}")
