"""Tenta endpoints GraphQL do Peugeot store com headers correctos."""
import ssl, urllib.request, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Headers que a página usa
session_h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36",
    "Accept": "application/json, */*",
    "Accept-Language": "pt-PT,pt;q=0.9",
    "Content-Type": "application/json",
    "Referer": "https://store.peugeot.pt/stock?channel=b2c",
    "Origin": "https://store.peugeot.pt",
    "x-nextjs-data": "1",
}

# Introspection query para descobrir o schema
introspection = json.dumps({
    "query": "{ __schema { queryType { fields { name args { name type { name } } } } } }",
    "variables": {},
}).encode()

# Query para buscar stock offers
stock_query = json.dumps({
    "query": """query GetStock($market: String!, $brand: String!, $channel: String!) {
        stockOffers(market: $market, brand: $brand, channel: $channel, limit: 50) {
            count
            offers {
                lcdv16
                nameplateBodyStyleSlug
                exteriorColour { id title }
                model { id title }
            }
        }
    }""",
    "variables": {"market": "pt", "brand": "peugeot", "channel": "b2c"},
}).encode()

endpoints = [
    "https://store.peugeot.pt/spc-api/graphql",
    "https://store.peugeot.pt/api/graphql",
    "https://store.peugeot.pt/api/core/graphql",
    "https://store.peugeot.pt/api/core/offers-service/graphql",
    "https://store.peugeot.pt/api/core/catalog-service/graphql",
    "https://store.peugeot.pt/api/core/stock-service/graphql",
]

for url in endpoints:
    for body_label, body in [("introspection", introspection), ("stock_query", stock_query)]:
        req = urllib.request.Request(url, data=body, headers=session_h, method="POST")
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
                data = r.read()
                print(f"OK {r.status} {len(data)}B | {url} | {body_label}")
                print(" ", data[:400].decode("utf-8", errors="replace"))
        except Exception as e:
            if "400" in str(e):
                # 400 = endpoint existe mas query errada
                pass
            else:
                print(f"ERRO {str(e)[:50]} | {url} | {body_label}")
        break  # Só testar introspection por enquanto
