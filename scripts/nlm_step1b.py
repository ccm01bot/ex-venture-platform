#!/usr/bin/env python3
"""Step 1: Add source - fix: target the MODAL textarea, not the search box."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import json, time, base64, urllib.request, websocket, os, datetime
today = datetime.date.today().strftime("%Y-%m-%d")
BRIEF_FILE = os.environ.get("BRIEF_FILE", f"/tmp/morningbrief/brief_{today}.md")
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
cdp("DOM.enable")

# Step 0: Go home, create notebook
print("Creating fresh notebook...")
js("window.location.href = 'https://notebooklm.google.com/'")
time.sleep(4)

js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.includes('Create new'));
    if (btn) btn.click();
})()""")
time.sleep(4)
ss("/tmp/morningbrief/b_created.png")

# Click Copied text in the modal
print("Clicking 'Copied text'...")
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent.includes('Copied text'));
    if (btn) btn.click();
})()""")
time.sleep(3)
ss("/tmp/morningbrief/b_paste_dialog.png")

# Find ALL textareas and identify which one is in the modal
print("Finding modal textarea...")
textarea_info = js("""(() => {
    const textareas = document.querySelectorAll('textarea');
    const info = [];
    for (const ta of textareas) {
        const overlay = ta.closest('.cdk-overlay-container, .cdk-overlay-pane, [role="dialog"], mat-dialog-container');
        info.push({
            placeholder: ta.placeholder,
            inOverlay: !!overlay,
            className: ta.className.substring(0, 100),
            parent: ta.parentElement?.className?.substring(0, 100) || '',
            id: ta.id || '',
            rows: ta.rows,
            visible: ta.offsetParent !== null,
        });
    }
    return JSON.stringify(info);
})()""")
print(f"  Textareas found: {textarea_info}")

# Focus the MODAL textarea specifically (the one with placeholder "Paste text here")
print("Focusing modal textarea...")
focused = js("""(() => {
    const textareas = document.querySelectorAll('textarea');
    for (const ta of textareas) {
        if (ta.placeholder && ta.placeholder.includes('Paste text here')) {
            // Remove all other focus
            document.activeElement?.blur();
            // Force focus on this specific textarea
            ta.focus({preventScroll: false});
            ta.click();
            // Dispatch focus event
            ta.dispatchEvent(new FocusEvent('focus', {bubbles: true}));
            ta.dispatchEvent(new FocusEvent('focusin', {bubbles: true}));
            return 'focused paste textarea';
        }
    }
    // Fallback: find textarea in overlay
    const overlay = document.querySelector('.cdk-overlay-container');
    if (overlay) {
        const ta = overlay.querySelector('textarea');
        if (ta) {
            document.activeElement?.blur();
            ta.focus();
            ta.click();
            return 'focused overlay textarea';
        }
    }
    return 'not found';
})()""")
print(f"  {focused}")
time.sleep(0.5)

# Verify focus
active = js("""(() => {
    const el = document.activeElement;
    return el ? el.tagName + ' | placeholder: ' + (el.placeholder || 'none') + ' | class: ' + el.className.substring(0,50) : 'nothing';
})()""")
print(f"  Active element: {active}")

# Now use DOM.focus via CDP for the specific node
print("Using CDP DOM.focus...")
doc = cdp("DOM.getDocument")
root_id = doc["result"]["root"]["nodeId"]

# Find textarea with placeholder "Paste text here"
search = cdp("DOM.performSearch", {"query": "textarea[placeholder*='Paste']"})
count = search.get("result", {}).get("resultCount", 0)
print(f"  DOM search results: {count}")

if count > 0:
    search_id = search["result"]["searchId"]
    results = cdp("DOM.getSearchResults", {"searchId": search_id, "fromIndex": 0, "toIndex": count})
    node_ids = results.get("result", {}).get("nodeIds", [])
    if node_ids:
        # Focus via CDP
        cdp("DOM.focus", {"nodeId": node_ids[0]})
        print(f"  ✓ CDP focused node {node_ids[0]}")
        time.sleep(0.5)

        # Now insertText should go to the right element
        print(f"Inserting text ({len(brief_text)} chars)...")
        cdp("Input.insertText", {"text": brief_text})
        time.sleep(2)

        # Verify
        val = js("""(() => {
            const textareas = document.querySelectorAll('textarea');
            for (const ta of textareas) {
                if (ta.placeholder?.includes('Paste')) return ta.value.length;
            }
            return 0;
        })()""")
        print(f"  Modal textarea length: {val}")

        ss("/tmp/morningbrief/b_text_filled.png")

        # Check Insert button state
        insert_state = js("""(() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => b.textContent.trim() === 'Insert');
            if (!btn) return 'not found';
            return btn.disabled ? 'disabled' : 'enabled';
        })()""")
        print(f"  Insert button: {insert_state}")

        if insert_state == 'enabled':
            print("Clicking Insert...")
            js("""(() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const btn = btns.find(b => b.textContent.trim() === 'Insert');
                if (btn) btn.click();
            })()""")
            time.sleep(10)
            sources = js("document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
            print(f"✓ Sources: {sources}")
        else:
            print("Insert still disabled. Trying to type a char to trigger validation...")
            # Type a space then backspace to trigger Angular change detection
            cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": " ", "code": "Space", "text": " "})
            cdp("Input.dispatchKeyEvent", {"type": "char", "text": " "})
            cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": " ", "code": "Space"})
            time.sleep(0.3)
            cdp("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
            cdp("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
            time.sleep(1)

            insert_state = js("""(() => {
                const btns = Array.from(document.querySelectorAll('button'));
                const btn = btns.find(b => b.textContent.trim() === 'Insert');
                return btn?.disabled ? 'disabled' : 'enabled';
            })()""")
            print(f"  Insert button after typing: {insert_state}")

            if insert_state == 'enabled':
                print("Clicking Insert...")
                js("""(() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const btn = btns.find(b => b.textContent.trim() === 'Insert');
                    if (btn) btn.click();
                })()""")
                time.sleep(10)
                sources = js("document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
                print(f"✓ Sources: {sources}")
            else:
                # Force enable and click
                print("Force-enabling Insert...")
                js("""(() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const btn = btns.find(b => b.textContent.trim() === 'Insert');
                    if (btn) { btn.disabled = false; btn.removeAttribute('disabled'); btn.click(); }
                })()""")
                time.sleep(10)
                sources = js("document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
                print(f"✓ Sources (after force): {sources}")

ss("/tmp/morningbrief/b_final.png")
notebook_url = js("window.location.href")
print(f"\nNotebook: {notebook_url}")

# Save notebook URL so subsequent scripts (generate_video_with_prompt, wait_download_post_final) use THIS specific notebook, not an old one
with open("/tmp/morningbrief/current_notebook_url.txt", "w") as f:
    f.write(notebook_url)
ws.close()
print("Done!")
