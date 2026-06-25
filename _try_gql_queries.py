"""Testa mais queries GraphQL para encontrar modelos elétricos."""
import ssl, urllib.request, json

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

# Tentar queries com filtro de energia eléctrica
tests = [
    ('getHotOffers electric', '{ getHotOffers(energy: "Electric") { offers { nameplateBodyStyleSlug model { title } lcdv16 trim { id } exteriorColour { id title } externalId } } }'),
    ('getHotOffers elétrico', '{ getHotOffers(energy: "Elétrico") { offers { nameplateBodyStyleSlug model { title } lcdv16 } } }'),
    ('getHotOffers fuel BEV', '{ getHotOffers(fuel: "BEV") { offers { nameplateBodyStyleSlug model { title } lcdv16 } } }'),
    ('getMtoOffers electric', '{ getMtoOffers(energy: "Electric") { offers { nameplateBodyStyleSlug model { title } lcdv16 trim { id } externalId } } }'),
    ('getStockOffers', '{ getStockOffers { offers { nameplateBodyStyleSlug model { title } lcdv16 exteriorColour { id title } } } }'),
    ('getAllOffers', '{ getAllOffers { offers { nameplateBodyStyleSlug model { title } lcdv16 } } }'),
    ('getEVOffers', '{ getEVOffers { offers { nameplateBodyStyleSlug model { title } lcdv16 } } }'),
    ('getNameplates', '{ getNameplates { id title slug } }'),
    ('nameplates', '{ nameplates { id title slug nameplateBodyStyleSlug } }'),
    ('models', '{ models { id title slug } }'),
]

for label, q in tests:
    try:
        d = gql(q)
        if "errors" in d:
            err = d["errors"][0].get("message", "?")[:50]
            print(f"  {label}: ERRO — {err}")
            continue
        # Tentar extrair dados úteis
        data = d.get("data", {})
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  {label} [{k}]: {len(v)} itens — {str(v[:2])[:100]}")
            elif isinstance(v, dict) and "offers" in v:
                offers = v["offers"]
                slugs = {o.get("nameplateBodyStyleSlug","") for o in offers}
                print(f"  {label} [{k}]: {len(offers)} offers — {sorted(slugs)}")
            else:
                print(f"  {label} [{k}]: {str(v)[:100]}")
    except Exception as e:
        print(f"  {label}: {str(e)[:80]}")
