#!/usr/bin/env python3
"""
fl_headless_audio_synthesizer.py - Canonical Bridge & Backward Compatibility Shim.
Wraps render_synthwave_flamenco_audio_preview.render_dark_cyber_flamenco_wav.
"""

from pathlib import Path
from typing import Optional
from scripts.render_synthwave_flamenco_audio_preview import render_dark_cyber_flamenco_wav


def render_headless_dark_cyber_flamenco(output_path: Optional[Path] = None) -> Path:
    """Renders the headless dark cyber flamenco 16-bar preview audio asset."""
    if output_path is None:
        bounces_dir = Path.home() / "Music" / "FL Studio Bounces"
        output_path = bounces_dir / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    return render_dark_cyber_flamenco_wav(Path(output_path))


if __name__ == "__main__":
    out = render_headless_dark_cyber_flamenco()
    print(f"✅ Rendered: {out}")
