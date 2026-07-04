---
name: verify
description: Build/launch/drive recipe for verifying ShalomCI GUI changes end-to-end (Streamlit + Playwright headless).
---

# Verifying ShalomCI (Streamlit GUI)

## Launch

```bash
.venv/bin/python -m streamlit run src/gui/app.py --server.headless true --server.port 8599 --browser.gatherUsageStats false
```

Run in background; app is up when `curl -s http://localhost:8599` returns 200 (~5s).
**Restart the server after editing any `src/` module** — Streamlit does not reload
imported modules (e.g. `ui_helpers.RTL_CSS` is baked at import).

## Drive (Playwright)

Project venv has no pip/playwright (uv-managed). Use a scratch venv:

```bash
uv venv $SCRATCH/pwenv && uv pip install --python $SCRATCH/pwenv/bin/python playwright
$SCRATCH/pwenv/bin/playwright install chromium
```

Key selectors / flow:
- Upload: `page.set_input_files('[data-testid="stFileUploaderDropzone"] input[type="file"]', bom_path)`
- Sample BOM: `TestData.csv` at repo root (tracked in git; restore with `git checkout -- TestData.csv` if missing)
- Run: `page.get_by_role("button", name="הפעל ניתוח").click()` then
  `page.wait_for_selector("text=ציון סיכון כללי", timeout=120000)` — real Mouser API calls, needs `.env` with `MOUSER_API_KEY`; `st.cache_data` makes reruns instant.
- Table is plain HTML (`pandas.Styler` via `st.html`): `page.locator("table")`.
- KPI strip: `[data-testid="stMetric"]`.

## Gotchas

- Much Hebrew text is injected via CSS `::after` (uploader dropzone, upload button
  caption) — it is **invisible to `inner_text()`**; screenshots are the only ground
  truth for those. Conversely, English text hidden with `font-size: 0` still shows
  up in `inner_text()`.
- The universal `* { font-size: 1rem }` rule in `RTL_CSS` re-applies size to
  descendants — hiding text needs `element, element *` selectors.
- RTL page flips neutral-direction strings like "1.0 / 5.0" — check numbers
  visually; LRI/PDI isolates (`⁦…⁩`) fix it.
- Emoji render as tofu (□) in headless Chromium (no emoji font) — environment
  artifact, not an app bug.
