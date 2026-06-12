"""
Fetch an English Quran translation from api.quran.com and write one
Markdown file per surah to ./quran-data/

Default translation: Saheeh International (id=20) — freely available.

NOTE on The Clear Quran (Dr. Mustafa Khattab):
  That translation is copyrighted and not available via any public API.
  If you own a licensed digital copy, place the text in a local JSON file
  with the structure:  { "1": ["verse1 text", ...], "2": [...], ... }
  then run:  python fetch_quran.py --local your_file.json

Run once:  python fetch_quran.py
Requires:  Python 3.10+, requests  (pip install requests)

Available English translation IDs on api.quran.com:
  20  — Saheeh International          (default)
  85  — M.A.S. Abdel Haleem (Oxford)
  84  — Mufti Taqi Usmani
  203 — Al-Hilali & Khan
"""

import argparse
import json
import os
import re
import time
import requests

OUT_DIR = os.path.join(os.path.dirname(__file__), "quran-data")
BASE = "https://api.quran.com/api/v4"
HEADERS = {"Accept": "application/json"}

TRANSLATION_NAMES = {
    20:  "Saheeh International",
    85:  "M.A.S. Abdel Haleem",
    84:  "Mufti Taqi Usmani",
    203: "Al-Hilali & Khan",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&#13;", "").replace("&#xa;", "\n")
    return text.strip()


def get(path: str, params: dict = None) -> dict:
    url = f"{BASE}{path}"
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


# ── API fetch ─────────────────────────────────────────────────────────────────

def fetch_chapters() -> list[dict]:
    return get("/chapters")["chapters"]


def fetch_verses_api(chapter_number: int, translation_id: int) -> list[dict]:
    params = {"translations": translation_id, "per_page": 300, "page": 1}
    data = get(f"/verses/by_chapter/{chapter_number}", params)
    result = []
    for v in data.get("verses", []):
        translations = v.get("translations", [])
        text = strip_html(translations[0]["text"]) if translations else ""
        result.append({"verse_number": v.get("verse_number", "?"), "text": text})
    return result


# ── local JSON mode (for user-supplied Khattab text) ─────────────────────────

def load_local(path: str) -> dict[str, list[str]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Normalise keys to int
    return {int(k): v for k, v in data.items()}


# ── write Markdown ────────────────────────────────────────────────────────────

def write_surah(chapter: dict, verses: list[dict], translation_label: str, out_dir: str) -> None:
    num = chapter["id"]
    name_simple = chapter.get("name_simple", "")
    name_complex = chapter.get("name_complex", "")
    name_arabic  = chapter.get("name_arabic", "")
    revelation   = chapter.get("revelation_place", "").capitalize()
    verse_count  = chapter.get("verses_count", len(verses))

    filename = f"{num:03d}-{name_simple.lower().replace(' ', '-')}.md"
    filepath = os.path.join(out_dir, filename)

    lines = [
        f"# Surah {num}: {name_simple} ({name_complex})",
        f"**Arabic Name:** {name_arabic} | **Revelation:** {revelation} | **Verses:** {verse_count}",
        f"**Translation:** {translation_label}",
        "",
        "## Verses",
        "",
    ]
    for v in verses:
        lines.append(f"{v['verse_number']}. {v['text']}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--translation", type=int, default=20,
                        help="Quran.com translation ID (default: 20 = Saheeh International)")
    parser.add_argument("--local", metavar="FILE",
                        help="Path to a local JSON file with Quran text (skip API)")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    local_data = None
    if args.local:
        print(f"Loading local translation file: {args.local}")
        local_data = load_local(args.local)
        translation_label = "The Clear Quran — Dr. Mustafa Khattab"
    else:
        translation_label = TRANSLATION_NAMES.get(args.translation, f"Translation #{args.translation}")
        print(f"Using API translation: {translation_label} (id={args.translation})")

    print("\nFetching chapter metadata...")
    chapters = fetch_chapters()
    print(f"  {len(chapters)} chapters found")

    print("\nFetching verses and writing Markdown files...")
    for chapter in chapters:
        num  = chapter["id"]
        name = chapter.get("name_simple", f"Surah {num}")
        print(f"  [{num:3d}/114] {name}...", end=" ", flush=True)

        if local_data:
            raw = local_data.get(num, [])
            verses = [{"verse_number": i + 1, "text": t} for i, t in enumerate(raw)]
        else:
            verses = fetch_verses_api(num, args.translation)
            time.sleep(0.3)

        write_surah(chapter, verses, translation_label, OUT_DIR)
        print(f"{len(verses)} verses -> {num:03d}-{name.lower().replace(' ', '-')}.md")

    print(f"\nDone! {len(chapters)} files written to: {OUT_DIR}")
    print("Next: graphify extract ./quran-data --backend claude")


if __name__ == "__main__":
    main()
