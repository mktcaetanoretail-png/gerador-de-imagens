"""Tenta introspeção GraphQL a partir do contexto da página."""
import json, time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    page = ctx.new_page()

    page.goto("https://store.peugeot.pt/stock?channel=b2c", wait_until="networkidle", timeout=40000)
    time.sleep(3)

    def gql(query_str):
        result = page.evaluate(f"""
        async () => {{
            const resp = await fetch('/api/graphql', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{query: {json.dumps(query_str)}}}),
            }});
            return resp.json();
        }}
        """)
        return result

    # 1. Introspeccionar tipos disponíveis
    print("=== Tipos de Query disponíveis ===")
    r = gql("{ __schema { queryType { fields { name args { name type { name kind ofType { name kind } } } } } } }")
    if "errors" not in r:
        fields = r.get("data", {}).get("__schema", {}).get("queryType", {}).get("fields", [])
        for f in fields:
            args = f.get("args", [])
            arg_str = ", ".join(
                f"{a['name']}: {a.get('type',{}).get('name') or a.get('type',{}).get('ofType',{}).get('name','?')}"
                for a in args
            )
            print(f"  {f['name']}({arg_str})")
    else:
        print(f"  ERRO: {r['errors'][0]['message'][:100]}")

    # 2. Tentar getDealerStockOffers com argumentos descobertos
    print("\n=== getDealerStockOffers — todos os args ===")
    r2 = gql("{ __type(name: \"Query\") { fields { name args { name type { name kind ofType { name } } } } } }")
    if "errors" not in r2:
        fields = r2.get("data", {}).get("__type", {}).get("fields", [])
        for f in fields:
            if "stock" in f["name"].lower() or "offer" in f["name"].lower():
                args = f.get("args", [])
                arg_str = [f"{a['name']}: {a.get('type',{}).get('name') or a.get('type',{}).get('ofType',{}).get('name','?')}" for a in args]
                print(f"  {f['name']}({', '.join(arg_str)})")

    browser.close()
