#!/usr/bin/env python3
"""
FL Studio Playlist Song Arranger & Binary Compiler (v14.0 Continuum)
Compiles complete multi-section song arrangements (Intro, Verse, Drop, Breakdown, Climax, Outro)
with pattern placement blocks, track assignments, and binary FLP encoding without GUI interaction.

Structural Form (64 Bars @ 112 BPM):
- Section 1 (Bars 1-8, Ticks 0-3072): Ambient Drone & 40Hz Gamma Entrainment
- Section 2 (Bars 9-24, Ticks 3072-9216): Bulerias Palmas & Acid Bass Build
- Section 3 (Bars 25-40, Ticks 9216-15360): Full 4-on-Floor Cyber Drop
- Section 4 (Bars 41-48, Ticks 15360-18432): Microtonal Hijaz Spanish Guitar Breakdown
- Section 5 (Bars 49-64, Ticks 18432-24576): Peak Exergy Climax & Resonance Release
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from scripts.fl_flp_project_builder import FLPProjectBuilder

logger = logging.getLogger("FLStudio-PlaylistArranger")

DEFAULT_SONG_SECTIONS = [
    {
        "section": "Intro Ambient & Gamma Entrainment",
        "bars_start": 1,
        "bars_end": 8,
        "duration_bars": 8,
        "active_channels": ["Phrygian Lead (Droning)", "Neuroacoustic Gamma 40Hz"],
        "energy_level": 0.35,
        "description": "Atmospheric drone in D with 40 Hz Gamma neuroacoustic binding bed."
    },
    {
        "section": "Bulerías Compás & Rolling Acid Build",
        "bars_start": 9,
        "bars_end": 24,
        "duration_bars": 16,
        "active_channels": ["Rolling Cyber Bass", "Bulerias Palmas 12-Beat", "Cyber Snare"],
        "energy_level": 0.65,
        "description": "12-beat Bulerías accents (3, 6, 8, 10, 12) with modulating cutoff 303 acid line."
    },
    {
        "section": "Full Cyber Drop",
        "bars_start": 25,
        "bars_end": 40,
        "duration_bars": 16,
        "active_channels": ["Kick (4-on-the-Floor)", "Cyber Snare", "Rolling Cyber Bass", "Phrygian Lead", "Bulerias Palmas"],
        "energy_level": 0.95,
        "description": "Maximum driving 4-on-the-floor kick with full sidechained rolling bass."
    },
    {
        "section": "Microtonal Hijaz Breakdown",
        "bars_start": 41,
        "bars_end": 48,
        "duration_bars": 8,
        "active_channels": ["Phrygian Lead (Microtonal)", "Neuroacoustic Theta 6Hz"],
        "energy_level": 0.45,
        "description": "Spanish Phrygian Hijaz modal improvisation with 6 Hz Theta meditation underlay."
    },
    {
        "section": "Peak Climax & High-Exergy Outro",
        "bars_start": 49,
        "bars_end": 64,
        "duration_bars": 16,
        "active_channels": ["Kick (4-on-the-Floor)", "Cyber Snare", "Rolling Cyber Bass", "Phrygian Lead", "Bulerias Palmas", "Neuroacoustic Gamma 40Hz"],
        "energy_level": 1.0,
        "description": "All stems firing in phase alignment; final high-exergy release."
    }
]


def compile_playlist_song_arrangement(
    sections: Optional[List[Dict[str, Any]]] = None,
    bpm: float = 112.0,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compiles a structured 64-bar song arrangement into both a native .flp binary project
    and a structured timeline arrangement manifest.
    """
    if sections is None:
        sections = DEFAULT_SONG_SECTIONS

    total_bars = max(s["bars_end"] for s in sections)
    ticks_per_bar = 96 * 4  # 384 ticks per bar (4/4 time, 96 PPQ)
    total_ticks = total_bars * ticks_per_bar
    duration_sec = round((total_bars * 4.0 * 60.0) / bpm, 2)

    # Output directory setup
    if not output_path:
        out_dir = Path.home() / "Music" / "FL Studio Bounces" / "Projects"
        out_dir.mkdir(parents=True, exist_ok=True)
        flp_file = out_dir / "Dark_Cyber_Flamenco_Arranged_Song_v14.flp"
        json_manifest = out_dir / "Dark_Cyber_Flamenco_Arrangement_Manifest_v14.json"
    else:
        flp_file = Path(output_path).expanduser().resolve()
        flp_file.parent.mkdir(parents=True, exist_ok=True)
        json_manifest = flp_file.with_suffix(".json")

    # Build binary FLP
    builder = FLPProjectBuilder(title=f"Dark Cyber Flamenco - Full Song Arrangement ({total_bars} Bars)", bpm=bpm, ppq=96)

    # Channel Definitions
    ch_kick = builder.add_channel("01_Kick_4onFloor")
    ch_snare = builder.add_channel("02_Cyber_Snare")
    ch_bass = builder.add_channel("03_Rolling_Cyber_Bass")
    ch_lead = builder.add_channel("04_Phrygian_Lead")
    ch_palmas = builder.add_channel("05_Bulerias_Palmas")

    # Populate Notes across Timeline based on Active Channels
    for sec in sections:
        start_tick = (sec["bars_start"] - 1) * ticks_per_bar
        end_tick = sec["bars_end"] * ticks_per_bar
        sec_bars = sec["duration_bars"]
        active = sec["active_channels"]

        # If Kick is active
        if any("Kick" in c for c in active):
            for b in range(sec_bars):
                bar_base = start_tick + b * ticks_per_bar
                for beat in range(4):
                    builder.add_note(pos_ticks=bar_base + beat * 96, pitch=36, duration_ticks=48, velocity=115, channel_index=ch_kick)

        # If Snare is active
        if any("Snare" in c for c in active):
            for b in range(sec_bars):
                bar_base = start_tick + b * ticks_per_bar
                # Snare on beats 2 and 4
                builder.add_note(pos_ticks=bar_base + 96, pitch=38, duration_ticks=48, velocity=105, channel_index=ch_snare)
                builder.add_note(pos_ticks=bar_base + 288, pitch=38, duration_ticks=48, velocity=108, channel_index=ch_snare)

        # If Bass is active
        if any("Bass" in c for c in active):
            # 16th-note rolling bass line in D
            bass_pitches = [38, 38, 41, 38, 39, 38, 38, 41]  # D2, D2, F2, D2, Eb2, D2, D2, F2
            for b in range(sec_bars):
                bar_base = start_tick + b * ticks_per_bar
                for s in range(16):
                    pitch = bass_pitches[s % len(bass_pitches)]
                    builder.add_note(pos_ticks=bar_base + s * 24, pitch=pitch, duration_ticks=20, velocity=95, channel_index=ch_bass)

        # If Palmas / Compás is active
        if any("Palmas" in c for c in active):
            # 12-beat Bulerías accents: 3, 6, 8, 10, 12
            accents = {2: 120, 5: 118, 7: 122, 9: 115, 11: 125}
            for b in range(0, sec_bars, 3):  # Each Bulerías cycle is 3 bars in 4/4 (12 beats)
                cycle_base = start_tick + b * ticks_per_bar
                for beat in range(12):
                    vel = accents.get(beat, 75)
                    builder.add_note(pos_ticks=cycle_base + beat * 96, pitch=60, duration_ticks=36, velocity=vel, channel_index=ch_palmas)

        # If Lead is active
        if any("Lead" in c for c in active):
            lead_melody = [62, 63, 66, 67, 66, 63, 62]  # D Phrygian Dominant: D4, Eb4, F#4, G4, F#4, Eb4, D4
            for b in range(sec_bars):
                bar_base = start_tick + b * ticks_per_bar
                p = lead_melody[b % len(lead_melody)]
                builder.add_note(pos_ticks=bar_base, pitch=p, duration_ticks=192, velocity=100, channel_index=ch_lead)

    # Compile FLP
    raw_flp = builder.build_binary()
    with open(flp_file, "wb") as f:
        f.write(raw_flp)

    # Arrangement Manifest
    manifest = {
        "title": f"Dark Cyber Flamenco - Master Song Arrangement ({total_bars} Bars)",
        "total_bars": total_bars,
        "bpm": bpm,
        "duration_sec": duration_sec,
        "ppq": 96,
        "total_ticks": total_ticks,
        "total_notes": len(builder.notes),
        "channels": [
            {"id": ch_kick, "name": "01_Kick_4onFloor", "color_hex": "#FF3366"},
            {"id": ch_snare, "name": "02_Cyber_Snare", "color_hex": "#00F0FF"},
            {"id": ch_bass, "name": "03_Rolling_Cyber_Bass", "color_hex": "#7928CA"},
            {"id": ch_lead, "name": "04_Phrygian_Lead", "color_hex": "#FFB800"},
            {"id": ch_palmas, "name": "05_Bulerias_Palmas", "color_hex": "#00FF66"}
        ],
        "timeline_sections": sections,
        "output_flp": str(flp_file),
        "file_size_bytes": len(raw_flp)
    }

    with open(json_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "status": "SUCCESS",
        "total_bars": total_bars,
        "duration_sec": duration_sec,
        "bpm": bpm,
        "total_notes": len(builder.notes),
        "sections_count": len(sections),
        "flp_project_file": str(flp_file),
        "json_manifest_file": str(json_manifest),
        "file_size_bytes": len(raw_flp)
    }


if __name__ == "__main__":
    res = compile_playlist_song_arrangement()
    print("Playlist Arranger output:", res)
