"""
Extrai o catálogo Volkswagen Portugal: modelos, cores e jantes.
Usa a API pública do configurador volkswagen.pt.
Cache em data/vw_catalog.json.
"""
import json
import os
import ssl
import urllib.request
from pathlib import Path

BASE = "https://configurador.volkswagen.pt/cc-pt/be/pt_PT_VW22"
CDN = "https://cdn.nwi-ms.com/media/pt/V/mc"
DATA_FILE = Path(__file__).parent.parent / "data" / "vw_catalog.json"

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://configurador.volkswagen.pt/",
}


def _get(url: str) -> dict | list:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, context=_ssl_ctx, timeout=20) as r:
        return json.loads(r.read())


def _get_model_detail(model_code: str, color: str, upholstery: str) -> dict:
    url = f"{BASE}/api/v2/modeldetailFull/V/{model_code}/{color}/{upholstery}/@/@"
    return _get(url)


def _build_image_url(model_code: str, view: str, color: str, upholstery: str, wheel: str = "") -> str:
    return (
        f"{CDN}/{model_code}/model/{view}.webp"
        f"?F={color}&P={upholstery}&M={wheel}&size=XL"
    )


def build_catalog(force: bool = False) -> dict:
    """
    Constrói e guarda o catálogo VW. Usa cache se existir.
    Devolve dict com estrutura:
    {
        "models": [
            {
                "groupCode": str,
                "groupName": str,
                "variants": [
                    {
                        "modelCode": str,
                        "variantName": str,
                        "name": str,
                        "defaultColor": str,
                        "defaultUpholstery": str,
                        "colors": [{"code", "name", "price", "swatchUrl"}],
                        "wheels": [{"code", "title", "serie", "imageUrl"}],
                    }
                ]
            }
        ]
    }
    """
    if not force and DATA_FILE.exists():
        print(f"Catálogo em cache: {DATA_FILE}")
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)

    print("A construir catálogo VW...")
    DATA_FILE.parent.mkdir(exist_ok=True)

    model_groups_data = _get(f"{BASE}/api/v2/modelgroup?brand=V")
    catalog = {"models": []}

    for mg in model_groups_data.get("modelgroups", []):
        group_code = mg["code"]
        group_name = mg["name"]
        print(f"\n  {group_name} ({group_code})")

        group_entry = {
            "groupCode": group_code,
            "groupName": group_name,
            "pictureUrl": mg.get("pictureURL", ""),
            "variants": [],
        }

        for variant in mg.get("variants", []):
            mc = variant.get("cheapestModelCode")
            if not mc:
                continue

            ps = variant.get("preSelection", {})
            default_color = ps.get("standardColorCode", "")
            default_upholstery = ps.get("standardUpholsteryCode", "")

            print(f"    {variant['name']} ({mc}) cor={default_color}")

            try:
                detail = _get_model_detail(mc, default_color, default_upholstery)
            except Exception as e:
                print(f"    ERRO ao buscar detalhe: {e}")
                continue

            colors = [
                {
                    "code": ext["code"],
                    "name": ext.get("bezf", ext["code"]),
                    "price": ext.get("preis", {}).get("brutto", 0) or 0,
                    "available": not ext.get("notAvailable", False),
                    "swatchUrl": ext.get("image", ""),
                }
                for ext in detail.get("availableExteriors", [])
                if not ext.get("notAvailable", False)
            ]

            wheels = [
                {
                    "code": w["code"],
                    "title": w.get("title", w["code"]),
                    "serie": w.get("serie", False),
                    "imageUrl": w.get("image", ""),
                }
                for w in detail.get("availableWheels", [])
            ]

            variant_entry = {
                "modelCode": mc,
                "variantName": variant["name"],
                "name": detail.get("name", f"{group_name} {variant['name']}"),
                "defaultColor": default_color,
                "defaultUpholstery": default_upholstery,
                "colors": colors,
                "wheels": wheels,
            }
            group_entry["variants"].append(variant_entry)

        catalog["models"].append(group_entry)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"\nCatálogo guardado: {DATA_FILE}")
    return catalog


def load_catalog() -> dict:
    """Devolve o catálogo do cache. Constrói se não existir."""
    return build_catalog(force=False)


def get_image_urls(model_code: str, color: str, upholstery: str, wheel: str = "") -> dict[str, str]:
    """
    Devolve dict com as 4 URLs de imagem para a configuração escolhida.
    views: exteriorfront, front, side, back
    """
    views = {
        "3/4 Frente": "exteriorfront",
        "Frente": "front",
        "Lado": "side",
        "Traseira": "back",
    }
    return {
        label: _build_image_url(model_code, view, color, upholstery, wheel)
        for label, view in views.items()
    }


if __name__ == "__main__":
    catalog = build_catalog(force=True)
    total_models = sum(len(g["variants"]) for g in catalog["models"])
    print(f"\nTotal: {len(catalog['models'])} grupos, {total_models} variantes")
