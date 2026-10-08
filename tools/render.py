"""Render an HTML/GSAP animation frame by frame, then encode it to MP4.
Usage (from the repo root):
  python tools/render.py projects/<project>/<page>.html            # -> projects/<project>/output/<page>-1080p.mp4
  python tools/render.py <page>.html --no-encode                    # frames only, in frames/<page>/
  FPS=60 python tools/render.py <page>.html
The page must expose `TL` (a paused-able GSAP timeline), `fit()` and a `#stage` element; the explainer template does.
Frames go to frames/<page-name>/ (git-ignored, cleared before each render so no stale frames are left behind).
"""
import argparse, asyncio, os, pathlib, shutil, subprocess
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
FPS = int(os.environ.get("FPS", 30))

def page_path(arg):
    p = pathlib.Path(arg)
    return (p if p.is_absolute() or p.exists() else ROOT / p).resolve()

async def frames(src, out):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(src.as_uri(), wait_until="load")
        # let fonts and images settle before driving the timeline; early calls can crash headless Chromium
        await page.wait_for_timeout(1500)
        # output size follows the stage: 1920x1080 for 16:9, 1080x1920 for portrait
        w, h = await page.evaluate("() => [stage.offsetWidth, stage.offsetHeight]")
        await page.set_viewport_size({"width": w, "height": h})
        await page.add_style_tag(content=(
            "body{padding:0!important;display:block!important}"
            f"#viewport{{width:{w}px!important;border-radius:0!important;box-shadow:none!important}}"
            "#controls{display:none!important}"))
        await page.evaluate("() => { fit(); TL.pause(); }")
        duration = await page.evaluate("() => TL.duration()")
        total = int(round(FPS * duration))
        for i in range(total):
            t = i / FPS
            # the braces matter: returning the timeline would make Playwright try to serialise it and hang
            await page.evaluate(
                "t => { TL.seek(t); document.getAnimations().forEach(a => { a.pause(); a.currentTime = t * 1000; }); }", t)
            await page.screenshot(path=str(out / f"{i:05d}.jpg"), type="jpeg", quality=93)
            if i % 150 == 0:
                print(f"frame {i}/{total}", flush=True)
        await browser.close()
        return w, h

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--no-encode", action="store_true")
    ap.add_argument("--out", help="MP4 path (default: <project>/output/<page>-1080p.mp4)")
    a = ap.parse_args()
    src = page_path(a.page)
    out = ROOT / "frames" / src.stem
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    w, h = asyncio.run(frames(src, out))
    if a.no_encode:
        print(f"frames in {out}")
        return
    mp4 = pathlib.Path(a.out) if a.out else src.parent / "output" / f"{src.stem}-{min(w, h)}p.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(out / "%05d.jpg"),
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)], check=True)
    print(f"wrote {mp4}")

main()
