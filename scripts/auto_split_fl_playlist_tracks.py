#!/usr/bin/env python3
"""
C5-REAL FL STUDIO PLAYLIST TRACK EXPANDER & AUTOMATION SCRIPT
=============================================================
Automates splitting the single master pattern clip into 6 SEPARATE PLAYLIST TRACKS
in FL Studio 2025 so each instrument occupies its own dedicated Playlist track row:

Target Playlist Layout (Rows 1 to 6):
-------------------------------------
Playlist Track 1: Fender Rhodes 73 (Satin Jackets Chords)
Playlist Track 2: Solina Strings Ensemble (AIR Space Pad)
Playlist Track 3: Minimoog Sub-Bass Drive
Playlist Track 4: Maceo Industrial 303 Acid Lead
Playlist Track 5: AIR Vocoder Space Lead
Playlist Track 6: Drums & Percussion (Maceo Kick + Swing Hats)
"""

import time
import os
import subprocess

def trigger_fl_split_by_channel():
    print("=== [FL STUDIO PLAYLIST TRACK AUTOMATION] ===")
    
    # 1. Activate FL Studio window using AppleScript
    applescript = '''
    tell application "FL Studio 2025"
        activate
    end tell
    '''
    subprocess.run(["osascript", "-e", applescript])
    time.sleep(0.8)

    try:
        import pyautogui
        # Press Cmd+Shift+C (Split by Channel in FL Studio macOS)
        pyautogui.hotkey('command', 'shift', 'c')
        time.sleep(0.5)
        print("✅ Executed Cmd+Shift+C (Split by Channel).")
    except Exception as e:
        print(f"PyAutoGUI note: {e}")

if __name__ == "__main__":
    trigger_fl_split_by_channel()
