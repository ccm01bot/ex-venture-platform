#!/usr/bin/env python3
"""
Daily Shorts Production Pipeline — 10 YouTube Shorts per day across 7 content formats.

Slot types:
  1  "AI JUST DID THIS"      — viral demo clip, three-zone layout
  2  "DAY X/7 SERIES"        — Remotion NewsShort, AI tool showcase
  3  NotebookLM Animated     — delegated to create_shorts_combined.py
  4  "VS COMPARISON"          — Remotion NewsShort, model comparison
  5  NotebookLM Animated     — delegated
  6  "ONE PROMPT DOES THIS"  — before/after clip, three-zone layout
  7  "QUICK AI HACK"         — 15s Remotion ultra-short
  8  NotebookLM Animated     — delegated
  9  "TOP 3 AI TOOLS"        — Remotion listicle
 10  "CONTROVERSIAL TAKE"    — Remotion opinion short

Usage:
  python3 produce_daily_shorts.py --all          # produce all non-NLM slots
  python3 produce_daily_shorts.py --slot 2       # produce a single slot
  python3 produce_daily_shorts.py --slot 3       # write NLM marker file
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import subprocess
import datetime
import time
import glob
import argparse
import logging
import shutil
import urllib.request
import textwrap
from pathlib import Path

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
TODAY = datetime.date.today()
DATE_STR = TODAY.strftime("%Y-%m-%d")
SHORTS_DIR = "/tmp/morningbrief/shorts"
WORK_DIR = f"/tmp/morningbrief/shorts_work_{DATE_STR}"
REMOTION_DIR = "/Users/franzccm/projects/ex-venture-platform/remotion-video"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if not GEMINI_KEY:
    print("WARNING: GEMINI_API_KEY not set. Gemini calls will fail.")
    print("  Set it with: export GEMINI_API_KEY=your_key")
GEMINI_MODEL = "gemini-2.5-flash"
LOG_FILE = f"{SHORTS_DIR}/production.log"

NLM_SLOTS = {3, 5, 8}
ALL_SLOTS = list(range(1, 11))
NON_NLM_SLOTS = [s for s in ALL_SLOTS if s not in NLM_SLOTS]

# Day-of-series tracker
SERIES_FILE = f"{SHORTS_DIR}/series_tracker.json"

os.makedirs(SHORTS_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("shorts")


# ──────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────

def output_path(slot: int) -> str:
    return f"{SHORTS_DIR}/slot_{slot}_{DATE_STR}.mp4"


def meta_path(slot: int) -> str:
    return f"{SHORTS_DIR}/slot_{slot}_{DATE_STR}.json"


def save_meta(slot: int, title: str, description: str, tags: list[str]):
    data = {
        "slot": slot,
        "date": DATE_STR,
        "title": title,
        "description": description,
        "tags": tags,
        "file": output_path(slot),
        "produced_at": datetime.datetime.now().isoformat(),
    }
    with open(meta_path(slot), "w") as f:
        json.dump(data, f, indent=2)
    log.info(f"  Metadata saved: {meta_path(slot)}")


def gemini_call(prompt: str, json_mode: bool = True) -> dict | list | str:
    """Call Gemini API and return parsed response."""
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
    }
    if json_mode:
        body["generationConfig"] = {"responseMimeType": "application/json"}

    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    if json_mode:
        return json.loads(text)
    return text


def get_brief_text() -> str:
    """Load the latest morning brief."""
    brief_file = f"/tmp/morningbrief/brief_{DATE_STR}.md"
    if not os.path.exists(brief_file):
        briefs = sorted(glob.glob("/tmp/morningbrief/brief_*.md"))
        brief_file = briefs[-1] if briefs else None
    if brief_file and os.path.exists(brief_file):
        with open(brief_file) as f:
            return f.read()
    return ""


def get_series_day() -> int:
    """Track Day X/7 series counter."""
    data = {}
    if os.path.exists(SERIES_FILE):
        with open(SERIES_FILE) as f:
            data = json.load(f)
    last_date = data.get("last_date", "")
    day = data.get("day", 0)
    if last_date != DATE_STR:
        day = (day % 7) + 1
        data = {"last_date": DATE_STR, "day": day}
        with open(SERIES_FILE, "w") as f:
            json.dump(data, f)
    return day


def render_remotion(props: dict, out_file: str, duration_frames: int | None = None) -> bool:
    """Render a Remotion NewsShort composition."""
    props_json = json.dumps(props)
    cmd = [
        "./node_modules/.bin/remotion", "render",
        "src/index.tsx", "NewsShort",
        out_file,
        f"--props={props_json}",
    ]
    if duration_frames:
        cmd.append(f"--frames=0-{duration_frames - 1}")

    log.info(f"  Remotion render: {out_file}")
    log.info(f"  Props: {props_json[:120]}...")

    result = subprocess.run(
        cmd,
        cwd=REMOTION_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        log.error(f"  Remotion FAILED (exit {result.returncode})")
        log.error(f"  stderr: {result.stderr[-500:]}")
        return False
    log.info(f"  Remotion render complete")
    return True


def download_video(search_query: str, max_duration: int = 60) -> str | None:
    """Use yt-dlp to search YouTube and download a short clip."""
    dl_path = f"{WORK_DIR}/dl_{int(time.time())}.mp4"
    cmd = [
        "yt-dlp",
        f"ytsearch1:{search_query}",
        "--match-filter", f"duration<{max_duration}",
        "-f", "best[height<=720]",
        "--no-playlist",
        "-o", dl_path,
        "--no-warnings",
        "--quiet",
    ]
    log.info(f"  yt-dlp search: {search_query}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not os.path.exists(dl_path):
        log.warning(f"  yt-dlp failed: {result.stderr[:200]}")
        return None
    log.info(f"  Downloaded: {dl_path}")
    return dl_path


def extract_segment(input_file: str, start: float, duration: float, output_file: str) -> bool:
    """Extract a segment from a video file."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-i", input_file,
        "-t", str(duration),
        "-c", "copy",
        output_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return result.returncode == 0 and os.path.exists(output_file)


def get_video_duration(file_path: str) -> float:
    """Get video duration in seconds."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def three_zone_layout(
    video_file: str,
    hook_text: str,
    caption_text: str,
    accent_word: str,
    output_file: str,
) -> bool:
    """
    Create a 9:16 three-zone layout:
      - Top zone (0-350px): hook text with branding
      - Middle zone (350-1470px): video with padding and rounded corners
      - Bottom zone (1470-1920px): caption text
    Uses ffmpeg filter_complex for the composite.
    """
    log.info(f"  Three-zone layout: {output_file}")

    # Build a complex filtergraph:
    # 1. Create a dark background canvas (1080x1920)
    # 2. Scale the source video to fit middle zone (1020x1120 max)
    # 3. Overlay video onto canvas at position (30, 350)
    # 4. Draw text overlays for top and bottom zones

    # Escape text for ffmpeg drawtext
    def esc(t: str) -> str:
        return t.replace("'", "'\\''").replace(":", "\\:").replace("%", "%%")

    hook_escaped = esc(hook_text)
    caption_escaped = esc(caption_text)
    accent_escaped = esc(accent_word)
    branding = esc("EXAI GLOBAL")

    filter_complex = (
        # Dark background
        f"color=c=0x0a0a0f:s=1080x1920:d=60[bg];"
        # Scale video to fit middle zone with padding
        f"[0:v]scale=1020:1120:force_original_aspect_ratio=decrease,"
        f"pad=1020:1120:(ow-iw)/2:(oh-ih)/2:color=0x0a0a0f[vid];"
        # Overlay video on background
        f"[bg][vid]overlay=30:350:shortest=1[comp];"
        # Top zone: branding
        f"[comp]drawtext=text='{branding}':fontsize=36:fontcolor=cyan:"
        f"x=40:y=30:fontfile=/System/Library/Fonts/Helvetica.ttc[b1];"
        # Top zone: AI NEWS badge
        f"[b1]drawtext=text='AI NEWS':fontsize=28:fontcolor=red:"
        f"box=1:boxcolor=red@0.3:boxborderw=8:"
        f"x=380:y=32[b2];"
        # Top zone: hook text (main)
        f"[b2]drawtext=text='{hook_escaped}':fontsize=52:fontcolor=white:"
        f"x=40:y=100:fontfile=/System/Library/Fonts/Helvetica.ttc[b3];"
        # Top zone: accent word in yellow
        f"[b3]drawtext=text='{accent_escaped}':fontsize=52:fontcolor=#FFD700:"
        f"x=40:y=200:fontfile=/System/Library/Fonts/Helvetica.ttc[b4];"
        # Bottom zone: caption
        f"[b4]drawtext=text='{caption_escaped}':fontsize=32:fontcolor=white:"
        f"x=40:y=1500:fontfile=/System/Library/Fonts/Helvetica.ttc[b5];"
        # Bottom zone: subscribe CTA (appears last 5 seconds, approximate with enable)
        f"[b5]drawtext=text='SUBSCRIBE for daily AI':fontsize=28:"
        f"fontcolor=cyan:x=300:y=1850:"
        f"fontfile=/System/Library/Fonts/Helvetica.ttc:"
        f"enable='gte(t,max_t-5)'"
    )

    # Simpler approach: use enable based on duration minus 5
    vid_dur = get_video_duration(video_file)
    if vid_dur <= 0:
        vid_dur = 30
    cta_start = max(0, vid_dur - 5)

    # Replace the enable expression with a concrete time
    filter_complex = filter_complex.replace("max_t-5", str(cta_start))

    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-filter_complex", filter_complex,
        "-map", "[b5]" if "enable='gte" not in filter_complex else "[b5]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(min(vid_dur, 58)),
        "-shortest",
        output_file,
    ]

    # Rebuild with simpler approach — overlay + drawtext in one pass
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x0a0a0f:s=1080x1920:d={min(vid_dur, 58)}:r=30",
        "-i", video_file,
        "-filter_complex",
        (
            f"[1:v]scale=1020:-2,pad=1020:1120:(ow-iw)/2:(oh-ih)/2:color=0x0a0a0f[vid];"
            f"[0:v][vid]overlay=30:350:shortest=1[comp];"
            f"[comp]drawtext=text='{branding}':fontsize=36:fontcolor=cyan:"
            f"x=40:y=30[b1];"
            f"[b1]drawtext=text='{hook_escaped}':fontsize=48:fontcolor=white:"
            f"x=40:y=100[b2];"
            f"[b2]drawtext=text='{accent_escaped}':fontsize=48:fontcolor=#FFD700:"
            f"x=40:y=200[b3];"
            f"[b3]drawtext=text='{caption_escaped}':fontsize=32:fontcolor=white:"
            f"x=40:y=1500[b4];"
            f"[b4]drawtext=text='SUBSCRIBE for daily AI':fontsize=28:"
            f"fontcolor=cyan:x=300:y=1850:"
            f"enable='gte(t\\,{cta_start})'"
        ),
        "-map", "[b4]",
        "-map", "1:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(min(vid_dur, 58)),
        "-shortest",
        output_file,
    ]

    # Fix: map the last filter output (with CTA)
    # The drawtext chain ends at the enable filter output — need to name it
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=0x0a0a0f:s=1080x1920:d={min(vid_dur, 58)}:r=30",
        "-i", video_file,
        "-filter_complex",
        (
            f"[1:v]scale=1020:-2,pad=1020:1120:(ow-iw)/2:(oh-ih)/2:color=0x0a0a0f[vid];"
            f"[0:v][vid]overlay=30:350:shortest=1,"
            f"drawtext=text='{branding}':fontsize=36:fontcolor=cyan:x=40:y=30,"
            f"drawtext=text='{hook_escaped}':fontsize=48:fontcolor=white:x=40:y=100,"
            f"drawtext=text='{accent_escaped}':fontsize=48:fontcolor=#FFD700:x=40:y=200,"
            f"drawtext=text='{caption_escaped}':fontsize=32:fontcolor=white:x=40:y=1500,"
            f"drawtext=text='SUBSCRIBE for daily AI':fontsize=28:"
            f"fontcolor=cyan:x=300:y=1850:"
            f"enable='gte(t\\,{cta_start})'[out]"
        ),
        "-map", "[out]",
        "-map", "1:a?",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(min(vid_dur, 58)),
        "-shortest",
        output_file,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        log.error(f"  ffmpeg three-zone FAILED: {result.stderr[-500:]}")
        return False
    log.info(f"  Three-zone layout complete: {output_file}")
    return True


# ──────────────────────────────────────────────
# Slot producers
# ──────────────────────────────────────────────

def produce_slot_1():
    """TYPE 1 — 'AI JUST DID THIS' — shocking demo clip."""
    log.info("=== SLOT 1: AI JUST DID THIS ===")
    brief = get_brief_text()

    data = gemini_call(f"""From today's AI news, pick the single most visually shocking AI demo story.
Return JSON:
{{
  "title": "short YouTube title under 50 chars with emoji",
  "search_query": "YouTube search query to find a demo video of this, last 48 hours",
  "hook_text": "3-5 word hook for top of screen",
  "accent_word": "1 keyword to highlight in yellow",
  "caption": "1-line caption for bottom zone, max 60 chars",
  "description": "YouTube description 2-3 sentences",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

NEWS CONTEXT:
{brief[:3000]}""")

    video = download_video(data["search_query"], max_duration=120)
    if not video:
        log.error("  Could not download demo video, trying fallback search")
        video = download_video("AI demo 2026 viral", max_duration=120)
    if not video:
        raise RuntimeError("No video found for slot 1")

    # Extract best 25-30 second segment (from 5s in to skip intros)
    dur = get_video_duration(video)
    start = min(5, dur * 0.1)
    seg_dur = min(28, dur - start)
    segment = f"{WORK_DIR}/slot1_segment.mp4"
    extract_segment(video, start, seg_dur, segment)

    out = output_path(1)
    ok = three_zone_layout(
        segment, data["hook_text"], data["caption"], data["accent_word"], out
    )
    if not ok:
        raise RuntimeError("Three-zone layout failed for slot 1")

    save_meta(1, data["title"], data["description"], data["tags"])
    log.info(f"  SLOT 1 DONE: {out}")


def produce_slot_2():
    """TYPE 2 — 'DAY X/7 SERIES' — AI tool showcase via Remotion."""
    day = get_series_day()
    log.info(f"=== SLOT 2: DAY {day}/7 SERIES ===")
    brief = get_brief_text()

    data = gemini_call(f"""Pick an AI tool to showcase for a "Day {day}/7" YouTube Short series.
It should be a trending or newly-released AI tool. Generate content for a 35-second motion graphics short.

Return JSON:
{{
  "tool_name": "Name of the AI tool",
  "title": "Day {day}/7: Tool Name",
  "lines": ["What it does (max 10 words)", "Why it's game-changing (max 10 words)", "How to try it today (max 10 words)"],
  "accent_color": "#hex color that matches the tool's brand",
  "description": "YouTube description 2-3 sentences",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

NEWS CONTEXT:
{brief[:2000]}""")

    out = output_path(2)
    props = {
        "title": data["title"],
        "lines": data["lines"],
        "accentColor": data.get("accent_color", "#00aaff"),
    }
    ok = render_remotion(props, out)
    if not ok:
        raise RuntimeError("Remotion render failed for slot 2")

    save_meta(2, data["title"], data["description"], data["tags"])
    log.info(f"  SLOT 2 DONE: {out}")


def produce_slot_nlm():
    """TYPE 3, 5, 8 — NotebookLM Animated — write marker file for existing pipeline."""
    log.info("=== SLOTS 3, 5, 8: NotebookLM Animated ===")
    brief = get_brief_text()

    data = gemini_call(f"""Pick 3 different AI news stories for NotebookLM animated YouTube Shorts.
Each needs a 40-second narration script (~90-100 words) with a clear ending.

Return JSON array:
[
  {{
    "slot": 3,
    "title": "viral title under 50 chars with emoji",
    "script": "NotebookLM narration script, 90-100 words, one story, complete ending",
    "overlay_lines": ["line1 max 8 words", "line2", "line3"]
  }},
  {{
    "slot": 5,
    "title": "...",
    "script": "...",
    "overlay_lines": ["..."]
  }},
  {{
    "slot": 8,
    "title": "...",
    "script": "...",
    "overlay_lines": ["..."]
  }}
]

NEWS CONTEXT:
{brief[:3000]}""")

    marker_file = f"{SHORTS_DIR}/nlm_needed_{DATE_STR}.txt"
    with open(marker_file, "w") as f:
        f.write(json.dumps(data, indent=2))
    log.info(f"  NLM marker written: {marker_file}")

    for item in data:
        slot = item["slot"]
        save_meta(
            slot,
            item["title"],
            f"NotebookLM animated short: {item['title']}",
            ["AI", "news", "shorts", "NotebookLM"],
        )
    log.info("  SLOTS 3, 5, 8 marker file written — existing pipeline will produce videos")


def produce_slot_4():
    """TYPE 4 — 'VS COMPARISON' — model comparison via Remotion."""
    log.info("=== SLOT 4: VS COMPARISON ===")
    brief = get_brief_text()

    data = gemini_call(f"""Create content for a 30-second "VS" comparison YouTube Short about AI models.
Pick 2-3 AI models to compare on a specific task (e.g., coding, image gen, reasoning).

Return JSON:
{{
  "title": "Model A vs Model B: Who Wins? with emoji",
  "lines": [
    "TASK: specific task being compared",
    "MODEL A: score or result (e.g., GPT-5: 94%)",
    "MODEL B: score or result (e.g., Claude 4: 97%)",
    "WINNER: brief verdict"
  ],
  "accent_color": "#ff4444",
  "description": "YouTube description 2-3 sentences",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

NEWS CONTEXT:
{brief[:2000]}""")

    out = output_path(4)
    props = {
        "title": data["title"],
        "lines": data["lines"],
        "accentColor": data.get("accent_color", "#ff4444"),
    }
    ok = render_remotion(props, out, duration_frames=30 * 30)  # 30 seconds
    if not ok:
        raise RuntimeError("Remotion render failed for slot 4")

    save_meta(4, data["title"], data["description"], data["tags"])
    log.info(f"  SLOT 4 DONE: {out}")


def produce_slot_6():
    """TYPE 6 — 'ONE PROMPT DOES THIS' — before/after clip, three-zone layout."""
    log.info("=== SLOT 6: ONE PROMPT DOES THIS ===")
    brief = get_brief_text()

    data = gemini_call(f"""Pick an AI transformation/generation story for a "One Prompt Does This" YouTube Short.
Something where a single prompt produces an amazing result (image gen, code gen, video gen, etc).

Return JSON:
{{
  "title": "One Prompt Does THIS with emoji, under 50 chars",
  "search_query": "YouTube search query to find a before/after AI demo",
  "hook_text": "ONE PROMPT",
  "accent_word": "DOES THIS",
  "caption": "caption for bottom zone, max 60 chars",
  "description": "YouTube description 2-3 sentences",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

NEWS CONTEXT:
{brief[:2000]}""")

    video = download_video(data["search_query"], max_duration=120)
    if not video:
        video = download_video("AI one prompt transformation 2026", max_duration=120)
    if not video:
        raise RuntimeError("No video found for slot 6")

    dur = get_video_duration(video)
    start = min(3, dur * 0.1)
    seg_dur = min(25, dur - start)
    segment = f"{WORK_DIR}/slot6_segment.mp4"
    extract_segment(video, start, seg_dur, segment)

    out = output_path(6)
    ok = three_zone_layout(
        segment, data["hook_text"], data["caption"], data["accent_word"], out
    )
    if not ok:
        raise RuntimeError("Three-zone layout failed for slot 6")

    save_meta(6, data["title"], data["description"], data["tags"])
    log.info(f"  SLOT 6 DONE: {out}")


def produce_slot_7():
    """TYPE 7 — 'QUICK AI HACK' — 15s ultra-short via Remotion."""
    log.info("=== SLOT 7: QUICK AI HACK (15s) ===")
    brief = get_brief_text()

    data = gemini_call(f"""Create content for a 15-second ultra-short "Quick AI Hack" YouTube Short.
One single actionable AI tip that viewers can use immediately. Maximum completion rate.

Return JSON:
{{
  "title": "Quick AI Hack with emoji, under 40 chars",
  "lines": ["Step 1: do this (max 8 words)", "Step 2: then this (max 8 words)", "Result: what you get (max 8 words)"],
  "accent_color": "#00ff88",
  "description": "YouTube description 2-3 sentences",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

NEWS CONTEXT:
{brief[:1500]}""")

    out = output_path(7)
    props = {
        "title": data["title"],
        "lines": data["lines"],
        "accentColor": data.get("accent_color", "#00ff88"),
    }
    ok = render_remotion(props, out, duration_frames=450)  # 15 seconds at 30fps
    if not ok:
        raise RuntimeError("Remotion render failed for slot 7")

    save_meta(7, data["title"], data["description"], data["tags"])
    log.info(f"  SLOT 7 DONE: {out}")


def produce_slot_9():
    """TYPE 9 — 'TOP 3 AI TOOLS' — listicle via Remotion."""
    log.info("=== SLOT 9: TOP 3 AI TOOLS ===")
    brief = get_brief_text()

    data = gemini_call(f"""Create content for a "Top 3 AI Tools" YouTube Short listicle.
Pick 3 tools that are trending or newly released this week.

Return JSON:
{{
  "title": "Top 3 AI Tools You Need with emoji, under 50 chars",
  "lines": [
    "1. ToolName — one-line description max 10 words",
    "2. ToolName — one-line description max 10 words",
    "3. ToolName — one-line description max 10 words"
  ],
  "accent_color": "#ffaa00",
  "description": "YouTube description 2-3 sentences",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

NEWS CONTEXT:
{brief[:2000]}""")

    out = output_path(9)
    props = {
        "title": data["title"],
        "lines": data["lines"],
        "accentColor": data.get("accent_color", "#ffaa00"),
    }
    ok = render_remotion(props, out)
    if not ok:
        raise RuntimeError("Remotion render failed for slot 9")

    save_meta(9, data["title"], data["description"], data["tags"])
    log.info(f"  SLOT 9 DONE: {out}")


def produce_slot_10():
    """TYPE 10 — 'CONTROVERSIAL TAKE' — opinion short via Remotion."""
    log.info("=== SLOT 10: CONTROVERSIAL TAKE ===")
    brief = get_brief_text()

    data = gemini_call(f"""Create content for a "Controversial Take" YouTube Short.
A bold, debate-sparking opinion about AI that will drive comments. End with "Agree? Comment below."

Return JSON:
{{
  "title": "Hot Take title with emoji, under 50 chars",
  "lines": [
    "Bold opening statement max 10 words",
    "Supporting argument max 10 words",
    "Counter-intuitive conclusion max 10 words",
    "Agree? Comment below"
  ],
  "accent_color": "#ff2222",
  "description": "YouTube description 2-3 sentences. Include a question to drive comments.",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

NEWS CONTEXT:
{brief[:2000]}""")

    out = output_path(10)
    props = {
        "title": data["title"],
        "lines": data["lines"],
        "accentColor": data.get("accent_color", "#ff2222"),
    }
    ok = render_remotion(props, out)
    if not ok:
        raise RuntimeError("Remotion render failed for slot 10")

    save_meta(10, data["title"], data["description"], data["tags"])
    log.info(f"  SLOT 10 DONE: {out}")


# ──────────────────────────────────────────────
# Dispatcher
# ──────────────────────────────────────────────

SLOT_PRODUCERS = {
    1: produce_slot_1,
    2: produce_slot_2,
    3: produce_slot_nlm,
    4: produce_slot_4,
    5: produce_slot_nlm,  # same function writes marker for 3, 5, 8
    6: produce_slot_6,
    7: produce_slot_7,
    8: produce_slot_nlm,
    9: produce_slot_9,
    10: produce_slot_10,
}


def produce_slot(slot: int):
    """Produce a single slot, handling errors gracefully."""
    t0 = time.time()
    try:
        producer = SLOT_PRODUCERS.get(slot)
        if not producer:
            log.error(f"Unknown slot: {slot}")
            return False
        producer()
        elapsed = time.time() - t0
        log.info(f"  Slot {slot} completed in {elapsed:.1f}s\n")
        return True
    except Exception as e:
        elapsed = time.time() - t0
        log.error(f"  Slot {slot} FAILED after {elapsed:.1f}s: {e}\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Daily Shorts Production Pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slot", type=int, help="Produce a specific slot (1-10)")
    group.add_argument("--all", action="store_true", help="Produce all non-NLM slots")
    group.add_argument("--everything", action="store_true", help="Produce all slots including NLM marker")
    args = parser.parse_args()

    log.info("=" * 60)
    log.info(f"DAILY SHORTS PRODUCTION — {DATE_STR}")
    log.info("=" * 60)

    t_start = time.time()
    results = {}

    if args.slot:
        slot = args.slot
        if slot not in ALL_SLOTS:
            log.error(f"Invalid slot {slot}. Must be 1-10.")
            sys.exit(1)
        # NLM slots: only call the producer once (it handles 3, 5, 8 together)
        if slot in NLM_SLOTS:
            results[slot] = produce_slot(3)  # always call via slot 3
        else:
            results[slot] = produce_slot(slot)

    elif args.all:
        log.info(f"Producing {len(NON_NLM_SLOTS)} non-NLM slots: {NON_NLM_SLOTS}")
        for slot in NON_NLM_SLOTS:
            results[slot] = produce_slot(slot)

    elif args.everything:
        log.info(f"Producing all {len(ALL_SLOTS)} slots")
        # Produce NLM marker first (once), then all others
        results[3] = produce_slot(3)
        results[5] = results[3]
        results[8] = results[3]
        for slot in NON_NLM_SLOTS:
            results[slot] = produce_slot(slot)

    # Summary
    elapsed = time.time() - t_start
    ok = sum(1 for v in results.values() if v)
    fail = sum(1 for v in results.values() if not v)
    log.info("=" * 60)
    log.info(f"PRODUCTION COMPLETE — {ok} succeeded, {fail} failed, {elapsed:.1f}s total")
    log.info(f"Output: {SHORTS_DIR}/")
    log.info("=" * 60)

    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
