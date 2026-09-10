#!/usr/bin/env python3
"""
EL DUENDE DEL COSMOS MICROTONAL
================================
Master Multi-Track Song Arrangement Generator (144 Bars at 122 BPM)
Fuses 7 iconic influences:
1. The Cure (Post-punk chorus bassline & atmospheric melancholic guitar/synth)
2. Röyksopp (Scandinavian cosmic analog pads & crystalline synth leads)
3. COIL (Esoteric industrial sub-drone, occult 24-TET pitch shading & metallic textures)
4. Lindstrøm (Space disco arpeggiated bass with VCF filter sweeps)
5. Camarón de la Isla (Cante jondo lead synth with vocal melismas & quejíos)
6. Paco de Lucía (Virtuosic flamenco guitar falsetas & compás polyrhythm)
7. Solomun (Melodic techno 50Hz punch kick, driving swing hats & breakdown euphoria)

Tuning System: 24-TET Makam Bayati / Hijaz / Modo Flamenco por Arriba (Root E)
"""

import math
import os
import random
import mido

WORKSPACE_DIR = os.path.expanduser("~/10_PROJECTS/flstudio-mcp")
OUTPUT_MIDI_PATH = os.path.join(WORKSPACE_DIR, "samples", "el_duende_del_cosmos_microtonal.mid")

BPM = 122.0
TICKS_PER_BEAT = 480
BEATS_PER_BAR = 4
TICKS_PER_BAR = TICKS_PER_BEAT * BEATS_PER_BAR # 1920 ticks

def cents_to_pitch_bend(cents_offset: float, semitone_range: float = 2.0) -> int:
    """Converts cents offset (-200..+200) to 14-bit MIDI pitch bend (-8192..+8191)."""
    max_cents = semitone_range * 100.0
    normalized = max(-1.0, min(1.0, cents_offset / max_cents))
    return int(round(normalized * 8191.0))

# -----------------------------------------------------------------------------
# Scale & Chords (Por Arriba / E Phrygian Dominant + 24-TET Quarter-Tones)
# E=52/64, F=53/65, G#=56/68, A=57/69, B=59/71, C=60/72, D=62/74
# -----------------------------------------------------------------------------
# Pitch Bends for 24-TET microtonal inflections:
# F neutral 2nd: -50 cents on F
# G# neutral 3rd: -50 cents on G#
# D neutral 7th: +50 cents on D
PB_NEUTRAL_MINUS50 = cents_to_pitch_bend(-50.0)
PB_NEUTRAL_PLUS50 = cents_to_pitch_bend(50.0)

SECTIONS = [
    {"name": "1. Intro (COIL Industrial Drone & Röyksopp Pads)", "bars": 16},
    {"name": "2. Verse 1 (The Cure Post-Punk Bass & Lindstrøm Arp)", "bars": 16},
    {"name": "3. Flamenco Solitude (Paco Guitar Falseta & Camarón Cante)", "bars": 16},
    {"name": "4. Build-Up (Solomun Ingress & 24-TET Arp Escalation)", "bars": 16},
    {"name": "5. Main Peak Drop 1 (Full 7-Influence Fusion)", "bars": 32},
    {"name": "6. Breakdown / Silence (COIL Sub-Drone & Camarón Quejío)", "bars": 16},
    {"name": "7. False Drop & Microtonal Picardy Shift", "bars": 8},
    {"name": "8. Final Apex Drop 2 (Maximum Euphoric Cosmic Flamenco)", "bars": 16},
    {"name": "9. Outro / Deconstruction (Paco Guitar Fade & COIL Residual)", "bars": 8},
]

def generate_duende_cosmico_midi() -> str:
    mid = mido.MidiFile(type=1)
    mid.ticks_per_beat = TICKS_PER_BEAT

    # -------------------------------------------------------------------------
    # TRACK 0: Master Conductor & Markers
    # -------------------------------------------------------------------------
    tr_conductor = mido.MidiTrack()
    mid.tracks.append(tr_conductor)
    tr_conductor.append(mido.MetaMessage('track_name', name='Master Tempo & Structure (122 BPM)'))
    tr_conductor.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))

    curr_tick = 0
    for sec in SECTIONS:
        tr_conductor.append(mido.MetaMessage('marker', text=sec["name"], time=curr_tick if curr_tick == 0 else 0))
        curr_tick = sec["bars"] * TICKS_PER_BAR

    # -------------------------------------------------------------------------
    # TRACK 1: The Cure - Post-Punk Chorus Bass (Channel 0)
    # -------------------------------------------------------------------------
    tr_cure_bass = mido.MidiTrack()
    mid.tracks.append(tr_cure_bass)
    tr_cure_bass.append(mido.MetaMessage('track_name', name='The Cure - Post-Punk Chorus Bass'))

    # Cure Bassline Riff (Driving 8ths/16ths with melodic octaves)
    # Bars 17-96 & 113-136
    cure_pattern = [
        # Bar 1: E2 drive
        (40, 0, 240, 100), (40, 240, 240, 85), (52, 480, 240, 105), (40, 720, 240, 85),
        (41, 960, 240, 95), (40, 1200, 240, 85), (52, 1440, 240, 100), (40, 1680, 240, 90),
        # Bar 2: F2 to G#2 progression
        (41, 1920, 240, 100), (41, 2160, 240, 85), (53, 2400, 240, 105), (41, 2640, 240, 85),
        (44, 2880, 240, 95), (41, 3120, 240, 85), (56, 3360, 240, 100), (40, 3600, 240, 90)
    ]

    total_bars = sum(s["bars"] for s in SECTIONS)
    for b in range(1, total_bars + 1):
        # Active in Verse 1, Main Drop 1, False Drop, Apex Drop 2
        if (17 <= b <= 32) or (49 <= b <= 96) or (113 <= b <= 136):
            bar_start = (b - 1) * TICKS_PER_BAR
            pattern_offset = ((b - 1) % 2) * 1920
            for note, t_rel, dur, vel in cure_pattern:
                if t_rel < 1920 and pattern_offset == 0:
                    abs_t = bar_start + t_rel
                    tr_cure_bass.append(mido.Message('note_on', channel=0, note=note, velocity=vel, time=0 if len(tr_cure_bass) > 1 else abs_t))
                    tr_cure_bass.append(mido.Message('note_off', channel=0, note=note, velocity=0, time=dur))
                elif t_rel >= 1920 and pattern_offset == 1920:
                    abs_t = bar_start + (t_rel - 1920)
                    tr_cure_bass.append(mido.Message('note_on', channel=0, note=note, velocity=vel, time=0))
                    tr_cure_bass.append(mido.Message('note_off', channel=0, note=note, velocity=0, time=dur))

    # Sort track events by absolute time to ensure valid MIDI output
    def sanitize_track(track):
        # Re-order messages by accumulated time
        events = []
        cur = 0
        for msg in track:
            if hasattr(msg, 'time'):
                cur += msg.time
                events.append((cur, msg))
        events.sort(key=lambda x: x[0])
        
        new_track = mido.MidiTrack()
        last_t = 0
        for t, msg in events:
            msg_copy = msg.copy(time=t - last_t)
            new_track.append(msg_copy)
            last_t = t
        return new_track

    # -------------------------------------------------------------------------
    # TRACK 2: Röyksopp - Warm Analog Pads & Cosmic Synth (Channel 1)
    # -------------------------------------------------------------------------
    tr_royksopp = mido.MidiTrack()
    mid.tracks.append(tr_royksopp)
    tr_royksopp.append(mido.MetaMessage('track_name', name='Röyksopp - Warm Analog Space Pads'))

    # Chord progression: E5/Emaj -> Fmaj7 -> Am9 -> E5 (Por Arriba Flamenco-Pop)
    royksopp_chords = [
        [52, 64, 68, 71, 76], # E maj (Por Arriba)
        [53, 65, 69, 72, 77], # F maj7
        [45, 60, 64, 69, 72], # A min9
        [52, 64, 68, 71, 76]  # E maj
    ]

    for b in range(1, total_bars + 1):
        if (1 <= b <= 32) or (49 <= b <= 112) or (121 <= b <= 140):
            bar_start = (b - 1) * TICKS_PER_BAR
            chord = royksopp_chords[(b - 1) % len(royksopp_chords)]
            for n in chord:
                tr_royksopp.append(mido.Message('note_on', channel=1, note=n, velocity=75, time=bar_start if n == chord[0] else 0))
            for n in chord:
                tr_royksopp.append(mido.Message('note_off', channel=1, note=n, velocity=0, time=TICKS_PER_BAR - 10 if n == chord[0] else 0))

    # -------------------------------------------------------------------------
    # TRACK 3: COIL - Esoteric Industrial Sub-Drone & 24-TET (Channel 2)
    # -------------------------------------------------------------------------
    tr_coil = mido.MidiTrack()
    mid.tracks.append(tr_coil)
    tr_coil.append(mido.MetaMessage('track_name', name='COIL - Industrial 50Hz Sub-Drone'))

    # Continuous low sub-drone (E1 = Note 28) with 24-TET pitch modulation
    for b in range(1, total_bars + 1):
        if (1 <= b <= 24) or (81 <= b <= 120) or (137 <= b <= 144):
            bar_start = (b - 1) * TICKS_PER_BAR
            # Apply subtle occult 24-TET microtonal drift
            pb = PB_NEUTRAL_MINUS50 if (b % 4 == 0) else 0
            tr_coil.append(mido.Message('pitchwheel', channel=2, pitch=pb, time=bar_start))
            tr_coil.append(mido.Message('note_on', channel=2, note=28, velocity=110, time=0))
            tr_coil.append(mido.Message('note_off', channel=2, note=28, velocity=0, time=TICKS_PER_BAR - 20))

    # -------------------------------------------------------------------------
    # TRACK 4: Lindstrøm - Space Disco Arp (Channel 3)
    # -------------------------------------------------------------------------
    tr_lindstrom = mido.MidiTrack()
    mid.tracks.append(tr_lindstrom)
    tr_lindstrom.append(mido.MetaMessage('track_name', name='Lindstrøm - Space Disco 24-TET Arp'))

    # 16th-note arpeggiator motif with 24-TET microtonal quarter-tones
    arp_notes = [64, 65, 68, 71, 72, 74, 76, 77]
    for b in range(1, total_bars + 1):
        if (17 <= b <= 96) or (113 <= b <= 136):
            bar_start = (b - 1) * TICKS_PER_BAR
            for s in range(16): # 16th notes per bar
                step_t = bar_start + (s * 120)
                n = arp_notes[(b * 3 + s) % len(arp_notes)]
                pb = PB_NEUTRAL_MINUS50 if n in [65, 77] else (PB_NEUTRAL_PLUS50 if n == 74 else 0)
                
                tr_lindstrom.append(mido.Message('pitchwheel', channel=3, pitch=pb, time=step_t if s == 0 else 0))
                tr_lindstrom.append(mido.Message('note_on', channel=3, note=n, velocity=random.randint(85, 105), time=0))
                tr_lindstrom.append(mido.Message('note_off', channel=3, note=n, velocity=0, time=100))

    # -------------------------------------------------------------------------
    # TRACK 5: Camarón de la Isla - Cante Jondo Vocal Lead (Channel 4)
    # -------------------------------------------------------------------------
    tr_camaron = mido.MidiTrack()
    mid.tracks.append(tr_camaron)
    tr_camaron.append(mido.MetaMessage('track_name', name='Camarón - Cante Jondo Vocal Lead'))

    # Expressive vocal melismas ("Quejíos" - Ay, ay, ay) in 24-TET
    camaron_phrases = [
        # Phrase 1: Intense intro quejío (Bar 33-40)
        (33, [(76, 0, 960, 115, 0), (74, 960, 480, 100, PB_NEUTRAL_PLUS50), (72, 1440, 480, 90, 0)]),
        (34, [(71, 0, 960, 105, 0), (68, 960, 480, 95, PB_NEUTRAL_MINUS50), (65, 1440, 480, 100, PB_NEUTRAL_MINUS50)]),
        (35, [(64, 0, 1920, 120, 0)]), # Sustained Duende root
        # Phrase 2: Breakdown peak emotional cante (Bar 97-104)
        (97, [(76, 0, 1440, 125, 0), (77, 1440, 480, 110, PB_NEUTRAL_MINUS50)]),
        (98, [(76, 0, 960, 115, 0), (74, 960, 960, 105, PB_NEUTRAL_PLUS50)]),
        (99, [(72, 0, 480, 100, 0), (71, 480, 480, 95, 0), (68, 960, 480, 110, PB_NEUTRAL_MINUS50), (64, 1440, 480, 120, 0)])
    ]

    for b_num, p_notes in camaron_phrases:
        bar_start = (b_num - 1) * TICKS_PER_BAR
        for n, rel_t, dur, vel, pb in p_notes:
            abs_t = bar_start + rel_t
            tr_camaron.append(mido.Message('pitchwheel', channel=4, pitch=pb, time=abs_t))
            tr_camaron.append(mido.Message('note_on', channel=4, note=n, velocity=vel, time=0))
            tr_camaron.append(mido.Message('note_off', channel=4, note=n, velocity=0, time=dur - 10))

    # -------------------------------------------------------------------------
    # TRACK 6: Paco de Lucía - Flamenco Guitar Falsetas (Channel 5)
    # -------------------------------------------------------------------------
    tr_paco = mido.MidiTrack()
    mid.tracks.append(tr_paco)
    tr_paco.append(mido.MetaMessage('track_name', name='Paco de Lucía - Flamenco Guitar Falseta'))

    # Fast syncopated picado runs & rasgueado chords (Por Arriba)
    # Active in Flamenco Solitude (Bars 33-48), Main Drop (65-80), Apex Drop (121-136)
    falseta_notes = [64, 65, 68, 69, 71, 72, 74, 76, 77, 80]
    for b in range(1, total_bars + 1):
        if (33 <= b <= 48) or (65 <= b <= 80) or (121 <= b <= 136) or (137 <= b <= 144):
            bar_start = (b - 1) * TICKS_PER_BAR
            # 3/4 over 4/4 syncopated compás
            for i in range(12): # 12-beat compás accents
                rel_t = i * 160
                abs_t = bar_start + rel_t
                n = falseta_notes[(b * 2 + i) % len(falseta_notes)]
                pb = PB_NEUTRAL_MINUS50 if n in [65, 77] else 0
                vel = 120 if (i % 3 == 0) else random.randint(85, 105)
                
                tr_paco.append(mido.Message('pitchwheel', channel=5, pitch=pb, time=abs_t))
                tr_paco.append(mido.Message('note_on', channel=5, note=n, velocity=vel, time=0))
                tr_paco.append(mido.Message('note_off', channel=5, note=n, velocity=0, time=130))

    # -------------------------------------------------------------------------
    # TRACK 7: Solomun - Melodic Techno Kick & Drums (Channel 9 / Percussion)
    # -------------------------------------------------------------------------
    tr_solomun_drums = mido.MidiTrack()
    mid.tracks.append(tr_solomun_drums)
    tr_solomun_drums.append(mido.MetaMessage('track_name', name='Solomun - Melodic Techno Drums'))

    # Kick (C1=36), Snare/Clap (D1=38), Closed Hat (F#1=42), Open Hat (A#1=46)
    for b in range(1, total_bars + 1):
        # Drums active in Build-Up, Main Drop 1, False Drop, Apex Drop 2
        kick_active = (49 <= b <= 96) or (113 <= b <= 136)
        hats_active = (17 <= b <= 96) or (113 <= b <= 138)
        
        bar_start = (b - 1) * TICKS_PER_BAR
        
        if kick_active:
            # 4-on-the-floor driving kick
            for beat in range(4):
                k_time = bar_start + (beat * 480)
                tr_solomun_drums.append(mido.Message('note_on', channel=9, note=36, velocity=127, time=k_time))
                tr_solomun_drums.append(mido.Message('note_off', channel=9, note=36, velocity=0, time=120))
                
                # Clap on beats 2 and 4
                if beat in [1, 3]:
                    tr_solomun_drums.append(mido.Message('note_on', channel=9, note=38, velocity=110, time=k_time))
                    tr_solomun_drums.append(mido.Message('note_off', channel=9, note=38, velocity=0, time=140))

        if hats_active:
            # Offbeat open hi-hat + 62% swing 16th closed hi-hats
            for s in range(16):
                h_time = bar_start + (s * 120)
                if s % 4 == 2: # Offbeat open hat
                    tr_solomun_drums.append(mido.Message('note_on', channel=9, note=46, velocity=105, time=h_time))
                    tr_solomun_drums.append(mido.Message('note_off', channel=9, note=46, velocity=0, time=90))
                elif s % 2 == 1: # Swing closed hat
                    swing_t = h_time + 15 # 62% swing offset
                    tr_solomun_drums.append(mido.Message('note_on', channel=9, note=42, velocity=85, time=swing_t))
                    tr_solomun_drums.append(mido.Message('note_off', channel=9, note=42, velocity=0, time=70))

    # Sanitize and re-order all tracks to guarantee valid MIDI timestamps
    sanitized_tracks = []
    for tr in mid.tracks:
        sanitized_tracks.append(sanitize_track(tr))
    mid.tracks = sanitized_tracks

    os.makedirs(os.path.dirname(OUTPUT_MIDI_PATH), exist_ok=True)
    mid.save(OUTPUT_MIDI_PATH)
    print(f" Successfully generated Master Multi-Track MIDI -> {OUTPUT_MIDI_PATH}")
    return OUTPUT_MIDI_PATH

if __name__ == "__main__":
    generate_duende_cosmico_midi()
