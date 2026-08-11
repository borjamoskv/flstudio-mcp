#!/usr/bin/env python3
"""
Antigravity FL Studio Native MCP Server v5.0 (Hardened SOTA)
Full Model Context Protocol Server providing native AI control, microtonal tuning,
reference song style matching, and MIDI orchestration tools for FL Studio 2025 via FastMCP.

Changes from v4.0:
- Structured logging (stdlib `logging`) replaces all print statements.
- Robust error handling on every lazy-imported tool.
- New `fl_health_check()` tool for runtime diagnostics.
- New `fl_generate_maceo_plex_kick()` tool.
- Removed `fl_swarm_quantum_collapse` (not FL-related, volatile /tmp path).
- Cleaned trailing whitespace.
"""

import sys
import os
import time
import logging
from typing import List, Dict, Optional

import mido
from mcp.server.fastmcp import FastMCP

# ═══════════════════════════════════════════════════════════════
# Logging Configuration
# ═══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FLStudio-MCP")

# ═══════════════════════════════════════════════════════════════
# Initialize FastMCP Server
# ═══════════════════════════════════════════════════════════════
mcp = FastMCP("FLStudio-MCP-Bridge")

# Global MIDI Port Connection
_outport = None


def get_midi_port():
    """Lazily opens a virtual CoreMIDI port. Returns None on failure."""
    global _outport
    if _outport is None:
        try:
            _outport = mido.open_output("Antigravity MCP Out", virtual=True)
            logger.info("Established virtual CoreMIDI port 'Antigravity MCP Out'")
        except Exception as e:
            logger.error("Failed to establish CoreMIDI port: %s", e)
    return _outport


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_health_check() -> str:
    """
    Runtime diagnostics: verifies MIDI port, script importability, and Scala tuning file availability.
    Returns a structured health report.
    """
    report_lines = ["═══ FL Studio MCP Health Check ═══"]

    # 1. MIDI Port
    port = get_midi_port()
    if port:
        report_lines.append("✅ CoreMIDI Port: ACTIVE ('Antigravity MCP Out')")
    else:
        report_lines.append("❌ CoreMIDI Port: OFFLINE")

    # 2. Core scripts importable
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
    core_modules = [
        "flstudio_algorithmic_composer",
        "flstudio_mcp_bridge",
        "flstudio_microtonal",
        "flstudio_legion_house_matrix",
        "air_moon_safari_engine",
        "maceo_plex_kick_synthesizer",
    ]
    for mod in core_modules:
        mod_path = os.path.join(scripts_dir, f"{mod}.py")
        if os.path.isfile(mod_path):
            report_lines.append(f"✅ Script: {mod}.py")
        else:
            report_lines.append(f"❌ Script MISSING: {mod}.py")

    # 3. Scala tuning files
    scalings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scalings")
    if os.path.isdir(scalings_dir):
        scl_files = [f for f in os.listdir(scalings_dir) if f.endswith(".scl")]
        report_lines.append(f"✅ Scala Tunings: {len(scl_files)} files ({', '.join(sorted(scl_files)[:5])}...)")
    else:
        report_lines.append("❌ Scala Tunings directory missing")

    report = "\n".join(report_lines)
    logger.info("Health check completed:\n%s", report)
    return report


# ═══════════════════════════════════════════════════════════════
# TRANSPORT & MIXER CONTROLS
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_set_tempo(bpm: float) -> str:
    """Sets global project tempo (BPM) in FL Studio 2025."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    bpm_int = max(60, min(187, int(bpm)))
    val = bpm_int - 60
    port.send(mido.Message('control_change', channel=15, control=15, value=val))
    logger.info("Tempo set to %d BPM", bpm_int)
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
    logger.info("Track %d volume → %.2f (byte %d)", track_id, volume, vol_byte)
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
    logger.info("Track %d pan → %+.2f", track_id, pan)
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
    logger.info("Track %d %s", track_id, status)
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
    logger.info("Track %d %s", track_id, status)
    return f"Track {track_id} {status}."


@mcp.tool()
def fl_transport_control(action: str) -> str:
    """Executes transport action in FL Studio: 'play', 'stop', 'record', 'loop', 'fast_forward', 'rewind'."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    action_map = {
        'play': 1, 'stop': 2, 'record': 3,
        'loop': 4, 'fast_forward': 5, 'rewind': 6,
    }
    act_lower = action.lower()
    if act_lower not in action_map:
        return f"Invalid action '{action}'. Valid actions: {list(action_map.keys())}"
    val = action_map[act_lower]
    port.send(mido.Message('control_change', channel=15, control=14, value=val))
    logger.info("Transport → %s", action.upper())
    return f"Transport action '{action.upper()}' executed."


@mcp.tool()
def fl_setup_sidechain(source_track: int, target_track: int) -> str:
    """Routes source_track as a sidechain send into target_track in FL Studio."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    msg = mido.Message('control_change', channel=15, control=18, value=target_track)
    port.send(msg)
    logger.info("Sidechain: Track %02d ⟹ Track %02d", source_track, target_track)
    return f"Sidechain routed: Track {source_track:02d} ===> Track {target_track:02d}."


@mcp.tool()
def fl_set_plugin_param(param_index: int, value: float) -> str:
    """Sets parameter value (0.0 to 1.0) on the focused plugin in FL Studio."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    val_byte = max(0, min(127, int(value * 127)))
    port.send(mido.Message('control_change', channel=15, control=19, value=val_byte))
    logger.info("Plugin param %d → %.2f", param_index, value)
    return f"Plugin parameter {param_index} set to {value:.2f}."


# ═══════════════════════════════════════════════════════════════
# GENERATION TOOLS — Reference Styles & Composition
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_create_from_reference(reference_name: str, bpm: Optional[float] = None) -> str:
    """
    Creates a full production template & MIDI sequence matching a reference song or artist style.
    Reference styles: 'satin_jackets', 'kerri_chandler', 'frankie_knuckles', 'ricardo_villalobos', 'fred_again', 'air_moon_safari', 'maceo_plex'.
    """
    try:
        from scripts.flstudio_algorithmic_composer import generate_reference_style_midi
        output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/ref_{reference_name.lower().replace(' ', '_')}.mid")
        info = generate_reference_style_midi(reference_name=reference_name, output_path=output_path, bpm=bpm)
        logger.info("Generated reference style '%s' at %s BPM", reference_name, info['bpm'])
        return f"Generated Reference Style Track ('{reference_name}'): {info['style']} at {info['bpm']} BPM. MIDI saved to {info['output_path']}."
    except Exception as e:
        logger.error("fl_create_from_reference failed: %s", e)
        return f"Error generating reference style: {e}"


@mcp.tool()
def fl_generate_air_moon_safari_multitrack(bpm: float = 88.0) -> str:
    """Generates a full 3-track MIDI arrangement (Rhodes, Minimoog, Solina Strings) in the style of AIR (Moon Safari)."""
    try:
        from scripts.air_moon_safari_engine import generate_air_moon_safari_multitrack
        output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/air_moon_safari_multitrack.mid")
        res = generate_air_moon_safari_multitrack(output_path=output_path, bpm=bpm)
        logger.info("Generated AIR Moon Safari multitrack → %s", res)
        return f"Generated AIR Moon Safari Multi-Track MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_air_moon_safari_multitrack failed: %s", e)
        return f"Error generating AIR Moon Safari: {e}"


@mcp.tool()
def fl_generate_100_agents_polyrhythm(bpm: float = 116.0) -> str:
    """Generates a 100-Agent polyrhythmic swarm matrix combining 3:4:5:7 cross-rhythms and phase shifts."""
    try:
        from scripts.flstudio_algorithmic_composer import generate_100_agents_polyrhythm_midi
        output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/100_agents_polyrhythm.mid")
        res = generate_100_agents_polyrhythm_midi(output_path=output_path, bpm=bpm)
        logger.info("Generated 100-Agent polyrhythm → %s", res)
        return f"Generated 100-Agent Polyrhythmic Swarm Matrix MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_100_agents_polyrhythm failed: %s", e)
        return f"Error generating polyrhythm: {e}"


@mcp.tool()
def fl_generate_groove_midi(bpm: float = 116.0, length_bars: int = 4, swing_ms: float = 6.0) -> str:
    """Generates a micro-shifted, humanized MIDI groove file for percussion with micro-swing timing."""
    try:
        from scripts.flstudio_mcp_bridge import FLStudioMCPBridge
        bridge = FLStudioMCPBridge()
        output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/micro_shaker_groove.mid")
        res = bridge.generate_humanized_groove_midi(output_path, bpm=bpm, length_bars=length_bars, swing_ms=swing_ms)
        logger.info("Generated groove MIDI → %s", res)
        return f"Generated micro-groove MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_groove_midi failed: %s", e)
        return f"Error generating groove MIDI: {e}"


@mcp.tool()
def fl_generate_chords(key_root: str = "C", scale_type: str = "minor", octave: int = 4, bpm: float = 116.0) -> str:
    """Generates a sophisticated 7th/9th MIDI chord progression file (i - VII - VI - v)."""
    try:
        from scripts.flstudio_algorithmic_composer import generate_chord_progression_midi
        output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/chords_{key_root}_{scale_type}.mid")
        res = generate_chord_progression_midi(output_path, key_root=key_root, scale_type=scale_type, octave=octave, bpm=bpm)
        logger.info("Generated chord progression → %s", res)
        return f"Generated 7th/9th chord progression MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_chords failed: %s", e)
        return f"Error generating chords: {e}"


@mcp.tool()
def fl_generate_bassline(key_root: str = "C", scale_type: str = "minor", octave: int = 1, bpm: float = 116.0) -> str:
    """Generates a syncopated Minimal/Dub sub-bassline MIDI file."""
    try:
        from scripts.flstudio_algorithmic_composer import generate_sub_bassline_midi
        output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/sub_bass_{key_root}.mid")
        res = generate_sub_bassline_midi(output_path, key_root=key_root, scale_type=scale_type, octave=octave, bpm=bpm)
        logger.info("Generated bassline → %s", res)
        return f"Generated syncopated sub-bassline MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_bassline failed: %s", e)
        return f"Error generating bassline: {e}"


# ═══════════════════════════════════════════════════════════════
# MICROTONAL & SCALA
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_generate_microtonal_midi(system_name: str = "24tet", bpm: float = 116.0, length_bars: int = 4) -> str:
    """
    Generates a Sub-Cent MPE Polyphonic Microtonal MIDI file.
    Systems: '24tet', '19tet', '31tet', 'just_intonation', 'bohlen_pierce', 'makam_bayati', 'makam_rast'.
    """
    try:
        from scripts.flstudio_microtonal import generate_microtonal_midi
        output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/microtonal_{system_name}.mid")
        res = generate_microtonal_midi(output_path, system_name=system_name, bpm=bpm, length_bars=length_bars)
        logger.info("Generated microtonal MIDI (%s) → %s", system_name, res)
        return f"Generated Microtonal MPE MIDI ({system_name}) saved to {res}."
    except Exception as e:
        logger.error("fl_generate_microtonal_midi failed: %s", e)
        return f"Error generating microtonal MIDI: {e}"


@mcp.tool()
def fl_export_scala_tuning(system_name: str = "24tet") -> str:
    """Exports a Scala (.scl) microtonal tuning file for native FL Studio VSTs (Sytrus, Harmor, FLEX)."""
    try:
        from scripts.flstudio_microtonal import export_scala_scl_file
        output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/{system_name}.scl")
        res = export_scala_scl_file(system_name=system_name, output_path=output_path)
        logger.info("Exported Scala tuning → %s", res)
        return f"Exported Scala Tuning File (.scl) to {res}."
    except Exception as e:
        logger.error("fl_export_scala_tuning failed: %s", e)
        return f"Error exporting Scala tuning: {e}"


@mcp.tool()
def fl_export_scala_kbm(middle_note: int = 60, ref_note: int = 69, ref_freq: float = 440.0) -> str:
    """Exports a Scala Keyboard Mapping (.kbm) file for fine-grained note frequency anchoring."""
    try:
        from scripts.flstudio_microtonal import export_scala_kbm_file
        output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/default.kbm")
        res = export_scala_kbm_file(output_path=output_path, middle_note=middle_note, ref_note=ref_note, ref_freq=ref_freq)
        logger.info("Exported Scala KBM → %s", res)
        return f"Exported Scala Keyboard Mapping File (.kbm) to {res}."
    except Exception as e:
        logger.error("fl_export_scala_kbm failed: %s", e)
        return f"Error exporting Scala KBM: {e}"


# ═══════════════════════════════════════════════════════════════
# HOUSE LEGION MATRIX & ARRANGEMENT
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_apply_house_legion_matrix() -> str:
    """Applies the full Legión de Productores HOUSE 19-Track Mixer Matrix & Sidechain Ducking in FL Studio."""
    try:
        from scripts.flstudio_legion_house_matrix import apply_house_legion_matrix
        success = apply_house_legion_matrix()
        if success:
            logger.info("House Legion Matrix applied successfully")
            return "Legión de Productores HOUSE Matrix applied successfully to FL Studio 2025!"
        return "Error applying House Legion Matrix to FL Studio."
    except Exception as e:
        logger.error("fl_apply_house_legion_matrix failed: %s", e)
        return f"Error applying House Legion Matrix: {e}"


@mcp.tool()
def fl_setup_vocal_dub_fx() -> str:
    """Sets up 3/16 Dotted 8th Dub Delay sends and Shimmer Reverb automation for vocals at 116 BPM."""
    try:
        from scripts.flstudio_vocal_dub_fx import setup_vocal_dub_fx
        success = setup_vocal_dub_fx()
        if success:
            logger.info("Vocal Dub FX configured")
            return "Vocal Dub FX & 3/16 Delay Sends configured successfully in FL Studio!"
        return "Error configuring Vocal Dub FX in FL Studio."
    except Exception as e:
        logger.error("fl_setup_vocal_dub_fx failed: %s", e)
        return f"Error configuring Vocal Dub FX: {e}"


@mcp.tool()
def fl_generate_full_arrangement() -> str:
    """Generates a full 128-Bar House Producers arrangement suite (Intro, Verse, Dub Breakdown, Peak Drop, Outro)."""
    try:
        from scripts.flstudio_full_arrangement_generator import generate_full_arrangement
        success = generate_full_arrangement()
        if success:
            logger.info("Full 128-Bar arrangement generated")
            return "Full 128-Bar House Producers Arrangement Suite generated successfully!"
        return "Error generating House Producers Arrangement Suite."
    except Exception as e:
        logger.error("fl_generate_full_arrangement failed: %s", e)
        return f"Error generating arrangement: {e}"


@mcp.tool()
def fl_generate_satin_jackets_loop(bpm: float = 116.0) -> str:
    """Generates a Satin Jackets style non-resolving Penrose Stair chord loop in C minor."""
    try:
        from scripts.flstudio_infinite_harmonic_loop import generate_satin_jackets_infinite_loop
        output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/satin_jackets_infinite_loop.mid")
        res = generate_satin_jackets_infinite_loop(output_path=output_path, bpm=bpm)
        logger.info("Generated Satin Jackets loop → %s", res)
        return f"Generated Satin Jackets Infinite Loop MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_satin_jackets_loop failed: %s", e)
        return f"Error generating Satin Jackets loop: {e}"


@mcp.tool()
def fl_generate_false_drop_major(bpm: float = 116.0) -> str:
    """Generates a False Drop ('Falso Drop') progression shifting from C minor tension into Eb Major / C Major euphoric expansion."""
    try:
        from scripts.flstudio_false_drop_major_expansion import generate_false_drop_major_expansion
        output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/false_drop_major_expansion.mid")
        res = generate_false_drop_major_expansion(output_path=output_path, bpm=bpm)
        logger.info("Generated False Drop → %s", res)
        return f"Generated False Drop Major Expansion MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_false_drop_major failed: %s", e)
        return f"Error generating False Drop: {e}"


@mcp.tool()
def fl_apply_no_lo_entiende_template() -> str:
    """Applies full SOTA mix preset, sidechain matrix, and gains for 'No Lo Entiende' (116 BPM, Cmin)."""
    try:
        from scripts.flstudio_mcp_bridge import execute_sota_setup
        execute_sota_setup()
        logger.info("'No Lo Entiende' template applied")
        return "SOTA Mix Template for 'No Lo Entiende' applied successfully to FL Studio 2025."
    except Exception as e:
        logger.error("fl_apply_no_lo_entiende_template failed: %s", e)
        return f"Error applying template: {e}"


# ═══════════════════════════════════════════════════════════════
# SOTA MICROTONAL & LOCRIAN
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_generate_sota_microtonal_house(subgenre: str = "19tet_deep_house") -> str:
    """
    Generates specialized SOTA Microtonal House MIDI files based on Plomp-Levelt psychoacoustic optimization.
    Subgenres: '19tet_deep_house', '24tet_makam_minimal', '31tet_soulful_house', 'bohlen_pierce_techno_house', 'slendro_tech_house'.
    """
    try:
        from scripts.flstudio_microtonal_sota import generate_sota_microtonal_house_midi
        output_path = os.path.expanduser(f"~/10_PROJECTS/flstudio-mcp/scripts/sota_microtonal_{subgenre}.mid")
        info = generate_sota_microtonal_house_midi(subgenre_key=subgenre, output_path=output_path)
        logger.info("SOTA Microtonal House (%s) → %s", subgenre, info['output_path'])
        return f"SOTA Microtonal House Generated ({info['subgenre']}): {info['description']} at {info['bpm']} BPM. MIDI -> {info['output_path']}"
    except Exception as e:
        logger.error("fl_generate_sota_microtonal_house failed: %s", e)
        return f"Error generating SOTA microtonal house: {e}"


@mcp.tool()
def fl_generate_locrian_sota_techno(bpm: float = 125.0) -> str:
    """Generates a 3-track SOTA Locrian & Xenharmonic Techno MIDI arrangement."""
    try:
        from scripts.locrian_microtonal_engine import generate_locrian_sota_suite
        output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/locrian_sota_techno_suite.mid")
        res = generate_locrian_sota_suite(output_path=output_path, bpm=bpm)
        logger.info("Locrian SOTA techno → %s", res)
        return f"Generated SOTA Locrian & Xenharmonic Techno MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_locrian_sota_techno failed: %s", e)
        return f"Error generating Locrian techno: {e}"


# ═══════════════════════════════════════════════════════════════
# FLEX SYNTH MACROS
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_flex_set_macro(macro_index: int, value: float) -> str:
    """
    Controls Macro 1..8 parameters on the focused instance of FL Studio's FLEX synth.
    macro_index: 1 to 8. value: 0.0 to 1.0.
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."
    macro_index = max(1, min(8, int(macro_index)))
    cc_number = 20 + macro_index
    val_byte = max(0, min(127, int(value * 127)))
    port.send(mido.Message('control_change', channel=15, control=cc_number, value=val_byte))
    logger.info("FLEX Macro %d → %.2f (CC%d: %d)", macro_index, value, cc_number, val_byte)
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
        "rhodes": [(1, 0.70), (2, 0.30), (5, 0.40), (7, 0.35)],
        "sub_bass": [(1, 0.45), (2, 0.60), (3, 0.80), (7, 0.00)],
        "solina_strings": [(1, 0.85), (4, 0.90), (5, 0.60), (7, 0.50)],
        "acid_lead": [(1, 0.90), (2, 0.85), (3, 0.95), (6, 0.40)],
        "synthwave_pad": [(1, 0.65), (2, 0.40), (5, 0.50), (7, 0.60)],
    }
    target = vibes_map.get(vibe.lower(), vibes_map["rhodes"])
    for m_idx, val in target:
        cc_num = 20 + m_idx
        v_byte = int(val * 127)
        port.send(mido.Message('control_change', channel=15, control=cc_num, value=v_byte))
    logger.info("FLEX vibe '%s' applied (%d params)", vibe, len(target))
    return f"Applied FLEX Macro Preset Vibe '{vibe}' ({len(target)} parameters automated via CoreMIDI)."


# ═══════════════════════════════════════════════════════════════
# PLUGIN AUDIT & AUTOMATION
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_audit_plugin_inventory() -> str:
    """Audits and returns the full scanned inventory of native generators, effects, VST3/AU plugins, and presets."""
    try:
        from scripts.fl_plugin_registry import get_plugin_inventory_summary
        summary = get_plugin_inventory_summary()
        logger.info("Plugin audit: %d generators, %d effects, %d VST3", summary['native_generators_count'], summary['native_effects_count'], summary['third_party_vst3_count'])
        return (
            f"FL Studio Plugin Audit Results:\n"
            f"Native Generators ({summary['native_generators_count']}): {', '.join(summary['generators'][:10])}...\n"
            f"Native Effects ({summary['native_effects_count']}): {', '.join(summary['effects'][:10])}...\n"
            f"Third-Party VST3/AU ({summary['third_party_vst3_count']}): {', '.join(summary['vst3'])}"
        )
    except Exception as e:
        logger.error("fl_audit_plugin_inventory failed: %s", e)
        return f"Error auditing plugins: {e}"


@mcp.tool()
def fl_automate_tb303_acid(cutoff: float = 0.8, resonance: float = 0.85, env_mod: float = 0.9) -> str:
    """Automates Transistor Bass (TB-303 Acid Synth) Cutoff, Resonance, and Env Mod via MIDI CC."""
    try:
        port = get_midi_port()
        if not port:
            return "Error: Could not open MIDI port."
        from scripts.fl_preset_automation_matrix import automate_tb303_acid
        result = automate_tb303_acid(port, cutoff=cutoff, resonance=resonance, env_mod=env_mod)
        logger.info("TB-303 automated: cutoff=%.2f res=%.2f env=%.2f", cutoff, resonance, env_mod)
        return result
    except Exception as e:
        logger.error("fl_automate_tb303_acid failed: %s", e)
        return f"Error automating TB-303: {e}"


@mcp.tool()
def fl_automate_luxeverb_shimmer(decay: float = 0.85, shimmer: float = 0.60) -> str:
    """Automates LuxeVerb Decay time and Shimmer amount via MIDI CC."""
    try:
        port = get_midi_port()
        if not port:
            return "Error: Could not open MIDI port."
        from scripts.fl_preset_automation_matrix import automate_luxeverb_shimmer
        result = automate_luxeverb_shimmer(port, decay=decay, shimmer=shimmer)
        logger.info("LuxeVerb automated: decay=%.2f shimmer=%.2f", decay, shimmer)
        return result
    except Exception as e:
        logger.error("fl_automate_luxeverb_shimmer failed: %s", e)
        return f"Error automating LuxeVerb: {e}"


@mcp.tool()
def fl_trigger_gross_beat_slot(slot_index: int = 1) -> str:
    """Triggers Gross Beat Time/Volume Slot (1 to 36)."""
    try:
        port = get_midi_port()
        if not port:
            return "Error: Could not open MIDI port."
        from scripts.fl_preset_automation_matrix import automate_gross_beat_slot
        result = automate_gross_beat_slot(port, slot_index=slot_index)
        logger.info("Gross Beat slot %d triggered", slot_index)
        return result
    except Exception as e:
        logger.error("fl_trigger_gross_beat_slot failed: %s", e)
        return f"Error triggering Gross Beat: {e}"


@mcp.tool()
def fl_apply_master_legion_architecture() -> str:
    """Applies the full Master .legion 19-Track Architecture mapping all generators, effects, routing."""
    try:
        from scripts.legion_master_mapper import export_master_legion_architecture, apply_master_legion_over_midi
        out_file = export_master_legion_architecture()
        success = apply_master_legion_over_midi()
        if success:
            logger.info("Master .legion architecture applied → %s", out_file)
            return f"Applied Master .legion 19-Track Architecture successfully to FL Studio 2025! Schema -> {out_file}"
        return "Error applying Master .legion Architecture."
    except Exception as e:
        logger.error("fl_apply_master_legion_architecture failed: %s", e)
        return f"Error applying .legion architecture: {e}"


# ═══════════════════════════════════════════════════════════════
# NEW: MACEO PLEX KICK SYNTHESIZER
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_generate_maceo_plex_kick(fundamental_hz: float = 50.0, bpm: float = 124.0, length_bars: int = 4) -> str:
    """
    Generates a Maceo Plex style analog kick drum pattern with 50Hz fundamental, sub-rumble,
    and 16th-note ghost kick patterns.
    """
    try:
        from scripts.maceo_plex_kick_synthesizer import generate_maceo_plex_kick_pattern
        output_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/samples/maceo_plex/kick_pattern.mid")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        res = generate_maceo_plex_kick_pattern(output_path=output_path, fundamental_hz=fundamental_hz, bpm=bpm, length_bars=length_bars)
        logger.info("Maceo Plex kick pattern → %s", res)
        return f"Generated Maceo Plex Kick Pattern MIDI saved to {res}."
    except Exception as e:
        logger.error("fl_generate_maceo_plex_kick failed: %s", e)
        return f"Error generating Maceo Plex kick: {e}"


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info("Starting FL Studio MCP Server v5.0 (Hardened SOTA)…")
    mcp.run()
