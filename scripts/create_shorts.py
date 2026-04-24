#!/usr/bin/env python3
"""
Create 3 standalone viral YouTube Shorts about today's AI news.
Each Short is its own NotebookLM video — not cut from the long-form.
Optimized for the Shorts algorithm: hook, fast pace, vertical.
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import subprocess
import urllib.request
import datetime
import time
import base64
import glob
import shutil
import websocket

TODAY = datetime.date.today()
DATE_SHORT = TODAY.strftime("%Y-%m-%d")
DATE_FRIENDLY = TODAY.strftime("%B %d, %Y")
BRIEF_FILE = f"/tmp/morningbrief/brief_{DATE_SHORT}.md"
SHORTS_DIR = f"/tmp/morningbrief/shorts_{DATE_SHORT}"
CDP = "http://127.0.0.1:9222"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "GEMINI_API_KEY_REVOKED_PLACEHOLDER")
DL_DIR = "/tmp/morningbrief/downloads_shorts"

os.makedirs(SHORTS_DIR, exist_ok=True)
os.makedirs(DL_DIR, exist_ok=True)

if not os.path.exists(BRIEF_FILE):
    print(f"No brief: {BRIEF_FILE}")
    sys.exit(1)

with open(BRIEF_FILE) as f:
    brief_text = f.read()

# Ask Gemini to pick 3 viral-worthy stories and write short scripts
print("=== Creating 3 Viral Shorts ===\n")
print("Asking Gemini for 3 viral stories...")

shorts_data = []
try:
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
        data=json.dumps({
            "contents": [{"parts": [{"text": f"""From this AI news brief, pick the 3 most viral-worthy stories for YouTube Shorts.

BRIEF:
{brief_text[:3000]}

For each story write a short script (under 150 words) based on topics from the main video:
- Start with a HOOK (shocking statement or bold claim)
- Cover the story properly — give enough context so the viewer understands
- Keep it under 45 seconds when read aloud
- End with "Subscribe for daily AI news!"
- ONE story per Short
- Make it engaging and informative

Return JSON array:
[
  {{"title": "viral title under 50 chars with emoji", "script": "the full script text"}},
  ...
]"""}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    shorts_data = json.loads(result['candidates'][0]['content']['parts'][0]['text'])
    print(f"  ✓ {len(shorts_data)} stories selected")
    for i, s in enumerate(shorts_data):
        print(f"    {i+1}. {s['title']}")
except Exception as e:
    print(f"  ✗ Gemini failed: {str(e)[:80]}")
    sys.exit(1)

# For each Short: create NotebookLM notebook → generate video → download → crop vertical → upload
mid = 0

def get_any_ws():
    """Get any NotebookLM tab — used only for creating new tabs."""
    resp = urllib.request.urlopen(f"{CDP}/json")
    tabs = json.loads(resp.read())
    for t in tabs:
        if "notebooklm.google.com" in t.get("url", "") and "accounts" not in t.get("url", "") and "Rotate" not in t.get("url", ""):
            return websocket.create_connection(t["webSocketDebuggerUrl"])
    return None

def create_new_tab(url):
    """Open a NEW browser tab and return its websocket URL."""
    ws = get_any_ws()
    if not ws: return None
    cdp(ws, "Runtime.enable")
    r = cdp(ws, "Target.createTarget", {"url": url})
    target_id = r.get("result", {}).get("targetId", "")
    ws.close()
    if not target_id: return None
    time.sleep(3)
    resp = urllib.request.urlopen(f"{CDP}/json")
    tabs = json.loads(resp.read())
    for t in tabs:
        if t.get("id") == target_id:
            return t["webSocketDebuggerUrl"]
    return None

def cdp(ws, method, params=None):
    global mid; mid += 1
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid: return r

def js(ws, e):
    return cdp(ws, "Runtime.evaluate", {"expression": e, "returnByValue": True, "awaitPromise": True}).get("result", {}).get("result", {}).get("value")

uploaded_shorts = []

# Create ALL 3 notebooks and start generation in parallel first
notebook_urls = []
for i, short in enumerate(shorts_data[:3]):
    print(f"\n--- Creating Short {i+1}/3 in NEW tab ---")

    script_text = f"""**VIDEO INSTRUCTIONS:** Create a YouTube Short video. Under 50 seconds. Start with a hook. Cover one AI news story with enough detail that the viewer understands what happened and why it matters. End with "Subscribe for daily AI news!" Make it cinematic and animated.

{short['script']}"""

    # Open NotebookLM in a NEW tab (doesn't touch main video tab)
    tab_ws_url = create_new_tab("https://notebooklm.google.com/")
    if not tab_ws_url:
        print("  ✗ Could not create tab")
        notebook_urls.append(None)
        continue

    ws = websocket.create_connection(tab_ws_url)
    cdp(ws, "Runtime.enable")
    cdp(ws, "Page.enable")
    cdp(ws, "DOM.enable")

    # Create notebook in this tab
    js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Create new'))?.click(); })()""")
    time.sleep(5)

    js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Copied text'))?.click(); })()""")
    time.sleep(3)

    for attempt in range(3):
        search = cdp(ws, "DOM.performSearch", {"query": "textarea[placeholder*='Paste']"})
        if search["result"]["resultCount"] > 0:
            sid = search["result"]["searchId"]
            r = cdp(ws, "DOM.getSearchResults", {"searchId": sid, "fromIndex": 0, "toIndex": 1})
            cdp(ws, "DOM.focus", {"nodeId": r["result"]["nodeIds"][0]})
            time.sleep(0.5)
            cdp(ws, "Input.insertText", {"text": script_text})
            time.sleep(2)
            js(ws, """(() => { const b = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Insert'); if(b){b.disabled=false;b.click();} })()""")
            time.sleep(8)
            break
        time.sleep(2)

    sources = js(ws, "document.body.innerText.match(/(\\d+)\\s*source/)?.[1] || '0'")
    if sources == '0':
        print(f"  ✗ Source failed")
        notebook_urls.append(None)
        ws.close()
        continue

    # Trigger video generation
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    cdp(ws, "Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    time.sleep(2)
    js(ws, """(() => { const els = document.querySelectorAll('*'); for (const el of els) { if (el.childElementCount === 0 && el.textContent.trim().startsWith('Video')) { el.closest('button, [role="button"], a, [tabindex]')?.click(); return; }} })()""")
    time.sleep(3)
    js(ws, """(() => { const els = document.querySelectorAll('*'); for (const el of els) { if (el.textContent.trim() === 'Brief' && el.childElementCount <= 1) { el.closest('button, [role="button"], div[class*="card"], div[class*="tile"], [tabindex]')?.click(); return; }} })()""")
    time.sleep(2)
    js(ws, """(() => { Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Generate')?.click(); })()""")
    time.sleep(3)

    nb_url = js(ws, "window.location.href")
    notebook_urls.append(nb_url)
    print(f"  ✓ Generating in own tab: {nb_url.split('/notebook/')[-1][:12]}...")
    ws.close()

print(f"\n=== All {len([u for u in notebook_urls if u])} shorts generating in parallel ===")
print("Waiting for all to complete...\n")

# Open separate tabs for each notebook and navigate them
print("\n=== Opening separate tabs for parallel download ===")
tab_ws = {}
for i, nb_url in enumerate(notebook_urls):
    if not nb_url: continue
    try:
        # Create new tab with this notebook URL
        main_ws = get_ws()
        if not main_ws: continue
        cdp(main_ws, "Runtime.enable")
        r = cdp(main_ws, "Target.createTarget", {"url": nb_url})
        target_id = r.get("result", {}).get("targetId", "")
        main_ws.close()
        if target_id:
            # Connect to the new tab
            time.sleep(3)
            resp = urllib.request.urlopen(f"{CDP}/json")
            tabs = json.loads(resp.read())
            for t in tabs:
                if t.get("id") == target_id:
                    tab_ws[i] = {"ws_url": t["webSocketDebuggerUrl"], "target_id": target_id, "nb_url": nb_url}
                    print(f"  Tab {i+1}: opened {nb_url.split('/notebook/')[-1][:12]}")
                    break
    except Exception as e:
        print(f"  Tab {i+1} failed: {str(e)[:60]}")

# Poll ALL tabs simultaneously until all ready
print("\n=== Waiting for all shorts (parallel) ===")
ready_tabs = set()
for j in range(120):
    for i, tab_info in tab_ws.items():
        if i in ready_tabs: continue
        try:
            ws = websocket.create_connection(tab_info["ws_url"])
            cdp(ws, "Runtime.enable")
            ready = js(ws, """(() => {
                const t = document.body.innerText;
                if (t.includes('Good video') || t.includes('Bad video')) return true;
                if (t.includes('is ready')) return true;
                return false;
            })()""")
            ws.close()
            if ready:
                ready_tabs.add(i)
                print(f"  Short {i+1} ready! ({j*10}s)")
        except:
            pass
    if len(ready_tabs) == len(tab_ws):
        print(f"  All {len(ready_tabs)} shorts ready!")
        break
    if j % 6 == 0 and j > 0:
        print(f"  [{j*10}s] {len(ready_tabs)}/{len(tab_ws)} ready...")
    time.sleep(10)

# Download all ready shorts
for i, tab_info in tab_ws.items():
    if i not in ready_tabs: continue
    short = shorts_data[i]
    print(f"\n--- Downloading Short {i+1}: {short['title'][:40]} ---")

    ws = websocket.create_connection(tab_info["ws_url"])
    cdp(ws, "Runtime.enable")
    cdp(ws, "Page.enable")

    # Download
    for f in glob.glob(f"{DL_DIR}/*"): os.unlink(f)
    cdp(ws, "Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": DL_DIR})

    url = ""
    for _ in range(5):
        js(ws, """(() => { const els = document.querySelectorAll('*'); for (const el of els) { if (el.childElementCount === 0 && el.textContent.trim() === 'Video Overview') { el.closest('button, [role="button"], a, [tabindex]')?.click(); }} })()""")
        time.sleep(3)
        js(ws, """(() => { document.querySelector('[aria-label*="Play"]')?.click(); })()""")
        time.sleep(3)
        js(ws, """(() => { document.querySelectorAll('video').forEach(v => { v.hidden=false; v.style.display='block'; v.load(); }); })()""")
        time.sleep(2)
        url = js(ws, "document.querySelector('video')?.src || ''")
        if url and len(url) > 50: break

    if url and len(url) > 50:
        base_url = url.split('=m22')[0] if '=m22' in url else url.split('?')[0]
        r = cdp(ws, "Target.createTarget", {"url": base_url + "=dv"})
        tid = r.get("result", {}).get("targetId", "")
        for k in range(60):
            time.sleep(5)
            done = [f for f in glob.glob(f"{DL_DIR}/*") if not f.endswith('.crdownload')]
            if done:
                raw_file = f"{SHORTS_DIR}/short_{i+1}_raw.mp4"
                shutil.copy2(done[0], raw_file)
                print(f"  ✓ Downloaded: {os.path.getsize(raw_file)/1024/1024:.1f} MB")

                # Render with Remotion (full 9:16, overlays, branding)
                final_file = f"{SHORTS_DIR}/short_{i+1}.mp4"
                remotion_dir = "/Users/franzccm/projects/ex-venture-platform/remotion-video"
                public_dir = os.path.join(remotion_dir, "public")
                os.makedirs(public_dir, exist_ok=True)

                # Copy raw video to Remotion public folder
                import shutil as _shutil
                input_name = f"short_{i+1}_input.mp4"
                _shutil.copy2(raw_file, os.path.join(public_dir, input_name))

                dur_check = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", raw_file], capture_output=True, text=True)
                raw_dur = min(58, float(json.loads(dur_check.stdout)["format"]["duration"]))
                frames = int(raw_dur * 30)

                # Clean title for JSON
                clean_title = short["title"].replace('"', "'")
                props = json.dumps({"src": input_name, "startFrom": 0, "duration": raw_dur, "title": clean_title})

                print(f"  Rendering with Remotion ({frames} frames)...")
                remotion_result = subprocess.run([
                    "npx", "remotion", "render",
                    "src/index.tsx", "Short", final_file,
                    "--props", props,
                    f"--frames=0-{frames}",
                ], capture_output=True, text=True, cwd=remotion_dir, timeout=300)

                if not os.path.exists(final_file) or os.path.getsize(final_file) < 10000:
                    print(f"  Remotion failed, ffmpeg fallback...")
                    subprocess.run([
                        "ffmpeg", "-y", "-i", raw_file, "-t", "58",
                        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                        "-c:v", "libx264", "-c:a", "aac", "-ac", "2", "-ar", "44100",
                        "-pix_fmt", "yuv420p", "-r", "30",
                        "-map", "0:v:0", "-map", "0:a:0",
                        final_file
                    ], capture_output=True, text=True)

                if os.path.exists(final_file) and os.path.getsize(final_file) > 10000:
                    print(f"  ✓ Rendered: {os.path.getsize(final_file)/1024/1024:.1f} MB")
                    uploaded_shorts.append({"file": final_file, "title": short["title"]})
                break
        if tid:
            cdp(ws, "Target.closeTarget", {"targetId": tid})

    ws.close()

# Upload all shorts to YouTube
if not uploaded_shorts:
    print("\nNo shorts to upload")
    sys.exit(0)

TOKEN_FILE = os.path.expanduser("~/.youtube-exai/token.json")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

with open(TOKEN_FILE) as f:
    t = json.load(f)
creds = Credentials(token=t['token'], refresh_token=t['refresh_token'],
    token_uri=t['token_uri'], client_id=t['client_id'],
    client_secret=t['client_secret'], scopes=t.get('scopes', []))
if creds.expired:
    creds.refresh(Request())
    t['token'] = creds.token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(t, f, indent=2)

youtube = build('youtube', 'v3', credentials=creds)

print(f"\n=== Uploading {len(uploaded_shorts)} Shorts ===")
for short in uploaded_shorts:
    title = short["title"][:100]
    body = {
        'snippet': {
            'title': title,
            'description': f"AI News {DATE_FRIENDLY} #Shorts #AI #AINews #TechNews #EXAI\n\nSubscribe for daily AI updates!",
            'tags': ['AI', 'AI news', 'shorts', 'tech news', 'artificial intelligence', 'EXAI'],
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

print(f"\nDone — {len(uploaded_shorts)} viral Shorts uploaded.")
