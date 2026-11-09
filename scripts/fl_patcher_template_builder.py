#!/usr/bin/env python3
"""
Antigravity Modular Patcher Rig Builder for FL Studio 2025
Generates modular Patcher architecture manifests mapping:
- VFX Key Mapper -> VFX Keyboard Splitter
- Low-End Path (< 90Hz Mono Sub 12-TET)
- High-End Path (> 90Hz 19-TET / 24-TET Microtonal Chords & Leads)
- Sidechain Ducking Curve Matrix
"""

import os
import json

PATCHER_RIG_SCHEMA = {
    "name": "Antigravity SOTA Microtonal Modular Patcher Rig",
    "version": "2.0-SOVEREIGN",
    "nodes": [
        {"id": "MIDI_IN", "type": "FL Studio Native MIDI Input"},
        {"id": "VFX_KEY_MAPPER", "type": "VFX Key Mapper", "scale": "24-TET Makam Bayati"},
        {"id": "VFX_SPLITTER", "type": "VFX Keyboard Splitter", "split_note": "C4 (MIDI 60)"},
        {"id": "SUB_SYNTH", "type": "3x Osc / BooBass", "freq_range": "20Hz - 90Hz", "mode": "12-TET Strict Mono"},
        {"id": "CHORD_SYNTH", "type": "Harmor / FLEX", "freq_range": "> 90Hz", "mode": "19-TET / 24-TET Microtonal"},
        {"id": "SIDECHAIN_SHAPER", "type": "Fruity Love Philter / Gross Beat", "curve": "Logarithmic 4/4 RMS Ducking"},
        {"id": "AUDIO_OUT", "type": "FL Studio Audio Output"}
    ],
    "connections": [
        {"from": "MIDI_IN", "to": "VFX_KEY_MAPPER"},
        {"from": "VFX_KEY_MAPPER", "to": "VFX_SPLITTER"},
        {"from": "VFX_SPLITTER.low", "to": "SUB_SYNTH"},
        {"from": "VFX_SPLITTER.high", "to": "CHORD_SYNTH"},
        {"from": "SUB_SYNTH", "to": "SIDECHAIN_SHAPER"},
        {"from": "CHORD_SYNTH", "to": "SIDECHAIN_SHAPER"},
        {"from": "SIDECHAIN_SHAPER", "to": "AUDIO_OUT"}
    ]
}

def export_patcher_rig_manifest(output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(PATCHER_RIG_SCHEMA, f, indent=2)

    print(f"✅ Exported Modular Patcher Rig Manifest -> {output_path}")
    return output_path

if __name__ == "__main__":
    out_manifest = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/patcher_microtonal_rig.json")
    export_patcher_rig_manifest(out_manifest)
