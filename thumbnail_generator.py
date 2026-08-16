import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Built-in presets for high-converting YouTube thumbnails
PRESETS = {
    "clear_negative_energy": {
        "top_tag": "DIVINE FLUTE MUSIC · 432Hz",
        "lines": ["Clear All", "Negative", "Energy"],
        "font": "PlayfairDisplay.ttf",
        "color": (145, 12, 18),
        "style": "crimson"
    },
    "attract_positive_energy": {
        "top_tag": "DEEP HEALING & PEACE",
        "lines": ["Attract", "Positive", "Energy"],
        "font": "PlayfairDisplay.ttf",
        "color": (235, 185, 60),
        "style": "gold_text"
    },
    "stop_overthinking": {
        "top_tag": "INSTANT ANXIETY RELIEF",
        "lines": ["Stop", "Overthinking", "Instantly"],
        "font": "PlayfairDisplay.ttf",
        "color": (150, 12, 18),
        "style": "crimson"
    },
    "instant_stress_relief": {
        "top_tag": "MEDITATION & SLEEP MUSIC",
        "lines": ["INSTANT", "STRESS", "RELIEF"],
        "font": "Cinzel.ttf",
        "color": (140, 10, 15),
        "style": "gold"
    },
    "remove_mental_blockages": {
        "top_tag": "FLUTE · SITAR · TABLA",
        "lines": ["Remove", "Mental", "Blockages"],
        "font": "PlayfairDisplay.ttf",
        "color": (138, 12, 18),
        "style": "crimson"
    }
}

def draw_vignette(img, intensity=0.28):
    """Adds a subtle vignette/glow behind the right side text to elevate contrast."""
    W, H = img.size
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for x in range(int(W * 0.42), W):
        progress = (x - int(W * 0.42)) / (W * 0.58)
        alpha = int(220 * (progress ** 1.7) * intensity)
        draw.line([(x, 0), (x, H)], fill=(30, 8, 4, alpha))
        
    return Image.alpha_composite(img, overlay)

def draw_flourish(draw, center_x, center_y, width, color=(140, 25, 25, 230)):
    """Draws an elegant ornate line with central ornament under the tagline."""
    x1 = center_x - width // 2
    x2 = center_x + width // 2
    
    draw.line([(x1, center_y), (x2, center_y)], fill=color, width=2)
    d_size = 5
    draw.polygon([
        (center_x - d_size, center_y),
        (center_x, center_y - d_size),
        (center_x + d_size, center_y),
        (center_x, center_y + d_size)
    ], fill=color)
    draw.ellipse([center_x - width//2 - 6, center_y - 2, center_x - width//2 - 2, center_y + 2], fill=color)
    draw.ellipse([center_x + width//2 + 2, center_y - 2, center_x + width//2 + 6, center_y + 2], fill=color)

def create_thumbnail(bg_path, output_path, top_tag, lines, left_tag="WITH\nSHRI\nKRISHNA", font_name="PlayfairDisplay.ttf", main_color=(145, 12, 18), glow_style="crimson"):
    img = Image.open(bg_path).convert("RGBA")
    W, H = img.size
    
    img = draw_vignette(img, intensity=0.28)
    txt_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    # Locate font file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(script_dir, "assets", "fonts", font_name)
    if not os.path.exists(font_path):
        font_path = os.path.join(r"C:\Windows\Fonts", "georgiab.ttf")
        
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
        
    font_main = ImageFont.truetype(font_path, font_size)
    font_top = ImageFont.truetype(font_path, int(H * 0.034))
    font_left = ImageFont.truetype(r"C:\Windows\Fonts\georgia.ttf", int(H * 0.024))
    
    # Left Tag ("WITH SHRI KRISHNA")
    left_x = int(W * 0.035)
    left_y = int(H * 0.46)
    for i, line in enumerate(left_tag.split("\n")):
        draw.text((left_x + 1, left_y + i * 26 + 1), line, font=font_left, fill=(20, 5, 0, 220))
        draw.text((left_x, left_y + i * 26), line, font=font_left, fill=(175, 110, 55, 240))
        
    # Right Content Center
    right_center_x = int(W * 0.68)
    
    # Top Tagline
    top_text = top_tag.upper()
    letter_space = 7
    top_width = sum([font_top.getlength(c) + letter_space for c in top_text]) - letter_space
    top_x = right_center_x - int(top_width / 2)
    top_y = int(H * 0.14)
    
    curr_x = top_x
    for c in top_text:
        draw.text((curr_x + 1, top_y + 1), c, font=font_top, fill=(30, 5, 0, 200))
        draw.text((curr_x, top_y), c, font=font_top, fill=(125, 25, 25, 240))
        curr_x += font_top.getlength(c) + letter_space
        
    # Flourish Under Top Tag
    flourish_y = top_y + int(H * 0.05)
    draw_flourish(draw, right_center_x, flourish_y, int(top_width * 0.75), color=(135, 25, 25, 220))
    
    # Main Headline Text
    for i, line in enumerate(lines):
        line_w = font_main.getlength(line)
        lx = right_center_x - int(line_w / 2)
        ly = start_y + i * line_height
        
        # Shadow
        for dx, dy, a in [(-4, -4, 170), (4, 4, 190), (-4, 4, 170), (4, -4, 170), (0, 6, 240), (6, 0, 240), (0, -6, 220), (-6, 0, 220)]:
            draw.text((lx + dx, ly + dy), line, font=font_main, fill=(15, 2, 2, a))
            
        if glow_style == "gold":
            draw.text((lx - 1, ly - 1), line, font=font_main, fill=(255, 215, 120, 200))
            draw.text((lx, ly), line, font=font_main, fill=main_color)
        elif glow_style == "gold_text":
            draw.text((lx, ly), line, font=font_main, fill=(245, 195, 75))
            draw.text((lx - 1, ly - 1), line, font=font_main, fill=(255, 240, 180, 220))
        else:
            draw.text((lx - 1, ly - 1), line, font=font_main, fill=(255, 220, 150, 180))
            draw.text((lx, ly), line, font=font_main, fill=main_color)

    # NOTE: NO LOGO / EMBLEM IN CORNER (As requested by user)

    final_img = Image.alpha_composite(img, txt_layer)
    final_img.convert("RGB").save(output_path, quality=98)
    print(f"[THUMBNAIL OK - NO LOGO] Saved: {output_path}")

def generate_preset_thumbnail(bg_path, output_path, preset_name="clear_negative_energy"):
    if preset_name not in PRESETS:
        preset_name = "clear_negative_energy"
    config = PRESETS[preset_name]
    create_thumbnail(
        bg_path,
        output_path,
        top_tag=config["top_tag"],
        lines=config["lines"],
        font_name=config["font"],
        main_color=config["color"],
        glow_style=config["style"]
    )
