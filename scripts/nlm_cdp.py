#!/usr/bin/env python3
"""Drive NotebookLM via Chrome DevTools Protocol (CDP) directly — no Playwright."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import json
import time
import os
import urllib.request
import websocket

BRIEF_FILE = "/tmp/morningbrief/brief_2026-04-14.md"
SLACK_WEBHOOK = "SLACK_WEBHOOK_PLACEHOLDER"
CDP = "http://127.0.0.1:9222"

with open(BRIEF_FILE) as f:
    brief_text = f.read()

# Find the NotebookLM notebook tab
resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = None
for tab in tabs:
    if "notebooklm.google.com/notebook" in tab.get("url", ""):
        nlm_tab = tab
        break

if not nlm_tab:
    # Use the main NotebookLM tab
    for tab in tabs:
        if "notebooklm.google.com" in tab.get("url", "") and "accounts" not in tab.get("url", ""):
            nlm_tab = tab
            break

if not nlm_tab:
    print("✗ No NotebookLM tab found!")
    sys.exit(1)

print(f"✓ Found tab: {nlm_tab['url'][:80]}")
ws_url = nlm_tab["webSocketDebuggerUrl"]

ws = websocket.create_connection(ws_url)
msg_id = 0

def cdp_send(method, params=None):
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
        # Skip events

def js(expression):
    """Run JS in the page and return the result."""
    result = cdp_send("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True,
    })
    val = result.get("result", {}).get("result", {}).get("value")
    return val

def screenshot(filename):
    """Take a screenshot."""
    result = cdp_send("Page.captureScreenshot", {"format": "png"})
    import base64
    data = result.get("result", {}).get("data", "")
    if data:
        with open(filename, "wb") as f:
            f.write(base64.b64decode(data))

print("✓ Connected via CDP\n")

# Enable necessary domains
cdp_send("Page.enable")
cdp_send("Runtime.enable")

# Check current state
title = js("document.title")
url = js("window.location.href")
print(f"Page: {title} | {url}")

screenshot("/tmp/morningbrief/cdp_start.png")

# Step 1: Close any open modals
print("\n--- Step 1: Preparing notebook ---")
js("""
    // Close any overlay/modal
    document.querySelectorAll('.cdk-overlay-backdrop').forEach(b => b.click());
    const closeBtn = document.querySelector('[aria-label="Close"]');
    if (closeBtn) closeBtn.click();
""")
time.sleep(1)

# Press Escape via CDP
cdp_send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp_send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(1)

screenshot("/tmp/morningbrief/cdp_clean.png")

# Click Add sources
print("  Clicking Add sources...")
js("""
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.includes('Add sources') || b.textContent.includes('Upload a source'));
    if (btn) btn.click();
""")
time.sleep(2)
screenshot("/tmp/morningbrief/cdp_add_sources.png")

# Click Copied text
print("  Clicking Copied text...")
js("""
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.includes('Copied text'));
    if (btn) btn.click();
""")
time.sleep(2)
screenshot("/tmp/morningbrief/cdp_copied_text.png")

# Fill textarea using keyboard simulation
print("  Filling textarea with morningbrief...")

# Focus the textarea
js("document.querySelector('textarea')?.focus()")
time.sleep(0.3)

# Type text using CDP Input.insertText (fast, simulates real input)
cdp_send("Input.insertText", {"text": brief_text})
time.sleep(1)

# Verify
length = js("document.querySelector('textarea')?.value?.length || 0")
print(f"  ✓ Textarea filled: {length} characters")

screenshot("/tmp/morningbrief/cdp_text_filled.png")

# Click Insert button
print("  Clicking Insert...")
js("""
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.trim() === 'Insert');
    if (btn) btn.click();
""")
time.sleep(8)

screenshot("/tmp/morningbrief/cdp_inserted.png")

# Check if source was added
sources = js("document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
print(f"  Sources: {sources}")

# Wait for processing
print("  ⏳ Waiting for source to process...")
time.sleep(10)

# Close modals
cdp_send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp_send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(1)

screenshot("/tmp/morningbrief/cdp_ready.png")

# Step 2: Generate Video
print("\n--- Step 2: Generating Video ---")

# Click on Video tile in Studio panel
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
screenshot("/tmp/morningbrief/cdp_video_clicked.png")

# Click Generate
js("""
    (() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.trim().includes('Generate'));
        if (btn) btn.click();
    })()
""")
time.sleep(3)
screenshot("/tmp/morningbrief/cdp_generate.png")

# Confirm if needed
js("""
    (() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.trim() === 'Generate');
        if (btn) btn.click();
    })()
""")
time.sleep(2)

print("  ⏳ Waiting for video generation (5-15 minutes)...")

generated = False
for i in range(90):
    time.sleep(10)

    if i % 3 == 0:
        screenshot(f"/tmp/morningbrief/cdp_progress_{i}.png")

    status = js("""
        (() => {
            const text = document.body.innerText;
            if (text.includes('Play') && !text.includes('Generating')) return 'done';
            const video = document.querySelector('video');
            if (video) return 'done';
            if (text.includes('Generating') || text.includes('generating') || text.includes('Loading')) return 'generating';
            return 'waiting';
        })()
    """)

    if status == 'done':
        generated = True
        print(f"  ✓ Video generated! ({(i+1)*10}s)")
        break

    if i % 6 == 0 and i > 0:
        print(f"  [{status}] ({(i+1)*10}s)")

screenshot("/tmp/morningbrief/cdp_video_done.png")

# Step 3: Share and post to Slack
print("\n--- Step 3: Posting to Slack ---")

notebook_url = js("window.location.href")

# Enable sharing
js("""
    (() => {
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            const label = btn.getAttribute('aria-label') || '';
            if (label.toLowerCase().includes('share')) { btn.click(); return; }
        }
    })()
""")
time.sleep(2)

js("""
    (() => {
        const switches = document.querySelectorAll('[role="switch"]');
        switches.forEach(s => {
            if (s.getAttribute('aria-checked') !== 'true') s.click();
        });
    })()
""")
time.sleep(1)

cdp_send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp_send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})

# Post to Slack
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
print(f"  ✓ Posted to Slack: {resp.read().decode()}")

print(f"\n=== Pipeline complete! ===")
print(f"Notebook: {notebook_url}")

ws.close()
