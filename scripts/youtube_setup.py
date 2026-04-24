#!/usr/bin/env python3
"""One-time YouTube OAuth setup. Run this interactively to authorize."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube']
CREDS_DIR = os.path.expanduser('~/.youtube-exai')
TOKEN_FILE = os.path.join(CREDS_DIR, 'token.json')
CLIENT_SECRET_FILE = os.path.join(CREDS_DIR, 'client_secret.json')

os.makedirs(CREDS_DIR, exist_ok=True)

print("=== YouTube API Setup for EXAI Global ===\n")

if not os.path.exists(CLIENT_SECRET_FILE):
    print("You need OAuth client credentials from Google Cloud Console.")
    print("\nSteps:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a project (or select existing)")
    print("3. Enable 'YouTube Data API v3'")
    print("4. Go to Credentials → Create Credentials → OAuth client ID")
    print("5. Application type: Desktop app")
    print("6. Download the JSON file")
    print(f"7. Save it as: {CLIENT_SECRET_FILE}")
    print("\nThen run this script again.")
    sys.exit(1)

# Run OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
credentials = flow.run_local_server(port=8080, prompt='consent')

# Save token
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

# Verify by listing channels
youtube = build('youtube', 'v3', credentials=credentials)
request = youtube.channels().list(part='snippet', mine=True)
response = request.execute()
for channel in response.get('items', []):
    print(f"✓ Connected to channel: {channel['snippet']['title']} (ID: {channel['id']})")
