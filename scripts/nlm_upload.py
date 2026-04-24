#!/usr/bin/env python3
"""
NotebookLM automation via CDP.
Strategy: Upload the brief as a .txt file instead of pasting text.
Then generate video and post to Slack.
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import json
import time
import os
import base64
import urllib.request
import websocket

BRIEF_FILE = "/tmp/morningbrief/brief_2026-04-14.md"
SLACK_WEBHOOK = "SLACK_WEBHOOK_PLACEHOLDER"
CDP = "http://127.0.0.1:9222"

with open(BRIEF_FILE) as f:
    brief_text = f.read()

# Find NotebookLM tab
resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = None
for tab in tabs:
    url = tab.get("url", "")
    if "notebooklm.google.com" in url and "accounts" not in url and "RotateCookies" not in url:
        nlm_tab = tab
        break

if not nlm_tab:
    print("✗ No NotebookLM tab found!")
    sys.exit(1)

print(f"✓ Tab: {nlm_tab['url'][:80]}")
ws = websocket.create_connection(nlm_tab["webSocketDebuggerUrl"])
msg_id = 0

def cdp(method, params=None):
    global msg_id
    msg_id += 1
    msg = {"id": msg_id, "method": method}
    if params:
        msg["params"] = params
    ws.send(json.dumps(msg))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp

def js(expr):
    r = cdp("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    return r.get("result", {}).get("result", {}).get("value")

def screenshot(name):
    r = cdp("Page.captureScreenshot", {"format": "png"})
    d = r.get("result", {}).get("data", "")
    if d:
        with open(name, "wb") as f:
            f.write(base64.b64decode(d))

cdp("Page.enable")
cdp("Runtime.enable")
cdp("DOM.enable")

print("✓ CDP connected\n")

# Navigate to NotebookLM home to create a fresh notebook
print("--- Creating fresh notebook ---")
js("window.location.href = 'https://notebooklm.google.com/'")
time.sleep(3)

screenshot("/tmp/morningbrief/u_home.png")

# Click Create new notebook
js("""
    (() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Create new'));
        if (btn) btn.click();
        return btn ? 'clicked' : 'not found';
    })()
""")
time.sleep(3)
screenshot("/tmp/morningbrief/u_created.png")

# Close the "add source" popup that appears
js("""
    (() => {
        const close = document.querySelector('[aria-label="Close"]');
        if (close) close.click();
    })()
""")
time.sleep(1)

cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(1)

screenshot("/tmp/morningbrief/u_clean.png")

# Now use file upload approach - click "Add sources", then "Upload files"
print("\n--- Uploading morningbrief as file ---")

# Click Add sources
js("""
    (() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Add sources'));
        if (btn) { btn.click(); return 'clicked'; }
        return 'not found';
    })()
""")
time.sleep(2)

# Click Upload files
js("""
    (() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Upload files'));
        if (btn) { btn.click(); return 'clicked'; }
        return 'not found';
    })()
""")
time.sleep(1)

screenshot("/tmp/morningbrief/u_upload_dialog.png")

# Use CDP to intercept the file chooser
# First, enable file chooser interception
cdp("Page.setInterceptFileChooserDialog", {"enabled": True})

# Click Upload files again to trigger file dialog
js("""
    (() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Upload files'));
        if (btn) { btn.click(); return 'clicked'; }
        // Also try clicking the drop zone or input
        const input = document.querySelector('input[type="file"]');
        if (input) { input.click(); return 'clicked input'; }
        return 'not found';
    })()
""")

# Wait for file chooser event
time.sleep(1)

# Read the file content
with open(BRIEF_FILE, 'rb') as f:
    file_data = base64.b64encode(f.read()).decode()

# Find the file input and set files via CDP DOM
# Use DOM.setFileInputFiles
file_input = js("""
    (() => {
        const inputs = document.querySelectorAll('input[type="file"]');
        for (const inp of inputs) {
            return true;
        }
        return false;
    })()
""")

if file_input:
    # Get the file input node
    doc = cdp("DOM.getDocument")
    root_id = doc["result"]["root"]["nodeId"]

    # Find file input
    result = cdp("DOM.querySelectorAll", {
        "nodeId": root_id,
        "selector": "input[type='file']"
    })
    file_nodes = result.get("result", {}).get("nodeIds", [])

    if file_nodes:
        # Write the brief to a temp .txt file
        txt_path = "/tmp/morningbrief/brief_2026-04-14.txt"
        with open(txt_path, "w") as f:
            f.write(brief_text)

        # Set the file on the input
        cdp("DOM.setFileInputFiles", {
            "nodeId": file_nodes[0],
            "files": [txt_path]
        })
        print("  ✓ File set on input!")
        time.sleep(5)
    else:
        print("  ✗ No file input nodes found")
else:
    print("  ✗ No file input found, trying drag and drop approach")

screenshot("/tmp/morningbrief/u_after_upload.png")

# Wait for upload to process
print("  ⏳ Waiting for upload and processing...")
for i in range(12):
    time.sleep(5)
    sources = js("document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
    if sources != '0':
        print(f"  ✓ Source added! ({sources} sources)")
        break
    if i % 2 == 0:
        screenshot(f"/tmp/morningbrief/u_wait_{i}.png")

# Close modal
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(2)

screenshot("/tmp/morningbrief/u_source_ready.png")

# Verify source was added
sources = js("document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
print(f"  Final source count: {sources}")

# Step 2: Generate Video
print("\n--- Step 2: Generating Video ---")

# Click Video tile in Studio panel
result = js("""
    (() => {
        const allEls = document.querySelectorAll('*');
        for (const el of allEls) {
            if (el.childElementCount === 0 && el.textContent.trim().match(/^Video/)) {
                const clickable = el.closest('button, [role="button"], a, [tabindex], div[class*="card"], div[class*="tile"]');
                if (clickable) { clickable.click(); return 'clicked'; }
            }
        }
        return 'not found';
    })()
""")
print(f"  Video tile: {result}")
time.sleep(3)
screenshot("/tmp/morningbrief/u_video_clicked.png")

# Click Generate buttons
for _ in range(2):
    js("""
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => b.textContent.trim().includes('Generate'));
            if (btn) btn.click();
        })()
    """)
    time.sleep(2)

screenshot("/tmp/morningbrief/u_generating.png")

print("  ⏳ Waiting for video (5-15 minutes)...")

generated = False
for i in range(90):
    time.sleep(10)

    if i % 3 == 0:
        screenshot(f"/tmp/morningbrief/u_progress_{i}.png")

    status = js("""
        (() => {
            const text = document.body.innerText;
            const video = document.querySelector('video');
            if (video) return 'done';
            if (text.includes('Download') && !text.includes('Generating')) return 'done';
            if (text.includes('Play') && !text.includes('Generating')) return 'done';
            if (text.includes('Generating') || text.includes('Loading')) return 'generating';
            return 'waiting';
        })()
    """)

    if status == 'done':
        generated = True
        print(f"  ✓ Video ready! ({(i+1)*10}s)")
        break

    if i % 6 == 0 and i > 0:
        print(f"  [{status}] ({(i+1)*10}s)")

screenshot("/tmp/morningbrief/u_video_done.png")

# Step 3: Post to Slack
print("\n--- Step 3: Posting to Slack ---")

notebook_url = js("window.location.href")

# Share notebook
js("""
    (() => {
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            if ((btn.getAttribute('aria-label') || '').toLowerCase().includes('share')) {
                btn.click(); return;
            }
        }
    })()
""")
time.sleep(2)
js("""
    (() => {
        document.querySelectorAll('[role="switch"]').forEach(s => {
            if (s.getAttribute('aria-checked') !== 'true') s.click();
        });
    })()
""")
time.sleep(1)
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})

slack_msg = (
    "*:tv: AI Morning Brief — Video Edition*\n"
    "*Monday, April 14, 2026*\n\n"
    ":rotating_light: Your daily AI intelligence briefing is ready!\n\n"
    f":point_right: *Watch the full video briefing:* {notebook_url}\n\n"
    "_Open the link and click 'Video Overview' to watch today's AI news summary._\n\n"
    "---\n"
    "_Compiled by ExVenture AI Research Team | Next brief: tomorrow 11:00am_"
)

data = json.dumps({"text": slack_msg}).encode()
req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(f"  ✓ Slack: {resp.read().decode()}")

print(f"\n=== Done! ===")
print(f"Notebook: {notebook_url}")

ws.close()
