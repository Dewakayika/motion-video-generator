# Interlace motion videos

Product explainers, promos and bumpers built as HTML + GSAP and rendered to MP4. Explainers use real screenshots of the apps, a moving camera, spotlights, callouts and captions, with an optional AI voiceover (ElevenLabs).

New here? Read **[docs/HOW-TO.md](docs/HOW-TO.md)**. With Claude Code, the `explainer-video` skill in `.claude/` does the whole process the same way every time.

## What is in the repo

```
.claude/
  skills/explainer-video/   SKILL.md (the process), style.md (look, motion, captions), qa-checklist.md
  agents/                   explainer-storyboard (plans a video), explainer-qa (checks frames before rendering)
  settings.json             lets Claude run the render/QA tools without asking each time
templates/explainer/        starter for a new explainer: explainer.html, capture.py, README.md, placeholder shot
tools/
  render.py                 HTML → frames → MP4 (projects/<p>/output/)
  frames.py                 QA contact sheets at chosen moments, reports missing files
  vo.py                     ElevenLabs voiceover: generate per caption, retime the video, mix into the MP4
projects/
  signature-template-builder/   Template Builder explainer · light · 2:30 with voiceover
  migration-occupation-detail/  Occupation Detail explainer · dark · 2:28
  migration-eoi-analysis/       EOI Analysis explainer · dark · 1:44
  interlace-promo/              Interlace Studies 30 s promo
  genuine-solutions-bumper/     Genuine Solutions bumper, 30 s / 60 s / portrait cuts
assets/                     shared logos, photos and Figma exports
docs/HOW-TO.md              step-by-step guide
frames/                     render scratch (git-ignored, safe to delete)
_archive/                   third-party reference videos and scratch files (git-ignored, not for sharing)
```

Each project folder has its own README (scenes with times, where to edit, how to render) and an `output/` folder with the finished MP4s.

## Quick start

```
pip install -r requirements.txt
python -m playwright install chromium
# ffmpeg must be on PATH

python tools/frames.py projects/signature-template-builder/template-builder-explainer.html --scenes   # check
python tools/render.py projects/signature-template-builder/template-builder-explainer.html            # render
```

Open any `projects/*/*.html` in a browser to play and scrub it. Rendering needs internet (GSAP and fonts load from CDNs).
