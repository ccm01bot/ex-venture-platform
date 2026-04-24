#!/usr/bin/env python3
"""Close the customize dialog, find the completed video, download it, upload to Slack."""

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
nlm_tab = None
for tab in tabs:
    if "notebooklm.google.com/notebook" in tab.get("url", ""):
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

print("✓ Connected")

# Close the "Customize Video" dialog
print("\n--- Closing customize dialog ---")
js("""(() => {
    // Close button
    const close = document.querySelector('[aria-label="Close"]');
    if (close) close.click();
})()""")
time.sleep(1)

cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(2)

ss("/tmp/morningbrief/fix_after_close.png")

# Check if there's already a completed video (I saw a play button in the screenshot)
print("\n--- Looking for completed video ---")

# Click on Video Overview in Studio panel to see if there's a completed one
result = js("""(() => {
    const allEls = document.querySelectorAll('*');
    for (const el of allEls) {
        const text = el.textContent.trim();
        if (el.childElementCount === 0 && (text === 'Video Overview' || text.startsWith('Video'))) {
            const clickable = el.closest('button, [role="button"], a, div[tabindex]');
            if (clickable) { clickable.click(); return 'clicked: ' + text; }
        }
    }
    return 'not found';
})()""")
print(f"  {result}")
time.sleep(3)
ss("/tmp/morningbrief/fix_video_panel.png")

# Look for play button or video element
has_video = js("""(() => {
    const video = document.querySelector('video');
    if (video) return 'video element found, src: ' + (video.src || 'no src').substring(0, 100);

    // Check for play button
    const play = document.querySelector('[aria-label*="Play"], [aria-label*="play"], button[aria-label*="Play"]');
    if (play) return 'play button found';

    // Check page text
    const text = document.body.innerText;
    if (text.includes('Video overview') && !text.includes('Generating')) return 'video section exists, not generating';

    return 'no video found';
})()""")
print(f"  Status: {has_video}")

# Click the play button if found
if 'play' in has_video.lower():
    js("""(() => {
        const play = document.querySelector('[aria-label*="Play"], [aria-label*="play"], button[aria-label*="Play"]');
        if (play) play.click();
    })()""")
    time.sleep(3)
    ss("/tmp/morningbrief/fix_after_play.png")

    # Now check for video element
    video_src = js("""(() => {
        const video = document.querySelector('video');
        if (video && video.src) return video.src;
        if (video) {
            const source = video.querySelector('source');
            if (source) return source.src;
        }
        return '';
    })()""")
    print(f"  Video src: {video_src[:100] if video_src else 'none'}")

# Try to find the three-dot menu on the video and click download
print("\n--- Looking for download option ---")
js("""(() => {
    // Find all three-dot/more buttons near video
    const btns = Array.from(document.querySelectorAll('button'));
    const moreBtn = btns.find(b => {
        const label = b.getAttribute('aria-label') || '';
        const text = b.textContent.trim();
        return label.includes('More') || label.includes('more') ||
               text === 'more_vert' || text === '⋮' ||
               label.includes('options') || label.includes('Options');
    });
    if (moreBtn) { moreBtn.click(); return 'clicked more'; }
    return 'no more button';
})()""")
time.sleep(1)
ss("/tmp/morningbrief/fix_more_menu.png")

# Click download in menu
js("""(() => {
    const items = document.querySelectorAll('[role="menuitem"], button, a');
    for (const item of items) {
        if (item.textContent.includes('Download')) {
            item.click();
            return 'clicked download';
        }
    }
    return 'no download option';
})()""")
time.sleep(3)

# Check for video element now
video_src = js("""(() => {
    const video = document.querySelector('video');
    if (video && video.src) return video.src;
    if (video) {
        const source = video.querySelector('source');
        if (source) return source.src;
    }
    // Check all video/audio sources
    const sources = document.querySelectorAll('video source, video[src]');
    for (const s of sources) return s.src || s.getAttribute('src');
    return '';
})()""")
print(f"  Video src after menu: {video_src[:150] if video_src else 'none'}")

ss("/tmp/morningbrief/fix_current.png")

# If we have a video source, download it
if video_src:
    print(f"\n--- Downloading video ---")
    if video_src.startswith('blob:'):
        print("  Blob URL detected, fetching via page context...")
        b64_data = js("""(async () => {
            const video = document.querySelector('video');
            if (!video || !video.src) return '';
            try {
                const resp = await fetch(video.src);
                const blob = await resp.blob();
                return new Promise(resolve => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result.split(',')[1]);
                    reader.readAsDataURL(blob);
                });
            } catch(e) { return 'error: ' + e.message; }
        })()""")
        if b64_data and not b64_data.startswith('error'):
            with open(VIDEO_PATH, 'wb') as f:
                f.write(base64.b64decode(b64_data))
            print(f"  ✓ Downloaded: {os.path.getsize(VIDEO_PATH) / 1024 / 1024:.1f} MB")
        else:
            print(f"  ✗ Blob fetch failed: {b64_data}")
    elif video_src.startswith('http'):
        print("  Direct URL, downloading...")
        req = urllib.request.Request(video_src)
        resp = urllib.request.urlopen(req)
        with open(VIDEO_PATH, 'wb') as f:
            f.write(resp.read())
        print(f"  ✓ Downloaded: {os.path.getsize(VIDEO_PATH) / 1024 / 1024:.1f} MB")
else:
    # No video element. The first video gen might still be going.
    # Let's check if we need to click Generate in the Brief format
    print("\n--- No video found. Checking if we need to generate ---")
    ss("/tmp/morningbrief/fix_no_video.png")

    # Check page state
    page_has = js("""(() => {
        const text = document.body.innerText;
        return {
            generating: text.includes('Generating'),
            customize: text.includes('Customize'),
            generate_btn: !!Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Generate'),
            play_btn: !!document.querySelector('[aria-label*="Play"]'),
            video_el: !!document.querySelector('video'),
        };
    })()""")
    print(f"  Page state: {page_has}")

# Upload to Slack if we have the video
if os.path.exists(VIDEO_PATH) and os.path.getsize(VIDEO_PATH) > 1000:
    print(f"\n--- Uploading to Slack ---")
    size_mb = os.path.getsize(VIDEO_PATH) / 1024 / 1024
    print(f"  File: {VIDEO_PATH} ({size_mb:.1f} MB)")

    result = subprocess.run([
        "curl", "-s",
        "-F", f"file=@{VIDEO_PATH}",
        "-F", f"channels={SLACK_CHANNEL}",
        "-F", "initial_comment=:tv: *AI Morning Brief — Video Edition*\n*Monday, April 14, 2026*\n\n:rotating_light: Your daily AI intelligence briefing — watch the video summary!",
        "-F", "title=AI Morning Brief - April 14, 2026.mp4",
        "-H", f"Authorization: Bearer {SLACK_TOKEN}",
        "https://slack.com/api/files.upload"
    ], capture_output=True, text=True)

    resp_data = json.loads(result.stdout) if result.stdout else {}
    if resp_data.get("ok"):
        print(f"  ✓ Uploaded to Slack!")
        file_url = resp_data.get("file", {}).get("permalink", "")
        print(f"  Link: {file_url}")
    else:
        print(f"  ✗ Upload failed: {resp_data.get('error', result.stdout[:200])}")
else:
    print("\n  No video file to upload yet.")

print("\nDone.")
ws.close()
