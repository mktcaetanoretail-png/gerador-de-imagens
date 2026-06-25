"""Inspecciona a estrutura actual do __NEXT_DATA__ Peugeot (nova estrutura pageProps)."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

with open(DATA_DIR / "peugeot_nd_fresh.json", encoding="utf-8") as f:
    nd = json.load(f)

pp = nd["props"]["pageProps"]
mto = pp.get("mtoOffers", {})
stock = pp.get("stockModels", {})

print(f"mtoOffers type: {type(mto).__name__}")
print(f"stockModels type: {type(stock).__name__}")
print()

# Se for dict, ver as keys
if isinstance(mto, dict):
    print(f"mtoOffers keys: {list(mto.keys())[:20]}")
    for k, v in list(mto.items())[:3]:
        print(f"\n  [{k}]: {type(v).__name__}")
        if isinstance(v, (list, dict)):
            print(f"    len={len(v)}")
            item = v[0] if isinstance(v, list) and v else (list(v.values())[0] if isinstance(v, dict) and v else None)
            if isinstance(item, dict):
                for k2, v2 in list(item.items())[:15]:
                    t = type(v2).__name__
                    extra = f" ({len(v2)} items)" if isinstance(v2, (list, dict)) else f" = {str(v2)[:100]}"
                    print(f"    {k2}: {t}{extra}")
        else:
            print(f"    = {str(v)[:200]}")
elif isinstance(mto, list):
    print(f"mtoOffers len: {len(mto)}")
    if mto:
        item = mto[0]
        if isinstance(item, dict):
            for k, v in list(item.items())[:20]:
                t = type(v).__name__
                extra = f" ({len(v)} items)" if isinstance(v, (list, dict)) else f" = {str(v)[:100]}"
                print(f"  {k}: {t}{extra}")

print("\n=== featureFlags ===")
ff = pp.get("featureFlags", {})
if isinstance(ff, dict):
    for k, v in list(ff.items())[:20]:
        print(f"  {k}: {v}")
elif isinstance(ff, list):
    for item in ff[:5]:
        print(f"  {item}")
