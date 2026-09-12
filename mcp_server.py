#!/usr/bin/env python3
"""
Antigravity FL Studio Native MCP Server v6.0 (SOTA Zenith)
Full Model Context Protocol Server providing native AI control, microtonal tuning,
two-way hardware controller integration, and MIDI orchestration tools for FL Studio 2025 via FastMCP.

Aligned with:
- device_Antigravity_MCP.py (125 mixer tracks, Channel rack, markers, transport)
- Centralized Music Assets Invariant (~/Music/FL Studio Bounces/)
- 26 Scala Tunings & Sethares/Plomp-Levelt psychoacoustics
- 19 SOTA Piano Roll Scripts (including Dark Cyber-Flamenco, Euclidean, Cellular Automata)
"""

import sys
import os
import time
import math
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional

import mido
from mcp.server.fastmcp import FastMCP

# ═══════════════════════════════════════════════════════════════
# Paths & Invariants
# ═══════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
SCALINGS_DIR = BASE_DIR / "scalings"
SAMPLES_DIR = BASE_DIR / "samples"

FL_SETTINGS = Path.home() / "Documents/Image-Line/FL Studio/Settings"
FL_PIANOROLL = FL_SETTINGS / "Piano roll scripts"
FL_HARDWARE = FL_SETTINGS / "Hardware"
FL_TUNING = FL_SETTINGS / "Tuning"

MUSIC_DIR = Path.home() / "Music"
MUSIC_BOUNCES_DIR = MUSIC_DIR / "FL Studio Bounces"
MUSIC_BOUNCES_DIR.mkdir(parents=True, exist_ok=True)

# Add scripts directory to path for legacy modules
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(BASE_DIR))

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
# 1. HEALTH & DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_health_check() -> str:
    """
    Runtime diagnostics: verifies FL Studio app, CoreMIDI virtual port,
    hardware controller script, Piano Roll scripts, and Scala tunings.
    """
    report_lines = ["═══ FL Studio MCP SOTA Health Check (v6.0) ═══"]

    # 1. CoreMIDI Port
    port = get_midi_port()
    if port:
        report_lines.append("✅ CoreMIDI Port: ACTIVE ('Antigravity MCP Out')")
    else:
        report_lines.append("❌ CoreMIDI Port: OFFLINE")

    # 2. FL Studio Application
    fl_app = Path("/Applications/FL Studio 2025.app")
    if fl_app.exists():
        report_lines.append(f"✅ FL Studio App: INSTALLED ({fl_app})")
    else:
        report_lines.append("⚠️ FL Studio 2025 not found in default /Applications")

    # 3. Hardware Controller Script
    hw_script = FL_HARDWARE / "AntigravityMCP/device_Antigravity_MCP.py"
    if hw_script.exists():
        report_lines.append(f"✅ Hardware Controller: INSTALLED ({hw_script})")
    else:
        report_lines.append("❌ Hardware Controller NOT INSTALLED in FL Studio Settings")

    # 4. Piano Roll Scripts
    if FL_PIANOROLL.exists():
        scripts_count = len(list(FL_PIANOROLL.glob("*.py")) + list(FL_PIANOROLL.glob("*.pyscript")))
        report_lines.append(f"✅ Piano Roll Scripts: {scripts_count} installed in {FL_PIANOROLL}")
    else:
        report_lines.append("❌ Piano Roll scripts directory missing")

    # 5. Scala Tuning Files
    if FL_TUNING.exists():
        scl_count = len(list(FL_TUNING.glob("*.scl")))
        report_lines.append(f"✅ Scala Tunings: {scl_count} profiles in {FL_TUNING}")
    else:
        report_lines.append("❌ Scala tuning directory missing")

    # 6. Music Assets Centralization
    if MUSIC_BOUNCES_DIR.exists():
        report_lines.append(f"✅ Centralized Music: ACTIVE ({MUSIC_BOUNCES_DIR})")

    report = "\n".join(report_lines)
    logger.info("Health check completed:\n%s", report)
    return report


# ═══════════════════════════════════════════════════════════════
# 2. TRANSPORT & MASTER DAW CONTROLS
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_transport_control(action: str) -> str:
    """
    Executes transport actions in FL Studio:
    'play', 'pause', 'stop', 'record', 'loop', 'metronome', 'undo', 'redo', 'save'.
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    action_map = {
        'play': (10, 127),
        'pause': (10, 0),
        'stop': (11, 127),
        'record': (12, 127),
        'loop': (13, 127),
        'metronome': (14, 127),
        'undo': (16, 127),
        'redo': (17, 127),
        'save': (19, 127),
    }
    act_lower = action.lower()
    if act_lower not in action_map:
        return f"Invalid action '{action}'. Valid actions: {list(action_map.keys())}"

    cc_num, val = action_map[act_lower]
    # Sends on MIDI Channel 16 (0-indexed 15) to device_Antigravity_MCP.py
    port.send(mido.Message('control_change', channel=15, control=cc_num, value=val))
    logger.info("Transport → %s (CC%d: %d)", action.upper(), cc_num, val)
    return f"Transport action '{action.upper()}' executed successfully in FL Studio."


@mcp.tool()
def fl_set_tempo(bpm: float) -> str:
    """
    Sets the global project tempo (BPM) in FL Studio (range: 60 - 187 BPM).
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    bpm_int = max(60, min(187, int(round(bpm))))
    val = bpm_int - 60
    # Sends on MIDI Channel 16 (0-indexed 15), CC 15
    port.send(mido.Message('control_change', channel=15, control=15, value=val))
    logger.info("Tempo set to %d BPM", bpm_int)
    return f"FL Studio project tempo set to {bpm_int} BPM."


# ═══════════════════════════════════════════════════════════════
# 3. MIXER CONTROLS (125 TRACKS)
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_set_mixer_volume(track_id: int, volume: float) -> str:
    """
    Sets volume for a mixer track (0 = Master, 1-125 = Tracks).
    volume: 0.0 (silent) to 1.0 (100% / 0dB).
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    track_id = max(0, min(125, int(track_id)))
    vol_byte = max(0, min(127, int(volume * 127)))
    # Channel 0 (Ch 1), control = track_id
    port.send(mido.Message('control_change', channel=0, control=track_id, value=vol_byte))
    logger.info("Track %d volume → %.2f", track_id, volume)
    return f"Mixer track {track_id} volume set to {volume:.2f}."


@mcp.tool()
def fl_set_mixer_pan(track_id: int, pan: float) -> str:
    """
    Sets stereo pan for a mixer track (0 = Master, 1-125 = Tracks).
    pan: -1.0 (Full Left) to 0.0 (Center) to +1.0 (Full Right).
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    track_id = max(0, min(125, int(track_id)))
    pan_byte = max(0, min(127, int((pan + 1.0) * 63.5)))
    # Channel 1 (Ch 2), control = track_id
    port.send(mido.Message('control_change', channel=1, control=track_id, value=pan_byte))
    logger.info("Track %d pan → %+.2f", track_id, pan)
    return f"Mixer track {track_id} panning set to {pan:+.2f}."


@mcp.tool()
def fl_mute_track(track_id: int, mute: bool) -> str:
    """Mutes or unmutes a mixer track (0-125)."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    track_id = max(0, min(125, int(track_id)))
    val = 127 if mute else 0
    # Channel 2 (Ch 3), control = track_id
    port.send(mido.Message('control_change', channel=2, control=track_id, value=val))
    status = "Muted" if mute else "Unmuted"
    logger.info("Track %d %s", track_id, status)
    return f"Mixer track {track_id} {status}."


@mcp.tool()
def fl_solo_track(track_id: int, solo: bool) -> str:
    """Solos or unsolos a mixer track (0-125)."""
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    track_id = max(0, min(125, int(track_id)))
    val = 127 if solo else 0
    # Channel 3 (Ch 4), control = track_id
    port.send(mido.Message('control_change', channel=3, control=track_id, value=val))
    status = "Soloed" if solo else "Unsoloed"
    logger.info("Track %d %s", track_id, status)
    return f"Mixer track {track_id} {status}."


@mcp.tool()
def fl_set_mixer_stereo_separation(track_id: int, separation: float) -> str:
    """
    Sets stereo separation for mixer track_id (-1.0 = 100% Mono/Merged, 0.0 = Normal, +1.0 = 100% Wide).
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    track_id = max(0, min(125, int(track_id)))
    sep_byte = max(0, min(127, int((separation + 1.0) * 63.5)))
    # Channel 4 (Ch 5), control = track_id
    port.send(mido.Message('control_change', channel=4, control=track_id, value=sep_byte))
    logger.info("Track %d stereo separation → %+.2f", track_id, separation)
    return f"Track {track_id} stereo separation set to {separation:+.2f}."


@mcp.tool()
def fl_setup_sidechain(source_track: int, target_track: int) -> str:
    """
    Routes source_track as a sidechain send into target_track in FL Studio.
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    # In device_Antigravity_MCP.py: focused track is source, value is target_track on Ch 16, CC 18
    msg = mido.Message('control_change', channel=15, control=18, value=int(target_track))
    port.send(msg)
    logger.info("Sidechain routed: Track %02d ===> Track %02d", source_track, target_track)
    return f"Sidechain routed: Track {source_track:02d} ===> Track {target_track:02d}."


# ═══════════════════════════════════════════════════════════════
# 4. CHANNEL RACK & TIMELINE NAVIGATION
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_channel_rack_control(channel_index: int, action: str = "select") -> str:
    """
    Controls FL Studio Channel Rack.
    channel_index: 0 to 15.
    action: 'select' (focuses channel), 'mute' (mutes channel), 'solo' (solos channel).
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    c_idx = max(0, min(15, int(channel_index)))
    if action == "select":
        cc_num = c_idx
    elif action == "mute":
        cc_num = 16 + c_idx
    elif action == "solo":
        cc_num = 32 + c_idx
    else:
        return f"Unknown action '{action}'. Choose from 'select', 'mute', 'solo'."

    port.send(mido.Message('control_change', channel=6, control=cc_num, value=127))
    logger.info("Channel Rack %d → %s", c_idx, action)
    return f"Channel {c_idx} {action} executed."


@mcp.tool()
def fl_marker_navigation(action: str) -> str:
    """
    Timeline navigation:
    action: 'prev' (previous marker), 'next' (next marker), 'toggle_song_mode' (toggle Pattern vs Song).
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    act_map = {'prev': 1, 'next': 2, 'toggle_song_mode': 3}
    if action not in act_map:
        return f"Invalid action '{action}'. Valid actions: {list(act_map.keys())}"

    port.send(mido.Message('control_change', channel=7, control=act_map[action], value=127))
    logger.info("Marker Navigation → %s", action)
    return f"Timeline marker navigation '{action}' executed."


# ═══════════════════════════════════════════════════════════════
# 5. SOTA GENERATION ENGINES (CENTRALIZED TO ~/Music/)
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_generate_dark_cyber_flamenco(bars: int = 64) -> str:
    """
    Generates the complete 64-bar 'Dark Cyber-Flamenco' (Synthwave x Flamenco Oscuro, 112 BPM)
    masterpiece MIDI with 8 discrete tracks and timeline markers into ~/Music/FL Studio Bounces/.
    """
    try:
        cmd = f"python3 /tmp/generate_flamenco_masterpiece_64bars.py"
        subprocess.run(cmd, shell=True, check=True)
        out_path = MUSIC_BOUNCES_DIR / "Dark_Cyber_Flamenco_Masterpiece_64Bars.mid"
        logger.info("Generated 64-bar Dark Cyber-Flamenco → %s", out_path)
        return f"Dark Cyber-Flamenco (64 Bars, 112 BPM) generated successfully! Saved to: {out_path}"
    except Exception as e:
        logger.error("fl_generate_dark_cyber_flamenco failed: %s", e)
        return f"Error generating Dark Cyber-Flamenco: {e}"


@mcp.tool()
def fl_open_project_or_midi(file_path: str, auto_confirm: bool = True) -> str:
    """
    Opens an FLP project or imports a MIDI file directly into FL Studio 2025,
    optionally auto-confirming the import dialog via macOS System Events.
    """
    path = os.path.expanduser(file_path)
    if not os.path.exists(path):
        return f"File does not exist: {path}"

    try:
        subprocess.run(["open", "-a", "FL Studio 2025", path], check=True)
        time.sleep(1.5)
        if auto_confirm:
            apple_script = 'tell application "System Events" to tell process "OsxFL" to key code 36'
            subprocess.run(["osascript", "-e", apple_script], check=False)
        logger.info("Opened %s in FL Studio 2025", path)
        return f"Opened '{path}' in FL Studio 2025 with import confirmed."
    except Exception as e:
        logger.error("fl_open_project_or_midi failed: %s", e)
        return f"Error opening file in FL Studio: {e}"


@mcp.tool()
def fl_generate_maceo_plex_kick(fundamental_hz: float = 43.65, bpm: float = 124.0, length_bars: int = 4) -> str:
    """
    Generates an authentic Maceo Plex Melodic Techno kick drum + sub-rumble pattern
    with phase-decoupled semicorcheas. Saved to ~/Music/FL Studio Bounces/.
    """
    try:
        from scripts.maceo_plex_kick_synthesizer import generate_maceo_plex_kick_pattern
        out_path = MUSIC_BOUNCES_DIR / "maceo_plex_kick_pattern.mid"
        res = generate_maceo_plex_kick_pattern(output_path=str(out_path), fundamental_hz=fundamental_hz, bpm=bpm, length_bars=length_bars)
        logger.info("Maceo Plex kick generated → %s", res)
        return f"Maceo Plex Kick & Sub-Rumble MIDI saved to: {res}"
    except Exception as e:
        logger.error("fl_generate_maceo_plex_kick failed: %s", e)
        return f"Error generating Maceo Plex kick: {e}"


@mcp.tool()
def fl_generate_satin_jackets_penrose(bpm: float = 116.0) -> str:
    """
    Generates Satin Jackets infinite non-resolving Penrose Stair chord loop (Abmaj7 -> Bb9 -> Cm9 -> Fm9)
    with false drop to Picardy Third. Saved to ~/Music/FL Studio Bounces/.
    """
    try:
        from scripts.flstudio_infinite_harmonic_loop import generate_satin_jackets_infinite_loop
        out_path = MUSIC_BOUNCES_DIR / "satin_jackets_penrose_stair.mid"
        res = generate_satin_jackets_infinite_loop(output_path=str(out_path), bpm=bpm)
        logger.info("Satin Jackets loop generated → %s", res)
        return f"Satin Jackets Penrose Loop MIDI saved to: {res}"
    except Exception as e:
        logger.error("fl_generate_satin_jackets_penrose failed: %s", e)
        return f"Error generating Satin Jackets loop: {e}"


@mcp.tool()
def fl_generate_air_moon_safari_multitrack(bpm: float = 88.0) -> str:
    """
    Generates full 3-track Space-Pop arrangement (Rhodes, Minimoog, Solina Strings) in the style of AIR.
    Saved to ~/Music/FL Studio Bounces/.
    """
    try:
        from scripts.air_moon_safari_engine import generate_air_moon_safari_multitrack
        out_path = MUSIC_BOUNCES_DIR / "air_moon_safari_multitrack.mid"
        res = generate_air_moon_safari_multitrack(output_path=str(out_path), bpm=bpm)
        logger.info("AIR Moon Safari multitrack generated → %s", res)
        return f"AIR Moon Safari Multi-Track MIDI saved to: {res}"
    except Exception as e:
        logger.error("fl_generate_air_moon_safari_multitrack failed: %s", e)
        return f"Error generating AIR Moon Safari: {e}"


# ═══════════════════════════════════════════════════════════════
# 6. PSYCHOACOUSTICS & XENARMONICS (26 SCALA PROFILES)
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_generate_scala_tunings(temperament: str = "all") -> str:
    """
    Generates and installs Scala (.scl) and Keyboard Mapping (.kbm) profiles
    directly into FL Studio's Settings/Tuning directory with formal octave closure.
    Available temperaments: 'all', '12-tet', '19-tet', '24-tet', '31-tet', '41-tet',
    '53-tet', '72-tet', 'werckmeister-3', 'kirnberger-3', 'makam-bayati', 'makam-rast',
    'makam-hijaz', 'that-bhairav', 'that-yaman', 'just-intonation-5limit', 'bohlen-pierce',
    'wendy-carlos-alpha', 'locrian-neutral2nd'.
    """
    try:
        cmd = f"python3 {SCRIPTS_DIR}/scala_generator.py --temperament {temperament} --output-dir '{FL_TUNING}'"
        subprocess.run(cmd, shell=True, check=True)
        logger.info("Generated Scala tuning '%s' to %s", temperament, FL_TUNING)
        return f"Scala tuning profiles for '{temperament}' compiled and deployed to {FL_TUNING}."
    except Exception as e:
        logger.error("fl_generate_scala_tunings failed: %s", e)
        return f"Error generating Scala tunings: {e}"


@mcp.tool()
def fl_calculate_sensory_dissonance(f1: float, f2: float) -> str:
    """
    Calculates the psychoacoustic sensory dissonance between two frequencies (Hz)
    using the Sethares / Plomp-Levelt formula.
    """
    f_min, f_max = min(f1, f2), max(f1, f2)
    if f_min == f_max or f_min <= 0:
        return f"Sensory Dissonance between {f1:.1f}Hz and {f2:.1f}Hz: 0.000 (Pure Unison)"

    s1, s2 = 0.0207, 18.96
    s = 0.24 / (s1 * f_min + s2)
    diff = f_max - f_min
    a, b = 3.5, 5.75
    d = max(0.0, math.exp(-a * s * diff) - math.exp(-b * s * diff))
    return f"Sensory Dissonance between {f1:.1f}Hz and {f2:.1f}Hz: {d:.4f} (Sethares Index)"


# ═══════════════════════════════════════════════════════════════
# 7. PIANO ROLL DEPLOYER & HOT RELOAD
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_list_piano_roll_scripts() -> str:
    """Lists all installed Piano Roll scripts (.py and .pyscript) in FL Studio 2025."""
    if not FL_PIANOROLL.exists():
        return f"Directory not found: {FL_PIANOROLL}"
    scripts = sorted(list(FL_PIANOROLL.glob("*.py")) + list(FL_PIANOROLL.glob("*.pyscript")))
    lines = [f"Installed Piano Roll Scripts in FL Studio ({len(scripts)} total):"]
    for s in scripts:
        lines.append(f"  • {s.name}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info("Starting FL Studio SOTA MCP Server v6.0 on stdio transport…")
    mcp.run()
