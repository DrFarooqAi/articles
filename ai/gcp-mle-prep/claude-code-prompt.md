# Claude Code Task — GCP MLE Prep Site Automation

## Context
I have a GitHub Pages site at https://drfarooqai.github.io
My repo is at https://github.com/drfarooqai/drfarooqai.github.io
I have two files already built locally:
- `mcq.html` (the exam prep page)
- `questions.json` (the MCQ data file, currently has 5 questions)

## What I need you to do

### Step 1 — Set up folder structure
1. In the repo root, create a new folder called `gcp-mle-prep`
2. Move `mcq.html` into `gcp-mle-prep/` and rename it to `index.html`
3. Move `questions.json` into `gcp-mle-prep/`

### Step 2 — Fix the Back to Site link
In `gcp-mle-prep/index.html`, find the nav back link:
```html
<a href="index.html" class="nav-back">← Back to Site</a>
```
Change it to:
```html
<a href="https://drfarooqai.github.io" class="nav-back">← Back to Site</a>
```

### Step 3 — Add a link on the main landing page
In the root `index.html`, find the nav `<ul class="nav-links">` section and add this link:
```html
<li><a href="gcp-mle-prep/">GCP MLE Prep</a></li>
```

Also add a card in the footer area (just before the `<footer>` closing tag) linking to the prep page:
```html
<div style="text-align:center; padding: 2rem 4vw; position:relative; z-index:2;">
  <a href="gcp-mle-prep/" style="display:inline-block; padding:0.8rem 2rem;
    border:1px solid rgba(5,245,233,0.3); color:#05f5e9;
    font-family:'DM Sans',sans-serif; font-size:0.8rem;
    letter-spacing:0.12em; text-transform:uppercase; text-decoration:none;
    transition:all 0.3s;">
    &#128221; GCP MLE Exam Prep →
  </a>
</div>
```

### Step 4 — Commit and push everything
Run these git commands:
```bash
git add .
git commit -m "Add GCP MLE exam prep page under /gcp-mle-prep"
git push origin main
```

### Step 5 — Verify it is live
After pushing, wait 60 seconds then check:
- https://drfarooqai.github.io/gcp-mle-prep/ loads correctly
- https://drfarooqai.github.io still loads correctly
- The nav link on the main page points to the prep page

## Future task — adding more questions
Every time I give you a new batch of MCQs, do this:
1. Read the existing `gcp-mle-prep/questions.json`
2. Append the new questions to the JSON array (keep the same structure)
3. Make sure `id` numbers are unique and sequential
4. Commit with message: "Add questions [X] to [Y] to GCP MLE prep"

## JSON structure for each question (follow this exactly)
```json
{
  "id": 1,
  "topic": "Topic Name Here",
  "question": "Full question text here.",
  "options": {
    "A": "First option text",
    "B": "Second option text",
    "C": "Third option text",
    "D": "Fourth option text"
  },
  "correct": "A",
  "analogy": "The analogy/big picture explanation here.",
  "explanation": "The detailed explanation of why the correct answer is right.",
  "why_not": "Why the wrong answers are incorrect."
}
```

## Notes
- Never touch `gcp-mle-prep/index.html` (the page code) when adding questions
- Only ever edit `gcp-mle-prep/questions.json`
- The page automatically reads the JSON — no HTML changes needed for new questions
- If GitHub Pages is not enabled, go to repo Settings → Pages → Source → main branch → root
