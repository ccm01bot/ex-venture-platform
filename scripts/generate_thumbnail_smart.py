#!/usr/bin/env python3
"""Generate thumbnail: try OpenAI DALL-E first, then Gemini, then Pillow fallback."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import base64
import urllib.request
import datetime

TODAY = datetime.date.today()
DATE_SHORT = TODAY.strftime("%Y-%m-%d")
THUMB_PATH = os.environ.get("THUMB_PATH", f"/tmp/morningbrief/thumbnail_{DATE_SHORT}.png")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "GEMINI_API_KEY_PLACEHOLDER")

PROMPT = f"Professional YouTube thumbnail for a daily AI news report video. Dark blue and purple tech background with glowing circuit board patterns and neural network visuals. Bold large white text says AI NEWS {TODAY.strftime('%b %d')}. Red BREAKING badge in corner. Modern, clean, eye-catching. No people no faces. 16:9 aspect ratio."

print("--- Generating thumbnail ---")
generated = False

# 1. Try OpenAI DALL-E
if OPENAI_KEY and not generated:
    print("  Trying OpenAI DALL-E...")
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=json.dumps({"model": "dall-e-3", "prompt": PROMPT, "n": 1, "size": "1792x1024", "quality": "hd"}).encode(),
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        img_url = result['data'][0]['url']
        img_resp = urllib.request.urlopen(img_url)
        with open(THUMB_PATH, 'wb') as f:
            f.write(img_resp.read())
        print(f"  ✓ DALL-E: {os.path.getsize(THUMB_PATH)/1024:.0f} KB")
        generated = True
    except Exception as e:
        print(f"  ✗ DALL-E failed: {str(e)[:80]}")

# 2. Try Gemini
if GEMINI_KEY and not generated:
    print("  Trying Gemini...")
    try:
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_KEY}",
            data=json.dumps({
                "contents": [{"parts": [{"text": f"Generate an image: {PROMPT}"}]}],
                "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
            }).encode(),
            headers={"Content-Type": "application/json"}
        )
        resp = urllib.request.urlopen(req, timeout=90)
        result = json.loads(resp.read())
        for part in result.get('candidates', [{}])[0].get('content', {}).get('parts', []):
            if 'inlineData' in part:
                with open(THUMB_PATH, 'wb') as f:
                    f.write(base64.b64decode(part['inlineData']['data']))
                print(f"  ✓ Gemini: {os.path.getsize(THUMB_PATH)/1024:.0f} KB")
                generated = True
                break
        if not generated:
            print("  ✗ Gemini returned no image")
    except Exception as e:
        print(f"  ✗ Gemini failed: {str(e)[:80]}")

# 3. Fallback to Pillow
if not generated:
    print("  Falling back to Pillow...")
    import subprocess
    env = os.environ.copy()
    env['THUMB_PATH'] = THUMB_PATH
    env['HEADLINE'] = f"AI News {TODAY.strftime('%b %d, %Y')}"
    env['PYTHONPATH'] = '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages'
    result = subprocess.run(
        ['python3', '/Users/franzccm/projects/ex-venture-platform/scripts/generate_thumbnail.py'],
        capture_output=True, text=True, env=env
    )
    if os.path.exists(THUMB_PATH) and os.path.getsize(THUMB_PATH) > 1000:
        print(f"  ✓ Pillow: {os.path.getsize(THUMB_PATH)/1024:.0f} KB")
    else:
        print(f"  ✗ All methods failed")
