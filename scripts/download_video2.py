#!/usr/bin/env python3
"""Download NotebookLM video by intercepting network requests via CDP."""

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

cdp("Runtime.enable")
cdp("Page.enable")

# Approach: Use CDP to get all cookies, then download video with cookies via urllib
print("Getting browser cookies...")

# Get cookies via Network domain
cdp("Network.enable")
cookie_result = cdp("Network.getAllCookies")
all_cookies = cookie_result.get("result", {}).get("cookies", [])

# Filter for google cookies
google_cookies = [c for c in all_cookies if 'google' in c.get('domain', '')]
print(f"  Found {len(google_cookies)} Google cookies")

# Build cookie header
cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in google_cookies])

# Get the video URL
video_url = js("""(() => {
    const video = document.querySelector('video');
    if (video && video.src) return video.src;
    return '';
})()""")
print(f"Video URL: {video_url[:120] if video_url else 'none'}")

if video_url:
    print("\nDownloading with cookies...")
    req = urllib.request.Request(video_url)
    req.add_header('Cookie', cookie_str)
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    req.add_header('Referer', 'https://notebooklm.google.com/')

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        content_type = resp.headers.get('Content-Type', '')
        data = resp.read()
        print(f"  Content-Type: {content_type}")
        print(f"  Size: {len(data) / 1024 / 1024:.1f} MB")

        with open(VIDEO_PATH, 'wb') as f:
            f.write(data)

        file_type = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout.strip()
        print(f"  File type: {file_type}")

        if 'video' in content_type.lower() or 'mp4' in content_type.lower() or 'ISO Media' in file_type or 'video' in file_type.lower():
            print("  ✓ Real video file!")

            if SLACK_TOKEN:
                print(f"\nUploading to Slack...")
                result = subprocess.run([
                    "curl", "-s",
                    "-F", f"file=@{VIDEO_PATH}",
                    "-F", f"channels={SLACK_CHANNEL}",
                    "-F", "initial_comment=:tv: *AI Morning Brief — Video Edition*\n*Monday, April 14, 2026*\n\n:rotating_light: Your daily AI intelligence briefing — watch the video summary!",
                    "-F", "title=AI Morning Brief - April 14 2026",
                    "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                    "https://slack.com/api/files.upload"
                ], capture_output=True, text=True)

                resp_data = json.loads(result.stdout) if result.stdout else {}
                if resp_data.get("ok"):
                    print(f"  ✓ Uploaded to Slack!")
                else:
                    error = resp_data.get('error', '')
                    print(f"  ✗ Slack error: {error}")
                    if error == 'missing_scope':
                        print("\n  Your token needs 'files:write' scope.")
                        print("  Go to: https://api.slack.com/apps")
                        print("  → Your app → OAuth & Permissions → Scopes → Add 'files:write'")
                        print("  → Reinstall app → Copy new token")
                        print(f"\n  Video saved at: {VIDEO_PATH}")
        else:
            print(f"  ✗ Not a video file. First 200 bytes: {data[:200]}")

    except Exception as e:
        print(f"  ✗ Download error: {e}")

ws.close()
print("\nDone.")
