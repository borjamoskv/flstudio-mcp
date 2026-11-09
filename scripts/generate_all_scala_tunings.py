#!/usr/bin/env python3
"""
Generates a complete SOTA Scala (.scl) and Keyboard Mapping (.kbm) Tuning Library
for FL Studio native plugins (Harmor, Sytrus, FLEX) and VST3 synths (Vital, Surge XT, Serum).
"""

import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.flstudio_microtonal import export_scala_scl_file, export_scala_kbm_file, MICROTONAL_SYSTEMS

def build_tuning_library():
    target_dir = os.path.expanduser("~/10_PROJECTS/flstudio-mcp/scalings")
    os.makedirs(target_dir, exist_ok=True)

    print(f"🎵 Generating SOTA Microtonal Scala Library in {target_dir}...")

    generated_files = []
    for sys_name in MICROTONAL_SYSTEMS.keys():
        scl_path = os.path.join(target_dir, f"{sys_name}.scl")
        export_scala_scl_file(system_name=sys_name, output_path=scl_path)
        generated_files.append(scl_path)

    kbm_path = os.path.join(target_dir, "default_a440.kbm")
    export_scala_kbm_file(output_path=kbm_path, middle_note=60, ref_note=69, ref_freq=440.0)
    generated_files.append(kbm_path)

    print(f"✅ Generated {len(generated_files)} tuning files successfully!")
    return generated_files

if __name__ == "__main__":
    build_tuning_library()
