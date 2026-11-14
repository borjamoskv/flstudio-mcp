#!/usr/bin/env python3
"""
SIKAH-128: Generador Simbólico Multimétrico (3/2 -> 6/4 -> 12/8), Microtonal y Maqueta DSP.

- Exporta SMF Tipo 1 (.mid) con modulación métrica isócrona 3/2 -> 6/4 -> 12/8
  (2880 ticks/compás @ 480 PPQ; 384 corcheas/min => 12/8 a 128.0 BPM).
- Estribillo estricto: la tónica D4 (0.00c) ocupa invariablemente la posición
  anteúltima (n_7 de 8 notas) y cierra suspendida en E medio-bemol (+150.00c).
- Exporta escala Scala (D_Maqam_Septimal_12.scl / .kbm) y script nativo
  SIKAH128_Estribillo.pyscript para el Piano Roll de FL Studio 2025.
- Con --render-maquette compila stems + mezcla + máster a 48 kHz / 24-bit
  etiquetados como AUTÓMATA_SINTÉTICO_ESTRUCTURAL sobre c5_dsp_core.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import mido
import numpy as np
from scipy import signal

try:
    from scripts.bounces_paths import resolve_bounces_dir, resolve_fl_user_dir
    from scripts.c5_dsp_core import (
        apply_coherent_shared_room,
        apply_noncommutative_dub_echo,
        apply_zero_crackle_envelope,
        build_coupled_multiband_sidechain,
        carve_polyphonic_mud,
        check_zero_crackle_derivatives,
        enforce_low_end_mono,
        freeze_array,
        generate_warm_analog_tape_bed,
        lr4_zero_phase_crossover,
        make_time_axis,
        oversampled_soft_saturate,
        synthesize_phase_locked_kick,
        write_pcm_wav,
    )
    from scripts.mastering_reverse_engine_fl import (
        compute_rubin_metrics,
        master_audio_reverse_engineered,
    )
except ImportError:
    from bounces_paths import resolve_bounces_dir, resolve_fl_user_dir
    from c5_dsp_core import (
        apply_coherent_shared_room,
        apply_noncommutative_dub_echo,
        apply_zero_crackle_envelope,
        build_coupled_multiband_sidechain,
        carve_polyphonic_mud,
        check_zero_crackle_derivatives,
        enforce_low_end_mono,
        freeze_array,
        generate_warm_analog_tape_bed,
        lr4_zero_phase_crossover,
        make_time_axis,
        oversampled_soft_saturate,
        synthesize_phase_locked_kick,
        write_pcm_wav,
    )
    from mastering_reverse_engine_fl import (
        compute_rubin_metrics,
        master_audio_reverse_engineered,
    )

PPQ = 480
BAR_TICKS = 2880  # 12 corcheas * 240 ticks = 6 negras * 480 ticks
QUARTER_BPM = 192.0  # 384 corcheas/min => 3/2=96 BPM, 6/4=64/192 BPM, 12/8=128 BPM
BAR_DURATION_SEC = (6.0 / QUARTER_BPM) * 60.0  # 1.875 s exactos por compás
SAMPLE_RATE = 48000
D4_REF_HZ = 440.0 * (2.0 ** (-7.0 / 12.0))  # 293.6647679174076 Hz

RUBIN_LINTER_PATH = Path(
    "/Users/borjafernandezangulo/.gemini/config/skills/"
    "c5-rubin-acoustic-linter/scripts/audit_acoustic_exergy.py"
)

# Cents exactos respecto a D4 (0.00c)
SCALE_CENTS_D4: Dict[str, float] = {
    "D1": -3600.00,
    "D2": -2400.00,
    "A2": -1698.04,
    "D3": -1200.00,
    "Eb_sikah3": -1050.00,
    "F_neut3": -850.00,
    "G3": -701.96,
    "Gs_11th3": -648.68,
    "A3": -498.04,
    "D4": 0.00,
    "Eb_sikah4": 150.00,
    "E4": 203.91,
    "F_neut4": 350.00,
    "Fs4": 386.31,
    "G4": 498.04,
    "Gs_11th4": 551.32,
    "A4": 701.96,
    "Bb_neut4": 850.00,
    "C_sept5": 968.83,
    "C_neut5": 1050.00,
    "Cs5": 1088.27,
    "D5": 1200.00,
}

# Mapeo 12-TET + pitchoffset en cents (|offset| <= 55c)
NOTE_MAP: Dict[str, Tuple[int, int]] = {
    "D1": (26, 0),
    "D2": (38, 0),
    "A2": (45, 2),
    "D3": (50, 0),
    "Eb_sikah3": (52, -50),
    "F_neut3": (53, 50),
    "G3": (55, -2),
    "Gs_11th3": (56, -49),
    "A3": (57, 2),
    "D4": (62, 0),
    "Eb_sikah4": (64, -50),
    "E4": (64, 4),
    "F_neut4": (65, 50),
    "G4": (67, -2),
    "Gs_11th4": (68, -49),
    "A4": (69, 2),
    "Bb_neut4": (71, -50),
    "C_sept5": (72, -31),
    "C_neut5": (72, 50),
    "D5": (74, 0),
}

# Hook de estribillo (8 notas): n_7 (index -2) = Tónica D4; n_8 (index -1) = Eb_sikah4
CHORUS_MELODY: List[Tuple[str, int]] = [
    ("D5", 200),
    ("C_sept5", 200),
    ("A4", 200),
    ("Gs_11th4", 200),
    ("F_neut4", 360),
    ("G4", 360),
    ("D4", 200),         # Anteúltima nota = Tónica (0.00c)
    ("Eb_sikah4", 220),  # Última nota = Suspensión microtonal (+150.00c)
]

CHORUS_OFFSETS_TICKS: Dict[str, List[int]] = {
    "3/2": [0, 480, 960, 1200, 1440, 1920, 2400, 2640],
    "6/4": [0, 480, 720, 1200, 1440, 1920, 2400, 2640],
    "12/8": [0, 480, 720, 1200, 1440, 1920, 2160, 2640],
}

SECTIONS_PLAN: List[Tuple[str, int, int, int]] = [
    ("3/2", 3, 2, 4),
    ("6/4", 6, 4, 4),
    ("12/8", 12, 8, 8),
]

SCALA_SCL_CONTENT = """! D_Maqam_Septimal_12.scl
! SIKAH-128: Microtonal Melodic Techno in D (Quarter-tones + 7-limit/11-limit JI)
D Maqam-Septimal Hybrid (0c, 150c, 9/8, 350c, 5/4, 4/3, 11/8, 3/2, 850c, 7/4, 1050c, 15/8, 2/1)
 12
!
 150.0000
 9/8
 350.0000
 5/4
 4/3
 11/8
 3/2
 850.0000
 7/4
 1050.0000
 15/8
 2/1
"""

SCALA_KBM_CONTENT = f"""! D_Maqam_Septimal_12.kbm
! Root D4 (MIDI 62) -> {D4_REF_HZ:.6f} Hz, octave closure degree 12
12
0
127
62
62
{D4_REF_HZ:.6f}
12
0
1
2
3
4
5
6
7
8
9
10
11
"""

FL_PYSCRIPT_CONTENT = '''# name = SIKAH-128 Estribillo & Trombones (3/2 -> 6/4 -> 12/8)
# author = Borja Fernández Angulo / MOSKV-1
# description = Estribillo microtonal (tónica D4 anteúltima, cierre Sikah +150c) con slides de trombón.

import flpianoroll as flp


def createDialog():
    form = flp.ScriptDialog(
        "SIKAH-128 (3/2 -> 6/4 -> 12/8)",
        "Genera el estribillo microtonal (Tónica D4 anteúltima) y trombones en 3/2, 6/4 y 12/8.",
    )
    form.AddInputCombo(
        "Compas Activo",
        "3/2 (4+4+4),6/4 (Hemiola 6+6),12/8 (Climax 128 BPM),Secuencia Completa 3/2->6/4->12/8",
        3,
    )
    form.AddInputCheckbox("Incluir Slides Microtonales", True)
    return form


def _add_note(score, number, time_480, len_480, vel, pitchoffset=0, slide=False, color=0, scale=1.0):
    n = flp.Note()
    n.number = int(number)
    n.time = int(round(time_480 * scale))
    n.length = max(1, int(round(len_480 * scale)))
    n.velocity = float(vel)
    if hasattr(n, "pitchoffset"):
        n.pitchoffset = int(pitchoffset)
    if hasattr(n, "slide") and slide:
        n.slide = True
    if hasattr(n, "color"):
        n.color = int(color)
    score.addNote(n)


def apply(form):
    mode = form.GetInputValue("Compas Activo")
    use_slides = form.GetInputValue("Incluir Slides Microtonales")
    flp.score.clear()

    ppq = getattr(flp.score, "PPQ", 96)
    scale = ppq / 480.0
    bar_480 = 2880

    # n_7 (anteúltima) = D4 (62, 0c), n_8 (última) = Eb_sikah4 (64, -50c)
    melody = [
        (74, 0, 200, 0.92),     # D5
        (72, -31, 200, 0.82),   # C_sept5 (7/4)
        (69, 2, 200, 0.86),     # A4 (3/2)
        (68, -49, 200, 0.84),   # Gs_11th4 (11/8)
        (65, 50, 360, 0.88),    # F_neut4
        (67, -2, 230, 0.85),    # G4 (4/3)
        (62, 0, 200, 0.96),     # D4 (TÓNICA = ANTEÚLTIMA)
        (64, -50, 220, 0.98),   # Eb_sikah4 (ÚLTIMA = TENSIÓN +150c)
    ]
    grids = {
        "3/2": [0, 480, 960, 1200, 1440, 1920, 2400, 2640],
        "6/4": [0, 480, 720, 1200, 1440, 1920, 2400, 2640],
        "12/8": [0, 480, 720, 1200, 1440, 1920, 2160, 2640],
    }

    if mode == 0:
        seq = ["3/2"] * 4
    elif mode == 1:
        seq = ["6/4"] * 4
    elif mode == 2:
        seq = ["12/8"] * 4
    else:
        seq = ["3/2", "3/2", "6/4", "6/4", "12/8", "12/8", "12/8", "12/8"]

    prev_sig = None
    for bar_i, sig in enumerate(seq):
        b0 = bar_i * bar_480
        if sig != prev_sig and hasattr(flp, "Marker"):
            try:
                m = flp.Marker()
                m.name = f"Compas {sig}"
                m.time = int(round(b0 * scale))
                flp.score.addMarker(m)
            except Exception:
                pass
            prev_sig = sig

        for idx_n, ((midi_n, cents, dur, vel), off) in enumerate(zip(melody, grids[sig])):
            if use_slides and idx_n == 3:
                _add_note(flp.score, 67, b0 + off, dur, vel, pitchoffset=-2, color=0, scale=scale)
                _add_note(
                    flp.score,
                    midi_n,
                    b0 + off + 60,
                    max(60, dur - 60),
                    vel,
                    pitchoffset=cents,
                    slide=True,
                    color=0,
                    scale=scale,
                )
            else:
                _add_note(flp.score, midi_n, b0 + off, dur, vel, pitchoffset=cents, color=0, scale=scale)

        _add_note(flp.score, 38, b0, 1200, 0.80, pitchoffset=0, color=1, scale=scale)
        tr_off = 1920 if sig == "3/2" else 1440
        if use_slides:
            _add_note(flp.score, 55, b0 + tr_off, 800, 0.85, pitchoffset=-2, color=1, scale=scale)
            _add_note(
                flp.score,
                56,
                b0 + tr_off + 120,
                620,
                0.88,
                pitchoffset=-49,
                slide=True,
                color=1,
                scale=scale,
            )
        else:
            _add_note(flp.score, 56, b0 + tr_off, 800, 0.85, pitchoffset=-49, color=1, scale=scale)


def createScore():
    class _DefaultForm:
        def GetInputValue(self, key):
            return 3 if key == "Compas Activo" else True

    apply(_DefaultForm())
'''


def cents_to_pitchwheel(cents: float, bend_range_semitones: float = 2.0) -> int:
    """Convierte desviación en cents a valor MIDI pitchwheel [-8192, +8191]."""
    max_cents = bend_range_semitones * 100.0
    norm = max(-1.0, min(1.0, cents / max_cents))
    return max(-8192, min(8191, int(round(norm * 8191))))


def note_name_to_hz(note_name: str) -> float:
    """Calcula la frecuencia exacta en Hz a partir de SCALE_CENTS_D4."""
    cents = SCALE_CENTS_D4[note_name]
    return float(D4_REF_HZ * (2.0 ** (cents / 1200.0)))


def tick_to_sample(tick: float, sample_rate: int = SAMPLE_RATE) -> int:
    """Convierte tick absoluto (480 PPQ) a índice de muestra isócrono."""
    sec = (float(tick) / float(BAR_TICKS)) * BAR_DURATION_SEC
    return int(round(sec * sample_rate))


def events_to_track(
    name: str,
    channel: int,
    raw_events: List[Tuple[int, mido.Message]],
    include_rpn: bool = True,
) -> mido.MidiTrack:
    """Convierte eventos absolutos (tick, msg) en pista MIDI ordenada por delta-time."""
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name=name, time=0))
    if include_rpn:
        track.append(mido.Message("control_change", channel=channel, control=101, value=0, time=0))
        track.append(mido.Message("control_change", channel=channel, control=100, value=0, time=0))
        track.append(mido.Message("control_change", channel=channel, control=6, value=2, time=0))

    raw_events.sort(key=lambda item: item[0])
    last_t = 0
    for abs_t, msg in raw_events:
        t_clamped = max(last_t, int(abs_t))
        delta = t_clamped - last_t
        track.append(msg.copy(time=delta))
        last_t = t_clamped
    track.append(mido.MetaMessage("end_of_track", time=0))
    return track


def build_midi(out_mid: Path, sections: Sequence[Tuple[str, int, int, int]] = SECTIONS_PLAN) -> Path:
    """Genera el archivo MIDI SMF Tipo 1 multimétrico (3/2 -> 6/4 -> 12/8) y microtonal."""
    mid = mido.MidiFile(type=1, ticks_per_beat=PPQ)
    conductor = mido.MidiTrack()
    conductor.append(mido.MetaMessage("track_name", name="SIKAH128_Conductor", time=0))
    conductor.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(QUARTER_BPM), time=0))

    kick_ev: List[Tuple[int, mido.Message]] = []
    cast_ev: List[Tuple[int, mido.Message]] = []
    tromb_ev: List[Tuple[int, mido.Message]] = []
    lead_ev: List[Tuple[int, mido.Message]] = []
    bass_ev: List[Tuple[int, mido.Message]] = []

    cur_tick = 0
    prev_tick_sig = 0

    for label, num, den, n_bars in sections:
        delta_sig = cur_tick - prev_tick_sig
        cpc = 48 if label == "3/2" else (24 if label == "6/4" else 36)
        conductor.append(
            mido.MetaMessage(
                "time_signature",
                numerator=num,
                denominator=den,
                clocks_per_click=cpc,
                notated_32nd_notes_per_beat=8,
                time=delta_sig,
            )
        )
        conductor.append(mido.MetaMessage("marker", text=f"Acto_{label}", time=0))
        prev_tick_sig = cur_tick

        for bar in range(n_bars):
            b0 = cur_tick
            is_pre_drop_vacuum = label == "6/4" and bar == n_bars - 1

            # 1. Bombo Techno (Canal 10 / index 9, nota 36)
            if label == "3/2":
                kick_grid = [0, 960, 1920]
            elif label == "6/4":
                kick_grid = (
                    [0, 480, 960, 1440]
                    if is_pre_drop_vacuum
                    else [0, 480, 960, 1440, 1920, 2400]
                )
            else:
                kick_grid = [0, 720, 1440, 2160]

            for k_off in kick_grid:
                t_k = b0 + k_off
                kick_ev.append((t_k, mido.Message("note_on", channel=9, note=36, velocity=115)))
                kick_ev.append((t_k + 120, mido.Message("note_off", channel=9, note=36, velocity=0)))

            # 2. Sub-Bajo Techno D2 (Canal 3)
            if not is_pre_drop_vacuum:
                bass_grid = [240, 1200, 2160] if label == "3/2" else [240, 960, 1680, 2400]
                for b_off in bass_grid:
                    t_b = b0 + b_off
                    bass_ev.append((t_b, mido.Message("note_on", channel=3, note=38, velocity=100)))
                    bass_ev.append(
                        (t_b + 180, mido.Message("note_off", channel=3, note=38, velocity=0))
                    )

            # 3. Castañuelas: Macho (76) y Hembra Carretilla (77)
            if not is_pre_drop_vacuum:
                macho_offs = (
                    [960, 2400]
                    if label == "3/2"
                    else ([1440] if label == "6/4" else [720, 2160])
                )
                for m_off in macho_offs:
                    cast_ev.append(
                        (b0 + m_off, mido.Message("note_on", channel=9, note=76, velocity=105))
                    )
                    cast_ev.append(
                        (b0 + m_off + 90, mido.Message("note_off", channel=9, note=76, velocity=0))
                    )

                carretilla_anchor = 1920 if label in ("3/2", "6/4") else 1800
                for dt, vel in [(0, 62), (75, 76), (140, 90), (200, 112)]:
                    t_c = b0 + carretilla_anchor + dt
                    cast_ev.append((t_c, mido.Message("note_on", channel=9, note=77, velocity=vel)))
                    cast_ev.append(
                        (t_c + 45, mido.Message("note_off", channel=9, note=77, velocity=0))
                    )

            # 4. Trombones / Cuerno Analógico (automatización CC #74/#11 + fraseo respirado)
            bar_global = (cur_tick // BAR_TICKS)
            cutoff_cc = min(127, max(28, int(round(36 + 5.2 * bar_global))))
            tromb_ev.append((b0, mido.Message("control_change", channel=1, control=74, value=cutoff_cc)))
            tromb_ev.append((b0, mido.Message("control_change", channel=1, control=11, value=96)))
            if bar % 2 == 0 and not is_pre_drop_vacuum:
                tromb_ev.append((b0 + 6, mido.Message("pitchwheel", channel=1, pitch=0)))
                tromb_ev.append((b0 + 8, mido.Message("note_on", channel=1, note=38, velocity=88)))
                tromb_ev.append(
                    (b0 + BAR_TICKS - 120, mido.Message("note_off", channel=1, note=38, velocity=0))
                )

            if not is_pre_drop_vacuum and (bar % 2 == 1 or label == "6/4"):
                t_tr = b0 + (1920 if label == "3/2" else 1440)
                note_num, cents_off = NOTE_MAP["Gs_11th3"]
                tromb_ev.append(
                    (
                        t_tr - 5,
                        mido.Message(
                            "pitchwheel", channel=1, pitch=cents_to_pitchwheel(cents_off)
                        ),
                    )
                )
                tromb_ev.append(
                    (t_tr + 8, mido.Message("note_on", channel=1, note=note_num, velocity=94))
                )
                tromb_ev.append(
                    (t_tr + 920, mido.Message("note_off", channel=1, note=note_num, velocity=0))
                )

            # 5. Estribillo Lead Melódico (n_7 = Tónica D4 anteúltima, n_8 = Eb_sikah4)
            # Incluye automatización continua de filtro/expresión (CC #74, CC #1, CC #11) y legato
            lead_cc74 = (
                42 + 6 * bar
                if label == "3/2"
                else (68 + 10 * bar if label == "6/4" else (96 if bar % 2 == 0 else 76))
            )
            lead_ev.append(
                (b0, mido.Message("control_change", channel=2, control=74, value=min(124, lead_cc74)))
            )
            lead_ev.append(
                (
                    b0,
                    mido.Message(
                        "control_change",
                        channel=2,
                        control=1,
                        value=28 if label == "3/2" else (52 if label == "6/4" else 78),
                    ),
                )
            )
            offsets = CHORUS_OFFSETS_TICKS[label]
            vel_arc = [92, 74, 80, 86, 94, 84, 106, 112]
            pocket_ticks = [0, 7, -4, 9, 5, -3, 4, 8]
            for idx_n, ((n_name, dur), off_t) in enumerate(zip(CHORUS_MELODY, offsets)):
                if is_pre_drop_vacuum and idx_n < 6:
                    continue
                midi_n, cents_off = NOTE_MAP[n_name]
                # Mantener estrictamente dentro de [b0 + 4, b0 + BAR_TICKS - 24]
                raw_on = b0 + off_t + pocket_ticks[idx_n]
                t_on = max(b0 + (4 if idx_n > 0 else 0), min(b0 + BAR_TICKS - 60, raw_on))
                next_off = offsets[idx_n + 1] if idx_n + 1 < len(offsets) else BAR_TICKS
                legato_span = max(110, next_off - off_t - 12)
                eff_dur = max(dur, int(round(legato_span * 0.90)))
                eff_dur = min(eff_dur, max(80, (b0 + next_off - 8) - t_on))
                dyn_scale = 0.68 if label == "3/2" else (0.85 if label == "6/4" else 1.0)
                if label == "12/8" and bar % 2 == 1 and idx_n < 4:
                    dyn_scale *= 0.62
                vel = max(42, min(122, int(round(vel_arc[idx_n] * dyn_scale))))
                lead_ev.append(
                    (
                        max(0, t_on - 2),
                        mido.Message(
                            "pitchwheel", channel=2, pitch=cents_to_pitchwheel(cents_off)
                        ),
                    )
                )
                lead_ev.append(
                    (t_on, mido.Message("note_on", channel=2, note=midi_n, velocity=vel))
                )
                lead_ev.append(
                    (t_on + eff_dur, mido.Message("note_off", channel=2, note=midi_n, velocity=0))
                )

            cur_tick += BAR_TICKS

    conductor.append(mido.MetaMessage("end_of_track", time=0))
    mid.tracks.append(conductor)
    mid.tracks.append(events_to_track("Kick_Techno_D1", 9, kick_ev, include_rpn=False))
    mid.tracks.append(events_to_track("Castanuelas_Macho_Hembra", 9, cast_ev, include_rpn=False))
    mid.tracks.append(events_to_track("Trombones_Microtonales", 1, tromb_ev))
    mid.tracks.append(events_to_track("Estribillo_Tonic_Penultimate", 2, lead_ev))
    mid.tracks.append(events_to_track("Sub_Rumble_Tecno_D", 3, bass_ev))

    out_mid.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(out_mid))
    return out_mid


def export_fl_assets(
    bounces_dir: Optional[Path] = None,
    fl_user_dir: Optional[Path] = None,
    sections: Sequence[Tuple[str, int, int, int]] = SECTIONS_PLAN,
) -> Dict[str, Path]:
    """Exporta MIDI multimétrico, Scala (.scl/.kbm) y script de Piano Roll FL Studio."""
    b_dir = Path(bounces_dir) if bounces_dir is not None else resolve_bounces_dir()
    u_dir = Path(fl_user_dir) if fl_user_dir is not None else resolve_fl_user_dir()

    b_dir.mkdir(parents=True, exist_ok=True)
    tuning_dir = u_dir / "Settings" / "Tuning"
    scripts_dir = u_dir / "Settings" / "Piano roll scripts"
    tuning_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)

    mid_path = build_midi(b_dir / "SIKAH_128_Triptych_3_2_6_4_12_8.mid", sections=sections)

    scl_path = tuning_dir / "D_Maqam_Septimal_12.scl"
    scl_path.write_text(SCALA_SCL_CONTENT, encoding="utf-8")

    kbm_path = tuning_dir / "D_Maqam_Septimal_12.kbm"
    kbm_path.write_text(SCALA_KBM_CONTENT, encoding="utf-8")

    pyscript_path = scripts_dir / "SIKAH128_Estribillo.pyscript"
    pyscript_path.write_text(FL_PYSCRIPT_CONTENT, encoding="utf-8")

    # Espejo junto al bounce MIDI para portabilidad inmediata en FL Studio
    mirror_dir = b_dir / "SIKAH_128_Assets"
    mirror_dir.mkdir(parents=True, exist_ok=True)
    (mirror_dir / "D_Maqam_Septimal_12.scl").write_text(SCALA_SCL_CONTENT, encoding="utf-8")
    (mirror_dir / "D_Maqam_Septimal_12.kbm").write_text(SCALA_KBM_CONTENT, encoding="utf-8")
    (mirror_dir / "SIKAH128_Estribillo.pyscript").write_text(FL_PYSCRIPT_CONTENT, encoding="utf-8")

    return {
        "midi_path": mid_path,
        "scl_path": scl_path,
        "kbm_path": kbm_path,
        "pyscript_path": pyscript_path,
        "mirror_dir": mirror_dir,
    }


def _place_stereo(
    dest_l: np.ndarray,
    dest_r: np.ndarray,
    start_idx: int,
    mono_sig: np.ndarray,
    gain_l: float,
    gain_r: float,
) -> None:
    """Suma señal mono con ganancias L/R protegiendo límites negativos/superiores."""
    if start_idx >= len(dest_l) or len(mono_sig) == 0:
        return
    src_offset = 0
    dst_start = start_idx
    if dst_start < 0:
        src_offset = -dst_start
        dst_start = 0
    if src_offset >= len(mono_sig):
        return
    n_copy = min(len(mono_sig) - src_offset, len(dest_l) - dst_start)
    if n_copy <= 0:
        return
    seg = mono_sig[src_offset : src_offset + n_copy]
    dest_l[dst_start : dst_start + n_copy] += seg * gain_l
    dest_r[dst_start : dst_start + n_copy] += seg * gain_r


def _humanize_pitch_curve(
    freq_start: float,
    freq_end: float,
    duration_sec: float,
    glide_sec: float = 0.0,
    vib_hz: float = 4.8,
    vib_cents: float = 7.0,
    vib_delay_sec: float = 0.14,
    scoop_cents: float = -8.0,
    scoop_ms: float = 24.0,
    seed: int = 0,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Curva de afinación orgánica con scoop inicial, vibrato diferido y micro-deriva."""
    n_samp = max(256, int(round(duration_sec * sample_rate)))
    if glide_sec > 0.0 and abs(freq_end - freq_start) > 1e-3:
        n_glide = min(n_samp, max(16, int(round(glide_sec * sample_rate))))
        base = np.empty(n_samp, dtype=np.float64)
        t_norm = np.linspace(0.0, np.pi, n_glide, dtype=np.float64)
        base[:n_glide] = freq_start + (freq_end - freq_start) * 0.5 * (1.0 - np.cos(t_norm))
        base[n_glide:] = freq_end
    else:
        base = np.full(n_samp, freq_start, dtype=np.float64)

    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed)

    tau_scoop = max(0.004, scoop_ms / 1000.0)
    scoop = freeze_array(np.multiply(scoop_cents, np.exp(np.divide(-t, tau_scoop))))

    t_vib = freeze_array(np.maximum(0.0, np.subtract(t, vib_delay_sec)))
    vib_env = freeze_array(1.0 - np.exp(np.divide(-t_vib, 0.075)))
    vib_phase = rng.uniform(0.0, 2.0 * np.pi)
    vib_hz_eff = vib_hz * rng.uniform(0.95, 1.06)
    vib_sin = np.sin(np.add(np.multiply(2.0 * np.pi * vib_hz_eff, t), vib_phase))
    vib = freeze_array(np.multiply(np.multiply(vib_cents, vib_env), vib_sin))

    drift_depth = rng.uniform(-2.2, 2.2)
    drift_phase = rng.uniform(0.0, 2.0 * np.pi)
    drift = freeze_array(
        np.multiply(drift_depth, np.sin(np.add(2.0 * np.pi * 0.85 * t, drift_phase)))
    )

    cents_total = freeze_array(np.add(np.add(scoop, vib), drift))
    mult = freeze_array(np.power(2.0, np.divide(cents_total, 1200.0)))
    return freeze_array(np.multiply(freeze_array(base), mult))


def _band_formant(
    sig: np.ndarray,
    center_hz: float,
    rel_width: float = 0.28,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Resonador pasa-banda estable (Butterworth 2º orden) para cuerpo acústico."""
    nyq = 0.5 * float(sample_rate)
    low = max(40.0, center_hz * (1.0 - rel_width))
    high = min(nyq * 0.88, center_hz * (1.0 + rel_width))
    if high <= low * 1.05:
        return np.zeros_like(sig)
    sos = signal.butter(2, [low / nyq, high / nyq], btype="band", output="sos")
    return signal.sosfilt(sos, sig)


def _synth_brass_note(
    freq_start: float,
    freq_end: float,
    duration_sec: float,
    glide_sec: float = 0.0,
    seed: int = 101,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Trombón orgánico por síntesis armónica dinámica, formantes de pabellón y aire.

    Etiquetado estrictamente como AUTÓMATA_SINTÉTICO_ESTRUCTURAL.
    """
    curve = _humanize_pitch_curve(
        freq_start=freq_start,
        freq_end=freq_end,
        duration_sec=duration_sec,
        glide_sec=glide_sec,
        vib_hz=4.5,
        vib_cents=6.5,
        vib_delay_sec=0.18,
        scoop_cents=-11.0,
        scoop_ms=34.0,
        seed=seed,
        sample_rate=sample_rate,
    )
    n_samp = len(curve)
    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed + 17)

    phase = freeze_array(np.multiply(2.0 * np.pi / float(sample_rate), np.cumsum(curve)))
    breath = (1.0 - np.exp(np.divide(-t, 0.044))) * np.exp(
        np.divide(-t, max(0.35, duration_sec * 1.45))
    )
    b_max = max(float(np.max(breath)), 1e-9)
    breath = freeze_array(np.divide(breath, b_max))

    mean_f = max(40.0, float(np.mean(curve)))
    body = np.zeros(n_samp, dtype=np.float64)
    nyq_lim = 0.38 * float(sample_rate)
    for k in range(1, 13):
        fk = mean_f * float(k)
        if fk >= nyq_lim:
            break
        rolloff = 1.0 / (1.0 + (fk / 1150.0) ** 2)
        base_w = (1.0 / (float(k) ** 1.28)) * rolloff
        dyn_env = freeze_array(np.power(breath, 0.38 + 0.16 * float(k - 1)))
        ph_k = 0.0 if k == 1 else rng.uniform(0.0, 2.0 * np.pi)
        harmonic = np.sin(np.add(np.multiply(float(k), phase), ph_k))
        body += np.multiply(base_w, np.multiply(dyn_env, harmonic))

    bell_low = _band_formant(body, 275.0, rel_width=0.30, sample_rate=sample_rate)
    bell_mid = _band_formant(body, 620.0, rel_width=0.26, sample_rate=sample_rate)

    air_raw = rng.normal(0.0, 1.0, n_samp)
    air_band = _band_formant(air_raw, 1350.0, rel_width=0.45, sample_rate=sample_rate)
    air_env = freeze_array(np.add(np.multiply(0.065, np.exp(np.divide(-t, 0.032))), 0.018))
    brass_mix = body + 0.28 * bell_low + 0.16 * bell_mid + np.multiply(air_band, air_env)

    warm = oversampled_soft_saturate(brass_mix, drive_db=0.9, threshold_db=-2.8, asymmetry=0.02)
    cutoff = min(2350.0, max(540.0, mean_f * 7.2))
    sos = signal.butter(3, cutoff / (0.5 * float(sample_rate)), btype="low", output="sos")
    shaped = signal.sosfilt(sos, warm)
    peak = max(float(np.max(np.abs(shaped))), 1e-12)
    scaled = np.multiply(shaped, 0.62 / peak)
    return apply_zero_crackle_envelope(
        scaled, sample_rate=sample_rate, attack_ms=14.0, release_ms=42.0
    )


def _synth_lead_note(
    freq_start: float,
    freq_end: float,
    duration_sec: float,
    glide_sec: float = 0.0,
    seed: int = 303,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Solista orgánico de caña/madera microtonal con vibrato y formante vocal."""
    curve = _humanize_pitch_curve(
        freq_start=freq_start,
        freq_end=freq_end,
        duration_sec=duration_sec,
        glide_sec=glide_sec,
        vib_hz=5.1,
        vib_cents=8.5,
        vib_delay_sec=0.11,
        scoop_cents=-7.5,
        scoop_ms=18.0,
        seed=seed,
        sample_rate=sample_rate,
    )
    n_samp = len(curve)
    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed + 29)

    phase = freeze_array(np.multiply(2.0 * np.pi / float(sample_rate), np.cumsum(curve)))
    attack_arch = 1.0 - np.exp(np.divide(-t, 0.015))
    body_decay = 0.40 * np.exp(np.divide(-t, 0.14)) + 0.60 * np.exp(
        np.divide(-t, max(0.28, duration_sec * 1.45))
    )
    reed_env = attack_arch * body_decay
    reed_env = freeze_array(np.divide(reed_env, max(float(np.max(reed_env)), 1e-9)))

    mean_f = max(60.0, float(np.mean(curve)))
    voice = np.zeros(n_samp, dtype=np.float64)
    nyq_lim = 0.38 * float(sample_rate)
    for k in range(1, 11):
        if mean_f * float(k) >= nyq_lim:
            break
        odd_bias = 1.0 if (k % 2 == 1) else 0.60
        base_w = odd_bias / (float(k) ** 1.32)
        h_decay = freeze_array(np.exp(np.multiply(-0.42 * float(k - 1), t)))
        ph_k = 0.0 if k == 1 else rng.uniform(0.0, 2.0 * np.pi)
        harmonic = np.sin(np.add(np.multiply(float(k), phase), ph_k))
        voice += np.multiply(base_w, np.multiply(np.multiply(reed_env, h_decay), harmonic))

    wood_chest = _band_formant(voice, 680.0, rel_width=0.28, sample_rate=sample_rate)
    vowel_form = _band_formant(voice, 1340.0, rel_width=0.24, sample_rate=sample_rate)
    air_puff = _band_formant(
        rng.normal(0.0, 1.0, n_samp), 1850.0, rel_width=0.40, sample_rate=sample_rate
    )
    air_env = freeze_array(np.multiply(0.045, np.exp(np.divide(-t, 0.018))))
    reed_mix = voice + 0.25 * wood_chest + 0.14 * vowel_form + np.multiply(air_puff, air_env)

    warm = oversampled_soft_saturate(reed_mix, drive_db=0.75, threshold_db=-2.8, asymmetry=0.015)
    sos = signal.butter(3, 3200.0 / (0.5 * float(sample_rate)), btype="low", output="sos")
    filtered = signal.sosfilt(sos, warm)
    peak = max(float(np.max(np.abs(filtered))), 1e-12)
    scaled = np.multiply(filtered, 0.44 / peak)
    return apply_zero_crackle_envelope(
        scaled, sample_rate=sample_rate, attack_ms=9.0, release_ms=28.0
    )


def _synth_castanet_hit(
    center_hz: float,
    amplitude: float,
    seed: int = 0,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Choque físico de castañuela (4 modos de granadillo + rebote de concha, round-robin).

    Etiquetado estrictamente como AUTÓMATA_SINTÉTICO_ESTRUCTURAL.
    """
    dur_sec = 0.038
    n_samp = int(round(dur_sec * sample_rate))
    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed)

    f0 = center_hz * rng.uniform(0.968, 1.032)
    decay_scale = rng.uniform(0.90, 1.12)
    modal_ratios = (0.63, 1.00, 1.44, 2.19)
    modal_gains = (0.28, 0.52, 0.24, 0.11)

    knock = np.zeros(n_samp, dtype=np.float64)
    for ratio, gain in zip(modal_ratios, modal_gains):
        tau = (0.0048 * decay_scale) / math.sqrt(ratio)
        ph = rng.uniform(0.0, 2.0 * np.pi)
        env = np.exp(np.divide(-t, tau))
        knock += gain * env * np.sin(np.add(2.0 * np.pi * (f0 * ratio) * t, ph))

    wood_noise = _band_formant(
        rng.normal(0.0, 1.0, n_samp), f0 * 1.45, rel_width=0.55, sample_rate=sample_rate
    )
    knock += 0.22 * wood_noise * np.exp(np.divide(-t, 0.0018))

    # Doble rebote natural entre ambas hojas de la castañuela
    bounce_samples = int(round(rng.uniform(0.0032, 0.0049) * sample_rate))
    bounce_gain = rng.uniform(0.28, 0.40)
    full = knock.copy()
    if 0 < bounce_samples < n_samp:
        full[bounce_samples:] += bounce_gain * knock[: n_samp - bounce_samples]

    sos_hp = signal.butter(3, 280.0 / (0.5 * float(sample_rate)), btype="high", output="sos")
    clean = signal.sosfilt(sos_hp, full)
    peak = max(float(np.max(np.abs(clean))), 1e-12)
    burst = np.multiply(clean, amplitude / peak)
    return apply_zero_crackle_envelope(
        burst, sample_rate=sample_rate, attack_ms=0.9, release_ms=9.0
    )


def _synth_organic_sub_bass(
    freq_hz: float,
    duration_sec: float = 0.26,
    amplitude: float = 0.34,
    seed: int = 0,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Sub-rumble analógico coherente en fase (<190 Hz, fundamental + calidez 2º/3º armónico)."""
    n_samp = max(256, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed)

    settle = 3.5 * np.exp(np.divide(-t, 0.011))
    freq_curve = freeze_array(np.add(freq_hz * rng.uniform(0.9985, 1.0015), settle))
    phase = freeze_array(np.multiply(2.0 * np.pi / float(sample_rate), np.cumsum(freq_curve)))

    h1 = 0.84 * np.sin(phase)
    h2 = 0.14 * np.sin(np.multiply(2.0, phase))
    h3 = 0.06 * np.multiply(np.exp(np.divide(-t, 0.055)), np.sin(np.multiply(3.0, phase)))
    body_env = np.exp(np.divide(-t, max(0.14, duration_sec * 0.85)))
    raw = np.multiply(h1 + h2 + h3, body_env)

    sos_lp = signal.butter(3, 185.0 / (0.5 * float(sample_rate)), btype="low", output="sos")
    filt = signal.sosfilt(sos_lp, raw)
    peak = max(float(np.max(np.abs(filt))), 1e-12)
    scaled = np.multiply(filt, amplitude / peak)
    return apply_zero_crackle_envelope(
        scaled, sample_rate=sample_rate, attack_ms=6.5, release_ms=24.0
    )


def _stem_stats(left: np.ndarray, right: np.ndarray) -> Dict[str, float]:
    """Métricas de nivel y cresta para trazabilidad por stem."""
    mono = 0.5 * (left + right)
    peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
    rms = math.sqrt(float(np.mean(mono * mono)) + 1e-18)
    return {
        "peak_dbfs": round(20.0 * math.log10(max(peak, 1e-12)), 2),
        "rms_dbfs": round(20.0 * math.log10(max(rms, 1e-12)), 2),
    }


def _pan_gains(pan: float) -> Tuple[float, float]:
    """Paneo de potencia constante en [-1.0, +1.0]."""
    angle = (max(-1.0, min(1.0, pan)) + 1.0) * (np.pi / 4.0)
    return float(np.cos(angle)), float(np.sin(angle))


def render_verification_maquette(
    bounces_dir: Optional[Path] = None,
    sections: Sequence[Tuple[str, int, int, int]] = SECTIONS_PLAN,
    profile_name: str = "dub_techno",
    run_mastering: bool = True,
    run_linter_subprocess: bool = False,
) -> Dict[str, Any]:
    """Compila maqueta DSP 48 kHz / 24-bit orgánica y stems para auditoría Rubin."""
    b_dir = Path(bounces_dir) if bounces_dir is not None else resolve_bounces_dir()
    stems_dir = b_dir / "SIKAH_128_Stems_48k24b"
    stems_dir.mkdir(parents=True, exist_ok=True)

    total_bars = sum(n_bars for _, _, _, n_bars in sections)
    tail_sec = 1.8
    total_sec = total_bars * BAR_DURATION_SEC + tail_sec
    n_total = int(round(total_sec * SAMPLE_RATE))

    kick_l = np.zeros(n_total, dtype=np.float64)
    kick_r = np.zeros(n_total, dtype=np.float64)
    bass_l = np.zeros(n_total, dtype=np.float64)
    bass_r = np.zeros(n_total, dtype=np.float64)
    tromb_l = np.zeros(n_total, dtype=np.float64)
    tromb_r = np.zeros(n_total, dtype=np.float64)
    lead_l = np.zeros(n_total, dtype=np.float64)
    lead_r = np.zeros(n_total, dtype=np.float64)
    cast_l = np.zeros(n_total, dtype=np.float64)
    cast_r = np.zeros(n_total, dtype=np.float64)

    kick_proto = synthesize_phase_locked_kick(
        sample_rate=SAMPLE_RATE,
        duration_sec=0.38,
        root_hz=note_name_to_hz("D1"),
        punch_hz=135.0,
        click_hz=1150.0,
        tau_click=0.0032,
        tau_punch=0.028,
        tau_body=0.195,
        drive_db=1.8,
        pultec_sub_gain=0.18,
        mud_notch_hz=195.0,
        beater_gain=0.07,
        beater_hz=1350.0,
    )
    kick_proto = freeze_array(
        apply_zero_crackle_envelope(
            kick_proto, sample_rate=SAMPLE_RATE, attack_ms=1.2, release_ms=15.0
        )
    )

    rng = np.random.default_rng(12864)
    macho_gl, macho_gr = _pan_gains(-0.26)
    hembra_gl, hembra_gr = _pan_gains(0.30)

    def _jitter_samp(max_ms: float) -> int:
        delta_ms = float(np.clip(rng.normal(0.0, max_ms * 0.45), -max_ms, max_ms))
        return int(round((delta_ms / 1000.0) * SAMPLE_RATE))

    kick_onsets: List[int] = []
    cur_tick = 0
    bar_idx = 0

    for label, _num, _den, n_bars in sections:
        for bar in range(n_bars):
            b0 = cur_tick
            is_pre_drop_vacuum = label == "6/4" and bar == n_bars - 1
            if label == "3/2":
                sec_gain = 0.85 + 0.03 * min(bar, 3)
            elif label == "6/4":
                sec_gain = 0.72 if is_pre_drop_vacuum else 0.96
            else:
                sec_gain = 1.04

            if label == "3/2":
                kick_grid = [0, 960, 1920]
            elif label == "6/4":
                kick_grid = (
                    [0, 480, 960, 1440]
                    if is_pre_drop_vacuum
                    else [0, 480, 960, 1440, 1920, 2400]
                )
            else:
                kick_grid = [0, 720, 1440, 2160]

            for idx_k, k_off in enumerate(kick_grid):
                k_jit = 0 if idx_k == 0 else _jitter_samp(0.8)
                s_idx = max(0, tick_to_sample(b0 + k_off) + k_jit)
                kick_onsets.append(s_idx)
                k_vel = (0.56 if idx_k == 0 else 0.51) * sec_gain * rng.uniform(0.97, 1.03)
                _place_stereo(kick_l, kick_r, s_idx, np.multiply(kick_proto, k_vel), 1.0, 1.0)

            # Sub-Rumble Analógico D2 con groove orgánico
            if not is_pre_drop_vacuum:
                bass_grid = [240, 1200, 2160] if label == "3/2" else [240, 960, 1680, 2400]
                f_d2 = note_name_to_hz("D2")
                for idx_b, b_off in enumerate(bass_grid):
                    pocket_jit = int(round((rng.uniform(0.0004, 0.0018)) * SAMPLE_RATE))
                    s_idx = tick_to_sample(b0 + b_off) + pocket_jit
                    b_amp = 0.34 * sec_gain * rng.uniform(0.92, 1.06)
                    b_sig = _synth_organic_sub_bass(
                        f_d2,
                        duration_sec=0.26,
                        amplitude=b_amp,
                        seed=4000 + bar_idx * 16 + idx_b,
                        sample_rate=SAMPLE_RATE,
                    )
                    _place_stereo(bass_l, bass_r, s_idx, b_sig, 1.0, 1.0)

            # Castañuelas de Granadillo (Macho & Hembra carretillas con round-robin)
            if not is_pre_drop_vacuum:
                macho_offs = (
                    [960, 2400]
                    if label == "3/2"
                    else ([1440] if label == "6/4" else [720, 2160])
                )
                for idx_m, m_off in enumerate(macho_offs):
                    m_hit = _synth_castanet_hit(
                        1160.0,
                        amplitude=0.145 * sec_gain * rng.uniform(0.86, 1.12),
                        seed=1000 + bar_idx * 32 + idx_m,
                        sample_rate=SAMPLE_RATE,
                    )
                    _place_stereo(
                        cast_l,
                        cast_r,
                        tick_to_sample(b0 + m_off) + _jitter_samp(2.4),
                        m_hit,
                        macho_gl,
                        macho_gr,
                    )

                carretilla_anchor = 1920 if label in ("3/2", "6/4") else 1800
                carretilla_gain = 0.78 if (label == "3/2" and bar % 2 == 0) else 1.0
                for idx_c, (dt, scale_v) in enumerate(
                    [(0, 0.50), (72, 0.68), (138, 0.84), (198, 1.00)]
                ):
                    h_hit = _synth_castanet_hit(
                        1720.0,
                        amplitude=0.115 * scale_v * sec_gain * carretilla_gain,
                        seed=2000 + bar_idx * 32 + idx_c,
                        sample_rate=SAMPLE_RATE,
                    )
                    _place_stereo(
                        cast_l,
                        cast_r,
                        tick_to_sample(b0 + carretilla_anchor + dt) + _jitter_samp(2.0),
                        h_hit,
                        hembra_gl,
                        hembra_gr,
                    )

            # Trombones Bajo D2 + Tenor 11/8 con embocadura humana y aire
            brass_seed = 3000 + bar_idx * 8
            d2_sig = _synth_brass_note(
                note_name_to_hz("D2"),
                note_name_to_hz("D2"),
                duration_sec=0.92,
                seed=brass_seed,
                sample_rate=SAMPLE_RATE,
            )
            d2_gain = 0.27 * sec_gain * rng.uniform(0.94, 1.06)
            _place_stereo(
                tromb_l,
                tromb_r,
                tick_to_sample(b0) + _jitter_samp(2.5),
                np.multiply(d2_sig, d2_gain),
                0.80,
                0.76,
            )

            if not is_pre_drop_vacuum:
                t_tr = b0 + (1920 if label == "3/2" else 1440)
                tenor_sig = _synth_brass_note(
                    note_name_to_hz("G3"),
                    note_name_to_hz("Gs_11th3"),
                    duration_sec=0.60,
                    glide_sec=0.19,
                    seed=brass_seed + 1,
                    sample_rate=SAMPLE_RATE,
                )
                tr_gl, tr_gr = _pan_gains(-0.18)
                tr_gain = 0.31 * sec_gain * rng.uniform(0.93, 1.07)
                _place_stereo(
                    tromb_l,
                    tromb_r,
                    tick_to_sample(t_tr) + _jitter_samp(3.0),
                    np.multiply(tenor_sig, tr_gain),
                    tr_gl,
                    tr_gr,
                )

            # Estribillo Lead Melódico (n_7=D4 anteúltima, n_8=Eb_sikah4 última)
            offsets = CHORUS_OFFSETS_TICKS[label]
            for idx_n, ((n_name, dur_ticks), off_t) in enumerate(zip(CHORUS_MELODY, offsets)):
                if is_pre_drop_vacuum and idx_n < 6:
                    continue
                next_off = offsets[idx_n + 1] if idx_n + 1 < len(offsets) else BAR_TICKS
                eff_ticks = min(dur_ticks, max(80, next_off - off_t - 6))
                dur_sec = (eff_ticks / float(BAR_TICKS)) * BAR_DURATION_SEC + 0.015
                f_end = note_name_to_hz(n_name)
                if idx_n == 3:
                    f_start = note_name_to_hz("G4")
                    glide = 0.060
                else:
                    f_start = f_end
                    glide = 0.0
                v_sig = _synth_lead_note(
                    f_start,
                    f_end,
                    duration_sec=dur_sec,
                    glide_sec=glide,
                    seed=5000 + bar_idx * 16 + idx_n,
                    sample_rate=SAMPLE_RATE,
                )
                accent = 0.52 if idx_n in (0, 6, 7) else 0.40
                l_gain = accent * sec_gain * rng.uniform(0.93, 1.06)
                ld_gl, ld_gr = _pan_gains(0.11 if idx_n % 2 == 0 else -0.11)
                _place_stereo(
                    lead_l,
                    lead_r,
                    tick_to_sample(b0 + off_t) + _jitter_samp(2.1),
                    np.multiply(v_sig, l_gain),
                    ld_gl,
                    ld_gr,
                )

            cur_tick += BAR_TICKS
            bar_idx += 1

    # Procesado espectral C5-REAL: Sidechain multibanda + Carving + Dub Echo + Sala
    sc_sub, sc_high = build_coupled_multiband_sidechain(
        n_total, kick_onsets, sample_rate=SAMPLE_RATE, tau_body=0.195, sub_depth=0.90, high_depth=0.20
    )
    sc_sub.flags.writeable = False
    sc_high.flags.writeable = False

    def _apply_multiband_sc(left: np.ndarray, right: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        l_sub, l_hi = lr4_zero_phase_crossover(left, 140.0, SAMPLE_RATE)
        r_sub, r_hi = lr4_zero_phase_crossover(right, 140.0, SAMPLE_RATE)
        l_sub.flags.writeable = False
        l_hi.flags.writeable = False
        r_sub.flags.writeable = False
        r_hi.flags.writeable = False
        return (l_sub * sc_sub + l_hi * sc_high), (r_sub * sc_sub + r_hi * sc_high)

    bass_l, bass_r = _apply_multiband_sc(bass_l, bass_r)
    bass_l, bass_r = enforce_low_end_mono(bass_l, bass_r, cutoff_hz=120.0, sample_rate=SAMPLE_RATE)

    tromb_l, tromb_r = carve_polyphonic_mud(
        tromb_l, tromb_r, sample_rate=SAMPLE_RATE, hpf_hz=85.0, mud_hz=260.0, mud_cut_blend=0.38
    )
    tromb_l, tromb_r = _apply_multiband_sc(tromb_l, tromb_r)

    lead_l, lead_r = carve_polyphonic_mud(
        lead_l, lead_r, sample_rate=SAMPLE_RATE, hpf_hz=185.0, mud_hz=375.0, mud_cut_blend=0.42
    )
    lead_l, lead_r = apply_noncommutative_dub_echo(
        lead_l,
        lead_r,
        sample_rate=SAMPLE_RATE,
        delay_sec=0.3125,  # 2 corcheas exactas @ 384 corcheas/min
        feedback=0.40,
        lpf_hz=2350.0,
        hpf_hz=240.0,
        wet=0.28,
        taps=4,
    )
    lead_l, lead_r = _apply_multiband_sc(lead_l, lead_r)

    # Inmutabilizar stems antes de sumas lineales (protección CPython 3.14 LOAD_FAST_BORROW)
    for stem_buf in (
        kick_l,
        kick_r,
        bass_l,
        bass_r,
        tromb_l,
        tromb_r,
        lead_l,
        lead_r,
        cast_l,
        cast_r,
    ):
        stem_buf.flags.writeable = False

    # Sala compartida de madera para integración física trombones + lead + castañuelas
    room_in_l = tromb_l * 0.52 + lead_l * 0.48 + cast_l * 0.32
    room_in_r = tromb_r * 0.52 + lead_r * 0.48 + cast_r * 0.32
    room_l, room_r = apply_coherent_shared_room(
        room_in_l, room_in_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, rt60_sec=1.40, wet=0.18
    )
    room_l.flags.writeable = False
    room_r.flags.writeable = False

    # Lecho continuo analógico a -57 dBFS (cero digital prohibido, protege pre-drop)
    tape_l, tape_r = generate_warm_analog_tape_bed(
        n_total, sample_rate=SAMPLE_RATE, level_dbfs=-57.0, seed=1995
    )
    tape_l.flags.writeable = False
    tape_r.flags.writeable = False

    pre_l = kick_l + bass_l + tromb_l + lead_l + cast_l + room_l * 0.40 + tape_l
    pre_r = kick_r + bass_r + tromb_r + lead_r + cast_r + room_r * 0.40 + tape_r

    pre_l = oversampled_soft_saturate(pre_l, drive_db=0.80, threshold_db=-2.6, asymmetry=0.02)
    pre_r = oversampled_soft_saturate(pre_r, drive_db=0.80, threshold_db=-2.6, asymmetry=0.02)
    # Mono sub-bass DESPUÉS de saturar para garantizar LPC >= 0.99 sin intermodulación lateral
    pre_l, pre_r = enforce_low_end_mono(pre_l, pre_r, cutoff_hz=120.0, sample_rate=SAMPLE_RATE)

    # Envolvente final sin clicks en apertura/cierre de archivo
    pre_l = apply_zero_crackle_envelope(pre_l, sample_rate=SAMPLE_RATE, attack_ms=15.0, release_ms=180.0)
    pre_r = apply_zero_crackle_envelope(pre_r, sample_rate=SAMPLE_RATE, attack_ms=15.0, release_ms=180.0)

    peak_pre = float(max(np.max(np.abs(pre_l)), np.max(np.abs(pre_r)), 1e-12))
    target_pre_peak = 0.78
    if peak_pre > target_pre_peak:
        scale_headroom = target_pre_peak / peak_pre
        pre_l = pre_l * scale_headroom
        pre_r = pre_r * scale_headroom
    pre_l.flags.writeable = False
    pre_r.flags.writeable = False

    stem_files = {
        "kick": write_pcm_wav(stems_dir / "01_Kick_Techno_D1.wav", kick_l, kick_r, SAMPLE_RATE, 24),
        "rumble_bass": write_pcm_wav(
            stems_dir / "02_Sub_Rumble_Tecno_D.wav", bass_l, bass_r, SAMPLE_RATE, 24
        ),
        "trombones": write_pcm_wav(
            stems_dir / "03_Trombones_Maqueta_DSP.wav", tromb_l, tromb_r, SAMPLE_RATE, 24
        ),
        "lead_estribillo": write_pcm_wav(
            stems_dir / "04_Estribillo_Sikah_Lead.wav", lead_l, lead_r, SAMPLE_RATE, 24
        ),
        "castanets": write_pcm_wav(
            stems_dir / "05_Castanuelas_Maqueta_DSP.wav", cast_l, cast_r, SAMPLE_RATE, 24
        ),
        "tape_bed": write_pcm_wav(
            stems_dir / "06_Analog_Tape_Bed_57dBFS.wav", tape_l, tape_r, SAMPLE_RATE, 24
        ),
    }

    premaster_path = write_pcm_wav(
        b_dir / "SIKAH_128_Maquette_Premaster_48k24b.wav", pre_l, pre_r, SAMPLE_RATE, 24
    )

    mastered_path = b_dir / f"SIKAH_128_Maquette_Master_{profile_name}_48k24b.wav"
    master_report: Optional[Dict[str, Any]] = None
    if run_mastering:
        master_report = master_audio_reverse_engineered(
            str(premaster_path),
            str(mastered_path),
            profile_name=profile_name,
            bit_depth=24,
        )

    rubin_pre = compute_rubin_metrics(pre_l, pre_r, sample_rate=SAMPLE_RATE)
    crackle_check_sub = check_zero_crackle_derivatives(0.5 * (bass_l + bass_r))
    pre_sub_mono, _ = lr4_zero_phase_crossover(
        0.5 * (pre_l + pre_r), crossover_hz=120.0, sample_rate=SAMPLE_RATE
    )
    crackle_check_sub_bass = check_zero_crackle_derivatives(pre_sub_mono)
    per_stem_stats = {
        "kick": _stem_stats(kick_l, kick_r),
        "rumble_bass": _stem_stats(bass_l, bass_r),
        "trombones": _stem_stats(tromb_l, tromb_r),
        "lead_estribillo": _stem_stats(lead_l, lead_r),
        "castanets": _stem_stats(cast_l, cast_r),
    }

    linter_stdout: Optional[str] = None
    target_audit = mastered_path if (run_mastering and mastered_path.exists()) else premaster_path
    if run_linter_subprocess and RUBIN_LINTER_PATH.exists():
        proc = subprocess.run(
            [sys.executable, str(RUBIN_LINTER_PATH), str(target_audit)],
            capture_output=True,
            text=True,
            check=False,
        )
        linter_stdout = proc.stdout if proc.returncode == 0 else (proc.stdout + "\n" + proc.stderr)

    audit_summary = {
        "project": "SIKAH-128",
        "engine_version": "organic_v2",
        "classification": "AUTÓMATA_SINTÉTICO_ESTRUCTURAL",
        "gate_notice": (
            "Maqueta DSP sintética orgánica (48 kHz / 24-bit). "
            "No sustituye grabación acústica humana ni librerías multi-round-robin finales."
        ),
        "sample_rate": SAMPLE_RATE,
        "duration_sec": round(n_total / float(SAMPLE_RATE), 4),
        "premaster_wav": str(premaster_path),
        "mastered_wav": str(mastered_path) if run_mastering else None,
        "stems": {k: str(v) for k, v in stem_files.items()},
        "per_stem_stats": per_stem_stats,
        "rubin_premaster": rubin_pre,
        "master_report": master_report,
        "crackle_check_premaster": crackle_check_sub,
        "crackle_check_sub_bass": crackle_check_sub_bass,
        "rubin_linter_stdout": linter_stdout,
    }
    audit_json_path = b_dir / "SIKAH_128_Render_Audit.json"
    audit_json_path.write_text(json.dumps(audit_summary, indent=2, default=str), encoding="utf-8")
    audit_summary["audit_json"] = str(audit_json_path)
    return audit_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generador SIKAH-128 (3/2 -> 6/4 -> 12/8).")
    parser.add_argument("--bounces-dir", type=Path, default=None, help="Directorio de bounces.")
    parser.add_argument("--fl-user-dir", type=Path, default=None, help="Directorio FL Studio User.")
    parser.add_argument(
        "--render-maquette",
        action="store_true",
        help="Compila stems + maqueta WAV 48 kHz/24-bit y ejecuta auditoría Rubin.",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="dub_techno",
        help="Perfil de masterización (dub_techno, club_c5, techno, streaming_sota).",
    )
    parser.add_argument(
        "--run-linter",
        action="store_true",
        help="Invoca audit_acoustic_exergy.py sobre el WAV generado si --render-maquette está activo.",
    )
    args = parser.parse_args()

    assets = export_fl_assets(bounces_dir=args.bounces_dir, fl_user_dir=args.fl_user_dir)
    print(json.dumps({"exported_assets": {k: str(v) for k, v in assets.items()}}, indent=2))

    if args.render_maquette:
        render_out = render_verification_maquette(
            bounces_dir=args.bounces_dir,
            profile_name=args.profile,
            run_mastering=True,
            run_linter_subprocess=args.run_linter,
        )
        print(json.dumps(render_out, indent=2, default=str))


if __name__ == "__main__":
    main()
