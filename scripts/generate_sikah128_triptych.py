#!/usr/bin/env python3
"""
SIKAH-128: Generador Simbólico Multimétrico (3/2 -> 6/4 -> 12/8), Microtonal y Maqueta DSP.

- Exporta SMF Tipo 1 (.mid) con modulación métrica isócrona 3/2 -> 6/4 -> 12/8
  (2880 ticks/compás @ 480 PPQ; 230.4 corcheas/min => 12/8 a 76.8 BPM, 40% más lento).
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
        polyblep_pulse,
        polyblep_saw,
        synthesize_phase_locked_kick,
        write_pcm_wav,
    )
    from scripts.mastering_reverse_engine_fl import (
        compute_rubin_metrics,
        load_wav_stereo,
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
        polyblep_pulse,
        polyblep_saw,
        synthesize_phase_locked_kick,
        write_pcm_wav,
    )
    from mastering_reverse_engine_fl import (
        compute_rubin_metrics,
        load_wav_stereo,
        master_audio_reverse_engineered,
    )

PPQ = 480
BAR_TICKS = 2880  # 12 corcheas * 240 ticks = 6 negras * 480 ticks
QUARTER_BPM = 115.2  # 40% más lento (230.4 corcheas/min => 3/2=57.6, 6/4=38.4/115.2, 12/8=76.8 BPM)
BAR_DURATION_SEC = (6.0 / QUARTER_BPM) * 60.0  # 3.125 s exactos por compás
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


def _voss_clarke_1f_drift(n_samples: int, seed: int = 128) -> np.ndarray:
    """Curva fractal 1/f determinista (Voss-Clarke) suave en [-1.0, +1.0] para deriva analógica."""
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float64)
    n = max(64, int(n_samples))
    rng = np.random.default_rng(seed)
    white = rng.normal(0.0, 1.0, n)
    spec = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1.0 / float(SAMPLE_RATE))
    # Limitar deriva térmica a bajas frecuencias (< 3.5 Hz) para evitar aspereza FM
    mask = ((freqs >= 0.04) & (freqs <= 3.5)).astype(np.float64)
    safe_f = np.maximum(freqs, 0.04)
    shaped = spec * mask / np.sqrt(safe_f)
    drift = np.fft.irfft(shaped, n=n)[:n_samples]
    std = float(np.std(drift))
    if std > 1e-9:
        drift = drift / std
    return freeze_array(np.tanh(drift * 0.55) / math.tanh(1.1))


def _band_formant(
    sig: np.ndarray,
    center_hz: float,
    rel_width: float = 0.28,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Resonador pasa-banda estable (Butterworth 2º orden) para cavidades físicas."""
    nyq = 0.5 * float(sample_rate)
    low = max(40.0, center_hz * (1.0 - rel_width))
    high = min(nyq * 0.88, center_hz * (1.0 + rel_width))
    if high <= low * 1.05:
        return np.zeros_like(sig)
    sos = signal.butter(2, [low / nyq, high / nyq], btype="band", output="sos")
    return signal.sosfilt(sos, sig)


def _dynamic_analog_ladder_filter(
    sig: np.ndarray,
    cutoff_hz_curve: np.ndarray,
    resonance: float = 0.42,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """
    Filtro escalera analógico variante en el tiempo (24 dB/oct + pico resonante de esquina)
    evaluado sin clicks ni ruido de cremallera mediante banco logarítmico de 9 nodos C-vectorizados.
    """
    n = len(sig)
    if n == 0:
        return np.zeros(0, dtype=np.float64)

    grid_hz = np.array(
        [185.0, 275.0, 410.0, 610.0, 905.0, 1340.0, 1980.0, 2920.0, 4250.0],
        dtype=np.float64,
    )
    nyq = 0.5 * float(sample_rate)
    src = freeze_array(np.asarray(sig, dtype=np.float64))
    bands = np.empty((len(grid_hz), n), dtype=np.float64)

    for idx, fc in enumerate(grid_hz):
        wn = min(0.88, fc / nyq)
        sos_lp = signal.butter(4, wn, btype="low", output="sos")
        lp = signal.sosfilt(sos_lp, src)
        if resonance > 0.02:
            b_pk, a_pk = signal.iirpeak(min(nyq * 0.84, fc * 0.90), Q=2.4, fs=sample_rate)
            pk = signal.lfilter(b_pk, a_pk, lp)
            bands[idx] = lp + resonance * pk
        else:
            bands[idx] = lp

    fc_clamped = np.clip(cutoff_hz_curve, grid_hz[0], grid_hz[-1] - 1e-3)
    log_min = math.log(grid_hz[0])
    log_step = math.log(grid_hz[1] / grid_hz[0])
    u = (np.log(fc_clamped) - log_min) / log_step
    idx_lo = np.clip(np.floor(u).astype(np.int32), 0, len(grid_hz) - 2)
    frac = freeze_array(u - idx_lo.astype(np.float64))

    samples_idx = np.arange(n, dtype=np.intp)
    v0 = freeze_array(bands[idx_lo, samples_idx])
    v1 = freeze_array(bands[idx_lo + 1, samples_idx])
    return freeze_array(v0 + frac * (v1 - v0))


def _apply_analog_bbd_chorus(
    mono_sig: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
    depth_ms: float = 2.4,
    rate_hz: float = 0.42,
    mix: float = 0.28,
) -> Tuple[np.ndarray, np.ndarray]:
    """Chorus analógico BBD estéreo aplicado estrictamente por encima de 165 Hz."""
    n = len(mono_sig)
    if n < 64:
        return mono_sig.copy(), mono_sig.copy()
    lo, hi = lr4_zero_phase_crossover(mono_sig, 165.0, sample_rate)
    lo = freeze_array(lo)
    hi = freeze_array(hi)

    t = make_time_axis(n, sample_rate)
    base_d = 0.0085 * sample_rate
    mod_d = (depth_ms / 1000.0) * sample_rate
    idx_base = np.arange(n, dtype=np.float64)

    pos_l = np.clip(idx_base - (base_d + mod_d * np.sin(2.0 * math.pi * rate_hz * t)), 0.0, n - 1.001)
    pos_r = np.clip(
        idx_base - (base_d + mod_d * np.cos(2.0 * math.pi * (rate_hz * 1.09) * t)),
        0.0,
        n - 1.001,
    )

    def _interp_delay(buf: np.ndarray, pos: np.ndarray) -> np.ndarray:
        i0 = pos.astype(np.intp)
        fr = pos - i0
        return buf[i0] * (1.0 - fr) + buf[i0 + 1] * fr

    wet_l = freeze_array(_interp_delay(hi, pos_l))
    wet_r = freeze_array(_interp_delay(hi, pos_r))
    out_l = lo + (1.0 - 0.35 * mix) * hi + mix * wet_l
    out_r = lo + (1.0 - 0.35 * mix) * hi + mix * wet_r
    return freeze_array(out_l), freeze_array(out_r)


def _render_cavern_kick_rumble(
    kick_mono: np.ndarray,
    sections: Sequence[Tuple[str, int, int, int]],
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """
    Rumble subterráneo de club (topología Berghain / Maceo Plex, CERO notas sawtooth MIDI):
      1. Envía el propio Kick D1 a reflexiones oscuras pre-filtradas (3/16, 1/8, 5/16) + caverna.
      2. Satura por transformador asimétrico y filtra a 102 Hz (24 dB/oct) con muesca anti-barro.
      3. Funde una onda de presión subgrave continua en D1/D2 con deriva 1/f y laid-back (+7 ms),
         evacuando por completo el vacío Pre-Drop del compás 6/4 final.
    """
    n_total = len(kick_mono)
    src = freeze_array(np.asarray(kick_mono, dtype=np.float64))
    nyq = 0.5 * float(sample_rate)

    # 1. Reflexiones de caverna acopladas al tempo (1 corchea = BAR_DURATION_SEC / 12)
    eighth_sec = BAR_DURATION_SEC / 12.0
    taps_cfg = [
        (eighth_sec * 0.75, 0.58),
        (eighth_sec * 1.00, 0.72),
        (eighth_sec * 1.50, 0.54),
        (eighth_sec * 2.00, 0.40),
        (eighth_sec * 2.50, 0.28),
    ]
    cavern = np.zeros(n_total, dtype=np.float64)
    sos_pre = signal.butter(2, [32.0 / nyq, 145.0 / nyq], btype="band", output="sos")
    k_band = freeze_array(signal.sosfilt(sos_pre, src))
    for d_sec, g_tap in taps_cfg:
        shift = int(round(d_sec * sample_rate))
        if 0 < shift < n_total:
            cavern[shift:] += g_tap * k_band[:-shift]

    # Difusión corta de caverna subterránea (sin cola aguda)
    rng = np.random.default_rng(3671)
    ir_len = int(round(0.46 * sample_rate))
    t_ir = make_time_axis(ir_len, sample_rate)
    ir_Sub = rng.normal(0.0, 1.0, ir_len) * np.exp(-t_ir / 0.13)
    ir_Sub = signal.sosfilt(sos_pre, ir_Sub)
    ir_Sub /= math.sqrt(float(np.dot(ir_Sub, ir_Sub)) + 1e-12)
    diffused = signal.fftconvolve(cavern, ir_Sub, mode="full")[:n_total]

    driven = oversampled_soft_saturate(
        0.65 * cavern + 0.55 * diffused, drive_db=4.4, threshold_db=-6.0, asymmetry=0.05
    )

    # 2. Presión subgrave continua (D1 + octava D2 suave, cero blips oom-pah)
    drift = _voss_clarke_1f_drift(n_total, seed=7342)
    f_d1 = note_name_to_hz("D1")
    f_d2 = note_name_to_hz("D2")
    f_inst = freeze_array(f_d1 * np.power(2.0, (drift * 2.2) / 1200.0))
    ph_d1 = freeze_array((2.0 * math.pi / float(sample_rate)) * np.cumsum(f_inst))
    sub_drone = 0.76 * np.sin(ph_d1) + 0.24 * np.sin(2.0 * ph_d1 + 0.35)

    # Envolvente macro por sección y evacuación estricta en el Pre-Drop Vacuum
    env_macro = np.zeros(n_total, dtype=np.float64)
    cur_tick = 0
    pocket_samp = int(round(0.0068 * sample_rate))
    for label, _num, _den, n_bars in sections:
        for bar in range(n_bars):
            s0 = min(n_total, tick_to_sample(cur_tick) + pocket_samp)
            s1 = min(n_total, tick_to_sample(cur_tick + BAR_TICKS) + pocket_samp)
            is_vacuum = label == "6/4" and bar == n_bars - 1
            if is_vacuum:
                # Corta en seco en la segunda mitad del compás Pre-Drop
                s_mid = min(n_total, tick_to_sample(cur_tick + 1440))
                if s_mid > s0:
                    env_macro[s0:s_mid] = 0.72
            else:
                lvl = 0.68 if label == "3/2" else (0.84 if label == "6/4" else 1.0)
                env_macro[s0:s1] = lvl
            cur_tick += BAR_TICKS

    # Suavizar transiciones de envolvente macro (raised-cosine / Hanning 28 ms) para 0 crackle
    k_smooth = max(9, int(round(0.028 * sample_rate)) | 1)
    win = np.hanning(k_smooth)
    win /= np.sum(win)
    env_smooth = freeze_array(
        np.convolve(np.pad(env_macro, k_smooth // 2, mode="edge"), win, mode="valid")[:n_total]
    )

    breath_mod = freeze_array(0.86 + 0.14 * _voss_clarke_1f_drift(n_total, seed=909))
    combined = (0.62 * driven + 0.24 * sub_drone * breath_mod) * env_smooth

    # Filtro paso-bajo de subgrave estricto a 98 Hz -> garantiza derivadas d1/d2 ultra-limpias
    sos_sub_lp = signal.butter(4, 98.0 / nyq, btype="low", output="sos")
    sos_sub_hp = signal.butter(2, 29.0 / nyq, btype="high", output="sos")
    rumble = signal.sosfiltfilt(sos_sub_lp, signal.sosfiltfilt(sos_sub_hp, combined))
    # Refuerzo armónico sutil en D2 (73.4 Hz)
    b_pultec, a_pultec = signal.iirpeak(f_d2, Q=2.8, fs=sample_rate)
    rumble_f = freeze_array(rumble)
    rumble = 0.82 * rumble_f + 0.18 * signal.lfilter(b_pultec, a_pultec, rumble_f)

    peak = max(float(np.max(np.abs(rumble))), 1e-12)
    rumble = np.multiply(rumble, 0.33 / peak)
    return freeze_array(
        apply_zero_crackle_envelope(rumble, sample_rate=sample_rate, attack_ms=18.0, release_ms=80.0)
    )


def _synth_cs80_brass_swell(
    voices_hz: Sequence[Tuple[float, float, float]],
    duration_sec: float,
    cutoff_start_hz: float = 190.0,
    cutoff_peak_hz: float = 1120.0,
    cutoff_end_hz: float = 240.0,
    peak_pos: float = 0.58,
    amplitude: float = 0.26,
    seed: int = 202,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Cuerno / metal grave analógico estilo CS-80 / Bodzin (CERO trombón General MIDI):
      - Múltiples voces con portamento continuo (f_start -> f_end, glide_ratio),
      - Deriva térmica 1/f independiente por oscilador (PolyBLEP saw + pulse + sub),
      - Plegado de onda suave dependiente de la presión (harmonic bloom),
      - Filtro escalera de 24 dB/oct barriendo continuamente cutoff_start -> cutoff_peak -> cutoff_end,
      - Chorus analógico BBD por encima de 165 Hz.
    """
    n_samp = max(512, int(round(duration_sec * sample_rate)))
    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed)

    # Curva de respiración lenta (swell cinematográfico, ataque suave de 180-320 ms)
    u = np.clip(t / max(duration_sec, 1e-4), 0.0, 1.0)
    p = float(np.clip(peak_pos, 0.20, 0.85))
    rise = 0.5 * (1.0 - np.cos(math.pi * np.clip(u / p, 0.0, 1.0)))
    fall = 0.35 + 0.65 * (0.5 * (1.0 + np.cos(math.pi * np.clip((u - p) / (1.0 - p), 0.0, 1.0))))
    swell = freeze_array(np.where(u <= p, rise, fall))

    mix_mono = np.zeros(n_samp, dtype=np.float64)
    for v_idx, (f_start, f_end, glide_frac) in enumerate(voices_hz):
        if glide_frac > 0.01 and abs(f_end - f_start) > 1e-3:
            n_gl = min(n_samp, max(32, int(round(duration_sec * glide_frac * sample_rate))))
            f_base = np.empty(n_samp, dtype=np.float64)
            # Retrasar inicio del glissando un 22% para apoyar primero la nota real
            n_hold = min(n_samp // 3, int(round(0.22 * duration_sec * sample_rate)))
            n_move = max(16, min(n_gl, n_samp - n_hold))
            f_base[:n_hold] = f_start
            ramp = 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, n_move)))
            f_base[n_hold : n_hold + n_move] = f_start + (f_end - f_start) * ramp
            f_base[n_hold + n_move :] = f_end
        else:
            f_base = np.full(n_samp, f_start, dtype=np.float64)

        drift_a = _voss_clarke_1f_drift(n_samp, seed=seed * 13 + v_idx * 7 + 1)
        drift_b = _voss_clarke_1f_drift(n_samp, seed=seed * 13 + v_idx * 7 + 2)
        f_a = freeze_array(f_base * np.power(2.0, (-4.2 + 3.8 * drift_a) / 1200.0))
        f_b = freeze_array(f_base * np.power(2.0, (4.4 + 3.8 * drift_b) / 1200.0))

        saw = polyblep_saw(f_a, n_samp, sample_rate=sample_rate, initial_phase=rng.uniform(0.0, 1.0))
        pls = polyblep_pulse(
            f_b, n_samp, sample_rate=sample_rate, duty=0.44, initial_phase=rng.uniform(0.0, 1.0)
        )
        ph_sub = (2.0 * math.pi / float(sample_rate)) * np.cumsum(f_base * 0.5)
        sub = 0.28 * np.sin(ph_sub)
        v_weight = 1.0 / math.sqrt(float(len(voices_hz)))
        mix_mono += v_weight * (0.46 * saw + 0.36 * pls + sub)

    # Saturación progresiva asimétrica de pabellón de latón: suave en pianissimo, mordiente en pico
    dyn_drive = freeze_array(0.65 + 1.35 * swell)
    asym = freeze_array(mix_mono + 0.08 * (mix_mono * mix_mono))
    folded = np.tanh(asym * dyn_drive)

    # Barrido continuo del filtro escalera de 24 dB/oct
    fc_rise = cutoff_start_hz + (cutoff_peak_hz - cutoff_start_hz) * rise
    fc_fall = cutoff_end_hz + (cutoff_peak_hz - cutoff_end_hz) * (
        0.5 * (1.0 + np.cos(math.pi * np.clip((u - p) / (1.0 - p), 0.0, 1.0)))
    )
    cutoff_curve = freeze_array(np.where(u <= p, fc_rise, fc_fall))
    sculpted = _dynamic_analog_ladder_filter(
        folded, cutoff_curve, resonance=0.44, sample_rate=sample_rate
    )

    # Formantes reales de trombón / pabellón metálico (320 Hz tubo + 1060 Hz campana de bronce)
    bore_warmth = _band_formant(sculpted, 320.0, rel_width=0.30, sample_rate=sample_rate)
    bell_flare = _band_formant(sculpted, 1060.0, rel_width=0.25, sample_rate=sample_rate)

    # Soplo de embocadura y latón vivo
    air = _band_formant(rng.normal(0.0, 1.0, n_samp), 1320.0, rel_width=0.42, sample_rate=sample_rate)
    body = sculpted + 0.16 * bore_warmth + 0.24 * bell_flare
    with_air = body * (0.30 + 0.70 * swell) + 0.036 * air * swell

    peak = max(float(np.max(np.abs(with_air))), 1e-12)
    normed = apply_zero_crackle_envelope(
        np.multiply(with_air, amplitude / peak),
        sample_rate=sample_rate,
        attack_ms=65.0,
        release_ms=110.0,
    )
    return _apply_analog_bbd_chorus(normed, sample_rate=sample_rate, depth_ms=2.3, rate_hz=0.38, mix=0.30)


def _render_continuous_legato_lead(
    sections: Sequence[Tuple[str, int, int, int]],
    n_total: int,
    sample_rate: int = SAMPLE_RATE,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Circuito monofónico continuo de guía de ondas cúbica + filtro escalera resonante:
      - La fase del oscilador jamás se reinicia (0% efecto 'pit-pit-pit' MIDI).
      - Portamento RC analógico real entre notas ligadas y silencios respirados Call & Response.
      - Dramaturgia humana en 3 actos:
          * Acto I (3/2): Silencio y susurros velados del cierre Sikah (520-680 Hz) en compases impares.
          * Acto II (6/4): Llamada en hemiola, respuesta de eco dub en espacio y suspensión desnuda
            D4 (0c) -> Eb_sikah4 (+150c) en el vacío Pre-Drop.
          * Acto III (12/8): Diálogo Call & Response (frase completa ligada alternando con respuestas
            espaciadas, variaciones oscuras de filtro y Living Exit hacia la cola de cinta).
    """
    total_bars = sum(nb for _, _, _, nb in sections)
    short_mode = total_bars <= 4

    # Planificar eventos (start_samp, end_samp, freq_hz, expr_gain, cutoff_target_hz, is_slurred)
    events: List[Tuple[int, int, float, float, float, bool]] = []
    rng = np.random.default_rng(5128)
    cur_tick = 0
    bar_global = 0

    for label, _num, _den, n_bars in sections:
        offsets = CHORUS_OFFSETS_TICKS[label]
        for bar in range(n_bars):
            b0 = cur_tick
            is_vacuum = label == "6/4" and bar == n_bars - 1

            # Selección dramatúrgica de qué grados cantan realmente en este compás (anti-ringtone)
            if short_mode:
                if is_vacuum:
                    active_indices = [6, 7]
                elif label == "3/2":
                    active_indices = [6, 7]
                else:
                    active_indices = list(range(8))
                base_cutoff = 680.0 if label == "3/2" else (1150.0 if label == "6/4" else 1780.0)
                bar_expr = 0.62 if label == "3/2" else (0.82 if label == "6/4" else 0.98)
            else:
                if label == "3/2":
                    # Acto I: compases 0 y 2 dejan respirar la caverna; 1 y 3 insinúan la cadencia Sikah
                    if bar in (0, 2):
                        active_indices = []
                    elif bar == 1:
                        active_indices = [6, 7]
                    else:
                        active_indices = [4, 5, 6, 7]
                    base_cutoff = 520.0 + 75.0 * bar
                    bar_expr = 0.52 + 0.06 * bar
                elif label == "6/4":
                    if is_vacuum:
                        # Vacío Pre-Drop: solo la cadencia desnuda D4 (tónica anteúltima) -> Eb_sikah4 (+150c)
                        active_indices = [6, 7]
                        base_cutoff = 1320.0
                        bar_expr = 0.88
                    elif bar == 0:
                        active_indices = [0, 1, 2, 3, 4, 5, 6, 7]
                        base_cutoff = 920.0
                        bar_expr = 0.74
                    elif bar == 1:
                        # Respuesta espacial: deja sonar el eco dub en la 1ª mitad y remata al final
                        active_indices = [5, 6, 7]
                        base_cutoff = 840.0
                        bar_expr = 0.68
                    else:
                        active_indices = [2, 3, 4, 5, 6, 7]
                        base_cutoff = 1460.0
                        bar_expr = 0.86
                else:
                    # Acto III (12/8 Clímax): Call & Response real cada 2 compases
                    if bar in (0, 4):
                        active_indices = [0, 1, 2, 3, 4, 5, 6, 7]
                        base_cutoff = 1720.0 if bar == 0 else 2080.0
                        bar_expr = 0.96 if bar == 0 else 1.02
                    elif bar in (1, 5):
                        # El eco dub contesta en los pulsos 1-2; el solista cierra la frase
                        active_indices = [4, 5, 6, 7]
                        base_cutoff = 1280.0
                        bar_expr = 0.82
                    elif bar == 2:
                        # Variación íntima filtrada y sincopada
                        active_indices = [0, 2, 4, 5, 6, 7]
                        base_cutoff = 960.0
                        bar_expr = 0.78
                    elif bar == 3:
                        # Giro microtonal 11/8 hacia la suspensión Sikah
                        active_indices = [3, 5, 6, 7]
                        base_cutoff = 1480.0
                        bar_expr = 0.88
                    elif bar == 6:
                        # Ápice expresivo
                        active_indices = [0, 1, 2, 3, 4, 5, 6, 7]
                        base_cutoff = 2180.0
                        bar_expr = 1.04
                    else:
                        # Compás final (Living Exit): descenso cadencial largo fundiéndose en el eco
                        active_indices = [4, 5, 6, 7]
                        base_cutoff = 1180.0
                        bar_expr = 0.85

            note_contour = [0.92, 0.76, 0.82, 0.88, 0.94, 0.85, 1.00, 1.05]
            prev_end_samp = -999999
            for idx_n in active_indices:
                n_name, _dur_nom = CHORUS_MELODY[idx_n]
                off_t = offsets[idx_n]
                next_off = offsets[idx_n + 1] if idx_n + 1 < len(offsets) else BAR_TICKS

                # Micro-bolsillo humano (+4 a +11 ms laid-back sobre el grid matemático)
                pocket_ms = rng.uniform(3.5, 10.5) if idx_n not in (0, 6) else rng.uniform(1.5, 5.5)
                s_start = max(0, tick_to_sample(b0 + off_t) + int(round((pocket_ms / 1000.0) * sample_rate)))

                # Articulación legato real: las notas internas se ligan (98% del intervalo);
                # la última nota Eb_sikah4 (+150c) respira más larga en cierres de frase
                span_ticks = max(160, next_off - off_t)
                if idx_n == 7 and (bar == n_bars - 1 or bar % 2 == 0):
                    hold_ratio = 1.45 if (label == "12/8" and bar == n_bars - 1) else 1.12
                elif (idx_n + 1) in active_indices:
                    hold_ratio = 0.98
                else:
                    hold_ratio = 0.86

                dur_sec = (span_ticks * hold_ratio / float(BAR_TICKS)) * BAR_DURATION_SEC
                s_end = min(n_total - 64, s_start + max(320, int(round(dur_sec * sample_rate))))
                if s_end <= s_start + 64:
                    continue

                f_target = note_name_to_hz(n_name)
                # Variación octava grave cálida en el compás íntimo del clímax (bar 2 de 12/8)
                if not short_mode and label == "12/8" and bar == 2 and idx_n in (0, 2, 4):
                    f_target *= 0.5

                expr = bar_expr * note_contour[idx_n] * rng.uniform(0.95, 1.05)
                fc_note = base_cutoff * (0.82 + 0.30 * note_contour[idx_n])
                is_slurred = (s_start - prev_end_samp) <= int(0.035 * sample_rate)
                events.append((s_start, s_end, f_target, expr, fc_note, is_slurred))
                prev_end_samp = s_end

            cur_tick += BAR_TICKS
            bar_global += 1

    if not events:
        z = np.zeros(n_total, dtype=np.float64)
        return z, z.copy()

    # Construir vectores continuos sobre toda la línea temporal (0 reinicios de fase)
    freq_target_arr = np.full(n_total, events[0][2], dtype=np.float64)
    gate_arr = np.zeros(n_total, dtype=np.float64)
    cutoff_target_arr = np.full(n_total, 480.0, dtype=np.float64)
    vib_depth_cents = np.zeros(n_total, dtype=np.float64)

    for ev_i, (s0, s1, f_hz, expr, fc_hz, slurred) in enumerate(events):
        next_s0 = events[ev_i + 1][0] if ev_i + 1 < len(events) else n_total
        # Mantener f_hz hasta el inicio del siguiente evento para que la cola caiga afinada
        freq_target_arr[s0:next_s0] = f_hz
        cutoff_target_arr[s0:next_s0] = fc_hz

        seg_len = s1 - s0
        t_seg = np.arange(seg_len, dtype=np.float64) / float(sample_rate)
        att_s = 0.008 if slurred else 0.022
        rel_s = 0.045
        n_a = min(seg_len // 2, max(4, int(round(att_s * sample_rate))))
        n_r = min(seg_len - n_a, max(8, int(round(rel_s * sample_rate))))
        env_seg = np.ones(seg_len, dtype=np.float64) * expr
        if not slurred:
            env_seg[:n_a] *= 0.5 * (1.0 - np.cos(math.pi * np.arange(n_a) / max(1, n_a - 1)))
        # Caída natural suave durante la nota sostenida
        env_seg *= 0.72 + 0.28 * np.exp(-t_seg / 0.26)
        # Si la siguiente nota NO está ligada, cerrar suavemente al final
        next_slurred = events[ev_i + 1][5] if ev_i + 1 < len(events) else False
        if not next_slurred and n_r > 2:
            env_seg[-n_r:] *= 0.5 * (1.0 + np.cos(math.pi * np.arange(n_r) / (n_r - 1)))

        gate_arr[s0:s1] = np.maximum(gate_arr[s0:s1], env_seg)

        # Vibrato diferido (entra solo tras 145 ms en notas largas sostenidas, 0 scoop caricaturesco)
        if seg_len > int(0.20 * sample_rate):
            v_env = np.clip((t_seg - 0.145) / 0.12, 0.0, 1.0) * 7.5
            vib_depth_cents[s0:s1] = np.maximum(vib_depth_cents[s0:s1], v_env)

    # Portamento RC continuo sobre log-frecuencia (tau = 24 ms -> glissando sedoso analógico)
    log_f = np.log2(np.maximum(freq_target_arr, 40.0))
    tau_glide = 0.024
    a_gl = math.exp(-1.0 / (tau_glide * sample_rate))
    log_f_smooth = signal.lfilter([1.0 - a_gl], [1.0, -a_gl], log_f, zi=[log_f[0]])[0]

    # Suavizado analógico de envolvente de aire/VCA y de cutoff
    a_env = math.exp(-1.0 / (0.012 * sample_rate))
    gate_smooth = freeze_array(signal.lfilter([1.0 - a_env], [1.0, -a_env], gate_arr))
    a_fc = math.exp(-1.0 / (0.032 * sample_rate))
    fc_smooth = signal.lfilter([1.0 - a_fc], [1.0, -a_fc], cutoff_target_arr, zi=[cutoff_target_arr[0]])[0]

    t_full = make_time_axis(n_total, sample_rate)
    drift_1f = _voss_clarke_1f_drift(n_total, seed=8128)
    vib_lfo = np.sin(2.0 * math.pi * 5.15 * t_full + 0.4 * drift_1f)
    total_cents = freeze_array(3.4 * drift_1f + freeze_array(vib_depth_cents) * vib_lfo)
    f_inst = freeze_array(np.power(2.0, log_f_smooth + total_cents / 1200.0))

    # Oscilador continuo híbrido: PolyBLEP saw + pulse simétrico + tubo/lengüeta cúbica (x - x^3/3)
    saw_core = polyblep_saw(f_inst, n_total, sample_rate=sample_rate, initial_phase=0.12)
    pulse_core = polyblep_pulse(
        freeze_array(f_inst * (2.0 ** (3.1 / 1200.0))),
        n_total,
        sample_rate=sample_rate,
        duty=0.47,
        initial_phase=0.37,
    )
    ph_sub = (2.0 * math.pi / float(sample_rate)) * np.cumsum(f_inst * 0.5)
    sub_body = 0.24 * np.sin(ph_sub)

    exciter = freeze_array(0.50 * saw_core + 0.34 * pulse_core + sub_body)
    # Unión no-lineal de lengüeta/tubo acústico (curva Bernoulli x - x^3/3 dependiente de presión)
    p_drive = np.clip(exciter * (0.75 + 0.85 * gate_smooth), -1.35, 1.35)
    bore_sig = freeze_array(p_drive - (p_drive * p_drive * p_drive) / 3.0)

    # Resonancias de cuerpo de madera cálida (sin estridencia nasal MIDI)
    chest_res = _band_formant(bore_sig, 560.0, rel_width=0.30, sample_rate=sample_rate)
    throat_res = _band_formant(bore_sig, 1180.0, rel_width=0.25, sample_rate=sample_rate)
    raw_lead = freeze_array(0.74 * bore_sig + 0.22 * chest_res + 0.14 * throat_res)

    # Filtro escalera resonante acoplado simultáneamente al arco de frase y a la presión de aire
    dyn_fc = freeze_array(np.clip(fc_smooth * (0.42 + 0.68 * gate_smooth), 210.0, 3100.0))
    filtered = _dynamic_analog_ladder_filter(
        raw_lead, dyn_fc, resonance=0.48, sample_rate=sample_rate
    )

    shaped = oversampled_soft_saturate(
        filtered * gate_smooth, drive_db=1.2, threshold_db=-3.0, asymmetry=0.025
    )
    peak = max(float(np.max(np.abs(shaped))), 1e-12)
    mono_lead = apply_zero_crackle_envelope(
        np.multiply(shaped, 0.36 / peak), sample_rate=sample_rate, attack_ms=10.0, release_ms=40.0
    )
    return _apply_analog_bbd_chorus(
        mono_lead, sample_rate=sample_rate, depth_ms=1.7, rate_hz=0.52, mix=0.22
    )


def _apply_ducked_dub_echo(
    dry_l: np.ndarray,
    dry_r: np.ndarray,
    sample_rate: int = SAMPLE_RATE,
    delay_sec: float = 0.3125,
    feedback: float = 0.44,
    wet: float = 0.34,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Eco de cinta analógica con Auto-Ducking (Ley RAE #3 Call & Response):
    mientras el solista canta, el retorno húmedo se agacha -6.5 dB; en los silencios
    de respuesta (compases impares / huecos), la cola filtrada a 2100 Hz florece limpia.
    """
    d_l = freeze_array(np.asarray(dry_l, dtype=np.float64))
    d_r = freeze_array(np.asarray(dry_r, dtype=np.float64))
    echo_mix_l, echo_mix_r = apply_noncommutative_dub_echo(
        d_l,
        d_r,
        sample_rate=sample_rate,
        delay_sec=delay_sec,
        feedback=feedback,
        lpf_hz=2150.0,
        hpf_hz=250.0,
        wet=1.0,
        taps=5,
    )
    only_wet_l = freeze_array(echo_mix_l - d_l)
    only_wet_r = freeze_array(echo_mix_r - d_r)

    # Seguidor de envolvente suave sobre la señal seca
    det = np.sqrt(0.5 * (d_l * d_l + d_r * d_r) + 1e-18)
    a_lp = math.exp(-1.0 / (0.085 * sample_rate))
    env = signal.lfilter([1.0 - a_lp], [1.0, -a_lp], det)
    env_norm = np.clip(env / max(float(np.percentile(env, 96)) if np.any(env > 1e-5) else 0.1, 0.04), 0.0, 1.0)
    duck_gain = freeze_array(1.0 - 0.56 * env_norm)

    return freeze_array(d_l + wet * only_wet_l * duck_gain), freeze_array(
        d_r + wet * only_wet_r * duck_gain
    )


def _synth_granadillo_wood_strike(
    cavity_hz: float,
    amplitude: float,
    seed: int = 0,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """
    Golpe físico de madera hueca de granadillo (CERO osciladores sinusoidales puros):
    impulso transitorio estocástico + fricción de contacto excitando un banco de resonadores
    IIR ortotrópicos de cavidad (Helmholtz + concha) con rebote asimétrico de hojas.
    """
    dur_sec = 0.046
    n_samp = int(round(dur_sec * sample_rate))
    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed)

    # Excitación física de choque sin una sola senoide estacionaria
    impact_env = np.exp(-t / rng.uniform(0.0011, 0.0017))
    scrape_env = np.exp(-t / rng.uniform(0.0042, 0.0062))
    exciter = (
        rng.normal(0.0, 1.0, n_samp) * impact_env
        + 0.35 * rng.normal(0.0, 1.0, n_samp) * scrape_env
    )

    f0 = cavity_hz * rng.uniform(0.955, 1.045)
    nyq = 0.5 * float(sample_rate)
    # 3 resonancias físicas acopladas: cavidad hueca (0.61*f0), tabla principal (f0), borde (1.58*f0)
    resonances = [
        (max(340.0, f0 * 0.61), rng.uniform(5.5, 7.2), 0.48),
        (min(nyq * 0.80, f0), rng.uniform(7.0, 9.5), 0.72),
        (min(nyq * 0.85, f0 * 1.58), rng.uniform(4.5, 6.2), 0.30),
    ]
    shell = np.zeros(n_samp, dtype=np.float64)
    for r_hz, q_val, g_val in resonances:
        b_r, a_r = signal.iirpeak(r_hz, Q=q_val, fs=sample_rate)
        shell += g_val * signal.lfilter(b_r, a_r, exciter)

    # Amortiguamiento por los dedos sobre la concha de madera
    damping = np.exp(-t / rng.uniform(0.0075, 0.0115))
    body = shell * damping

    # Micro-rebote mecánico entre las dos hojas
    b_delay = int(round(rng.uniform(0.0036, 0.0058) * sample_rate))
    b_gain = rng.uniform(0.24, 0.38)
    full = body.copy()
    if 0 < b_delay < n_samp:
        full[b_delay:] += b_gain * body[: n_samp - b_delay]

    sos_bp = signal.butter(2, [310.0 / nyq, min(0.88, 5200.0 / nyq)], btype="band", output="sos")
    clean = signal.sosfilt(sos_bp, full)
    peak = max(float(np.max(np.abs(clean))), 1e-12)
    return apply_zero_crackle_envelope(
        np.multiply(clean, amplitude / peak),
        sample_rate=sample_rate,
        attack_ms=0.8,
        release_ms=10.0,
    )


def _synth_palma_sorda(
    amplitude: float = 0.12,
    seed: int = 0,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Palma flamenca sorda (cavidad palmar 680-820 Hz + rebote de dedos, cero MIDI)."""
    dur_sec = 0.095
    n_samp = int(round(dur_sec * sample_rate))
    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed)

    rebound_s = rng.uniform(0.0065, 0.0105)
    env = np.exp(-t / 0.013) + rng.uniform(0.32, 0.48) * np.exp(
        -np.maximum(0.0, t - rebound_s) / 0.017
    ) * (t >= rebound_s)
    noise = rng.normal(0.0, 1.0, n_samp) * env

    f_cup = rng.uniform(690.0, 815.0)
    b1, a1 = signal.iirpeak(f_cup, Q=3.1, fs=sample_rate)
    b2, a2 = signal.iirpeak(f_cup * 1.72, Q=2.4, fs=sample_rate)
    cupped = 0.78 * signal.lfilter(b1, a1, noise) + 0.26 * signal.lfilter(b2, a2, noise)
    sos_hp = signal.butter(2, 220.0 / (0.5 * sample_rate), btype="high", output="sos")
    clean = signal.sosfilt(sos_hp, cupped)
    peak = max(float(np.max(np.abs(clean))), 1e-12)
    return apply_zero_crackle_envelope(
        np.multiply(clean, amplitude / peak),
        sample_rate=sample_rate,
        attack_ms=1.5,
        release_ms=16.0,
    )


def _synth_brushed_shaker(
    decay_sec: float = 0.024,
    amplitude: float = 0.042,
    seed: int = 0,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Micro-shaker analógico cepillado (>6.8 kHz, fuera de la banda Wiener 500-5000 Hz)."""
    dur_sec = max(0.036, min(0.14, decay_sec * 3.4))
    n_samp = int(round(dur_sec * sample_rate))
    t = make_time_axis(n_samp, sample_rate)
    rng = np.random.default_rng(seed)
    env = np.sin(math.pi * np.clip(t / 0.006, 0.0, 0.5)) ** 2 * np.exp(-t / max(0.010, decay_sec))
    nyq = 0.5 * float(sample_rate)
    sos_bp = signal.butter(3, [6800.0 / nyq, 13600.0 / nyq], btype="band", output="sos")
    grain = signal.sosfilt(sos_bp, rng.normal(0.0, 1.0, n_samp)) * env
    peak = max(float(np.max(np.abs(grain))), 1e-12)
    return apply_zero_crackle_envelope(
        np.multiply(grain, amplitude / peak),
        sample_rate=sample_rate,
        attack_ms=1.8,
        release_ms=8.0,
    )


def _fit_external_stem(
    wav_path: Path, n_total: int, sample_rate: int = SAMPLE_RATE
) -> Tuple[np.ndarray, np.ndarray]:
    """Carga un stem acústico real externo y lo adapta de forma segura a (n_total, 48 kHz)."""
    stereo, sr_in = load_wav_stereo(str(wav_path))
    if sr_in != sample_rate and len(stereo) >= 16:
        gcd = math.gcd(sample_rate, sr_in)
        stereo = signal.resample_poly(stereo, up=sample_rate // gcd, down=sr_in // gcd, axis=0)
    out_l = np.zeros(n_total, dtype=np.float64)
    out_r = np.zeros(n_total, dtype=np.float64)
    n_copy = min(n_total, len(stereo))
    if n_copy > 0:
        out_l[:n_copy] = apply_zero_crackle_envelope(stereo[:n_copy, 0], sample_rate=sample_rate)
        out_r[:n_copy] = apply_zero_crackle_envelope(stereo[:n_copy, 1], sample_rate=sample_rate)
    return freeze_array(out_l), freeze_array(out_r)


def _stem_stats(left: np.ndarray, right: np.ndarray) -> Dict[str, float]:
    """Métricas de nivel y cresta para trazabilidad por stem."""
    l_f = freeze_array(np.asarray(left, dtype=np.float64))
    r_f = freeze_array(np.asarray(right, dtype=np.float64))
    mono = freeze_array(0.5 * (l_f + r_f))
    peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
    rms = math.sqrt(float(np.dot(mono, mono) / max(1, len(mono))) + 1e-18)
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
    profile_name: str = "club_c5",
    run_mastering: bool = True,
    run_linter_subprocess: bool = False,
    brass_stem_path: Optional[Path] = None,
    lead_stem_path: Optional[Path] = None,
    perc_stem_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Compila la arquitectura DSP analógico-física SIKAH-128 (analog_waveguide_v3) a 48 kHz / 24-bit:
      - Rumble de caverna real derivado del Kick D1 (cero bajo oom-pah MIDI).
      - Swells de cuerno analógico CS-80/Bodzin de 2 compases con filtro escalera de 24 dB/oct.
      - Solista continuo legato en guía de ondas cúbica con fraseo Call & Response y Dub Auto-Ducking.
      - Percusión física sin senoides (resonadores IIR de granadillo, palmas sordas y micro-shaker).
    """
    b_dir = Path(bounces_dir) if bounces_dir is not None else resolve_bounces_dir()
    stems_dir = b_dir / "SIKAH_128_Stems_48k24b"
    stems_dir.mkdir(parents=True, exist_ok=True)

    total_bars = sum(n_bars for _, _, _, n_bars in sections)
    tail_sec = 2.0
    total_sec = total_bars * BAR_DURATION_SEC + tail_sec
    n_total = int(round(total_sec * SAMPLE_RATE))

    kick_l = np.zeros(n_total, dtype=np.float64)
    kick_r = np.zeros(n_total, dtype=np.float64)
    tromb_l = np.zeros(n_total, dtype=np.float64)
    tromb_r = np.zeros(n_total, dtype=np.float64)
    cast_l = np.zeros(n_total, dtype=np.float64)
    cast_r = np.zeros(n_total, dtype=np.float64)

    kick_proto = synthesize_phase_locked_kick(
        sample_rate=SAMPLE_RATE,
        duration_sec=0.39,
        root_hz=note_name_to_hz("D1"),
        punch_hz=124.0,
        click_hz=920.0,
        tau_click=0.0030,
        tau_punch=0.029,
        tau_body=0.200,
        drive_db=1.9,
        pultec_sub_gain=0.20,
        mud_notch_hz=195.0,
        beater_gain=0.048,
        beater_hz=1120.0,
    )
    kick_proto = freeze_array(
        apply_zero_crackle_envelope(
            kick_proto, sample_rate=SAMPLE_RATE, attack_ms=1.2, release_ms=16.0
        )
    )

    rng = np.random.default_rng(12864)
    macho_gl, macho_gr = _pan_gains(-0.24)
    hembra_gl, hembra_gr = _pan_gains(0.27)

    def _jitter_samp(max_ms: float) -> int:
        delta_ms = float(np.clip(rng.normal(0.0, max_ms * 0.48), -max_ms, max_ms))
        return int(round((delta_ms / 1000.0) * SAMPLE_RATE))

    kick_onsets: List[int] = []
    cur_tick = 0
    bar_idx = 0

    for label, _num, _den, n_bars in sections:
        for bar in range(n_bars):
            b0 = cur_tick
            is_pre_drop_vacuum = label == "6/4" and bar == n_bars - 1
            if label == "3/2":
                sec_gain = 0.84 + 0.035 * min(bar, 3)
            elif label == "6/4":
                sec_gain = 0.74 if is_pre_drop_vacuum else (0.90 + 0.04 * bar)
            else:
                sec_gain = 1.04

            # 1. Kick sísmico D1 con micro-dinámica de pulso
            if label == "3/2":
                kick_grid = [0, 960, 1920]
            elif label == "6/4":
                kick_grid = [0, 480, 960, 1440] if is_pre_drop_vacuum else [0, 480, 960, 1440, 1920, 2400]
            else:
                kick_grid = [0, 720, 1440, 2160]

            for idx_k, k_off in enumerate(kick_grid):
                k_jit = 0 if idx_k == 0 else _jitter_samp(0.9)
                s_idx = max(0, tick_to_sample(b0 + k_off) + k_jit)
                kick_onsets.append(s_idx)
                accent_k = 0.62 if idx_k == 0 else (0.56 if idx_k % 2 == 0 else 0.52)
                k_vel = accent_k * sec_gain * rng.uniform(0.97, 1.03)
                _place_stereo(kick_l, kick_r, s_idx, np.multiply(kick_proto, k_vel), 1.0, 1.0)

            # 2. Percusión orgánica: Granadillo + Palmas Sordas + Shaker cepillado (evolución por acto)
            if not is_pre_drop_vacuum and perc_stem_path is None:
                # Palmas sordas en apoyos estructurales de compás / hemiola
                palma_offs = (
                    [960] if (label == "3/2" and bar % 2 == 1)
                    else ([720, 2160] if label == "6/4" else ([360, 1800] if bar % 2 == 0 else [1080]))
                )
                for idx_p, p_off in enumerate(palma_offs):
                    p_hit = _synth_palma_sorda(
                        amplitude=0.095 * sec_gain * rng.uniform(0.85, 1.12),
                        seed=7000 + bar_idx * 16 + idx_p,
                        sample_rate=SAMPLE_RATE,
                    )
                    p_gl, p_gr = _pan_gains(-0.16 if idx_p % 2 == 0 else 0.18)
                    _place_stereo(
                        cast_l,
                        cast_r,
                        tick_to_sample(b0 + p_off) + _jitter_samp(5.5),
                        p_hit,
                        p_gl,
                        p_gr,
                    )

                # Castañuela macho espaciada (no en todos los compases del intro)
                if not (label == "3/2" and bar == 0):
                    macho_offs = [2400] if label == "3/2" else ([1440] if label == "6/4" else [1080, 2520])
                    for idx_m, m_off in enumerate(macho_offs):
                        m_hit = _synth_granadillo_wood_strike(
                            1040.0,
                            amplitude=0.105 * sec_gain * rng.uniform(0.84, 1.10),
                            seed=1000 + bar_idx * 32 + idx_m,
                            sample_rate=SAMPLE_RATE,
                        )
                        _place_stereo(
                            cast_l,
                            cast_r,
                            tick_to_sample(b0 + m_off) + _jitter_samp(4.2),
                            m_hit,
                            macho_gl,
                            macho_gr,
                        )

                # Carretilla humana de hembra solo en cierres de semifrase (cada 2 compases, 0 ametralladora)
                if bar % 2 == 1 or n_bars == 1:
                    carretilla_anchor = 1920 if label in ("3/2", "6/4") else 1820
                    # Aceleración inercial humana de los 4 dedos (meñique -> anular -> corazón -> índice)
                    for idx_c, (dt, scale_v) in enumerate(
                        [(0, 0.42), (78, 0.58), (144, 0.78), (198, 1.00)]
                    ):
                        h_hit = _synth_granadillo_wood_strike(
                            1580.0,
                            amplitude=0.092 * scale_v * sec_gain,
                            seed=2000 + bar_idx * 32 + idx_c,
                            sample_rate=SAMPLE_RATE,
                        )
                        _place_stereo(
                            cast_l,
                            cast_r,
                            tick_to_sample(b0 + carretilla_anchor + dt) + _jitter_samp(3.1),
                            h_hit,
                            hembra_gl,
                            hembra_gr,
                        )

                # Pulso sutil de shaker cepillado off-grid en el clímax 12/8 (Decay Morphing Ley RAE #9)
                if label == "12/8":
                    morph = 0.016 + 0.022 * ((bar % 4) / 3.0)
                    for sub_i, sh_off in enumerate([240, 480, 960, 1200, 1680, 1920, 2400, 2640]):
                        swing_t = 18 if sub_i % 2 == 0 else 0
                        sh_hit = _synth_brushed_shaker(
                            decay_sec=morph,
                            amplitude=0.036 * (1.15 if sub_i % 2 == 0 else 0.72),
                            seed=9000 + bar_idx * 32 + sub_i,
                            sample_rate=SAMPLE_RATE,
                        )
                        sh_gl, sh_gr = _pan_gains(0.22 if sub_i % 2 == 0 else -0.20)
                        _place_stereo(
                            cast_l,
                            cast_r,
                            tick_to_sample(b0 + sh_off + swing_t) + _jitter_samp(3.8),
                            sh_hit,
                            sh_gl,
                            sh_gr,
                        )

            # 3. Cuerno / Brass analógico CS-80 en swells largos de 2 compases (cero blat MIDI por compás)
            if brass_stem_path is None and (bar % 2 == 0 or n_bars == 1):
                span_bars = 1 if (bar == n_bars - 1) else 2
                # Si el par incluye el compás Pre-Drop Vacuum, cortar limpio antes del vacío
                includes_vacuum = (label == "6/4") and (bar + span_bars - 1 == n_bars - 1)
                if includes_vacuum:
                    swell_dur = (span_bars - 0.48) * BAR_DURATION_SEC
                else:
                    swell_dur = span_bars * BAR_DURATION_SEC * 0.96

                f_d2 = note_name_to_hz("D2")
                f_a2 = note_name_to_hz("A2")
                f_g3 = note_name_to_hz("G3")
                f_gs11 = note_name_to_hz("Gs_11th3")
                f_fneut3 = note_name_to_hz("F_neut3")

                if label == "3/2":
                    voices = (
                        [(f_d2, f_d2, 0.0), (f_a2, f_a2, 0.0)]
                        if bar == 0
                        else [(f_d2, f_d2, 0.0), (f_g3, f_gs11, 0.42)]
                    )
                    c0, cp, c1 = 170.0, 680.0, 210.0
                    b_amp = 0.23 * sec_gain
                elif label == "6/4":
                    voices = (
                        [(f_d2, f_d2, 0.0), (f_fneut3, f_a2 * 2.0, 0.35)]
                        if bar == 0
                        else [(f_d2, f_d2, 0.0), (f_g3, f_gs11, 0.50)]
                    )
                    c0, cp, c1 = 230.0, (1480.0 if includes_vacuum else 1080.0), 310.0
                    b_amp = 0.27 * sec_gain
                else:
                    if (bar // 2) % 2 == 0:
                        voices = [(f_d2, f_d2, 0.0), (f_a2, f_a2, 0.0), (f_g3, f_gs11, 0.38)]
                        c0, cp, c1 = 240.0, 1280.0, 260.0
                    else:
                        voices = [(f_d2, f_d2, 0.0), (f_fneut3, f_g3, 0.40), (f_gs11, f_g3, 0.45)]
                        c0, cp, c1 = 220.0, 1050.0, 230.0
                    b_amp = 0.28 * sec_gain

                sw_l, sw_r = _synth_cs80_brass_swell(
                    voices_hz=voices,
                    duration_sec=max(0.55, swell_dur),
                    cutoff_start_hz=c0,
                    cutoff_peak_hz=cp,
                    cutoff_end_hz=c1,
                    peak_pos=0.72 if includes_vacuum else 0.54,
                    amplitude=b_amp,
                    seed=3000 + bar_idx * 11,
                    sample_rate=SAMPLE_RATE,
                )
                s_sw = tick_to_sample(b0) + _jitter_samp(4.0)
                n_sw = min(len(sw_l), max(0, n_total - max(0, s_sw)))
                if n_sw > 0 and s_sw >= 0:
                    tromb_l[s_sw : s_sw + n_sw] += sw_l[:n_sw]
                    tromb_r[s_sw : s_sw + n_sw] += sw_r[:n_sw]

            cur_tick += BAR_TICKS
            bar_idx += 1

    kick_l = freeze_array(kick_l)
    kick_r = freeze_array(kick_r)

    # 4. Rumble tectónico de caverna acoplado al Kick D1 (o stem externo)
    rumble_mono = _render_cavern_kick_rumble(kick_l, sections=sections, sample_rate=SAMPLE_RATE)
    bass_l = rumble_mono.copy()
    bass_r = rumble_mono.copy()

    # 5. Solista continuo legato en guía de ondas cúbica (o stem acústico externo)
    if lead_stem_path is not None and Path(lead_stem_path).exists():
        lead_l, lead_r = _fit_external_stem(Path(lead_stem_path), n_total, SAMPLE_RATE)
    else:
        lead_l, lead_r = _render_continuous_legato_lead(
            sections=sections, n_total=n_total, sample_rate=SAMPLE_RATE
        )

    if brass_stem_path is not None and Path(brass_stem_path).exists():
        tromb_l, tromb_r = _fit_external_stem(Path(brass_stem_path), n_total, SAMPLE_RATE)
    if perc_stem_path is not None and Path(perc_stem_path).exists():
        cast_l, cast_r = _fit_external_stem(Path(perc_stem_path), n_total, SAMPLE_RATE)

    # Procesado espectral C5-REAL: Sidechain multibanda + Carving Bark + Auto-Ducked Dub Echo + Sala
    sc_sub, sc_high = build_coupled_multiband_sidechain(
        n_total, kick_onsets, sample_rate=SAMPLE_RATE, tau_body=0.200, sub_depth=0.92, high_depth=0.22
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
    # Garantizar suavidad de derivadas d1/d2 en sub-rumble tras el sidechain
    nyq = 0.5 * float(SAMPLE_RATE)
    sos_bass_clean = signal.butter(3, 108.0 / nyq, btype="low", output="sos")
    bass_l = apply_zero_crackle_envelope(signal.sosfiltfilt(sos_bass_clean, bass_l), SAMPLE_RATE, 15.0, 60.0)
    bass_r = bass_l.copy()

    tromb_l, tromb_r = carve_polyphonic_mud(
        tromb_l, tromb_r, sample_rate=SAMPLE_RATE, hpf_hz=82.0, mud_hz=265.0, mud_cut_blend=0.40
    )
    tromb_l, tromb_r = _apply_multiband_sc(tromb_l, tromb_r)

    lead_l, lead_r = carve_polyphonic_mud(
        lead_l, lead_r, sample_rate=SAMPLE_RATE, hpf_hz=190.0, mud_hz=375.0, mud_cut_blend=0.42
    )
    lead_l, lead_r = _apply_ducked_dub_echo(
        lead_l,
        lead_r,
        sample_rate=SAMPLE_RATE,
        delay_sec=0.3125,  # 2 corcheas exactas @ 384 corcheas/min
        feedback=0.44,
        wet=0.34,
    )
    lead_l, lead_r = _apply_multiband_sc(lead_l, lead_r)

    # Inmutabilizar stems antes de sumas lineales (protección CPython 3.14 LOAD_FAST_BORROW)
    kick_l = freeze_array(kick_l)
    kick_r = freeze_array(kick_r)
    bass_l = freeze_array(bass_l)
    bass_r = freeze_array(bass_r)
    tromb_l = freeze_array(tromb_l)
    tromb_r = freeze_array(tromb_r)
    lead_l = freeze_array(lead_l)
    lead_r = freeze_array(lead_r)
    cast_l = freeze_array(cast_l)
    cast_r = freeze_array(cast_r)

    # Sala oscura coherente (18 ms pre-delay, 84% núcleo mono difuso)
    room_in_l = tromb_l * 0.48 + lead_l * 0.44 + cast_l * 0.34
    room_in_r = tromb_r * 0.48 + lead_r * 0.44 + cast_r * 0.34
    room_l, room_r = apply_coherent_shared_room(
        room_in_l, room_in_r, sample_rate=SAMPLE_RATE, pre_delay_ms=18.0, rt60_sec=1.35, wet=0.16
    )
    room_l = freeze_array(room_l)
    room_r = freeze_array(room_r)

    # Lecho continuo analógico a -57 dBFS (cero digital prohibido, protege pre-drop)
    tape_l, tape_r = generate_warm_analog_tape_bed(
        n_total, sample_rate=SAMPLE_RATE, level_dbfs=-57.0, seed=1995
    )
    tape_l = freeze_array(tape_l)
    tape_r = freeze_array(tape_r)

    pre_l = kick_l + bass_l + tromb_l + lead_l + cast_l + room_l * 0.36 + tape_l
    pre_r = kick_r + bass_r + tromb_r + lead_r + cast_r + room_r * 0.36 + tape_r

    pre_l = oversampled_soft_saturate(pre_l, drive_db=0.85, threshold_db=-2.5, asymmetry=0.02)
    pre_r = oversampled_soft_saturate(pre_r, drive_db=0.85, threshold_db=-2.5, asymmetry=0.02)
    # Mono sub-bass DESPUÉS de saturar para garantizar LPC == 1.000 sin intermodulación lateral
    pre_l, pre_r = enforce_low_end_mono(pre_l, pre_r, cutoff_hz=120.0, sample_rate=SAMPLE_RATE)

    # Envolvente final sin clicks en apertura/cierre de archivo
    pre_l = apply_zero_crackle_envelope(
        pre_l, sample_rate=SAMPLE_RATE, attack_ms=15.0, release_ms=180.0
    )
    pre_r = apply_zero_crackle_envelope(
        pre_r, sample_rate=SAMPLE_RATE, attack_ms=15.0, release_ms=180.0
    )

    peak_pre = float(max(np.max(np.abs(pre_l)), np.max(np.abs(pre_r)), 1e-12))
    target_pre_peak = 0.78
    if peak_pre > target_pre_peak:
        scale_headroom = target_pre_peak / peak_pre
        pre_l = pre_l * scale_headroom
        pre_r = pre_r * scale_headroom
    pre_l = freeze_array(pre_l)
    pre_r = freeze_array(pre_r)

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

    pre_mono = freeze_array(0.5 * (pre_l + pre_r))
    rubin_pre = compute_rubin_metrics(pre_l, pre_r, sample_rate=SAMPLE_RATE)
    crackle_check_sub = check_zero_crackle_derivatives(0.5 * (bass_l + bass_r))
    pre_sub_mono, _ = lr4_zero_phase_crossover(
        pre_mono, crossover_hz=120.0, sample_rate=SAMPLE_RATE
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

    classification = (
        "HÍBRIDO_ORGÁNICO_C5"
        if any(p is not None for p in (brass_stem_path, lead_stem_path, perc_stem_path))
        else "AUTÓMATA_SINTÉTICO_ESTRUCTURAL"
    )
    audit_summary = {
        "project": "SIKAH-128",
        "engine_version": "analog_waveguide_v3",
        "classification": classification,
        "gate_notice": (
            "Síntesis analógico-física continua v3 (Cavern Kick-Rumble + CS-80 Ladder Swell + "
            "Legato Cubic Waveguide + Auto-Ducked Dub Echo, 48 kHz / 24-bit). "
            "Admite stems acústicos reales vía --brass-stem / --lead-stem / --perc-stem."
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
        default="club_c5",
        help="Perfil de masterización (club_c5, dub_techno, techno, streaming_sota).",
    )
    parser.add_argument(
        "--brass-stem",
        type=Path,
        default=None,
        help="Ruta opcional a stem WAV real de metales grabado/exportado desde DAW.",
    )
    parser.add_argument(
        "--lead-stem",
        type=Path,
        default=None,
        help="Ruta opcional a stem WAV real solista microtonal exportado desde DAW.",
    )
    parser.add_argument(
        "--perc-stem",
        type=Path,
        default=None,
        help="Ruta opcional a stem WAV real de castañuelas/palmas acústicas.",
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
            brass_stem_path=args.brass_stem,
            lead_stem_path=args.lead_stem,
            perc_stem_path=args.perc_stem,
        )
        print(json.dumps(render_out, indent=2, default=str))


if __name__ == "__main__":
    main()
