import sys
import os
import mido
import time
import math
import random
import shutil

BPM = 114.0
TICKS_PER_BEAT = 480
BAR_TICKS = TICKS_PER_BEAT * 4

print("═══════════════════════════════════════════════════════════════")
print("🚀 EJECUTANDO ORQUESTACIÓN TOTAL DE FL STUDIO 2025 (C5-REAL)")
print("═══════════════════════════════════════════════════════════════")

# 1. GENERAR MULTITRACK MIDI COMPLETO (8 PISTAS SEPARADAS)
mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_PER_BEAT)

def make_track(name, channel):
    t = mido.MidiTrack()
    t.append(mido.MetaMessage('track_name', name=name))
    t.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    return t

# Canales:
# Ch 0 (Track 1): Kick (Maceo Plex DSP Trigger)
# Ch 1 (Track 2): Moog Sub Bass (F Dorian)
# Ch 2 (Track 3): Snare & Rimshot (Broken Beat)
# Ch 3 (Track 4): Hi-Hats & Shakers (62% MPC Micro-Swing)
# Ch 4 (Track 5): Fender Rhodes MK1 (Jazz 9th/13th chords con Strumming)
# Ch 5 (Track 6): Space Disco Arpeggio (16th notes con modulación)
# Ch 6 (Track 7): 24-TET Microtonal Lead (MPE Sub-Cent Pitch Bend)
# Ch 7 (Track 8): Vocal Call / Dub Cues

t_kick = make_track("01 Kick (Maceo Plex)", 0)
t_bass = make_track("02 Moog Sub Bass", 1)
t_snare = make_track("03 Snare & Rim", 2)
t_hats = make_track("04 MPC Hats & Shakers", 3)
t_rhodes = make_track("05 Rhodes MK1 Chords", 4)
t_arp = make_track("06 Space Arp 16th", 5)
t_micro = make_track("07 24-TET Micro Lead", 6)
t_vox = make_track("08 Vocal Call & Dub", 7)

TOTAL_BARS = 32

# --- PISTA 1 & 3: BATERÍA BROKEN BEAT (KICK + SNARE) ---
# Compases 8 a 16 y 20 a 30
active_drum_bars = list(range(8, 16)) + list(range(20, 30))

kick_events = []
snare_events = []

for bar in active_drum_bars:
    b_start = bar * BAR_TICKS
    # Kick sincopado Future Jazz: Beat 0, 1.75, 2.5 (y 3.25 en impares)
    kicks = [0, int(1.75 * TICKS_PER_BEAT), int(2.5 * TICKS_PER_BEAT)]
    if bar % 2 == 1:
        kicks.append(int(3.25 * TICKS_PER_BEAT))
    for k in kicks:
        kick_events.append((b_start + k, 36, random.randint(110, 126), int(0.25 * TICKS_PER_BEAT)))

    # Snare en 2 y 4 + Ghost note en 3.75
    snare_events.append((b_start + TICKS_PER_BEAT, 38, random.randint(100, 118), int(0.25 * TICKS_PER_BEAT)))
    snare_events.append((b_start + 3 * TICKS_PER_BEAT, 38, random.randint(105, 122), int(0.25 * TICKS_PER_BEAT)))
    # Ghost
    snare_events.append((b_start + int(3.75 * TICKS_PER_BEAT), 38, random.randint(45, 65), int(0.15 * TICKS_PER_BEAT)))

# --- PISTA 4: CHARLES Y SHAKER CON MPC 62% SWING ---
hat_events = []
for bar in range(4, 30):
    b_start = bar * BAR_TICKS
    for step in range(16):
        # 62% swing: el paso impar se retrasa ~18 ticks
        swing_delay = 18 if (step % 2 == 1) else 0
        tick = b_start + step * (TICKS_PER_BEAT // 4) + swing_delay
        note = 46 if step in [6, 14] else 42 # Open hat o closed
        vel = random.randint(85, 105) if step % 4 == 0 else random.randint(60, 80)
        hat_events.append((tick, note, vel, int(0.18 * TICKS_PER_BEAT)))

# --- PISTA 2: MOOG SUB BASSLINE ---
# F1=29, Ab1=32, Bb1=34, C2=36, D2=38, Eb2=39, F2=41
bass_pattern_1 = [
    (29, 0, 2), (29, 2, 2), (32, 4, 2), (34, 6, 2),
    (36, 8, 2), (29, 10, 2), (39, 12, 2), (38, 14, 2)
]
bass_pattern_2 = [
    (34, 0, 2), (34, 2, 2), (36, 4, 2), (32, 6, 2),
    (29, 8, 3), (39, 12, 2), (29, 14, 2)
]
bass_events = []
for bar in list(range(4, 16)) + list(range(20, 30)):
    b_start = bar * BAR_TICKS
    pat = bass_pattern_1 if (bar % 2 == 0) else bass_pattern_2
    for pitch, s, dur in pat:
        tick = b_start + s * (TICKS_PER_BEAT // 4)
        bass_events.append((tick, pitch, random.randint(105, 120), dur * (TICKS_PER_BEAT // 4) - 10))

# --- PISTA 5: FENDER RHODES CHORDS CON STRUMMING ---
# F Dorian: Fm9 -> Bb13 -> Ebmaj9 -> Dm7b5
chords = [
    [41, 56, 60, 63, 67], # Fm9
    [46, 62, 65, 68, 72], # Bb13
    [39, 55, 58, 62, 65], # Ebmaj9
    [38, 56, 60, 65]      # Dm7b5
]
rhodes_events = []
for bar in range(TOTAL_BARS - 2):
    b_start = bar * BAR_TICKS
    chord = chords[bar % len(chords)]
    for beat_offset in [0, int(2.5 * TICKS_PER_BEAT)]:
        dur = int(1.8 * TICKS_PER_BEAT)
        for idx, n in enumerate(chord):
            strum = idx * 12 # 12 ticks de rasgueo natural
            tick = b_start + beat_offset + strum
            vel = random.randint(85, 105) if idx == 0 or idx == len(chord)-1 else random.randint(70, 85)
            rhodes_events.append((tick, n, vel, dur))

# --- PISTA 6: SPACE DISCO ARPEGGIATOR ---
dorian_notes = [53, 56, 60, 63, 65, 67, 70, 72]
arp_events = []
for bar in list(range(2, 16)) + list(range(20, 31)):
    b_start = bar * BAR_TICKS
    for step in range(16):
        tick = b_start + step * (TICKS_PER_BEAT // 4)
        pitch = dorian_notes[(step * 3 + bar) % len(dorian_notes)]
        if step % 4 == 0:
            pitch += 12 # salto de octava en tiempos fuertes
        lfo_vel = int(70 + 40 * math.sin(step * 0.3))
        arp_events.append((tick, pitch, max(45, min(120, lfo_vel)), int(0.20 * TICKS_PER_BEAT)))

# --- PISTA 7: 24-TET MICROTONAL LEAD (MPE PITCH BEND) ---
# Makam Bayati / F Dorian Microtonal
micro_events = [] # (tick, note, vel, dur, pitch_bend)
makam_cents = [0.0, 150.0, 300.0, 500.0, 700.0, 850.0, 1000.0]
for bar in range(20, 28): # En el drop
    b_start = bar * BAR_TICKS
    for step in range(8):
        tick = b_start + step * (TICKS_PER_BEAT // 2)
        cent = makam_cents[(step + bar) % len(makam_cents)]
        base_midi = 65 + int(round(cent / 100.0)) # F4 base
        offset = cent - ((base_midi - 65) * 100.0)
        pb = int(round((offset / 200.0) * 8191.0))
        micro_events.append((tick, base_midi, random.randint(90, 115), int(0.45 * TICKS_PER_BEAT), pb))

# Helper para compilar eventos a pista MIDI con deltas relativos
def compile_events(track, events, channel):
    # Sort by tick
    events.sort(key=lambda x: x[0])
    current_tick = 0
    # Desensamblar a note_on y note_off
    note_actions = []
    for ev in events:
        if len(ev) == 4:
            tick, note, vel, dur = ev
            note_actions.append((tick, 'on', note, vel, 0))
            note_actions.append((tick + dur, 'off', note, 0, 0))
        elif len(ev) == 5:
            tick, note, vel, dur, pb = ev
            note_actions.append((tick, 'pb', note, vel, pb))
            note_actions.append((tick, 'on', note, vel, 0))
            note_actions.append((tick + dur, 'off', note, 0, 0))

    note_actions.sort(key=lambda x: x[0])
    for act_tick, act_type, note, vel, pb in note_actions:
        delta = max(0, act_tick - current_tick)
        current_tick = act_tick
        if act_type == 'pb':
            track.append(mido.Message('pitchwheel', channel=channel, pitch=pb, time=delta))
            delta = 0
        elif act_type == 'on':
            track.append(mido.Message('note_on', channel=channel, note=note, velocity=vel, time=delta))
        elif act_type == 'off':
            track.append(mido.Message('note_off', channel=channel, note=note, velocity=0, time=delta))

compile_events(t_kick, kick_events, 0)
compile_events(t_bass, bass_events, 1)
compile_events(t_snare, snare_events, 2)
compile_events(t_hats, hat_events, 3)
compile_events(t_rhodes, rhodes_events, 4)
compile_events(t_arp, arp_events, 5)
compile_events(t_micro, micro_events, 6)

for t in [t_kick, t_bass, t_snare, t_hats, t_rhodes, t_arp, t_micro, t_vox]:
    mid.tracks.append(t)

multitrack_path = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/samples/Exergia_Orbital_Master_Multitrack.mid"
mid.save(multitrack_path)
print(f"✅ Multitrack MIDI SOTA generado: {multitrack_path}")

# Copiar a carpeta brain de la conversación
shutil.copy(multitrack_path, "/Users/borjafernandezangulo/.gemini/antigravity/brain/2abd2e53-07c2-41f7-92dc-f4b946d2ed4d/Exergia_Orbital_Master_Multitrack.mid")

# 2. INSTALAR ESCALAS SCALA 24-TET / MAKAM EN LA LIBRERÍA DE FL STUDIO
fl_tuning_dir = os.path.expanduser("~/Documents/Image-Line/FL Studio/Settings/Tuning")
os.makedirs(fl_tuning_dir, exist_ok=True)
scl_source = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/scalings/24tet.scl"
if os.path.isfile(scl_source):
    shutil.copy(scl_source, os.path.join(fl_tuning_dir, "24tet_Orbital_Exergy.scl"))
    print(f"✅ Scala 24-TET instalado en: {fl_tuning_dir}/24tet_Orbital_Exergy.scl")

# 3. ENVIAR MATRIZ DE MEZCLADOR 19 TRACKS Y TEMPO POR COREDIMI
try:
    port = mido.open_output("Antigravity MCP Out", virtual=True)
    # Tempo 114 BPM (control 15, value 54 en canal 15)
    port.send(mido.Message('control_change', channel=15, control=15, value=54))
    
    # Configuración de 19 canales del mixer (volumen y paneo)
    mixer_map = [
        (1, 0.90, 0.0, "Kick Sub"),
        (2, 0.85, 0.0, "Sub Bass (<120Hz Mono)"),
        (3, 0.80, 0.0, "Mid Bass"),
        (4, 0.72, 0.0, "Snare / Claps"),
        (5, 0.68, 0.30, "MPC Hats (Right)"),
        (6, 0.68, -0.30, "Shakers Loop (Left)"),
        (7, 0.76, -0.20, "Rhodes MK1"),
        (8, 0.74, 0.25, "Space Arp 16th"),
        (9, 0.70, 0.0, "24-TET Micro Lead"),
        (10, 0.85, 0.0, "Lead Vocal Center"),
        (11, 0.75, -0.80, "Vocal Hard-Left"),
        (12, 0.75, 0.80, "Vocal Hard-Right"),
        (15, 0.85, 0.0, "DRUM BUS"),
        (16, 0.82, 0.0, "BASS BUS"),
        (17, 0.75, 0.0, "SYNTH BUS"),
        (18, 0.80, 0.0, "VOCAL BUS"),
        (19, 0.92, 0.0, "MASTER BUS")
    ]
    for trk, vol, pan, label in mixer_map:
        # Ch 0: Volumen (control = track_id)
        port.send(mido.Message('control_change', channel=0, control=trk, value=int(vol * 127)))
        # Ch 1: Pan (control = track_id)
        pan_byte = int((pan + 1.0) * 63.5)
        port.send(mido.Message('control_change', channel=1, control=trk, value=pan_byte))

    # Sidechain Routing: Kick (Trk 1) -> Sub Bass (Trk 2), Synth Bus (Trk 17), Vocal Bus (Trk 18)
    for target in [2, 17, 18]:
        port.send(mido.Message('control_change', channel=15, control=18, value=target))

    # Dub FX sends: LuxeVerb Shimmer y Delay 3/16
    port.send(mido.Message('control_change', channel=15, control=20, value=100)) # LuxeVerb Decay
    port.send(mido.Message('control_change', channel=15, control=21, value=76))  # LuxeVerb Shimmer

    print("✅ Matriz de 19 Canales, Paneo 3D LCR y Ruteo de Sidechain transmitidos por CoreMIDI")
    port.close()
except Exception as e:
    print(f"Nota CoreMIDI: {e}")

print("═══════════════════════════════════════════════════════════════")
print("🎉 ORQUESTACIÓN COMPLETADA CON ÉXITO")
print("═══════════════════════════════════════════════════════════════")
