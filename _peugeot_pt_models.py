"""Explora peugeot.pt com Playwright para descobrir modelos e lcdv16."""
import json, time
from playwright.sync_api import sync_playwright

captured = []

def on_response(response):
    url = response.url
    if response.status == 200:
        ct = response.headers.get("content-type", "")
        if "json" in ct and not "gdpr" in url and not "google" in url:
            try:
                body = response.json()
                if body and (isinstance(body, list) or (isinstance(body, dict) and len(body) > 0)):
                    captured.append({"url": url, "body": body})
            except Exception:
                pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(
        viewport={"width": 1400, "height": 900},
        locale="pt-PT",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    )
    page = ctx.new_page()
    page.on("response", on_response)

    # Tentar a página principal peugeot.pt
    print("A carregar peugeot.pt...")
    page.goto("https://www.peugeot.pt", wait_until="networkidle", timeout=30000)
    time.sleep(3)
    title = page.title()
    print(f"Título: {title}")

    # Procurar links para modelos
    links = page.evaluate("""
    () => Array.from(document.querySelectorAll('a')).map(a => a.href).filter(h =>
        h.includes('peugeot.pt') && (h.includes('model') || h.includes('veiculo') || h.includes('gam') || h.includes('208') || h.includes('2008'))
    ).slice(0, 20)
    """)
    print(f"\nLinks encontrados: {links[:10]}")

    # Tentar __NEXT_DATA__ ou dados similares
    nd = page.evaluate("() => window.__NEXT_DATA__ || window.__PAGE_DATA__ || window.__MODEL_DATA__ || null")
    if nd:
        print(f"\n__NEXT_DATA__ encontrado: {len(json.dumps(nd))} chars")
        # Procurar lcdv16 ou slugs
        def find_keys(obj, target_keys, depth=0, path=""):
            if depth > 6: return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(t in k.lower() for t in target_keys) and isinstance(v, str) and len(v) > 3:
                        print(f"  {path}.{k} = {v}")
                    find_keys(v, target_keys, depth+1, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj[:3]):
                    find_keys(item, target_keys, depth+1, f"{path}[{i}]")
        find_keys(nd, ["lcdv", "slug", "model", "version", "nameplate"])

    browser.close()

print(f"\nRespostas JSON úteis: {len(captured)}")
for c in captured[:5]:
    print(f"\n  {c['url']}")
    body = c["body"]
    print(f"  {str(body)[:200]}")
