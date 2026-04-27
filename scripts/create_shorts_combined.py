#!/usr/bin/env python3
"""
Combined Shorts Pipeline:
- NotebookLM generates animated video + narration (sound)
- Remotion adds text overlays, branding, 9:16 framing on top
- 3 shorts created in parallel
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import subprocess
import urllib.request
import datetime
import time
import glob
import shutil
import websocket
from concurrent.futures import ThreadPoolExecutor

TODAY = datetime.date.today()
DATE_SHORT = TODAY.strftime("%Y-%m-%d")
BRIEF_FILE = f"/tmp/morningbrief/brief_{DATE_SHORT}.md"
SHORTS_DIR = f"/tmp/morningbrief/shorts_{DATE_SHORT}"
CDP = "http://127.0.0.1:9222"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "GEMINI_API_KEY_PLACEHOLDER")
REMOTION_DIR = "/Users/franzccm/projects/ex-venture-platform/remotion-video"
DL_BASE = "/tmp/morningbrief/downloads_shorts"

os.makedirs(SHORTS_DIR, exist_ok=True)
os.makedirs(DL_BASE, exist_ok=True)

# Use latest brief
if not os.path.exists(BRIEF_FILE):
    briefs = sorted(glob.glob("/tmp/morningbrief/brief_*.md"))
    BRIEF_FILE = briefs[-1] if briefs else None
    if not BRIEF_FILE:
        print("No brief found")
        sys.exit(1)

with open(BRIEF_FILE) as f:
    brief_text = f.read()

print(f"[{time.strftime('%H:%M:%S')}] === Combined Shorts Pipeline ===\n")

# ═══ Step 1: Get 3 viral stories from Gemini ═══
print(f"[{time.strftime('%H:%M:%S')}] Getting 3 viral stories from Gemini...")
shorts_data = []
try:
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
        data=json.dumps({
            "contents": [{"parts": [{"text": f"""From this AI news brief, pick the 3 most viral-worthy stories for YouTube Shorts.

BRIEF:
{brief_text[:3000]}

For each story write:
1. A viral YouTube title (under 50 chars, with emoji)
2. A script for NotebookLM that takes exactly 40 seconds to narrate (about 90-100 words). One story. Must have a clear complete ending.
3. 3-4 key text lines to overlay on screen (short punchy phrases, max 8 words each)

Return JSON array:
[{{"title": "title", "script": "notebooklm script", "overlay_lines": ["line1", "line2", "line3"]}}]"""}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    shorts_data = json.loads(result['candidates'][0]['content']['parts'][0]['text'])
    for i, s in enumerate(shorts_data[:3]):
        print(f"  {i+1}. {s['title']}")
except Exception as e:
    print(f"  Gemini failed: {str(e)[:80]}")
    sys.exit(1)

shorts_data = shorts_data[:3]

# ═══ Step 2: Create 3 NotebookLM notebooks + trigger video generation (parallel) ═══
print(f"\n[{time.strftime('%H:%M:%S')}] Creating 3 NotebookLM notebooks...")

mid = 0

def get_any_ws():
    resp = urllib.request.urlopen(f"{CDP}/json")
    tabs = json.loads(resp.read())
    for t in tabs:
        if "notebooklm.google.com" in t.get("url", "") and "accounts" not in t.get("url", "") and "Rotate" not in t.get("url", ""):
            return websocket.create_connection(t["webSocketDebuggerUrl"])
    return None

def cdp(ws, method, params=None):
    global mid; mid += 1
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid: return r

def js(ws, e):
    return cdp(ws, "Runtime.evaluate", {"expression": e, "returnByValue": True, "awaitPromise": True}).get("result", {}).get("result", {}).get("value")

notebook_data = []  # [{nb_url, tab_ws_url, title, overlay_lines}]

for i, short in enumerate(shorts_data):
    print(f"\n  --- Short {i+1}/3 ---")

    script = f"""**VIDEO INSTRUCTIONS:** Create a short animated AI news clip about ONE story. Start with a hook. Make it cinematic. DO NOT generate any text — only animated visuals and narration.

{short['script']}"""

    # Create new tab
    ws = get_any_ws()
    if not ws:
        print(f"  ✗ No browser")
        continue
    cdp(ws, "Runtime.enable")
    r = cdp(ws, "Target.createTarget", {"url": "https://notebooklm.google.com/"})
    target_id = r.get("result", {}).get("targetId", "")
    ws.close()

    if not target_id:
        print(f"  ✗ No tab created")
        continue

    time.sleep(4)

    # Find the new tab's websocket
    resp = urllib.request.urlopen(f"{CDP}/json")
    tabs = json.loads(resp.read())
    tab_ws_url = None
    for t in tabs:
        if t.get("id") == target_id:
            tab_ws_url = t["webSocketDebuggerUrl"]
            break

    if not tab_ws_url:
        print(f"  ✗ Tab not found")
        continue

    ws = websocket.create_connection(tab_ws_url)
    cdp(ws, "Runtime.enable")
    cdp(ws, "Page.enable")
    cdp(ws, "DOM.enable")

    # Create notebook
    js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Create new'))?.click(); })()""")
    time.sleep(5)

    # Add source
    js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Copied text'))?.click(); })()""")
    time.sleep(3)

    for attempt in range(3):
        search = cdp(ws, "DOM.performSearch", {"query": "textarea[placeholder*='Paste']"})
        if search["result"]["resultCount"] > 0:
            sid = search["result"]["searchId"]
            r = cdp(ws, "DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": 1})
            cdp(ws, "DOM.focus", {"nodeId": r["result"]["nodeIds"][0]})
            time.sleep(0.5)
            cdp(ws, "Input.insertText", {"text": script})
            time.sleep(2)
            js(ws, """(() => { const b = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Insert'); if(b){b.disabled=false;b.click();} })()""")
            time.sleep(8)
            break
        time.sleep(2)

    sources = js(ws, "document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
    if sources == '0':
        print(f"  ✗ Source failed")
        ws.close()
        continue

    # Trigger video
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    time.sleep(2)
    js(ws, """(() => { const els = document.querySelectorAll('*'); for (const el of els) { if (el.childElementCount === 0 && el.textContent.trim().startsWith('Video')) { el.closest('button, [role="button"], a, [tabindex]')?.click(); return; }} })()""")
    time.sleep(3)
    js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Generate')?.click(); })()""")
    time.sleep(3)

    nb_url = js(ws, "window.location.href")
    notebook_data.append({
        "nb_url": nb_url,
        "tab_ws_url": tab_ws_url,
        "title": short["title"],
        "overlay_lines": short.get("overlay_lines", []),
        "index": i,
    })
    print(f"  ✓ Generating: {nb_url.split('/notebook/')[-1][:12]}")
    ws.close()

print(f"\n[{time.strftime('%H:%M:%S')}] All {len(notebook_data)} shorts generating in parallel on NotebookLM")

# ═══ Step 3: Wait for all videos to finish ═══
print(f"[{time.strftime('%H:%M:%S')}] Waiting for all to complete...")

ready_set = set()
for check in range(180):
    for nd in notebook_data:
        if nd["index"] in ready_set:
            continue
        try:
            ws = websocket.create_connection(nd["tab_ws_url"])
            cdp(ws, "Runtime.enable")
            ready = js(ws, """(() => {
                const t = document.body.innerText;
                if (t.includes('Good video') || t.includes('Bad video') || t.includes('is ready')) return true;
                return false;
            })()""")
            ws.close()
            if ready:
                ready_set.add(nd["index"])
                print(f"  Short {nd['index']+1} ready! ({check*10}s)")
        except:
            pass
    if len(ready_set) == len(notebook_data):
        break
    if check % 6 == 0 and check > 0:
        print(f"  [{check*10}s] {len(ready_set)}/{len(notebook_data)} ready...")
    time.sleep(10)

print(f"[{time.strftime('%H:%M:%S')}] All videos ready!")

# ═══ Step 4: Download all videos ═══
print(f"\n[{time.strftime('%H:%M:%S')}] Downloading all shorts...")

raw_files = {}
for nd in notebook_data:
    i = nd["index"]
    dl_dir = f"{DL_BASE}/short_{i}"
    os.makedirs(dl_dir, exist_ok=True)
    for f in glob.glob(f"{dl_dir}/*"): os.unlink(f)

    ws = websocket.create_connection(nd["tab_ws_url"])
    cdp(ws, "Runtime.enable")
    cdp(ws, "Page.enable")
    cdp(ws, "Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": dl_dir})

    # Get video URL
    url = ""
    for _ in range(5):
        js(ws, """(() => { document.querySelectorAll('*').forEach(el => { if (el.childElementCount === 0 && el.textContent.trim() === 'Video Overview') { el.closest('button, [role="button"], a, [tabindex]')?.click(); }}); })()""")
        time.sleep(3)
        js(ws, """(() => { document.querySelector('[aria-label*="Play"]')?.click(); })()""")
        time.sleep(3)
        js(ws, """(() => { document.querySelectorAll('video').forEach(v => { v.hidden=false; v.style.display='block'; v.load(); }); })()""")
        time.sleep(2)
        url = js(ws, "document.querySelector('video')?.src || ''")
        if url and len(url) > 50: break

    if url and len(url) > 50:
        base = url.split('=m22')[0] if '=m22' in url else url.split('?')[0]
        r = cdp(ws, "Target.createTarget", {"url": base + "=dv"})
        tid = r.get("result", {}).get("targetId", "")
        for k in range(60):
            time.sleep(5)
            done = [f for f in glob.glob(f"{dl_dir}/*") if not f.endswith('.crdownload')]
            if done:
                raw_file = f"{SHORTS_DIR}/short_{i+1}_raw.mp4"
                shutil.copy2(done[0], raw_file)
                raw_files[i] = raw_file
                print(f"  Short {i+1}: {os.path.getsize(raw_file)/1024/1024:.1f} MB")
                break
        if tid: cdp(ws, "Target.closeTarget", {"targetId": tid})

    # Close the tab
    cdp(ws, "Target.closeTarget", {"targetId": nd["tab_ws_url"].split("/")[-1].split("?")[0] if "/" in nd["tab_ws_url"] else ""})
    ws.close()

# ═══ Step 5: Remotion overlay on each video (parallel) ═══
print(f"\n[{time.strftime('%H:%M:%S')}] Rendering Remotion overlays (parallel)...")

HF_DIR = "/Users/franzccm/projects/ex-venture-platform/morningbrief-edit"

def hyperframes_short(raw_file, final_file, title, headline, detail, duration):
    """Post-process a short with Hyperframes overlays."""
    template = os.path.join(HF_DIR, "short-template.html")
    work_html = os.path.join(HF_DIR, "index.html")

    with open(template) as f:
        html = f.read()

    # Fill in content
    html = html.replace("HOOK_TITLE", title.replace('"', "'")[:40])
    html = html.replace("PANEL_HEADLINE", headline.replace('"', "'")[:50])
    html = html.replace("PANEL_DETAIL", detail.replace('"', "'")[:80])
    dur = int(min(duration, 58))
    html = html.replace('data-duration="58"', f'data-duration="{dur}"')

    with open(work_html, "w") as f:
        f.write(html)

    # Copy video to project
    shutil.copy2(raw_file, os.path.join(HF_DIR, "short_input.mp4"))

    # Render
    result = subprocess.run(
        ["npx", "hyperframes", "render", "--output", final_file],
        capture_output=True, text=True, cwd=HF_DIR, timeout=300
    )
    return os.path.exists(final_file) and os.path.getsize(final_file) > 10000

def find_silence_before(video_path, max_time=58):
    """Find the last silence point before max_time to cut at a sentence boundary."""
    result = subprocess.run([
        "ffmpeg", "-i", video_path, "-af",
        f"silencedetect=noise=-30dB:d=0.3", "-t", str(max_time + 5),
        "-f", "null", "-"
    ], capture_output=True, text=True)

    # Parse silence end timestamps
    import re
    silences = re.findall(r'silence_end: ([\d.]+)', result.stderr)
    silences = [float(s) for s in silences if float(s) <= max_time]

    if silences:
        # Pick the last silence before max_time
        return silences[-1]
    return max_time  # No silence found, hard cap

def render_short(nd):
    i = nd["index"]
    if i not in raw_files:
        return None

    raw_file = raw_files[i]
    final_file = f"{SHORTS_DIR}/short_{i+1}.mp4"

    # Get full duration
    dur_check = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", raw_file], capture_output=True, text=True)
    full_dur = float(json.loads(dur_check.stdout)["format"]["duration"])

    # Smart trim at sentence boundary if over 59s
    if full_dur <= 59:
        trim_dur = full_dur
        print(f"  Short {i+1}: {full_dur:.0f}s — fits in Shorts")
    else:
        trim_dur = find_silence_before(raw_file, 58)
        print(f"  Short {i+1}: {full_dur:.0f}s → trimmed to {trim_dur:.1f}s at sentence boundary")

    # First: scale to 9:16
    scaled_file = f"{SHORTS_DIR}/short_{i+1}_scaled.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_file,
        "-t", str(trim_dur),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-c:a", "aac", "-ac", "2", "-ar", "44100",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-map", "0:v:0", "-map", "0:a:0",
        scaled_file
    ], capture_output=True, text=True)

    if not os.path.exists(scaled_file):
        return None

    # Then: Hyperframes overlays (branding, hook card, info panel, subscribe, progress bar)
    headline = nd.get("overlay_lines", [""])[0] if nd.get("overlay_lines") else nd["title"]
    detail = nd.get("overlay_lines", ["", ""])[1] if len(nd.get("overlay_lines", [])) > 1 else "Breaking AI News"

    print(f"  Short {i+1}: Adding Hyperframes overlays...")
    if hyperframes_short(scaled_file, final_file, nd["title"], headline, detail, trim_dur):
        check = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", final_file], capture_output=True, text=True)
        final_dur = float(json.loads(check.stdout)["format"]["duration"])
        print(f"  Short {i+1}: ✓ Hyperframes {final_dur:.0f}s, {os.path.getsize(final_file)/1024/1024:.1f} MB")
        return {"file": final_file, "title": nd["title"]}
    else:
        # Fallback: use scaled video without overlays
        shutil.copy2(scaled_file, final_file)
        print(f"  Short {i+1}: ✓ ffmpeg only {os.path.getsize(final_file)/1024/1024:.1f} MB")
        return {"file": final_file, "title": nd["title"]}

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(render_short, notebook_data))

uploaded_shorts = [r for r in results if r]

# ═══ Step 6: Upload to YouTube ═══
if not uploaded_shorts:
    print("No shorts to upload")
    sys.exit(0)

print(f"\n[{time.strftime('%H:%M:%S')}] Uploading {len(uploaded_shorts)} shorts to YouTube...")

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

with open(os.path.expanduser("~/.youtube-exai/token.json")) as f:
    t = json.load(f)
creds = Credentials(token=t['token'], refresh_token=t['refresh_token'],
    token_uri=t['token_uri'], client_id=t['client_id'],
    client_secret=t['client_secret'], scopes=t.get('scopes', []))
if creds.expired:
    creds.refresh(Request())
    t['token'] = creds.token
    with open(os.path.expanduser("~/.youtube-exai/token.json"), 'w') as f:
        json.dump(t, f, indent=2)

youtube = build('youtube', 'v3', credentials=creds)

for short in uploaded_shorts:
    title = short["title"][:100]
    body = {
        'snippet': {
            'title': title,
            'description': f"AI News {TODAY.strftime('%B %d, %Y')} #Shorts #AI #AINews #TechNews #EXAI\n\n🎬 Full AI news report: {open(sorted(glob.glob('/tmp/morningbrief/youtube_*.txt'), reverse=True)[0]).read().strip() if glob.glob('/tmp/morningbrief/youtube_*.txt') else 'youtube.com/@EXAIGlobal'}\n\n🔔 Subscribe for daily AI updates!",
            'tags': ['AI', 'AI news', 'shorts', 'tech news', 'EXAI'],
            'categoryId': '28',
        },
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }
    media = MediaFileUpload(short["file"], mimetype='video/mp4', resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
    print(f"  ✓ https://youtu.be/{response['id']} — {title}")

print(f"\n[{time.strftime('%H:%M:%S')}] === Done — {len(uploaded_shorts)} shorts uploaded ===")
