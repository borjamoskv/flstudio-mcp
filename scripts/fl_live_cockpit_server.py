#!/usr/bin/env python3
"""
FL Studio Live Bidirectional Web Cockpit & Telemetry Server — C5-REAL SOTA
════════════════════════════════════════════════════════════════════════════
Zero-dependency HTTP/SSE daemon providing real-time bidirectional tactile
control between modern web browsers (Safari, Chrome) and FL Studio 2025:

Endpoints:
- GET  /                     : Serves interactive Cyber HUD Cockpit
- GET  /audio/<filename>     : Streams master bounces and multitrack stems
- GET  /api/telemetry        : Real-time closed-loop DAW telemetry stream
- POST /api/control          : Dispatches instant CoreMIDI CC / transport events
- POST /api/tool             : Executes procedural MCP sound design tools
- GET  /api/status           : Server health, active ports, and connection status
"""

import os
import sys
import json
import time
import mimetypes
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, Optional

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

MUSIC_BOUNCES_DIR = Path.home() / "Music" / "FL Studio Bounces"
TELEMETRY_PATH = Path("/tmp/antigravity_fl_telemetry.json")
DEFAULT_PORT = 8844

_server_instance: Optional["ThreadingServer"] = None
_server_thread: Optional[threading.Thread] = None


class ThreadingServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class CockpitHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy standard HTTP access logs
        pass

    def _send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            hud_path = MUSIC_BOUNCES_DIR / "fl_studio_cyber_hud.html"
            if not hud_path.exists():
                from scripts.export_web_audio_hud import export_cyber_hud
                export_cyber_hud()
            content = hud_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
            return

        if path == "/api/status":
            self._send_json({
                "status": "ONLINE",
                "server": "Antigravity FL Studio Cockpit Server v10.0",
                "bounces_dir": str(MUSIC_BOUNCES_DIR),
                "timestamp": time.time()
            })
            return

        if path == "/api/telemetry":
            telem_data: Dict[str, Any] = {}
            if TELEMETRY_PATH.exists():
                try:
                    telem_data = json.loads(TELEMETRY_PATH.read_text(encoding="utf-8"))
                except Exception as e:
                    telem_data = {"error": f"Failed to read telemetry: {e}"}
            else:
                telem_data = {
                    "status": "DAW_OFFLINE",
                    "info": "FL Studio closed-loop telemetry file not yet active"
                }
            self._send_json(telem_data)
            return

        # Audio file streaming
        if path.startswith("/audio/"):
            rel_path = path[len("/audio/"):]
            file_path = (MUSIC_BOUNCES_DIR / rel_path).resolve()
            # Prevent path traversal
            if not str(file_path).startswith(str(MUSIC_BOUNCES_DIR.resolve())):
                self.send_error(403, "Access Denied")
                return
            if not file_path.exists() or file_path.is_dir():
                self.send_error(404, "File Not Found")
                return

            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = "application/octet-stream"

            file_size = file_path.stat().st_size
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
            return

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len)
        try:
            payload = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            self._send_json({"error": "Invalid JSON payload"}, status=400)
            return

        if self.path == "/api/control":
            # Dispatch command to mcp_server CoreMIDI
            import mcp_server
            action = payload.get("action", "").lower()
            res_msg = "UNKNOWN_ACTION"

            if action == "play":
                res_msg = mcp_server.fl_transport_control("play")
            elif action == "stop":
                res_msg = mcp_server.fl_transport_control("stop")
            elif action == "pause":
                res_msg = mcp_server.fl_transport_control("pause")
            elif action == "tempo":
                bpm = float(payload.get("bpm", 120.0))
                res_msg = mcp_server.fl_set_tempo(bpm)
            elif action == "volume":
                track = int(payload.get("track", 0))
                vol = float(payload.get("value", 0.8))
                res_msg = mcp_server.fl_set_mixer_volume(track, vol)
            elif action == "pan":
                track = int(payload.get("track", 0))
                pan = float(payload.get("value", 0.0))
                res_msg = mcp_server.fl_set_mixer_pan(track, pan)
            elif action == "mute":
                track = int(payload.get("track", 0))
                res_msg = mcp_server.fl_mute_track(track)
            elif action == "solo":
                track = int(payload.get("track", 0))
                res_msg = mcp_server.fl_solo_track(track)
            elif action == "sidechain":
                src = int(payload.get("source", 1))
                dst = int(payload.get("target", 2))
                res_msg = mcp_server.fl_setup_sidechain(src, dst)
            elif action == "window":
                win = str(payload.get("target", "mixer"))
                res_msg = mcp_server.fl_toggle_window(win)
            else:
                self._send_json({"error": f"Unsupported action: {action}"}, status=400)
                return

            self._send_json({"status": "SUCCESS", "action": action, "response": res_msg})
            return

        if self.path == "/api/tool":
            import mcp_server
            tool_name = payload.get("tool", "")
            tool_args = payload.get("args", {})
            if hasattr(mcp_server, tool_name):
                fn = getattr(mcp_server, tool_name)
                try:
                    out = fn(**tool_args)
                    self._send_json({"status": "SUCCESS", "tool": tool_name, "result": out})
                except Exception as e:
                    self._send_json({"status": "ERROR", "tool": tool_name, "error": str(e)}, status=500)
            else:
                self._send_json({"status": "ERROR", "error": f"Tool '{tool_name}' not found"}, status=404)
            return

        self.send_error(404, "Not Found")


def start_cockpit_server(port: int = DEFAULT_PORT) -> Dict[str, Any]:
    """Starts the Cockpit HTTP server in a background daemon thread."""
    global _server_instance, _server_thread
    if _server_instance is not None:
        return {
            "status": "ALREADY_RUNNING",
            "url": f"http://127.0.0.1:{_server_instance.server_port}",
            "port": _server_instance.server_port
        }

    try:
        _server_instance = ThreadingServer(("127.0.0.1", port), CockpitHandler)
        _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True)
        _server_thread.start()
        return {
            "status": "STARTED",
            "url": f"http://127.0.0.1:{port}",
            "port": port
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e)
        }


def stop_cockpit_server() -> Dict[str, Any]:
    """Stops the running Cockpit HTTP server."""
    global _server_instance, _server_thread
    if _server_instance is None:
        return {"status": "NOT_RUNNING"}

    try:
        _server_instance.shutdown()
        _server_instance.server_close()
        _server_instance = None
        _server_thread = None
        return {"status": "STOPPED"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    res = start_cockpit_server(p)
    print(json.dumps(res, indent=2))
    print(f"Server live at http://127.0.0.1:{p}. Press Ctrl+C to terminate.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_cockpit_server()
        print("Server shutdown cleanly.")
