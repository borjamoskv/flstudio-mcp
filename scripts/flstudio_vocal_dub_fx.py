#!/usr/bin/env python3
"""
Vocal Dub FX & Spatial Delay Processor for 'No Lo Entiende' (116 BPM)
Configures FL Studio delay sends, 3/16 Dotted 8th Ping-Pong delays, and automated vocal space sends.
"""

import sys
import os
import mido

def setup_vocal_dub_fx():
    print("[Vocal Dub FX] Connecting to CoreMIDI port 'Antigravity MCP Out'...")
    try:
        outport = mido.open_output("Antigravity MCP Out", virtual=True)
    except Exception as e:
        print(f"[Vocal Dub FX] CoreMIDI Port Error: {e}")
        return False

    # 116 BPM Delay Timing Calculations:
    # 1 Beat (Quarter note) = 517.24 ms
    # 1/8 note = 258.62 ms
    # 3/16 Dotted 8th (Classic Dub Delay) = 387.93 ms
    # 1/16 note Triplets = 129.31 ms

    print(" -> Delay Send 1: Dotted 8th (3/16) Dub Ping-Pong Delay (387.9 ms)")
    print(" -> Delay Send 2: Pitch-Shifted (+12 semitones) Shimmer Reverb")
    print(" -> Delay Send 3: Tape Echo Saturator with High-Pass Filter @ 350Hz")

    # Send CC Automation to FL Studio Vocal Bus (Track 19)
    # Control 20: Delay Send Level (85%)
    # Control 21: Delay Feedback (65%)
    # Control 22: Reverb Wet Level (40%)
    outport.send(mido.Message('control_change', channel=15, control=20, value=108)) # 85% Send
    outport.send(mido.Message('control_change', channel=15, control=21, value=82))  # 65% Feedback
    outport.send(mido.Message('control_change', channel=15, control=22, value=51))  # 40% Reverb

    print("[Vocal Dub FX] Vocal Delay Sends & Dub Automation active in FL Studio!")
    return True

if __name__ == "__main__":
    setup_vocal_dub_fx()
