# Template Builder explainer (130s, 16:9, light mode, English captions)

Walkthrough of the Template Builder (`localhost:8000/signatures/modular/builder`), built from real light-mode screenshots of the page. The content follows `interlace-education-portal/Documentation/02-Features/Digital-Signatures/TEMPLATE_BUILDER.md`.

- `template-builder-explainer.html`: the video (HTML/CSS + GSAP). Open it in a browser to play/scrub.
- `output/template-builder-explainer-1080p.mp4`: rendered output.
- `capture.py`: logs in to the local portal and re-captures `shots/` in light mode: default view, New template bar, From library, a hidden section (Unsaved changes), HTML mode, Custom fields (empty, Save blocked, three fields), Fee schedule (empty, three fees), inserting a field token, a new "Fee Summary" section with the fee tokens, and the preview with the fee tables. Nothing is saved: the demo edits stay in the page and the browser closes without Save. Login comes from `SIG_USER` / `SIG_PASS` (default: seeded admin).
- `shots/`: 2x viewport captures (1920×1080 CSS px) used by the video, plus `boxes.json` (element positions).

The Create Agreement form (staff side) is shown as a drawn scene, not a screenshot, because capturing it would need a template saved with fields and fees and a service linked to it. No section in the local data is shared between templates, so the orange "Make a copy for this template" warning is only mentioned in the summary.

## Scenes
Intro 0–5.2 · One screen, four jobs 5.2–13.8 · Three kinds of variables 13.8–21.8 · Layout 21.8–26.8 · Pick or create a template 26.8–35.6 · Sections (order, on/off, Unsaved changes, new section, library) 35.6–48.2 · Editor (Visual/HTML, page options) 48.2–56.2 · Custom fields 56.2–70.2 · Fee schedule 70.2–84.2 · Insert tokens and preview 84.2–101.6 · Fee calculation 101.6–110.2 · Save & Cancel 110.2–115.8 · Create Agreement 115.8–124.6 · Summary 124.6–130.

## Where to edit
- Captions: the `CAP` array (`[start, end, text]`). Scene markers: `SCN`.
- Highlight positions: the `B` object (boxes in builder viewport px). If the UI layout changes, update them from `shots/boxes.json`.
- Camera moves, spotlights and callouts: `build()`, one commented block per scene with its time range.

## Voiceover (ElevenLabs)
The video timing follows the voice. `tools/vo.py` reads the key from `ELEVENLABS_API_KEY` only.
```
python tools/vo.py gen projects/signature-template-builder/template-builder-explainer.html   # needs the key
python tools/render.py projects/signature-template-builder/template-builder-explainer.html
python tools/vo.py mux projects/signature-template-builder/template-builder-explainer.html projects/signature-template-builder/output/template-builder-explainer-1080p.mp4
```
- `vo/NN.mp3`: one clip per caption, cached in `vo/clips.json`, so only changed lines are generated again.
- `WARP` in the page: `[[original time, new time], ...]`. Where a clip needs more room than the gap to the next caption, that stretch of the animation plays slower. `const WARP=[]` restores the original timing.
- Output: `output/template-builder-explainer-vo-1080p.mp4` and `template-builder-explainer-vo.wav` (voice only). Default voice: Charlie (Australian English); change it with `--voice <id>`.

## Render
From the repo root:
```
python tools/render.py projects/signature-template-builder/template-builder-explainer.html      # frames + MP4 in projects/signature-template-builder/output/
python tools/frames.py projects/signature-template-builder/template-builder-explainer.html --scenes   # quick visual check (contact sheets)
```
