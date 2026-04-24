#!/usr/bin/env python3
"""Generate video with specific ExVenture prompt."""

import sys, json, base64, urllib.request, time
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

EXVENTURE_PROMPT = """Generate a cinematic animated AI news video for YouTube. Feature a dynamic, consistent AI news anchor character presenting. Emulate the visual style and energetic pacing of a modern, engaging news show like 'Logo!', but with a sophisticated, professional AI theme suitable for a global tech audience. Incorporate fast-paced transitions, high-quality animated on-screen graphics, and an overall fun yet deeply informative tone. The video should feel cutting-edge, professional, and visually captivating."""
CDP = "http://127.0.0.1:9222"

resp = urllib.request.urlopen(f"{CDP}/json")
tabs = json.loads(resp.read())
nlm_tab = [t for t in tabs if "notebooklm.google.com/notebook" in t.get("url", "")][0]
ws = websocket.create_connection(nlm_tab["webSocketDebuggerUrl"])
mid = 0

def cdp(method, params=None):
    global mid; mid += 1
    ws.send(json.dumps({"id":mid,"method":method,"params":params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid: return r

def js(e):
    r = cdp("Runtime.evaluate",{"expression":e,"returnByValue":True,"awaitPromise":True})
    return r.get("result",{}).get("result",{}).get("value")

def ss(n):
    r = cdp("Page.captureScreenshot",{"format":"png"})
    d = r.get("result",{}).get("data","")
    if d:
        with open(n,"wb") as f: f.write(base64.b64decode(d))

cdp("Runtime.enable")
cdp("Page.enable")

# Close any modal
cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
time.sleep(2)

print(f"URL: {js('window.location.href')}")

# Click Video in Studio panel
print("\n--- Clicking Video tile ---")
js("""(() => {
    const allEls = document.querySelectorAll('*');
    for (const el of allEls) {
        if (el.childElementCount === 0 && el.textContent.trim().startsWith('Video')) {
            const clickable = el.closest('button, [role="button"], a, [tabindex]');
            if (clickable) { clickable.click(); return 'clicked'; }
        }
    }
})()""")
time.sleep(3)
ss("/tmp/morningbrief/g_video_dialog.png")

# The Customize Video dialog should appear. Find the prompt textarea and fill it.
print("--- Filling prompt textarea ---")

# Find textarea in the customize dialog
import json as j
result = cdp("DOM.performSearch", {"query": "mat-dialog-container textarea, .cdk-overlay-pane textarea"})
count = result.get("result", {}).get("resultCount", 0)
print(f"  Textareas in dialog: {count}")

if count > 0:
    sid = result["result"]["searchId"]
    r2 = cdp("DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": count})
    nodes = r2.get("result", {}).get("nodeIds", [])

    # Focus the last textarea (should be the prompt one - the "How would you like it customized")
    for node_id in nodes:
        # Focus and get info about this textarea
        cdp("DOM.focus", {"nodeId": node_id})
        time.sleep(0.3)

        # Check what this textarea is
        active = js("""(() => {
            const el = document.activeElement;
            if (!el) return 'none';
            return JSON.stringify({
                placeholder: el.placeholder,
                name: el.name || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                parent: el.parentElement?.textContent?.substring(0, 100) || ''
            });
        })()""")
        print(f"  Active textarea: {active}")

        # If this is the prompt textarea (placeholder about "customization" or "Things to try")
        info = json.loads(active) if active and active.startswith('{') else {}
        placeholder = info.get('placeholder', '')
        if 'customiz' in placeholder.lower() or 'try' in placeholder.lower() or 'how' in placeholder.lower() or 'things' in placeholder.lower():
            # Insert the ExVenture prompt
            cdp("Input.insertText", {"text": EXVENTURE_PROMPT})
            time.sleep(1)
            val = js("""(() => {
                const el = document.activeElement;
                return el ? el.value?.length || 0 : 0;
            })()""")
            print(f"  ✓ Inserted prompt ({val} chars)")
            break
    else:
        # If no specific match, use the last textarea
        cdp("DOM.focus", {"nodeId": nodes[-1]})
        time.sleep(0.3)
        cdp("Input.insertText", {"text": EXVENTURE_PROMPT})
        time.sleep(1)

ss("/tmp/morningbrief/g_prompt_filled.png")

# Click Generate button
print("\n--- Clicking Generate ---")
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.trim() === 'Generate');
    if (btn) { btn.click(); return 'clicked'; }
    return 'not found';
})()""")
time.sleep(3)
ss("/tmp/morningbrief/g_generating.png")

print("✓ Video generation started with ExVenture prompt")
print(f"Notebook URL: {js('window.location.href')}")

ws.close()
