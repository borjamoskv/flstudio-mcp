#!/usr/bin/env python3
"""
Pika 2.5 Pro - Prompt Clipboard Exporter
=========================================
Genera un archivo de texto con todos los prompts listos para copiar/pegar
directamente en la interfaz web de Pika 2.5 Pro.

Incluye los parametros reales de Pika: -ar, -motion, -fps, -gs, -neg
"""

import os

PROMPTS = [
    {
        "title": "Shot 1 - GENESIS (Image-to-Video - shot1_genesis.png)",
        "prompt": (
            "A dark obsidian monolith floating in zero gravity, vintage Fender Rhodes "
            "piano visible inside translucent crystal, soft magenta and cyan volumetric "
            "light, golden dust particles drifting slowly, 35mm anamorphic lens, "
            "gentle dolly-in"
        ),
        "params": "-ar 16:9 -motion 1 -fps 24 -gs 14",
        "neg": "morphing, blurry, text, watermark",
        "feature": "Image-to-Video (usar shot1_genesis.png como input)",
    },
    {
        "title": "Shot 2 - CRYSTALLIZATION (Scene Extension desde Shot 1)",
        "prompt": (
            "The obsidian crystal monolith begins glowing brighter from within, "
            "magenta and cyan light intensifying through fractures in the dark stone, "
            "Rhodes piano keys subtly vibrating, particles accelerating outward, "
            "35mm anamorphic lens, slow push in"
        ),
        "params": "-ar 16:9 -motion 2 -fps 24 -gs 14",
        "neg": "morphing, blurry, text",
        "feature": "Scene Extension (ultimo frame del Shot 1 como base)",
    },
    {
        "title": "Shot 3 - IMPACT (Image-to-Video - shot3_impact.png)",
        "prompt": (
            "Extreme macro of dark magnetic ferrofluid forming sharp geometric spikes "
            "on brushed titanium, pulsing rhythmically, teal and deep purple rim "
            "lighting, industrial warehouse atmosphere, high-speed camera aesthetic, "
            "steady tracking shot left to right"
        ),
        "params": "-ar 16:9 -motion 3 -fps 24 -gs 16",
        "neg": "morphing, blurry, text, faces",
        "feature": "Image-to-Video (usar shot3_impact.png como input) + Pikaffects",
    },
    {
        "title": "Shot 4 - PULSE (Scene Extension desde Shot 3)",
        "prompt": (
            "The ferrofluid spikes collapse and reform in rhythmic pulses synchronized "
            "with bass frequencies, dark titanium surface reflecting teal light, subtle "
            "slow-motion ripple effect, macro lens 100mm, gentle arc right"
        ),
        "params": "-ar 16:9 -motion 2 -fps 24 -gs 14",
        "neg": "morphing, blurry, text",
        "feature": "Scene Extension (ultimo frame del Shot 3 como base)",
    },
    {
        "title": "Shot 5 - ASCENSION (Image-to-Video - shot5_ascension.png)",
        "prompt": (
            "Inside a retro-futuristic observatory dome, giant holographic light rings "
            "slowly spinning, 1970s analog film grain, warm golden glow merging with "
            "cyan cosmic nebula through the glass dome, vintage synthesizer console in "
            "foreground, ultra-wide angle, slow tilt up"
        ),
        "params": "-ar 16:9 -motion 2 -fps 24 -gs 14",
        "neg": "morphing, blurry, text, modern",
        "feature": "Image-to-Video (usar shot5_ascension.png como input) + Pikascenes",
    },
    {
        "title": "Shot 6 - RESONANCE (Scene Extension desde Shot 5)",
        "prompt": (
            "The holographic rings inside the observatory dome spin faster, golden light "
            "intensifies, cosmic dust particles swirling inward toward the center, all "
            "light converging to a single bright point, 1970s film grain, dramatic "
            "crescendo atmosphere, slow push in"
        ),
        "params": "-ar 16:9 -motion 3 -fps 24 -gs 16",
        "neg": "morphing, blurry, text",
        "feature": "Scene Extension (ultimo frame del Shot 5 como base)",
    },
    {
        "title": "Shot 7 - THE FALSE DROP (Image-to-Video - shot7_false_drop.png)",
        "prompt": (
            "Dramatic explosion of pure golden sunlight shattering through dark obsidian "
            "monolithic geometry, brilliant anamorphic lens flares, dark stone fragments "
            "floating in slow motion, transition from deep industrial darkness to radiant "
            "ethereal golden horizon, volumetric god rays, epic scale, cinematic 4k"
        ),
        "params": "-ar 16:9 -motion 4 -fps 24 -gs 18",
        "neg": "morphing, blurry, text, faces",
        "feature": "Image-to-Video (usar shot7_false_drop.png como input) + Pikatwists (shatter)",
    },
    {
        "title": "Shot 8 - RECOMPOSITION (Scene Extension + Pikaframes)",
        "prompt": (
            "The scattered obsidian stone fragments slowly reassemble in reverse, "
            "reforming the dark monolith from the opening shot, golden light fading to "
            "soft magenta and cyan glow, dust particles settling, 35mm anamorphic lens, "
            "slow dolly-out, fade to black"
        ),
        "params": "-ar 16:9 -motion 1 -fps 24 -gs 12",
        "neg": "morphing, blurry, text",
        "feature": "Scene Extension (ultimo frame Shot 7) + Pikaframes (destino: shot1_genesis.png)",
    },
]

NEG_GLOBAL = "morphing, bad quality, blurry, watermark, text overlay, distorted faces, jpeg artifacts"


def export_prompts(output_path):
    lines = []
    lines.append("=" * 80)
    lines.append("PIKA 2.5 PRO - PROMPT PACK: Satin Jackets x Maceo Plex x AIR")
    lines.append("Storyboard v2.0 | 118 BPM | 8 Compases | Industrial Noir")
    lines.append("=" * 80)
    lines.append("")
    lines.append("NEGATIVE PROMPT GLOBAL: " + NEG_GLOBAL)
    lines.append("")

    for i, data in enumerate(PROMPTS, 1):
        lines.append("-" * 80)
        lines.append("[{}/8] {}".format(i, data["title"]))
        lines.append("-" * 80)
        lines.append("")
        lines.append("  PROMPT:")
        lines.append("  " + data["prompt"])
        lines.append("")
        lines.append("  PARAMETERS: " + data["params"])
        lines.append("  NEGATIVE:   -neg " + data["neg"])
        lines.append("  FEATURE:    " + data["feature"])
        lines.append("")
        full_prompt = "{} {} -neg {}".format(data["prompt"], data["params"], data["neg"])
        lines.append("  COPY-PASTE READY:")
        lines.append("  " + full_prompt)
        lines.append("")

    lines.append("=" * 80)
    lines.append("KEYFRAME FILES (subir a Pika como Image-to-Video):")
    lines.append("  Shot 1: pika_keyframes/shot1_genesis.png")
    lines.append("  Shot 3: pika_keyframes/shot3_impact.png")
    lines.append("  Shot 5: pika_keyframes/shot5_ascension.png")
    lines.append("  Shot 7: pika_keyframes/shot7_false_drop.png")
    lines.append("=" * 80)

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path


if __name__ == "__main__":
    out = export_prompts(
        os.path.expanduser("~/10_PROJECTS/flstudio-mcp/pika_keyframes/PIKA_PROMPT_PACK.txt")
    )
    print("Pika 2.5 Prompt Pack exported: " + out)
    print("")
    print("Keyframes ready at: ~/10_PROJECTS/flstudio-mcp/pika_keyframes/")
    print("   -> shot1_genesis.png")
    print("   -> shot3_impact.png")
    print("   -> shot5_ascension.png")
    print("   -> shot7_false_drop.png")
    print("")
    print("Open Pika 2.5 Pro and use Image-to-Video with each keyframe + prompt.")
