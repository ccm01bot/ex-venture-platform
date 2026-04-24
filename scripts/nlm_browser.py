#!/usr/bin/env python3
"""
Drive NotebookLM directly through the user's logged-in browser via CDP.
No cookies needed — just controls the open browser.
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import json
import time
import os
from playwright.sync_api import sync_playwright

BRIEF_FILE = "/tmp/morningbrief/brief_2026-04-14.md"
SLACK_WEBHOOK = "SLACK_WEBHOOK_PLACEHOLDER"

# Read the morningbrief
with open(BRIEF_FILE) as f:
    brief_text = f.read()

print("=== NotebookLM Video Pipeline (Browser Automation) ===\n")

with sync_playwright() as p:
    # Connect to the already-open Chrome
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    print("✓ Connected to your browser")

    # Get existing context and pages
    context = browser.contexts[0]
    pages = context.pages

    # Find or create a NotebookLM page
    nlm_page = None
    for page in pages:
        if "notebooklm" in page.url:
            nlm_page = page
            break

    if not nlm_page:
        nlm_page = context.new_page()
        nlm_page.goto("https://notebooklm.google.com/", wait_until="networkidle", timeout=30000)

    print(f"✓ On page: {nlm_page.url}")
    print(f"✓ Title: {nlm_page.title()}")

    # Step 1: Create a new notebook
    print("\n--- Step 1: Creating new notebook ---")
    time.sleep(2)

    # Look for "New notebook" or "Create" button
    nlm_page.screenshot(path="/tmp/morningbrief/step0_homepage.png")

    # Try clicking "New notebook" or the create button
    create_btn = None
    for selector in [
        'button:has-text("New notebook")',
        'button:has-text("Create new")',
        'button:has-text("Create")',
        '[aria-label*="New"]',
        '[aria-label*="Create"]',
        'button:has-text("new")',
        '.create-notebook-button',
        'a:has-text("New notebook")',
    ]:
        try:
            el = nlm_page.wait_for_selector(selector, timeout=3000)
            if el and el.is_visible():
                create_btn = el
                print(f"  Found button: {selector}")
                break
        except:
            continue

    if create_btn:
        create_btn.click()
        time.sleep(3)
        print("  ✓ Clicked create notebook")
    else:
        # Try using the + button or fab
        print("  Looking for + button...")
        nlm_page.screenshot(path="/tmp/morningbrief/step0_no_button.png")
        # Try keyboard shortcut or direct navigation
        try:
            # Some versions use a direct URL pattern
            nlm_page.goto("https://notebooklm.google.com/notebook/new", wait_until="networkidle", timeout=15000)
            time.sleep(2)
            print("  ✓ Navigated to new notebook")
        except:
            print("  ✗ Could not find create button. Taking screenshot for debug.")

    nlm_page.screenshot(path="/tmp/morningbrief/step1_notebook.png")
    print(f"  Current URL: {nlm_page.url}")

    # Step 2: Add source with the morningbrief text
    print("\n--- Step 2: Adding morningbrief as source ---")
    time.sleep(2)

    # Look for "Add source" or paste text option
    add_source = None
    for selector in [
        'button:has-text("Add source")',
        'button:has-text("Add")',
        'button:has-text("Upload")',
        '[aria-label*="Add source"]',
        '[aria-label*="add source"]',
        'button:has-text("source")',
        ':text("Paste text")',
        'button:has-text("paste")',
    ]:
        try:
            el = nlm_page.wait_for_selector(selector, timeout=3000)
            if el and el.is_visible():
                add_source = el
                print(f"  Found: {selector}")
                break
        except:
            continue

    if add_source:
        add_source.click()
        time.sleep(2)
        nlm_page.screenshot(path="/tmp/morningbrief/step2a_add_source.png")

        # Look for "Copied text" or "Paste text" option
        paste_opt = None
        for selector in [
            ':text("Copied text")',
            ':text("Paste text")',
            ':text("Text")',
            'button:has-text("Copied text")',
            'button:has-text("paste")',
            'button:has-text("Text")',
            '[data-source-type="text"]',
        ]:
            try:
                el = nlm_page.wait_for_selector(selector, timeout=3000)
                if el and el.is_visible():
                    paste_opt = el
                    print(f"  Found paste option: {selector}")
                    break
            except:
                continue

        if paste_opt:
            paste_opt.click()
            time.sleep(2)

            # Find the text input area and paste the brief
            textarea = None
            for selector in ['textarea', '[contenteditable="true"]', 'div[role="textbox"]', '.text-input', 'input[type="text"]']:
                try:
                    el = nlm_page.wait_for_selector(selector, timeout=3000)
                    if el and el.is_visible():
                        textarea = el
                        break
                except:
                    continue

            if textarea:
                textarea.click()
                textarea.fill(brief_text)
                print("  ✓ Pasted morningbrief text")
                time.sleep(1)

                # Look for title field
                for selector in ['input[placeholder*="title"]', 'input[placeholder*="Title"]', 'input[placeholder*="name"]', 'input[aria-label*="title"]']:
                    try:
                        title_el = nlm_page.wait_for_selector(selector, timeout=2000)
                        if title_el and title_el.is_visible():
                            title_el.fill("AI Morning Brief — April 14, 2026")
                            print("  ✓ Set title")
                            break
                    except:
                        continue

                # Click Insert/Add/Save button
                for selector in [
                    'button:has-text("Insert")',
                    'button:has-text("Add")',
                    'button:has-text("Save")',
                    'button:has-text("Submit")',
                    'button[type="submit"]',
                ]:
                    try:
                        btn = nlm_page.wait_for_selector(selector, timeout=3000)
                        if btn and btn.is_visible():
                            btn.click()
                            print(f"  ✓ Clicked: {selector}")
                            break
                    except:
                        continue

                time.sleep(5)
                print("  ✓ Source added")
            else:
                print("  ✗ Could not find text input")
        else:
            print("  ✗ Could not find paste text option")
    else:
        print("  ✗ Could not find add source button")

    nlm_page.screenshot(path="/tmp/morningbrief/step2_source_added.png")

    # Step 3: Generate video/audio overview
    print("\n--- Step 3: Generating overview ---")
    time.sleep(3)

    # Look for Audio Overview or Generate button
    generate_btn = None
    for selector in [
        'button:has-text("Generate")',
        'button:has-text("Audio Overview")',
        'button:has-text("Video")',
        ':text("Audio Overview")',
        ':text("Generate audio")',
        '[aria-label*="Generate"]',
        '[aria-label*="Audio"]',
        'button:has-text("overview")',
    ]:
        try:
            el = nlm_page.wait_for_selector(selector, timeout=3000)
            if el and el.is_visible():
                generate_btn = el
                print(f"  Found: {selector}")
                break
        except:
            continue

    if generate_btn:
        generate_btn.click()
        time.sleep(2)
        nlm_page.screenshot(path="/tmp/morningbrief/step3a_generate.png")

        # If there's a confirm/generate dialog
        for selector in [
            'button:has-text("Generate")',
            'button:has-text("Create")',
            'button:has-text("Start")',
        ]:
            try:
                btn = nlm_page.wait_for_selector(selector, timeout=3000)
                if btn and btn.is_visible():
                    btn.click()
                    print(f"  ✓ Confirmed: {selector}")
                    break
            except:
                continue

        print("  ⏳ Waiting for generation (this can take a few minutes)...")

        # Wait for generation to complete (poll for up to 10 minutes)
        for i in range(60):
            time.sleep(10)
            nlm_page.screenshot(path=f"/tmp/morningbrief/step3_progress_{i}.png")

            # Check if a play button or download link appeared
            try:
                done = nlm_page.query_selector('button:has-text("Play")') or \
                       nlm_page.query_selector('[aria-label*="Play"]') or \
                       nlm_page.query_selector('audio') or \
                       nlm_page.query_selector('video') or \
                       nlm_page.query_selector('button:has-text("Download")') or \
                       nlm_page.query_selector('a:has-text("Download")')
                if done:
                    print(f"  ✓ Generation complete! ({(i+1)*10}s)")
                    break
            except:
                pass

            if i % 6 == 0 and i > 0:
                print(f"  Still generating... ({(i+1)*10}s)")
    else:
        print("  ✗ Could not find generate button")

    nlm_page.screenshot(path="/tmp/morningbrief/step3_final.png")

    # Step 4: Get shareable link
    print("\n--- Step 4: Getting share link ---")

    share_link = nlm_page.url

    for selector in [
        'button:has-text("Share")',
        '[aria-label*="Share"]',
        'button:has-text("share")',
    ]:
        try:
            el = nlm_page.wait_for_selector(selector, timeout=3000)
            if el and el.is_visible():
                el.click()
                time.sleep(2)
                # Enable public sharing if possible
                for toggle in ['button:has-text("Anyone with the link")', 'input[type="checkbox"]', '[role="switch"]']:
                    try:
                        t = nlm_page.wait_for_selector(toggle, timeout=2000)
                        if t and t.is_visible():
                            t.click()
                            time.sleep(1)
                            break
                    except:
                        continue
                # Copy link
                for copy_btn in ['button:has-text("Copy link")', 'button:has-text("Copy")']:
                    try:
                        c = nlm_page.wait_for_selector(copy_btn, timeout=2000)
                        if c and c.is_visible():
                            c.click()
                            time.sleep(1)
                            break
                    except:
                        continue
                break
        except:
            continue

    share_link = nlm_page.url
    print(f"  Link: {share_link}")

    nlm_page.screenshot(path="/tmp/morningbrief/step4_share.png")

    # Save the link
    with open("/tmp/morningbrief/share_link.txt", "w") as f:
        f.write(share_link)

    print(f"\n✓ Pipeline complete!")
    print(f"  Screenshots saved to /tmp/morningbrief/")
    print(f"  Share link: {share_link}")

    # Don't close the browser - user is still using it
    browser.close()
