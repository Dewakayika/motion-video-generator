# Genuine Solutions – 60s bumper animatic

- `index.html`: the original 60s animatic (HTML/CSS + GSAP 3.12.5 from cdnjs, Plus Jakarta Sans from Google Fonts). Open it in a browser to play/scrub.
- `index-60s.html`: 60s cut in the clean dark style, with product UI rebuilt from the Figma file (Find Candidates, Kanban, Resume sheet, job-seeker onboarding, dashboard, application detail).
- `index-30s.html`: 30s cut in the same style.
- The 30s Interlace Studies promo now lives in `projects/interlace-promo/`. Notes kept here for reference: 30s Interlace Studies promo (16:9, brand blue/white). Five sections: Hook 0–6.2, Services 6.2–12.6, Migration agents 12.6–18.6, Success story 18.6–25, Call to action 25–30. Services is a Pinterest-style rotating card wheel (`WHEEL` constant; photos in `assets/interlace/photos/`, taken from interlace.com.au). Logo in `assets/interlace/` (`logo-crop.png` for light scenes, `logo-white.png` for the CTA). Migration agents (`AGENTS`: name, MARN, photo in `assets/interlace/agents/`) come from interlace.com.au. The success story is a testimonial carousel (`TESTI`) using Google reviews shown on interlace.com.au.
- `../../assets/figma/`: icons and images downloaded from Figma for those screens.
- Render from the repo root: `python tools/render.py projects/genuine-solutions-bumper/index-60s.html` (frames + MP4 in `output/`).
- `output/`: rendered cuts (30s, 60s, 60s portrait).

## Where to edit
- Scene markup: the `scenes.innerHTML` template in the `<script>`.
- UI recreations: `dashLeads()`, `dashJob()`, `myApps()`, plus the phone screens in scene 9.
- Timing: everything lives in `build()`; each scene block is commented with its time range (e.g. `/* 6 Matching 28–36 */`). Times are absolute seconds.
- Colours: CSS tokens `--navy #09295C`, `--green #41FF95`, `--deep #061A3A`.
- VO captions: the `VO` array. Scene markers: the `SCN` array.

## Production swaps
- Replace the text-based `LOGO` constant with the official logo SVG.
- Replace the flat gradient star (`#bigstar`) with a rendered 3D star if needed.
- Requires internet for GSAP and the font; for offline rendering, download gsap.min.js locally and install Plus Jakarta Sans.
