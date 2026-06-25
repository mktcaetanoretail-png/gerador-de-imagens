"""
Abre o configurador VW para um modelo específico e intercepta
todas as chamadas API, para encontrar o endpoint de cores/jantes.
Também testa padrões de ângulo adicionais para as imagens.
"""
import json
import os
import ssl
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
CDN = "https://cdn.nwi-ms.com/media/pt/V/mc"

# Usar Golf como modelo de teste (modelo principal do catálogo)
GOLF_MODEL_CODE = "DA12BXA4"
GOLF_MODEL_GROUP = "D03"
GOLF_DEFAULT_COLOR = "5K5K"
GOLF_DEFAULT_UPHOLSTERY = "BD"


def get_bytes(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        return r.read()


def test_more_angles(model_code, color, upholstery):
    print(f"\n=== Teste alargado de ângulos: {model_code} ===")
    # Ângulos adicionais a testar
    angles = [
        "34", "34f", "34front", "quarter", "quarterfront",
        "front34", "angledfront", "angled", "diagonal",
        "view1", "view2", "view3", "view4",
        "1", "2", "3", "4", "5",
        "exterior", "profile", "3q", "threequarter",
        "frontside", "frontrear",
        "default",
    ]
    found = []
    for angle in angles:
        url = f"{CDN}/{model_code}/model/{angle}.webp?F={color}&P={upholstery}&M="
        req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                size = int(r.headers.get("Content-Length", 0))
                print(f"  ENCONTRADO ({size}b): {angle}.webp")
                found.append((angle, url))
        except urllib.error.HTTPError as e:
            if e.code not in (404, 400):
                print(f"  [{e.code}] {angle}.webp")
        except Exception:
            pass
    return found


def download_sample_images(model_code, color, upholstery):
    """Descarrega imagens de amostra para verificar qualidade."""
    os.makedirs("data/samples", exist_ok=True)
    print(f"\n=== Download de amostras: {model_code} ===")
    angles = ["front", "side", "back"]
    for angle in angles:
        url = f"{CDN}/{model_code}/model/{angle}.webp?F={color}&P={upholstery}&M="
        try:
            data = get_bytes(url)
            if data:
                path = f"data/samples/{model_code}_{angle}.webp"
                with open(path, "wb") as f:
                    f.write(data)
                print(f"  Guardado ({len(data)}b): {path}")
            else:
                print(f"  Vazio: {angle}.webp")
        except Exception as e:
            print(f"  ERRO {angle}: {e}")


def intercept_configurator(model_code, model_group):
    """Usa Playwright para interceptar chamadas API do configurador."""
    print(f"\n=== Interceptação Playwright: {model_code} ===")

    api_calls = {}
    config_url = f"https://configurador.volkswagen.pt/cc-pt/pt_PT_VW22/V/models/{model_group}/{model_code}"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=True,
        )
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
                    api_calls[url] = data
                    # Mostrar só as que parecem relevantes para config
                    if any(k in url for k in ["color", "wheel", "option", "config", "equipment", "exterior"]):
                        print(f"  [RELEVANTE] {url[:90]}")
                    else:
                        print(f"  [API] {url[:90]}")
                except Exception:
                    pass

        page.on("response", on_response)

        try:
            print(f"  A navegar para: {config_url}")
            page.goto(config_url, wait_until="load", timeout=45000)
            # Aguardar conteúdo dinâmico carregar
            time.sleep(8)

            page.screenshot(path="data/golf_config.png", full_page=False)
            print("  Screenshot: data/golf_config.png")

        except Exception as e:
            print(f"  Aviso: {e}")

        browser.close()

    # Guardar todas as chamadas API
    with open("data/golf_api_calls.json", "w", encoding="utf-8") as f:
        json.dump(api_calls, f, ensure_ascii=False, indent=2)
    print(f"\n  {len(api_calls)} chamadas API → data/golf_api_calls.json")

    # Analisar para cores e jantes
    print("\n  Análise das respostas API:")
    for url, data in api_calls.items():
        if isinstance(data, dict):
            keys = list(data.keys())
            if any(k in str(keys).lower() for k in ["color", "colour", "cor", "wheel", "rim", "jante", "option", "exterior"]):
                print(f"\n  URL: {url}")
                print(f"  Keys: {keys}")
                print(f"  Preview: {json.dumps(data, ensure_ascii=False)[:500]}")
        elif isinstance(data, list) and data:
            sample = data[0]
            if isinstance(sample, dict):
                keys = list(sample.keys())
                if any(k in str(keys).lower() for k in ["color", "colour", "cor", "wheel", "rim", "option"]):
                    print(f"\n  URL: {url}")
                    print(f"  Lista com {len(data)} items, keys: {keys}")
                    print(f"  Preview: {json.dumps(data[:2], ensure_ascii=False)[:500]}")

    return api_calls


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    # 1. Testar mais ângulos de imagem
    found_angles = test_more_angles(GOLF_MODEL_CODE, GOLF_DEFAULT_COLOR, GOLF_DEFAULT_UPHOLSTERY)

    # 2. Descarregar amostras das imagens existentes
    download_sample_images(GOLF_MODEL_CODE, GOLF_DEFAULT_COLOR, GOLF_DEFAULT_UPHOLSTERY)

    # 3. Interceptar configurador para encontrar API de cores/jantes
    api_calls = intercept_configurator(GOLF_MODEL_CODE, GOLF_MODEL_GROUP)

    print("\n=== Sumário ===")
    print(f"Ângulos encontrados: {[a for a, _ in found_angles]}")
    print(f"APIs interceptadas: {len(api_calls)}")
