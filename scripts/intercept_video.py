#!/usr/bin/env python3
"""Click play, intercept the video network request, download the response."""

import sys, json, base64, urllib.request, time, os, subprocess, threading
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

def cdp_send(method, params=None):
    global msg_id; msg_id += 1
    msg = {"id": msg_id, "method": method}
    if params: msg["params"] = params
    ws.send(json.dumps(msg))
    return msg_id

def cdp_recv(expected_id=None):
    while True:
        r = json.loads(ws.recv())
        if expected_id and r.get("id") == expected_id:
            return r
        if not expected_id:
            return r

def cdp(method, params=None):
    mid = cdp_send(method, params)
    return cdp_recv(mid)

def js(expr):
    r = cdp("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
    return r.get("result", {}).get("result", {}).get("value")

cdp("Runtime.enable")
cdp("Page.enable")
cdp("Network.enable")

print("✓ Connected")

# Enable Network request interception to capture video URLs
video_requests = []

# Click the play button on the video player
print("\nClicking play button...")
js("""(() => {
    // Find the play button in the video player area
    const btns = Array.from(document.querySelectorAll('button'));
    for (const btn of btns) {
        const label = btn.getAttribute('aria-label') || '';
        if (label.includes('Play') || label.includes('play')) {
            btn.click();
            return 'clicked: ' + label;
        }
    }
    // Try clicking the video element directly
    const v = document.querySelector('video');
    if (v) { v.play(); return 'played video element'; }
    return 'not found';
})()""")

# Wait and collect network requests
print("Monitoring network requests for video...")
time.sleep(3)

# Get all network request URLs from performance API
urls = js("""(() => {
    const entries = performance.getEntriesByType('resource');
    return entries
        .filter(e => e.name.includes('video') || e.name.includes('mp4') ||
                     e.name.includes('lh3.google') || e.name.includes('media'))
        .map(e => e.name)
        .join('\\n');
})()""")
print(f"  Resource URLs:\n  {urls}")

# Check the video element state
video_state = js("""(() => {
    const v = document.querySelector('video');
    if (!v) return 'no video';
    return JSON.stringify({
        src: v.src,
        currentSrc: v.currentSrc,
        readyState: v.readyState,
        networkState: v.networkState,
        error: v.error ? {code: v.error.code, message: v.error.message} : null,
        paused: v.paused,
        hidden: v.hidden,
    });
})()""")
print(f"\n  Video state: {video_state}")

# If the video is hidden, make it visible and try playing
js("""(() => {
    const v = document.querySelector('video');
    if (v) {
        v.hidden = false;
        v.style.display = 'block';
        v.play().catch(e => console.log('play error:', e));
    }
})()""")
time.sleep(5)

video_state2 = js("""(() => {
    const v = document.querySelector('video');
    if (!v) return 'no video';
    return JSON.stringify({
        src: v.src,
        readyState: v.readyState,
        networkState: v.networkState,
        duration: v.duration,
        error: v.error ? {code: v.error.code, message: v.error.message} : null,
    });
})()""")
print(f"  After unhide+play: {video_state2}")

# If error, the video URL might need to be refreshed
# Let's try a different approach - use the NotebookLM internal API to get the video URL
print("\n--- Trying NotebookLM internal API ---")
# NotebookLM stores artifact data internally - try to access it
artifact_data = js("""(() => {
    // Look for any Angular service/store data about artifacts
    // Try accessing __zone_symbol__value or similar
    const scripts = document.querySelectorAll('script');

    // Check for data attributes
    const allData = [];
    document.querySelectorAll('[data-video-url], [data-artifact-id], [data-src]').forEach(el => {
        allData.push({tag: el.tagName, attrs: Object.fromEntries([...el.attributes].map(a => [a.name, a.value.substring(0, 100)]))});
    });

    return JSON.stringify(allData);
})()""")
print(f"  Data attributes: {artifact_data}")

# Try to find the video download URL from the page's internal state
download_url = js("""(() => {
    // Look for download links or video URLs in the page
    const all = document.querySelectorAll('a[href*="download"], a[href*="video"], a[download]');
    for (const a of all) return a.href;

    // Check meta tags
    const metas = document.querySelectorAll('meta[content*="video"], meta[content*="mp4"]');
    for (const m of metas) return m.content;

    // Look through all network entries for video content type
    const perf = performance.getEntriesByType('resource');
    for (const p of perf) {
        if (p.name.includes('lh3.google') && !p.name.includes('thumbnail')) {
            return p.name;
        }
    }

    return '';
})()""")
print(f"  Download URL: {download_url[:150] if download_url else 'none'}")

# Let's try getting cookies and using curl with -L to follow redirects
cookies_result = cdp("Network.getAllCookies")
cookies = cookies_result.get("result", {}).get("cookies", [])
cookie_jar = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

video_src = js("document.querySelector('video')?.src || ''")
if video_src:
    print(f"\nDownloading {video_src[:80]}... with {len(cookies)} cookies")
    # Use curl with all cookies, follow redirects, and accept video
    result = subprocess.run([
        "curl", "-v", "-L", "-o", VIDEO_PATH,
        "--max-time", "60",
        "-H", f"Cookie: {cookie_jar}",
        "-H", "Accept: video/mp4,video/webm,video/*,*/*",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "-H", "Referer: https://notebooklm.google.com/",
        "-H", "Origin: https://notebooklm.google.com",
        video_src
    ], capture_output=True, text=True, timeout=120)

    # Check stderr for content-type and redirect info
    stderr_lines = [l for l in result.stderr.split('\n') if 'content-type' in l.lower() or 'location' in l.lower() or '< HTTP' in l]
    print(f"  Response headers: {stderr_lines[:5]}")

    if os.path.exists(VIDEO_PATH):
        ft = subprocess.run(["file", VIDEO_PATH], capture_output=True, text=True).stdout.strip()
        sz = os.path.getsize(VIDEO_PATH)
        print(f"  Result: {sz/1024:.0f} KB | {ft}")

ws.close()
print("\nDone.")
