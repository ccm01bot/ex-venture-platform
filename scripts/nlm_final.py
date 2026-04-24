#!/usr/bin/env python3
"""NotebookLM automation - paste text, generate video, post to Slack."""

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

    nlm_page = None
    for page in context.pages:
        if "notebooklm" in page.url:
            nlm_page = page
            break

    if not nlm_page:
        print("✗ No NotebookLM page found")
        sys.exit(1)

    print(f"✓ Page: {nlm_page.url}")

    # First, close the existing modal and start fresh on this notebook
    print("\n--- Closing existing modal ---")
    nlm_page.evaluate("""(() => {
        const closeBtn = document.querySelector('button[aria-label="Close"], button[aria-label="close"]');
        if (closeBtn) closeBtn.click();
        const backdrops = document.querySelectorAll('.cdk-overlay-backdrop');
        backdrops.forEach(b => b.click());
    })()""")
    time.sleep(1)
    nlm_page.keyboard.press("Escape")
    time.sleep(1)

    nlm_page.screenshot(path="/tmp/morningbrief/f_step0.png")

    # Click "Add sources" button
    print("\n--- Step 1: Adding source ---")
    nlm_page.evaluate("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Add sources'));
        if (btn) btn.click();
    })()""")
    time.sleep(2)
    nlm_page.screenshot(path="/tmp/morningbrief/f_step1_addsource.png")

    # Click "Copied text"
    nlm_page.evaluate("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.includes('Copied text'));
        if (btn) btn.click();
    })()""")
    time.sleep(2)
    nlm_page.screenshot(path="/tmp/morningbrief/f_step1_copiedtext.png")

    # Focus textarea and type the text using keyboard
    print("  Typing text into textarea...")

    # Focus the textarea via JS
    nlm_page.evaluate("""(() => {
        const ta = document.querySelector('textarea');
        if (ta) { ta.focus(); ta.click(); }
    })()""")
    time.sleep(0.5)

    # Use Playwright's type method which simulates real keypresses
    # But the text is long, so let's use clipboard
    # Set clipboard content and paste
    nlm_page.evaluate(f"""(() => {{
        const ta = document.querySelector('textarea');
        if (ta) {{
            ta.focus();
            // Use execCommand to simulate paste
            const dt = new DataTransfer();
            dt.setData('text/plain', {json.dumps(brief_text)});
            const pasteEvent = new ClipboardEvent('paste', {{
                clipboardData: dt,
                bubbles: true,
                cancelable: true
            }});
            ta.dispatchEvent(pasteEvent);
        }}
    }})()""")
    time.sleep(1)

    # Check if textarea has content
    ta_value = nlm_page.evaluate("""(() => {
        const ta = document.querySelector('textarea');
        return ta ? ta.value : '';
    })()""")

    if not ta_value:
        print("  Paste event didn't fill textarea, using direct type...")
        # Focus and use Playwright keyboard
        nlm_page.evaluate("""(() => {
            const ta = document.querySelector('textarea');
            if (ta) { ta.focus(); }
        })()""")
        time.sleep(0.3)
        # Type the text (Playwright simulates real keys)
        nlm_page.keyboard.type(brief_text, delay=0)
        time.sleep(1)

    # Verify text
    ta_value = nlm_page.evaluate("""(() => {
        const ta = document.querySelector('textarea');
        return ta ? ta.value.length : 0;
    })()""")
    print(f"  ✓ Textarea has {ta_value} characters")

    nlm_page.screenshot(path="/tmp/morningbrief/f_step1_textfilled.png")

    # Click Insert
    print("  Clicking Insert...")
    nlm_page.evaluate("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => b.textContent.trim() === 'Insert');
        if (btn) btn.click();
    })()""")
    time.sleep(8)
    nlm_page.screenshot(path="/tmp/morningbrief/f_step1_inserted.png")

    # Check source count
    source_count = nlm_page.evaluate("""(() => {
        const el = document.body.innerText;
        const match = el.match(/(\\d+)\\s*source/);
        return match ? match[1] : '0';
    })()""")
    print(f"  Sources: {source_count}")

    # Wait for source processing
    print("  ⏳ Waiting for source to finish processing...")
    time.sleep(10)

    # Close any modal
    nlm_page.keyboard.press("Escape")
    time.sleep(1)

    nlm_page.screenshot(path="/tmp/morningbrief/f_step2_ready.png")

    # Step 2: Generate Video Overview
    print("\n--- Step 2: Generating Video ---")

    # Click on Video tile in Studio panel
    nlm_page.evaluate("""(() => {
        const tiles = document.querySelectorAll('[class*="tile"], [class*="card"], button, div[role="button"]');
        for (const tile of tiles) {
            if (tile.textContent.includes('Video') && !tile.textContent.includes('Overview')) {
                tile.click();
                return 'clicked video tile';
            }
        }
        // Try finding by text
        const allEls = document.querySelectorAll('*');
        for (const el of allEls) {
            if (el.childElementCount === 0 && el.textContent.trim().startsWith('Video')) {
                const clickable = el.closest('button, [role="button"], a, [tabindex]');
                if (clickable) { clickable.click(); return 'clicked video parent'; }
                el.click();
                return 'clicked video text';
            }
        }
        return 'not found';
    })()""")
    time.sleep(3)
    nlm_page.screenshot(path="/tmp/morningbrief/f_step2_video_clicked.png")

    # Click Generate button
    nlm_page.evaluate("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const genBtn = btns.find(b => b.textContent.trim().includes('Generate'));
        if (genBtn) genBtn.click();
    })()""")
    time.sleep(3)
    nlm_page.screenshot(path="/tmp/morningbrief/f_step2_generate.png")

    # Click any confirmation Generate button
    nlm_page.evaluate("""(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const genBtn = btns.find(b => b.textContent.trim() === 'Generate');
        if (genBtn) genBtn.click();
    })()""")
    time.sleep(2)

    print("  ⏳ Waiting for video generation (5-15 minutes)...")

    generated = False
    for i in range(90):  # Up to 15 minutes
        time.sleep(10)

        if i % 3 == 0:
            nlm_page.screenshot(path=f"/tmp/morningbrief/f_video_progress_{i}.png")

        # Check for video/play/download
        status = nlm_page.evaluate("""(() => {
            const page = document.body.innerText;
            if (page.includes('Play') || page.includes('Download')) return 'done';
            if (page.includes('Generating') || page.includes('generating')) return 'generating';
            const video = document.querySelector('video');
            if (video) return 'done';
            return 'waiting';
        })()""")

        if status == 'done':
            generated = True
            print(f"  ✓ Video generated! ({(i+1)*10}s)")
            break

        if i % 6 == 0 and i > 0:
            print(f"  [{status}] ({(i+1)*10}s)")

    nlm_page.screenshot(path="/tmp/morningbrief/f_step2_done.png")

    # Step 3: Share notebook and post to Slack
    print("\n--- Step 3: Sharing & posting to Slack ---")

    notebook_url = nlm_page.url

    # Enable sharing
    nlm_page.evaluate("""(() => {
        const btns = document.querySelectorAll('button');
        for (const btn of btns) {
            const label = btn.getAttribute('aria-label') || '';
            if (label.toLowerCase().includes('share')) { btn.click(); return; }
        }
    })()""")
    time.sleep(2)

    nlm_page.evaluate("""(() => {
        const switches = document.querySelectorAll('[role="switch"]');
        switches.forEach(s => {
            if (s.getAttribute('aria-checked') !== 'true') s.click();
        });
    })()""")
    time.sleep(1)
    nlm_page.keyboard.press("Escape")
    time.sleep(1)

    # Post to Slack
    slack_msg = (
        "*:tv: AI Morning Brief — Video Edition*\n"
        "*Monday, April 14, 2026*\n\n"
        ":rotating_light: Your daily AI intelligence briefing is ready!\n\n"
        f":point_right: *Watch the full video briefing:* {notebook_url}\n\n"
        "_Open the link and click 'Video Overview' to watch today's AI news summary._\n\n"
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
