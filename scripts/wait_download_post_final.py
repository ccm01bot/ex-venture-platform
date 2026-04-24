#!/usr/bin/env python3
"""Poll for today's NEW video to finish, download via CDP new-tab download, upload MP4 to Slack."""

import sys, json, base64, urllib.request, time, os, subprocess, glob, datetime
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

SLACK_USER_TOKEN = "SLACK_USER_TOKEN_PLACEHOLDER"
SLACK_CHANNEL = "C074JDBNJD9"  # #1-the-group-chat
CDP = "http://127.0.0.1:9222"
DL_DIR = "/tmp/morningbrief/downloads"
_startup_date = datetime.date.today().strftime("%Y-%m-%d")
VIDEO_PATH = f"/tmp/morningbrief/morningbrief_video_{_startup_date}.mp4"

os.makedirs(DL_DIR, exist_ok=True)
# Clear old downloads
for f in glob.glob(f"{DL_DIR}/*"): os.unlink(f)

mid = 0

# Load the target notebook URL from step 1 so we connect to the RIGHT notebook, not any random tab
try:
    with open("/tmp/morningbrief/current_notebook_url.txt") as f:
        TARGET_NOTEBOOK_URL = f.read().strip()
    # Extract notebook ID from URL
    TARGET_NOTEBOOK_ID = TARGET_NOTEBOOK_URL.split("/notebook/")[-1].split("?")[0].split("#")[0]
    print(f"Target notebook ID: {TARGET_NOTEBOOK_ID}")
except Exception as e:
    print(f"WARNING: Could not load target notebook URL: {e}")
    TARGET_NOTEBOOK_ID = None

def get_ws():
    resp = urllib.request.urlopen(f"{CDP}/json")
    tabs = json.loads(resp.read())
    # First try to find the specific notebook tab
    if TARGET_NOTEBOOK_ID:
        for tab in tabs:
            if TARGET_NOTEBOOK_ID in tab.get("url", ""):
                return websocket.create_connection(tab["webSocketDebuggerUrl"]), tab["url"]
        # If not found, navigate there in any notebooklm tab
        for tab in tabs:
            if "notebooklm.google.com" in tab.get("url", "") and "accounts" not in tab.get("url", "") and "Rotate" not in tab.get("url", ""):
                ws = websocket.create_connection(tab["webSocketDebuggerUrl"])
                ws.send(json.dumps({"id": 99999, "method": "Page.navigate", "params": {"url": TARGET_NOTEBOOK_URL}}))
                while True:
                    r = json.loads(ws.recv())
                    if r.get("id") == 99999: break
                time.sleep(5)
                return ws, TARGET_NOTEBOOK_URL
    # Fallback
    for tab in tabs:
        if "notebooklm.google.com/notebook" in tab.get("url", ""):
            return websocket.create_connection(tab["webSocketDebuggerUrl"]), tab["url"]
    return None, None

def cdp(ws, method, params=None):
    global mid; mid += 1
    ws.send(json.dumps({"id":mid,"method":method,"params":params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid: return r

def js(ws, e):
    r = cdp(ws, "Runtime.evaluate",{"expression":e,"returnByValue":True,"awaitPromise":True})
    return r.get("result",{}).get("result",{}).get("value")

print(f"=== Daily Morningbrief Pipeline — {_startup_date} ===\n")
print("Polling for video generation to complete...")

notebook_url = ""
for i in range(180):  # Up to 90 minutes
    try:
        ws, url = get_ws()
        if not ws: time.sleep(30); continue
        cdp(ws, "Runtime.enable")
        notebook_url = url

        status = js(ws, """(() => {
            const text = document.body.innerText;
            if (text.includes('Good video') || text.includes('Bad video')) return 'video_available';
            if (text.includes('Video Overview') && text.includes('is ready')) return 'video_available';
            if (text.includes('Customize') && !text.includes('Generating') && !text.includes('Creating')) return 'video_available';
            const v = document.querySelector('video');
            if (v && v.src && v.src.includes('googleusercontent')) return 'video_available';
            if (text.includes('Generating Video') || text.includes('Generating video') || text.includes('generating video')) return 'generating';
            if (text.includes('Generating Cinematic') || text.includes('Creating') || text.includes('creating')) return 'generating';
            if (text.includes('This may take a while') || text.includes('This may ta')) return 'generating';
            return 'unknown';
        })()""")

        if i % 6 == 0:
            print(f"  [{i*30}s] {status}")

        if status == 'video_available':
            print(f"\n✓ Video available after {i*30}s")
            ws.close()
            break

        ws.close()
    except Exception as e:
        print(f"  Error: {e}")
    time.sleep(30)
else:
    print("\n✗ Timed out. Video may still be generating.")
    sys.exit(1)

# Now download the video
print("\n--- Downloading video ---")
ws, _ = get_ws()
cdp(ws, "Runtime.enable")
cdp(ws, "Page.enable")
cdp(ws, "Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": DL_DIR})

# Robust video URL extraction with multiple fallbacks
def get_video_url(ws, max_attempts=5):
    for attempt in range(max_attempts):
        # First try direct video element
        url = js(ws, "document.querySelector('video')?.src || ''")
        if url and len(url) > 50 and 'googleusercontent' in url:
            return url

        # Try to expand Video Overview panel
        js(ws, """(() => {
            const els = document.querySelectorAll('*');
            for (const el of els) {
                if (el.childElementCount === 0 && el.textContent.trim() === 'Video Overview') {
                    const c = el.closest('button, [role="button"], a, [tabindex], div[class*="tile"], div[class*="card"]');
                    if (c) { c.click(); return; }
                }
            }
        })()""")
        time.sleep(3)

        # Check all video elements (including hidden/shadow DOM)
        url = js(ws, """(() => {
            const videos = document.querySelectorAll('video');
            for (const v of videos) {
                if (v.src && v.src.includes('googleusercontent')) return v.src;
                if (v.currentSrc && v.currentSrc.includes('googleusercontent')) return v.currentSrc;
                const sources = v.querySelectorAll('source');
                for (const s of sources) {
                    if (s.src && s.src.includes('googleusercontent')) return s.src;
                }
            }
            return '';
        })()""")
        if url and len(url) > 50:
            return url

        # Try clicking the play button to force video load
        js(ws, """(() => {
            const btn = document.querySelector('button[aria-label*="Play"], button[aria-label*="play"]');
            if (btn) btn.click();
        })()""")
        time.sleep(3)

        # Unhide any hidden videos
        js(ws, """(() => {
            document.querySelectorAll('video').forEach(v => {
                v.hidden = false;
                v.style.display = 'block';
                v.load();
            });
        })()""")
        time.sleep(2)
        print(f"  URL attempt {attempt+1} failed, retrying...")
    return ''

video_url = get_video_url(ws)

print(f"Video URL: {video_url[:100]}")

# CRITICAL: refuse to download if URL is empty — prevents re-posting cached/old video
if not video_url or len(video_url) < 50:
    print(f"✗ ABORT: Video URL is empty or too short. Refusing to download stale/cached video.")
    print(f"  This is the bug that caused Wednesday's video to get re-posted on Thursday.")
    ws.close()
    sys.exit(1)

# Also verify the URL looks like a valid Google NotebookLM video URL
if 'lh3.googleusercontent.com' not in video_url and 'googleusercontent' not in video_url:
    print(f"✗ ABORT: Video URL doesn't look like a valid NotebookLM video URL: {video_url[:150]}")
    ws.close()
    sys.exit(1)

# Clear download directory right before downloading to avoid picking up stale files
for f in glob.glob(f"{DL_DIR}/*"): os.unlink(f)

base_url = video_url.split('=m22')[0] if '=m22' in video_url else video_url.split('?')[0]
download_url = base_url + '=dv'
print(f"Download URL: {download_url[:100]}")

# Open in new tab to trigger download
print("Opening download URL in new tab...")
r = cdp(ws, "Target.createTarget", {"url": download_url})
target_id = r.get("result",{}).get("targetId","")

# Wait for download
print("Waiting for download to complete...")
for i in range(60):
    time.sleep(5)
    files = glob.glob(f"{DL_DIR}/*")
    complete = [f for f in files if not f.endswith('.crdownload')]
    if complete:
        src = complete[0]
        size = os.path.getsize(src)
        import shutil
        shutil.copy2(src, VIDEO_PATH)
        print(f"✓ Downloaded: {size/1024/1024:.1f} MB → {VIDEO_PATH}")
        break
    partial = [f for f in files if f.endswith('.crdownload')]
    if partial:
        psize = os.path.getsize(partial[0])/1024/1024
        if i % 3 == 0:
            print(f"  [{i*5}s] Downloading... {psize:.1f} MB")

if target_id:
    cdp(ws, "Target.closeTarget", {"targetId": target_id})
ws.close()

# Verify it's a video
ft = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout.strip()
print(f"File type: {ft}")

if 'ISO Media' not in ft and 'MP4' not in ft:
    print("✗ Downloaded file is not a video")
    sys.exit(1)

# CRITICAL: verify this video is NEW vs previous days' videos (hash comparison)
import hashlib
def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

today_hash = file_hash(VIDEO_PATH)
print(f"Video hash: {today_hash[:16]}...")

# Compare against recent videos
for prev in sorted(glob.glob("/tmp/morningbrief/morningbrief_video_*.mp4"))[:-1]:
    if prev != VIDEO_PATH and os.path.exists(prev):
        if file_hash(prev) == today_hash:
            print(f"✗ ABORT: Downloaded video is IDENTICAL to {prev}")
            print(f"  This means we re-downloaded yesterday's video. Refusing to post duplicate.")
            sys.exit(1)
print("✓ Video is unique (different from previous days)")

# Add EXAI watermark over NotebookLM logo (bottom-left corner)
print("Adding EXAI watermark...")
watermarked = VIDEO_PATH.replace(".mp4", "_branded.mp4")
subprocess.run([
    "ffmpeg", "-y", "-i", VIDEO_PATH,
    "-vf", "drawtext=text='EXAI GLOBAL':fontsize=28:fontcolor=white@0.9:x=20:y=h-50:fontfile=/System/Library/Fonts/Helvetica.ttc:borderw=2:bordercolor=black@0.5",
    "-c:v", "libx264", "-c:a", "copy",
    "-pix_fmt", "yuv420p",
    watermarked
], capture_output=True, text=True)
if os.path.exists(watermarked) and os.path.getsize(watermarked) > 50000:
    os.rename(watermarked, VIDEO_PATH)
    print(f"✓ Watermark added: {os.path.getsize(VIDEO_PATH)/1024/1024:.1f} MB")
else:
    print("  Watermark failed, using original")

# Upload to Slack — compute date NOW, right before posting
POSTING_DATE_ISO = datetime.date.today().strftime("%Y-%m-%d")
POSTING_DATE_FRIENDLY = datetime.date.today().strftime("%A, %B %d, %Y")

print(f"\n--- Uploading to Slack group chat ({POSTING_DATE_FRIENDLY}) ---")
size = os.path.getsize(VIDEO_PATH)

r = subprocess.run(["curl", "-s",
    "-F", f"length={size}",
    "-F", f"filename=AI_Morning_Brief_{POSTING_DATE_ISO}.mp4",
    "-H", f"Authorization: Bearer {SLACK_USER_TOKEN}",
    "https://slack.com/api/files.getUploadURLExternal"
], capture_output=True, text=True)
upload_info = json.loads(r.stdout)
if not upload_info.get('ok'):
    print(f"✗ {upload_info.get('error')}")
    sys.exit(1)

subprocess.run(["curl", "-s", "-X", "POST", "-F", f"file=@{VIDEO_PATH}", upload_info['upload_url']],
               capture_output=True, text=True)

today_friendly = POSTING_DATE_FRIENDLY
payload = json.dumps({
    "files": [{"id": upload_info['file_id'], "title": f"AI Morning Brief - {today_friendly}"}],
    "channel_id": SLACK_CHANNEL,
    "initial_comment": f":tv: AI Morning Brief - Video Edition\n{today_friendly}\n\nYour daily AI intelligence briefing - watch the video!"
})
r = subprocess.run(["curl", "-s", "-X", "POST",
    "-H", f"Authorization: Bearer {SLACK_USER_TOKEN}",
    "-H", "Content-Type: application/json; charset=utf-8",
    "-d", payload,
    "https://slack.com/api/files.completeUploadExternal"
], capture_output=True, text=True)
res = json.loads(r.stdout)
print(f"Complete upload: ok={res.get('ok')}")

file_id = upload_info['file_id']
permalink = f"https://geminoai.slack.com/files/U085T05UVQX/{file_id.upper()}/ai_morning_brief_{POSTING_DATE_ISO.replace('-','_')}.mp4"

print(f"\n✓ DONE! Video posted to group chat (single post).")
print(f"  File: {VIDEO_PATH} ({size/1024/1024:.1f} MB)")
print(f"  Permalink: {permalink}")
