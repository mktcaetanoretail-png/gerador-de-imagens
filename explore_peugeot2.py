"""
Analisa a API do configurador Peugeot PT:
1. Extrai o buildId actual do Next.js
2. Descarrega o JSON de configuração completo
3. Navega por um modelo para capturar chamadas de imagem
"""
import json, re, ssl, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, context=_ssl_ctx, timeout=30) as r:
        return r.read()


def get_build_id() -> str:
    html = fetch("https://store.peugeot.pt/configurable").decode("utf-8", errors="replace")
    m = re.search(r'"buildId":"([^"]+)"', html)
    if not m:
        raise RuntimeError("buildId nao encontrado no HTML")
    return m.group(1)


def show_keys(d, prefix="", depth=3):
    if depth == 0 or d is None:
        return
    if isinstance(d, dict):
        for k, v in list(d.items())[:25]:
            tag = f" ({len(v)} items)" if isinstance(v, (list, dict)) else f" = {str(v)[:100]}"
            print(f"{prefix}{k}: {type(v).__name__}{tag}")
            show_keys(v, prefix + "  ", depth - 1)
    elif isinstance(d, list) and d:
        print(f"{prefix}[0]: {type(d[0]).__name__}")
        show_keys(d[0], prefix + "  ", depth - 1)


def main():
    img_calls = []
    api_calls = []
    next_data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=False)
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})

        def on_response(r):
            url = r.url
            ct = r.headers.get("content-type", "")
            if any(ext in url for ext in [".webp", ".jpg", ".jpeg", ".png"]):
                img_calls.append({"url": url, "status": r.status})
            elif "json" in ct:
                api_calls.append({"url": url, "status": r.status, "ct": ct})

        ctx.on("response", on_response)
        page = ctx.new_page()

        # --- Pagina principal do configurador ---
        print("A abrir configurador Peugeot...")
        page.goto("https://store.peugeot.pt/configurable?channel=b2c",
                  wait_until="networkidle", timeout=40000)
        time.sleep(3)
        page.screenshot(path=str(DATA_DIR / "peugeot_p2_01_landing.png"))

        # Extrair __NEXT_DATA__ da pagina
        nd = page.evaluate("() => window.__NEXT_DATA__ || null")
        if nd:
            next_data["configurable"] = nd
            print("  __NEXT_DATA__ extraido da pagina de configuracao")

        # Listar todos os links de modelos
        links = page.locator("a").all()
        model_links = []
        for lnk in links:
            try:
                href = lnk.get_attribute("href") or ""
                if "/configurator/" in href or "/configure/" in href or ("/pt/" in href and href.count("/") >= 3):
                    model_links.append(href)
            except Exception:
                pass
        model_links = list(dict.fromkeys(model_links))  # dedup
        print(f"  Links de modelos encontrados: {len(model_links)}")
        for ml in model_links[:10]:
            print(f"    {ml}")

        # Clicar no primeiro carro da lista
        try:
            cards = page.locator("article, [class*='card'], [class*='Card'], [class*='vehicle'], [class*='Vehicle']").all()
            print(f"  Cards encontrados: {len(cards)}")
            if cards:
                cards[0].click(timeout=5000)
                time.sleep(4)
                page.screenshot(path=str(DATA_DIR / "peugeot_p2_02_model.png"))
                nd2 = page.evaluate("() => window.__NEXT_DATA__ || null")
                if nd2:
                    next_data["model_page"] = nd2
                    print(f"  URL apos clique: {page.url}")
        except Exception as e:
            print(f"  Nao conseguiu clicar: {e}")

        # Se nao navegou, tentar URL directa de um modelo (208, 2008, etc.)
        if len(next_data) < 2:
            for slug in ["208", "2008", "308", "3008", "5008", "e-208"]:
                test_url = f"https://store.peugeot.pt/pt/configurator/{slug}?channel=b2c"
                try:
                    page.goto(test_url, wait_until="networkidle", timeout=20000)
                    time.sleep(2)
                    nd3 = page.evaluate("() => window.__NEXT_DATA__ || null")
                    if nd3 and page.url != "https://store.peugeot.pt/pt/configurable":
                        next_data[f"model_{slug}"] = nd3
                        print(f"  Modelo {slug} carregado: {page.url}")
                        page.screenshot(path=str(DATA_DIR / f"peugeot_p2_model_{slug}.png"))
                        break
                except Exception as e:
                    print(f"  {slug}: {e}")

        browser.close()

    # Guardar tudo
    out = DATA_DIR / "peugeot_next_data.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(next_data, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado __NEXT_DATA__: {out}")

    out_calls = DATA_DIR / "peugeot_img_calls.json"
    with open(out_calls, "w", encoding="utf-8") as f:
        json.dump({"images": img_calls[:100], "api": api_calls[:100]}, f, ensure_ascii=False, indent=2)

    print(f"\n=== Imagens capturadas ({len(img_calls)}) ===")
    for c in img_calls[:30]:
        print(f"  [{c['status']}] {c['url'][:160]}")

    print(f"\n=== API JSON capturadas ({len(api_calls)}) ===")
    for c in api_calls[:30]:
        print(f"  [{c['status']}] {c['url'][:160]}")

    print(f"\n=== Estrutura __NEXT_DATA__ (configurable) ===")
    show_keys(next_data.get("configurable", {}), depth=4)


if __name__ == "__main__":
    main()
