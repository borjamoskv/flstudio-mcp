import numpy as np
from PIL import Image, ImageDraw

faces_dir = "/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/public/faces"
top_img = Image.open(f"{faces_dir}/mitxu_top.png").convert("RGBA")
jaw_img = Image.open(f"{faces_dir}/mitxu_jaw.png").convert("RGBA")
w, h = top_img.size # 371, 403

# Padding
pad_x = 40
pad_top = 40
pad_bot = 25
cw = w + pad_x * 2 # 451
ch = h + pad_top + pad_bot # 468

# Cut line Y in new canvas
cut_y = 335 + pad_top # 375

# 1. Base head layers
top_canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
top_canvas.paste(top_img, (pad_x, pad_top), top_img)

jaw_canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
jaw_canvas.paste(jaw_img, (pad_x, pad_top), jaw_img)

# Colors
ORANGE = (234, 88, 12, 255)       # Kenny orange #ea580c
ORANGE_SHADOW = (194, 65, 12, 255)
BROWN_TRIM = (120, 53, 15, 255)   # Kenny hood lining #78350f
BROWN_DARK = (70, 30, 8, 255)
BLACK = (0, 0, 0, 255)

# Outer hood bounds
hood_left = 10
hood_right = cw - 10
hood_top = 10
hood_bot = ch - 8

# Face opening hole:
# Mitxu's sunglasses: left ~ 65+pad_x = 105, right ~ 345+pad_x = 385
# Glasses width is ~ 280.
# So hole should be wide enough:
# Center X is 205 + pad_x = 245
hole_cx = 245
hole_cy = 248
hole_rx = 160 # width = 320 (x from 85 to 405)
hole_ry = 145 # height = 290 (y from 103 to 393)

trim_rx = hole_rx + 20
trim_ry = hole_ry + 20

# Create full hood
hood_full = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
draw_h = ImageDraw.Draw(hood_full)

# Outer dome
draw_h.ellipse([hood_left, hood_top, hood_right, hood_bot], fill=ORANGE, outline=BLACK, width=6)

# Brown trim around hole
draw_h.ellipse([hole_cx - trim_rx, hole_cy - trim_ry, hole_cx + trim_rx, hole_cy + trim_ry], fill=BROWN_TRIM, outline=BLACK, width=5)

# Cut out hole from hood_full
hole_mask = Image.new("L", (cw, ch), 255)
draw_mask = ImageDraw.Draw(hole_mask)
draw_mask.ellipse([hole_cx - hole_rx, hole_cy - hole_ry, hole_cx + hole_rx, hole_cy + hole_ry], fill=0)

hood_np = np.array(hood_full)
hood_np[:, :, 3] = np.minimum(hood_np[:, :, 3], np.array(hole_mask))
hood_full = Image.fromarray(hood_np)

# Inner black outline for the hole
draw_rim = ImageDraw.Draw(hood_full)
draw_rim.ellipse([hole_cx - hole_rx, hole_cy - hole_ry, hole_cx + hole_rx, hole_cy + hole_ry], outline=BLACK, width=5)

# Drawstrings at bottom
ds_top = hole_cy + hole_ry - 4
draw_rim.polygon([(hole_cx - 15, ds_top), (hole_cx - 28, ch - 5), (hole_cx - 16, ch - 3), (hole_cx - 6, ds_top + 2)], fill=BROWN_DARK, outline=BLACK)
draw_rim.ellipse([hole_cx - 32, ch - 12, hole_cx - 14, ch], fill=BROWN_DARK, outline=BLACK, width=2)

draw_rim.polygon([(hole_cx + 6, ds_top + 2), (hole_cx + 16, ch - 3), (hole_cx + 28, ch - 5), (hole_cx + 15, ds_top)], fill=BROWN_DARK, outline=BLACK)
draw_rim.ellipse([hole_cx + 14, ch - 12, hole_cx + 32, ch], fill=BROWN_DARK, outline=BLACK, width=2)

# Now composite top piece and jaw piece!
# Inside cavity back layer (behind head)
back_layer = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
draw_b = ImageDraw.Draw(back_layer)
draw_b.ellipse([hood_left + 8, hood_top + 8, hood_right - 8, hood_bot - 8], fill=(35, 18, 10, 255))

# Top piece:
# Back layer + top head + hood (everything above cut_y)
comp_top = Image.alpha_composite(back_layer, top_canvas)
comp_top = Image.alpha_composite(comp_top, hood_full)

# Cut at cut_y: top gets y <= cut_y
top_np = np.array(comp_top)
top_np[cut_y:, :, :] = 0 # zero out bottom
final_top = Image.fromarray(top_np)

# Jaw piece:
# Back layer + jaw head + hood (everything from cut_y downwards)
comp_jaw = Image.alpha_composite(back_layer, jaw_canvas)
comp_jaw = Image.alpha_composite(comp_jaw, hood_full)

jaw_np = np.array(comp_jaw)
jaw_np[:cut_y, :, :] = 0 # zero out top
final_jaw = Image.fromarray(jaw_np)

# Save the two pieces for Remotion
final_top.save(f"{faces_dir}/mitxu_hood_top.png")
final_jaw.save(f"{faces_dir}/mitxu_hood_jaw.png")
print("Saved mitxu_hood_top.png and mitxu_hood_jaw.png")

# Now let's create two preview images:
# 1. Closed mouth
preview_closed = Image.alpha_composite(final_jaw, final_top)
preview_closed.save("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/out/preview_hood_closed.png")

# 2. Open mouth (flapGap = 16)
flapGap = 16
preview_open = Image.new("RGBA", (cw, ch + flapGap), (0, 0, 0, 0))
# Paste jaw at bottom (offset by flapGap)
preview_open.paste(final_jaw, (0, flapGap), final_jaw)
# Black mouth cavity inside
draw_open = ImageDraw.Draw(preview_open)
draw_open.rectangle([hole_cx - 70, cut_y, hole_cx + 70, cut_y + flapGap + 12], fill=(15, 15, 15, 255))
# Paste top at 0 (lifted)
preview_open.paste(final_top, (0, 0), final_top)
preview_open.save("/Users/borjafernandezangulo/10_PROJECTS/flstudio-mcp/remotion-video/out/preview_hood_open.png")
print("Saved preview_hood_closed.png and preview_hood_open.png")
