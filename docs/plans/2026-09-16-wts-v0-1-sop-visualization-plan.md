# WTS 0.1 SOP Visualization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a self-contained interactive webpage that lets product and business teams understand the WTS 0.1 SOP in 5–10 minutes.

**Architecture:** Create a static three-file webpage under `visualization/wts-v0-1-sop/`. The HTML owns semantic content, CSS owns the responsive product-journey presentation, and JavaScript progressively enhances expandable nodes and reading progress. A standard-library Python test protects the required source-backed sections and accessibility hooks.

**Tech Stack:** Semantic HTML5, CSS, vanilla JavaScript, Python `unittest`, local HTTP server, browser visual inspection.

---

### Task 1: Add source-backed structure tests

**Files:**
- Create: `tests/test_wts_sop_visualization.py`

**Step 1: Write the failing test**

Add tests that require:

- `visualization/wts-v0-1-sop/index.html`, `styles.css`, and `app.js`.
- The six main stages: JD input, clarification, confirmation gate, retrieval loop, scoring, final report.
- The six key-node cards and four role categories.
- Accessible buttons with `aria-expanded` and associated detail regions.
- No external `http://` or `https://` assets in the webpage files.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_wts_sop_visualization.py -v`

Expected: FAIL because the visualization files do not exist.

**Step 3: Commit the test**

```bash
git add tests/test_wts_sop_visualization.py
git commit -m "test: define WTS SOP visualization contract"
```

### Task 2: Build the semantic webpage

**Files:**
- Create: `visualization/wts-v0-1-sop/index.html`

**Step 1: Implement the content structure**

Create sections for:

- Hero and six-stage summary.
- Five operating principles.
- Main product journey with four actor types.
- Six expandable key-node cards.
- Seven-step retrieval loop.
- Stop conditions and deliverables.
- Source note linking the frozen WTS 0.1 files.

Use product language for headings and keep implementation terms inside supporting descriptions.

**Step 2: Run structure tests**

Run: `python -m unittest tests/test_wts_sop_visualization.py -v`

Expected: Content tests pass; CSS/JS existence tests still fail.

### Task 3: Add responsive visual design

**Files:**
- Create: `visualization/wts-v0-1-sop/styles.css`

**Step 1: Implement visual hierarchy**

Use CSS custom properties, a restrained dark-on-warm-light palette, role colors, a horizontal desktop journey, mobile stacking, clear focus states, and reduced-motion support.

**Step 2: Verify common widths in browser**

Check approximately 1440 px, 1024 px, and 390 px widths. Confirm no horizontal page overflow and no clipped labels.

### Task 4: Add interaction and keyboard support

**Files:**
- Create: `visualization/wts-v0-1-sop/app.js`

**Step 1: Implement progressive enhancement**

- Toggle key-node details with click or keyboard activation.
- Keep `aria-expanded` synchronized.
- Support "expand all" and "collapse all".
- Update a reading-progress indicator without external libraries.

**Step 2: Run the complete automated test**

Run: `python -m unittest tests/test_wts_sop_visualization.py -v`

Expected: PASS.

### Task 5: Perform content and visual acceptance

**Files:**
- Verify: `visualization/wts-v0-1-sop/index.html`
- Verify: `visualization/wts-v0-1-sop/styles.css`
- Verify: `visualization/wts-v0-1-sop/app.js`

**Step 1: Cross-check content against frozen source**

Compare the visual flow with `versions/wts-v0-1/SKILL.md` and the referenced scoring, search-plan, PRF, requirements, company-research, and final-report documents.

**Step 2: Serve locally**

Run: `python -m http.server 8765 --directory visualization/wts-v0-1-sop`

Expected: `http://127.0.0.1:8765/` loads without console errors.

**Step 3: Inspect the rendered page**

Confirm desktop and mobile layout, interaction state, keyboard focus, copy legibility, and accurate role coloring.

**Step 4: Commit and push**

```bash
git add visualization/wts-v0-1-sop tests/test_wts_sop_visualization.py docs/plans/2026-09-16-wts-v0-1-sop-visualization-plan.md
git commit -m "feat: visualize WTS 0.1 SOP"
git push origin main
```
