import os
import glob
import sys
import argparse
import json
from thumbnail_generator import create_thumbnail, generate_preset_thumbnail, PRESETS
from video_generator import build_hd_video
from titles_descriptions_parser import parse_titles_descriptions, get_parsed_json_path
from google_drive_fetch import sync_from_drive

def main():
    parser = argparse.ArgumentParser(description="Raaga Blumes YouTube 1-Hour Video & Thumbnail Automation Bot")
    parser.add_argument("--preset", type=str, default="clear_negative_energy", help="Preset text option (clear_negative_energy, attract_positive_energy, stop_overthinking, instant_stress_relief, remove_mental_blockages)")
    parser.add_argument("--image", type=str, default=None, help="Path to custom input background image")
    parser.add_argument("--audio", type=str, default=None, help="Path to input audio file")
    parser.add_argument("--duration", type=int, default=3600, help="Video duration in seconds (default 3600s = 1 hour)")
    parser.add_argument("--all-presets", action="store_true", help="Generate all thumbnail presets at once")
    parser.add_argument("--sync-drive", action="store_true", help="Sync assets from Google Drive before running")

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_images_dir = os.path.join(base_dir, "input_images")
    input_audio_dir = os.path.join(base_dir, "input_audio")
    output_thumb_dir = os.path.join(base_dir, "output_thumbnails")
    output_video_dir = os.path.join(base_dir, "output_videos")

    os.makedirs(output_thumb_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)

    if args.sync_drive:
        sync_from_drive()

    # Load parsed titles & descriptions
    tracks = get_parsed_json_path(base_dir)

    # 1. Determine background image
    if args.image and os.path.exists(args.image):
        bg_image = args.image
    else:
        images = glob.glob(os.path.join(input_images_dir, "*.[jJ][pP]*[gG]")) + glob.glob(os.path.join(input_images_dir, "*.[pP][nN][gG]"))
        if images:
            bg_image = images[0]
        else:
            print("ERROR: No images found in input_images/ folder. Please place a background image there!")
            return

    # 2. Determine audio file
    if args.audio and os.path.exists(args.audio):
        audio_file = args.audio
    else:
        audios = glob.glob(os.path.join(input_audio_dir, "*.mp3")) + glob.glob(os.path.join(input_audio_dir, "*.wav"))
        if audios:
            audio_file = audios[0]
        else:
            audio_file = None

    print("==================================================")
    print("      RAAGA BLUMES YOUTUBE 1-HOUR VIDEO BOT       ")
    print("==================================================")
    print(f"Background Image: {bg_image}")
    print(f"Audio Track:      {audio_file if audio_file else 'None (Silent)'}")
    print(f"Video Duration:   {args.duration} seconds ({args.duration//60} mins)")
    print(f"Available Tracks: {len(tracks)} loaded from titles_descriptions.txt")
    print("--------------------------------------------------")

    # 3. Generate Thumbnails
    generated_thumbnails = []
    if args.all_presets:
        for preset in PRESETS.keys():
            thumb_out = os.path.join(output_thumb_dir, f"Thumbnail_{preset}.jpg")
            generate_preset_thumbnail(bg_image, thumb_out, preset_name=preset)
            generated_thumbnails.append(thumb_out)
    else:
        thumb_out = os.path.join(output_thumb_dir, f"Thumbnail_{args.preset}.jpg")
        generate_preset_thumbnail(bg_image, thumb_out, preset_name=args.preset)
        generated_thumbnails.append(thumb_out)

    # 4. Generate 1-Hour 1080p Video
    main_thumb = generated_thumbnails[0]
    img_name = os.path.splitext(os.path.basename(bg_image))[0]
    video_out = os.path.join(output_video_dir, f"{img_name}_{args.duration//60}Min_1080p.mp4")
    
    build_hd_video(main_thumb, video_out, audio_path=audio_file, duration_seconds=args.duration)

    print("==================================================")
    print("SUCCESS! Bot automation finished.")
    print(f"Thumbnail saved to: {main_thumb}")
    print(f"Video saved to:     {video_out}")
    print("==================================================")

if __name__ == "__main__":
    main()
