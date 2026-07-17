"""
attendance/photo_service.py
=============================
AttendancePhoto service.

Single responsibility: validate, store, and retrieve attendance proof
photos. Does NOT perform any biometric analysis — photos are proof
records only.

File structure:
    uploads/attendance/<employee_id>/<date_YYYY-MM-DD>_<uuid8>.jpg
"""

import logging
import os
import uuid
from datetime import date
from pathlib import Path
from typing import Optional, Tuple

from flask import current_app, request
from werkzeug.datastructures import FileStorage

from app.extensions.database import db
from app.models.attendance_photo import AttendancePhoto

logger = logging.getLogger("attendance")

ALLOWED_EXTENSIONS: frozenset = frozenset({"jpg", "jpeg", "png", "webp"})
MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB


class PhotoService:
    """
    Handles saving and retrieval of attendance proof photos.

    Usage:
        svc = PhotoService()
        ok, msg, photo = svc.save_check_in_photo(attendance, employee_id, file)
    """

    def save_check_in_photo(
        self,
        attendance,
        employee_id: int,
        file: FileStorage,
    ) -> Tuple[bool, str, Optional[AttendancePhoto]]:
        """
        Validate and persist a check-in proof photo.

        Args:
            attendance:  Attendance model instance that owns this photo.
            employee_id: Employee's ID (for folder organisation).
            file:        Werkzeug FileStorage from request.files.

        Returns:
            (success, message, AttendancePhoto_or_None)
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
            logger.warning("PHOTO_UPLOAD | emp=%s | FAIL: size=%d", employee_id, size)
            return False, f"Photo exceeds 5 MB limit ({size / 1024 / 1024:.1f} MB).", None

        logger.info(
            "PHOTO_UPLOAD | emp=%s | att=%s | filename=%s | ext=%s | size=%d | content_type=%s",
            employee_id, attendance.id, file.filename, ext, size, file.content_type,
        )

        # Verify actual image content (prevent polyglot uploads)
        if not self._is_valid_image(file):
            logger.warning("PHOTO_UPLOAD | emp=%s | FAIL: magic bytes invalid", employee_id)
            return False, "File does not appear to be a valid image. Please select a JPG, PNG, or WEBP file.", None

        # Check for existing photo on this attendance record
        existing = AttendancePhoto.query.filter_by(attendance_id=attendance.id).first()
        if existing:
            logger.info("PHOTO_UPLOAD | emp=%s | att=%s | FAIL: already uploaded", employee_id, attendance.id)
            return False, "A photo has already been uploaded for this check-in.", None

        # Build storage path — resolve to absolute so saves work on Render
        today_str = date.today().isoformat()
        unique_id = uuid.uuid4().hex[:8]
        filename  = f"{today_str}_{unique_id}.{ext}"
        subfolder = f"attendance/{employee_id}"
        rel_path  = f"{subfolder}/{filename}"

        raw_folder  = current_app.config.get("UPLOAD_FOLDER", "./instance/uploads")
        upload_base = Path(raw_folder)
        if not upload_base.is_absolute():
            # Strip leading "./" if present, then join to app root parent
            # current_app.root_path = .../smart_hrms/app
            # parent                = .../smart_hrms
            clean = raw_folder
            if clean.startswith("./"):
                clean = clean[2:]
            upload_base = Path(current_app.root_path).parent / clean
        upload_base = upload_base.resolve()

        logger.info("PHOTO_UPLOAD | upload_base=%s", upload_base)

        dest_dir    = upload_base / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path   = dest_dir / filename

        try:
            file.seek(0)
            file.save(str(dest_path))
        except OSError as exc:
            logger.error("Photo save failed: %s", exc)
            return False, "Failed to save photo. Please try again.", None

        # Persist record
        try:
            photo = AttendancePhoto(
                attendance_id=attendance.id,
                employee_id=employee_id,
                file_path=rel_path,
                original_filename=file.filename[:255],
                file_size_bytes=size,
                mime_type=file.content_type,
                ip_address=self._get_ip(),
            )
            db.session.add(photo)
            db.session.commit()
            logger.info("PHOTO_SAVED | emp=%s | att=%s | path=%s", employee_id, attendance.id, rel_path)
            return True, "Photo uploaded successfully.", photo
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logger.error("Photo DB record failed: %s", exc)
            # Clean up file on DB failure
            if dest_path.exists():
                dest_path.unlink(missing_ok=True)
            return False, "Failed to record photo. Please try again.", None

    def get_photo_url(self, photo: AttendancePhoto) -> Optional[str]:
        """Build a URL for serving a stored attendance photo."""
        if not photo or not photo.file_path:
            return None
        from flask import url_for  # noqa: PLC0415
        return url_for("attendance.serve_photo", filename=photo.file_path)

    def delete_photo(self, photo: AttendancePhoto) -> bool:
        """
        Remove an attendance photo file and its database record.

        Args:
            photo: AttendancePhoto model instance.

        Returns:
            True on success.
        """
        try:
            raw_folder  = current_app.config.get("UPLOAD_FOLDER", "./instance/uploads")
            upload_base = Path(raw_folder)
            if not upload_base.is_absolute():
                clean = raw_folder
                if clean.startswith("./"):
                    clean = clean[2:]
                upload_base = Path(current_app.root_path).parent / clean
            upload_base = upload_base.resolve()
            file_path   = upload_base / photo.file_path
            if file_path.exists():
                file_path.unlink()
            db.session.delete(photo)
            db.session.commit()
            return True
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logger.error("Photo delete failed: %s", exc)
            return False

    def _is_valid_image(self, file: FileStorage) -> bool:
        """
        Verify file is a real image by checking magic bytes in the header.
        Uses raw bytes instead of Pillow to avoid false rejections on
        progressive JPEGs, HEIC-converted files, and mobile camera photos
        that have unusual EXIF structures.
        Falls back to True (trust extension check) if read fails.
        """
        MAGIC = {
            b'\xff\xd8\xff': 'jpeg',       # JPEG
            b'\x89PNG': 'png',             # PNG
            b'RIFF': 'webp_candidate',     # WebP starts with RIFF....WEBP
            b'GIF8': 'gif',               # GIF87a / GIF89a
        }
        try:
            file.seek(0)
            header = file.read(12)
            file.seek(0)
            if not header:
                return False
            for magic, _ in MAGIC.items():
                if header[:len(magic)] == magic:
                    # Extra check for WebP
                    if magic == b'RIFF':
                        return header[8:12] == b'WEBP'
                    return True
            # Unknown magic — reject
            logger.warning("PHOTO_UNKNOWN_MAGIC | first12=%r", header[:12])
            return False
        except Exception as exc:  # noqa: BLE001
            logger.warning("PHOTO_MAGIC_CHECK_FAILED | %s — accepting on extension", exc)
            file.seek(0)
            return True  # Trust the extension check rather than blocking valid photos

    def _get_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For", "")
        return xff.split(",")[0].strip() if xff else (request.remote_addr or "unknown")
