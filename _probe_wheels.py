"""Verifica se o GraphQL Peugeot tem campos de jantes e se o V3D aceita parâmetro de roda."""
import ssl, urllib.request, json, urllib.request

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

# 1. Tentar alloyWheels
print("=== alloyWheels field ===")
q = """{ getHotOffers { offers {
    nameplateBodyStyleSlug
    alloyWheels { id title }
    trim { id title }
} } }"""
try:
    d = gql(q)
    if "errors" in d:
        print("ERRO:", d["errors"][0]["message"])
    else:
        offers = d["data"]["getHotOffers"]["offers"]
        for o in offers[:5]:
            slug = o.get("nameplateBodyStyleSlug", "")
            trim = (o.get("trim") or {}).get("id", "")
            wheels = o.get("alloyWheels") or {}
            print(f"  {slug} | trim={trim} | wheels={wheels}")
except Exception as e:
    print("ERRO:", e)

# 2. Tentar wheels (alternativa)
print("\n=== wheels field ===")
q2 = """{ getHotOffers { offers {
    nameplateBodyStyleSlug
    wheels { id title }
} } }"""
try:
    d2 = gql(q2)
    if "errors" in d2:
        print("ERRO:", d2["errors"][0]["message"])
    else:
        for o in d2["data"]["getHotOffers"]["offers"][:3]:
            print(f"  {o.get('nameplateBodyStyleSlug')} | wheels={o.get('wheels')}")
except Exception as e:
    print("ERRO:", e)

# 3. Verificar campo custom para info de jantes num offer
print("\n=== custom field — 208 offer ===")
q3 = """{ getHotOffers { offers {
    nameplateBodyStyleSlug
    trim { id }
    custom
    externalId
} } }"""
try:
    d3 = gql(q3)
    for o in d3["data"]["getHotOffers"]["offers"]:
        if o.get("nameplateBodyStyleSlug") == "208-5-portas":
            print(f"  externalId={o.get('externalId')}")
            custom = o.get("custom") or {}
            if isinstance(custom, dict):
                for k, v in custom.items():
                    print(f"    {k}: {v}")
            break
except Exception as e:
    print("ERRO:", e)

# 4. Testar V3D com parâmetro de rims (wheel)
print("\n=== V3D com parâmetro rim/wheel ===")
base = "https://visuel3d-secure.peugeot.com/V3DImage.ashx?client=SOLVCG&ratio=1&format=jpg&quality=90&width=400&height=220&back=0&view=006&mkt=PT"
version = "1PP2A5HJLKB02PH2"
color = "0MM00NEQ"
trim = "0PG90RFX"

for extra_param in ["", "&wheel=1", "&rim=1", "&jante=1", "&options=rim"]:
    url = f"{base}&version={version}&color={color}&trim={trim}{extra_param}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            size = len(r.read())
            print(f"  {extra_param or '(base)'}: {r.status} {size} bytes")
    except Exception as e:
        print(f"  {extra_param or '(base)'}: ERRO {e}")
