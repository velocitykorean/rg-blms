"""
Daily Automation Pipeline for Raaga Blumes
Fully automated Google Drive sync (Video, Audio, Image triplets), metadata matching,
aesthetic watermark-free thumbnail generation, seamless 1080p looping video rendering (NVENC/CPU),
and YouTube publishing.
"""
import os
import sys
import json
import glob
import random
import time
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

from thumbnail_generator import create_raaga_thumbnail, create_thumbnail, RAAGA_HOOKS
from video_generator import build_raaga_blumes_video, build_hd_video
from titles_descriptions_parser import get_parsed_json_path
from google_drive_fetch import fetch_assets_triplet, get_repost_counts
from publish_youtube import upload_to_youtube, set_video_thumbnail

PUBLISHED_LOG = "published_songs.json"
ALLOW_REPOST = os.getenv("ALLOW_REPOST", "true").lower() == "true"

def get_published_history():
    """Returns list of all publication records."""
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_published_song(song_name, video_id, title, metadata=None, video_name=None):
    """Logs the newly published video into published_songs.json."""
    history = get_published_history()
    entry = {
        "song_name": os.path.basename(song_name),
        "video_file": os.path.basename(video_name) if video_name else "",
        "video_id": video_id,
        "youtube_url": f"https://youtu.be/{video_id}" if video_id else "LOCAL_RENDER",
        "title": title,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {}
    }
    history.append(entry)
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"[LOG] Saved {song_name} to {PUBLISHED_LOG} (Total Published: {len(history)})")

def generate_fallback_metadata(song_base_name):
    """Generates viral, SEO-rich Indian Classical / Bansuri metadata if no text match found."""
    clean_name = song_base_name.replace("_", " ").title()

    title_templates = [
        f"Still Awake at 2 AM? 🌌 | {clean_name} - 432Hz Bansuri Flute for Deep Sleep & Inner Peace",
        f"Clear All Negative Energy & Overthinking 🕊 | {clean_name} Indian Classical Meditation (1 Hour)",
        f"Deep Sleep Instantly | {clean_name} Peaceful Bansuri Flute & Ambient Tanpura 432Hz",
        f"Instant Stress Relief & Anxiety Release | {clean_name} Divine Flute Meditation (1 Hour)",
        f"Calm Your Mind & Attract Positive Energy ✨ | {clean_name} 528Hz Healing Bansuri"
    ]

    title = random.choice(title_templates)

    desc = (
        f"Immerse yourself in 1 hour of divine Indian Classical Bansuri meditation with '{clean_name}'.\n\n"
        f"Designed to melt away anxiety, quiet overthinking, release stress, and guide you into deep, restorative sleep. "
        f"The pure organic frequencies of the Bansuri flute combined with gentle ambient resonance create an atmosphere of profound tranquility.\n\n"
        f"✨ Ideal for:\n"
        f"• Deep Sleep & Overcoming Insomnia\n"
        f"• Meditation, Yoga & Breathwork\n"
        f"• Stress Relief & Anxiety Release\n"
        f"• Deep Focus, Reading & Creative Flow\n"
        f"• Clearing Negative Energy & Aligning Chakras\n\n"
        f"🎵 Instrument: Indian Classical Bansuri Flute\n"
        f"🔊 Frequency: 432Hz / Harmonized Resonance\n"
        f"🌿 Mood: Deep Stillness, Spiritual Peace & Healing\n\n"
        f"#Bansuri #MeditationMusic #IndianClassical #DeepSleep #432Hz #StressRelief #RaagaBlumes #FluteMeditation"
    )

    tags = [
        "bansuri", "flute meditation", "indian classical music", "deep sleep music",
        "432hz flute", "stress relief music", "stop overthinking", "sleep instantly",
        "meditation music", "raaga blumes", "bansuri meditation", "inner peace", "relaxing flute"
    ]

    return title, desc, tags

def run_daily_pipeline(dry_run=False, custom_duration=3600):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_videos_dir = os.path.join(base_dir, "input_videos")
    input_images_dir = os.path.join(base_dir, "input_images")
    input_audio_dir = os.path.join(base_dir, "input_audio")
    output_thumb_dir = os.path.join(base_dir, "output_thumbnails")
    output_video_dir = os.path.join(base_dir, "output_videos")

    os.makedirs(input_videos_dir, exist_ok=True)
    os.makedirs(input_images_dir, exist_ok=True)
    os.makedirs(input_audio_dir, exist_ok=True)
    os.makedirs(output_thumb_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)

    print("==================================================")
    print("      RAAGA BLUMES AUTOMATED PUBLISHING PIPELINE   ")
    print("==================================================")

    # 1. Fetch assets triplet (Video, Audio, Image)
    print("\n[STEP 1] Fetching Video, Audio & Image Triplet...")
    candidate_video, candidate_audio, candidate_image, is_repost = fetch_assets_triplet(allow_repost=ALLOW_REPOST)

    if not candidate_video or not candidate_audio:
        print("[ERROR] Required video and audio assets could not be retrieved. Stopping pipeline.")
        return False

    audio_filename = os.path.basename(candidate_audio)
    video_filename = os.path.basename(candidate_video)
    song_base_name = os.path.splitext(audio_filename)[0]
    safe_name = "".join(c for c in song_base_name if c.isalnum() or c in (' ', '_', '-')).strip()

    print(f"\n[STEP 2] Assets Selected:")
    print(f"  • Video: {video_filename}")
    print(f"  • Audio: {audio_filename}")
    print(f"  • Image: {os.path.basename(candidate_image) if candidate_image else 'Extracting frame from video'}")
    print(f"  • Mode:  {'WEIGHTED REPOST' if is_repost else 'NEW TRACK'}")

    # If no thumbnail image, extract high-res frame at 2s from video
    if not candidate_image or not os.path.exists(candidate_image):
        candidate_image = os.path.join(input_images_dir, f"frame_{safe_name}.jpg")
        print(f"[THUMBNAIL] Extracting base frame from {video_filename} at 00:00:02...")
        try:
            subprocess.run(['ffmpeg', '-y', '-ss', '00:00:02', '-i', candidate_video, '-frames:v', '1', candidate_image], check=True, capture_output=True)
        except Exception as e:
            print(f"[WARN] Failed to extract frame: {e}")

    # 3. Match / Generate Metadata
    tracks_meta = get_parsed_json_path(base_dir)
    matched_meta = None

    for m in tracks_meta:
        raag_name = m.get("raag", "").lower().replace("-inspired", "").strip()
        if raag_name and raag_name in song_base_name.lower():
            matched_meta = m
            break

    if matched_meta:
        yt_title = matched_meta["title"]
        yt_desc = matched_meta["description"]
        yt_tags = matched_meta.get("tags", [])
        hook_main = matched_meta.get("hook", "DEEP SLEEP")
        raag_str = matched_meta.get('raag', 'BANSURI').replace('-inspired', '').strip().upper()
        tuning_str = matched_meta.get('tuning', '432Hz')
        hook_sub = f"Raag {raag_str.title()} · {tuning_str} Deep Peace"
        top_tag = f"RAAG {raag_str} · {tuning_str}"
    else:
        yt_title, yt_desc, yt_tags = generate_fallback_metadata(song_base_name)
        preset = random.choice(RAAGA_HOOKS)
        hook_main = preset["main"]
        hook_sub = preset["sub"]
        top_tag = "DIVINE BANSURI · 432Hz"

    # 4. Generate Aesthetic Watermark-Free Thumbnail
    thumb_path = os.path.join(output_thumb_dir, f"Thumb_{safe_name}.jpg")
    dur_label = f"{custom_duration//60}min" if custom_duration >= 60 else f"{custom_duration}s"
    video_path = os.path.join(output_video_dir, f"Video_{safe_name}_{dur_label}.mp4")

    print(f"\n[STEP 3] Generating Aesthetic Watermark-Free Thumbnail...")
    print(f"  • Top Tag:  {top_tag}")
    print(f"  • Headline: {hook_main}")
    print(f"  • Subtitle: {hook_sub}")

    create_raaga_thumbnail(
        bg_path=candidate_image,
        output_path=thumb_path,
        main_text=hook_main,
        sub_text=hook_sub,
        top_tag=top_tag
    )

    # 5. Render 1080p Looping Video (Seamless ping-pong + audio fadeout)
    print(f"\n[STEP 4] Rendering {dur_label} 1080p Looping Video (No in-video text)...")
    success = build_raaga_blumes_video(
        input_video=candidate_video,
        input_audio=candidate_audio,
        output_path=video_path,
        duration_seconds=custom_duration,
        remove_watermark=True,
        upscale_to_1080p=True
    )

    if not success:
        print("[ERROR] Video generation failed.")
        return False

    # 6. YouTube Publishing / Dry Run
    if dry_run:
        print("\n[DRY RUN] Complete! Video & Thumbnail saved successfully:")
        print(f"  • Video:     {video_path}")
        print(f"  • Thumbnail: {thumb_path}")
        save_published_song(audio_filename, None, yt_title, matched_meta, video_name=video_filename)
        return True

    print("\n[STEP 5] Uploading to YouTube...")
    try:
        video_id = upload_to_youtube(video_path, yt_title, yt_desc, tags=yt_tags)
        if video_id:
            set_video_thumbnail(video_id, thumb_path)
            save_published_song(audio_filename, video_id, yt_title, matched_meta, video_name=video_filename)
            print("==================================================")
            print(f"🎉 SUCCESS! Video published: https://youtu.be/{video_id}")
            print("==================================================")
            return True
    except Exception as e:
        print(f"[YOUTUBE NOTE] YouTube API upload skipped or failed: {e}")
        save_published_song(audio_filename, None, yt_title, matched_meta, video_name=video_filename)
        return True

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    dur = 3600
    for idx, arg in enumerate(sys.argv):
        if arg == "--duration" and idx + 1 < len(sys.argv):
            dur = int(sys.argv[idx + 1])
    run_daily_pipeline(dry_run=is_dry, custom_duration=dur)
