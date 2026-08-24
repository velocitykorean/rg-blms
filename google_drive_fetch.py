"""
Google Drive Integration Module (Raaga Blumes)
Fetches:
1. Video Loops (MP4/MOV/MKV) from GOOGLE_DRIVE_VIDEO_FOLDER_ID
2. Audio Tracks (MP3/WAV/FLAC) from GOOGLE_DRIVE_AUDIO_FOLDER_ID
3. Background Images (JPG/PNG/WEBP) from GOOGLE_DRIVE_IMAGE_FOLDER_ID

Supports:
- Priority for new unpublished tracks
- Infinite circulation mode (Weighted Least-Recently-Used selection)
- Dynamic remixing across video, audio, and thumbnail permutations
- Seamless local folder fallback
"""
import os
import io
import json
import sys
import glob
import random
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Strictly read from environment variables / secrets
GOOGLE_DRIVE_VIDEO_FOLDER_ID = os.getenv("GOOGLE_DRIVE_VIDEO_FOLDER_ID", "1NQJFn3ygcDUlXHr6mXIWFXyTxUV4p2o6")
GOOGLE_DRIVE_AUDIO_FOLDER_ID = os.getenv("GOOGLE_DRIVE_AUDIO_FOLDER_ID", "1Z8s1pdczQGesG1ALc9BQR64YJ2rQGWWR")
GOOGLE_DRIVE_IMAGE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_IMAGE_FOLDER_ID", "1QozOnV0LLfSdPcLE92CfnS0NkR03mF-v")
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY", "service_account.json")

LOCAL_VIDEO_DIR = os.getenv("LOCAL_VIDEO_DIR", "input_videos")
LOCAL_AUDIO_DIR = os.getenv("LOCAL_AUDIO_DIR", "input_audio")
LOCAL_IMAGE_DIR = os.getenv("LOCAL_IMAGE_DIR", "input_images")
PUBLISHED_LOG = "published_songs.json"

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Build and return an authorized Google Drive v3 service instance."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("[DRIVE] Google API libraries not installed. Run: pip install google-api-python-client google-auth")
        return None

    if not GOOGLE_SERVICE_ACCOUNT_KEY:
        print("[DRIVE ERROR] GOOGLE_SERVICE_ACCOUNT_KEY is not set.")
        return None

    try:
        key_str = GOOGLE_SERVICE_ACCOUNT_KEY.strip()
        if key_str.startswith('{'):
            # Raw JSON content passed via GitHub Actions Secret
            info = json.loads(key_str)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            return build('drive', 'v3', credentials=credentials)
        elif os.path.exists(GOOGLE_SERVICE_ACCOUNT_KEY):
            # Local file path
            credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_KEY, scopes=SCOPES)
            return build('drive', 'v3', credentials=credentials)
        else:
            # Relative path from script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sa_path = os.path.join(script_dir, GOOGLE_SERVICE_ACCOUNT_KEY)
            if os.path.exists(sa_path):
                credentials = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
                return build('drive', 'v3', credentials=credentials)
            return None
    except Exception as e:
        print(f"[DRIVE ERROR] Failed to initialize Google Drive: {e}")
        return None

def list_files_in_folder(folder_id, mime_prefix=None, extensions=None):
    """List all non-trashed files inside a Google Drive folder."""
    if not folder_id:
        return []
    service = get_drive_service()
    if not service:
        return []
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, size)",
            pageSize=100
        ).execute()
        files = results.get('files', [])
        if mime_prefix or extensions:
            filtered = []
            for f in files:
                name = f.get('name', '').lower()
                mime = f.get('mimeType', '').lower()
                if mime_prefix and mime.startswith(mime_prefix):
                    filtered.append(f)
                elif extensions and any(name.endswith(ext) for ext in extensions):
                    filtered.append(f)
            return filtered
        return files
    except Exception as e:
        print(f"[DRIVE ERROR] Error listing files in folder {folder_id}: {e}")
        return []

def download_file(file_id, dest_path):
    """Downloads a single file from Google Drive."""
    try:
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError:
        return False
    service = get_drive_service()
    if not service:
        return False
    try:
        request = service.files().get_media(fileId=file_id)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        with io.FileIO(dest_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=10*1024*1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        return True
    except Exception as e:
        print(f"[DRIVE ERROR] Error downloading {file_id}: {e}")
        return False

def get_repost_counts():
    """Counts how many times each audio track has been published."""
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                counts = {}
                for item in data:
                    sname = (item.get("song_name") or item.get("audio_file") or item.get("audio_name") or "").strip().lower()
                    if sname:
                        counts[sname] = counts.get(sname, 0) + 1
                return counts
        except Exception:
            return {}
    return {}

def fetch_assets_triplet(allow_repost=True):
    """
    Fetches ONE video, ONE audio track, and ONE background image.
    Supports Infinite Circulation Mode with Weighted Least-Recently-Used selection.
    Returns: (video_path, audio_path, image_path, is_repost)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    vid_dir = os.path.join(script_dir, LOCAL_VIDEO_DIR)
    aud_dir = os.path.join(script_dir, LOCAL_AUDIO_DIR)
    img_dir = os.path.join(script_dir, LOCAL_IMAGE_DIR)

    os.makedirs(vid_dir, exist_ok=True)
    os.makedirs(aud_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    drive_service = get_drive_service()
    drive_ready = (drive_service is not None) and bool(GOOGLE_DRIVE_AUDIO_FOLDER_ID)

    if drive_ready:
        print("[DRIVE] Querying Google Drive folders for Videos, Audio, and Images...")
        v_files = list_files_in_folder(GOOGLE_DRIVE_VIDEO_FOLDER_ID, extensions=['.mp4', '.mov', '.mkv'])
        a_files = list_files_in_folder(GOOGLE_DRIVE_AUDIO_FOLDER_ID, extensions=['.mp3', '.wav', '.flac'])
        i_files = list_files_in_folder(GOOGLE_DRIVE_IMAGE_FOLDER_ID, extensions=['.jpg', '.jpeg', '.png', '.webp'])

        print(f"[DRIVE] Found {len(v_files)} videos, {len(a_files)} audio tracks, and {len(i_files)} images.")

        if a_files and v_files:
            repost_counts = get_repost_counts()
            unpublished = [f for f in a_files if f['name'].strip().lower() not in repost_counts]

            if unpublished:
                # Phase 1: Pick unpublished audio first
                sel_audio = unpublished[0]
                sel_video = v_files[len(repost_counts) % len(v_files)]
                sel_image = i_files[len(repost_counts) % len(i_files)] if i_files else None
                is_repost = False
                print(f"[PIPELINE] New Track Found: {sel_audio['name']} with Video: {sel_video['name']}")
            elif allow_repost:
                # Phase 2: Infinite Circulation - Weighted Random Selection
                weights = [max(1, 1000 // (3 ** min(repost_counts.get(f['name'].strip().lower(), 0), 6))) for f in a_files]
                sel_audio = random.choices(a_files, weights=weights, k=1)[0]
                sel_video = random.choice(v_files)
                sel_image = random.choice(i_files) if i_files else None
                is_repost = True
                prev_c = repost_counts.get(sel_audio['name'].strip().lower(), 0)
                print(f"[PIPELINE] Infinite Circulation: Selected {sel_audio['name']} (published {prev_c} times before) with dynamic video remix: {sel_video['name']}")
            else:
                print("[INFO] All tracks published and repost is disabled.")
                return None, None, None, False

            v_dest = os.path.join(vid_dir, sel_video['name'])
            a_dest = os.path.join(aud_dir, sel_audio['name'])
            i_dest = os.path.join(img_dir, sel_image['name']) if sel_image else None

            if not os.path.exists(v_dest):
                print(f"[DRIVE] Downloading video: {sel_video['name']}...")
                download_file(sel_video['id'], v_dest)
            else:
                print(f"[DRIVE] Video cached locally: {sel_video['name']}")

            if not os.path.exists(a_dest):
                print(f"[DRIVE] Downloading audio: {sel_audio['name']}...")
                download_file(sel_audio['id'], a_dest)
            else:
                print(f"[DRIVE] Audio cached locally: {sel_audio['name']}")

            if i_dest:
                if not os.path.exists(i_dest):
                    print(f"[DRIVE] Downloading image: {sel_image['name']}...")
                    download_file(sel_image['id'], i_dest)
                else:
                    print(f"[DRIVE] Image cached locally: {sel_image['name']}")

            return v_dest, a_dest, i_dest, is_repost

    # Local files fallback
    print("[PIPELINE] Using local input folders as fallback...")
    local_vids = sorted(glob.glob(os.path.join(vid_dir, "*.mp4")) + glob.glob(os.path.join(vid_dir, "*.mov")) + glob.glob(os.path.join(vid_dir, "*.mkv")))
    local_auds = sorted(glob.glob(os.path.join(aud_dir, "*.mp3")) + glob.glob(os.path.join(aud_dir, "*.wav")))
    local_imgs = sorted(glob.glob(os.path.join(img_dir, "*.jpg")) + glob.glob(os.path.join(img_dir, "*.png")) + glob.glob(os.path.join(img_dir, "*.jpeg")))

    if not local_vids or not local_auds:
        print(f"[WARN] Local folders missing media: {len(local_vids)} videos, {len(local_auds)} audios found.")
        return None, None, None, False

    repost_counts = get_repost_counts()
    unpublished = [f for f in local_auds if os.path.basename(f).strip().lower() not in repost_counts]

    if unpublished:
        sel_aud = unpublished[0]
        sel_vid = local_vids[len(repost_counts) % len(local_vids)]
        sel_img = local_imgs[len(repost_counts) % len(local_imgs)] if local_imgs else None
        is_repost = False
    elif allow_repost:
        weights = [max(1, 1000 // (3 ** min(repost_counts.get(os.path.basename(f).strip().lower(), 0), 6))) for f in local_auds]
        sel_aud = random.choices(local_auds, weights=weights, k=1)[0]
        sel_vid = random.choice(local_vids)
        sel_img = random.choice(local_imgs) if local_imgs else None
        is_repost = True
    else:
        return None, None, None, False

    return sel_vid, sel_aud, sel_img, is_repost

def fetch_one_pair_from_drive(allow_repost=True):
    """Backwards-compatible wrapper that returns (audio_path, image_path, is_repost)."""
    _, a, img, is_rep = fetch_assets_triplet(allow_repost=allow_repost)
    return a, img, is_rep

if __name__ == "__main__":
    v, a, img, is_rep = fetch_assets_triplet(allow_repost=True)
    print("\n--- Fetched Assets Triplet ---")
    print("Video:", v)
    print("Audio:", a)
    print("Image:", img)
    print("Is Repost:", is_rep)
