#!/usr/bin/env python3
"""Upload morningbrief video to YouTube with AI-generated thumbnail and SEO description."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import datetime
import base64
import urllib.request
import subprocess
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Config
CREDS_DIR = os.path.expanduser('~/.youtube-exai')
TOKEN_FILE = os.path.join(CREDS_DIR, 'token.json')
OPENAI_KEY = os.environ.get('OPENAI_API_KEY', '')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', 'GEMINI_API_KEY_REVOKED_PLACEHOLDER')
TODAY = datetime.date.today()
DATE_FRIENDLY = TODAY.strftime("%A, %B %d, %Y")
DATE_SHORT = TODAY.strftime("%Y-%m-%d")
VIDEO_PATH = f"/tmp/morningbrief/morningbrief_video_{DATE_SHORT}.mp4"
BRIEF_FILE = f"/tmp/morningbrief/brief_{DATE_SHORT}.md"
THUMB_PATH = f"/tmp/morningbrief/thumbnail_{DATE_SHORT}.png"

print(f"=== YouTube Upload — {DATE_FRIENDLY} ===\n")

if not os.path.exists(VIDEO_PATH):
    print(f"✗ No video found: {VIDEO_PATH}")
    sys.exit(1)

# Load brief for SEO content
brief_text = ""
if os.path.exists(BRIEF_FILE):
    with open(BRIEF_FILE) as f:
        brief_text = f.read()

# ─── Step 1: Generate thumbnail via OpenAI DALL-E ───
print("--- Generating thumbnail ---")

# Generate thumbnail with Pillow (no API key needed)
try:
    # Extract headline from brief for thumbnail
    headline = "Latest AI Updates & Breaking News"
    for line in brief_text.split('\n'):
        if 'PRIORITY' in line or 'TOP STORY' in line:
            next_lines = brief_text[brief_text.index(line):].split('\n')[1:3]
            for nl in next_lines:
                nl = nl.strip().replace('**', '').replace('*', '')
                if nl and len(nl) > 15 and not nl.startswith(':') and not nl.startswith('Source'):
                    headline = nl[:45]
                    break
            break

    import subprocess
    env = os.environ.copy()
    env['HEADLINE'] = headline
    env['THUMB_PATH'] = THUMB_PATH
    env['PYTHONPATH'] = '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages'
    result = subprocess.run(
        ['python3', '/Users/franzccm/projects/ex-venture-platform/scripts/generate_thumbnail.py'],
        capture_output=True, text=True, env=env
    )
    if os.path.exists(THUMB_PATH) and os.path.getsize(THUMB_PATH) > 1000:
        thumb_generated = True
        print(f"  ✓ Thumbnail: {os.path.getsize(THUMB_PATH)/1024:.0f} KB")
    else:
        print(f"  ✗ Thumbnail generation failed: {result.stderr[:100]}")
        THUMB_PATH = None
except Exception as e:
    print(f"  ✗ Thumbnail error: {e}")
    THUMB_PATH = None

# ─── Step 2: Generate SEO-optimized title, description, tags via Gemini ───
print("\n--- Generating SEO metadata via Gemini ---")

# Extract key topics from brief for tags
topics = []
keywords = ['Claude', 'GPT', 'Gemini', 'OpenAI', 'Anthropic', 'Google', 'DeepSeek', 'Meta', 'Llama',
            'Cursor', 'AI agents', 'funding', 'startup', 'open source', 'regulation', 'Nvidia',
            'xAI', 'Grok', 'Mistral', 'Apple AI', 'Microsoft', 'AI coding', 'LLM']
for kw in keywords:
    if kw.lower() in brief_text.lower():
        topics.append(kw)

# Use Gemini to generate SEO-optimized title
seo_prompt = f"""Based on this AI news brief, generate a YouTube video title and description.

BRIEF (first 2000 chars):
{brief_text[:2000]}

RULES FOR TITLE:
- Must be under 70 characters
- Must include "AI News" and today's date ({TODAY.strftime('%b %d')})
- Use power words: Breaking, Massive, Just Dropped, Game-Changing, etc.
- Include the #1 story headline
- Optimized for YouTube search (people search "AI news today", "latest AI news", "AI update")
- Create 3 title options ranked by click potential

RULES FOR DESCRIPTION:
- Start with a compelling 2-sentence hook
- Include timestamps-style bullet points for each story
- Include relevant keywords naturally
- End with call to action (subscribe, like)
- Under 3000 chars

Return as JSON:
{{"titles": ["title1", "title2", "title3"], "description": "full description text"}}
"""

titles = []
description = ""

if GEMINI_KEY:
    try:
        req_data = json.dumps({
            "contents": [{"parts": [{"text": seo_prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}",
            data=req_data,
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        text = result['candidates'][0]['content']['parts'][0]['text']
        seo_data = json.loads(text)
        titles = seo_data.get('titles', [])
        description = seo_data.get('description', '')
        print(f"  Gemini generated {len(titles)} title options")
    except Exception as e:
        print(f"  Gemini SEO failed: {str(e)[:80]}")

# Fallback if Gemini fails
if not titles:
    top_headline = ""
    for line in brief_text.split('\n'):
        if 'PRIORITY' in line:
            next_lines = brief_text[brief_text.index(line):].split('\n')[1:3]
            for nl in next_lines:
                nl = nl.strip()
                if nl and len(nl) > 15 and not nl.startswith(':') and not nl.startswith('Source'):
                    top_headline = nl[:50]
                    break
            break
    titles = [f"AI News Today {TODAY.strftime('%b %d')} — {top_headline}" if top_headline else f"AI News Today — {DATE_FRIENDLY}"]

if not description:
    # Extract story headlines from brief for timestamps
    stories = []
    for line in brief_text.split('\n'):
        line = line.strip()
        if line.startswith('* **') or line.startswith('- **'):
            # Extract the bold part as headline
            headline = line.split('**')[1] if '**' in line else line[:60]
            headline = headline.replace(':', ' —').strip()
            if len(headline) > 10:
                stories.append(headline[:60])

    # Build timestamp section (estimate ~30s per story)
    timestamp_lines = ""
    if stories:
        timestamp_lines = "\n⏱️ TIMESTAMPS:\n"
        for idx, story in enumerate(stories[:8]):
            mins = idx * 30 // 60
            secs = (idx * 30) % 60
            timestamp_lines += f"{mins}:{secs:02d} — {story}\n"

    description = f"""🤖 Daily AI News Report — {DATE_FRIENDLY}

🔥 Everything new in AI from the last 48 hours — all in one video!
{timestamp_lines}
📋 IN THIS VIDEO:
🚀 Latest AI model releases and updates
🛠️ New tools and features you can try right now
📅 What's dropping in the next 7 days
🔮 Insider leaks and rumors

📌 Topics covered: {', '.join(topics[:10])}

🔔 Subscribe to EXAI Global — new AI news video every single day!
👍 Like this video if you want to stay ahead in AI
💬 Comment which AI update excites you the most!

🌐 exventure.co
📧 Compiled by ExVenture AI Research Team

#AI #ArtificialIntelligence #AINews #TechNews #DailyAIUpdate #MachineLearning #LLM #GPT #Claude #Gemini #AIStartups #TechUpdate #EXAI #OpenAI #Anthropic #Google
"""

# Use title #1 as primary, save all for A/B testing
title = titles[0]
if len(title) > 100:
    title = title[:97] + "..."

# Save all title options for A/B rotation
ab_data = {
    "video_date": DATE_SHORT,
    "titles": titles,
    "current_title_index": 0,
    "rotations": [],
}
with open(f"/tmp/morningbrief/ab_test_{DATE_SHORT}.json", 'w') as f:
    json.dump(ab_data, f, indent=2)

tags = [
    "AI news", "artificial intelligence", "AI update", "daily AI", "tech news",
    "AI news today", f"AI news {TODAY.strftime('%B %Y')}", "machine learning",
    "LLM", "large language models", "AI startups", "AI funding",
    "OpenAI", "Anthropic", "Claude", "GPT", "Gemini", "Google AI",
    "AI tools", "AI agents", "EXAI Global", "ExVenture",
    "AI briefing", "tech briefing", "AI report",
] + topics

seen = set()
unique_tags = []
for t in tags:
    if t.lower() not in seen:
        seen.add(t.lower())
        unique_tags.append(t)
tags = unique_tags[:30]

for i, t in enumerate(titles):
    print(f"  Title {i+1}: {t}")
print(f"  Using: {title}")
print(f"  Tags: {len(tags)} tags")
print(f"  Description: {len(description)} chars")

# ─── Step 3: Upload to YouTube ───
print("\n--- Uploading to YouTube ---")

if not os.path.exists(TOKEN_FILE):
    print(f"  ✗ No YouTube token. Run youtube_setup.py first.")
    sys.exit(1)

with open(TOKEN_FILE) as f:
    token_data = json.load(f)

credentials = Credentials(
    token=token_data['token'],
    refresh_token=token_data['refresh_token'],
    token_uri=token_data['token_uri'],
    client_id=token_data['client_id'],
    client_secret=token_data['client_secret'],
    scopes=token_data.get('scopes', [])
)

# Refresh if expired
if credentials.expired:
    credentials.refresh(Request())
    token_data['token'] = credentials.token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)

youtube = build('youtube', 'v3', credentials=credentials)

body = {
    'snippet': {
        'title': title,
        'description': description,
        'tags': tags,
        'categoryId': '28',  # Science & Technology
        'defaultLanguage': 'en',
    },
    'status': {
        'privacyStatus': 'public',
        'selfDeclaredMadeForKids': False,
    }
}

media = MediaFileUpload(VIDEO_PATH, mimetype='video/mp4', resumable=True, chunksize=10*1024*1024)

print(f"  Uploading {os.path.getsize(VIDEO_PATH)/1024/1024:.1f} MB...")

request = youtube.videos().insert(
    part='snippet,status',
    body=body,
    media_body=media
)

response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"  Progress: {int(status.progress() * 100)}%")

video_id = response['id']
video_url = f"https://youtu.be/{video_id}"
print(f"  ✓ Uploaded! {video_url}")

# ─── Step 4: Set thumbnail ───
if THUMB_PATH and os.path.exists(THUMB_PATH):
    print("\n--- Setting thumbnail ---")
    try:
        thumb_media = MediaFileUpload(THUMB_PATH, mimetype='image/png')
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=thumb_media
        ).execute()
        print("  ✓ Thumbnail set!")
    except Exception as e:
        print(f"  ✗ Thumbnail failed: {e}")

print(f"\n=== YouTube upload complete ===")
print(f"  Video: {video_url}")
print(f"  Title: {title}")
print(f"  Channel: EXAI Global")

# Save video URL for reference
with open(f"/tmp/morningbrief/youtube_{DATE_SHORT}.txt", 'w') as f:
    f.write(video_url)

# ─── Step 5: Announce YouTube video in Slack group chat ───
print("\n--- Announcing on Slack ---")
SLACK_WEBHOOK = "SLACK_WEBHOOK_PLACEHOLDER"
slack_msg = f":youtube: New AI News video just dropped on EXAI Global!\n\n{video_url}\n\nSubscribe and stay updated on the latest AI developments!"
try:
    req = urllib.request.Request(SLACK_WEBHOOK,
        data=json.dumps({"text": slack_msg}).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    print("  ✓ YouTube link posted to Slack")
except Exception as e:
    print(f"  ✗ Slack post failed: {e}")
