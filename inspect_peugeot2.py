"""Analisa as URLs de imagem e navega no configurador por modelo."""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA_DIR = Path(__file__).parent.parent / "data"

# --- 1. Imagens do offer existente ---
with open(DATA_DIR / "peugeot_next_data.json", encoding="utf-8") as f:
    d = json.load(f)

state = d.get("configurable", {}).get("props", {}).get("initialState", {})
offers = state.get("OfferList", {}).get("configurable", {}).get("offers", [])

print(f"=== Imagens do primeiro offer ({offers[0]['_id']}) ===")
obj = offers[0].get("_properties", {}).get("object", {})
for img in obj.get("images", []):
    print(f"  type={img.get('type')}")
    print(f"  url={img.get('url', '')}")
    for d2 in img.get("default", []):
        print(f"    default: {str(d2)[:200]}")
    print()

print(f"\n=== nameplateBodyStyleSlugs de todos os offers ===")
for o in offers:
    obj2 = o.get("_properties", {}).get("object", {})
    print(f"  {obj2.get('title')} -> slug={obj2.get('nameplateBodyStyleSlug')} | id={o['_id']}")

# --- 2. Navegar ao configurador do primeiro modelo ---
slug = obj.get("nameplateBodyStyleSlug", "208-5-portas")
print(f"\n=== A navegar para o configurador: {slug} ===")

api_json = []
img_urls = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})

    def on_response(r):
        url = r.url
        ct = r.headers.get("content-type", "")
        if "visuel3d" in url or "v3dcentral" in url or "V3DImage" in url:
            img_urls.append({"url": url, "status": r.status})
        if "json" in ct and ("spc-api" in url or "vehicle" in url or "color" in url
                             or "exterior" in url or "interior" in url or "motor" in url
                             or "option" in url or "configurator" in url):
            try:
                body = r.body()
                api_json.append({"url": url, "status": r.status, "size": len(body)})
            except Exception:
                api_json.append({"url": url, "status": r.status, "size": 0})

    ctx.on("response", on_response)
    page = ctx.new_page()

    for url_try in [
        f"https://store.peugeot.pt/pt/configurator/{slug}?channel=b2c",
        f"https://store.peugeot.pt/pt/configurator/{slug}",
    ]:
        page.goto(url_try, wait_until="networkidle", timeout=30000)
        time.sleep(3)
        final_url = page.url
        print(f"  Tentativa: {url_try}")
        print(f"  URL final: {final_url}")
        if "404" not in final_url and "configurable" not in final_url:
            break

    page.screenshot(path=str(DATA_DIR / "peugeot_p3_configurator.png"))

    # Extrair __NEXT_DATA__ da pagina do configurador
    nd = page.evaluate("() => window.__NEXT_DATA__ || null")
    if nd:
        out = DATA_DIR / "peugeot_configurator_data.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(nd, f, ensure_ascii=False, indent=2)
        print(f"  __NEXT_DATA__ guardado: {out}")

        # Mostrar estrutura
        cfg_state = nd.get("props", {}).get("initialState", {})
        configurator = cfg_state.get("Configurator", {})
        print(f"\n  Cores exteriores: {len(configurator.get('exteriorColors', []))}")
        print(f"  Cores interiores: {len(configurator.get('interiorColors', []))}")
        print(f"  Motorizacoes: {len(configurator.get('motorizations', []))}")

        # Mostrar primeira cor
        ext_colors = configurator.get("exteriorColors", [])
        if ext_colors:
            print(f"\n  Primeira cor exterior:")
            c = ext_colors[0]
            for k, v in c.items():
                if k != "prices":
                    print(f"    {k}: {str(v)[:120]}")

    browser.close()

print(f"\n=== URLs do visualizador 3D capturadas ({len(img_urls)}) ===")
for c in img_urls[:20]:
    print(f"  [{c['status']}] {c['url']}")

print(f"\n=== Chamadas API JSON ({len(api_json)}) ===")
for c in api_json[:20]:
    print(f"  [{c['status']}] {c['url'][:160]} ({c['size']} bytes)")
