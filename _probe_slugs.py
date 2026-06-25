"""Testa slugs prováveis para modelos Peugeot não encontrados na API."""
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
H_IMG = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "image/webp,image/*,*/*",
    "Referer": "https://store.peugeot.pt/",
}

def gql(q):
    body = json.dumps({"query": q}).encode()
    req = urllib.request.Request("https://store.peugeot.pt/api/graphql", data=body, headers=H, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return json.load(r)

# Usar Playwright para ver __NEXT_DATA__ do stock page
print("=== 1. Tentar getStockOffersByModel ===")
slugs_candidates = [
    "e-208-5-portas", "novo-e-208", "e208-5-portas", "208-e",
    "e-2008-suv", "novo-e-2008", "e2008-suv",
    "novo-e-3008", "e-3008-suv", "e3008-suv",
    "novo-e-5008", "e-5008-suv", "e5008-suv",
    "508-berlina", "novo-508", "508-sw",
    "rifter", "partner", "traveller",
    "508-fastback", "e-208", "e-2008",
]

# Verificar via V3D se existe um modelo com esse slug
# Tentativa: testar se o V3D tem algum lcdv16 específico para e-208
# Os lcdv16 Peugeot elétricos começam por 1PPXXXX onde XX é o código do modelo
# 208 petrol: 1PP2A5
# e-208 provável: começa diferente (M1 para BEV?)

# Primeiro: ver se a store tem uma página de stock com e-208
print("\n=== 2. Verificar Next.js __NEXT_DATA__ da página stock ===")
import urllib.request
urls_to_check = [
    "https://store.peugeot.pt/_next/data/builds/pt/stock.json?channel=b2c",
    "https://store.peugeot.pt/api/models",
    "https://store.peugeot.pt/api/nameplates",
]
for url in urls_to_check:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://store.peugeot.pt/",
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = r.read()
            print(f"  {url}: {r.status} — {len(data)}B")
            if len(data) < 5000:
                print(f"    {data[:500]}")
    except Exception as e:
        print(f"  {url}: {e}")

# Tentar API de configuração por slug directamente
print("\n=== 3. Tentar getConfigurableOffersBySlug ===")
test_slugs = ["e-208-5-portas", "novo-e-208", "e-208", "508-berlina"]
for slug in test_slugs:
    q = f'{{ getConfigurableOffers(nameplateBodyStyleSlug: "{slug}") {{ offers {{ lcdv16 trim {{ id }} exteriorColour {{ id title }} }} }} }}'
    try:
        d = gql(q)
        if "errors" not in d:
            offers = d.get("data", {}).get("getConfigurableOffers", {}).get("offers", [])
            print(f"  {slug}: {len(offers)} offers")
        else:
            print(f"  {slug}: {d['errors'][0]['message'][:60]}")
    except Exception as e:
        print(f"  {slug}: {e}")
