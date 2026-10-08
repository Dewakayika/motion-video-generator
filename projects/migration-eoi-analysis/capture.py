"""Capture the EOI Analysis page (localhost:3000) for the explainer video.
Usage: python capture.py   (needs the platform running locally)
Writes shots/<state>.jpg (2x, cropped) and shots/boxes.json (element boxes in CSS px).
Login: EOI_USER / EOI_PASS env vars, default to the local test account.
"""
import asyncio, json, os, pathlib, re
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "shots"
URL = "http://localhost:3000/dashboard/eoi-analysis"
USER = os.environ.get("EOI_USER", "admin@example.com")
PASS = os.environ.get("EOI_PASS", "12345678")

# Box of the nearest card-like ancestor of the element whose own text matches `text`.
BOXES = r"""(targets) => {
  const out = {};
  const all = [...document.querySelectorAll('body *')];
  for (const [key, text, up] of targets) {
    const el = all.find(e => !e.closest('aside,nav') && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().startsWith(text)));
    if (!el) { out[key] = null; continue; }
    let t = el;
    if (up === 'card') {
      while (t.parentElement && !/rounded-(lg|xl|2xl)/.test(t.className || '')) t = t.parentElement;
    } else {
      for (let i = 0; i < up && t.parentElement; i++) t = t.parentElement;
    }
    const r = t.getBoundingClientRect();
    out[key] = { x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height) };
  }
  out._page = { w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight };
  return out;
}"""

# heatmap rows and cell boxes, for placing highlights
ROWS = r"""() => {
  const t = document.querySelector('table'); if (!t) return 'no table';
  const box = e => { const r = e.getBoundingClientRect(); return [Math.round(r.left + scrollX), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; };
  return [...t.querySelectorAll('tr')].slice(0, 7).map(tr => box(tr).join(',') + ' | ' + [...tr.children].map(td => td.innerText.trim().replace(/\n/g, ' ') + '@' + box(td)[0] + 'w' + box(td)[2]).join(' ; ')).join('\n');
}"""

async def settle(pg, ms=12000):
    await pg.mouse.move(1900, 1070)
    try:
        await pg.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    await pg.wait_for_timeout(ms)

async def shot(pg, name, targets, boxes):
    await pg.mouse.move(1900, 1070)
    await pg.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    boxes[name] = await pg.evaluate(BOXES, targets)
    print(name, json.dumps(boxes[name]))

async def visa(pg, label):
    await pg.locator("button", has_text=re.compile(rf"^{re.escape(label)}$")).first.click()

async def main():
    OUT.mkdir(exist_ok=True)
    boxes = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        pg = await ctx.new_page()
        await pg.goto("http://localhost:3000/login?callbackUrl=%2Fdashboard%2Feoi-analysis")
        await pg.wait_for_selector("input[type=text]")
        await pg.fill("input[type=text]", USER)
        await pg.fill("input[type=password]", PASS)
        await pg.click("button[type=submit]")
        await pg.wait_for_url(lambda u: "/dashboard" in u, timeout=30000, wait_until="commit")
        await pg.wait_for_timeout(3000)
        await pg.goto(URL, wait_until="domcontentloaded")
        await settle(pg, 15000)

        summary = [
            ["title", "EOI Analysis", 1], ["month", "EOI Month", 1], ["state", "State / Territory", 1],
            ["visa", "Visa Subclass", 1],
            ["kpi_active", "Total Active EOIs", "card"], ["kpi_invited", "Total Estimated Invited", "card"],
            ["kpi_occ1", "SC 190 Occupations", "card"], ["kpi_occ2", "SC 491 Occupations", "card"],
            ["tabs", "Summary View", 1],
            ["total_chart", "Total Count EOIs in SkillSelect", "card"],
            ["points_chart", "Points Distribution", "card"],
            ["occ_table", "Top Occupations by Active EOIs", "card"],
        ]
        await shot(pg, "all", summary, boxes)

        # 190 + WA: filters flow through KPIs and charts
        await pg.select_option("select >> nth=1", "WA")
        await visa(pg, "190")
        await settle(pg)
        await shot(pg, "190_wa", summary + [["badge", "Most invited", 1]], boxes)

        # 189 + NSW: no state breakdown -> zeros
        await visa(pg, "189")
        await pg.select_option("select >> nth=1", "NSW")
        await settle(pg, 8000)
        await shot(pg, "189_nsw", summary, boxes)

        # back to All / All States for the tab views
        await pg.select_option("select >> nth=1", "")
        await visa(pg, "All")
        await settle(pg, 8000)
        await pg.get_by_role("button", name="Point Heatmap").click()
        await settle(pg, 8000)
        await shot(pg, "heatmap", summary[:9], boxes)
        await pg.get_by_role("button", name="State Matrix").click()
        await settle(pg, 8000)
        await shot(pg, "matrix", summary[:9], boxes)

        # Point Heatmap filters: 190 + VIC, Submitted then Invited
        await pg.get_by_role("button", name="Point Heatmap").click()
        await visa(pg, "190")
        await pg.select_option("select >> nth=1", "VIC")
        await settle(pg, 8000)
        await pg.select_option("select >> nth=2", "VIC")
        await settle(pg, 6000)
        heat = summary[:9] + [["heat_state", "State / Territory", "card"]]
        await shot(pg, "heat_vic_sub", heat, boxes)
        print(await pg.evaluate(ROWS))
        await pg.select_option("select >> nth=3", label="Invited")
        await settle(pg, 6000)
        await shot(pg, "heat_vic_inv", heat, boxes)
        print(await pg.evaluate(ROWS))
        await b.close()
    (OUT / "boxes.json").write_text(json.dumps(boxes, indent=1))
    # the video uses cropped JPGs (2x): crop height in CSS px per state
    from PIL import Image
    for name, h in [("all", 2400), ("190_wa", 1200), ("189_nsw", 1100), ("heatmap", 1400), ("matrix", 1400), ("heat_vic_sub", 1400), ("heat_vic_inv", 1100)]:
        png = OUT / f"{name}.png"
        im = Image.open(png).convert("RGB")
        im.crop((0, 0, im.width, min(h * 2, im.height))).save(OUT / f"{name}.jpg", quality=90)
        png.unlink()

asyncio.run(main())
