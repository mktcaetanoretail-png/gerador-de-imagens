"""Usa Playwright para capturar todos os modelos disponíveis na store Peugeot."""
import json, time
from playwright.sync_api import sync_playwright

captured = []

def handle_response(response):
    if "graphql" in response.url and response.status == 200:
        try:
            body = response.json()
            if body and "data" in body:
                captured.append(body)
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("response", handle_response)

    print("A carregar página de stock...")
    page.goto("https://store.peugeot.pt/stock?channel=b2c", wait_until="networkidle", timeout=40000)
    time.sleep(4)

    print("A carregar página configurável...")
    page.goto("https://store.peugeot.pt/configurable?channel=b2c", wait_until="networkidle", timeout=40000)
    time.sleep(4)

    # Tentar capturar __NEXT_DATA__
    nd = page.evaluate("() => window.__NEXT_DATA__ || null")
    if nd:
        with open("data/_next_data.json", "w", encoding="utf-8") as f:
            json.dump(nd, f, ensure_ascii=False, indent=2)
        print(f"__NEXT_DATA__ guardado ({len(json.dumps(nd))} chars)")

    browser.close()

# Analisar respostas GraphQL capturadas
print(f"\nRespostas GraphQL interceptadas: {len(captured)}")
all_slugs = {}
for resp in captured:
    data = resp.get("data", {})
    for key, val in data.items():
        if isinstance(val, dict) and "offers" in val:
            offers = val["offers"]
            print(f"  {key}: {len(offers)} offers")
            for o in offers:
                slug = o.get("nameplateBodyStyleSlug", "")
                model = (o.get("model") or {}).get("title", "")
                if slug:
                    all_slugs[slug] = model

print(f"\nSlugos únicos capturados: {len(all_slugs)}")
for slug, model in sorted(all_slugs.items()):
    print(f"  {slug}: {model}")
