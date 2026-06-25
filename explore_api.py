"""Explora os endpoints e padrões de imagem da API VW."""
import json
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://configurador.volkswagen.pt/",
}


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read())


def head(url):
    req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            return r.status, int(r.headers.get("Content-Length", 0))
    except urllib.error.HTTPError as e:
        return e.code, 0


BASE = "https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22"
CDN = "https://cdn.nwi-ms.com/media/pt/V/mc"


def explore_models():
    print("=== Lista de modelos ===")
    data = get_json(f"{BASE}/api/v2/modelgroup?brand=V")
    models = []
    for mg in data.get("modelgroups", []):
        print(f"  {mg['name']} ({mg['code']}) - ano {mg['year']}")
        for v in mg.get("variants", []):
            mc = v.get("cheapestModelCode")
            ps = v.get("preSelection", {})
            print(
                f"    variante: {v['name']} | modelCode={mc} "
                f"| cor={ps.get('standardColorCode')} | upholstery={ps.get('standardUpholsteryCode')}"
            )
            if mc:
                models.append(
                    {
                        "modelGroup": mg["name"],
                        "modelGroupCode": mg["code"],
                        "variant": v["name"],
                        "modelCode": mc,
                        "defaultColor": ps.get("standardColorCode"),
                        "defaultUpholstery": ps.get("standardUpholsteryCode"),
                    }
                )
    return models


def explore_model_config(model_code, color, upholstery):
    """Tenta encontrar endpoint que devolve cores e jantes disponíveis."""
    print(f"\n=== Configuração: {model_code} ===")

    # Tentar endpoints de configuração
    config_endpoints = [
        f"{BASE}/api/v1/models/{model_code}",
        f"{BASE}/api/v2/models/{model_code}",
        f"{BASE}/api/v1/configuration/{model_code}",
        f"https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22/wccarsummary/{model_code}",
        f"https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22/wccarprice/{model_code}",
    ]
    for url in config_endpoints:
        try:
            data = get_json(url)
            print(f"  OK: {url}")
            print(f"  {json.dumps(data, ensure_ascii=False)[:300]}")
        except Exception as e:
            print(f"  ERRO {url.split('/')[-1]}: {str(e)[:60]}")


def explore_image_urls(model_code, color, upholstery):
    """Testa padrões de URL de imagem para diferentes ângulos."""
    print(f"\n=== Imagens: {model_code} cor={color} ===")

    # Padrões de ângulo a testar
    angle_variants = [
        "default", "front", "rear", "side",
        "34front", "3-4-front", "3_4_front", "34_front",
        "back", "angle", "top", "quarter",
        "exterior_front", "exterior_side", "exterior_rear",
    ]
    # Formatos de imagem
    formats = ["webp", "jpg", "png"]

    found = []
    for angle in angle_variants:
        for fmt in ["webp"]:
            url = f"{CDN}/{model_code}/model/{angle}.{fmt}?F={color}&P={upholstery}&M="
            status, size = head(url)
            if status == 200:
                print(f"  ENCONTRADO ({size}b): model/{angle}.{fmt}")
                found.append(url)
            elif status not in (404, 400):
                print(f"  [{status}] model/{angle}.{fmt}")

    # Testar sem parâmetros de cor
    for angle in ["default", "front", "rear", "side", "34front"]:
        url = f"{CDN}/{model_code}/model/{angle}.webp"
        status, size = head(url)
        if status == 200:
            print(f"  ENCONTRADO sem cor ({size}b): {url}")
            found.append(url)

    return found


def explore_colors_wheels_api(model_code):
    """Tenta encontrar API que lista cores e jantes disponíveis para o modelo."""
    print(f"\n=== API de cores/jantes para {model_code} ===")

    endpoints = [
        f"https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22/wccarsummary/V/{model_code}",
        f"https://api.productdata.volkswagenag.com/v3/catalog/pt/models",
        f"https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22/wccaroptions/{model_code}",
        f"https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22/wccardetails/V/{model_code}",
    ]
    for url in endpoints:
        try:
            data = get_json(url)
            print(f"  OK: {url}")
            print(f"  keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            print(f"  {json.dumps(data, ensure_ascii=False)[:400]}")
        except Exception as e:
            print(f"  ERRO: {url.split('/')[-2:]}: {str(e)[:80]}")


if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)

    models = explore_models()
    # Guardar lista de modelos
    with open("data/vw_models_raw.json", "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)
    print(f"\nTotal de variantes: {len(models)}")

    if models:
        first = models[0]
        mc = first["modelCode"]
        color = first["defaultColor"]
        upholstery = first["defaultUpholstery"]

        explore_model_config(mc, color, upholstery)
        explore_colors_wheels_api(mc)
        found_urls = explore_image_urls(mc, color, upholstery)

        if found_urls:
            print(f"\nURLs de imagem encontradas:")
            for u in found_urls:
                print(f"  {u}")
