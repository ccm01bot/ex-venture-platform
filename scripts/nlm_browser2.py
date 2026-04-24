#!/usr/bin/env python3
"""Drive NotebookLM through the logged-in browser - handles the source modal."""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import json
import time
import os
import urllib.request
from playwright.sync_api import sync_playwright

BRIEF_FILE = "/tmp/morningbrief/brief_2026-04-14.md"
SLACK_WEBHOOK = "SLACK_WEBHOOK_PLACEHOLDER"

with open(BRIEF_FILE) as f:
    brief_text = f.read()

print("=== NotebookLM Video Pipeline ===\n")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    print("✓ Connected to browser")

    context = browser.contexts[0]

    # Find the NotebookLM page with the notebook we just created
    nlm_page = None
    for page in context.pages:
        if "notebooklm" in page.url:
            nlm_page = page
            break

    if not nlm_page:
        print("✗ No NotebookLM page found")
        sys.exit(1)

    print(f"✓ Page: {nlm_page.url}")
    nlm_page.screenshot(path="/tmp/morningbrief/current_state.png")

    # The modal is open with "Copied text" button visible
    # Click "Copied text" in the modal
    print("\n--- Adding source via 'Copied text' ---")

    try:
        # Click the "Copied text" button in the modal
        copied_btn = nlm_page.wait_for_selector('button:has-text("Copied text")', timeout=5000)
        if copied_btn:
            copied_btn.click()
            print("  ✓ Clicked 'Copied text'")
            time.sleep(2)
    except:
        # Modal might be closed, try reopening
        print("  Modal not found, clicking Add sources...")
        # Close any overlay first
        try:
            close_btn = nlm_page.query_selector('button[aria-label="Close"]')
            if close_btn:
                close_btn.click()
                time.sleep(1)
        except:
            pass
        # Press Escape to close any modal
        nlm_page.keyboard.press("Escape")
        time.sleep(1)

        # Click Add sources
        add_btn = nlm_page.wait_for_selector('button:has-text("Add sources")', timeout=5000)
        if add_btn:
            add_btn.click()
            time.sleep(2)

        copied_btn = nlm_page.wait_for_selector('button:has-text("Copied text")', timeout=5000)
        if copied_btn:
            copied_btn.click()
            print("  ✓ Clicked 'Copied text'")
            time.sleep(2)

    nlm_page.screenshot(path="/tmp/morningbrief/step_paste_dialog.png")

    # Now we should see a text input area - find and fill it
    print("  Looking for text input...")

    textarea = None
    for selector in [
        'textarea',
        'div[contenteditable="true"]',
        'div[role="textbox"]',
        '.source-text-input textarea',
        'mat-dialog-container textarea',
    ]:
        try:
            el = nlm_page.wait_for_selector(selector, timeout=3000)
            if el and el.is_visible():
                textarea = el
                print(f"  Found textarea: {selector}")
                break
        except:
            continue

    if textarea:
        textarea.click()
        # Use fill for textarea, type for contenteditable
        try:
            textarea.fill(brief_text)
        except:
            textarea.type(brief_text, delay=1)
        print("  ✓ Pasted morningbrief text")
        time.sleep(1)

        # Set title if field exists
        for selector in ['input[placeholder*="itle"]', 'input[placeholder*="ource"]', 'input[aria-label*="itle"]']:
            try:
                title_el = nlm_page.wait_for_selector(selector, timeout=2000)
                if title_el and title_el.is_visible():
                    title_el.fill("AI Morning Brief — April 14, 2026")
                    print("  ✓ Set title")
                    break
            except:
                continue

        nlm_page.screenshot(path="/tmp/morningbrief/step_text_filled.png")

        # Click Insert/Add button
        for selector in [
            'button:has-text("Insert")',
            'button:has-text("Add source")',
            'button:has-text("Save")',
            'button:has-text("Submit")',
        ]:
            try:
                btn = nlm_page.wait_for_selector(selector, timeout=3000)
                if btn and btn.is_visible() and btn.is_enabled():
                    btn.click()
                    print(f"  ✓ Clicked '{selector}'")
                    break
            except:
                continue

        time.sleep(5)
        print("  ✓ Source added!")
    else:
        print("  ✗ Could not find text area")
        nlm_page.screenshot(path="/tmp/morningbrief/step_no_textarea.png")

    nlm_page.screenshot(path="/tmp/morningbrief/step_after_source.png")

    # Step 3: Wait for source processing, then generate Audio Overview
    print("\n--- Generating Audio Overview ---")
    time.sleep(5)

    # Look in the Studio panel on the right for Audio Overview
    # First close any remaining modals
    nlm_page.keyboard.press("Escape")
    time.sleep(1)

    nlm_page.screenshot(path="/tmp/morningbrief/step_before_generate.png")

    # The Studio panel should show "Audio Overview" section
    generate_clicked = False
    for selector in [
        'button:has-text("Generate")',
        'button:has-text("Audio Overview")',
        ':text("Audio Overview")',
        'button:has-text("Deep Dive")',
        '[aria-label*="Audio"]',
        '[aria-label*="Generate"]',
    ]:
        try:
            el = nlm_page.wait_for_selector(selector, timeout=3000)
            if el and el.is_visible():
                el.click()
                print(f"  ✓ Clicked: {selector}")
                generate_clicked = True
                time.sleep(2)
                break
        except:
            continue

    if not generate_clicked:
        # Try scrolling the Studio panel to find it
        print("  Looking in Studio panel...")
        try:
            studio = nlm_page.query_selector('text=Studio')
            if studio:
                studio.scroll_into_view_if_needed()
        except:
            pass

    nlm_page.screenshot(path="/tmp/morningbrief/step_generate_clicked.png")

    # Confirm generation if dialog appears
    time.sleep(2)
    for selector in [
        'button:has-text("Generate")',
        'button:has-text("Create")',
        'button:has-text("Start")',
        'button:has-text("OK")',
    ]:
        try:
            btn = nlm_page.wait_for_selector(selector, timeout=3000)
            if btn and btn.is_visible():
                btn.click()
                print(f"  ✓ Confirmed: {selector}")
                break
        except:
            continue

    # Wait for generation
    print("  ⏳ Waiting for audio generation (this takes a few minutes)...")
    generated = False
    for i in range(60):  # Up to 10 minutes
        time.sleep(10)

        if i % 3 == 0:
            nlm_page.screenshot(path=f"/tmp/morningbrief/progress_{i}.png")

        # Check if play button or audio element appeared
        for selector in [
            'button[aria-label*="Play"]',
            'audio',
            'button:has-text("Play")',
            '[aria-label*="play"]',
            'button:has-text("Share audio")',
        ]:
            try:
                el = nlm_page.query_selector(selector)
                if el and el.is_visible():
                    generated = True
                    print(f"  ✓ Audio generated! ({(i+1)*10}s)")
                    break
            except:
                pass

        if generated:
            break

        if i % 6 == 0 and i > 0:
            print(f"  Still generating... ({(i+1)*10}s)")

    nlm_page.screenshot(path="/tmp/morningbrief/step_generated.png")

    # Step 4: Get the share link for the notebook
    print("\n--- Getting share link ---")

    notebook_url = nlm_page.url

    # Try to enable sharing
    for selector in [
        'button[aria-label="Share"]',
        'button:has-text("Share")',
        '[aria-label*="share"]',
    ]:
        try:
            el = nlm_page.wait_for_selector(selector, timeout=3000)
            if el and el.is_visible():
                el.click()
                time.sleep(2)
                nlm_page.screenshot(path="/tmp/morningbrief/step_share_dialog.png")

                # Enable public access
                for toggle in [
                    ':text("Anyone with the link")',
                    'button:has-text("Anyone")',
                    '[role="switch"]',
                ]:
                    try:
                        t = nlm_page.wait_for_selector(toggle, timeout=2000)
                        if t and t.is_visible():
                            t.click()
                            time.sleep(1)
                            break
                    except:
                        continue

                # Copy link
                for copy_sel in ['button:has-text("Copy link")', 'button:has-text("Copy")']:
                    try:
                        c = nlm_page.wait_for_selector(copy_sel, timeout=2000)
                        if c and c.is_visible():
                            c.click()
                            time.sleep(1)
                            break
                    except:
                        continue

                nlm_page.keyboard.press("Escape")
                break
        except:
            continue

    print(f"  Notebook URL: {notebook_url}")

    # Step 5: Post to Slack
    print("\n--- Posting to Slack ---")

    slack_msg = (
        "*:tv: AI Morning Brief — Video Edition*\n"
        "*Monday, April 14, 2026*\n\n"
        ":rotating_light: Your daily AI intelligence briefing is ready!\n\n"
        f":point_right: *Open the full briefing:* {notebook_url}\n\n"
        "_Open the link → click 'Audio Overview' to listen to the podcast-style summary._\n\n"
        "---\n"
        "_Compiled by ExVenture AI Research Team | Next brief: tomorrow 11:00am_"
    )

    data = json.dumps({"text": slack_msg}).encode()
    req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    print(f"  ✓ Posted to Slack: {resp.read().decode()}")

    print("\n=== Pipeline complete! ===")
    print(f"Notebook: {notebook_url}")

    browser.close()
