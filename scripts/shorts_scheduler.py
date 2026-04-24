#!/usr/bin/env python3
"""
Daily Shorts Scheduler — uploads 10 shorts per day at optimal times.
5x Type A (clip mashup) + 5x Type B (NotebookLM animated)
Runs as a background daemon via launchd.
"""

import sys
sys.path.insert(0, '/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages')

import os, json, time, datetime, subprocess, glob

SCRIPTS = "/Users/franzccm/projects/ex-venture-platform/scripts"
SHORTS_DIR = "/tmp/morningbrief/shorts_queue"
POSTED_LOG = "/tmp/morningbrief/shorts_posted.json"

os.makedirs(SHORTS_DIR, exist_ok=True)

# Schedule: 10 slots per day (WITA/UTC+8)
SCHEDULE = [
    {"time": "06:00", "type": "B"},
    {"time": "07:30", "type": "A"},
    {"time": "09:00", "type": "B"},
    {"time": "11:00", "type": "A"},
    {"time": "13:00", "type": "B"},
    {"time": "15:00", "type": "A"},
    {"time": "17:00", "type": "B"},
    {"time": "19:30", "type": "A"},
    {"time": "21:00", "type": "B"},
    {"time": "23:00", "type": "A"},
]

def get_posted_today():
    today = datetime.date.today().isoformat()
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG) as f:
            data = json.load(f)
        return data.get(today, [])
    return []

def mark_posted(slot_time):
    today = datetime.date.today().isoformat()
    data = {}
    if os.path.exists(POSTED_LOG):
        with open(POSTED_LOG) as f:
            data = json.load(f)
    data.setdefault(today, []).append(slot_time)
    with open(POSTED_LOG, 'w') as f:
        json.dump(data, f, indent=2)

def create_type_a():
    """Create a clip mashup short."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages"
    env["GEMINI_API_KEY"] = "GEMINI_API_KEY_REVOKED_PLACEHOLDER"
    result = subprocess.run(
        ["python3", "-u", f"{SCRIPTS}/create_viral_short.py"],
        capture_output=True, text=True, env=env, timeout=600
    )
    # Extract YouTube URL from output
    for line in result.stdout.split('\n'):
        if 'youtu.be/' in line:
            return line.strip()
    return None

def create_type_b():
    """Create a NotebookLM animated short."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "/Users/franzccm/Library/Python/3.14/lib/python3.14/site-packages"
    env["GEMINI_API_KEY"] = "GEMINI_API_KEY_REVOKED_PLACEHOLDER"
    result = subprocess.run(
        ["python3", "-u", f"{SCRIPTS}/create_shorts_combined.py"],
        capture_output=True, text=True, env=env, timeout=3600
    )
    for line in result.stdout.split('\n'):
        if 'youtu.be/' in line:
            return line.strip()
    return None

def run_scheduler():
    print(f"[{time.strftime('%H:%M:%S')}] Shorts Scheduler started")
    print(f"  10 shorts/day, checking every 5 minutes\n")

    while True:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        posted = get_posted_today()

        for slot in SCHEDULE:
            slot_time = slot["time"]

            # Skip if already posted
            if slot_time in posted:
                continue

            # Check if we're within 5 minutes of the slot
            slot_h, slot_m = map(int, slot_time.split(':'))
            slot_dt = now.replace(hour=slot_h, minute=slot_m, second=0)
            diff = (now - slot_dt).total_seconds()

            if 0 <= diff <= 300:  # Within 5 minutes after slot time
                print(f"[{time.strftime('%H:%M:%S')}] Slot {slot_time} — Creating Type {slot['type']} short...")

                try:
                    if slot["type"] == "A":
                        result = create_type_a()
                    else:
                        result = create_type_b()

                    if result:
                        print(f"  ✓ {result}")
                    else:
                        print(f"  ✗ Creation failed")
                except Exception as e:
                    print(f"  ✗ Error: {str(e)[:80]}")

                mark_posted(slot_time)

        # Sleep 5 minutes before checking again
        time.sleep(300)

if __name__ == "__main__":
    run_scheduler()
