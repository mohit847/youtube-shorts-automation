"""
MiniMax Music Generator  —  Two-step pipeline
=============================================
Step 1: Lyrics Generation API  → auto-write SHORT structured lyrics (30-50 sec)
                                 tailored to a specific Indian identity
Step 2: Music Generation API   → compose & produce a complete MP3

Falls back to Google Drive download if either step fails.

APIs:
  POST https://api.minimax.io/v1/lyrics_generation
  POST https://api.minimax.io/v1/music_generation
"""

import binascii
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MINIMAX_API_KEY, SONGS_DIR


# ─── Constants ────────────────────────────────────────────────────────────────

MINIMAX_LYRICS_URL = "https://api.minimax.io/v1/lyrics_generation"
MINIMAX_MUSIC_URL  = "https://api.minimax.io/v1/music_generation"

# music-2.6-free: available to all API-key holders (lower RPM)
# Switch to "music-2.6" on a Token / paid plan for higher RPM
MINIMAX_MODEL = "music-2.6-free"


# ─── Step 1: Lyrics Generation ───────────────────────────────────────────────

def generate_lyrics_minimax(song_theme: str, identity_name: str = "") -> str | None:
    """
    Call the MiniMax Lyrics Generation API to produce SHORT structured lyrics
    suitable for a 30–50 second song.

    Args:
        song_theme:     Vivid description of what the song should convey
        identity_name:  The Indian warrior / deity / figure the song is about

    Returns:
        Lyrics string (8–12 lines, [Verse] + [Chorus]) or None on failure.
    """
    if not MINIMAX_API_KEY:
        print("  [Music] MINIMAX_API_KEY not set — cannot generate lyrics")
        return None

    try:
        import requests
    except ImportError:
        print("  [Music] 'requests' not installed")
        return None

    subject_line = f" about {identity_name}" if identity_name else ""
    print(f"  [Music] Step 1/2 — Generating short lyrics (30-50 sec){subject_line}...")

    # ── CRITICAL: lyrics must be short so the generated song is 30-50 seconds ──
    theme_prompt = (
        f"Write a SHORT Hindi song{subject_line}.\n\n"
        f"Theme and Character Aura:\n{song_theme}\n\n"
        "CRITICAL CONSTRAINTS (MUST OBEY):\n"
        "1. SCRIPT: You MUST write the lyrics ENTIRELY in pure Hindi Devanagari script (e.g. मैं, शूरवीर, देवी). DO NOT use English letters or Roman transliteration. This guarantees the AI singer uses native Hindi pronunciation without a foreign accent.\n"
        "2. LENGTH: The song MUST NOT exceed 45 seconds.\n"
        "   - Generate exactly ONE [Verse] and ONE [Chorus] ONLY.\n"
        "   - The entire song must be maximum 6 to 8 short lines total.\n"
        "3. TONE: Strictly reflect the specified character's aura in the wording."
    )

    payload = {
        "mode": "write_full_song",
        "prompt": theme_prompt[:2000]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINIMAX_API_KEY}"
    }

    try:
        resp = requests.post(
            MINIMAX_LYRICS_URL,
            json=payload,
            headers=headers,
            timeout=60
        )
    except requests.exceptions.Timeout:
        print("  [Music] Lyrics API timed out (>60s)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [Music] Lyrics API network error: {e}")
        return None

    if resp.status_code != 200:
        print(f"  [Music] Lyrics API HTTP {resp.status_code}: {resp.text[:200]}")
        return None

    body = resp.json()
    base_resp = body.get("base_resp", {})
    if base_resp.get("status_code", -1) != 0:
        print(f"  [Music] Lyrics API error: {base_resp.get('status_msg', 'unknown')}")
        return None

    data = body.get("data", {})
    lyrics = data.get("lyrics") or data.get("text") or ""
    if not lyrics:
        lyrics = body.get("lyrics") or body.get("text") or ""

    if not lyrics:
        print(f"  [Music] Lyrics API returned no content. Response: {str(body)[:200]}")
        return None

    # Hard-trim to at most 15 non-empty, non-tag lines to guarantee short output
    lines = lyrics.splitlines()
    kept, content_count = [], 0
    for line in lines:
        stripped = line.strip()
        is_tag = stripped.startswith("[") and stripped.endswith("]")
        if is_tag:
            kept.append(line)
        elif stripped:
            if content_count < 15:
                kept.append(line)
                content_count += 1
        else:
            kept.append(line)  # keep blank lines for readability

    lyrics = "\n".join(kept).strip()
    print(f"  [Music]   Lyrics ready: {content_count} lines (target: < 45 sec)")
    print("  [Music]   === GENERATED LYRICS ===")
    for line in lyrics.splitlines():
        print(f"            {line}")
    print("  [Music]   ========================")
    
    return lyrics


# ─── Step 2: Music Generation ─────────────────────────────────────────────────

def generate_song_minimax(music_style: str, lyrics: str, song_name: str = "generated_song") -> Path | None:
    """
    Call the MiniMax Music Generation API and save the result as an MP3.

    Args:
        music_style: Style/mood tags e.g. "Devotional Bhajan, tabla, orchestral strings"
        lyrics:      Short structured lyrics (output of generate_lyrics_minimax)
        song_name:   Base filename (no extension) for the saved MP3

    Returns:
        Path to the saved MP3, or None on failure.
    """
    if not MINIMAX_API_KEY:
        print("  [Music] MINIMAX_API_KEY not set — skipping")
        return None

    try:
        import requests
    except ImportError:
        print("  [Music] 'requests' not installed")
        return None

    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in song_name)
    output_path = SONGS_DIR / f"{safe_name}.mp3"

    # CRITICAL: Force native Hindi diction to fix foreigner-accent issues and prevent long intros/outros
    enhanced_music_style = f"{music_style}, native Indian singer, traditional Indian vocals, absolute pure Hindi pronunciation, 0 intro, instant vocal start, no aalap, no raag, no humming before lyrics, immediate singing, no instrumental intro, no musical outro, proper clean fadeout ending"

    print(f"  [Music] Step 2/2 — Composing via MiniMax Music API (model: {MINIMAX_MODEL})...")
    print(f"  [Music]   Style: {enhanced_music_style[:90]}...")

    payload = {
        "model": MINIMAX_MODEL,
        "prompt": enhanced_music_style[:2000],
        "lyrics": lyrics[:3500],
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3"
        },
        "output_format": "hex"   # hex so we save locally; url expires in 24h
    }
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            MINIMAX_MUSIC_URL,
            json=payload,
            headers=headers,
            timeout=300       # generation can take 2-4 min
        )
    except requests.exceptions.Timeout:
        print("  [Music] Music API timed out (>300s)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [Music] Music API network error: {e}")
        return None

    if resp.status_code != 200:
        print(f"  [Music] Music API HTTP {resp.status_code}: {resp.text[:300]}")
        return None

    body = resp.json()
    base_resp = body.get("base_resp", {})
    if base_resp.get("status_code", -1) != 0:
        print(f"  [Music] Music API error: {base_resp.get('status_msg', 'unknown')}")
        return None

    audio_hex = body.get("data", {}).get("audio", "")
    if not audio_hex:
        print(f"  [Music] Music API returned empty audio. Response: {str(body)[:300]}")
        return None

    try:
        audio_bytes = binascii.unhexlify(audio_hex)
    except (binascii.Error, ValueError) as e:
        print(f"  [Music] Failed to decode audio hex: {e}")
        return None

    SONGS_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio_bytes)

    extra = body.get("extra_info", {})
    duration_s = extra.get("music_duration", 0) / 1000
    size_kb = len(audio_bytes) / 1024
    print(f"  [Music] Song saved: {output_path.name}  ({size_kb:.0f} KB, ~{duration_s:.0f}s)")

    if duration_s > 0 and not (25 <= duration_s <= 60):
        print(f"  [Music]   WARNING: Duration {duration_s:.0f}s is outside target 30-50s range")

    return output_path


# ─── Combined two-step flow ───────────────────────────────────────────────────

def generate_song_full(song_theme: str, music_style: str, song_name: str,
                       identity_name: str = "") -> Path | None:
    """
    Full two-step flow:
      1. Generate SHORT lyrics from song_theme  (Lyrics API)
      2. Compose the song from those lyrics     (Music API)

    Args:
        song_theme:    Plain-text theme for the lyrics
        music_style:   Style tags for the Music API
        song_name:     Base filename for the saved MP3
        identity_name: Identity being celebrated (shown in logs)

    Returns:
        Path to the saved MP3, or None if either step fails.
    """
    lyrics = generate_lyrics_minimax(song_theme, identity_name)
    if not lyrics:
        print("  [Music] Lyrics generation failed — aborting")
        return None
    return generate_song_minimax(music_style, lyrics, song_name)


# ─── High-level helper for main.py ───────────────────────────────────────────

def get_song(creds, song_theme: str, music_style: str, song_name: str = "generated_song",
             identity_name: str = "",
             *, drive_fallback_fn=None, drive_file_id: str = None,
             drive_filename: str = None):
    """
    Obtain an audio file for the pipeline:

    1. MiniMax two-step (lyrics → music)  → return (path, "minimax", None)
    2. Fallback: Google Drive download     → return (path, "drive",   file_id)
    3. Both fail                           → return (None, None,      None)

    Args:
        creds:             Google OAuth credentials (for Drive fallback)
        song_theme:        Theme passed to Lyrics API
        music_style:       Style passed to Music API
        song_name:         Output MP3 base filename
        identity_name:     Identity being celebrated (for logging)
        drive_fallback_fn: Callable(creds, file_id, filename) -> Path
        drive_file_id:     Drive file ID for fallback
        drive_filename:    Drive filename for fallback
    """
    print(f"  [Music] Starting MiniMax two-step generation (Lyrics -> Music)...")
    song_path = generate_song_full(song_theme, music_style, song_name, identity_name)

    if song_path is not None:
        print(f"  [Music] Using MiniMax-generated song: {song_path.name}")
        return song_path, "minimax", None

    print("  [Music] MiniMax failed — falling back to Google Drive...")
    if drive_fallback_fn is None or drive_file_id is None or drive_filename is None:
        print("  [Music] No Drive fallback configured.")
        return None, None, None

    try:
        song_path = drive_fallback_fn(creds, drive_file_id, drive_filename)
        print(f"  [Music] Using Drive song: {drive_filename}")
        return song_path, "drive", drive_file_id
    except Exception as e:
        print(f"  [Music] Drive download also failed: {e}")
        return None, None, None
