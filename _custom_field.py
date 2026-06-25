"""Mostra engine title para todos os modelos e detecta padrão EV."""
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

q = """{ getHotOffers { offers {
    nameplateBodyStyleSlug model { title } lcdv16
    trim { id }
    engine { title }
    externalId
} } }"""

d = gql(q)
offers = d.get("data", {}).get("getHotOffers", {}).get("offers", [])

by_slug = defaultdict(list)
for o in offers:
    by_slug[o.get("nameplateBodyStyleSlug","")].append(o)

for slug, slug_offers in sorted(by_slug.items()):
    print(f"\n=== {slug} ===")
    for o in slug_offers:
        trim = (o.get("trim") or {}).get("id", "").strip("_")
        engine = (o.get("engine") or {}).get("title", "?")
        lcdv = o.get("lcdv16","")
        exid = o.get("externalId","")
        is_ev = "léctrico" in engine or "Electric" in engine
        marker = " [EV]" if is_ev else ""
        print(f"  {trim:10} {engine}{marker}")
        print(f"    lcdv={lcdv}")
        parts = exid.split("+") if exid else []
        if len(parts) >= 3:
            print(f"    trimCode={parts[2]}")
