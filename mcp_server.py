#!/usr/bin/env python3
"""
Antigravity FL Studio Native MCP Server (SOTA Ultramax)
Full Model Context Protocol Server providing native AI control tools for FL Studio 2025 via FastMCP.
"""

import sys
import os
import time
import mido
from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("FLStudio-MCP-Bridge")

# Global MIDI Port Connection
_outport = None

def get_midi_port():
    global _outport
    if _outport is None:
        try:
            _outport = mido.open_output("Antigravity MCP Out", virtual=True)
            print("[MCP Server] Established virtual CoreMIDI port 'Antigravity MCP Out'")
        except Exception as e:
            print(f"[MCP Server] Error establishing port: {e}")
    return _outport


@mcp.tool()
def fl_set_tempo(bpm: float) -> str:
    """Sets global project tempo (BPM) in FL Studio 2025."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    bpm_int = max(60, min(187, int(bpm)))
    val = bpm_int - 60
    port.send(mido.Message('control_change', channel=15, control=15, value=val))
    return f"FL Studio tempo set to {bpm_int} BPM."


@mcp.tool()
def fl_set_mixer_volume(track_id: int, volume: float) -> str:
    """Sets volume (0.0 = silent, 1.0 = 100%/0dB) for a specific FL Studio mixer track_id (0-125)."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    track_id = max(0, min(125, int(track_id)))
    vol_byte = max(0, min(127, int(volume * 127)))
    port.send(mido.Message('control_change', channel=15, control=10, value=vol_byte))
    return f"Track {track_id} volume set to {volume:.2f} (MIDI byte: {vol_byte})."


@mcp.tool()
def fl_set_mixer_pan(track_id: int, pan: float) -> str:
    """Sets panning (-1.0 = Full Left, 0.0 = Center, +1.0 = Full Right) for mixer track_id."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    track_id = max(0, min(125, int(track_id)))
    pan_byte = max(0, min(127, int((pan + 1.0) * 63.5)))
    port.send(mido.Message('control_change', channel=15, control=11, value=pan_byte))
    return f"Track {track_id} panning set to {pan:+.2f}."


@mcp.tool()
def fl_mute_track(track_id: int, mute: bool) -> str:
    """Mutes or unmutes a specific FL Studio mixer track_id."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    val = 127 if mute else 0
    port.send(mido.Message('control_change', channel=15, control=12, value=val))
    status = "Muted" if mute else "Unmuted"
    return f"Track {track_id} {status}."


@mcp.tool()
def fl_solo_track(track_id: int, solo: bool) -> str:
    """Solos or unsolos a specific FL Studio mixer track_id."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    val = 127 if solo else 0
    port.send(mido.Message('control_change', channel=15, control=13, value=val))
    status = "Soloed" if solo else "Unsoloed"
    return f"Track {track_id} {status}."


@mcp.tool()
def fl_transport_control(action: str) -> str:
    """Executes transport action in FL Studio: 'play', 'stop', 'record', 'loop', 'fast_forward', 'rewind'."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    action_map = {
        'play': 1,
        'stop': 2,
        'record': 3,
        'loop': 4,
        'fast_forward': 5,
        'rewind': 6
    }
    act_lower = action.lower()
    if act_lower not in action_map:
        return f"Invalid action '{action}'. Valid actions: {list(action_map.keys())}"
    
    val = action_map[act_lower]
    port.send(mido.Message('control_change', channel=15, control=14, value=val))
    return f"Transport action '{action.upper()}' executed."


@mcp.tool()
def fl_setup_sidechain(source_track: int, target_track: int) -> str:
    """Routes source_track as a sidechain send into target_track in FL Studio."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    msg = mido.Message('control_change', channel=15, control=18, value=target_track)
    port.send(msg)
    return f"Sidechain routed: Track {source_track:02d} ===> Track {target_track:02d}."


@mcp.tool()
def fl_set_plugin_param(param_index: int, value: float) -> str:
    """Sets parameter value (0.0 to 1.0) on the focused plugin in FL Studio."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    val_byte = max(0, min(127, int(value * 127)))
    port.send(mido.Message('control_change', channel=15, control=19, value=val_byte))
    return f"Plugin parameter {param_index} set to {value:.2f}."


@mcp.tool()
def fl_generate_groove_midi(bpm: float = 116.0, length_bars: int = 4, swing_ms: float = 6.0) -> str:
    """Generates a micro-shifted, humanized MIDI groove file for percussion with micro-swing timing."""
    from scripts.flstudio_mcp_bridge import FLStudioMCPBridge
    bridge = FLStudioMCPBridge()
    output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/micro_shaker_groove.mid")
    res = bridge.generate_humanized_groove_midi(output_path, bpm=bpm, length_bars=length_bars, swing_ms=swing_ms)
    return f"Generated micro-groove MIDI saved to {res}."


@mcp.tool()
def fl_generate_chords(key_root: str = "C", scale_type: str = "minor", octave: int = 4, bpm: float = 116.0) -> str:
    """Generates a sophisticated 7th/9th MIDI chord progression file (i - VII - VI - v)."""
    from scripts.flstudio_algorithmic_composer import generate_chord_progression_midi
    output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/chords_{key_root}_{scale_type}.mid")
    res = generate_chord_progression_midi(output_path, key_root=key_root, scale_type=scale_type, octave=octave, bpm=bpm)
    return f"Generated 7th/9th chord progression MIDI saved to {res}."


@mcp.tool()
def fl_generate_bassline(key_root: str = "C", scale_type: str = "minor", octave: int = 1, bpm: float = 116.0) -> str:
    """Generates a syncopated Minimal/Dub sub-bassline MIDI file."""
    from scripts.flstudio_algorithmic_composer import generate_sub_bassline_midi
    output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/sub_bass_{key_root}.mid")
    res = generate_sub_bassline_midi(output_path, key_root=key_root, scale_type=scale_type, octave=octave, bpm=bpm)
    return f"Generated syncopated sub-bassline MIDI saved to {res}."


@mcp.tool()
def fl_apply_no_lo_entiende_template() -> str:
    """Applies full SOTA mix preset, sidechain matrix, and gains for 'No Lo Entiende' (116 BPM, Cmin)."""
    from scripts.flstudio_mcp_bridge import execute_sota_setup
    execute_sota_setup()
    return "SOTA Mix Template for 'No Lo Entiende' applied successfully to FL Studio 2025."


if __name__ == "__main__":
    mcp.run()
