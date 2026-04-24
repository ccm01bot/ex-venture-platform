#!/usr/bin/env python3
"""Step 2: Generate video from the notebook with source, then post to Slack."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import json, time, base64, urllib.request, websocket, datetime

# NOTE: never cache date at import time - always recompute right before Slack post
EXVENTURE_PROMPT = """Generate a cinematic animated AI news video for YouTube. Feature a dynamic, consistent AI news anchor character presenting. Emulate the visual style and energetic pacing of a modern, engaging news show like 'Logo!', but with a sophisticated, professional AI theme suitable for a global tech audience. Incorporate fast-paced transitions, high-quality animated on-screen graphics, and an overall fun yet deeply informative tone. The video should feel cutting-edge, professional, and visually captivating."""
SLACK_WEBHOOK = "SLACK_WEBHOOK_PLACEHOLDER"
CDP = "http://127.0.0.1:9222"

resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = None
for tab in tabs:
    url = tab.get("url", "")
    if "notebooklm.google.com/notebook" in url:
        nlm_tab = tab
        break

if not nlm_tab:
    print("✗ No notebook tab found")
    sys.exit(1)

print(f"✓ Tab: {nlm_tab['url'][:80]}")
ws = websocket.create_connection(nlm_tab["webSocketDebuggerUrl"])
msg_id = 0

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

cdp("Page.enable")
cdp("Runtime.enable")

# Close any open modals
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(1)

ss("/tmp/morningbrief/v_start.png")
notebook_url = js("window.location.href")
print(f"Notebook: {notebook_url}")

# Click Video tile in Studio panel
print("\n--- Generating Video ---")
result = js("""(() => {
    // Find all elements that contain "Video" text in the Studio panel
    const allEls = document.querySelectorAll('*');
    for (const el of allEls) {
        if (el.childElementCount === 0 && el.textContent.trim().startsWith('Video')) {
            // Find closest clickable parent
            let parent = el;
            for (let i = 0; i < 5; i++) {
                parent = parent.parentElement;
                if (!parent) break;
                if (parent.tagName === 'BUTTON' || parent.getAttribute('role') === 'button' ||
                    parent.hasAttribute('tabindex') || parent.classList.contains('tile') ||
                    parent.classList.contains('card') || parent.onclick) {
                    parent.click();
                    return 'clicked: ' + parent.tagName + '.' + parent.className.substring(0,50);
                }
            }
            el.click();
            return 'clicked text directly';
        }
    }
    return 'not found';
})()""")
print(f"  Video tile: {result}")
time.sleep(3)
ss("/tmp/morningbrief/v_video_clicked.png")

# Look for what appeared - might be a panel or dialog
page_text = js("document.body.innerText.substring(0, 2000)")
print(f"  Page text excerpt: ...{page_text[500:800]}...")

# Click Generate button
print("  Clicking Generate...")
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.trim().includes('Generate'));
    if (btn) { btn.click(); return 'clicked'; }
    return 'not found';
})()""")
time.sleep(3)
ss("/tmp/morningbrief/v_generate1.png")

# Click confirm Generate if there's a second one
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.trim() === 'Generate');
    if (btn) btn.click();
})()""")
time.sleep(2)
ss("/tmp/morningbrief/v_generate2.png")

print("  ⏳ Waiting for video generation (5-15 minutes)...")

generated = False
for i in range(120):  # Up to 20 minutes
    time.sleep(10)

    if i % 3 == 0:
        ss(f"/tmp/morningbrief/v_progress_{i}.png")

    status = js("""(() => {
        const text = document.body.innerText;
        const video = document.querySelector('video');
        if (video && video.src) return 'video_element';
        if (text.includes('Your video overview is ready')) return 'ready_text';
        if (text.includes('Play') && text.includes('Video overview')) return 'play_available';
        if (text.includes('Download')) return 'download_available';
        if (text.includes('Generating') || text.includes('generating') || text.includes('Creating')) return 'generating';
        if (text.includes('Loading') || text.includes('loading')) return 'loading';
        if (text.includes('queued') || text.includes('Queued')) return 'queued';
        return 'waiting';
    })()""")

    if status in ('video_element', 'ready_text', 'play_available', 'download_available'):
        generated = True
        print(f"  ✓ Video ready! Status: {status} ({(i+1)*10}s)")
        break

    if i % 6 == 0:
        print(f"  [{status}] ({(i+1)*10}s)")

ss("/tmp/morningbrief/v_done.png")

if not generated:
    print("  ⚠ Video generation may still be in progress")

# Share notebook
print("\n--- Sharing notebook ---")
js("""(() => {
    const btns = document.querySelectorAll('button');
    for (const btn of btns) {
        const label = (btn.getAttribute('aria-label') || '').toLowerCase();
        if (label.includes('share')) { btn.click(); return 'clicked'; }
    }
    return 'not found';
})()""")
time.sleep(2)

# Enable public link
js("""(() => {
    const switches = document.querySelectorAll('[role="switch"]');
    switches.forEach(s => {
        if (s.getAttribute('aria-checked') !== 'true') s.click();
    });
})()""")
time.sleep(1)
ss("/tmp/morningbrief/v_shared.png")

cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(1)

# Post to Slack — compute date NOW, right before posting
POSTING_DATE = datetime.date.today().strftime("%A, %B %d, %Y")
print(f"\n--- Posting to Slack ({POSTING_DATE}) ---")
slack_msg = (
    "*:tv: AI Morning Brief — Video Edition*\n"
    f"*{POSTING_DATE}*\n\n"
    ":rotating_light: Your daily AI intelligence briefing is ready!\n\n"
    f":point_right: *Watch the full video briefing:* {notebook_url}\n\n"
    "_Open the link and click the Video Overview to watch today's AI news summary._\n\n"
    "---\n"
    "_Compiled by ExVenture AI Research Team | Next brief: tomorrow 11:00am_"
)

data = json.dumps({"text": slack_msg}).encode()
req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(f"  ✓ Slack: {resp.read().decode()}")

print(f"\n=== Complete! ===")
print(f"Notebook: {notebook_url}")

ws.close()
