"""Busca o modeldetailFull e extrai stageImages, cores e jantes."""
import json
import ssl
import urllib.request
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://configurador.volkswagen.pt/",
}

BASE = "https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22"

# Golf LIFE
MODEL_CODE = "DA13HYA2"
COLOR_CODE = "5K5K"
UPHOLSTERY = "BD"


def get_model_detail(model_code, color_code, upholstery):
    url = f"{BASE}/api/v2/modeldetailFull/V/{model_code}/{color_code}/{upholstery}/@/@"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read())


def main():
    os.makedirs("data", exist_ok=True)

    print(f"A buscar modeldetailFull para {MODEL_CODE}...")
    data = get_model_detail(MODEL_CODE, COLOR_CODE, UPHOLSTERY)

    # 1. stageImages
    print("\n=== stageImages ===")
    stage = data.get("stageImages", {})
    print(f"  Keys: {list(stage.keys())}")

    carousel = stage.get("carouselImages", [])
    print(f"\n  carouselImages ({len(carousel)} items):")
    for i, img in enumerate(carousel):
        print(f"    [{i}] {json.dumps(img, ensure_ascii=False)[:300]}")

    rotation = stage.get("responsiveRotationImages", [])
    print(f"\n  responsiveRotationImages ({len(rotation)} items):")
    for i, img in enumerate(rotation[:8]):
        print(f"    [{i}] {json.dumps(img, ensure_ascii=False)[:300]}")

    sphere = stage.get("sphereViewImage")
    if sphere:
        print(f"\n  sphereViewImage: {sphere}")

    # 2. altTextsByView
    print("\n=== altTextsByView ===")
    alts = data.get("altTextsByView", {})
    for k, v in alts.items():
        print(f"  [{k}]: {v}")

    # 3. imageUrl e variantes
    print("\n=== imageUrls ===")
    for key in ["imageUrl", "pdfImageUrl", "unifiedSmallImageUrl", "exteriorCloseupImageUrl",
                "interiorCloseupImageUrl", "tireCloseupImageUrl", "hdOverviewImageUrl",
                "hdImageUrl", "drivePageImageUrl"]:
        val = data.get(key)
        if val:
            print(f"  {key}: {val}")

    # 4. Cores disponíveis
    print("\n=== availableExteriors ===")
    for ext in data.get("availableExteriors", []):
        code = ext.get("code")
        name = ext.get("bezf", "?")
        price = ext.get("preis", {}).get("brutto", 0)
        img = ext.get("image", "")
        available = not ext.get("notAvailable", False)
        print(f"  {code}: {name} | preco={price} | disponivel={available}")
        print(f"    img: {img}")

    # 5. Jantes disponíveis
    print("\n=== availableWheels ===")
    for w in data.get("availableWheels", []):
        code = w.get("code")
        title = w.get("title", "?")
        serie = w.get("serie", False)
        img = w.get("image", "")
        print(f"  {code}: {title} | serie={serie}")
        print(f"    img: {img}")

    # Guardar dados relevantes
    summary = {
        "modelCode": MODEL_CODE,
        "modelName": data.get("name"),
        "colors": [
            {
                "code": e.get("code"),
                "name": e.get("bezf"),
                "price": e.get("preis", {}).get("brutto", 0),
                "available": not e.get("notAvailable", False),
                "image": e.get("image"),
            }
            for e in data.get("availableExteriors", [])
            if not e.get("notAvailable", False)
        ],
        "wheels": [
            {
                "code": w.get("code"),
                "title": w.get("title"),
                "serie": w.get("serie", False),
                "image": w.get("image"),
            }
            for w in data.get("availableWheels", [])
        ],
        "stageImages": stage,
        "imageUrl": data.get("imageUrl"),
    }
    with open("data/golf_life_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\nGuardado: data/golf_life_summary.json")

    # Teste: buscar a mesma data com uma cor diferente para verificar que as imagens mudam
    print("\n=== Teste com cor diferente (0Q0Q - Preto) ===")
    try:
        data2 = get_model_detail(MODEL_CODE, "0Q0Q", UPHOLSTERY)
        print(f"  imageUrl: {data2.get('imageUrl')}")
        stage2 = data2.get("stageImages", {})
        carousel2 = stage2.get("carouselImages", [])
        print(f"  carouselImages ({len(carousel2)}):")
        for img in carousel2[:3]:
            print(f"    {json.dumps(img, ensure_ascii=False)[:200]}")
    except Exception as e:
        print(f"  Erro: {e}")


if __name__ == "__main__":
    main()
