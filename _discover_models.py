"""Descobre todos os slugs/modelos disponíveis via GraphQL."""
import ssl, urllib.request, json
from collections import defaultdict

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Referer": "https://store.peugeot.pt/stock?channel=b2c",
    "Origin": "https://store.peugeot.pt",
}

def gql(q):
    body = json.dumps({"query": q}).encode()
    req = urllib.request.Request("https://store.peugeot.pt/api/graphql", data=body, headers=H, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return json.load(r)

all_slugs = defaultdict(lambda: {"trims": set(), "colors": set(), "count": 0})

for qname in ["getHotOffers", "getMtoOffers", "getDealerStockOffers"]:
    q = f"""{{
        {qname} {{
            offers {{
                externalId
                lcdv16
                nameplateBodyStyleSlug
                model {{ id title }}
                bodyStyle {{ title }}
                trim {{ id title }}
                exteriorColour {{ id title }}
                custom
            }}
        }}
    }}"""
    try:
        d = gql(q)
        offers = d.get("data", {}).get(qname, {}).get("offers", [])
        for o in offers:
            slug = o.get("nameplateBodyStyleSlug", "")
            if not slug:
                continue
            model = o.get("model") or {}
            body = o.get("bodyStyle") or {}
            trim = o.get("trim") or {}
            ext = o.get("exteriorColour") or {}
            custom = o.get("custom") or {}
            show_body = custom.get("showExtendedBodyStyleLabel", False) if isinstance(custom, dict) else False
            label = f"{model.get('title','')} {body.get('title','')}".strip() if show_body else model.get("title","")
            all_slugs[slug]["model"] = label or slug
            all_slugs[slug]["count"] += 1
            if trim.get("id"):
                all_slugs[slug]["trims"].add(trim["id"].strip("_"))
            if ext.get("id"):
                all_slugs[slug]["colors"].add(ext.get("title", ext["id"]))
        print(f"{qname}: {len(offers)} offers")
    except Exception as e:
        print(f"{qname}: ERRO {e}")

print(f"\nTotal slugs únicos: {len(all_slugs)}\n")
for slug, info in sorted(all_slugs.items()):
    trims = ", ".join(sorted(info["trims"])) or "-"
    colors = ", ".join(sorted(info["colors"])) or "-"
    print(f"  {slug}")
    print(f"    Modelo: {info['model']}  |  Offers: {info['count']}")
    print(f"    Trims: {trims}")
    print(f"    Cores: {colors}")
