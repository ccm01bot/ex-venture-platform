#!/usr/bin/env python3
"""Close the customize dialog, access the existing video, download and upload."""

import sys, json, base64, urllib.request, time, os, subprocess
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = "C074JDBNJD9"
CDP = "http://127.0.0.1:9222"
VIDEO_PATH = "/tmp/morningbrief/morningbrief_video.mp4"

msg_id = 0
resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = [t for t in tabs if "notebooklm.google.com/notebook" in t.get("url", "")][0]
ws = websocket.create_connection(nlm_tab["webSocketDebuggerUrl"])

def cdp(method, params=None):
    global msg_id; msg_id += 1
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

# Close the customize dialog
print("Closing customize dialog...")
js("""(() => {
    // Click X button
    const btns = document.querySelectorAll('button');
    for (const btn of btns) {
        const label = btn.getAttribute('aria-label') || '';
        if (label === 'Close' || label === 'close') { btn.click(); return 'closed'; }
    }
    // Click overlay backdrop
    const backdrops = document.querySelectorAll('.cdk-overlay-backdrop');
    for (const b of backdrops) { b.click(); }
    return 'clicked backdrop';
})()""")
time.sleep(1)
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(2)
ss("/tmp/morningbrief/gv_closed.png")

# Now look at the page - video should be visible with the player
print("Looking for video player...")
video_info = js("""(() => {
    const videos = document.querySelectorAll('video');
    const info = [];
    for (const v of videos) {
        info.push({
            src: v.src ? v.src.substring(0, 100) : 'none',
            readyState: v.readyState,
            duration: v.duration,
            paused: v.paused,
            hidden: v.hidden,
            display: getComputedStyle(v).display,
        });
    }
    return JSON.stringify(info);
})()""")
print(f"  Videos: {video_info}")

# Try clicking the three-dot menu (...) on the video
print("\nLooking for three-dot menu on video...")
result = js("""(() => {
    // The three dots are usually a mat-icon-button with more_vert
    const btns = Array.from(document.querySelectorAll('button, [role="button"]'));
    for (const btn of btns) {
        const text = btn.textContent.trim();
        const label = btn.getAttribute('aria-label') || '';
        // Look for the three-dot menu specifically near the video/studio section
        if (text === 'more_vert' || label.includes('More options') || label.includes('more_vert')) {
            btn.click();
            return 'clicked: ' + (label || text);
        }
    }
    // Also try the ... button
    for (const btn of btns) {
        if (btn.textContent.trim() === '...' || btn.textContent.trim() === '⋮') {
            btn.click();
            return 'clicked dots';
        }
    }
    return 'not found';
})()""")
print(f"  {result}")
time.sleep(1)
ss("/tmp/morningbrief/gv_menu.png")

# Click Download in menu
dl = js("""(() => {
    const items = document.querySelectorAll('[role="menuitem"], [role="option"], button, a');
    for (const item of items) {
        if (item.textContent.trim().includes('Download')) {
            item.click();
            return 'clicked: ' + item.textContent.trim();
        }
    }
    return 'no download option';
})()""")
print(f"  {dl}")
time.sleep(3)
ss("/tmp/morningbrief/gv_after_dl.png")

# Check ~/Downloads for new file
import glob
downloads = glob.glob(os.path.expanduser("~/Downloads/*.mp4")) + \
            glob.glob(os.path.expanduser("~/Downloads/*.webm")) + \
            glob.glob(os.path.expanduser("~/Downloads/*video*"))
recent = sorted(downloads, key=os.path.getmtime, reverse=True)
if recent:
    newest = recent[0]
    age = time.time() - os.path.getmtime(newest)
    if age < 60:  # Less than 60 seconds old
        print(f"\n  Found new download: {newest} ({os.path.getsize(newest)/1024/1024:.1f} MB)")
        import shutil
        shutil.copy2(newest, VIDEO_PATH)

# Also check /tmp/morningbrief/downloads
dl_files = glob.glob("/tmp/morningbrief/downloads/*")
if dl_files:
    newest = sorted(dl_files, key=os.path.getmtime, reverse=True)[0]
    print(f"  Found in downloads dir: {newest}")
    import shutil
    shutil.copy2(newest, VIDEO_PATH)

# If still no video, try getting the video source URL and use CDP Network to fetch
if not os.path.exists(VIDEO_PATH) or os.path.getsize(VIDEO_PATH) < 50000:
    print("\nTrying Network.getResponseBody approach...")
    video_src = js("document.querySelector('video')?.src || ''")
    if video_src:
        # Navigate directly to video URL in a new tab-like approach
        # Use CDP to load the URL and get content
        print(f"  Video src: {video_src[:100]}")

        # Create an img element to test if the URL works with credentials
        works = js(f"""(async () => {{
            try {{
                const r = await fetch('{video_src}', {{credentials: 'include'}});
                const type = r.headers.get('content-type');
                const size = r.headers.get('content-length');
                if (type && type.includes('video')) {{
                    const buf = await r.arrayBuffer();
                    const bytes = new Uint8Array(buf);
                    // Convert to base64 in chunks
                    let binary = '';
                    for (let i = 0; i < bytes.length; i += 32768) {{
                        const chunk = bytes.subarray(i, Math.min(i + 32768, bytes.length));
                        binary += String.fromCharCode.apply(null, chunk);
                    }}
                    return JSON.stringify({{ok: true, type: type, size: bytes.length, data: btoa(binary)}});
                }}
                return JSON.stringify({{ok: false, type: type, size: size}});
            }} catch(e) {{
                return JSON.stringify({{ok: false, error: e.message}});
            }}
        }})()""")
        if works:
            info = json.loads(works)
            if info.get('ok') and info.get('data'):
                data = base64.b64decode(info['data'])
                with open(VIDEO_PATH, 'wb') as f:
                    f.write(data)
                print(f"  ✓ Downloaded via fetch: {len(data)/1024/1024:.1f} MB")
            else:
                print(f"  ✗ {info}")

# Final check and upload
if os.path.exists(VIDEO_PATH) and os.path.getsize(VIDEO_PATH) > 50000:
    ft = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout.strip()
    print(f"\n✓ Video: {ft} ({os.path.getsize(VIDEO_PATH)/1024/1024:.1f} MB)")

    if 'HTML' not in ft and SLACK_TOKEN:
        print("Uploading to Slack...")
        r = subprocess.run(["curl", "-s",
            "-F", f"length={os.path.getsize(VIDEO_PATH)}",
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
                print("✓ VIDEO UPLOADED TO SLACK #ai-updates!")
            else:
                print(f"✗ Slack: {res.get('error','')} — need 'files:write' scope")
        else:
            print(f"✗ {u.get('error','')}")
else:
    print(f"\n✗ No valid video file to upload")

ws.close()
print("\nDone.")
