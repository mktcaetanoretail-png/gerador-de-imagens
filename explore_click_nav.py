"""
Navegação click-through no configurador VW:
Modelos -> Golf -> LIFE -> Exterior (cores)
Intercepta as APIs de cores e jantes.
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
            skip = ["cookielaw", "onetrust", "geolocation", "scripttemplates", "ping"]
            if not any(s in url for s in skip):
                api_calls[url] = data
                print(f"  [API] {url[:100]}")
        except Exception:
            pass


def wait_and_screenshot(page: Page, name: str, wait_secs: float = 3):
    time.sleep(wait_secs)
    path = f"data/nav_{name}.png"
    page.screenshot(path=path)
    print(f"  Screenshot: {path}")
    return path


def find_and_click(page: Page, selectors: list, label: str, wait_after: float = 3) -> bool:
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                href = el.get_attribute("href") or ""
                txt = el.inner_text(timeout=1000).strip()[:40]
                print(f"  Clicando '{label}': {sel} | texto='{txt}' href='{href[:50]}'")
                el.click()
                time.sleep(wait_after)
                return True
        except Exception:
            pass
    print(f"  NAO ENCONTRADO: {label}")
    return False


def navigate_to_golf_colors():
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

        # 1. Abrir página de modelos
        print("1. A abrir pagina de modelos...")
        page.goto(BASE_URL, wait_until="load", timeout=45000)
        wait_and_screenshot(page, "01_models", 4)

        # 2. Clicar em GOLF
        print("\n2. A clicar em GOLF...")
        golf_selectors = [
            "a[href*='/auv/D03']",
            "a[href*='/models/D03']",
            "a:has-text('GOLF'):not(:has-text('VARIANT'))",
            "[class*='tile']:has-text('GOLF'):not(:has-text('VARIANT')) a",
        ]
        clicked_golf = find_and_click(page, golf_selectors, "GOLF", wait_after=5)
        wait_and_screenshot(page, "02_golf_variants", 3)
        print(f"  URL actual: {page.url}")

        if not clicked_golf:
            print("  A tentar navegacao directa...")
            page.goto(
                f"https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/auv/D03",
                wait_until="load", timeout=30000,
            )
            time.sleep(5)
            wait_and_screenshot(page, "02b_golf_direct", 2)

        # 3. Clicar em LIFE (ou primeiro variant disponível)
        print("\n3. A seleccionar variante LIFE...")
        life_selectors = [
            "a:has-text('LIFE'):not(:has-text('GTI')):not(:has-text('GTE'))",
            "button:has-text('LIFE')",
            "[class*='variant']:has-text('LIFE') a",
            "a[href*='DA13HYA2']",
            # Fallback: primeiro link de variante
            "[class*='tile-list'] a:first-child",
            "[class*='variant-list'] a:first-child",
            "[class*='model-tile'] a",
        ]
        clicked_life = find_and_click(page, life_selectors, "LIFE", wait_after=5)
        wait_and_screenshot(page, "03_golf_config", 3)
        print(f"  URL actual: {page.url}")

        # 4. Procurar e clicar em tab "Exteriores" / "Cor" / "Design"
        print("\n4. A clicar no tab de Exteriores/Design/Cor...")
        design_selectors = [
            "a:has-text('Exteriores')",
            "a:has-text('Exterior')",
            "a:has-text('Design')",
            "a:has-text('Cores')",
            "a:has-text('Cor')",
            "li:has-text('Exteriores') a",
            "li:has-text('Design') a",
            "li:has-text('Cor') a",
            "[class*='tab']:has-text('Exterior') a",
            "[class*='tab']:has-text('Design') a",
            "[href*='exterior']",
            "[href*='design']",
            "[href*='color']",
        ]
        clicked_design = find_and_click(page, design_selectors, "Design/Cor", wait_after=5)
        wait_and_screenshot(page, "04_design_colors", 3)
        print(f"  URL actual: {page.url}")

        # 5. Aguardar mais tempo para carregar cores
        print("\n5. A aguardar carregamento de cores...")
        time.sleep(5)
        wait_and_screenshot(page, "05_colors_loaded", 2)

        # 6. Listar elementos de cor encontrados
        print("\n6. Elementos de cor na pagina:")
        color_selectors = [
            "[class*='swatch']",
            "[class*='color-option']",
            "[class*='colour']",
            "[data-color-code]",
            "[data-color]",
            "input[type='radio']",
            "[class*='color-tile']",
            "label[class*='color']",
            "[class*='exterior-color']",
        ]
        for sel in color_selectors:
            try:
                els = page.locator(sel).all()
                if els:
                    print(f"  '{sel}': {len(els)} elementos")
                    for el in els[:3]:
                        try:
                            outer = el.evaluate("el => el.outerHTML")[:200]
                            print(f"    {outer}")
                        except Exception:
                            pass
            except Exception:
                pass

        # 7. Dump do HTML da pagina actual
        html = page.content()
        with open("data/golf_exterior_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("\n  HTML guardado: data/golf_exterior_page.html")

        browser.close()

    # Guardar APIs
    with open("data/click_nav_api.json", "w", encoding="utf-8") as f:
        json.dump(api_calls, f, ensure_ascii=False, indent=2)
    print(f"\nTotal APIs interceptadas: {len(api_calls)}")

    # Analisar APIs novas relevantes
    known_apis = {"modelgroup", "wcproducts", "wcping", "all-messages", "features/list", "config/V"}
    print("\nAPIs nao-standard:")
    for url, data in api_calls.items():
        if not any(k in url for k in known_apis) and "wcmcrates" not in url and "cookielaw" not in url:
            print(f"\n  URL: {url}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
            elif isinstance(data, list):
                print(f"  Lista: {len(data)} items")
                if data and isinstance(data[0], dict):
                    print(f"  [0] Keys: {list(data[0].keys())[:8]}")
            content = json.dumps(data, ensure_ascii=False)
            print(f"  Preview: {content[:600]}")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    navigate_to_golf_colors()
