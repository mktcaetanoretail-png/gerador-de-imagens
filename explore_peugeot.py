"""
Explora o configurador Peugeot PT para identificar APIs de modelos, cores, jantes e imagens.
Intercepta chamadas de rede e guarda em data/peugeot_api.json
"""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT = DATA_DIR / "peugeot_api.json"

calls = []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})

    ctx.on("response", lambda r: calls.append({
        "url": r.url,
        "status": r.status,
        "ct": r.headers.get("content-type", ""),
    }) if ("json" in r.headers.get("content-type", "") or
           "api" in r.url or "catalog" in r.url or "model" in r.url or
           "config" in r.url.lower()) else None)

    page = ctx.new_page()
    print("A abrir configurador Peugeot...")
    page.goto("https://store.peugeot.pt/configurable", wait_until="load", timeout=30000)
    time.sleep(5)
    page.screenshot(path=str(DATA_DIR / "peugeot_01_landing.png"))
    print(f"  Screenshot: peugeot_01_landing.png")

    # Aguardar mais para carregar completamente
    time.sleep(5)
    page.screenshot(path=str(DATA_DIR / "peugeot_02_loaded.png"))

    print(f"\nChamadas API capturadas: {len(calls)}")
    for c in calls[:30]:
        print(f"  [{c['status']}] {c['url'][:120]}")

    # Guardar todas as chamadas
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(calls, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado: {OUT}")

    browser.close()
