"""Carrega o configurador de um modelo Peugeot e extrai cores/versões."""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "peugeot_next_data.json", encoding="utf-8") as f:
    d = json.load(f)

state = d["configurable"]["props"]["initialState"]
offers = state["OfferList"]["configurable"]["offers"]
slug = offers[0]["_properties"]["object"]["nameplateBodyStyleSlug"]
url = f"https://store.peugeot.pt/configurator/{slug}?channel=b2c"
print(f"A carregar: {url}")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.goto(url, wait_until="networkidle", timeout=30000)
    time.sleep(3)
    nd = page.evaluate("() => window.__NEXT_DATA__ || null")
    browser.close()

if not nd:
    print("SEM __NEXT_DATA__"); exit()

out = DATA_DIR / "peugeot_model_data.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(nd, f, ensure_ascii=False, indent=2)
print(f"Guardado: {out}")

cfg = nd.get("props", {}).get("initialState", {}).get("Configurator", {})
ext = cfg.get("exteriorColors", [])
int_ = cfg.get("interiorColors", [])
mots = cfg.get("motorizations", [])
print(f"\nexteriorColors: {len(ext)}")
print(f"interiorColors: {len(int_)}")
print(f"motorizations: {len(mots)}")

if ext:
    print("\n=== Primeira cor exterior ===")
    c = ext[0]
    for k, v in c.items():
        if k not in ("prices", "pricesV2", "specs"):
            print(f"  {k}: {str(v)[:120]}")

if mots:
    print("\n=== Primeira motorização ===")
    m = mots[0]
    for k, v in m.items():
        if k not in ("prices", "pricesV2", "specs"):
            print(f"  {k}: {str(v)[:120]}")

# Também ver TrimSelector
ts = nd.get("props", {}).get("initialState", {}).get("TrimSelector", {})
tc = ts.get("configurable", {})
print(f"\n=== TrimSelector.configurable ===")
for k, v in tc.items():
    t = type(v).__name__
    extra = f" ({len(v)} items)" if isinstance(v, (list, dict)) else f" = {str(v)[:100]}"
    print(f"  {k}: {t}{extra}")
    if isinstance(v, list) and v:
        item = v[0]
        if isinstance(item, dict):
            for k2, v2 in list(item.items())[:10]:
                print(f"    {k2}: {str(v2)[:100]}")
