"""
Scrape configurator sem b2c para ver se tem mais modelos/cores.
Também intercepta todos os pedidos de rede para encontrar APIs de cor.
"""
from playwright.sync_api import sync_playwright
import json, time

api_urls = []
img_urls = []

def handle_response(response):
    url = response.url
    ct = response.headers.get("content-type", "")
    if "json" in ct and response.status < 400 and "peugeot" in url:
        try:
            body = response.body()
            if len(body) > 100:
                api_urls.append({"url": url, "data": body[:5000]})
        except Exception:
            pass
    if "V3DImage" in url:
        img_urls.append(url)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("response", handle_response)

    # Sem b2c
    page.goto(
        "https://store.peugeot.pt/configurable",
        wait_until="networkidle",
        timeout=40000,
    )
    time.sleep(4)
    nd = page.evaluate("() => window.__NEXT_DATA__ || null")
    browser.close()

print("=== __NEXT_DATA__ keys ===")
if nd:
    pp = nd.get("props", {}).get("pageProps", {})
    print("pageProps keys:", list(pp.keys()))
    mto = pp.get("mtoOffers", {})
    if isinstance(mto, dict):
        offers = mto.get("offers", [])
        print(f"mtoOffers.offers: {len(offers)} offers")
        for o in offers[:3]:
            ext = o.get("exteriorColour") or {}
            print(f"  externalId={o.get('externalId')}  color={ext.get('title')}  id_cor={ext.get('id','?')}")
    # Ver outros campos que podem ter cores
    for k, v in pp.items():
        if k not in ["mtoOffers"] and isinstance(v, (list, dict)):
            print(f"  {k}: {type(v).__name__} len={len(v)}")
            if isinstance(v, list) and v and isinstance(v[0], dict):
                print("    sample keys:", list(v[0].keys())[:8])

print(f"\n=== V3D Image URLs capturadas: {len(img_urls)} ===")
for u in img_urls[:10]:
    print(u[:200])

print(f"\n=== API JSON calls: {len(api_urls)} ===")
for c in api_urls:
    print("URL:", c["url"][:120])
