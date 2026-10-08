"""Quality check: grab frames at chosen times and tile them into contact sheets.
Usage (from the repo root):
  python tools/frames.py projects/<project>/<page>.html 3,11,19.5,24     # specific seconds
  python tools/frames.py projects/<project>/<page>.html --every 4        # one frame every 4 s
  python tools/frames.py projects/<project>/<page>.html --scenes         # the middle of every SCN scene
Writes frames/_qa/<page>/f_<time>.jpg and sheet_<n>.jpg (6 frames per sheet, 2 x 3, half size).
Also prints page errors and any file that failed to load (missing screenshot, wrong asset path).
"""
import argparse, asyncio, pathlib, shutil
from playwright.async_api import async_playwright
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent

async def grab(src, out, times, scenes):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        problems = []
        pg.on("pageerror", lambda e: problems.append(f"page error: {e}"))
        pg.on("requestfailed", lambda r: problems.append(f"failed to load: {r.url}"))
        pg.on("response", lambda r: problems.append(f"HTTP {r.status}: {r.url}") if r.status >= 400 else None)
        await pg.goto(src.as_uri(), wait_until="load")
        await pg.wait_for_timeout(2500)
        w, h = await pg.evaluate("() => [stage.offsetWidth, stage.offsetHeight]")
        await pg.set_viewport_size({"width": w, "height": h})
        await pg.add_style_tag(content=f"body{{padding:0!important;display:block!important}}#viewport{{width:{w}px!important;border-radius:0!important}}#controls{{display:none!important}}")
        await pg.evaluate("() => { fit(); TL.pause(); }")
        dur = await pg.evaluate("() => TL.duration()")
        if scenes:
            marks = await pg.evaluate("() => SCN.map(s => typeof rewarp === 'function' ? rewarp(s[0]) : s[0])")
            ends = marks[1:] + [dur]
            times = [round((a + b) / 2, 1) for a, b in zip(marks, ends)]
        shots = []
        for t in times:
            if t > dur:
                continue
            await pg.evaluate("t => { TL.seek(t); }", t)   # braces: never return the timeline
            f = out / f"f_{t:06.1f}.jpg"
            await pg.screenshot(path=str(f), type="jpeg", quality=75)
            shots.append(f)
        await b.close()
        return shots, problems, (w, h)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("times", nargs="?", help="comma-separated seconds")
    ap.add_argument("--every", type=float)
    ap.add_argument("--scenes", action="store_true")
    a = ap.parse_args()
    src = pathlib.Path(a.page)
    src = (src if src.exists() else ROOT / src).resolve()
    out = ROOT / "frames" / "_qa" / src.stem
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    times = [float(t) for t in a.times.split(",")] if a.times else []
    if a.every:
        times = [round(i * a.every, 1) for i in range(1, 1000)]
    shots, problems, (w, h) = asyncio.run(grab(src, out, times, a.scenes))
    tw, th = w // 2, h // 2
    for k in range(0, len(shots), 6):
        group = shots[k:k + 6]
        sheet = Image.new("RGB", (tw * 2, th * 3), "white")
        for i, f in enumerate(group):
            sheet.paste(Image.open(f).resize((tw, th)), ((i % 2) * tw, (i // 2) * th))
        sheet.save(out / f"sheet_{k // 6}.jpg", quality=80)
        print(f"sheet_{k // 6}.jpg: " + ", ".join(f.stem[2:] for f in group))
    print(f"{len(shots)} frames in {out}")
    for p in dict.fromkeys(problems):
        print("PROBLEM", p)

main()
