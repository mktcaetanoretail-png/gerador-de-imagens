"""Captura chamadas API para encontrar o endpoint de stockModels com todas as cores."""
from playwright.sync_api import sync_playwright
import json, time

calls = []

def handle_response(response):
    url = response.url
    ct = response.headers.get("content-type", "")
    if response.status < 400 and "json" in ct:
        try:
            body = response.body()
            if b"exteriorColour" in body or b"colour" in body.lower() or b"offers" in body:
                calls.append({"url": url, "body": body[:8000]})
        except Exception:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()
    page.on("response", handle_response)
    page.goto(
        "https://store.peugeot.pt/configurable?channel=b2c",
        wait_until="networkidle",
        timeout=40000,
    )
    time.sleep(5)
    # Scroll para forcar carregamento lazy
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(3)
    browser.close()

print(f"Calls com 'colour/offers': {len(calls)}")
for c in calls:
    print("\nURL:", c["url"][:150])
    try:
        data = json.loads(c["body"])
        if isinstance(data, dict):
            print("  keys:", list(data.keys())[:8])
        elif isinstance(data, list):
            print("  list len:", len(data))
            if data:
                print("  sample keys:", list(data[0].keys())[:8] if isinstance(data[0], dict) else data[0])
    except Exception:
        print("  raw:", c["body"][:300])
