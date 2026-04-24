#!/usr/bin/env python3
"""Download video from NotebookLM via CDP fetch (uses browser's auth cookies)."""

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

# Get the video URL from the page
video_url = js("""(() => {
    const video = document.querySelector('video');
    if (video && video.src) return video.src;
    return '';
})()""")
print(f"Video URL: {video_url[:100] if video_url else 'none'}")

if not video_url:
    # Click play to load video
    js("""(() => {
        const play = document.querySelector('[aria-label*="Play"], button[aria-label*="play"]');
        if (play) play.click();
    })()""")
    time.sleep(3)
    video_url = js("""(() => {
        const video = document.querySelector('video');
        if (video && video.src) return video.src;
        return '';
    })()""")
    print(f"Video URL after play: {video_url[:100] if video_url else 'none'}")

if video_url:
    # Download via browser's fetch (uses auth cookies)
    print("\nDownloading video via browser fetch...")
    b64_data = js("""(async () => {
        const video = document.querySelector('video');
        const url = video ? video.src : '';
        if (!url) return '';
        try {
            const resp = await fetch(url, {credentials: 'include'});
            const blob = await resp.blob();
            const type = blob.type;
            const size = blob.size;
            console.log('Blob type:', type, 'size:', size);
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => {
                    const base64 = reader.result.split(',')[1];
                    resolve(JSON.stringify({data: base64, type: type, size: size}));
                };
                reader.onerror = () => reject('reader error');
                reader.readAsDataURL(blob);
            });
        } catch(e) {
            return JSON.stringify({error: e.message});
        }
    })()""")

    if b64_data:
        info = json.loads(b64_data)
        if 'error' in info:
            print(f"  ✗ Fetch error: {info['error']}")
        elif info.get('data'):
            video_bytes = base64.b64decode(info['data'])
            with open(VIDEO_PATH, 'wb') as f:
                f.write(video_bytes)
            size_mb = len(video_bytes) / 1024 / 1024
            print(f"  ✓ Downloaded: {size_mb:.1f} MB (type: {info.get('type', 'unknown')})")

            # Verify it's a real video
            file_type = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout
            print(f"  File type: {file_type.strip()}")

            if 'video' in file_type.lower() or 'mp4' in file_type.lower() or 'ISO Media' in file_type:
                # Upload to Slack
                if SLACK_TOKEN:
                    print(f"\nUploading to Slack #ai-updates...")
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
                        print(f"  Link: {resp_data.get('file', {}).get('permalink', '')}")
                    else:
                        error = resp_data.get('error', '')
                        print(f"  ✗ Slack error: {error}")
                        if error == 'missing_scope':
                            print("  Token needs 'files:write' scope. Go to api.slack.com/apps → your app → OAuth → add files:write")
                else:
                    print(f"\n  Video saved to {VIDEO_PATH}")
                    print("  Set SLACK_BOT_TOKEN to upload automatically")
            else:
                print(f"  ✗ Downloaded file is not a video: {file_type}")
        else:
            print("  ✗ No data in response")
    else:
        print("  ✗ No response from fetch")

ws.close()
print("\nDone.")
