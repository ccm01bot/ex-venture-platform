#!/usr/bin/env python3
"""
A/B Test Rotation for YouTube videos.
Runs every 12 hours after upload. Swaps title and thumbnail, tracks performance.
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import glob
import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_FILE = os.path.expanduser('~/.youtube-exai/token.json')
TODAY = datetime.date.today().strftime("%Y-%m-%d")

# Find the most recent A/B test file
ab_files = sorted(glob.glob("/tmp/morningbrief/ab_test_*.json"), reverse=True)
if not ab_files:
    print("No A/B test data found.")
    sys.exit(0)

ab_file = ab_files[0]
with open(ab_file) as f:
    ab = json.load(f)

video_url_file = f"/tmp/morningbrief/youtube_{ab['video_date']}.txt"
if not os.path.exists(video_url_file):
    print(f"No YouTube URL found for {ab['video_date']}")
    sys.exit(0)

with open(video_url_file) as f:
    video_url = f.read().strip()
video_id = video_url.split('/')[-1]

# Load YouTube API
with open(TOKEN_FILE) as f:
    t = json.load(f)

creds = Credentials(
    token=t['token'], refresh_token=t['refresh_token'],
    token_uri=t['token_uri'], client_id=t['client_id'],
    client_secret=t['client_secret'], scopes=t.get('scopes', [])
)
if creds.expired:
    creds.refresh(Request())
    t['token'] = creds.token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(t, f, indent=2)

youtube = build('youtube', 'v3', credentials=creds)

# Get current video stats
stats = youtube.videos().list(part='statistics,snippet', id=video_id).execute()
if not stats.get('items'):
    print(f"Video {video_id} not found")
    sys.exit(1)

video = stats['items'][0]
current_title = video['snippet']['title']
views = int(video['statistics'].get('viewCount', 0))
likes = int(video['statistics'].get('likeCount', 0))
ctr_proxy = likes / max(views, 1)  # likes/views as CTR proxy

print(f"Video: {video_id}")
print(f"Current title: {current_title}")
print(f"Views: {views} | Likes: {likes} | Like ratio: {ctr_proxy:.2%}")

# Log current performance
rotation = {
    "timestamp": datetime.datetime.now().isoformat(),
    "title_index": ab.get('current_title_index', 0),
    "thumb_index": ab.get('current_thumb_index', 0),
    "views": views,
    "likes": likes,
}
ab.setdefault('rotations', []).append(rotation)

# Rotate to next title
titles = ab.get('titles', [])
thumbs = ab.get('thumbnails', [])
next_title_idx = (ab.get('current_title_index', 0) + 1) % max(len(titles), 1)
next_thumb_idx = (ab.get('current_thumb_index', 0) + 1) % max(len(thumbs), 1)

changed = False

# Swap title if we have alternatives
if len(titles) > 1 and next_title_idx != ab.get('current_title_index', 0):
    new_title = titles[next_title_idx]
    if len(new_title) > 100:
        new_title = new_title[:97] + "..."
    youtube.videos().update(
        part='snippet',
        body={
            'id': video_id,
            'snippet': {
                'title': new_title,
                'categoryId': video['snippet']['categoryId'],
                'description': video['snippet']['description'],
                'tags': video['snippet'].get('tags', []),
            }
        }
    ).execute()
    ab['current_title_index'] = next_title_idx
    print(f"✓ Title rotated to #{next_title_idx + 1}: {new_title}")
    changed = True

# Swap thumbnail if we have alternatives
if len(thumbs) > 1 and next_thumb_idx != ab.get('current_thumb_index', 0):
    thumb_path = thumbs[next_thumb_idx]
    if os.path.exists(thumb_path):
        try:
            media = MediaFileUpload(thumb_path, mimetype='image/png')
            youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
            ab['current_thumb_index'] = next_thumb_idx
            print(f"✓ Thumbnail rotated to #{next_thumb_idx + 1}")
            changed = True
        except Exception as e:
            print(f"✗ Thumbnail rotation failed: {str(e)[:80]}")

if not changed:
    print("No rotation needed (single title/thumbnail)")

# Check if we have enough data to pick a winner
if len(ab.get('rotations', [])) >= 4:  # 2 full rotations
    print("\n--- A/B Test Results ---")
    for i, rot in enumerate(ab['rotations']):
        print(f"  Round {i+1}: Title #{rot['title_index']+1} | Thumb #{rot['thumb_index']+1} | Views: {rot['views']} | Likes: {rot['likes']}")

    # Find best performing title by views gained per rotation
    if len(ab['rotations']) >= 4:
        best_title = 0
        best_views = 0
        for i in range(1, len(ab['rotations'])):
            delta = ab['rotations'][i]['views'] - ab['rotations'][i-1]['views']
            tidx = ab['rotations'][i]['title_index']
            if delta > best_views:
                best_views = delta
                best_title = tidx
        print(f"\n  Best title: #{best_title+1} — {titles[best_title]}")
        print(f"  Recommendation: Lock in title #{best_title+1}")

# Save updated data
with open(ab_file, 'w') as f:
    json.dump(ab, f, indent=2)

print("\nDone.")
