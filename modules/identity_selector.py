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
The song MUST perfectly reflect the character's unique aura, personality, and legendary traits.
The music_style you generate is the SINGLE MOST IMPORTANT field — it directly controls the tempo,
energy, instruments, and mood of the generated song. Use it to make each song feel completely
different from the last.

MUSIC STYLE GUIDE — match the character type to the appropriate energy level:

  ⚔️  FIERCE WARRIORS (battle heroes, Kshatriyas, Rajput/Maratha warriors at war):
      → 140–160 BPM, aggressive battle drums, thundering dhol, war trumpets, heavy bass,
        intense powerful roaring male vocals, high energy, fast-paced, fierce, relentless,
        orchestral strings in rapid staccato, feels like a war cry on a battlefield.
        Example: "Fast-paced 150 BPM war anthem, thundering battle drums, heavy dhol, brass war trumpets,
        powerful roaring male Indian vocals, aggressive, fierce, intense, relentless high energy, orchestral strings"

  🧘  DIVINE PEACEFUL GODS (Vishnu, Ram, calm avatar forms, meditative deities):
      → 50–70 BPM, slow gentle tempo, serene Bansuri flute, soft harmonium, light tabla,
        warm resonant male vocals, devotional, spiritual, divine, peaceful, uplifting.
        Example: "Slow 60 BPM devotional bhajan, serene Bansuri flute, warm harmonium, gentle tabla,
        resonant deep male Indian vocals, peaceful, divine, uplifting, meditative, spiritual warmth"

  🔱  POWERFUL DESTROYER GODS (Shiva in Rudra form, Kali, Durga in battle, Mahakaal):
      → 100–130 BPM, dramatic, intense, deep resonant male/female chant, thunderous tabla,
        electric sitar, drone bass, cinematic orchestral swells, raw power meets divinity,
        feels both terrifying and awe-inspiring.
        Example: "Intense 120 BPM Shiva chant, thunderous tabla, electric sitar, deep resonant male vocals,
        dramatic orchestral swells, raw divine power, cinematic, awe-inspiring, powerful drone bass"

  🌸  MOTHER GODDESSES / NURTURING DEITIES (Lakshmi, Saraswati, Parvati in gentle form):
      → 40–60 BPM, very slow, soft, gentle, flute-led melody, sitar, gentle tabla,
        sweet melodious female vocals, devotional, tender, motherly warmth, divine grace.
        Example: "Very slow 50 BPM Saraswati bhajan, soft Bansuri flute, gentle sitar, light tabla,
        sweet melodious female Indian vocals, tender, graceful, divine, soothing, devotional"

  🦁  FREEDOM FIGHTERS / REVOLUTIONARY HEROES:
      → 120–140 BPM, patriotic anthem style, proud march beat, snare drums, brass section,
        powerful passionate male vocals, stirring, emotional, inspiring, rebellious energy,
        feels like a rally cry for the nation.
        Example: "Patriotic 130 BPM march anthem, proud snare drums, brass section, passionate powerful
        male Indian vocals, stirring, emotional, inspiring, rebellious, nationalistic, march tempo"

  🏹  EPIC MYTHOLOGICAL HEROES (Arjuna, Karna, Hanuman in battle, Parashurama):
      → 110–140 BPM, epic cinematic style, orchestral strings, tabla, dramatic builds and drops,
        heroic powerful male vocals, legendary, grand, mythological, larger-than-life feeling.
        Example: "Epic 125 BPM cinematic hero anthem, orchestral strings, tabla, dramatic builds,
        heroic powerful male Indian vocals, grand, legendary, mythological, larger-than-life"

  🌿  TRIBAL / REGIONAL WARRIORS (forest warriors, indigenous heroes):
      → 90–120 BPM, tribal folk rhythm, earthy percussion, indigenous instruments,
        raw energetic male vocals, folk-rock energy, grounded, primal, earthy, defiant.
        Example: "Folk-tribal 105 BPM, earthy tribal drums, indigenous percussion, raw folk male vocals,
        primal, energetic, defiant, grounded, forest warrior energy, authentic regional folk style"

  🙏  SIKH GURUS (Guru Nanak, Guru Gobind Singh, etc.):
      → 70–100 BPM, Gurbani kirtan style, Sarangi, tabla, harmonium, peaceful yet powerful,
        devotional, spiritual elevation, deep male vocals with reverence and strength.
        Example: "Kirtan-inspired 85 BPM, warm harmonium, Sarangi, medium tabla, deep reverent
        male Indian vocals, devotional, spiritually elevated, peaceful yet powerful, divine"

RESPOND IN THIS EXACT JSON (no markdown, no code block):
{{
  "name": "Full name of the identity (English transliteration)",
  "category": "Category name from the list above",
  "description": "2-3 sentences about who they are and why they are celebrated in Indian culture.",
  "song_theme": "A vividly detailed theme for a short (< 40 second) Hindi devotional or heroic song. You MUST explicitly describe their personality, aura (e.g. fierce, divine, calming, aggressive, regal), character traits, and exactly how the tone of the song should mirror their core essence. 3-4 sentences.",
  "music_style": "Highly specific MiniMax music style tags. MUST include: (1) Exact BPM number or range, (2) specific instruments, (3) energy level, (4) vocal character (male/female, powerful/soft/roaring/gentle), (5) overall mood. Follow the Music Style Guide above — match to the character's archetype precisely. Do NOT be generic. 40-70 words."
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
