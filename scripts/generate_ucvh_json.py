#!/usr/bin/env python3
"""
Generador de Estructura Narrativa UCVH — El Falso Podcast (20 Minutos)
========================================================================
Sátira tecno-filosófica minimalista sin música, con cadencia seca,
pausas de respiración (silenceDuration) y plano medio continuo de estudio.
"""

import json
import os

PODCAST_SCENES = [
    {
        "audioTexto": "Hoy en día, cualquier manifestación de la naturaleza reptiliana es etiquetada inmediatamente por los mamíferos como discurso de odio. Si digo que prefiero el agua templada, soy excluyente.",
        "subtitulo": "Cualquier manifestación de la naturaleza reptiliana es etiquetada por los mamíferos como discurso de odio.",
        "silenceDuration": 800,
        "geminiPrompt": "Static medium shot of a realistic green crocodile sitting in a dark, empty podcast studio. Soft gray background, no distractions. A professional Shure SM7B microphone is fixed right in front of its mouth. The crocodile talks with subtle, serious lip and eye movements, looking strictly at the camera. Photorealistic, raw podcast aesthetics, 16:9"
    },
    {
        "audioTexto": "Se confunde el debate sobre la termorregulación con la incitación a la violencia. La censura de las plataformas está llegando a un punto donde tener escamas ya te pone bajo sospecha algorítmica.",
        "subtitulo": "Se confunde el debate sobre la termorregulación con la incitación a la violencia.",
        "silenceDuration": 1200,
        "geminiPrompt": "Static medium shot of a realistic green crocodile in a dark podcast studio, subtle stern expression, Shure SM7B microphone fixed in front, raw podcast lighting, photorealistic 16:9"
    },
    {
        "audioTexto": "Yo defiendo que cualquier animal pueda rugir lo que quiera en la selva. El libre mercado de las ideas. Pero si una nutria hace un meme de mis escamas, le meto una demanda por el código civil de la fauna.",
        "subtitulo": "Defiendo el rugido libre... hasta que una nutria me hace un meme.",
        "silenceDuration": 900,
        "geminiPrompt": "Static medium shot of a realistic green crocodile podcaster looking protective and stern, black rectangular glasses, dark empty studio, photorealistic 16:9"
    },
    {
        "audioTexto": "Condeno la cultura de la cancelación de los mamíferos. Sin embargo, si un castor critica mi tono en un videoensayo, exijo la clausura cautelar inmediata de su presa por difamación institucional.",
        "subtitulo": "Condeno la cancelación mamífera... pero exijo clausurar la presa del castor por difamación.",
        "silenceDuration": 1000,
        "geminiPrompt": "Static medium shot of a realistic green crocodile looking analytical, Shure SM7B microphone, dark quiet podcast studio, 16:9 photorealistic"
    },
    {
        "audioTexto": "Dicen que soy un activista del fango, pero yo solo leo datos. Que el noventa por ciento de las cebras mueran a manos de leones no es un problema sistémico felino, es pura biología matemática.",
        "subtitulo": "Yo solo leo datos... no es un problema sistémico felino, es pura biología matemática.",
        "silenceDuration": 1100,
        "geminiPrompt": "Static medium shot of a realistic green crocodile podcaster pointing a scaly claw slightly upward, dry analytical expression, dark studio background, 16:9"
    },
    {
        "audioTexto": "Miren mi estética: tono pausado, gafas de lectura, micrófono Shure SM7B y luz azul de estudio. Es imposible que alguien con este setup sea un agitador ideológico. Es simple ciencia computacional.",
        "subtitulo": "Micrófono Shure SM7B y luz azul de estudio... es imposible que alguien con este setup sea un agitador.",
        "silenceDuration": 850,
        "geminiPrompt": "Static medium shot of a realistic green crocodile looking directly into camera with black rectangular glasses, quiet podcast atmosphere, 16:9 photorealistic"
    }
]

def generate_podcast_json(output_path):
    scenes = []
    scene_id = 1
    
    # 120 scenes total = 1200 seconds = 20 mins
    for cycle in range(20):
        for item in PODCAST_SCENES:
            scene = {
                "id": scene_id,
                "durationInSeconds": 10,
                "durationInFrames": 300, # 10s @ 30fps
                "audioTexto": item["audioTexto"],
                "subtitulo": item["subtitulo"],
                "silenceDuration": item["silenceDuration"],
                "geminiPrompt": item["geminiPrompt"],
                "clipVideo": f"/clips/ucvh_{scene_id}.mp4",
                "audioSpeech": f"/audios/ucvh_voz_{scene_id}.mp3",
                "keyframeFallback": f"/shot1_keyframe.png"
            }
            scenes.append(scene)
            scene_id += 1

    data = {
        "metadata": {
            "title": "UCVH: El Falso Podcast",
            "subtitle": "Monólogo Seco y Analítico (20 Minutos - Sin Música)",
            "format": "Raw Minimalist Podcast",
            "totalScenes": len(scenes),
            "totalDurationSeconds": len(scenes) * 10,
            "totalDurationFrames": len(scenes) * 300,
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
    out_file = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/ucvh_podcast.json"
    generate_podcast_json(out_file)
    print(f"✅ Generated UCVH Falso Podcast JSON: {out_file}")
