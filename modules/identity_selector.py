"""
Identity Selector
=================
Uses Gemini to pick ONE unique Indian historical / mythological identity
for each song creation run, ensuring no identity is repeated.

Tracks used identities in: output/used_identities.json

Categories covered (from user spec):
  1. Ancient Indian Warriors (Mahabharata, Ramayana, regional kingdoms)
  2. Medieval Indian Warriors (excluding Mughal rulers / generals)
  3. Rajput Warriors
  4. Maratha Warriors
  5. South Indian Warriors (Chola, Pandya, Vijayanagara, etc.)
  6. Sikh Warriors and Punjabi Gurus
  7. Indian Freedom Fighters (pre-1947)
  8. Tribal and Regional Warriors of India
  9. Hindu Gods and Goddesses
 10. Other Indian Deities (folk, regional, lesser-known)
 11. Legendary and Mythological Warriors
"""

import json
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import GEMINI_API_KEY, OUTPUT_DIR


USED_IDENTITIES_LOG = OUTPUT_DIR / "used_identities.json"

# ─── Persistence ──────────────────────────────────────────────────────────────

def load_used_identities() -> list:
    """Load previously used identity entries from disk."""
    if USED_IDENTITIES_LOG.exists():
        try:
            with open(USED_IDENTITIES_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_used_identity(identity: dict) -> None:
    """Append a newly selected identity to the log."""
    entries = load_used_identities()
    entries.append({**identity, "used_at": datetime.now().isoformat()})
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(USED_IDENTITIES_LOG, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


# ─── Gemini selection ─────────────────────────────────────────────────────────

def select_identity() -> dict:
    """
    Ask Gemini to choose ONE fresh Indian identity from the defined categories.
    Avoids any identity already in used_identities.json.

    Returns a dict with keys:
        name          – full name of the identity
        category      – which of the 11 categories they belong to
        description   – 2-3 sentence cultural/historical summary
        song_theme    – vivid theme for a SHORT Hindi devotional/heroic song
        music_style   – MiniMax music style string
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError("google-genai package not installed")

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env")

    client = genai.Client(api_key=GEMINI_API_KEY)

    used = load_used_identities()
    used_names = [e.get("name", "") for e in used]
    
    # ── TOKEN SAVING OPTIMIZATION ──
    # Only pass the last 30 used identities to Gemini. 
    # This prevents the prompt from ballooning in size while still avoiding recent repeats.
    recent_used_names = used_names[-30:] if len(used_names) > 30 else used_names
    used_list_str = ", ".join(recent_used_names) if recent_used_names else "None yet"

    print(f"  [Identity] {len(used_names)} identities used so far. Selecting a new one (memory truncated to 30 to save tokens)...")

    prompt = f"""Act as a historian and cultural expert specialising in Indian history,
religion, and warrior traditions.

Your task: pick ONE identity for an inspiring Hindi devotional or heroic song.

ELIGIBLE CATEGORIES (choose from any):
1. Ancient Indian Warriors (Mahabharata, Ramayana, regional kingdoms)
2. Medieval Indian Warriors (excluding Mughal rulers and generals)
3. Rajput Warriors
4. Maratha Warriors
5. South Indian Warriors (Chola, Pandya, Vijayanagara, etc.)
6. Sikh Warriors and Punjabi Gurus
7. Indian Freedom Fighters (pre-1947)
8. Tribal and Regional Warriors of India
9. Hindu Gods and Goddesses
10. Other Indian Deities (folk, regional, lesser-known)
11. Legendary and Mythological Warriors

STRICT RULES:
- Do NOT include Mughal rulers or Mughal generals.
- Pick someone who has strong visual imagery, inspiring stories, or deep devotional significance.
- Vary the category across runs — don't always pick gods; mix warriors, freedom fighters, etc.
- NEVER pick any name from this already-used list: {used_list_str}

CRITICAL REQUIREMENT:
The song must PERFECTLY reflect the character's unique aura, personality, persona, and legendary traits. 
Their unmatched bravery, their serene divinity, their fierce rage, or their supreme devotion MUST dictate everything from the lyrics to the musical instruments, energy, and specifically the SINGER'S VOICE.

RESPOND IN THIS EXACT JSON (no markdown, no code block):
{{
  "name": "Full name of the identity (English transliteration)",
  "category": "Category name from the list above",
  "description": "2-3 sentences about who they are and why they are celebrated in Indian culture.",
  "song_theme": "A vividly detailed theme for a short (< 40 second) Hindi devotional or heroic song. You MUST explicitly describe their personality, aura (e.g. fierce, divine, calming, aggressive, regal, kind-hearted), and character traits. Tell the lyricist EXACTLY how the tone should mirror the core essence of this specific identity. 3-4 sentences.",
  "music_style": "Comma-separated MiniMax music style tags perfectly matching their personality/aura. You MUST explicitly describe the vocal style and the EXACT tempo/speed of the song (e.g. fast-paced, slow tempo). E.g. for a fierce warrior: 'Aggressive battle drums, fast tempo, heavy bass, fierce, high energy, powerful roaring male Indian vocals, pure authentic Hindi pronunciation'. For a kind-hearted mother goddess: 'Serene flute, slow soothing tempo, soft tabla, divine, calming, peaceful, sweet kind-hearted authentic female Indian vocals, absolute pure native Hindi pronunciation'."
}}"""

    models_to_try = [
        "gemini-2.5-flash", 
        "gemini-3.1-flash-lite-preview", 
        "gemini-2.0-flash", 
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b"
    ]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            text = response.text.strip()
            # Strip markdown wrappers if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("\n", 1)[0]
            if text.startswith("json"):
                text = text[4:].strip()

            identity = json.loads(text)
            
            # ── STRICT PYTHON VALIDATION ──
            # Even though Gemini only knows the last 30 names, we check the ENTIRE history locally!
            generated_name = identity.get("name", "").strip().lower()
            if generated_name in [n.strip().lower() for n in used_names]:
                raise ValueError(f"Identity '{identity.get('name')}' is an ancient duplicate not in the truncated prompt! Retrying...")

            # Validate required keys
            for key in ("name", "category", "description", "song_theme", "music_style"):
                if key not in identity:
                    raise ValueError(f"Missing key: {key}")

            print(f"  [Identity] Selected : {identity['name']}")
            print(f"  [Identity] Category : {identity['category']}")
            print(f"  [Identity] Theme    : {identity['song_theme'][:100]}...")

            save_used_identity(identity)
            return identity

        except json.JSONDecodeError as e:
            print(f"  [Identity] Bad JSON from {model_name}: {e} — retrying...")
            continue
        except Exception as e:
            err = str(e)
            if "quota" in err.lower() or "429" in err:
                print(f"  [Identity] {model_name} quota hit — trying next model...")
                continue
            print(f"  [Identity] {model_name} error: {err[:120]} — retrying...")
            continue

    raise RuntimeError("Identity selection failed: all Gemini models exhausted")
