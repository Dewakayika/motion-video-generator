# QA checklist (before every render)

Run `python tools/frames.py projects/<p>/<page>.html --scenes` and look at every contact sheet. Add specific times for each callout and each swap. Fix, then check again.

## Loads
- [ ] No `PROBLEM` lines (missing screenshot, wrong asset path, page error).
- [ ] Logo, fonts and screenshots render; no broken-image icons.

## Every frame
- [ ] The spotlight frames a real element, with the element fully inside it.
- [ ] Callouts sit beside or under what they explain, never on top of it, never in the caption band.
- [ ] Captions are on one line (two at most) and do not cover a callout.
- [ ] Nothing is cut off at the frame edge (60 px safe margin).
- [ ] The screenshot shown matches what the caption says (right state, right filter, right tab).
- [ ] No hover artefacts, dev overlays, cookie banners or personal data in the captures.

## Content
- [ ] Every number in a caption or callout appears in the capture or the documentation.
- [ ] UI labels are spelled exactly as in the app.
- [ ] Nothing that looks like a bug is on camera; anything odd is reported to the person instead.
- [ ] States that could not be captured without saving data are drawn scenes, and the README says so.

## Timing
- [ ] Each caption 3.5–5 s, ≤ ~80 characters, one idea.
- [ ] Callouts hold ≥ 2.5 s; no camera move starts mid-sentence.
- [ ] `SCN` markers match the scene blocks in `build()`; `DUR` covers the last caption + ~0.5 s.

## After rendering
- [ ] `ffprobe` shows 1920×1080 and the expected duration (`OUT` when the page is retimed).
- [ ] With voiceover: spot-check 2–3 lines; the caption appears as its line starts.
