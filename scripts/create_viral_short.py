#!/usr/bin/env python3
"""
Create a viral YouTube Short by:
1. Gemini picks today's top stories
2. Download viral AI demo clips from YouTube/social
3. ffmpeg stitches clips + transitions
4. Hyperframes adds branding, text overlays, subscribe CTA
5. Upload to YouTube
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os, json, subprocess, datetime, time, shutil, glob, urllib.request

TODAY = datetime.date.today()
DATE_SHORT = TODAY.strftime("%Y-%m-%d")
WORK_DIR = f"/tmp/morningbrief/viral_short_{DATE_SHORT}"
HF_DIR = "/Users/franzccm/projects/ex-venture-platform/morningbrief-edit"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "GEMINI_API_KEY_REVOKED_PLACEHOLDER")
BRIEF = None

# Find brief
for f in sorted(glob.glob("/tmp/morningbrief/brief_*.md"), reverse=True):
    BRIEF = f
    break

os.makedirs(WORK_DIR, exist_ok=True)

print(f"[{time.strftime('%H:%M:%S')}] === Viral AI Short Creator ===\n")

# ═══ Step 1: Get stories + find viral video URLs ═══
print("Step 1: Getting stories and video URLs from Gemini...")

brief_text = ""
if BRIEF:
    with open(BRIEF) as f:
        brief_text = f.read()[:2000]

try:
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
        data=json.dumps({
            "contents": [{"parts": [{"text": f"""I need 4 viral AI demo/news videos from YouTube that were uploaded in the last 7 days. Search for the most viewed/trending AI demos, tool showcases, and news recaps.

Focus on: ChatGPT demos, Claude demos, Gemini demos, AI tool showcases, AI news recaps, viral AI moments.

For each video provide:
1. A YouTube search query to find the video (e.g. "ChatGPT 4o voice demo 2026")
2. A 5-word description of what's shown
3. Start timestamp (seconds) for the best 8-second clip

Also write for each clip:
- overlay: punchy text overlay (max 6 words, ALL CAPS)
- context: 2 sentences explaining what this clip shows and why it matters (this will be shown as subtitle)

Based on this brief for context:
{brief_text[:1000]}

Return JSON:
{{
  "clips": [
    {{"url": "youtube_url", "desc": "short description", "start": 10, "overlay": "BOLD TEXT OVERLAY", "subtitle": "Subtitle explaining the clip"}},
    ...
  ],
  "hook": "Attention-grabbing first line under 8 words",
  "title": "Viral YouTube Short title with emoji under 50 chars"
}}"""}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(json.loads(resp.read())['candidates'][0]['content']['parts'][0]['text'])
    print(f"  ✓ {len(data['clips'])} clips found")
    print(f"  Hook: {data['hook']}")
    print(f"  Title: {data['title']}")
except Exception as e:
    print(f"  ✗ Gemini failed: {str(e)[:80]}")
    # Fallback
    data = {
        "clips": [
            {"url": "https://www.youtube.com/watch?v=iUQjxiJAJoE", "desc": "AI news weekly recap", "start": 15, "overlay": "AI JUST CHANGED FOREVER"},
            {"url": "https://www.youtube.com/watch?v=iUQjxiJAJoE", "desc": "GPT-5 demo showcase", "start": 60, "overlay": "GPT-5 IS INSANE"},
            {"url": "https://www.youtube.com/watch?v=iUQjxiJAJoE", "desc": "Claude design tool", "start": 120, "overlay": "CLAUDE BUILDS WEBSITES"},
            {"url": "https://www.youtube.com/watch?v=iUQjxiJAJoE", "desc": "Gemini workspace AI", "start": 180, "overlay": "GOOGLE WENT ALL IN"},
        ],
        "hook": "AI just broke the internet AGAIN",
        "title": "🤯 AI Just Broke The Internet AGAIN!"
    }

# ═══ Step 2: Download clips via yt-dlp search (real videos, not Gemini URLs) ═══
print("\nStep 2: Downloading clips from YouTube...")

searches = [
    "AI news today 2026 demo",
    "ChatGPT new update demo",
    "Claude AI demo",
    "Gemini AI new feature",
    "AI tool goes viral",
]

clip_files = []
for i, query in enumerate(searches):
    if len(clip_files) >= 4:
        break

    out_full = f"{WORK_DIR}/full_{i}.mp4"
    out_file = f"{WORK_DIR}/clip_{i}.mp4"
    overlay = data['clips'][i]['overlay'] if i < len(data.get('clips', [])) else query.upper()[:25]
    print(f"  Searching: {query}...")

    try:
        subprocess.run([
            "yt-dlp", "--no-warnings", "-q",
            "-f", "best[height<=720]",
            "--max-downloads", "1",
            "-o", out_full,
            f"ytsearch1:{query}"
        ], capture_output=True, text=True, timeout=120)

        if os.path.exists(out_full) and os.path.getsize(out_full) > 10000:
            subprocess.run([
                "ffmpeg", "-y", "-ss", "15", "-i", out_full,
                "-t", "8", "-c:v", "libx264", "-c:a", "aac",
                out_file
            ], capture_output=True, text=True)

            try:
                os.unlink(out_full)
            except:
                pass

            if os.path.exists(out_file) and os.path.getsize(out_file) > 5000:
                clip_files.append({"file": out_file, "overlay": overlay})
                print(f"  ✓ {os.path.getsize(out_file)/1024:.0f} KB")
            else:
                print(f"  ✗ Trim failed")
        else:
            print(f"  ✗ Download failed")
    except Exception as e:
        print(f"  ✗ {str(e)[:60]}")

if len(clip_files) < 2:
    print("Not enough clips. Aborting.")
    sys.exit(1)

# ═══ Step 3: Generate TTS narration for each clip ═══
print("\nStep 3: Generating narration...")

from gtts import gTTS

# Build full narration script
narration_parts = []
hook_text = data.get('hook', 'Here are the biggest AI updates you need to know about')
narration_parts.append(hook_text)

for clip in clip_files:
    context = clip.get('context', clip.get('overlay', 'Major AI update'))
    if isinstance(context, str) and len(context) > 10:
        narration_parts.append(context)
    else:
        narration_parts.append(clip['overlay'])

narration_parts.append("Subscribe for daily AI news updates!")

# Generate TTS for each part
tts_files = []
for i, text in enumerate(narration_parts):
    tts_file = f"{WORK_DIR}/tts_{i}.mp3"
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(tts_file)
        tts_files.append(tts_file)
        print(f"  ✓ TTS {i+1}: {text[:40]}...")
    except Exception as e:
        print(f"  ✗ TTS {i+1}: {str(e)[:40]}")

# ═══ Step 4: Process each clip to 9:16 + replace audio with narration ═══
print("\nStep 4: Processing clips with narration...")

processed = []
for i, clip in enumerate(clip_files):
    out = f"{WORK_DIR}/processed_{i}.mp4"
    tts_idx = i + 1  # skip hook narration (index 0)

    if tts_idx < len(tts_files):
        # Get TTS duration to match clip length
        tts_dur = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", tts_files[tts_idx]], capture_output=True, text=True)
        tts_length = float(json.loads(tts_dur.stdout)["format"]["duration"])
        clip_length = max(tts_length + 1, 8)  # clip is at least as long as narration + 1s padding

        # Scale video to 9:16, mute original audio, add TTS narration
        subprocess.run([
            "ffmpeg", "-y",
            "-i", clip['file'],
            "-i", tts_files[tts_idx],
            "-t", str(clip_length),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-c:a", "aac", "-ac", "2", "-ar", "44100",
            "-pix_fmt", "yuv420p", "-r", "30",
            "-map", "0:v:0", "-map", "1:a:0",
            "-shortest",
            out
        ], capture_output=True, text=True)
    else:
        # No TTS, just scale
        subprocess.run([
            "ffmpeg", "-y", "-i", clip['file'],
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-c:a", "aac", "-ac", "2", "-ar", "44100",
            "-pix_fmt", "yuv420p", "-r", "30", "-t", "10",
            out
        ], capture_output=True, text=True)

    if os.path.exists(out):
        processed.append({"file": out, "overlay": clip['overlay']})
        print(f"  ✓ Clip {i+1}: {os.path.getsize(out)/1024:.0f} KB")

# ═══ Step 5: Create hook intro clip (TTS over black/gradient) ═══
print("\nStep 5: Creating hook intro...")

if tts_files:
    hook_img = f"{WORK_DIR}/hook_frame.png"
    # Create hook frame with Pillow
    from PIL import Image, ImageDraw, ImageFont
    def font(size):
        for p in ['/System/Library/Fonts/Helvetica.ttc', '/Library/Fonts/Arial.ttf']:
            if os.path.exists(p):
                try: return ImageFont.truetype(p, size)
                except: pass
        return ImageFont.load_default()

    img = Image.new('RGB', (1080, 1920), (10, 14, 39))
    d = ImageDraw.Draw(img)
    # Grid
    for x in range(0, 1080, 80):
        d.line([(x, 0), (x, 1920)], fill=(30, 30, 70), width=1)
    for y in range(0, 1920, 80):
        d.line([(0, y), (1080, y)], fill=(30, 30, 70), width=1)
    # Branding
    d.text((30, 50), 'EXAI GLOBAL', fill=(0, 170, 255), font=font(28))
    d.rounded_rectangle([880, 48, 1050, 82], radius=6, fill=(204, 0, 0))
    d.text((898, 52), 'AI NEWS', fill=(255, 255, 255), font=font(20))
    # Hook text
    d.rounded_rectangle([60, 750, 1020, 950], radius=16, fill=(0, 20, 60))
    d.rectangle([60, 750, 66, 950], fill=(0, 170, 255))
    hook_words = hook_text.split()
    line1 = ' '.join(hook_words[:len(hook_words)//2])
    line2 = ' '.join(hook_words[len(hook_words)//2:])
    d.text((90, 790), line1.upper(), fill=(255, 255, 255), font=font(48))
    d.text((90, 860), line2.upper(), fill=(0, 170, 255), font=font(48))
    img.save(hook_img)

    # Create hook video: image + TTS audio
    hook_clip = f"{WORK_DIR}/hook_clip.mp4"
    tts_dur_check = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", tts_files[0]], capture_output=True, text=True)
    hook_dur = float(json.loads(tts_dur_check.stdout)["format"]["duration"]) + 0.5

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", hook_img,
        "-i", tts_files[0],
        "-t", str(hook_dur),
        "-vf", "scale=1080:1920",
        "-c:v", "libx264", "-c:a", "aac", "-ac", "2", "-ar", "44100",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-shortest",
        hook_clip
    ], capture_output=True, text=True)

    if os.path.exists(hook_clip):
        processed.insert(0, {"file": hook_clip, "overlay": "HOOK"})
        print(f"  ✓ Hook: {os.path.getsize(hook_clip)/1024:.0f} KB")

# ═══ Step 6: Stitch all clips ═══
print("\nStep 6: Stitching...")

concat_file = f"{WORK_DIR}/concat.txt"
with open(concat_file, "w") as f:
    for p in processed:
        f.write(f"file '{p['file']}'\n")

stitched = f"{WORK_DIR}/stitched.mp4"
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
    "-c:v", "libx264", "-c:a", "aac",
    "-pix_fmt", "yuv420p",
    stitched
], capture_output=True, text=True)

if not os.path.exists(stitched):
    print("  ✗ Stitching failed")
    sys.exit(1)

dur_check = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", stitched], capture_output=True, text=True)
total_dur = float(json.loads(dur_check.stdout)["format"]["duration"])
print(f"  ✓ Stitched: {total_dur:.0f}s, {os.path.getsize(stitched)/1024/1024:.1f} MB")

# ═══ Step 8: Upload to YouTube (stitched video already has narration + hook) ═══
final = stitched
print(f"\nStep 8: Uploading to YouTube...")

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

yt = build('youtube', 'v3', credentials=creds)
title = data.get('title', f'🤯 AI News Recap {TODAY.strftime("%b %d")}')[:100]

# Get latest longform video link
longform_link = ""
yt_files = sorted(glob.glob("/tmp/morningbrief/youtube_*.txt"), reverse=True)
if yt_files:
    with open(yt_files[0]) as f:
        longform_link = f.read().strip()

body = {
    'snippet': {
        'title': f'{title} #Shorts',
        'description': f'AI News {TODAY.strftime("%B %d, %Y")} #Shorts #AI #AINews #EXAI\n\n🎬 Watch the full AI news report: {longform_link}\n\n🔔 Subscribe for daily AI updates!',
        'tags': ['AI', 'AI news', 'shorts', 'EXAI', 'viral', 'tech news'],
        'categoryId': '28',
    },
    'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
}
media = MediaFileUpload(final, mimetype='video/mp4', resumable=True)
request = yt.videos().insert(part='snippet,status', body=body, media_body=media)
response = None
while response is None:
    status, response = request.next_chunk()

print(f"  ✓ https://youtu.be/{response['id']}")
print(f"\n=== Done ===")
