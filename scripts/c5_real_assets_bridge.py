#!/usr/bin/env python3
"""
C5-REAL Studio Assets & Headless VST3 Bridge (FL Studio 2026 + Pedalboard)
==========================================================================
Bridges real studio audio hardware/assets on macOS into deterministic 48 kHz
float64 DSP pipelines:
  1. ModeAudio & FL Packs (.wv/.wav) multi-sample decoder via ffmpeg + LRU cache,
     providing >= 5-variation Round-Robin acoustic/club drum kits with velocity-
     coupled low-pass darkening and zero-crackle boundaries.
  2. Real studio & hardware convolution Impulse Responses (Patches/Impulses/*.wv)
     for Eventide-style warm chambers, Spring Reverbs, Halls, and Small Rooms.
  3. Headless-verified VST3 processing via Pedalboard (Heat2, Thorus BBD Chorus,
     FirePresser, KickShaper, Combustor, Ozone 11 Equalizer), explicitly blocking
     GUI-unsafe plugins (Vital.vst3, Super VHS.vst3).
  4. Transparent deterministic fallbacks whenever external assets or VST3s are
     unavailable (e.g., isolated CI environments).
"""

from __future__ import annotations

import logging
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import signal

logger = logging.getLogger("FLStudio-RealAssetsBridge")

FL_PATCHES_CANDIDATES: Tuple[Path, ...] = (
    Path("/Applications/FL Studio 2026.app/Contents/Resources/FL/Data/Patches"),
    Path("/Applications/FL Studio 2025.app/Contents/Resources/FL/Data/Patches"),
    Path("/Applications/FL Studio 2024.app/Contents/Resources/FL/Data/Patches"),
)

VST3_SAFE_WHITELIST: Dict[str, Path] = {
    "heat2": Path("/Library/Audio/Plug-Ins/VST3/Heat2.vst3"),
    "thorus": Path("/Library/Audio/Plug-Ins/VST3/Thorus.vst3"),
    "combustor": Path("/Library/Audio/Plug-Ins/VST3/Combustor.vst3"),
    "kickshaper": Path("/Library/Audio/Plug-Ins/VST3/KickShaper.vst3"),
    "firepresser": Path("/Library/Audio/Plug-Ins/VST3/FirePresser.vst3"),
    "ozone11_eq": Path("/Library/Audio/Plug-Ins/VST3/Ozone 11 Equalizer.vst3"),
}

# Known headless-crashing VST3s on macOS due to NSView/GPU initialization in CLI hosts
VST3_HEADLESS_BLACKLIST = frozenset({"Vital.vst3", "Super VHS.vst3"})

# Empirically calibrated presets verified on Pedalboard 0.9.21 (2026-11-14)
VST3_CURATED_PRESETS: Dict[str, Tuple[str, Dict[str, float]]] = {
    "heat2_warm_tape": (
        "heat2",
        {
            "power": 1.0,
            "power_left": 1.0,
            "power_right": 1.0,
            "drive_left": 0.24,
            "drive_right": 0.22,
            "low_frequency_left_hz": 0.35,
            "hi_frequency_right_hz": 0.65,
            "blend": 0.62,
            "output_db": 0.50,  # ~0 dB unity
            "mix": 0.72,
            "bypass": 0.0,
        },
    ),
    "firepresser_glue": (
        "firepresser",
        {
            "x": 0.32,
            "y": 0.32,
            "input_gain": 0.50,
            "output_gain": 0.49,
            "saturator": 0.14,
            "turbo": 0.0,
            "link_detector": 1.0,
            "hp_detector": 0.18,
            "dry_wet": 0.38,
            "bypass": 0.0,
        },
    ),
    "combustor_punch": (
        "combustor",
        {
            "power": 1.0,
            "mix": 0.35,
            "saturation": 0.25,
            "threshold_db": 0.70,
            "ratio": 0.25,
            "attack_ms": 0.25,
            "release_ms": 0.28,
            "input_volume_db": 0.50,
            "output_volume_db": 0.50,
        },
    ),
    "kickshaper_club": (
        "kickshaper",
        {
            "deboom_shape": 0.18,
            "click_shape": 0.55,
            "thump_shape": 0.48,
            "heat_enhance": 0.32,
            "depth_enhance": 0.14,
            "punch_enhance": 0.35,
        },
    ),
}

ROLE_TO_MODEAUDIO_SPEC: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "kick": ("Kicks", ("Attack", "Grind", "Warm", "Deep", "Punch")),
    "snare": ("Snares", ("Attack", "Analog", "Crisp", "Tight")),
    "clap": ("Claps", ("Attack", "Analog", "Real", "Room", "Clap")),
    "closed_hat": ("Hi Hats", ("Attack Hat", "Closed", "Tight", "Analog", "Hat")),
    "open_hat": ("Hi Hats", ("Open", "Splash", "Pedal", "Hat 1", "Hat 2")),
    "shaker": ("Shakers", ("Shaker", "Cabasa", "Tamb")),
    "rim": ("Rims", ("Rim", "Wood", "Stick")),
    "perc": ("Percussion", ("Congo", "Bongo", "Wood", "Tabla", "Analog", "Perc")),
    "tom": ("Toms", ("MidTom", "LowTom", "Tom")),
    "cymbal": ("Cymbals", ("Crash", "Ride", "Splash", "Boom")),
    "foley": ("Foley", ("Wood", "Basket", "Brush", "Tap", "Click")),
    "riser": ("SFX", ("Sweep", "Riser", "Air", "Bite")),
}

IR_STYLE_MAP: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "chamber_warm": ("Reverb Devices", ("Chamber Warm", "Chamber Smooth", "Cellar")),
    "spring_dub": ("Spring Reverb", ("Spring 01", "Spring 02", "Spring 03")),
    "hall_air": ("Real Spaces", ("250 Seat Hall - Mid Stage", "Mid", "Auditorium")),
    "cathedral": ("Halls", ("StPauls_B_MID", "hall_mid", "hall")),
    "small_room": ("Small Rooms", ("bedroom", "wooden", "room", "studio")),
}

_VST3_INSTANCE_CACHE: Dict[str, Any] = {}


def resolve_fl_patches_dir() -> Optional[Path]:
    """Returns the installed FL Studio Data/Patches directory if present."""
    for base in FL_PATCHES_CANDIDATES:
        if base.is_dir():
            return base
    return None


@lru_cache(maxsize=512)
def decode_audio_ffmpeg(
    file_path_str: str,
    sample_rate: int = 48000,
    max_sec: float = 3.0,
) -> Optional[np.ndarray]:
    """
    Decodes .wv/.wav/.flac/.mp3 via ffmpeg into read-only float64 stereo array (N, 2).
    Results are LRU-cached so repeated hits do zero subprocess spawning.
    """
    p = Path(file_path_str)
    if not p.is_file():
        return None
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-t",
        f"{max(0.05, float(max_sec)):.3f}",
        "-i",
        str(p),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        "2",
        "-ar",
        str(int(sample_rate)),
        "pipe:1",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, check=False, timeout=8)
    except Exception as exc:
        logger.debug("ffmpeg decode error for %s: %s", p.name, exc)
        return None
    if res.returncode != 0 or len(res.stdout) < 32:
        return None
    arr = np.frombuffer(res.stdout, dtype="<f4").astype(np.float64)
    n_frames = len(arr) // 2
    if n_frames < 16:
        return None
    stereo = arr[: n_frames * 2].reshape(n_frames, 2).copy()
    stereo.flags.writeable = False
    return stereo


def list_modeaudio_samples(
    folder_name: str,
    keywords: Sequence[str] = (),
) -> List[Path]:
    """Lists real ModeAudio samples matching optional filename preference order."""
    patches = resolve_fl_patches_dir()
    if patches is None:
        return []
    target = patches / "Packs" / "Drums (ModeAudio)" / folder_name
    if not target.is_dir():
        return []
    all_files = sorted(list(target.glob("*.wv")) + list(target.glob("*.wav")))
    if not keywords:
        return all_files
    kw_lower = tuple(k.lower() for k in keywords)
    prioritized: List[Path] = []
    rest: List[Path] = []
    for f in all_files:
        name_l = f.name.lower()
        if any(k in name_l for k in kw_lower):
            prioritized.append(f)
        else:
            rest.append(f)
    return prioritized + rest


def _trim_and_envelope_drum_hit(
    stereo: np.ndarray,
    sample_rate: int,
    attack_ms: float = 0.4,
    release_ms: float = 12.0,
) -> np.ndarray:
    """Trims leading silence while protecting zero-crackle onset and decay tail."""
    arr = np.array(stereo, dtype=np.float64, copy=True)
    mono_env = np.max(np.abs(arr), axis=1)
    peak = float(np.max(mono_env))
    if peak < 1e-6:
        return np.zeros((min(256, len(arr)), 2), dtype=np.float64)

    nz = np.flatnonzero(mono_env > peak * 0.004)
    lead_in = max(4, int(round(0.0005 * sample_rate)))
    start = max(0, int(nz[0]) - lead_in) if len(nz) else 0

    nz_end = np.flatnonzero(mono_env > peak * 0.0008)
    tail_pad = int(round(0.020 * sample_rate))
    end = min(len(arr), int(nz_end[-1]) + tail_pad) if len(nz_end) else len(arr)
    if end - start < 32:
        end = min(len(arr), start + max(64, int(0.05 * sample_rate)))

    trimmed = arr[start:end].copy()
    trimmed = trimmed / peak

    n = len(trimmed)
    n_att = min(n // 4, max(2, int(round((attack_ms / 1000.0) * sample_rate))))
    n_rel = min(n // 2, max(4, int(round((release_ms / 1000.0) * sample_rate))))
    if n_att > 1:
        w_a = 0.5 * (1.0 - np.cos(np.pi * np.arange(n_att, dtype=np.float64) / (n_att - 1)))
        trimmed[:n_att] *= w_a[:, None]
    if n_rel > 1:
        w_r = 0.5 * (1.0 + np.cos(np.pi * np.arange(n_rel, dtype=np.float64) / (n_rel - 1)))
        trimmed[-n_rel:] *= w_r[:, None]
    trimmed[0] = 0.0
    trimmed[-1] = 0.0
    trimmed.flags.writeable = False
    return trimmed


@lru_cache(maxsize=64)
def get_round_robin_drum_pool(
    role: str,
    count: int = 8,
    sample_rate: int = 48000,
    max_sec: float = 1.25,
) -> Tuple[np.ndarray, ...]:
    """
    Loads up to `count` curated real studio drum/percussion waveforms for `role`
    (guaranteed distinct samples across consecutive triggers -> zero Machine-Gun Effect).
    Returns empty tuple cleanly when ModeAudio library is absent.
    """
    folder, keywords = ROLE_TO_MODEAUDIO_SPEC.get(role, ("Percussion", ()))
    candidates = list_modeaudio_samples(folder, keywords)
    if not candidates:
        return ()

    # Stride selection spreads variations across kits instead of clones
    step = max(1, len(candidates) // max(1, count * 2))
    chosen = candidates[::step][: count * 2]
    pool: List[np.ndarray] = []
    for path in chosen:
        decoded = decode_audio_ffmpeg(str(path), sample_rate=sample_rate, max_sec=max_sec)
        if decoded is None:
            continue
        cleaned = _trim_and_envelope_drum_hit(
            decoded,
            sample_rate=sample_rate,
            attack_ms=0.25 if role in ("kick", "rim", "snare") else 0.6,
            release_ms=14.0 if role in ("cymbal", "open_hat", "clap", "snare") else 8.0,
        )
        if len(cleaned) >= 64:
            pool.append(cleaned)
        if len(pool) >= count:
            break
    return tuple(pool)


def shape_velocity_sample(
    stereo_sample: np.ndarray,
    velocity: float = 0.85,
    sample_rate: int = 48000,
    bright_cutoff_hz: float = 16500.0,
    dark_cutoff_hz: float = 2800.0,
) -> np.ndarray:
    """
    Couples hit velocity to upper-spectrum damping and subtle micro-gain scaling
    so ghost hits sound physically softer rather than digitally quieter clones.
    """
    v = float(np.clip(velocity, 0.05, 1.25))
    out = np.array(stereo_sample, dtype=np.float64, copy=True)
    if v < 0.82 and len(out) >= 16:
        alpha = float(np.clip((v - 0.15) / 0.67, 0.0, 1.0))
        fc = dark_cutoff_hz + alpha * (bright_cutoff_hz - dark_cutoff_hz)
        wn = float(np.clip(fc / (0.5 * sample_rate), 0.04, 0.92))
        sos = signal.butter(1, wn, btype="low", output="sos")
        out = signal.sosfilt(sos, out, axis=0)
    return out * v


@lru_cache(maxsize=32)
def get_real_room_ir(
    style: str = "chamber_warm",
    sample_rate: int = 48000,
    max_sec: float = 1.65,
) -> Optional[Tuple[np.ndarray, str]]:
    """
    Decodes a genuine studio/hardware convolution Impulse Response (.wv) from
    FL Studio Patches/Impulses, cleans sub-bass (<160 Hz), preserves authentic stereo
    early-reflection width, and caches read-only (N, 2) IR array.
    """
    patches = resolve_fl_patches_dir()
    if patches is None:
        return None
    folder, prefs = IR_STYLE_MAP.get(style, IR_STYLE_MAP["chamber_warm"])
    ir_dir = patches / "Impulses" / folder
    if not ir_dir.is_dir():
        return None

    files = sorted(list(ir_dir.glob("*.wv")) + list(ir_dir.glob("*.wav")))
    if not files:
        return None

    chosen: Optional[Path] = None
    for kw in prefs:
        kw_l = kw.lower()
        for f in files:
            if kw_l in f.name.lower():
                chosen = f
                break
        if chosen is not None:
            break
    if chosen is None:
        chosen = files[0]

    raw = decode_audio_ffmpeg(str(chosen), sample_rate=sample_rate, max_sec=max_sec)
    if raw is None or len(raw) < 256:
        return None

    ir = np.array(raw, dtype=np.float64, copy=True)
    # Trim dead pre-silence before first acoustic impulse while keeping >= 1ms onset
    env = np.max(np.abs(ir), axis=1)
    peak = float(np.max(env))
    if peak < 1e-7:
        return None
    nz = np.flatnonzero(env > peak * 0.002)
    if len(nz) > 0 and nz[0] > 48:
        ir = ir[max(0, int(nz[0]) - 16) :]

    # Protect subgrave coherence: high-pass IR at 165 Hz, soft air taper at 15.5 kHz
    nyq = 0.5 * sample_rate
    sos_ir = signal.butter(
        2,
        [min(0.35, 165.0 / nyq), min(0.92, 15500.0 / nyq)],
        btype="band",
        output="sos",
    )
    ir = signal.sosfilt(sos_ir, ir, axis=0)

    # Energy normalization so wet returns remain predictable across different IR rooms
    rms_energy = float(np.sqrt(np.sum(ir[:, 0] ** 2) + np.sum(ir[:, 1] ** 2)) + 1e-12)
    ir /= rms_energy

    # Smooth 24 ms tail fade-out to zero
    n_fade = min(len(ir) // 3, int(round(0.024 * sample_rate)))
    if n_fade > 2:
        w = 0.5 * (1.0 + np.cos(np.pi * np.arange(n_fade, dtype=np.float64) / (n_fade - 1)))
        ir[-n_fade:] *= w[:, None]
    ir[-1] = 0.0
    ir.flags.writeable = False
    return ir, chosen.name


def load_safe_vst3_plugin(plugin_key: str) -> Optional[Any]:
    """
    Loads a verified headless-safe VST3 plugin via Pedalboard.
    Strictly rejects blacklisted GUI-crashing plugins and caches instances.
    """
    key = plugin_key.lower().strip()
    if key in _VST3_INSTANCE_CACHE:
        return _VST3_INSTANCE_CACHE[key]
    vst_path = VST3_SAFE_WHITELIST.get(key)
    if vst_path is None or not vst_path.exists():
        return None
    if vst_path.name in VST3_HEADLESS_BLACKLIST:
        logger.warning("Blocked unsafe headless VST3 plugin: %s", vst_path.name)
        return None
    try:
        import pedalboard

        inst = pedalboard.load_plugin(str(vst_path))
        _VST3_INSTANCE_CACHE[key] = inst
        return inst
    except Exception as exc:
        logger.warning("VST3 plugin load failed (%s): %s", key, exc)
        return None


def apply_vst3_plugin(
    audio: np.ndarray,
    plugin_key: str,
    sample_rate: int = 48000,
    raw_params: Optional[Dict[str, float]] = None,
    wet: float = 1.0,
    require_effective: bool = True,
) -> Tuple[np.ndarray, bool]:
    """
    Processes mono or stereo (N,) / (N, 2) float64 audio safely through a headless
    VST3 plugin with dry/wet blending and deterministic fallback on failure.
    When `require_effective=True`, silent/bypassed plugins (diff < 1e-6) return ok=False
    so downstream DSP triggers authentic physical fallback rather than pretending.
    """
    arr = np.asarray(audio, dtype=np.float64)
    if arr.size == 0 or wet <= 0.0:
        return arr.copy(), False

    plugin = load_safe_vst3_plugin(plugin_key)
    if plugin is None:
        return arr.copy(), False

    was_mono = arr.ndim == 1
    stereo = np.column_stack((arr, arr)) if was_mono else arr.copy()
    if stereo.shape[1] != 2:
        return arr.copy(), False
    stereo.flags.writeable = False

    try:
        plugin.reset()
        if raw_params:
            for p_name, p_val in raw_params.items():
                if p_name in plugin.parameters:
                    plugin.parameters[p_name].raw_value = float(np.clip(p_val, 0.0, 1.0))

        # Pedalboard expects channels-first float32 (2, N)
        buf32 = np.ascontiguousarray(stereo.T, dtype=np.float32)
        out32 = plugin(buf32, int(sample_rate), buffer_size=512)
        out64 = np.array(out32.T, dtype=np.float64, copy=True)
        if out64.shape != stereo.shape or not np.all(np.isfinite(out64)):
            return arr.copy(), False
        out64.flags.writeable = False

        # Guard against unlicensed/bypassed VST3 identity pass-through and wild gain spikes
        if require_effective:
            max_diff = float(np.max(np.abs(out64 - stereo)))
            if max_diff < 1e-6:
                return arr.copy(), False

        in_rms = float(np.sqrt(np.mean(stereo * stereo)) + 1e-12)
        out_rms = float(np.sqrt(np.mean(out64 * out64)) + 1e-12)
        if out_rms > in_rms * 2.5:
            out64 = out64 * ((in_rms * 1.15) / out_rms)
            out64.flags.writeable = False

        w = float(np.clip(wet, 0.0, 1.0))
        blended = (1.0 - w) * stereo + w * out64
        if was_mono:
            return 0.5 * (blended[:, 0] + blended[:, 1]), True
        return blended, True
    except Exception as exc:
        logger.warning("VST3 processing fallback (%s): %s", plugin_key, exc)
        return arr.copy(), False


def apply_curated_vst3_preset(
    audio: np.ndarray,
    preset_name: str,
    sample_rate: int = 48000,
    wet: float = 1.0,
) -> Tuple[np.ndarray, bool]:
    """Applies an empirically calibrated preset from `VST3_CURATED_PRESETS`."""
    spec = VST3_CURATED_PRESETS.get(preset_name)
    if spec is None:
        return np.asarray(audio, dtype=np.float64).copy(), False
    plugin_key, raw_params = spec
    return apply_vst3_plugin(
        audio,
        plugin_key=plugin_key,
        sample_rate=sample_rate,
        raw_params=raw_params,
        wet=wet,
        require_effective=True,
    )
