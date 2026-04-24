#!/usr/bin/env python3
"""YouTube OAuth setup — simple version."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
CLIENT_SECRET = os.path.expanduser('~/.youtube-exai/client_secret.json')
TOKEN_FILE = os.path.expanduser('~/.youtube-exai/token.json')

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
credentials = flow.run_local_server(port=8080, open_browser=True)

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

youtube = build('youtube', 'v3', credentials=credentials)
resp = youtube.channels().list(part='snippet', mine=True).execute()
for ch in resp.get('items', []):
    print(f"Connected to: {ch['snippet']['title']}")
print("Done!")
