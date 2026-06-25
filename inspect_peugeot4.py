"""Inspecciona todos os offers da nova estrutura e os campos de cor."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "peugeot_nd_fresh.json", encoding="utf-8") as f:
    nd = json.load(f)

pp = nd["props"]["pageProps"]
offers = pp["mtoOffers"]["offers"]

print(f"Total offers: {len(offers)}\n")

for o in offers:
    ext = o.get("exteriorColour") or {}
    int_ = o.get("interiorColour") or {}
    model = o.get("model") or {}
    body = o.get("bodyStyle") or {}
    print(f"externalId: {o['externalId']}")
    print(f"  lcdv16: {o['lcdv16']}")
    print(f"  slug: {o.get('nameplateBodyStyleSlug')}")
    print(f"  model: {model}")
    print(f"  bodyStyle: {body}")
    print(f"  exteriorColour: {ext}")
    print(f"  interiorColour: {int_}")
    print(f"  trim: {o.get('trim')}")
    print(f"  custom: {o.get('custom')}")
    print()

# Ver o custom dict em detalhe (provavelmente tem mais info)
print("=== custom do primeiro offer ===")
c = offers[0].get("custom", {})
for k, v in c.items():
    print(f"  {k}: {str(v)[:300]}")
