"""Inspecciona a estrutura do __NEXT_DATA__ Peugeot guardado."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "peugeot_next_data.json", encoding="utf-8") as f:
    d = json.load(f)

state = d.get("configurable", {}).get("props", {}).get("initialState", {})
offers = state.get("OfferList", {}).get("configurable", {}).get("offers", [])

print(f"Total de offers: {len(offers)}")
print()

for o in offers[:3]:
    oid = o.get("_id", "")
    obj = o.get("_properties", {}).get("object", {})
    np_data = obj.get("nameplate", {})
    print(f"ID: {oid}")
    print(f"  nameplate.title: {np_data.get('title')}")
    print(f"  nameplate.id: {np_data.get('id')}")
    for k, v in obj.items():
        if k == "prices":
            continue
        t = type(v).__name__
        extra = f" ({len(v)} items)" if isinstance(v, (list, dict)) else f" = {str(v)[:100]}"
        print(f"  obj.{k}: {t}{extra}")
    print()

# Inspecionar o primeiro offer em detalhe - ver campos com imagens/cores
print("\n=== Primeiro offer — objeto completo (sem prices) ===")
if offers:
    obj = offers[0].get("_properties", {}).get("object", {})

    def dump(d2, prefix="", depth=4):
        if depth == 0:
            return
        if isinstance(d2, dict):
            for k, v in list(d2.items())[:30]:
                extra = f" ({len(v)} items)" if isinstance(v, (list, dict)) else f" = {str(v)[:120]}"
                print(f"{prefix}{k}: {type(v).__name__}{extra}")
                if k not in ("prices", "monthlyPrices", "translations"):
                    dump(v, prefix + "  ", depth - 1)
        elif isinstance(d2, list) and d2:
            print(f"{prefix}[0]: {type(d2[0]).__name__}")
            dump(d2[0], prefix + "  ", depth - 1)

    dump(obj)
