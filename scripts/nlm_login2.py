#!/usr/bin/env python3
"""NotebookLM login - uses Playwright Chromium with explicit path."""

import sys
import os
import json
import time

sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

from playwright.sync_api import sync_playwright

CHROME_PATH = "/Users/franzccm/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
STORAGE_DIR = os.path.expanduser("~/.notebooklm")
STORAGE_FILE = os.path.join(STORAGE_DIR, "storage_state.json")

os.makedirs(STORAGE_DIR, exist_ok=True)

print("Launching Chrome for Testing...")
print(f"Executable: {CHROME_PATH}")
print(f"Exists: {os.path.exists(CHROME_PATH)}")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        executable_path=CHROME_PATH,
        args=["--no-sandbox", "--disable-gpu"],
    )
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()

    page.goto("https://notebooklm.google.com/", timeout=30000)
    print("\n✓ Browser opened! Navigate to NotebookLM and log in.")
    print("Polling for login state...\n")

    max_wait = 300
    start = time.time()
    logged_in = False

    while time.time() - start < max_wait:
        try:
            url = page.url
            title = page.title()
            elapsed = int(time.time() - start)

            if elapsed % 15 == 0 and elapsed > 0:
                print(f"  [{elapsed}s] URL: {url[:80]} | Title: {title[:40]}")

            # Detect successful login - user is on the NotebookLM app
            if "notebooklm.google.com" in url:
                # Check if we're past the login screen
                if any(x in url for x in ["/notebook", "/n/"]):
                    logged_in = True
                    break
                # Check page content for logged-in indicators
                content = page.content()
                if "Create new" in content or "New notebook" in content or "Sources" in content:
                    logged_in = True
                    break
        except Exception as e:
            print(f"  Check error: {e}")
        time.sleep(3)

    # Final fallback check
    if not logged_in and "notebooklm.google.com" in page.url and "accounts.google" not in page.url:
        logged_in = True

    if logged_in:
        time.sleep(3)
        context.storage_state(path=STORAGE_FILE)
        print(f"\n✓ Login detected! Cookies saved to {STORAGE_FILE}")
        with open(STORAGE_FILE) as f:
            data = json.load(f)
        print(f"✓ {len(data.get('cookies', []))} cookies saved")
    else:
        print("\n✗ Timed out. Try again.")

    browser.close()
    print("Done.")
