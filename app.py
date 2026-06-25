"""
Gerador de Imagens — Veículos Novos — Caetano
Interface para gerar 4 imagens de carros em diferentes ângulos.
"""
import base64
from pathlib import Path

import streamlit as st
from scraper.vw_catalog import load_catalog as vw_load_catalog, get_image_urls
from scraper.vw_images import generate_images as vw_generate_images, images_to_zip as vw_images_to_zip
from scraper.peugeot_catalog import load_catalog as peugeot_load_catalog
from scraper.peugeot_images import generate_images as peugeot_generate_images, images_to_zip as peugeot_images_to_zip
from scraper.composite import composite, has_template

st.set_page_config(
    page_title="Gerador de Imagens - Veículos Novos",
    page_icon="🚗",
    layout="wide",
)

# ── Logo Caetano (canto superior direito) ──────────────────────────────────────
_LOGO_CANDIDATES = [
    Path(__file__).parent / "data" / "logo_caetano.png",
    Path(__file__).parent / "data" / "logo_caetano.webp",
    Path(__file__).parent / "data" / "logo_caetano.jpg",
]
_logo_path = next((p for p in _LOGO_CANDIDATES if p.exists()), None)

# ── CSS global (string normal — sem f-string para não precisar escapar { }) ───
st.markdown("""
<style>
/* ── Logo fixo — sem fundo ── */
.caetano-logo {
    position: fixed;
    top: 14px;
    right: 80px;
    z-index: 9999;
    background: none;
    padding: 0;
    line-height: 0;
}

/* ════════════════════════════════════════════════════════
   CONTROL PANEL — cobre Streamlit <1.35 (column)
                        e Streamlit ≥1.35 (stColumn)
════════════════════════════════════════════════════════ */
[data-testid="stColumn"]:first-child,
[data-testid="column"]:first-child,
[data-testid="stHorizontalBlock"] > div:nth-child(1) {
    background: linear-gradient(165deg, #00408f 0%, #002c59 45%, #001830 100%) !important;
    border-radius: 18px !important;
    padding: 28px 20px 32px !important;
    box-shadow:
        12px 14px 32px rgba(0,0,0,.6),
        -3px -3px 8px rgba(255,255,255,.05),
        inset 0 1px 0 rgba(255,255,255,.22),
        inset 0 -3px 8px rgba(0,0,0,.4) !important;
    border: 1px solid rgba(255,255,255,.14) !important;
}

/* Catch-all: todo o texto dentro do painel a branco. */
[data-testid="stColumn"]:first-child *,
[data-testid="column"]:first-child *,
[data-testid="stHorizontalBlock"] > div:nth-child(1) * {
    color: white !important;
}

/* Override: popup/menu do dropdown — texto escuro sobre fundo branco.
   Deve vir DEPOIS do catch-all para ter precedência. */
[data-baseweb="popover"] *,
[data-baseweb="menu"] *,
[role="option"],
[role="option"] *,
ul[data-baseweb] li,
ul[data-baseweb] li * {
    color: #1a1a1a !important;
    background-color: white !important;
}

[data-testid="stColumn"]:first-child h3,
[data-testid="column"]:first-child h3,
[data-testid="stHorizontalBlock"] > div:nth-child(1) h3 {
    color: white !important;
    font-weight: 700 !important;
    letter-spacing: .5px !important;
    text-shadow: 0 2px 6px rgba(0,0,0,.4) !important;
    padding-bottom: 10px !important;
    border-bottom: 1px solid rgba(255,255,255,.18) !important;
    margin-bottom: 18px !important;
}

[data-testid="stColumn"]:first-child label,
[data-testid="column"]:first-child label,
[data-testid="stHorizontalBlock"] > div:nth-child(1) label {
    color: rgba(255,255,255,.9) !important;
    font-weight: 500 !important;
}

[data-testid="stColumn"]:first-child [data-baseweb="select"] > div,
[data-testid="column"]:first-child [data-baseweb="select"] > div,
[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-baseweb="select"] > div {
    background-color: rgba(255,255,255,.1) !important;
    border-color: rgba(255,255,255,.28) !important;
    border-radius: 8px !important;
}

[data-testid="stColumn"]:first-child [data-baseweb="select"] span,
[data-testid="column"]:first-child [data-baseweb="select"] span,
[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-baseweb="select"] span {
    color: white !important;
}

[data-testid="stColumn"]:first-child [data-baseweb="select"] svg,
[data-testid="column"]:first-child [data-baseweb="select"] svg,
[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-baseweb="select"] svg {
    fill: rgba(255,255,255,.75) !important;
}

[data-testid="stColumn"]:first-child hr,
[data-testid="column"]:first-child hr,
[data-testid="stHorizontalBlock"] > div:nth-child(1) hr {
    border-color: rgba(255,255,255,.2) !important;
    margin: 18px 0 !important;
}

[data-testid="stColumn"]:first-child figcaption,
[data-testid="column"]:first-child figcaption,
[data-testid="stHorizontalBlock"] > div:nth-child(1) figcaption {
    color: rgba(255,255,255,.7) !important;
}

[data-testid="stColumn"]:first-child [data-testid="stButton"] > button,
[data-testid="column"]:first-child [data-testid="stButton"] > button,
[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stButton"] > button {
    background: linear-gradient(135deg, #1a6fcf 0%, #0d4fa8 100%) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,.3) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    letter-spacing: .4px !important;
    box-shadow: 0 4px 14px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.25) !important;
    margin-top: 4px !important;
}

[data-testid="stColumn"]:first-child [data-testid="stButton"] > button:hover,
[data-testid="column"]:first-child [data-testid="stButton"] > button:hover,
[data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #2179db 0%, #1460c0 100%) !important;
    box-shadow: 0 7px 22px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.3) !important;
    transform: translateY(-1px) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Logo HTML — chamada separada para não interferir com o CSS ─────────────────
if _logo_path:
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
    _ext = _logo_path.suffix.lstrip(".")
    _mime = "image/jpeg" if _ext == "jpg" else f"image/{_ext}"
    st.markdown(
        f'<div class="caetano-logo"><img src="data:{_mime};base64,{_logo_b64}" height="120" /></div>',
        unsafe_allow_html=True,
    )

st.title("Gerador de Imagens — Veículos Novos")
st.caption("Caetano — imagens para anúncios")

# ── Catálogos com cache ────────────────────────────────────────────────────────
@st.cache_data(show_spinner="A carregar catálogo VW...")
def get_vw_catalog():
    return vw_load_catalog()

@st.cache_data(show_spinner="A carregar catálogo Peugeot...")
def get_peugeot_catalog():
    return peugeot_load_catalog()

LABELS_PT = {"3_4_frente": "3/4 Frente", "frente": "Frente", "lado": "Lado", "traseira": "Traseira"}

# ── Layout ─────────────────────────────────────────────────────────────────────
col_sel, col_imgs = st.columns([1, 2], gap="large")

# ── Painel de selecção ─────────────────────────────────────────────────────────
with col_sel:
    st.subheader("Configuração")

    BRANDS = {"Volkswagen": "vw", "Peugeot": "peugeot"}
    selected_brand = BRANDS[st.selectbox("Marca", list(BRANDS.keys()))]

    # Limpar imagens ao mudar de marca
    if st.session_state.get("last_brand") != selected_brand:
        st.session_state.generated_images = None
        st.session_state.generated_config = None
        st.session_state.last_brand = selected_brand

    gerar_btn = False  # default

    # ── VW ────────────────────────────────────────────────────────────────────
    if selected_brand == "vw":
        catalog = get_vw_catalog()
        all_variants = [
            {"label": f"{g['groupName']} — {v['variantName']}", **v}
            for g in catalog.get("models", [])
            for v in g.get("variants", [])
        ]
        variant_labels = [v["label"] for v in all_variants]
        sel_variant_label = st.selectbox("Modelo", variant_labels, key="vw_model")
        selected_variant = next(v for v in all_variants if v["label"] == sel_variant_label)
        model_code = selected_variant["modelCode"]
        default_upholstery = selected_variant["defaultUpholstery"]
        colors = selected_variant["colors"]
        wheels = selected_variant["wheels"]

        color_labels = [
            f"{c['name']} (+{c['price']:.0f}€)" if c["price"] > 0 else c["name"]
            for c in colors
        ]
        color_map = {lbl: c for lbl, c in zip(color_labels, colors)}
        sel_color = color_map[st.selectbox("Cor", color_labels, key="vw_color")]
        if sel_color.get("swatchUrl"):
            st.image(sel_color["swatchUrl"], width=60, caption=sel_color["name"])

        wheel_labels = [f"{w['title']} {'(série)' if w['serie'] else ''}" for w in wheels]
        wheel_map = {lbl: w for lbl, w in zip(wheel_labels, wheels)}
        sel_wheel = wheel_map[st.selectbox("Jantes", wheel_labels, key="vw_wheels")]
        if sel_wheel.get("imageUrl"):
            st.image(sel_wheel["imageUrl"], width=120, caption=sel_wheel["title"])

        st.divider()
        gerar_btn = st.button("Gerar 4 Imagens", type="primary", use_container_width=True)

    # ── Peugeot ───────────────────────────────────────────────────────────────
    else:
        pcat = get_peugeot_catalog()
        pmodels = pcat.get("models", [])
        model_names = [m["modelName"] for m in pmodels]
        model_map = {name: m for name, m in zip(model_names, pmodels)}
        sel_model = model_map[st.selectbox("Modelo", model_names, key="peugeot_model")]

        # Seletor de versão (trim)
        variants = sel_model["variants"]
        variant_names = [v["variantName"] for v in variants]
        variant_map = {n: v for n, v in zip(variant_names, variants)}
        sel_variant = variant_map[st.selectbox("Versão", variant_names, key="peugeot_version")]

        # Seletor de cor
        pcolors = sel_variant["colors"]
        pcolor_labels = [c["name"] for c in pcolors]
        pcolor_map = {n: c for n, c in zip(pcolor_labels, pcolors)}
        sel_pcolor = pcolor_map[st.selectbox("Cor", pcolor_labels, key="peugeot_color")]

        if sel_pcolor.get("swatchUrl"):
            st.image(sel_pcolor["swatchUrl"], width=60, caption=sel_pcolor["name"])

        st.divider()
        gerar_btn = st.button("Gerar 4 Imagens", type="primary", use_container_width=True)

# ── Coluna de imagens ──────────────────────────────────────────────────────────
with col_imgs:
    st.subheader("Imagens Geradas")

    if "generated_images" not in st.session_state:
        st.session_state.generated_images = None
        st.session_state.generated_config = None

    if gerar_btn:
        with st.spinner("A gerar imagens..."):
            if selected_brand == "vw":
                color_code = sel_color["code"]
                wheel_code = sel_wheel["code"] if not sel_wheel.get("serie") else ""
                images = vw_generate_images(
                    model_code=model_code,
                    color_code=color_code,
                    upholstery_code=default_upholstery,
                    wheel_code=wheel_code,
                )
                cfg = {
                    "brand": "VW",
                    "model": selected_variant.get("name"),
                    "color": sel_color.get("name"),
                    "detail": sel_wheel.get("title"),
                    "zip_prefix": f"VW_{model_code}_{color_code}",
                }
            else:
                images = peugeot_generate_images(
                    version=sel_variant["lcdv16"],
                    color_id=sel_pcolor["id"],
                    trim_id=sel_variant["trimCode"],
                )
                cfg = {
                    "brand": "Peugeot",
                    "model": sel_model["modelName"],
                    "color": sel_pcolor["name"],
                    "detail": sel_variant["variantName"],
                    "zip_prefix": f"Peugeot_{sel_variant['lcdv16']}_{sel_pcolor['id']}",
                }

            if images and has_template():
                images = {k: composite(v) for k, v in images.items()}

        if images:
            st.session_state.generated_images = images
            st.session_state.generated_config = cfg
        else:
            st.error("Não foi possível gerar as imagens. Verifica a ligação.")

    if st.session_state.generated_images:
        images = st.session_state.generated_images
        cfg    = st.session_state.generated_config
        st.caption(f"**{cfg['model']}** · Cor: {cfg['color']} · {cfg['detail']}")

        view_keys = list(images.keys())
        for row_keys in [view_keys[:2], view_keys[2:]]:
            cols = st.columns(len(row_keys))
            for col, key in zip(cols, row_keys):
                col.image(images[key], caption=LABELS_PT.get(key, key), width="stretch")

        st.divider()
        zip_name  = f"{cfg['zip_prefix']}.zip"
        if cfg["brand"] == "VW":
            zip_bytes = vw_images_to_zip(images, zip_name)
        else:
            zip_bytes = peugeot_images_to_zip(images, zip_name)
        st.download_button(
            label=f"Download ZIP ({len(images)} imagens)",
            data=zip_bytes,
            file_name=zip_name,
            mime="application/zip",
            use_container_width=True,
        )

    else:
        st.info("Selecciona um modelo e clica em **Gerar 4 Imagens**.")
        if selected_brand == "vw":
            color_code = sel_color["code"]
            wheel_code = sel_wheel["code"] if not sel_wheel.get("serie") else ""
            st.image(
                f"https://cdn.nwi-ms.com/media/pt/V/mc/{model_code}/model/exteriorfront.webp"
                f"?F={color_code}&P={default_upholstery}&M={wheel_code}&size=L",
                caption=f"Preview — {selected_variant.get('name')}",
                width="stretch",
            )
        else:
            v = sel_variant["lcdv16"]; c = sel_pcolor["id"]; t = sel_variant["trimCode"]
            st.image(
                f"https://visuel3d-secure.peugeot.com/V3DImage.ashx"
                f"?client=SOLVCG&ratio=1&format=jpg&quality=90&width=900&height=500"
                f"&back=0&view=006&version={v}&color={c}&trim={t}&mkt=PT",
                caption=f"Preview — {sel_model['modelName']}",
                width="stretch",
            )
