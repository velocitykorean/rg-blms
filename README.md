# 🪈 Raaga Blumes (rg-blms) — YouTube 1-Hour Meditation & Flute Video Bot

An automated Python bot suite designed for the **Raaga Blumes** YouTube channel to automatically create high-converting viral thumbnails and 1-hour (3600s) Full HD (1080p) Indian classical flute meditation videos.

---

## 📁 Directory Structure

```
raaga blumes/
├── assets/
│   └── fonts/
│       ├── PlayfairDisplay.ttf     <-- High-CTR Display Serif Font
│       └── Cinzel.ttf              <-- Classic All-Caps Serif Font
├── input_images/                   <-- Background images (.jpg / .png)
├── input_audio/                    <-- 100+ Indian Classical Bansuri Audio tracks (.mp3)
├── output_thumbnails/              <-- Generated YouTube thumbnails with text overlay
├── output_videos/                  <-- Generated 1-hour 1080p HD videos (3600s)
├── titles_descriptions.txt         <-- 30 YouTube titles, descriptions, hashtags & metadata
├── titles_descriptions_parser.py   <-- Parser for titles, descriptions & tags
├── thumbnail_generator.py          <-- Typography, vignette, flourishes & no-logo overlays
├── video_generator.py              <-- FFmpeg 1080p video rendering engine (1-hour audio loop)
├── google_drive_fetch.py           <-- Google Drive integration (Images & Audio sync)
├── auto_bot.py                     <-- Main automated bot script
└── README.md                       <-- Project documentation
```

---

## 🔗 Google Drive Links
- **Images Folder:** `https://drive.google.com/drive/folders/1QozOnV0LLfSdPcLE92CfnS0NkR03mF-v`
- **Audio Folder:** `https://drive.google.com/drive/folders/1Z8s1pdczQGesG1ALc9BQR64YJ2rQGWWR`

---

## 🚀 Usage

### 1. Run 1-Hour Video & Thumbnail Generation:
```bash
python auto_bot.py
```

### 2. Generate All 5 Thumbnail Presets:
```bash
python auto_bot.py --all-presets
```

### 3. Sync from Google Drive & Generate:
```bash
python auto_bot.py --sync-drive --all-presets
```

### 4. Custom Duration (e.g. 30 Minutes = 1800s):
```bash
python auto_bot.py --duration 1800
```
