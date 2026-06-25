"""
Constrói o catálogo Peugeot via GraphQL (getHotOffers + getMtoOffers).
Agrupa por modelo e recolhe todas as combinações únicas de cor.
"""
import ssl, urllib.request, json
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

GQL = "https://store.peugeot.pt/api/graphql"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Referer": "https://store.peugeot.pt/stock?channel=b2c",
    "Origin": "https://store.peugeot.pt",
}
_V3D_COLORS = "https://visuel3d-secure.peugeot.com/v3dcentral/Colors/NDP/th_{}.png"
_V3D_TRIMS  = "https://visuel3d-secure.peugeot.com/v3dcentral/Trims/ndp/th_{}.png"


def gql(query):
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(GQL, data=body, headers=H, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return json.load(r)


def fetch_all_offers():
    """Recolhe getHotOffers + getMtoOffers."""
    all_offers = []

    # getMtoOffers
    res = gql("""
    {
        getMtoOffers {
            offers {
                externalId
                lcdv16
                nameplateBodyStyleSlug
                model { id title }
                bodyStyle { id title }
                exteriorColour { id title }
                trim { id title }
                custom
            }
        }
    }
    """)
    offers = res["data"]["getMtoOffers"]["offers"]
    for o in offers:
        o["_source"] = "mto"
    all_offers.extend(offers)
    print(f"getMtoOffers: {len(offers)}")

    # getHotOffers
    res = gql("""
    {
        getHotOffers {
            offers {
                externalId
                lcdv16
                nameplateBodyStyleSlug
                model { id title }
                bodyStyle { id title }
                exteriorColour { id title }
                trim { id title }
                custom
            }
        }
    }
    """)
    offers = res["data"]["getHotOffers"]["offers"]
    for o in offers:
        o["_source"] = "hot"
    all_offers.extend(offers)
    print(f"getHotOffers: {len(offers)}")

    return all_offers


def build_catalog(offers):
    models = {}

    for o in offers:
        ext_id = o.get("externalId", "")
        parts = ext_id.split("+") if ext_id else []
        version  = parts[0] if len(parts) > 0 else o.get("lcdv16", "")
        color_id = parts[1] if len(parts) > 1 else (o.get("exteriorColour") or {}).get("id", "")
        trim_id  = parts[2] if len(parts) > 2 else ""

        slug = o.get("nameplateBodyStyleSlug", "")
        model_data = o.get("model") or {}
        body_data  = o.get("bodyStyle") or {}
        ext_data   = o.get("exteriorColour") or {}
        trim_data  = o.get("trim") or {}
        custom     = o.get("custom") or {}

        model_title = model_data.get("title", "")
        body_title  = body_data.get("title", "")
        show_body   = custom.get("showExtendedBodyStyleLabel", False)
        model_label = f"{model_title} {body_title}".strip() if show_body else model_title

        color_name = ext_data.get("title", color_id)
        trim_name  = trim_data.get("title", trim_id)

        if not slug:
            continue

        if slug not in models:
            models[slug] = {
                "modelId": slug,
                "modelName": model_label or slug,
                "colors": {},
            }

        # Agrupar por cor única — guardar apenas 1 versão representativa por cor
        if color_id and color_id not in models[slug]["colors"]:
            models[slug]["colors"][color_id] = {
                "version": version,
                "color": {
                    "id": color_id,
                    "name": color_name,
                    "swatchUrl": _V3D_COLORS.format(color_id) if color_id else "",
                },
                "trim": {
                    "id": trim_id,
                    "name": trim_name,
                    "swatchUrl": _V3D_TRIMS.format(trim_id) if trim_id else "",
                },
            }

    # Converter para lista
    result_models = []
    for slug, data in models.items():
        colors_list = list(data["colors"].values())
        offers = [
            {
                "offerId": f"{c['version']}+{c['color']['id']}+{c['trim']['id']}",
                "offerTitle": f"{data['modelName']} — {c['color']['name']}",
                "version": c["version"],
                "slug": slug,
                "color": c["color"],
                "trim": c["trim"],
            }
            for c in colors_list
            if c["color"]["id"]
        ]
        if offers:
            result_models.append({
                "modelId": slug,
                "modelName": data["modelName"],
                "offers": offers,
            })

    return {"models": result_models}


if __name__ == "__main__":
    print("A recolher dados via GraphQL...")
    offers = fetch_all_offers()
    catalog = build_catalog(offers)

    print(f"\nTotal modelos: {len(catalog['models'])}")
    for m in catalog["models"]:
        print(f"\n  {m['modelName']} ({m['modelId']}) — {len(m['offers'])} cores")
        for o in m["offers"]:
            print(f"    {o['color']['name']} ({o['color']['id']}) trim={o['trim']['id']} ver={o['version']}")

    out = Path(__file__).parent.parent / "data" / "peugeot_catalog.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado em: {out}")
