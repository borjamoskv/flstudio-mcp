#!/usr/bin/env python3
"""
Sovereign Musical Forge: Red River Mist (Sentimental Acid)
Homage to Andras - River Red (Joyful / Beats In Space Records BIS041)
Architecture: C5-REAL & FL Studio 2025 MCP Specification
BPM: 126.0 | Key: C Lydian / Fmaj7 | Sub-bass Monofonic < 120Hz
Generates:
1. Multi-track MIDI File (.mid) for FL Studio Channel Rack
2. Multitrack Stems (WAV 24-bit 44.1kHz)
3. Final Stereo Master (WAV 24-bit 44.1kHz)
4. FL Studio Piano Roll Script (.pyscript)
"""

import os
import struct
import wave
import mido
import numpy as np

OUTPUT_DIR = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/bounces/andras_river_red_sentimental_acid"
STEMS_DIR = os.path.join(OUTPUT_DIR, "stems")
os.makedirs(STEMS_DIR, exist_ok=True)

SR = 44100
BPM = 126.0
BEAT_SEC = 60.0 / BPM
BAR_SEC = BEAT_SEC * 4.0
NUM_BARS = 32  # 32 compases (~61 segundos de desarrollo temático completo)
TOTAL_SAMPLES = int(NUM_BARS * BAR_SEC * SR)

print("=== FORJANDO 'RED RIVER MIST (SENTIMENTAL ACID)' ===")
print(f"BPM: {BPM} | Duración: {NUM_BARS * BAR_SEC:.1f}s | Sample Rate: {SR} Hz")

# ---------------------------------------------------------
# 1. GENERACIÓN DE ARCHIVO MIDI MULTITRACK (.mid)
# ---------------------------------------------------------
def generate_midi():
    midi_path = os.path.join(OUTPUT_DIR, "Red_River_Mist_Sentimental_Acid.mid")
    mid = mido.MidiFile(type=1)
    mid.ticks_per_beat = 480
    ticks_per_beat = 480

    # Pista 0: Conductor
    t0 = mido.MidiTrack()
    mid.tracks.append(t0)
    t0.append(mido.MetaMessage('track_name', name='Conductor (126 BPM)'))
    t0.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))

    # Pista 1: 01_Kick_Sub (Ch 0) - Four-on-the-floor
    t1 = mido.MidiTrack()
    mid.tracks.append(t1)
    t1.append(mido.MetaMessage('track_name', name='01 Kick & Sub (Mono 50Hz)'))
    # Comienza en compás 4 (después de la intro flotante)
    start_beat = 4 * 4
    for b in range(start_beat, NUM_BARS * 4):
        # Kick en cada beat
        t1.append(mido.Message('note_on', channel=0, note=36, velocity=105, time=0 if b == start_beat else 240))
        t1.append(mido.Message('note_off', channel=0, note=36, velocity=0, time=240))

    # Pista 2: 02_Sentimental_Acid_303 (Ch 1) - TB-303 Arpegio Lidio / Mayor
    t2 = mido.MidiTrack()
    mid.tracks.append(t2)
    t2.append(mido.MetaMessage('track_name', name='02 Sentimental Acid 303 (C Lydian)'))
    # Riff de 16 semicorcheas por compás (C2 -> E2 -> G2 -> B2 -> C3 -> D3 -> E3...)
    riff_notes = [
        # Bar 1 (Fmaj7): F2, C3, E3, A3, F2, C3, E3, G3, F2, A3, C4, E4, F2, E3, C3, A2
        [41, 48, 52, 57, 41, 48, 52, 55, 41, 57, 60, 64, 41, 52, 48, 45],
        # Bar 2 (Cmaj7): C2, G2, B2, E3, C2, G2, B2, D3, C2, E3, G3, B3, C2, B2, G2, E2
        [36, 43, 47, 52, 36, 43, 47, 50, 36, 52, 55, 59, 36, 47, 43, 40],
        # Bar 3 (Dm9):   D2, A2, C3, F3, D2, A2, C3, E3, D2, F3, A3, C4, D2, C3, A2, F2
        [38, 45, 48, 53, 38, 45, 48, 52, 38, 53, 57, 60, 38, 48, 45, 41],
        # Bar 4 (G13sus): G2, D3, F3, B3, G2, D3, F3, A3, G2, B3, D4, E4, G2, F3, D3, B2
        [43, 50, 53, 59, 43, 50, 53, 57, 43, 59, 62, 64, 43, 53, 50, 47]
    ]
    # Entra en compás 8
    acid_start_bar = 8
    t2.append(mido.Message('control_change', channel=1, control=74, value=68, time=0)) # Cutoff inicial
    for bar in range(acid_start_bar, NUM_BARS):
        pattern = riff_notes[(bar - acid_start_bar) % 4]
        for idx, n in enumerate(pattern):
            # Acentos dinámicos
            vel = 110 if idx in (0, 3, 6, 10, 12) else 80
            t2.append(mido.Message('note_on', channel=1, note=n, velocity=vel, time=0 if (bar == acid_start_bar and idx == 0) else 15))
            t2.append(mido.Message('note_off', channel=1, note=n, velocity=0, time=105))

    # Pista 3: 03_Lydian_Pads (Ch 2) - Acordes sostenidos atmosféricos
    t3 = mido.MidiTrack()
    mid.tracks.append(t3)
    t3.append(mido.MetaMessage('track_name', name='03 Lydian Ambient Pads (Juno Warmth)'))
    pad_chords = [
        [53, 57, 60, 64, 65, 71], # Fmaj7(#11) -> F, A, C, E, F, B
        [48, 52, 55, 59, 64, 71], # Cmaj7 -> C, E, G, B, E, B
        [50, 53, 57, 60, 64, 69], # Dm9 -> D, F, A, C, E, A
        [43, 50, 53, 57, 60, 67]  # G9sus4 -> G, D, F, A, C, G
    ]
    ticks_per_bar = ticks_per_beat * 4
    for bar in range(NUM_BARS):
        chord = pad_chords[bar % 4]
        for n in chord:
            t3.append(mido.Message('note_on', channel=2, note=n, velocity=75, time=0))
        for i, n in enumerate(chord):
            t3.append(mido.Message('note_off', channel=2, note=n, velocity=0, time=ticks_per_bar if i == 0 else 0))

    # Pista 4: 04_Warm_Rhodes (Ch 3)
    t4 = mido.MidiTrack()
    mid.tracks.append(t4)
    t4.append(mido.MetaMessage('track_name', name='04 Nostalgic Rhodes Arpeggio'))
    # Arpegios de semicorchea dispersos estilo Melbourne sound
    for bar in range(NUM_BARS):
        base_chord = pad_chords[bar % 4]
        for step in range(8):
            note = base_chord[(step * 2) % len(base_chord)]
            t4.append(mido.Message('note_on', channel=3, note=note, velocity=68, time=0 if (bar == 0 and step == 0) else 60))
            t4.append(mido.Message('note_off', channel=3, note=note, velocity=0, time=180))

    # Pista 5: 05_Organic_Hats_Shaker (Ch 9)
    t5 = mido.MidiTrack()
    mid.tracks.append(t5)
    t5.append(mido.MetaMessage('track_name', name='05 Organic Shaker & Hats'))
    for b in range(start_beat, NUM_BARS * 4):
        # Shaker continuo en semicorcheas con swing Roger Linn
        for s in range(4):
            vel = 85 if s % 2 == 1 else 60
            t5.append(mido.Message('note_on', channel=9, note=42, velocity=vel, time=0 if (b == start_beat and s == 0) else 30))
            t5.append(mido.Message('note_off', channel=9, note=42, velocity=0, time=90))

    mid.save(midi_path)
    print(f"✓ MIDI multicanal exportado: {midi_path}")
    return midi_path

# ---------------------------------------------------------
# 2. SÍNTESIS BARE-METAL DSP DE STEMS Y MASTER (PCM 24-BIT)
# ---------------------------------------------------------
def synthesize_audio():
    np.linspace(0, NUM_BARS * BAR_SEC, TOTAL_SAMPLES, endpoint=False)
    
    # 1. KICK & SUB MONO (< 120Hz)
    kick_stem = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    start_kick_sample = int(4 * BAR_SEC * SR)
    beat_samples = int(BEAT_SEC * SR)
    
    kick_len = int(0.45 * SR)
    t_k = np.linspace(0, 0.45, kick_len, endpoint=False)
    # Barrido de frecuencia exponencial 150 Hz -> 48 Hz
    f_k = 48.0 + (150.0 - 48.0) * np.exp(-t_k / 0.045)
    phase_k = 2.0 * np.pi * np.cumsum(f_k) / SR
    env_k = np.exp(-t_k / 0.16) * (1.0 - np.exp(-t_k / 0.005))
    kick_single = np.sin(phase_k) * env_k * 0.95
    # Click de transitorio sutil
    click = np.sin(2.0 * np.pi * 950.0 * t_k) * np.exp(-t_k / 0.008) * 0.15
    kick_single += click

    for s in range(start_kick_sample, TOTAL_SAMPLES - kick_len, beat_samples):
        kick_stem[s:s+kick_len] += kick_single

    # 2. SENTIMENTAL ACID 303 (Filtro Diode Ladder Resonante modulado)
    acid_stem = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    acid_start_sample = int(8 * BAR_SEC * SR)
    step_samples = int((BEAT_SEC / 4.0) * SR)
    
    # Secuencia melódica en frecuencias Hz (Fmaj7 -> Cmaj7 -> Dm9 -> Gsus)
    chord_freqs = [
        [87.31, 130.81, 164.81, 220.00, 261.63, 329.63, 493.88], # F Lydian
        [65.41, 98.00, 123.47, 164.81, 196.00, 246.94, 329.63],  # C Maj
        [73.42, 110.00, 130.81, 174.61, 220.00, 293.66, 349.23], # Dm9
        [98.00, 146.83, 174.61, 220.00, 261.63, 392.00, 493.88]  # G13sus
    ]
    
    step_idx = 0
    for s in range(acid_start_sample, TOTAL_SAMPLES - step_samples, step_samples):
        bar_current = int(s / (BAR_SEC * SR))
        scale = chord_freqs[(bar_current - 8) % 4]
        f_note = scale[step_idx % len(scale)]
        step_idx += 1
        
        t_note = np.linspace(0, BEAT_SEC / 4.0, step_samples, endpoint=False)
        # Diente de sierra rico
        saw = 2.0 * (f_note * t_note - np.floor(f_note * t_note + 0.5))
        # Envolvente de filtro resonante modulada
        env_filt = np.exp(-t_note / 0.12)
        # Saturación analógica tipo tanh suave
        note_audio = np.tanh(saw * (1.5 + 2.5 * env_filt)) * np.exp(-t_note / 0.15) * 0.42
        acid_stem[s:s+step_samples] += note_audio

    # Filtro paso-bajo a 2200 Hz para el ácido (sedimento analógico)
    from scipy.signal import butter, sosfilt
    sos_acid = butter(4, 2200.0, btype='low', fs=SR, output='sos')
    acid_stem = sosfilt(sos_acid, acid_stem)

    # 3. LYDIAN PADS (Juno-106 analog warmth)
    pad_stem_L = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    pad_stem_R = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    
    pad_freqs_prog = [
        [174.61, 220.00, 261.63, 329.63, 493.88], # Fmaj7(#11)
        [130.81, 164.81, 196.00, 246.94, 329.63], # Cmaj7
        [146.83, 174.61, 220.00, 261.63, 329.63], # Dm9
        [196.00, 261.63, 293.66, 349.23, 392.00]  # G9sus4
    ]
    
    for bar in range(NUM_BARS):
        s_bar = int(bar * BAR_SEC * SR)
        e_bar = min(TOTAL_SAMPLES, int((bar + 1) * BAR_SEC * SR))
        t_b = np.linspace(0, (e_bar - s_bar)/SR, e_bar - s_bar, endpoint=False)
        freqs = pad_freqs_prog[bar % 4]
        
        # Envolvente suave con ataque de 0.8s y decaimiento
        env_pad = np.maximum(0.0, np.sin(np.pi * np.clip(t_b / BAR_SEC, 0.0, 1.0))) ** 0.8
        
        pad_mono = np.zeros(len(t_b), dtype=np.float64)
        for f in freqs:
            # Osciladores desafinados con chorus sutil
            pad_mono += np.sin(2.0 * np.pi * f * t_b) * 0.12
            pad_mono += np.sin(2.0 * np.pi * (f * 1.002) * t_b) * 0.08
            pad_mono += np.sin(2.0 * np.pi * (f * 0.998) * t_b) * 0.08
            
        pad_mono *= env_pad
        # Paneo estéreo cálido y coherente (LPC > 0.95)
        pad_stem_L[s_bar:e_bar] += pad_mono * 0.9
        pad_stem_R[s_bar:e_bar] += pad_mono * 1.0

    sos_pad = butter(4, [180.0, 4800.0], btype='bandpass', fs=SR, output='sos')
    pad_stem_L = sosfilt(sos_pad, pad_stem_L)
    pad_stem_R = sosfilt(sos_pad, pad_stem_R)

    # 4. ORGANIC SHAKER & HATS
    shaker_stem = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    shaker_start = int(4 * BAR_SEC * SR)
    for s in range(shaker_start, TOTAL_SAMPLES - int(0.1*SR), int((BEAT_SEC/2.0)*SR)):
        # Ruido modelado filtrado a 7500 Hz con caída suave
        dur = int(0.08 * SR)
        t_sh = np.linspace(0, 0.08, dur, endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, dur) * np.exp(-t_sh / 0.02) * 0.18
        shaker_stem[s:s+dur] += noise
        
    sos_shaker = butter(3, [3500.0, 12000.0], btype='bandpass', fs=SR, output='sos')
    shaker_stem = sosfilt(sos_shaker, shaker_stem)

    # 5. NOSTALGIC VOCAL LOOP ("When I feel...")
    # Síntesis formántica armónica evocadora
    vocal_stem = np.zeros(TOTAL_SAMPLES, dtype=np.float64)
    vocal_start = int(2 * BAR_SEC * SR)
    # Frase cada 4 compases
    for s in range(vocal_start, TOTAL_SAMPLES - int(3.0*SR), int(4.0 * BAR_SEC * SR)):
        dur_v = int(2.4 * SR)
        t_v = np.linspace(0, 2.4, dur_v, endpoint=False)
        # Formantes vocales /e/ y /i/
        f0 = 261.63 # C4
        v_sound = (np.sin(2*np.pi*f0*t_v) * 0.3 +
                   np.sin(2*np.pi*f0*2*t_v) * 0.2 +
                   np.sin(2*np.pi*480*t_v) * 0.25 +   # Formante 1
                   np.sin(2*np.pi*1850*t_v) * 0.18 +  # Formante 2
                   np.sin(2*np.pi*2500*t_v) * 0.12)   # Formante 3
        # Envolvente silábica ("When... I... feel...")
        env_v = (np.sin(np.pi * (t_v / 0.7)) * (t_v < 0.7) * 0.8 +
                 np.sin(np.pi * ((t_v - 0.7) / 0.5)) * ((t_v >= 0.7) & (t_v < 1.2)) * 0.6 +
                 np.sin(np.pi * ((t_v - 1.2) / 1.1)) * ((t_v >= 1.2) & (t_v < 2.3)) * 0.9)
        vocal_stem[s:s+dur_v] += v_sound * env_v * 0.25

    # Retardo dub estéreo filtrado a 2400 Hz
    delay_samples = int(0.357 * SR) # Dotted eighth note delay at 126 BPM
    dub_tail = np.zeros(TOTAL_SAMPLES)
    for rep in range(1, 4):
        pos = rep * delay_samples
        gain = (0.45 ** rep)
        if pos < TOTAL_SAMPLES:
            dub_tail[pos:] += vocal_stem[:-pos] * gain
    vocal_stem += dub_tail
    sos_vocal = butter(3, 2400.0, btype='low', fs=SR, output='sos')
    vocal_stem = sosfilt(sos_vocal, vocal_stem)

    # ---------------------------------------------------------
    # EXPORTACIÓN DE STEMS PCM WAV (24-BIT)
    # ---------------------------------------------------------
    def save_wav_24bit(filename, data_L, data_R=None):
        path = os.path.join(STEMS_DIR, filename)
        if data_R is None:
            data_R = data_L
        # Normalizar sin clipping
        max_val = max(np.max(np.abs(data_L)), np.max(np.abs(data_R)), 1e-6)
        scale = 0.90 / max_val if max_val > 0.90 else 1.0
        
        # Empacar 24-bit PCM
        samples_L = np.clip(data_L * scale * 8388607.0, -8388607, 8388607).astype(np.int32)
        samples_R = np.clip(data_R * scale * 8388607.0, -8388607, 8388607).astype(np.int32)
        
        raw_bytes = bytearray()
        for l, r in zip(samples_L, samples_R):  # noqa: E741
            raw_bytes.extend(struct.pack('<i', l)[:3])
            raw_bytes.extend(struct.pack('<i', r)[:3])
            
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(3)
            wf.setframerate(SR)
            wf.writeframes(raw_bytes)
        print(f"  ✓ Stem guardado: {filename}")
        return path

    print("\nGuardando Stems Multitrack 24-bit:")
    save_wav_24bit("01_Kick_Sub_Mono.wav", kick_stem, kick_stem)
    save_wav_24bit("02_Sentimental_Acid_303.wav", acid_stem, acid_stem)
    save_wav_24bit("03_Lydian_Ambient_Pads.wav", pad_stem_L, pad_stem_R)
    save_wav_24bit("04_Organic_Shaker_Hats.wav", shaker_stem * 0.95, shaker_stem * 1.05)
    save_wav_24bit("05_Vocal_Mantra_WhenIFeel.wav", vocal_stem, vocal_stem)

    # ---------------------------------------------------------
    # MASTERIZACIÓN ESTÉREO CLUB C5 (Bark Carving, Glue, Soft-Clip)
    # ---------------------------------------------------------
    print("\nProcesando Master Estéreo C5:")
    master_L = kick_stem * 0.85 + acid_stem * 0.65 + pad_stem_L * 0.55 + shaker_stem * 0.35 + vocal_stem * 0.45
    master_R = kick_stem * 0.85 + acid_stem * 0.65 + pad_stem_R * 0.55 + shaker_stem * 0.38 + vocal_stem * 0.45

    # Lecho de cinta analógica (-58 dBFS)
    tape_noise = np.random.normal(0, 0.0012, TOTAL_SAMPLES)
    master_L += tape_noise
    master_R += tape_noise

    # Consolidación subgrave monofónica estricta < 120Hz (Linkwitz-Riley)
    sos_sub = butter(4, 120.0, btype='low', fs=SR, output='sos')
    sub_mono = sosfilt(sos_sub, (master_L + master_R) * 0.5)
    
    sos_hi = butter(4, 120.0, btype='high', fs=SR, output='sos')
    hi_L = sosfilt(sos_hi, master_L)
    hi_R = sosfilt(sos_hi, master_R)
    
    master_L = sub_mono + hi_L
    master_R = sub_mono + hi_R

    # Soft-clipping analógico suave (tanh)
    master_L = np.tanh(master_L * 1.15)
    master_R = np.tanh(master_R * 1.15)

    # Techo True Peak a -0.5 dBTP
    pk = max(np.max(np.abs(master_L)), np.max(np.abs(master_R)))
    target_pk = 10.0 ** (-0.5 / 20.0)
    master_L = master_L * (target_pk / pk)
    master_R = master_R * (target_pk / pk)

    master_path = os.path.join(OUTPUT_DIR, "Red_River_Mist_Sentimental_Acid_Master.wav")
    samples_L = np.clip(master_L * 8388607.0, -8388607, 8388607).astype(np.int32)
    samples_R = np.clip(master_R * 8388607.0, -8388607, 8388607).astype(np.int32)
    raw_master = bytearray()
    for l, r in zip(samples_L, samples_R):  # noqa: E741
        raw_master.extend(struct.pack('<i', l)[:3])
        raw_master.extend(struct.pack('<i', r)[:3])

    with wave.open(master_path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(3)
        wf.setframerate(SR)
        wf.writeframes(raw_master)
    print(f"✓ Master 24-bit generado: {master_path}")
    return master_path

# ---------------------------------------------------------
# 3. SCRIPT PARA PIANO ROLL DE FL STUDIO (.pyscript)
# ---------------------------------------------------------
def generate_flpianoroll_script():
    pyscript_path = os.path.join(OUTPUT_DIR, "Sentimental_Acid_Generator.pyscript")
    code = '''# FL Studio 2025 Piano Roll Script: Sentimental Acid Generator
# Inspired by Andras - River Red (Lydian Mode / Major 7th Acid Arpeggiator)
import flpianoroll as flp

def createDialog():
    form = flp.ScriptDialog("Sentimental Acid (C5)", "Genera arpegios ácidos mayores y lídios.")
    form.AddInputCombo("Modo Tonal", "C Lydian,F Major 7,D Minor 9,G 13sus4", 0)
    form.AddInputKnob("Swing Roger Linn", 58, 50, 75)
    form.AddInputCheckbox("Slide en Notas Altas", True)
    form.AddInputKnob("Acento Probabilidad", 35, 10, 80)
    return form

def apply(form):
    mode = form.GetInputValue("Modo Tonal")
    swing = form.GetInputValue("Swing Roger Linn")
    slide = form.GetInputValue("Slide en Notas Altas")
    accent_prob = form.GetInputValue("Acento Probabilidad")
    
    scales = [
        [48, 52, 55, 59, 62, 66, 71], # C Lydian
        [53, 57, 60, 64, 69, 72, 77], # Fmaj7
        [50, 53, 57, 60, 64, 69, 72], # Dm9
        [43, 50, 53, 57, 60, 65, 67]  # G13sus
    ]
    notes_pool = scales[int(mode)]
    
    flp.score.clear()
    ppq = flp.score.PPQ
    step_ticks = ppq // 4 # Semicorchea
    
    for step in range(32):
        n = flp.Note()
        n_pitch = notes_pool[step % len(notes_pool)]
        n.number = n_pitch
        
        # Swing en pasos impares
        time_offset = int((swing - 50) * 0.02 * step_ticks) if (step % 2 == 1) else 0
        n.time = step * step_ticks + time_offset
        n.length = int(step_ticks * 0.85)
        
        # Acento
        is_accent = (step % 4 == 0) or ((step * 7) % 100 < accent_prob)
        n.velocity = 0.95 if is_accent else 0.65
        
        # Slide en saltos de octava
        if slide and (step % 8 == 7):
            n.slide = True
            
        flp.score.addNote(n)
'''
    with open(pyscript_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"✓ Script FL Piano Roll (.pyscript) generado: {pyscript_path}")
    return pyscript_path

if __name__ == "__main__":
    generate_midi()
    master = synthesize_audio()
    generate_flpianoroll_script()
    print("\n¡FORJA COMPLETA EXITOSA!")
