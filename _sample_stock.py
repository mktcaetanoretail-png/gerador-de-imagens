"""
Chama getDealerStockOffers múltiplas vezes para amostrar diferentes offers
dos 1374 disponíveis e descobrir modelos não visíveis na amostra padrão.
"""
import ssl, urllib.request, json, time
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

Q = """{ getDealerStockOffers {
    offers {
        nameplateBodyStyleSlug
        lcdv16
        externalId
        model { id title }
        bodyStyle { title }
        trim { id title }
        exteriorColour { id title }
        custom
    }
} }"""

all_offers = {}  # externalId → offer
slugs_seen = defaultdict(lambda: {"model": "", "count": 0, "lcdvs": set(), "colors": set(), "exids": []})

print("A amostrar getDealerStockOffers (30 chamadas)...")
for i in range(30):
    try:
        d = gql(Q)
        offers = d.get("data", {}).get("getDealerStockOffers", {}).get("offers", [])
        new_offers = 0
        for o in offers:
            exid = o.get("externalId", "") or o.get("lcdv16", "") + str(i)
            if exid not in all_offers:
                all_offers[exid] = o
                new_offers += 1
            slug = o.get("nameplateBodyStyleSlug", "")
            if slug:
                slugs_seen[slug]["model"] = (o.get("model") or {}).get("title", "")
                slugs_seen[slug]["count"] += 1
                lcdv = o.get("lcdv16", "")
                color = (o.get("exteriorColour") or {}).get("title", "")
                if lcdv: slugs_seen[slug]["lcdvs"].add(lcdv)
                if color: slugs_seen[slug]["colors"].add(color)
                if exid not in slugs_seen[slug]["exids"] and len(slugs_seen[slug]["exids"]) < 5:
                    slugs_seen[slug]["exids"].append(exid)
        if i % 5 == 0:
            print(f"  Iteração {i+1}: {len(all_offers)} offers únicos, {len(slugs_seen)} slugs")
        time.sleep(0.3)
    except Exception as e:
        print(f"  Iteração {i+1}: ERRO {e}")

print(f"\nTotal: {len(all_offers)} offers únicos de {len(slugs_seen)} modelos:\n")
for slug, info in sorted(slugs_seen.items()):
    print(f"  {slug}: {info['model']} ({info['count']} ocorrências)")
    print(f"    lcdv16: {sorted(info['lcdvs'])[:3]}")
    print(f"    cores: {sorted(info['colors'])[:5]}")
    print(f"    exids: {info['exids'][:2]}")
