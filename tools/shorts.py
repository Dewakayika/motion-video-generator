"""Portrait shorts (TikTok / Reels / Shorts, 1080x1920) from templates/shorts/.

Run from the repo root:
  python tools/shorts.py new <name> --voice <voice.mp3> [--presenter <clip.mp4>]   # projects/<name>/
  python tools/shorts.py config <name> --interactive   # project setup questions (asked first; answers saved in config.json)
  python tools/shorts.py segments <name>          # find the spoken lines in voice.mp3 -> segments.js
  python tools/shorts.py sheet <name>             # QA contact sheet of every scene -> projects/<name>/qa/sheet.jpg
  python tools/shorts.py render <name> [--music bg.mp3] [--fps 30]   # -> projects/<name>/output/<name>-1080x1920.mp4
  python tools/shorts.py capture <name> --url <page> [--find "exact text on the page"] [--name shot]
      # phone-width screenshot of a public page -> projects/<name>/shots/<shot>.png plus <shot>.json:
      # headings, the element holding --find, and a ready-to-paste "web" scene (highlight already placed)

A project holds short.html (engine, copied from the template), script.js (the content you edit),
segments.js (written by `segments`), voice.mp3 and optionally presenter.mp4 (with people) and images.
"""
import argparse, asyncio, json, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "templates" / "shorts"


def proj(name):
    p = pathlib.Path(name)
    p = p if p.is_dir() else ROOT / "projects" / name
    if not (p / "short.html").exists():
        sys.exit(f"{p} has no short.html (create it with: python tools/shorts.py new <name> --voice <file>)")
    return p.resolve()


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


# ---------- configuration (asked before anything else) ----------
CONFIG_QUESTIONS = [
    ("voice_language", "What language is the voiceover?", ["nepali", "english", "nepali + english mix"], "nepali + english mix"),
    ("caption_language", "What language should the on-screen captions be?", ["english", "nepali", "same as the voice"], "english"),
    ("voice_source", "Where does the voiceover come from?", ["i provide an audio file", "generate it with ElevenLabs", "the presenter's own audio"], "i provide an audio file"),
    ("voice_name", "ElevenLabs voice name (only if generating; leave blank otherwise)", None, ""),
    ("presenter", "Is there a person on camera?", ["no", "yes, footage provided"], "no"),
    ("look", "Visual look", ["interlace", "dark", "warm"], "interlace"),
    ("backdrop_mode", "Backdrops behind the scenes", ["images", "video clips", "mixed images and video", "none (plain background)"], "images"),
    ("backdrop_tool", "Make the backdrops with", ["kling", "elevenlabs", "higgsfield", "bloom", "my own files"], "kling"),
    ("backdrop_budget", "Spend limit for generated media (say the number and the unit, e.g. '1 USD' or '100 Kling credits')", None, "ask me before spending"),
    ("length_seconds", "Target length in seconds", None, "45-60"),
    ("music", "Background music", ["none", "my own licensed track"], "none"),
    ("logo", "Logo file inside the project folder", None, "logo.png"),
    ("sources", "Check facts on official pages and show the sources on screen?", ["yes", "no"], "yes"),
    ("privacy", "Names and personal details", ["no client names", "names are allowed"], "no client names"),
]
CONFIG_OPTIONAL = {"voice_name"}


def config_path(p):
    return pathlib.Path(p) / "config.json"


def new_config():
    return {"status": "needs-setup", "answers": {k: None for k, _, _, _ in CONFIG_QUESTIONS}}


def load_config(p):
    f = config_path(p)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def save_config(p, cfg):
    missing = [k for k, _, _, _ in CONFIG_QUESTIONS if k not in CONFIG_OPTIONAL and cfg["answers"].get(k) in (None, "")]
    cfg["status"] = "ready" if not missing else "needs-setup"
    config_path(p).write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return missing


def configure(p, interactive=False, sets=(), redo=False):
    cfg = load_config(p) or new_config()
    for item in sets:
        k, _, v = item.partition("=")
        if k not in cfg["answers"]:
            sys.exit("unknown setting '%s'. Settings: %s" % (k, ", ".join(cfg["answers"])))
        cfg["answers"][k] = v.strip()
    if interactive:
        print("\nProject setup. Press Enter to accept the suggestion in [brackets].\n")
        for key, question, choices, default in CONFIG_QUESTIONS:
            if cfg["answers"].get(key) not in (None, "") and not redo:
                continue
            print(question)
            for i, c in enumerate(choices or [], 1):
                print("  %d) %s" % (i, c))
            try:
                raw = input("  [%s] > " % default).strip()
            except EOFError:        # no real terminal (piped input): stop asking, leave the rest unanswered
                print("(no terminal to ask in: answer later with --interactive or --set)")
                break
            if raw.isdigit() and choices and 1 <= int(raw) <= len(choices):
                raw = choices[int(raw) - 1]
            cfg["answers"][key] = raw or default
            print()
    missing = save_config(p, cfg)
    print("configuration: %s" % cfg["status"])
    for key, question, _, _ in CONFIG_QUESTIONS:
        print("  %-18s %s" % (key, cfg["answers"].get(key) if cfg["answers"].get(key) not in (None, "") else "(not set)"))
    if missing:
        print("\nstill needed: %s\nanswer with:  python tools/shorts.py config <project> --interactive   or   --set key=value" % ", ".join(missing))
    return cfg, missing


def warn_config(p):
    cfg = load_config(p)
    if cfg is not None and cfg.get("status") != "ready":
        print("WARNING: %s is not configured yet. Run: python tools/shorts.py config %s --interactive" % (pathlib.Path(p).name, pathlib.Path(p).name), file=sys.stderr)


def cmd_config(a):
    p = proj(a.project)
    cfg, missing = configure(p, interactive=a.interactive, sets=a.set or [], redo=a.redo)
    if missing:
        sys.exit(1)


# ---------- new ----------
def cmd_new(a):
    dst = ROOT / "projects" / a.name
    if dst.exists():
        sys.exit(f"{dst} already exists")
    shutil.copytree(TEMPLATE, dst, ignore=shutil.ignore_patterns("README.md", "segments.js"))
    (dst / "output").mkdir()
    if a.voice:
        shutil.copy(a.voice, dst / "voice.mp3")
    if a.presenter:
        shutil.copy(a.presenter, dst / ("presenter" + pathlib.Path(a.presenter).suffix.lower()))
    print(f"created {dst}")
    save_config(dst, new_config())
    if sys.stdin.isatty():
        configure(dst, interactive=True)
    else:
        print(f"configuration needed first: python tools/shorts.py config {a.name} --interactive   (or let the director agent ask you)")
    if a.voice:
        a.project = a.name
        cmd_segments(a)


# ---------- segments ----------
def cmd_segments(a):
    p = proj(a.project)
    voice = p / "voice.mp3"
    if not voice.exists():
        sys.exit(f"put the voiceover at {voice}")
    total = duration(voice)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(voice), "-af",
                          f"silencedetect=noise={a.noise}dB:d={a.min_pause}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    segs, cur = [], 0.0
    for s, e in zip(starts, ends):
        if s - cur > 0.15:
            segs.append([round(cur, 2), round(s, 2)])
        cur = e
    if total - cur > 0.15:
        segs.append([round(cur, 2), round(total, 2)])
    (p / "segments.js").write_text(
        "// written by tools/shorts.py segments: [start, end] of each spoken line in voice.mp3\n"
        f"window.AUDIO_DURATION = {round(total, 2)};\nwindow.SEGMENTS = {json.dumps(segs)};\n", encoding="utf-8")
    print(f"{len(segs)} lines in {total:.1f}s of voice:")
    for i, (s, e) in enumerate(segs):
        print(f"  seg {i:2d}  {s:6.2f} - {e:6.2f}  ({e - s:4.1f}s)")


# ---------- browser ----------
async def open_page(pw, html, presenter, alpha=False):
    browser = None
    if presenter:  # bundled Chromium cannot decode H.264; Edge/Chrome can
        for ch in ("msedge", "chrome"):
            try:
                browser = await pw.chromium.launch(channel=ch)
                break
            except Exception:
                pass
    browser = browser or await pw.chromium.launch()
    page = await browser.new_page(viewport={"width": 1080, "height": 1920})
    await page.goto(html.as_uri() + ("?alpha=1" if alpha else ""), wait_until="load")
    await page.evaluate("() => document.fonts.ready")
    await page.wait_for_timeout(1200)
    await page.add_style_tag(content=(
        f"body{{padding:0!important;display:block!important;background:{'transparent' if alpha else '#000'}!important}}"
        "#viewport{width:1080px!important;border-radius:0!important;box-shadow:none!important}"
        "#controls{display:none!important}"))
    await page.evaluate("() => { fit(); TL.pause(); }")
    return browser, page


async def seek(page, t):
    await page.evaluate("async t => { TL.seek(t); await window.seekMedia(t); }", t)


# ---------- sheet ----------
async def sheet(p):
    from PIL import Image
    html = p / "short.html"
    qa = p / "qa"
    qa.mkdir(exist_ok=True)
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser, page = await open_page(pw, html, any(p.glob("presenter.*")))
        times = await page.evaluate("""() => { const d = window.DUR; const ts = new Set();
            TL.getChildren(false, true, false).forEach(c => { const t = c.startTime(); if (t > .05 && t < d) ts.add(Math.round((t + .9) * 10) / 10); });
            return [...ts].sort((a, b) => a - b).filter((t, i, a) => i === 0 || t - a[i - 1] > .8).concat([d - .1]); }""")
        shots = []
        for t in times:
            await seek(page, t)
            f = qa / f"t{t:06.1f}.jpg"
            await page.screenshot(path=str(f), type="jpeg", quality=80)
            shots.append((t, f))
        await browser.close()
    cols, w, h = 6, 270, 480
    rows = (len(shots) + cols - 1) // cols
    sheet_img = Image.new("RGB", (cols * w, rows * (h + 30)), "white")
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet_img)
    for i, (t, f) in enumerate(shots):
        x, y = (i % cols) * w, (i // cols) * (h + 30)
        sheet_img.paste(Image.open(f).resize((w, h)), (x, y + 30))
        d.text((x + 8, y + 8), f"{t:.1f}s", fill="black")
    out = qa / "sheet.jpg"
    sheet_img.save(out, quality=85)
    print(f"wrote {out} ({len(shots)} moments)")


def cmd_sheet(a):
    warn_config(proj(a.project))
    asyncio.run(sheet(proj(a.project)))


# ---------- render ----------
async def frames(p, out, fps, workers=4):
    """Screenshot every frame as lossless PNG; `workers` browsers each take an interleaved share of frames."""
    from playwright.async_api import async_playwright
    presenter = any(p.glob("presenter.*"))
    async with async_playwright() as pw:
        b0, pg0 = await open_page(pw, p / "short.html", presenter)
        dur = await pg0.evaluate("() => window.DUR")
        total = int(round(dur * fps))
        done = [0]

        async def worker(k, browser, page):
            for i in range(k, total, workers):
                await seek(page, i / fps)
                await page.screenshot(path=str(out / f"{i:05d}.png"), type="png")
                done[0] += 1
                if done[0] % 300 == 0:
                    print(f"frame {done[0]}/{total}", flush=True)
            await browser.close()

        others = [await open_page(pw, p / "short.html", presenter) for _ in range(workers - 1)]
        await asyncio.gather(*(worker(k, b, pg) for k, (b, pg) in enumerate([(b0, pg0)] + others)))
        return dur


async def frames_layered(p, out, fps, workers=4, start=None, end=None):
    """Draw the graphics twice per frame, transparent: 'back' (behind the presenter) and 'front' (in front)."""
    from playwright.async_api import async_playwright
    (out / "back").mkdir(exist_ok=True)
    (out / "front").mkdir(exist_ok=True)
    async with async_playwright() as pw:
        pages = [await open_page(pw, p / "short.html", False, alpha=True) for _ in range(workers)]
        dur = await pages[0][1].evaluate("() => window.DUR")
        moves = await pages[0][1].evaluate("() => (window.SCRIPT && window.SCRIPT.moves) || []")
        backdrops = await pages[0][1].evaluate("() => (window.SCRIPT && window.SCRIPT.backdrops) || []")
        layers = ("bd", "back", "front") if backdrops else ("back", "front")
        (out / "bd").mkdir(exist_ok=True)
        f0 = int(round((start or 0) * fps))
        f1 = min(int(round(dur * fps)), int(round((end if end is not None else dur) * fps)))
        done = [0]

        async def worker(k, browser, page):
            for i in range(f0 + k, f1, workers):
                await page.evaluate("async t => { TL.seek(t); await window.seekMedia(t); }", i / fps)
                for layer in layers:
                    await page.evaluate("l => { document.body.dataset.layer = l; }", layer)
                    await page.screenshot(path=str(out / layer / f"{i:05d}.png"), type="png", omit_background=True)
                done[0] += 1
                if done[0] % 150 == 0:
                    print(f"frame {done[0]}/{f1 - f0}", flush=True)
            await browser.close()

        await asyncio.gather(*(worker(k, b, pg) for k, (b, pg) in enumerate(pages)))
    return dur, f0, f1, moves, backdrops


def _ease(x):
    c = "clip(" + x + ",0,1)"
    return "(" + c + "*" + c + "*(3-2*" + c + "))"          # smoothstep


def composite(p, matte, out, silent, fps, f0, f1, crf, moves=(), backdrops=()):
    """presenter (graded) -> [blurred backdrop while shrunk] -> back graphics -> person (matte) -> front graphics.
    moves: 'anchor' = the cut-out person shrinks to a corner (graphics fill the space behind them);
           'punch'  = a quick camera zoom-in on the footage."""
    import numpy as np
    from PIL import Image
    presenter = next(p.glob("presenter.*"))
    ys = np.arange(1920, dtype=np.float32)
    top = 150 * (1 - np.clip(ys, 0, 900) / 900) ** 1.6
    bot = 170 * (np.clip(ys - 1150, 0, None) / 770) ** 1.4
    arr = np.zeros((1920, 1080, 4), np.uint8)
    arr[..., 3] = np.clip(top + bot, 0, 255).astype(np.uint8)[:, None]
    Image.fromarray(arr, "RGBA").save(out / "grad.png")
    start, D = f0 / fps, 0.45
    T = "(t+%.3f)" % start
    anchors = sorted([m for m in moves if m.get("mode") == "anchor"], key=lambda m: m["t"])
    punches = [m for m in moves if m.get("mode") == "punch"]

    def pulse(m):
        return "(" + _ease("((%s-%s)/%s)" % (T, m["t"], D)) + "-" + _ease("((%s-(%s-%s))/%s)" % (T, m["end"], D, D)) + ")"

    S = "(1" + "".join("+(%s-1)*%s" % (m.get("scale", 0.6), pulse(m)) for m in anchors) + ")"
    side = {"right": 1, "left": -1}
    DX = "(0" + "".join("+(%d*(540*(1-%s)-14))*%s" % (side.get(m.get("side", "right"), 0), m.get("scale", 0.6), pulse(m))
                        for m in anchors) + ")"
    Z = "(1" + "".join("+%s*(%s-%s)" % (m.get("amount", 0.12), _ease("((%s-%s)/0.18)" % (T, m["t"])),
                                         _ease("((%s-(%s+0.18))/0.75)" % (T, m["t"]))) for m in punches) + ")"
    zoom = ("scale=w='trunc(1080*%s/2)*2':h='trunc(1920*%s/2)*2':eval=frame,crop=1080:1920" % (Z, Z)) if punches else "null"
    pscale = ("scale=w='trunc(1080*%s/2)*2':h='trunc(1920*%s/2)*2':eval=frame" % (S, S)) if anchors else "null"
    ovp = ("overlay=x='(main_w-overlay_w)/2+%s':y='main_h-overlay_h':format=auto" % DX) if anchors else "overlay=format=auto"
    # backdrop intervals: union of the anchor moves (adjacent ones share one fade)
    spans = []
    def _has_bd(a_, b_):  # a generated backdrop already fills this stretch: no blurred room needed
        return any((x.get("t") or 0) <= a_ + 0.01 and (x.get("end") if x.get("end") is not None else 1e9) >= b_ - 0.01 for x in backdrops)
    for m in anchors:
        if spans and m["t"] <= spans[-1][1] - D + 0.01:
            spans[-1][1] = max(spans[-1][1], m["end"])
        else:
            spans.append([m["t"], m["end"]])
    spans = [sp for sp in spans if not _has_bd(sp[0], sp[1])]
    pad = "tpad=stop_mode=clone:stop_duration=60"  # footage shorter than the voiceover holds its last frame
    fc = ["[0:v]fps=%s,%s,eq=contrast=1.04:saturation=1.06,format=rgb24,split=%d[va][vb]%s" % (fps, pad, 3 if spans else 2, "[vc]" if spans else ""),
          "[1:v]fps=%s,%s,format=gray[mv]" % (fps, pad),
          "[vb][mv]alphamerge[pm]",
          "[va]%s[vz]" % zoom,
          "[pm]%s,%s[pz]" % (zoom, pscale),
          ("[vz][5:v]overlay=format=auto[vbd];[vbd][4:v]overlay=format=auto[g0]" if backdrops else "[vz][4:v]overlay=format=auto[g0]")]
    cur = "g0"
    if spans:
        n = len(spans)
        blur = "[vc]scale=270:480,gblur=sigma=8,scale=1080:1920,eq=brightness=-0.2:saturation=0.9,format=rgba"
        if n > 1:
            fc.append(blur + ",split=%d%s" % (n, "".join("[bl%d]" % i for i in range(n))))
        else:
            fc.append(blur + "[bl0]")
        for i, (a, b) in enumerate(spans):
            fc.append("[bl%d]fade=t=in:st=%.3f:d=%s:alpha=1,fade=t=out:st=%.3f:d=%s:alpha=1[bf%d]" % (i, a - start, D, b - D - start, D, i))
            fc.append("[%s][bf%d]overlay=format=auto[g%d]" % (cur, i, i + 1))
            cur = "g%d" % (i + 1)
    fc += ["[%s][2:v]overlay=format=auto[b1]" % cur,
           "[b1][pz]%s[b2]" % ovp,
           "[b2][3:v]overlay=format=auto,format=yuv420p[v]"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-ss", "%.3f" % start, "-i", str(presenter),
           "-ss", "%.3f" % start, "-i", str(matte),
           "-framerate", str(fps), "-start_number", str(f0), "-i", str(out / "back" / "%05d.png"),
           "-framerate", str(fps), "-start_number", str(f0), "-i", str(out / "front" / "%05d.png"),
           "-framerate", str(fps), "-loop", "1", "-i", str(out / "grad.png")]
    if backdrops:
        cmd += ["-framerate", str(fps), "-start_number", str(f0), "-i", str(out / "bd" / "%05d.png")]
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-frames:v", str(f1 - f0),
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-profile:v", "high", str(silent)]
    subprocess.run(cmd, check=True)


def cmd_render(a):
    p = proj(a.project)
    warn_config(p)
    out = ROOT / "frames" / f"short-{p.name}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    silent = out / "silent.mp4"
    matte = next(iter(sorted(p.glob("*matte*.mkv"))), None)
    if any(p.glob("presenter.*")) and matte:
        # presenter + cutout: graphics behind the person, the person, graphics in front
        dur, f0, f1, moves, backdrops = asyncio.run(frames_layered(p, out, a.fps, a.workers, a.start, a.end))
        composite(p, matte, out, silent, a.fps, f0, f1, a.crf, moves, backdrops)
        if a.start is not None or a.end is not None:
            test = p / "output" / f"{p.name}-test.mp4"
            test.parent.mkdir(exist_ok=True)
            shutil.copy(silent, test)
            print(f"wrote {test} (test cut, no audio)")
            return
    else:
        dur = asyncio.run(frames(p, out, a.fps, a.workers))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps), "-i", str(out / "%05d.png"),
                        "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                        "-profile:v", "high", "-x264-params", "aq-mode=3", str(silent)], check=True)
    mp4 = p / "output" / f"{p.name}-1080x1920.mp4"
    mp4.parent.mkdir(exist_ok=True)
    voice = p / "voice.mp3"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent)]
    if voice.exists():
        cmd += ["-i", str(voice)]
        if a.music:
            # music under the voice, ducked whenever the voice speaks, faded out at the end
            cmd += ["-stream_loop", "-1", "-i", a.music, "-filter_complex",
                    f"[2:a]volume={a.music_vol},afade=t=out:st={max(0, dur - 2):.2f}:d=2[m];"
                    "[m][1:a]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[md];"
                    "[1:a][md]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-map", "0:v", "-map", "1:a"]
        cmd += ["-c:a", "aac", "-b:a", "256k"]
    cmd += ["-c:v", "copy", "-t", f"{dur:.3f}", "-movflags", "+faststart", str(mp4)]
    subprocess.run(cmd, check=True)
    print(f"wrote {mp4}")


# ---------- capture ----------
async def capture(p, url, find, name, height, width):
    """Read-only: load a public page like a phone, find the text to highlight, screenshot just that area."""
    from playwright.async_api import async_playwright
    shots = p / "shots"
    shots.mkdir(exist_ok=True)
    k = 3  # device pixels per CSS pixel (device_scale_factor below)
    async with async_playwright() as pw:
        browser = None
        for ch in ("msedge", "chrome"):
            try:
                browser = await pw.chromium.launch(channel=ch)
                break
            except Exception:
                pass
        browser = browser or await pw.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": width, "height": 932}, device_scale_factor=k, locale="en-AU",
            user_agent="Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36 Edg/130.0")
        pg = await ctx.new_page()
        try:
            await pg.goto(url, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"load issue ({e.__class__.__name__}); capturing what loaded")
        await pg.wait_for_timeout(2000)
        for sel in ["button:has-text('Decline')", "button:has-text('Reject')", "button:has-text('Accept only essential')"]:
            try:
                await pg.locator(sel).first.click(timeout=800)  # close consent banners, never accept tracking
            except Exception:
                pass
        headings = await pg.evaluate(
            "() => [...document.querySelectorAll('h1,h2,h3')].map(h => h.innerText.trim()).filter(Boolean).slice(0, 12)")
        matches = []
        if find:
            matches = await pg.evaluate("""(t) => {
                t = t.toLowerCase(); const hits = [];
                for (const el of document.querySelectorAll('p,li,h1,h2,h3,h4,dd,dt,blockquote,td,a,span,div')) {
                    const txt = (el.innerText || '').trim();
                    if (!txt || !txt.toLowerCase().includes(t)) continue;
                    if ([...el.children].some(c => (c.innerText || '').toLowerCase().includes(t))) continue; // keep the deepest element
                    const r = el.getBoundingClientRect();
                    if (r.width < 2 || r.height < 2) continue;
                    hits.push({ text: txt.slice(0, 160), x: r.left, y: r.top + scrollY, w: r.width, h: r.height });
                }
                return hits.slice(0, 6);
            }""", find)
            if not matches:
                print(f"'{find}' was not found on the page; capturing the top instead (check the headings list)")
        page_h = await pg.evaluate("() => document.documentElement.scrollHeight")
        if matches:
            m = matches[0]
            top = max(0, m["y"] - 240)
            bottom = min(page_h, m["y"] + m["h"] + 700)
        else:
            top, bottom = 0, min(page_h, height)
        clip_h = bottom - top
        out = shots / f"{name}.png"
        await pg.screenshot(path=str(out), full_page=True, clip={"x": 0, "y": top, "width": width, "height": clip_h})
        await browser.close()

    marks = [{"y": round((m["y"] - top) * k), "h": round(m["h"] * k), "at": 1.2} for m in matches[:1]]
    start = max(0, marks[0]["y"] - 600) if marks else 0
    info = {
        "img": f"shots/{name}.png", "url": url, "srcWidth": width * k, "height_px": round(clip_h * k),
        "headings": headings, "matches": matches,
        "scene": {"type": "web", "img": f"shots/{name}.png", "url": url.split("//")[-1].rstrip("/"),
                  "srcWidth": width * k, "from": start, "to": start, "marks": marks},
    }
    (shots / f"{name}.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


def cmd_capture(a):
    p = proj(a.project)
    name = a.name or re.sub(r"[^a-z0-9]+", "-", a.url.split("//")[-1].lower()).strip("-")[:40]
    info = asyncio.run(capture(p, a.url, a.find, name, a.height, a.width))
    print(f"wrote {p / 'shots' / (name + '.png')} ({info['height_px'] // 3}px tall, CSS)")
    print("headings:", info["headings"][:6])
    for m in info["matches"][:3]:
        print("match:", m["text"][:110])
    print("scene (paste into script.js and set its time):")
    print(json.dumps(info["scene"], ensure_ascii=False))


# ---------- reference frames ----------
def cmd_frames(a):
    """Cut a reference video into one frame per --every seconds and draw a 1080x1920 coordinate grid on each,
    so caption, graphic and face positions can be read off in pixels and copied into script.js."""
    from PIL import Image, ImageDraw
    p = proj(a.project)
    src = pathlib.Path(a.video).resolve()
    out = p / "ref"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(src), "-vf",
                    f"fps=1/{a.every},scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
                    str(out / "f_%03d.jpg")], check=True)
    files = sorted(out.glob("f_*.jpg"))
    cols, w, h = 5, 216, 384
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + 22)), "white")
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB").resize((w, h))
        x, y = (i % cols) * w, (i // cols) * (h + 22)
        sheet.paste(im, (x, y + 22))
        for gy in range(0, 1920, 240):  # grid every 240 px (1/8 of the height)
            yy = y + 22 + int(gy * h / 1920)
            d.line([(x, yy), (x + w, yy)], fill=(255, 0, 0), width=1)
            d.text((x + 3, yy + 1), str(gy), fill=(255, 0, 0))
        for gx in range(0, 1080, 270):
            xx = x + int(gx * w / 1080)
            d.line([(xx, y + 22), (xx, y + 22 + h)], fill=(0, 160, 255), width=1)
        d.text((x + 3, y + 4), f"{i * a.every}s", fill="black")
    sheet_path = out / "grid-sheet.jpg"
    sheet.save(sheet_path, quality=88)
    print(f"{len(files)} frames in {out}")
    print(f"grid sheet: {sheet_path}  (red lines = y in px of 1920; blue = x in px of 1080)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("name"); n.add_argument("--voice"); n.add_argument("--presenter")
    n.add_argument("--noise", default="-35"); n.add_argument("--min-pause", type=float, default=0.35)
    s = sub.add_parser("segments"); s.add_argument("project")
    s.add_argument("--noise", default="-35", help="silence threshold in dB (default -35)")
    s.add_argument("--min-pause", type=float, default=0.35, help="shortest pause that splits lines, seconds")
    q = sub.add_parser("sheet"); q.add_argument("project")
    r = sub.add_parser("render"); r.add_argument("project"); r.add_argument("--fps", type=int, default=30)
    r.add_argument("--music"); r.add_argument("--music-vol", default="0.18")
    r.add_argument("--workers", type=int, default=4, help="parallel browsers (default 4)")
    r.add_argument("--from", dest="start", type=float, help="test render: start second (presenter + matte mode only)")
    r.add_argument("--to", dest="end", type=float, help="test render: end second")
    r.add_argument("--crf", type=int, default=14, help="x264 quality, lower = better (default 14, visually lossless)")
    c = sub.add_parser("capture"); c.add_argument("project"); c.add_argument("--url", required=True)
    c.add_argument("--find", help="exact text on the page to highlight (copy it from the page)")
    c.add_argument("--name", help="shot name (default: from the URL)")
    c.add_argument("--height", type=int, default=1100, help="CSS px to capture when --find is not given")
    c.add_argument("--width", type=int, default=430, help="phone width in CSS px")
    cf = sub.add_parser("config"); cf.add_argument("project")
    cf.add_argument("--interactive", action="store_true", help="ask the setup questions")
    cf.add_argument("--set", action="append", metavar="KEY=VALUE", help="set one answer (repeatable)")
    cf.add_argument("--redo", action="store_true", help="ask every question again, even answered ones")
    fr = sub.add_parser("frames"); fr.add_argument("project"); fr.add_argument("video")
    fr.add_argument("--every", type=float, default=1.0, help="seconds between reference frames (default 1)")
    a = ap.parse_args()
    {"new": cmd_new, "segments": cmd_segments, "sheet": cmd_sheet, "render": cmd_render,
     "capture": cmd_capture, "frames": cmd_frames, "config": cmd_config}[a.cmd](a)


main()
