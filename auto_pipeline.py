"""
Daily Automation Pipeline for Raaga Blumes
Handles Drive Sync, Metadata Matching, Thumbnail Creation, 1-Hour Video Rendering, and YouTube Publishing.
"""
import os
import sys
import json
import glob
import time
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from thumbnail_generator import create_thumbnail, generate_preset_thumbnail
from video_generator import build_hd_video
from titles_descriptions_parser import parse_titles_descriptions, get_parsed_json_path
from google_drive_fetch import sync_from_drive
from publish_youtube import upload_to_youtube, set_video_thumbnail

PUBLISHED_LOG = "published_songs.json"

def get_published_history():
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_published_song(song_name, video_id, title, metadata=None):
    history = get_published_history()
    entry = {
        "song_name": song_name,
        "video_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}",
        "title": title,
        "published_at": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata or {}
    }
    history.append(entry)
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"[LOG] Saved {song_name} to {PUBLISHED_LOG}")

def run_daily_pipeline(dry_run=False, custom_duration=3600):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_images_dir = os.path.join(base_dir, "input_images")
    input_audio_dir = os.path.join(base_dir, "input_audio")
    output_thumb_dir = os.path.join(base_dir, "output_thumbnails")
    output_video_dir = os.path.join(base_dir, "output_videos")

    os.makedirs(output_thumb_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)

    print("==================================================")
    print("      RAAGA BLUMES AUTOMATED PUBLISHING PIPELINE   ")
    print("==================================================")

    # 1. Sync from Google Drive if Service Account & Folder IDs are provided
    if os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY") and os.getenv("GOOGLE_DRIVE_AUDIO_FOLDER_ID"):
        print("\n[STEP 1] Checking & Syncing Google Drive...")
        try:
            sync_from_drive()
        except Exception as e:
            print(f"[DRIVE WARN] Drive sync encountered notice: {e}")

    # 2. Get list of available audio tracks
    local_audio_files = sorted(glob.glob(os.path.join(input_audio_dir, "*.mp3")) + glob.glob(os.path.join(input_audio_dir, "*.wav")))
    if not local_audio_files:
        print("[ERROR] No audio files found in input_audio/. Pipeline aborting.")
        return False

    # 3. Filter unpublished songs
    history = get_published_history()
    published_names = set(item.get("song_name", "").strip().lower() for item in history)

    candidate_audio = None
    for apath in local_audio_files:
        aname = os.path.basename(apath).strip().lower()
        if aname not in published_names:
            candidate_audio = apath
            break

    # If all tracks published once, pick least published
    if not candidate_audio:
        print("[INFO] All tracks published at least once. Selecting next in cycle...")
        candidate_audio = local_audio_files[len(history) % len(local_audio_files)]

    audio_filename = os.path.basename(candidate_audio)
    song_base_name = os.path.splitext(audio_filename)[0]
    print(f"\n[STEP 2] Selected Audio Track: {audio_filename}")

    # 4. Match metadata from titles_descriptions.txt
    tracks_meta = get_parsed_json_path(base_dir)
    matched_meta = None

    # Check if song matches any Raag in metadata
    for m in tracks_meta:
        raag_name = m.get("raag", "").lower().replace("-inspired", "").strip()
        if raag_name and raag_name in song_base_name.lower():
            matched_meta = m
            break

    # Fallback to index matching if no direct Raag name match
    if not matched_meta and tracks_meta:
        matched_meta = tracks_meta[len(history) % len(tracks_meta)]

    if matched_meta:
        yt_title = matched_meta["title"]
        yt_desc = matched_meta["description"]
        yt_tags = matched_meta.get("tags", [])
        hook_text = matched_meta.get("hook", "Deep Peace")
        top_tag = f"RAAG {matched_meta.get('raag', 'BANSURI').upper()} · {matched_meta.get('tuning', '432Hz')}"
    else:
        yt_title = f"{song_base_name} | Indian Classical Bansuri Flute Meditation 432Hz"
        yt_desc = f"Experience deep peace and relaxation with this Indian Classical Bansuri Flute meditation performance.\n\n#Bansuri #MeditationMusic #IndianClassical #432Hz #DeepSleep"
        yt_tags = ['Bansuri', 'MeditationMusic', 'IndianClassical', '432Hz', 'DeepSleep', 'RaagaBlumes']
        hook_text = "Deep Peace"
        top_tag = "DIVINE FLUTE MUSIC · 432Hz"

    print(f"Matched Title: {yt_title}")

    # 5. Select Background Image
    images = glob.glob(os.path.join(input_images_dir, "*.[jJ][pP]*[gG]")) + glob.glob(os.path.join(input_images_dir, "*.[pP][nN][gG]"))
    if not images:
        print("[ERROR] No background images found in input_images/!")
        return False
    bg_image = images[len(history) % len(images)]
    print(f"Selected Image: {os.path.basename(bg_image)}")

    # 6. Generate Custom Thumbnail (Clean, No Logo)
    safe_name = "".join(c for c in song_base_name if c.isalnum() or c in (' ', '_', '-')).strip()
    thumb_path = os.path.join(output_thumb_dir, f"Thumb_{safe_name}.jpg")
    video_path = os.path.join(output_video_dir, f"Video_{safe_name}_1080p.mp4")

    # Split hook into up to 3 lines
    words = hook_text.split()
    if len(words) <= 2:
        lines = [hook_text]
    elif len(words) == 3:
        lines = [words[0], words[1], words[2]]
    elif len(words) == 4:
        lines = [f"{words[0]} {words[1]}", f"{words[2]} {words[3]}"]
    else:
        lines = [f"{words[0]} {words[1]}", f"{words[2]} {words[3]}", " ".join(words[4:])]

    print("\n[STEP 3] Generating Thumbnail with Typography...")
    create_thumbnail(
        bg_path=bg_image,
        output_path=thumb_path,
        top_tag=top_tag,
        lines=lines,
        left_tag="WITH\nSHRI\nKRISHNA",
        font_name="PlayfairDisplay.ttf",
        main_color=(145, 12, 18),
        glow_style="crimson"
    )

    # 7. Render Video
    print(f"\n[STEP 4] Rendering {custom_duration//60}-Minute 1080p Video via FFmpeg...")
    success = build_hd_video(thumb_path, video_path, audio_path=candidate_audio, duration_seconds=custom_duration)
    if not success:
        print("[ERROR] Video generation failed.")
        return False

    # 8. Upload & Publish to YouTube
    if dry_run:
        print("\n[DRY RUN] Skipping YouTube upload. Video and Thumbnail generated successfully.")
        return True

    print("\n[STEP 5] Uploading to YouTube...")
    try:
        video_id = upload_to_youtube(video_path, yt_title, yt_desc, tags=yt_tags)
        if video_id:
            set_video_thumbnail(video_id, thumb_path)
            save_published_song(audio_filename, video_id, yt_title, matched_meta)
            print("==================================================")
            print(f"🎉 SUCCESS! Video published: https://youtu.be/{video_id}")
            print("==================================================")
            return True
    except Exception as e:
        print(f"[YOUTUBE ERROR] Upload failed: {e}")
        return False

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    dur = 3600
    for idx, arg in enumerate(sys.argv):
        if arg == "--duration" and idx + 1 < len(sys.argv):
            dur = int(sys.argv[idx + 1])
    run_daily_pipeline(dry_run=is_dry, custom_duration=dur)
