"""Captura TODAS as chamadas de rede (incluindo POST/GraphQL) ao carregar a página Peugeot."""
from playwright.sync_api import sync_playwright
import json, time

all_requests = []

def on_request(request):
    if request.post_data:
        all_requests.append({
            "type": "POST",
            "url": request.url,
            "data": request.post_data[:2000],
        })

def on_response(response):
    url = response.url
    ct = response.headers.get("content-type", "")
    if response.status < 400 and ("json" in ct or "graphql" in url.lower()):
        try:
            body = response.body()
            if len(body) > 200 and (b"colour" in body.lower() or b"color" in body.lower() or b"model" in body.lower()):
                all_requests.append({
                    "type": "GET",
                    "url": url,
                    "data": body[:5000].decode("utf-8", errors="replace"),
                })
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("request", on_request)
    page.on("response", on_response)
    page.goto(
        "https://store.peugeot.pt/configurable?channel=b2c",
        wait_until="networkidle",
        timeout=40000,
    )
    time.sleep(6)
    browser.close()

print(f"Total relevant calls: {len(all_requests)}")
for c in all_requests:
    print(f"\n[{c['type']}] {c['url'][:130]}")
    data = c["data"]
    try:
        parsed = json.loads(data)
        if isinstance(parsed, dict):
            keys = list(parsed.keys())
            print("  dict keys:", keys[:10])
            # Procurar arrays com muitos items
            for k, v in parsed.items():
                if isinstance(v, list) and len(v) > 5:
                    print(f"  {k}: list[{len(v)}]")
                    if v and isinstance(v[0], dict):
                        print("    sample:", list(v[0].keys())[:6])
    except Exception:
        print("  raw:", str(data)[:300])
