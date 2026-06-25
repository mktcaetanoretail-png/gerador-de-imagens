"""Analisa filterCategories e filters para encontrar modelos Peugeot."""
import json

with open("data/_next_data.json", encoding="utf-8") as f:
    nd = json.load(f)

state = nd.get("props", {}).get("initialState", {})
filters_state = state.get("Filters", {})

print("=== filterCategories ===")
for cat in filters_state.get("filterCategories", []):
    print(f"\nCategoria: {cat.get('name')} — {cat.get('displayName')}")
    for f in cat.get("filters", []):
        print(f"  {f.get('name')}: {f.get('displayName')} = {f.get('value')}")

print("\n=== filters (activos) ===")
for f in filters_state.get("filters", []):
    print(f"  {f.get('name')} ({f.get('parent')}): {f.get('displayName')} = {f.get('value')}")

# Procurar por "nameplate" ou "model" nos filterCategories
print("\n=== Todos os filtros com 'nameplate' ou 'model' ===")
def find_model_filters(obj, path=""):
    if isinstance(obj, dict):
        name = obj.get("name", "")
        if "nameplate" in str(name).lower() or "model" in str(name).lower():
            print(f"  {path}: {obj}")
        for k, v in obj.items():
            find_model_filters(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_model_filters(item, f"{path}[{i}]")

find_model_filters(filters_state)
