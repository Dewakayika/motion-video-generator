# <Page name> explainer (<length>s, 16:9, <light|dark> look, English captions)

Walkthrough of <page> (`<url>`), built from real screenshots of the page. The content follows `<path to the source documentation>`.

- `explainer.html`: the video (HTML/CSS + GSAP). Open it in a browser to play/scrub. Rename it to `<page>-explainer.html`.
- `output/<page>-explainer-1080p.mp4`: rendered output (and `-vo-1080p.mp4` with voiceover).
- `capture.py`: logs in to the local app and re-captures `shots/` (<list the states>). Run it again when the UI or data changes. Nothing is saved in the app.
- `shots/`: 2x captures used by the video, plus `boxes.json` (element positions in page px).
- `vo/`: voiceover clips (one per caption), created by `tools/vo.py`.

## Scenes
Intro 0–5 · <scene> a–b · … · Summary x–y.

## Where to edit
- Captions (= voiceover script): the `CAP` array (`[start, end, text]`). Scene markers: `SCN`.
- Highlight positions: the `B` object (boxes in page px). If the UI layout changes, update them from `shots/boxes.json`.
- Camera moves, spotlights and callouts: `build()`, one commented block per scene with its time range.
- Look: `data-look="light"` or `"dark"` on `#stage`.

## Render
From the repo root:
```
python tools/frames.py projects/<project>/<page>-explainer.html --scenes   # contact sheets to check
python tools/render.py projects/<project>/<page>-explainer.html            # MP4 in output/
```

## Voiceover (optional, ElevenLabs)
```
python tools/vo.py gen projects/<project>/<page>-explainer.html     # needs ELEVENLABS_API_KEY in the environment
python tools/render.py projects/<project>/<page>-explainer.html
python tools/vo.py mux projects/<project>/<page>-explainer.html projects/<project>/output/<page>-explainer-1080p.mp4
```
