#!/usr/bin/env python3
import asyncio, os, subprocess
import soundfile as sf
import numpy as np
import scipy.signal as signal
import edge_tts

OUT_DIR = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ceutong_audio"
os.makedirs(OUT_DIR, exist_ok=True)

async def synthesize_all():
    print("=== [1/5] SINTETIZANDO VOCES NEURALES SOTA (EDGE-TTS) ===")
    
    # 1. BORJA MOSKV (BILBAO VISIONARIO)
    t_borja = "¡A ver chavales, escuchadme bien! Lo de Ceuta amurallada es una ruina de cojones. ¡Hay que hacer CEUTONG! Desacoplamos la soberanía funcional, metemos un Hong Kong al cero por ciento de impuestos con Tetuán, y en diez años los rascacielos tapan el Peñón de Gibraltar, ¡hostia!"
    f_borja = os.path.join(OUT_DIR, "borja_ceutong_pitch.wav")
    c1 = edge_tts.Communicate(t_borja, "es-ES-AlvaroNeural", rate="+9%", pitch="+2Hz")
    tmp_b = "/tmp/borja_raw.mp3"
    await c1.save(tmp_b)
    # Convert to 44.1k wav with radio broadcast EQ
    cmd_b = ["ffmpeg", "-y", "-i", tmp_b, "-af", "equalizer=f=3500:t=q:w=1.2:g=3.5,loudnorm=I=-16:TP=-1.0:LRA=8", "-ar", "44100", f_borja]
    subprocess.run(cmd_b, check=True)
    print("✓ Borja Moskv generado con éxito.")

    # 2. MITXU (BILBAO TRINCHERA / PARKING CEUTA)
    t_mitxu = "¡Pero qué me estás contando, Borja! ¡La virgen! Si en Ceuta lo único que hay es el parking de los ferrys y viento de levante. ¡Como montes un Hong Kong ahí, a la que te descuides te ponen una gilda de cinco pisos y a cobrar el txakoli a diez euros!"
    f_mitxu = os.path.join(OUT_DIR, "mitxu_ceutong_rant.wav")
    c2 = edge_tts.Communicate(t_mitxu, "es-ES-AlvaroNeural", rate="+14%", pitch="-3Hz")
    tmp_m = "/tmp/mitxu_raw.mp3"
    await c2.save(tmp_m)
    cmd_m = ["ffmpeg", "-y", "-i", tmp_m, "-af", "equalizer=f=300:t=q:w=1.0:g=2,equalizer=f=4000:t=q:w=1.5:g=3,loudnorm=I=-16:TP=-1.0:LRA=8", "-ar", "44100", f_mitxu]
    subprocess.run(cmd_m, check=True)
    print("✓ Mitxu generado con éxito.")

    # 3. ALAIN ELECTRO (NEXUS // NEGOCIODAD)
    t_alain = "Negociodad : Ceutong. Y Villa Melilla, Ciudad Vacacional. ¡Esto lo petamos seguro con dos txakolis en el helipuerto!"
    f_alain = os.path.join(OUT_DIR, "alain_negociodad.wav")
    c3 = edge_tts.Communicate(t_alain, "es-ES-AlvaroNeural", rate="+7%", pitch="+4Hz")
    tmp_a = "/tmp/alain_raw.mp3"
    await c3.save(tmp_a)
    cmd_a = ["ffmpeg", "-y", "-i", tmp_a, "-af", "loudnorm=I=-16:TP=-1.0:LRA=8", "-ar", "44100", f_alain]
    subprocess.run(cmd_a, check=True)
    print("✓ Alain Electro generado con éxito.")

    # 4. ECHENIQUE CYBER-RACER (ROSARINO // ROBOTIC VOCODER TUNING)
    t_ech = "Compañeros... la plusvalía termodinámica de Ceutong es científicamente irrebatible. Pero por favor, asfaltad bien la recta del casino que a esta silla con alerón y leds le va a dar una taquicardia cuántica a ciento ochenta por hora."
    tmp_e = "/tmp/ech_raw.mp3"
    c4 = edge_tts.Communicate(t_ech, "es-AR-TomasNeural", rate="+3%", pitch="-1Hz")
    await c4.save(tmp_e)
    
    # Read and apply cyber vocoder ring-modulator
    d_e, sr_e = sf.read(tmp_e)
    if len(d_e.shape) > 1:
        d_e = d_e[:, 0]
    t = np.arange(len(d_e)) / sr_e
    ring = 0.72 + 0.28 * np.sin(2 * np.pi * 75.0 * t)
    d_e_rob = d_e * ring
    # metallic delay
    del_s = int(0.015 * sr_e)
    d_e_rob[del_s:] += 0.35 * d_e[:-del_s]
    d_e_rob = d_e_rob / np.max(np.abs(d_e_rob)) * 0.95
    f_ech = os.path.join(OUT_DIR, "echenique_cyber.wav")
    sf.write(f_ech, d_e_rob, sr_e)
    print("✓ Echenique Cyber-Racer generado con éxito.")

    # 5. MACGYVER (ACCIÓN 80s // BRICOLAJE HEROICO)
    t_mac = "Tranquilos todos. Con un clip de oficina, un chicle de fresa y dos botellas de txakoli he hackeado la aduana del Estrecho. ¡Ceutong está al cien por cien de exergía!"
    f_mac = os.path.join(OUT_DIR, "macgyver_hero.wav")
    tmp_mc = "/tmp/mac_raw.mp3"
    c5 = edge_tts.Communicate(t_mac, "es-ES-AlvaroNeural", rate="+4%", pitch="-5Hz")
    await c5.save(tmp_mc)
    cmd_mc = ["ffmpeg", "-y", "-i", tmp_mc, "-af", "equalizer=f=3500:t=q:w=1:g=3.5,aecho=0.8:0.5:30:0.25,loudnorm=I=-16:TP=-1.0:LRA=8", "-ar", "44100", f_mac]
    subprocess.run(cmd_mc, check=True)
    print("✓ MacGyver generado con éxito.")

    # 6. BORJA DROP CALL
    t_drop = "¡Pues que empiece la fiesta en el helipuerto de Ceutong! ¡Soltad los bombos a cien BPMs!"
    f_bdrop = os.path.join(OUT_DIR, "borja_drop_intro.wav")
    tmp_bd = "/tmp/borja_drop_raw.mp3"
    c6 = edge_tts.Communicate(t_drop, "es-ES-AlvaroNeural", rate="+11%", pitch="+3Hz")
    await c6.save(tmp_bd)
    cmd_bd = ["ffmpeg", "-y", "-i", tmp_bd, "-af", "loudnorm=I=-15:TP=-1.0:LRA=7", "-ar", "44100", f_bdrop]
    subprocess.run(cmd_bd, check=True)
    print("✓ Borja drop intro generado con éxito.")

asyncio.run(synthesize_all())
print("\n=== TODAS LAS VOCES SOTA HAN SIDO GENERADAS Y MASTERIZADAS CON ÉXITO ===")
