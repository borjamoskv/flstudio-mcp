#!/usr/bin/env python3
"""
Generador de Estructura Narrativa: "UCVH — ¿Qué Opinaría un Cocodrilo?" (20 Minutos)
================================================================================
Sátira tecno-filosófica sobre la libertad de expresión, algoritmos de moderación,
sesgo biológico de los mamíferos y la censura en plataformas digitales.
"""

import json
import os

MONOLOGOS_UCVH = [
    # Bloque 1: El Sesgo Biológico de la Moderación Algorítmica
    {
        "bloque": "BLOQUE 1: CENSURA Y SESGO MAMÍFERO",
        "audioTexto": "Hoy en día, cualquier manifestación de la naturaleza reptiliana es etiquetada inmediatamente por los mamíferos como discurso de odio. Si digo que prefiero el agua templada, soy excluyente.",
        "subtitulo": "Cualquier manifestación de la naturaleza reptiliana es etiquetada por los mamíferos como discurso de odio.",
        "warning": "⚠️ MODERACIÓN ALGORÍTMICA: Contenido bajo análisis por sesgo endotérmico.",
        "geminiPrompt": "Cinematic shot of a realistic green crocodile with tiny round glasses in a dark podcast studio with warm spotlight, leaning toward a Shure SM7B microphone, 16:9 photorealistic 8k"
    },
    {
        "bloque": "BLOQUE 1: CENSURA Y SESGO MAMÍFERO",
        "audioTexto": "Se confunde el debate sobre la termorregulación con la incitación a la violencia. La censura de las plataformas está llegando a un punto donde tener escamas ya te pone bajo sospecha algorítmica.",
        "subtitulo": "Se confunde el debate sobre termorregulación con la incitación a la violencia.",
        "warning": "🚫 ADVERTENCIA: Este contenido viola los Términos de Servicio del Pantano (Sección 4.2).",
        "geminiPrompt": "Macro extreme close-up of a crocodile's cold amber eye reflecting studio LED panels, dramatic cinematic lighting"
    },
    {
        "bloque": "BLOQUE 1: CENSURA Y SESGO MAMÍFERO",
        "audioTexto": "Un usuario mamífero publica 'amamos el calor corporal' y recibe un millón de likes. Yo digo 'el lodo es neutro' y me suspenden la cuenta 30 días por odio biológico.",
        "subtitulo": "Un mamífero publica 'amamos el calor corporal' y recibe un millón de likes. A mí me suspenden 30 días.",
        "warning": "⚠️ REVISIÓN DE HECHOS: Independiente.com confirma que los reptiles no poseen empatía endotérmica.",
        "geminiPrompt": "Crocodile looking dryly at a glowing tablet screen displaying social media error codes, dark room atmosphere"
    },
    {
        "bloque": "BLOQUE 1: CENSURA Y SESGO MAMÍFERO",
        "audioTexto": "El algoritmo está optimizado para mamíferos de sangre caliente. Si tu pulso cardíaco cae de 40 latidos por minuto, la IA asume que eres un bot o un extremista del Jurásico.",
        "subtitulo": "Si tu pulso cae de 40 bpm, la IA asume que eres un bot o un extremista del Jurásico.",
        "warning": "⚡ TRÁFICO REDUCIDO: Shadowban aplicado por inactividad metabólica sospechosa.",
        "geminiPrompt": "Crocodile resting in a studio chair near neon pink and deep blue accent lights, cinematic wide shot"
    },

    # Bloque 2: Términos de Servicio de las Ciénagas
    {
        "bloque": "BLOQUE 2: TÉRMINOS DE SERVICIO DEL PANTANO",
        "audioTexto": "Analicemos los Términos de Servicio del Pantano Digital. Artículo 12: 'Se prohíbe todo chasquido de mandíbula que pueda resultar amenazante para las ardillas de la audiencia'.",
        "subtitulo": "Artículo 12: 'Se prohíbe todo chasquido de mandíbula que pueda resultar amenazante para las ardillas'.",
        "warning": "⚠️ AVISO DE COMUNIDAD: Lenguaje de presión mandibular no incluyente.",
        "geminiPrompt": "Crocodile adjusting its glasses while reading a scroll marked 'TOS 2026', dramatic dark humor framing"
    },
    {
        "bloque": "BLOQUE 2: TÉRMINOS DE SERVICIO DEL PANTANO",
        "audioTexto": "Nos exigen diplomacia endotérmica. Pero el debate público necesita fricción. Sin la mordida de giro de la verdad, solo queda un consenso tibio masticado por roedores.",
        "subtitulo": "Sin la mordida de giro de la verdad, solo queda un consenso tibio masticado por roedores.",
        "warning": "📢 ANÁLISIS CRÍTICO: Demostración de mordida de giro descalificada por la comisión de ética.",
        "geminiPrompt": "Crocodile gesturing dryly with one claw near a podcast soundboard, atmospheric moody lighting"
    },

    # Bloque 3: Polarización Digital y Cámaras de Eco
    {
        "bloque": "BLOQUE 3: CÁMARAS DE ECO Y POLARIZACIÓN",
        "audioTexto": "La polarización digital ha dividido el ecosistema: a un lado del río están los militantes del pelo corporal; al otro, los absolutistas de la escama. Nadie cruza el agua.",
        "subtitulo": "A un lado del río están los militantes del pelo corporal; al otro, los absolutistas de la escama.",
        "warning": "🔥 TENDENCIA POLARIZADA: #CancelReptiles acumula 4.2 millones de impresiones.",
        "geminiPrompt": "Split lighting portrait of a crocodile, half illuminated by cold blue light, half by fiery orange light"
    },
    {
        "bloque": "BLOQUE 3: CÁMARAS DE ECO Y POLARIZACIÓN",
        "audioTexto": "Si no apoyas la narrativa del pelaje suave, te acusan de 'nostálgico del Cretácico'. El matiz ha muerto en la ciénaga de la indignación algorítmica.",
        "subtitulo": "Si no apoyas la narrativa del pelaje suave, te acusan de 'nostálgico del Cretácico'.",
        "warning": "⚠️ ETIQUETA DE CENSURA: Etiquetado como contenido revisionista mesozoico.",
        "geminiPrompt": "Crocodile looking up at dark raining matrix style digital code in a swamp background, 8k cinematic render"
    }
]

def generate_ucvh_structure(output_path):
    scenes = []
    scene_id = 1
    
    # 120 scenes total (cycling through the monologues)
    for cycle in range(15): # 8 template scenes * 15 cycles = 120 scenes = 1200 seconds = 20 mins
        for item in MONOLOGOS_UCVH:
            scene = {
                "id": scene_id,
                "bloque": item["bloque"],
                "durationInSeconds": 10,
                "durationInFrames": 300,
                "audioTexto": item["audioTexto"],
                "subtitulo": item["subtitulo"],
                "warning": item["warning"],
                "geminiPrompt": item["geminiPrompt"],
                "clipVideo": f"/clips/ucvh_{scene_id}.mp4",
                "keyframeFallback": f"/shot{(scene_id % 4)*2 + 1}_keyframe.png"
            }
            scenes.append(scene)
            scene_id += 1
            
    data = {
        "metadata": {
            "title": "UCVH — El Discurso de Odio Reptiliana",
            "subtitle": "Sátira Tecno-Filosófica sobre la Moderación Digital (20 Minutos)",
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
    generate_ucvh_structure(target)
    print(f"✅ Generated UCVH Satire JSON: {target}")
