"""Analisa o HTML do configurador para encontrar selectores de navegação."""
import re

with open("data/pintura_page.html", encoding="utf-8", errors="replace") as f:
    content = f.read()

# Encontrar todos os menu-elements com data-cy-menu
menus = re.findall(r'data-cy-menu="([^"]+)"[^>]*title="([^"]+)"', content)
print("=== Menu elements ===")
for cy, title in menus:
    print(f"  data-cy-menu='{cy}' | title='{title}'")

print()

# Encontrar o nwi-button Continuar
idx = content.find("Continuar")
if idx >= 0:
    print("=== Continuar button context ===")
    print(content[max(0, idx-400):idx+300])

print()

# Encontrar swatches de cor (quando existirem)
swatch_patterns = [
    r'class="[^"]*swatch[^"]*"',
    r'data-color[^=]?=',
    r'class="[^"]*color-tile[^"]*"',
    r'class="[^"]*paint[^"]*"',
]
print("=== Padroes de swatch ===")
for pat in swatch_patterns:
    found = re.findall(pat, content)
    if found:
        print(f"  '{pat}': {len(found)} ocorrencias")
        for f_ in found[:3]:
            print(f"    {f_}")
