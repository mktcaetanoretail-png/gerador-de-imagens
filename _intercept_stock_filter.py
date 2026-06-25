"""
Interceta o pedido GraphQL real quando se filtra por 'Elétrico' na página de stock.
Captura o corpo exato do pedido POST para reproduzir.
"""
import json, time
from playwright.sync_api import sync_playwright

captured_requests = []
captured_responses = []

def handle_request(request):
    if "graphql" in request.url:
        try:
            body = request.post_data
            if body:
                captured_requests.append({
                    "url": request.url,
                    "body": json.loads(body),
                    "headers": dict(request.headers),
                })
        except Exception:
            pass

def handle_response(response):
    if "graphql" in response.url and response.status == 200:
        try:
            body = response.json()
            if body and "data" in body:
                captured_responses.append({"url": response.url, "body": body})
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)  # visible para debug
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("request", handle_request)
    page.on("response", handle_response)

    print("A carregar /stock...")
    page.goto("https://store.peugeot.pt/stock?channel=b2c", wait_until="networkidle", timeout=40000)
    time.sleep(3)

    # Scroll para mostrar filtros
    page.evaluate("window.scrollTo(0, 300)")
    time.sleep(1)

    # Tentar clicar no filtro elétrico
    try:
        # Procurar label/checkbox do filtro
        elec = page.locator("label").filter(has_text="Elétrico").first
        elec.scroll_into_view_if_needed()
        time.sleep(1)
        elec.click(force=True)
        time.sleep(4)
        print("Filtro Elétrico clicado")
    except Exception as e:
        print(f"Erro ao clicar: {e}")

    time.sleep(3)
    browser.close()

print(f"\nPedidos GraphQL capturados: {len(captured_requests)}")
for req in captured_requests:
    print(f"\n  POST {req['url']}")
    body = req["body"]
    print(f"  Query: {body.get('query', '')[:200]}")
    if "variables" in body:
        print(f"  Variables: {json.dumps(body['variables'])[:200]}")

print(f"\nRespostas GraphQL capturadas: {len(captured_responses)}")
for resp in captured_responses:
    data = resp["body"].get("data", {})
    for k, v in data.items():
        if isinstance(v, dict) and "offers" in v:
            offers = v["offers"]
            slugs = {}
            for o in offers:
                slug = o.get("nameplateBodyStyleSlug", "")
                model = (o.get("model") or {}).get("title", "")
                lcdv = o.get("lcdv16", "")
                if slug not in slugs:
                    slugs[slug] = {"model": model, "lcdvs": set()}
                slugs[slug]["lcdvs"].add(lcdv)
            print(f"\n  {k}: {len(offers)} offers")
            for slug, info in sorted(slugs.items()):
                print(f"    {slug}: {info['model']} — {list(info['lcdvs'])[:3]}")
