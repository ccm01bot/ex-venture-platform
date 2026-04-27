#!/usr/bin/env python3
"""
Daily Shorts Scheduler — 10-slot system with typed content per slot.

Slots (WITA/UTC+8):
  1  06:00  demo          AI demo short
  2  07:30  series        Day X/7 series
  3  09:00  nlm           NotebookLM animated
  4  11:00  comparison    AI vs AI
  5  13:00  nlm           NotebookLM animated
  6  15:00  beforeafter   Before/After
  7  17:00  quickhack     15s ultra-short
  8  19:30  nlm           NotebookLM animated
  9  21:00  listicle      Top 3 AI tools
 10  23:00  controversial Hot take

Runs as a background daemon via launchd, checks every 5 minutes.
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import time
import datetime
import subprocess
import glob
import logging
import traceback

# ─── Paths ───────────────────────────────────────────────────────────────────
SCRIPTS = "/Users/franzccm/projects/ex-venture-platform/scripts"
SHORTS_DIR = "/tmp/morningbrief/shorts"
POSTED_LOG = "/tmp/morningbrief/shorts_posted.json"
SERIES_STATE = "/tmp/morningbrief/shorts_series_state.json"
LOG_FILE = "/tmp/morningbrief/shorts_scheduler.log"
YOUTUBE_TOKEN = os.path.expanduser("~/.youtube-exai/token.json")
YOUTUBE_CLIENT_SECRET = os.path.expanduser("~/.youtube-exai/client_secret.json")
PIN_COMMENT = "\U0001f514 Subscribe for daily AI news! New tools every day."

os.makedirs(SHORTS_DIR, exist_ok=True)

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("shorts_scheduler")

# ─── 3-Slot Schedule (optimal for growth: 3/day = 4.4x more subs than 1/day) ──
# Week 1: Test 3 different time windows to find what works best
# Optimizer (every 6h) will analyze which slot gets most views and adjust
# Starting with: EU afternoon, US morning, US evening (covers global audience)
SCHEDULE = [
    {"slot": 1, "time": "14:00", "type": "nlm", "label": "Breaking AI news"},      # 06:00 UTC — EU afternoon
    {"slot": 2, "time": "20:00", "type": "nlm", "label": "AI demo / comparison"},   # 12:00 UTC — US East morning
    {"slot": 3, "time": "03:00", "type": "nlm", "label": "Hot take / controversial"},# 19:00 UTC — US evening prime
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def today_str():
    return datetime.date.today().isoformat()


def slot_video_path(slot_num, date=None):
    date = date or today_str()
    return os.path.join(SHORTS_DIR, f"slot_{slot_num}_{date}.mp4")


def slot_meta_path(slot_num, date=None):
    date = date or today_str()
    return os.path.join(SHORTS_DIR, f"slot_{slot_num}_{date}.json")


def get_longform_link():
    """Return today's longform YouTube URL from /tmp/morningbrief/youtube_*.txt."""
    date = today_str()
    path = f"/tmp/morningbrief/youtube_{date}.txt"
    if os.path.exists(path):
        with open(path) as f:
            url = f.read().strip()
        if url:
            return url
    # Fallback: latest file
    files = sorted(glob.glob("/tmp/morningbrief/youtube_*.txt"))
    if files:
        with open(files[-1]) as f:
            return f.read().strip()
    return None


# ─── Duplicate Prevention ────────────────────────────────────────────────────

def get_posted_today():
    date = today_str()
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG) as f:
            data = json.load(f)
        return data.get(date, [])
    return []


def mark_posted(slot_num):
    date = today_str()
    data = {}
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG) as f:
            data = json.load(f)
    posted = data.setdefault(date, [])
    if slot_num not in posted:
        posted.append(slot_num)
    with open(POSTED_LOG, "w") as f:
        json.dump(data, f, indent=2)


# ─── Series Day Tracker ─────────────────────────────────────────────────────

def get_series_day():
    """Return current day number (1-7) for the Day X/7 series slot."""
    if os.path.exists(SERIES_STATE):
        with open(SERIES_STATE) as f:
            state = json.load(f)
    else:
        state = {"day": 0, "last_date": ""}

    date = today_str()
    if state.get("last_date") == date:
        return state["day"]  # Already advanced today

    day = (state.get("day", 0) % 7) + 1
    state = {"day": day, "last_date": date}
    with open(SERIES_STATE, "w") as f:
        json.dump(state, f, indent=2)
    return day


# ─── Production: create video if not pre-produced ────────────────────────────

def _run_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = "/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages"
    env["GEMINI_API_KEY"] = os.environ.get(
        "GEMINI_API_KEY", "GEMINI_API_KEY_PLACEHOLDER"
    )
    return env


def produce_nlm(slot_num):
    """Trigger create_shorts_combined.py for an NLM slot."""
    log.info("Slot %d: Triggering create_shorts_combined.py (NLM)", slot_num)
    result = subprocess.run(
        [
            "python3", "-u",
            os.path.join(SCRIPTS, "create_shorts_combined.py"),
            "--slot", str(slot_num),
        ],
        capture_output=True, text=True,
        env=_run_env(),
        timeout=3600,
    )
    if result.returncode != 0:
        log.error("create_shorts_combined.py failed:\nSTDOUT: %s\nSTDERR: %s",
                  result.stdout[-500:] if result.stdout else "", result.stderr[-500:] if result.stderr else "")
    return result.returncode == 0


def produce_other(slot_num):
    """Trigger produce_daily_shorts.py --slot N for non-NLM types."""
    log.info("Slot %d: Triggering produce_daily_shorts.py --slot %d", slot_num, slot_num)
    result = subprocess.run(
        [
            "python3", "-u",
            os.path.join(SCRIPTS, "produce_daily_shorts.py"),
            "--slot", str(slot_num),
        ],
        capture_output=True, text=True,
        env=_run_env(),
        timeout=1800,
    )
    if result.returncode != 0:
        log.error("produce_daily_shorts.py --slot %d failed:\nSTDOUT: %s\nSTDERR: %s",
                  slot_num,
                  result.stdout[-500:] if result.stdout else "",
                  result.stderr[-500:] if result.stderr else "")
    return result.returncode == 0


# ─── YouTube Upload ─────────────────────────────────────────────────────────

def _build_youtube_service():
    """Build an authenticated YouTube Data API v3 service."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    with open(YOUTUBE_TOKEN) as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes", [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl",
        ]),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(YOUTUBE_TOKEN, "w") as f:
            json.dump(token_data, f, indent=2)
        log.info("YouTube token refreshed")

    return build("youtube", "v3", credentials=creds)


def upload_to_youtube(video_path, meta, slot_entry):
    """
    Upload video to YouTube as a public Short, pin a comment, return video URL.

    meta dict keys: title, description, tags (list)
    """
    from googleapiclient.http import MediaFileUpload

    youtube = _build_youtube_service()

    # Ensure #Shorts in title
    title = meta.get("title", f"AI Short — {today_str()}")
    if "#Shorts" not in title and "#shorts" not in title.lower():
        title = f"{title} #Shorts"

    # Build description with longform link
    description = meta.get("description", "")
    longform = get_longform_link()
    if longform:
        description += f"\n\n\U0001f4fa Full episode: {longform}"

    tags = meta.get("tags", ["AI", "shorts", "tech"])
    if "Shorts" not in tags:
        tags.append("Shorts")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28",  # Science & Technology
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    log.info("Uploading %s to YouTube...", os.path.basename(video_path))
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info("  Upload progress: %d%%", int(status.progress() * 100))

    video_id = response["id"]
    video_url = f"https://youtu.be/{video_id}"
    log.info("Upload complete: %s  (slot %d, type=%s)",
             video_url, slot_entry["slot"], slot_entry["type"])

    # Pin comment
    try:
        comment_body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": PIN_COMMENT,
                    }
                },
            }
        }
        comment_resp = youtube.commentThreads().insert(
            part="snippet", body=comment_body
        ).execute()
        comment_id = comment_resp["id"]
        log.info("Pinned comment on %s (comment %s)", video_id, comment_id)
    except Exception as e:
        log.warning("Could not pin comment on %s: %s", video_id, e)

    return video_url


# ─── Slot Handler ────────────────────────────────────────────────────────────

def handle_slot(slot_entry):
    """Process a single slot: ensure video exists, upload, return URL or None."""
    slot_num = slot_entry["slot"]
    slot_type = slot_entry["type"]
    date = today_str()

    video_path = slot_video_path(slot_num, date)
    meta_path = slot_meta_path(slot_num, date)

    # ── Step 1: Check for pre-produced video ──
    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
        log.info("Slot %d (%s): Pre-produced video found at %s", slot_num, slot_type, video_path)
    else:
        # ── Step 2: Produce on the fly ──
        log.info("Slot %d (%s): No pre-produced video, triggering production...", slot_num, slot_type)
        if slot_type == "nlm":
            ok = produce_nlm(slot_num)
        else:
            ok = produce_other(slot_num)

        if not ok or not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            log.error("Slot %d: Production failed — no video at %s", slot_num, video_path)
            return None

    # ── Step 3: Load metadata ──
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        log.info("Slot %d: Loaded metadata from %s", slot_num, meta_path)
    else:
        # Fallback metadata
        series_tag = ""
        if slot_type == "series":
            day = get_series_day()
            series_tag = f" Day {day}/7"
        meta = {
            "title": f"{slot_entry['label']}{series_tag} — {date}",
            "description": f"{slot_entry['label']} | AI daily shorts",
            "tags": ["AI", "shorts", "tech", slot_type],
        }
        log.info("Slot %d: Using fallback metadata (no JSON found)", slot_num)

    # Inject series day into title if series slot
    if slot_type == "series":
        day = get_series_day()
        title = meta.get("title", "")
        if "Day" not in title:
            meta["title"] = f"Day {day}/7 — {title}"

    # ── Step 4: Upload to YouTube ──
    try:
        url = upload_to_youtube(video_path, meta, slot_entry)
        return url
    except Exception as e:
        log.error("Slot %d: YouTube upload failed: %s\n%s", slot_num, e, traceback.format_exc())
        return None


# ─── Main Loop ───────────────────────────────────────────────────────────────

def run_scheduler():
    log.info("=" * 60)
    log.info("Shorts Scheduler started — 10 slots/day, 5-min check interval")
    for s in SCHEDULE:
        log.info("  Slot %2d  %s  %-14s  %s", s["slot"], s["time"], s["type"], s["label"])
    log.info("=" * 60)

    while True:
        now = datetime.datetime.now()
        posted = get_posted_today()

        for slot_entry in SCHEDULE:
            slot_num = slot_entry["slot"]
            slot_time = slot_entry["time"]

            # Skip if already posted today
            if slot_num in posted:
                continue

            # Check if we are within 5 minutes after the slot time
            slot_h, slot_m = map(int, slot_time.split(":"))
            slot_dt = now.replace(hour=slot_h, minute=slot_m, second=0, microsecond=0)
            diff = (now - slot_dt).total_seconds()

            if 0 <= diff <= 300:
                log.info(
                    "──── Slot %d triggered (%s) — type=%s  %s ────",
                    slot_num, slot_time, slot_entry["type"], slot_entry["label"],
                )

                url = handle_slot(slot_entry)
                if url:
                    log.info("Slot %d SUCCESS: %s", slot_num, url)
                else:
                    log.warning("Slot %d FAILED — marked as posted to avoid retry storm", slot_num)

                mark_posted(slot_num)

        # Sleep 5 minutes
        time.sleep(300)


if __name__ == "__main__":
    run_scheduler()
