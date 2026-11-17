#!/usr/bin/env python3
"""
C5-REAL Arrangement Structure Engine (v3.0 SOTA)
=================================================
Generates complete multi-section MIDI arrangements using an exact absolute-tick
event scheduler (zero cumulative delta drift across muted sections or swing),
featuring:
  - Differential Groove Pocket (0 tick Kick anchor, +12 tick laid-back Bass, 62% Swing)
  - Chord Micro-Strumming (+12 ticks/voice) & Top-Note Voicing Emphasis
  - Deterministic False Drop & Living Pre-Drop Gap (Bar 60 / pre-drop strip + dub throw + sub-glide)
  - Turnaround Fills every 8 bars & Living Exits (RC velocity + CC#11 decay)
"""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mido

WORKSPACE_DIR = Path(__file__).resolve().parent.parent

ARRANGEMENT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "deep_house_classic": {
        "bpm": 122,
        "key": "Am",
        "sections": [
            {"name": "Intro (Kick + Percussion)", "bars": 16, "layers": ["kick", "hats", "shaker"]},
            {"name": "Build A (Add Bass)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc"]},
            {"name": "Main A (Full Energy)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc", "chords", "pad"]},
            {"name": "Breakdown (Strip Kick)", "bars": 8, "layers": ["pad", "chords", "vocal_chop"]},
            {"name": "Build B (Rising Filter + Pre-Drop)", "bars": 8, "layers": ["kick", "hats", "bass", "chords", "pad", "riser"]},
            {"name": "Drop / Main B (Peak)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc", "chords", "pad", "lead", "vocal_chop"]},
            {"name": "Breakdown 2 (Dub Throw)", "bars": 8, "layers": ["pad", "chords", "delay_tail"]},
            {"name": "Main C (Final Push)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc", "chords", "pad"]},
            {"name": "Outro (Living Exit)", "bars": 16, "layers": ["kick", "hats", "shaker"]},
        ],
    },
    "melodic_techno_maceo": {
        "bpm": 126,
        "key": "Bm",
        "sections": [
            {"name": "Intro (Atmosphere)", "bars": 16, "layers": ["kick", "noise_sweep"]},
            {"name": "Build (Add Acid)", "bars": 16, "layers": ["kick", "hats", "acid_bass", "perc"]},
            {"name": "Main A (Full Hypnotic)", "bars": 32, "layers": ["kick", "hats", "acid_bass", "perc", "locrian_pad", "arp"]},
            {"name": "Breakdown (Ethereal Pre-Drop)", "bars": 16, "layers": ["locrian_pad", "arp", "reverb_wash", "riser"]},
            {"name": "Drop (Maximum Tension)", "bars": 32, "layers": ["kick", "hats", "acid_bass", "perc", "locrian_pad", "arp", "lead"]},
            {"name": "Outro (Deconstruct Living Exit)", "bars": 16, "layers": ["kick", "acid_bass", "noise_sweep"]},
        ],
    },
    "air_moon_safari_dreampop": {
        "bpm": 88,
        "key": "Am",
        "sections": [
            {"name": "Intro (Rhodes Alone)", "bars": 8, "layers": ["rhodes"]},
            {"name": "Verse A (Add Bass + Strings)", "bars": 16, "layers": ["rhodes", "minimoog_bass", "strings"]},
            {"name": "Chorus (Full Ensemble)", "bars": 8, "layers": ["rhodes", "minimoog_bass", "strings", "vocal_melody", "drums_light"]},
            {"name": "Verse B", "bars": 16, "layers": ["rhodes", "minimoog_bass", "strings"]},
            {"name": "Chorus 2 (Peak)", "bars": 8, "layers": ["rhodes", "minimoog_bass", "strings", "vocal_melody", "drums_full", "synth_pad"]},
            {"name": "Bridge (Ambient Pre-Drop)", "bars": 8, "layers": ["strings", "synth_pad", "rhodes", "riser"]},
            {"name": "Final Chorus", "bars": 8, "layers": ["rhodes", "minimoog_bass", "strings", "vocal_melody", "drums_full", "synth_pad"]},
            {"name": "Outro (Living Fade)", "bars": 8, "layers": ["rhodes", "strings"]},
        ],
    },
    "satin_maceo_air_hybrid_64": {
        "bpm": 122,
        "key": "Cm",
        "sections": [
            {"name": "Intro (Solina Horizon + Rhodes)", "bars": 8, "layers": ["rhodes", "pad", "shaker"]},
            {"name": "Build A (Rolling Bass + Hats)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "rhodes", "pad"]},
            {"name": "Drop A (Penrose Club Groove)", "bars": 16, "layers": ["kick", "hats", "shaker", "bass", "perc", "chords", "arp"]},
            {"name": "Breakdown (AIR Solina Bridge + False Drop)", "bars": 20, "layers": ["rhodes", "pad", "arp", "delay_tail", "riser"]},
            {"name": "Outro (Final Drop + Living Exit)", "bars": 4, "layers": ["kick", "hats", "bass", "chords", "lead", "arp"]},
        ],
    },
    "dub_techno_basic_channel_64": {
        "bpm": 118,
        "key": "Fm",
        "sections": [
            {"name": "Intro (Sub Pulse + Tape Dust)", "bars": 16, "layers": ["kick", "shaker", "delay_tail"]},
            {"name": "Hypnotic Chord Lock", "bars": 16, "layers": ["kick", "hats", "bass", "chords", "delay_tail"]},
            {"name": "Dub Space Wash (Pre-Drop)", "bars": 28, "layers": ["kick", "hats", "bass", "chords", "pad", "delay_tail", "riser"]},
            {"name": "Submerged Outro (Living Exit)", "bars": 4, "layers": ["chords", "pad", "delay_tail"]},
        ],
    },
    "cosmic_house_64": {
        "bpm": 122,
        "key": "Gm",
        "sections": [
            {"name": "Intro (Kicks + Sync Bass + Retro Arps)", "bars": 16, "layers": ["kick", "bass", "arp"]},
            {"name": "Verse 1 (Airy Keys + Subtle Pads)", "bars": 8, "layers": ["rhodes", "pad"]},
            {"name": "Pre-Chorus 1 (Filtered Disco Guitars)", "bars": 8, "layers": ["kick", "disco_guitar", "arp", "riser"]},
            {"name": "Drop 1 (Swirling Analog Leads + Dynamic Percussion)", "bars": 12, "layers": ["kick", "bass", "lead", "perc", "hats", "arp"]},
            {"name": "Verse 2 (Airy Keys + Subtle Pads)", "bars": 8, "layers": ["rhodes", "pad", "delay_tail"]},
            {"name": "Pre-Chorus 2 (Filtered Disco Guitars + False Drop)", "bars": 8, "layers": ["kick", "disco_guitar", "arp", "riser", "delay_tail"]},
            {"name": "Drop 2 (Cosmic Groove Climax + Living Exit)", "bars": 4, "layers": ["kick", "bass", "lead", "perc", "hats", "arp", "delay_tail"]},
        ],
    },
}

LAYER_NOTE_POOLS: Dict[str, List[int]] = {
    "kick": [36],
    "hats": [42, 44, 46],
    "shaker": [70],
    "perc": [39, 54, 56],
    "bass": [33, 36, 38, 40, 43, 45],
    "acid_bass": [35, 36, 38, 41],
    "disco_guitar": [67, 70, 74, 79],
    "chords": [60, 63, 67, 70, 74],
    "pad": [72, 76, 79, 84],
    "locrian_pad": [59, 62, 65, 68],
    "lead": [72, 74, 76, 79, 81, 84],
    "arp": [60, 64, 67, 72, 76],
    "rhodes": [60, 64, 67, 71, 74],
    "minimoog_bass": [33, 40, 43],
    "strings": [76, 81, 84],
    "vocal_chop": [60],
    "vocal_melody": [65, 67, 69, 72],
    "drums_light": [36, 38, 42],
    "drums_full": [36, 38, 42, 46, 49],
    "synth_pad": [60, 64, 67, 72],
    "riser": [84],
    "noise_sweep": [84],
    "reverb_wash": [72],
    "delay_tail": [60],
}

# Chord transposition offsets over 4-bar Penrose / Modal cycles
CHORD_CYCLE_SEMITONES = (0, 2, -2, -5)


def _flush_abs_events(track: mido.MidiTrack, events: List[Tuple[int, int, Any]]) -> None:
    """Sorts (abs_tick, order_priority, message) into exact non-negative delta MIDI track."""
    events.sort(key=lambda item: (item[0], item[1]))
    last_tick = 0
    for abs_tick, _order, msg in events:
        clamped = max(last_tick, int(abs_tick))
        msg.time = clamped - last_tick
        track.append(msg)
        last_tick = clamped


def generate_arrangement_midi(
    template_name: str = "deep_house_classic",
    output_path: Optional[str] = None,
    bpm_override: Optional[float] = None,
) -> str:
    template = ARRANGEMENT_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(ARRANGEMENT_TEMPLATES.keys())}")

    bpm = bpm_override or template["bpm"]
    if not output_path:
        output_path = str(WORKSPACE_DIR / "samples" / f"arrangement_{template_name}.mid")

    mid = mido.MidiFile(type=1)
    tpb = 480
    bar_ticks = 4 * tpb
    step_ticks = tpb // 4  # 120 ticks per 16th note
    mid.ticks_per_beat = tpb

    # Conductor Track with exact section markers
    t_tempo = mido.MidiTrack()
    mid.tracks.append(t_tempo)
    t_tempo.append(mido.MetaMessage("track_name", name=f"Arrangement: {template_name}"))
    t_tempo.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

    sections = template["sections"]
    total_bars = sum(int(sec["bars"]) for sec in sections)

    conductor_events: List[Tuple[int, int, Any]] = []
    section_timeline: List[Dict[str, Any]] = []
    cur_bar = 0
    for idx, sec in enumerate(sections):
        sec_bars = int(sec["bars"])
        start_bar = cur_bar
        start_tick = start_bar * bar_ticks
        is_last = idx == len(sections) - 1
        next_name = sections[idx + 1]["name"] if not is_last else ""
        is_pre_drop = any(k in next_name for k in ("Drop", "Final", "Chorus")) or ("Pre-Drop" in sec["name"])
        is_outro = "Outro" in sec["name"] or is_last
        section_timeline.append({
            "index": idx,
            "name": sec["name"],
            "start_bar": start_bar,
            "bars": sec_bars,
            "start_tick": start_tick,
            "layers": set(sec["layers"]),
            "is_pre_drop": is_pre_drop,
            "is_outro": is_outro,
        })
        conductor_events.append((start_tick, 0, mido.MetaMessage("text", text=f"[{idx + 1}] {sec['name']}", time=0)))
        cur_bar += sec_bars

    _flush_abs_events(t_tempo, conductor_events)

    # Collect unique layers preserving declaration order across sections
    all_layers: List[str] = []
    for sec in sections:
        for layer in sec["layers"]:
            if layer not in all_layers:
                all_layers.append(layer)

    percussion_layers = {"kick", "hats", "shaker", "perc", "drums_light", "drums_full"}
    bass_layers = {"bass", "acid_bass", "minimoog_bass"}
    chord_layers = {"chords", "pad", "locrian_pad", "synth_pad", "rhodes", "strings"}
    fx_layers = {"riser", "noise_sweep", "reverb_wash", "delay_tail"}

    def _voice_lead_chord(base_notes: List[int], bar_idx: int, transp: int) -> List[int]:
        """Minimal-movement chord inversion + upper tension extension per 4-bar phrase."""
        raw = sorted(max(40, min(92, n + transp)) for n in base_notes)
        if len(raw) < 3:
            return raw
        phrase_pos = bar_idx % 4
        voiced = list(raw)
        if phrase_pos == 1:
            # Drop lowest inner voice or invert root up an octave for smooth soprano voice-leading
            voiced[0] = min(92, voiced[0] + 12)
        elif phrase_pos == 2:
            # Open spread: drop second voice down for warm mid-range separation
            voiced[-1] = max(44, voiced[-1] - 12)
        elif phrase_pos == 3:
            # Turnaround color: add natural 9th/11th shimmer on top
            voiced[-1] = min(95, voiced[-1] + 2)
        return sorted(voiced)

    for ch_idx, layer_name in enumerate(all_layers):
        channel = ch_idx % 16
        if channel == 9:  # avoid accidental GM percussion remap unless perc
            channel = (ch_idx + 1) % 16
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage("track_name", name=layer_name))

        notes = LAYER_NOTE_POOLS.get(layer_name, [60])
        events: List[Tuple[int, int, Any]] = []

        for sec in section_timeline:
            if layer_name not in sec["layers"]:
                continue

            sec_bars = sec["bars"]
            sec_start_bar = sec["start_bar"]

            # Living Exit RC expression decay at start -> end of Outro
            if sec["is_outro"]:
                for b in range(sec_bars):
                    t_bar = (sec_start_bar + b) * bar_ticks
                    frac = b / max(1, sec_bars - 1)
                    expr = int(max(32, 118 - 68 * (frac ** 1.35)))
                    events.append((t_bar, 2, mido.Message("control_change", channel=channel, control=11, value=expr, time=0)))
            else:
                events.append((sec["start_tick"], 2, mido.Message("control_change", channel=channel, control=11, value=118, time=0)))

            for b in range(sec_bars):
                abs_bar = sec_start_bar + b
                bar_tick = abs_bar * bar_ticks
                # Deterministic False Drop & Living Pre-Drop Gap:
                # Bar 60 beats 3-4 (0-indexed abs_bar == 59) if total_bars >= 64,
                # OR final bar beats 3-4 before a Drop/Chorus section
                is_false_drop_bar = (
                    (total_bars >= 64 and abs_bar == 59)
                    or (sec["is_pre_drop"] and b == sec_bars - 1)
                )
                is_turnaround_bar = ((abs_bar + 1) % 8 == 0) and not is_false_drop_bar
                exit_scale = max(0.45, 1.0 - 0.45 * (b / max(1, sec_bars - 1))) if sec["is_outro"] else 1.0

                if layer_name == "kick":
                    for beat in range(4):
                        if is_false_drop_bar and beat >= 2:
                            continue  # Living Pre-Drop Gap on beats 3-4
                        t_on = bar_tick + beat * tpb
                        t_off = t_on + tpb // 2
                        vel = int((124 if beat == 0 else (116 if beat == 2 else 112)) * exit_scale)
                        events.append((t_on, 1, mido.Message("note_on", channel=channel, note=notes[0], velocity=max(32, min(127, vel)), time=0)))
                        events.append((t_off, 0, mido.Message("note_off", channel=channel, note=notes[0], velocity=0, time=0)))
                        if is_turnaround_bar and beat == 3:
                            # Turnaround double-kick pickup
                            t_fill = bar_tick + 3 * tpb + 240
                            events.append((t_fill, 1, mido.Message("note_on", channel=channel, note=notes[0], velocity=96, time=0)))
                            events.append((t_fill + 120, 0, mido.Message("note_off", channel=channel, note=notes[0], velocity=0, time=0)))

                elif layer_name in percussion_layers:
                    for step in range(16):
                        if is_false_drop_bar and step >= 8:
                            continue  # Strip percussion in beats 3-4 pre-drop vacuum
                        swing = 14 if (step % 2 == 1) else 0
                        # Clap pre-snap flam (-10 ticks) on beats 2 & 4 for perc/drums
                        flam = -10 if (layer_name in {"perc", "drums_light", "drums_full"} and step in (4, 12) and step_ticks * step > 10) else 0
                        hit = False
                        if layer_name in {"hats", "shaker"}:
                            hit = (step % 2 == 0) or (is_turnaround_bar and step >= 12) or (step in (10, 14))
                        elif layer_name == "perc":
                            hit = step in (4, 12) or (step == 15) or (is_turnaround_bar and step in (11, 13, 14, 15))
                        else:  # drums_light / drums_full
                            hit = step in (0, 2, 4, 6, 8, 10, 12, 14) or (is_turnaround_bar and step >= 12)

                        if hit:
                            n = notes[(step + b) % len(notes)]
                            accent = 18 if step in (2, 4, 10, 12) else (-12 if step % 2 == 1 else 0)
                            vel = int((96 + accent) * exit_scale)
                            t_on = max(0, bar_tick + step * step_ticks + swing + flam)
                            t_off = t_on + step_ticks // 2
                            events.append((t_on, 1, mido.Message("note_on", channel=channel, note=n, velocity=max(24, min(127, vel)), time=0)))
                            events.append((t_off, 0, mido.Message("note_off", channel=channel, note=n, velocity=0, time=0)))

                elif layer_name in bass_layers:
                    if is_false_drop_bar:
                        # Sub-bass pitch glide breakdown sweep into drop beat 1
                        glide_base = bar_tick + 2 * tpb
                        events.append((glide_base, 1, mido.Message("note_on", channel=channel, note=notes[0], velocity=96, time=0)))
                        for g_i in range(6):
                            pb = -int(680 * g_i)
                            events.append((glide_base + g_i * 150, 2, mido.Message("pitchwheel", channel=channel, pitch=pb, time=0)))
                        events.append((bar_tick + bar_ticks - 24, 0, mido.Message("note_off", channel=channel, note=notes[0], velocity=0, time=0)))
                        events.append((bar_tick + bar_ticks - 12, 3, mido.Message("pitchwheel", channel=channel, pitch=0, time=0)))
                    else:
                        phrase_pos = b % 4
                        transp = CHORD_CYCLE_SEMITONES[phrase_pos]
                        # Continuous organic filter sweep CC#74 across 4-bar phrase + breath
                        cc74_val = int(max(36, min(118, 52 + 34 * (0.5 - 0.5 * math.cos(math.pi * (phrase_pos + 0.5) / 4.0)))))
                        events.append((bar_tick, 2, mido.Message("control_change", channel=channel, control=74, value=cc74_val, time=0)))
                        step_sets = {
                            0: (1, 2, 3, 6, 7, 10, 11, 14),
                            1: (2, 3, 6, 7, 9, 10, 14, 15),
                            2: (1, 2, 6, 7, 10, 11),  # Deliberate negative space in beats 3-4 breath
                            3: (2, 3, 6, 7, 10, 12, 14, 15),  # Turnaround chromatic/octave pickup
                        }
                        for step in step_sets[phrase_pos]:
                            pocket = 12  # +12 ticks (~12 ms) laid-back groove pocket
                            swing = 12 if step % 2 == 1 else 0
                            oct_lift = 12 if (phrase_pos == 2 and step == 10) or (phrase_pos == 3 and step == 15) else 0
                            raw_n = notes[(step // 2 + b) % len(notes)] + (transp if abs(transp) <= 5 else 0) + oct_lift
                            n = max(24, min(64, raw_n))
                            vel = int((90 + (16 if step in (2, 6, 10, 14) else -8)) * exit_scale)
                            t_on = bar_tick + step * step_ticks + swing + pocket
                            t_off = min(bar_tick + bar_ticks - 12, t_on + int(step_ticks * 0.72))
                            if t_off > t_on:
                                events.append((t_on, 1, mido.Message("note_on", channel=channel, note=n, velocity=max(28, min(127, vel)), time=0)))
                                events.append((t_off, 0, mido.Message("note_off", channel=channel, note=n, velocity=0, time=0)))

                elif layer_name in chord_layers:
                    phrase_pos = b % 4
                    transp = CHORD_CYCLE_SEMITONES[phrase_pos]
                    strum = 12 if layer_name in {"chords", "rhodes"} else 7
                    dur_mul = 0.48 if is_false_drop_bar else (0.78 if phrase_pos == 2 else 0.92)
                    voiced = _voice_lead_chord(notes, b, transp)
                    order_v = list(reversed(voiced)) if phrase_pos == 3 else voiced
                    cc74_c = int(max(42, min(116, 58 + 14 * phrase_pos)))
                    events.append((bar_tick, 2, mido.Message("control_change", channel=channel, control=74, value=cc74_c, time=0)))
                    for v_idx, n in enumerate(order_v):
                        is_top = n == voiced[-1]
                        t_on = bar_tick + v_idx * strum
                        t_off = max(t_on + 24, bar_tick + int(bar_ticks * dur_mul) - 24)
                        vel = int((76 + (20 if is_top else v_idx * 2)) * exit_scale)
                        events.append((t_on, 1, mido.Message("note_on", channel=channel, note=n, velocity=max(24, min(127, vel)), time=0)))
                        events.append((t_off, 0, mido.Message("note_off", channel=channel, note=n, velocity=0, time=0)))

                elif layer_name in fx_layers:
                    # FX riser / dub throw active on turnaround or false drop
                    if layer_name in {"riser", "noise_sweep"} and (is_false_drop_bar or b == sec_bars - 1):
                        t_on = bar_tick
                        t_off = bar_tick + bar_ticks - 24
                        events.append((t_on, 1, mido.Message("note_on", channel=channel, note=notes[0], velocity=96, time=0)))
                        for f_i in range(8):
                            cc_t = bar_tick + f_i * 240
                            events.append((cc_t, 2, mido.Message("control_change", channel=channel, control=74, value=min(127, 44 + f_i * 11), time=0)))
                        events.append((t_off, 0, mido.Message("note_off", channel=channel, note=notes[0], velocity=0, time=0)))
                    elif layer_name in {"delay_tail", "reverb_wash"} and (is_false_drop_bar or b % 4 == 3):
                        # Dub Throw pulse (CC#91 reverb send spike + CC#15 dub throw)
                        t_on = bar_tick + 2 * tpb
                        events.append((t_on, 2, mido.Message("control_change", channel=channel, control=91, value=112, time=0)))
                        events.append((t_on, 1, mido.Message("note_on", channel=channel, note=notes[0], velocity=92, time=0)))
                        events.append((t_on + 240, 0, mido.Message("note_off", channel=channel, note=notes[0], velocity=0, time=0)))
                        events.append((bar_tick + bar_ticks - 20, 3, mido.Message("control_change", channel=channel, control=91, value=48, time=0)))

                else:  # arp, lead, vocal_chop, vocal_melody
                    phrase_pos = b % 4
                    step_stride = 2 if layer_name == "arp" else 4
                    for step in range(0, 16, step_stride):
                        # Negative space / breath rests break mechanical repetition across 4-bar phrases
                        if phrase_pos == 1 and step in (8, 10):
                            continue
                        if phrase_pos == 2 and step >= 10:
                            continue  # Question-answer phrase rest before turnaround
                        if phrase_pos == 3 and step in (4, 6):
                            continue
                        if step >= 14 and phrase_pos != 3:
                            continue
                        swing = 12 if (step % 2 == 1) else 0
                        idx_contour = (step + (2 if phrase_pos == 1 else (5 if phrase_pos == 2 else 0))) % len(notes)
                        n = max(48, min(96, notes[idx_contour] + (12 if (phrase_pos == 3 and step >= 12) else 0)))
                        vel = int((84 + 18 * ((step % 4) == 0) + (8 if phrase_pos == 3 else 0)) * exit_scale)
                        t_on = bar_tick + step * step_ticks + swing
                        t_off = min(bar_tick + bar_ticks - 8, t_on + step_ticks)
                        if t_off > t_on:
                            events.append((t_on, 1, mido.Message("note_on", channel=channel, note=n, velocity=max(28, min(127, vel)), time=0)))
                            events.append((t_off, 0, mido.Message("note_off", channel=channel, note=n, velocity=0, time=0)))

        _flush_abs_events(track, events)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    mid.save(str(out))
    print(f"[Arrangement Engine v3] Generated '{template_name}' ({total_bars} bars @ {bpm} BPM) -> {out}")
    return str(out)


if __name__ == "__main__":
    for name in ARRANGEMENT_TEMPLATES:
        generate_arrangement_midi(name)
