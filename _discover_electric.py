"""
Descobre modelos elétricos Peugeot PT navegando para páginas de modelo
e intercetando respostas da API.
"""
import json, time
from playwright.sync_api import sync_playwright
from collections import defaultdict

captured_offers = []

def handle_response(response):
    if "graphql" in response.url and response.status == 200:
        try:
            body = response.json()
            if body and "data" in body:
                for key, val in body["data"].items():
                    if isinstance(val, dict) and "offers" in val:
                        for o in val.get("offers", []):
                            captured_offers.append(o)
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("response", handle_response)

    # Tentar URLs de modelo específicas
    urls = [
        "https://store.peugeot.pt/configurable?channel=b2c&nameplateBodyStyleSlug=e-208-5-portas",
        "https://store.peugeot.pt/configurable?channel=b2c&nameplateBodyStyleSlug=e208-5-portas",
        "https://store.peugeot.pt/stock?channel=b2c&energy=Eletrico",
        "https://store.peugeot.pt/stock?channel=b2c&fuel=Electric",
    ]

    for url in urls:
        print(f"A carregar: {url}")
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            nd = page.evaluate("() => window.__NEXT_DATA__ || null")
            if nd:
                state = nd.get("props", {}).get("initialState", {})
                ol = state.get("OfferList", {})
                for section in ["stock", "configurable"]:
                    s_offers = ol.get(section, {}).get("offers", [])
                    if s_offers:
                        print(f"  {section}: {len(s_offers)} offers")
                        for o in s_offers:
                            slug = o.get("nameplateBodyStyleSlug", "")
                            model = (o.get("model") or {}).get("title", "")
                            lcdv = o.get("lcdv16", "")
                            print(f"    {slug}: {model} — lcdv16={lcdv}")
        except Exception as e:
            print(f"  ERRO: {e}")

    browser.close()

print(f"\nOffers GraphQL interceptadas: {len(captured_offers)}")
slugs = defaultdict(lambda: {"model": "", "lcdv": set(), "trims": set()})
for o in captured_offers:
    slug = o.get("nameplateBodyStyleSlug", "")
    if slug:
        slugs[slug]["model"] = (o.get("model") or {}).get("title", "")
        lcdv = o.get("lcdv16", "")
        trim = (o.get("trim") or {}).get("id", "")
        if lcdv: slugs[slug]["lcdv"].add(lcdv)
        if trim: slugs[slug]["trims"].add(trim)

for slug, info in sorted(slugs.items()):
    print(f"  {slug}: {info['model']}")
    print(f"    lcdv16: {sorted(info['lcdv'])[:3]}")
    print(f"    trims: {sorted(info['trims'])}")
