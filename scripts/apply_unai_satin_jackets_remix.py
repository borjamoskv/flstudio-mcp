#!/usr/bin/env python3
"""
Master Integration Script: 'No Lo Entiende' (Unai Bellamy Stems) x Satin Jackets Infinite Loop Remix
Applies:
1. 116 BPM Project Tempo
2. 19-Track House Producers Mixer Matrix + Sidechain Ducking
3. Vocal Dub FX (3/16 Dotted 8th Ping-Pong Delay & Shimmer Reverb)
4. Satin Jackets Penrose Stair Infinite Loop MIDI (Cm9 Penultimate Tonic) mapped to Unai's C minor key.
"""

import sys
import os
import time
import mido

# Ensure parent directory is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def execute_unai_remix_integration():

    print("="*70)
    print(" INTEGRACIÓN MAESTRA: 'NO LO ENTIENDE' (UNAI STEMS) x SATIN JACKETS REMIX")
    print("="*70)

    try:
        outport = mido.open_output("Antigravity MCP Out", virtual=True)
        print("[CoreMIDI] Port 'Antigravity MCP Out' connected.")
    except Exception as e:
        print(f"[Error] CoreMIDI Port: {e}")
        return False

    # 1. Global Tempo
    outport.send(mido.Message('control_change', channel=15, control=15, value=56)) # 116 BPM
    print(" [1/4] Tempo global ajustado a 116.0 BPM (Do Menor / Cmin)")

    # 2. House Producers 19-Track Mixer Setup
    from scripts.flstudio_legion_house_matrix import run_legion_house_pipeline
    run_legion_house_pipeline()
    print(" [2/4] Matriz de Mezcla de 19 Pistas y Sidechain de Kick cargados")



    # 3. Vocal Dub FX Envíos
    from scripts.flstudio_vocal_dub_fx import setup_vocal_dub_fx
    setup_vocal_dub_fx()
    print(" [3/4] Envíos de Delay Dub 3/16 (387.9ms) y Shimmer Reverb configurados para las voces de Unai")

    # 4. Enviar Secuencia Armónica Infinita (Satin Jackets Penrose Loop)
    midi_path = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scripts/satin_jackets_infinite_loop.mid")
    if os.path.exists(midi_path):
        mid = mido.MidiFile(midi_path)
        print(f" [4/4] Transmitiendo bucle armónico infinito 'Satin Jackets' (Cm9 Penúltima Tónica) a FL Studio...")
        for track in mid.tracks:
            for msg in track:
                if not msg.is_meta:
                    time.sleep(msg.time / 1000.0)
                    outport.send(msg)

    print("\n" + "="*70)
    print(" REMIX INTEGRADO CON ÉXITO EN FL STUDIO 2025!")
    print("="*70)
    return True

if __name__ == "__main__":
    execute_unai_remix_integration()
