"""
build_graph.py — Keyword-based Quran knowledge graph builder.
No API calls needed. Reads 558 ruku .md files and builds a topic-centric graph.

Output: graphify-out/graph.json  +  graphify-out/enriched_graph.json
"""

import json
import os
import re
from collections import defaultdict

# Pre-compile keyword patterns with word-boundary at start
# (no trailing \b so "pray" still matches "prayer", "fast" matches "fasting")
_KW_CACHE: dict = {}

def _compile(kw: str):
    if kw not in _KW_CACHE:
        _KW_CACHE[kw] = re.compile(r'\b' + re.escape(kw.lower()))
    return _KW_CACHE[kw]

BASE = os.path.dirname(os.path.abspath(__file__))
RUKU_DIR     = os.path.join(BASE, "quran-data-ruku")
OUT_DIR      = os.path.join(BASE, "graphify-out")
GRAPH_OUT    = os.path.join(OUT_DIR, "graph.json")
ENRICHED_OUT = os.path.join(OUT_DIR, "enriched_graph.json")
VERSE_CACHE  = os.path.join(BASE, "verse_cache.json")

# ── Concept definitions ───────────────────────────────────────────────────────
# Each entry: id, label, keywords (case-insensitive), category, color
CONCEPTS = [
    # ── Pillars of Islam ─────────────────────────────────────────────────────
    {
        "id": "prayer", "label": "Prayer",
        "keywords": [
            "prayer", "salah", "salat", "establish prayer", "establishing prayer",
            "prostrat", "bowing", "place of prayer", "night prayer", "dawn prayer",
            "friday prayer", "congregation", "call to prayer", "ritual prayer",
            "standing in prayer", "fajr", "dhuhr", "asr", "maghrib", "isha",
            "qiblah", "qibla", "masjid",
        ],
        "category": "Pillars of Islam", "color": "#1B5E20",
    },
    {
        "id": "fasting", "label": "Fasting",
        "keywords": [
            "fast", "fasting", "sawm", "ramadan", "month of ramadan",
            "abstain from eating", "iftar", "suhoor", "i'tikaf",
        ],
        "category": "Pillars of Islam", "color": "#4A148C",
    },
    {
        "id": "zakat", "label": "Zakat",
        "keywords": [
            "zakah", "zakat", "alms", "almsgiving", "obligatory charity",
            "purifying dues", "poor-due", "spend in the way of allah",
            "give in charity", "charity", "spend from what",
        ],
        "category": "Pillars of Islam", "color": "#E65100",
    },
    {
        "id": "hajj", "label": "Hajj",
        "keywords": [
            "hajj", "pilgrimage", "umrah", "ka'bah", "kaaba",
            "sacred mosque", "al-masjid al-haram", "ihram",
            "tawaf", "sa'y", "arafah",
            "sacred house", "ancient house",
        ],
        "category": "Pillars of Islam", "color": "#BF360C",
    },
    {
        "id": "shahada", "label": "Declaration of Faith",
        "keywords": [
            "there is no god but allah", "none has the right to be worshipped",
            "testify", "testimony of faith", "kalimah",
        ],
        "category": "Pillars of Islam", "color": "#1A237E",
    },

    # ── Core Beliefs ─────────────────────────────────────────────────────────
    {
        "id": "tawhid", "label": "Tawhid",
        "keywords": [
            "tawhid", "monotheism", "oneness of allah", "one god",
            "none worthy of worship", "no partner", "no associate",
            "he is one", "allāh is one", "allah is one",
        ],
        "category": "Core Beliefs", "color": "#0D47A1",
    },
    {
        "id": "iman", "label": "Faith",
        "keywords": [
            "faith", "belief", "believe", "true belief", "iman",
            "those who believe", "believers", "mu'min",
        ],
        "category": "Core Beliefs", "color": "#006064",
    },
    {
        "id": "angels", "label": "Angels",
        "keywords": [
            "angel", "angels", "malaikah", "gabriel", "jibreel",
            "jibrīl", "michael", "mika'il", "israfil", "malik",
            "bearers of the throne", "heavenly beings",
        ],
        "category": "Core Beliefs", "color": "#F57F17",
    },
    {
        "id": "divine_decree", "label": "Divine Decree",
        "keywords": [
            "divine decree", "qadar", "qadr", "predestination",
            "whatever allah wills", "allah wills", "whatever he wills",
            "his command", "his decree", "decreed", "ordained",
            "night of decree", "night of power",
        ],
        "category": "Core Beliefs", "color": "#37474F",
    },

    # ── Allah's Attributes ────────────────────────────────────────────────────
    {
        "id": "divine_mercy", "label": "Divine Mercy",
        "keywords": [
            "mercy", "merciful", "compassionate", "rahman", "rahim",
            "al-rahman", "al-rahim", "forgiveness", "most forgiving",
            "all-forgiving", "oft-forgiving",
        ],
        "category": "Allah's Attributes", "color": "#00695C",
    },
    {
        "id": "divine_knowledge", "label": "Divine Knowledge",
        "keywords": [
            "all-knowing", "all-aware", "well-acquainted", "fully aware",
            "knows what", "allāh knows", "allah knows", "omniscient",
            "acquainted with all things",
        ],
        "category": "Allah's Attributes", "color": "#01579B",
    },
    {
        "id": "divine_power", "label": "Divine Power",
        "keywords": [
            "all-powerful", "almighty", "able to do all things",
            "over all things competent", "al-qadir", "al-qawi",
            "mighty", "omnipotent",
        ],
        "category": "Allah's Attributes", "color": "#880E4F",
    },
    {
        "id": "divine_guidance", "label": "Divine Guidance",
        "keywords": [
            "guidance", "guide", "straight path", "right path",
            "guided", "hidayah", "sirat al-mustaqim", "right direction",
        ],
        "category": "Allah's Attributes", "color": "#558B2F",
    },

    # ── Moral / Spiritual ────────────────────────────────────────────────────
    {
        "id": "taqwa", "label": "Taqwa",
        "keywords": [
            "taqwa", "god-conscious", "piety", "righteous", "righteousness",
            "fear allah", "conscious of allah", "mindful of allah",
            "those who are mindful", "those who fear",
        ],
        "category": "Moral & Spiritual", "color": "#2E7D32",
    },
    {
        "id": "tawbah", "label": "Repentance",
        "keywords": [
            "repent", "repentance", "tawbah", "turn to allah",
            "seek forgiveness", "ask for forgiveness", "forgive",
            "atone", "return to him",
        ],
        "category": "Moral & Spiritual", "color": "#4527A0",
    },
    {
        "id": "sabr", "label": "Patience",
        "keywords": [
            "patience", "patient", "sabr", "persevere", "perseverance",
            "endure", "steadfast", "steadfastness", "bear with",
        ],
        "category": "Moral & Spiritual", "color": "#6A1B9A",
    },
    {
        "id": "shukr", "label": "Gratitude",
        "keywords": [
            "grateful", "gratitude", "thankful", "thankfulness", "shukr",
            "give thanks", "be grateful", "ungrateful",
        ],
        "category": "Moral & Spiritual", "color": "#E65100",
    },
    {
        "id": "justice", "label": "Justice",
        "keywords": [
            "justice", "just", "fairness", "fair", "equity", "adl",
            "witness fairly", "stand firmly for justice",
            "with equity", "equitable",
        ],
        "category": "Moral & Spiritual", "color": "#1565C0",
    },
    {
        "id": "truthfulness", "label": "Truthfulness",
        "keywords": [
            "truthful", "truth", "honest", "honesty", "sincere",
            "sincerity", "true believers", "people of truth",
        ],
        "category": "Moral & Spiritual", "color": "#00838F",
    },
    {
        "id": "tawakkul", "label": "Trust in Allah",
        "keywords": [
            "trust in allah", "put your trust", "rely on allah",
            "tawakkul", "rely upon him", "best of disposers",
            "sufficient for us is allah",
        ],
        "category": "Moral & Spiritual", "color": "#283593",
    },

    # ── Social / Legal ───────────────────────────────────────────────────────
    {
        "id": "marriage", "label": "Marriage",
        "keywords": [
            "marriage", "marry", "married", "nikah", "wedlock", "spouse",
            "husband", "wife", "wives", "mahr", "dowry", "matrimony",
        ],
        "category": "Social & Legal", "color": "#AD1457",
    },
    {
        "id": "divorce", "label": "Divorce",
        "keywords": [
            "divorce", "talaq", "divorced women", "waiting period",
            "iddah", "zihar", "li'an", "khul'",
        ],
        "category": "Social & Legal", "color": "#C62828",
    },
    {
        "id": "inheritance", "label": "Inheritance",
        "keywords": [
            "inheritance", "inherit", "bequest", "legacy",
            "shares of inheritance", "bequeath",
        ],
        "category": "Social & Legal", "color": "#4E342E",
    },
    {
        "id": "riba", "label": "Riba (Interest)",
        "keywords": [
            "riba", "interest", "usury", "consume interest",
            "transaction of interest",
        ],
        "category": "Social & Legal", "color": "#B71C1C",
    },
    {
        "id": "halal_haram", "label": "Halal & Haram",
        "keywords": [
            "lawful", "unlawful", "forbidden", "prohibited", "permissible",
            "halal", "haram", "intoxicant", "wine", "alcohol",
            "carrion", "blood of", "flesh of swine", "pork",
        ],
        "category": "Social & Legal", "color": "#795548",
    },
    {
        "id": "orphans", "label": "Orphans",
        "keywords": [
            "orphan", "orphans", "yatim",
        ],
        "category": "Social & Legal", "color": "#546E7A",
    },
    {
        "id": "warfare", "label": "Warfare & Peace",
        "keywords": [
            "fight", "fighting", "battle", "war", "warfare", "enemy",
            "kill", "slay", "combat", "conquer", "victory", "defeat",
            "peace", "truce", "treaty", "armistice",
        ],
        "category": "Social & Legal", "color": "#37474F",
    },

    # ── Groups / Communities ─────────────────────────────────────────────────
    {
        "id": "believers", "label": "Believers",
        "keywords": [
            "those who believe", "the believers", "mu'minoon", "mu'min",
            "people of faith",
        ],
        "category": "Communities", "color": "#1B5E20",
    },
    {
        "id": "disbelievers", "label": "Disbelievers",
        "keywords": [
            "disbelieve", "disbelievers", "those who disbelieve",
            "kafir", "kufr", "infidel", "rejecters",
        ],
        "category": "Communities", "color": "#B71C1C",
    },
    {
        "id": "hypocrites", "label": "Hypocrites",
        "keywords": [
            "hypocrite", "hypocrites", "munafiqoon", "nifaq",
            "those in whose hearts is disease", "outwardly believing",
        ],
        "category": "Communities", "color": "#6D4C41",
    },
    {
        "id": "people_of_book", "label": "People of the Book",
        "keywords": [
            "people of the book", "people of the scripture",
            "ahl al-kitab", "jews", "christians",
        ],
        "category": "Communities", "color": "#0277BD",
    },
    {
        "id": "children_of_israel", "label": "Children of Israel",
        "keywords": [
            "children of israel", "banu isra'il", "bani isra'il",
            "israelites", "tribes of israel",
        ],
        "category": "Communities", "color": "#00695C",
    },
    {
        "id": "shirk", "label": "Shirk",
        "keywords": [
            "shirk", "polytheism", "associate partners", "idolatry",
            "idol", "false gods", "partners with allah",
            "associating others", "mushrikeen",
        ],
        "category": "Communities", "color": "#4E342E",
    },

    # ── Prophets ─────────────────────────────────────────────────────────────
    {
        "id": "prophet_muhammad", "label": "Prophet Muhammad",
        "keywords": [
            "muḥammad", "muhammad", "the messenger", "messenger of allah",
            "the prophet", "o prophet", "o messenger",
        ],
        "category": "Prophets", "color": "#1A237E",
    },
    {
        "id": "moses", "label": "Moses",
        "keywords": [
            "moses", "mūsā", "musa", "prophet musa",
        ],
        "category": "Prophets", "color": "#006064",
    },
    {
        "id": "jesus", "label": "Jesus",
        "keywords": [
            "jesus", "'isa", "isa", "son of mary", "ibn maryam",
            "messiah", "al-masih",
        ],
        "category": "Prophets", "color": "#01579B",
    },
    {
        "id": "abraham", "label": "Abraham",
        "keywords": [
            "abraham", "ibrāhīm", "ibrahim", "friend of allah",
        ],
        "category": "Prophets", "color": "#E65100",
    },
    {
        "id": "noah", "label": "Noah",
        "keywords": [
            "noah", "nūḥ", "nuh", "the flood", "ark",
        ],
        "category": "Prophets", "color": "#4527A0",
    },
    {
        "id": "adam", "label": "Adam",
        "keywords": [
            "adam", "ādam", "first human", "garden of eden",
        ],
        "category": "Prophets", "color": "#2E7D32",
    },
    {
        "id": "mary", "label": "Mary",
        "keywords": [
            "mary", "maryam", "virgin", "daughter of 'imran",
        ],
        "category": "Prophets", "color": "#880E4F",
    },
    {
        "id": "joseph", "label": "Joseph",
        "keywords": [
            "joseph", "yūsuf", "yusuf",
        ],
        "category": "Prophets", "color": "#F57F17",
    },
    {
        "id": "solomon", "label": "Solomon",
        "keywords": [
            "solomon", "sulaymān", "sulayman", "queen of sheba",
        ],
        "category": "Prophets", "color": "#558B2F",
    },
    {
        "id": "david", "label": "David",
        "keywords": [
            "david", "dāwūd", "dawud",
        ],
        "category": "Prophets", "color": "#1565C0",
    },
    {
        "id": "pharaoh", "label": "Pharaoh",
        "keywords": [
            "pharaoh", "fir'awn", "firawn",
        ],
        "category": "Historical Figures", "color": "#BF360C",
    },
    {
        "id": "prophets_general", "label": "Prophets (General)",
        "keywords": [
            "prophets", "messengers", "we sent", "we raised",
            "a prophet", "a messenger", "the prophets",
        ],
        "category": "Prophets", "color": "#37474F",
    },

    # ── Eschatology ──────────────────────────────────────────────────────────
    {
        "id": "day_of_judgment", "label": "Day of Judgment",
        "keywords": [
            "day of judgment", "day of recompense", "day of resurrection",
            "the last day", "hereafter", "akhirah", "yawm al-qiyamah",
            "resurrection", "day of reckoning", "hour", "the hour",
            "day when",
        ],
        "category": "Eschatology", "color": "#212121",
    },
    {
        "id": "paradise", "label": "Paradise",
        "keywords": [
            "paradise", "garden", "gardens", "jannah", "al-firdaws",
            "beneath which rivers flow", "eternal abode", "abode of bliss",
        ],
        "category": "Eschatology", "color": "#1B5E20",
    },
    {
        "id": "hellfire", "label": "Hellfire",
        "keywords": [
            "hellfire", "hell", "fire of hell", "jahannam", "blazing fire",
            "scorching fire", "eternal punishment", "abode of fire",
        ],
        "category": "Eschatology", "color": "#B71C1C",
    },

    # ── Other Important Topics ───────────────────────────────────────────────
    {
        "id": "quran", "label": "The Quran",
        "keywords": [
            "quran", "qur'an", "the book", "this book", "scripture",
            "divine revelation", "revelation", "the reminder",
            "the criterion", "al-furqan",
        ],
        "category": "Divine Revelation", "color": "#0D47A1",
    },
    {
        "id": "jihad", "label": "Jihad",
        "keywords": [
            "jihad", "strive", "striving", "striving in the cause",
            "striving in allah's cause", "strive with your wealth",
            "strive with your lives",
        ],
        "category": "Worship & Action", "color": "#4E342E",
    },
    {
        "id": "creation", "label": "Creation",
        "keywords": [
            "created", "creation", "creator", "he created",
            "created the heavens and earth", "heavens and the earth",
            "seven heavens",
        ],
        "category": "Divine Acts", "color": "#006064",
    },
    {
        "id": "wealth", "label": "Wealth & Provision",
        "keywords": [
            "wealth", "provision", "rizq", "sustenance", "property",
            "spend in the way", "what we have provided", "livelihood",
        ],
        "category": "Social & Legal", "color": "#F57F17",
    },
    {
        "id": "knowledge", "label": "Knowledge",
        "keywords": [
            "knowledge", "ilm", "learn", "teach", "wisdom",
            "the wise", "those who know", "ponder",
        ],
        "category": "Moral & Spiritual", "color": "#01579B",
    },
    {
        "id": "signs_miracles", "label": "Signs & Miracles",
        "keywords": [
            "sign", "signs", "miracle", "miracles", "ayat",
            "proof", "clear proof", "evidence",
        ],
        "category": "Divine Acts", "color": "#558B2F",
    },
    {
        "id": "covenant", "label": "Covenant",
        "keywords": [
            "covenant", "pledge", "promise", "oath", "covenant of allah",
            "mithaq", "treaty",
        ],
        "category": "Social & Legal", "color": "#283593",
    },
    {
        "id": "dhikr", "label": "Remembrance of Allah",
        "keywords": [
            "remember allah", "remembrance of allah", "dhikr",
            "mention of allah", "glorify", "glorification",
            "exalt", "exaltation", "praise be",
        ],
        "category": "Worship & Action", "color": "#00695C",
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_verse_cache(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_ruku_file(path: str) -> dict:
    """Return {verse_keys, surah_name, surah_num, ruku_num, label, content}."""
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Verse keys
    m = re.search(r"\*\*Verse keys:\*\*\s*([0-9:, \-–]+)", content)
    verse_keys = []
    if m:
        raw = m.group(1)
        verse_keys = [k.strip() for k in re.split(r"[,\s]+", raw) if re.match(r"\d+:\d+", k.strip())]

    # Surah name
    m2 = re.search(r"\*\*Surah:\*\*\s*([^·]+)·\s*Surah\s*(\d+)", content)
    surah_name = m2.group(1).strip() if m2 else ""
    surah_num  = int(m2.group(2)) if m2 else 0

    # Ruku number (from filename or header)
    fname = os.path.basename(path)
    ruku_num = int(fname.split("-")[0])

    # Title / label from first header
    m3 = re.match(r"# (.+)", content)
    label = m3.group(1).strip() if m3 else fname

    return {
        "verse_keys":  verse_keys,
        "surah_name":  surah_name,
        "surah_num":   surah_num,
        "ruku_num":    ruku_num,
        "label":       label,
        "content":     content.lower(),  # lowercase for matching
    }


def concept_matches(concept: dict, content_lower: str) -> bool:
    """Return True if any keyword appears in the ruku content (word-boundary safe)."""
    for kw in concept["keywords"]:
        if _compile(kw).search(content_lower):
            return True
    return False


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Load verse text cache
    verse_cache = load_verse_cache(VERSE_CACHE)
    print(f"Verse cache: {len(verse_cache)} entries")

    # Read all ruku files
    ruku_files = sorted(
        f for f in os.listdir(RUKU_DIR)
        if f.endswith(".md")
    )
    print(f"Ruku files: {len(ruku_files)}")

    ruku_data = {}
    for fname in ruku_files:
        path = os.path.join(RUKU_DIR, fname)
        ruku_data[fname] = parse_ruku_file(path)

    # ── Build nodes ───────────────────────────────────────────────────────────
    # Document nodes (rukus)
    doc_nodes = []
    for fname, d in ruku_data.items():
        node_id = f"ruku_{d['ruku_num']:03d}"
        doc_nodes.append({
            "id":          node_id,
            "label":       d["label"],
            "file_type":   "document",
            "source_file": fname,
            "surah_name":  d["surah_name"],
            "surah_num":   d["surah_num"],
            "ruku_num":    d["ruku_num"],
            "verse_keys":  d["verse_keys"],
        })

    # Build ruku_num -> node_id map
    ruku_id_map = {d["ruku_num"]: f"ruku_{d['ruku_num']:03d}" for d in ruku_data.values()}

    # Concept nodes
    concept_nodes = []
    for c in CONCEPTS:
        concept_nodes.append({
            "id":        f"concept_{c['id']}",
            "label":     c["label"],
            "file_type": "concept",
            "category":  c["category"],
            "color":     c["color"],
        })

    # ── Verse-level matching ──────────────────────────────────────────────────
    # Build verse_key → ruku_num lookup
    verse_to_ruku: dict[str, int] = {}
    for d in ruku_data.values():
        for vk in d["verse_keys"]:
            verse_to_ruku[vk] = d["ruku_num"]

    # Match each individual verse against every concept
    concept_verse_sets: dict[str, set] = defaultdict(set)
    for vk, text in verse_cache.items():
        text_lower = text.lower()
        for c in CONCEPTS:
            if concept_matches(c, text_lower):
                concept_verse_sets[f"concept_{c['id']}"].add(vk)

    # Build edges: concept → ruku when at least one verse matched
    edges = []
    seen_edges: set = set()
    concept_ruku_count: dict[str, int] = defaultdict(int)

    def vk_sort(vk: str):
        s, v = vk.split(":")
        return (int(s), int(v))

    for n in concept_nodes:
        cid = n["id"]
        matched_verses = concept_verse_sets.get(cid, set())
        matching_rukus = {verse_to_ruku[vk] for vk in matched_verses if vk in verse_to_ruku}

        for rn in sorted(matching_rukus):
            rid = ruku_id_map.get(rn)
            if rid and (cid, rid) not in seen_edges:
                seen_edges.add((cid, rid))
                edges.append({"source": cid, "target": rid, "relation": "appears_in"})

        n["verse_refs"]  = sorted(matched_verses, key=vk_sort)
        n["verse_count"] = len(matched_verses)
        n["ruku_count"]  = len(matching_rukus)
        concept_ruku_count[cid] = len(matching_rukus)

    all_nodes = concept_nodes + doc_nodes
    print(f"Nodes: {len(all_nodes)} ({len(concept_nodes)} concepts + {len(doc_nodes)} rukus)")
    print(f"Edges: {len(edges)}")

    # Top concepts
    sorted_concepts = sorted(concept_nodes, key=lambda x: x["verse_count"], reverse=True)
    print("\nTop 10 concepts by verse count:")
    for c in sorted_concepts[:10]:
        print(f"  {c['label']:30s}  {c['verse_count']:5d} verses  {c['ruku_count']:3d} rukus")

    graph = {
        "nodes":       all_nodes,
        "edges":       edges,
        "hyperedges":  [],
        "directed":    False,
    }

    with open(GRAPH_OUT, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"\nGraph written to: {GRAPH_OUT}")

    # enriched_graph.json is the same (verse_refs already embedded)
    with open(ENRICHED_OUT, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"Enriched graph written to: {ENRICHED_OUT}")


if __name__ == "__main__":
    main()
