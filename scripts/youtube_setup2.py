#!/usr/bin/env python3
"""YouTube OAuth setup — opens browser manually."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
import subprocess
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
CREDS_DIR = os.path.expanduser('~/.youtube-exai')
TOKEN_FILE = os.path.join(CREDS_DIR, 'token.json')
CLIENT_SECRET_FILE = os.path.join(CREDS_DIR, 'client_secret.json')

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)

# Generate the auth URL and open it manually
flow.redirect_uri = 'http://localhost:8080/'
auth_url, _ = flow.authorization_url(prompt='consent')

print(f"\nOpening browser to:\n{auth_url}\n")
subprocess.run(['open', auth_url])

# Start local server to catch the redirect
credentials = flow.run_local_server(port=8080, open_browser=False, prompt='consent')

token_data = {
    'token': credentials.token,
    'refresh_token': credentials.refresh_token,
    'token_uri': credentials.token_uri,
    'client_id': credentials.client_id,
    'client_secret': credentials.client_secret,
    'scopes': list(credentials.scopes),
}
with open(TOKEN_FILE, 'w') as f:
    json.dump(token_data, f, indent=2)

print(f"\n✓ Token saved to {TOKEN_FILE}")

from googleapiclient.discovery import build
youtube = build('youtube', 'v3', credentials=credentials)
request = youtube.channels().list(part='snippet', mine=True)
response = request.execute()
for channel in response.get('items', []):
    print(f"✓ Connected to: {channel['snippet']['title']}")
