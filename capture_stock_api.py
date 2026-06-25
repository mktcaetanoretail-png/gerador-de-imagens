"""
Carrega a página de stock Peugeot e captura os pedidos de rede que trazem mais ofertas.
Intercepts XHR/fetch após o carregamento inicial.
"""
from playwright.sync_api import sync_playwright, Route
import json, time

all_responses = []

def on_response(response):
    url = response.url
    ct = response.headers.get("content-type", "")
    status = response.status
    if status < 400 and ("json" in ct or "graphql" in url.lower()):
        try:
            body = response.body()
            if len(body) > 500:
                all_responses.append({
                    "url": url,
                    "ct": ct,
                    "body": body,
                    "method": response.request.method,
                    "post": response.request.post_data or "",
                })
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("response", on_response)

    page.goto("https://store.peugeot.pt/stock?channel=b2c", wait_until="networkidle", timeout=40000)
    time.sleep(3)

    # Scroll para forcar carregamento
    for _ in range(5):
        page.evaluate("window.scrollBy(0, 800)")
        time.sleep(1)

    # Tentar clicar em "load more" ou paginar
    try:
        load_more = page.locator("button:has-text('Ver mais'), button:has-text('Carregar'), [data-testid*='load']").first
        load_more.click(timeout=3000)
        time.sleep(3)
    except Exception:
        pass

    time.sleep(3)
    browser.close()

print(f"Total responses capturadas: {len(all_responses)}")
for c in all_responses:
    body_str = c["body"].decode("utf-8", errors="replace")
    has_colour = "colour" in body_str.lower() or "color" in body_str.lower() or "lcdv" in body_str.lower()
    print(f"\n[{c['method']}] {c['url'][:120]}")
    print(f"  CT: {c['ct'][:40]} | {len(c['body'])}B | colour_data: {has_colour}")
    if has_colour and len(c["body"]) > 1000:
        try:
            d = json.loads(body_str)
            if isinstance(d, dict):
                print("  keys:", list(d.keys())[:10])
                # Procurar listas com ofertas
                for k, v in d.items():
                    if isinstance(v, list) and len(v) > 3:
                        print(f"  {k}: list[{len(v)}]")
                        if v and isinstance(v[0], dict) and "exteriorColour" in v[0]:
                            print("  >>> TEM exteriorColour!")
                            for o in v[:5]:
                                ext = (o.get("exteriorColour") or {})
                                slug = o.get("nameplateBodyStyleSlug", "")
                                print(f"    {slug}: {ext.get('title')} ({ext.get('id')})")
        except Exception:
            pass
    if c["post"]:
        print("  POST body:", c["post"][:300])
