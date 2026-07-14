"""
app/utils/image_utils.py
=========================
Image processing utilities — resizing, thumbnail generation, and validation.

Uses Pillow (PIL) for all image operations. Converts images to a safe
format (JPEG/PNG) on save to prevent polyglot file attacks.
"""

import io
from pathlib import Path
from typing import Optional

from app.constants.limits import Limits
from app.core.exceptions import FileOperationError


def resize_image(
    source_path: str,
    max_width: int,
    max_height: int,
    output_path: Optional[str] = None,
    quality: int = 85,
) -> str:
    """
    Resize an image to fit within max_width × max_height, preserving aspect ratio.

    Args:
        source_path: Absolute path to the source image.
        max_width: Maximum output width in pixels.
        max_height: Maximum output height in pixels.
        output_path: Absolute path for the output. If None, overwrites source.
        quality: JPEG compression quality (1-95).

    Returns:
        Path to the resized image.

    Raises:
        FileOperationError: If the file is not a valid image.
    """
    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError as exc:
        raise FileOperationError("Pillow is required for image processing.") from exc

    if output_path is None:
        output_path = source_path

    try:
        with Image.open(source_path) as img:
            # Convert RGBA to RGB for JPEG compatibility
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.thumbnail((max_width, max_height), Image.LANCZOS)
            img.save(output_path, optimize=True, quality=quality)
    except (OSError, Exception) as exc:  # noqa: BLE001
        raise FileOperationError(f"Image processing failed: {exc}") from exc

    return output_path


def generate_thumbnail(
    source_path: str,
    width: int = Limits.File.THUMBNAIL_WIDTH,
    height: int = Limits.File.THUMBNAIL_HEIGHT,
    suffix: str = "_thumb",
) -> str:
    """
    Generate a square thumbnail for a profile photo.

    Crops the center square of the image before resizing to ensure
    the thumbnail is always square regardless of source aspect ratio.

    Args:
        source_path: Absolute path to the source image.
        width: Thumbnail width in pixels.
        height: Thumbnail height in pixels.
        suffix: Suffix appended before the extension in the thumbnail filename.

    Returns:
        Absolute path to the generated thumbnail.

    Raises:
        FileOperationError: If image processing fails.
    """
    try:
        from PIL import Image, ImageOps  # noqa: PLC0415
    except ImportError as exc:
        raise FileOperationError("Pillow is required for image processing.") from exc

    source = Path(source_path)
    thumb_path = source.with_name(f"{source.stem}{suffix}{source.suffix}")

    try:
        with Image.open(source_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Crop to center square
            img = ImageOps.fit(img, (width, height), Image.LANCZOS)
            img.save(str(thumb_path), optimize=True, quality=85)
    except (OSError, Exception) as exc:  # noqa: BLE001
        raise FileOperationError(f"Thumbnail generation failed: {exc}") from exc

    return str(thumb_path)


def is_valid_image(file_bytes: bytes) -> bool:
    """
    Verify that a byte stream is a valid image using Pillow.

    Used to validate image content beyond just checking the extension
    (defense against polyglot / MIME-type spoofing attacks).

    Args:
        file_bytes: Raw bytes of the uploaded file.

    Returns:
        True if the bytes represent a valid image.
    """
    try:
        from PIL import Image  # noqa: PLC0415
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()  # Raises on invalid image data
        return True
    except Exception:  # noqa: BLE001
        return False


def get_image_dimensions(image_path: str) -> tuple[int, int]:
    """
    Return the (width, height) of an image in pixels.

    Args:
        image_path: Absolute path to the image file.

    Returns:
        Tuple of (width, height).

    Raises:
        FileOperationError: If the file is not a readable image.
    """
    try:
        from PIL import Image  # noqa: PLC0415
        with Image.open(image_path) as img:
            return img.size
    except Exception as exc:  # noqa: BLE001
        raise FileOperationError(f"Could not read image dimensions: {exc}") from exc
