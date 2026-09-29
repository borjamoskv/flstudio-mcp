#!/usr/bin/env python3
"""
Generate crisp, hilarious South Park paper cut-out character parts and studio background
"""
import os
from PIL import Image, ImageDraw, ImageFont

PUB = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public"
os.makedirs(PUB, exist_ok=True)

# 1. ALAIN HEAD - TOP (Upper oval, hair, eyebrows, beady eyes, upper lip)
w, h = 400, 300
img_top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
draw = ImageDraw.Draw(img_top)

# Skin tone: classic warm paper peach
skin = (252, 215, 178, 255)
skin_outline = (30, 20, 15, 255)

# Upper half head shape (dome)
bbox = [60, 40, 340, 320]
draw.pieslice(bbox, 180, 360, fill=skin, outline=skin_outline, width=5)
draw.rectangle([60, 180, 340, 200], fill=skin, outline=None)
draw.line([60, 200, 340, 200], fill=skin_outline, width=5)

# Curly wild hair (Alain Elektrocaniche style)
hair_color = (65, 45, 30, 255)
# Hair curls across top
curls = [(80, 50, 45), (120, 30, 50), (170, 20, 55), (225, 22, 55), (280, 35, 50), (320, 60, 45),
         (65, 90, 40), (335, 95, 40), (55, 135, 35), (345, 140, 35)]
for cx, cy, r in curls:
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=hair_color, outline=(20, 15, 10, 255), width=4)

# Eyes (South Park oval cutouts)
# Left eye
draw.ellipse([135, 115, 185, 175], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=4)
draw.ellipse([155, 138, 170, 153], fill=(15, 15, 15, 255))
# Right eye
draw.ellipse([215, 115, 265, 175], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=4)
draw.ellipse([235, 138, 250, 153], fill=(15, 15, 15, 255))

# Eyebrows (expressive / animated)
draw.arc([130, 95, 180, 115], 190, 350, fill=(30, 20, 15, 255), width=5)
draw.arc([220, 95, 270, 115], 190, 350, fill=(30, 20, 15, 255), width=5)

# Nose (cute paper hook)
draw.arc([190, 150, 215, 180], 260, 90, fill=(180, 130, 100, 255), width=4)

img_top.save(os.path.join(PUB, "sp_alain_head_top.png"))
print("Saved sp_alain_head_top.png")

# 2. ALAIN HEAD - JAW (Bottom half oval)
img_jaw = Image.new("RGBA", (400, 200), (0, 0, 0, 0))
draw_jaw = ImageDraw.Draw(img_jaw)

# Lower jaw slice
draw_jaw.pieslice([60, -80, 340, 180], 0, 180, fill=skin, outline=skin_outline, width=5)
draw_jaw.line([60, 50, 340, 50], fill=skin_outline, width=5)

# Chin stubble / little goatee dots (Alain style)
for dx, dy in [(185, 120), (195, 125), (205, 122), (215, 125), (200, 140)]:
    draw_jaw.ellipse([dx-2, dy-2, dx+2, dy+2], fill=(80, 60, 45, 255))

img_jaw.save(os.path.join(PUB, "sp_alain_head_jaw.png"))
print("Saved sp_alain_head_jaw.png")

# 3. ALAIN BODY (South Park coat with buttons and collar)
bw, bh = 500, 450
img_body = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
draw_b = ImageDraw.Draw(img_body)

# Dark teal / retro jacket
coat_col = (45, 105, 115, 255)
coat_out = (15, 45, 50, 255)

# Coat torso
draw_b.polygon([(140, 40), (360, 40), (420, 380), (80, 380)], fill=coat_col, outline=coat_out)
draw_b.line([(250, 40), (250, 380)], fill=coat_out, width=5) # Zipper line

# Collar
draw_b.polygon([(170, 40), (250, 90), (190, 105)], fill=(30, 75, 85, 255), outline=coat_out, width=4)
draw_b.polygon([(330, 40), (250, 90), (310, 105)], fill=(30, 75, 85, 255), outline=coat_out, width=4)

# Big round buttons
for by in [140, 210, 280]:
    draw_b.ellipse([238, by-10, 262, by+10], fill=(20, 20, 20, 255), outline=(220, 220, 220, 255), width=3)

# Arms & Mittens
# Left arm
draw_b.polygon([(140, 60), (70, 180), (110, 220), (170, 120)], fill=coat_col, outline=coat_out, width=4)
# Left red mitten
draw_b.ellipse([60, 190, 120, 250], fill=(210, 45, 45, 255), outline=(100, 15, 15, 255), width=4)
draw_b.ellipse([95, 185, 125, 215], fill=(210, 45, 45, 255), outline=(100, 15, 15, 255), width=4) # Thumb

# Right arm
draw_b.polygon([(360, 60), (430, 180), (390, 220), (330, 120)], fill=coat_col, outline=coat_out, width=4)
# Right red mitten
draw_b.ellipse([380, 190, 440, 250], fill=(210, 45, 45, 255), outline=(100, 15, 15, 255), width=4)
draw_b.ellipse([375, 185, 405, 215], fill=(210, 45, 45, 255), outline=(100, 15, 15, 255), width=4)

img_body.save(os.path.join(PUB, "sp_alain_body.png"))
print("Saved sp_alain_body.png")

# 4. BORJA HOST CHARACTER (Complete South Park style)
borja_w, borja_h = 500, 650
img_borja = Image.new("RGBA", (borja_w, borja_h), (0, 0, 0, 0))
draw_bj = ImageDraw.Draw(img_borja)

# Borja body (Black hoodie / jacket)
hoodie_col = (30, 32, 38, 255)
hoodie_out = (10, 10, 15, 255)
draw_bj.polygon([(160, 260), (340, 260), (400, 600), (100, 600)], fill=hoodie_col, outline=hoodie_out, width=5)

# Borja Head
b_skin = (255, 222, 190, 255)
draw_bj.ellipse([140, 70, 360, 280], fill=b_skin, outline=skin_outline, width=5)

# Borja Short Dark Hair
draw_bj.pieslice([135, 60, 365, 240], 180, 360, fill=(35, 30, 25, 255), outline=skin_outline, width=5)

# Headphones (Studio over-ear)
draw_bj.arc([125, 40, 375, 220], 180, 360, fill=(15, 15, 20, 255), width=16) # Headband
draw_bj.ellipse([110, 130, 155, 210], fill=(220, 50, 50, 255), outline=(15, 15, 15, 255), width=5) # Ear cup L
draw_bj.ellipse([345, 130, 390, 210], fill=(220, 50, 50, 255), outline=(15, 15, 15, 255), width=5) # Ear cup R

# Eyes (South Park style with glasses or sharp glance)
draw_bj.ellipse([190, 140, 235, 190], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=4)
draw_bj.ellipse([205, 158, 220, 173], fill=(20, 20, 20, 255))
draw_bj.ellipse([265, 140, 310, 190], fill=(255, 255, 255, 255), outline=(20, 20, 20, 255), width=4)
draw_bj.ellipse([280, 158, 295, 173], fill=(20, 20, 20, 255))

# Smile
draw_bj.arc([220, 200, 280, 235], 20, 160, fill=(30, 20, 15, 255), width=5)

# Arms & hands resting on desk
draw_bj.polygon([(160, 280), (110, 420), (180, 470), (220, 340)], fill=hoodie_col, outline=hoodie_out, width=4)
draw_bj.ellipse([150, 450, 210, 510], fill=b_skin, outline=skin_outline, width=4)

draw_bj.polygon([(340, 280), (390, 420), (320, 470), (280, 340)], fill=hoodie_col, outline=hoodie_out, width=4)
draw_bj.ellipse([290, 450, 350, 510], fill=b_skin, outline=skin_outline, width=4)

img_borja.save(os.path.join(PUB, "sp_borja_host.png"))
print("Saved sp_borja_host.png")

# 5. SOUTH PARK STUDIO BACKGROUND & DESK
bg_w, bg_h = 1920, 1080
img_bg = Image.new("RGB", (bg_w, bg_h), (210, 230, 245)) # South park sky blue
draw_bg = ImageDraw.Draw(img_bg)

# Snowy mountains in background
draw_bg.polygon([(0, 650), (300, 200), (600, 650)], fill=(240, 248, 255), outline=(150, 180, 210), width=4)
draw_bg.polygon([(250, 200), (300, 200), (350, 280), (300, 290)], fill=(255, 255, 255))

draw_bg.polygon([(450, 650), (850, 160), (1250, 650)], fill=(235, 245, 255), outline=(150, 180, 210), width=4)
draw_bg.polygon([(1100, 650), (1500, 220), (1920, 650)], fill=(240, 248, 255), outline=(150, 180, 210), width=4)

# Pine trees (cut-paper triangles)
trees = [(150, 580), (220, 600), (950, 590), (1050, 610), (1700, 580), (1780, 600)]
for tx, ty in trees:
    draw_bg.polygon([(tx-40, ty), (tx, ty-90), (tx+40, ty)], fill=(35, 95, 60), outline=(15, 55, 30), width=3)
    draw_bg.polygon([(tx-30, ty-50), (tx, ty-120), (tx+30, ty-50)], fill=(45, 115, 75), outline=(15, 55, 30), width=3)

# Wall / Podcast Studio Room Base (Paper wall)
draw_bg.rectangle([0, 550, 1920, 1080], fill=(238, 225, 205), outline=(180, 165, 140), width=6)
draw_bg.rectangle([0, 550, 1920, 580], fill=(200, 180, 150)) # Dado de pared

# Podcast studio signs on the wall
draw_bg.rectangle([700, 590, 1220, 710], fill=(250, 245, 230), outline=(50, 40, 30), width=6)
# Simple decorative badge
draw_bg.rectangle([715, 605, 1205, 695], fill=(235, 70, 60), outline=(20, 20, 20), width=4)

img_bg.save(os.path.join(PUB, "sp_studio_bg.png"))
print("Saved sp_studio_bg.png")

# 6. PODCAST DESK & MICS OVERLAY
desk_img = Image.new("RGBA", (1920, 450), (0, 0, 0, 0))
draw_d = ImageDraw.Draw(desk_img)

# Curved Wooden Podcast Desk
draw_d.polygon([(100, 120), (1820, 120), (1920, 450), (0, 450)], fill=(160, 95, 55, 255), outline=(60, 30, 15, 255), width=8)
draw_d.rectangle([0, 410, 1920, 450], fill=(110, 60, 35, 255)) # Rim

# Two Podcast Microphones on Desk Stands
for mx in [550, 1350]:
    # Base
    draw_d.ellipse([mx-45, 180, mx+45, 215], fill=(40, 40, 45, 255), outline=(15, 15, 20, 255), width=4)
    # Stand pole
    draw_d.rectangle([mx-8, 60, mx+8, 190], fill=(70, 75, 80, 255), outline=(20, 20, 20, 255), width=3)
    # Mic body (SM7B capsule)
    draw_d.rectangle([mx-26, 10, mx+26, 75], fill=(25, 25, 30, 255), outline=(10, 10, 10, 255), width=4)
    # Windscreen foam
    draw_d.ellipse([mx-24, 0, mx+24, 30], fill=(45, 45, 50, 255))

desk_img.save(os.path.join(PUB, "sp_desk_mics.png"))
print("Saved sp_desk_mics.png")
