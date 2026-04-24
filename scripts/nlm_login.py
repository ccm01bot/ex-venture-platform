#!/usr/bin/env python3
"""NotebookLM login via Playwright - keeps browser open until auth is saved."""

import sys
import os
import json
import time

# Add playwright to path
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

from playwright.sync_api import sync_playwright

STORAGE_DIR = os.path.expanduser("~/.notebooklm")
STORAGE_FILE = os.path.join(STORAGE_DIR, "storage_state.json")
PROFILE_DIR = os.path.join(STORAGE_DIR, "browser_profile")

os.makedirs(STORAGE_DIR, exist_ok=True)

print("Launching browser for NotebookLM login...")
print("Log in with your Google account, then wait for this script to detect it.\n")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        slow_mo=500,
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
    )
    page = context.new_page()

    # Navigate to NotebookLM
    page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
    print("Browser opened. Please log in with your entradeceo Google account.")
    print("Waiting for NotebookLM to load after login...\n")

    # Poll until we detect the user is logged in (NotebookLM homepage loaded)
    max_wait = 300  # 5 minutes
    start = time.time()
    logged_in = False

    while time.time() - start < max_wait:
        try:
            url = page.url
            # NotebookLM redirects to the main app after login
            if "notebooklm.google.com" in url and "/notebook" in url.lower():
                logged_in = True
                break
            # Check for the main app UI elements
            if page.query_selector('[data-notebook-list]') or \
               page.query_selector('button[aria-label*="Create"]') or \
               page.query_selector('button[aria-label*="New"]') or \
               page.query_selector('[class*="notebook"]'):
                logged_in = True
                break
            # Check title
            title = page.title()
            if "NotebookLM" in title and "Sign in" not in title:
                # Wait a bit more to ensure cookies are set
                time.sleep(3)
                logged_in = True
                break
        except Exception:
            pass
        time.sleep(2)
        elapsed = int(time.time() - start)
        if elapsed % 10 == 0:
            print(f"  Waiting... ({elapsed}s elapsed, url: {page.url[:60]})")

    if not logged_in:
        # Last chance - check if we're on any notebooklm page
        if "notebooklm.google.com" in page.url:
            logged_in = True

    if logged_in:
        # Save storage state (cookies + local storage)
        time.sleep(2)  # Let cookies settle
        context.storage_state(path=STORAGE_FILE)
        print(f"\n✓ Login successful! Storage state saved to: {STORAGE_FILE}")

        # Verify the file
        if os.path.exists(STORAGE_FILE):
            size = os.path.getsize(STORAGE_FILE)
            print(f"✓ Storage file size: {size} bytes")
            with open(STORAGE_FILE) as f:
                data = json.load(f)
            cookies = len(data.get("cookies", []))
            print(f"✓ Cookies saved: {cookies}")
        else:
            print("✗ Storage file not found after save!")
    else:
        print("\n✗ Timed out waiting for login. Please try again.")

    browser.close()

print("\nDone. You can now use notebooklm CLI commands.")
