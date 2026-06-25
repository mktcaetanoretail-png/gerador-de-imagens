"""Captura todas as chamadas API do configurador Peugeot para um modelo específico."""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA_DIR = Path(__file__).parent.parent / "data"

api_calls = []
color_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})

    def on_response(r):
        url = r.url
        ct = r.headers.get("content-type", "")
        if "spc-api" in url:
            try:
                body = r.body()
                parsed = json.loads(body) if body else None
                api_calls.append({"url": url, "status": r.status, "data": parsed})
                print(f"  API: [{r.status}] {url[:120]}")
            except Exception as e:
                api_calls.append({"url": url, "status": r.status, "data": None})

    ctx.on("response", on_response)
    page = ctx.new_page()

    url = "https://store.peugeot.pt/configurator/208-5-portas?channel=b2c"
    print(f"A carregar: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)

    # Aguardar hidratação React (esperar por elementos de cor)
    print("A aguardar carregamento completo...")
    for _ in range(15):
        time.sleep(1)
        # Tentar extrair cores do DOM
        try:
            colors_from_dom = page.evaluate("""() => {
                // Tentar obter do Redux store via window
                const storeKeys = Object.keys(window).filter(k =>
                    k.includes('store') || k.includes('Store') || k.includes('redux')
                );
                if (storeKeys.length > 0) {
                    for (const k of storeKeys) {
                        try {
                            const s = window[k].getState?.();
                            if (s && s.Configurator && s.Configurator.exteriorColors?.length > 0) {
                                return {source: k, colors: s.Configurator.exteriorColors};
                            }
                        } catch(e) {}
                    }
                }
                // Tentar via __NEXT_DATA__ actualizado
                const nd = window.__NEXT_DATA__;
                if (nd?.props?.initialState?.Configurator?.exteriorColors?.length > 0) {
                    return {source: '__NEXT_DATA__', colors: nd.props.initialState.Configurator.exteriorColors};
                }
                return null;
            }""")
            if colors_from_dom:
                color_data.append(colors_from_dom)
                print(f"  Cores encontradas via {colors_from_dom['source']}: {len(colors_from_dom['colors'])}")
                break
        except Exception:
            pass

    page.screenshot(path=str(DATA_DIR / "peugeot_configurator_loaded.png"))

    # Extrair swatches visíveis do DOM
    swatches = page.evaluate("""() => {
        const result = [];
        // Procurar elementos de cor no DOM
        const imgs = document.querySelectorAll('img[src*="Colors"], img[src*="color"], img[src*="colour"]');
        imgs.forEach(img => result.push({type: 'img', src: img.src, alt: img.alt || ''}));
        // Procurar botões/divs com data-color
        const btns = document.querySelectorAll('[data-color], [data-colour], [data-colorid]');
        btns.forEach(b => result.push({type: 'btn', attrs: b.dataset}));
        return result;
    }""")
    print(f"\nSwatches no DOM: {len(swatches)}")
    for s in swatches[:10]:
        print(f"  {s}")

    # Tentar clicar em "Cor exterior" ou similar
    try:
        color_section = page.locator('text=/cor exterior|exterior colour|couleur/i').first
        if color_section.is_visible(timeout=2000):
            color_section.click()
            time.sleep(2)
            print("  Clicou em secção de cor")
    except Exception:
        pass

    time.sleep(3)
    page.screenshot(path=str(DATA_DIR / "peugeot_configurator_final.png"))
    browser.close()

print(f"\n=== {len(api_calls)} chamadas spc-api capturadas ===")
for c in api_calls:
    data_preview = str(c["data"])[:200] if c["data"] else "null"
    print(f"\n[{c['status']}] {c['url']}")
    print(f"  {data_preview}")

out = DATA_DIR / "peugeot_api_full.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump({"api_calls": api_calls, "color_data": color_data}, f, ensure_ascii=False, indent=2)
print(f"\nGuardado: {out}")
