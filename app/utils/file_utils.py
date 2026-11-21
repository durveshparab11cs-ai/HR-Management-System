"""
app/utils/file_utils.py
========================
File upload validation, path management, and cleanup utilities.

All file paths returned are relative to the UPLOAD_FOLDER for
portability. Never store absolute filesystem paths in the database.
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.constants.limits import Limits
from app.core.exceptions import FileOperationError


def get_upload_folder(subfolder: str = "") -> Path:
    """
    Resolve the absolute upload folder path, creating it if needed.

    Args:
        subfolder: Optional subdirectory within the upload folder
                   (e.g., 'profile_photos', 'documents').

    Returns:
        Resolved absolute Path object.
    """
    from flask import current_app  # noqa: PLC0415
    base = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target = base / subfolder if subfolder else base
    target.mkdir(parents=True, exist_ok=True)
    return target


def allowed_image(filename: str) -> bool:
    """
    Check whether a filename has an allowed image extension.

    Args:
        filename: Original filename from the upload.

    Returns:
        True if the extension is in ALLOWED_IMAGE_EXTENSIONS.
    """
    ext = _get_extension(filename)
    return ext in Limits.File.__dict__.get(
        "ALLOWED_IMAGE_EXTENSIONS",
        {"png", "jpg", "jpeg", "gif", "webp"},
    )


def allowed_document(filename: str) -> bool:
    """
    Check whether a filename has an allowed document extension.

    Args:
        filename: Original filename from the upload.

    Returns:
        True if the extension is in ALLOWED_DOCUMENT_EXTENSIONS.
    """
    ext = _get_extension(filename)
    return ext in {"pdf", "doc", "docx", "xls", "xlsx", "csv"}


def save_file(
    file: FileStorage,
    subfolder: str,
    max_bytes: int = Limits.File.MAX_DOCUMENT_BYTES,
    allowed_extensions: Optional[set] = None,
) -> str:
    """
    Validate and save an uploaded file securely.
    Seamlessly routes through S3StorageService if AWS S3 is enabled,
    or local filesystem if in development.
    """
    from app.services.s3_storage_service import storage_service
    if storage_service.use_s3:
        try:
            return storage_service.upload_file(file, folder=subfolder, allowed_extensions=allowed_extensions, max_bytes=max_bytes)
        except Exception as exc:
            raise FileOperationError(f"Cloud upload failed: {exc}") from exc

    if not file or not file.filename:
        raise FileOperationError("No file provided.")

    original_name = secure_filename(file.filename)
    ext = _get_extension(original_name)

    if allowed_extensions and ext not in allowed_extensions:
        raise FileOperationError(
            f"File type '.{ext}' is not allowed. "
            f"Accepted: {', '.join(sorted(allowed_extensions))}"
        )

    # Check file size by seeking to end
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)     # Reset

    if file_size > max_bytes:
        mb = max_bytes / (1024 * 1024)
        raise FileOperationError(f"File exceeds the maximum size of {mb:.0f} MB.")

    # Generate collision-resistant filename
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = get_upload_folder(subfolder)
    absolute_path = upload_dir / unique_filename

    try:
        file.save(str(absolute_path))
    except OSError as exc:
        raise FileOperationError(f"Failed to save file: {exc}") from exc

    # Return path relative to UPLOAD_FOLDER for storage
    return str(Path(subfolder) / unique_filename).replace("\\", "/")


def get_file_url(relative_path: str, expires_in: int = 3600) -> str:
    """Get public or presigned download URL for a file path/key."""
    from app.services.s3_storage_service import storage_service
    return storage_service.get_download_url(relative_path, expires_in=expires_in)


def delete_file(relative_path: str) -> bool:
    """
    Delete a file by its relative path from UPLOAD_FOLDER or S3.
    """
    from app.services.s3_storage_service import storage_service
    if storage_service.use_s3:
        return storage_service.delete_file(relative_path)

    from flask import current_app  # noqa: PLC0415
    base = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    target = base / relative_path

    if target.exists() and target.is_file():
        target.unlink()
        return True
    return False


def get_file_url(relative_path: Optional[str]) -> Optional[str]:
    """
    Build the URL for a stored file using Flask's url_for.

    Args:
        relative_path: Relative path as stored in the database.

    Returns:
        URL string or None if relative_path is falsy.
    """
    if not relative_path:
        return None
    from flask import url_for  # noqa: PLC0415
    return url_for("static", filename=f"uploads/{relative_path}")


def _get_extension(filename: str) -> str:
    """Extract and lowercase the file extension without the leading dot."""
    return Path(filename).suffix.lstrip(".").lower()
