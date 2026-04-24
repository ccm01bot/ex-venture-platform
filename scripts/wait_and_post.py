#!/usr/bin/env python3
"""Poll NotebookLM until video is ready, then share and post to Slack."""

import sys, json, base64, urllib.request, time
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

SLACK_WEBHOOK = "SLACK_WEBHOOK_PLACEHOLDER"
CDP = "http://127.0.0.1:9222"

def get_ws():
    resp = urllib.request.urlopen(f"{CDP}/json")
    tabs = json.loads(resp.read())
    for tab in tabs:
        if "notebooklm.google.com/notebook" in tab.get("url", ""):
            return websocket.create_connection(tab["webSocketDebuggerUrl"]), tab["url"]
    return None, None

msg_id = 0
def cdp(ws, method, params=None):
    global msg_id
    msg_id += 1
    msg = {"id": msg_id, "method": method}
    if params: msg["params"] = params
    ws.send(json.dumps(msg))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == msg_id: return r

def js(ws, expr):
    r = cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    return r.get("result", {}).get("result", {}).get("value")

print("Waiting for NotebookLM video to finish generating...")
print("Polling every 30 seconds.\n")

for i in range(120):  # Up to 60 minutes
    try:
        ws, url = get_ws()
        if not ws:
            print(f"  [{i*30}s] No notebook tab found, retrying...")
            time.sleep(30)
            continue

        cdp(ws, "Runtime.enable")

        status = js(ws, """(() => {
            const text = document.body.innerText;
            if (text.includes('Generating Video') || text.includes('generating')) return 'generating';
            if (text.includes('Your video overview is ready')) return 'ready';
            // Check if video tile changed state
            const studio = text.substring(text.indexOf('Studio'), text.indexOf('Add note'));
            if (studio.includes('Play') || studio.includes('Download')) return 'ready';
            // Check for video element
            if (document.querySelector('video')) return 'ready';
            // Check if generating text is gone and video section exists
            if (!text.includes('Generating') && text.includes('Video Overview')) return 'maybe_ready';
            return 'unknown';
        })()""")

        print(f"  [{i*30}s] Status: {status}")

        if status in ('ready', 'maybe_ready'):
            print("\n✓ Video is ready!")

            # Share notebook
            js(ws, """(() => {
                const btns = document.querySelectorAll('button');
                for (const btn of btns) {
                    if ((btn.getAttribute('aria-label') || '').toLowerCase().includes('share')) {
                        btn.click(); return;
                    }
                }
            })()""")
            time.sleep(2)

            js(ws, """(() => {
                document.querySelectorAll('[role="switch"]').forEach(s => {
                    if (s.getAttribute('aria-checked') !== 'true') s.click();
                });
            })()""")
            time.sleep(1)

            # Close share dialog
            cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
            cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})

            notebook_url = url

            # Post to Slack
            slack_msg = (
                "*:tv: AI Morning Brief — Video Edition*\n"
                "*Monday, April 14, 2026*\n\n"
                ":rotating_light: Your daily AI intelligence briefing is ready as a video!\n\n"
                f":point_right: *Watch the full video briefing:* {notebook_url}\n\n"
                ":headphones: _Open the link → click 'Video Overview' in the Studio panel to watch._\n\n"
                "---\n"
                "_Compiled by ExVenture AI Research Team | Next brief: tomorrow 11:00am_"
            )

            data = json.dumps({"text": slack_msg}).encode()
            req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
            resp = urllib.request.urlopen(req)
            print(f"✓ Posted to Slack: {resp.read().decode()}")
            print(f"Notebook: {notebook_url}")

            ws.close()
            break

        ws.close()
    except Exception as e:
        print(f"  [{i*30}s] Error: {e}")

    time.sleep(30)
else:
    print("\n✗ Timed out after 60 minutes.")
