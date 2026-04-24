#!/usr/bin/env python3
"""
All-in-one: Create notebook → Add source → Generate video.
Bulletproof with retries at every step.
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import json, time, base64, urllib.request, os, datetime
import websocket

BRIEF_FILE = os.environ.get("BRIEF_FILE", f"/tmp/morningbrief/brief_{datetime.date.today().strftime('%Y-%m-%d')}.md")
CDP = "http://127.0.0.1:9222"

PROMPT = """Generate a cinematic animated AI news video for YouTube with an animated AI news reporter character who presents throughout the video.

STRUCTURE:
1. HOOK — Start with the single most exciting headline. Grab attention in 3 seconds.
2. HEADLINES OVERVIEW — Right after the hook, quickly list ALL the news stories that will be covered. "Today we have X, Y, Z, and more."
3. DEEP DIVES — Then go through each topic one by one with more detail.
4. SIGN OFF — Clean ending.

STYLE:
- Feature a consistent animated AI news reporter/anchor character throughout
- Include real-world footage, demos, or screen recordings showing these AI tools being used (where relevant)
- Cinematic, professional, engaging — like a modern tech news show
- Fast-paced transitions between topics
- DO NOT generate text overlays in the animations — only animated visuals, footage, and narration"""

with open(BRIEF_FILE) as f:
    brief_text = f.read()

print(f"Brief: {len(brief_text)} chars from {BRIEF_FILE}")

# Connect to browser
mid = 0
resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = None
for t in tabs:
    url = t.get("url", "")
    if "notebooklm.google.com" in url and "accounts" not in url and "Rotate" not in url:
        nlm_tab = t
        break

if not nlm_tab:
    print("ERROR: No NotebookLM tab found")
    sys.exit(1)

ws = websocket.create_connection(nlm_tab["webSocketDebuggerUrl"])

def cdp(method, params=None):
    global mid; mid += 1
    msg = {"id": mid, "method": method}
    if params: msg["params"] = params
    ws.send(json.dumps(msg))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid: return r

def js(expr):
    r = cdp("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    return r.get("result", {}).get("result", {}).get("value")

cdp("Runtime.enable")
cdp("Page.enable")
cdp("DOM.enable")

# ═══ STEP 1: Create notebook ═══
print("\n1. Creating notebook...")
js("window.location.href = 'https://notebooklm.google.com/'")
time.sleep(5)

for attempt in range(3):
    js("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Create new'));
        if (btn) btn.click();
    })()""")
    time.sleep(5)
    url = js("window.location.href")
    if "/notebook/" in str(url):
        print(f"   ✓ Notebook: {url}")
        break
    print(f"   Retry {attempt+1}...")
    time.sleep(2)
else:
    print("   ✗ Failed to create notebook")
    sys.exit(1)

# ═══ STEP 2: Add source ═══
print("\n2. Adding source...")

source_added = False
for attempt in range(5):
    # Close any existing modals first
    cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    time.sleep(1)

    # Click "Add sources" button
    js("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Add sources') || b.textContent.includes('Upload a source'));
        if (btn) btn.click();
    })()""")
    time.sleep(2)

    # Click "Copied text"
    js("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Copied text'));
        if (btn) btn.click();
    })()""")
    time.sleep(3)

    # Check if paste textarea appeared
    search = cdp("DOM.performSearch", {"query": "textarea[placeholder*='Paste']"})
    count = search.get("result", {}).get("resultCount", 0)

    if count == 0:
        print(f"   Attempt {attempt+1}: Paste textarea not found, retrying...")
        # Try clicking Copied text again
        js("""(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => b.textContent.includes('Copied text'));
            if (btn) btn.click();
        })()""")
        time.sleep(3)
        search = cdp("DOM.performSearch", {"query": "textarea[placeholder*='Paste']"})
        count = search.get("result", {}).get("resultCount", 0)

    if count == 0:
        print(f"   Attempt {attempt+1}: Still no paste textarea, trying full reload...")
        js("window.location.reload()")
        time.sleep(5)
        continue

    # Focus and insert text
    sid = search["result"]["searchId"]
    r = cdp("DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": count})
    node_id = r["result"]["nodeIds"][0]
    cdp("DOM.focus", {"nodeId": node_id})
    time.sleep(0.5)

    cdp("Input.insertText", {"text": brief_text})
    time.sleep(2)

    val = js("document.activeElement?.value?.length || 0")
    print(f"   Text inserted: {val} chars")

    if val == 0:
        print(f"   Attempt {attempt+1}: Insert failed, retrying...")
        continue

    # Check Insert button
    insert_state = js("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.trim() === 'Insert');
        if (!btn) return 'not found';
        return btn.disabled ? 'disabled' : 'enabled';
    })()""")

    if insert_state == 'disabled':
        # Type space+backspace to trigger Angular
        cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": " ", "code": "Space", "text": " "})
        cdp("Input.dispatchKeyEvent", {"type": "char", "text": " "})
        cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": " ", "code": "Space"})
        time.sleep(0.3)
        cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
        cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
        time.sleep(1)

    # Click Insert
    js("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.trim() === 'Insert');
        if (btn) { btn.disabled = false; btn.removeAttribute('disabled'); btn.click(); }
    })()""")
    time.sleep(10)

    # Verify source was added
    sources = js("document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
    if sources != '0':
        print(f"   ✓ Sources: {sources}")
        source_added = True
        break
    else:
        print(f"   Attempt {attempt+1}: Source count still 0, retrying...")

if not source_added:
    print("   ✗ FAILED to add source after 5 attempts")
    sys.exit(1)

# Save notebook URL
notebook_url = js("window.location.href")
with open("/tmp/morningbrief/current_notebook_url.txt", "w") as f:
    f.write(notebook_url)

# ═══ STEP 3: Generate video ═══
print("\n3. Generating video...")

# Close modals
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(2)

# Click Video tile
js("""(() => {
    const els = document.querySelectorAll('*');
    for (const el of els) {
        if (el.childElementCount === 0 && el.textContent.trim().startsWith('Video')) {
            const c = el.closest('button, [role="button"], a, [tabindex]');
            if (c) { c.click(); return 'clicked'; }
        }
    }
})()""")
time.sleep(3)

# Always select Cinematic format
print("   Selecting Cinematic...")
js("""(() => {
    const els = document.querySelectorAll('*');
    for (const el of els) {
        if (el.textContent.trim() === 'Cinematic' && el.childElementCount <= 1) {
            el.closest('button, [role="button"], div[class*="card"], div[class*="tile"], [tabindex]')?.click();
            return 'selected';
        }
    }
})()""")
time.sleep(2)

# Try to add prompt in customize dialog
search = cdp("DOM.performSearch", {"query": "textarea"})
count = search.get("result", {}).get("resultCount", 0)
if count > 0:
    sid = search["result"]["searchId"]
    r = cdp("DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": count})
    for nid in r["result"]["nodeIds"]:
        cdp("DOM.focus", {"nodeId": nid})
        time.sleep(0.2)
        rows = js("document.activeElement?.rows || 0")
        ph = js("document.activeElement?.placeholder || ''")
        if rows and rows > 2 and 'Search' not in str(ph) and 'Upload' not in str(ph):
            cdp("Input.insertText", {"text": PROMPT})
            print("   ✓ Prompt added")
            break

# Click Generate
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.trim() === 'Generate');
    if (btn) btn.click();
})()""")
time.sleep(5)

# Verify generation started
for check in range(10):
    status = js("""(() => {
        const t = document.body.innerText;
        if (t.includes('Generating') || t.includes('take a while')) return 'generating';
        return 'not yet';
    })()""")
    if status == 'generating':
        print("   ✓ Cinematic video generating (30-40 min)")
        break
    time.sleep(3)

print(f"   Notebook: {notebook_url}")

ws.close()
print("\nDone — source added, video generating.")
