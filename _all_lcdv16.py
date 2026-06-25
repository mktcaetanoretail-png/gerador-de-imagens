"""Lista todos os lcdv16 únicos por modelo de todos os sources."""
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

by_slug = defaultdict(lambda: {"lcdvs": {}, "exids": []})

for qname in ["getHotOffers", "getMtoOffers", "getDealerStockOffers"]:
    q = f"""{{ {qname} {{ offers {{
        nameplateBodyStyleSlug lcdv16 externalId
        model {{ title }} trim {{ id title }}
        custom
    }} }} }}"""
    try:
        d = gql(q)
        offers = d.get("data", {}).get(qname, {}).get("offers", [])
        for o in offers:
            slug = o.get("nameplateBodyStyleSlug", "")
            lcdv = o.get("lcdv16", "")
            exid = o.get("externalId", "")
            trim = (o.get("trim") or {}).get("id", "")
            custom = o.get("custom") or {}
            fuel = custom.get("energyLabel", "") if isinstance(custom, dict) else ""
            if slug and lcdv:
                if lcdv not in by_slug[slug]["lcdvs"]:
                    by_slug[slug]["lcdvs"][lcdv] = {"trim": trim, "fuel": fuel, "source": qname}
                    if exid:
                        by_slug[slug]["exids"].append(exid)
    except Exception as e:
        print(f"{qname}: ERRO {e}")

print("Todos os lcdv16 por modelo:\n")
for slug, data in sorted(by_slug.items()):
    print(f"  {slug}: {len(data['lcdvs'])} variantes lcdv16")
    for lcdv, info in sorted(data["lcdvs"].items()):
        fuel_str = f" [{info['fuel']}]" if info["fuel"] else ""
        print(f"    {lcdv} — trim={info['trim'].strip('_') or '?'} src={info['source']}{fuel_str}")
