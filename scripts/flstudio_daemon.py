#!/usr/bin/env python3
"""
Antigravity MCP Daemon for FL Studio 21+
Keeps virtual CoreMIDI port 'Antigravity MCP Out' active continuously in background.
"""

import time
import signal
import sys
import mido

running = True

def signal_handler(sig, frame):
    global running
    print("\n[MCP Daemon] Shutting down virtual MIDI port...")
    running = False

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    port_name = "Antigravity MCP Out"
    try:
        outport = mido.open_output(port_name, virtual=True)
        print(f"[MCP Daemon] Virtual MIDI Port '{port_name}' ACTIVE and listening.")
        print("[MCP Daemon] FL Studio 2025 will auto-bind to this port via deviceNameMatches.")
        
        while running:
            time.sleep(1)
            
        outport.close()
        print("[MCP Daemon] Port closed cleanly.")
    except Exception as e:
        print(f"[MCP Daemon] Error opening port: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
