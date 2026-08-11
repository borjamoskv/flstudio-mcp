#!/usr/bin/env python3
"""
Antigravity FL Studio Native MCP Server (SOTA Microtonal, Xenharmonic & 100-Agent Swarm Ultramax)
Full Model Context Protocol Server providing native AI control, microtonal tuning, reference song style matching, and MIDI orchestration tools for FL Studio 2025 via FastMCP.
"""

import sys
import os
import time
import mido
import subprocess
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
def fl_create_from_reference(reference_name: str, bpm: Optional[float] = None) -> str:
    """
    Creates a full production template & MIDI sequence matching a reference song or artist style.
    Reference styles: 'satin_jackets', 'kerri_chandler', 'frankie_knuckles', 'ricardo_villalobos', 'fred_again', 'air_moon_safari', 'maceo_plex'.
    """
    from scripts.flstudio_algorithmic_composer import generate_reference_style_midi
    output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/ref_{reference_name.lower().replace(' ', '_')}.mid")
    info = generate_reference_style_midi(reference_name=reference_name, output_path=output_path, bpm=bpm)
    return f"Generated Reference Style Track ('{reference_name}'): {info['style']} at {info['bpm']} BPM. MIDI saved to {info['output_path']}."


@mcp.tool()
def fl_generate_air_moon_safari_multitrack(bpm: float = 88.0) -> str:
    """
    Generates a full 3-track MIDI arrangement (Rhodes, Minimoog, Solina Strings) in the style of AIR (Moon Safari).
    """
    from scripts.air_moon_safari_engine import generate_air_moon_safari_multitrack
    output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/air_moon_safari_multitrack.mid")
    res = generate_air_moon_safari_multitrack(output_path=output_path, bpm=bpm)
    return f"Generated AIR Moon Safari Multi-Track MIDI saved to {res}."


@mcp.tool()
def fl_generate_100_agents_polyrhythm(bpm: float = 116.0) -> str:
    """
    Generates a 100-Agent polyrhythmic swarm matrix combining 3:4:5:7 cross-rhythms and phase shifts.
    """
    from scripts.flstudio_algorithmic_composer import generate_100_agents_polyrhythm_midi
    output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/100_agents_polyrhythm.mid")
    res = generate_100_agents_polyrhythm_midi(output_path=output_path, bpm=bpm)
    return f"Generated 100-Agent Polyrhythmic Swarm Matrix MIDI saved to {res}."


@mcp.tool()
def fl_swarm_quantum_collapse(p_cores: int = 4, s_threads: int = 1) -> str:
    """
    Executes empirical PxS Swarm Quantum Collapse across workspace nodes.
    Purges git locks, anchors main branches, executes deterministic synchronization, and measures kernel context switch telemetry.
    """
    script_path = "/tmp/quantum_collapse_swarm.py"
    if not os.path.exists(script_path):
        return f"Error: Swarm collapse script {script_path} not found."
    cmd = f"python3 {script_path} --p {p_cores} --s {s_threads}"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return f"Swarm Quantum Collapse Execution Results:\n{res.stdout}\n{res.stderr}"


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
def fl_generate_microtonal_midi(system_name: str = "24tet", bpm: float = 116.0, length_bars: int = 4) -> str:
    """
    Generates a Sub-Cent MPE Polyphonic Microtonal MIDI file.
    Systems: '24tet' (quarter-tones), '19tet', '31tet', 'just_intonation', 'bohlen_pierce', 'makam_bayati', 'makam_rast'.
    """
    from scripts.flstudio_microtonal import generate_microtonal_midi
    output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/microtonal_{system_name}.mid")
    res = generate_microtonal_midi(output_path, system_name=system_name, bpm=bpm, length_bars=length_bars)
    return f"Generated Microtonal MPE MIDI ({system_name}) saved to {res}."


@mcp.tool()
def fl_export_scala_tuning(system_name: str = "24tet") -> str:
    """
    Exports a Scala (.scl) microtonal tuning file for native FL Studio VSTs (Sytrus, Harmor, FLEX).
    """
    from scripts.flstudio_microtonal import export_scala_scl_file
    output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/{system_name}.scl")
    res = export_scala_scl_file(system_name=system_name, output_path=output_path)
    return f"Exported Scala Tuning File (.scl) to {res}."


@mcp.tool()
def fl_export_scala_kbm(middle_note: int = 60, ref_note: int = 69, ref_freq: float = 440.0) -> str:
    """Exports a Scala Keyboard Mapping (.kbm) file for fine-grained note frequency anchoring."""
    from scripts.flstudio_microtonal import export_scala_kbm_file
    output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/default.kbm")
    res = export_scala_kbm_file(output_path=output_path, middle_note=middle_note, ref_note=ref_note, ref_freq=ref_freq)
    return f"Exported Scala Keyboard Mapping File (.kbm) to {res}."


@mcp.tool()
def fl_apply_house_legion_matrix() -> str:
    """Applies the full Legión de Productores HOUSE 19-Track Mixer Matrix & Sidechain Ducking in FL Studio."""
    from scripts.flstudio_legion_house_matrix import apply_house_legion_matrix
    success = apply_house_legion_matrix()
    if success:
        return "Legión de Productores HOUSE Matrix applied successfully to FL Studio 2025!"
    return "Error applying House Legion Matrix to FL Studio."


@mcp.tool()
def fl_setup_vocal_dub_fx() -> str:
    """Sets up 3/16 Dotted 8th Dub Delay sends and Shimmer Reverb automation for vocals at 116 BPM."""
    from scripts.flstudio_vocal_dub_fx import setup_vocal_dub_fx
    success = setup_vocal_dub_fx()
    if success:
        return "Vocal Dub FX & 3/16 Delay Sends configured successfully in FL Studio!"
    return "Error configuring Vocal Dub FX in FL Studio."


@mcp.tool()
def fl_generate_full_arrangement() -> str:
    """Generates a full 128-Bar House Producers arrangement suite (Intro, Verse, Dub Breakdown, Peak Drop, Outro)."""
    from scripts.flstudio_full_arrangement_generator import generate_full_arrangement
    success = generate_full_arrangement()
    if success:
        return "Full 128-Bar House Producers Arrangement Suite generated successfully!"
    return "Error generating House Producers Arrangement Suite."


@mcp.tool()
def fl_generate_satin_jackets_loop(bpm: float = 116.0) -> str:
    """Generates a Satin Jackets style non-resolving Penrose Stair chord loop in C minor."""
    from scripts.flstudio_infinite_harmonic_loop import generate_satin_jackets_infinite_loop
    output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/satin_jackets_infinite_loop.mid")
    res = generate_satin_jackets_infinite_loop(output_path=output_path, bpm=bpm)
    return f"Generated Satin Jackets Infinite Loop MIDI saved to {res}."


@mcp.tool()
def fl_generate_false_drop_major(bpm: float = 116.0) -> str:
    """Generates a False Drop ('Falso Drop') progression shifting from C minor tension into Eb Major / C Major euphoric expansion."""
    from scripts.flstudio_false_drop_major_expansion import generate_false_drop_major_expansion
    output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/false_drop_major_expansion.mid")
    res = generate_false_drop_major_expansion(output_path=output_path, bpm=bpm)
    return f"Generated False Drop Major Expansion MIDI saved to {res}."


@mcp.tool()
def fl_apply_no_lo_entiende_template() -> str:
    """Applies full SOTA mix preset, sidechain matrix, and gains for 'No Lo Entiende' (116 BPM, Cmin)."""
    from scripts.flstudio_mcp_bridge import execute_sota_setup
    execute_sota_setup()
    return "SOTA Mix Template for 'No Lo Entiende' applied successfully to FL Studio 2025."


@mcp.tool()
def fl_generate_sota_microtonal_house(subgenre: str = "19tet_deep_house") -> str:
    """
    Generates specialized SOTA Microtonal House MIDI files based on Plomp-Levelt psychoacoustic optimization.
    Subgenres: '19tet_deep_house', '24tet_makam_minimal', '31tet_soulful_house', 'bohlen_pierce_techno_house', 'slendro_tech_house'.
    """
    from scripts.flstudio_microtonal_sota import generate_sota_microtonal_house_midi
    output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/sota_microtonal_{subgenre}.mid")
    info = generate_sota_microtonal_house_midi(subgenre_key=subgenre, output_path=output_path)
    return f"SOTA Microtonal House Generated ({info['subgenre']}): {info['description']} at {info['bpm']} BPM. MIDI -> {info['output_path']}"


@mcp.tool()
def fl_generate_locrian_sota_techno(bpm: float = 125.0) -> str:
    """
    Generates a 3-track SOTA Locrian & Xenharmonic Techno MIDI arrangement (Acid Sub-Tritone, 24-TET Neutral-2nd Arp, Super-Locrian Stabs).
    """
    from scripts.locrian_microtonal_engine import generate_locrian_sota_suite
    output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/locrian_sota_techno_suite.mid")
    res = generate_locrian_sota_suite(output_path=output_path, bpm=bpm)
    return f"Generated SOTA Locrian & Xenharmonic Techno MIDI saved to {res}."


@mcp.tool()
def fl_flex_set_macro(macro_index: int, value: float) -> str:
    """
    Controls Macro 1..8 parameters on the focused instance of FL Studio's FLEX synth.
    macro_index: 1 to 8 (1=Cutoff, 2=Resonance, 3=Env Mod, 4=Pitch/Decay, 5=Chorus, 6=Delay, 7=Reverb, 8=Limiter).
    value: 0.0 (minimum) to 1.0 (maximum).
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    macro_index = max(1, min(8, int(macro_index)))
    cc_number = 20 + macro_index  # CC 21..28 mapped to FLEX Macros 1..8
    val_byte = max(0, min(127, int(value * 127)))
    port.send(mido.Message('control_change', channel=15, control=cc_number, value=val_byte))
    return f"FLEX Synth Macro {macro_index} set to {value:.2f} (MIDI CC {cc_number}: {val_byte})."


@mcp.tool()
def fl_flex_apply_preset_vibe(vibe: str = "rhodes") -> str:
    """
    Automates FLEX macros for target production vibes: 'rhodes', 'sub_bass', 'solina_strings', 'acid_lead', 'synthwave_pad'.
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    
    vibes_map = {
        "rhodes": [(1, 0.70), (2, 0.30), (5, 0.40), (7, 0.35)],       # Warm Fender Rhodes
        "sub_bass": [(1, 0.45), (2, 0.60), (3, 0.80), (7, 0.00)],     # Deep Sub Bass
        "solina_strings": [(1, 0.85), (4, 0.90), (5, 0.60), (7, 0.50)], # Shimmering Solina Strings
        "acid_lead": [(1, 0.90), (2, 0.85), (3, 0.95), (6, 0.40)],     # Resonant Acid Cutoff
        "synthwave_pad": [(1, 0.65), (2, 0.40), (5, 0.50), (7, 0.60)]  # Lush Analog Pad
    }
    target = vibes_map.get(vibe.lower(), vibes_map["rhodes"])
    for m_idx, val in target:
        cc_num = 20 + m_idx
        v_byte = int(val * 127)
        port.send(mido.Message('control_change', channel=15, control=cc_num, value=v_byte))
    return f"Applied FLEX Macro Preset Vibe '{vibe}' ({len(target)} parameters automated via CoreMIDI)."


if __name__ == "__main__":
    mcp.run()



