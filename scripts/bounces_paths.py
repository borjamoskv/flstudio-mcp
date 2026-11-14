#!/usr/bin/env python3
"""
Canonical Bounce & FL Studio Settings Path Resolver (C5-REAL).
Provides resilient, zero-crash directory resolution across live macOS sessions
(~/Music/FL Studio Bounces) and sandboxed/CI environments (WORKSPACE/bounces).
"""

import os
import tempfile
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent


def _is_writable_directory(path: Path) -> bool:
    """Empirically verifies whether `path` is an existing or creatable writable directory."""
    try:
        if path.is_symlink() and not path.exists():
            return False
        path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            return False
        with tempfile.NamedTemporaryFile(dir=str(path), prefix=".c5_probe_", delete=True):
            pass
        return True
    except OSError:
        return False


def resolve_bounces_dir() -> Path:
    """
    Resolves the canonical output directory for rendered audio, stems, scores, and projects:
    1. Respects `FLSTUDIO_BOUNCES_DIR` environment override if set and writable.
    2. Uses `~/Music/FL Studio Bounces` when accessible and writable.
    3. Transparently falls back to `<workspace>/bounces` (git-ignored) if `~/Music/FL Studio Bounces`
       is a dangling symlink or restricted by an OS sandbox.
    """
    env_override = os.environ.get("FLSTUDIO_BOUNCES_DIR")
    if env_override:
        env_path = Path(env_override).expanduser().resolve()
        if _is_writable_directory(env_path):
            return env_path

    default_music = Path.home() / "Music" / "FL Studio Bounces"
    if _is_writable_directory(default_music):
        return default_music

    fallback = WORKSPACE_DIR / "bounces"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def resolve_fl_user_dir() -> Path:
    """
    Resolves FL Studio's user data directory (`~/Documents/Image-Line/FL Studio`),
    falling back to `<bounces>/FL_Studio_User_Mirror` in sandboxed/headless environments.
    """
    fl_user = Path.home() / "Documents" / "Image-Line" / "FL Studio"
    if _is_writable_directory(fl_user / "Settings" / "Tuning"):
        return fl_user

    mirror = resolve_bounces_dir() / "FL_Studio_User_Mirror"
    mirror.mkdir(parents=True, exist_ok=True)
    return mirror
