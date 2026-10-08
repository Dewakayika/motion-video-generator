# Style: how the explainers look, move and read

The three finished explainers share these rules. Keep to them so every video looks like part of one series.

## Frame
- 1920×1080 stage, 30 fps, MP4 H.264 (CRF 18).
- Safe margin 60 px. The caption band (bottom 44–150 px) is reserved for captions: no callout, card or highlight sits there.
- Font: Plus Jakarta Sans (400/500/600). Monospace for tokens/code: JetBrains Mono.

## Looks
Set with `data-look` on `#stage`; colours are CSS variables in the template, never hard-coded in scenes.

| | Light (`light`) | Dark (`dark`) |
|---|---|---|
| Use for | apps used in light mode, admin tools | dashboards shown in dark mode |
| Background | `#F3F6FB` + soft blue blobs | `#050A16` + one blue blob |
| Panels / cards | white, 1 px `#DCE4EF`, radius 26 | `#0E1729`, 1 px faint line |
| Text | `#0F2440`, muted `#5B6B80` | `#EAF1FB`, muted `#93A4BF` |
| Accent | `#3467AD` (brand blue), highlight `#2F6FD6` | `#3B82F6`, highlight `#60A5FA` |
| Warning callout | orange `#C2620A` on `#FFF8F0` | orange `#F59E0B` |
| Spotlight dim | `rgba(15,30,55,.42)` | `rgba(3,6,16,.68)` |
| Logo | `assets/interlace/logo-crop.png` | `assets/interlace/logo-white.png` |

## Type sizes (stage px)
Title 80 (intro), 60 (scene titles), 72 (summary) · eyebrow 20 uppercase, letter-spacing .2em · callout title 30, text 21 · card title 28–32, text 21–22 · caption 34.

## Motion vocabulary
Use only these moves; they are the helpers in the template.
| Move | Helper | Timing |
|---|---|---|
| Window flies in, then fills the frame | `#win` fromTo scale .72→.8, then →1 | 1.2 s in, 1.1 s fill |
| Camera to a region | `cam(camFor(box, rect), t)` | 1.0–1.3 s, power2.inOut |
| Spotlight on an element | `spot(box, t)` | 0.5–0.6 s |
| Callout | `pop(co(...), t)` / `hide` | 0.55 s in, 0.3 s out |
| Switch to another captured state | `swap(fromShot, toShot, t)` | 0.45 s cross-fade |
| Click | `cursorIn` + `clickOn`, then `swap` ~0.8 s later | cursor 0.7 s travel |
| Title words | `words(el, t)` | stagger .07–.08 |
| Lists / cards | `fromTo` with `stagger` | .35–1.3 s apart |

- Zoom so the thing explained fills most of the frame: camera rect ~1800×860 for wide regions, ~1000×870 when a callout sits beside it.
- Hold a callout at least 2.5 s; move the spotlight before the callout that explains it.
- Camera moves overlap the end of the previous caption by ~0.2 s, never mid-sentence of the next.

## Captions (they are also the voiceover)
- One idea per caption, ≤ ~80 characters, 3.5–5 s on screen (about 2.5 words per second).
- Plain English, present tense, second person where it helps ("Pick a template here…").
- Use the UI's exact labels; put them in `<em>` when a caption names a control.
- Real numbers only, read from the capture; round the way the UI does.
- No abbreviations the voice cannot read: write "Estimated" not "Est.", "info icon" not "(i)".
- The intro caption names the page; the last caption repeats the three rules of the summary scene.

## Callouts
- Kicker (uppercase, small) = the UI label; title = the answer in a few words; text = one sentence of why/how.
- Place beside or under the highlighted element, never on top of it; never over the caption band.
- Use the orange `warn` callout only for real pitfalls (data that misleads, actions with side effects).

## Designed scenes (not screenshots)
Use them for concepts the UI cannot show: what the page answers, key terms, a worked calculation, flows that would need saved data. Cards on the stage background, the same type scale, and real values from the documentation.
