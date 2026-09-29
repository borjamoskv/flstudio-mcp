import numpy as np
from PIL import Image, ImageDraw, ImageFilter

faces_dir = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/faces"
top_img = Image.open(f"{faces_dir}/mitxu_top.png").convert("RGBA")
jaw_img = Image.open(f"{faces_dir}/mitxu_jaw.png").convert("RGBA")
w, h = top_img.size # 371, 403

# Canvas with extra padding for the puffy parka hood
pad_x = 45
pad_top = 45
pad_bot = 35
cw = w + pad_x * 2 # 461
ch = h + pad_top + pad_bot # 483

# Cut line Y in new canvas
cut_y = 335 + pad_top # 380

# 1. Base head on new canvas
head_canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
head_canvas.paste(jaw_img, (pad_x, pad_top), jaw_img)
head_canvas.paste(top_img, (pad_x, pad_top), top_img)

# 2. Draw Kenny Parka Hood
# Outer hood dome bounding box
# Center x is ~ 205 + pad_x = 250
# Center y is ~ 210 + pad_top = 255
hood_left = 15
hood_right = cw - 15
hood_top = 10
hood_bot = ch - 10

ORANGE = (234, 88, 12, 255)       # Kenny orange #ea580c
ORANGE_DARK = (194, 65, 12, 255)  # #c2410c
BROWN_TRIM = (120, 53, 15, 255)   # #78350f
BROWN_DARK = (70, 30, 8, 255)
BLACK = (0, 0, 0, 255)

# Outer hood image
outer_hood = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
draw_h = ImageDraw.Draw(outer_hood)

# Draw main hood oval dome
draw_h.ellipse([hood_left, hood_top, hood_right, hood_bot], fill=ORANGE, outline=BLACK, width=6)

# Face opening (hole through which Mitxu is visible)
# Sunglasses are roughly x from 60+pad_x to 345+pad_x (105 to 390)
# Mouth is roughly x from 130+pad_x to 275+pad_x (175 to 320)
# Hole should comfortably reveal sunglasses, nose, and mouth, while covering calva, ears, and outer jaw!
hole_left = 68
hole_right = cw - 68
hole_top = 115
hole_bot = ch - 50

# Brown fur/fabric trim around hole: slightly larger than the hole
trim_left = hole_left - 18
trim_right = hole_right + 18
trim_top = hole_top - 18
trim_bot = hole_bot + 18

draw_h.ellipse([trim_left, trim_top, trim_right, trim_bot], fill=BROWN_TRIM, outline=BLACK, width=5)

# Now cut out the hole from outer_hood so the face shows through!
# We can do this using a mask or drawing transparent ellipse
hole_mask = Image.new("L", (cw, ch), 255)
draw_mask = ImageDraw.Draw(hole_mask)
draw_mask.ellipse([hole_left, hole_top, hole_right, hole_bot], fill=0)

# Apply hole to outer_hood
outer_hood_np = np.array(outer_hood)
outer_hood_np[:, :, 3] = np.minimum(outer_hood_np[:, :, 3], np.array(hole_mask))
outer_hood = Image.fromarray(outer_hood_np)

# Draw inner border of the hole
draw_rim = ImageDraw.Draw(outer_hood)
draw_rim.ellipse([hole_left, hole_top, hole_right, hole_bot], outline=BLACK, width=5)

# Two drawstrings under the chin
# Drawstring left
draw_rim.polygon([(215, hole_bot - 8), (200, ch - 8), (210, ch - 5), (222, hole_bot - 5)], fill=BROWN_DARK, outline=BLACK)
draw_rim.ellipse([197, ch - 12, 213, ch - 2], fill=BROWN_DARK, outline=BLACK, width=2)
# Drawstring right
draw_rim.polygon([(245, hole_bot - 8), (260, ch - 8), (250, ch - 5), (238, hole_bot - 5)], fill=BROWN_DARK, outline=BLACK)
draw_rim.ellipse([247, ch - 12, 263, ch - 2], fill=BROWN_DARK, outline=BLACK, width=2)

# Composite: Back layer (orange background in case head doesn't fill hole)
back_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
draw_b = ImageDraw.Draw(back_layer)
draw_b.ellipse([hood_left + 10, hood_top + 10, hood_right - 10, hood_bot - 10], fill=(40, 20, 10, 255))

final_composite = Image.alpha_composite(back_layer, head_canvas)
final_composite = Image.alpha_composite(final_composite, outer_hood)

final_composite.save("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/test_mitxu_hood.png")
print("Saved test_mitxu_hood.png successfully!")
