"""
9:16 Music Visualizer Video Creator
Creates stunning vertical videos using background images with waveform/spectrum overlays.
Images slide with Ken Burns effects for a professional look.
Lyric captions are displayed as stylish animated text like a pro editor.
"""

import subprocess
import json
import os
from pathlib import Path
from mutagen import File as MutagenFile

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, MAX_VIDEO_DURATION,
    INTRO_SKIP_SECONDS, VIDEOS_DIR, FFMPEG_PATH, FFPROBE_PATH,
    WATERMARK_TEXT, CHANNEL_NAME, CTA_TEXT, CTA_DURATION
)

# Portable font setup for GitHub Actions/CI deployment
_font_path = Path(__file__).parent.parent / "assets" / "fonts" / "Hind-Bold.ttf"
# FFmpeg drawtext requires Windows drive letters to have escaped colons: C\:/path...
_escaped_font_path = str(_font_path).replace("\\", "/").replace(":", r"\:")
FONT_BOLD = f"'{_escaped_font_path}'"
FONT_REGULAR = f"'{_escaped_font_path}'"


def get_audio_metadata(audio_path):
    """Extract metadata from an audio file."""
    audio_path = Path(audio_path)
    metadata = {
        "title": audio_path.stem,
        "artist": CHANNEL_NAME,
        "album": "",
        "duration": 0,
        "filename": audio_path.name
    }
    try:
        audio = MutagenFile(str(audio_path), easy=True)
        if audio:
            if audio.get("title"): metadata["title"] = audio["title"][0]
            if audio.get("artist"): metadata["artist"] = audio["artist"][0]
            if audio.get("album"): metadata["album"] = audio["album"][0]
            if hasattr(audio, "info") and audio.info:
                metadata["duration"] = audio.info.length
    except Exception:
        pass
    if metadata["duration"] == 0:
        try:
            result = subprocess.run(
                [FFPROBE_PATH, "-v", "quiet", "-print_format", "json",
                 "-show_format", str(audio_path)],
                capture_output=True, text=True
            )
            probe_data = json.loads(result.stdout)
            metadata["duration"] = float(probe_data["format"]["duration"])
        except Exception:
            metadata["duration"] = 60
    return metadata


import re

def _esc(text):
    """
    Escape text for FFmpeg drawtext filter.
    
    Escaping levels when filter_complex is passed as a subprocess list arg (no shell):
      Level 1 – FFmpeg filter-graph parser: \\ and ' are special inside '…' quoted values.
      Level 2 – drawtext text expander: % is special (strftime / metadata codes).
    
    Inside text='…':
      literal backslash  →  \\           (escaped at filter level)
      literal single-quote →  '\\''      (close quote, escaped quote, open quote)
      literal colon       →  as-is       (safe inside single-quoted value)
      literal percent     →  %%          (drawtext expansion level)
    
    Also strips emojis and control characters to prevent unreadable output.
    """
    if not isinstance(text, str):
        text = str(text)
        
    # Strip emojis and symbols (High blocks, Dingbats, Variation Selectors)
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'[\u2600-\u27bf]', '', text)
    text = re.sub(r'[\ufe00-\ufe0f]', '', text)
    
    # Strip ALL control characters (0x00-0x1F except \n) — especially \x0b (vertical tab)
    # which was previously used for line-wrapping but breaks FFmpeg's filter parser.
    text = re.sub(r'[\x00-\x09\x0b-\x0c\x0e-\x1f]', '', text)
    text = text.strip()
    
    # Log original text for debugging
    print(f"       _esc input: {repr(text[:80])}")
    
    # --- Level 1: FFmpeg filter-graph parser (inside single-quoted value) ---
    # Backslash is the escape character; single-quote ends the value.
    text = text.replace("\\", "\\\\")           # \ → \\
    text = text.replace("'", "'\\''")            # ' → '\'' (end-quote, literal ', start-quote)
    
    # --- Level 2: drawtext text expansion ---
    text = text.replace("%", "%%")              # % → %%
    
    # Remove characters that could break filter-graph syntax if they leak outside quotes
    for ch in ";[]{}":
        text = text.replace(ch, "")
    
    # Log escaped text
    print(f"       _esc output: {repr(text[:80])}")
    
    return text


def create_visualizer_video(audio_path, output_path=None, metadata=None,
                             analysis=None, background_images=None, cta_text=None):
    """
    Create a 9:16 music visualizer video with stylish lyric captions.
    
    If background_images are provided, creates a professional slideshow
    with Ken Burns zoom/pan effects + waveform/spectrum overlay + lyric captions.
    Otherwise, falls back to solid background with waveform + captions.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if metadata is None:
        metadata = get_audio_metadata(audio_path)

    # Use analysis data for naming (NOT displayed on video)
    song_name = analysis.get("song_name", metadata["title"]) if analysis else metadata["title"]

    if output_path is None:
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in song_name)
        output_path = VIDEOS_DIR / f"{safe_name}.mp4"
    output_path = Path(output_path)

    total_duration = metadata["duration"]
    start_time = min(INTRO_SKIP_SECONDS, max(0, total_duration - MAX_VIDEO_DURATION - 5))
    video_duration = min(MAX_VIDEO_DURATION, total_duration - start_time)
    if video_duration <= 0:
        start_time = 0
        video_duration = min(MAX_VIDEO_DURATION, total_duration)

    # Extract timed lyrics from analysis
    timed_lyrics = []
    if analysis:
        timed_lyrics = analysis.get("timed_lyrics", [])
        print(f"\n  📝 Lyrics Analysis:")
        print(f"     Timed lyrics count: {len(timed_lyrics)}")
        if timed_lyrics:
            print(f"     First lyric: {repr(timed_lyrics[0])}")
            if len(timed_lyrics) > 1:
                print(f"     Second lyric: {repr(timed_lyrics[1])}")
    
    # If no timed lyrics, fallback to simple string lines
    if not timed_lyrics and analysis:
        lyrics_text = analysis.get("lyrics", "")
        print(f"     Fallback to lyrics text: {repr(lyrics_text[:100])}...")
        if lyrics_text and lyrics_text != "Instrumental or lyrics unavailable":
            raw_lines = lyrics_text.replace("\r\n", "\n").split("\n")
            timed_lyrics = [{"text": l.strip()} for l in raw_lines if l.strip()]

    print(f"  🎬 Creating video: {song_name}")
    print(f"  ⏱️  Duration: {video_duration:.1f}s (from {start_time:.1f}s)")
    if timed_lyrics:
        print(f"  📝 Lyric captions: {len(timed_lyrics)} lines")

    # Strategy: use image backgrounds if available, otherwise waveform-only
    if background_images and len(background_images) > 0:
        valid_images = [p for p in background_images if Path(p).exists()]
        if valid_images:
            try:
                return _create_image_slideshow_video(
                    audio_path, output_path, valid_images,
                    timed_lyrics, start_time, video_duration,
                    cta_text=cta_text
                )
            except Exception as e:
                print(f"  ⚠️  Image slideshow failed: {e}")

    # Fallback: waveform-only video
    try:
        return _create_waveform_video(
            audio_path, output_path, timed_lyrics,
            start_time, video_duration, cta_text=cta_text
        )
    except Exception as e:
        print(f"  ⚠️  Waveform failed: {e}")
        return _create_minimal_video(
            audio_path, output_path, timed_lyrics,
            start_time, video_duration, cta_text=cta_text
        )


def _add_watermark_filters(input_label, output_label):
    """Adds a configurable watermark with a red vertical bar at the top left."""
    if not WATERMARK_TEXT:
        return [f"[{input_label}]null[{output_label}]"]
        
    escaped_text = _esc(WATERMARK_TEXT)
    
    # Render a red vertical rectangle, then render the text to its right
    filter_str = (
        f"[{input_label}]"
        f"drawbox=x=60:y=60:w=8:h=60:color=red@0.9:t=fill,"
        f"drawtext="
        f"fontfile={FONT_BOLD}:"
        f"text='{escaped_text}':"
        f"fontsize=55:"
        f"fontcolor=white:"
        f"x=85:y=62:"
        f"shadowcolor=black@0.6:shadowx=4:shadowy=4"
        f"[{output_label}]"
    )
    return [filter_str]


def _build_lyric_caption_filters(timed_lyrics, video_duration, input_label, output_label, cta_text=None):
    """
    Build FFmpeg drawtext filters for stylish animated lyric captions.
    Uses precise timestamps generated by AI for perfect lyric sync.
    Prevents temporal overlap between consecutive captions.
    """
    if not timed_lyrics:
        # No captions — just pass through
        print("  ⚠️  No lyrics provided for captions")
        return [f"[{input_label}]null[{output_label}]"]

    print(f"\n  📝 Building captions for {len(timed_lyrics)} lyric lines...")
    filters = []
    
    prev_label = input_label
    
    # Determine CTA start time so we can end captions before it
    final_cta = cta_text if cta_text else CTA_TEXT
    cta_start_time = max(0, video_duration - CTA_DURATION) if (final_cta and final_cta.strip()) else video_duration
    
    # --- Pre-process: collect valid caption entries with resolved times ---
    caption_entries = []
    for i, lyric_obj in enumerate(timed_lyrics):
        if isinstance(lyric_obj, str):
            line = lyric_obj
            start_t = min(3.0, video_duration * 0.1) + (i * 2.5)
            end_t = start_t + 2.5
        else:
            line = lyric_obj.get("text", "")
            start_t = float(lyric_obj.get("start", 0.0))
            end_t = float(lyric_obj.get("end", 0.0))
            
            if start_t == 0.0 and end_t == 0.0 and i > 0:
                prev_end = caption_entries[-1]["end"] if caption_entries else 0.0
                start_t = prev_end + 0.1
                end_t = start_t + 2.5
                
            if end_t - start_t < 1.0:
                end_t = start_t + 2.0

        # Skip if beyond video duration
        if start_t >= video_duration - 1.0:
            break
        end_t = min(end_t, video_duration - 0.5)
        
        # Skip empty/music-symbol lines early
        test_line = line.strip()
        test_line = __import__('re').sub(r'[\U00010000-\U0010ffff]', '', test_line)
        test_line = __import__('re').sub(r'[\u2600-\u27bf]', '', test_line)
        test_line = test_line.strip()
        if not test_line:
            continue
        
        caption_entries.append({"line": line, "start": start_t, "end": end_t, "idx": i})
    
    # --- Fix overlapping times: each caption ends before the next one starts ---
    for j in range(len(caption_entries) - 1):
        curr = caption_entries[j]
        nxt = caption_entries[j + 1]
        if curr["end"] > nxt["start"]:
            # Trim current caption to end just before next starts (with small gap for fade)
            curr["end"] = nxt["start"] - 0.05
            if curr["end"] <= curr["start"] + 0.3:
                # If trimming makes it too short, split the overlap evenly
                mid_time = (curr["start"] + nxt["start"]) / 2
                curr["end"] = mid_time
            print(f"     ⏱️  Trimmed caption {j+1} end to {curr['end']:.2f}s (avoid overlap with caption {j+2})")
    
    # --- Ensure last caption ends before CTA starts ---
    if caption_entries and cta_start_time < video_duration:
        last = caption_entries[-1]
        if last["end"] > cta_start_time - 0.5:
            last["end"] = cta_start_time - 0.5
            print(f"     ⏱️  Trimmed last caption end to {last['end']:.2f}s (before CTA)")
    
    # --- Pixel-accurate caption wrapping (same approach as CTA) ---
    from PIL import ImageFont
    cap_fontsize = 70
    max_cap_width = VIDEO_WIDTH - 100  # 50px margin each side
    
    try:
        cap_font = ImageFont.truetype(str(_font_path), cap_fontsize)
    except Exception:
        cap_font = ImageFont.load_default()
    
    cap_y_base = int(VIDEO_HEIGHT * 0.58)
    cap_line_spacing = cap_fontsize + 10
    
    # --- Build drawtext filters for each caption ---
    for j, entry in enumerate(caption_entries):
        line = entry["line"]
        start_t = entry["start"]
        end_t = entry["end"]
        i = entry["idx"]
        
        # Skip if duration is too short after trimming
        if end_t - start_t < 0.3:
            print(f"  📄 Caption {i+1}: ⚠️  Skipped (too short after overlap fix)")
            continue
        
        print(f"  📄 Caption {i+1}/{len(timed_lyrics)}:")
        print(f"     Original: {repr(line)}")
        print(f"     Time: {start_t:.2f}s - {end_t:.2f}s")

        # Wrap using actual pixel width measurement
        words = line.split()
        cap_lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip() if current else word
            bbox = cap_font.getbbox(test)
            text_w = bbox[2] - bbox[0] if bbox else 0
            if text_w > max_cap_width and current:
                cap_lines.append(current)
                current = word
            else:
                current = test
        if current:
            cap_lines.append(current)
        
        if len(cap_lines) > 1:
            print(f"     Wrapped into {len(cap_lines)} lines: {cap_lines}")
        
        # Skip empty
        all_escaped = [_esc(cl) for cl in cap_lines]
        if not any(el.strip() for el in all_escaped):
            print(f"     ⚠️  Skipped (empty after escaping)")
            continue
        
        # Calculate optimal fade time (max 0.3s, proportional to duration)
        duration = end_t - start_t
        fade_time = min(0.3, duration * 0.15)
        
        alpha_expr = (
            f"if(lt(t-{start_t},{fade_time}),"
            f"(t-{start_t})/{fade_time},"
            f"if(gt(t,{end_t - fade_time}),"
            f"({end_t}-t)/{fade_time},"
            f"1))"
        )
        
        # Center the caption block vertically around cap_y_base
        block_height = len(cap_lines) * cap_line_spacing
        block_start_y = cap_y_base - block_height // 2
        
        # Render each caption line as a separate drawtext filter
        for line_idx, cap_line in enumerate(cap_lines):
            cap_esc = all_escaped[line_idx]
            if not cap_esc.strip():
                continue
            line_y = block_start_y + (line_idx * cap_line_spacing)
            
            out_label = f"cap{i}_{line_idx}"
            
            drawtext_filter = (
                f"drawtext=fontfile={FONT_BOLD}:"
                f"text='{cap_esc}':"
                f"fontsize={cap_fontsize}:"
                f"fontcolor=white:"
                f"borderw=4:bordercolor=0x000000@0.8:"
                f"shadowcolor=black@0.6:shadowx=5:shadowy=5:"
                f"x='(w-text_w)/2':"
                f"y={line_y}:"
                f"alpha='{alpha_expr}':"
                f"enable='between(t,{start_t},{end_t})'"
            )
            filters.append(f"[{prev_label}]{drawtext_filter}[{out_label}]")
            prev_label = out_label
    
    # Guarantee the output label is produced and connected to the stream
    if not filters:
        filters.append(f"[{input_label}]null[{output_label}]")
    else:
        # Add CTA in the last few seconds
        if final_cta and final_cta.strip():
            cta_start = cta_start_time
            cta_end = video_duration
            cta_fade = 0.3
            
            cta_alpha = (
                f"if(lt(t-{cta_start},{cta_fade}),"
                f"(t-{cta_start})/{cta_fade},"
                f"if(gt(t,{cta_end - cta_fade}),"
                f"({cta_end}-t)/{cta_fade},"
                f"1))"
            )
            
            # --- Pixel-accurate CTA line wrapping ---
            # Use Pillow to measure actual text width with the real font,
            # so no word ever gets cropped regardless of language/script.
            from PIL import ImageFont
            cta_fontsize = 55
            max_text_width = VIDEO_WIDTH - 80  # 40px margin each side
            
            try:
                pil_font = ImageFont.truetype(str(_font_path), cta_fontsize)
            except Exception:
                pil_font = ImageFont.load_default()
            
            words = final_cta.split()
            cta_lines = []
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip() if current_line else word
                bbox = pil_font.getbbox(test_line)
                text_w = bbox[2] - bbox[0] if bbox else 0
                if text_w > max_text_width and current_line:
                    # Current word would overflow — push current line and start new
                    cta_lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                cta_lines.append(current_line)
            
            print(f"  📝 CTA Lines ({len(cta_lines)}):")
            for li, cl in enumerate(cta_lines):
                bbox = pil_font.getbbox(cl)
                px_w = bbox[2] - bbox[0] if bbox else 0
                print(f"     Line {li+1}: {repr(cl)} ({px_w}px / {max_text_width}px max)")
            
            cta_base_y = int(VIDEO_HEIGHT * 0.75)
            line_spacing = cta_fontsize + 12
            
            # Center the block vertically around cta_base_y
            total_block_height = len(cta_lines) * line_spacing
            block_start_y = cta_base_y - total_block_height // 2
            
            # Render each CTA line as a separate drawtext filter
            for line_idx, cta_line in enumerate(cta_lines):
                cta_esc = _esc(cta_line)
                line_y = block_start_y + (line_idx * line_spacing)
                
                cta_out_label = f"cta{line_idx}" if line_idx < len(cta_lines) - 1 else output_label
                
                cta_filter = (
                    f"drawtext=fontfile={FONT_BOLD}:"
                    f"text='{cta_esc}':"
                    f"fontsize={cta_fontsize}:"
                    f"fontcolor=white:"
                    f"borderw=3:bordercolor=0xFF0000@0.9:"
                    f"shadowcolor=black@0.7:shadowx=4:shadowy=4:"
                    f"x='(w-text_w)/2':"
                    f"y={line_y}:"
                    f"alpha='{cta_alpha}':"
                    f"enable='between(t,{cta_start},{cta_end})'"
                )
                filters.append(f"[{prev_label}]{cta_filter}[{cta_out_label}]")
                prev_label = cta_out_label
        else:
            filters.append(f"[{prev_label}]null[{output_label}]")
        
    return filters
def _create_image_slideshow_video(audio_path, output_path, images,
                                    timed_lyrics, start_time, video_duration, cta_text=None):
    """
    Create a video with image slideshow background + waveform overlay + lyric captions.
    Images transition with crossfade and Ken Burns zoom effects.
    NO song title, artist name, or filename displayed — only lyric captions.
    """
    num_images = len(images)
    slide_duration = video_duration / num_images
    fade_out_start = max(0, video_duration - 1.5)

    print(f"  📸 Using {num_images} background images (each {slide_duration:.1f}s)")

    # Build FFmpeg command with multiple image inputs
    cmd = [FFMPEG_PATH, "-y"]

    # Add audio input (index 0)
    cmd.extend(["-ss", str(start_time), "-t", str(video_duration),
                "-i", str(audio_path)])

    # Add image inputs (indices 1, 2, 3, ...)
    for img_path in images:
        cmd.extend(["-loop", "1", "-t", str(video_duration), "-i", str(img_path)])

    # Build the filter complex
    filters = []

    # --- Scale each image to 9:16 with Ken Burns zoom effect ---
    for i in range(num_images):
        input_idx = i + 1  # image inputs start from index 1
        zoom_speed = 0.0008 + (i % 3) * 0.0003  # Vary zoom speed per image
        filters.append(
            f"[{input_idx}:v]scale={VIDEO_WIDTH*2}:{VIDEO_HEIGHT*2},"
            f"zoompan=z='min(zoom+{zoom_speed},{1.3 + (i%2)*0.2})':"
            f"x='iw/2-(iw/zoom/2)+{20*(i%3)}':"
            f"y='ih/2-(ih/zoom/2)+{10*(i%2)}':"
            f"d={int(slide_duration * VIDEO_FPS)}:"
            f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
            f"fps={VIDEO_FPS}[img{i}]"
        )

    # List of safe, universally supported transitions
    transitions = [
        "fade", "dissolve", "pixelize", "fadeblack", "fadewhite", "zoomin"
    ]

    # --- Concatenate images with crossfade ---
    if num_images == 1:
        filters.append(f"[img0]trim=duration={video_duration},setpts=PTS-STARTPTS[slideshow]")
    elif num_images == 2:
        fade_d = min(1.0, slide_duration * 0.3)
        offset = slide_duration - fade_d
        trans = transitions[0]
        filters.append(
            f"[img0][img1]xfade=transition={trans}:duration={fade_d}:offset={offset}[slideshow]"
        )
    else:
        # Chain xfades for 3+ images
        prev = "img0"
        for i in range(1, num_images):
            fade_d = min(1.0, slide_duration * 0.3)
            offset = slide_duration * i - fade_d * i
            out_label = "slideshow" if i == num_images - 1 else f"xf{i}"
            trans = transitions[i % len(transitions)]
            filters.append(
                f"[{prev}][img{i}]xfade=transition={trans}:duration={fade_d}:offset={offset}[{out_label}]"
            )
            prev = out_label

    # --- Darken the slideshow slightly and add Vignette for a premium cinematic look ---
    filters.append(
        f"[slideshow]colorlevels=rimax=0.75:gimax=0.75:bimax=0.75,vignette=PI/4[darkened]"
    )

    # --- Audio waveform overlay (semi-transparent band in center) ---
    filters.append(f"[0:a]asplit=2[a_waves][a_fade]")
    filters.append(
        f"[a_waves]showwaves=s={VIDEO_WIDTH}x300:mode=cline:rate={VIDEO_FPS}"
        f":colors=0xFFFFFF@0.4|0x7B68EE@0.3:scale=cbrt[waves]"
    )
    wave_y = (VIDEO_HEIGHT - 300) // 2 + 200  # Slightly below center
    filters.append(
        f"[darkened][waves]overlay=0:{wave_y}:shortest=1:format=auto[with_waves]"
    )

    # --- Add Watermark ---
    watermark_filters = _add_watermark_filters("with_waves", "with_watermark")
    filters.extend(watermark_filters)

    # --- Stylish Lyric Captions (replaces old title/artist text) ---
    caption_filters = _build_lyric_caption_filters(
        timed_lyrics, video_duration, "with_watermark", "with_captions", cta_text=cta_text
    )
    filters.extend(caption_filters)

    # Fade in/out on whole video
    filters.append(
        f"[with_captions]fade=t=in:st=0:d=1.5,fade=t=out:st={fade_out_start}:d=1.5"
        f"[video_out]"
    )

    # Audio: fade in/out
    filters.append(
        f"[a_fade]afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_start}:d=1.5"
        f"[audio_out]"
    )

    filter_str = ";".join(filters)
    
    # Log filter complex for debugging
    print(f"\n  🔧 FFmpeg Filter Complex (first 500 chars):")
    print(f"     {filter_str[:500]}...")
    print(f"  📏 Total filter length: {len(filter_str)} characters")

    cmd.extend([
        "-filter_complex", filter_str,
        "-map", "[video_out]",
        "-map", "[audio_out]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-r", str(VIDEO_FPS),
        "-movflags", "+faststart",
        str(output_path)
    ])
    
    print(f"\n  ▶️  Running FFmpeg...")

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=600)

    if result.returncode != 0:
        err = result.stderr[-800:] if result.stderr else "Unknown"
        print(f"\n\n🚨 FFMPEG DEBUG 🚨")
        print(f"Filter complex:\n{filter_str}\n")
        print(f"Stderr:\n{err}\n")
        raise RuntimeError(f"FFmpeg error: {err}")

    print(f"  ✅ Video created: {output_path}")
    return output_path


def _create_waveform_video(audio_path, output_path, timed_lyrics,
                            start_time, video_duration, cta_text=None):
    """Waveform-only fallback on dark background with lyric captions."""
    fade_out_start = max(0, video_duration - 1.5)
    
    # Build caption filters as a separate step
    watermark_section = ""
    caption_section = ""
    
    wtmk_filters = _add_watermark_filters("base", "with_watermark")
    watermark_section = ";" + ";".join(wtmk_filters)
    
    if timed_lyrics:
        cap_filters = _build_lyric_caption_filters(
            timed_lyrics, video_duration, "with_watermark", "with_captions", cta_text=cta_text
        )
        caption_section = ";" + ";".join(cap_filters)
        final_label = "with_captions"
    else:
        final_label = "with_watermark"

    fc = (
        f"color=c=0x0d0d2b:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={video_duration}:r={VIDEO_FPS}[bg];"
        f"[0:a]asplit=2[a_waves][a_fade];"
        f"[a_waves]showwaves=s={VIDEO_WIDTH}x500:mode=cline:rate={VIDEO_FPS}"
        f":colors=0x7B68EE|0x00CED1:scale=cbrt[waves];"
        f"[bg][waves]overlay=0:{(VIDEO_HEIGHT-500)//2}:shortest=1[base]"
        f"{watermark_section}{caption_section};"
        f"[{final_label}]fade=t=in:st=0:d=1.5,fade=t=out:st={fade_out_start}:d=1.5[video_out];"
        f"[a_fade]afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_start}:d=1.5[audio_out]"
    )
    return _run_ffmpeg(audio_path, output_path, fc, start_time, video_duration)


def _create_minimal_video(audio_path, output_path, timed_lyrics,
                           start_time, video_duration, cta_text=None):
    """Absolute minimal fallback with lyric captions only."""
    fade_out_start = max(0, video_duration - 1.5)
    
    # Build caption filters
    watermark_section = ""
    caption_section = ""
    
    wtmk_filters = _add_watermark_filters("bg", "with_watermark")
    watermark_section = ";" + ";".join(wtmk_filters)
    
    if timed_lyrics:
        cap_filters = _build_lyric_caption_filters(
            timed_lyrics, video_duration, "with_watermark", "with_captions", cta_text=cta_text
        )
        caption_section = ";" + ";".join(cap_filters)
        final_label = "with_captions"
    else:
        final_label = "with_watermark"

    fc = (
        f"color=c=0x0d0d2b:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={video_duration}:r={VIDEO_FPS}[bg]"
        f"{watermark_section}{caption_section};"
        f"[{final_label}]fade=t=in:st=0:d=1.5,fade=t=out:st={fade_out_start}:d=1.5[video_out];"
        f"[0:a]afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out_start}:d=1.5[audio_out]"
    )
    return _run_ffmpeg(audio_path, output_path, fc, start_time, video_duration)


def _run_ffmpeg(audio_path, output_path, filter_complex, start_time, video_duration):
    """Execute FFmpeg."""
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", str(start_time), "-t", str(video_duration),
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[video_out]", "-map", "[audio_out]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-r", str(VIDEO_FPS),
        "-movflags", "+faststart",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=600)
    if result.returncode != 0:
        err = result.stderr[-800:] if result.stderr else "Unknown"
        print(f"\n\n🚨 FFMPEG DEBUG 🚨")
        print(f"Filter complex:\n{filter_complex}\n")
        print(f"Stderr:\n{err}\n")
        raise RuntimeError(f"FFmpeg error: {err}")
    print(f"  ✅ Video created: {output_path}")
    return output_path
