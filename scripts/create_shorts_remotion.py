#!/usr/bin/env python3
"""
Create 3 YouTube Shorts using Remotion — text-based animated news cards.
No NotebookLM, no browser automation. Pure Remotion rendering.

Usage:
  python3 create_shorts_remotion.py [YYYY-MM-DD]

Reads brief from /tmp/morningbrief/brief_YYYY-MM-DD.md,
asks Gemini to pick 3 viral stories and write scripts,
renders each with Remotion in parallel,
uploads each to YouTube as a Short.
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import datetime
import subprocess
import urllib.request
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── Config ───

GEMINI_KEY = os.environ.get('GEMINI_API_KEY', 'GEMINI_API_KEY_REVOKED_PLACEHOLDER')
CREDS_DIR = os.path.expanduser('~/.youtube-exai')
TOKEN_FILE = os.path.join(CREDS_DIR, 'token.json')
REMOTION_DIR = '/Users/franzccm/projects/ex-venture-platform/remotion-video'

# Date handling
if len(sys.argv) > 1:
    DATE_SHORT = sys.argv[1]
    TODAY = datetime.datetime.strptime(DATE_SHORT, '%Y-%m-%d').date()
else:
    TODAY = datetime.date.today()
    DATE_SHORT = TODAY.strftime('%Y-%m-%d')

DATE_FRIENDLY = TODAY.strftime('%A, %B %d, %Y')
BRIEF_FILE = f'/tmp/morningbrief/brief_{DATE_SHORT}.md'
OUTPUT_DIR = f'/tmp/morningbrief/shorts_{DATE_SHORT}'
LOG_FILE = '/tmp/morningbrief/shorts.log'

# Duration config
SHORT_DURATION_SEC = 35  # 35 seconds per short
FPS = 30
TOTAL_FRAMES = SHORT_DURATION_SEC * FPS


def log(msg):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def gemini_request(prompt, response_json=True):
    """Call Gemini API with a prompt, return parsed response."""
    config = {"temperature": 0.9}
    if response_json:
        config["responseMimeType"] = "application/json"

    req_data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": config,
    }).encode()

    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
        data=req_data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    text = result['candidates'][0]['content']['parts'][0]['text']

    if response_json:
        return json.loads(text)
    return text


def pick_stories(brief_text):
    """Ask Gemini to pick 3 viral stories and write scripts for Shorts."""
    prompt = f"""You are a viral YouTube Shorts content strategist for EXAI Global, a tech news channel.

From this AI/tech news brief, pick the 3 MOST VIRAL stories — the ones that would make someone stop scrolling.

BRIEF:
{brief_text[:4000]}

For each story, create a SHORT SCRIPT as a series of text cards (sentences that appear one at a time on screen).

RULES:
- Each story needs a HOOK title (under 8 words, attention-grabbing, no clickbait lies)
- Each story needs exactly 4-5 text card lines
- Each line must be under 80 characters (it needs to fit on a phone screen in large text)
- Total word count per story: under 60 words (excluding title)
- Write in punchy, direct language — like a news ticker
- Include one emoji per line for visual interest (start of line)
- End the last line with a call-to-action or cliffhanger
- Stories should cover DIFFERENT topics (don't repeat)

Return JSON:
{{
  "stories": [
    {{
      "title": "Hook Title Here",
      "lines": [
        "First text card line",
        "Second text card line",
        "Third text card line",
        "Fourth text card line"
      ],
      "hashtags": ["#AI", "#Tech", "#relevant"],
      "yt_title": "YouTube title under 60 chars with keywords",
      "yt_description": "2-3 sentence SEO description"
    }}
  ]
}}
"""
    return gemini_request(prompt)


def render_short(story_index, story, output_path):
    """Render a single Short with Remotion."""
    props = {
        "title": story["title"],
        "lines": story["lines"],
        "accentColor": ["#00aaff", "#ff6b35", "#00ff88"][story_index % 3],
    }

    # Write props to temp file (avoids shell escaping issues)
    props_file = os.path.join(OUTPUT_DIR, f'props_{story_index}.json')
    with open(props_file, 'w') as f:
        json.dump(props, f)

    cmd = [
        'npx', 'remotion', 'render',
        'src/index.tsx',
        'NewsShort',
        output_path,
        f'--props={props_file}',
        f'--frames=0-{TOTAL_FRAMES - 1}',
        '--log=error',
    ]

    log(f"  Rendering Short #{story_index + 1}: {story['title']}")
    start = time.time()

    result = subprocess.run(
        cmd,
        cwd=REMOTION_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )

    elapsed = time.time() - start

    if result.returncode != 0:
        log(f"  ERROR rendering #{story_index + 1}: {result.stderr[:200]}")
        return False

    size_mb = os.path.getsize(output_path) / 1024 / 1024 if os.path.exists(output_path) else 0
    log(f"  Done #{story_index + 1} in {elapsed:.0f}s ({size_mb:.1f} MB)")
    return True


def upload_short(story, video_path, story_index):
    """Upload a rendered Short to YouTube."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        log("  ERROR: google-api-python-client not installed")
        return None

    if not os.path.exists(TOKEN_FILE):
        log(f"  ERROR: No YouTube token at {TOKEN_FILE}")
        return None

    if not os.path.exists(video_path):
        log(f"  ERROR: No video file at {video_path}")
        return None

    with open(TOKEN_FILE) as f:
        token_data = json.load(f)

    credentials = Credentials(
        token=token_data['token'],
        refresh_token=token_data['refresh_token'],
        token_uri=token_data['token_uri'],
        client_id=token_data['client_id'],
        client_secret=token_data['client_secret'],
        scopes=token_data.get('scopes', []),
    )

    if credentials.expired:
        credentials.refresh(Request())
        token_data['token'] = credentials.token
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)

    youtube = build('youtube', 'v3', credentials=credentials)

    yt_title = story.get('yt_title', story['title'])
    if len(yt_title) > 100:
        yt_title = yt_title[:97] + '...'

    hashtags = story.get('hashtags', ['#AI', '#Tech', '#News'])
    hashtag_str = ' '.join(hashtags[:5])

    yt_desc = story.get('yt_description', '')
    description = f"""{yt_desc}

{hashtag_str}

Subscribe to EXAI Global for daily AI news!
exventure.co

#Shorts #AINews #TechNews #EXAI #DailyAI
"""

    body = {
        'snippet': {
            'title': yt_title,
            'description': description,
            'tags': [h.replace('#', '') for h in hashtags] + [
                'AI news', 'tech news', 'AI update', 'Shorts',
                'EXAI Global', 'artificial intelligence',
            ],
            'categoryId': '28',
            'defaultLanguage': 'en',
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        },
    }

    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)

    log(f"  Uploading Short #{story_index + 1}: {yt_title}")
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log(f"    Progress: {int(status.progress() * 100)}%")

    video_id = response['id']
    video_url = f"https://youtu.be/{video_id}"
    log(f"  Uploaded #{story_index + 1}: {video_url}")
    return video_url


def main():
    log(f"=== YouTube Shorts Pipeline — {DATE_FRIENDLY} ===")
    log(f"Brief: {BRIEF_FILE}")
    log(f"Output: {OUTPUT_DIR}")

    # ─── Step 1: Read brief ───
    if not os.path.exists(BRIEF_FILE):
        log(f"ERROR: Brief not found at {BRIEF_FILE}")
        sys.exit(1)

    with open(BRIEF_FILE) as f:
        brief_text = f.read()

    if len(brief_text) < 100:
        log("ERROR: Brief too short")
        sys.exit(1)

    log(f"Brief loaded: {len(brief_text)} chars")

    # ─── Step 2: Ask Gemini for 3 viral stories ───
    log("Asking Gemini for 3 viral stories...")
    try:
        result = pick_stories(brief_text)
        stories = result.get('stories', [])
    except Exception as e:
        log(f"ERROR: Gemini failed: {e}")
        sys.exit(1)

    if len(stories) < 3:
        log(f"WARNING: Gemini returned only {len(stories)} stories")
        if len(stories) == 0:
            sys.exit(1)

    for i, s in enumerate(stories):
        log(f"  Story {i+1}: {s['title']} ({len(s['lines'])} cards)")

    # ─── Step 3: Render all 3 in parallel ───
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    video_paths = []
    log("\nRendering shorts in parallel...")

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        for i, story in enumerate(stories):
            output_path = os.path.join(OUTPUT_DIR, f'short_{i+1}.mp4')
            video_paths.append(output_path)
            futures[executor.submit(render_short, i, story, output_path)] = i

        render_results = {}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                render_results[idx] = future.result()
            except Exception as e:
                log(f"  EXCEPTION rendering #{idx + 1}: {e}")
                render_results[idx] = False

    success_count = sum(1 for v in render_results.values() if v)
    log(f"\nRendered {success_count}/{len(stories)} shorts successfully")

    if success_count == 0:
        log("ERROR: No shorts rendered")
        sys.exit(1)

    # ─── Step 4: Upload each to YouTube ───
    log("\nUploading shorts to YouTube...")
    uploaded_urls = []

    for i, story in enumerate(stories):
        if not render_results.get(i, False):
            log(f"  Skipping #{i+1} (render failed)")
            continue

        try:
            url = upload_short(story, video_paths[i], i)
            if url:
                uploaded_urls.append(url)
        except Exception as e:
            log(f"  ERROR uploading #{i+1}: {e}")

    # ─── Step 5: Summary ───
    log(f"\n=== Shorts Pipeline Complete ===")
    log(f"  Rendered: {success_count}/{len(stories)}")
    log(f"  Uploaded: {len(uploaded_urls)}/{len(stories)}")
    for url in uploaded_urls:
        log(f"  {url}")

    # Save results
    results_file = os.path.join(OUTPUT_DIR, 'results.json')
    with open(results_file, 'w') as f:
        json.dump({
            'date': DATE_SHORT,
            'stories': stories,
            'videos': video_paths,
            'youtube_urls': uploaded_urls,
            'rendered': success_count,
            'uploaded': len(uploaded_urls),
        }, f, indent=2)

    log(f"Results saved to {results_file}")


if __name__ == '__main__':
    main()
