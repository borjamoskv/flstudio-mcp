#!/usr/bin/env python3
"""
Polirritmia Cavernosa (Club House Avant-Garde Edition 6:30)
Composed for Borja Moskv under C5-REAL Physical Acoustics & Invariants.

Synthesizes a high-energy dancefloor House version without losing the avant-garde essence:
1. Total duration: 390.00s (6m 30s) exact (208 bars @ 128 BPM).
2. Xylophone: Rosewood bar physical modal synthesis (modes 1 : 3.0 : 9.2).
   - Core motif: Tonic (D6) is strictly the ANTEPENULTIMATE note!
     F#5 -> A5 -> B5 -> C#6 -> E6 -> [D6 (TÓNICA / ANTEPENÚLTIMA)] -> E6 -> F#6.
     Generates perpetual opening, rising euphoria, and forward momentum.
3. House Groove & Dancefloor Propulsion ("más house, más para pista"):
   - 909-style punch kick (enters strictly at t=195.00s / Bar 105).
   - Offbeat open 909 hi-hats on every '&' of the beat.
   - Swinging 16th-note shakers and closed hats with 56% MPC shuffle.
   - Bouncing, syncopated Chicago / Deep House bassline (Kerri Chandler / Bicep style).
   - Rhythmic sidechain ducking on pads and bass.
4. Avant-Garde Preservation ("sin perder avant-garde"):
   - 3:4 cross-metric polyrhythm of the xylophone against the 4/4 house grid.
   - 5:4 marimba counterpoint.
   - Palmas asincopadas flamencas (sordas 320Hz and secas 2800Hz with 8ms micro-flam).
   - Subterranean cavernous pads convolved with 8.0s RT60 impulse response.
   - Pre-drop whisper "La voz..." in the vacuum.
   - Drop at t=195.00s with 12 vocal hits ("bum x 12").
   - At Compás 12 del drop (Bar 116), the full avant-garde melody detonates back in!
5. Deterministic C5 Rubin Acoustic Linter verification (Crest Factor >= 12 dB, Coherence >= 0.95).
"""

import sys
import math
import numpy as np
import scipy.signal as signal
from pathlib import Path
import soundfile as sf
import subprocess

sys.path.insert(0, '/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp')
sys.path.insert(0, '/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/scripts')

SAMPLE_RATE = 44100
BPM = 128.0
BEAT_SEC = 60.0 / BPM          # 0.46875 s
BAR_SEC = BEAT_SEC * 4.0       # 1.875 s
SIXTEENTH_SEC = BEAT_SEC / 4.0 # 0.1171875 s
TOTAL_BARS = 208
DURATION_SEC = TOTAL_BARS * BAR_SEC  # 390.000 s exact (6m 30s)
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION_SEC)

DROP_BAR = 105                 # Bar 105 starts at (104 * 1.875) = 195.000 s exact
MELODY_RETURN_BAR = 116        # Compás 12 del drop (104 + 12 = 116)
OUTRO_BAR = 193                # Outro starts, kick stops, decay to 208

BOUNCES_DIR = Path("/Users/borjafernandezangulo/Music/LIBRARY/04-Stems/FL_Studio/Bounces")
STEMS_DIR = BOUNCES_DIR / "POLIRRITMIA_CAVERNOSA_CLUB_HOUSE_STEMS"
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
        
        imp_len = min(n, int(0.0022 * self.sr))
        t_imp = np.linspace(0, np.pi, imp_len)
        mallet = np.zeros(n, dtype=np.float32)
        mallet[:imp_len] = (np.sin(t_imp) ** 2).astype(np.float32)
        
        noise = (np.random.normal(0, 0.05, imp_len) * (np.sin(t_imp) ** 2)).astype(np.float32)
        click = signal.lfilter(self.b_click, self.a_click, noise)
        mallet[:imp_len] += click * 0.35
        
        # Modal decays (undercut rosewood bar modes: 1 : 3.0 : 9.2)
        d0 = np.exp(-t * (4.2 + 0.0025 * f0), dtype=np.float32)
        d1 = np.exp(-t * (14.0 + 0.0080 * f0), dtype=np.float32)
        d2 = np.exp(-t * (36.0 + 0.0200 * f0), dtype=np.float32)
        
        m0 = np.sin(2 * np.pi * f0 * t, dtype=np.float32) * d0
        m1 = np.sin(2 * np.pi * (f0 * 3.00) * t, dtype=np.float32) * d1 * 0.38
        m2 = np.sin(2 * np.pi * (f0 * 9.20) * t, dtype=np.float32) * d2 * 0.14
        
        body = (m0 + m1 + m2 + mallet * 0.22) * velocity
        
        # Subtle Mid-Side stereo spread
        pan_clamped = np.clip(pan, -0.35, 0.35)
        gain_l = 1.0 - 0.25 * pan_clamped
        gain_r = 1.0 + 0.25 * pan_clamped
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
        
        pan_clamped = np.clip(pan, -0.35, 0.35)
        gain_l = 1.0 - 0.25 * pan_clamped
        gain_r = 1.0 + 0.25 * pan_clamped
        return out * gain_l, out * gain_r

# ─────────────────────────────────────────────────────────────────────────────
# 3. 909 HOUSE KICK & DRUM SYNTHESIZER
# ─────────────────────────────────────────────────────────────────────────────
class HouseDrumSynthesizer:
    def __init__(self, sr=SAMPLE_RATE):
        self.sr = sr
        # 1. 909 Punch Kick
        dur_k = 0.36
        n_k = int(dur_k * sr)
        t_k = np.linspace(0, dur_k, n_k, endpoint=False)
        f_k_start, f_k_end, k_sweep = 160.0, 48.0, 34.0
        phase_k = 2.0 * np.pi * (f_k_end * t_k + ((f_k_start - f_k_end) / k_sweep) * (1.0 - np.exp(-k_sweep * t_k)))
        env_k = np.exp(-t_k * 10.5)
        click_k = 0.45 * np.sin(2.0 * np.pi * 1850.0 * t_k) * np.exp(-t_k * 150.0)
        self.kick_sample = (np.tanh(1.8 * (np.sin(phase_k) + click_k)) * env_k * 0.88).astype(np.float32)
        
        # 2. 909 Offbeat Open Hi-Hat
        dur_oh = 0.22
        n_oh = int(dur_oh * sr)
        t_oh = np.linspace(0, dur_oh, n_oh, endpoint=False)
        noise_oh = np.random.randn(n_oh).astype(np.float32)
        metallic = 0.35 * (np.sin(2*np.pi*7100*t_oh) + np.sin(2*np.pi*9200*t_oh) + np.sin(2*np.pi*5800*t_oh))
        b_oh, a_oh = signal.butter(2, [4500/(sr*0.5), 14000/(sr*0.5)], btype='band')
        hat_filt = signal.lfilter(b_oh, a_oh, noise_oh * 0.70 + metallic * 0.30)
        self.open_hat_sample = (hat_filt * np.exp(-t_oh * 16.5) * 0.55).astype(np.float32)
        
        # 3. 16th-Note Shaker & Closed Hat (MPC Swing)
        dur_sh = 0.08
        n_sh = int(dur_sh * sr)
        t_sh = np.linspace(0, dur_sh, n_sh, endpoint=False)
        noise_sh = np.random.randn(n_sh).astype(np.float32)
        b_sh, a_sh = signal.butter(2, 6000/(sr*0.5), btype='high')
        shaker_filt = signal.lfilter(b_sh, a_sh, noise_sh)
        self.shaker_sample = (shaker_filt * np.exp(-t_sh * 45.0) * 0.35).astype(np.float32)
        
        # 4. House Rimshot / Wood Snare
        dur_rim = 0.12
        n_rim = int(dur_rim * sr)
        t_rim = np.linspace(0, dur_rim, n_rim, endpoint=False)
        tone_rim = np.sin(2 * np.pi * 920.0 * t_rim) * np.exp(-t_rim * 60.0)
        snap_rim = np.random.randn(n_rim).astype(np.float32) * np.exp(-t_rim * 90.0)
        self.rim_sample = (tone_rim * 0.6 + snap_rim * 0.4).astype(np.float32) * 0.45

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
# 5. NEURAL VOCAL TRACK PROVIDER
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
# 6. COMPOSITION TIMELINE GENERATOR (CLUB HOUSE EDITION)
# ─────────────────────────────────────────────────────────────────────────────
def generate_composition():
    print("═══ GENERATING POLIRRITMIA CAVERNOSA (CLUB HOUSE AVANT-GARDE EDITION 6:30) ═══")
    print(f"Total Duration: {DURATION_SEC:.2f}s ({TOTAL_SAMPLES} samples)")
    print(f"Halfway Point: 195.00s (Bar {DROP_BAR})")
    print(f"Melody Return Point: Bar {MELODY_RETURN_BAR} (Compás 12 del drop)")
    
    stem_xylo_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_xylo_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_palmas_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_palmas_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_pads_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_pads_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_kick_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_kick_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_hats_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_hats_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_voice_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_voice_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_bass_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_bass_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    stem_marimba_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    stem_marimba_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

    xylo = RosewoodXylophone(SAMPLE_RATE)
    palmas = FlamencoPalmasEngine(SAMPLE_RATE)
    drums = HouseDrumSynthesizer(SAMPLE_RATE)

    # ── 1. XYLOPHONE MOTIF (ANTEPENULTIMATE TONIC IN D LYDIAN) ──
    # Primary rule: Tónica (D6) is strictly the ANTEPENÚLTIMA note!
    # F#5 -> A5 -> B5 -> C#6 -> E6 -> [D6 (TÓNICA)] -> E6 -> F#6!
    phrase_1 = [
        (739.99, 0.40, -0.2),  # F#5
        (880.00, 0.40, -0.1),  # A5
        (987.77, 0.40, 0.1),   # B5
        (1108.73, 0.40, 0.2),  # C#6
        (1318.51, 0.45, 0.3),  # E6
        (1174.66, 0.45, 0.0),  # D6 -> TÓNICA (ANTEPENÚLTIMA!)
        (1318.51, 0.40, 0.2),  # E6 -> PENÚLTIMA
        (1479.98, 0.50, 0.3)   # F#6 -> ÚLTIMA (Apertura infinita hacia arriba)
    ]
    phrase_2 = [
        (880.00, 0.40, -0.1),  # A5
        (987.77, 0.40, 0.0),   # B5
        (1108.73, 0.40, 0.1),  # C#6
        (1174.66, 0.40, 0.1),  # D6
        (1661.22, 0.45, 0.3),  # G#6 (Lydian #4)
        (1174.66, 0.45, 0.0),  # D6 -> TÓNICA (ANTEPENÚLTIMA!)
        (1479.98, 0.40, 0.2),  # F#6 -> PENÚLTIMA
        (1760.00, 0.55, 0.3)   # A6 -> ÚLTIMA (Cielo abierto)
    ]

    print("Synthesizing Avant-Garde Xylophone tracks...")
    for bar in range(0, TOTAL_BARS):
        if 103 <= bar < 115: # Pre-drop vacuum & drop shock silence
            continue
            
        bar_start_s = bar * BAR_SEC
        if bar < 12:
            base_vel = 0.65 + 0.15 * (bar / 12.0)
            use_octave = False
        elif bar < 64:
            base_vel = 0.75 + 0.10 * ((bar - 12) / 52.0)
            use_octave = (bar % 4 == 0)
        elif bar < 103:
            base_vel = 0.82 + 0.16 * ((bar - 64) / 39.0)
            use_octave = True
        elif 115 <= bar < 184:
            # COMPÁS 12 DEL DROP (Bar 116) - RETORNO MELÓDICO TRIUNFAL!
            base_vel = 0.95
            use_octave = True
        else:
            base_vel = max(0.2, 0.85 - 0.65 * ((bar - 184) / 24.0))
            use_octave = False
            
        curr_phrase = phrase_1 if (bar // 2) % 2 == 0 else phrase_2
        
        for note_idx, (f0, n_dur, n_pan) in enumerate(curr_phrase):
            note_time = bar_start_s + note_idx * (BEAT_SEC * 0.75) # 3:4 cross-meter
            if note_time >= DURATION_SEC - 2.0:
                break
            idx_s = int(note_time * SAMPLE_RATE)
            vel = base_vel * (0.90 + 0.15 * math.sin(note_idx * 1.5))
            nl, nr = xylo.render_note(f0, duration=n_dur, velocity=vel, pan=n_pan)
            rem = min(len(nl), TOTAL_SAMPLES - idx_s)
            if rem > 0 and idx_s < TOTAL_SAMPLES:
                stem_xylo_l[idx_s : idx_s + rem] += nl[:rem]
                stem_xylo_r[idx_s : idx_s + rem] += nr[:rem]
                
            if use_octave and (note_idx in [5, 6, 7]):
                nl_8, nr_8 = xylo.render_note(f0 * 0.5, duration=n_dur * 1.2, velocity=vel * 0.6, pan=-n_pan)
                rem8 = min(len(nl_8), TOTAL_SAMPLES - idx_s)
                if rem8 > 0:
                    stem_xylo_l[idx_s : idx_s + rem8] += nl_8[:rem8]
                    stem_xylo_r[idx_s : idx_s + rem8] += nr_8[:rem8]

    # ── 2. FLAMENCO PALMAS ASINCOPADAS ──
    print("Synthesizing Syncopated Palmas...")
    buleria_accents = {0: True, 2: True, 5: True, 7: True, 9: True}
    for bar in range(0, TOTAL_BARS):
        if bar < 12 or bar >= 192:
            continue
        if 103 <= bar < 105:
            continue
            
        bar_start_s = bar * BAR_SEC
        is_drop_zone = (105 <= bar < 184)
        
        for beat in range(4):
            beat_s = bar_start_s + beat * BEAT_SEC
            beat_in_cycle = (bar * 4 + beat) % 12
            is_accent = buleria_accents.get(beat_in_cycle, False)
            if is_accent or is_drop_zone:
                is_seca = is_drop_zone or (is_accent and bar > 48)
                vel = 0.90 if is_accent else 0.72
                jitter = np.random.uniform(-0.003, 0.003)
                idx_s = int(max(0, (beat_s + jitter) * SAMPLE_RATE))
                pl, pr = palmas.render_palma(is_seca=is_seca, velocity=vel, pan=-0.20)
                rem = min(len(pl), TOTAL_SAMPLES - idx_s)
                if rem > 0:
                    stem_palmas_l[idx_s : idx_s + rem] += pl[:rem]
                    stem_palmas_r[idx_s : idx_s + rem] += pr[:rem]
                    
            if bar > 24:
                contra_s = beat_s + BEAT_SEC * 0.5 + np.random.uniform(-0.003, 0.003)
                idx_c = int(contra_s * SAMPLE_RATE)
                is_seca_contra = (bar > 64) or is_drop_zone
                vel_c = 0.78 if is_seca_contra else 0.60
                pl, pr = palmas.render_palma(is_seca=is_seca_contra, velocity=vel_c, pan=0.20)
                rem = min(len(pl), TOTAL_SAMPLES - idx_c)
                if rem > 0:
                    stem_palmas_l[idx_c : idx_c + rem] += pl[:rem]
                    stem_palmas_r[idx_c : idx_c + rem] += pr[:rem]

    # ── 3. HOUSE DRUM SECTION (OPEN HATS, SHAKERS, MPC SWING) ──
    print("Synthesizing House Hats, Shakers & MPC Groove...")
    swing_delay = 0.012 # 56% MPC swing offset for second 16ths
    for bar in range(0, TOTAL_BARS):
        bar_s = bar * BAR_SEC
        
        # Pre-drop anticipation (shakers enter at bar 32, building dancefloor sway)
        if 32 <= bar < 103 or (105 <= bar < 188):
            sh_vol = 0.45 if bar < 64 else (0.65 if bar < 103 else 0.85)
            for s16 in range(16):
                is_swing = (s16 % 2 == 1)
                t_sh = bar_s + s16 * SIXTEENTH_SEC + (swing_delay if is_swing else 0.0)
                idx_sh = int(t_sh * SAMPLE_RATE)
                rem = min(len(drums.shaker_sample), TOTAL_SAMPLES - idx_sh)
                if rem > 0:
                    stem_hats_l[idx_sh : idx_sh + rem] += drums.shaker_sample[:rem] * sh_vol
                    stem_hats_r[idx_sh : idx_sh + rem] += drums.shaker_sample[:rem] * sh_vol
                    
        # House Rimshots on 2 & 4 (entering at bar 64 to anchor the 4/4 groove before the drop)
        if (64 <= bar < 103) or (105 <= bar < 184):
            for beat in [1, 3]:
                t_rim = bar_s + beat * BEAT_SEC
                idx_rim = int(t_rim * SAMPLE_RATE)
                rem = min(len(drums.rim_sample), TOTAL_SAMPLES - idx_rim)
                if rem > 0:
                    stem_hats_l[idx_rim : idx_rim + rem] += drums.rim_sample[:rem] * 0.70
                    stem_hats_r[idx_rim : idx_rim + rem] += drums.rim_sample[:rem] * 0.70

        # Offbeat 909 Open Hats (THE DANCEFLOOR ENGINE): Starts strictly at Bar 105 (Drop!)
        if 105 <= bar < 188:
            for beat in range(4):
                t_oh = bar_s + (beat + 0.5) * BEAT_SEC # Offbeat '&'
                idx_oh = int(t_oh * SAMPLE_RATE)
                rem = min(len(drums.open_hat_sample), TOTAL_SAMPLES - idx_oh)
                if rem > 0:
                    stem_hats_l[idx_oh : idx_oh + rem] += drums.open_hat_sample[:rem] * 0.82
                    stem_hats_r[idx_oh : idx_oh + rem] += drums.open_hat_sample[:rem] * 0.82

    # ── 4. CAVERNOUS PADS WITH PUMPING SIDECHAIN ──
    print("Synthesizing Cavernous Pads with Sidechain Pump...")
    chord_bank = [
        [146.83, 185.00, 220.00, 277.18, 329.63], # Dmaj9
        [98.00, 146.83, 185.00, 246.94, 277.18],  # Gmaj7#11
        [123.47, 185.00, 220.00, 293.66, 329.63], # Bm11
        [110.00, 164.81, 220.00, 246.94, 293.66]  # Asus4add9
    ]
    pad_raw_l = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    pad_raw_r = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    for bar in range(0, TOTAL_BARS, 2):
        if 103 <= bar < 105:
            continue
        chord_idx = (bar // 2) % len(chord_bank)
        chord_freqs = chord_bank[chord_idx]
        bar_s = bar * BAR_SEC
        dur_chord = BAR_SEC * 2.0
        n_c = int(dur_chord * SAMPLE_RATE)
        t_c = np.linspace(0, dur_chord, n_c, endpoint=False)
        env = (np.sin(np.pi * (t_c / dur_chord)) ** 0.6).astype(np.float32)
        
        if bar < 104:
            cutoff = 350.0 + 1900.0 * (bar / 104.0) ** 1.8
        elif 105 <= bar < 116:
            cutoff = 750.0
        elif 116 <= bar < 184:
            cutoff = 2200.0
        else:
            cutoff = max(250.0, 1800.0 - 1500.0 * ((bar - 184) / 24.0))
            
        b_pad, a_pad = signal.butter(2, cutoff / (SAMPLE_RATE * 0.5), btype='low')
        voice_l = np.zeros(n_c, dtype=np.float32)
        voice_r = np.zeros(n_c, dtype=np.float32)
        
        for v_idx, f in enumerate(chord_freqs):
            detune = 1.0 + 0.0016 * ((v_idx % 3) - 1)
            saw1 = signal.sawtooth(2 * np.pi * f * detune * t_c)
            saw2 = signal.sawtooth(2 * np.pi * f * (2.0 - detune) * t_c)
            sub = np.sin(2 * np.pi * (f * 0.5) * t_c) * 0.4
            
            p_pan = -0.3 + 0.6 * (v_idx / len(chord_freqs))
            gain_l = 1.0 - 0.25 * p_pan
            gain_r = 1.0 + 0.25 * p_pan
            comb = (saw1 * 0.35 + saw2 * 0.35 + sub) * env
            voice_l += comb * gain_l
            voice_r += comb * gain_r
            
        filt_l = signal.lfilter(b_pad, a_pad, voice_l)
        filt_r = signal.lfilter(b_pad, a_pad, voice_r)
        
        # Pumping Sidechain ducking post-drop (Bars 105 - 188)
        if 105 <= bar < 188:
            for s_i in range(n_c):
                sample_in_beat = (int(bar_s * SAMPLE_RATE) + s_i) % int(BEAT_SEC * SAMPLE_RATE)
                t_beat = sample_in_beat / SAMPLE_RATE
                if t_beat < 0.28:
                    duck = 1.0 - 0.70 * np.exp(-t_beat * 24.0)
                    filt_l[s_i] *= duck
                    filt_r[s_i] *= duck
                    
        idx_s = int(bar_s * SAMPLE_RATE)
        rem = min(len(filt_l), TOTAL_SAMPLES - idx_s)
        if rem > 0:
            pad_raw_l[idx_s : idx_s + rem] += filt_l[:rem] * 0.45
            pad_raw_r[idx_s : idx_s + rem] += filt_r[:rem] * 0.45

    ir_l, ir_r = get_cavern_ir(SAMPLE_RATE, rt60=8.0)
    stem_pads_l = signal.fftconvolve(pad_raw_l, ir_l, mode='same') + pad_raw_l * 0.55
    stem_pads_r = signal.fftconvolve(pad_raw_r, ir_r, mode='same') + pad_raw_r * 0.55

    # ── 5. 909 HOUSE KICK (Strictly enters at t=195.00s / Bar 105) ──
    print(f"Synthesizing 909 House Kick (Strict entrance at Bar {DROP_BAR} / t=195.00s)...")
    for bar in range(DROP_BAR, OUTRO_BAR):
        bar_s = bar * BAR_SEC
        for beat in range(4):
            beat_s = bar_s + beat * BEAT_SEC
            idx_s = int(beat_s * SAMPLE_RATE)
            kl, kr = drums.render_kick(velocity=0.96)
            rem = min(len(kl), TOTAL_SAMPLES - idx_s)
            if rem > 0:
                stem_kick_l[idx_s : idx_s + rem] += kl[:rem]
                stem_kick_r[idx_s : idx_s + rem] += kr[:rem]

    # ── 6. NEURAL VOCAL TRACK ("La voz... bum x 12") ──
    print("Synthesizing Vocal Chants ('La voz...' + 12 'bum's)...")
    vocal_raw = get_vocal_bum_tracks(SAMPLE_RATE)
    
    pre_drop_s = (103 * BAR_SEC) + (BEAT_SEC * 1.8)
    pre_idx = int(pre_drop_s * SAMPLE_RATE)
    la_voz_slice = vocal_raw[:int(0.75 * SAMPLE_RATE)]
    rem_v = min(len(la_voz_slice), TOTAL_SAMPLES - pre_idx)
    if rem_v > 0:
        stem_voice_l[pre_idx : pre_idx + rem_v] += la_voz_slice[:rem_v] * 0.85
        stem_voice_r[pre_idx : pre_idx + rem_v] += la_voz_slice[:rem_v] * 0.85
        
    bum_slice = vocal_raw[int(0.92 * SAMPLE_RATE) : int(1.35 * SAMPLE_RATE)]
    bum_slice = bum_slice / (np.max(np.abs(bum_slice)) + 1e-6)
    t_bum = np.linspace(0, 1, len(bum_slice))
    fade = np.clip(1.0 - t_bum**2, 0, 1)
    bum_slice = (bum_slice * fade * 0.92).astype(np.float32)
    
    for bum_idx in range(12):
        bum_time = (DROP_BAR * BAR_SEC) + (bum_idx * BEAT_SEC)
        b_idx = int(bum_time * SAMPLE_RATE)
        pan = -0.2 + 0.4 * (bum_idx % 2)
        g_l = 1.0 - 0.2 * pan
        g_r = 1.0 + 0.2 * pan
        rem = min(len(bum_slice), TOTAL_SAMPLES - b_idx)
        if rem > 0:
            stem_voice_l[b_idx : b_idx + rem] += bum_slice[:rem] * g_l
            stem_voice_r[b_idx : b_idx + rem] += bum_slice[:rem] * g_r
            
    vocal_delay_l = np.zeros_like(stem_voice_l)
    vocal_delay_r = np.zeros_like(stem_voice_r)
    d_samples = int(SAMPLE_RATE * (BEAT_SEC * 0.75))
    vocal_delay_l[d_samples:] = stem_voice_l[:-d_samples] * 0.35
    vocal_delay_r[d_samples:] = stem_voice_r[:-d_samples] * 0.35
    stem_voice_l += vocal_delay_l
    stem_voice_r += vocal_delay_r

    # ── 7. BOUNCING CHICAGO / DEEP HOUSE BASSLINE ──
    print("Synthesizing Bouncing Chicago/Deep House Bassline...")
    # Syncopated 16th-note bounce: root (beat 1), offbeat ghost (1&), octave punch (2&), 5th (3), push (3a)
    house_bass_pattern = [
        (0, 0.0, 0.95, 0.85),   # Beat 1: Root
        (2, 0.0, 0.65, 0.45),   # Beat 1&: Root ghost
        (5, 1200.0, 0.80, 0.50), # Beat 2&: Octave jump!
        (8, 700.0, 0.90, 0.80),  # Beat 3: 5th
        (11, 0.0, 0.75, 0.40),  # Beat 3a: Root bounce
        (14, 1000.0, 0.70, 0.45) # Beat 4&: 7th push to next bar
    ]
    
    for bar in range(DROP_BAR, OUTRO_BAR):
        chord_idx = (bar // 2) % len(chord_bank)
        root_f = [73.42, 49.00, 61.74, 55.00][chord_idx] # D2, G1, B1, A1
        bar_s = bar * BAR_SEC
        
        for step, cents_offset, vel, dur_fact in house_bass_pattern:
            t_note = bar_s + step * SIXTEENTH_SEC + (swing_delay if step % 2 == 1 else 0.0)
            f_note = root_f * (2.0 ** (cents_offset / 1200.0))
            
            b_dur = SIXTEENTH_SEC * dur_fact * 1.8
            n_b = int(b_dur * SAMPLE_RATE)
            t_b = np.linspace(0, b_dur, n_b, endpoint=False)
            
            sub = np.sin(2 * np.pi * f_note * t_b) * np.exp(-t_b * 5.0)
            harm = np.sin(2 * np.pi * (f_note * 2.0) * t_b) * np.exp(-t_b * 9.0) * 0.35
            bass_tone = np.tanh((sub + harm) * 1.6) * vel * 0.60
            
            # Sidechain duck if note coincides with kick
            if step in [0, 8]:
                bass_tone[:int(0.04 * SAMPLE_RATE)] *= np.linspace(0.4, 1.0, int(0.04 * SAMPLE_RATE))
                
            idx_s = int(t_note * SAMPLE_RATE)
            rem = min(n_b, TOTAL_SAMPLES - idx_s)
            if rem > 0:
                stem_bass_l[idx_s : idx_s + rem] += bass_tone[:rem]
                stem_bass_r[idx_s : idx_s + rem] += bass_tone[:rem]

    # ── 8. MARIMBA 5:4 POLYRHYTHMIC COUNTERPOINT ──
    print("Synthesizing Marimba 5:4 Polyrhythm...")
    marimba_notes = [369.99, 440.00, 493.88, 554.37, 587.33] # F#4, A4, B4, C#5, D5
    for bar in range(32, OUTRO_BAR):
        if 103 <= bar < 116:
            continue
        bar_s = bar * BAR_SEC
        step_5 = (BAR_SEC / 5.0)
        for m_idx in range(5):
            m_time = bar_s + m_idx * step_5
            f = marimba_notes[(bar + m_idx) % len(marimba_notes)]
            idx_s = int(m_time * SAMPLE_RATE)
            vel = 0.60 if bar < 104 else 0.78
            ml, mr = xylo.render_note(f, duration=0.8, velocity=vel, pan=0.25)
            rem = min(len(ml), TOTAL_SAMPLES - idx_s)
            if rem > 0:
                stem_marimba_l[idx_s : idx_s + rem] += ml[:rem]
                stem_marimba_r[idx_s : idx_s + rem] += mr[:rem]

    # ── 9. MASTER MIXDOWN & EXERGY GAIN STAGING (MID-SIDE COHESION) ──
    print("Performing Sovereign Master Mixdown & EBU R128 Gain Staging (Mid-Side Cohesion)...")
    mid_pad = 0.5 * (stem_pads_l + stem_pads_r)
    side_pad = 0.5 * (stem_pads_l - stem_pads_r)
    b_ms, a_ms = signal.butter(2, 200.0 / (SAMPLE_RATE * 0.5), btype='high')
    side_pad_filt = signal.lfilter(b_ms, a_ms, side_pad)
    pads_clean_l = mid_pad + 0.22 * side_pad_filt
    pads_clean_r = mid_pad - 0.22 * side_pad_filt

    mid_v = 0.5 * (stem_voice_l + stem_voice_r)
    side_v = 0.5 * (stem_voice_l - stem_voice_r)
    voice_clean_l = mid_v + 0.18 * side_v
    voice_clean_r = mid_v - 0.18 * side_v

    mid_p = 0.5 * (stem_palmas_l + stem_palmas_r)
    side_p = 0.5 * (stem_palmas_l - stem_palmas_r)
    palmas_clean_l = mid_p + 0.22 * side_p
    palmas_clean_r = mid_p - 0.22 * side_p

    mid_x = 0.5 * (stem_xylo_l + stem_xylo_r)
    side_x = 0.5 * (stem_xylo_l - stem_xylo_r)
    xylo_clean_l = mid_x + 0.25 * side_x
    xylo_clean_r = mid_x - 0.25 * side_x

    kick_mono = 0.5 * (stem_kick_l + stem_kick_r)
    bass_mono = 0.5 * (stem_bass_l + stem_bass_r)

    # Hats Mid-Side
    mid_h = 0.5 * (stem_hats_l + stem_hats_r)
    side_h = 0.5 * (stem_hats_l - stem_hats_r)
    hats_clean_l = mid_h + 0.20 * side_h
    hats_clean_r = mid_h - 0.20 * side_h

    # Professional dancefloor mix summing
    master_l = (
        xylo_clean_l * 0.48 +
        palmas_clean_l * 0.35 +
        pads_clean_l * 0.26 +
        kick_mono * 0.75 +
        hats_clean_l * 0.42 +
        voice_clean_l * 0.48 +
        bass_mono * 0.52 +
        stem_marimba_l * 0.28
    )
    master_r = (
        xylo_clean_r * 0.48 +
        palmas_clean_r * 0.35 +
        pads_clean_r * 0.26 +
        kick_mono * 0.75 +
        hats_clean_r * 0.42 +
        voice_clean_r * 0.48 +
        bass_mono * 0.52 +
        stem_marimba_r * 0.28
    )

    pk = max(np.max(np.abs(master_l)), np.max(np.abs(master_r))) + 1e-6
    target_peak = 0.912 # -0.8 dBTP
    master_l = master_l * (target_peak / pk)
    master_r = master_r * (target_peak / pk)

    # ── 10. EXPORT STEMS AND MASTER WAV ──
    stems = {
        "01_Xilofono_AvantGarde_3_4.wav": (xylo_clean_l, xylo_clean_r),
        "02_Palmas_Asincopadas_Flamencas.wav": (palmas_clean_l, palmas_clean_r),
        "03_Pads_Cavernosos_8s_Reverb.wav": (pads_clean_l, pads_clean_r),
        "04_Kick_909_House_Drop.wav": (kick_mono, kick_mono),
        "05_House_Hats_Shakers_Swing.wav": (hats_clean_l, hats_clean_r),
        "06_Bajo_House_Groove_Bouncing.wav": (bass_mono, bass_mono),
        "07_Vocal_LaVoz_Bum12_Dub.wav": (voice_clean_l, voice_clean_r),
        "08_Marimba_Polirritmia_5_4.wav": (stem_marimba_l, stem_marimba_r)
    }

    for name, (l, r) in stems.items():  # noqa: E741
        out_stem = STEMS_DIR / name
        p = max(np.max(np.abs(l)), np.max(np.abs(r))) + 1e-6
        norm_l = (l / p) * 0.88
        norm_r = (r / p) * 0.88
        stereo_stem = np.column_stack([norm_l, norm_r])
        sf.write(str(out_stem), stereo_stem, SAMPLE_RATE, subtype='PCM_24')
        print(f"  ✓ Exported Stem: {name}")

    master_path = BOUNCES_DIR / "BORJA_MOSKV_Polirritmia_Cavernosa_Club_House_6m30.wav"
    master_stereo = np.column_stack([master_l, master_r])
    sf.write(str(master_path), master_stereo, SAMPLE_RATE, subtype='PCM_24')
    print(f"✅ Exported Stereo Master: {master_path.name}")
    print(f"   Size: {master_path.stat().st_size / (1024*1024):.2f} MB")

    return master_path, STEMS_DIR

# ─────────────────────────────────────────────────────────────────────────────
# 7. FLP PROJECT COMPILER
# ─────────────────────────────────────────────────────────────────────────────
def compile_flp_project(stems_dir: Path, output_flp: Path):
    print("Compiling FL Studio Native Project (.flp)...")
    try:
        from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    except ImportError:
        from flp_multitrack_stem_compiler import compile_multitrack_stems_flp
    
    staging = {
        "01_Xilofono_AvantGarde_3_4": {"mixer_track": 1, "volume": 105, "pan": 64},
        "02_Palmas_Asincopadas_Flamencas": {"mixer_track": 2, "volume": 95, "pan": 64},
        "03_Pads_Cavernosos_8s_Reverb": {"mixer_track": 3, "volume": 90, "pan": 64},
        "04_Kick_909_House_Drop": {"mixer_track": 4, "volume": 118, "pan": 64},
        "05_House_Hats_Shakers_Swing": {"mixer_track": 5, "volume": 102, "pan": 64},
        "06_Bajo_House_Groove_Bouncing": {"mixer_track": 6, "volume": 110, "pan": 64},
        "07_Vocal_LaVoz_Bum12_Dub": {"mixer_track": 7, "volume": 108, "pan": 64},
        "08_Marimba_Polirritmia_5_4": {"mixer_track": 8, "volume": 88, "pan": 64}
    }
    
    res = compile_multitrack_stems_flp(
        stems_dir=str(stems_dir),
        project_title="BORJA MOSKV - Polirritmia Cavernosa (Club House 6m30)",
        bpm=128.0,
        output_flp=str(output_flp),
        total_bars=TOTAL_BARS,
        channel_staging=staging
    )
    print(f"✅ FLP Project successfully compiled: {output_flp.name}")
    return res

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    master_wav, stems_path = generate_composition()
    
    target_flp = BOUNCES_DIR / "Polirritmia_Cavernosa_Club_House_6m30.flp"
    compile_flp_project(stems_path, target_flp)
    
    print("\n════ RUNNING DETERMINISTIC C5 RUBIN ACOUSTIC AUDITOR ════")
    cmd_audit = f"python3 /Users/borjafernandezangulo/.gemini/config/skills/c5-rubin-acoustic-linter/scripts/audit_acoustic_exergy.py '{master_wav}'"
    subprocess.run(cmd_audit, shell=True, check=True)
    print("═════════════════════════════════════════════════════════\n")
