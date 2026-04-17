"""
MiniMax Music Generator  —  Two-step pipeline
=============================================
Step 1: Lyrics Generation API  → auto-write structured lyrics from a theme
Step 2: Music Generation API   → compose & produce a complete MP3 from those lyrics

Falls back to Google Drive download if either step fails.

APIs used:
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

# Use music-2.6-free (all API-key holders).
# Switch to "music-2.6" if you upgrade to a Token / paid plan.
MINIMAX_MODEL = "music-2.6-free"

# Default theme used when no hint is available at all
_DEFAULT_THEME = "A soulful Bollywood song about love, longing, and hope. Melodious, emotional, cinematic."
_DEFAULT_STYLE = "Bollywood, melodious, soulful, romantic, emotional, cinematic, orchestral"


# ─── Step 1: Lyrics Generation ───────────────────────────────────────────────

def generate_lyrics_minimax(theme_prompt: str) -> str | None:
    """
    Call the MiniMax Lyrics Generation API to produce a full structured song
    (Verse, Chorus, Bridge, etc.) from a plain-text theme description.

    Args:
        theme_prompt: e.g. "A soulful Bollywood song about missing someone"

    Returns:
        Lyrics string ready to pass to generate_song_minimax(), or None on failure.
    """
    if not MINIMAX_API_KEY:
        print("  [Music] MINIMAX_API_KEY not set — cannot generate lyrics")
        return None

    try:
        import requests
    except ImportError:
        print("  [Music] 'requests' not installed — cannot call MiniMax API")
        return None

    print(f"  [Music] Step 1/2 — Generating lyrics via MiniMax Lyrics API...")
    print(f"  [Music]   Theme: {theme_prompt[:100]}")

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

    # Check API-level status
    base_resp = body.get("base_resp", {})
    if base_resp.get("status_code", -1) != 0:
        print(f"  [Music] Lyrics API error: {base_resp.get('status_msg', 'unknown')}")
        return None

    # Extract lyrics — field may be at data.lyrics or data.text depending on version
    data = body.get("data", {})
    lyrics = data.get("lyrics") or data.get("text") or ""
    if not lyrics:
        # Fallback: some versions return lyrics directly in body
        lyrics = body.get("lyrics") or body.get("text") or ""

    if not lyrics:
        print(f"  [Music] Lyrics API returned no lyrics content. Response: {str(body)[:200]}")
        return None

    line_count = len([l for l in lyrics.splitlines() if l.strip()])
    print(f"  [Music]   Lyrics generated: {line_count} lines")
    return lyrics


# ─── Step 2: Music Generation ─────────────────────────────────────────────────

def generate_song_minimax(music_prompt: str, lyrics: str, song_name: str = "generated_song") -> Path | None:
    """
    Call the MiniMax Music Generation API and save the result as an MP3.

    Args:
        music_prompt: Style/mood description e.g. "Bollywood, soulful, slow tempo"
        lyrics:       Full structured lyrics (output of generate_lyrics_minimax)
        song_name:    Base filename (no extension) for the saved MP3

    Returns:
        Path to the saved MP3, or None on failure.
    """
    if not MINIMAX_API_KEY:
        print("  [Music] MINIMAX_API_KEY not set — skipping music generation")
        return None

    try:
        import requests
    except ImportError:
        print("  [Music] 'requests' not installed")
        return None

    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in song_name)
    output_path = SONGS_DIR / f"{safe_name}.mp3"

    print(f"  [Music] Step 2/2 — Composing song via MiniMax Music API (model: {MINIMAX_MODEL})...")
    print(f"  [Music]   Style: {music_prompt[:80]}")

    payload = {
        "model": MINIMAX_MODEL,
        "prompt": music_prompt[:2000],
        "lyrics": lyrics[:3500],
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 256000,
            "format": "mp3"
        },
        "output_format": "hex"   # hex so we can save locally; url expires in 24h
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
            timeout=300      # music generation can take 2-4 minutes
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
        print(f"  [Music] Music API returned empty audio. Full response: {str(body)[:300]}")
        return None

    # Decode hex → raw bytes → MP3 file
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

    return output_path


# ─── Combined two-step flow ───────────────────────────────────────────────────

def generate_song_full(theme_prompt: str, music_style: str, song_name: str) -> Path | None:
    """
    Run the full two-step flow:
      1. Generate lyrics from theme_prompt  (Lyrics API)
      2. Compose the song from those lyrics (Music API)

    Args:
        theme_prompt: Plain-text theme, e.g. "A Bollywood song about missing someone at night"
        music_style:  Style string for the Music API, e.g. "Bollywood, soulful, orchestral"
        song_name:    Base filename for the saved MP3

    Returns:
        Path to the saved MP3, or None if either step fails.
    """
    # Step 1 — lyrics
    lyrics = generate_lyrics_minimax(theme_prompt)
    if not lyrics:
        print("  [Music] Lyrics generation failed — aborting music generation")
        return None

    # Step 2 — music
    return generate_song_minimax(music_style, lyrics, song_name)


# ─── High-level helper for main.py ───────────────────────────────────────────

def get_song(creds, theme_prompt: str, music_style: str, song_name: str = "generated_song",
             *, drive_fallback_fn=None, drive_file_id: str = None,
             drive_filename: str = None):
    """
    Obtain an audio file for the pipeline:

    1. Try the full MiniMax two-step flow (lyrics → music) → return (path, "minimax", None)
    2. On any failure, fall back to Google Drive download    → return (path, "drive", file_id)
    3. If both fail                                          → return (None, None, None)

    Args:
        creds:             Google OAuth credentials (for Drive fallback)
        theme_prompt:      Lyrics API theme, e.g. "Bollywood song about missing someone"
        music_style:       Music API style string, e.g. "Bollywood, soulful, slow tempo"
        song_name:         Base filename for the output MP3
        drive_fallback_fn: Callable(creds, file_id, filename) -> Path
        drive_file_id:     Drive file ID for fallback
        drive_filename:    Drive filename for fallback
    """
    # ── 1. Try MiniMax two-step flow ──────────────────────────────────────────
    print("  [Music] Starting MiniMax two-step generation (Lyrics -> Music)...")
    song_path = generate_song_full(theme_prompt, music_style, song_name)

    if song_path is not None:
        print(f"  [Music] Using MiniMax-generated song: {song_path.name}")
        return song_path, "minimax", None

    # ── 2. Fall back to Google Drive ─────────────────────────────────────────
    print("  [Music] MiniMax failed — falling back to Google Drive...")

    if drive_fallback_fn is None or drive_file_id is None or drive_filename is None:
        print("  [Music] No Drive fallback configured. Cannot obtain a song.")
        return None, None, None

    try:
        song_path = drive_fallback_fn(creds, drive_file_id, drive_filename)
        print(f"  [Music] Using Drive song: {drive_filename}")
        return song_path, "drive", drive_file_id
    except Exception as e:
        print(f"  [Music] Drive download also failed: {e}")
        return None, None, None
