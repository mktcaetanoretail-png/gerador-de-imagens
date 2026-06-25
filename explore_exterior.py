"""
Navega directamente ao passo de cores/exterior do configurador VW Golf LIFE
e intercepta a API de cores. Também analisa all-messages para nomes de cores.
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
GOLF_LIFE_CODE = "DA13HYA2"
GOLF_GROUP = "D03"


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read())


def analyse_all_messages():
    """Procura nomes de cores nas mensagens de tradução."""
    print("=== all-messages: procura de cores ===")
    data = get_json(f"{BASE}/all-messages")
    color_keys = {k: v for k, v in data.items() if "color" in k.lower() or "colour" in k.lower() or "cor" in k.lower()}
    print(f"  Chaves com 'color/cor': {len(color_keys)}")
    for k, v in list(color_keys.items())[:20]:
        print(f"  {k}: {v}")
    with open("data/all_messages_colors.json", "w", encoding="utf-8") as f:
        json.dump(color_keys, f, ensure_ascii=False, indent=2)


def navigate_to_exterior():
    """Navega ao passo de exterior/cores do Golf LIFE e intercepta APIs."""
    print("\n=== Navegacao ao exterior do Golf LIFE ===")

    # URLs a tentar para o passo de cores
    urls_to_try = [
        f"https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models/{GOLF_GROUP}/{GOLF_LIFE_CODE}/V/exterior",
        f"https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models/{GOLF_GROUP}/{GOLF_LIFE_CODE}/V/colours",
        f"https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models/{GOLF_GROUP}/{GOLF_LIFE_CODE}/V/colors",
        f"https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models/{GOLF_GROUP}/{GOLF_LIFE_CODE}/V",
    ]

    api_calls = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1440, "height": 900},
            ignore_https_errors=True,
            # Definir cookie de consentimento para evitar o modal
            storage_state=None,
        )
        # Injectar cookie de consentimento antes de navegar
        page = context.new_page()

        def on_response(response):
            ct = response.headers.get("content-type", "")
            if "json" in ct and response.status == 200:
                try:
                    data = response.json()
                    url = response.url
                    if "cookielaw" not in url and "onetrust" not in url:
                        api_calls[url] = data
                        print(f"  [API] {url[:100]}")
                except Exception:
                    pass

        page.on("response", on_response)

        # Visitar primeiro a página para obter os cookies de sessão
        page.goto("https://configurador.volkswagen.pt/", wait_until="load", timeout=30000)
        time.sleep(2)

        # Injectar cookie de consentimento OneTrust
        context.add_cookies([
            {
                "name": "OptanonAlertBoxClosed",
                "value": "2026-05-25T10:00:00.000Z",
                "domain": ".volkswagen.pt",
                "path": "/",
            },
            {
                "name": "OptanonConsent",
                "value": "isGpcEnabled=0&datestamp=Sun+May+25+2026&version=202603.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=test&interactionCount=1&isAnonUser=1&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1",
                "domain": ".volkswagen.pt",
                "path": "/",
            },
        ])

        for url in urls_to_try:
            print(f"\n  A tentar: {url}")
            try:
                page.goto(url, wait_until="load", timeout=30000)
                time.sleep(6)
                current_url = page.url
                print(f"  URL final: {current_url}")

                # Screenshot
                slug = url.split("/V/")[-1].replace("/", "_")
                screenshot_path = f"data/exterior_{slug}.png"
                page.screenshot(path=screenshot_path)
                print(f"  Screenshot: {screenshot_path}")

                # Verificar se carregou a página certa
                title = page.title()
                print(f"  Titulo: {title}")

                # Verificar se apareceram novas APIs com cores
                new_color_apis = {
                    k: v for k, v in api_calls.items()
                    if any(term in k for term in ["color", "colour", "exterior", "paint", "equip"])
                    and "cookielaw" not in k
                }
                if new_color_apis:
                    print(f"  APIs com cores encontradas: {list(new_color_apis.keys())}")
                    break

            except Exception as e:
                print(f"  Erro: {e}")

        # Tentar clicar no tab de cores se existir
        print("\n  A procurar elementos de cor na pagina...")
        color_selectors = [
            "[class*='color-swatch']",
            "[class*='colour-swatch']",
            "[data-color-code]",
            "[data-colour]",
            "input[type='radio'][name*='color']",
            "[class*='exterior'] [class*='option']",
            "button[class*='color']",
        ]
        for sel in color_selectors:
            try:
                els = page.locator(sel).all()
                if els:
                    print(f"    '{sel}': {len(els)} elementos")
                    for el in els[:3]:
                        try:
                            outer = el.evaluate("el => el.outerHTML")[:200]
                            print(f"      {outer}")
                        except Exception:
                            pass
            except Exception:
                pass

        browser.close()

    # Guardar e analisar
    with open("data/exterior_api_calls.json", "w", encoding="utf-8") as f:
        json.dump(api_calls, f, ensure_ascii=False, indent=2)
    print(f"\n  Total APIs: {len(api_calls)}")
    print("  Guardado: data/exterior_api_calls.json")

    # Mostrar todas as novas APIs (não duplicadas das anteriores)
    known = {
        "api/v2/modelgroup", "wcproducts", "wcping", "all-messages",
        "features/list", "config/V", "wcmcrates",
    }
    new_apis = {k: v for k, v in api_calls.items() if not any(p in k for p in known)}
    print(f"\n  APIs novas: {len(new_apis)}")
    for url, data in new_apis.items():
        print(f"\n  URL: {url}")
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())[:10]}")
        elif isinstance(data, list):
            print(f"  Lista: {len(data)} items")
            if data and isinstance(data[0], dict):
                print(f"  [0] Keys: {list(data[0].keys())[:8]}")
        content = json.dumps(data, ensure_ascii=False)
        print(f"  Preview: {content[:500]}")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    analyse_all_messages()
    navigate_to_exterior()
