import os
import sys
import subprocess
from thumbnail_generator import create_thumbnail

def run_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_image = os.path.join(base_dir, "input_images", "Krishna_Base.png")
    input_audio = os.path.join(base_dir, "input_audio", "Bageshri Breath.mp3")
    
    output_thumb_dir = os.path.join(base_dir, "output_thumbnails")
    output_video_dir = os.path.join(base_dir, "output_videos")
    
    os.makedirs(output_thumb_dir, exist_ok=True)
    os.makedirs(output_video_dir, exist_ok=True)

    thumb_path = os.path.join(output_thumb_dir, "Raag_Bageshri_Deep_Sleep_Thumbnail.jpg")
    video_path = os.path.join(output_video_dir, "Raag_Bageshri_Deep_Sleep_1Hour_1080p.mp4")
    meta_path = os.path.join(output_video_dir, "Raag_Bageshri_Deep_Sleep_Metadata.txt")

    print("==================================================")
    print("      GENERATING 1-HOUR YOUTUBE VIDEO PACKAGE     ")
    print("==================================================")

    # 1. Generate High-CTR Thumbnail (No Logo)
    print("\n[STEP 1/3] Generating High-Resolution Thumbnail...")
    create_thumbnail(
        bg_path=input_image,
        output_path=thumb_path,
        top_tag="RAAG BAGESHRI · 396Hz DEEP SLEEP",
        lines=["Still Awake", "At 2 AM?", "Deep Peace"],
        left_tag="WITH\nSHRI\nKRISHNA",
        font_name="PlayfairDisplay.ttf",
        main_color=(145, 12, 18),
        glow_style="crimson"
    )
    print(f"Thumbnail created: {thumb_path}")

    # 2. Write YouTube Metadata File (Title, Description, Tags)
    print("\n[STEP 2/3] Writing YouTube Metadata File...")
    yt_title = "Still Awake at 2 AM? 🌌 | Raag Bageshri Bansuri 396Hz for Deep Sleep & Inner Stillness"
    yt_desc = """Let the soft, breathy sound of Bansuri carry you into a quieter state with this Raag Bageshri-inspired instrumental in a 396Hz tuning concept. Slow, spacious phrases and gentle flute improvisation create a peaceful atmosphere for nighttime relaxation, meditation, reading, or simply slowing down.

🎵 Raag: Bageshri-inspired
🎻 Instrument: Bansuri Flute
🔊 Tuning concept: 396Hz
🌙 Mood: Deep, peaceful, introspective
⏱️ Duration: 1 Hour (Looping Meditation)

Use this music as a calming background while you rest, meditate, study, or unwind.

#Bansuri #RaagBageshri #IndianClassical #MeditationMusic #DeepSleep #RelaxingMusic #RaagaBlumes #432Hz #396Hz
"""
    with open(meta_path, 'w', encoding='utf-8') as f:
        f.write(f"TITLE:\n{yt_title}\n\nDESCRIPTION:\n{yt_desc}\n")
    print(f"Metadata written: {meta_path}")

    # 3. Render 1-Hour (3600s) 1080p Video via FFmpeg
    duration_seconds = 3600 # 1 Hour
    print(f"\n[STEP 3/3] Rendering 1-Hour (3600s) 1080p HD Video via FFmpeg...")
    print(f"  Visual: {thumb_path}")
    print(f"  Audio:  {input_audio} (Looping)")
    print(f"  Output: {video_path}")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", thumb_path,
        "-stream_loop", "-1",
        "-i", input_audio,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-crf", "20",
        "-t", str(duration_seconds),
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        video_path
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"\n[SUCCESS] 1-Hour Video successfully rendered: {video_path}")
    else:
        print(f"\n[ERROR] FFmpeg rendering failed: {res.stderr}")

if __name__ == "__main__":
    run_pipeline()
