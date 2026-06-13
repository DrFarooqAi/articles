"""
Fetch all Quran verses and write one Markdown file per ruku (~558 sections).
Ruku = traditional thematic paragraph division (marked with ع in Quran).
Ruku numbers are global (1-558) across the full Quran.

Output: quran-data-ruku/ with ~558 files, each file carries verse_keys
        so graphify can create concept nodes with full verse-level refs.

Run:   python fetch_quran_ruku.py
       python fetch_quran_ruku.py --translation 85   # Abdel Haleem
Needs: pip install requests
"""

import argparse
import json
import os
import re
import time

import requests

OUT_DIR = os.path.join(os.path.dirname(__file__), "quran-data-ruku")
BASE    = "https://api.quran.com/api/v4"
FIELDS  = "ruku_number,verse_key,juz_number,page_number"
HEADERS = {"Accept": "application/json"}

TRANSLATION_NAMES = {
    20:  "Saheeh International",
    85:  "M.A.S. Abdel Haleem (Oxford)",
    84:  "Mufti Taqi Usmani",
    203: "Al-Hilali & Khan",
}


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    return (text
            .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&nbsp;", " ").replace("&#13;", "").replace("&#xa;", "\n")
            .strip())


def get(path: str, params: dict = None, retries: int = 5) -> dict:
    for attempt in range(retries):
        try:
            r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"\n  [retry {attempt+1}/{retries}] {e} — waiting {wait}s...")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def fetch_chapters() -> dict[int, dict]:
    return {c["id"]: c for c in get("/chapters")["chapters"]}


def fetch_all_verses(chapters: dict, translation_id: int, resume_from: int = 1) -> list[dict]:
    """Return flat list of all 6,236 verses with ruku_number + translation.
    Pass resume_from to skip already-fetched surahs."""
    all_verses = []
    for num in range(resume_from, 115):
        name = chapters[num].get("name_simple", f"Surah {num}")
        print(f"  [{num:3d}/114] {name}...", end=" ", flush=True)
        params = {
            "translations": translation_id,
            "per_page": 300,
            "page": 1,
            "fields": FIELDS,
        }
        data = get(f"/verses/by_chapter/{num}", params)
        verses = data.get("verses", [])
        for v in verses:
            trans = v.get("translations", [])
            text = strip_html(trans[0]["text"]) if trans else ""
            all_verses.append({
                "surah_num":   num,
                "surah_name":  name,
                "surah_name_arabic": chapters[num].get("name_arabic", ""),
                "revelation":  chapters[num].get("revelation_place", "").capitalize(),
                "verse_key":   v.get("verse_key", f"{num}:{v.get('verse_number','')}"),
                "verse_number": v.get("verse_number", ""),
                "ruku_number": v.get("ruku_number", 0),
                "juz_number":  v.get("juz_number", 0),
                "page_number": v.get("page_number", 0),
                "text":        text,
            })
        print(f"{len(verses)} verses")
        time.sleep(0.3)
    return all_verses


def group_by_ruku(verses: list[dict]) -> dict[int, list[dict]]:
    groups: dict[int, list[dict]] = {}
    for v in verses:
        rn = v["ruku_number"]
        groups.setdefault(rn, []).append(v)
    return groups


def write_ruku_files(groups: dict[int, list[dict]], translation_label: str, out_dir: str) -> int:
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for ruku_num in sorted(groups):
        verses    = groups[ruku_num]
        first     = verses[0]
        last      = verses[-1]
        surah_num = first["surah_num"]
        surah_name = first["surah_name"]
        surah_arabic = first["surah_name_arabic"]
        revelation = first["revelation"]
        juz_num    = first["juz_number"]

        # Verse range — may span surah boundary (rare edge case)
        start_key = first["verse_key"]
        end_key   = last["verse_key"]
        verse_range = start_key if start_key == end_key else f"{start_key}–{end_key}"
        verse_keys_list = ", ".join(v["verse_key"] for v in verses)

        # Surah may change mid-ruku (extremely rare — handle gracefully)
        surahs_in_ruku = sorted({v["surah_num"] for v in verses})
        surah_label = surah_name
        if len(surahs_in_ruku) > 1:
            surah_label = " + ".join(
                f"Surah {n}" for n in surahs_in_ruku
            )

        filename = f"{ruku_num:03d}-s{surah_num:03d}-ruku.md"
        filepath = os.path.join(out_dir, filename)

        lines = [
            f"# Ruku {ruku_num}: {surah_label} ({verse_range})",
            f"**Surah:** {surah_name} ({surah_arabic}) · Surah {surah_num} · {revelation}",
            f"**Juz:** {juz_num} | **Verse range:** {verse_range} | **Ruku:** {ruku_num}/558",
            f"**Verse keys:** {verse_keys_list}",
            f"**Translation:** {translation_label}",
            "",
            "## Verses",
            "",
        ]
        for v in verses:
            lines.append(f"**{v['verse_key']}** {v['text']}")
            lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        written += 1

    return written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--translation", type=int, default=20,
                        help="Quran.com translation ID (default 20 = Saheeh International)")
    args = parser.parse_args()

    label = TRANSLATION_NAMES.get(args.translation, f"Translation #{args.translation}")
    print(f"Translation: {label} (id={args.translation})")

    print("\nFetching chapter metadata...")
    chapters = fetch_chapters()

    # Resume support: load partial verse cache if it exists
    raw_cache_path = os.path.join(os.path.dirname(__file__), "verse_raw_cache.json")
    existing_verses: list[dict] = []
    resume_from = 1
    if os.path.exists(raw_cache_path):
        with open(raw_cache_path, encoding="utf-8") as f:
            existing_verses = json.load(f)
        if existing_verses:
            last_surah = max(v["surah_num"] for v in existing_verses)
            resume_from = last_surah + 1
            print(f"  Resuming from Surah {resume_from} ({len(existing_verses)} verses already cached)")

    print(f"\nFetching verses (Surahs {resume_from}–114)...")
    new_verses = fetch_all_verses(chapters, args.translation, resume_from=resume_from)
    verses = existing_verses + new_verses
    print(f"\n  Total verses: {len(verses)}")

    # Save raw verse cache for resume capability
    with open(raw_cache_path, "w", encoding="utf-8") as f:
        json.dump(verses, f, ensure_ascii=False, indent=2)

    print("\nGrouping by ruku...")
    groups = group_by_ruku(verses)
    print(f"  Total rukus: {len(groups)}")

    # Save verse lookup (verse_key -> text)
    cache_path = os.path.join(os.path.dirname(__file__), "verse_cache.json")
    verse_lookup = {v["verse_key"]: v["text"] for v in verses}
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(verse_lookup, f, ensure_ascii=False, indent=2)
    print(f"  Verse cache saved: {cache_path}")

    print(f"\nWriting ruku files to {OUT_DIR} ...")
    written = write_ruku_files(groups, label, OUT_DIR)
    print(f"\nDone! {written} ruku files written.")
    print("Next: graphify extract ./quran-data-ruku --backend claude")


if __name__ == "__main__":
    main()
