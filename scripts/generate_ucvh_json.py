#!/usr/bin/env python3
"""
Generador de Estructura Narrativa UCVH v2.0
===========================================
Sátira tecno-filosófica de 20 Minutos (120 escenas) basada en los dos ejes estructurales:
1. Libertad de Expresión Absoluta vs. Demandas a Nutrias por Memes.
2. Objetividad del 'Analista de Datos' vs. Activismo de Trinchera del Fango.
"""

import json
import os

BLOQUES_UCVH = [
    # Eje 1: La Paradoja de la Libertad de Expresión vs. Demandas Judiciales a la Fauna
    {
        "bloque": "EJE 1: LIBERTAD DE LIBRE RUGIDO VS. LA VÍA JUDICIAL",
        "audioTexto": "Yo defiendo que cualquier animal pueda rugir lo que quiera en la selva. El libre mercado de las ideas. Pero si una nutria hace un meme de mis escamas, le meto una demanda por el código civil de la fauna.",
        "subtitulo": "Defiendo el rugido libre... hasta que una nutria me hace un meme.",
        "warning": "⚖️ QUERELLA EN CURSO: Demanda interpuesta a Nutria_Satírica_99 por vulneración del derecho al honor reptiliano.",
        "chartData": {"title": "Estadística de Demandas Judiciales por Memes", "stat": "+450% Querellas en Pantanos"},
        "geminiPrompt": "A green crocodile podcaster looking very stern and protective, adjusting its microphone in a dark studio. Sharp look. 16:9 aspect ratio."
    },
    {
        "bloque": "EJE 1: LIBERTAD DE LIBRE RUGIDO VS. LA VÍA JUDICIAL",
        "audioTexto": "Condeno severamente la cultura de la cancelación de los mamíferos. Sin embargo, si un castor critica mi tono en un videoensayo, exijo la clausura inmediata de su presa por difamación institucional.",
        "subtitulo": "Condeno la cancelación mamífera... pero exijo clausurar la presa del castor por difamación.",
        "warning": "🚫 ORDEN JUDICIAL CAUTELAR: Bloqueo de presa y embargo preventivo de madera.",
        "chartData": {"title": "Presas Clausuradas por Orden Tribunal Mammalia", "stat": "127 Presas Embargadas"},
        "geminiPrompt": "Crocodile looking dryly at a stack of legal subpoenas on a mahogany desk, dark podcast room, cinematic light"
    },

    # Eje 2: Objetividad del Analista Neutral vs. Activismo de Trinchera
    {
        "bloque": "EJE 2: ANALISTA NEUTRAL VS. ACTIVISMO DEL FANGO",
        "audioTexto": "Dicen que soy un activista del fango, pero yo solo leo datos. Que el noventa por ciento de las cebras mueran a manos de leones no es un problema sistémico de los felinos, es pura biología matemática.",
        "subtitulo": "Yo solo leo datos... no es un problema sistémico felino, es pura biología matemática.",
        "warning": "📊 ESTUDIO FACT-CHECK: Estadística validada por el Instituto de Biología Cuantitativa de los Pantanos.",
        "chartData": {"title": "Mortalidad de Cebras vs Felinos", "stat": "90.4% Biología Matemática"},
        "geminiPrompt": "Close up of the crocodile pointing at a glowing holographic bar chart on screen with an analytical expression. 16:9 aspect ratio."
    },
    {
        "bloque": "EJE 2: ANALISTA NEUTRAL VS. ACTIVISMO DEL FANGO",
        "audioTexto": "Miren mi estética: tono pausado, gafas de lectura, micrófono Shure SM7B y luz azul de estudio. Es imposible que alguien con este setup sea un agitador ideológico. Es simple ciencia computacional.",
        "subtitulo": "Micrófono Shure SM7B y luz azul de estudio... es imposible que alguien con este setup sea un agitador.",
        "warning": "🎙️ NEUTRALIDAD DE SETUP: Certificado de Analista Objetivo 100% Neón.",
        "chartData": {"title": "Índice de Percepción de Objetividad por Setup", "stat": "99.8% Tono Pausado"},
        "geminiPrompt": "Crocodile sitting in a high-tech studio with glowing LED bar charts floating in air, professional video essayist aesthetic"
    },

    # Eje 3: Términos de Servicio y Algoritmos del Pantano
    {
        "bloque": "EJE 3: CENSURA ALGORÍTMICA DE LAS PLATAFORMAS",
        "audioTexto": "El algoritmo favorece al pelaje suave porque genera más clics por empatía endotérmica. A los que tenemos sangre fría nos aplican shadowban sistemático por baja tasa de pulso cardíaco.",
        "subtitulo": "El algoritmo favorece al pelaje suave. A los de sangre fría nos aplican shadowban por baja tasa de pulso.",
        "warning": "⚡ RESTRICCIÓN DE ALGORITMO: Shadowban por inactividad metabólica sospechosa.",
        "chartData": {"title": "Alcance Algorítmico: Sangre Caliente vs Sangre Fría", "stat": "-78% Impr. Reptiles"},
        "geminiPrompt": "Crocodile staring intensely at a laptop screen displaying red declining analytics charts, dark moody background"
    },

    # Eje 4: La Paradoja de la Termorregulación
    {
        "bloque": "EJE 4: DEBATE SOBRE TERMORREGULACIÓN",
        "audioTexto": "Se confunde el debate de la termorregulación con la incitación a la violencia. Si digo que prefiero el lodo tibio a 32 grados, las ardillas del chat me acusan de supremacismo ectotérmico.",
        "subtitulo": "Si digo que prefiero el lodo a 32 grados, me acusan de supremacismo ectotérmico.",
        "warning": "⚠️ AUDITORÍA DE CHAT: 4,000 comentarios marcados por incitación a la temperatura.",
        "chartData": {"title": "Temperatura Óptima del Lodo", "stat": "32.5°C Ectotermia Neutra"},
        "geminiPrompt": "Macro shot of crocodile eyes reflecting green matrix code while floating in shallow warm mud"
    }
]

def generate_ucvh_v2_structure(output_path):
    scenes = []
    scene_id = 1
    
    # Generate 120 total scenes (cycling through the 6 core template scenes)
    for cycle in range(20): # 6 scenes * 20 cycles = 120 scenes = 20 mins
        for item in BLOQUES_UCVH:
            scene = {
                "id": scene_id,
                "bloque": item["bloque"],
                "durationInSeconds": 10,
                "durationInFrames": 300,
                "audioTexto": item["audioTexto"],
                "subtitulo": item["subtitulo"],
                "warning": item["warning"],
                "chartData": item["chartData"],
                "geminiPrompt": item["geminiPrompt"],
                "clipVideo": f"/clips/ucvh_{scene_id}.mp4",
                "keyframeFallback": f"/shot{(scene_id % 4)*2 + 1}_keyframe.png"
            }
            scenes.append(scene)
            scene_id += 1
            
    data = {
        "metadata": {
            "title": "UCVH — La Paradoja del Discurso Reptiliano",
            "subtitle": "Sátira Tecno-Filosófica sobre la Libertad de Expresión y la Vía Judicial (20 Minutos)",
            "totalScenes": len(scenes),
            "totalDurationSeconds": len(scenes) * 10, # 1200s
            "totalDurationFrames": len(scenes) * 300, # 36000 frames
            "fps": 30,
            "width": 1920,
            "height": 1080
        },
        "scenes": scenes
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    return output_path

if __name__ == "__main__":
    target = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ucvh_odio.json"
    generate_ucvh_v2_structure(target)
    print(f"✅ Generated UCVH v2.0 JSON dataset: {target}")
