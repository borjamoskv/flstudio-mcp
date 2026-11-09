#!/usr/bin/env python3
"""
fl_stems_generator.py - Canonical Bridge & Backward Compatibility Shim.
Wraps render_multitrack_stems_pack.render_multitrack_stems.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from scripts.render_multitrack_stems_pack import render_multitrack_stems


def generate_flamenco_stems_pack(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Generates the multi-track stem pack for Dark Cyber Flamenco."""
    if output_dir is None:
        bounces_dir = Path.home() / "Music" / "FL Studio Bounces"
        output_dir = bounces_dir / "Stems" / "Dark_Cyber_Flamenco_Stems_16Bars"
    return render_multitrack_stems(Path(output_dir))


if __name__ == "__main__":
    res = generate_flamenco_stems_pack()
    print(f"✅ Generated stems: {res}")
