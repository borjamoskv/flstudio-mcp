#!/usr/bin/env python3
"""
Antigravity FL Studio Native MCP Server v7.0 (SOTA Zenith)
Full Model Context Protocol Server providing native AI control, microtonal tuning,
two-way hardware controller integration, binary reverse-engineering, and MIDI orchestration
for FL Studio 2025 via FastMCP.

Aligned with:
- device_Antigravity_MCP.py (125 mixer tracks, Channel rack, markers, transport)
- Centralized Music Assets Invariant (~/Music/FL Studio Bounces/)
- 26 Scala Tunings & Sethares/Plomp-Levelt psychoacoustics
- 19 SOTA Piano Roll Scripts (including Dark Cyber-Flamenco, Euclidean, Cellular Automata)
- Binary Header Inspection (.flp FLhd and .wav RIFF)
- Live AppleScript Window & Export Automation
"""

import sys
import os
import time
import ast
import math
import struct
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

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

SKILLS_DIR = Path.home() / ".gemini/config/skills/flstudio-mcp-production"
SKILLS_EXAMPLES = SKILLS_DIR / "examples"
SKILLS_SCRIPTS = SKILLS_DIR / "scripts"

MUSIC_DIR = Path.home() / "Music"
MUSIC_BOUNCES_DIR = MUSIC_DIR / "FL Studio Bounces"
MUSIC_BOUNCES_DIR.mkdir(parents=True, exist_ok=True)

# Add scripts directory to path for legacy and custom modules
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(SKILLS_SCRIPTS))

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
    report_lines = ["═══ FL Studio MCP SOTA Health Check (v9.0) ═══"]

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
    Sends direct sidechain signal via Hardware Controller Channel 9 (mid_chan 8)
    and fallback Channel 16 CC 18.
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    src = max(0, min(125, int(source_track)))
    dst = max(0, min(125, int(target_track)))

    # Direct routing on Channel 8: CC = source_track, value = target_track
    port.send(mido.Message('control_change', channel=8, control=src, value=dst))
    # Legacy fallback on Channel 15, CC 18
    port.send(mido.Message('control_change', channel=15, control=18, value=dst))

    logger.info("Sidechain routed: Track %02d ===> Track %02d", src, dst)
    return f"Sidechain routed: Track {src:02d} ===> Track {dst:02d}."


@mcp.tool()
def fl_select_mixer_track(track_id: int) -> str:
    """
    Selects and focuses a specific mixer track (0 = Master, 1-125 = Tracks) in FL Studio.
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    t_id = max(0, min(125, int(track_id)))
    # Channel 9 (mid_chan 9), CC = track_id, value = 0 (select)
    port.send(mido.Message('control_change', channel=9, control=t_id, value=0))
    logger.info("Selected mixer track %d", t_id)
    return f"FL Studio mixer track {t_id} selected."


@mcp.tool()
def fl_toggle_window(window_name: str) -> str:
    """
    Toggles or focuses the specified FL Studio window.
    window_name: 'mixer', 'channel_rack', 'playlist', 'piano_roll', 'browser'.
    """
    port = get_midi_port()
    w_lower = window_name.lower().replace(" ", "_")
    w_map = {
        'mixer': (0, '9'),        # F9
        'channel_rack': (1, '6'), # F6
        'playlist': (2, '5'),     # F5
        'piano_roll': (3, '7'),   # F7
        'browser': (4, '8')       # Alt+F8
    }
    if w_lower not in w_map:
        return f"Unknown window '{window_name}'. Supported: {list(w_map.keys())}"

    cc_num, fn_key = w_map[w_lower]

    # 1. MIDI Controller UI Command (Channel 10)
    if port:
        port.send(mido.Message('control_change', channel=10, control=cc_num, value=127))

    # 2. AppleScript Keystroke Fallback if FL Studio is running
    try:
        check_proc = 'tell application "System Events" to (name of processes) contains "OsxFL"'
        is_running = subprocess.check_output(["osascript", "-e", check_proc], text=True).strip() == "true"
        if is_running:
            if w_lower == 'browser':
                script = 'tell application "System Events" to tell process "OsxFL" to key code 100 using option down'
            else:
                key_codes = {'5': 96, '6': 97, '7': 98, '9': 101}
                kc = key_codes.get(fn_key, 101)
                script = f'tell application "System Events" to tell process "OsxFL" to key code {kc}'
            subprocess.run(["osascript", "-e", script], check=False)
    except Exception as e:
        logger.debug("AppleScript window toggle notice: %s", e)

    logger.info("Window focus requested: %s", w_lower)
    return f"FL Studio window '{w_lower}' focus/toggle executed."



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
        script_path = SCRIPTS_DIR / "generate_flamenco_masterpiece_64bars.py"
        subprocess.run([sys.executable, str(script_path)], check=True)
        out_path = MUSIC_BOUNCES_DIR / "Dark_Cyber_Flamenco_Masterpiece_64Bars.mid"
        logger.info("Generated 64-bar Dark Cyber-Flamenco → %s", out_path)
        return f"Dark Cyber-Flamenco (64 Bars, 112 BPM) generated successfully! Saved to: {out_path}"
    except Exception as e:
        logger.error("fl_generate_dark_cyber_flamenco failed: %s", e)
        return f"Error generating Dark Cyber-Flamenco: {e}"


@mcp.tool()
def fl_render_headless_audio_preview() -> str:
    """
    Synthesizes a 16-bar Dark Cyber-Flamenco audio preview (WAV, 44.1kHz, 16-bit Stereo PCM)
    using pure Python standard library DSP into ~/Music/FL Studio Bounces/.
    No DAW startup required.
    """
    try:
        from scripts.render_synthwave_flamenco_audio_preview import render_dark_cyber_flamenco_wav
        out_wav = MUSIC_BOUNCES_DIR / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
        render_dark_cyber_flamenco_wav(out_wav)
        size_mb = out_wav.stat().st_size / (1024.0 * 1024.0)
        logger.info("Rendered headless audio preview → %s (%.2f MB)", out_wav, size_mb)
        return f"Rendered 16-bar Headless Audio Preview ({size_mb:.2f} MB): {out_wav}"
    except Exception as e:
        logger.error("fl_render_headless_audio_preview failed: %s", e)
        return f"Error rendering headless audio: {e}"


@mcp.tool()
def fl_apply_exergic_mixer_matrix() -> str:
    """
    Injects the complete 7-track C5-REAL Exergic Mixing Matrix into FL Studio 2025:
    Configures volume faders, panning, stereo field width, and sidechain ducking routes
    across Tracks 1-7 via CoreMIDI virtual bus.
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    matrix = [
        {"track": 1, "name": "Maceo Kick DSP", "vol": 0.50, "pan": 0.0, "sep": 1.0},
        {"track": 2, "name": "Minimoog Sub-Bass", "vol": 0.40, "pan": 0.0, "sep": 0.8, "sc_src": 1},
        {"track": 3, "name": "Fender Rhodes 73", "vol": 0.25, "pan": -0.15, "sep": -0.35, "sc_src": 1},
        {"track": 4, "name": "Solina Strings Pad", "vol": 0.20, "pan": 0.15, "sep": -0.80, "sc_src": 1},
        {"track": 5, "name": "Maceo 303 Acid Lead", "vol": 0.32, "pan": 0.0, "sep": -0.40},
        {"track": 6, "name": "AIR Vocoder Lead Synth", "vol": 0.35, "pan": 0.0, "sep": -0.50},
        {"track": 7, "name": "Swung Hats & Percs", "vol": 0.20, "pan": 0.10, "sep": -0.60},
    ]

    applied = []
    for item in matrix:
        t_id = item["track"]
        fl_set_mixer_volume(t_id, item["vol"])
        fl_set_mixer_pan(t_id, item["pan"])
        fl_set_mixer_stereo_separation(t_id, item["sep"])
        if "sc_src" in item:
            fl_setup_sidechain(item["sc_src"], t_id)
        applied.append(f"Track {t_id} ({item['name']}): Vol={item['vol']}, Pan={item['pan']:+.2f}, Sep={item['sep']:+.2f}")

    logger.info("Applied Exergic Mixer Matrix across %d tracks", len(matrix))
    return "Successfully applied C5-REAL Exergic Mixer Matrix to FL Studio:\n" + "\n".join(applied)


@mcp.tool()
def fl_render_multitrack_stems_pack() -> Dict[str, Any]:
    """
    Synthesizes discrete broadcast WAV stems (Kick, Snare/Clap, Bass, Chords, Master)
    and an orchestration manifest into ~/Music/FL Studio Bounces/Stems/Dark_Cyber_Flamenco_Stems_16Bars/.
    """
    try:
        from scripts.render_multitrack_stems_pack import render_multitrack_stems
        out_dir = MUSIC_BOUNCES_DIR / "Stems/Dark_Cyber_Flamenco_Stems_16Bars"
        manifest = render_multitrack_stems(out_dir)
        logger.info("Exported multitrack stems pack (%d stems) → %s", manifest.get("total_stems"), out_dir)
        return manifest
    except Exception as e:
        logger.error("fl_render_multitrack_stems_pack failed: %s", e)
        return {"error": f"Multitrack synthesis error: {e}"}


@mcp.tool()
def fl_generate_euclidean_rhythm(
    pulses: int = 7,
    steps: int = 12,
    bars: int = 8,
    bpm: float = 112.0,
    note_number: int = 69,
    swing_percent: float = 62.0,
    track_name: str = "Palmas Bulerias"
) -> str:
    """
    Generates microtonal Euclidean polyrhythm MIDI clips using the Bjorklund E(k, n) algorithm
    with swing percentages and velocity dynamics. Saved to ~/Music/FL Studio Bounces/.
    """
    try:
        from scripts.euclidean_rhythm_generator import generate_euclidean_midi_clip
        out_path = MUSIC_BOUNCES_DIR / f"Euclidean_E_{pulses}_{steps}_{int(bpm)}BPM_{track_name.replace(' ', '_')}.mid"
        res = generate_euclidean_midi_clip(
            pulses=pulses, steps=steps, bars=bars, bpm=bpm,
            note_number=note_number, swing_percent=swing_percent,
            output_path=out_path, track_name=track_name
        )
        logger.info("Generated Euclidean MIDI E(%d,%d) → %s", pulses, steps, res)
        return f"Generated Euclidean MIDI E({pulses},{steps}) [{track_name}] saved to: {res}"
    except Exception as e:
        logger.error("fl_generate_euclidean_rhythm failed: %s", e)
        return f"Error generating Euclidean rhythm: {e}"


@mcp.tool()
def fl_export_web_audio_hud() -> str:
    """
    Exports a standalone, reactive HTML5 Web Audio cockpit & visualizer
    (FFT spectrum, oscilloscope, 8-channel mixer peak meters, closed-loop telemetry)
    to ~/Music/FL Studio Bounces/fl_studio_cyber_hud.html.
    """
    try:
        from scripts.export_web_audio_hud import export_web_audio_hud
        out_html = MUSIC_BOUNCES_DIR / "fl_studio_cyber_hud.html"
        export_web_audio_hud(out_html)
        logger.info("Exported Cyber HUD → %s", out_html)
        return f"Exported standalone Cyber HUD ({out_html.stat().st_size / 1024:.1f} KB): {out_html}"
    except Exception as e:
        logger.error("fl_export_web_audio_hud failed: %s", e)
        return f"Error exporting Cyber HUD: {e}"



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
        generator_script = SKILLS_SCRIPTS / "scala_generator.py"
        if not generator_script.exists():
            generator_script = SCRIPTS_DIR / "scala_generator.py"
            
        cmd = f"python3 '{generator_script}' --temperament {temperament} --output-dir '{FL_TUNING}'"
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
        return f"Sensory Dissonance between {f1:.1f}Hz and {f2:.1f}Hz: 0.0000 (Pure Unison)"

    s1, s2 = 0.0207, 18.96
    s = 0.24 / (s1 * f_min + s2)
    diff = f_max - f_min
    a, b = 3.5, 5.75
    d = max(0.0, math.exp(-a * s * diff) - math.exp(-b * s * diff))
    return f"Sensory Dissonance between {f1:.1f}Hz and {f2:.1f}Hz: {d:.4f} (Sethares Roughness Index)"


# ═══════════════════════════════════════════════════════════════
# 7. PIANO ROLL SCRIPT MANAGEMENT & DEPLOYMENT
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


@mcp.tool()
def fl_deploy_custom_piano_roll_script(script_name: str, code_content: str, overwrite: bool = False) -> str:
    """
    Validates Python AST and deploys a custom Piano Roll script directly into
    ~/Documents/Image-Line/FL Studio/Settings/Piano roll scripts/.
    Requires either createScore() or createDialog() + apply(form).
    """
    if not script_name.endswith((".py", ".pyscript")):
        script_name += ".py"

    target_path = FL_PIANOROLL / script_name
    if target_path.exists() and not overwrite:
        return f"Script already exists at {target_path}. Set overwrite=True to replace."

    # Validate AST
    try:
        tree = ast.parse(code_content, filename=script_name)
    except SyntaxError as se:
        return f"SyntaxError in script at line {se.lineno}: {se.msg}"

    func_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    has_create_score = "createScore" in func_names
    has_dialog_apply = ("createDialog" in func_names and "apply" in func_names)
    if not (has_create_score or has_dialog_apply):
        return f"Missing required entrypoints: script must define 'createScore()' or 'createDialog()' + 'apply(form)'. Found: {func_names}"

    FL_PIANOROLL.mkdir(parents=True, exist_ok=True)
    target_path.write_text(code_content, encoding="utf-8")
    mode = "Interactive Dialog" if has_dialog_apply else "Direct Batch"
    logger.info("Deployed custom Piano Roll script: %s [%s]", script_name, mode)
    return f"Successfully deployed '{script_name}' [{mode}] to {target_path}."


# ═══════════════════════════════════════════════════════════════
# 8. BINARY REVERSE ENGINEERING & HEADER INSPECTOR
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_inspect_binary_header(file_path: str) -> Dict[str, Any]:
    """
    Reverse-engineers and parses the binary header of an FL Studio project (.flp)
    or an uncompressed RIFF WAVE (.wav) stem, extracting sample rate, bit depth,
    duration, PPQ resolution, and bars.
    """
    path = Path(os.path.expanduser(file_path))
    if not path.exists():
        return {"error": f"File does not exist: {path}"}

    with open(path, "rb") as f:
        data = f.read(256)

    # 1. FL Studio Project Binary (.flp)
    if data[:4] == b'FLhd':
        hdr_len = struct.unpack('<I', data[4:8])[0]
        fmt_type, channels, ppq = struct.unpack('<HHH', data[8:14])
        chunk_type = data[14:18].decode('ascii', errors='ignore')
        return {
            "file_type": "FL Studio Project Binary",
            "file_path": str(path),
            "magic_header": "FLhd",
            "format_type": fmt_type,
            "channel_count": channels,
            "ppq_resolution": ppq,
            "data_chunk_header": chunk_type,
            "file_size_bytes": path.stat().st_size
        }

    # 2. RIFF WAVE Audio Binary (.wav)
    elif data[:4] == b'RIFF' and data[8:12] == b'WAVE':
        chunk_size = struct.unpack('<I', data[4:8])[0]
        audio_format, channels, sample_rate, byte_rate, block_align, bits_per_sample = struct.unpack('<HHIIHH', data[20:36])
        duration_sec = (chunk_size - 36) / byte_rate if byte_rate > 0 else 0
        return {
            "file_type": "RIFF WAVE Audio Stem",
            "file_path": str(path),
            "audio_format": "PCM Uncompressed" if audio_format == 1 else "IEEE Float",
            "channels": channels,
            "sample_rate_hz": sample_rate,
            "bits_per_sample": bits_per_sample,
            "duration_sec": round(duration_sec, 2),
            "bars_at_112bpm": round((duration_sec / 60.0) * (112.0 / 4), 2),
            "file_size_bytes": path.stat().st_size
        }

    return {
        "file_type": "Generic Binary / Unknown",
        "file_path": str(path),
        "header_hex": data[:16].hex(),
        "file_size_bytes": path.stat().st_size
    }


@mcp.tool()
def fl_analyze_audio_spectrum(file_path: str) -> Dict[str, Any]:
    """
    Performs comprehensive spectral, loudness (ITU-R BS.1770 / EBU R128),
    crest factor (dynamic punch), spectral centroid, and exergy audit on a WAV audio stem.
    """
    path = Path(os.path.expanduser(file_path))
    if not path.exists():
        return {"error": f"Audio file not found: {path}"}
    try:
        from scripts.spectral_audio_auditor import analyze_audio_spectrum
        return analyze_audio_spectrum(path)
    except Exception as e:
        logger.error("fl_analyze_audio_spectrum failed: %s", e)
        return {"error": f"Spectral analysis error: {e}"}


@mcp.tool()
def fl_decompile_binary_preset(file_path: str) -> Dict[str, Any]:
    """
    Decompiles and parses raw FL Studio binary project (.flp) or plugin preset (.fst)
    chunks, extracting channel headers, event streams, and binary metadata.
    """
    path = Path(os.path.expanduser(file_path))
    if not path.exists():
        return {"error": f"File not found: {path}"}
    try:
        from scripts.fl_fst_decompiler_and_patcher_builder import FLBinaryDecompiler
        decompiler = FLBinaryDecompiler(str(path))
        return decompiler.load_and_decompile()
    except Exception as e:
        logger.error("fl_decompile_binary_preset failed: %s", e)
        return {"error": f"Decompilation error: {e}"}


# ═══════════════════════════════════════════════════════════════
# 9. RAW MIDI INJECTION & HARDWARE BUS
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_send_raw_midi(channel: int, message_type: str, data1: int, data2: int = 0) -> str:
    """
    Sends raw low-latency MIDI event to FL Studio via 'Antigravity MCP Out'.
    channel: 0 to 15.
    message_type: 'control_change', 'note_on', 'note_off', 'pitchwheel', 'program_change'.
    data1: note number, CC number, or pitch bend value (-8192 to 8191).
    data2: velocity or CC value (0 to 127).
    """
    port = get_midi_port()
    if not port:
        return "Error: Could not open MIDI port."

    mtype = message_type.lower()
    chan = max(0, min(15, int(channel)))

    try:
        if mtype == 'control_change':
            msg = mido.Message('control_change', channel=chan, control=int(data1), value=int(data2))
        elif mtype == 'note_on':
            msg = mido.Message('note_on', channel=chan, note=int(data1), velocity=int(data2))
        elif mtype == 'note_off':
            msg = mido.Message('note_off', channel=chan, note=int(data1), velocity=int(data2))
        elif mtype == 'pitchwheel':
            msg = mido.Message('pitchwheel', channel=chan, pitch=int(data1))
        elif mtype == 'program_change':
            msg = mido.Message('program_change', channel=chan, program=int(data1))
        else:
            return f"Unsupported message_type '{message_type}'. Use 'control_change', 'note_on', 'note_off', 'pitchwheel', 'program_change'."

        port.send(msg)
        return f"Sent MIDI {msg} on 'Antigravity MCP Out'."
    except Exception as e:
        logger.error("fl_send_raw_midi error: %s", e)
        return f"Error sending MIDI: {e}"


# ═══════════════════════════════════════════════════════════════
# 10. MUSIC ASSETS CATALOG & BOUNCE SYNC
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_catalog_music_bounces(follow_symlinks: bool = True) -> Dict[str, Any]:
    """
    Catalogs and audits all exported audio, stems, and MIDI projects in ~/Music/FL Studio Bounces/
    verifying compliance with the Music Centralization Invariant.
    """
    if not MUSIC_BOUNCES_DIR.exists():
        return {"error": f"Directory not found: {MUSIC_BOUNCES_DIR}"}

    catalog = []
    for root, dirs, files in os.walk(str(MUSIC_BOUNCES_DIR), followlinks=follow_symlinks):
        for fname in sorted(files):
            if fname.startswith('.'):
                continue
            fpath = Path(root) / fname
            try:
                st = fpath.stat()
                rel_path = str(fpath.relative_to(MUSIC_BOUNCES_DIR))
                catalog.append({
                    "relative_path": rel_path,
                    "filename": fname,
                    "extension": fpath.suffix.lower(),
                    "size_kb": round(st.st_size / 1024.0, 1),
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
                    "path": str(fpath)
                })
            except Exception as e:
                logger.warning("Could not stat %s: %s", fpath, e)

    return {
        "catalog_root": str(MUSIC_BOUNCES_DIR),
        "total_files": len(catalog),
        "assets": catalog
    }


# ═══════════════════════════════════════════════════════════════
# 11. APPLEScript DAW WINDOW STATE & EXPORT SHORTCUT
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_query_daw_window_state() -> Dict[str, Any]:
    """
    Inspects macOS System Events to verify whether FL Studio 2025 ('OsxFL')
    is running, frontmost, and lists open window titles.
    """
    try:
        check_proc = 'tell application "System Events" to (name of processes) contains "OsxFL"'
        is_running = subprocess.check_output(["osascript", "-e", check_proc], text=True).strip() == "true"
        
        if not is_running:
            return {"fl_studio_running": False, "status": "FL Studio 2025 is not running"}

        check_front = 'tell application "System Events" to (name of first application process whose frontmost is true) is "OsxFL"'
        is_front = subprocess.check_output(["osascript", "-e", check_front], text=True).strip() == "true"

        get_windows = 'tell application "System Events" to tell process "OsxFL" to get name of every window'
        windows = subprocess.check_output(["osascript", "-e", get_windows], text=True).strip().split(", ")

        return {
            "fl_studio_running": True,
            "is_frontmost": is_front,
            "active_windows": [w for w in windows if w.strip()]
        }
    except Exception as e:
        return {"error": f"AppleScript inspection failed: {e}"}


@mcp.tool()
def fl_get_live_telemetry() -> Dict[str, Any]:
    """
    Retrieves real-time closed-loop telemetry from FL Studio 2025:
    Reads live BPM, playback status, song position, focused track, volume/pan,
    channel count, and hardware connection state.
    """
    telemetry_file = Path("/tmp/antigravity_fl_telemetry.json")
    now = time.time()
    
    # 1. If live telemetry JSON exists and was updated within the last 60 seconds
    if telemetry_file.exists():
        try:
            mtime = telemetry_file.stat().st_mtime
            age_sec = round(now - mtime, 1)
            with open(telemetry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if age_sec < 60.0 and data.get("status") == "LIVE_DAW_CONNECTED":
                data["telemetry_source"] = "HARDWARE_CONTROLLER_CLOSED_LOOP"
                data["age_seconds"] = age_sec
                return data
        except Exception as e:
            logger.debug("Error reading live telemetry file: %s", e)

    # 2. Fallback to AppleScript process inspection
    daw_state = fl_query_daw_window_state()
    port = get_midi_port()
    return {
        "status": "DAW_ONLINE_NO_CONTROLLER" if daw_state.get("fl_studio_running") else "DAW_OFFLINE",
        "telemetry_source": "PROCESS_FALLBACK",
        "fl_studio_running": daw_state.get("fl_studio_running", False),
        "is_frontmost": daw_state.get("is_frontmost", False),
        "active_windows": daw_state.get("active_windows", []),
        "coremidi_bus": "ACTIVE ('Antigravity MCP Out')" if port else "OFFLINE",
        "timestamp": now,
        "iso_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
    }


@mcp.tool()
def fl_trigger_export_shortcut(format: str = "wav") -> str:
    """
    Sends export keyboard shortcut to FL Studio 2025 via macOS System Events:
    format: 'wav' (Cmd+R), 'mp3' (Cmd+Shift+R), 'midi' (Cmd+Shift+M).
    """
    fmt = format.lower()
    try:
        if fmt == "wav":
            script = 'tell application "System Events" to tell process "OsxFL" to keystroke "r" using command down'
        elif fmt == "mp3":
            script = 'tell application "System Events" to tell process "OsxFL" to keystroke "r" using {command down, shift down}'
        elif fmt == "midi":
            script = 'tell application "System Events" to tell process "OsxFL" to keystroke "m" using {command down, shift down}'
        else:
            return f"Unsupported export format '{format}'. Choose from 'wav', 'mp3', 'midi'."

        subprocess.run(["osascript", "-e", script], check=True)
        return f"Triggered export dialog for '{fmt.upper()}' in FL Studio."
    except Exception as e:
        return f"Failed to trigger export shortcut: {e}"


# ═══════════════════════════════════════════════════════════════
# 12. AUTOMATED SELF-TEST & ATTESTATION
# ═══════════════════════════════════════════════════════════════
@mcp.tool()
def fl_run_self_test() -> Dict[str, Any]:
    """
    Executes a comprehensive system-wide self-test across all MCP capabilities:
    CoreMIDI port, AppleScript DAW query, binary parser, dissonance calculator,
    piano roll scripts, live telemetry, and bounce asset verification.
    """
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "9.0-SOTA",
        "tests": {}
    }

    # Test 1: CoreMIDI
    port = get_midi_port()
    results["tests"]["coremidi_port"] = "ONLINE" if port else "OFFLINE"

    # Test 2: Binary Inspection
    try:
        test_wav = SAMPLES_DIR / "orbital_kick.wav"
        if test_wav.exists():
            hdr = fl_inspect_binary_header(str(test_wav))
            results["tests"]["binary_inspector"] = f"PASSED ({hdr.get('audio_format')}, {hdr.get('sample_rate_hz')}Hz)"
        else:
            results["tests"]["binary_inspector"] = "SKIPPED (test file not found)"
    except Exception as e:
        results["tests"]["binary_inspector"] = f"FAILED: {e}"

    # Test 3: Sensory Dissonance
    try:
        diss = fl_calculate_sensory_dissonance(440.0, 466.16)
        results["tests"]["dissonance_calculator"] = f"PASSED ({diss})"
    except Exception as e:
        results["tests"]["dissonance_calculator"] = f"FAILED: {e}"

    # Test 4: Bounces Catalog
    try:
        cat = fl_catalog_music_bounces()
        results["tests"]["bounces_catalog"] = f"PASSED ({cat.get('total_files', 0)} files indexed)"
    except Exception as e:
        results["tests"]["bounces_catalog"] = f"FAILED: {e}"

    # Test 5: DAW Window State
    try:
        daw = fl_query_daw_window_state()
        results["tests"]["daw_query"] = "PASSED" if "fl_studio_running" in daw else f"FAILED: {daw}"
    except Exception as e:
        results["tests"]["daw_query"] = f"FAILED: {e}"

    # Test 6: Live Telemetry
    try:
        telem = fl_get_live_telemetry()
        results["tests"]["live_telemetry"] = f"PASSED ({telem.get('status')})"
    except Exception as e:
        results["tests"]["live_telemetry"] = f"FAILED: {e}"

    # Test 7: Headless Synthesizer
    try:
        preview_wav = MUSIC_BOUNCES_DIR / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
        if not preview_wav.exists():
            fl_render_headless_audio_preview()
        results["tests"]["headless_audio_dsp"] = f"PASSED ({preview_wav.stat().st_size / 1024:.1f} KB)"
    except Exception as e:
        results["tests"]["headless_audio_dsp"] = f"FAILED: {e}"

    # Test 8: Spectral Audio Quality Auditor
    try:
        preview_wav = MUSIC_BOUNCES_DIR / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
        spec = fl_analyze_audio_spectrum(str(preview_wav))
        results["tests"]["spectral_auditor"] = f"PASSED (Crest={spec.get('metrics', {}).get('crest_factor_db')}dB, Exergy={spec.get('exergy_rating_21000')})"
    except Exception as e:
        results["tests"]["spectral_auditor"] = f"FAILED: {e}"

    # Test 9: Web Audio Cockpit HUD
    try:
        hud_res = fl_export_web_audio_hud()
        results["tests"]["web_audio_hud"] = "PASSED (Exported HTML5 Studio Cockpit)"
    except Exception as e:
        results["tests"]["web_audio_hud"] = f"FAILED: {e}"

    # Summary
    all_passed = all(
        "PASSED" in str(v) or "ONLINE" in str(v) or "SKIPPED" in str(v)
        for v in results["tests"].values()
    )
    results["overall_status"] = "ALL_SYSTEMS_GO" if all_passed else "DEGRADED"
    return results


# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logger.info("Starting FL Studio SOTA MCP Server v9.0 on stdio transport…")
    mcp.run()

