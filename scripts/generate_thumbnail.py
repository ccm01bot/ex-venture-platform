#!/usr/bin/env python3
"""Generate YouTube thumbnail using Pillow. No API key needed."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import datetime
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TODAY = datetime.date.today()
DATE_STR = TODAY.strftime("%b %d, %Y")
DATE_SHORT = TODAY.strftime("%Y-%m-%d")
THUMB_PATH = os.environ.get("THUMB_PATH", f"/tmp/morningbrief/thumbnail_{DATE_SHORT}.png")

# Get headline from brief if available
HEADLINE = os.environ.get("HEADLINE", "Latest AI Updates & Breaking News")
if len(HEADLINE) > 45:
    HEADLINE = HEADLINE[:42] + "..."

W, H = 1280, 720

img = Image.new('RGB', (W, H))
draw = ImageDraw.Draw(img)

# Background gradient: dark blue to dark purple
for y in range(H):
    r = int(10 + (25 - 10) * y / H)
    g = int(10 + (5 - 10) * y / H)
    b = int(40 + (80 - 40) * y / H)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Add grid/circuit pattern
for x in range(0, W, 60):
    draw.line([(x, 0), (x, H)], fill=(30, 30, 70), width=1)
for y in range(0, H, 60):
    draw.line([(0, y), (W, y)], fill=(30, 30, 70), width=1)

# Add glowing dots at intersections
random.seed(42)
for x in range(0, W, 60):
    for y in range(0, H, 60):
        if random.random() > 0.7:
            brightness = random.randint(60, 150)
            r = random.choice([(brightness, brightness//2, brightness*2), (brightness//2, brightness, brightness*2), (brightness*2, brightness//2, brightness)])
            draw.ellipse([x-3, y-3, x+3, y+3], fill=r)

# Add diagonal accent lines
for i in range(5):
    x_start = random.randint(0, W)
    draw.line([(x_start, 0), (x_start - 200, H)], fill=(50, 100, 200, 80), width=2)

# Red "BREAKING" badge top-left
badge_w, badge_h = 200, 45
draw.rounded_rectangle([30, 30, 30 + badge_w, 30 + badge_h], radius=8, fill=(220, 30, 30))

# Blue accent bar on the left
draw.rectangle([0, 0, 8, H], fill=(0, 120, 255))

# Bottom gradient bar
for y in range(H - 120, H):
    alpha = int((y - (H - 120)) / 120 * 200)
    draw.line([(0, y), (W, y)], fill=(0, 0, 0))

# Try to load a nice font, fallback to default
def get_font(size, bold=False):
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    if bold:
        font_paths = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ] + font_paths
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
    return ImageFont.load_default()

font_badge = get_font(24, bold=True)
font_main = get_font(72, bold=True)
font_sub = get_font(36, bold=True)
font_date = get_font(28)
font_brand = get_font(22)

# Draw "BREAKING" text
draw.text((55, 33), "BREAKING", fill=(255, 255, 255), font=font_badge)

# Main title "AI NEWS"
# Shadow
draw.text((52, 152), "AI NEWS", fill=(0, 0, 0), font=font_main)
# Main text
draw.text((50, 150), "AI NEWS", fill=(255, 255, 255), font=font_main)

# Blue accent line under title
draw.rectangle([50, 240, 350, 246], fill=(0, 150, 255))

# Date
draw.text((50, 260), DATE_STR.upper(), fill=(100, 180, 255), font=font_sub)

# Headline
draw.text((50, 320), HEADLINE, fill=(200, 200, 210), font=font_date)

# Bottom bar with branding
draw.rectangle([0, H - 55, W, H], fill=(0, 0, 0))
draw.text((50, H - 42), "EXAI GLOBAL", fill=(0, 150, 255), font=font_brand)
draw.text((W - 250, H - 42), "DAILY AI BRIEFING", fill=(150, 150, 160), font=font_brand)

# Add a subtle glow effect on the right side
glow = Image.new('RGB', (400, 400), (0, 50, 150))
glow = glow.filter(ImageFilter.GaussianBlur(100))
# Paste with transparency simulation
for x in range(400):
    for y in range(400):
        px = glow.getpixel((x, y))
        if px[2] > 20:
            ox, oy = W - 450 + x, 100 + y
            if 0 <= ox < W and 0 <= oy < H:
                orig = img.getpixel((ox, oy))
                blended = tuple(min(255, orig[i] + px[i] // 4) for i in range(3))
                img.putpixel((ox, oy), blended)

img.save(THUMB_PATH, quality=95)
print(f"✓ Thumbnail: {THUMB_PATH} ({os.path.getsize(THUMB_PATH)/1024:.0f} KB)")
