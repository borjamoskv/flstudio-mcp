import os
from PIL import Image, ImageDraw

faces_dir = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/faces"
top_img = Image.open(f"{faces_dir}/mitxu_top.png").convert("RGBA")
jaw_img = Image.open(f"{faces_dir}/mitxu_jaw.png").convert("RGBA")
w, h = top_img.size # 371, 403

# Colors
ORANGE = (234, 88, 12, 255)       # Kenny coat orange #ea580c
ORANGE_DARK = (194, 65, 12, 255)  # Shadow/fold orange #c2410c
BROWN_TRIM = (120, 53, 15, 255)   # Kenny hood lining #78350f
BROWN_DARK = (80, 35, 10, 255)    # Drawstring & inner rim #50230a
BLACK = (0, 0, 0, 255)

# Cut line y
cut_y = 335

# Let's test creating the hood in the exact same coordinate space (371, 403) so it drops right in!
# Or let's see where Mitxu's face features are:
# Sunglasses top: y ~ 115
# Sunglasses bottom: y ~ 230
# Sunglasses left: x ~ 65, right: x ~ 340 (glasses width is ~275)
# Mouth: y ~ 320-370, x ~ 140-270
# Center x is ~ 205, center y is ~ 230

# If canvas is (371, 403):
# Outer hood dome:
# Fits snugly in (371, 403) or slightly expanded?
# If in (371, 403), the dome can go from x=15 to x=356, y=10 to y=395.
# Let's test an expanded canvas vs exact canvas.
# If we keep exact (371, 403), Remotion code requires zero layout changes!
# Let's inspect where the outer boundary of the head is currently:
# Calva top is at y=0. Ears are at x=0 and x=371.
# So (371, 403) is the exact bounding box of Mitxu's head.

# Let's build a hood that covers the calva and ears, framing the face!
