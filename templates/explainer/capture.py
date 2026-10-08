"""Capture the app page for the explainer video.
Usage: python capture.py   (the app must be running locally)
Writes shots/<state>.jpg (2x) and shots/boxes.json (element boxes in CSS px).

Rules (see .claude/skills/explainer-video/SKILL.md):
- Real screenshots only. Never save, submit or delete anything in the app: demo edits stay in the page and the
  browser closes without saving. If a state needs saved data, stop and ask the owner.
- Credentials come from environment variables; the defaults are local seeded test accounts only.
- Use one viewport (1920x1080) and device_scale_factor=2 for every shot, so boxes stay in the same px space.
"""
import asyncio, json, os, pathlib, re
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "shots"
BASE = os.environ.get("APP_BASE", "http://localhost:3000")       # TODO: app URL
URL = f"{BASE}/path/to/page"                                      # TODO: page to explain
USER = os.environ.get("APP_USER", "admin@example.com")            # TODO: local test account
PASS = os.environ.get("APP_PASS", "password")
LIGHT = True                                                      # light or dark app theme
HIDE = ".phpdebugbar,#__next-build-watcher,nextjs-portal{display:none!important}"  # dev overlays to hide

# Boxes of visible buttons, selects, inputs, headings, labels and table headers, plus elements whose own text
# starts with one of `texts`. Page px (scroll included), so they match a full-page capture.
BOXES = r"""(texts) => {
  const box = e => { const r = e.getBoundingClientRect(); return { x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height) }; };
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const out = {};
  document.querySelectorAll('button,select,h1,h2,h3,h4,label,th,[role=tab]').forEach(e => {
    if (e.closest('aside,nav') || !vis(e)) return;
    const t = (e.innerText || '').trim().split('\n')[0].slice(0, 40);
    const k = e.tagName.toLowerCase() + ':' + t;
    if (t && !out[k]) out[k] = box(e);
  });
  document.querySelectorAll('input,textarea').forEach((e, i) => { if (vis(e) && e.type !== 'checkbox') out['input' + i + ':' + (e.value || e.placeholder || '').slice(0, 30)] = box(e); });
  for (const t of texts) {
    const el = [...document.querySelectorAll('body *')].find(e => vis(e) && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().startsWith(t)));
    out['text:' + t] = el ? box(el) : null;
  }
  out._page = { w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight, scrollY };
  return out;
}"""

TEXTS = ["TODO: card title", "TODO: KPI label"]   # texts you want boxes for

async def settle(pg, ms=4000):
    await pg.mouse.move(1900, 1070)            # move the pointer away so no hover state is captured
    try:
        await pg.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    await pg.wait_for_timeout(ms)

async def shot(pg, name, boxes, full=False):
    """full=True: whole page from the top (camera can pan down). False: the viewport as it is (overlays, tooltips)."""
    if full:
        await pg.evaluate("window.scrollTo(0, 0)")
    await pg.mouse.move(1900, 1070)
    await pg.wait_for_timeout(500)
    await pg.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    boxes[name] = await pg.evaluate(BOXES, TEXTS)
    print(name, json.dumps({k: v for k, v in boxes[name].items() if k.startswith(("text:", "h1", "h2", "_page"))}))

async def main():
    OUT.mkdir(exist_ok=True)
    boxes = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2,
                                  color_scheme="light" if LIGHT else "dark")
        # many apps keep their theme in localStorage or a cookie; set both before any page loads
        theme = "light" if LIGHT else "dark"
        await ctx.add_cookies([{"name": "appearance", "value": theme, "url": BASE}])
        await ctx.add_init_script(f"try{{localStorage.setItem('appearance','{theme}');localStorage.setItem('theme','{theme}')}}catch(e){{}}")
        pg = await ctx.new_page()
        pg.on("dialog", lambda d: asyncio.ensure_future(d.dismiss()))   # never accept "leave / delete?" prompts

        # log in (TODO: adjust selectors)
        await pg.goto(f"{BASE}/login")
        await pg.fill("input[type=email], input[type=text]", USER)
        await pg.fill("input[type=password]", PASS)
        await pg.click("button[type=submit]")
        await pg.wait_for_url(lambda u: "/login" not in u, timeout=30000, wait_until="commit")
        await pg.goto(URL, wait_until="domcontentloaded")
        await pg.add_style_tag(content=HIDE)
        await settle(pg, 8000)

        # 1. default view
        await shot(pg, "overview", boxes, full=True)

        # 2. TODO: one block per state the video needs, e.g. a filter change:
        # await pg.select_option("select >> nth=0", "value")
        # await settle(pg)
        # await shot(pg, "filtered", boxes, full=True)
        #
        # a tooltip or an open dialog: hover/click, then a viewport shot (full=False)
        # await pg.get_by_role("button", name="Info").hover()
        # await shot(pg, "tooltip", boxes)

        await b.close()   # closes without saving anything
    (OUT / "boxes.json").write_text(json.dumps(boxes, indent=1))
    # the video uses JPGs; optional crop height in CSS px per state (None = keep all)
    from PIL import Image
    crops = {}   # e.g. {"overview": 2400}
    for png in OUT.glob("*.png"):
        im = Image.open(png).convert("RGB")
        h = crops.get(png.stem)
        if h:
            im = im.crop((0, 0, im.width, min(h * 2, im.height)))
        im.save(png.with_suffix(".jpg"), quality=88)
        png.unlink()

asyncio.run(main())
