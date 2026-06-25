"""
Extrai códigos de cor Peugeot do bundle JS da página configurável.
Procura padrões como colorId, exteriorColour, 0MM.
"""
import ssl, urllib.request, re, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
h = {"User-Agent": "Mozilla/5.0"}

# Obter a página para encontrar o URL do bundle
page_url = "https://store.peugeot.pt/configurable?channel=b2c"
req = urllib.request.Request(page_url, headers=h)
with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
    html = r.read().decode("utf-8", errors="replace")

# Encontrar links de JS chunk
js_chunks = re.findall(r'/_next/static/chunks/[^"\']+\.js', html)
# Filtrar para chunks que provavelmente têm dados de configuração
interesting = [c for c in js_chunks if any(x in c for x in ["pages", "configur", "955", "catalog"])]
print("JS chunks interessantes:", interesting[:5])

# Tentar também o chunk da página configurable
config_chunk = next((c for c in js_chunks if "configurable" in c), None)
if config_chunk:
    interesting = [config_chunk] + [c for c in interesting if c != config_chunk]

colors_found = {}

for chunk_path in interesting[:4]:
    url = f"https://store.peugeot.pt{chunk_path}"
    print(f"\nA ler: {url[:100]}")
    req2 = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req2, context=ctx, timeout=15) as r2:
            js = r2.read().decode("utf-8", errors="replace")
        print(f"  Tamanho: {len(js)} chars")

        # Procurar códigos de cor no formato 0MM...
        colors = re.findall(r'0MM[0-9A-Z]{5}', js)
        unique_colors = list(dict.fromkeys(colors))
        print(f"  Códigos 0MM encontrados: {len(unique_colors)} — {unique_colors[:15]}")

        # Procurar pares {id: "...", title/name: "..."}
        pairs = re.findall(r'"id"\s*:\s*"(0MM[^"]+)"[^}]*?"(?:title|name)"\s*:\s*"([^"]+)"', js)
        if pairs:
            print(f"  Pares id+nome: {pairs[:10]}")

        colors_found.update({c: "" for c in unique_colors})
    except Exception as e:
        print(f"  ERRO: {e}")

print(f"\nTotal cores 0MM encontradas: {len(colors_found)}")
for c in sorted(colors_found.keys()):
    print(" ", c)
