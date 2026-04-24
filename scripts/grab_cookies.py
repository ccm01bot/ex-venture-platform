#!/usr/bin/env python3
"""
Grab NotebookLM cookies from a running Chrome via remote debugging.

Step 1: Relaunch Chrome with --remote-debugging-port=9222
Step 2: This script connects and pulls cookies
"""

import json
import os
import sys
import urllib.request

CDP_URL = "http://127.0.0.1:9222"
STORAGE_FILE = os.path.expanduser("~/.notebooklm/storage_state.json")
os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)

# Connect to Chrome DevTools Protocol
try:
    resp = urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=5)
    info = json.loads(resp.read())
    ws_url = info["webSocketDebuggerUrl"]
    print(f"✓ Connected to Chrome: {info.get('Browser', 'unknown')}")
except Exception as e:
    print(f"✗ Cannot connect to Chrome on port 9222: {e}")
    print("\nChrome needs to be launched with remote debugging.")
    print("Close Chrome completely, then run:")
    print('  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 &')
    print("\nThen run this script again.")
    sys.exit(1)

# Use CDP HTTP endpoint to get cookies
import websocket  # type: ignore

ws = websocket.create_connection(ws_url)

# Get all cookies for google.com domains
ws.send(json.dumps({
    "id": 1,
    "method": "Network.getAllCookies"
}))

result = json.loads(ws.recv())
all_cookies = result.get("result", {}).get("cookies", [])
ws.close()

# Filter for Google/NotebookLM cookies
google_cookies = [
    c for c in all_cookies
    if any(d in c.get("domain", "") for d in [
        "google.com", "googleapis.com", "youtube.com",
        "gstatic.com", "doubleclick.net"
    ])
]

print(f"✓ Total cookies: {len(all_cookies)}")
print(f"✓ Google cookies: {len(google_cookies)}")

# Convert to Playwright storage_state format
pw_cookies = []
for c in google_cookies:
    sameSite_map = {"Strict": "Strict", "Lax": "Lax", "None": "None"}
    pw_cookies.append({
        "name": c["name"],
        "value": c["value"],
        "domain": c["domain"],
        "path": c.get("path", "/"),
        "expires": c.get("expires", -1),
        "httpOnly": c.get("httpOnly", False),
        "secure": c.get("secure", False),
        "sameSite": sameSite_map.get(c.get("sameSite", "None"), "None"),
    })

storage_state = {
    "cookies": pw_cookies,
    "origins": [
        {
            "origin": "https://notebooklm.google.com",
            "localStorage": []
        }
    ]
}

with open(STORAGE_FILE, 'w') as f:
    json.dump(storage_state, f, indent=2)

print(f"\n✓ Saved {len(pw_cookies)} cookies to {STORAGE_FILE}")
print("✓ NotebookLM CLI should now be authenticated!")
print("\nTest with: notebooklm list")
