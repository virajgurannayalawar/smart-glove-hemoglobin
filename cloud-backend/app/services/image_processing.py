from io import BytesIO
from typing import Tuple

from PIL import Image, ImageOps


class ImageProcessingError(ValueError):
    pass


def _center_crop_square(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def preprocess_for_model(
    image_bytes: bytes,
    *,
    size: int,
    grayscale: bool = False,
    autocontrast: bool = True,
) -> Tuple[bytes, str]:
    """
    Deterministic preprocessing:
    - decode
    - EXIF orientation fix
    - center crop square
    - resize to (size,size)
    - optional autocontrast
    - encode to PNG

    Returns: (processed_bytes, format)
    """
    if not image_bytes:
        raise ImageProcessingError("Empty image payload")
    if size <= 0 or size > 2048:
        raise ImageProcessingError("Invalid target size")

    try:
        img = Image.open(BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
    except Exception as e:
        raise ImageProcessingError(f"Invalid image: {e}")

    img = _center_crop_square(img)
    img = img.resize((size, size), resample=Image.BILINEAR)

    if grayscale:
        img = ImageOps.grayscale(img)
    if autocontrast:
        img = ImageOps.autocontrast(img)

    out = BytesIO()
    img.save(out, format="PNG", optimize=True)
    return out.getvalue(), "png"

