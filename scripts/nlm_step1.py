#!/usr/bin/env python3
"""Step 1 only: Navigate to NotebookLM, create notebook, add source via Copied text.
Uses Input.dispatchKeyEvent to type character by character into textarea."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import json, time, base64, urllib.request, websocket

BRIEF_FILE = "/tmp/morningbrief/brief_2026-04-14.md"
CDP = "http://127.0.0.1:9222"

with open(BRIEF_FILE) as f:
    brief_text = f.read()

resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = None
for tab in tabs:
    url = tab.get("url", "")
    if "notebooklm.google.com" in url and "accounts" not in url and "Rotate" not in url:
        nlm_tab = tab
        break

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

# Go to home
print("Navigating to NotebookLM home...")
js("window.location.href = 'https://notebooklm.google.com/'")
time.sleep(4)
ss("/tmp/morningbrief/s1_home.png")

# Create new notebook
print("Creating notebook...")
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.includes('Create new'));
    if (btn) btn.click();
})()""")
time.sleep(4)
ss("/tmp/morningbrief/s1_created.png")

# Now the "add source" modal should be open
# Click "Copied text" button
print("Clicking 'Copied text'...")
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.includes('Copied text'));
    if (btn) btn.click();
})()""")
time.sleep(3)
ss("/tmp/morningbrief/s1_paste_dialog.png")

# Now focus the textarea
print("Focusing textarea...")
js("""(() => {
    const ta = document.querySelector('textarea');
    if (ta) { ta.focus(); ta.click(); }
})()""")
time.sleep(0.5)

# Use Input.insertText which simulates real keyboard input
# This should trigger Angular's input handling
print(f"Inserting text ({len(brief_text)} chars)...")
cdp("Input.insertText", {"text": brief_text})
time.sleep(2)

# Verify textarea content
val = js("document.querySelector('textarea')?.value?.length || 0")
print(f"Textarea length: {val}")

# Check if Insert button is enabled
insert_state = js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.trim() === 'Insert');
    if (!btn) return 'not found';
    return btn.disabled ? 'disabled' : 'enabled';
})()""")
print(f"Insert button: {insert_state}")

ss("/tmp/morningbrief/s1_text_filled.png")

# If insert is disabled, try triggering input events manually
if insert_state == 'disabled':
    print("Insert disabled, triggering input events...")
    js("""(() => {
        const ta = document.querySelector('textarea');
        if (ta) {
            ta.dispatchEvent(new Event('input', {bubbles: true}));
            ta.dispatchEvent(new Event('change', {bubbles: true}));
            ta.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true}));
            ta.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true}));
        }
    })()""")
    time.sleep(1)
    insert_state = js("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.trim() === 'Insert');
        return btn?.disabled ? 'disabled' : 'enabled';
    })()""")
    print(f"Insert button after events: {insert_state}")

# Try clicking Insert regardless
print("Clicking Insert...")
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.trim() === 'Insert');
    if (btn) {
        btn.disabled = false;
        btn.click();
    }
})()""")
time.sleep(8)
ss("/tmp/morningbrief/s1_after_insert.png")

# Check sources
sources = js("""(() => {
    const text = document.body.innerText;
    const match = text.match(/(\\d+)\\s*source/);
    return match ? match[1] : '0';
})()""")
print(f"\nSources: {sources}")
print(f"URL: {js('window.location.href')}")

ss("/tmp/morningbrief/s1_final.png")
ws.close()
print("\nDone. Check screenshots in /tmp/morningbrief/")
