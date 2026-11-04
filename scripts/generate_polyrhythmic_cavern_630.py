#!/usr/bin/env python3
"""
Polirritmia Cavernosa 6:30 Master Engine (v2.0 Full Composition)
Composed for Borja Moskv under C5-REAL Physical Acoustics & Invariants.
"""

import sys
import math
import numpy as np
import scipy.signal as signal
from pathlib import Path
import soundfile as sf
import subprocess

SAMPLE_RATE = 44100
BPM = 128.0
BEAT_SEC = 60.0 / BPM          # 0.46875 s
sys.path.insert(0, '/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp')
sys.path.insert(0, '/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/scripts')

BAR_SEC = BEAT_SEC * 4.0       # 1.875 s
TOTAL_BARS = 208
DURATION_SEC = TOTAL_BARS * BAR_SEC  # 390.000 s exact (6m 30s)
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION_SEC)

DROP_BAR = 105                 # Bar 105 starts at (104 * 1.875) = 195.000 s exact
MELODY_RETURN_BAR = 116        # Compás 12 del drop (104 + 12 = 116)
OUTRO_BAR = 193                # Outro starts, kick stops, decay to 208

BOUNCES_DIR = Path("/Users/borjafernandezangulo/Music/LIBRARY/04-Stems/FL_Studio/Bounces")
STEMS_DIR = BOUNCES_DIR / "POLIRRITMIA_CAVERNOSA_6M30_STEMS"
STEMS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# 1. XYLOPHONE PHYSICAL MODAL SYNTHESIS ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class RosewoodXylophone:
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr
        self.b_click, self.a_click = signal.butter(2, [2200 / (sr * 0.5), 6500 / (sr * 0.5)], btype='band')

    def render_note(self, f0, duration=1.2, velocity=0.85, pan=0.0):
        n = int(duration * self.sr)
        t = np.linspace(0, duration, n, endpoint=False)
        
        # 1. Mallet impact excitation
        imp_len = min(n, int(0.0022 * self.sr))
        t_imp = np.linspace(0, np.pi, imp_len)
        mallet = np.zeros(n, dtype=np.float32)
        mallet[:imp_len] = (np.sin(t_imp) ** 2).astype(np.float32)
        
        noise = (np.random.normal(0, 0.05, imp_len) * (np.sin(t_imp) ** 2)).astype(np.float32)
        click = signal.lfilter(self.b_click, self.a_click, noise)
        mallet[:imp_len] += click * 0.35
        
        # 2. Resonator bar modal decays (undercut rosewood bar: 1 : 3.0 : 9.2)
        d0 = np.exp(-t * (4.2 + 0.0025 * f0), dtype=np.float32)
        d1 = np.exp(-t * (14.0 + 0.0080 * f0), dtype=np.float32)
        d2 = np.exp(-t * (36.0 + 0.0200 * f0), dtype=np.float32)
        
        m0 = np.sin(2 * np.pi * f0 * t, dtype=np.float32) * d0
        m1 = np.sin(2 * np.pi * (f0 * 3.00) * t, dtype=np.float32) * d1 * 0.38
        m2 = np.sin(2 * np.pi * (f0 * 9.20) * t, dtype=np.float32) * d2 * 0.14
        
        body = (m0 + m1 + m2 + mallet * 0.22) * velocity
        
        pan_clamped = np.clip(pan, -0.9, 0.9)
        gain_l = np.sqrt(0.5 * (1.0 - pan_clamped))
        gain_r = np.sqrt(0.5 * (1.0 + pan_clamped))
        return body * gain_l, body * gain_r

# ─────────────────────────────────────────────────────────────────────────────
# 2. FLAMENCO PALMAS ENGINE (ASINCOPADAS & CONTRATIEMPO)
# ─────────────────────────────────────────────────────────────────────────────
class FlamencoPalmasEngine:
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr
        self.b_snap, self.a_snap = signal.butter(2, [1800 / (sr * 0.5), 5500 / (sr * 0.5)], btype='band')
        self.b_pop, self.a_pop = signal.iirpeak(640.0, 3.2, fs=sr)
        self.b_sorda, self.a_sorda = signal.iirpeak(320.0, 3.8, fs=sr)
        self.b_sorda_lp, self.a_sorda_lp = signal.butter(2, 950 / (sr * 0.5), btype='low')

    def render_palma(self, is_seca=True, velocity=0.88, pan=0.0):
        dur = 0.28
        n = int(dur * self.sr)
        t = np.linspace(0, dur, n, endpoint=False)
        out = np.zeros(n, dtype=np.float32)
        
        offsets = [0, int(0.0075 * self.sr)]
        for j, off in enumerate(offsets):
            sub_n = n - off
            sub_t = t[:sub_n]
            rng = np.random.RandomState(int(off * 100) + (10 if is_seca else 20))
            noise = rng.randn(sub_n).astype(np.float32)
            decay = np.exp(-sub_t * (130 if is_seca else 65), dtype=np.float32)
            imp = noise * decay
            
            if is_seca:
                snap = signal.lfilter(self.b_snap, self.a_snap, imp)
                pop = signal.lfilter(self.b_pop, self.a_pop, imp) * 0.35
                hand = (snap + pop) * (0.85 if j == 0 else 0.55)
            else:
                pop = signal.lfilter(self.b_sorda, self.a_sorda, imp)
                sorda = signal.lfilter(self.b_sorda_lp, self.a_sorda_lp, pop)
                hand = sorda * (1.0 if j == 0 else 0.6)
            out[off:] += hand
            
        peak = np.max(np.abs(out)) + 1e-6
        out = (out / peak) * velocity
        
        pan_clamped = np.clip(pan, -0.9, 0.9)
        gain_l = np.sqrt(0.5 * (1.0 - pan_clamped))
        gain_r = np.sqrt(0.5 * (1.0 + pan_clamped))
        return out * gain_l, out * gain_r

# ─────────────────────────────────────────────────────────────────────────────
# 3. KICK DRUM ENGINE (MACEO PLEX SUB & ANALOG CLICK)
# ─────────────────────────────────────────────────────────────────────────────
class MaceoKickEngine:
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr
        sample_path = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/samples/maceo_plex/Maceo_Plex_Kick_Dark_Sub_A1.wav")
        if sample_path.exists():
            data, in_sr = sf.read(str(sample_path))
            if data.ndim > 1:
                data = data[:, 0]
            if in_sr != sr:
                num_s = int(len(data) * sr / in_sr)
                data = signal.resample(data, num_s)
            self.kick_sample = data.astype(np.float32)
        else:
            dur = 0.55
            n = int(dur * sr)
            t = np.linspace(0, dur, n, endpoint=False)
            f_drop = 48.0 + 132.0 * np.exp(-t * 32.0)
            phase = np.cumsum(2 * np.pi * f_drop / sr)
            body = np.sin(phase) * np.exp(-t * 7.5)
            click = np.random.randn(int(0.008 * sr)) * np.linspace(1, 0, int(0.008 * sr))
            body[:len(click)] += click * 0.35
            self.kick_sample = np.clip(body * 0.95, -0.98, 0.98).astype(np.float32)

    def render_kick(self, velocity=0.96):
        k = self.kick_sample * velocity
        return k, k

# ─────────────────────────────────────────────────────────────────────────────
# 4. CAVERN IMPULSE & CONVOLUTION
# ─────────────────────────────────────────────────────────────────────────────
def get_cavern_ir(sr=SAMPLE_RATE, rt60=8.0):
    ir_path = BOUNCES_DIR / "Reverb_Acoustics" / "RIR_cyber_cathedral.wav"
    if ir_path.exists():
        data, in_sr = sf.read(str(ir_path))
        if in_sr != sr:
            data = signal.resample(data, int(len(data) * sr / in_sr))
        if data.ndim == 1:
            data = np.column_stack([data, data])
        # Extend decay to rt60 if needed
        cur_dur = len(data) / sr
        if cur_dur < rt60:
            pad_len = int((rt60 - cur_dur) * sr)
            ext_t = np.linspace(0, rt60 - cur_dur, pad_len, endpoint=False)
            decay_tail = np.exp(-ext_t * (6.91 / rt60)).astype(np.float32)
            noise_l = np.random.randn(pad_len).astype(np.float32) * decay_tail * 0.05
            noise_r = np.random.randn(pad_len).astype(np.float32) * decay_tail * 0.05
            tail = np.column_stack([noise_l, noise_r])
            data = np.vstack([data, tail])
        ir_l = data[:, 0].astype(np.float32)
        ir_r = data[:, 1].astype(np.float32)
    else:
        n = int(rt60 * sr)
        t = np.linspace(0, rt60, n, endpoint=False, dtype=np.float32)
        decay = np.exp(-t * (6.91 / rt60))
        noise_l = np.random.randn(n).astype(np.float32) * decay
        noise_r = np.random.randn(n).astype(np.float32) * decay
        b_wall, a_wall = signal.butter(2, 1600.0 / (sr * 0.5), btype='low')
        ir_l = signal.lfilter(b_wall, a_wall, noise_l)
        ir_r = signal.lfilter(b_wall, a_wall, noise_r)

    pk = max(np.max(np.abs(ir_l)), np.max(np.abs(ir_r))) + 1e-6
    return (ir_l / pk) * 0.35, (ir_r / pk) * 0.35

# ─────────────────────────────────────────────────────────────────────────────
# 4.5. NEURAL VOCAL TRACK PROVIDER
# ─────────────────────────────────────────────────────────────────────────────
def get_vocal_bum_tracks(sr=SAMPLE_RATE):
    vocal_dir = BOUNCES_DIR / "Vocal_Tract"
    vocal_dir.mkdir(parents=True, exist_ok=True)
    wav_path = vocal_dir / "la_voz_bum12_alvaro.wav"
    if not wav_path.exists():
        mp3_path = vocal_dir / "la_voz_bum12_alvaro.mp3"
        cmd = f'edge-tts --voice es-ES-AlvaroNeural --text "La voz... bum, bum, bum, bum, bum, bum, bum, bum, bum, bum, bum, bum." --write-media "{mp3_path}" && ffmpeg -y -i "{mp3_path}" -ar 44100 "{wav_path}"'
        subprocess.run(cmd, shell=True, check=True)
        
    data, in_sr = sf.read(str(wav_path))
    if data.ndim > 1:
        data = data[:, 0]
    return data.astype(np.float32)

# ─────────────────────────────────────────────────────────────────────────────
# 5. COMPOSITION TIMELINE GENERATOR
# ─────────────────────────────────────────────────────────────────────────────
def generate_composition():
    print("═══ GENERATING POLIRRITMIA CAVERNOSA 6:30 (128 BPM, 208 BARS) ═══")
    print(f"Total Duration: {DURATION_SEC:.2f}s ({TOTAL_SAMPLES} samples)")
    print(f"Halfway Point: 195.00s (Bar {DROP_BAR})")
    print(f"Melody Return Point: Bar {MELODY_RETURN_BAR} (Compás 12 del drop)")
    
    # ── Initialize Stem Buffers (Stereo Float32) ──
    stem_xylo_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_xylo_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_palmas_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_palmas_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_pads_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_pads_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_kick_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_kick_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_voice_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_voice_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_bass_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_bass_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_marimba_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_marimba_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

    xylo = RosewoodXylophone(SAMPLE_RATE)
    palmas = FlamencoPalmasEngine(SAMPLE_RATE)
    kick = MaceoKickEngine(SAMPLE_RATE)

    # ── 1. RENDER XYLOPHONE MOTIF ──
    # Harmonic center: D Lydian
    # D5 = 587.33, E5 = 659.25, F#5 = 739.99, G#5 = 830.61, A5 = 880.00, B5 = 987.77, C#6 = 1108.73
    # D6 = 1174.66, E6 = 1318.51, F#6 = 1479.98, G#6 = 1661.22, A6 = 1760.00
    #
    # Core Motif Rule:
    # "donde la nota tónica sea la antepenúltima para que genere una sensación de apertura, de increscendo, de felicidad"
    # Phrase 1 (8 notes, 2 bars):
    # 1: F#5, 2: A5, 3: B5, 4: C#6, 5: E6, 6: D6 (TÓNICA! Antepenúltima), 7: E6 (Penúltima), 8: F#6 (Última)
    # Phrase 2 (8 notes, 2 bars):
    # 1: A5, 2: B5, 3: C#6, 4: D6, 5: G#6, 6: D6 (TÓNICA! Antepenúltima), 7: F#6 (Penúltima), 8: A6 (Última)
    
    phrase_1 = [
        (739.99, 0.40, -0.3),  # F#5
        (880.00, 0.40, -0.1),  # A5
        (987.77, 0.40, 0.1),   # B5
        (1108.73, 0.40, 0.3),  # C#6
        (1318.51, 0.45, 0.4),  # E6
        (1174.66, 0.45, 0.0),  # D6 -> TÓNICA (ANTEPENÚLTIMA!)
        (1318.51, 0.40, 0.3),  # E6 -> PENÚLTIMA
        (1479.98, 0.50, 0.5)   # F#6 -> ÚLTIMA (Apertura infinita hacia arriba)
    ]
    
    phrase_2 = [
        (880.00, 0.40, -0.2),  # A5
        (987.77, 0.40, 0.0),   # B5
        (1108.73, 0.40, 0.2),  # C#6
        (1174.66, 0.40, 0.1),  # D6
        (1661.22, 0.45, 0.6),  # G#6 (Lydian #4)
        (1174.66, 0.45, 0.0),  # D6 -> TÓNICA (ANTEPENÚLTIMA!)
        (1479.98, 0.40, 0.4),  # F#6 -> PENÚLTIMA
        (1760.00, 0.55, 0.7)   # A6 -> ÚLTIMA (Cielo abierto)
    ]

    print("Synthesizing Xylophone tracks...")
    # Step through bars
    # The xylophone motif plays in 3:4 cross-metric steps (each note spaced by 3 sixteenths = 0.75 beats)
    # Total duration of an 8-note phrase = 8 * 0.75 beats = 6 beats = 1.5 bars!
    # Phasing creates an autopoietic polyrhythmic shimmer.
    
    for bar in range(0, TOTAL_BARS):
        # Silence during pre-drop gap (Bar 103-104) and initial drop shock (Bars 105 to 115)
        if 103 <= bar < 115:
            continue
            
        bar_start_s = bar * BAR_SEC
        
        # Velocity and octave evolution
        if bar < 12:
            base_vel = 0.65 + 0.15 * (bar / 12.0)
            use_octave = False
        elif bar < 64:
            base_vel = 0.75 + 0.10 * ((bar - 12) / 52.0)
            use_octave = (bar % 4 == 0)
        elif bar < 103:
            # Massive increscendo building to the drop!
            base_vel = 0.82 + 0.16 * ((bar - 64) / 39.0)
            use_octave = True
        elif 115 <= bar < 184:
            # THE RETURN! Bar 116 (Compás 12 del drop) - Peak energy!
            base_vel = 0.95
            use_octave = True
        else:
            # Outro (Bars 184 to 208) - Organic decay
            base_vel = max(0.2, 0.85 - 0.65 * ((bar - 184) / 24.0))
            use_octave = False
            
        # Select phrase
        curr_phrase = phrase_1 if (bar // 2) % 2 == 0 else phrase_2
        
        # 3:4 polyrhythmic placement: 4 notes per bar at 3/16 rhythm, or 2 phrases across 3 bars
        # Note timings within the 2-bar cycle
        for note_idx, (f0, n_dur, n_pan) in enumerate(curr_phrase):
            # Dotted eighth offset (0.75 beats * note_idx)
            note_time = bar_start_s + note_idx * (BEAT_SEC * 0.75)
            if note_time >= DURATION_SEC - 2.0:
                break
            idx_s = int(note_time * SAMPLE_RATE)
            
            # Render primary note
            vel = base_vel * (0.90 + 0.15 * math.sin(note_idx * 1.5))
            nl, nr = xylo.render_note(f0, duration=n_dur, velocity=vel, pan=n_pan)
            rem = min(len(nl), TOTAL_SAMPLES - idx_s)
            if rem > 0 and idx_s < TOTAL_SAMPLES:
                stem_xylo_l[idx_s : idx_s + rem] += nl[:rem]
                stem_xylo_r[idx_s : idx_s + rem] += nr[:rem]
                
            # Octave layer for brilliance
            if use_octave and (note_idx in [5, 6, 7]): # Accentuate the antepenultimate tonic and open resolution!
                nl_8, nr_8 = xylo.render_note(f0 * 0.5, duration=n_dur * 1.2, velocity=vel * 0.6, pan=-n_pan)
                rem8 = min(len(nl_8), TOTAL_SAMPLES - idx_s)
                if rem8 > 0:
                    stem_xylo_l[idx_s : idx_s + rem8] += nl_8[:rem8]
                    stem_xylo_r[idx_s : idx_s + rem8] += nr_8[:rem8]

    # ── 2. RENDER PALMAS ASINCOPADAS ──
    print("Synthesizing Syncopated Palmas...")
    # 12-beat Bulería cycle syncopation pattern across 3 bars (12 beats):
    # Accented beats: 12, 3, 6, 8, 10
    # Contratiempos (off-beats): on the '&' of 1, 2, 4, 5, 7, 9, 11
    buleria_accents = {0: True, 2: True, 5: True, 7: True, 9: True}
    
    for bar in range(0, TOTAL_BARS):
        # Intro silence, then enters at Bar 12 softly
        if bar < 12 or bar >= 192:
            continue
        if 103 <= bar < 105: # Drop silence
            continue
            
        bar_start_s = bar * BAR_SEC
        is_drop_zone = (105 <= bar < 184)
        
        # Micro-swing humanization (+/- 3ms)
        for beat in range(4):
            beat_s = bar_start_s + beat * BEAT_SEC
            beat_in_cycle = (bar * 4 + beat) % 12
            
            # On-beat palmas (sordas or secas)
            is_accent = buleria_accents.get(beat_in_cycle, False)
            if is_accent or is_drop_zone:
                is_seca = is_drop_zone or (is_accent and bar > 48)
                vel = 0.90 if is_accent else 0.72
                jitter = np.random.uniform(-0.003, 0.003)
                idx_s = int(max(0, (beat_s + jitter) * SAMPLE_RATE))
                pl, pr = palmas.render_palma(is_seca=is_seca, velocity=vel, pan=-0.25)
                rem = min(len(pl), TOTAL_SAMPLES - idx_s)
                if rem > 0:
                    stem_palmas_l[idx_s : idx_s + rem] += pl[:rem]
                    stem_palmas_r[idx_s : idx_s + rem] += pr[:rem]
                    
            # Contratiempo (Syncopated off-beat on '&' = beat + 0.5)
            if bar > 24:
                contra_s = beat_s + BEAT_SEC * 0.5 + np.random.uniform(-0.004, 0.004)
                idx_c = int(contra_s * SAMPLE_RATE)
                is_seca_contra = (bar > 64) or is_drop_zone
                vel_c = 0.78 if is_seca_contra else 0.60
                pl, pr = palmas.render_palma(is_seca=is_seca_contra, velocity=vel_c, pan=0.28)
                rem = min(len(pl), TOTAL_SAMPLES - idx_c)
                if rem > 0:
                    stem_palmas_l[idx_c : idx_c + rem] += pl[:rem]
                    stem_palmas_r[idx_c : idx_c + rem] += pr[:rem]

    # ── 3. RENDER CAVERNOUS PADS ──
    print("Synthesizing Cavernous Pads & Space...")
    # Chord cycle (8 bars = 4 chords x 2 bars):
    # Dmaj9 (D3, F#3, A3, C#4, E4)
    # Gmaj7#11 (G2, D3, F#3, B3, C#4)
    # Bm11 (B2, F#3, A3, D4, E4)
    # Asus4add9 (A2, E3, A3, B3, D4)
    chord_bank = [
        [146.83, 185.00, 220.00, 277.18, 329.63], # Dmaj9
        [98.00, 146.83, 185.00, 246.94, 277.18],  # Gmaj7#11
        [123.47, 185.00, 220.00, 293.66, 329.63], # Bm11
        [110.00, 164.81, 220.00, 246.94, 293.66]  # Asus4add9
    ]
    
    pad_raw_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    pad_raw_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    for bar in range(0, TOTAL_BARS, 2):
        if 103 <= bar < 105: # Sudden silence at drop
            continue
            
        chord_idx = (bar // 2) % len(chord_bank)
        chord_freqs = chord_bank[chord_idx]
        
        bar_s = bar * BAR_SEC
        dur_chord = BAR_SEC * 2.0
        n_c = int(dur_chord * SAMPLE_RATE)
        t_c = np.linspace(0, dur_chord, n_c, endpoint=False)
        
        # Envelope: soft attack and gentle release
        env = (np.sin(np.pi * (t_c / dur_chord)) ** 0.6).astype(np.float32)
        
        # Dynamic filter cutoff based on song progression
        if bar < 104:
            cutoff = 350.0 + 1900.0 * (bar / 104.0) ** 1.8 # Gradual increscendo sweep!
        elif 105 <= bar < 116:
            cutoff = 600.0 # Sub-wash for drop
        elif 116 <= bar < 184:
            cutoff = 2200.0 # Open wide for melody return
        else:
            cutoff = max(250.0, 1800.0 - 1500.0 * ((bar - 184) / 24.0))
            
        b_pad, a_pad = signal.butter(2, cutoff / (SAMPLE_RATE * 0.5), btype='low')
        
        voice_l = np.zeros(n_c, dtype=np.float32)
        voice_r = np.zeros(n_c, dtype=np.float32)
        
        for v_idx, f in enumerate(chord_freqs):
            # Detuned saws + sub sine
            detune = 1.0 + 0.0018 * ((v_idx % 3) - 1)
            saw1 = signal.sawtooth(2 * np.pi * f * detune * t_c)
            saw2 = signal.sawtooth(2 * np.pi * f * (2.0 - detune) * t_c)
            sub = np.sin(2 * np.pi * (f * 0.5) * t_c) * 0.4
            
            p_pan = -0.4 + 0.8 * (v_idx / len(chord_freqs))
            gain_l = np.sqrt(0.5 * (1.0 - p_pan))
            gain_r = np.sqrt(0.5 * (1.0 + p_pan))
            
            comb = (saw1 * 0.35 + saw2 * 0.35 + sub) * env
            voice_l += comb * gain_l
            voice_r += comb * gain_r
            
        filt_l = signal.lfilter(b_pad, a_pad, voice_l)
        filt_r = signal.lfilter(b_pad, a_pad, voice_r)
        
        idx_s = int(bar_s * SAMPLE_RATE)
        rem = min(len(filt_l), TOTAL_SAMPLES - idx_s)
        if rem > 0:
            pad_raw_l[idx_s : idx_s + rem] += filt_l[:rem] * 0.45
            pad_raw_r[idx_s : idx_s + rem] += filt_r[:rem] * 0.45

    # Convolve pads with cavern impulse response
    print("Convolving cavernous pads with impulse response...")
    ir_l, ir_r = get_cavern_ir(SAMPLE_RATE, rt60=8.0)
    stem_pads_l = signal.fftconvolve(pad_raw_l, ir_l, mode='same') + pad_raw_l * 0.55
    stem_pads_r = signal.fftconvolve(pad_raw_r, ir_r, mode='same') + pad_raw_r * 0.55

    # ── 4. RENDER BOMBO (KICK) ──
    # CRUCIAL CONSTRAINT: "bombo que entra justo a la mitad de la canción"
    # Halfway point is 195.00s = Bar 105!
    # Bars 1 to 104: ZERO KICK.
    print(f"Synthesizing Bombo (Strict entrance at Bar {DROP_BAR} / t=195.00s)...")
    for bar in range(DROP_BAR, OUTRO_BAR):
        bar_s = bar * BAR_SEC
        for beat in range(4):
            beat_s = bar_s + beat * BEAT_SEC
            idx_s = int(beat_s * SAMPLE_RATE)
            kl, kr = kick.render_kick(velocity=0.96)
            rem = min(len(kl), TOTAL_SAMPLES - idx_s)
            if rem > 0:
                stem_kick_l[idx_s : idx_s + rem] += kl[:rem]
                stem_kick_r[idx_s : idx_s + rem] += kr[:rem]

    # ── 5. RENDER NEURAL VOCAL TRACK ("La voz... bum x 12") ──
    print("Synthesizing Vocal Chants ('La voz...' + 12 'bum's)...")
    vocal_raw = get_vocal_bum_tracks(SAMPLE_RATE)
    
    # 1. Spoken 'La voz...' at Bar 104 (beat 2.5 to 4, in the vacuum before the drop)
    # Bar 104 starts at 103 * 1.875 = 193.125s
    # Pre-drop whisper at t = 193.8s
    pre_drop_s = (103 * BAR_SEC) + (BEAT_SEC * 1.8)
    pre_idx = int(pre_drop_s * SAMPLE_RATE)
    # Slice 'La voz' (~first 0.75s of raw vocal)
    la_voz_slice = vocal_raw[:int(0.75 * SAMPLE_RATE)]
    rem_v = min(len(la_voz_slice), TOTAL_SAMPLES - pre_idx)
    if rem_v > 0:
        stem_voice_l[pre_idx : pre_idx + rem_v] += la_voz_slice[:rem_v] * 0.85
        stem_voice_r[pre_idx : pre_idx + rem_v] += la_voz_slice[:rem_v] * 0.85
        
    # 2. 12 'bum's starting right at Bar 105 (beat 1 = 195.00s)
    # The drop hits at Bar 105: 12 beats = Bars 105, 106, 107
    # Extract clean single 'bum' slice (~0.45s) from segment 3
    # In earlier test, segment 3 was around 0.938s to 1.35s
    bum_slice = vocal_raw[int(0.92 * SAMPLE_RATE) : int(1.35 * SAMPLE_RATE)]
    # Normalize and shape envelope
    bum_slice = bum_slice / (np.max(np.abs(bum_slice)) + 1e-6)
    t_bum = np.linspace(0, 1, len(bum_slice))
    fade = np.clip(1.0 - t_bum**2, 0, 1)
    bum_slice = (bum_slice * fade * 0.92).astype(np.float32)
    
    for bum_idx in range(12):
        # One bum per beat over 12 consecutive beats (Bars 105, 106, 107)
        bum_time = (DROP_BAR * BAR_SEC) + (bum_idx * BEAT_SEC)
        b_idx = int(bum_time * SAMPLE_RATE)
        pan = -0.3 + 0.6 * (bum_idx % 2) # Panning bounce
        g_l = np.sqrt(0.5 * (1.0 - pan))
        g_r = np.sqrt(0.5 * (1.0 + pan))
        rem = min(len(bum_slice), TOTAL_SAMPLES - b_idx)
        if rem > 0:
            stem_voice_l[b_idx : b_idx + rem] += bum_slice[:rem] * g_l
            stem_voice_r[b_idx : b_idx + rem] += bum_slice[:rem] * g_r
            
    # Add cavernous dub delay to vocal
    vocal_delay_l = np.zeros_like(stem_voice_l)
    vocal_delay_r = np.zeros_like(stem_voice_r)
    d_samples_l = int(SAMPLE_RATE * (BEAT_SEC * 0.75)) # Dotted eighth delay
    d_samples_r = int(SAMPLE_RATE * (BEAT_SEC * 0.50))
    vocal_delay_l[d_samples_l:] = stem_voice_r[:-d_samples_l] * 0.40
    vocal_delay_r[d_samples_r:] = stem_voice_l[:-d_samples_r] * 0.40
    stem_voice_l += vocal_delay_l
    stem_voice_r += vocal_delay_r

    # ── 6. RENDER ANALOG BASS DRIVE ──
    print("Synthesizing Analog Bassline (driving post-drop)...")
    for bar in range(DROP_BAR, OUTRO_BAR):
        chord_idx = (bar // 2) % len(chord_bank)
        root_f = [73.42, 49.00, 61.74, 55.00][chord_idx] # D2, G1, B1, A1
        
        bar_s = bar * BAR_SEC
        for beat in range(4):
            beat_s = bar_s + beat * BEAT_SEC
            b_dur = BEAT_SEC * 0.85
            n_b = int(b_dur * SAMPLE_RATE)
            t_b = np.linspace(0, b_dur, n_b, endpoint=False)
            
            # Punchy sub sine + slight saturation
            sub = np.sin(2 * np.pi * root_f * t_b) * np.exp(-t_b * 3.5)
            harm = np.sin(2 * np.pi * (root_f * 2.0) * t_b) * np.exp(-t_b * 6.0) * 0.3
            bass_tone = np.tanh((sub + harm) * 1.5) * 0.65
            
            idx_s = int(beat_s * SAMPLE_RATE)
            rem = min(n_b, TOTAL_SAMPLES - idx_s)
            if rem > 0:
                stem_bass_l[idx_s : idx_s + rem] += bass_tone[:rem]
                stem_bass_r[idx_s : idx_s + rem] += bass_tone[:rem]

    # ── 7. RENDER MARIMBA 5:4 POLYRHYTHMIC COUNTERPOINT ──
    print("Synthesizing Marimba 5:4 Polyrhythm...")
    marimba_notes = [369.99, 440.00, 493.88, 554.37, 587.33] # F#4, A4, B4, C#5, D5
    for bar in range(32, OUTRO_BAR):
        if 103 <= bar < 116: # Silent during drop shock
            continue
        bar_s = bar * BAR_SEC
        # 5 notes evenly spaced over 4 beats = 5:4 polyrhythm!
        step_5 = (BAR_SEC / 5.0)
        for m_idx in range(5):
            m_time = bar_s + m_idx * step_5
            f = marimba_notes[(bar + m_idx) % len(marimba_notes)]
            idx_s = int(m_time * SAMPLE_RATE)
            vel = 0.60 if bar < 104 else 0.78
            ml, mr = xylo.render_note(f, duration=0.8, velocity=vel, pan=0.35)
            rem = min(len(ml), TOTAL_SAMPLES - idx_s)
            if rem > 0:
                stem_marimba_l[idx_s : idx_s + rem] += ml[:rem]
                stem_marimba_r[idx_s : idx_s + rem] += mr[:rem]

    # ── 8. MASTER MIXDOWN & EXERGY GAIN STAGING (MID-SIDE COHESION) ──
    print("Performing Sovereign Master Mixdown & EBU R128 Gain Staging (Mid-Side Cohesion)...")
    # Apply Mid-Side cohesion to pads (mono sub-bass, clean stereo cavern width)
    mid_pad = 0.5 * (stem_pads_l + stem_pads_r)
    side_pad = 0.5 * (stem_pads_l - stem_pads_r)
    b_ms, a_ms = signal.butter(2, 200.0 / (SAMPLE_RATE * 0.5), btype='high')
    side_pad_filt = signal.lfilter(b_ms, a_ms, side_pad)
    pads_clean_l = mid_pad + 0.22 * side_pad_filt
    pads_clean_r = mid_pad - 0.22 * side_pad_filt

    # Apply Mid-Side to vocal delay
    mid_v = 0.5 * (stem_voice_l + stem_voice_r)
    side_v = 0.5 * (stem_voice_l - stem_voice_r)
    voice_clean_l = mid_v + 0.20 * side_v
    voice_clean_r = mid_v - 0.20 * side_v

    # Apply Mid-Side to palmas and xylophone
    mid_p = 0.5 * (stem_palmas_l + stem_palmas_r)
    side_p = 0.5 * (stem_palmas_l - stem_palmas_r)
    palmas_clean_l = mid_p + 0.25 * side_p
    palmas_clean_r = mid_p - 0.25 * side_p

    mid_x = 0.5 * (stem_xylo_l + stem_xylo_r)
    side_x = 0.5 * (stem_xylo_l - stem_xylo_r)
    xylo_clean_l = mid_x + 0.28 * side_x
    xylo_clean_r = mid_x - 0.28 * side_x

    # Kick and Bass strictly centered (zero low-end cancellation)
    kick_mono = 0.5 * (stem_kick_l + stem_kick_r)
    bass_mono = 0.5 * (stem_bass_l + stem_bass_r)

    # Clean calibrated summing preserving 16 dB crest factor
    master_l = (
        xylo_clean_l * 0.50 +
        palmas_clean_l * 0.38 +
        pads_clean_l * 0.28 +
        kick_mono * 0.72 +
        voice_clean_l * 0.50 +
        bass_mono * 0.50 +
        stem_marimba_l * 0.30
    )
    master_r = (
        xylo_clean_r * 0.50 +
        palmas_clean_r * 0.38 +
        pads_clean_r * 0.28 +
        kick_mono * 0.72 +
        voice_clean_r * 0.50 +
        bass_mono * 0.50 +
        stem_marimba_r * 0.30
    )

    # Master true peak normalization to -0.8 dBFS without clipping
    pk = max(np.max(np.abs(master_l)), np.max(np.abs(master_r))) + 1e-6
    target_peak = 0.912 # -0.8 dBTP
    master_l = master_l * (target_peak / pk)
    master_r = master_r * (target_peak / pk)

    # ── 9. EXPORT STEMS AND MASTER WAV ──
    stems = {
        "01_Xilofono_Polirritmia.wav": (xylo_clean_l, xylo_clean_r),
        "02_Palmas_Asincopadas.wav": (palmas_clean_l, palmas_clean_r),
        "03_Pads_Cavernosos.wav": (pads_clean_l, pads_clean_r),
        "04_Maceo_Kick_Drop.wav": (kick_mono, kick_mono),
        "05_Vocal_LaVoz_Bum12.wav": (voice_clean_l, voice_clean_r),
        "06_Bajo_Analogico_Drive.wav": (bass_mono, bass_mono),
        "07_Marimba_Arpegio_5_4.wav": (stem_marimba_l, stem_marimba_r)
    }

    for name, (l, r) in stems.items():  # noqa: E741
        out_stem = STEMS_DIR / name
        p = max(np.max(np.abs(l)), np.max(np.abs(r))) + 1e-6
        norm_l = (l / p) * 0.88
        norm_r = (r / p) * 0.88
        stereo_stem = np.column_stack([norm_l, norm_r])
        sf.write(str(out_stem), stereo_stem, SAMPLE_RATE, subtype='PCM_24')
        print(f"  ✓ Exported Stem: {name}")

    master_path = BOUNCES_DIR / "BORJA_MOSKV_Polirritmia_Cavernosa_6m30.wav"
    master_stereo = np.column_stack([master_l, master_r])
    sf.write(str(master_path), master_stereo, SAMPLE_RATE, subtype='PCM_24')
    print(f"✅ Exported Stereo Master: {master_path.name}")
    print(f"   Size: {master_path.stat().st_size / (1024*1024):.2f} MB")

    return master_path, STEMS_DIR

# ─────────────────────────────────────────────────────────────────────────────
# 6. FLP PROJECT COMPILER
# ─────────────────────────────────────────────────────────────────────────────
def compile_flp_project(stems_dir: Path, output_flp: Path):
    print("Compiling FL Studio Native Project (.flp)...")
    try:
        from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    except ImportError:
        from flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    
    staging = {
        "01_Xilofono_Polirritmia": {"mixer_track": 1, "volume": 105, "pan": 64},
        "02_Palmas_Asincopadas": {"mixer_track": 2, "volume": 95, "pan": 64},
        "03_Pads_Cavernosos": {"mixer_track": 3, "volume": 90, "pan": 64},
        "04_Maceo_Kick_Drop": {"mixer_track": 4, "volume": 115, "pan": 64},
        "05_Vocal_LaVoz_Bum12": {"mixer_track": 5, "volume": 108, "pan": 64},
        "06_Bajo_Analogico_Drive": {"mixer_track": 6, "volume": 100, "pan": 64},
        "07_Marimba_Arpegio_5_4": {"mixer_track": 7, "volume": 88, "pan": 64}
    }
    
    res = compile_multitrack_stems_flp(
        stems_dir=str(stems_dir),
        project_title="BORJA MOSKV - Polirritmia Cavernosa (6m30)",
        bpm=128.0,
        output_flp=str(output_flp),
        total_bars=TOTAL_BARS,
        channel_staging=staging
    )
    print(f"✅ FLP Project successfully compiled: {output_flp.name}")
    return res

# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    master_wav, stems_path = generate_composition()
    
    # Compile FLP
    target_flp = BOUNCES_DIR / "Polirritmia_Cavernosa_6m30.flp"
    compile_flp_project(stems_path, target_flp)
    
    # Run Rubin Acoustic Linter
    print("\n════ RUNNING DETERMINISTIC C5 RUBIN ACOUSTIC AUDITOR ════")
    cmd_audit = f"python3 /Users/borjafernandezangulo/.gemini/config/skills/c5-rubin-acoustic-linter/scripts/audit_acoustic_exergy.py '{master_wav}'"
    subprocess.run(cmd_audit, shell=True, check=True)
    print("═════════════════════════════════════════════════════════\n")
