#!/usr/bin/env python3
"""
Post-process the raw NotebookLM video with Hyperframes:
- Add EXAI branding overlay (top bar, watermark)
- Add lower-third topic cards
- Add infographic panels
- Add breaking news ticker
- Cover NotebookLM logo
"""

import sys, os, json, subprocess, shutil, datetime, glob

DATE_SHORT = datetime.date.today().strftime("%Y-%m-%d")
DATE_FRIENDLY = datetime.date.today().strftime("%B %d, %Y")
VIDEO_PATH = os.environ.get("VIDEO_PATH", f"/tmp/morningbrief/morningbrief_video_{DATE_SHORT}.mp4")
BRIEF_FILE = os.environ.get("BRIEF_FILE", f"/tmp/morningbrief/brief_{DATE_SHORT}.md")
HF_DIR = "/Users/franzccm/projects/ex-venture-platform/morningbrief-edit"
OUTPUT = VIDEO_PATH.replace(".mp4", "_edited.mp4")

if not os.path.exists(VIDEO_PATH):
    print(f"No video: {VIDEO_PATH}")
    sys.exit(1)

print(f"Post-processing {VIDEO_PATH}...")

# Get video duration
probe = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", VIDEO_PATH],
                       capture_output=True, text=True)
duration = int(float(json.loads(probe.stdout)["format"]["duration"]))

# Extract topics from brief for lower thirds and ticker
topics = []
ticker_text = "BREAKING: Latest AI news "
if os.path.exists(BRIEF_FILE):
    with open(BRIEF_FILE) as f:
        brief = f.read()
    for line in brief.split('\n'):
        line = line.strip()
        if line.startswith('* **') or line.startswith('- **'):
            parts = line.split('**')
            if len(parts) >= 2:
                topic = parts[1].replace(':', '').strip()[:50]
                if len(topic) > 5:
                    topics.append(topic)
    ticker_items = [t for t in topics[:6]]
    ticker_text = " • ".join(ticker_items) + " • Subscribe to EXAI Global •"

# Update the HTML template with today's data
with open(os.path.join(HF_DIR, "index.html")) as f:
    html = f.read()

html = html.replace("April 24, 2026", DATE_FRIENDLY)
html = html.replace('data-duration="60"', f'data-duration="{duration}"', 1)  # root duration
html = html.replace("Breaking: Today's Top AI Stories", topics[0] if topics else "AI News Today")
html = html.replace("Your daily AI intelligence briefing", topics[1] if len(topics) > 1 else "EXAI Global")
html = html.replace("BREAKING: Latest AI news from the last 48 hours • New models, tools, and features dropping daily • Subscribe to EXAI Global for daily updates •", ticker_text)

with open(os.path.join(HF_DIR, "index.html"), "w") as f:
    f.write(html)

# Copy raw video to hyperframes project
shutil.copy2(VIDEO_PATH, os.path.join(HF_DIR, "input.mp4"))

# Render with Hyperframes
print(f"Rendering with Hyperframes ({duration}s)...")
result = subprocess.run(
    ["npx", "hyperframes", "render", "--output", OUTPUT],
    capture_output=True, text=True, cwd=HF_DIR, timeout=600
)

if os.path.exists(OUTPUT) and os.path.getsize(OUTPUT) > 100000:
    # Replace original with edited version
    os.rename(OUTPUT, VIDEO_PATH)
    print(f"✓ Post-processed: {os.path.getsize(VIDEO_PATH)/1024/1024:.1f} MB")
else:
    print(f"Hyperframes render failed: {result.stderr[:200]}")
    print("Using original video without overlays")
