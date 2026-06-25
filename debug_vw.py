"""
Ferramenta de inspecção do configurador VW.
Corre este script primeiro para perceber a estrutura DOM e APIs usadas.
Gera ficheiros em data/ para análise.
"""
import json
import os
import sys
from playwright.sync_api import sync_playwright

URL_MODELOS = "https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models"

SELECTORES_A_TESTAR = [
    "a[href*='/models/']",
    "[data-model-id]",
    "[data-e2e*='model']",
    "[class*='model-tile']",
    "[class*='model-card']",
    "[class*='ModelTile']",
    "[class*='tile-item']",
    "article",
    "[class*='vehicle']",
]


def dump_file(path, content, mode="w", encoding="utf-8"):
    with open(path, mode, encoding=encoding) as f:
        f.write(content)
    print(f"  Guardado: {path}")


def inspect_models_page(page):
    api_calls = {}

    def on_response(response):
        ct = response.headers.get("content-type", "")
        if "json" in ct and response.status == 200:
            try:
                data = response.json()
                api_calls[response.url] = data
                print(f"  [API] {response.url[:90]}")
            except Exception:
                pass

    page.on("response", on_response)

    print(f"\n--- Página de modelos ---")
    print(f"A abrir: {URL_MODELOS}")
    page.goto(URL_MODELOS, wait_until="networkidle", timeout=60000)

    page.screenshot(path="data/inspect_01_models.png", full_page=True)
    dump_file("data/inspect_01_models.html", page.content())

    print("\n  Selectores encontrados:")
    for sel in SELECTORES_A_TESTAR:
        try:
            els = page.locator(sel).all()
            if els:
                print(f"    '{sel}': {len(els)} elemento(s)")
                for el in els[:3]:
                    try:
                        txt = el.inner_text(timeout=1000).strip()[:80].replace("\n", " ")
                        href = el.get_attribute("href") or ""
                        outer = el.evaluate("el => el.outerHTML")[:150]
                        print(f"      texto='{txt}' href='{href}'")
                        print(f"      html={outer}")
                    except Exception:
                        pass
        except Exception:
            pass

    dump_file("data/inspect_api_models.json", json.dumps(api_calls, ensure_ascii=False, indent=2))
    print(f"\n  {len(api_calls)} chamadas API interceptadas → data/inspect_api_models.json")

    return api_calls, page


def inspect_first_model(page, api_calls):
    """Tenta navegar para o primeiro modelo e inspeccionar a página de configuração."""
    link = page.locator("a[href*='/models/']").first
    if not link:
        print("\nNão foi possível encontrar link para um modelo.")
        return

    href = link.get_attribute("href")
    print(f"\n--- Página de configuração (primeiro modelo) ---")
    print(f"A navegar para: {href}")

    config_api_calls = {}

    def on_config_response(response):
        ct = response.headers.get("content-type", "")
        if "json" in ct and response.status == 200:
            try:
                data = response.json()
                config_api_calls[response.url] = data
                print(f"  [API] {response.url[:90]}")
            except Exception:
                pass

    page.on("response", on_config_response)

    if href.startswith("http"):
        page.goto(href, wait_until="networkidle", timeout=60000)
    else:
        page.goto(f"https://configurador.volkswagen.pt{href}", wait_until="networkidle", timeout=60000)

    page.screenshot(path="data/inspect_02_config.png", full_page=True)
    dump_file("data/inspect_02_config.html", page.content())

    print("\n  Selectores de cor:")
    for sel in ["[class*='color']", "[data-color]", "[data-color-id]", "[class*='swatch']", "button[title]"]:
        try:
            els = page.locator(sel).all()
            if els:
                print(f"    '{sel}': {len(els)}")
                for el in els[:2]:
                    try:
                        outer = el.evaluate("el => el.outerHTML")[:200]
                        print(f"      {outer}")
                    except Exception:
                        pass
        except Exception:
            pass

    print("\n  Selectores de jantes:")
    for sel in ["[class*='wheel']", "[class*='rim']", "[class*='jante']", "[data-wheel]"]:
        try:
            els = page.locator(sel).all()
            if els:
                print(f"    '{sel}': {len(els)}")
                for el in els[:2]:
                    try:
                        outer = el.evaluate("el => el.outerHTML")[:200]
                        print(f"      {outer}")
                    except Exception:
                        pass
        except Exception:
            pass

    print("\n  Elemento de imagem do carro:")
    for sel in ["canvas", "img[src*='media']", "img[class*='car']", "[class*='stage'] img", "[class*='viewer'] img"]:
        try:
            el = page.locator(sel).first
            if el:
                outer = el.evaluate("el => el.outerHTML")[:300]
                print(f"    '{sel}': {outer}")
        except Exception:
            pass

    dump_file("data/inspect_api_config.json", json.dumps(config_api_calls, ensure_ascii=False, indent=2))
    print(f"\n  {len(config_api_calls)} chamadas API → data/inspect_api_config.json")


def main():
    os.makedirs("data", exist_ok=True)

    headless = "--headless" in sys.argv
    print(f"Modo: {'headless' if headless else 'com browser visível'}")
    print("(passa --headless para correr sem janela)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=headless,
            slow_mo=300 if not headless else 0,
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()

        api_calls, page = inspect_models_page(page)
        inspect_first_model(page, api_calls)

        if not headless:
            input("\nPrima Enter para fechar o browser...")

        browser.close()

    print("\nInspecção concluída. Analisa os ficheiros em data/")


if __name__ == "__main__":
    main()
