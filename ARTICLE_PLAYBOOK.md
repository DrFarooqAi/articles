# Article Playbook — Dr. Farooq's GitHub Pages

> Purpose: make publishing a new article a **copy + fill + jump-to-marker + push** job,
> so we never re-read whole HTML files to relearn the design system or find where cards go.
> **Rule:** do NOT full-read existing articles or the CV. Copy the template, then `grep`
> the marker comments below and paste the matching snippet.

## Repos & paths
- **Articles hub:** `C:/Users/ac/Desktop/DrFarooqAi-articles/` → live at https://drfarooqai.github.io/articles/
  - Articles live in `ai/<slug>.html` (kebab-case slug).
  - **Template:** `ai/_templates/article-template.html` (canonical teal "lovable-light + snake-ring" style).
- **CV / portfolio:** `C:/Users/ac/Desktop/dr-farooq-cv-temp/` → live at https://drfarooqai.github.io/dr-farooq-cv/
- New article URL: `https://drfarooqai.github.io/articles/ai/<slug>.html`

## Step 1 — Write the article
1. Copy `ai/_templates/article-template.html` → `ai/<slug>.html`.
2. Fill every `{{PLACEHOLDER}}`. Keep the `<style>` and `<script>` blocks as-is.
3. Update `secIds=[...]` in the script to match your section ids, and add one
   `<a class="sec" href="#id">` nav link per section.
4. Components available (duplicate as needed): `.kpi`, `.card`/`.grid g3`, `.tablewrap`,
   `.vmbox.vision|.mission`, `.chartcard`+Chart.js, `.diagram`+mermaid, `.flip`,
   `.checks`, `.closeband`, `.refs`. Footer already carries the 4 standard cross-links.

## Step 2 — Register it (routing by content type)
Every article ALWAYS gets an Articles-hub card. It is ADDITIONALLY cross-posted into one
CV section depending on type. **Find markers with `grep`/Grep — line numbers drift.**

| Content type | Articles hub (always) | Also → CV section + marker |
|---|---|---|
| General AI / healthcare article | ✅ hub card | — |
| Hospital / transformation advisory | ✅ | **Hospital Transformation Projects** → `<!-- HOSPITAL TRANSFORMATION PROJECTS -->` · add `PROJECT NO. N` card · accent cycle purple→cyan→gold→green |
| Training / course / multi-part series | ✅ | **Trainings & Deployments** → `<!-- TRAININGS & DEPLOYMENTS -->` · series item `<span class="tr-series-num">NN</span>` |
| Physician-growth topic | ✅ | **Physician Growth Advisor** → `<!-- PHYSICIAN GROWTH ADVISOR -->` |
| Vision 2030 / policy | ✅ | **Vision 2030 & AI in Health** → `<!-- VISION 2030 & AI IN HEALTH -->` |
| Built app / tool (with write-up) | ✅ | **AI Projects / Pipeline** → `<!-- PROJECTS -->` · `.pipeline-card` |
| **Quran** | ✅ single suite card | — (Quran is a suite, see below) |

### 2a. Articles-hub card — `DrFarooqAi-articles/index.html`
Grep `<!-- ARTICLE GRID -->` then the first `<!-- Published -->`. Paste as the new first card:
```html
    <a href="ai/<slug>.html" class="article-card">
      <div class="card-category">CATEGORY · SUBTAG</div>
      <div class="card-title">ARTICLE TITLE</div>
      <p class="card-desc">One-sentence description.</p>
      <div class="card-footer">
        <span class="card-date">Mon 2026</span>
        <span class="card-arrow">→</span>
      </div>
    </a>
```

### 2b. CV "Hospital Transformation Projects" card — `dr-farooq-cv-temp/index.html`
Grep `<!-- HOSPITAL TRANSFORMATION PROJECTS -->`. Cards are numbered `PROJECT NO. N`;
accent border/button color cycles purple → cyan → gold → green → (repeat). Paste after the
last project card, before the section's closing `</div></section>`:
```html
    <div style="background:var(--surface);border:1px solid var(--ACCENT);border-radius:16px;padding:32px 36px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;">
      <div style="flex:1;min-width:0;">
        <div style="font-family:'Space Mono',monospace;font-size:11px;color:var(--text-muted);letter-spacing:0.1em;margin-bottom:8px;">PROJECT NO. N</div>
        <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:var(--text);">PROJECT TITLE</div>
      </div>
      <a href="https://drfarooqai.github.io/articles/ai/<slug>.html" target="_blank" style="flex-shrink:0;display:inline-flex;align-items:center;gap:10px;background:var(--ACCENT);color:#fff;font-family:'Space Mono',monospace;font-size:13px;font-weight:700;padding:14px 28px;border-radius:10px;text-decoration:none;white-space:nowrap;transition:all 0.2s;" onmouseover="this.style.background='HOVER'" onmouseout="this.style.background='var(--ACCENT)'">
        Read Advisory →
      </a>
    </div>
```
Accent → hover pairs: `--purple`→`#c084fc`, `--cyan`→`#67e8f9`, `--gold`→`#fcd34d`, `--green`→`#6ee7b7`. (gold/cyan/green buttons use `color:#030712` instead of `#fff`.)

### 2c. Quran content (special)
Quran is a **suite**, not a standalone teal article. Hub: `ai/quran-ai/index.html`; tool
subdirs: `quran-knowledge-graph`, `quran-topic-explorer`, `quran-concept-graph`,
`quran-bipartite-map`. A new tool = a new subdir linked from `ai/quran-ai/index.html`.
The main `index.html` keeps **one** `.quran-ai-card` pointing at the suite (no per-tool card).

## Step 3 — Cross-links (fixed; already wired)
- New article (from template) carries: nav `← Portfolio`; footer **LinkedIn / Profile & Projects / More Articles**.
- The hub card and any CV card link **into** the new article URL.
- Hub ↔ CV are already mutually linked — no extra wiring per article.

## Step 4 — Publish
Run in each repo you touched (Pages publishes from `main`):
```
git add <files> && git commit -m "Add article: <title>" && git push
```
If the CV push is rejected: `git pull --rebase` then `git push` (then confirm the card survived the rebase).

## Style note
The back catalog has two palettes: **teal lovable-light** (canonical, this template) and an
older green/pink cyberpunk. **All new articles use the teal template.**
