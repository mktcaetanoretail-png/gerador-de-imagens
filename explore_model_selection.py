"""
Tenta navegar de auv para model-selection (motor) para desbloquear exterior.
"""
import json
import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models"
api_calls = {}


def add_consent_cookies(context):
    context.add_cookies([
        {"name": "OptanonAlertBoxClosed", "value": "2026-05-25T10:00:00.000Z", "domain": ".volkswagen.pt", "path": "/"},
        {"name": "OptanonConsent", "value": "isGpcEnabled=0&datestamp=Sun+May+25+2026&version=202603.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=x&interactionCount=1&isAnonUser=1&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1", "domain": ".volkswagen.pt", "path": "/"},
    ])


def on_response(response):
    ct = response.headers.get("content-type", "")
    if "json" in ct and response.status == 200:
        try:
            data = response.json()
            url = response.url
            if not any(s in url for s in ["cookielaw", "onetrust", "geolocation", "scripttemplates", "linkedin", "inside-graph"]):
                api_calls[url] = data
                print(f"  [API] {url[:100]}")
        except Exception:
            pass


def js(page, script: str, label: str = ""):
    try:
        r = page.evaluate(f"(() => {{ {script} }})()")
        print(f"  JS {label}: {str(r)[:120]}")
        return r
    except Exception as e:
        print(f"  JS {label} erro: {e}")
        return None


def screenshot(page, name: str, wait: float = 4):
    time.sleep(wait)
    page.screenshot(path=f"data/ms_{name}.png")
    print(f"  URL: {page.url} | screenshot: ms_{name}.png")


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

        # 1. Models -> Golf -> LIFE
        page.goto(BASE_URL, wait_until="load", timeout=45000)
        time.sleep(3)
        js(page, "document.querySelector('[href*=\"/auv/D03\"]').click()", "GOLF click")
        time.sleep(5)

        # Seleccionar LIFE
        js(page, """
            const cards = document.querySelectorAll('[data-cy="variant-name"]');
            for (const c of cards) {
                if (c.textContent.includes('LIFE')) { c.closest('[data-cy="variant"]').click(); return 'LIFE clicked'; }
            }
            return 'LIFE not found';
        """, "LIFE select")
        time.sleep(2)

        print("\n--- Clicar model-selection ---")
        js(page, "document.querySelector('[data-cy-menu=\"model-selection\"]').click()", "model-selection click")
        screenshot(page, "01_model_selection", 5)

        # Ver o que há na página de model-selection
        page_info = js(page, """
            return {
                title: document.querySelector('h1')?.textContent?.trim(),
                menus: Array.from(document.querySelectorAll('[data-cy-menu]')).map(e => ({
                    id: e.getAttribute('data-cy-menu'),
                    disabled: e.getAttribute('aria-disabled'),
                    active: e.classList.contains('active')
                })),
                tiles: Array.from(document.querySelectorAll('[class*="model-tile"], cc-model-tile, [data-cy="model-tile"]')).slice(0,5).map(e => e.textContent.trim().substring(0,80)),
                allTiles: Array.from(document.querySelectorAll('[role="button"]')).slice(0,10).map(e => ({
                    class: e.className.substring(0,60),
                    text: e.textContent.trim().substring(0,50),
                    tag: e.tagName
                }))
            };
        """, "model-selection page info")

        print(f"\n  Titulo: {page_info.get('title') if page_info else 'N/A'}")
        if page_info:
            print(f"  Menus: {page_info.get('menus')}")
            print(f"  Tiles: {page_info.get('tiles')}")
            print(f"  Buttons: {page_info.get('allTiles')[:5]}")

        # Tentar clicar no primeiro tile/model disponível
        print("\n--- Seleccionar primeiro modelo/motor ---")
        js(page, """
            const selectors = [
                'cc-model-tile',
                '[data-cy="model-tile"]',
                '[class*="model-card"] [role="button"]',
                '.model-tile',
                '[class*="motorization"] [role="button"]',
                '[class*="engine"] [role="button"]',
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) { el.click(); return 'clicked: ' + sel; }
            }
            // Fallback: clicar no primeiro role=button que não seja header/nav
            const buttons = document.querySelectorAll('[role="button"]');
            for (const btn of buttons) {
                const cls = btn.className;
                if (!cls.includes('menu-element') && !cls.includes('nwi-button') && !cls.includes('price')) {
                    btn.click();
                    return 'fallback clicked: ' + cls.substring(0,50);
                }
            }
            return 'nothing clicked';
        """, "first model")
        time.sleep(2)

        # Continuar para exterior
        print("\n--- Clicar Continuar para ir para Exterior ---")
        js(page, "const btn = document.querySelector('.next-button'); if(btn) btn.click(); return btn ? 'ok' : 'not found';", "Continuar")
        screenshot(page, "02_after_continuar", 5)

        # Tentar clicar exterior
        print("\n--- Clicar exterior menu ---")
        menu_state = js(page, """
            return Array.from(document.querySelectorAll('[data-cy-menu]')).map(e => ({
                id: e.getAttribute('data-cy-menu'),
                disabled: e.getAttribute('aria-disabled')
            }));
        """, "menu state")
        print(f"  Menu state: {menu_state}")

        js(page, "document.querySelector('[data-cy-menu=\"exterior\"]').click()", "exterior click")
        screenshot(page, "03_exterior", 6)

        # Ver APIs e swatches
        print(f"\nAPIs: {len(api_calls)}")

        color_el = js(page, """
            return {
                swatches: Array.from(document.querySelectorAll('[class*="swatch"], cc-exterior-color, cc-color-swatch, [class*="color-option"]')).slice(0,10).map(e => ({
                    tag: e.tagName,
                    class: e.className.substring(0,80),
                    outer: e.outerHTML.substring(0, 300)
                })),
                title: document.querySelector('h1')?.textContent?.trim(),
                anyColorInput: document.querySelector('input[name*="color"], [data-color]')?.outerHTML?.substring(0,200)
            };
        """, "color elements")
        print(f"  Color elements: {json.dumps(color_el, ensure_ascii=False)[:500] if color_el else 'none'}")

        # Guardar HTML
        html = page.content()
        with open("data/model_selection_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("  HTML: data/model_selection_page.html")

        browser.close()

    # Guardar APIs
    with open("data/model_sel_api.json", "w", encoding="utf-8") as f:
        json.dump(api_calls, f, ensure_ascii=False, indent=2)

    standard = {"modelgroup", "wcproducts", "wcping", "all-messages", "features/list", "config/V", "wcmcrates", "artificialVariants", "referenceModel"}
    print("\nAPIs novas:")
    for url, data in api_calls.items():
        if not any(k in url for k in standard):
            content_str = json.dumps(data, ensure_ascii=False)
            if len(content_str) > 50:
                print(f"\n  URL: {url}")
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    print(f"  Lista: {len(data)}")
                    if data and isinstance(data[0], dict):
                        print(f"  [0] keys: {list(data[0].keys())[:8]}")
                print(f"  {content_str[:1000]}")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    run()
