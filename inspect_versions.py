"""Inspecciona as versoes/trims disponíveis por modelo via getHotOffers."""
import ssl, urllib.request, json, collections

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
H = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Referer": "https://store.peugeot.pt/",
    "Origin": "https://store.peugeot.pt",
}

def gql(query):
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request("https://store.peugeot.pt/api/graphql", data=body, headers=H, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return json.load(r)

res = gql("""
{
    getHotOffers {
        offers {
            externalId
            lcdv16
            nameplateBodyStyleSlug
            model { id title }
            bodyStyle { title }
            trim { id title }
            exteriorColour { id title }
        }
    }
}
""")

offers = res["data"]["getHotOffers"]["offers"]
print(f"Total hot offers: {len(offers)}\n")

by_model = collections.defaultdict(list)
for o in offers:
    slug = o.get("nameplateBodyStyleSlug", "")
    by_model[slug].append(o)

for slug, model_offers in sorted(by_model.items()):
    print(f"\n=== {slug} ({len(model_offers)} versoes) ===")
    # Agrupar por trim
    by_trim = collections.defaultdict(list)
    for o in model_offers:
        trim = o.get("trim") or {}
        by_trim[trim.get("id", "")].append(o)

    for trim_id, trim_offers in by_trim.items():
        o = trim_offers[0]
        trim = o.get("trim") or {}
        engine = o.get("engine") or {}
        gearbox = o.get("gearbox") or {}
        ext = o.get("exteriorColour") or {}
        parts = (o.get("externalId") or "").split("+")
        version = parts[0] if parts else o.get("lcdv16", "")
        trim_id_clean = trim.get("id", "").strip("_")
        trim_name = trim.get("title", trim_id_clean).strip("_") or trim_id_clean
        print(f"  [{trim_name}] trim_id={trim.get('id','')} | ver={version} | cor={ext.get('title')} | {len(trim_offers)} vars")
