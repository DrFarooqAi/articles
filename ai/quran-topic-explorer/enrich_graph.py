"""
Post-process graphify's graph.json to add verse-level references to every concept node.

What it does:
1. Parses each ruku .md file to extract the "Verse keys: x:x, x:x, ..." line
2. For each concept node in graph.json, finds all connected ruku document nodes
3. Aggregates all verse_keys from those rukus onto the concept node
4. Merges alias nodes (prayer / salah / salat / establish prayer → canonical)
5. Writes enriched_graph.json

Run AFTER graphify extract completes:
    python enrich_graph.py
"""

import json
import os
import re
from collections import defaultdict

RUKU_DIR    = os.path.join(os.path.dirname(__file__), "quran-data-ruku")
GRAPH_IN    = os.path.join(os.path.dirname(__file__), "graphify-out", "graph.json")
GRAPH_OUT   = os.path.join(os.path.dirname(__file__), "graphify-out", "enriched_graph.json")
VERSE_CACHE = os.path.join(os.path.dirname(__file__), "verse_cache.json")

# ── Alias groups: first entry is the canonical label ─────────────────────────
ALIAS_GROUPS = [
    ["Prayer", "Salah", "Salat", "Establish Prayer", "Establishing Prayer",
     "Worship and Prayer", "Ritual Prayer", "Daily Prayer", "Five Prayers"],
    ["Fasting", "Sawm", "Ramadan Fasting", "Fast"],
    ["Zakat", "Zakah", "Charity", "Obligatory Charity", "Almsgiving"],
    ["Hajj", "Pilgrimage", "Annual Pilgrimage"],
    ["Jihad", "Striving", "Striving in Allah's Cause", "Fighting in Allah's Cause"],
    ["Tawhid", "Monotheism", "Oneness of Allah", "Divine Unity", "Tawheed"],
    ["Iman", "Faith", "Belief", "True Belief"],
    ["Tawbah", "Repentance", "Seeking Forgiveness", "Turning to Allah"],
    ["Quran", "The Quran", "Holy Quran", "Scripture", "Divine Revelation"],
    ["Prophet Muhammad", "The Prophet", "Muhammad", "Messenger of Allah",
     "The Messenger"],
    ["Day of Judgment", "Day of Recompense", "Yawm al-Qiyamah", "Resurrection",
     "The Last Day", "Hereafter", "Akhirah"],
    ["Jannah", "Paradise", "Gardens of Paradise", "Heaven"],
    ["Jahannam", "Hellfire", "Hell", "Fire of Hell"],
    ["Angels", "Angel", "The Angels", "Malaikah"],
    ["Shirk", "Polytheism", "Associating Partners with Allah", "Idolatry"],
    ["Riba", "Interest", "Usury"],
    ["Marriage", "Nikah", "Matrimony"],
    ["Divorce", "Talaq"],
    ["Moses", "Prophet Moses", "Musa"],
    ["Jesus", "Prophet Jesus", "Isa", "Son of Mary"],
    ["Abraham", "Prophet Abraham", "Ibrahim"],
    ["Noah", "Prophet Noah", "Nuh"],
    ["Adam", "Prophet Adam"],
    ["Mary", "Maryam", "Virgin Mary"],
    ["Pharaoh", "Fir'awn"],
    ["Children of Israel", "Banu Israel", "Israelites", "Jews"],
    ["People of the Scripture", "People of the Book", "Ahl al-Kitab"],
    ["Divine Mercy", "Mercy of Allah", "Rahman", "Rahim",
     "Divine Mercy (Rahman/Rahim)"],
    ["Divine Guidance", "Hidayah", "Guidance", "Right Path",
     "The Straight Path", "Sirat al-Mustaqim"],
    ["Taqwa", "God-consciousness", "Piety", "Fear of Allah", "Righteousness"],
    ["Knowledge", "Divine Knowledge", "Ilm"],
    ["Justice", "Adl", "Fairness", "Equity"],
    ["Patience", "Sabr"],
    ["Gratitude", "Shukr", "Thankfulness"],
    ["Wealth", "Rizq", "Provision", "Sustenance"],
    ["Creation", "The Creation", "Creator", "Allah as Creator"],
]


# ── helpers ───────────────────────────────────────────────────────────────────

def load_ruku_verse_keys() -> dict[str, list[str]]:
    """Return {filename_stem: [verse_key, ...]} for every ruku file."""
    result = {}
    if not os.path.isdir(RUKU_DIR):
        return result
    for fname in sorted(os.listdir(RUKU_DIR)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(RUKU_DIR, fname)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        # Extract "**Verse keys:** 2:1, 2:2, ..." line
        m = re.search(r"\*\*Verse keys:\*\*\s*([0-9:, –\-]+)", content)
        if m:
            raw = m.group(1)
            keys = [k.strip() for k in re.split(r"[,\s]+", raw) if re.match(r"\d+:\d+", k.strip())]
            result[fname[:-3]] = keys  # strip .md
    return result


def build_alias_map(nodes: list[dict]) -> dict[str, str]:
    """Return {node_id: canonical_node_id} for alias merging."""
    # Build label -> node_id lookup (lowercase)
    label_to_id: dict[str, str] = {}
    for n in nodes:
        label_to_id[n["label"].lower()] = n["id"]

    alias_map: dict[str, str] = {}
    for group in ALIAS_GROUPS:
        canonical_label = group[0].lower()
        canonical_id = label_to_id.get(canonical_label)
        if not canonical_id:
            # Try to find any member present in graph as canonical
            for member in group:
                cid = label_to_id.get(member.lower())
                if cid:
                    canonical_id = cid
                    break
        if not canonical_id:
            continue
        for member in group[1:]:
            mid = label_to_id.get(member.lower())
            if mid and mid != canonical_id:
                alias_map[mid] = canonical_id
    return alias_map


def ruku_stem_to_filename(stem: str) -> str:
    """Convert node source_file like '042-s003-ruku.md' to stem '042-s003-ruku'."""
    return stem.replace(".md", "")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(GRAPH_IN):
        print(f"Graph not found: {GRAPH_IN}")
        print("Run graphify extract first.")
        return

    with open(GRAPH_IN, encoding="utf-8") as f:
        graph = json.load(f)

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    print(f"Loaded graph: {len(nodes)} nodes, {len(edges)} edges")

    # Load verse_cache for text lookup
    verse_cache = {}
    if os.path.exists(VERSE_CACHE):
        with open(VERSE_CACHE, encoding="utf-8") as f:
            verse_cache = json.load(f)
        print(f"Loaded verse cache: {len(verse_cache)} entries")

    # Load ruku -> verse_keys mapping
    ruku_keys = load_ruku_verse_keys()
    print(f"Loaded {len(ruku_keys)} ruku files with verse key data")

    # Build node lookup
    node_by_id = {n["id"]: n for n in nodes}

    # Build alias map
    alias_map = build_alias_map(nodes)
    print(f"Alias merges identified: {len(alias_map)}")

    # Build ruku document node lookup: node_id -> ruku verse_keys
    ruku_node_verse_keys: dict[str, list[str]] = {}
    for n in nodes:
        if n.get("file_type") == "document":
            sf = n.get("source_file", "")
            stem = ruku_stem_to_filename(sf)
            if stem in ruku_keys:
                ruku_node_verse_keys[n["id"]] = ruku_keys[stem]

    # Build adjacency: concept_node_id -> set of connected ruku node_ids
    concept_to_rukus: dict[str, set] = defaultdict(set)
    for e in edges:
        src, tgt = e["source"], e["target"]
        src_n = node_by_id.get(src, {})
        tgt_n = node_by_id.get(tgt, {})
        if src_n.get("file_type") == "concept" and tgt in ruku_node_verse_keys:
            concept_to_rukus[src].add(tgt)
        if tgt_n.get("file_type") == "concept" and src in ruku_node_verse_keys:
            concept_to_rukus[tgt].add(src)

    # Enrich concept nodes with aggregated verse refs
    enriched = 0
    for n in nodes:
        if n.get("file_type") != "concept":
            continue
        nid = n["id"]
        connected_rukus = concept_to_rukus.get(nid, set())
        all_keys: list[str] = []
        seen = set()
        for ruku_id in sorted(connected_rukus):
            for vk in ruku_node_verse_keys.get(ruku_id, []):
                if vk not in seen:
                    all_keys.append(vk)
                    seen.add(vk)
        if all_keys:
            n["verse_refs"] = all_keys
            n["verse_count"] = len(all_keys)
            enriched += 1

    print(f"Enriched {enriched} concept nodes with verse references")

    # Apply alias merges: redirect edges, remove alias nodes
    if alias_map:
        new_edges = []
        for e in edges:
            src = alias_map.get(e["source"], e["source"])
            tgt = alias_map.get(e["target"], e["target"])
            if src == tgt:
                continue  # self-loop after merge
            e = dict(e)
            e["source"] = src
            e["target"] = tgt
            new_edges.append(e)
        # Deduplicate edges
        seen_edges = set()
        deduped = []
        for e in new_edges:
            key = (e["source"], e["target"], e.get("relation"))
            if key not in seen_edges:
                seen_edges.add(key)
                deduped.append(e)
        removed_nodes = set(alias_map.keys())
        nodes = [n for n in nodes if n["id"] not in removed_nodes]
        edges = deduped
        print(f"After alias merge: {len(nodes)} nodes, {len(edges)} edges "
              f"(removed {len(removed_nodes)} alias nodes)")

    graph["nodes"] = nodes
    graph["edges"] = edges

    os.makedirs(os.path.dirname(GRAPH_OUT), exist_ok=True)
    with open(GRAPH_OUT, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"\nEnriched graph written to: {GRAPH_OUT}")


if __name__ == "__main__":
    main()
