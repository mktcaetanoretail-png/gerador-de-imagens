"""
Navega directamente ao tab 'Pintura' do configurador Golf
e intercepta a API de cores e jantes.
"""
import json
import os
import time
from playwright.sync_api import sync_playwright, Page

BASE_URL = "https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models"
api_calls = {}


def add_consent_cookies(context):
    context.add_cookies([
        {
            "name": "OptanonAlertBoxClosed",
            "value": "2026-05-25T10:00:00.000Z",
            "domain": ".volkswagen.pt",
            "path": "/",
        },
        {
            "name": "OptanonConsent",
            "value": (
                "isGpcEnabled=0&datestamp=Sun+May+25+2026&version=202603.1.0"
                "&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=x"
                "&interactionCount=1&isAnonUser=1"
                "&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1"
            ),
            "domain": ".volkswagen.pt",
            "path": "/",
        },
    ])


def on_response(response):
    ct = response.headers.get("content-type", "")
    if "json" in ct and response.status == 200:
        try:
            data = response.json()
            url = response.url
            skip = ["cookielaw", "onetrust", "geolocation", "scripttemplates", "linkedin", "inside-graph"]
            if not any(s in url for s in skip):
                api_calls[url] = data
                print(f"  [API] {url[:100]}")
        except Exception:
            pass


def screenshot(page: Page, name: str):
    path = f"data/p_{name}.png"
    page.screenshot(path=path)
    print(f"  Screenshot: {path}")


def click_first_visible(page: Page, selectors: list, label: str, wait: float = 4) -> bool:
    for sel in selectors:
        try:
            els = page.locator(sel).all()
            for el in els:
                if el.is_visible(timeout=1000):
                    txt = el.inner_text(timeout=500).strip()[:50]
                    print(f"  Click '{label}': '{txt}' [{sel}]")
                    el.click()
                    time.sleep(wait)
                    return True
        except Exception:
            pass
    print(f"  NAO ENCONTRADO: {label}")
    return False


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1440, "height": 900},
            ignore_https_errors=True,
        )
        add_consent_cookies(context)
        page = context.new_page()
        page.on("response", on_response)

        # 1. Modelos
        print("=== PASSO 1: Modelos ===")
        page.goto(BASE_URL, wait_until="load", timeout=45000)
        time.sleep(4)
        screenshot(page, "01_models")

        # 2. Clicar em GOLF
        print("\n=== PASSO 2: GOLF ===")
        click_first_visible(page, [
            "a[href*='/auv/D03']",
            "a[href*='/models/D03']",
        ], "GOLF", wait=5)
        screenshot(page, "02_golf")
        print(f"  URL: {page.url}")

        # 3. Navegar directamente ao tab "Pintura"
        print("\n=== PASSO 3: Tab Pintura ===")
        pintura_selectors = [
            "a:has-text('Pintura')",
            "li:has-text('Pintura') a",
            "a[href*='pintura']",
            "a[href*='paint']",
            "[class*='nav'] a:has-text('Pintura')",
            "[class*='step'] a:has-text('Pintura')",
            "[class*='tab'] a:has-text('Pintura')",
        ]
        clicked_pintura = click_first_visible(page, pintura_selectors, "Pintura", wait=6)
        screenshot(page, "03_pintura")
        print(f"  URL: {page.url}")

        if not clicked_pintura:
            # Tentar "Continuar" para avançar de nível de equipamento
            print("  A tentar 'Continuar'...")
            click_first_visible(page, [
                "button:has-text('Continuar')",
                "a:has-text('Continuar')",
                "button[class*='continue']",
                "button[class*='next']",
            ], "Continuar", wait=5)
            screenshot(page, "03b_after_continuar")
            print(f"  URL: {page.url}")

            # Tentar Pintura de novo
            click_first_visible(page, pintura_selectors, "Pintura (2a tentativa)", wait=6)
            screenshot(page, "03c_pintura2")

        # 4. Aguardar e tirar screenshot da página de cores
        print("\n=== PASSO 4: Aguardar cores ===")
        time.sleep(5)
        screenshot(page, "04_colors_loaded")
        print(f"  URL: {page.url}")

        # 5. Listar elementos de swatches de cor
        print("\n=== PASSO 5: Swatches de cor ===")
        swatch_selectors = [
            "[class*='swatch']",
            "[class*='color-swatch']",
            "[class*='colour']",
            "label[class*='color']",
            "[data-color]",
            "[data-color-id]",
            "[data-color-code]",
            "input[type='radio']",
            "[class*='tile']:not([class*='model'])",
            "[class*='option']",
        ]
        for sel in swatch_selectors:
            try:
                els = page.locator(sel).all()
                if els and len(els) > 0:
                    print(f"  '{sel}': {len(els)} elementos")
                    for el in els[:4]:
                        try:
                            outer = el.evaluate("el => el.outerHTML")[:300]
                            print(f"    {outer}")
                        except Exception:
                            pass
            except Exception:
                pass

        # 6. Guardar HTML para análise manual
        html = page.content()
        with open("data/pintura_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\n  HTML: data/pintura_page.html")

        browser.close()

    # Guardar APIs
    with open("data/pintura_api.json", "w", encoding="utf-8") as f:
        json.dump(api_calls, f, ensure_ascii=False, indent=2)
    print(f"\nTotal APIs: {len(api_calls)}")

    # Mostrar APIs que parecem ser de configuração (não as habituais)
    standard = {"modelgroup", "wcproducts", "wcping", "all-messages", "features/list", "config/V"}
    print("\nAPIs de configuracao (nao-standard):")
    for url, data in api_calls.items():
        if not any(k in url for k in standard) and "wcmcrates" not in url:
            content = json.dumps(data, ensure_ascii=False)
            # Mostrar se tem mais de 100 chars de conteúdo
            if len(content) > 100:
                print(f"\n  URL: {url}")
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())[:12]}")
                elif isinstance(data, list) and data:
                    print(f"  Lista: {len(data)} items, [0] keys: {list(data[0].keys())[:8] if isinstance(data[0], dict) else type(data[0])}")
                print(f"  Preview: {content[:800]}")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    run()
