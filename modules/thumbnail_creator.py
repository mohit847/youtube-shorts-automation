"""
Thumbnail Creator
Generates eye-catching thumbnails for YouTube Shorts using Pillow.
"""

import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import THUMBNAILS_DIR, FFMPEG_PATH


def extract_frame(video_path, output_path, timestamp=2.0):
    """Extract a single frame from the video at the given timestamp."""
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True, timeout=30)
    return Path(output_path)


def create_thumbnail(video_path, song_title, artist="", output_path=None):
    """
    Create a stunning thumbnail for the YouTube Short.

    Design:
    - Extract an interesting frame from the video
    - Apply color enhancement + vignette
    - Add bold song title with glow effect
    - Add artist name
    - Add music emoji/icon
    - Output: 1280x720 JPEG

    Returns the path to the generated thumbnail.
    """
    if output_path is None:
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in song_title)
        output_path = THUMBNAILS_DIR / f"{safe_name}_thumb.jpg"
    output_path = Path(output_path)

    # Extract frame from video
    frame_path = output_path.with_suffix(".temp.png")
    extract_frame(video_path, frame_path, timestamp=5.0)

    if frame_path.exists():
        img = Image.open(frame_path)
        # Resize to thumbnail dimensions (1280x720)
        img = img.resize((1280, 720), Image.LANCZOS)
    else:
        # If frame extraction fails, create a gradient background
        img = _create_gradient_background(1280, 720)

    # Enhance the image
    img = _enhance_image(img)

    # Add vignette effect
    img = _add_vignette(img)

    # Draw text overlays
    draw = ImageDraw.Draw(img)

    # Load font (try system fonts)
    title_font = _get_font(58)
    artist_font = _get_font(32)
    icon_font = _get_font(72)

    # Add music icon at top
    icon_text = "🎵"
    try:
        draw.text((640, 60), icon_text, font=icon_font, fill=(255, 105, 180),
                   anchor="mt", stroke_width=2, stroke_fill=(100, 0, 50))
    except Exception:
        draw.text((600, 40), "MUSIC", font=artist_font, fill=(255, 105, 180))

    # Add song title — big, bold, centered
    title_text = song_title.upper() if len(song_title) < 30 else song_title
    _draw_text_with_glow(draw, (640, 320), title_text, title_font,
                          fill=(255, 255, 255), glow_color=(123, 104, 238))

    # Add artist name
    if artist and artist != "Unknown Artist":
        _draw_text_with_glow(draw, (640, 400), artist, artist_font,
                              fill=(200, 200, 255), glow_color=(75, 0, 130))

    # Add "YouTube Shorts" badge
    badge_font = _get_font(22)
    # Draw badge background
    badge_w, badge_h = 200, 35
    badge_x, badge_y = 1050, 660
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=8, fill=(255, 0, 0, 200)
    )
    draw.text((badge_x + badge_w//2, badge_y + badge_h//2), "#SHORTS",
              font=badge_font, fill="white", anchor="mm")

    # Save
    img = img.convert("RGB")
    img.save(str(output_path), "JPEG", quality=95)

    # Cleanup temp frame
    if frame_path.exists():
        frame_path.unlink()

    print(f"  🖼️  Thumbnail created: {output_path}")
    return output_path


def _get_font(size):
    """Try to load a good font, fallback to default."""
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",     # Arial Bold (Windows)
        "C:/Windows/Fonts/impact.ttf",        # Impact (Windows)
        "C:/Windows/Fonts/segoeui.ttf",       # Segoe UI (Windows)
        "C:/Windows/Fonts/arial.ttf",         # Arial (Windows)
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _create_gradient_background(width, height):
    """Create a dark gradient background as fallback."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        r = int(13 + (45 - 13) * (y / height))
        g = int(13 + (27 - 13) * (y / height))
        b = int(43 + (105 - 43) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img


def _enhance_image(img):
    """Apply color and contrast enhancement."""
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    # Increase color saturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.4)

    # Slight brightness boost
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)

    return img


def _add_vignette(img):
    """Add a subtle vignette (dark edges) effect."""
    width, height = img.size
    vignette = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(vignette)

    # Draw concentric ellipses from bright center to dark edges
    for i in range(min(width, height) // 2, 0, -1):
        opacity = int(255 * (i / (min(width, height) / 2)))
        x0 = (width // 2) - i
        y0 = (height // 2) - int(i * height / width)
        x1 = (width // 2) + i
        y1 = (height // 2) + int(i * height / width)
        draw.ellipse([x0, y0, x1, y1], fill=opacity)

    # Apply vignette as a luminance mask
    img_rgba = img.convert("RGBA")
    vignette_rgba = Image.merge("RGBA", [
        vignette, vignette, vignette,
        Image.new("L", (width, height), 255)
    ])

    # Blend original with darkened version using vignette mask
    dark = ImageEnhance.Brightness(img).enhance(0.3)
    result = Image.composite(img, dark, vignette)

    return result


def _draw_text_with_glow(draw, position, text, font, fill=(255, 255, 255),
                          glow_color=(123, 104, 238)):
    """Draw text with a glow/outline effect."""
    x, y = position

    # Draw glow (multiple offset passes)
    for offset in range(3, 0, -1):
        alpha = 150 - offset * 40
        glow = (*glow_color[:3], max(0, alpha))
        try:
            draw.text((x, y), text, font=font, fill=glow, anchor="mm",
                      stroke_width=offset + 2, stroke_fill=glow)
        except Exception:
            # Fallback without anchor
            draw.text((x - len(text) * 10, y - 15), text,
                      font=font, fill=glow_color)
            break

    # Draw main text
    try:
        draw.text((x, y), text, font=font, fill=fill, anchor="mm",
                  stroke_width=2, stroke_fill=(0, 0, 0))
    except Exception:
        draw.text((x - len(text) * 10, y - 15), text, font=font, fill=fill)
