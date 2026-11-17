#!/usr/bin/env python3
"""
FL Studio Playlist Song Arranger & Binary Compiler (v15.0 C5-REAL Continuum)
Compiles complete multi-section song arrangements into native .flp projects + manifests,
upgraded with:
  - Differential rhythmic pocket (+2 ticks laid-back bass, -3 ticks palma/snare pre-snap)
  - Bar 60 Beats 3-4 False Drop / Living Pre-Drop Gap before Final Climax boost
  - Turnaround fills every 8 bars & Bar 64 Living Exit RC velocity decay
  - Per-note FLP 0xE0 expression (pan stereo width, release contour, velocity-coupled mod_x)
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from scripts.bounces_paths import resolve_bounces_dir  # noqa: E402
from scripts.fl_flp_project_builder import FLPProjectBuilder  # noqa: E402

logger = logging.getLogger("FLStudio-PlaylistArranger")

DEFAULT_SONG_SECTIONS = [
    {
        "section": "Intro Ambient & Gamma Entrainment",
        "bars_start": 1,
        "bars_end": 8,
        "duration_bars": 8,
        "active_channels": ["Phrygian Lead (Droning)", "Neuroacoustic Gamma 40Hz"],
        "energy_level": 0.35,
        "description": "Atmospheric drone in D with 40 Hz Gamma neuroacoustic binding bed.",
    },
    {
        "section": "Bulerías Compás & Rolling Acid Build",
        "bars_start": 9,
        "bars_end": 24,
        "duration_bars": 16,
        "active_channels": ["Rolling Cyber Bass", "Bulerias Palmas 12-Beat", "Cyber Snare"],
        "energy_level": 0.65,
        "description": "12-beat Bulerías accents (3, 6, 8, 10, 12) with modulating cutoff 303 acid line.",
    },
    {
        "section": "Full Cyber Drop",
        "bars_start": 25,
        "bars_end": 40,
        "duration_bars": 16,
        "active_channels": ["Kick (4-on-the-Floor)", "Cyber Snare", "Rolling Cyber Bass", "Phrygian Lead", "Bulerias Palmas"],
        "energy_level": 0.95,
        "description": "Maximum driving 4-on-the-floor kick with full sidechained rolling bass.",
    },
    {
        "section": "Microtonal Hijaz Breakdown",
        "bars_start": 41,
        "bars_end": 48,
        "duration_bars": 8,
        "active_channels": ["Phrygian Lead (Microtonal)", "Neuroacoustic Theta 6Hz"],
        "energy_level": 0.45,
        "description": "Spanish Phrygian Hijaz modal improvisation with 6 Hz Theta meditation underlay.",
    },
    {
        "section": "Peak Climax & High-Exergy Outro",
        "bars_start": 49,
        "bars_end": 64,
        "duration_bars": 16,
        "active_channels": ["Kick (4-on-the-Floor)", "Cyber Snare", "Rolling Cyber Bass", "Phrygian Lead", "Bulerias Palmas", "Neuroacoustic Gamma 40Hz"],
        "energy_level": 1.0,
        "description": "All stems firing in phase alignment; Bar 60 False Drop gap & Bar 64 Living Exit.",
    },
]


def compile_playlist_song_arrangement(
    sections: Optional[List[Dict[str, Any]]] = None,
    bpm: float = 112.0,
    output_path: Optional[str] = None,
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

    if not output_path:
        out_dir = resolve_bounces_dir() / "Projects"
        out_dir.mkdir(parents=True, exist_ok=True)
        flp_file = out_dir / "Dark_Cyber_Flamenco_Arranged_Song_v14.flp"
        json_manifest = out_dir / "Dark_Cyber_Flamenco_Arrangement_Manifest_v14.json"
    else:
        flp_file = Path(output_path).expanduser().resolve()
        flp_file.parent.mkdir(parents=True, exist_ok=True)
        json_manifest = flp_file.with_suffix(".json")

    builder = FLPProjectBuilder(title=f"Dark Cyber Flamenco - Full Song Arrangement ({total_bars} Bars)", bpm=bpm, ppq=96)

    ch_kick = builder.add_channel("01_Kick_4onFloor")
    ch_snare = builder.add_channel("02_Cyber_Snare")
    ch_bass = builder.add_channel("03_Rolling_Cyber_Bass")
    ch_lead = builder.add_channel("04_Phrygian_Lead")
    ch_palmas = builder.add_channel("05_Bulerias_Palmas")

    false_drop_bars = {60} if total_bars >= 60 else set()

    for sec in sections:
        start_tick = (sec["bars_start"] - 1) * ticks_per_bar
        sec_bars = sec["duration_bars"]
        active = sec["active_channels"]
        is_final_section = sec["bars_end"] == total_bars

        def _exit_decay(bar_1idx: int) -> float:
            if is_final_section and bar_1idx >= total_bars - 1:
                return 0.62 if bar_1idx == total_bars else 0.80
            return 1.0

        # Kick (0 tick grid anchor, Bar 60 beats 3-4 False Drop vacuum)
        if any("Kick" in c for c in active):
            for b in range(sec_bars):
                abs_bar = sec["bars_start"] + b
                bar_base = start_tick + b * ticks_per_bar
                decay = _exit_decay(abs_bar)
                for beat in range(4):
                    if abs_bar in false_drop_bars and beat >= 2:
                        continue
                    vel = int((122 if beat == 0 else 114) * decay)
                    builder.add_note(
                        pos_ticks=bar_base + beat * 96,
                        pitch=36,
                        duration_ticks=48,
                        velocity=max(40, vel),
                        channel_index=ch_kick,
                        pan=64,
                        release=118,
                    )

        # Cyber Snare (-3 tick pre-snap micro-displacement + 8-bar turnaround fills)
        if any("Snare" in c for c in active):
            for b in range(sec_bars):
                abs_bar = sec["bars_start"] + b
                bar_base = start_tick + b * ticks_per_bar
                decay = _exit_decay(abs_bar)
                is_turnaround = (abs_bar % 8 == 0) and (abs_bar not in false_drop_bars)
                if abs_bar not in false_drop_bars:
                    builder.add_note(pos_ticks=bar_base + 93, pitch=38, duration_ticks=44, velocity=int(105 * decay), channel_index=ch_snare, pan=62, release=124)
                    builder.add_note(pos_ticks=bar_base + 285, pitch=38, duration_ticks=44, velocity=int(110 * decay), channel_index=ch_snare, pan=66, release=124)
                    if is_turnaround:
                        for fill_step in (12, 14, 15):
                            builder.add_note(
                                pos_ticks=bar_base + fill_step * 24 - 2,
                                pitch=40 if fill_step == 15 else 38,
                                duration_ticks=18,
                                velocity=int((82 + (fill_step - 12) * 10) * decay),
                                channel_index=ch_snare,
                                pan=56 + (fill_step - 12) * 8,
                            )
                else:
                    # Single snap on beat 2 leaving beats 3-4 hollow before drop
                    builder.add_note(pos_ticks=bar_base + 93, pitch=38, duration_ticks=44, velocity=108, channel_index=ch_snare, pan=62)

        # Rolling Cyber Bass (+2 tick laid-back pocket & velocity-coupled mod_x)
        if any("Bass" in c for c in active):
            bass_pitches = [38, 38, 41, 38, 39, 38, 38, 41]
            for b in range(sec_bars):
                abs_bar = sec["bars_start"] + b
                bar_base = start_tick + b * ticks_per_bar
                decay = _exit_decay(abs_bar)
                for s in range(16):
                    if abs_bar in false_drop_bars and s >= 8:
                        continue
                    pitch = bass_pitches[s % len(bass_pitches)]
                    pocket = 2 if (s % 4 != 0) else 1
                    vel = int((104 if s % 4 == 2 else 92) * decay)
                    builder.add_note(
                        pos_ticks=bar_base + s * 24 + pocket,
                        pitch=pitch,
                        duration_ticks=20,
                        velocity=max(36, vel),
                        channel_index=ch_bass,
                        pan=64,
                        release=112,
                        mod_x=int(56 + (vel * 0.52)),
                    )

        # Palmas / Compás (Stereo panning + -3 tick pre-snap accents)
        if any("Palmas" in c for c in active):
            accents = {2: 120, 5: 118, 7: 122, 9: 115, 11: 125}
            for b in range(0, sec_bars, 3):
                cycle_base = start_tick + b * ticks_per_bar
                for beat in range(12):
                    abs_bar = sec["bars_start"] + b + (beat // 4)
                    if abs_bar in false_drop_bars and (beat % 4) >= 2:
                        continue
                    vel = int(accents.get(beat, 75) * _exit_decay(abs_bar))
                    pre_snap = -3 if beat in accents else 0
                    pan = 42 if (beat % 2 == 0) else 86
                    builder.add_note(
                        pos_ticks=max(0, cycle_base + beat * 96 + pre_snap),
                        pitch=60,
                        duration_ticks=34,
                        velocity=max(32, vel),
                        channel_index=ch_palmas,
                        pan=pan,
                        release=105,
                    )

        # Phrygian Lead (Dyad strumming +6 ticks + top-note emphasis)
        if any("Lead" in c for c in active):
            lead_melody = [62, 63, 66, 67, 66, 63, 62]
            for b in range(sec_bars):
                abs_bar = sec["bars_start"] + b
                bar_base = start_tick + b * ticks_per_bar
                decay = _exit_decay(abs_bar)
                root_p = lead_melody[b % len(lead_melody)]
                voicing = [root_p - 12, root_p, root_p + 7]
                for v_i, pitch in enumerate(voicing):
                    is_top = v_i == len(voicing) - 1
                    vel = int((84 + (20 if is_top else v_i * 6)) * decay)
                    builder.add_note(
                        pos_ticks=bar_base + v_i * 6,
                        pitch=pitch,
                        duration_ticks=180 if abs_bar not in false_drop_bars else 120,
                        velocity=max(32, vel),
                        channel_index=ch_lead,
                        pan=54 + v_i * 10,
                        release=156,
                    )

    raw_flp = builder.build_binary()
    with open(flp_file, "wb") as f:
        f.write(raw_flp)

    manifest = {
        "title": f"Dark Cyber Flamenco - Master Song Arrangement ({total_bars} Bars)",
        "total_bars": total_bars,
        "bpm": bpm,
        "duration_sec": duration_sec,
        "ppq": 96,
        "total_ticks": total_ticks,
        "total_notes": len(builder.notes),
        "structural_invariants_applied": {
            "false_drop_bar_60": 60 in false_drop_bars,
            "living_exits_rc_decay": True,
            "differential_pocket_ticks": {"kick": 0, "bass": 2, "snare_palmas": -3},
            "per_note_flp_expression": ["pan", "release", "mod_x"],
        },
        "channels": [
            {"id": ch_kick, "name": "01_Kick_4onFloor", "color_hex": "#FF3366"},
            {"id": ch_snare, "name": "02_Cyber_Snare", "color_hex": "#00F0FF"},
            {"id": ch_bass, "name": "03_Rolling_Cyber_Bass", "color_hex": "#7928CA"},
            {"id": ch_lead, "name": "04_Phrygian_Lead", "color_hex": "#FFB800"},
            {"id": ch_palmas, "name": "05_Bulerias_Palmas", "color_hex": "#00FF66"},
        ],
        "timeline_sections": sections,
        "output_flp": str(flp_file),
        "file_size_bytes": len(raw_flp),
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
        "file_size_bytes": len(raw_flp),
    }


if __name__ == "__main__":
    res = compile_playlist_song_arrangement()
    print("Playlist Arranger output:", res)
