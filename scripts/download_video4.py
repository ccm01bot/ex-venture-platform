#!/usr/bin/env python3
"""Download video by reloading it and capturing network response via CDP."""

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

# Use Fetch domain to intercept video request
cdp("Fetch.enable", {
    "patterns": [
        {"urlPattern": "*lh3.googleusercontent.com*", "requestStage": "Response"},
        {"urlPattern": "*video*mp4*", "requestStage": "Response"},
        {"urlPattern": "*.mp4*", "requestStage": "Response"},
    ]
})

print("Fetch interception enabled")

# Get video URL
video_url = js("""(() => {
    const video = document.querySelector('video');
    return video ? video.src : '';
})()""")
print(f"Video URL: {video_url[:120] if video_url else 'none'}")

# Try XMLHttpRequest with auth (runs in page context with cookies)
print("\nTrying XMLHttpRequest download...")
b64_result = js(f"""(async () => {{
    return new Promise((resolve, reject) => {{
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '{video_url}', true);
        xhr.responseType = 'arraybuffer';
        xhr.withCredentials = true;
        xhr.onload = function() {{
            if (xhr.status === 200) {{
                const bytes = new Uint8Array(xhr.response);
                let binary = '';
                const chunkSize = 8192;
                for (let i = 0; i < bytes.length; i += chunkSize) {{
                    const chunk = bytes.subarray(i, Math.min(i + chunkSize, bytes.length));
                    binary += String.fromCharCode.apply(null, chunk);
                }}
                resolve(JSON.stringify({{
                    ok: true,
                    size: bytes.length,
                    type: xhr.getResponseHeader('Content-Type'),
                    data: btoa(binary)
                }}));
            }} else {{
                resolve(JSON.stringify({{ok: false, status: xhr.status, statusText: xhr.statusText}}));
            }}
        }};
        xhr.onerror = function() {{
            resolve(JSON.stringify({{ok: false, error: 'network error'}}));
        }};
        xhr.send();
    }});
}})()""")

if b64_result:
    result = json.loads(b64_result)
    if result.get('ok'):
        data = base64.b64decode(result['data'])
        print(f"  ✓ Downloaded via XHR: {len(data)/1024/1024:.1f} MB (type: {result.get('type')})")
        with open(VIDEO_PATH, 'wb') as f:
            f.write(data)

        file_type = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout.strip()
        print(f"  File: {file_type}")

        if SLACK_TOKEN and ('video' in file_type.lower() or 'ISO Media' in file_type or len(data) > 100000):
            print(f"\nUploading to Slack...")
            # files.getUploadURLExternal
            r = subprocess.run([
                "curl", "-s",
                "-F", f"length={len(data)}",
                "-F", "filename=AI_Morning_Brief_April_14_2026.mp4",
                "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                "https://slack.com/api/files.getUploadURLExternal"
            ], capture_output=True, text=True)
            upload_info = json.loads(r.stdout) if r.stdout else {}
            print(f"  getUploadURL: {upload_info.get('ok')} / {upload_info.get('error','')}")

            if upload_info.get('ok'):
                # Upload file
                r = subprocess.run([
                    "curl", "-s",
                    "-X", "POST",
                    "-F", f"file=@{VIDEO_PATH}",
                    upload_info['upload_url']
                ], capture_output=True, text=True)
                print(f"  Upload: {r.stdout[:100] if r.stdout else 'ok'}")

                # Complete
                payload = json.dumps({
                    "files": [{"id": upload_info['file_id'], "title": "AI Morning Brief - April 14, 2026"}],
                    "channel_id": SLACK_CHANNEL,
                    "initial_comment": ":tv: *AI Morning Brief — Video Edition*\n*Monday, April 14, 2026*\n\n:rotating_light: Your daily AI intelligence briefing — watch the video!"
                })
                r = subprocess.run([
                    "curl", "-s", "-X", "POST",
                    "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                    "-H", "Content-Type: application/json",
                    "-d", payload,
                    "https://slack.com/api/files.completeUploadExternal"
                ], capture_output=True, text=True)
                complete = json.loads(r.stdout) if r.stdout else {}
                if complete.get('ok'):
                    print(f"  ✓ Video uploaded to Slack #ai-updates!")
                else:
                    print(f"  ✗ Complete error: {complete.get('error','')}")
                    print(f"    Response: {r.stdout[:300]}")
            else:
                print(f"  Need to add 'files:write' scope to bot token at api.slack.com/apps")
    else:
        print(f"  ✗ XHR failed: {result}")

cdp("Fetch.disable")
ws.close()
print("\nDone.")
