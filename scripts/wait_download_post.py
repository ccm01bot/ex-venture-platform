#!/usr/bin/env python3
"""Poll NotebookLM until video is ready, download MP4, upload to Slack."""

import sys, json, base64, urllib.request, time, os, re
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')
import websocket

SLACK_WEBHOOK = "SLACK_WEBHOOK_PLACEHOLDER"
SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = "C074JDBNJD9"  # #ai-updates
CDP = "http://127.0.0.1:9222"
VIDEO_PATH = "/tmp/morningbrief/morningbrief_video.mp4"

msg_id = 0

def get_ws():
    resp = urllib.request.urlopen(f"{CDP}/json")
    tabs = json.loads(resp.read())
    for tab in tabs:
        if "notebooklm.google.com/notebook" in tab.get("url", ""):
            return websocket.create_connection(tab["webSocketDebuggerUrl"]), tab["url"]
    return None, None

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

print("=== Waiting for video, then download & upload to Slack ===\n")

# Poll until video is ready
for i in range(120):
    try:
        ws, url = get_ws()
        if not ws:
            time.sleep(30); continue

        cdp(ws, "Runtime.enable")

        status = js(ws, """(() => {
            const text = document.body.innerText;
            if (text.includes('Generating Video') || text.includes('generating')) return 'generating';
            if (document.querySelector('video')) return 'ready';
            if (!text.includes('Generating') && !text.includes('generating')) return 'maybe_ready';
            return 'unknown';
        })()""")

        print(f"  [{i*30}s] Status: {status}")

        if status in ('ready', 'maybe_ready'):
            # Click on Video Overview to open it
            js(ws, """(() => {
                const allEls = document.querySelectorAll('*');
                for (const el of allEls) {
                    if (el.childElementCount === 0 && el.textContent.trim().startsWith('Video Overview')) {
                        const clickable = el.closest('button, [role="button"], a, div[tabindex]');
                        if (clickable) { clickable.click(); return 'clicked'; }
                        el.click(); return 'clicked text';
                    }
                }
                // Try the Video tile
                for (const el of allEls) {
                    if (el.childElementCount === 0 && el.textContent.trim().match(/^Video/)) {
                        const clickable = el.closest('button, [role="button"], a, div[tabindex]');
                        if (clickable) { clickable.click(); return 'clicked video'; }
                    }
                }
                return 'not found';
            })()""")
            time.sleep(3)

            # Try to find video URL
            video_url = js(ws, """(() => {
                // Check for video element
                const video = document.querySelector('video');
                if (video && video.src) return video.src;
                if (video) {
                    const source = video.querySelector('source');
                    if (source) return source.src;
                }
                // Check for download link
                const links = document.querySelectorAll('a[href*="video"], a[download]');
                for (const a of links) {
                    if (a.href) return a.href;
                }
                // Check for blob URLs in network
                return '';
            })()""")

            print(f"  Video URL: {video_url[:100] if video_url else 'not found'}")

            if not video_url:
                # Try clicking a download/three-dot menu
                js(ws, """(() => {
                    // Look for download button or menu
                    const btns = Array.from(document.querySelectorAll('button'));
                    const dl = btns.find(b => b.textContent.includes('Download') ||
                                                (b.getAttribute('aria-label') || '').includes('Download') ||
                                                (b.getAttribute('aria-label') || '').includes('download'));
                    if (dl) { dl.click(); return 'clicked download'; }

                    // Try more menu / three dots
                    const more = btns.find(b => (b.getAttribute('aria-label') || '').includes('More') ||
                                                 b.textContent.trim() === 'more_vert');
                    if (more) { more.click(); return 'clicked more'; }
                    return 'no download found';
                })()""")
                time.sleep(2)

                # Check for download option in menu
                js(ws, """(() => {
                    const items = document.querySelectorAll('[role="menuitem"], button, a');
                    for (const item of items) {
                        if (item.textContent.includes('Download')) {
                            item.click();
                            return 'clicked download menu item';
                        }
                    }
                    return 'no menu item';
                })()""")
                time.sleep(3)

                # Re-check for video URL
                video_url = js(ws, """(() => {
                    const video = document.querySelector('video');
                    if (video && video.src) return video.src;
                    if (video) {
                        const source = video.querySelector('source');
                        if (source) return source.src;
                    }
                    return '';
                })()""")

            if video_url and video_url.startswith('http'):
                # Download the video
                print(f"\n  Downloading video...")
                req = urllib.request.Request(video_url)
                resp = urllib.request.urlopen(req)
                with open(VIDEO_PATH, 'wb') as f:
                    f.write(resp.read())
                size = os.path.getsize(VIDEO_PATH)
                print(f"  ✓ Downloaded: {VIDEO_PATH} ({size / 1024 / 1024:.1f} MB)")

            elif video_url and video_url.startswith('blob:'):
                # Blob URL - need to fetch via page context
                print(f"\n  Video is a blob URL, fetching via page...")
                b64_data = js(ws, """(async () => {
                    const video = document.querySelector('video');
                    if (!video || !video.src) return '';
                    const resp = await fetch(video.src);
                    const blob = await resp.blob();
                    return new Promise(resolve => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result.split(',')[1]);
                        reader.readAsDataURL(blob);
                    });
                })()""")
                if b64_data:
                    with open(VIDEO_PATH, 'wb') as f:
                        f.write(base64.b64decode(b64_data))
                    size = os.path.getsize(VIDEO_PATH)
                    print(f"  ✓ Downloaded blob: {VIDEO_PATH} ({size / 1024 / 1024:.1f} MB)")
                else:
                    print("  ✗ Could not fetch blob video")
            else:
                print("  ✗ No video URL found. Video may not be ready yet.")
                # Take screenshot for debug
                sr = cdp(ws, "Page.captureScreenshot", {"format": "png"})
                d = sr.get("result", {}).get("data", "")
                if d:
                    with open("/tmp/morningbrief/debug_video_status.png", "wb") as f:
                        f.write(base64.b64decode(d))
                    print("  Screenshot saved to /tmp/morningbrief/debug_video_status.png")

                ws.close()
                time.sleep(30)
                continue

            ws.close()

            # Upload to Slack
            if os.path.exists(VIDEO_PATH) and os.path.getsize(VIDEO_PATH) > 0:
                print(f"\n  Uploading to Slack #{SLACK_CHANNEL}...")

                if SLACK_TOKEN:
                    # Use Slack API files.upload
                    import subprocess
                    result = subprocess.run([
                        "curl", "-s",
                        "-F", f"file=@{VIDEO_PATH}",
                        "-F", f"channels={SLACK_CHANNEL}",
                        "-F", "initial_comment=:tv: *AI Morning Brief — Video Edition*\n*Monday, April 14, 2026*\n\n:rotating_light: Your daily AI intelligence briefing — watch the video!",
                        "-F", "title=Morning Brief - April 14, 2026",
                        "-H", f"Authorization: Bearer {SLACK_TOKEN}",
                        "https://slack.com/api/files.upload"
                    ], capture_output=True, text=True)
                    print(f"  Slack API response: {result.stdout[:200]}")
                else:
                    print("  No SLACK_BOT_TOKEN set. Saving video path for manual upload.")
                    print(f"  Video file: {VIDEO_PATH}")
                    # Post link via webhook as fallback
                    slack_msg = (
                        "*:tv: AI Morning Brief — Video Edition*\n"
                        "*Monday, April 14, 2026*\n\n"
                        ":rotating_light: Your daily AI intelligence briefing video has been generated!\n\n"
                        f":point_right: *Watch in NotebookLM:* {url}\n\n"
                        "_Video file saved locally. Upload manually or set SLACK_BOT_TOKEN for auto-upload._\n\n"
                        "---\n"
                        "_Compiled by ExVenture AI Research Team | Next brief: tomorrow 11:00am_"
                    )
                    data = json.dumps({"text": slack_msg}).encode()
                    req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
                    resp = urllib.request.urlopen(req)
                    print(f"  ✓ Posted link to Slack: {resp.read().decode()}")

            print(f"\n=== Done! ===")
            break

        ws.close()
    except Exception as e:
        print(f"  [{i*30}s] Error: {e}")

    time.sleep(30)
