#!/bin/bash
# ExVenture Morning Brief — Daily Pipeline
# Generates brief → NotebookLM notebook → Video → Slack
# Scheduled at 11 AM WITA (Central Indonesian Time) via launchd
# Will NOT run if launchd catches up outside 10-12 AM window

set -euo pipefail

# Check if today's video was already posted (prevents duplicate runs on same day)
# Disabled for today's test run — re-enable after confirming pipeline works
# DATE_CHECK=$(date +"%Y-%m-%d")
# if [ -f "/tmp/morningbrief/morningbrief_video_${DATE_CHECK}.mp4" ] && [ -f "/tmp/morningbrief/posted_${DATE_CHECK}.flag" ]; then
#     echo "Today's video already posted. Skipping."
#     exit 0
# fi

export PATH="/Users/franzccm/Library/Python/3.14/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export PYTHONPATH="/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages:${PYTHONPATH:-}"
export SLACK_USER_TOKEN="SLACK_USER_TOKEN_PLACEHOLDER"
export OPENAI_API_KEY="OPENAI_API_KEY_PLACEHOLDER"
export GEMINI_API_KEY="GEMINI_API_KEY_PLACEHOLDER"
export OPENROUTER_API_KEY="OPENROUTER_API_KEY_PLACEHOLDER"
SCRIPTS_DIR="/Users/franzccm/projects/ex-venture-platform/scripts"
BRIEF_DIR="/tmp/morningbrief"
DATE_SHORT=$(date +"%Y-%m-%d")
BRIEF_FILE="$BRIEF_DIR/brief_${DATE_SHORT}.md"
LOG_FILE="$BRIEF_DIR/pipeline_${DATE_SHORT}.log"
CHROMIUM="/Users/franzccm/Library/Caches/ms-playwright/chromium-1208/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
CDP_PORT=9222

mkdir -p "$BRIEF_DIR"

exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== Morning Brief Pipeline — $(date) ==="

# ─── Step 0: Ensure Chrome for Testing is running with debug port ───
if ! curl -s "http://127.0.0.1:$CDP_PORT/json/version" > /dev/null 2>&1; then
    echo "Starting Chrome for Testing with debug port..."
    USER_DATA="/Users/franzccm/.notebooklm/chrome_profile"
    mkdir -p "$USER_DATA"
    open -a "$CHROMIUM" --args --user-data-dir="$USER_DATA" --remote-debugging-port=$CDP_PORT --remote-allow-origins="*" "https://notebooklm.google.com"
    sleep 10
fi

# Verify Chrome is accessible
if ! curl -s "http://127.0.0.1:$CDP_PORT/json/version" > /dev/null 2>&1; then
    echo "ERROR: Chrome not accessible on port $CDP_PORT"
    exit 1
fi
echo "✓ Chrome running on port $CDP_PORT"

# ─── Step 1: Generate the morningbrief text via Claude Code CLI ───
if [ ! -f "$BRIEF_FILE" ]; then
    echo "Generating morningbrief via Claude Code..."
    claude --dangerously-skip-permissions -p "You are an elite AI industry intelligence unit. Research EVERYTHING that happened in AI in the LAST 48 HOURS using web search. Be COMPREHENSIVE. Also research what is coming in the NEXT 7 DAYS.

Write the document in the EXACT format below. This document will be uploaded to NotebookLM to generate a cinematic animated AI news video.

FORMAT:

**VIDEO GENERATION INSTRUCTIONS:**
Produce a daily AI news video for the EXAI Global YouTube channel with an animated AI news reporter character.

STRUCTURE:
1. HOOK — Start with the most exciting headline to grab attention immediately.
2. HEADLINES — Right after the hook, quickly list ALL stories covered today as a preview.
3. DEEP DIVES — Go through each story with detail. Include references to real demos, screenshots, or footage of these AI tools being used where possible.
4. UPCOMING — What drops next week.
5. SIGN OFF — Clean ending.

Just report the news — no advice, no opinions. Include links to demo videos or tool showcases from YouTube/social media where relevant.

# AI News: The Last 48 Hours

For each news item use this format:
* **[Company/Product Name] — [What happened]:** [2-3 sentence factual description of what shipped, launched, or happened. Bold key names and metrics.] [Source: URL]

Focus ONLY on new tools, new models, new features, new products, new releases. NO funding rounds, NO market cap, NO valuations, NO revenue numbers, NO investor news. Just what is NEW that people can USE or TRY.

# AI News: What is Coming in the Next 7 Days

* **[Expected date] — [Tool/Product name]:** [What it does and when it drops.] [Source: URL]

---
Sources: [all URLs used]

Write ONLY the brief, nothing else. Include ALL source URLs inline and in the sources list at the bottom." > "$BRIEF_FILE" 2>>"$LOG_FILE" || {
        echo "ERROR: Claude Code brief generation failed"
        exit 1
    }
fi

echo "✓ Brief file: $BRIEF_FILE ($(wc -c < "$BRIEF_FILE") bytes)"

# ─── Step 2: Create main video notebook + trigger generation ───
echo ""
echo "=== Creating main video notebook ==="
python3 -u "$SCRIPTS_DIR/nlm_create_and_generate.py"

# ─── Step 3: Immediately start shorts + thumbnail (main video already generating) ───
echo ""
echo "=== Starting shorts + thumbnail (all parallel with main video) ==="
THUMB_PATH="/tmp/morningbrief/thumbnail_${DATE_SHORT}.png" python3 -u "$SCRIPTS_DIR/generate_thumbnail_smart.py" &
THUMB_PID=$!

# Shorts: NotebookLM animations + Remotion text/branding (parallel with main video)
python3 -u "$SCRIPTS_DIR/create_shorts_combined.py" > /tmp/morningbrief/shorts.log 2>&1 &
SHORTS_PID=$!

echo "  Main video: generating on NotebookLM"
echo "  Shorts: generating in parallel (PID $SHORTS_PID)"
echo "  Thumbnail: generating (PID $THUMB_PID)"

# ─── Step 4: Wait for main video + download + Slack ───
echo ""
echo "=== Waiting for main video ==="

# The main video poller needs to use only the MAIN notebook tab
# Shorts use their own tabs via Target.createTarget so no conflict
python3 -u "$SCRIPTS_DIR/wait_download_post_final.py"

# ─── Step 4b: Post-process with Hyperframes (infographics, branding, ticker) ───
echo ""
echo "=== Post-processing video with Hyperframes ==="
VIDEO_PATH="/tmp/morningbrief/morningbrief_video_${DATE_SHORT}.mp4" BRIEF_FILE="$BRIEF_FILE" python3 -u "$SCRIPTS_DIR/postprocess_video.py" || echo "Post-processing failed (non-fatal, using raw video)"

# ─── Step 5: Upload main video to YouTube ───
echo ""
echo "=== Uploading to YouTube ==="
wait $THUMB_PID 2>/dev/null || true
# Retry up to 3 times with 30-min waits (handles upload limit from previous day's shorts)
for attempt in 1 2 3; do
    echo "YouTube upload attempt $attempt/3..."
    python3 -u "$SCRIPTS_DIR/youtube_upload.py" && break
    echo "Upload failed (attempt $attempt). Waiting 30 min before retry..."
    [ $attempt -lt 3 ] && sleep 1800
done

# ─── Step 6: A/B rotation ───
python3 -u "$SCRIPTS_DIR/youtube_ab_rotate.py" > /dev/null 2>&1 || true

# ─── Step 7: Wait for shorts to finish uploading ───
echo ""
echo "=== Waiting for Shorts ==="
wait $SHORTS_PID 2>/dev/null
echo "Shorts output:"
cat /tmp/morningbrief/shorts.log 2>/dev/null || echo "No shorts log"

# Mark today as posted
touch "/tmp/morningbrief/posted_${DATE_SHORT}.flag"

echo ""
echo "=== Pipeline complete — $(date) ==="
