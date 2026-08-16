import os
import subprocess

def build_hd_video(image_path, output_video_path, audio_path=None, duration_seconds=3600):
    """
    Renders a 1080p Full HD video from an image and audio file using FFmpeg.
    Default duration: 3600 seconds (1 Hour).
    """
    mins = duration_seconds // 60
    print(f"[VIDEO START] Creating {mins}-minute (1080p) video from:\n  Image: {image_path}\n  Audio: {audio_path}")
    
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    
    if audio_path and os.path.exists(audio_path):
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-stream_loop", "-1",
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-t", str(duration_seconds),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_video_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-t", str(duration_seconds),
            "-pix_fmt", "yuv420p",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_video_path
        ]
        
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[VIDEO SUCCESS] {mins}-minute 1080p Video created at: {output_video_path}")
        return True
    else:
        print(f"[VIDEO ERROR] FFmpeg failed: {res.stderr}")
        return False
