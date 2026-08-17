import os
import sys
import glob
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def upload_all_audio_to_drive():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sa_path = os.path.join(base_dir, 'service_account.json')
    audio_dir = os.path.join(base_dir, 'input_audio')
    folder_id = '1Z8s1pdczQGesG1ALc9BQR64YJ2rQGWWR'

    scopes = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=scopes)
    service = build('drive', 'v3', credentials=creds)

    # 1. Fetch existing files in Drive folder to avoid duplicate uploads
    print("[DRIVE UPLOAD] Fetching existing files in folder...")
    existing_files = set()
    page_token = None
    while True:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="nextPageToken, files(id, name)",
            pageSize=100,
            pageToken=page_token
        ).execute()
        for f in results.get('files', []):
            existing_files.add(f['name'])
        page_token = results.get('nextPageToken')
        if not page_token:
            break

    print(f"[DRIVE UPLOAD] Found {len(existing_files)} existing files in Drive folder.")

    # 2. Get local audio files
    local_files = sorted(glob.glob(os.path.join(audio_dir, "*.mp3")) + glob.glob(os.path.join(audio_dir, "*.wav")))
    print(f"[DRIVE UPLOAD] Found {len(local_files)} local audio files to process.")

    uploaded_count = 0
    skipped_count = 0

    for idx, fpath in enumerate(local_files, 1):
        fname = os.path.basename(fpath)
        if fname in existing_files:
            skipped_count += 1
            continue

        print(f"[{idx}/{len(local_files)}] Uploading: {fname}...")
        file_metadata = {
            'name': fname,
            'parents': [folder_id]
        }
        media = MediaFileUpload(fpath, mimetype='audio/mpeg', resumable=True)
        try:
            file_obj = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            uploaded_count += 1
            print(f"  --> Uploaded ID: {file_obj.get('id')}")
        except Exception as e:
            print(f"  [!] Failed to upload {fname}: {e}")

    print("==================================================")
    print(f"[DRIVE UPLOAD COMPLETE] Uploaded: {uploaded_count}, Skipped (already in Drive): {skipped_count}")
    print("==================================================")

if __name__ == "__main__":
    upload_all_audio_to_drive()
