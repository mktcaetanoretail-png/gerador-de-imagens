"""Captura __NEXT_DATA__ da página de stock Peugeot para ver todos os modelos."""
import json, time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()

    print("A carregar /stock...")
    page.goto("https://store.peugeot.pt/stock?channel=b2c", wait_until="networkidle", timeout=40000)
    time.sleep(5)

    nd = page.evaluate("() => window.__NEXT_DATA__ || null")
    browser.close()

if not nd:
    print("Sem __NEXT_DATA__")
    exit()

with open("data/_next_data_stock.json", "w", encoding="utf-8") as f:
    json.dump(nd, f, ensure_ascii=False, indent=2)
print(f"Guardado: {len(json.dumps(nd))} chars")

# Analisar
state = nd.get("props", {}).get("initialState", {})
offer_list = state.get("OfferList", {})
stock = offer_list.get("stock", {})
offers = stock.get("offers", [])
print(f"\nStock offers: {len(offers)}")
print(f"Total count: {stock.get('totalVehiclesCount', '?')}")

# Agrupar por slug
slugs = {}
for o in offers:
    slug = o.get("nameplateBodyStyleSlug", "")
    model = (o.get("model") or {}).get("title", "")
    ext = (o.get("exteriorColour") or {}).get("title", "")
    exid = o.get("externalId", "")
    lcdv = o.get("lcdv16", "")
    trim = (o.get("trim") or {}).get("id", "")
    if slug not in slugs:
        slugs[slug] = {"model": model, "count": 0, "colors": set(), "trims": set(), "sample_lcdv": lcdv}
    slugs[slug]["count"] += 1
    if ext: slugs[slug]["colors"].add(ext)
    if trim: slugs[slug]["trims"].add(trim.strip("_"))

for slug, info in sorted(slugs.items()):
    print(f"  {slug}: {info['model']} — {info['count']} offers — trims: {sorted(info['trims'])} — cores: {sorted(info['colors'])}")
    print(f"    sample lcdv16: {info['sample_lcdv']}")

# Ver filters de modelos
filters = state.get("Filters", {})
print("\n=== Filter categories ===")
for cat in filters.get("filterCategories", []):
    cat_filters = cat.get("filters", [])
    print(f"  {cat.get('name')}: {[f.get('displayName') for f in cat_filters]}")
