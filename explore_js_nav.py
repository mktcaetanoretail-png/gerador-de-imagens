"""
Usa JavaScript para navegar no configurador VW:
GOLF -> Continuar -> Pintura/Exterior -> interceptar API de cores.
"""
import json
import os
import time
from playwright.sync_api import sync_playwright

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


def js_click(page, selector_js: str, label: str) -> bool:
    """Usa JS para encontrar e clicar um elemento."""
    try:
        result = page.evaluate(f"""
            (() => {{
                const el = {selector_js};
                if (el) {{
                    el.click();
                    return el.textContent || el.outerHTML.substring(0, 100);
                }}
                return null;
            }})()
        """)
        if result:
            print(f"  JS click '{label}': {str(result)[:80]}")
            return True
        else:
            print(f"  JS click '{label}': nao encontrado")
            return False
    except Exception as e:
        print(f"  JS click '{label}' erro: {e}")
        return False


def get_page_menu_items(page) -> list:
    """Extrai todos os items de menu visíveis."""
    try:
        items = page.evaluate("""
            () => {
                const els = document.querySelectorAll('[role="button"].menu-element, [data-cy-menu]');
                return Array.from(els).map(el => ({
                    id: el.id,
                    title: el.getAttribute('title') || el.textContent.trim().substring(0,30),
                    dataCy: el.getAttribute('data-cy-menu'),
                    disabled: el.getAttribute('aria-disabled'),
                    class: el.className.substring(0,80)
                }));
            }
        """)
        return items or []
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

        # 1. Modelos
        print("=== 1. Modelos ===")
        page.goto(BASE_URL, wait_until="load", timeout=45000)
        time.sleep(4)

        # 2. Clicar GOLF via JS
        print("\n=== 2. GOLF ===")
        js_click(page, "document.querySelector('[href*=\"/auv/D03\"]')", "GOLF")
        time.sleep(5)
        print(f"  URL: {page.url}")

        # Mostrar menus
        menus = get_page_menu_items(page)
        if menus:
            print(f"  Menus: {menus}")

        # 3. Clicar Continuar via JS
        print("\n=== 3. Continuar ===")
        js_click(page, "document.querySelector('.next-button')", "Continuar")
        time.sleep(6)
        print(f"  URL: {page.url}")
        page.screenshot(path="data/js_03_after_continuar.png")

        # Mostrar menus novamente
        menus = get_page_menu_items(page)
        if menus:
            print(f"  Menus: {menus}")

        # Verificar que APIs novas foram capturadas
        print(f"  APIs ate agora: {len(api_calls)}")

        # 4. Tentar navegar para Exterior/Pintura via menu
        print("\n=== 4. Exterior/Pintura ===")
        # Tentar pelo data-cy-menu
        for menu_name in ["exterior", "paint", "pintura", "colour", "color", "design"]:
            clicked = js_click(
                page,
                f'document.querySelector("[data-cy-menu=\\"{menu_name}\\"]")',
                f"menu:{menu_name}"
            )
            if clicked:
                time.sleep(5)
                print(f"  URL: {page.url}")
                page.screenshot(path=f"data/js_04_{menu_name}.png")
                break

        # 5. Aguardar e verificar
        print("\n=== 5. Estado final ===")
        time.sleep(5)
        print(f"  URL: {page.url}")
        page.screenshot(path="data/js_05_final.png")

        # Listar todos os data-cy e aria-labels da página
        elements_info = page.evaluate("""
            () => {
                const result = {};
                // Elementos com data-cy
                const cy = document.querySelectorAll('[data-cy]');
                result.dataCy = Array.from(cy).slice(0,20).map(el => ({
                    cy: el.getAttribute('data-cy'),
                    tag: el.tagName,
                    text: el.textContent.trim().substring(0,30)
                }));
                // Elementos com data-color
                const colors = document.querySelectorAll('[data-color-id], [data-color], [class*="swatch"]');
                result.colorEls = Array.from(colors).slice(0,10).map(el => ({
                    tag: el.tagName,
                    class: el.className.substring(0,60),
                    colorId: el.getAttribute('data-color-id'),
                    color: el.getAttribute('data-color'),
                    outer: el.outerHTML.substring(0,200)
                }));
                return result;
            }
        """)
        print(f"  data-cy elements: {json.dumps(elements_info.get('dataCy', []), ensure_ascii=False)[:500]}")
        print(f"  color elements: {json.dumps(elements_info.get('colorEls', []), ensure_ascii=False)[:500]}")

        # Guardar HTML final
        html = page.content()
        with open("data/js_final_page.html", "w", encoding="utf-8") as f:
            f.write(html)

        browser.close()

    # Guardar APIs
    with open("data/js_api.json", "w", encoding="utf-8") as f:
        json.dump(api_calls, f, ensure_ascii=False, indent=2)

    print(f"\nTotal APIs: {len(api_calls)}")
    standard = {"modelgroup", "wcproducts", "wcping", "all-messages", "features/list", "config/V", "wcmcrates"}
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
                print(f"  {content_str[:600]}")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    run()
