#!/usr/bin/env python3
"""Download NotebookLM video via CDP download + Slack upload v2."""

import sys, json, base64, urllib.request, time, os, subprocess, glob
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = "C074JDBNJD9"
CDP = "http://127.0.0.1:9222"
DOWNLOAD_DIR = "/tmp/morningbrief/downloads"
VIDEO_PATH = "/tmp/morningbrief/morningbrief_video.mp4"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
# Clear old downloads
for f in glob.glob(f"{DOWNLOAD_DIR}/*"):
    os.unlink(f)

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

def ss(name):
    r = cdp("Page.captureScreenshot", {"format": "png"})
    d = r.get("result", {}).get("data", "")
    if d:
        with open(name, "wb") as f: f.write(base64.b64decode(d))

cdp("Runtime.enable")
cdp("Page.enable")
cdp("Network.enable")

# Set download behavior to allow downloads to a specific directory
cdp("Browser.setDownloadBehavior", {
    "behavior": "allow",
    "downloadPath": DOWNLOAD_DIR,
})
print(f"✓ Downloads will go to: {DOWNLOAD_DIR}")

# Get the video URL
video_url = js("""(() => {
    const video = document.querySelector('video');
    if (video && video.src) return video.src;
    return '';
})()""")

if not video_url:
    # Click play
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

print(f"Video URL: {video_url[:120] if video_url else 'none'}")

# Trigger download via creating a download link in the page
print("\nTriggering download via page...")
js(f"""(() => {{
    const video = document.querySelector('video');
    if (video && video.src) {{
        const a = document.createElement('a');
        a.href = video.src;
        a.download = 'morningbrief_video.mp4';
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        return 'download triggered';
    }}
    return 'no video';
}})()""")

# Also try the three-dot menu download
time.sleep(2)
ss("/tmp/morningbrief/dl_state.png")

# Check for three-dot menu near the video player
js("""(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    // Find more_vert or three-dot button near video area
    for (const btn of btns) {
        const label = btn.getAttribute('aria-label') || '';
        const text = btn.textContent.trim();
        if (text === 'more_vert' || label.includes('More options') || label.includes('More actions')) {
            btn.click();
            return 'clicked more: ' + label;
        }
    }
    return 'no more button';
})()""")
time.sleep(1)

# Click Download in menu
dl_result = js("""(() => {
    const items = document.querySelectorAll('[role="menuitem"], [role="option"], button, a');
    for (const item of items) {
        const text = item.textContent.trim();
        if (text.includes('Download')) {
            item.click();
            return 'clicked download: ' + text;
        }
    }
    return 'no download option';
})()""")
print(f"  {dl_result}")

# Wait for download
print("  Waiting for download...")
for i in range(30):
    time.sleep(2)
    files = os.listdir(DOWNLOAD_DIR)
    if files:
        # Filter out .crdownload (partial downloads)
        complete = [f for f in files if not f.endswith('.crdownload')]
        if complete:
            dl_file = os.path.join(DOWNLOAD_DIR, complete[0])
            size = os.path.getsize(dl_file)
            print(f"  ✓ Downloaded: {complete[0]} ({size / 1024 / 1024:.1f} MB)")
            # Move to expected path
            os.rename(dl_file, VIDEO_PATH)
            break
        else:
            print(f"  Downloading... ({[f for f in files]})")
    if i == 15:
        print("  Still waiting...")

# Check result
if os.path.exists(VIDEO_PATH):
    file_type = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout.strip()
    size_mb = os.path.getsize(VIDEO_PATH) / 1024 / 1024
    print(f"\nFile: {file_type}")
    print(f"Size: {size_mb:.1f} MB")

    if 'video' in file_type.lower() or 'ISO Media' in file_type or size_mb > 1:
        if SLACK_TOKEN:
            print(f"\nUploading to Slack #ai-updates...")

            # Use new Slack files.completeUploadExternal API flow
            # Step 1: Get upload URL
            result = subprocess.run([
                "curl", "-s",
                "-F", f"length={os.path.getsize(VIDEO_PATH)}",
                "-F", "filename=AI_Morning_Brief_April_14_2026.mp4",
                "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                "https://slack.com/api/files.getUploadURLExternal"
            ], capture_output=True, text=True)
            upload_data = json.loads(result.stdout) if result.stdout else {}
            print(f"  Upload URL response: ok={upload_data.get('ok')}")

            if upload_data.get('ok'):
                upload_url = upload_data['upload_url']
                file_id = upload_data['file_id']

                # Step 2: Upload file to the URL
                result = subprocess.run([
                    "curl", "-s",
                    "-F", f"file=@{VIDEO_PATH}",
                    upload_url
                ], capture_output=True, text=True)
                print(f"  Upload result: {result.stdout[:100]}")

                # Step 3: Complete upload
                complete_payload = json.dumps({
                    "files": [{"id": file_id, "title": "AI Morning Brief - April 14, 2026"}],
                    "channel_id": SLACK_CHANNEL,
                    "initial_comment": ":tv: *AI Morning Brief — Video Edition*\n*Monday, April 14, 2026*\n\n:rotating_light: Your daily AI intelligence briefing — watch the video summary!"
                })
                result = subprocess.run([
                    "curl", "-s",
                    "-X", "POST",
                    "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                    "-H", "Content-Type: application/json",
                    "-d", complete_payload,
                    "https://slack.com/api/files.completeUploadExternal"
                ], capture_output=True, text=True)
                complete_data = json.loads(result.stdout) if result.stdout else {}
                if complete_data.get('ok'):
                    print(f"  ✓ Video uploaded to Slack #ai-updates!")
                else:
                    print(f"  ✗ Complete failed: {complete_data.get('error', result.stdout[:200])}")
            else:
                print(f"  ✗ Upload URL failed: {upload_data.get('error', '')}")
    else:
        print(f"  ✗ Not a video file")
else:
    print("\n  No video downloaded")

ws.close()
print("\nDone.")
