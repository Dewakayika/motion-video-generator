# EOI Dashboard explainer (104s, 16:9, English captions)

Walkthrough of the EOI Analysis page (`localhost:3000/dashboard/eoi-analysis`), built from real screenshots of the page. The content follows `Migration-Intelligence-Platform-2/documentation/eoi-skillselect.md`.

- `eoi-explainer.html`: the video (HTML/CSS + GSAP). Open it in a browser to play/scrub.
- `output/eoi-explainer-1080p.mp4`: rendered output.
- `capture.py`: logs in to the local platform and re-captures `shots/` (all filters, 190 + WA, 189 + NSW, Point Heatmap, State Matrix, Point Heatmap 190 + VIC Submitted and Invited). Run it again when the dashboard UI or data changes. Login comes from `EOI_USER` / `EOI_PASS`, defaulting to the local test account.
- `shots/`: 2x page captures used by the video, plus `boxes.json` (element positions in page px).

## Scenes
Intro 0–5.5 · What is an EOI 5.5–15 · Dashboard overview 15–20 · Filters 20–29 · KPI cards 29–41 · Total Count chart 41–52 · Points Distribution 52–59 · Filter example 190 + WA 59–67 · Occupations table 67–75 · Point Heatmap with its State and Status filters (190 + VIC, Submitted then Invited) 75–90.5 · State Matrix 90.5–94 · 189 + state warning 94–99 · Summary 99–104.

## Where to edit
- Captions: the `CAP` array (`[start, end, text]`). Scene markers: `SCN`.
- Highlight positions: the `B` object (boxes in dashboard page px). If the UI layout changes, update them from `shots/boxes.json`.
- Camera moves, spotlights and callouts: `build()`, one commented block per scene with its time range.

## Render
From the repo root:
```
python tools/render.py projects/migration-eoi-analysis/eoi-explainer.html      # frames + MP4 in projects/migration-eoi-analysis/output/
python tools/frames.py projects/migration-eoi-analysis/eoi-explainer.html --scenes   # quick visual check (contact sheets)
```
