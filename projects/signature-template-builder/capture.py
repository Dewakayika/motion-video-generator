"""Capture the Template Builder (localhost:8000, light mode) for the explainer video.
Usage: python capture.py   (needs the portal running locally)
Writes shots/<state>.jpg (2x viewport) and shots/boxes.json (element boxes in CSS px).
Login: SIG_USER / SIG_PASS env vars, default to the seeded admin.
Nothing is saved: the demo edits stay in the page and the browser is closed without Save.
"""
import asyncio, json, os, pathlib, re
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "shots"
BASE = os.environ.get("SIG_BASE", "http://localhost:8000")
URL = f"{BASE}/signatures/modular/builder"
USER = os.environ.get("SIG_USER", "admin@gmail.com")
PASS = os.environ.get("SIG_PASS", "password")
HIDE = ".phpdebugbar,.phpdebugbar-openhandler{display:none!important}"

# boxes of visible buttons, inputs, selects, headings and labelled text, in viewport px
BOXES = r"""(texts) => {
  const box = e => { const r = e.getBoundingClientRect(); return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) }; };
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight; };
  const out = {};
  document.querySelectorAll('button,select,h1,h2,h3,label,th').forEach(e => {
    const t = (e.innerText || '').trim().split('\n')[0].slice(0, 40);
    if (t && vis(e) && !out[e.tagName.toLowerCase() + ':' + t]) out[e.tagName.toLowerCase() + ':' + t] = box(e);
  });
  document.querySelectorAll('input').forEach((e, i) => { if (vis(e) && e.type !== 'checkbox') out['input' + i + ':' + (e.value || e.placeholder || '').slice(0, 30)] = box(e); });
  for (const t of texts) {
    const el = [...document.querySelectorAll('body *')].find(e => vis(e) && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().startsWith(t)));
    out['text:' + t] = el ? box(el) : null;
  }
  return out;
}"""

TEXTS = ["SECTIONS", "Preview", "INSERT", "Unsaved changes", "Up to date", "Custom fields", "Fee schedule",
         "This section is also used", "Grand Total", "[Employer ABN]", "Start on a new page"]

async def shot(pg, name, boxes):
    await pg.mouse.move(1900, 1070)
    await pg.wait_for_timeout(500)
    await pg.screenshot(path=str(OUT / f"{name}.png"))
    boxes[name] = await pg.evaluate(BOXES, TEXTS)
    print(name, json.dumps({k: v for k, v in boxes[name].items() if k.startswith(("text:", "h", "label"))}))

async def preview_to(pg, text):
    """Scroll the A4 preview so the element whose text starts with `text` sits near its top."""
    return await pg.evaluate(r"""(t) => {
      const el = [...document.querySelectorAll('body *')].find(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().startsWith(t)) && e.getBoundingClientRect().left > 1300);
      if (!el) return false;
      let p = el.parentElement; while (p && !(p.scrollHeight > p.clientHeight + 10 && /(auto|scroll)/.test(getComputedStyle(p).overflowY))) p = p.parentElement;
      if (!p) return false;
      p.scrollTop += el.getBoundingClientRect().top - p.getBoundingClientRect().top - 40; return true;
    }""", text)

async def main():
    OUT.mkdir(exist_ok=True)
    boxes = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2, color_scheme="light")
        await ctx.add_cookies([{"name": "appearance", "value": "light", "url": BASE}])
        await ctx.add_init_script("try{localStorage.setItem('appearance','light')}catch(e){}")
        pg = await ctx.new_page()
        pg.on("dialog", lambda d: asyncio.ensure_future(d.dismiss()))
        await pg.goto(f"{BASE}/login")
        await pg.fill("input[type=email]", USER)
        await pg.fill("input[type=password]", PASS)
        await pg.click("button[type=submit]")
        await pg.wait_for_timeout(4000)
        await pg.goto(URL, wait_until="networkidle")
        await pg.add_style_tag(content=HIDE)
        await pg.wait_for_timeout(4000)

        # 1. default view
        await shot(pg, "overview", boxes)

        # 2. New template dialog (not created)
        await pg.get_by_role("button", name="New template").click()
        await pg.wait_for_timeout(800)
        await shot(pg, "new_template", boxes)
        await pg.get_by_role("button", name="Create").locator("xpath=following-sibling::button[1]").click()
        await pg.wait_for_timeout(500)

        # 3. From library
        await pg.get_by_role("button", name="From library").click()
        await pg.wait_for_timeout(800)
        await shot(pg, "library", boxes)
        await pg.get_by_role("button", name=re.compile(r"^Cancel$")).first.click()
        await pg.wait_for_timeout(400)

        # 4. hide a section -> Unsaved changes
        await pg.locator("input[type=checkbox]").nth(6).uncheck()
        await pg.wait_for_timeout(1500)
        await shot(pg, "unsaved", boxes)
        await pg.locator("input[type=checkbox]").nth(6).check()

        # 5. HTML mode on Client Details
        await pg.get_by_role("button", name="HTML").click()
        await pg.wait_for_timeout(600)
        await shot(pg, "html", boxes)
        await pg.get_by_role("button", name="Visual").click()

        # 6. custom fields
        await pg.get_by_role("button", name=re.compile(r"^Custom fields")).first.click()
        await pg.wait_for_timeout(600)
        await shot(pg, "fields_empty", boxes)
        await pg.get_by_role("button", name="Add field").click()
        await pg.wait_for_timeout(500)
        await shot(pg, "save_blocked", boxes)
        await pg.get_by_placeholder("e.g. Employer ABN").nth(0).fill("Employer ABN")
        req = pg.get_by_placeholder("e.g. Employer ABN").nth(0).locator("xpath=ancestor::tr[1]").locator("input[type=checkbox]")
        await req.first.check()
        await pg.get_by_role("button", name="Add field").click()
        await pg.get_by_placeholder("e.g. Employer ABN").nth(1).fill("Nominated Occupation")
        row = pg.get_by_placeholder("e.g. Employer ABN").nth(1).locator("xpath=ancestor::tr[1]")
        await row.locator("input[type=text]").last.fill("Software Engineer")
        await pg.get_by_role("button", name="Add field").click()
        await pg.get_by_placeholder("e.g. Employer ABN").nth(2).fill("Visa Stream")
        row = pg.get_by_placeholder("e.g. Employer ABN").nth(2).locator("xpath=ancestor::tr[1]")
        await row.locator("select").first.select_option(label="Dropdown")
        await pg.wait_for_timeout(300)
        opts = pg.get_by_placeholder("Dropdown options, separated by commas")
        if await opts.count():
            await opts.first.fill("Temporary Skill Shortage, Employer Nomination, Regional")
        await pg.wait_for_timeout(800)
        await shot(pg, "fields", boxes)

        # 7. fee schedule
        await pg.get_by_role("button", name=re.compile(r"^Fee schedule")).first.click()
        await pg.wait_for_timeout(600)
        await shot(pg, "fees_empty", boxes)
        fees = [("Professional fee", "Service Fee", "2000", "fixed", True),
                ("Government charge", "Visa Application Charge", "500", "per_adult", False),
                ("Government charge", "Child Charge", "100", "per_child", False)]
        for i, (kind, label, amount, unit, gst) in enumerate(fees):
            await pg.get_by_role("button", name=kind).click()
            await pg.wait_for_timeout(300)
            await pg.get_by_placeholder("e.g. Visa Application Charge").nth(i).fill(label)
            row = pg.get_by_placeholder("e.g. Visa Application Charge").nth(i).locator("xpath=ancestor::tr[1]")
            await row.locator("input[type=number]").fill(amount)
            await row.locator("select").last.select_option(unit)
            cbs = row.locator("input[type=checkbox]")
            if gst:
                await cbs.nth(0).check()
            else:
                await cbs.nth(0).uncheck()
        await pg.wait_for_timeout(800)
        await shot(pg, "fees", boxes)

        # 8. insert a custom field token at the end of Client Details
        await pg.locator("[draggable=true]").nth(0).click(position={"x": 120, "y": 14})
        await pg.wait_for_timeout(500)
        ed = pg.locator("[contenteditable=true]").first
        await ed.click()
        await pg.keyboard.press("Control+End")
        await pg.keyboard.press("Enter")
        await pg.keyboard.type("Employer ABN: ")
        await pg.get_by_role("button", name=re.compile(r"^Custom fields \(")).click()
        await pg.wait_for_timeout(400)
        await shot(pg, "insert_fields", boxes)
        await pg.get_by_role("button", name=re.compile(r"Employer ABN")).last.click()
        await pg.wait_for_timeout(2500)
        await preview_to(pg, "Employer ABN") or await preview_to(pg, "PRIMARY CLIENT DETAILS")
        await pg.wait_for_timeout(600)
        await shot(pg, "field_inserted", boxes)

        # 9. a new section with the fee tables
        await pg.get_by_role("button", name="New section").click()
        await pg.wait_for_timeout(300)
        await pg.get_by_placeholder("Section title").fill("Fee Summary")
        await shot(pg, "new_section", boxes)
        await pg.get_by_role("button", name=re.compile(r"^\+?\s*Add$")).click()
        await pg.wait_for_timeout(800)
        ed = pg.locator("[contenteditable=true]").first
        await ed.locator("p").last.click(click_count=3)
        await pg.keyboard.type("The fees below are calculated from the fee schedule.")
        await pg.keyboard.press("End")
        await pg.keyboard.press("Enter")
        await pg.get_by_role("button", name=re.compile(r"^Fees$")).click()
        await pg.wait_for_timeout(400)
        await shot(pg, "insert_fees", boxes)
        await pg.get_by_role("button", name="Full fee schedule").first.click()
        await pg.wait_for_timeout(300)
        await pg.get_by_role("button", name=re.compile(r"^\+?\s*Totals$")).first.click()
        await pg.wait_for_timeout(3500)
        await preview_to(pg, "Fee Summary")
        await pg.wait_for_timeout(600)
        await shot(pg, "fee_preview", boxes)
        await preview_to(pg, "The fees below")
        await pg.evaluate("""() => { const el=[...document.querySelectorAll('body *')].find(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim().startsWith('The fees below'))&&e.getBoundingClientRect().left>1300); let p=el.parentElement; while(p&&!(p.scrollHeight>p.clientHeight+10&&/(auto|scroll)/.test(getComputedStyle(p).overflowY)))p=p.parentElement; p.scrollTop+=420; }""")
        await pg.wait_for_timeout(600)
        await shot(pg, "fee_total", boxes)

        # 10. Insert: Tables & signatures, page options
        await pg.get_by_role("button", name="Tables & signatures").click()
        await pg.wait_for_timeout(400)
        await shot(pg, "insert_tables", boxes)
        await b.close()   # leaves without saving
    (OUT / "boxes.json").write_text(json.dumps(boxes, indent=1))
    from PIL import Image
    for png in OUT.glob("*.png"):
        Image.open(png).convert("RGB").save(png.with_suffix(".jpg"), quality=90)
        png.unlink()

asyncio.run(main())
