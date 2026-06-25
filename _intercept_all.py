"""Interceta TODOS os pedidos de rede na página de stock para encontrar API de modelos."""
import json, time
from playwright.sync_api import sync_playwright

api_calls = []

def handle_response(response):
    url = response.url
    status = response.status
    ct = response.headers.get("content-type", "")
    if ("api" in url or "graphql" in url or "/data/" in url) and status == 200:
        try:
            if "json" in ct:
                body = response.json()
                api_calls.append({"url": url, "body": body})
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("response", handle_response)

    print("A carregar stock com filtro elétrico...")
    page.goto(
        "https://store.peugeot.pt/stock?channel=b2c",
        wait_until="networkidle",
        timeout=40000,
    )
    time.sleep(5)

    # Tentar clicar no filtro de combustível elétrico se existir
    try:
        elec_btn = page.locator("text=Elétrico").first
        if elec_btn.count() > 0:
            elec_btn.click()
            time.sleep(3)
            print("Filtro Elétrico clicado")
    except Exception as e:
        print(f"Sem filtro clicável: {e}")

    browser.close()

print(f"\nChamadas API interceptadas: {len(api_calls)}")
for call in api_calls:
    url = call["url"]
    body = call["body"]
    print(f"\n  URL: {url}")
    if isinstance(body, dict):
        if "data" in body:
            for k, v in body["data"].items():
                if isinstance(v, dict) and "offers" in v:
                    offers = v["offers"]
                    slugs = {o.get("nameplateBodyStyleSlug","") for o in offers}
                    print(f"    {k}: {len(offers)} offers — slugs: {sorted(slugs)}")
                else:
                    print(f"    {k}: {str(v)[:100]}")
        else:
            print(f"    {str(body)[:200]}")
