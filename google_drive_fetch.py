"""
Google Drive Integration Module (Raaga Blumes)
Fetches audio (MP3/WAV) and images directly from Google Drive using Service Account secrets.
Supports both file paths (local dev) and raw JSON strings (GitHub Actions secrets).
Supports weighted random repost selection for infinite circulation.
"""
import os
import io
import json
import sys
import glob
import random
import tempfile
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Strictly read from environment variables / secrets
GOOGLE_DRIVE_AUDIO_FOLDER_ID = os.getenv("GOOGLE_DRIVE_AUDIO_FOLDER_ID")
GOOGLE_DRIVE_IMAGE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_IMAGE_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")

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
        print("[DRIVE ERROR] GOOGLE_SERVICE_ACCOUNT_KEY environment variable/secret is not set!")
        return None

    try:
        key_str = GOOGLE_SERVICE_ACCOUNT_KEY.strip()
        if key_str.startswith('{'):
            # Raw JSON content passed via GitHub Actions Secret
            info = json.loads(key_str)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
            print("[DRIVE] Initialized Google Drive with Service Account JSON Secret.")
            return build('drive', 'v3', credentials=credentials)
        elif os.path.exists(GOOGLE_SERVICE_ACCOUNT_KEY):
            # Local file path
            credentials = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_KEY, scopes=SCOPES)
            print("[DRIVE] Initialized Google Drive with Service Account file.")
            return build('drive', 'v3', credentials=credentials)
        else:
            # Script directory relative path fallback
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sa_path = os.path.join(script_dir, GOOGLE_SERVICE_ACCOUNT_KEY)
            if os.path.exists(sa_path):
                credentials = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
                print("[DRIVE] Initialized Google Drive with relative Service Account file.")
                return build('drive', 'v3', credentials=credentials)
            else:
                print(f"[DRIVE ERROR] Invalid GOOGLE_SERVICE_ACCOUNT_KEY format or file not found.")
                return None
    except Exception as e:
        print(f"[DRIVE ERROR] Failed to initialize Google Drive: {e}")
        return None

def list_files_in_folder(folder_id, mime_type_prefix=None):
    """List all non-trashed files inside a Google Drive folder."""
    if not folder_id:
        print("[DRIVE WARN] Folder ID is empty.")
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
        if mime_type_prefix:
            files = [f for f in files if f.get('mimeType', '').startswith(mime_type_prefix) or f.get('name', '').lower().endswith(('.mp3', '.wav', '.jpg', '.jpeg', '.png'))]
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
                    sname = item.get("song_name", "").strip().lower()
                    if sname:
                        counts[sname] = counts.get(sname, 0) + 1
                return counts
        except Exception:
            return {}
    return {}

def fetch_one_pair_from_drive(allow_repost=True):
    """
    Fetches ONE audio track and ONE background image from Google Drive.
    Uses Weighted Random Selection when all songs have been published.
    Returns: (audio_path, image_path, is_repost)
    """
    os.makedirs(LOCAL_IMAGE_DIR, exist_ok=True)
    os.makedirs(LOCAL_AUDIO_DIR, exist_ok=True)

    print("\n[DRIVE] Connecting to Google Drive...")
    audio_files = list_files_in_folder(GOOGLE_DRIVE_AUDIO_FOLDER_ID, mime_type_prefix="audio/")
    image_files = list_files_in_folder(GOOGLE_DRIVE_IMAGE_FOLDER_ID, mime_type_prefix="image/")

    if not audio_files:
        print("[DRIVE ERROR] No audio files found in Google Drive audio folder.")
        return None, None, False
    if not image_files:
        print("[DRIVE ERROR] No image files found in Google Drive image folder.")
        return None, None, False

    print(f"[DRIVE] Found {len(audio_files)} audio tracks and {len(image_files)} images in Drive.")

    repost_counts = get_repost_counts()
    print(f"[DRIVE] Total unique tracks previously published: {len(repost_counts)}")

    # Phase 1: Look for unpublished audio
    unpublished = [f for f in audio_files if f['name'].strip().lower() not in repost_counts]

    if unpublished:
        selected_audio_info = unpublished[0]
        # Pick matching index or round-robin image
        image_idx = len(repost_counts) % len(image_files)
        selected_image_info = image_files[image_idx]
        is_repost = False
        print(f"\n✅ [NEW TRACK] Selected {selected_audio_info['name']} with Image {selected_image_info['name']}")
    elif allow_repost:
        # Phase 2: Weighted Random Selection
        weights = []
        for a_info in audio_files:
            sname = a_info['name'].strip().lower()
            count = repost_counts.get(sname, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_audio_info = random.choices(audio_files, weights=weights, k=1)[0]
        selected_image_info = random.choice(image_files)
        is_repost = True
        prev_count = repost_counts.get(selected_audio_info['name'].strip().lower(), 0)
        print(f"\n🔄 [WEIGHTED REPOST] Selected {selected_audio_info['name']} (Published {prev_count} times before) with Image {selected_image_info['name']}")
    else:
        print("[DRIVE] All songs published and repost is disabled.")
        return None, None, False

    # Download Selected Audio
    audio_dest = os.path.join(LOCAL_AUDIO_DIR, selected_audio_info['name'])
    if not os.path.exists(audio_dest):
        print(f"[DRIVE] Downloading audio: {selected_audio_info['name']}...")
        if not download_file(selected_audio_info['id'], audio_dest):
            return None, None, False
    else:
        print(f"[DRIVE] Audio already present locally: {selected_audio_info['name']}")

    # Download Selected Image
    image_dest = os.path.join(LOCAL_IMAGE_DIR, selected_image_info['name'])
    if not os.path.exists(image_dest):
        print(f"[DRIVE] Downloading image: {selected_image_info['name']}...")
        if not download_file(selected_image_info['id'], image_dest):
            return None, None, False
    else:
        print(f"[DRIVE] Image already present locally: {selected_image_info['name']}")

    return audio_dest, image_dest, is_repost

if __name__ == "__main__":
    a, img, is_rep = fetch_one_pair_from_drive()
    print("Downloaded Pair:", a, img, "Is Repost:", is_rep)
