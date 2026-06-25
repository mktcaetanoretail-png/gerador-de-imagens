"""
Navegacao completa: Models -> GOLF -> LIFE -> Motor -> Exterior (cores/jantes).
Usa JS para clicar em componentes Angular (nwi-button, cc-variant-card).
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


def js_eval(page, script: str, label: str):
    try:
        result = page.evaluate(script)
        print(f"  JS '{label}': {str(result)[:100]}")
        return result
    except Exception as e:
        print(f"  JS '{label}' erro: {e}")
        return None


def wait_screenshot(page, name: str, secs: float = 4):
    time.sleep(secs)
    path = f"data/ff_{name}.png"
    page.screenshot(path=path)
    print(f"  Screenshot: {path} | URL: {page.url}")


def get_menu_state(page):
    try:
        return page.evaluate("""
            () => document.querySelectorAll('[data-cy-menu]')
                ? Array.from(document.querySelectorAll('[data-cy-menu]')).map(e => ({
                    id: e.getAttribute('data-cy-menu'),
                    disabled: e.getAttribute('aria-disabled'),
                    active: e.classList.contains('active') || e.classList.contains('selected')
                }))
                : []
        """)
    except Exception:
        return []


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

        # 1. Abrir modelos e ir para Golf
        print("=== PASSO 1: Modelos -> Golf ===")
        page.goto(BASE_URL, wait_until="load", timeout=45000)
        time.sleep(3)
        js_eval(page, "document.querySelector('[href*=\"/auv/D03\"]').click(); 'clicked'", "GOLF")
        wait_screenshot(page, "01_auv", 5)

        # 2. Seleccionar LIFE (CC-VARIANT-CARD com texto LIFE)
        print("\n=== PASSO 2: Seleccionar variante LIFE ===")
        variant_info = js_eval(page, """
            () => {
                const cards = document.querySelectorAll('cc-variant-card');
                return Array.from(cards).map(c => ({
                    name: c.getAttribute('data-cy-variant-name') || c.querySelector('[data-cy="variant-name"]')?.textContent?.trim(),
                    outer: c.outerHTML.substring(0, 200)
                }));
            }
        """, "variant cards")

        # Clicar na carta LIFE
        life_clicked = js_eval(page, """
            () => {
                const cards = document.querySelectorAll('cc-variant-card');
                for (const card of cards) {
                    const nameEl = card.querySelector('[data-cy="variant-name"]');
                    if (nameEl && nameEl.textContent.includes('LIFE')) {
                        card.click();
                        return 'clicked LIFE: ' + nameEl.textContent.trim();
                    }
                }
                // Fallback: tentar pelo texto directamente
                const all = document.querySelectorAll('[data-cy="variant-name"]');
                for (const el of all) {
                    if (el.textContent.includes('LIFE')) {
                        el.closest('[data-cy="variant"]')?.click();
                        el.click();
                        return 'clicked via name: ' + el.textContent.trim();
                    }
                }
                return null;
            }
        """, "LIFE card click")
        time.sleep(2)

        # 3. Clicar Continuar
        print("\n=== PASSO 3: Continuar (auv -> motor) ===")
        js_eval(page, "document.querySelector('.next-button').click(); 'clicked'", "Continuar")
        wait_screenshot(page, "02_after_continuar", 5)
        print(f"  Menus: {get_menu_state(page)}")

        # 4. Ver o que está na página de motor
        print("\n=== PASSO 4: Motor - ver elementos ===")
        engine_info = js_eval(page, """
            () => {
                // Procurar listas de motores/motorizations
                const result = {};
                // Típico: cc-engine-card, cc-model-card, ou tiles com motor
                result.engineCards = Array.from(document.querySelectorAll('[data-cy="engine-tile"], [data-cy="model-tile"], cc-model-tile, cc-engine-tile')).slice(0,5).map(e => e.textContent.trim().substring(0,100));
                result.tiles = Array.from(document.querySelectorAll('[class*="tile"]:not([class*="model-group"])')).slice(0,5).map(e => ({
                    class: e.className.substring(0,60),
                    text: e.textContent.trim().substring(0,80),
                    tag: e.tagName
                }));
                result.nextButton = document.querySelector('.next-button')?.textContent?.trim();
                result.pageTitle = document.querySelector('h1')?.textContent?.trim();
                return result;
            }
        """, "motor page info")

        # Tentar clicar no primeiro motor disponível
        print("\n=== PASSO 5: Seleccionar primeiro motor ===")
        js_eval(page, """
            () => {
                // Tentar vários selectores de motor
                const selectors = [
                    '[data-cy="engine-tile"]',
                    '[data-cy="model-tile"]',
                    'cc-model-tile',
                    'cc-engine-tile',
                    '[class*="engine"] [role="button"]',
                    '[class*="model-tile"] [role="button"]',
                    '.model-tile',
                ];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        el.click();
                        return 'clicked: ' + sel;
                    }
                }
                return 'nenhum motor encontrado';
            }
        """, "first engine")
        time.sleep(2)

        # Clicar Continuar de novo
        js_eval(page, "const btn = document.querySelector('.next-button'); if(btn) { btn.click(); return 'clicked'; } return 'not found';", "Continuar (motor)")
        wait_screenshot(page, "03_after_motor_continuar", 5)
        print(f"  Menus: {get_menu_state(page)}")
        print(f"  APIs: {len(api_calls)}")

        # 6. Navegar para Exterior via menu
        print("\n=== PASSO 6: Menu Exterior ===")
        exterior_result = js_eval(page, """
            () => {
                const el = document.querySelector('[data-cy-menu="exterior"]');
                if (el) {
                    const disabled = el.getAttribute('aria-disabled');
                    el.click();
                    return 'clicked, was-disabled: ' + disabled;
                }
                return 'not found';
            }
        """, "exterior menu")
        wait_screenshot(page, "04_exterior", 6)
        print(f"  APIs: {len(api_calls)}")

        # 7. Procurar swatches de cor
        print("\n=== PASSO 7: Swatches de cor ===")
        color_info = js_eval(page, """
            () => {
                const result = {};
                // Swatches de cor
                const swatches = document.querySelectorAll('[class*="swatch"], [data-color-id], [data-color-code], cc-exterior-color, cc-color-swatch');
                result.swatches = Array.from(swatches).slice(0,10).map(e => ({
                    tag: e.tagName,
                    class: e.className.substring(0,60),
                    attrs: {
                        colorId: e.getAttribute('data-color-id'),
                        colorCode: e.getAttribute('data-color-code'),
                        color: e.getAttribute('data-color'),
                    },
                    outer: e.outerHTML.substring(0,200)
                }));
                result.pageTitle = document.querySelector('h1')?.textContent?.trim();
                result.url = window.location.href;
                return result;
            }
        """, "color swatches")

        # Guardar HTML final
        html = page.content()
        with open("data/exterior_page.html", "w", encoding="utf-8") as f:
            f.write(html)

        browser.close()

    # Guardar APIs
    with open("data/full_flow_api.json", "w", encoding="utf-8") as f:
        json.dump(api_calls, f, ensure_ascii=False, indent=2)

    print(f"\nTotal APIs: {len(api_calls)}")
    standard = {"modelgroup", "wcproducts", "wcping", "all-messages", "features/list", "config/V", "wcmcrates", "artificialVariants", "referenceModel"}
    print("\nAPIs nao-standard:")
    for url, data in api_calls.items():
        if not any(k in url for k in standard):
            content_str = json.dumps(data, ensure_ascii=False)
            print(f"\n  URL: {url}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:10]}")
            elif isinstance(data, list):
                print(f"  Lista: {len(data)}")
            print(f"  {content_str[:800]}")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    run()
