#!/usr/bin/env python3
"""
fl_headless_audio_synthesizer.py - Canonical Bridge & Backward Compatibility Shim.
Wraps render_synthwave_flamenco_audio_preview.render_dark_cyber_flamenco_wav.
"""

from pathlib import Path
from typing import Optional

try:
    from scripts.bounces_paths import resolve_bounces_dir
    from scripts.render_synthwave_flamenco_audio_preview import render_dark_cyber_flamenco_wav
except ImportError:
    from bounces_paths import resolve_bounces_dir
    from render_synthwave_flamenco_audio_preview import render_dark_cyber_flamenco_wav


def render_headless_dark_cyber_flamenco(output_path: Optional[Path] = None) -> Path:
    """Renders the headless dark cyber flamenco 16-bar 48 kHz preview audio asset."""
    if output_path is None:
        output_path = resolve_bounces_dir() / "Dark_Cyber_Flamenco_Audio_Preview_16Bars.wav"
    return render_dark_cyber_flamenco_wav(Path(output_path))


if __name__ == "__main__":
    out = render_headless_dark_cyber_flamenco()
    print(f"Rendered: {out}")
