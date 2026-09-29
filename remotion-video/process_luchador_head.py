import numpy as np
from PIL import Image, ImageDraw

img = Image.open("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/faces/mitxu_luchador.jpg").convert("RGBA")
w, h = img.size # 1024, 1024

# The mask head is roughly:
# Center around (512, 420), radius around 350-380
# Let us crop the head bounding box:
# Top: around y=70, Bottom: around y=780, Left: around x=160, Right: around x=860
cx, cy = 512, 425
rx, ry = 345, 360

mask = Image.new("L", (w, h), 0)
draw = ImageDraw.Draw(mask)
draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)

head_cutout = Image.new("RGBA", (w, h), (0, 0, 0, 0))
head_cutout.paste(img, (0, 0), mask)

# Crop to head bounds
bbox = head_cutout.getbbox()
head_cropped = head_cutout.crop(bbox) # e.g. ~700 x 720
head_cropped = head_cropped.resize((451, 468), Image.Resampling.LANCZOS)

# Save full luchador head
head_cropped.save("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/faces/mitxu_lucha_full.png")

# Now cut into top and jaw along the mouth line
# In 451x468, mouth cut line is around y=365
cut_y = 365
hw, hh = head_cropped.size

top_img = head_cropped.copy()
top_arr = np.array(top_img)
top_arr[cut_y:, :, :] = 0
top_img = Image.fromarray(top_arr)
top_img.save("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/faces/mitxu_lucha_top.png")

jaw_img = head_cropped.copy()
jaw_arr = np.array(jaw_img)
jaw_arr[:cut_y, :, :] = 0
jaw_img = Image.fromarray(jaw_arr)
jaw_img.save("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/faces/mitxu_lucha_jaw.png")

print(f"Saved mitxu_lucha_full.png, mitxu_lucha_top.png, mitxu_lucha_jaw.png (size: {hw}x{hh})")
