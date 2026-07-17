"""
attendance/photo_service.py
=============================
AttendancePhoto service.

Storage strategy: photos are stored as base64 data URLs directly in
the PostgreSQL database (image_data column). This makes photos durable
across Render redeploys — Render's filesystem is ephemeral and is wiped
on every deploy, which would destroy any file-based uploads.

The file_path column is kept for backward compatibility but left empty
for new uploads.
"""

import base64
import logging
from pathlib import Path
from typing import Optional, Tuple

from flask import request
from werkzeug.datastructures import FileStorage

from app.extensions.database import db
from app.models.attendance_photo import AttendancePhoto

logger = logging.getLogger("attendance")

ALLOWED_EXTENSIONS: frozenset = frozenset({"jpg", "jpeg", "png", "webp"})
MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB

# MIME types mapped from extension
MIME_MAP = {
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "png":  "image/png",
    "webp": "image/webp",
}


class PhotoService:
    """
    Handles saving and retrieval of attendance proof photos.
    Photos are stored as base64 data URLs in PostgreSQL for Render compatibility.
    """

    def save_check_in_photo(
        self,
        attendance,
        employee_id: int,
        file: FileStorage,
    ) -> Tuple[bool, str, Optional[AttendancePhoto]]:
        """
        Validate and persist a check-in proof photo as base64 in the DB.
        """
        if not file or not file.filename:
            logger.warning("PHOTO_UPLOAD | emp=%s | att=%s | FAIL: no file", employee_id, attendance.id)
            return False, "No photo file provided.", None

        # Extension check
        ext = Path(file.filename).suffix.lstrip(".").lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning("PHOTO_UPLOAD | emp=%s | FAIL: bad ext=%s", employee_id, ext)
            return False, f"Invalid file type '{ext}'. Only JPG, PNG, WEBP allowed.", None

        # Size check
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_BYTES:
            logger.warning("PHOTO_UPLOAD | emp=%s | FAIL: size=%d bytes", employee_id, size)
            return False, f"Photo exceeds 5 MB limit ({size / 1024 / 1024:.1f} MB).", None

        logger.info(
            "PHOTO_UPLOAD | emp=%s | att=%s | filename=%s | ext=%s | size=%d | content_type=%s",
            employee_id, attendance.id, file.filename, ext, size, file.content_type,
        )

        # Magic-byte validation (no Pillow dependency)
        if not self._is_valid_image(file):
            logger.warning("PHOTO_UPLOAD | emp=%s | FAIL: magic bytes invalid", employee_id)
            return False, "File does not appear to be a valid image. Please select a JPG, PNG, or WEBP file.", None

        # Duplicate check — but allow replacement if old record has no base64 data
        # (happens when existing record was saved as a file that no longer exists
        # after a Render redeploy wiped the ephemeral filesystem)
        existing = AttendancePhoto.query.filter_by(attendance_id=attendance.id).first()
        if existing:
            if existing.image_data:
                # Already has valid base64 data — truly a duplicate
                logger.info("PHOTO_UPLOAD | emp=%s | att=%s | FAIL: already uploaded", employee_id, attendance.id)
                return False, "A photo has already been uploaded for this check-in.", None
            else:
                # Old file-based record with no image_data — delete it and replace
                logger.info(
                    "PHOTO_UPLOAD | emp=%s | att=%s | replacing stale file-based record (id=%s)",
                    employee_id, attendance.id, existing.id,
                )
                db.session.delete(existing)
                db.session.flush()  # ensure deleted before new insert

        # Read file bytes and encode as base64 data URL
        try:
            file.seek(0)
            raw_bytes = file.read()
            mime      = MIME_MAP.get(ext, "image/jpeg")
            b64       = base64.b64encode(raw_bytes).decode("utf-8")
            data_url  = f"data:{mime};base64,{b64}"
        except Exception as exc:
            logger.error("PHOTO_ENCODE_FAILED | emp=%s | %s", employee_id, exc)
            return False, "Failed to process photo. Please try again.", None

        # Persist to DB
        try:
            photo = AttendancePhoto(
                attendance_id=attendance.id,
                employee_id=employee_id,
                file_path="",           # empty — photo stored in image_data
                image_data=data_url,    # base64 data URL stored in DB
                original_filename=file.filename[:255],
                file_size_bytes=size,
                mime_type=mime,
                ip_address=self._get_ip(),
            )
            db.session.add(photo)
            db.session.commit()
            logger.info(
                "PHOTO_SAVED_DB | emp=%s | att=%s | size=%d | mime=%s",
                employee_id, attendance.id, size, mime,
            )
            return True, "Photo uploaded successfully.", photo
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logger.error("PHOTO_DB_SAVE_FAILED | emp=%s | %s", employee_id, exc)
            return False, "Failed to record photo. Please try again.", None

    def get_photo_url(self, photo: AttendancePhoto) -> Optional[str]:
        """
        Return the photo URL for the API response.
        For DB-stored photos, return the data URL directly.
        For old file-based photos, return the serve_photo URL.
        """
        if not photo:
            return None
        if photo.image_data:
            return photo.image_data          # data URL — no HTTP request needed
        if photo.file_path:
            from flask import url_for        # noqa: PLC0415
            return url_for("attendance.serve_photo", filename=photo.file_path)
        return None

    def delete_photo(self, photo: AttendancePhoto) -> bool:
        """Remove photo record from DB (and file if it exists)."""
        try:
            # Also delete file if it exists (backward compat)
            if photo.file_path:
                from flask import current_app  # noqa: PLC0415
                raw_folder = current_app.config.get("UPLOAD_FOLDER", "./instance/uploads")
                from pathlib import Path as _P  # noqa: PLC0415
                upload_base = _P(raw_folder)
                if not upload_base.is_absolute():
                    clean = raw_folder
                    if clean.startswith("./"):
                        clean = clean[2:]
                    upload_base = _P(current_app.root_path).parent / clean
                fp = upload_base.resolve() / photo.file_path
                if fp.exists():
                    fp.unlink(missing_ok=True)
            db.session.delete(photo)
            db.session.commit()
            return True
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logger.error("Photo delete failed: %s", exc)
            return False

    def _is_valid_image(self, file: FileStorage) -> bool:
        """Check magic bytes — no Pillow needed."""
        MAGIC = {
            b'\xff\xd8\xff': 'jpeg',
            b'\x89PNG':      'png',
            b'RIFF':         'webp',
            b'GIF8':         'gif',
        }
        try:
            file.seek(0)
            header = file.read(12)
            file.seek(0)
            if not header:
                return False
            for magic in MAGIC:
                if header[:len(magic)] == magic:
                    if magic == b'RIFF':
                        return header[8:12] == b'WEBP'
                    return True
            logger.warning("PHOTO_UNKNOWN_MAGIC | first12=%r", header[:12])
            return False
        except Exception as exc:  # noqa: BLE001
            logger.warning("PHOTO_MAGIC_CHECK_FAILED | %s — trusting extension", exc)
            file.seek(0)
            return True

    def _get_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For", "")
        return xff.split(",")[0].strip() if xff else (request.remote_addr or "unknown")
