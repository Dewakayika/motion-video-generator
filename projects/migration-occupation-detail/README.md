# Occupation Detail explainer (148s, 16:9, English captions)

Walkthrough of the Occupation Detail page (`localhost:3000/dashboard/occupation/261313`, Software Engineer), built from real screenshots of the page. It covers every section: top-bar filters, header, KPI strip, Visa & State Streams (cards, status, table, month and state filters, national visas) and the four Detailed Analytics tabs. The SkillSelect parts follow `Migration-Intelligence-Platform-2/documentation/occupation-visa-streams.md`; the other tabs follow the page itself (`frontend/src/app/dashboard/occupation/[anzsco]/page.tsx`).

- `occupation-explainer.html`: the video (HTML/CSS + GSAP). Open it in a browser to play/scrub.
- `output/occupation-explainer-1080p.mp4`: rendered output.
- `capture.py`: logs in to the local platform and re-captures `shots/` (default view, Quiet tooltip, sticky bar, Table view, June 2026, June 2026 + SA, Subclass 189, and the Demand, Workforce and Regional tabs). Run it again when the page UI or data changes. Login comes from `EOI_USER` / `EOI_PASS`, the occupation from `OCC_ANZSCO` (default 261313).
- `shots/`: 2x page captures used by the video, plus `boxes.json` (element positions in page px). `quiet_tip.jpg` and `sticky.jpg` are viewport captures; the video places them at their scroll offset (255 px and 867 px).

## Scenes
Intro 0–5.5 · What the page answers 5.5–15 · Page overview 15–21 · Filters and sticky bar 21–31 · Header and Invite Rate 31–37 · KPI strip 37–49 · Stream cards (cutoff, consistency, status tooltip) 49–64 · Reading example and Table view 64–73 · One month, then one state (June 2026, SA) 73–85 · National visas (189) 85–91 · EOI & Invitations tab 91–102 · Demand & Vacancies 102–116 · Workforce & Demographics 116–129 · Regional & AI Forecasts 129–142 · Summary 142–148.

## Where to edit
- Captions: the `CAP` array (`[start, end, text]`). Scene markers: `SCN`.
- Highlight positions: the `B` object (boxes in dashboard page px). If the UI layout changes, update them from `shots/boxes.json`.
- Camera moves, spotlights and callouts: `build()`, one commented block per scene with its time range.

## Render
From the repo root:
```
python tools/render.py projects/migration-occupation-detail/occupation-explainer.html      # frames + MP4 in projects/migration-occupation-detail/output/
python tools/frames.py projects/migration-occupation-detail/occupation-explainer.html --scenes   # quick visual check (contact sheets)
```
