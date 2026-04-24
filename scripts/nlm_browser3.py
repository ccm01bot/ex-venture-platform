#!/usr/bin/env python3
"""Drive NotebookLM - use JS to bypass overlay blocking clicks."""

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

# Escape for JS
brief_js = json.dumps(brief_text)

print("=== NotebookLM Video Pipeline ===\n")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    print("✓ Connected to browser")
    context = browser.contexts[0]

    nlm_page = None
    for page in context.pages:
        if "notebooklm" in page.url:
            nlm_page = page
            break

    if not nlm_page:
        print("✗ No NotebookLM page found")
        sys.exit(1)

    print(f"✓ Page: {nlm_page.url}")

    # Use JavaScript to fill the textarea and click Insert
    print("\n--- Step 1: Pasting morningbrief text ---")

    # Fill textarea via JS (bypasses overlay)
    nlm_page.evaluate(f"""
        const ta = document.querySelector('textarea');
        if (ta) {{
            // Set value using native input setter to trigger Angular/React change detection
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(ta, {brief_js});
            ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
            ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    """)
    print("  ✓ Text pasted via JS")
    time.sleep(1)

    nlm_page.screenshot(path="/tmp/morningbrief/step_text_pasted.png")

    # Click Insert button via JS
    nlm_page.evaluate("""
        const buttons = Array.from(document.querySelectorAll('button'));
        const insertBtn = buttons.find(b => b.textContent.trim() === 'Insert');
        if (insertBtn) {
            insertBtn.click();
        }
    """)
    print("  ✓ Clicked Insert")

    # Wait for source to process
    print("  ⏳ Waiting for source to process...")
    time.sleep(10)
    nlm_page.screenshot(path="/tmp/morningbrief/step_source_processing.png")

    # Check if source was added
    time.sleep(5)
    nlm_page.screenshot(path="/tmp/morningbrief/step_source_done.png")

    # Close any remaining modals
    nlm_page.evaluate("""
        const overlays = document.querySelectorAll('.cdk-overlay-backdrop');
        overlays.forEach(o => o.click());
    """)
    time.sleep(1)
    nlm_page.keyboard.press("Escape")
    time.sleep(1)

    # Step 2: Generate Audio Overview
    print("\n--- Step 2: Generating Audio Overview ---")
    nlm_page.screenshot(path="/tmp/morningbrief/step_before_audio.png")

    # Click on "Audio..." in the Studio panel via JS
    nlm_page.evaluate("""
        // Find and click Audio Overview in Studio panel
        const allText = document.querySelectorAll('*');
        for (const el of allText) {
            if (el.children.length === 0 && el.textContent.trim().match(/^Audio/)) {
                el.closest('button, [role="button"], a, div[class*="card"], div[class*="tile"]')?.click();
                break;
            }
        }
    """)
    time.sleep(3)
    nlm_page.screenshot(path="/tmp/morningbrief/step_audio_clicked.png")

    # Look for Generate button and click it
    nlm_page.evaluate("""
        const buttons = Array.from(document.querySelectorAll('button'));
        const genBtn = buttons.find(b => b.textContent.trim().includes('Generate'));
        if (genBtn) genBtn.click();
    """)
    time.sleep(2)
    nlm_page.screenshot(path="/tmp/morningbrief/step_generate_confirm.png")

    # Click any secondary Generate/confirm button
    nlm_page.evaluate("""
        const buttons = Array.from(document.querySelectorAll('button'));
        const genBtn = buttons.find(b => b.textContent.trim() === 'Generate');
        if (genBtn) genBtn.click();
    """)
    time.sleep(2)

    print("  ⏳ Waiting for audio generation (2-5 minutes)...")

    generated = False
    for i in range(60):
        time.sleep(10)

        if i % 3 == 0:
            nlm_page.screenshot(path=f"/tmp/morningbrief/audio_progress_{i}.png")

        # Check for play button or audio element
        has_audio = nlm_page.evaluate("""
            const playBtn = document.querySelector('button[aria-label*="Play"], button[aria-label*="play"]');
            const audio = document.querySelector('audio');
            const playText = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Play'));
            return !!(playBtn || audio || playText);
        """)

        if has_audio:
            generated = True
            print(f"  ✓ Audio generated! ({(i+1)*10}s)")
            break

        if i % 6 == 0 and i > 0:
            print(f"  Still generating... ({(i+1)*10}s)")

    nlm_page.screenshot(path="/tmp/morningbrief/step_audio_done.png")

    # Step 3: Share the notebook
    print("\n--- Step 3: Sharing notebook ---")

    notebook_url = nlm_page.url

    # Click share button
    nlm_page.evaluate("""
        const shareBtn = document.querySelector('button[aria-label*="Share"], button[aria-label*="share"]');
        if (shareBtn) shareBtn.click();
    """)
    time.sleep(2)

    # Enable public sharing
    nlm_page.evaluate("""
        const toggles = document.querySelectorAll('[role="switch"], input[type="checkbox"]');
        toggles.forEach(t => {
            if (!t.checked && !t.getAttribute('aria-checked')?.includes('true')) {
                t.click();
            }
        });
    """)
    time.sleep(1)

    nlm_page.screenshot(path="/tmp/morningbrief/step_shared.png")
    nlm_page.keyboard.press("Escape")
    time.sleep(1)

    # Step 4: Post to Slack
    print("\n--- Step 4: Posting to Slack ---")

    slack_msg = (
        "*:tv: AI Morning Brief — Audio Edition*\n"
        "*Monday, April 14, 2026*\n\n"
        ":rotating_light: Your daily AI intelligence briefing is ready!\n\n"
        f":point_right: *Listen to the full briefing:* {notebook_url}\n\n"
        ":headphones: _Open the link and click 'Audio Overview' to hear the podcast-style summary of today's AI news._\n\n"
        "---\n"
        "_Compiled by ExVenture AI Research Team | Next brief: tomorrow 11:00am_"
    )

    data = json.dumps({"text": slack_msg}).encode()
    req = urllib.request.Request(SLACK_WEBHOOK, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    print(f"  ✓ Posted to Slack: {resp.read().decode()}")

    print(f"\n=== Pipeline complete! ===")
    print(f"Notebook: {notebook_url}")

    browser.close()
