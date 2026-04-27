#!/usr/bin/env python3
"""
Shorts Machine -- Automated NotebookLM shorts production + YouTube upload + self-optimization.

Phases:
  1. Content Planning   -- Gemini picks stories, informed by past performance
  2. Parallel Production -- CDP opens 3-5 NotebookLM tabs, generates videos concurrently
  3. Post-Processing     -- Silence-based trim, watermark overlay, immediate YouTube upload
  4. Self-Optimization   -- Pull view counts, analyze what works, feed back into planning

CLI:
  python3 shorts_machine.py --produce     # Full pipeline
  python3 shorts_machine.py --optimize    # Pull stats + analyze
  python3 shorts_machine.py --status      # Show today's state
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import time
import datetime
import subprocess
import glob
import shutil
import re
import argparse
import logging
import traceback
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

TODAY = datetime.date.today()
DATE_STR = TODAY.isoformat()
TIMESTAMP = lambda: time.strftime("%H:%M:%S")

CDP = "http://127.0.0.1:9222"
GEMINI_KEY = "GEMINI_API_KEY_PLACEHOLDER"
GEMINI_MODEL = "gemini-2.5-flash"

SHORTS_DIR = f"/tmp/morningbrief/shorts"
WORK_DIR = f"/tmp/morningbrief/shorts_machine_{DATE_STR}"
DL_DIR = f"/tmp/morningbrief/downloads_machine"
PERF_FILE = "/tmp/morningbrief/shorts/performance.json"
UPLOAD_LOG = "/tmp/morningbrief/shorts/uploads.json"
WATERMARK_PATH = "/tmp/morningbrief/shorts/exai_watermark.png"
YOUTUBE_TOKEN = os.path.expanduser("~/.youtube-exai/token.json")
LOG_FILE = "/tmp/morningbrief/shorts/machine.log"

PARALLEL_TABS = 3          # How many NLM tabs to run at once
MAX_SCRIPTS = 3            # 3 shorts/day is optimal (data: 4.4x growth vs 1/day, 10+/day hurts)
BATCH_SIZE = 3             # All 3 in one parallel batch
NLM_TIMEOUT = 2400         # 40 min max wait per video
PRODUCTION_METHOD = "notebooklm"  # ONLY NotebookLM cinematic — the one format that works
POLL_INTERVAL = 10         # Seconds between status checks

os.makedirs(SHORTS_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)
os.makedirs(DL_DIR, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("shorts_machine")

# Thread-safe CDP message ID counter
_mid_lock = Lock()
_mid = [0]

def next_mid():
    with _mid_lock:
        _mid[0] += 1
        return _mid[0]


# ═══════════════════════════════════════════════════════════════════════════════
# CDP Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def cdp(ws, method, params=None):
    """Send a CDP command and wait for the matching response."""
    mid = next_mid()
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            ws.settimeout(30)
            r = json.loads(ws.recv())
            if r.get("id") == mid:
                return r
        except Exception:
            break
    return {"error": "timeout"}


def js(ws, expr):
    """Evaluate JS in the page and return the value."""
    r = cdp(ws, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True,
    })
    return r.get("result", {}).get("result", {}).get("value")


def get_any_nlm_ws():
    """Get a websocket connection to any existing NotebookLM tab."""
    import websocket
    try:
        resp = urllib.request.urlopen(f"{CDP}/json", timeout=5)
        tabs = json.loads(resp.read())
        for t in tabs:
            url = t.get("url", "")
            if "notebooklm.google.com" in url and "accounts" not in url and "Rotate" not in url:
                return websocket.create_connection(t["webSocketDebuggerUrl"], timeout=10)
    except Exception:
        pass
    return None


def connect_tab(tab_ws_url):
    """Connect to a specific tab by its websocket URL."""
    import websocket
    try:
        ws = websocket.create_connection(tab_ws_url, timeout=15)
        cdp(ws, "Runtime.enable")
        cdp(ws, "Page.enable")
        cdp(ws, "DOM.enable")
        return ws
    except Exception as e:
        log.warning("Failed to connect to tab: %s", e)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Watermark Generation
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_watermark():
    """Create EXAI GLOBAL watermark PNG if it doesn't exist."""
    if os.path.exists(WATERMARK_PATH) and os.path.getsize(WATERMARK_PATH) > 100:
        return WATERMARK_PATH
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGBA", (400, 60), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except Exception:
            font = ImageFont.load_default()
        draw.text((10, 10), "EXAI GLOBAL", fill=(255, 255, 255, 180), font=font)
        img.save(WATERMARK_PATH)
        log.info("Created watermark at %s", WATERMARK_PATH)
    except Exception as e:
        log.warning("Could not create watermark: %s", e)
        return None
    return WATERMARK_PATH


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: Content Planning
# ═══════════════════════════════════════════════════════════════════════════════

def load_performance_context():
    """Load past performance data to inform Gemini's script generation."""
    if not os.path.exists(PERF_FILE):
        return ""
    try:
        with open(PERF_FILE) as f:
            perf = json.load(f)
        insights = perf.get("insights", [])
        top_topics = perf.get("top_topics", [])
        if not insights and not top_topics:
            return ""
        ctx = "\n\nPERFORMANCE DATA FROM PAST SHORTS:\n"
        if top_topics:
            ctx += "Top performing topics: " + ", ".join(top_topics[:5]) + "\n"
        if insights:
            for ins in insights[:5]:
                ctx += f"- {ins}\n"
        ctx += "\nPrioritize formats and topics similar to the top performers.\n"
        return ctx
    except Exception:
        return ""


def get_latest_brief():
    """Find the latest morning brief file."""
    today_brief = f"/tmp/morningbrief/brief_{DATE_STR}.md"
    if os.path.exists(today_brief):
        with open(today_brief) as f:
            return f.read()
    briefs = sorted(glob.glob("/tmp/morningbrief/brief_*.md"))
    if briefs:
        with open(briefs[-1]) as f:
            return f.read()
    return None


def generate_scripts(count=10):
    """Use Gemini to generate short scripts based on today's news + performance data."""
    log.info("PHASE 1: Generating %d short scripts via Gemini...", count)

    brief = get_latest_brief()
    if not brief:
        log.error("No brief found -- cannot generate scripts")
        return []

    perf_context = load_performance_context()

    # Load strategy improvements if available
    strategy_context = ""
    prompt_additions_file = os.path.join(SHORTS_DIR, "prompt_additions.txt")
    if os.path.exists(prompt_additions_file):
        with open(prompt_additions_file) as f:
            strategy_context = f"\nSTRATEGY LEARNINGS FROM SELF-IMPROVEMENT ENGINE:\n{f.read()}\n"

    strategy_file = os.path.join(SHORTS_DIR, "strategy.json")
    if os.path.exists(strategy_file):
        try:
            with open(strategy_file) as f:
                strat = json.load(f)
            title_patterns = strat.get("title_patterns", [])
            engagement_tactics = strat.get("engagement_tactics", [])
            if title_patterns:
                strategy_context += f"\nPROVEN TITLE PATTERNS: {', '.join(title_patterns[:5])}"
            if engagement_tactics:
                strategy_context += f"\nENGAGEMENT TACTICS TO USE: {', '.join(engagement_tactics[:3])}"
        except Exception:
            pass

    prompt = f"""You are a viral YouTube Shorts scriptwriter for EXAI GLOBAL, an AI news channel.
We post exactly 3 shorts per day — each one MUST be the absolute best quality.

From this AI news brief, create {count} unique short video scripts for NotebookLM narration.

THE 3 SHORTS MUST BE DIFFERENT FORMATS:
1. BREAKING NEWS — the biggest AI story today, told urgently
2. DEMO/COMPARISON — show what an AI tool can do, or compare two AI models
3. HOT TAKE/CONTROVERSIAL — a bold opinion that drives comments and shares

RULES:
- Each script is 90-100 words (about 40 seconds of narration)
- ONE topic per script — tell it as a compelling story with a hook
- Start with a gripping hook in the FIRST sentence (question, shocking stat, or bold claim)
- The hook must work in under 2 seconds — this determines if viewers swipe away
- End with "Subscribe to EXAI Global for daily AI news" or similar CTA
- Make it cinematic — describe dramatic visuals NotebookLM should generate
- No text instructions — only narration and visual descriptions
- Each short should make viewers want to SHARE it with someone

ANTI-SLOP RULES (CRITICAL — YouTube bans AI slop channels):
- NO generic filler ("in today's video", "let's dive in", "stay tuned")
- NO clickbait that doesn't deliver — the script MUST contain the actual news/insight promised
- Every sentence must contain REAL information — specific tool names, specific capabilities, specific numbers
- Sound like a knowledgeable insider sharing news with a friend, NOT a robot reading a template
- Each script must feel UNIQUE — different angle, different energy, different insight
- If you can't write something genuinely interesting about a topic, SKIP IT
{strategy_context}

{perf_context}

BRIEF:
{brief[:4000]}

Return a JSON array of exactly {count} objects:
[{{"title": "YouTube title with emoji under 50 chars #Shorts", "script": "the 90-100 word NotebookLM script", "topic": "topic category", "tags": ["tag1", "tag2", "tag3"]}}]"""

    try:
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}",
            data=json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        scripts = json.loads(result["candidates"][0]["content"]["parts"][0]["text"])
        scripts = scripts[:count]
        log.info("Generated %d scripts:", len(scripts))
        for i, s in enumerate(scripts):
            log.info("  %2d. %s (%d words)", i + 1, s["title"], len(s["script"].split()))

        # Save scripts to disk
        scripts_file = os.path.join(WORK_DIR, "scripts.json")
        with open(scripts_file, "w") as f:
            json.dump(scripts, f, indent=2)
        return scripts
    except Exception as e:
        log.error("Gemini script generation failed: %s", e)
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: Parallel NotebookLM Production
# ═══════════════════════════════════════════════════════════════════════════════

def create_notebook_and_generate(script_data, index):
    """
    Open a new NotebookLM tab, paste the script, trigger video generation.
    Returns dict with tab info or None on failure.
    """
    import websocket

    short_title = script_data["title"][:40]
    log.info("[Short %d] Starting: %s", index + 1, short_title)

    nlm_script = f"""**VIDEO INSTRUCTIONS:** Create a short animated AI news clip about ONE story. Start with a hook. Make it cinematic. DO NOT generate any text -- only animated visuals and narration.

{script_data['script']}"""

    # Get a WS connection to create a new tab
    ws = get_any_nlm_ws()
    if not ws:
        log.error("[Short %d] No browser connection", index + 1)
        return None

    try:
        cdp(ws, "Runtime.enable")
        r = cdp(ws, "Target.createTarget", {"url": "https://notebooklm.google.com/"})
        target_id = r.get("result", {}).get("targetId", "")
        ws.close()
    except Exception as e:
        log.error("[Short %d] Failed to create tab: %s", index + 1, e)
        return None

    if not target_id:
        log.error("[Short %d] No target ID returned", index + 1)
        return None

    time.sleep(5)

    # Find the new tab's websocket URL
    try:
        resp = urllib.request.urlopen(f"{CDP}/json", timeout=5)
        tabs = json.loads(resp.read())
    except Exception:
        log.error("[Short %d] Cannot list tabs", index + 1)
        return None

    tab_ws_url = None
    for t in tabs:
        if t.get("id") == target_id:
            tab_ws_url = t["webSocketDebuggerUrl"]
            break

    if not tab_ws_url:
        log.error("[Short %d] Tab websocket not found", index + 1)
        return None

    ws = connect_tab(tab_ws_url)
    if not ws:
        return None

    try:
        # Click "Create new"
        js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Create new'))?.click(); })()""")
        time.sleep(5)

        # Click "Copied text"
        js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Copied text'))?.click(); })()""")
        time.sleep(3)

        # Find textarea and paste script
        pasted = False
        for attempt in range(5):
            search = cdp(ws, "DOM.performSearch", {"query": "textarea[placeholder*='Paste']"})
            count = search.get("result", {}).get("resultCount", 0)
            if count > 0:
                sid = search["result"]["searchId"]
                r = cdp(ws, "DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": 1})
                node_ids = r.get("result", {}).get("nodeIds", [])
                if node_ids:
                    cdp(ws, "DOM.focus", {"nodeId": node_ids[0]})
                    time.sleep(0.5)
                    cdp(ws, "Input.insertText", {"text": nlm_script})
                    time.sleep(2)
                    js(ws, """(() => { const b = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Insert'); if(b){b.disabled=false;b.click();} })()""")
                    time.sleep(8)
                    pasted = True
                    break
            time.sleep(2)

        if not pasted:
            log.error("[Short %d] Failed to paste script", index + 1)
            ws.close()
            return None

        # Verify source added
        sources = js(ws, "document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
        if sources == '0':
            log.error("[Short %d] Source not added", index + 1)
            ws.close()
            return None

        # Dismiss any dialogs
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
        cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
        time.sleep(2)

        # Click Video tab
        js(ws, """(() => { const els = document.querySelectorAll('*'); for (const el of els) { if (el.childElementCount === 0 && el.textContent.trim().startsWith('Video')) { el.closest('button, [role="button"], a, [tabindex]')?.click(); return; }} })()""")
        time.sleep(3)

        # Click Generate
        js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Generate')?.click(); })()""")
        time.sleep(3)

        nb_url = js(ws, "window.location.href") or ""
        log.info("[Short %d] Generating: %s", index + 1, nb_url.split("/notebook/")[-1][:20] if "/notebook/" in nb_url else "unknown")
        ws.close()

        return {
            "index": index,
            "tab_ws_url": tab_ws_url,
            "target_id": target_id,
            "nb_url": nb_url,
            "title": script_data["title"],
            "topic": script_data.get("topic", "AI"),
            "tags": script_data.get("tags", ["AI", "Shorts"]),
            "script": script_data["script"],
            "started_at": time.time(),
        }
    except Exception as e:
        log.error("[Short %d] Error during notebook setup: %s\n%s", index + 1, e, traceback.format_exc())
        try:
            ws.close()
        except Exception:
            pass
        return None


def poll_video_ready(notebook):
    """Check if a NotebookLM video is ready. Returns True/False."""
    ws = connect_tab(notebook["tab_ws_url"])
    if not ws:
        return False
    try:
        ready = js(ws, """(() => {
            const t = document.body.innerText;
            if (t.includes('Good video') || t.includes('Bad video') || t.includes('is ready')) return true;
            return false;
        })()""")
        ws.close()
        return bool(ready)
    except Exception:
        try:
            ws.close()
        except Exception:
            pass
        return False


def download_video(notebook):
    """Download the video from a ready NotebookLM tab. Returns file path or None."""
    import websocket

    idx = notebook["index"]
    dl_dir = os.path.join(DL_DIR, f"machine_{idx}")
    os.makedirs(dl_dir, exist_ok=True)
    # Clear previous downloads
    for f in glob.glob(f"{dl_dir}/*"):
        os.unlink(f)

    ws = connect_tab(notebook["tab_ws_url"])
    if not ws:
        return None

    try:
        cdp(ws, "Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": dl_dir})

        # Get video URL
        video_url = ""
        for attempt in range(5):
            # Click Video Overview tab
            js(ws, """(() => { document.querySelectorAll('*').forEach(el => { if (el.childElementCount === 0 && el.textContent.trim() === 'Video Overview') { el.closest('button, [role="button"], a, [tabindex]')?.click(); }}); })()""")
            time.sleep(3)
            # Click Play
            js(ws, """(() => { document.querySelector('[aria-label*="Play"]')?.click(); })()""")
            time.sleep(3)
            # Ensure video is visible
            js(ws, """(() => { document.querySelectorAll('video').forEach(v => { v.hidden=false; v.style.display='block'; v.load(); }); })()""")
            time.sleep(2)
            video_url = js(ws, "document.querySelector('video')?.src || ''") or ""
            if video_url and len(video_url) > 50:
                break
            time.sleep(2)

        if not video_url or len(video_url) < 50:
            log.error("[Short %d] Could not get video URL", idx + 1)
            ws.close()
            return None

        # Construct download URL
        base = video_url.split('=m22')[0] if '=m22' in video_url else video_url.split('?')[0]
        dl_url = base + "=dv"

        r = cdp(ws, "Target.createTarget", {"url": dl_url})
        dl_target = r.get("result", {}).get("targetId", "")

        # Wait for download
        raw_file = None
        for k in range(90):  # Up to ~7.5 min
            time.sleep(5)
            done = [f for f in glob.glob(f"{dl_dir}/*") if not f.endswith('.crdownload')]
            if done:
                dest = os.path.join(WORK_DIR, f"short_{idx + 1}_raw.mp4")
                shutil.copy2(done[0], dest)
                raw_file = dest
                size_mb = os.path.getsize(dest) / 1024 / 1024
                log.info("[Short %d] Downloaded: %.1f MB", idx + 1, size_mb)
                break

        # Clean up download tab
        if dl_target:
            try:
                cdp(ws, "Target.closeTarget", {"targetId": dl_target})
            except Exception:
                pass

        # Close the notebook tab
        try:
            cdp(ws, "Target.closeTarget", {"targetId": notebook["target_id"]})
        except Exception:
            pass

        ws.close()
        return raw_file
    except Exception as e:
        log.error("[Short %d] Download error: %s", idx + 1, e)
        try:
            ws.close()
        except Exception:
            pass
        return None


def produce_batch(scripts, start_index=0):
    """
    Produce a batch of shorts via NotebookLM in parallel.
    Yields (notebook_info, raw_file_path) tuples as videos become ready.
    """
    batch = scripts[:PARALLEL_TABS]
    log.info("Starting batch of %d shorts (indices %d-%d)...",
             len(batch), start_index + 1, start_index + len(batch))

    # Phase 2a: Create all notebooks in parallel
    notebooks = []
    with ThreadPoolExecutor(max_workers=PARALLEL_TABS) as executor:
        futures = {
            executor.submit(create_notebook_and_generate, s, start_index + i): i
            for i, s in enumerate(batch)
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                notebooks.append(result)

    if not notebooks:
        log.error("No notebooks created in this batch")
        return

    log.info("%d/%d notebooks generating in parallel", len(notebooks), len(batch))

    # Phase 2b: Poll for completion, yield as soon as each is ready
    ready_set = set()
    failed_set = set()
    start_time = time.time()

    while len(ready_set) + len(failed_set) < len(notebooks):
        elapsed = time.time() - start_time
        if elapsed > NLM_TIMEOUT:
            for nb in notebooks:
                if nb["index"] not in ready_set and nb["index"] not in failed_set:
                    log.warning("[Short %d] Timed out after %d min -- skipping",
                                nb["index"] + 1, int(elapsed / 60))
                    failed_set.add(nb["index"])
            break

        for nb in notebooks:
            idx = nb["index"]
            if idx in ready_set or idx in failed_set:
                continue

            # Check per-video timeout
            video_elapsed = time.time() - nb["started_at"]
            if video_elapsed > NLM_TIMEOUT:
                log.warning("[Short %d] Individual timeout after %d min",
                            idx + 1, int(video_elapsed / 60))
                failed_set.add(idx)
                continue

            if poll_video_ready(nb):
                ready_set.add(idx)
                elapsed_min = (time.time() - nb["started_at"]) / 60
                log.info("[Short %d] Ready after %.1f min -- downloading...",
                         idx + 1, elapsed_min)

                raw_file = download_video(nb)
                if raw_file:
                    yield nb, raw_file
                else:
                    log.error("[Short %d] Download failed", idx + 1)

        remaining = len(notebooks) - len(ready_set) - len(failed_set)
        if remaining > 0 and int(elapsed) % 60 < POLL_INTERVAL:
            log.info("  [%dm%ds] %d/%d ready, %d pending...",
                     int(elapsed // 60), int(elapsed % 60),
                     len(ready_set), len(notebooks), remaining)

        time.sleep(POLL_INTERVAL)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: Post-Processing + Upload
# ═══════════════════════════════════════════════════════════════════════════════

def find_silence_trim_point(video_path, max_time=58):
    """Find the last silence point before max_time for clean sentence-boundary cut."""
    try:
        result = subprocess.run([
            "ffmpeg", "-i", video_path, "-af",
            "silencedetect=noise=-30dB:d=0.3",
            "-t", str(max_time + 5), "-f", "null", "-"
        ], capture_output=True, text=True, timeout=30)
        silences = re.findall(r'silence_end: ([\d.]+)', result.stderr)
        silences = [float(s) for s in silences if float(s) <= max_time]
        if silences:
            return silences[-1]
    except Exception:
        pass
    return max_time


def get_video_duration(path):
    """Get video duration in seconds."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True, timeout=10,
        )
        return float(json.loads(r.stdout)["format"]["duration"])
    except Exception:
        return 0


def post_process(raw_file, notebook_info):
    """
    Trim to <59s at silence boundary, add watermark, scale to 9:16.
    Returns final file path or None.
    """
    idx = notebook_info["index"]
    final_file = os.path.join(WORK_DIR, f"short_{idx + 1}_final.mp4")

    duration = get_video_duration(raw_file)
    if duration <= 0:
        log.error("[Short %d] Cannot read duration", idx + 1)
        return None

    if duration <= 59:
        trim_dur = duration
        log.info("[Short %d] %.0fs -- fits in Shorts", idx + 1, duration)
    else:
        trim_dur = find_silence_trim_point(raw_file, 58)
        log.info("[Short %d] %.0fs -> trimmed to %.1fs at sentence boundary",
                 idx + 1, duration, trim_dur)

    # Build ffmpeg filter: scale to 9:16 + watermark overlay
    watermark = ensure_watermark()
    if watermark and os.path.exists(watermark):
        # With watermark
        cmd = [
            "ffmpeg", "-y",
            "-i", raw_file,
            "-i", watermark,
            "-t", str(trim_dur),
            "-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[bg];"
            "[bg][1:v]overlay=W-w-20:H-h-20[out]",
            "-map", "[out]", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-ac", "2", "-ar", "44100",
            "-pix_fmt", "yuv420p", "-r", "30",
            "-movflags", "+faststart",
            final_file,
        ]
    else:
        # Without watermark
        cmd = [
            "ffmpeg", "-y",
            "-i", raw_file,
            "-t", str(trim_dur),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-ac", "2", "-ar", "44100",
            "-pix_fmt", "yuv420p", "-r", "30",
            "-map", "0:v:0", "-map", "0:a:0",
            "-movflags", "+faststart",
            final_file,
        ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        log.error("[Short %d] ffmpeg timed out", idx + 1)
        return None

    if os.path.exists(final_file) and os.path.getsize(final_file) > 10000:
        final_dur = get_video_duration(final_file)
        size_mb = os.path.getsize(final_file) / 1024 / 1024
        log.info("[Short %d] Post-processed: %.0fs, %.1f MB", idx + 1, final_dur, size_mb)
        return final_file
    else:
        log.error("[Short %d] Post-processing failed", idx + 1)
        return None


def get_longform_link():
    """Get today's longform YouTube video URL."""
    path = f"/tmp/morningbrief/youtube_{DATE_STR}.txt"
    if os.path.exists(path):
        with open(path) as f:
            url = f.read().strip()
        if url:
            return url
    files = sorted(glob.glob("/tmp/morningbrief/youtube_*.txt"))
    if files:
        with open(files[-1]) as f:
            return f.read().strip()
    return "youtube.com/@EXAIGlobal"


def upload_to_youtube(video_path, notebook_info):
    """Upload a single short to YouTube. Returns video URL or None."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    idx = notebook_info["index"]
    title = notebook_info["title"]
    if "#Shorts" not in title and "#shorts" not in title.lower():
        title = f"{title} #Shorts"
    title = title[:100]

    longform = get_longform_link()
    tags_list = notebook_info.get("tags", []) + ["AI", "Shorts", "EXAI", "AI News", "Tech"]
    tags_list = list(dict.fromkeys(tags_list))  # deduplicate

    description = (
        f"AI News {TODAY.strftime('%B %d, %Y')} #Shorts #AI #AINews #TechNews #EXAI\n\n"
        f"Full AI news report: {longform}\n\n"
        f"Subscribe for daily AI updates!\n\n"
        f"Topic: {notebook_info.get('topic', 'AI News')}"
    )

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags_list,
            "categoryId": "28",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    try:
        with open(YOUTUBE_TOKEN) as f:
            t = json.load(f)
        creds = Credentials(
            token=t["token"],
            refresh_token=t["refresh_token"],
            token_uri=t.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=t["client_id"],
            client_secret=t["client_secret"],
            scopes=t.get("scopes", [
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.force-ssl",
            ]),
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            t["token"] = creds.token
            with open(YOUTUBE_TOKEN, "w") as f:
                json.dump(t, f, indent=2)

        youtube = build("youtube", "v3", credentials=creds)
        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        log.info("[Short %d] Uploading to YouTube: %s", idx + 1, title)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.info("[Short %d] Upload progress: %d%%", idx + 1, int(status.progress() * 100))

        video_id = response["id"]
        video_url = f"https://youtu.be/{video_id}"
        log.info("[Short %d] UPLOADED: %s", idx + 1, video_url)

        # Pin comment
        try:
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": "Subscribe for daily AI news! New shorts every day.",
                            }
                        },
                    }
                },
            ).execute()
        except Exception:
            pass

        return {
            "video_id": video_id,
            "video_url": video_url,
            "title": title,
            "topic": notebook_info.get("topic", ""),
            "tags": tags_list,
            "uploaded_at": datetime.datetime.now().isoformat(),
            "date": DATE_STR,
        }
    except Exception as e:
        log.error("[Short %d] YouTube upload failed: %s\n%s", idx + 1, e, traceback.format_exc())
        return None


def log_upload(upload_info):
    """Append upload info to the persistent upload log."""
    data = []
    if os.path.exists(UPLOAD_LOG):
        try:
            with open(UPLOAD_LOG) as f:
                data = json.load(f)
        except Exception:
            data = []
    data.append(upload_info)
    with open(UPLOAD_LOG, "w") as f:
        json.dump(data, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: Self-Optimization
# ═══════════════════════════════════════════════════════════════════════════════

def run_optimization():
    """Pull YouTube view counts for recent shorts, analyze performance, save insights."""
    log.info("PHASE 4: Running self-optimization analysis...")

    if not os.path.exists(UPLOAD_LOG):
        log.info("No upload log found -- nothing to optimize")
        return

    with open(UPLOAD_LOG) as f:
        uploads = json.load(f)

    # Filter to last 7 days
    cutoff = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    recent = [u for u in uploads if u.get("date", "") >= cutoff]

    if not recent:
        log.info("No uploads in the last 7 days")
        return

    log.info("Found %d uploads in last 7 days", len(recent))

    # Pull view counts from YouTube API
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        with open(YOUTUBE_TOKEN) as f:
            t = json.load(f)
        creds = Credentials(
            token=t["token"],
            refresh_token=t["refresh_token"],
            token_uri=t.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=t["client_id"],
            client_secret=t["client_secret"],
            scopes=t.get("scopes", [
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.force-ssl",
            ]),
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        youtube = build("youtube", "v3", credentials=creds)

        # Get stats in batches of 50
        video_ids = [u["video_id"] for u in recent if "video_id" in u]
        stats_map = {}

        for batch_start in range(0, len(video_ids), 50):
            batch = video_ids[batch_start:batch_start + 50]
            resp = youtube.videos().list(
                part="statistics",
                id=",".join(batch),
            ).execute()
            for item in resp.get("items", []):
                vid = item["id"]
                s = item.get("statistics", {})
                stats_map[vid] = {
                    "views": int(s.get("viewCount", 0)),
                    "likes": int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                }

        # Merge stats into upload records
        for u in recent:
            vid = u.get("video_id", "")
            if vid in stats_map:
                u["stats"] = stats_map[vid]

        # Analyze
        with_stats = [u for u in recent if "stats" in u]
        if not with_stats:
            log.info("No stats available yet")
            return

        avg_views = sum(u["stats"]["views"] for u in with_stats) / len(with_stats)
        log.info("Average views: %.0f across %d shorts", avg_views, len(with_stats))

        # Sort by views
        ranked = sorted(with_stats, key=lambda u: u["stats"]["views"], reverse=True)

        # Top topics
        topic_views = {}
        topic_counts = {}
        for u in with_stats:
            topic = u.get("topic", "unknown")
            views = u["stats"]["views"]
            topic_views[topic] = topic_views.get(topic, 0) + views
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        topic_avg = {t: topic_views[t] / topic_counts[t] for t in topic_views}
        top_topics = sorted(topic_avg, key=topic_avg.get, reverse=True)

        # Generate insights
        insights = []
        for u in ranked[:3]:
            views = u["stats"]["views"]
            ratio = views / avg_views if avg_views > 0 else 0
            insights.append(
                f"'{u['title'][:50]}' got {views} views ({ratio:.1f}x average) -- topic: {u.get('topic', '?')}"
            )

        for topic in top_topics[:3]:
            avg = topic_avg[topic]
            ratio = avg / avg_views if avg_views > 0 else 0
            if ratio > 1.2:
                insights.append(
                    f"Topic '{topic}' averages {avg:.0f} views ({ratio:.1f}x average) -- prioritize this"
                )

        # Bottom performers
        for u in ranked[-2:]:
            if u["stats"]["views"] < avg_views * 0.5 and avg_views > 0:
                insights.append(
                    f"'{u['title'][:50]}' underperformed ({u['stats']['views']} views) -- consider different angle"
                )

        # ── Time-slot analysis: which posting hour gets the most views? ──
        hour_views = {}
        hour_counts = {}
        for u in with_stats:
            upload_time = u.get("upload_time", "")
            if upload_time:
                try:
                    hour = int(upload_time.split("T")[1].split(":")[0]) if "T" in upload_time else int(upload_time.split(":")[0])
                except (ValueError, IndexError):
                    hour = -1
            else:
                hour = -1
            if hour >= 0:
                hour_views[hour] = hour_views.get(hour, 0) + u["stats"]["views"]
                hour_counts[hour] = hour_counts.get(hour, 0) + 1

        hour_avg = {h: hour_views[h] / hour_counts[h] for h in hour_views}
        best_hours = sorted(hour_avg, key=hour_avg.get, reverse=True)

        if best_hours:
            log.info("Best posting hours (WITA): %s", ", ".join(
                f"{h:02d}:00 ({hour_avg[h]:.0f} avg views)" for h in best_hours[:5]
            ))
            insights.append(
                f"Best posting hours: {', '.join(f'{h:02d}:00' for h in best_hours[:3])} "
                f"(avg {hour_avg[best_hours[0]]:.0f} views for top slot)"
            )

            # Auto-adjust scheduler if we have enough data (7+ shorts with stats)
            if len(with_stats) >= 7 and len(best_hours) >= 3:
                sched_path = os.path.join(SCRIPTS_DIR, "shorts_scheduler.py") if 'SCRIPTS_DIR' in dir() else \
                    "/Users/franzccm/projects/ex-venture-platform/scripts/shorts_scheduler.py"
                try:
                    new_times = [f"{best_hours[i]:02d}:00" for i in range(min(3, len(best_hours)))]
                    log.info("Recommending schedule update to: %s", new_times)
                    insights.append(f"Recommended schedule: {', '.join(new_times)} WITA based on view data")
                except Exception:
                    pass

        # Save performance data
        perf_data = {
            "last_updated": datetime.datetime.now().isoformat(),
            "period_days": 7,
            "total_shorts": len(with_stats),
            "avg_views": round(avg_views, 1),
            "top_topics": top_topics,
            "topic_averages": {t: round(topic_avg[t], 1) for t in top_topics},
            "best_hours": best_hours[:5] if best_hours else [],
            "hour_averages": {str(h): round(hour_avg[h], 1) for h in best_hours[:5]} if best_hours else {},
            "insights": insights,
            "top_3": [
                {
                    "title": u["title"],
                    "views": u["stats"]["views"],
                    "topic": u.get("topic", ""),
                    "video_url": u.get("video_url", ""),
                }
                for u in ranked[:3]
            ],
        }

        with open(PERF_FILE, "w") as f:
            json.dump(perf_data, f, indent=2)

        log.info("Performance analysis saved to %s", PERF_FILE)
        log.info("Top topics: %s", ", ".join(top_topics[:5]))
        for ins in insights:
            log.info("  Insight: %s", ins)

    except Exception as e:
        log.error("Optimization failed: %s\n%s", e, traceback.format_exc())


# ═══════════════════════════════════════════════════════════════════════════════
# Full Production Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

def get_recommended_method():
    """Check strategy file for recommended production method."""
    if os.path.exists(STRATEGY_FILE):
        try:
            with open(STRATEGY_FILE) as f:
                strat = json.load(f)
            return strat.get("production_method", "notebooklm")
        except Exception:
            pass
    return "notebooklm"


def produce_remotion(script_info, index):
    """Produce a short using Remotion NewsShort (fast, 2min, motion graphics)."""
    log.info("[Short %d] Producing via Remotion...", index + 1)
    REMOTION_DIR = "/Users/franzccm/projects/ex-venture-platform/remotion-video"

    title = script_info.get("title", "AI NEWS")
    script_text = script_info.get("script", "")
    # Split script into 3-4 lines for text cards
    sentences = [s.strip() for s in script_text.replace(". ", ".\n").split("\n") if s.strip()]
    lines = sentences[:4] if len(sentences) >= 4 else sentences[:3]
    # Shorten each line for display
    lines = [l[:50] for l in lines]

    out_file = os.path.join(WORK_DIR, f"remotion_{index}.mp4")
    props = json.dumps({
        "title": title.replace("#Shorts", "").strip()[:40].upper(),
        "lines": lines,
        "accentColor": "#00ccff"
    })

    try:
        r = subprocess.run(
            [f"{REMOTION_DIR}/node_modules/.bin/remotion", "render",
             "src/index.tsx", "NewsShort", out_file, f"--props={props}"],
            cwd=REMOTION_DIR, capture_output=True, text=True, timeout=300
        )
        if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
            log.info("[Short %d] Remotion render: %.1f MB", index + 1, os.path.getsize(out_file)/1024/1024)
            return out_file
        log.error("[Short %d] Remotion render failed: %s", index + 1, r.stderr[-200:])
    except Exception as e:
        log.error("[Short %d] Remotion error: %s", index + 1, str(e)[:100])
    return None


def produce_ffmpeg_yt(script_info, index):
    """Produce a short by downloading a real YouTube demo + adding overlays."""
    log.info("[Short %d] Producing via yt-dlp + ffmpeg...", index + 1)

    query = script_info.get("tags", ["AI demo"])[0] + " demo 2026"
    title = script_info.get("title", "AI NEWS")
    out_file = os.path.join(WORK_DIR, f"ytdemo_{index}.mp4")
    dl_file = os.path.join(WORK_DIR, f"ytdl_{index}.mp4")
    clip_file = os.path.join(WORK_DIR, f"clip_{index}.mp4")

    try:
        # Download
        subprocess.run([
            "yt-dlp", "--no-warnings", "-q", "-f", "best[height<=720]",
            "--max-downloads", "1", "-o", dl_file,
            f"ytsearch1:{query}"
        ], capture_output=True, text=True, timeout=120)

        if not os.path.exists(dl_file) or os.path.getsize(dl_file) < 10000:
            log.error("[Short %d] yt-dlp download failed", index + 1)
            return None

        # Extract 30s clip
        subprocess.run([
            "ffmpeg", "-y", "-ss", "15", "-i", dl_file,
            "-t", "30", "-c:v", "libx264", "-c:a", "aac", clip_file
        ], capture_output=True, text=True)

        if not os.path.exists(clip_file):
            return None

        # Three-zone layout
        from PIL import Image, ImageDraw, ImageFont
        def gf(size):
            for p in ['/System/Library/Fonts/Helvetica.ttc', '/Library/Fonts/Arial.ttf']:
                if os.path.exists(p):
                    try: return ImageFont.truetype(p, size)
                    except: pass
            return ImageFont.load_default()

        overlay = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        d.rectangle([0, 0, 1080, 350], fill=(10, 10, 20, 255))
        d.rectangle([0, 1500, 1080, 1920], fill=(10, 10, 20, 255))
        d.rectangle([28, 50, 32, 78], fill=(0, 204, 255, 255))
        d.text((40, 50), "EXAI GLOBAL", fill=(0, 204, 255, 255), font=gf(18))
        d.rounded_rectangle([940, 45, 1050, 80], radius=6, fill=(230, 0, 0, 255))
        d.text((952, 50), "AI NEWS", fill=(255, 255, 255, 255), font=gf(15))
        hook = title.replace("#Shorts", "").strip()[:30].upper()
        d.text((540, 160), hook, fill=(255, 255, 255, 255), font=gf(44), anchor="mt")
        d.text((540, 1620), "Subscribe for daily AI tools", fill=(180, 180, 180, 255), font=gf(26), anchor="mt")
        d.rounded_rectangle([420, 1740, 660, 1790], radius=12, fill=(255, 0, 0, 255))
        d.text((540, 1755), "SUBSCRIBE", fill=(255, 255, 255, 255), font=gf(22), anchor="mt")
        ovl_path = os.path.join(WORK_DIR, f"overlay_{index}.png")
        overlay.save(ovl_path)

        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=0x0a0a14:s=1080x1920:d=30:r=30",
            "-i", clip_file, "-i", ovl_path,
            "-filter_complex",
            "[1:v]scale=1020:-1[vid];[0:v][vid]overlay=30:375:shortest=1[bg];[bg][2:v]overlay=0:0[out]",
            "-map", "[out]", "-map", "1:a?",
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", "-r", "30", "-t", "30",
            out_file
        ], capture_output=True, text=True)

        # Cleanup
        for f in [dl_file, clip_file]:
            try: os.unlink(f)
            except: pass

        if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
            log.info("[Short %d] ffmpeg+yt: %.1f MB", index + 1, os.path.getsize(out_file)/1024/1024)
            return out_file
    except Exception as e:
        log.error("[Short %d] ffmpeg+yt error: %s", index + 1, str(e)[:100])
    return None


def run_produce():
    """Run the full production pipeline: plan -> produce -> process -> upload.
    Dynamically switches between NotebookLM, Remotion, and ffmpeg based on
    strategy recommendations and fallback logic."""
    log.info("=" * 70)
    log.info("SHORTS MACHINE -- Full Production Run -- %s", DATE_STR)
    log.info("=" * 70)

    # Phase 1: Generate scripts
    scripts = generate_scripts(MAX_SCRIPTS)
    if not scripts:
        log.error("No scripts generated -- aborting")
        return

    uploaded_count = 0
    failed_count = 0
    total_scripts = len(scripts)

    # ALL shorts are NotebookLM cinematic — the ONLY format that works.
    # No Remotion, no ffmpeg fallback. If NLM fails, retry — don't substitute.
    log.info("Production method: NotebookLM cinematic (all %d shorts)", total_scripts)
    log.info("")
    log.info("=" * 50)
    log.info("Producing %d NotebookLM shorts in parallel", total_scripts)
    log.info("=" * 50)

    for notebook_info, raw_file in produce_batch(scripts, start_index=0):
        idx = notebook_info["index"]

        final_file = post_process(raw_file, notebook_info)
        if not final_file:
            failed_count += 1
            continue

        upload_result = upload_to_youtube(final_file, notebook_info)
        if upload_result:
            log_upload(upload_result)
            uploaded_count += 1
        else:
            failed_count += 1

    log.info("")
    log.info("=" * 70)
    log.info("PRODUCTION COMPLETE: %d uploaded, %d failed out of %d scripts",
             uploaded_count, failed_count, total_scripts)
    log.info("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════════
# Status
# ═══════════════════════════════════════════════════════════════════════════════

def run_status():
    """Show current status: what's been produced/uploaded today."""
    print(f"{'=' * 60}")
    print(f"SHORTS MACHINE STATUS -- {DATE_STR}")
    print(f"{'=' * 60}")

    # Check work directory
    work_files = glob.glob(os.path.join(WORK_DIR, "*.mp4"))
    print(f"\nWork directory: {WORK_DIR}")
    print(f"  Raw files:   {len([f for f in work_files if '_raw' in f])}")
    print(f"  Final files: {len([f for f in work_files if '_final' in f])}")

    # Check scripts
    scripts_file = os.path.join(WORK_DIR, "scripts.json")
    if os.path.exists(scripts_file):
        with open(scripts_file) as f:
            scripts = json.load(f)
        print(f"  Scripts:     {len(scripts)}")
    else:
        print(f"  Scripts:     None generated yet")

    # Check uploads
    print(f"\nUpload log: {UPLOAD_LOG}")
    if os.path.exists(UPLOAD_LOG):
        with open(UPLOAD_LOG) as f:
            uploads = json.load(f)
        today_uploads = [u for u in uploads if u.get("date") == DATE_STR]
        total_uploads = len(uploads)
        print(f"  Today:       {len(today_uploads)} uploaded")
        print(f"  All time:    {total_uploads} total")
        if today_uploads:
            print(f"\n  Today's uploads:")
            for u in today_uploads:
                print(f"    - {u.get('video_url', '?')}  {u.get('title', '?')[:50]}")
    else:
        print(f"  No uploads yet")

    # Check performance data
    print(f"\nPerformance: {PERF_FILE}")
    if os.path.exists(PERF_FILE):
        with open(PERF_FILE) as f:
            perf = json.load(f)
        print(f"  Last updated:  {perf.get('last_updated', '?')}")
        print(f"  Avg views:     {perf.get('avg_views', '?')}")
        print(f"  Top topics:    {', '.join(perf.get('top_topics', [])[:5])}")
        insights = perf.get("insights", [])
        if insights:
            print(f"\n  Recent insights:")
            for ins in insights[:5]:
                print(f"    - {ins}")
    else:
        print(f"  No performance data yet (run --optimize)")

    # Check Chrome CDP
    print(f"\nChrome CDP: {CDP}")
    try:
        resp = urllib.request.urlopen(f"{CDP}/json/version", timeout=3)
        info = json.loads(resp.read())
        print(f"  Browser:     {info.get('Browser', '?')}")
        resp2 = urllib.request.urlopen(f"{CDP}/json", timeout=3)
        tabs = json.loads(resp2.read())
        nlm_tabs = [t for t in tabs if "notebooklm" in t.get("url", "").lower()]
        print(f"  Open tabs:   {len(tabs)} ({len(nlm_tabs)} NotebookLM)")
    except Exception:
        print(f"  NOT CONNECTED (start Chrome with --remote-debugging-port=9222)")

    # Check YouTube token
    print(f"\nYouTube token: {YOUTUBE_TOKEN}")
    if os.path.exists(YOUTUBE_TOKEN):
        print(f"  Status:      Found")
    else:
        print(f"  Status:      MISSING")

    print(f"\n{'=' * 60}")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Shorts Machine -- Automated NotebookLM shorts production pipeline"
    )
    parser.add_argument("--produce", action="store_true",
                        help="Run full production pipeline (plan + produce + upload)")
    parser.add_argument("--optimize", action="store_true",
                        help="Run self-optimization analysis (pull stats, generate insights)")
    parser.add_argument("--status", action="store_true",
                        help="Show current production status")
    parser.add_argument("--improve", action="store_true",
                        help="Run deep self-improvement: competitor analysis, strategy update, tool discovery")

    args = parser.parse_args()

    if not any([args.produce, args.optimize, args.status, args.improve]):
        parser.print_help()
        sys.exit(1)

    if args.status:
        run_status()

    if args.optimize:
        run_optimization()

    if args.improve:
        run_self_improvement()

    if args.produce:
        run_produce()


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: Deep Self-Improvement Engine
# ═══════════════════════════════════════════════════════════════════════════════

IMPROVE_LOG = "/tmp/morningbrief/shorts/improvement_log.json"
STRATEGY_FILE = "/tmp/morningbrief/shorts/strategy.json"

def run_self_improvement():
    """
    Deep self-improvement loop:
    1. Analyze our channel vs top AI shorts channels
    2. Ask Gemini what we should change based on performance data
    3. Search for new tools/techniques and install them
    4. Auto-update posting schedule based on data
    5. Auto-adjust script prompts based on what worked
    """
    log.info("=" * 70)
    log.info("SELF-IMPROVEMENT ENGINE — Deep Analysis")
    log.info("=" * 70)

    # Load current performance data
    perf = {}
    if os.path.exists(PERF_FILE):
        with open(PERF_FILE) as f:
            perf = json.load(f)

    upload_history = []
    if os.path.exists(UPLOAD_LOG):
        with open(UPLOAD_LOG) as f:
            upload_history = json.load(f)

    # ── Step 1: Ask Gemini for strategic improvements ──
    log.info("Step 1: Asking Gemini for strategic analysis...")

    perf_summary = json.dumps(perf, indent=2) if perf else "No performance data yet — channel just started."
    upload_count = len(upload_history)

    improvement_prompt = f"""You are a YouTube growth strategist analyzing the EXAI Global channel (AI news shorts).

CURRENT STATE:
- Subscribers: ~20 (goal: 1,000 in 7 days)
- Total shorts uploaded: {upload_count}
- Performance data: {perf_summary}

CURRENT STRATEGY:
- 3 NotebookLM animated shorts per day (with AI narration + cinematic visuals)
- Formats: 1 breaking news, 1 demo/comparison, 1 hot take
- Posting times: 14:00, 20:00, 03:00 WITA (testing)
- Self-optimization every 6 hours

ANALYZE AND PROVIDE:

1. CONTENT STRATEGY CHANGES (what topics/angles should we pivot to?)
2. TITLE OPTIMIZATION (what title patterns drive more clicks in the Shorts feed?)
3. DESCRIPTION & HASHTAG STRATEGY (what tags are we missing?)
4. THUMBNAIL/FIRST FRAME optimization (what should the opening frame look like?)
5. POSTING SCHEDULE adjustment (based on data, what times should we test next?)
6. ENGAGEMENT TACTICS (how to drive more comments, shares, subscribes?)
7. GROWTH HACKS specific to channels under 1K subs
8. What COMPETITOR channels should we study? Name 5 AI shorts channels with their strategies.
9. What NEW TOOLS or techniques should we try? (e.g., AI voiceover tools, caption generators, trend trackers)
10. The single MOST IMPORTANT change to make RIGHT NOW

Return as JSON:
{{
  "content_pivots": ["pivot 1", "pivot 2"],
  "title_patterns": ["pattern 1", "pattern 2"],
  "hashtags": ["#tag1", "#tag2"],
  "first_frame_tips": ["tip 1"],
  "schedule_test": ["time1", "time2", "time3"],
  "engagement_tactics": ["tactic 1", "tactic 2"],
  "growth_hacks": ["hack 1", "hack 2"],
  "competitors_to_study": [{{"name": "channel", "strategy": "what they do"}}],
  "new_tools": [{{"name": "tool", "url": "url", "purpose": "what it does", "install_cmd": "pip3 install --user --break-system-packages PACKAGE or npm install PACKAGE"}}],
  "production_method": "Which method to use for EACH of the 3 daily shorts. Options: 'notebooklm' (cinematic AI animation+narration - best quality but slow, 10-20min), 'remotion' (React motion graphics - fast, 2min render, good for text/data), 'ffmpeg_yt' (download real YouTube demo clips + Pillow overlays - authentic demos), 'hybrid_nlm_overlay' (NotebookLM video + ffmpeg EXAI branding overlays). Pick the BEST method for each short type based on what's working.",
  "most_important_change": "the one thing to change right now",
  "updated_gemini_prompt_additions": "extra instructions to add to the script generation prompt based on this analysis"
}}"""

    try:
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}",
            data=json.dumps({
                "contents": [{"parts": [{"text": improvement_prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"},
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        strategy = json.loads(result["candidates"][0]["content"]["parts"][0]["text"])

        log.info("Strategic analysis complete:")
        log.info("  Most important change: %s", strategy.get("most_important_change", "?"))
        log.info("  Content pivots: %s", ", ".join(strategy.get("content_pivots", [])[:3]))
        log.info("  Title patterns: %s", ", ".join(strategy.get("title_patterns", [])[:3]))
        log.info("  Growth hacks: %s", ", ".join(strategy.get("growth_hacks", [])[:3]))

        competitors = strategy.get("competitors_to_study", [])
        if competitors:
            log.info("  Competitors to study:")
            for c in competitors[:5]:
                log.info("    - %s: %s", c.get("name", "?"), c.get("strategy", "?")[:60])

        new_tools = strategy.get("new_tools", [])
        if new_tools:
            log.info("  New tools to try:")
            for t in new_tools[:5]:
                log.info("    - %s: %s", t.get("name", "?"), t.get("purpose", "?")[:60])

        # Save strategy
        strategy["generated_at"] = datetime.datetime.now().isoformat()
        strategy["based_on_uploads"] = upload_count
        with open(STRATEGY_FILE, "w") as f:
            json.dump(strategy, f, indent=2)
        log.info("Strategy saved to %s", STRATEGY_FILE)

    except Exception as e:
        log.error("Gemini strategy analysis failed: %s", e)
        strategy = {}

    # ── Step 2: Auto-update the script generation prompt ──
    if strategy.get("updated_gemini_prompt_additions"):
        additions = strategy["updated_gemini_prompt_additions"]
        log.info("Step 2: Updating script prompt with Gemini's suggestions...")
        # Save the prompt additions so generate_scripts() can pick them up
        prompt_file = os.path.join(SHORTS_DIR, "prompt_additions.txt")
        with open(prompt_file, "w") as f:
            f.write(additions)
        log.info("  Saved prompt additions to %s", prompt_file)

    # ── Step 3: Auto-install recommended tools ──
    if new_tools:
        log.info("Step 3: Checking recommended tools...")
        for tool in new_tools[:3]:
            name = tool.get("name", "").lower().replace(" ", "-")
            url = tool.get("url", "")
            if not name:
                continue

            # Try pip install if it looks like a Python package
            if any(x in name for x in ["elevenlabs", "whisper", "caption", "subtitle", "tts",
                                         "moviepy", "pydub", "speech", "voice"]):
                log.info("  Attempting pip install: %s", name)
                try:
                    r = subprocess.run(
                        ["pip", "install", "--user", name],
                        capture_output=True, text=True, timeout=120
                    )
                    if r.returncode == 0:
                        log.info("  ✓ Installed %s", name)
                    else:
                        log.info("  ✗ Failed to install %s: %s", name, r.stderr[:100])
                except Exception as e:
                    log.info("  ✗ Install error for %s: %s", name, str(e)[:60])

            # Try npm install if it looks like a Node package
            elif any(x in name for x in ["remotion", "hyperframes", "ffmpeg", "sharp"]):
                log.info("  Skipping npm package %s (manual review needed)", name)

    # ── Step 4: Auto-adjust posting schedule ──
    schedule_test = strategy.get("schedule_test", [])
    best_hours = perf.get("best_hours", [])

    if best_hours and len(best_hours) >= 3:
        log.info("Step 4: Updating posting schedule based on view data...")
        new_schedule = best_hours[:3]
        log.info("  Data-driven schedule: %s WITA", [f"{h:02d}:00" for h in new_schedule])

        # Update scheduler file
        sched_path = "/Users/franzccm/projects/ex-venture-platform/scripts/shorts_scheduler.py"
        try:
            with open(sched_path) as f:
                content = f.read()

            # Build new schedule lines
            labels = ["Breaking AI news", "AI demo / comparison", "Hot take / controversial"]
            new_lines = []
            for i, hour in enumerate(new_schedule[:3]):
                label = labels[i] if i < len(labels) else f"Short {i+1}"
                new_lines.append(
                    f'    {{"slot": {i+1}, "time": "{hour:02d}:00", "type": "nlm", "label": "{label}"}},'
                )

            # Find and replace the SCHEDULE block
            import re as re_mod
            pattern = r'SCHEDULE = \[.*?\]'
            new_block = "SCHEDULE = [\n" + "\n".join(new_lines) + "\n]"
            new_content = re_mod.sub(pattern, new_block, content, flags=re_mod.DOTALL)

            if new_content != content:
                with open(sched_path, "w") as f:
                    f.write(new_content)
                log.info("  ✓ Scheduler updated with optimal times")

                # Reload launchd
                subprocess.run(["launchctl", "unload",
                    "/Users/franzccm/Library/LaunchAgents/com.exventure.shorts-scheduler.plist"],
                    capture_output=True)
                time.sleep(1)
                subprocess.run(["launchctl", "load",
                    "/Users/franzccm/Library/LaunchAgents/com.exventure.shorts-scheduler.plist"],
                    capture_output=True)
                log.info("  ✓ Scheduler daemon reloaded")
            else:
                log.info("  Schedule unchanged")
        except Exception as e:
            log.error("  ✗ Failed to update scheduler: %s", e)
    elif schedule_test:
        log.info("Step 4: Not enough data yet to auto-adjust schedule (need 7+ shorts)")
        log.info("  Gemini suggests testing: %s", schedule_test[:3])

    # ── Step 5: Log improvement run ──
    improvement_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "uploads_analyzed": upload_count,
        "avg_views": perf.get("avg_views", 0),
        "most_important_change": strategy.get("most_important_change", ""),
        "tools_installed": [t.get("name") for t in new_tools[:3] if t.get("name")],
        "schedule_updated": bool(best_hours and len(best_hours) >= 3),
    }

    history = []
    if os.path.exists(IMPROVE_LOG):
        with open(IMPROVE_LOG) as f:
            history = json.load(f)
    history.append(improvement_entry)
    # Keep last 30 entries
    history = history[-30:]
    with open(IMPROVE_LOG, "w") as f:
        json.dump(history, f, indent=2)

    log.info("=" * 70)
    log.info("SELF-IMPROVEMENT COMPLETE")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
