#!/usr/bin/env python3
"""
Antigravity FL Studio Native CLI & Terminal Dashboard (v8.0 SOTA)
Provides high-exergy command-line and interactive REPL control over FL Studio 2025.
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import mcp_server

BANNER = r"""
 ██████╗███████╗   ██████╗ ███████╗ █████╗ ██╗     
██╔════╝██╔════╝   ██╔══██╗██╔════╝██╔══██╗██║     
██║     ███████╗   ██████╔╝█████╗  ███████║██║     
██║     ╚════██║   ██╔══██╗██╔══╝  ██╔══██║██║     
╚██████╗███████║██╗██║  ██║███████╗██║  ██║███████╗
 ╚═════╝╚══════╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚══════╝
    Antigravity FL Studio 2025 MCP Engine (v8.0)
"""


def print_status():
    print(BANNER)
    print("─── SYSTEM HEALTH & DIAGNOSTICS ───")
    print(mcp_server.fl_health_check())
    print("\n─── LIVE DAW TELEMETRY ───")
    telemetry = mcp_server.fl_get_live_telemetry()
    for k, v in telemetry.items():
        print(f"  • {k:18s}: {v}")
    print("\n─── BOUNCES CATALOG SUMMARY ───")
    cat = mcp_server.fl_catalog_music_bounces()
    print(f"  • Root: {cat.get('catalog_root')}")
    print(f"  • Total Centralized Assets: {cat.get('total_files')} files")


def interactive_repl():
    print(BANNER)
    print("Entering Antigravity Interactive REPL. Type 'help' for commands, 'exit' to quit.\n")
    while True:
        try:
            line = input("antigravity-fl> ").strip()
            if not line:
                continue
            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ["exit", "quit", "q"]:
                print("Exiting REPL.")
                break
            elif cmd == "help":
                print("""
Available Commands:
  play | pause | stop | record | loop | save | undo | redo
  bpm <60-187>
  vol <track_id> <0.0-1.0>
  pan <track_id> <-1.0 to 1.0>
  mute <track_id> [1|0]
  solo <track_id> [1|0]
  sidechain <src_track> <dst_track>
  select <track_id>
  window <mixer|channel_rack|playlist|piano_roll|browser>
  render-audio (renders 16-bar headless WAV preview)
  render-midi (generates 64-bar cyber-flamenco MIDI)
  apply-matrix (injects exergic mixer matrix into FL Studio)
  status (prints full system and telemetry diagnostics)
  test (runs system self-test)
  exit
""")
            elif cmd in ["play", "pause", "stop", "record", "loop", "save", "undo", "redo"]:
                print(mcp_server.fl_transport_control(cmd))
            elif cmd == "bpm" and args:
                print(mcp_server.fl_set_tempo(float(args[0])))
            elif cmd == "vol" and len(args) >= 2:
                print(mcp_server.fl_set_mixer_volume(int(args[0]), float(args[1])))
            elif cmd == "pan" and len(args) >= 2:
                print(mcp_server.fl_set_mixer_pan(int(args[0]), float(args[1])))
            elif cmd == "mute" and args:
                state = bool(int(args[1])) if len(args) > 1 else True
                print(mcp_server.fl_mute_track(int(args[0]), state))
            elif cmd == "solo" and args:
                state = bool(int(args[1])) if len(args) > 1 else True
                print(mcp_server.fl_solo_track(int(args[0]), state))
            elif cmd == "sidechain" and len(args) >= 2:
                print(mcp_server.fl_setup_sidechain(int(args[0]), int(args[1])))
            elif cmd == "select" and args:
                print(mcp_server.fl_select_mixer_track(int(args[0])))
            elif cmd == "window" and args:
                print(mcp_server.fl_toggle_window(args[0]))
            elif cmd == "render-audio":
                print(mcp_server.fl_render_headless_audio_preview())
            elif cmd == "render-midi":
                print(mcp_server.fl_generate_dark_cyber_flamenco(64))
            elif cmd == "apply-matrix":
                print(mcp_server.fl_apply_exergic_mixer_matrix())
            elif cmd == "status":
                print_status()
            elif cmd == "test":
                import json
                print(json.dumps(mcp_server.fl_run_self_test(), indent=2))
            else:
                print(f"Unknown command '{cmd}'. Type 'help' for instructions.")
        except KeyboardInterrupt:
            print("\nExiting REPL.")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Antigravity FL Studio CLI v8.0")
    parser.add_argument("command", nargs="?", default="status", help="Command to execute or 'repl' for interactive mode")
    parser.add_argument("args", nargs="*", help="Command arguments")

    parsed = parser.parse_args()
    cmd = parsed.command.lower()
    args = parsed.args

    if cmd in ["repl", "interactive"]:
        interactive_repl()
    elif cmd == "status":
        print_status()
    elif cmd in ["play", "pause", "stop", "record", "loop", "save", "undo", "redo"]:
        print(mcp_server.fl_transport_control(cmd))
    elif cmd == "bpm" and args:
        print(mcp_server.fl_set_tempo(float(args[0])))
    elif cmd == "vol" and len(args) >= 2:
        print(mcp_server.fl_set_mixer_volume(int(args[0]), float(args[1])))
    elif cmd == "pan" and len(args) >= 2:
        print(mcp_server.fl_set_mixer_pan(int(args[0]), float(args[1])))
    elif cmd == "sidechain" and len(args) >= 2:
        print(mcp_server.fl_setup_sidechain(int(args[0]), int(args[1])))
    elif cmd == "window" and args:
        print(mcp_server.fl_toggle_window(args[0]))
    elif cmd == "render-audio":
        print(mcp_server.fl_render_headless_audio_preview())
    elif cmd == "render-midi":
        print(mcp_server.fl_generate_dark_cyber_flamenco(64))
    elif cmd == "apply-matrix":
        print(mcp_server.fl_apply_exergic_mixer_matrix())
    elif cmd == "test":
        import json
        print(json.dumps(mcp_server.fl_run_self_test(), indent=2))
    else:
        interactive_repl()


if __name__ == "__main__":
    main()
