import os
import re
import json

def parse_titles_descriptions(file_path):
    """
    Parses the 30 YouTube titles, descriptions, and metadata from the text file.
    Returns a list of structured track dictionary objects.
    """
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by separator line
    sections = re.split(r'={20,}', content)
    tracks = []

    for sec in sections:
        sec = sec.strip()
        if not sec or "YOUTUBE TITLE" not in sec:
            continue

        # Extract Title
        title_match = re.search(r'YOUTUBE TITLE\s+(\d+)\.\s+(.*?)(?=\n\s*DESCRIPTION|\n\n|\Z)', sec, re.DOTALL)
        if not title_match:
            continue

        item_num = int(title_match.group(1))
        raw_title = ' '.join(title_match.group(2).split()).strip()

        # Extract Description
        desc_match = re.search(r'DESCRIPTION\s+(.*?)(?=\n\s*🎵|\n\s*#|\Z)', sec, re.DOTALL)
        raw_desc = ' '.join(desc_match.group(1).split()).strip() if desc_match else ""

        # Extract metadata line (Raag, Instrument, Tuning, Mood)
        meta_match = re.search(r'🎵\s*Raag:\s*(.*?)\s*🎻\s*Instrument:\s*(.*?)\s*🔊\s*Tuning\s*concept:\s*(.*?)\s*(?:🌿|🌙|🌅|✨)?\s*Mood:\s*(.*?)(?=\n|\Z)', sec)
        raag = meta_match.group(1).strip() if meta_match else ""
        instrument = meta_match.group(2).strip() if meta_match else "Bansuri"
        tuning = meta_match.group(3).strip() if meta_match else "432Hz"
        mood = meta_match.group(4).strip() if meta_match else "Peaceful, meditative"

        # Extract hashtags
        tags = re.findall(r'#\w+', sec)

        # Full description text
        full_desc = f"{raw_desc}\n\n🎵 Raag: {raag}\n🎻 Instrument: {instrument}\n🔊 Tuning: {tuning}\n🌿 Mood: {mood}\n\n{' '.join(tags)}"

        # Generate viral thumbnail hook from title (e.g. "Still Awake at 2 AM?", "Calm the Mind", "Quiet Overthinking")
        hook_match = re.match(r'^(.*?)(?:\s*[\|·\-\(]|\s+Raag|\s+for)', raw_title)
        if hook_match:
            hook = hook_match.group(1).strip()
            # Clean emojis from hook for thumbnail
            hook_clean = re.sub(r'[^\w\s\?!\'\"&]', '', hook).strip()
        else:
            hook_clean = "Deep Meditation"

        tracks.append({
            "index": item_num,
            "title": raw_title,
            "hook": hook_clean,
            "description": full_desc,
            "raag": raag,
            "tuning": tuning,
            "mood": mood,
            "tags": tags
        })

    return tracks

def get_parsed_json_path(base_dir=None):
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    txt_file = os.path.join(base_dir, "titles_descriptions.txt")
    json_file = os.path.join(base_dir, "parsed_titles.json")
    
    tracks = parse_titles_descriptions(txt_file)
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, indent=2, ensure_ascii=False)
    return tracks

if __name__ == "__main__":
    t = get_parsed_json_path()
    print(f"Successfully parsed {len(t)} tracks from titles_descriptions.txt!")
