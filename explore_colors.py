"""
Testa endpoints da API VW para cores e jantes,
e usa Playwright com aceitação de cookies para navegar à configuração do Golf.
"""
import json
import os
import ssl
import time
import urllib.request
from playwright.sync_api import sync_playwright

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, */*",
    "Referer": "https://configurador.volkswagen.pt/",
}

BASE = "https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22"
GOLF_CODE = "DA12BXA4"
GOLF_GROUP = "D03"


def try_endpoints():
    """Testa múltiplos padrões de endpoint para encontrar cores e jantes."""
    print("=== Teste directo de endpoints ===")
    patterns = [
        f"{BASE}/wccarcolors/V/{GOLF_CODE}",
        f"{BASE}/wccarcolors/{GOLF_CODE}",
        f"{BASE}/wccaroptions/V/{GOLF_CODE}",
        f"{BASE}/wccaroptions/{GOLF_CODE}",
        f"{BASE}/wccarsummary/V/{GOLF_CODE}",
        f"{BASE}/wccarsummary/{GOLF_CODE}",
        f"{BASE}/wccardetails/V/{GOLF_CODE}",
        f"{BASE}/wccardetails/{GOLF_CODE}",
        f"{BASE}/wccarconfiguration/V/{GOLF_CODE}",
        f"{BASE}/wccarconfiguration/{GOLF_CODE}",
        f"{BASE}/api/v1/models/{GOLF_CODE}/colors",
        f"{BASE}/api/v1/models/{GOLF_CODE}/options",
        f"{BASE}/api/v2/models/{GOLF_CODE}",
        f"{BASE}/api/v1/configuration/{GOLF_CODE}",
        f"{BASE}/api/v1/configuration/V/{GOLF_CODE}",
        f"{BASE}/wccarcodes/{GOLF_CODE}",
        f"{BASE}/wccarcodes/V/{GOLF_CODE}",
        f"{BASE}/wccarequipment/{GOLF_CODE}",
        f"{BASE}/wccarequipment/V/{GOLF_CODE}",
        f"https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22/all-messages",
    ]
    for url in patterns:
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                data = json.loads(r.read())
                print(f"  OK 200: {url.split('/')[-2:]}")
                if isinstance(data, dict):
                    print(f"    keys: {list(data.keys())[:8]}")
                    # Procurar por listas de cores ou jantes
                    for k, v in data.items():
                        if isinstance(v, list) and len(v) > 2:
                            print(f"    {k}: lista com {len(v)} items")
                            if v:
                                sample = v[0]
                                if isinstance(sample, dict):
                                    print(f"    {k}[0] keys: {list(sample.keys())[:6]}")
                elif isinstance(data, list):
                    print(f"    lista com {len(data)} items")
                    if data and isinstance(data[0], dict):
                        print(f"    [0] keys: {list(data[0].keys())[:6]}")
        except urllib.error.HTTPError as e:
            print(f"  {e.code}: {url.split('/')[-2:]}")
        except Exception as e:
            print(f"  ERRO: {str(e)[:50]}: {url.split('/')[-2:]}")


def intercept_with_cookie_accept():
    """Usa Playwright, aceita cookies e navega ao Golf para interceptar cores/jantes."""
    print("\n=== Playwright com aceitacao de cookies ===")

    api_calls = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1440, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()

        def on_response(response):
            ct = response.headers.get("content-type", "")
            if "json" in ct and response.status == 200:
                try:
                    data = response.json()
                    url = response.url
                    if "cookielaw" not in url and "onetrust" not in url:
                        api_calls[url] = data
                        print(f"  [API] {url[:90]}")
                except Exception:
                    pass

        page.on("response", on_response)

        # 1. Abrir página de modelos
        print("  1. A abrir modelos...")
        page.goto("https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models",
                  wait_until="load", timeout=45000)
        time.sleep(3)

        # 2. Aceitar cookies se o botão existir
        print("  2. A aceitar cookies...")
        cookie_selectors = [
            "button#onetrust-accept-btn-handler",
            "button[id*='accept']",
            "button[class*='accept-all']",
            ".ot-pc-refuse-all-handler",
            "button:has-text('Aceitar')",
            "button:has-text('Accept')",
            "button:has-text('Aceitar todos')",
        ]
        accepted = False
        for sel in cookie_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    accepted = True
                    print(f"    Cookies aceites com: {sel}")
                    time.sleep(2)
                    break
            except Exception:
                pass
        if not accepted:
            print("    Cookie button nao encontrado - a continuar")

        # 3. Screenshot após aceitar cookies
        page.screenshot(path="data/after_cookies.png")

        # 4. Tentar navegar para Golf
        print("  3. A procurar Golf na lista...")
        golf_selectors = [
            "a[href*='D03']",
            "a:has-text('GOLF')",
            "a[href*='golf']",
            "*:has-text('GOLF'):not(script):not(style)",
        ]
        golf_found = False
        for sel in golf_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    href = el.get_attribute("href") or ""
                    print(f"    Golf encontrado: {sel} href={href[:60]}")
                    el.click()
                    golf_found = True
                    time.sleep(5)
                    break
            except Exception:
                pass

        if not golf_found:
            print("    Golf nao clicado - a navegar directamente")
            page.goto(
                f"https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models/{GOLF_GROUP}/{GOLF_CODE}",
                wait_until="load", timeout=30000
            )
            time.sleep(8)

        page.screenshot(path="data/golf_config2.png")
        print("    Screenshot: data/golf_config2.png")

        # 5. Tentar clicar no tab "Cores" ou equivalente
        print("  4. A procurar tab de cores...")
        color_tab_selectors = [
            "a:has-text('Cor')",
            "button:has-text('Cor')",
            "[data-tab='colors']",
            "a[href*='color']",
            "a[href*='exterior']",
            "li:has-text('Cor')",
        ]
        for sel in color_tab_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    print(f"    Tab de cores: {sel}")
                    el.click()
                    time.sleep(4)
                    page.screenshot(path="data/golf_colors_tab.png")
                    print("    Screenshot: data/golf_colors_tab.png")
                    break
            except Exception:
                pass

        time.sleep(3)

        browser.close()

    # Guardar e analisar
    with open("data/golf_api2.json", "w", encoding="utf-8") as f:
        json.dump(api_calls, f, ensure_ascii=False, indent=2)
    print(f"\n  {len(api_calls)} APIs interceptadas")

    # Procurar dados de cores
    print("\n  Analise para cores/jantes:")
    for url, data in api_calls.items():
        content = json.dumps(data, ensure_ascii=False)
        if any(k in content.lower() for k in ['"color"', '"colour"', '"hex"', '"rgb"', '"code":', '"wheel"', '"rim"']):
            if "cookielaw" not in url and "features" not in url:
                print(f"\n  URL: {url}")
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())[:10]}")
                print(f"  Preview: {content[:600]}")

    return api_calls


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    try_endpoints()
    intercept_with_cookie_accept()
