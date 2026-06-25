"""Intercepts Peugeot API calls to find color/config endpoints."""
from playwright.sync_api import sync_playwright
import json, time

api_calls = []

def handle_response(response):
    url = response.url
    ct = response.headers.get("content-type", "")
    if "json" in ct and response.status < 400:
        if any(x in url for x in ["peugeot", "visuel3d", "stellantis", "v3d"]):
            try:
                body = response.body()
                api_calls.append({"url": url, "data": body[:3000]})
            except Exception:
                api_calls.append({"url": url, "data": b"(err)"})

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.on("response", handle_response)
    page.goto(
        "https://store.peugeot.pt/configurable?channel=b2c",
        wait_until="networkidle",
        timeout=40000,
    )
    time.sleep(4)

    # Tentar clicar no primeiro card de modelo
    try:
        card = page.locator("article").first
        card.click(timeout=5000)
        time.sleep(5)
        print("Clicou no card")
    except Exception as e:
        print("Click erro:", e)

    # Ver URL actual
    print("URL actual:", page.url)
    browser.close()

print(f"\nTotal API calls JSON: {len(api_calls)}")
for c in api_calls:
    print("\nURL:", c["url"])
    try:
        parsed = json.loads(c["data"])
        print("KEYS:", list(parsed.keys())[:10] if isinstance(parsed, dict) else f"list len={len(parsed)}")
    except Exception:
        print("DATA (raw):", c["data"][:200])
