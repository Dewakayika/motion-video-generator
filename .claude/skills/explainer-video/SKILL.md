---
name: explainer-video
description: Make a product explainer / walkthrough video (16:9 MP4, captions, optional ElevenLabs voiceover) for a page of a web app, built from real screenshots with HTML + GSAP in this repo. Use when someone asks for an explainer, walkthrough, tutorial or "how to read this page/dashboard" video, or wants to update, re-render, retime or add a voiceover to one of the videos in projects/.
---

# Explainer video

Every video in `projects/` is one HTML page: real screenshots of the app, a GSAP timeline that moves a camera over them, spotlights, callouts, a cursor, and captions that are also the voiceover script. `tools/render.py` turns the page into an MP4. Follow the steps in order; each ends with something the person can check.

Reference examples (copy their patterns, not their content):
- `projects/signature-template-builder/`: light look, editing flow (dialogs, panels, inserted tokens, preview), voiceover with retiming.
- `projects/migration-occupation-detail/`: dark look, long dashboard page, filters changing every number, four analytics tabs.
- `projects/migration-eoi-analysis/`: dark look, charts and heatmaps.

Read `style.md` (look, motion, captions) before building and `qa-checklist.md` before rendering.

## 0. Inputs to get first
Ask only for what you cannot find:
1. **Page URL** and how to run the app locally, plus a **test login** (never a real user's password; prefer environment variables).
2. **Source documentation** for the page (a markdown doc, a spec). Without one, the page source code is the documentation.
3. **Audience and language** of the captions (default: English, for end users of the app).
4. **Look**: light or dark (match the app's theme the viewers use).
5. Voiceover wanted? (ElevenLabs needs the person's API key in their own environment, see step 7.)

## 1. Understand the page (storyboard)
- Read the documentation fully, then the page component(s) for anything the doc does not cover (sections, tabs, labels, tooltips, how each number is computed).
- Open the live page with Playwright and take one exploratory full-page screenshot per tab/state to see the real layout.
- Write a storyboard: a table of scenes with time range, what is on screen (which captured state, which element is highlighted), the caption, and where each number comes from. Typical shape, 100–150 s:
  Intro (5 s) · one or two designed concept scenes (what the page answers, key terms) · layout overview · one scene per section of the page · a worked example with real numbers · what changes when filters change · limits / watch-outs · summary of three rules.
- The `explainer-storyboard` agent can do this step; check its numbers against the screenshots yourself.
- Show the storyboard to the person before building when the video is new or the scope is unclear.

## 2. Create the project
```
cp -r templates/explainer projects/<project-name>      # kebab-case: <product>-<page>
mv projects/<project-name>/explainer.html projects/<project-name>/<page>-explainer.html
```
Delete the placeholder `shots/overview.jpg` once real captures exist.

## 3. Capture real screenshots (`capture.py`)
- One `shot()` per state the storyboard needs (default view, each filter change, each tab, open dialogs, tooltips, a filled form, the preview after an edit).
- Viewport 1920×1080, `device_scale_factor=2`, always. Full-page shots for scrolling pages; viewport shots for overlays and tooltips (place them in the HTML at their scroll offset: `style="top:<scrollY>px"`).
- Force the theme before load (cookie + localStorage + `color_scheme`), hide dev overlays (Laravel Debugbar, Next.js indicators), move the mouse away before each shot.
- **Never change app data.** Do not click Save/Submit/Delete/Create; dismiss confirm dialogs; close the browser without saving. Demo edits (adding a field, typing in an editor) are fine because they stay in the page. If a state can only exist with saved data, draw it as a designed scene and say so, or ask the owner.
- Rich-text editors insert at the cursor: click into the editor and press Ctrl+End before inserting, or the token lands at the start.
- Write `shots/boxes.json` (element boxes) and read real numbers from the captures (zoom in on crops) for the captions. Never invent a number.
- If the page shows something wrong (a bug, a misleading label), keep the camera off it and tell the person; do not narrate a bug as a feature.

## 4. Build the page
Edit only these parts of the HTML (the engine below them stays as in the template):
- `#scenes` markup for designed (non-screenshot) scenes, `<img class="shot">` tags for the captures.
- `CAP` (captions = voiceover), `SCN` (scene markers), `DUR`, `B` (boxes in page px from `boxes.json`).
- `build()`: one commented block per scene with its time range, using the helpers `cam(camFor(box,rect),t)`, `spot(box,t)`, `co(K(kicker,title,text),pos)` + `pop/hide`, `swap(fromShot,toShot,t)`, `cursorIn/clickOn`, `words()`.
Rules from `style.md` apply: one idea per caption, callouts never cover the thing they explain or the caption band, every highlight is on a real element.

## 5. Check (QA) before rendering
```
python tools/frames.py projects/<p>/<page>.html --scenes          # middle of every scene
python tools/frames.py projects/<p>/<page>.html 12.5,31,48        # specific moments
```
Open the `sheet_*.jpg` contact sheets and go through `qa-checklist.md`. Fix and re-check. The `explainer-qa` agent can run this loop. `PROBLEM` lines mean a missing file or a page error: fix them first.

## 6. Render
```
python tools/render.py projects/<p>/<page>.html      # → projects/<p>/output/<page>-1080p.mp4
```
About 6–10 minutes per minute of video; run it in the background. Verify with `ffprobe` (1920×1080, expected duration).

## 7. Voiceover (optional)
The captions are the script. The person sets `ELEVENLABS_API_KEY` in their own terminal (never paste keys into chat, files or command lines; if one is pasted, tell them to regenerate it).
```
python tools/vo.py gen projects/<p>/<page>.html      # person runs this (needs the key); writes vo/ and WARP into the page
python tools/render.py projects/<p>/<page>.html      # re-render with the new timing
python tools/vo.py mux projects/<p>/<page>.html projects/<p>/output/<page>-1080p.mp4
```
`gen` speaks at natural speed and stretches the timeline (`WARP`) wherever a line needs more room, so the video follows the voice. Clips are cached in `vo/clips.json`: only changed captions are generated again. Pronunciation fixes go in a `--fix` JSON (`{"caption": "spoken text"}`). Default voice: Charlie (Australian English); `--voice <id>` to change.

## 8. Hand over
Write the project `README.md` (from the template: scenes with times, where to edit, render and voiceover commands), then tell the person: the output path, length, what is drawn rather than captured, anything in the app that looked wrong, and the voiceover text if they need it.

## Gotchas (all hit in real projects)
- In Playwright, `page.evaluate("t => { TL.seek(t); }")`: keep the braces. Returning the GSAP timeline makes Playwright try to serialise it and hang.
- `TL.seek()` suppresses callbacks, so anything that must happen on seek is a tweened property (see `retime()`), never `onUpdate`.
- `render.py` clears `frames/<page>/` first; old frames past the new end would otherwise end up in the MP4.
- A file open in a video player cannot be moved or overwritten on Windows: close it first.
- Fonts and GSAP load from CDNs: rendering needs internet.
