#!/usr/bin/env python3
"""
Persistent CoreMIDI Daemon for Antigravity MCP Out
Keeps the virtual MIDI port permanently active in macOS CoreMIDI system.
"""

import time
import mido

def main():
    print("[CoreMIDI Daemon] Opening virtual output port 'Antigravity MCP Out'...")
    try:
        outport = mido.open_output("Antigravity MCP Out", virtual=True)
        print("[CoreMIDI Daemon] Port 'Antigravity MCP Out' is ONLINE and active.")
        print("[CoreMIDI Daemon] Click 'Refresh device list' in FL Studio MIDI Settings to activate.")
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"[CoreMIDI Daemon Error] {e}")

if __name__ == "__main__":
    main()
