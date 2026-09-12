import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
import random
import math
from pathlib import Path

PPQ = 480
BPM = 112
TEMPO_US = mido.bpm2tempo(BPM)
BAR_TICKS = PPQ * 4
SIXTEENTH = PPQ // 4
TRIPLET = PPQ // 3

midi = MidiFile(type=1, ticks_per_beat=PPQ)

def build_track(events, track_name, channel=0):
    track = MidiTrack()
    track.append(MetaMessage('track_name', name=track_name, time=0))
    events.sort(key=lambda x: (x[0], 0 if x[1] == 'note_off' else 1))
    
    last_t = 0
    for item in events:
        t = item[0]
        mtype = item[1]
        delta = max(0, t - last_t)
        
        if mtype in ['note_on', 'note_off']:
            _, _, note, vel = item
            track.append(Message(mtype, note=note, velocity=vel, time=delta, channel=channel))
        elif mtype == 'pitchwheel':
            _, _, pitch = item
            track.append(Message('pitchwheel', pitch=pitch, time=delta, channel=channel))
        elif mtype == 'control_change':
            _, _, control, value = item
            track.append(Message('control_change', control=control, value=value, time=delta, channel=channel))
        elif mtype == 'marker':
            _, _, text = item
            track.append(MetaMessage('marker', text=text, time=delta))
            
        last_t = t
        
    track.append(MetaMessage('end_of_track', time=0))
    return track

# ── Track 0: Conductor & Markers (64 Bars) ───────────────────────────
conductor_events = [
    (0, 'marker', '1. Intro Atmosférica (Noche en Neo-Cádiz)'),
    (8 * BAR_TICKS, 'marker', '2. Desarrollo 1 (Entrada Bajo Cyberpunk)'),
    (16 * BAR_TICKS, 'marker', '3. Tensión & Redoble Frigio'),
    (24 * BAR_TICKS, 'marker', '4. Drop 1 (Danza del Cíborg)'),
    (40 * BAR_TICKS, 'marker', '5. Breakdown (Falseta Mística Rubato)'),
    (48 * BAR_TICKS, 'marker', '6. Build 2 (Amalgama de Bulerías)'),
    (56 * BAR_TICKS, 'marker', '7. Climax Final (Tercera de Picardía & Outro)'),
]

# Harmony definitions (D Phrygian Dominant)
# Gm9 (iv), Fmaj7 (bIII), Ebmaj7(#11) (bII), D7(b9) (I)
CHORDS_ANDALUSIAN = [
    {"root": 31, "name": "Gm9", "notes": [55, 58, 62, 65, 69]},
    {"root": 29, "name": "Fmaj7", "notes": [53, 57, 60, 64, 67]},
    {"root": 27, "name": "Ebmaj7(#11)", "notes": [51, 55, 58, 62, 69]},
    {"root": 26, "name": "D7(b9)", "notes": [50, 54, 57, 60, 63]},
]
# Picardy resolution chord (Dmaj9)
CHORD_PICARDY = {"root": 26, "name": "Dmaj9", "notes": [50, 54, 57, 61, 64]}

# Containers
guitar_events = []
chords_events = []
bass_events = []
sub_events = []
lead_events = []
drum_events = []
palmas_cajon_events = []

# Helper for rasgueado strumming
def add_rasgueado(events, start_t, notes, direction=1, duration=720, vel=95, strum_spread=14):
    ordered = notes if direction == 1 else list(reversed(notes))
    for i, n in enumerate(ordered):
        t_note = start_t + (i * strum_spread)
        d_note = max(180, duration - (i * strum_spread))
        v_note = max(60, min(125, int(vel + random.uniform(-5, 5))))
        events.append((t_note, 'note_on', n, v_note))
        events.append((t_note + d_note, 'note_off', n, 0))

# ─────────────────────────────────────────────────────────────────────
# COMPOSICIÓN DE LAS 7 SECCIONES (64 COMPASES)
# ─────────────────────────────────────────────────────────────────────

# ═════════════════════════════════════════════════════════════════════
# SECCIÓN 1: INTRO (Compases 1 - 8)
# ═════════════════════════════════════════════════════════════════════
for bar in range(8):
    bar_t = bar * BAR_TICKS
    chord_info = CHORDS_ANDALUSIAN[(bar // 2) % 4]
    
    # Pad atmosférico suave sostenido
    for n in chord_info["notes"]:
        chords_events.append((bar_t, 'note_on', n, 55))
        chords_events.append((bar_t + BAR_TICKS - 40, 'note_off', n, 0))
        
    # Falseta de guitarra flamenca introductoria (notas individuales expresivas)
    falseta_scale = [62, 63, 66, 67, 69, 70, 74] # D, Eb, F#, G, A, Bb, D
    for step in range(4):
        if step % 2 == 0 or (bar % 2 == 1 and step == 3):
            t_f = bar_t + (step * PPQ) + random.randint(-4, 4)
            p_f = random.choice(falseta_scale)
            guitar_events.append((t_f, 'note_on', p_f, 85))
            guitar_events.append((t_f + int(PPQ * 0.85), 'note_off', p_f, 0))
            
    # Latido sub grave suave en compases 5-8
    if bar >= 4:
        sub_events.append((bar_t, 'note_on', chord_info["root"], 75))
        sub_events.append((bar_t + PPQ * 2, 'note_off', chord_info["root"], 0))

# ═════════════════════════════════════════════════════════════════════
# SECCIÓN 2: DESARROLLO 1 (Compases 9 - 16)
# ═════════════════════════════════════════════════════════════════════
for bar in range(8, 16):
    bar_t = bar * BAR_TICKS
    chord_info = CHORDS_ANDALUSIAN[((bar - 8) // 2) % 4]
    root = chord_info["root"]
    
    # 1. Bajo Rodante Synthwave en semicorcheas
    for step in range(16):
        s_t = bar_t + (step * SIXTEENTH)
        is_oct = (step % 2 == 1)
        b_note = root + (12 if is_oct else 0)
        v_b = 110 if (step % 4 == 0) else (95 if is_oct else 85)
        bass_events.append((s_t, 'note_on', b_note, v_b))
        bass_events.append((s_t + int(SIXTEENTH * 0.75), 'note_off', b_note, 0))
        
    # 2. Chords con rasgueos sutiles en compás 1 y 2
    triggers = [0, 960]
    for tr in triggers:
        add_rasgueado(chords_events, bar_t + tr, chord_info["notes"], direction=1, duration=880, vel=88)
        
    # 3. Hi-Hats y Kick suave
    drum_events.append((bar_t, 'note_on', 36, 110)) # Kick on 1
    drum_events.append((bar_t + 160, 'note_off', 36, 0))
    drum_events.append((bar_t + (PPQ * 2), 'note_on', 36, 105)) # Kick on 3
    drum_events.append((bar_t + (PPQ * 2) + 160, 'note_off', 36, 0))
    
    for step in range(16):
        h_t = bar_t + (step * SIXTEENTH)
        h_vel = 88 if step % 4 == 0 else 65
        drum_events.append((h_t, 'note_on', 42, h_vel))
        drum_events.append((h_t + 50, 'note_off', 42, 0))
        
    # 4. Palmas flamencas sordas entrando en compases 13-16
    if bar >= 12:
        for ps in [2, 5, 8, 11, 14]:
            p_t = bar_t + (ps * SIXTEENTH) + 8
            palmas_cajon_events.append((p_t, 'note_on', 39, 90))
            palmas_cajon_events.append((p_t + 60, 'note_off', 39, 0))

# ═════════════════════════════════════════════════════════════════════
# SECCIÓN 3: TENSIÓN & REDOBLE FRIGIO (Compases 17 - 24)
# ═════════════════════════════════════════════════════════════════════
for bar in range(16, 24):
    bar_t = bar * BAR_TICKS
    rel_bar = bar - 16
    
    # Acordes en crescendo de tensión hacia Ebmaj7(#11) y D7(b9)
    chord_info = CHORDS_ANDALUSIAN[2] if rel_bar < 4 else CHORDS_ANDALUSIAN[3]
    
    # Rasgueados flamencos agresivos
    add_rasgueado(chords_events, bar_t, chord_info["notes"], direction=1, duration=700, vel=min(125, 90 + rel_bar * 4))
    add_rasgueado(chords_events, bar_t + 720, chord_info["notes"], direction=-1, duration=600, vel=min(125, 95 + rel_bar * 4))
    
    # Bajo pulsante en corcheas
    for b_step in range(8):
        b_t = bar_t + (b_step * (PPQ // 2))
        bass_events.append((b_t, 'note_on', chord_info["root"], 105))
        bass_events.append((b_t + int(PPQ * 0.4), 'note_off', chord_info["root"], 0))
        
    # Snare roll acelerado en compases 21-23
    if rel_bar >= 4 and rel_bar < 7:
        sub_div = 4 if rel_bar == 4 else (8 if rel_bar == 5 else 16)
        div_len = BAR_TICKS // sub_div
        for s in range(sub_div):
            sn_t = bar_t + (s * div_len)
            sn_vel = min(127, 75 + (rel_bar * 12) + (s * 3))
            drum_events.append((sn_t, 'note_on', 38, sn_vel))
            drum_events.append((sn_t + int(div_len * 0.7), 'note_off', 38, 0))
            
    # Compás 24: SILENCIO SÚBITO en tiempos 3 y 4 (el 'corte flamenco')
    if rel_bar == 7:
        # Solo tiempo 1 y 2 tienen sonido
        add_rasgueado(guitar_events, bar_t, [50, 54, 57, 60, 63], direction=1, duration=480, vel=127)
        drum_events.append((bar_t, 'note_on', 36, 127))
        drum_events.append((bar_t + 200, 'note_off', 36, 0))
        drum_events.append((bar_t + PPQ, 'note_on', 38, 127))
        drum_events.append((bar_t + PPQ + 200, 'note_off', 38, 0))
        # Tiempos 3 y 4: SILENCIO ABSOLUTO (deja colar el delay dub)

# ═════════════════════════════════════════════════════════════════════
# SECCIÓN 4: DROP 1 (Compases 25 - 40, 16 Compases)
# ═════════════════════════════════════════════════════════════════════
for bar in range(24, 40):
    bar_t = bar * BAR_TICKS
    rel_bar = bar - 24
    chord_info = CHORDS_ANDALUSIAN[(rel_bar // 2) % 4]
    root = chord_info["root"]
    
    # 1. Batería Synthwave Pesada: Bombo en 1 y 3, Gated Snare en 2 y 4
    drum_events.append((bar_t, 'note_on', 36, 127)) # Kick 1
    drum_events.append((bar_t + 160, 'note_off', 36, 0))
    drum_events.append((bar_t + (PPQ * 2), 'note_on', 36, 125)) # Kick 3
    drum_events.append((bar_t + (PPQ * 2) + 160, 'note_off', 36, 0))
    
    drum_events.append((bar_t + PPQ, 'note_on', 38, 127)) # Gated Snare 2
    drum_events.append((bar_t + PPQ + 260, 'note_off', 38, 0))
    drum_events.append((bar_t + (PPQ * 3), 'note_on', 38, 127)) # Gated Snare 4
    drum_events.append((bar_t + (PPQ * 3) + 260, 'note_off', 38, 0))
    
    # Hi-Hats a semicorcheas con acentos
    for step in range(16):
        h_t = bar_t + (step * SIXTEENTH)
        h_vel = 110 if step in [0, 4, 8, 12] else (95 if step % 2 == 0 else 78)
        drum_events.append((h_t, 'note_on', 42, h_vel))
        drum_events.append((h_t + 50, 'note_off', 42, 0))
        
    # 2. Palmas Claras Flamencas & Cajón Golpe Agudo
    for ps in [2, 5, 8, 11, 14]:
        p_t = bar_t + (ps * SIXTEENTH) + 10
        palmas_cajon_events.append((p_t, 'note_on', 39, 115)) # Palmas Claras
        palmas_cajon_events.append((p_t + 80, 'note_off', 39, 0))
    # Cajón golpe grave en contratiempo de beat 2
    palmas_cajon_events.append((bar_t + PPQ + SIXTEENTH * 2, 'note_on', 35, 108))
    palmas_cajon_events.append((bar_t + PPQ + SIXTEENTH * 2 + 100, 'note_off', 35, 0))
    
    # 3. Bajo Rodante Cyberpunk
    for step in range(16):
        s_t = bar_t + (step * SIXTEENTH)
        is_oct = (step % 2 == 1) or (step % 4 == 3)
        b_note = root + (12 if is_oct else 0)
        v_b = 120 if (step % 4 == 0) else (105 if is_oct else 92)
        bass_events.append((s_t, 'note_on', b_note, v_b))
        bass_events.append((s_t + int(SIXTEENTH * 0.72), 'note_off', b_note, 0))
        
    # 4. Rasgueados Synth Chords
    for tr in [0, 720, 1440]:
        add_rasgueado(chords_events, bar_t + tr, chord_info["notes"], direction=(1 if tr % 2 == 0 else -1), duration=640, vel=108)
        
    # 5. Lead Solo Melismático Flamenco (Línea desgarradora en Re Frigio Dominante)
    solo_notes = [62, 63, 66, 67, 69, 70, 74, 75, 78] # D4, Eb4, F#4, G4, A4, Bb4, D5, Eb5, F#5
    lead_steps = [0, 180, 360, 480, 720, 960, 1200, 1440, 1680]
    for l_idx, l_off in enumerate(lead_steps):
        if random.random() < 0.25 and l_off not in [0, 480, 960]:
            continue
        l_t = bar_t + l_off
        p = random.choice(solo_notes)
        l_len = 160
        lead_events.append((l_t, 'note_on', p, 116))
        lead_events.append((l_t + l_len, 'note_off', p, 0))
        # Microtonal pitch bend en la sensible flamenca (Eb bajando a D)
        if p in [63, 75]:
            lead_events.append((l_t + 60, 'pitchwheel', -2048)) # -50 cents bend
            lead_events.append((l_t + l_len - 10, 'pitchwheel', 0))

# ═════════════════════════════════════════════════════════════════════
# SECCIÓN 5: BREAKDOWN (Compases 41 - 48, 8 Compases)
# ═════════════════════════════════════════════════════════════════════
for bar in range(40, 48):
    bar_t = bar * BAR_TICKS
    rel_bar = bar - 40
    chord_info = CHORDS_ANDALUSIAN[(rel_bar // 2) % 4]
    
    # Pads flotantes
    for n in chord_info["notes"]:
        chords_events.append((bar_t, 'note_on', n, 60))
        chords_events.append((bar_t + BAR_TICKS - 30, 'note_off', n, 0))
        
    # Falseta de Guitarra Flamenca pura con rubato
    falseta_phrase = [
        (0, 74, 320), (360, 75, 180), (540, 74, 240), (800, 70, 400),
        (1200, 69, 300), (1500, 67, 200), (1700, 66, 400)
    ]
    for f_off, f_note, f_dur in falseta_phrase:
        if bar % 2 == 0:
            guitar_events.append((bar_t + f_off, 'note_on', f_note, 96))
            guitar_events.append((bar_t + f_off + f_dur, 'note_off', f_note, 0))

# ═════════════════════════════════════════════════════════════════════
# SECCIÓN 6: BUILD 2 AMALGAMA BULERÍAS (Compases 49 - 56, 8 Compases)
# ═════════════════════════════════════════════════════════════════════
for bar in range(48, 56):
    bar_t = bar * BAR_TICKS
    rel_bar = bar - 48
    chord_info = CHORDS_ANDALUSIAN[3] if rel_bar >= 4 else CHORDS_ANDALUSIAN[2]
    
    # Compás flamenco de 12 tiempos (Bulerías amalgama adaptada a semicorcheas de 4/4)
    # Acentos en pasos: 2, 5, 8, 10, 12
    buleria_accents = [2, 5, 8, 10, 12, 14]
    for b_step in range(16):
        s_t = bar_t + (b_step * SIXTEENTH)
        is_acc = b_step in buleria_accents
        vel_p = 120 if is_acc else 70
        palmas_cajon_events.append((s_t, 'note_on', 39 if is_acc else 35, vel_p))
        palmas_cajon_events.append((s_t + 50, 'note_off', 39 if is_acc else 35, 0))
        
    # Arpegios ascendentes de sintetizador
    arp_scale = [50, 54, 57, 62, 66, 69, 74, 78]
    for s in range(16):
        a_t = bar_t + (s * SIXTEENTH)
        pitch = arp_scale[s % len(arp_scale)]
        v_a = min(127, 75 + (rel_bar * 6) + (s * 2))
        lead_events.append((a_t, 'note_on', pitch, v_a))
        lead_events.append((a_t + int(SIXTEENTH * 0.8), 'note_off', pitch, 0))

# ═════════════════════════════════════════════════════════════════════
# SECCIÓN 7: CLIMAX FINAL & OUTRO (Compases 57 - 64, 8 Compases)
# ═════════════════════════════════════════════════════════════════════
for bar in range(56, 64):
    bar_t = bar * BAR_TICKS
    rel_bar = bar - 56
    
    # MODULACIÓN EUFÓRICA: Tercera de Picardía a Dmaj9 en compases 57-60
    if rel_bar < 4:
        chord_info = CHORD_PICARDY
        root = chord_info["root"]
    else:
        # Retorno a Re Frigio oscuro para el desvanecimiento final
        chord_info = CHORDS_ANDALUSIAN[3]
        root = chord_info["root"]
        
    # Batería completa solo en 57-60, disipando en 61-64
    if rel_bar < 4:
        drum_events.append((bar_t, 'note_on', 36, 127))
        drum_events.append((bar_t + 160, 'note_off', 36, 0))
        drum_events.append((bar_t + (PPQ * 2), 'note_on', 36, 127))
        drum_events.append((bar_t + (PPQ * 2) + 160, 'note_off', 36, 0))
        drum_events.append((bar_t + PPQ, 'note_on', 38, 127))
        drum_events.append((bar_t + PPQ + 260, 'note_off', 38, 0))
        drum_events.append((bar_t + (PPQ * 3), 'note_on', 38, 127))
        drum_events.append((bar_t + (PPQ * 3) + 260, 'note_off', 38, 0))
        
        # Bajo rodante
        for step in range(16):
            s_t = bar_t + (step * SIXTEENTH)
            is_oct = (step % 2 == 1)
            b_note = root + (12 if is_oct else 0)
            bass_events.append((s_t, 'note_on', b_note, 115))
            bass_events.append((s_t + int(SIXTEENTH * 0.72), 'note_off', b_note, 0))
            
        # Rasgueados radiantes
        add_rasgueado(chords_events, bar_t, chord_info["notes"], direction=1, duration=800, vel=120)
        add_rasgueado(chords_events, bar_t + 960, chord_info["notes"], direction=-1, duration=800, vel=115)
    else:
        # Outro: Desvanecimiento
        if rel_bar == 4:
            # Último rasgueo abierto que decae
            add_rasgueado(guitar_events, bar_t, [50, 54, 57, 60, 63], direction=1, duration=BAR_TICKS * 3, vel=110)
            sub_events.append((bar_t, 'note_on', 26, 95))
            sub_events.append((bar_t + BAR_TICKS * 2, 'note_off', 26, 0))

# Ensamblar todas las pistas
midi.tracks.append(build_track(conductor_events, 'Conductor & Secciones', channel=0))
midi.tracks.append(build_track(guitar_events, 'Guitarra / Falseta Flamenca', channel=0))
midi.tracks.append(build_track(chords_events, 'Rasgueado Synth Chords (Pad/Brass)', channel=1))
midi.tracks.append(build_track(bass_events, 'Rolling Cyberpunk Bass (16ths)', channel=2))
midi.tracks.append(build_track(sub_events, 'Sub Bass Drone (808/Moog)', channel=3))
midi.tracks.append(build_track(lead_events, 'Dark Phrygian Lead Solo', channel=4))
midi.tracks.append(build_track(drum_events, 'Synthwave Linndrum Kit', channel=9))
midi.tracks.append(build_track(palmas_cajon_events, 'Palmas & Cajon Flamenco', channel=10))

out_file = Path.home() / "Music/FL Studio Bounces/Dark_Cyber_Flamenco_Masterpiece_64Bars.mid"
out_file.parent.mkdir(parents=True, exist_ok=True)
midi.save(str(out_file))
print(f"[✓] 64-Bar Masterpiece MIDI successfully saved to: {out_file}")
