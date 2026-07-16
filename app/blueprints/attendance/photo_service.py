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
            return False, "No photo file provided.", None

        # Extension check
        ext = Path(file.filename).suffix.lstrip(".").lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Invalid file type '.{ext}'. Only JPG, PNG, WEBP allowed.", None

        # Size check
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_BYTES:
            return False, f"Photo exceeds 5 MB limit ({size / 1024 / 1024:.1f} MB).", None

        # Verify actual image content (prevent polyglot uploads)
        if not self._is_valid_image(file):
            return False, "File does not appear to be a valid image.", None

        # Check for existing photo on this attendance record
        existing = AttendancePhoto.query.filter_by(attendance_id=attendance.id).first()
        if existing:
            return False, "A photo has already been uploaded for this check-in.", None

        # Build storage path
        today_str = date.today().isoformat()
        unique_id = uuid.uuid4().hex[:8]
        filename  = f"{today_str}_{unique_id}.{ext}"
        subfolder = f"attendance/{employee_id}"
        rel_path  = f"{subfolder}/{filename}"

        upload_base = Path(current_app.config.get("UPLOAD_FOLDER", "./instance/uploads")).resolve()
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
            upload_base = Path(current_app.config.get("UPLOAD_FOLDER", "./instance/uploads")).resolve()
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
        """Verify file header bytes to detect non-image uploads."""
        try:
            from PIL import Image
            file.seek(0)
            with Image.open(file) as img:
                img.verify()
            file.seek(0)
            return True
        except Exception:  # noqa: BLE001
            file.seek(0)
            return False

    def _get_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For", "")
        return xff.split(",")[0].strip() if xff else (request.remote_addr or "unknown")
