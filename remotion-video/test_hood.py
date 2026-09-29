import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

faces_dir = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/faces"
top_img = Image.open(f"{faces_dir}/mitxu_top.png").convert("RGBA")
jaw_img = Image.open(f"{faces_dir}/mitxu_jaw.png").convert("RGBA")
full_img = Image.open(f"{faces_dir}/mitxu_full.png").convert("RGBA")

w, h = full_img.size # 371, 403
print(f"Size: {w}x{h}")

# Canvas for hood
# Kenny's hood is wider and taller than the bare head
pad_x = 50
pad_y_top = 50
pad_y_bot = 30
nw = w + pad_x * 2 # 471
nh = h + pad_y_top + pad_y_bot # 483

print(f"New canvas: {nw}x{nh}")
