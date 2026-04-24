#!/usr/bin/env python3
"""Click play, wait for video to load, click three-dot menu → Download."""

import sys, json, base64, urllib.request, time, os, subprocess, glob
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = "C074JDBNJD9"
CDP = "http://127.0.0.1:9222"
DOWNLOAD_DIR = "/tmp/morningbrief/downloads"
VIDEO_PATH = "/tmp/morningbrief/morningbrief_video.mp4"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
for f in glob.glob(f"{DOWNLOAD_DIR}/*"):
    os.unlink(f)

msg_id = 0
resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = [t for t in tabs if "notebooklm.google.com/notebook" in t.get("url", "")][0]
ws = websocket.create_connection(nlm_tab["webSocketDebuggerUrl"])

def cdp(method, params=None):
    global msg_id
    msg_id += 1
    msg = {"id": msg_id, "method": method}
    if params: msg["params"] = params
    ws.send(json.dumps(msg))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == msg_id: return r

def js(expr):
    r = cdp("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    return r.get("result", {}).get("result", {}).get("value")

def ss(name):
    r = cdp("Page.captureScreenshot", {"format": "png"})
    d = r.get("result", {}).get("data", "")
    if d:
        with open(name, "wb") as f: f.write(base64.b64decode(d))

cdp("Runtime.enable")
cdp("Page.enable")

# Set download directory
cdp("Browser.setDownloadBehavior", {
    "behavior": "allow",
    "downloadPath": DOWNLOAD_DIR,
})

# First go back to the notebook view
js("window.history.back()")
time.sleep(2)
ss("/tmp/morningbrief/d5_start.png")

# Navigate to the notebook if needed
current_url = js("window.location.href")
print(f"Current: {current_url}")

# Click Video Overview in Studio
print("Clicking Video Overview...")
js("""(() => {
    const allEls = document.querySelectorAll('*');
    for (const el of allEls) {
        if (el.childElementCount === 0 && el.textContent.trim().match(/^Video/)) {
            const clickable = el.closest('button, [role="button"], a, div[tabindex]');
            if (clickable) { clickable.click(); return 'clicked'; }
        }
    }
    return 'not found';
})()""")
time.sleep(3)
ss("/tmp/morningbrief/d5_video_panel.png")

# Click play button
print("Clicking play...")
js("""(() => {
    const play = document.querySelector('video');
    if (play) { play.play(); return 'played video element'; }
    const btn = document.querySelector('[aria-label*="Play"], button[aria-label*="play"]');
    if (btn) { btn.click(); return 'clicked play btn'; }
    return 'not found';
})()""")
time.sleep(5)

# Wait for video to actually load
print("Waiting for video source to load...")
for i in range(20):
    src = js("""(() => {
        const v = document.querySelector('video');
        if (!v) return 'no video element';
        return JSON.stringify({
            src: v.src ? v.src.substring(0, 120) : 'none',
            currentSrc: v.currentSrc ? v.currentSrc.substring(0, 120) : 'none',
            readyState: v.readyState,
            networkState: v.networkState,
            duration: v.duration,
            error: v.error ? v.error.message : 'none'
        });
    })()""")
    print(f"  [{i*2}s] {src}")
    info = json.loads(src) if src and src.startswith('{') else {}

    if info.get('readyState', 0) >= 2 or (info.get('duration', 0) > 0):
        print("  ✓ Video loaded!")
        break
    time.sleep(2)

ss("/tmp/morningbrief/d5_loaded.png")

# Now try right-click → save as via CDP
# Use the video's actual source URL with proper cookies
video_src = js("""(() => {
    const v = document.querySelector('video');
    return v ? (v.currentSrc || v.src || '') : '';
})()""")
print(f"\nVideo source: {video_src[:150] if video_src else 'none'}")

if video_src and 'blob:' not in video_src:
    # Get all cookies for the download
    cookie_result = cdp("Network.getAllCookies")
    cookies = cookie_result.get("result", {}).get("cookies", [])
    cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies if 'google' in c.get('domain', '')])

    # Try curl with cookies
    print("Downloading via curl with cookies...")
    result = subprocess.run([
        "curl", "-s", "-L", "-o", VIDEO_PATH,
        "-H", f"Cookie: {cookie_header}",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "-H", "Referer: https://notebooklm.google.com/",
        video_src
    ], capture_output=True, text=True, timeout=120)

    if os.path.exists(VIDEO_PATH):
        size = os.path.getsize(VIDEO_PATH)
        file_type = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout.strip()
        print(f"  Size: {size/1024/1024:.1f} MB")
        print(f"  Type: {file_type}")

elif video_src and 'blob:' in video_src:
    # Blob URL - capture via MediaRecorder or direct blob fetch
    print("Blob URL - downloading via page context...")

    # Use MediaSource/SourceBuffer approach or direct blob fetch
    b64 = js("""(async () => {
        const video = document.querySelector('video');
        if (!video) return JSON.stringify({error: 'no video'});

        // Try canvas capture approach
        const canvas = document.createElement('canvas');
        // ... canvas approach won't work for full video

        // Try fetching the blob URL
        try {
            const resp = await fetch(video.src);
            const blob = await resp.blob();
            return new Promise(resolve => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(JSON.stringify({
                    ok: true,
                    data: reader.result.split(',')[1],
                    size: blob.size,
                    type: blob.type
                }));
                reader.readAsDataURL(blob);
            });
        } catch(e) {
            return JSON.stringify({error: e.message});
        }
    })()""")

    if b64:
        info = json.loads(b64)
        if info.get('ok'):
            data = base64.b64decode(info['data'])
            with open(VIDEO_PATH, 'wb') as f:
                f.write(data)
            print(f"  ✓ Downloaded: {len(data)/1024/1024:.1f} MB (type: {info.get('type')})")
        else:
            print(f"  ✗ Error: {info.get('error')}")

# Upload to Slack
if os.path.exists(VIDEO_PATH) and os.path.getsize(VIDEO_PATH) > 50000:
    file_type = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout
    if 'HTML' not in file_type and 'text' not in file_type.lower():
        print(f"\n✓ Video file ready: {os.path.getsize(VIDEO_PATH)/1024/1024:.1f} MB")
        if SLACK_TOKEN:
            print("Uploading to Slack...")
            r = subprocess.run(["curl", "-s",
                "-F", f"length={os.path.getsize(VIDEO_PATH)}",
                "-F", "filename=AI_Morning_Brief_April_14_2026.mp4",
                "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                "https://slack.com/api/files.getUploadURLExternal"
            ], capture_output=True, text=True)
            upload = json.loads(r.stdout) if r.stdout else {}
            if upload.get('ok'):
                subprocess.run(["curl", "-s", "-X", "POST", "-F", f"file=@{VIDEO_PATH}", upload['upload_url']])
                payload = json.dumps({
                    "files": [{"id": upload['file_id'], "title": "AI Morning Brief - April 14, 2026"}],
                    "channel_id": SLACK_CHANNEL,
                    "initial_comment": ":tv: *AI Morning Brief — Video Edition*\n*Monday, April 14, 2026*\n\n:rotating_light: Watch the video!"
                })
                r = subprocess.run(["curl", "-s", "-X", "POST",
                    "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                    "-H", "Content-Type: application/json",
                    "-d", payload,
                    "https://slack.com/api/files.completeUploadExternal"
                ], capture_output=True, text=True)
                result = json.loads(r.stdout) if r.stdout else {}
                print(f"  Result: {result.get('ok')} / {result.get('error','')}")
            else:
                print(f"  ✗ {upload.get('error','')}")
    else:
        print(f"\n✗ Downloaded file is HTML, not video")

ws.close()
print("\nDone.")
