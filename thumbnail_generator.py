"""
Aesthetic YouTube Thumbnail Generator (Raaga Blumes)
High-CTR, minimalist typography inspired by Calm Relaxation with Indian Classical depth:
- Auto-removes bottom-right AI watermarks (Gemini 4-point star / Grok logo) via OpenCV Telea inpainting
- 1280x720 16:9 cinematic framing with Lanczos scaling
- Rich color & contrast enhancement
- Smooth natural ambient dark shadow / scrim behind text areas (zero harsh boxes)
- Ultra-bold luxury serif typography (Cinzel-Black / PlayfairDisplay) for maximum mobile CTR
- Top-Right corner badge (e.g. "RAAG BAGESHRI · 432Hz" or "1 HOUR · 432Hz")
- Warm champagne gold subtitle + Solid crisp white main headline with Gaussian ambient drop shadow
"""

import os
import sys
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

RAAGA_HOOKS = [
    {"main": "STILL AWAKE AT 2 AM?", "sub": "Raag Bageshri · Deep Sleep"},
    {"main": "CLEAR ALL NEGATIVE ENERGY", "sub": "Raag Yaman · 432Hz Healing"},
    {"main": "STOP OVERTHINKING", "sub": "Raag Bhairavi · Inner Peace"},
    {"main": "INSTANT STRESS RELIEF", "sub": "Divine Bansuri Meditation"},
    {"main": "CALM YOUR MIND", "sub": "432Hz Positive Energy"},
    {"main": "REMOVE MENTAL BLOCKS", "sub": "Deep Peace & Healing"},
    {"main": "DEEP SLEEP INSTANTLY", "sub": "Night Bansuri · 432Hz"},
    {"main": "QUIET STILLNESS", "sub": "Indian Classical Flute Meditation"}
]

def get_font(font_name="Cinzel-Black.ttf", size=48):
    """Loads fonts with local asset priority and fallback to system fonts."""
    fonts = [
        os.path.join(SCRIPT_DIR, "assets", "fonts", font_name),
        os.path.join(SCRIPT_DIR, "assets", "fonts", "Cinzel-Black.ttf"),
        os.path.join(SCRIPT_DIR, "assets", "fonts", "PlayfairDisplay.ttf"),
        os.path.join(SCRIPT_DIR, "assets", "fonts", "Cinzel.ttf"),
        os.path.join(SCRIPT_DIR, "assets", "fonts", "Georgia-Bold.ttf"),
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"
    ]
    for f in fonts:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                pass
    return ImageFont.load_default()

def remove_thumbnail_watermark(pil_img):
    """Seamlessly inpaints and removes any AI watermark in the bottom-right corner."""
    if not CV2_AVAILABLE:
        return pil_img
    try:
        cv_img = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
        h, w = cv_img.shape[:2]

        # Mask bottom-right watermark region
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[int(h * 0.76):int(h * 0.95), int(w * 0.85):int(w * 0.98)] = 255

        inpainted = cv2.inpaint(cv_img, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
        return Image.fromarray(cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)).convert("RGBA")
    except Exception as e:
        print(f"[WARN] Watermark inpainting skipped: {e}")
        return pil_img

def draw_cinematic_text(draw_target, pos, text, font, fill_color, shadow_blur=10, shadow_offset=(3, 5), shadow_opacity=230):
    """
    Renders text with a smooth Gaussian ambient shadow + directional drop shadow.
    """
    w, h = draw_target.size
    shadow_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)

    # 1. Ambient soft shadow
    s_draw.text(pos, text, font=font, fill=(0, 0, 0, shadow_opacity))
    # 2. Directional offset shadow
    ox, oy = shadow_offset
    s_draw.text((pos[0] + ox, pos[1] + oy), text, font=font, fill=(0, 0, 0, int(shadow_opacity * 0.9)))

    # Gaussian blur
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))
    draw_target.alpha_composite(shadow_layer)

    # Draw crisp thick text on top
    text_layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    t_draw = ImageDraw.Draw(text_layer)
    t_draw.text(pos, text, font=font, fill=fill_color)
    draw_target.alpha_composite(text_layer)

def create_raaga_thumbnail(bg_path, output_path, main_text=None, sub_text=None, top_tag="RAAG BANSURI · 432Hz"):
    """
    Creates a clean, thick-font minimalist YouTube thumbnail with watermark removal.
    """
    if not main_text:
        preset = random.choice(RAAGA_HOOKS)
        main_text = preset["main"]
        sub_text = preset["sub"]

    # 1. Open and resize/crop to 1280x720 (16:9)
    img = Image.open(bg_path).convert("RGBA")
    target_w, target_h = 1280, 720

    if img.width / img.height > target_w / target_h:
        new_w = int(img.height * (target_w / target_h))
        offset = (img.width - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, img.height))
    else:
        new_h = int(img.width * (target_h / target_w))
        offset = (img.height - new_h) // 2
        img = img.crop((0, offset, img.width, offset + new_h))

    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # 2. Seamlessly remove bottom-right AI watermark
    img = remove_thumbnail_watermark(img)

    # 3. Rich color and contrast enhancement
    img = ImageEnhance.Color(img).enhance(1.08)
    img = ImageEnhance.Contrast(img).enhance(1.04)

    # 4. Smooth natural ambient dark shadow scrim behind text area
    scrim = Image.new("L", (target_w, target_h), 0)
    sdraw = ImageDraw.Draw(scrim)

    # Bottom-left text area smooth shadow
    for r in range(650, 0, -10):
        alpha = int((1.0 - (r / 650.0)**1.4) * 175)
        sdraw.ellipse([-140, target_h - 440, r * 1.9, target_h + 200], fill=alpha)

    # Top-right corner smooth shadow
    for r in range(360, 0, -10):
        alpha = int((1.0 - (r / 360.0)**1.4) * 140)
        sdraw.ellipse([target_w - r * 1.6, -90, target_w + 90, r * 1.3], fill=alpha)

    scrim = scrim.filter(ImageFilter.GaussianBlur(40))
    dark_bg = Image.new("RGBA", (target_w, target_h), (8, 6, 12, 255))
    canvas = Image.composite(dark_bg, img, scrim)

    font_main = get_font("Cinzel-Black.ttf", size=88 if len(main_text) <= 18 else 72)
    font_sub = get_font("Cinzel-Black.ttf", size=38)
    font_badge = get_font("Cinzel-Black.ttf", size=32)

    # --- 1. TOP-RIGHT BADGE ---
    if top_tag:
        dummy = ImageDraw.Draw(canvas)
        bbox = dummy.textbbox((0, 0), top_tag.upper(), font=font_badge)
        bw = bbox[2] - bbox[0]
        bx = target_w - bw - 70
        by = 48
        draw_cinematic_text(canvas, (bx, by), top_tag.upper(), font_badge, fill_color=(255, 240, 210, 255), shadow_blur=6, shadow_offset=(2, 4))

    # --- 2. BOTTOM-LEFT TEXT STACK ---
    x_pos = 70

    # Handle multi-line main headline if long
    main_words = main_text.strip().split()
    if len(main_text) > 22 and len(main_words) >= 3:
        mid = len(main_words) // 2
        line1 = " ".join(main_words[:mid]).upper()
        line2 = " ".join(main_words[mid:]).upper()
        main_lines = [line1, line2]
    else:
        main_lines = [main_text.upper()]

    line_height = 82 if len(main_lines) > 1 else 95
    y_base = target_h - 140 - (len(main_lines) - 1) * line_height
    sub_y = y_base - 56

    # Subtitle (Warm champagne gold)
    if sub_text:
        draw_cinematic_text(canvas, (x_pos, sub_y), sub_text.upper(), font_sub, fill_color=(255, 220, 130, 255), shadow_blur=8, shadow_offset=(2, 3))

    # Main Headline Lines (Crisp solid white)
    for idx, m_line in enumerate(main_lines):
        cur_y = y_base + idx * line_height
        draw_cinematic_text(canvas, (x_pos, cur_y), m_line, font_main, fill_color=(255, 255, 255, 255), shadow_blur=12, shadow_offset=(3, 6))

    # 5. Merge and save
    final = canvas.convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    final.save(output_path, quality=96)
    print(f"[+] Generated Clean High-CTR Thumbnail: {output_path}")
    return output_path

def create_thumbnail(bg_path, output_path, top_tag="RAAG BANSURI · 432Hz", lines=None, left_tag=None, **kwargs):
    """
    Backwards-compatible wrapper matching previous signature.
    """
    if isinstance(lines, list) and lines:
        main_text = " ".join(lines)
    elif isinstance(lines, str):
        main_text = lines
    else:
        main_text = "Deep Meditation"

    sub_text = kwargs.get("sub_text") or "Bansuri Flute · Inner Peace"
    return create_raaga_thumbnail(
        bg_path=bg_path,
        output_path=output_path,
        main_text=main_text,
        sub_text=sub_text,
        top_tag=top_tag
    )

if __name__ == "__main__":
    test_img = os.path.join(SCRIPT_DIR, "input_images")
    images = [os.path.join(test_img, f) for f in os.listdir(test_img) if f.lower().endswith(('.jpg', '.jpeg', '.png'))] if os.path.exists(test_img) else []
    if images:
        out_test = os.path.join(SCRIPT_DIR, "output_thumbnails", "test_raaga_thumb.jpg")
        create_raaga_thumbnail(images[0], out_test, "STILL AWAKE AT 2 AM?", "Raag Bageshri · 396Hz Deep Sleep", "RAAG BAGESHRI · 396Hz")
        print("Test thumbnail created at:", out_test)

