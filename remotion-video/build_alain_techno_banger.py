#!/usr/bin/env python3
import os
import json
import shutil
import numpy as np
import scipy.signal as signal
import soundfile as sf
from pathlib import Path

SR = 44100
FPS = 30
BPM = 132.0
BEAT_SEC = 60.0 / BPM
BAR_SEC = BEAT_SEC * 4.0
BEAT_SAMPLES = int(BEAT_SEC * SR)
BAR_SAMPLES = int(BAR_SEC * SR)
SIXTEENTH_SAMPLES = int(BEAT_SAMPLES / 4)

VOICE_DIR = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/alain_techno_audio")
OUT_WAV = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/alain_techno_audio.wav")
OUT_MP3 = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/alain_techno_audio.mp3")
OUT_JSON = Path("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/alain_techno_telemetry.json")
MUSIC_DIR = Path("/Users/borjafernandezangulo/Music/Voice_Clones_Nexus")

# Structure: 40 bars total @ 132 BPM = ~72.7 seconds
TOTAL_BARS = 40
TOTAL_DURATION = TOTAL_BARS * BAR_SEC
TOTAL_SAMPLES = int(TOTAL_DURATION * SR)

print(f"[*] Total duration: {TOTAL_DURATION:.2f}s ({TOTAL_BARS} bars @ {BPM} BPM, {TOTAL_SAMPLES} samples)")

# ==========================================
# 1. DSP DRUM SYNTHESIZERS (909 / PEAK TIME)
# ==========================================
def synth_kick(pitch_start=160.0, pitch_end=42.0, dur_sec=0.45):
    n = int(dur_sec * SR)
    t = np.linspace(0, dur_sec, n, endpoint=False)
    # Exponential pitch envelope
    p_env = np.exp(-t * 28.0)
    freq = pitch_end + (pitch_start - pitch_end) * p_env
    phase = 2 * np.pi * np.cumsum(freq) / SR
    # Body sine
    body = np.sin(phase)
    # Sub boom
    sub_env = np.exp(-t * 6.5)
    body *= sub_env
    # Click transient
    click_n = int(0.015 * SR)
    click = np.random.uniform(-1, 1, click_n) * np.exp(-np.linspace(0, 15, click_n))
    out = np.zeros(n)
    out[:click_n] += click * 0.4
    out += body * 0.95
    # Soft saturation
    out = np.tanh(out * 1.6)
    return out

def synth_clap(dur_sec=0.25):
    n = int(dur_sec * SR)
    t = np.linspace(0, dur_sec, n, endpoint=False)
    noise = np.random.uniform(-1, 1, n)
    # Bandpass filter around 1100 Hz
    b, a = signal.butter(3, [800.0 / (SR / 2), 2500.0 / (SR / 2)], btype='band')
    filtered = signal.lfilter(b, a, noise)
    # Envelope with 3 pre-claps
    env = np.exp(-t * 18.0)
    for burst in [0.01, 0.022, 0.035]:
        b_idx = int(burst * SR)
        b_len = int(0.012 * SR)
        if b_idx + b_len < n:
            env[b_idx:b_idx + b_len] += 0.8 * np.exp(-np.linspace(0, 5, b_len))
    return filtered * env * 0.7

def synth_open_hat(dur_sec=0.35):
    n = int(dur_sec * SR)
    t = np.linspace(0, dur_sec, n, endpoint=False)
    noise = np.random.uniform(-1, 1, n)
    # Highpass filter at 7 kHz
    b, a = signal.butter(4, 7000.0 / (SR / 2), btype='high')
    filtered = signal.lfilter(b, a, noise)
    env = np.exp(-t * 12.0)
    return filtered * env * 0.45

def synth_closed_hat(dur_sec=0.08):
    n = int(dur_sec * SR)
    t = np.linspace(0, dur_sec, n, endpoint=False)
    noise = np.random.uniform(-1, 1, n)
    b, a = signal.butter(4, 8500.0 / (SR / 2), btype='high')
    filtered = signal.lfilter(b, a, noise)
    env = np.exp(-t * 55.0)
    return filtered * env * 0.35

def synth_snare(dur_sec=0.22):
    n = int(dur_sec * SR)
    t = np.linspace(0, dur_sec, n, endpoint=False)
    tone = np.sin(2 * np.pi * 180 * np.exp(-t * 20.0) * t) * np.exp(-t * 15.0)
    noise = np.random.uniform(-1, 1, n)
    b, a = signal.butter(3, 2000.0 / (SR / 2), btype='high')
    filtered_noise = signal.lfilter(b, a, noise) * np.exp(-t * 12.0)
    return (tone * 0.4 + filtered_noise * 0.6) * 0.8

print("[*] Generating drum samples...")
kick_sample = synth_kick()
clap_sample = synth_clap()
open_hat_sample = synth_open_hat()
closed_hat_sample = synth_closed_hat()
snare_sample = synth_snare()

# ==========================================
# 2. TB-303 ROLLING ACID BASS SYNTHESIS
# ==========================================
def synth_acid_note(freq, dur_sec, cutoff_mult=2.5, res=0.7):
    n = int(dur_sec * SR)
    t = np.linspace(0, dur_sec, n, endpoint=False)
    # Sawtooth wave
    saw = 2.0 * (t * freq - np.floor(t * freq + 0.5))
    # Sub octave
    sub = np.sin(2 * np.pi * (freq / 2.0) * t) * 0.3
    raw = saw + sub
    # Modulated lowpass filter
    cutoff = float(np.clip(freq * max(cutoff_mult, 1.2), 180.0, SR * 0.45))
    b, a = signal.butter(2, cutoff / (SR / 2), btype='low')
    filt = signal.lfilter(b, a, raw)
    env = np.exp(-t * 7.0)
    # Saturation overdrive
    return np.tanh(filt * env * 2.8) * 0.5

# Bass notes for F minor / Acid progression (F1 = 43.65 Hz, Ab1 = 51.91 Hz, Bb1 = 58.27 Hz, C2 = 65.41 Hz)
bass_freqs = [43.65, 43.65, 51.91, 43.65, 58.27, 43.65, 65.41, 58.27]

# Initialize audio stems (L, R)
stereo_out = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

def add_sample(target, sample, start_idx, gain_l=1.0, gain_r=1.0):
    slen = len(sample)
    if start_idx >= len(target) or start_idx < 0:
        return
    end_idx = min(start_idx + slen, len(target))
    actual_len = end_idx - start_idx
    target[start_idx:end_idx, 0] += sample[:actual_len] * gain_l
    target[start_idx:end_idx, 1] += sample[:actual_len] * gain_r

# ==========================================
# 3. ARRANGEMENT TIMELINE
# ==========================================
# Section definitions (in bars):
# 0 - 8:   Intro dialogue + Atmospheric sub drone + Sub sweeps
# 8 - 16:  Build up: kick filter rising + hats start + snare roll + vocal hype
# 16 - 32: THE PEAK DROP: 16 bars of pure 132 BPM acid techno + vocal chops
# 32 - 40: Second section / Outro with acid breakdown and final crash

print("[*] Sequencing 132 BPM drums and bass...")
for bar in range(TOTAL_BARS):
    bar_start = bar * BAR_SAMPLES
    
    # KICK:
    # Bars 8-15: Filtered / rising kick
    # Bars 16-39: FULL PUNCH KICK (every quarter note)
    if 8 <= bar < 16:
        # Build up kick with increasing volume
        k_vol = (bar - 8 + 1) / 8.0 * 0.75
        for beat in range(4):
            idx = bar_start + beat * BEAT_SAMPLES
            add_sample(stereo_out, kick_sample * k_vol, idx, 0.9, 0.9)
    elif bar >= 16 and bar != 32: # brief silence on bar 32 beat 1
        for beat in range(4):
            idx = bar_start + beat * BEAT_SAMPLES
            add_sample(stereo_out, kick_sample, idx, 1.0, 1.0)
            
    # CLAP (beats 2 and 4):
    if (12 <= bar < 16) or (bar >= 16 and bar != 32):
        for beat in [1, 3]:
            idx = bar_start + beat * BEAT_SAMPLES
            add_sample(stereo_out, clap_sample, idx, 0.85, 0.85)

    # OPEN HAT (offbeat 8th notes):
    if bar >= 16:
        for beat in range(4):
            idx = bar_start + beat * BEAT_SAMPLES + int(BEAT_SAMPLES / 2)
            add_sample(stereo_out, open_hat_sample, idx, 0.65, 0.75)

    # CLOSED HAT (16th notes):
    if (10 <= bar < 16) or (bar >= 16):
        for sixteenth in range(16):
            if sixteenth % 4 != 2: # don't mask the open hat completely
                idx = bar_start + sixteenth * SIXTEENTH_SAMPLES
                pan_l = 0.5 + 0.2 * np.sin(sixteenth)
                pan_r = 0.5 - 0.2 * np.sin(sixteenth)
                add_sample(stereo_out, closed_hat_sample * 0.45, idx, pan_l, pan_r)

    # ACID 303 BASSLINE (16th note pattern in drop bars 16-39):
    if bar >= 16:
        cutoff_evolution = 3.5 + 2.0 * np.sin((bar - 16) / 4.0)
        for s in range(16):
            f_note = bass_freqs[s % len(bass_freqs)]
            # Accentuate certain steps
            accent = 1.3 if s in [0, 3, 6, 10, 12] else 0.8
            acid_n = synth_acid_note(f_note, dur_sec=BEAT_SEC * 0.25, cutoff_mult=cutoff_evolution * accent)
            idx = bar_start + s * SIXTEENTH_SAMPLES
            add_sample(stereo_out, acid_n * accent, idx, 0.7, 0.7)

    # BUILD-UP SNARE ROLL (Bar 14 and 15):
    if bar in [14, 15]:
        divisions = 8 if bar == 14 else 16
        div_len = int(BAR_SAMPLES / divisions)
        for d in range(divisions):
            idx = bar_start + d * div_len
            vol = (d + 1) / divisions * (0.8 if bar == 14 else 1.1)
            add_sample(stereo_out, snare_sample * vol, idx, 0.8, 0.8)

# ==========================================
# 4. VOCAL TIMELINE & CROPPING
# ==========================================
print("[*] Placing vocal stems and dialogue...")
dialogue_schedule = [
    # Bar 0.5: Alain intro
    (0.5 * BAR_SEC, "alain_drop1.wav", "alain", "¡Callaos ya, hostia! ¡No digáis pisos ni fondos tan alto, que tengo el móvil aquí y el Bot de Hacienda tiene micro abierto!"),
    # Bar 4.5: Mitxu responds
    (4.5 * BAR_SEC, "mitxu_resp1.wav", "mitxu", "¡Díselo Alain! ¡Que como te huelan el alquiler te precintan el subwoofer de quince pulgadas!"),
    # Bar 8.5: Alain build-up warning
    (8.0 * BAR_SEC, "alain_drop2.wav", "alain", "¡Ese bicho te huele las plusvalías a cinco kilómetros y me precinta los RCF y los platos!"),
    # Bar 11.5: Alain orders the 132 BPM kick
    (11.2 * BAR_SEC, "alain_bombo.wav", "alain", "¡Mete el bombo a ciento treinta y dos BPMs ya, hostia!"),
    # Bar 13.8: Mitxu hype before drop
    (13.8 * BAR_SEC, "mitxu_resp2.wav", "mitxu", "¡Dale zapatilla, tigre máquina! ¡Hacienda somos todos los pringaos!"),
    # THE DROP CHOPS (Bars 16 - 32):
    (16.0 * BAR_SEC, "alain_chop1.wav", "alain", "¡El Bot de Hacienda!"),
    (20.0 * BAR_SEC, "alain_chop2.wav", "alain", "¡Te precinta los RCF!"),
    (24.0 * BAR_SEC, "alain_chop1.wav", "alain", "¡El Bot de Hacienda!"),
    (28.0 * BAR_SEC, "mitxu_chop.wav",  "mitxu", "¡A la puta calle con el RCF!"),
    # Bar 32 breakdown vocal
    (32.5 * BAR_SEC, "alain_chop2.wav", "alain", "¡Te precinta los RCF!"),
    (36.0 * BAR_SEC, "alain_chop1.wav", "alain", "¡El Bot de Hacienda!")
]

events_for_json = []

for start_time, wav_name, speaker, text in dialogue_schedule:
    fpath = VOICE_DIR / wav_name
    if not fpath.exists():
        print(f"Warning: {fpath} does not exist!")
        continue
    v_data, v_sr = sf.read(fpath)
    if len(v_data.shape) > 1:
        v_data = v_data[:, 0]
    if v_sr != SR:
        v_data = signal.resample(v_data, int(len(v_data) * SR / v_sr))
    
    # Highpass vocal to keep low end clean for 132 BPM kick
    b_vhp, a_vhp = signal.butter(3, 130.0 / (SR / 2), btype='high')
    v_data = signal.lfilter(b_vhp, a_vhp, v_data)
    
    # Slight radio slapback delay (45 ms) for rave presence
    delay_s = int(0.045 * SR)
    slap = np.zeros(len(v_data) + delay_s)
    slap[:len(v_data)] += v_data
    slap[delay_s:] += v_data * 0.28
    
    dur_sec = len(v_data) / SR
    start_idx = int(start_time * SR)
    add_sample(stereo_out, slap, start_idx, 1.15, 1.15)
    
    events_for_json.append({
        "speaker": speaker,
        "text": text,
        "start_sec": start_time,
        "end_sec": start_time + dur_sec,
        "start_frame": int(start_time * FPS),
        "end_frame": int((start_time + dur_sec) * FPS)
    })

# ==========================================
# 5. MASTERING CHAIN (EBU R128 / LIMITER)
# ==========================================
print("[*] Mastering audio (soft clipping, brickwall limiter)...")
# Normalize peak to 0.98 with soft clipper
peak = np.max(np.abs(stereo_out))
if peak > 0:
    stereo_out = stereo_out / peak * 1.25
stereo_out = np.tanh(stereo_out * 0.85)

# Save WAV
sf.write(OUT_WAV, stereo_out, SR, subtype='PCM_16')
print(f"✓ Master WAV saved: {OUT_WAV}")

# Convert to MP3
cmd_mp3 = ["ffmpeg", "-y", "-i", str(OUT_WAV), "-b:a", "320k", str(OUT_MP3)]
import subprocess
subprocess.run(cmd_mp3, check=True)
print(f"✓ Master MP3 saved: {OUT_MP3}")

# Copy to Music/Voice_Clones_Nexus
shutil.copy2(OUT_WAV, MUSIC_DIR / "Alain_El_Bot_de_Hacienda_132BPM_Master.wav")
shutil.copy2(OUT_MP3, MUSIC_DIR / "Alain_El_Bot_de_Hacienda_132BPM_Master.mp3")
print(f"✓ Centralized master audio to {MUSIC_DIR}")

# ==========================================
# 6. EXTRACT FRAME TELEMETRY FOR REMOTION
# ==========================================
print("[*] Generating frame-by-frame telemetry JSON...")
total_frames = int(TOTAL_DURATION * FPS)
frames_telemetry = []

# Frame window length
hop_samples = int(SR / FPS)
fft_size = 2048

# Frequency band edges (16 bands)
band_edges = np.logspace(np.log10(30), np.log10(16000), 17)
freqs = np.fft.rfftfreq(fft_size, 1.0 / SR)

for f in range(total_frames):
    cur_sec = f / FPS
    s_idx = int(f * hop_samples)
    e_idx = min(s_idx + hop_samples, TOTAL_SAMPLES)
    
    if e_idx <= s_idx:
        chunk = np.zeros((hop_samples, 2))
    else:
        chunk = stereo_out[s_idx:e_idx]
    
    # Mono chunk
    mono = chunk.mean(axis=1)
    if len(mono) < fft_size:
        pad = np.zeros(fft_size)
        pad[:len(mono)] = mono
        mono_fft = pad
    else:
        mono_fft = mono[:fft_size]
        
    rms = float(np.sqrt(np.mean(mono ** 2)))
    
    # FFT spectrum
    spec = np.abs(np.fft.rfft(mono_fft * np.hanning(fft_size)))
    
    # Sub energy (30-100 Hz)
    sub_mask = (freqs >= 30) & (freqs <= 100)
    sub_energy = float(np.mean(spec[sub_mask])) if np.any(sub_mask) else 0.0
    
    # Mid energy (400-3000 Hz)
    mid_mask = (freqs >= 400) & (freqs <= 3000)
    mid_energy = float(np.mean(spec[mid_mask])) if np.any(mid_mask) else 0.0
    
    # High energy (5000-16000 Hz)
    high_mask = (freqs >= 5000) & (freqs <= 16000)
    high_energy = float(np.mean(spec[high_mask])) if np.any(high_mask) else 0.0
    
    # 16 bands normalized
    bands = []
    for b in range(16):
        b_mask = (freqs >= band_edges[b]) & (freqs < band_edges[b+1])
        b_val = float(np.mean(spec[b_mask])) if np.any(b_mask) else 0.0
        bands.append(round(min(b_val * 4.0, 1.0), 3))
        
    # Check speaker active
    spk = "none"
    cur_text = ""
    for ev in events_for_json:
        if ev["start_frame"] <= f <= ev["end_frame"]:
            spk = ev["speaker"]
            cur_text = ev["text"]
            break
            
    is_drop = (f >= 16 * BAR_SEC * FPS)
    is_kick_beat = (f % int(BEAT_SEC * FPS) == 0) and (f >= 8 * BAR_SEC * FPS)

    frames_telemetry.append({
        "frame": f,
        "time": round(cur_sec, 3),
        "rms": round(rms, 4),
        "sub": round(min(sub_energy * 5.0, 1.0), 4),
        "mid": round(min(mid_energy * 6.0, 1.0), 4),
        "high": round(min(high_energy * 10.0, 1.0), 4),
        "bands": bands,
        "speaker": spk,
        "text": cur_text,
        "isDrop": is_drop,
        "isKickBeat": is_kick_beat,
        "headbob": round(np.sin(f * 2 * np.pi * (BPM / 60.0) / FPS), 3)
    })

data_payload = {
    "bpm": BPM,
    "total_bars": TOTAL_BARS,
    "duration_sec": TOTAL_DURATION,
    "total_frames": total_frames,
    "events": events_for_json,
    "frames": frames_telemetry
}

with open(OUT_JSON, "w") as jf:
    json.dump(data_payload, jf, indent=2)

shutil.copy2(OUT_JSON, MUSIC_DIR / "Alain_El_Bot_de_Hacienda_Telemetry.json")
print(f"✓ Telemetry JSON saved: {OUT_JSON} ({len(frames_telemetry)} frames)")
print("=== TRACK SYNTHESIS COMPLETED SOTA ===")
