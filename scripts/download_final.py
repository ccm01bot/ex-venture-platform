#!/usr/bin/env python3
"""Navigate to the notebook, play the video, download via blob fetch, upload to Slack."""

import sys, json, base64, urllib.request, time, os, subprocess
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

NOTEBOOK_URL = "https://notebooklm.google.com/notebook/ddacc32d-9b3f-4549-9dc9-06eb87137307"
SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = "C074JDBNJD9"
CDP = "http://127.0.0.1:9222"
VIDEO_PATH = "/tmp/morningbrief/morningbrief_video.mp4"

msg_id = 0
resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = None
for tab in tabs:
    if "notebooklm.google.com" in tab.get("url", "") and "accounts" not in tab.get("url", "") and "Rotate" not in tab.get("url", ""):
        nlm_tab = tab
        break

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
cdp("Network.enable")

# Navigate to the notebook
print(f"Navigating to notebook...")
js(f"window.location.href = '{NOTEBOOK_URL}'")
time.sleep(5)
ss("/tmp/morningbrief/final_notebook.png")

# Click on Video Overview in Studio
print("Opening Video Overview...")
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
time.sleep(5)
ss("/tmp/morningbrief/final_video_panel.png")

# Click play if needed
js("""(() => {
    const btn = document.querySelector('[aria-label*="Play"], [aria-label*="play"]');
    if (btn) { btn.click(); return 'clicked play'; }
    const v = document.querySelector('video');
    if (v) { v.play(); return 'played video'; }
    return 'not found';
})()""")
time.sleep(5)

# Wait for video to load
print("Waiting for video to load...")
for i in range(15):
    info = js("""(() => {
        const v = document.querySelector('video');
        if (!v) return 'no video';
        return v.src.substring(0, 50) + ' | ready=' + v.readyState + ' | dur=' + v.duration;
    })()""")
    print(f"  [{i*3}s] {info}")
    if 'ready=4' in str(info) or 'ready=3' in str(info) or 'ready=2' in str(info):
        break
    time.sleep(3)

ss("/tmp/morningbrief/final_playing.png")

# Download the video
print("\nDownloading video...")
video_src = js("document.querySelector('video')?.src || ''")
print(f"  src: {video_src[:120] if video_src else 'none'}")

if video_src:
    # Fetch blob or URL through page context
    result = js("""(async () => {
        const video = document.querySelector('video');
        if (!video || !video.src) return JSON.stringify({error: 'no src'});

        try {
            // For non-blob URLs, create an XHR with credentials
            const resp = await fetch(video.src, {mode: 'no-cors', credentials: 'include'});
            const blob = await resp.blob();

            // Convert to base64 in chunks to avoid memory issues
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => {
                    const b64 = reader.result.split(',')[1] || '';
                    resolve(JSON.stringify({ok: true, size: blob.size, type: blob.type, data: b64}));
                };
                reader.readAsDataURL(blob);
            });
        } catch(e) {
            return JSON.stringify({error: e.message});
        }
    })()""")

    if result:
        info = json.loads(result)
        if info.get('ok') and info.get('data'):
            data = base64.b64decode(info['data'])
            with open(VIDEO_PATH, 'wb') as f:
                f.write(data)
            file_type = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout.strip()
            print(f"  ✓ {len(data)/1024/1024:.1f} MB | {file_type}")

            if 'HTML' not in file_type and len(data) > 50000:
                if SLACK_TOKEN:
                    print("\nUploading to Slack #ai-updates...")
                    r = subprocess.run(["curl", "-s",
                        "-F", f"length={len(data)}",
                        "-F", "filename=AI_Morning_Brief_April_14_2026.mp4",
                        "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                        "https://slack.com/api/files.getUploadURLExternal"
                    ], capture_output=True, text=True)
                    u = json.loads(r.stdout) if r.stdout else {}
                    if u.get('ok'):
                        subprocess.run(["curl", "-s", "-X", "POST", "-F", f"file=@{VIDEO_PATH}", u['upload_url']])
                        payload = json.dumps({
                            "files": [{"id": u['file_id'], "title": "AI Morning Brief - April 14, 2026"}],
                            "channel_id": SLACK_CHANNEL,
                            "initial_comment": ":tv: *AI Morning Brief — Video Edition*\n*Monday, April 14, 2026*\n\n:rotating_light: Watch the video!"
                        })
                        r = subprocess.run(["curl", "-s", "-X", "POST",
                            "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                            "-H", "Content-Type: application/json",
                            "-d", payload,
                            "https://slack.com/api/files.completeUploadExternal"
                        ], capture_output=True, text=True)
                        res = json.loads(r.stdout) if r.stdout else {}
                        if res.get('ok'):
                            print("  ✓ VIDEO UPLOADED TO SLACK!")
                        else:
                            print(f"  ✗ {res.get('error', r.stdout[:200])}")
                    else:
                        print(f"  ✗ Slack: {u.get('error','')}")
                        print("  Add 'files:write' scope at api.slack.com/apps")
        else:
            print(f"  ✗ {info.get('error', 'unknown error')}")

ws.close()
print("\nDone.")
