"""
Composta imagens de carro sobre o template Caetano Star.
Imagens com alpha usam-no directamente; imagens sem alpha têm o fundo
removido por rembg (U2Net).
"""
import io
from pathlib import Path

import numpy as np
from PIL import Image

TEMPLATE_PATH = Path(__file__).parent.parent / "data" / "template.png"

# Posição do carro no template (frações das dimensões do template)
CAR_MAX_WIDTH_FRAC  = 0.90
CAR_BOTTOM_Y_FRAC   = 0.83
CAR_CENTER_X_FRAC   = 0.50
MIN_TOP_MARGIN_FRAC = 0.17   # margem mínima no topo para não cobrir o logo


def _has_alpha(img: Image.Image) -> bool:
    """True se a imagem já tem transparência real no canal alpha."""
    if img.mode != "RGBA":
        return False
    arr = np.array(img)
    return bool((arr[:, :, 3] < 255).any())


_rembg_session = None


def _get_rembg_session():
    global _rembg_session
    if _rembg_session is None:
        from rembg import new_session
        _rembg_session = new_session("u2net")
    return _rembg_session


def _remove_bg_rembg(img_bytes: bytes) -> Image.Image:
    from rembg import remove
    result = remove(img_bytes, session=_get_rembg_session())
    return Image.open(io.BytesIO(result)).convert("RGBA")


def _crop_to_content(img: Image.Image) -> Image.Image:
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def composite(car_bytes: bytes) -> bytes:
    """
    Sobrepõe a imagem do carro sobre o template Caetano Star.
    Se o template não existir devolve a imagem original sem alteração.
    """
    if not TEMPLATE_PATH.exists():
        return car_bytes

    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    tw, th = template.size

    car = Image.open(io.BytesIO(car_bytes)).convert("RGBA")

    if not _has_alpha(car):
        car = _remove_bg_rembg(car_bytes)

    car = _crop_to_content(car)
    cw, ch = car.size

    # Escalar para caber em max_width × max_height (mantendo proporção)
    max_w = int(tw * CAR_MAX_WIDTH_FRAC)
    max_h = int(th * CAR_BOTTOM_Y_FRAC) - int(th * MIN_TOP_MARGIN_FRAC)
    scale = min(1.0, max_w / cw, max_h / ch)
    if scale < 1.0:
        car = car.resize((int(cw * scale), int(ch * scale)), Image.LANCZOS)
        cw, ch = car.size

    # Posicionar: centro horizontal, rodas na plataforma
    x = int(tw * CAR_CENTER_X_FRAC) - cw // 2
    y = int(th * CAR_BOTTOM_Y_FRAC) - ch

    result = template.copy()
    result.paste(car, (x, y), car)

    buf = io.BytesIO()
    result.convert("RGB").save(buf, format="JPEG", quality=93)
    return buf.getvalue()


def has_template() -> bool:
    return TEMPLATE_PATH.exists()
