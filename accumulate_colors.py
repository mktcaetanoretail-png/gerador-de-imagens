"""
Faz múltiplos pedidos a getDealerStockOffers para acumular cores únicas.
Tenta também descobrir argumentos válidos.
"""
import ssl, urllib.request, json, time, collections

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
GQL = "https://store.peugeot.pt/api/graphql"

def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(GQL, data=body, headers=H, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:600]}

FIELDS = """lcdv16 nameplateBodyStyleSlug model { id title } exteriorColour { id title }"""

# 1. Testar argumentos possíveis para getDealerStockOffers
print("=== Argumentos válidos de getDealerStockOffers ===")
for arg in ["(nameplateSlug: \"208-5-portas\")", "(modelSlug: \"208-5-portas\")", "(slug: \"208\")",
            "(color: \"0MM00NEQ\")", "(random: true)", "(seed: 42)", "(sort: \"colour\")"]:
    q = f"{{ getDealerStockOffers{arg} {{ count }} }}"
    res = gql(q)
    if "error" in res:
        body = res["body"]
        if "Unknown argument" in body:
            arg_name = arg.strip("()")
            print(f"  {arg}: argumento inválido")
        else:
            print(f"  {arg}: ERRO {body[:100]}")
    else:
        data = (res.get("data") or {}).get("getDealerStockOffers") or {}
        print(f"  {arg}: OK count={data.get('count')}")

# 2. Fazer 10 pedidos consecutivos para acumular cores
print("\n=== Acumulando cores de 10 pedidos ===")
all_colors = collections.defaultdict(dict)  # slug -> {colorId -> {name, lcdv16}}
q = f"{{ getDealerStockOffers {{ count offers {{ {FIELDS} }} }} }}"

for i in range(15):
    res = gql(q)
    if "error" in res:
        print(f"  Pedido {i+1}: ERRO")
        break
    data = (res.get("data") or {}).get("getDealerStockOffers") or {}
    offers = data.get("offers", [])
    new = 0
    for o in offers:
        slug = o.get("nameplateBodyStyleSlug", "")
        ext = o.get("exteriorColour") or {}
        cid = ext.get("id", "")
        cname = ext.get("title", "")
        lcdv = o.get("lcdv16", "")
        if slug and cid and cid not in all_colors[slug]:
            all_colors[slug][cid] = {"name": cname, "lcdv16": lcdv}
            new += 1
    total = sum(len(v) for v in all_colors.values())
    print(f"  Pedido {i+1}: +{new} novas | total_cores={total}")
    if new == 0:
        print("  (sem novas cores)")
    time.sleep(0.5)

print("\n=== Resultado Final ===")
for slug, colors in sorted(all_colors.items()):
    print(f"\n{slug}: {len(colors)} cores")
    for cid, cdata in colors.items():
        print(f"  {cdata['name']} ({cid}) | lcdv16={cdata['lcdv16']}")
