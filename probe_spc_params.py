"""Tenta spc-api com vários parâmetros para encontrar o endpoint de cores/modelos."""
import ssl, urllib.request, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
base_h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://store.peugeot.pt/",
    "x-channel": "b2c",
    "x-brand": "peugeot",
    "x-market": "pt",
    "x-locale": "pt",
}

attempts = [
    ("GET", "https://store.peugeot.pt/spc-api/mto/offers?channel=b2c", None),
    ("GET", "https://store.peugeot.pt/spc-api/offers?type=mto&channel=b2c", None),
    ("GET", "https://store.peugeot.pt/spc-api/stock/offers?channel=b2c", None),
    ("GET", "https://store.peugeot.pt/spc-api/catalog/models?channel=b2c", None),
    ("GET", "https://store.peugeot.pt/spc-api/catalog/colours?channel=b2c", None),
    ("GET", "https://store.peugeot.pt/api/core/offers?channel=b2c&brand=peugeot&market=pt", None),
    # GraphQL
    ("POST", "https://store.peugeot.pt/api/graphql", json.dumps({
        "query": "{ mtoOffers { offers { externalId exteriorColour { id title } model { id title } } } }"
    }).encode()),
    ("POST", "https://store.peugeot.pt/spc-api/graphql", json.dumps({
        "query": "{ models { id name colours { id name } } }"
    }).encode()),
]

for method, url, body in attempts:
    h = dict(base_h)
    if body:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = r.read()
            ct = r.headers.get("content-type", "")
            print(f"OK {r.status} {len(data)}B | {method} {url[:80]}")
            if data[:1] in (b"{", b"["):
                parsed = json.loads(data)
                print("  ", json.dumps(parsed, ensure_ascii=False)[:300])
    except Exception as e:
        print(f"ERRO: {str(e)[:60]} | {method} {url[:80]}")
