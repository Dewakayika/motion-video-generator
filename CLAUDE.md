# Interlace motion videos

HTML + GSAP animations rendered to MP4. Explainer videos of app pages are built from real screenshots.

- For any explainer/walkthrough video work (new, update, re-render, voiceover), follow `.claude/skills/explainer-video/SKILL.md`. Its `style.md` and `qa-checklist.md` define the look and the checks; keep new videos consistent with `projects/signature-template-builder/` (light) and `projects/migration-occupation-detail/` (dark).
- New explainers start as a copy of `templates/explainer/` in `projects/<product>-<page>/`. Finished MP4s go in that project's `output/`.
- Tools (run from the repo root): `tools/frames.py` (QA contact sheets), `tools/render.py` (MP4), `tools/vo.py` (ElevenLabs voiceover).
- Never change data in the apps being filmed: no Save/Submit/Delete during capture.
- API keys (ElevenLabs) live only in the person's environment (`ELEVENLABS_API_KEY`). Never put a key in a command, a file or a commit; if one is pasted in chat, ask the person to regenerate it.
- `_archive/` holds third-party reference videos: do not use them in outputs or share them.
- Captions are the voiceover script: English unless the person asks otherwise, real numbers only, exact UI labels.
