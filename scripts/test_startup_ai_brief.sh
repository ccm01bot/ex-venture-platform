#!/bin/bash
# Test run: "Best AI model for building a startup" video at 13:07 Bali

set -euo pipefail
export PATH="/Users/franzccm/Library/Python/3.14/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export SLACK_USER_TOKEN="SLACK_USER_TOKEN_PLACEHOLDER"

BRIEF_FILE="/tmp/morningbrief/brief_startup_test.md"
LOG="/tmp/morningbrief/test_startup_log.txt"
exec > >(tee -a "$LOG") 2>&1

echo "=== Test Brief: Best AI Model for Startups === $(date)"

# Ensure Chrome is running
if ! curl -s "http://127.0.0.1:9222/json/version" > /dev/null 2>&1; then
    echo "Starting Chrome for Testing..."
    open -a "/Users/franzccm/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing" --args --user-data-dir="/Users/franzccm/.notebooklm/chrome_profile" --remote-debugging-port=9222 --remote-allow-origins="*" "https://notebooklm.google.com"
    sleep 10
fi

# Generate brief via Claude Code CLI
echo "Generating brief via Claude Code..."
claude -p "Research and write a comprehensive briefing titled 'The Best AI Model for Building a Startup in 2026'. Cover:
- Best AI model for coding (Claude Sonnet 4.6, GPT-5.4, Gemini 3.1 Pro, etc.) with benchmarks and cost per task
- Best AI model for content/marketing
- Best AI model for customer support / chatbots
- Best AI for quick prototyping (v0, Cursor, Claude Code, Windsurf)
- Best agentic frameworks for building autonomous workflows
- Include PRICING comparison
- Include REAL-WORLD use cases from founders who have built with each
- ALL source URLs must be included in the brief
- Format: punchy, actionable, for startup founders

Write this in the ExVenture morning brief format with sections for PRIORITY, WHAT TO USE, PRICING, INSIDER INTEL, BOTTOM LINE. Make it 2000-3000 words. Only output the brief - no preamble." > "$BRIEF_FILE" 2>&1

echo "Brief written: $(wc -c < "$BRIEF_FILE") bytes"

# Upload to NotebookLM
echo "Uploading to NotebookLM..."
BRIEF_FILE="$BRIEF_FILE" python3 -u /Users/franzccm/projects/ex-venture-platform/scripts/nlm_step1b.py

# Generate video with ExVenture prompt
echo "Starting video generation..."
python3 -u /Users/franzccm/projects/ex-venture-platform/scripts/generate_video_with_prompt.py

# Wait for video and post to Slack
echo "Waiting for video and posting to Slack..."
python3 -u /Users/franzccm/projects/ex-venture-platform/scripts/wait_download_post_final.py

echo "=== Test complete === $(date)"
