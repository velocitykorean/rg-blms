import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

PRESETS = {
    "clear_negative_energy": {
        "top_tag": "RAAG BAGESHRI · 432Hz",
        "lines": ["Clear All", "Negative", "Energy"],
        "main_color": (145, 12, 18),
        "glow_style": "crimson"
    },
    "attract_positive_energy": {
        "top_tag": "RAAG YAMAN · 528Hz",
        "lines": ["Attract", "Positive", "Energy"],
        "main_color": (185, 75, 15),
        "glow_style": "gold"
    },
    "stop_overthinking": {
        "top_tag": "RAAG BHAIRAVI · 396Hz",
        "lines": ["Stop", "Overthinking", "Instantly"],
        "main_color": (145, 12, 18),
        "glow_style": "crimson"
    },
    "instant_stress_relief": {
        "top_tag": "MEDITATION BANSURI · 432Hz",
        "lines": ["Instant", "Stress", "Relief"],
        "main_color": (160, 20, 20),
        "glow_style": "crimson"
    },
    "remove_mental_blockages": {
        "top_tag": "DEEP HEALING · 432Hz",
        "lines": ["Remove", "Mental", "Blockages"],
        "main_color": (180, 50, 10),
        "glow_style": "gold"
    }
}

def get_font(font_name="PlayfairDisplay.ttf", size=48):
    """Cross-platform font loader with local asset priority."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    asset_font = os.path.join(script_dir, "assets", "fonts", font_name)
    if os.path.exists(asset_font):
        try:
            return ImageFont.truetype(asset_font, size)
        except Exception:
            pass

    # Secondary asset fallback
    cinzel_font = os.path.join(script_dir, "assets", "fonts", "Cinzel.ttf")
    if os.path.exists(cinzel_font):
        try:
            return ImageFont.truetype(cinzel_font, size)
        except Exception:
            pass

    # System fonts fallback (Linux & Windows)
    system_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\georgia.ttf",
        r"C:\Windows\Fonts\arial.ttf"
    ]
    for cand in system_candidates:
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                pass

    return ImageFont.load_default()

def draw_vignette(img, intensity=0.25):
    """Adds a soft warm vignette to frame the subject."""
    W, H = img.size
    mask = Image.new("L", (W, H), 0)
    draw_m = ImageDraw.Draw(mask)
    draw_m.ellipse([-W * 0.2, -H * 0.2, W * 1.2, H * 1.2], fill=int(255 * (1.0 - intensity)))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=int(W * 0.08)))
    
    dark = Image.new("RGBA", (W, H), (15, 6, 2, 255))
    return Image.composite(img, dark, mask)

def draw_top_flourish(draw, center_x, center_y, width=120, color=(240, 220, 175, 230)):
    """Draws a subtle elegant ornamental divider above typography."""
    draw.line([(center_x - width//2, center_y), (center_x + width//2, center_y)], fill=color, width=2)
    draw.polygon([(center_x, center_y - 4), (center_x + 5, center_y), (center_x, center_y + 4), (center_x - 5, center_y)], fill=color)
    draw.ellipse([center_x - width//2 - 6, center_y - 2, center_x - width//2 - 2, center_y + 2], fill=color)
    draw.ellipse([center_x + width//2 + 2, center_y - 2, center_x + width//2 + 6, center_y + 2], fill=color)

def create_thumbnail(bg_path, output_path, top_tag, lines, left_tag="WITH\nSHRI\nKRISHNA", font_name="PlayfairDisplay.ttf", main_color=(145, 12, 18), glow_style="crimson"):
    img = Image.open(bg_path).convert("RGBA")
    W, H = img.size
    
    img = draw_vignette(img, intensity=0.28)
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    num_lines = len(lines)
    if num_lines == 2:
        font_size = int(H * 0.16)
        line_height = int(H * 0.165)
        start_y = int(H * 0.30)
    elif num_lines == 3:
        font_size = int(H * 0.14)
        line_height = int(H * 0.14)
        start_y = int(H * 0.24)
    else:
        font_size = int(H * 0.12)
        line_height = int(H * 0.125)
        start_y = int(H * 0.20)
        
    font_main = get_font(font_name, font_size)
    font_top = get_font(font_name, int(H * 0.034))
    font_left = get_font(font_name, int(H * 0.024))
    
    # Left Tag ("WITH SHRI KRISHNA")
    left_x = int(W * 0.035)
    left_y = int(H * 0.46)
    for i, line in enumerate(left_tag.split("\n")):
        draw.text((left_x + 1, left_y + i * 26 + 1), line, font=font_left, fill=(20, 5, 0, 220))
        draw.text((left_x, left_y + i * 26), line, font=font_left, fill=(175, 110, 55, 240))
        
    # Right Content Center
    right_center_x = int(W * 0.68)
    
    # Top Tagline
    tag_bbox = draw.textbbox((0, 0), top_tag, font=font_top)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_x = right_center_x - tag_w // 2
    tag_y = start_y - int(H * 0.11)
    
    draw_top_flourish(draw, right_center_x, tag_y - 12, width=int(tag_w * 0.8), color=(235, 215, 165, 220))
    draw.text((tag_x + 1, tag_y + 1), top_tag, font=font_top, fill=(25, 10, 2, 230))
    draw.text((tag_x, tag_y), top_tag, font=font_top, fill=(245, 230, 190, 255))
    
    # Main Headline Lines
    for i, line in enumerate(lines):
        line_y = start_y + i * line_height
        bbox = draw.textbbox((0, 0), line, font=font_main)
        lw = bbox[2] - bbox[0]
        lx = right_center_x - lw // 2
        
        # Outer Deep Halo Shadow
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx*dx + dy*dy <= 18:
                    draw.text((lx + dx, line_y + dy), line, font=font_main, fill=(10, 3, 1, 190))
                    
        # Inner Warm Cream Outline
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    draw.text((lx + dx, line_y + dy), line, font=font_main, fill=(255, 245, 225, 250))
                    
        # Deep Velvet Fill
        draw.text((lx, line_y), line, font=font_main, fill=(*main_color, 255))
        
    out = Image.alpha_composite(img, txt_layer)
    out = out.convert("RGB")
    
    enhancer = ImageEnhance.Contrast(out)
    out = enhancer.enhance(1.08)
    
    out.save(output_path, "JPEG", quality=96)
    print(f"[THUMBNAIL] Generated clean high-CTR thumbnail: {output_path}")

def generate_preset_thumbnail(preset_key, bg_path, output_path):
    preset = PRESETS.get(preset_key, PRESETS["clear_negative_energy"])
    create_thumbnail(
        bg_path=bg_path,
        output_path=output_path,
        top_tag=preset["top_tag"],
        lines=preset["lines"],
        main_color=preset["main_color"],
        glow_style=preset["glow_style"]
    )
