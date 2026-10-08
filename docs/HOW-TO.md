# How to make an explainer video

This guide shows how to turn a page of one of our web apps into a 2–3 minute explainer video: real screenshots, a camera that moves to each part of the page, highlights, short explanations, captions and an optional AI voiceover. The three videos in `projects/` were made this way; use them as the quality bar.

There are two ways to work: ask Claude Code to do it (recommended, it follows the same process every time), or run the steps yourself.

---

## 1. One-time setup

You need:
- **Python 3.11+**, then in the repo folder:
  ```
  pip install -r requirements.txt
  python -m playwright install chromium
  ```
- **ffmpeg** on your PATH (`ffmpeg -version` should work). Windows: `winget install Gyan.FFmpeg`. Mac: `brew install ffmpeg`.
- **Internet** while rendering (the animation library and the font load from CDNs).
- **The app running locally** (the page you want to explain) and a **test login** for it.
- **Claude Code** (optional but recommended), opened in this repo folder so it picks up `CLAUDE.md` and `.claude/`.
- **ElevenLabs account** (optional, only for voiceover). See section 5.

Check everything works by rendering an existing video:
```
python tools/frames.py projects/signature-template-builder/template-builder-explainer.html --scenes
```
This writes contact sheets to `frames/_qa/…/sheet_*.jpg`. Open one: you should see frames of the video.

---

## 2. Making a video with Claude Code (recommended)

Open Claude Code in this folder and describe the video. Give it the page, the documentation and how to log in. For example:

> Make an explainer video for the Reports page, http://localhost:8000/reports. The documentation is in C:\…\Documentation\Reports.md. Log in with the seeded admin account. Light look, English captions, about 2 minutes.

Claude uses the `explainer-video` skill (`.claude/skills/explainer-video/SKILL.md`) and will:
1. **Plan**: read the documentation and the page code, look at the live page, and propose a storyboard (scenes, captions, which screens to capture). It may use the `explainer-storyboard` agent. **Review it**: are these the right sections, in the right order, with the right message?
2. **Capture**: write `capture.py` and take real screenshots. It never saves or deletes anything in the app.
3. **Build**: create `projects/<name>/` from the template and animate it.
4. **Check**: grab frames at every scene and fix overlaps or misplaced highlights (the `explainer-qa` agent).
5. **Render**: produce `projects/<name>/output/<page>-explainer-1080p.mp4`.
6. **Report**: tell you what it made, anything it had to draw instead of capture, and anything in the app that looked wrong.

Good follow-up requests:
- "Make the KPI scene slower." / "The callout covers the chart at 0:42, move it."
- "Change the caption at 1:05 to …" (then re-render).
- "Add a voiceover." (see section 5)
- "Re-capture the screenshots, the UI changed." (runs `capture.py` again)

---

## 3. Making a video by hand

1. **Copy the template**
   ```
   cp -r templates/explainer projects/reports-page
   ```
   Rename `explainer.html` to `reports-page-explainer.html`.
2. **Capture.** Edit `capture.py` (URL, login, one block per state you need) and run it from the project folder: `python capture.py`. Screenshots land in `shots/`, element positions in `shots/boxes.json`.
3. **Write the storyboard in the HTML.** In `reports-page-explainer.html`, change:
   - `CAP`: the captions, `[start, end, "text"]`. They are also the voiceover script.
   - `SCN`: scene names for the player's scrubber.
   - `B`: boxes of the elements you highlight (copy from `boxes.json`).
   - `<img class="shot">` tags for each screenshot.
   - `build()`: the animation, one commented block per scene. The template has an example of every move (camera, spotlight, callout, cursor click, screen swap).
4. **Preview** by opening the HTML in a browser (Space = play/pause, drag the bar to scrub).
5. **Check** with `python tools/frames.py projects/reports-page/reports-page-explainer.html --scenes` and go through `.claude/skills/explainer-video/qa-checklist.md`.
6. **Render**: `python tools/render.py projects/reports-page/reports-page-explainer.html` (about 6–10 minutes per minute of video).

The look and writing rules are in `.claude/skills/explainer-video/style.md`. Keep to them so every video looks like part of one series.

---

## 4. Rules that keep the quality consistent

- **Real screenshots, real numbers.** Every number on screen must be visible in a capture or in the documentation.
- **Never change app data while capturing.** No Save, Submit, Create or Delete. If a screen needs saved data, show it as a designed scene instead.
- **One idea per caption**, 3.5–5 seconds, under ~80 characters, with the app's exact labels.
- **Highlights on real elements; explanations beside them,** never covering them or the captions.
- **Check before rendering** (section 3, step 5). Rendering takes minutes; checking takes seconds.
- **Report app problems instead of filming them.**

---

## 5. Voiceover (ElevenLabs)

The captions become the voiceover. The video is retimed to the voice, so nothing sounds rushed and every line stays in sync with its highlight.

1. Create an ElevenLabs account and an API key (Profile → API Keys). A paid plan is needed for commercial use. The free plan has a monthly character limit; a 2.5-minute video is about 2,000 characters.
2. Set the key **in your own terminal** (never paste it into chat, files or shared documents):
   - PowerShell: `$env:ELEVENLABS_API_KEY="sk_..."` (this window only) or `setx ELEVENLABS_API_KEY "sk_..."` (permanent, restart the terminal/VS Code)
   - Mac/Linux: `export ELEVENLABS_API_KEY="sk_..."`
3. Generate the voice (you run this; it uses your key):
   ```
   python tools/vo.py gen projects/<p>/<page>.html
   ```
   It creates one clip per caption in `projects/<p>/vo/` and writes the new timing into the page.
4. Re-render and mix (Claude can do these; no key needed):
   ```
   python tools/render.py projects/<p>/<page>.html
   python tools/vo.py mux projects/<p>/<page>.html projects/<p>/output/<page>-1080p.mp4
   ```
   Result: `output/<page>-vo-1080p.mp4` (and `<page>-vo.wav`, the voice only).

Change the voice with `--voice <voice id>` (default: Charlie, Australian English). If a word is pronounced badly, add a `--fix fixes.json` with `{"caption text": "how to say it"}`. Only changed lines are generated again.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `PROBLEM failed to load …` from frames.py | A screenshot or asset path is wrong; check the file exists. |
| Render hangs at the start | Check internet (CDN). Never return the timeline from `page.evaluate` (keep `{ TL.seek(t); }`). |
| The MP4 has extra frames at the end | Use `tools/render.py`, which clears old frames first. |
| "Device or resource busy" moving or overwriting an MP4 | The file is open in a video player; close it. |
| Screenshots in dark mode instead of light | Set the theme in `capture.py` (cookie + localStorage + `color_scheme`). |
| A dev toolbar shows in the screenshots | Add its selector to `HIDE` in `capture.py`. |
| `vo.py gen` says the page has no WARP | Copy the "Voiceover retiming" block from `templates/explainer/explainer.html`. |
| ElevenLabs `401` / `missing_permissions` | The key needs Text to Speech access; listing voices is not required. |
