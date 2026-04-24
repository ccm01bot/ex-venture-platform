#!/usr/bin/env python3
"""Prepend the thumbnail as first 3 seconds of the video so YouTube auto-selects it."""

import subprocess
import os
import sys
import datetime

DATE_SHORT = datetime.date.today().strftime("%Y-%m-%d")
VIDEO_PATH = os.environ.get("VIDEO_PATH", f"/tmp/morningbrief/morningbrief_video_{DATE_SHORT}.mp4")
THUMB_PATH = os.environ.get("THUMB_PATH", f"/tmp/morningbrief/thumbnail_{DATE_SHORT}.png")
OUTPUT_PATH = VIDEO_PATH.replace(".mp4", "_final.mp4")

if not os.path.exists(VIDEO_PATH):
    print(f"No video: {VIDEO_PATH}")
    sys.exit(1)

if not os.path.exists(THUMB_PATH):
    print(f"No thumbnail: {THUMB_PATH}, skipping prepend")
    # Just copy video as-is
    import shutil
    shutil.copy2(VIDEO_PATH, OUTPUT_PATH)
    os.rename(OUTPUT_PATH, VIDEO_PATH)
    sys.exit(0)

print(f"Prepending thumbnail to video...")

# Get video dimensions and fps
probe = subprocess.run([
    "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", VIDEO_PATH
], capture_output=True, text=True)

import json
streams = json.loads(probe.stdout)
video_stream = [s for s in streams["streams"] if s["codec_type"] == "video"][0]
width = int(video_stream["width"])
height = int(video_stream["height"])
fps = video_stream.get("r_frame_rate", "30/1")

print(f"  Video: {width}x{height} @ {fps}")

# Create a 3-second video from the thumbnail image, with a subtle zoom effect
thumb_video = "/tmp/morningbrief/thumb_clip.mp4"
subprocess.run([
    "ffmpeg", "-y", "-loop", "1", "-i", THUMB_PATH,
    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.002,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=90:s={width}x{height}:fps={fps}",
    "-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", fps,
    thumb_video
], capture_output=True, text=True)

if not os.path.exists(thumb_video):
    print("  Failed to create thumb clip, trying simpler approach...")
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", THUMB_PATH,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        thumb_video
    ], capture_output=True, text=True)

if not os.path.exists(thumb_video):
    print("  Thumbnail clip creation failed, using video as-is")
    sys.exit(0)

print(f"  Thumb clip: {os.path.getsize(thumb_video)/1024:.0f} KB")

# Create concat file
concat_file = "/tmp/morningbrief/concat.txt"
with open(concat_file, "w") as f:
    f.write(f"file '{thumb_video}'\n")
    f.write(f"file '{VIDEO_PATH}'\n")

# Detect original video's audio properties
audio_probe = subprocess.run([
    "ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", VIDEO_PATH
], capture_output=True, text=True)
audio_info = json.loads(audio_probe.stdout)
audio_channels = 1
audio_rate = 44100
for s in audio_info.get("streams", []):
    if s["codec_type"] == "audio":
        audio_channels = int(s.get("channels", 1))
        audio_rate = int(s.get("sample_rate", 44100))
        break

channel_layout = "mono" if audio_channels == 1 else "stereo"
print(f"  Audio: {audio_channels}ch, {audio_rate}Hz ({channel_layout})")

# Add matching silent audio to thumbnail clip
thumb_with_audio = "/tmp/morningbrief/thumb_clip_audio.mp4"
subprocess.run([
    "ffmpeg", "-y", "-i", thumb_video,
    "-f", "lavfi", "-i", f"anullsrc=channel_layout={channel_layout}:sample_rate={audio_rate}",
    "-c:v", "copy", "-c:a", "aac", "-shortest",
    thumb_with_audio
], capture_output=True, text=True)

# Update concat file to use the version with audio
with open(concat_file, "w") as f:
    f.write(f"file '{thumb_with_audio}'\n")
    f.write(f"file '{VIDEO_PATH}'\n")

# Concatenate: thumbnail clip (with silent audio) + original video (with audio)
result = subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    OUTPUT_PATH
], capture_output=True, text=True)

if os.path.exists(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 100000:
    # Replace original with the prepended version
    os.rename(OUTPUT_PATH, VIDEO_PATH)
    print(f"  ✓ Thumbnail prepended: {os.path.getsize(VIDEO_PATH)/1024/1024:.1f} MB")
else:
    print(f"  ✗ Concat failed: {result.stderr[:200]}")

# Cleanup
for f in [thumb_video, thumb_with_audio, concat_file]:
    if os.path.exists(f):
        os.unlink(f)
