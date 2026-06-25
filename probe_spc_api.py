"""Probe Peugeot spc-api endpoints."""
import ssl, urllib.request, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://store.peugeot.pt/"}

endpoints = [
    "https://store.peugeot.pt/spc-api/cms-content/settings",
    "https://store.peugeot.pt/spc-api/vehicles",
    "https://store.peugeot.pt/spc-api/offers",
    "https://store.peugeot.pt/spc-api/catalog",
    "https://store.peugeot.pt/spc-api/models",
    "https://store.peugeot.pt/spc-api/stock",
    "https://store.peugeot.pt/spc-api/mto-offers",
    "https://store.peugeot.pt/spc-api/configurations",
    "https://store.peugeot.pt/spc-api/colours",
    "https://store.peugeot.pt/spc-api/colors",
]

for url in endpoints:
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
            data = r.read()
            ct = r.headers.get("content-type", "")
            print(f"OK {r.status} {len(data)}B {ct[:30]} | {url}")
            if data[:1] in (b"{", b"["):
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    print("  keys:", list(parsed.keys())[:8])
                elif isinstance(parsed, list):
                    print("  list len:", len(parsed))
    except Exception as e:
        print(f"ERRO: {str(e)[:50]} | {url}")
