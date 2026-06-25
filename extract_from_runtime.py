"""
Navega para a página stock da Peugeot store para capturar todos os modelos/cores disponíveis.
"""
from playwright.sync_api import sync_playwright
import json, time, re

color_offers = []

def on_response(response):
    url = response.url
    ct = response.headers.get("content-type", "")
    if response.status < 400 and "json" in ct:
        try:
            body = response.body()
            if b"exteriorColour" in body or b"lcdv16" in body:
                color_offers.append({"url": url, "data": body})
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("response", on_response)

    # Tentar página de stock
    for url in [
        "https://store.peugeot.pt/stock?channel=b2c",
        "https://store.peugeot.pt/search?channel=b2c",
        "https://store.peugeot.pt/stock",
    ]:
        try:
            resp = page.goto(url, wait_until="networkidle", timeout=20000)
            if resp and resp.status < 400:
                time.sleep(4)
                nd = page.evaluate("() => window.__NEXT_DATA__ || null")
                print(f"\nURL: {url} | status: {resp.status}")
                if nd:
                    pp = nd.get("props", {}).get("pageProps", {})
                    print("pageProps keys:", list(pp.keys())[:10])
                    sm = pp.get("stockModels", {})
                    if sm:
                        offers = sm.get("offers", [])
                        count = sm.get("count", 0)
                        print(f"stockModels: count={count}, loaded={len(offers)}")
                        for o in offers[:5]:
                            ext = o.get("exteriorColour") or {}
                            mod = o.get("model") or {}
                            slug = o.get("nameplateBodyStyleSlug", "")
                            print(f"  {slug} | {mod.get('title')} | {ext.get('title')} | id={ext.get('id')}")
                break
        except Exception as e:
            print(f"ERRO {url}: {e}")

    browser.close()

print(f"\nCapturou {len(color_offers)} respostas JSON com cor/lcdv16")
for c in color_offers:
    print("URL:", c["url"][:120])
    try:
        d = json.loads(c["data"])
        if isinstance(d, list):
            print(f"  list[{len(d)}]")
        elif isinstance(d, dict):
            print("  keys:", list(d.keys())[:6])
    except Exception:
        print("  raw:", c["data"][:100])
