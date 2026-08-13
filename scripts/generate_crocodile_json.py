#!/usr/bin/env python3
"""
Generador de Estructura Narrativa: "¿Qué opinaría un cocodrilo?" (20 Minutos)
==========================================================================
Genera 120 escenas de 10 segundos (300 frames a 30fps = 1200s total)
con monólogos humorístico-filosóficos de un cocodrilo sobre la humanidad.
"""

import json
import os

TEMAS = [
    {
        "bloque": "1. Zapatos y Bolsos de Piel",
        "subtitulos": [
            "¿Piel sintética? Por favor. Si me vas a usar de bolso, al menos asegúrate de que sea alta costura.",
            "Ven un par de zapatos y dicen '¡es elegante!'. Yo veo a mi primo Ernesto convertido en mocasín.",
            "La próxima vez que alguien lleve una correa de reloj de cocodrilo, le pediré la hora cada dos minutos.",
            "Tienen la audacia de llamarlo 'marroquinería fina'. Nosotros lo llamamos 'secuestro de vestuario'.",
            "¿Por qué nunca hacen zapatos de piel de humano? Tienen una textura bastante maleable, piénsenlo.",
            "Si un cocodrilo entra a una tienda Gucci, ¿cuenta como visita familiar o como inspección de trabajo?",
            "Nosotros estuvimos aquí antes de la moda. Sobrevivimos al meteorito, pero casi no sobrevivimos a los bolsos.",
            "Dicen 'resistente al agua'. ¡Claro que es resistente al agua, imbécil, nadaba en el Nilo!",
            "Un respeto a la piel escamada. Llevó 200 millones de años de evolución perfeccionar este tono oliva.",
            "Si ven a alguien con botas de cocodrilo en el pantano, el reembolso es inmediato y sin recibo."
        ],
        "prompts": [
            "Cinematic close up of a sarcastic hyperrealistic crocodile wearing tiny round glasses, sitting in a swamp, photorealistic 8k",
            "A crocodile looking judgingly at a pair of leather shoes left by a riverbank, dark comedy atmosphere",
            "Crocodile pointing its snout at a wristwatch, dramatic lighting, high detail nature documentary style",
            "Crocodile sitting in a luxury fashion boutique surrounded by handbags, surreal dark humor style",
            "Close up of crocodile skin texture under golden hour lighting, hyper-detailed render",
            "A crocodile walking into a high-end store looking shocked, cinematic camera angle",
            "Prehistoric crocodile side-by-side with a modern luxury handbag, humorous contrast lighting",
            "Crocodile splashing water dramatically with a smug facial expression, 4k ultra detailed",
            "Detailed macro shot of green scales shimmering with morning dew, 35mm lens",
            "Crocodile lurking underwater with eyes right above the surface, menacing yet funny optics"
        ]
    },
    {
        "bloque": "2. Los Humanos en los Zoológicos",
        "subtitulos": [
            "Ustedes pagan entrada para verme dormir 8 horas. El verdadero estafador soy yo.",
            "Golpean el cristal y gritan '¡haz algo!'. Hermano, estoy haciendo la digestión, respeta mi proceso.",
            "Me tiran monedas a la charca. No tengo bolsillos, ¿qué se supone que compre con esto?",
            "La gente me mira y dice '¡mira qué verde!'. Y yo los miro y pienso '¡mira qué comestible!'.",
            "El guardia cree que me tiene encerrado. Yo creo que tengo 500 humanos en exhibición al día.",
            "Hacen 'ja ja' cuando abro la boca. Si no hubiera este vidrio de 10 cm, estarías haciendo 'ay ay'.",
            "Los niños me tiran palomitas. Aprecio el gesto, pero prefiero la pierna del tipo de los helados.",
            "Un selfie con la boca abierta. La falta de instinto de supervivencia en su especie es fascinante.",
            "Me ponen un cartel de 'Peligro'. Deberían ponerle 'Peligro' al precio del café de la cafetería.",
            "El clima en el zoo es agradable, pero la conversación del público deja mucho que desear."
        ],
        "prompts": [
            "Crocodile looking through a thick zoo glass panel at confused human tourists, cinematic perspective",
            "Crocodile relaxing in a sunlit pool with eyes half closed, peaceful yet slightly smug expression",
            "Shiny coins sitting at the bottom of a muddy pond near a giant crocodile snout, detailed shot",
            "Crocodile evaluating humans walking past its enclosure, dramatic documentary style",
            "Wide shot of a zoo enclosure with a majestic crocodile in the center acting like the boss",
            "Crocodile opening its huge jaw near the glass window, shocked tourist reflections on glass",
            "Popcorn floating on water surface while a huge crocodile stares with mild amusement",
            "A tourist taking a selfie in front of a crocodile glass exhibit, funny cinematic lighting",
            "Close up of a yellow 'DANGER' sign next to a sleeping crocodile in a lush exhibit",
            "Crocodile soaking under a heat lamp looking like a spa guest, funny photorealistic render"
        ]
    },
    {
        "bloque": "3. Dinosaurios y Evolución",
        "subtitulos": [
            "Los T-Rex se extinguieron porque tenían los brazos cortos para aplaudir mi grandeza.",
            "200 millones de años sin cambiar de diseño. Si algo funciona, no lo actualices.",
            "Los mamíferos creen que inventaron la inteligencia. Nosotros inventamos la paciencia suprema.",
            "El meteorito cayó y dijo: 'apagar todo'. Nosotros dijimos: 'no, nosotros nos quedamos'.",
            "Tienen teléfonos plegables. Nosotros tenemos mandíbulas plegables desde el Jurásico.",
            "Las aves dicen ser los descendientes de los dinosaurios. Por favor, miren a una gallina y mirenme a mí.",
            "La evolución nos dio acorazado natural, visión nocturna y potencia de mordida. ¿A ustedes? Ansiedad.",
            "No necesitamos fuego para cocinar. El estomago de un reptil disuelve hasta las indirectas.",
            "El secreto de la longevidad es simple: no tener reuniones de Zoom y tomar sol todo el día.",
            "Cuando me preguntan por mis ancestros, les muestro fósiles y sonrío con mis 80 dientes."
        ],
        "prompts": [
            "A crocodile standing next to a museum T-Rex skeleton with a proud posture, dramatic museum light",
            "Ancient primordial swamp with giant prehistoric crocodiles, cinematic epic atmosphere",
            "Crocodile staring thoughtfully at a modern smartphone dropped in the mud, humorous concept",
            "Giant meteor hitting earth in background while a crocodile nonchalantly swims in a river",
            "Crocodile flexing its jaw strength in slow motion, cinematic nature film camera angle",
            "A tiny chicken standing next to a huge crocodile, funny evolutionary comparison",
            "Crocodile glowing with an futuristic armor aesthetic under dark moonlight, hyperrealistic",
            "Crocodile resting near ancient mossy rocks, ancient timeless look, 8k documentary style",
            "Crocodile sunbathing on a warm rock with total tranquility, golden hour natural light",
            "Detailed portrait of a crocodile smiling with rows of sharp white teeth, bright cinematic light"
        ]
    },
    {
        "bloque": "4. Filosofía del Pantano y la Vida Humana",
        "subtitulos": [
            "Tienen lavadoras, hipotecas y tráfico. Nosotros tenemos barro tibio y paz mental.",
            "La gente corre para hacer ejercicio. Yo floto durante 6 horas y mantengo la línea perfecta.",
            "¿Estrés laboral? Mi única tarea del día es decidir en qué lado del tronco me da mejor el sol.",
            "Tratan de descifrar el sentido de la vida. El sentido de la vida es: tragar y flotar.",
            "Dicen que los cocodrilos lloran lágrimas falsas. No son falsas, me da pena lo duro que trabajan.",
            "Un humano paga un spa por un baño de lodo. Yo vivo en uno de 50 hectáreas completamente gratis.",
            "No necesito redes sociales para que todos sepan que soy un depredador alfa.",
            "La serenidad no es yoga. La serenidad es no parpadear en 45 minutos mientras observas a una presa.",
            "Al final del día, todos somos materia orgánica. La diferencia es quién está arriba en la cadena.",
            "Si la vida te da limones, cámbiados por una presa gorda en el agua somera."
        ],
        "prompts": [
            "Crocodile resting in warm mud with a relaxed peaceful vibe, beautiful golden light",
            "Crocodile floating weightlessly in crystal clear tropical water, bottom angle shot",
            "Crocodile lounging lazily on a fallen tree trunk in a misty jungle river, atmospheric 8k",
            "Surreal image of a crocodile sitting on a leather sofa in the middle of a swamp, funny concept",
            "Macro portrait of a crocodile with a single glistening water tear, dramatic cinematic studio light",
            "Crocodile relaxing in a muddy natural hot spring like a resort guest, photorealistic render",
            "Crocodile looking up at the night sky full of stars, deep philosophical atmosphere",
            "Crocodile sitting motionless in shallow water perfectly camouflaged, sharp focus",
            "Crocodile silhouetted against a massive sunset over a calm river, cinematic masterpiece",
            "Crocodile catching a fish with precision in mid-air splash, action camera shot"
        ]
    }
]

def generate_full_structure(output_path):
    scenes = []
    scene_id = 1
    
    # Generate 120 total scenes (cycling through the 4 blocks of topics)
    for cycle in range(3): # 4 blocks * 10 quotes = 40 scenes per cycle * 3 = 120 scenes
        for tema in TEMAS:
            bloque_nombre = tema["bloque"]
            for idx in range(len(tema["subtitulos"])):
                sub = tema["subtitulos"][idx]
                prompt = tema["prompts"][idx]
                
                scene = {
                    "id": scene_id,
                    "bloque": bloque_nombre,
                    "durationInSeconds": 10,
                    "durationInFrames": 300, # 10s @ 30fps
                    "audioTexto": sub,
                    "subtitulo": sub,
                    "geminiPrompt": f"{prompt}, highly detailed, cinematic 4k render",
                    "clipVideo": f"/clips/cocodrilo_{scene_id}.mp4",
                    "keyframeFallback": f"/shot{(scene_id % 4)*2 + 1}_keyframe.png"
                }
                scenes.append(scene)
                scene_id += 1
                
    data = {
        "metadata": {
            "title": "¿Qué opinaría un cocodrilo?",
            "subtitle": "Monólogo Filosófico-Humorístico de 20 Minutos",
            "totalScenes": len(scenes),
            "totalDurationSeconds": len(scenes) * 10, # 1200s = 20 mins
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
    target = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/cocodrilo_estructura.json"
    generate_full_structure(target)
    print(f"✅ Generated 120-scene structure JSON: {target}")
