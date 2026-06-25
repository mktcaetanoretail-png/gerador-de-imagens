"""
Carrega a página de stock com espera longa para hydration e extrai dados do React.
Também tenta capturar a chamada fetch/XHR que carrega os stocks completos.
"""
from playwright.sync_api import sync_playwright
import json, time

post_bodies = []

def on_response(response):
    url = response.url
    ct = response.headers.get("content-type", "")
    if response.status < 400 and ("json" in ct):
        try:
            body = response.body()
            if (b"exteriorColour" in body or b"lcdv16" in body) and len(body) > 2000:
                post_bodies.append({
                    "url": url,
                    "method": response.request.method,
                    "post": response.request.post_data,
                    "body": body,
                })
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("response", on_response)

    page.goto("https://store.peugeot.pt/stock?channel=b2c", wait_until="networkidle", timeout=40000)
    time.sleep(8)  # Esperar hydration completa

    # Extrair dados directamente do React/Next state
    all_offers = page.evaluate("""
    () => {
        // Tentar window.__NEXT_DATA__
        if (window.__NEXT_DATA__) {
            const pp = window.__NEXT_DATA__.props?.pageProps;
            if (pp?.stockModels?.offers) return {source: '__NEXT_DATA__', offers: pp.stockModels.offers, count: pp.stockModels.count};
        }
        // Tentar React root
        const el = document.getElementById('__NEXT_DATA__');
        if (el) {
            try {
                const data = JSON.parse(el.textContent);
                const pp = data.props?.pageProps;
                if (pp?.stockModels?.offers) return {source: 'DOM', offers: pp.stockModels.offers, count: pp.stockModels.count};
            } catch(e) {}
        }
        return null;
    }
    """)

    if all_offers:
        print(f"Source: {all_offers['source']}, count: {all_offers['count']}, loaded: {len(all_offers['offers'])}")
        for o in all_offers["offers"]:
            ext = o.get("exteriorColour") or {}
            print(f"  {o.get('nameplateBodyStyleSlug')} | {ext.get('title')} | {ext.get('id')} | lcdv16: {o.get('lcdv16')}")
    else:
        print("Sem dados de stock na página")

    # Tentar scroll extremo para ver se carrega mais
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(5)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(5)

    all_offers2 = page.evaluate("""
    () => {
        if (window.__NEXT_DATA__) {
            const pp = window.__NEXT_DATA__.props?.pageProps;
            if (pp?.stockModels?.offers) return pp.stockModels.offers.length;
        }
        return -1;
    }
    """)
    print(f"\nApós scroll - offers no __NEXT_DATA__: {all_offers2}")

    browser.close()

print(f"\nCapturou {len(post_bodies)} respostas JSON com cores")
for r in post_bodies:
    print(f"\n[{r['method']}] {r['url'][:120]}")
    if r["post"]:
        print("POST body:", str(r["post"])[:300])
    try:
        d = json.loads(r["body"])
        print("Keys:", list(d.keys())[:6] if isinstance(d, dict) else f"list[{len(d)}]")
    except Exception:
        print("Raw:", r["body"][:100])
