"""Usa o GraphQL da Peugeot store para obter todos os modelos e cores."""
import ssl, urllib.request, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Referer": "https://store.peugeot.pt/stock?channel=b2c",
    "Origin": "https://store.peugeot.pt",
}
GQL = "https://store.peugeot.pt/api/graphql"

def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(GQL, data=body, headers=h, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return json.load(r)

# 1. Verificar que o GraphQL funciona
print("=== Ping ===")
ping = gql("{ __typename }")
print("OK:", ping)

# Tentar os nomes correctos
for query_name in ["getMtoOffers", "getHotOffers", "getOffers"]:
    print(f"\n=== {query_name} ===")
    try:
        res = gql(f"""
        {{
            {query_name} {{
                count
                offers {{
                    externalId
                    lcdv16
                    nameplateBodyStyleSlug
                    model {{ id title }}
                    exteriorColour {{ id title }}
                    trim {{ id title }}
                }}
            }}
        }}
        """)
        data = res.get("data", {})
        block = data.get(query_name, {}) or {}
        offers = block.get("offers", [])
        print(f"count={block.get('count')}, loaded={len(offers)}")
        for o in offers[:5]:
            ext = o.get("exteriorColour") or {}
            trim = o.get("trim") or {}
            print(f"  {o.get('nameplateBodyStyleSlug')} | {ext.get('title')} ({ext.get('id')}) | trim={trim.get('id')} | lcdv16={o.get('lcdv16')}")
    except Exception as e:
        err_body = e.read() if hasattr(e, "read") else b""
        print(f"ERRO: {e} | {err_body[:200]}")

# getStockOffer (singular - por ID)
print("\n=== getStockOffer (sem args) ===")
try:
    res = gql("{ getStockOffer { lcdv16 nameplateBodyStyleSlug exteriorColour { id title } } }")
    print(res.get("data"))
except Exception as e:
    err_body = e.read() if hasattr(e, "read") else b""
    print(f"ERRO: {e} | {err_body[:300]}")
