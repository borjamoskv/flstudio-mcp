#!/usr/bin/env python3
"""
FL Studio MCP — Elon Musk "Late Night Interview" Ambient Breakbeat (117 BPM)
═══════════════════════════════════════════════════════════════════════════
NO DROPS, NO HOOKS: Pure Continuous Atmospheric Downtempo Narrative.

Aesthetic Directives:
- Veto a la Mecánica Drop/Build-up: Cero redobles de caja, cero paradas artificiales
  para impacto de club, cero falsos drops de festival.
- Veto a Ganchos / Chops Vocales (No Hooks): La voz fluye en orden cronológico
  documental de principio a fin, como una entrevista grabada en cinta a altas horas.
- Textura Continua e Íntima: El groove de breakbeat a 117 BPM camina con suavidad
  constante (estilo Jon Hopkins / Burial / Bonobo / AIR), dejando que el diálogo
  y la armonía de Fa menor respiren sin sobresaltos.
- Silencios y Pausas Naturales: Respeta las dudas, respiraciones y vacíos
  reales entre la pregunta del entrevistador y la respuesta reflexiva de Elon.
- Masterizado EBU R128 (-14.0 LUFS, -1.0 dBFS True Peak, Linkwitz-Riley 120 Hz mono sub).
"""

import sys
import json
import subprocess
import numpy as np
import soundfile as sf
from scipy import signal
from pathlib import Path
import pyloudnorm as pln

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR))
sys.path.insert(0, str(WORKSPACE_DIR / "scripts"))

from scripts.flp_multitrack_stem_compiler import compile_multitrack_stems_flp  # noqa: E402

SR = 48000
BPM = 117.0
BARS = 76
BEATS_PER_BAR = 4
BEAT_DUR = 60.0 / BPM  # ~0.51282s
BAR_DUR = BEAT_DUR * BEATS_PER_BAR  # ~2.05128s
TOTAL_DUR = BAR_DUR * BARS  # ~155.90s (2m 36s)
TOTAL_SAMPLES = int(TOTAL_DUR * SR)

VOCAL_SOURCE_WAV = WORKSPACE_DIR / "samples" / "stems" / "elon_musk_loneliness" / "elon_musk_vocals_48k_24bit.wav"
OUTPUT_DIR = WORKSPACE_DIR / "samples" / "stems" / "elon_musk_loneliness"
STEMS_DIR = OUTPUT_DIR / "stems_117bpm"
STEMS_DIR.mkdir(parents=True, exist_ok=True)

MASTER_WAV = OUTPUT_DIR / "Elon_Musk_Breakbeat_117BPM_Master.wav"
MASTER_MP3 = OUTPUT_DIR / "Elon_Musk_Breakbeat_117BPM_Master.mp3"
OUTPUT_FLP = OUTPUT_DIR / "Elon_Musk_Breakbeat_117BPM.flp"


def create_reverb(audio: np.ndarray, decay_sec: float = 2.8, wet: float = 0.26) -> np.ndarray:
    """Warm convolution reverb with soft damping (shared EMT-140 room)."""
    imp_len = int(decay_sec * SR)
    t = np.linspace(0, decay_sec, imp_len, endpoint=False)
    env = np.exp(-t * 2.4)
    imp_l = env * np.random.randn(imp_len)
    imp_r = env * np.random.randn(imp_len)

    b, a = signal.butter(2, 4400 / (SR / 2), btype="low")
    imp_l = signal.filtfilt(b, a, imp_l)
    imp_r = signal.filtfilt(b, a, imp_r)

    imp_l = (imp_l / (np.linalg.norm(imp_l) + 1e-9)) * 0.28
    imp_r = (imp_r / (np.linalg.norm(imp_r) + 1e-9)) * 0.28

    out = np.zeros_like(audio)
    out[:, 0] = (1.0 - wet) * audio[:, 0] + wet * signal.fftconvolve(audio[:, 0], imp_l, mode="same")
    out[:, 1] = (1.0 - wet) * audio[:, 1] + wet * signal.fftconvolve(audio[:, 1], imp_r, mode="same")
    return out


def apply_warm_delay(
    audio: np.ndarray,
    delay_sec: float = 0.3846,  # 3/16 at 117 BPM
    feedback: float = 0.38,
    wet: float = 0.25,
    hp_hz: float = 300.0,
    lp_hz: float = 3800.0
) -> np.ndarray:
    """Subtle, non-intrusive tape delay for spatial depth."""
    delay_samples = int(delay_sec * SR)
    if delay_samples >= len(audio):
        return audio

    out = audio.copy()
    d_l = np.zeros(len(audio), dtype=np.float32)
    d_r = np.zeros(len(audio), dtype=np.float32)

    curr_l = audio[:, 0].copy()
    curr_r = audio[:, 1].copy()

    b, a = signal.butter(2, [hp_hz / (SR / 2), lp_hz / (SR / 2)], btype="bandpass")

    for tap in range(1, 4):
        offset = tap * delay_samples
        if offset >= len(audio):
            break
        gain = feedback ** tap
        filt_l = signal.filtfilt(b, a, curr_l[:-offset]) * gain
        filt_r = signal.filtfilt(b, a, curr_r[:-offset]) * gain

        d_l[offset:] += filt_l * (0.8 if tap % 2 == 1 else 1.0)
        d_r[offset:] += filt_r * (1.0 if tap % 2 == 1 else 0.8)

    out[:, 0] += d_l * wet
    out[:, 1] += d_r * wet
    return out


# -----------------------------------------------------------------------------
# 1. STEM: SUB KICK (Suave, constante, orgánico, sin drops)
# -----------------------------------------------------------------------------
def generate_sub_kick() -> np.ndarray:
    print("🥁 [1/6] Generando Bombo Sub continuo (50 Hz, pulso downtempo constante)...")
    kick_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    kick_len = int(0.30 * SR)
    t = np.linspace(0, 0.30, kick_len, endpoint=False)
    pitch_env = 50.0 + (115.0 - 50.0) * np.exp(-t * 40.0)
    phase = 2.0 * np.pi * np.cumsum(pitch_env) / SR
    amp_env = np.exp(-t * 11.5)
    click = np.sin(2 * np.pi * 850.0 * t) * np.exp(-t * 90.0) * 0.12
    single_kick = (np.sin(phase) + click) * amp_env * 0.82

    # Patrón constante y suave (sin build-ups ni paradas bruscas)
    # Entra suave en compás 4 y se mantiene hasta el compás 72
    pattern_a = [0.0, 1.5, 3.25]
    pattern_b = [0.0, 2.0, 2.75]

    for bar in range(BARS):
        if bar < 4 or bar >= 72:
            continue

        hits = pattern_a if (bar % 2 == 0) else pattern_b
        # Suave fade in en compases 4 a 8
        bar_vol = min(1.0, (bar - 3) / 4.0) if bar < 8 else (1.0 if bar < 68 else max(0.0, (72 - bar) / 4.0))

        for h in hits:
            start_s = int((bar * BAR_DUR + h * BEAT_DUR) * SR)
            end_s = min(TOTAL_SAMPLES, start_s + kick_len)
            dur = end_s - start_s
            kick_stem[start_s:end_s, 0] += single_kick[:dur] * bar_vol
            kick_stem[start_s:end_s, 1] += single_kick[:dur] * bar_vol

    return kick_stem


# -----------------------------------------------------------------------------
# 2. STEM: BREAKBEAT DRUMS (Groove de fondo constante, escobillas, cero redobles)
# -----------------------------------------------------------------------------
def generate_breakbeat_drums() -> np.ndarray:
    print("🥁 [2/6] Generando Batería Breakbeat Continua (Textura constante, sin redobles)...")
    drums_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    # Snare suave y profundo (180 Hz, cuerpo apagado estilo cinta)
    snare_len = int(0.22 * SR)
    t_sn = np.linspace(0, 0.22, snare_len, endpoint=False)
    sn_tone = np.sin(2 * np.pi * 180.0 * t_sn) * np.exp(-t_sn * 26.0) * 0.40
    noise = np.random.randn(snare_len)
    b_sn, a_sn = signal.butter(2, [750 / (SR / 2), 5500 / (SR / 2)], btype="bandpass")
    sn_noise = signal.filtfilt(b_sn, a_sn, noise) * np.exp(-t_sn * 18.0) * 0.45
    main_snare = (sn_tone + sn_noise) * 0.65
    ghost_snare = main_snare * 0.24

    # Charles cerrado cálido y oscuro
    hat_len = int(0.05 * SR)
    t_hat = np.linspace(0, 0.05, hat_len, endpoint=False)
    b_h, a_h = signal.butter(2, [5500 / (SR / 2), 12000 / (SR / 2)], btype="bandpass")
    filt_hat = signal.filtfilt(b_h, a_h, np.random.randn(hat_len)) * np.exp(-t_hat * 70.0) * 0.18

    # Shaker suave orgánico
    shaker_len = int(0.07 * SR)
    t_sh = np.linspace(0, 0.07, shaker_len, endpoint=False)
    b_sh, a_sh = signal.butter(2, [4000 / (SR / 2), 9500 / (SR / 2)], btype="bandpass")
    shaker = signal.filtfilt(b_sh, a_sh, np.random.randn(shaker_len)) * np.exp(-t_sh * 45.0) * 0.12

    for bar in range(BARS):
        if bar < 4 or bar >= 72:
            continue

        bar_vol = min(1.0, (bar - 3) / 4.0) if bar < 8 else (1.0 if bar < 68 else max(0.0, (72 - bar) / 4.0))
        bar_start_t = bar * BAR_DUR

        # Snares en pulsos 1.0 y 3.0
        for b_pos in [1.0, 3.0]:
            st = int((bar_start_t + b_pos * BEAT_DUR) * SR)
            en = min(TOTAL_SAMPLES, st + snare_len)
            drums_stem[st:en, 0] += main_snare[:en - st] * bar_vol
            drums_stem[st:en, 1] += main_snare[:en - st] * bar_vol

        # Ghost notes orgánicas para el groove
        for g_pos in [1.75, 2.25, 3.75]:
            st = int((bar_start_t + g_pos * BEAT_DUR) * SR)
            en = min(TOTAL_SAMPLES, st + snare_len)
            drums_stem[st:en, 0] += ghost_snare[:en - st] * bar_vol
            drums_stem[st:en, 1] += ghost_snare[:en - st] * bar_vol

        # 16th Hi-Hats sutiles
        for step in range(16):
            h_pos = step * 0.25
            is_offbeat = (step % 2 != 0)
            human_offset_s = 0.005 if is_offbeat else 0.001
            st = int((bar_start_t + h_pos * BEAT_DUR + human_offset_s) * SR)
            en = min(TOTAL_SAMPLES, st + hat_len)
            vel = (0.28 if (step % 4 == 2) else (0.14 if is_offbeat else 0.20)) * bar_vol
            drums_stem[st:en, 0] += filt_hat[:en - st] * vel * 0.85
            drums_stem[st:en, 1] += filt_hat[:en - st] * vel * 1.15

        # Shakers
        for step in range(8):
            s_pos = step * 0.5 + 0.25
            st = int((bar_start_t + s_pos * BEAT_DUR) * SR)
            en = min(TOTAL_SAMPLES, st + shaker_len)
            pan_l = (1.0 if step % 2 == 0 else 0.7) * bar_vol
            pan_r = (0.7 if step % 2 == 0 else 1.0) * bar_vol
            drums_stem[st:en, 0] += shaker[:en - st] * pan_l
            drums_stem[st:en, 1] += shaker[:en - st] * pan_r

    return drums_stem


# -----------------------------------------------------------------------------
# 3. STEM: SUB BASS (Línea de bajo rodante, armónica y continua)
# -----------------------------------------------------------------------------
def generate_sub_bass() -> np.ndarray:
    print("🎸 [3/6] Generando Sub Bass Continuo (F Minor / F Dorian, sin caídas de volumen)...")
    bass_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    root_freqs = [
        43.65, 43.65,  # Fm9 (F1)
        34.65, 51.91,  # Dbmaj7 (Db1) / Ab1
        58.27, 58.27,  # Bbm9 (Bb1)
        38.89, 43.65   # Ebadd9 (Eb1) / Fm9 (F1)
    ]

    for bar in range(BARS):
        if bar < 4 or bar >= 72:
            continue

        bar_vol = min(1.0, (bar - 3) / 4.0) if bar < 8 else (1.0 if bar < 68 else max(0.0, (72 - bar) / 4.0))

        freq = root_freqs[bar % len(root_freqs)]
        bar_start_s = int(bar * BAR_DUR * SR)
        bar_len_s = int(BAR_DUR * SR)

        t = np.linspace(0, BAR_DUR, bar_len_s, endpoint=False)
        sine1 = np.sin(2 * np.pi * freq * t)
        sine2 = np.sin(2 * np.pi * (freq * 2.0) * t) * 0.18
        bass_note = (sine1 + sine2) * bar_vol

        # Ataque suave de 15ms y relajación de 25ms para evitar cualquier clic
        att_len = int(0.015 * SR)
        rel_len = int(0.025 * SR)
        bass_note[:att_len] *= np.linspace(0, 1, att_len)
        bass_note[-rel_len:] *= np.linspace(1, 0, rel_len)

        # Sidechain muy sutil y suave (solo -3 dB en el bombo para no generar bombeo artificial)
        sidechain_env = np.ones(bar_len_s, dtype=np.float32)
        kick_beats = [0.0, 1.5, 3.25] if bar % 2 == 0 else [0.0, 2.0, 2.75]
        duck_len = int(0.18 * SR)
        for kb in kick_beats:
            kb_s = int(kb * BEAT_DUR * SR)
            kb_en = min(bar_len_s, kb_s + duck_len)
            d_dur = kb_en - kb_s
            t_duck = np.linspace(0, np.pi, d_dur)
            duck_curve = 0.55 + 0.45 * (0.5 - 0.5 * np.cos(t_duck))
            sidechain_env[kb_s:kb_en] *= duck_curve

        bass_note = bass_note * sidechain_env * 0.70

        end_s = min(TOTAL_SAMPLES, bar_start_s + bar_len_s)
        dur = end_s - bar_start_s
        bass_stem[bar_start_s:end_s, 0] += bass_note[:dur]
        bass_stem[bar_start_s:end_s, 1] += bass_note[:dur]

    # Filtro paso-bajo a 130 Hz
    b_lp, a_lp = signal.butter(2, 130.0 / (SR / 2), btype="low")
    bass_stem[:, 0] = signal.filtfilt(b_lp, a_lp, bass_stem[:, 0])
    bass_stem[:, 1] = signal.filtfilt(b_lp, a_lp, bass_stem[:, 1])

    return bass_stem


# -----------------------------------------------------------------------------
# 4. STEM: ATMOSPHERIC PADS (Manto continuo de Fa menor, sin interrupciones)
# -----------------------------------------------------------------------------
def generate_atmospheric_pads() -> np.ndarray:
    print("🎹 [4/6] Generando Atmospheric Pads (Manto cálido continuo de principio a fin)...")
    pads_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    progression = [
        [174.61, 207.65, 261.63, 311.13, 392.00],  # Fm9
        [138.59, 174.61, 207.65, 261.63, 311.13],  # Dbmaj7
        [116.54, 138.59, 174.61, 207.65, 261.63],  # Bbm9
        [155.56, 196.00, 233.08, 261.63, 349.23],  # Ebadd9
    ]

    chord_dur = BAR_DUR * 2.0
    chord_samples = int(chord_dur * SR)

    for bar_pair in range(0, BARS, 2):
        chord_idx = (bar_pair // 2) % len(progression)
        chord_freqs = progression[chord_idx]

        st = int(bar_pair * BAR_DUR * SR)
        en = min(TOTAL_SAMPLES, st + chord_samples)
        dur = en - st
        t = np.linspace(0, chord_dur, chord_samples, endpoint=False)[:dur]

        chord_signal_l = np.zeros(dur, dtype=np.float32)
        chord_signal_r = np.zeros(dur, dtype=np.float32)

        for f in chord_freqs:
            w1 = np.sin(2 * np.pi * f * t)
            w2 = signal.sawtooth(2 * np.pi * (f * 1.002) * t) * 0.12
            w3 = signal.sawtooth(2 * np.pi * (f * 0.998) * t) * 0.12
            voice = w1 + w2 + w3

            chord_signal_l += voice * 0.16
            chord_signal_r += (w1 + w3 + w2) * 0.16

        # Envolvente que enlaza suavemente sin cortes
        env = np.sin(np.linspace(0, np.pi, dur)) ** 0.4
        b_bp, a_bp = signal.butter(2, [180.0 / (SR / 2), 3800.0 / (SR / 2)], btype="bandpass")
        pad_l = signal.filtfilt(b_bp, a_bp, chord_signal_l * env)
        pad_r = signal.filtfilt(b_bp, a_bp, chord_signal_r * env)

        pads_stem[st:en, 0] += pad_l
        pads_stem[st:en, 1] += pad_r

    pads_stem = create_reverb(pads_stem, decay_sec=3.5, wet=0.35)
    return pads_stem


# -----------------------------------------------------------------------------
# 5. STEM: RHODES TEXTURES (Melodías sutiles de fondo, estilo Jon Hopkins / AIR)
# -----------------------------------------------------------------------------
def generate_rhodes_textures() -> np.ndarray:
    print("✨ [5/6] Generando Rhodes Textural (Melodía contemplativa dispersa, sin ostinatos)...")
    rhodes_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    # Notas espaciadas y contemplativas (no arpegio rápido continuo)
    # Acordes de paso en tiempos lentos
    notes = [
        392.00, 523.25, 622.25, 698.46, 523.25, 466.16,
        622.25, 783.99, 698.46, 523.25, 392.00, 466.16
    ]

    note_dur = BEAT_DUR * 1.5
    note_samples = int(note_dur * SR)
    t_n = np.linspace(0, note_dur, note_samples, endpoint=False)

    # El Rhodes aparece solo en momentos de respiración lírica
    active_bars = [6, 7, 14, 15, 22, 23, 30, 31, 38, 39, 46, 47, 54, 55, 62, 63, 68, 69]

    for bar in active_bars:
        if bar >= BARS:
            continue
        bar_start_s = int(bar * BAR_DUR * SR)

        for step in [0, 2]:
            f = notes[(bar + step) % len(notes)]
            st = bar_start_s + int(step * BEAT_DUR * SR)
            en = min(TOTAL_SAMPLES, st + note_samples)
            dur = en - st

            t_slice = t_n[:dur]
            tone = (np.sin(2 * np.pi * f * t_slice) +
                    np.sin(2 * np.pi * f * 2 * t_slice) * 0.22 +
                    np.sin(2 * np.pi * f * 3 * t_slice) * 0.05)
            decay_env = np.exp(-t_slice * 4.5)
            bell = tone * decay_env * 0.28

            rhodes_stem[st:en, 0] += bell * 0.9
            rhodes_stem[st:en, 1] += bell * 1.1

    rhodes_stem = apply_warm_delay(rhodes_stem, delay_sec=BEAT_DUR * 0.75, feedback=0.40, wet=0.32)
    rhodes_stem = create_reverb(rhodes_stem, decay_sec=2.8, wet=0.30)
    return rhodes_stem


# -----------------------------------------------------------------------------
# 6. STEM: NARRATIVA VOCAL COMPLETA Y LINEAL (Sin loops, sin chops, orden 100% natural)
# -----------------------------------------------------------------------------
def load_and_arrange_linear_vocal():
    print("🎙️ [6/6] Alineando la voz en orden cronológico documental continuo...")
    raw_vocal, sr = sf.read(str(VOCAL_SOURCE_WAV))
    if sr != SR:
        num_target = int(len(raw_vocal) * SR / sr)
        raw_vocal = signal.resample(raw_vocal, num_target)
    if raw_vocal.ndim == 1:
        raw_vocal = np.column_stack([raw_vocal, raw_vocal])

    # High-pass a 120 Hz para purgar subgrave
    b_hp, a_hp = signal.butter(2, 120.0 / (SR / 2), btype="high")
    vocal_clean = signal.filtfilt(b_hp, a_hp, raw_vocal, axis=0)

    # Nivelación suave
    peak = np.max(np.abs(vocal_clean)) + 1e-9
    vocal_clean = (vocal_clean / peak) * 0.75

    lead_vocal_stem = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    def get_slice(start_t: float, end_t: float) -> np.ndarray:
        s_idx = int(start_t * SR)
        e_idx = int(end_t * SR)
        chunk = vocal_clean[s_idx:e_idx].copy()
        fade_len = int(0.03 * SR)
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)
        chunk[:fade_len, 0] *= fade_in
        chunk[:fade_len, 1] *= fade_in
        chunk[-fade_len:, 0] *= fade_out
        chunk[-fade_len:, 1] *= fade_out
        return chunk

    def paste_chunk(chunk: np.ndarray, start_bar: float):
        st = int(start_bar * BAR_DUR * SR)
        en = min(TOTAL_SAMPLES, st + len(chunk))
        dur = en - st
        lead_vocal_stem[st:en, :] += chunk[:dur, :]

    # Slices de la entrevista (orden estrictamente cronológico, sin repeticiones):
    # 1. "What's something difficult you're going through that people don't often see?" [3.8s - 6.7s]
    seg1 = get_slice(3.8, 6.7)
    # 2. "Most people wouldn't want to be me. They may think they'd want to be me, but they don't.
    #     They don't know. They don't understand. I mean, my mind is a storm." [6.8s - 15.0s]
    seg2 = get_slice(6.8, 15.0)
    # 3. "How are you doing?" [20.7s - 22.0s]
    seg3 = get_slice(20.7, 22.0)
    # 4. "I'm in overall okay. In the grand scheme of things, I can't complain." [24.3s - 29.8s]
    seg4 = get_slice(24.3, 29.8)
    # 5. "Do you get lonely?" [31.0s - 32.5s]
    seg5 = get_slice(31.0, 32.5)
    # 6. "Sometimes, but you know, my kids and friends keep me company." [34.0s - 40.5s]
    seg6 = get_slice(34.0, 40.5)
    # 7. "So, not existential?" [42.6s - 44.5s]
    seg7 = get_slice(42.6, 44.5)
    # 8. "There are many nights I sleep alone. I don't have to, but I do." [46.0s - 51.5s]
    seg8 = get_slice(46.0, 51.5)

    # ═════════════════════════════════════════════════════════════════════════
    # DISTRIBUCIÓN CRONOLÓGICA CON AIRE Y RESPIRACIÓN NATURAL
    # ═════════════════════════════════════════════════════════════════════════

    # Compás 6.0: Pregunta inicial
    paste_chunk(seg1, start_bar=6.0)

    # Compás 9.0: Respuesta de Elon ("Most people wouldn't want to be me... mind is a storm")
    paste_chunk(seg2, start_bar=9.0)

    # Compases 14 a 22: Espacio instrumental (8 compases completos de música pura)
    # Compás 22.5: "¿How are you doing?"
    paste_chunk(seg3, start_bar=22.5)

    # Compás 24.5: "I mean, overall, okay. In the grand scheme of things..."
    paste_chunk(seg4, start_bar=24.5)

    # Compases 29 a 37: Espacio instrumental para asimilar (8 compases de música pura)
    # Compás 37.0: "Do you get lonely?"
    paste_chunk(seg5, start_bar=37.0)

    # Compás 39.0: "Sometimes, but you know, my kids and friends keep me company."
    paste_chunk(seg6, start_bar=39.0)

    # Compases 44 a 52: Espacio instrumental (8 compases de música pura)
    # Compás 52.0: "So, not existential?"
    paste_chunk(seg7, start_bar=52.0)

    # Compás 54.5: Conclusión reflexiva final ("There are many nights I sleep alone. I don't have to, but I do.")
    paste_chunk(seg8, start_bar=54.5)

    # Compases 60 a 76: Outro puramente instrumental, desvaneciéndose en el lecho analógico

    # Tratamiento acústico: EMT-140 natural (voz seca, íntima, cercana)
    lead_vocal_stem = create_reverb(lead_vocal_stem, decay_sec=1.8, wet=0.18)

    return lead_vocal_stem


# -----------------------------------------------------------------------------
# MASTERING & EBU R128 NORMALIZATION
# -----------------------------------------------------------------------------
def mix_and_master(stems_dict: dict) -> np.ndarray:
    print("🎛️ Masterizando mezcla continua EBU R128 (-14.0 LUFS, -1.0 dBFS True Peak)...")
    mix = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

    # Lecho analógico de cinta continuo (-56 dBFS)
    noise_raw = np.random.randn(TOTAL_SAMPLES)
    b_tape, a_tape = signal.butter(2, [200.0 / (SR / 2), 3600.0 / (SR / 2)], btype="bandpass")
    tape_hiss = signal.filtfilt(b_tape, a_tape, noise_raw)
    tape_level = 10.0 ** (-56.0 / 20.0)
    tape_bed = np.column_stack([tape_hiss * tape_level * 0.95, tape_hiss * tape_level * 1.05])
    mix += tape_bed

    gains = {
        "01_Sub_Kick.wav": 0.76,
        "02_Breakbeat_Drums.wav": 0.66,
        "03_Sub_Bass.wav": 0.72,
        "04_Atmospheric_Pads.wav": 0.54,
        "05_Rhodes_Textures.wav": 0.46,
        "06_Elon_Musk_Narrative_Vocal.wav": 0.84
    }

    for name, data in stems_dict.items():
        g = gains.get(name, 0.6)
        mix += data * g

    # Sub-rumble high-pass cut at 26 Hz
    b_hp, a_hp = signal.butter(3, 26.0 / (SR / 2), btype="high")
    mix[:, 0] = signal.filtfilt(b_hp, a_hp, mix[:, 0])
    mix[:, 1] = signal.filtfilt(b_hp, a_hp, mix[:, 1])

    # Linkwitz-Riley 4th order crossover at 120 Hz: Mono sub consolidation
    sos_lp = signal.butter(2, 120 / (SR / 2), btype="low", output="sos")
    sub_l = signal.sosfiltfilt(sos_lp, mix[:, 0])
    sub_r = signal.sosfiltfilt(sos_lp, mix[:, 1])
    sub_mono = (sub_l + sub_r) * 0.5

    sos_hp = signal.butter(2, 120 / (SR / 2), btype="high", output="sos")
    high_l = signal.sosfiltfilt(sos_hp, mix[:, 0])
    high_r = signal.sosfiltfilt(sos_hp, mix[:, 1])

    mix = np.column_stack([sub_mono + high_l, sub_mono + high_r])

    # EBU R128 Normalization
    meter = pln.Meter(SR)
    loudness = meter.integrated_loudness(mix)
    print(f"📊 Loudness antes de normalizar: {loudness:.2f} LUFS")

    target_lufs = -14.0
    gain_db = target_lufs - loudness
    linear_gain = 10.0 ** (gain_db / 20.0)
    master = mix * linear_gain

    # Transparent peak limit to -1.0 dBFS
    peak = np.max(np.abs(master))
    if peak > 0.891:
        print(f"⚠️ Limitando picos: {peak:.3f} -> 0.891 (-1.0 dBFS)")
        master = master * (0.891 / peak)

    final_lufs = meter.integrated_loudness(master)
    final_tp = 20 * np.log10(np.max(np.abs(master)) + 1e-9)
    print(f"🏆 Master Final Certificado: {final_lufs:.2f} LUFS | True Peak: {final_tp:.2f} dBFS")

    return master


def main():
    print("=" * 70)
    print("🚀 PRODUCCIÓN CONTINUA AMBIENT BREAKBEAT (NO DROPS / NO HOOKS)")
    print(f"⏱️ 76 Compases @ {BPM} BPM | 48.0 kHz / 24-bit PCM | Duración: 2m 36s")
    print("=" * 70)

    narrative_vocal = load_and_arrange_linear_vocal()

    stems = {
        "01_Sub_Kick.wav": generate_sub_kick(),
        "02_Breakbeat_Drums.wav": generate_breakbeat_drums(),
        "03_Sub_Bass.wav": generate_sub_bass(),
        "04_Atmospheric_Pads.wav": generate_atmospheric_pads(),
        "05_Rhodes_Textures.wav": generate_rhodes_textures(),
        "06_Elon_Musk_Narrative_Vocal.wav": narrative_vocal
    }

    # Clean previous stem files in stems_dir to avoid orphan stems
    for old_f in STEMS_DIR.glob("*.wav"):
        old_f.unlink()

    # Save individual stems
    print("💾 Guardando 6 Stems WAV multitrack en:", STEMS_DIR)
    for stem_name, stem_data in stems.items():
        out_path = STEMS_DIR / stem_name
        sf.write(str(out_path), stem_data, SR, subtype="PCM_24")

    # Master render
    master = mix_and_master(stems)
    sf.write(str(MASTER_WAV), master, SR, subtype="PCM_24")
    print(f"📀 Master WAV generado: {MASTER_WAV}")

    # Generate MP3
    cmd_mp3 = ["ffmpeg", "-y", "-i", str(MASTER_WAV), "-b:a", "320k", str(MASTER_MP3)]
    subprocess.run(cmd_mp3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"📱 Master MP3 generado: {MASTER_MP3}")

    # Compile Native FLP
    print("🎛️ Compilando archivo de sesión nativo .flp para FL Studio 2025...")
    staging = {
        "01_Sub_Kick.wav": {"mixer_track": 1, "volume": 100},
        "02_Breakbeat_Drums.wav": {"mixer_track": 2, "volume": 90},
        "03_Sub_Bass.wav": {"mixer_track": 3, "volume": 95},
        "04_Atmospheric_Pads.wav": {"mixer_track": 4, "volume": 85},
        "05_Rhodes_Textures.wav": {"mixer_track": 5, "volume": 80},
        "06_Elon_Musk_Narrative_Vocal.wav": {"mixer_track": 6, "volume": 105}
    }
    flp_res = compile_multitrack_stems_flp(
        stems_dir=str(STEMS_DIR),
        project_title="Elon Musk - Late Night Interview (Ambient Breakbeat 117 BPM)",
        bpm=BPM,
        output_flp=str(OUTPUT_FLP),
        total_bars=BARS,
        channel_staging=staging
    )
    print(f"✅ Sesión FL Studio compilada: {OUTPUT_FLP}")
    print(json.dumps(flp_res, indent=2))


if __name__ == "__main__":
    main()
