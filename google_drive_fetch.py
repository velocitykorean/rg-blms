"""
Google Drive Integration Module (Raaga Blumes)
Fetch audio (MP3/WAV) and image files from Google Drive folders.
"""
import os
import io
import json
import sys
import glob
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

GOOGLE_DRIVE_AUDIO_FOLDER_ID = os.getenv("GOOGLE_DRIVE_AUDIO_FOLDER_ID", "1Z8s1pdczQGesG1ALc9BQR64YJ2rQGWWR")
GOOGLE_DRIVE_IMAGE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_IMAGE_FOLDER_ID", "1QozOnV0LLfSdPcLE92CfnS0NkR03mF-v")
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY", "service_account.json")
LOCAL_AUDIO_DIR = os.getenv("LOCAL_AUDIO_DIR", "input_audio")
LOCAL_IMAGE_DIR = os.getenv("LOCAL_IMAGE_DIR", "input_images")

def get_drive_service():
    """Build and return an authorized Google Drive v3 service instance."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("[DRIVE] Google API libraries not installed. Run: pip install google-api-python-client google-auth")
        return None

    script_dir = os.path.dirname(os.path.abspath(__file__))
    sa_path = os.path.join(script_dir, GOOGLE_SERVICE_ACCOUNT_KEY)
    
    if not os.path.exists(sa_path):
        print(f"[DRIVE] Service account key not found at {sa_path}")
        return None

    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    credentials = service_account.Credentials.from_service_account_file(sa_path, scopes=scopes)
    return build('drive', 'v3', credentials=credentials)

def list_files_in_folder(folder_id, mime_type_prefix=None):
    """List all files inside a Google Drive folder."""
    service = get_drive_service()
    if not service or not folder_id:
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
            files = [f for f in files if f.get('mimeType', '').startswith(mime_type_prefix)]
        return files
    except Exception as e:
        print(f"[DRIVE] Error listing files in {folder_id}: {e}")
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
        fh = io.FileIO(dest_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return True
    except Exception as e:
        print(f"[DRIVE] Error downloading {file_id}: {e}")
        return False

def sync_from_drive():
    """Syncs images and audio from Google Drive to local folders."""
    os.makedirs(LOCAL_IMAGE_DIR, exist_ok=True)
    os.makedirs(LOCAL_AUDIO_DIR, exist_ok=True)

    print("[DRIVE] Checking Google Drive Images folder...")
    img_files = list_files_in_folder(GOOGLE_DRIVE_IMAGE_FOLDER_ID, mime_type_prefix="image/")
    print(f"[DRIVE] Found {len(img_files)} remote images.")
    for f in img_files:
        dest = os.path.join(LOCAL_IMAGE_DIR, f['name'])
        if not os.path.exists(dest):
            print(f"[DRIVE] Downloading image: {f['name']}")
            download_file(f['id'], dest)

    print("[DRIVE] Checking Google Drive Audio folder...")
    audio_files = list_files_in_folder(GOOGLE_DRIVE_AUDIO_FOLDER_ID, mime_type_prefix="audio/")
    print(f"[DRIVE] Found {len(audio_files)} remote audio files.")
    for f in audio_files:
        dest = os.path.join(LOCAL_AUDIO_DIR, f['name'])
        if not os.path.exists(dest):
            print(f"[DRIVE] Downloading audio: {f['name']}")
            download_file(f['id'], dest)

if __name__ == "__main__":
    sync_from_drive()
