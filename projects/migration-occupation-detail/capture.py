"""Capture the Occupation Detail page (localhost:3000) for the explainer video.
Usage: python capture.py   (needs the platform running locally)
Writes shots/<state>.jpg (2x, cropped) and shots/boxes.json (element boxes in CSS px).
Login: EOI_USER / EOI_PASS env vars, default to the local test account.
Occupation: OCC_ANZSCO env var, default 261313 Software Engineer.
"""
import asyncio, json, os, pathlib, re
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "shots"
ANZSCO = os.environ.get("OCC_ANZSCO", "261313")
URL = f"http://localhost:3000/dashboard/occupation/{ANZSCO}"
USER = os.environ.get("EOI_USER", "admin@example.com")
PASS = os.environ.get("EOI_PASS", "12345678")

# Box of the element whose own text starts with `text`, moved `up` parents
# (or to the nearest rounded card when up == 'card').
BOXES = r"""(targets) => {
  const out = {};
  const all = [...document.querySelectorAll('body *')];
  for (const [key, text, up] of targets) {
    const el = all.find(e => !e.closest('aside') && e.offsetParent !== null && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().startsWith(text)));
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

TOP = [
    ["back", "Back to Search", 0], ["title", "Software Engineer", 0],
    ["kpi_caption", "SkillSelect figures for", 0],
    ["k_states", "Inviting States", "card"], ["k_pool", "EOI Pool Size", "card"], ["k_inv", "Est. Invitations", "card"],
    ["k_ads", "Live Job Ads", "card"], ["k_growth", "2030 Growth", "card"],
    ["k_single", "Inviting", "card"],
    ["invite_rate", "Invite Rate", 2],
    ["streams_title", "Visa & State Streams", 0],
    ["analytics_title", "Detailed Analytics", 0],
    ["sources", "Official Data Sources", 1],
]
EOI_TAB = [
    ["total_chart", "Total Count EOIs in SkillSelect", "card"],
    ["points_chart", "Points Distribution", "card"],
    ["badge", "Most invited", 0],
]
DEMAND = [
    ["guide", "National Labour Demand", 2],
    ["spl", "JSA Skills Priority List Assessment", 2], ["osl", "DEWR Occupation Shortage List", 2],
    ["ivi_kpis", "Active Job Ads", 2], ["ivi_trend", "Online Job Vacancies Trend", 3],
]
WORKFORCE = [
    ["emp_trend", "National Employment Trend", 3], ["recruit", "Employer Recruitment Insights", 2],
    ["edu", "Educational Background of Workers", 2], ["age", "Age Group Distribution", 2],
    ["proj", "JSA Employment Projections to 2030", 2],
]
REGIONAL = [
    ["nero", "Regional vs Major City Employment", 2], ["nero_trend", "Regional vs Major Cities Trend", 3],
    ["sa4", "Top Hiring SA4 Regions", 2], ["ai", "AI Shortage Risk Forecast", 2],
]

# visible elements with these texts (buttons, card headings), for highlights
CONTROLS = r"""() => {
  const box = e => { const r = e.getBoundingClientRect(); return { x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height) }; };
  const out = {};
  document.querySelectorAll('select').forEach((s, i) => { if (!s.closest('aside') && s.offsetParent) out['select' + i] = box(s); });
  document.querySelectorAll('button').forEach(b => { const t = (b.innerText || '').trim(); if (t && !b.closest('aside') && b.offsetParent && t.length < 40) out['btn:' + t] = box(b); });
  document.querySelectorAll('h4').forEach(h => { const c = h.closest('[class*="rounded-2xl"],[class*="rounded-xl"]'); if (c) out['card:' + h.innerText.trim()] = box(c); });
  document.querySelectorAll('table').forEach((t, i) => { if (t.offsetParent) out['table' + i] = box(t); });
  return out;
}"""

async def settle(pg, ms=10000):
    await pg.mouse.move(1900, 1070)
    try:
        await pg.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    await pg.wait_for_timeout(ms)

async def shot(pg, name, targets, boxes, full=True):
    if full:
        await pg.evaluate("window.scrollTo(0, 0)")
        await pg.wait_for_timeout(800)
        await pg.mouse.move(1900, 1070)
    await pg.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    b = await pg.evaluate(BOXES, targets)
    b.update(await pg.evaluate(CONTROLS))
    boxes[name] = b
    print(name, json.dumps({k: v for k, v in b.items() if not k.startswith(("btn:", "select"))}))

async def visa(pg, label):
    await pg.locator("button", has_text=re.compile(rf"^{re.escape(label)}$")).first.click()

async def tab(pg, label):
    await pg.get_by_role("button", name=label).click()

async def main():
    OUT.mkdir(exist_ok=True)
    boxes = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        pg = await ctx.new_page()
        await pg.goto("http://localhost:3000/login?callbackUrl=%2Fdashboard")
        await pg.wait_for_selector("input[type=text]")
        await pg.fill("input[type=text]", USER)
        await pg.fill("input[type=password]", PASS)
        await pg.click("button[type=submit]")
        await pg.wait_for_url(lambda u: "/dashboard" in u, timeout=30000, wait_until="commit")
        await pg.wait_for_timeout(3000)
        await pg.goto(URL, wait_until="domcontentloaded")
        await settle(pg, 15000)

        # default: Last 12 months, Subclass 190, All States, EOI & Invitations tab
        await shot(pg, "top", TOP + EOI_TAB, boxes)

        # status tooltip on the NSW (Quiet) card: hover its (i)
        nsw = pg.locator("h4", has_text="New South Wales").locator("xpath=ancestor::*[contains(@class,'rounded-2xl')][1]")
        await nsw.hover()
        await nsw.locator("button").first.hover()
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=str(OUT / "quiet_tip.png"), full_page=False)
        boxes["quiet_tip"] = await pg.evaluate(CONTROLS)

        # sticky compact bar after scrolling
        await pg.evaluate("window.scrollTo(0, 900)")
        await pg.wait_for_timeout(1500)
        await pg.mouse.move(1900, 1070)
        await pg.screenshot(path=str(OUT / "sticky.png"), full_page=False)
        boxes["sticky"] = await pg.evaluate(CONTROLS)

        # table view
        await pg.evaluate("window.scrollTo(0, 0)")
        await pg.get_by_role("button", name="Table").click()
        await settle(pg, 2500)
        await shot(pg, "table", TOP, boxes)
        await pg.get_by_role("button", name="Cards").click()

        # one month + one state: June 2026, South Australia
        await pg.select_option("select >> nth=0", "month:06/2026")
        await settle(pg, 6000)
        await pg.select_option("select >> nth=1", "SA")
        await settle(pg, 6000)
        await shot(pg, "sa_june", TOP + EOI_TAB, boxes)

        # one month, all states: June 2026 (Invited / No invitations)
        await pg.select_option("select >> nth=1", "all")
        await settle(pg, 6000)
        await shot(pg, "june", TOP, boxes)

        # national visa: 189, last 12 months
        await pg.select_option("select >> nth=0", "last12")
        await visa(pg, "189")
        await settle(pg, 8000)
        await shot(pg, "national", TOP + EOI_TAB, boxes)

        # back to the default for the analytics tabs
        await visa(pg, "190")
        await settle(pg, 6000)
        for name, label, targets in [("demand", "Demand & Vacancies", DEMAND),
                                     ("workforce", "Workforce & Demographics", WORKFORCE),
                                     ("regional", "Regional & AI Forecasts", REGIONAL)]:
            await tab(pg, label)
            await settle(pg, 6000)
            await shot(pg, name, TOP + targets, boxes)
        await b.close()
    (OUT / "boxes.json").write_text(json.dumps(boxes, indent=1))
    # the video uses JPGs (2x); crop height in CSS px per state (None = full page)
    from PIL import Image
    for name, h in [("top", None), ("quiet_tip", None), ("sticky", None), ("table", 1150), ("sa_june", None),
                    ("june", 1150), ("national", None), ("demand", None), ("workforce", None), ("regional", None)]:
        png = OUT / f"{name}.png"
        im = Image.open(png).convert("RGB")
        if h:
            im = im.crop((0, 0, im.width, min(h * 2, im.height)))
        im.save(OUT / f"{name}.jpg", quality=88)
        png.unlink()

asyncio.run(main())
