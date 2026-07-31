"""
proof_image_generator.py — Professional Attendance Proof Image Generator
=========================================================================

Generates enterprise-quality JPEG attendance proof images using Pillow.

Each image contains:
- Employee selfie (centered with border)
- Smart HRMS branding/logo
- Employee info (name, code, department, designation)
- Office name and address
- Check-In or Check-Out badge (color-coded)
- IST timestamp
- GPS coordinates, accuracy, distance from office, allowed radius
- Device information (browser, platform)
- QR code containing attendance ID

Output: 1200x1600px JPEG (landscape → portrait for mobile readability)

Usage:
    gen = ProofImageGenerator()
    proof_jpeg_base64 = gen.generate(
        selfie_base64='data:image/jpeg;base64,...',
        employee_name='John Doe',
        employee_code='EMP001',
        department='Engineering',
        designation='Senior Engineer',
        office_name='Pune Office',
        office_address='123 Business Park, Pune',
        check_type='checkin',  # or 'checkout'
        latitude=18.5204,
        longitude=73.8567,
        accuracy=25.0,
        distance_metres=15.5,
        allowed_radius=100,
        device_info='Chrome 120 / Windows 10'
    )
"""

import base64
import io
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import qrcode

logger = logging.getLogger("attendance")


class ProofImageGenerator:
    """Generate professional attendance proof images with employee info and QR code."""

    # ─ Image dimensions ─
    WIDTH = 1200
    HEIGHT = 1600

    # ─ Colors ─
    COLOR_NAVY = (26, 60, 110)
    COLOR_LIGHT_GRAY = (248, 250, 252)
    COLOR_DARK_GRAY = (51, 65, 85)
    COLOR_MEDIUM_GRAY = (100, 116, 139)
    COLOR_LIGHT_TEXT = (209, 213, 219)
    COLOR_GREEN = (16, 185, 129)
    COLOR_BLUE = (59, 130, 246)
    COLOR_RED = (239, 68, 68)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BORDER = (229, 231, 235)

    # ─ Padding and spacing ─
    MARGIN_TOP = 40
    MARGIN_SIDE = 40
    SECTION_GAP = 30

    def __init__(self):
        """Initialize the generator with font paths."""
        # Font paths for different OS (Windows, Linux, macOS)
        font_paths = [
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux (Debian/Ubuntu)
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux (alternative)
            "/System/Library/Fonts/Arial.ttf",  # macOS
        ]

        # Try to load system fonts; fall back to default if not available
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 14)
                logger.info("Loaded font from: %s", font_path)
                break
            except (IOError, OSError):
                continue

        if font is None:
            logger.warning("System fonts not found, using default PIL font")
            self.font_title = ImageFont.load_default()
            self.font_subtitle = ImageFont.load_default()
            self.font_text = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_tiny = ImageFont.load_default()
        else:
            # Use the found font with different sizes
            base_path = font_path
            try:
                self.font_title = ImageFont.truetype(base_path, 32)
                self.font_subtitle = ImageFont.truetype(base_path, 18)
                self.font_text = ImageFont.truetype(base_path, 14)
                self.font_small = ImageFont.truetype(base_path, 11)
                self.font_tiny = ImageFont.truetype(base_path, 9)
            except (IOError, OSError):
                logger.warning("Failed to load font sizes, using default PIL font")
                self.font_title = ImageFont.load_default()
                self.font_subtitle = ImageFont.load_default()
                self.font_text = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
                self.font_tiny = ImageFont.load_default()

    def generate(
        self,
        selfie_base64,
        employee_name,
        employee_code,
        department,
        designation,
        office_name,
        office_address,
        check_type,
        latitude,
        longitude,
        accuracy,
        distance_metres,
        allowed_radius,
        device_info,
        attendance_id=None,
    ):
        """
        Generate professional attendance proof image.

        Args:
            selfie_base64 (str): Base64-encoded selfie image (JPEG or PNG)
            employee_name (str): Full employee name
            employee_code (str): Employee ID code
            department (str): Department name
            designation (str): Job designation
            office_name (str): Office location name
            office_address (str): Full office address
            check_type (str): 'checkin' or 'checkout'
            latitude (float): Employee GPS latitude
            longitude (float): Employee GPS longitude
            accuracy (float): GPS accuracy in metres
            distance_metres (float): Distance from office in metres
            allowed_radius (int): Allowed geofence radius in metres
            device_info (str): Device info string (e.g., "Chrome 120 / Windows 10")
            attendance_id (str, optional): Attendance record ID for QR code

        Returns:
            str: Base64-encoded JPEG data URL (e.g., 'data:image/jpeg;base64,...')
        """
        logger.info("Starting proof image generation for employee: %s", employee_name)

        # Create blank canvas
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.COLOR_WHITE)
        draw = ImageDraw.Draw(img)

        # ─ 1. HEADER SECTION (Blue background) ─
        self._draw_header(
            img, draw, check_type, office_name
        )

        # ─ 2. EMPLOYEE SELFIE (centered) ─
        selfie_y = self._draw_selfie(img, selfie_base64)

        # ─ 3. EMPLOYEE INFO SECTION ─
        info_y = self._draw_employee_info(
            draw, selfie_y, employee_name, employee_code, department, designation
        )

        # ─ 4. OFFICE INFO ─
        office_y = self._draw_office_info(draw, info_y, office_name, office_address)

        # ─ 5. GPS INFO ─
        gps_y = self._draw_gps_info(
            draw, office_y, latitude, longitude, accuracy, distance_metres, allowed_radius
        )

        # ─ 6. DEVICE INFO ─
        device_y = self._draw_device_info(draw, gps_y, device_info)

        # ─ 7. TIMESTAMP (IST) ─
        ts_y = self._draw_timestamp(draw, device_y)

        # ─ 8. QR CODE ─
        self._draw_qr_code(img, ts_y, attendance_id or employee_code)

        # ─ 9. FOOTER ─
        self._draw_footer(img, draw)

        # Convert to JPEG base64
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95)
        jpeg_bytes = output.getvalue()
        base64_str = base64.b64encode(jpeg_bytes).decode("utf-8")

        logger.info("Proof image generated successfully (size: %d bytes)", len(jpeg_bytes))
        return f"data:image/jpeg;base64,{base64_str}"

    def _draw_header(self, img, draw, check_type, office_name):
        """Draw header section with branding and check type badge."""
        # Blue background
        draw.rectangle(
            [(0, 0), (self.WIDTH, 120)],
            fill=self.COLOR_NAVY
        )

        # Logo text (Smart HRMS)
        logo_text = "Smart HRMS"
        draw.text(
            (self.MARGIN_SIDE, 20),
            logo_text,
            fill=self.COLOR_WHITE,
            font=self.font_subtitle,
        )

        # Badge (CHECK IN / CHECK OUT)
        badge_text = "CHECK IN" if check_type == "checkin" else "CHECK OUT"
        badge_color = self.COLOR_GREEN if check_type == "checkin" else self.COLOR_RED
        badge_x = self.WIDTH - self.MARGIN_SIDE - 200
        badge_y = 20

        draw.rectangle(
            [(badge_x, badge_y), (badge_x + 180, badge_y + 40)],
            fill=badge_color,
        )
        draw.text(
            (badge_x + 10, badge_y + 8),
            badge_text,
            fill=self.COLOR_WHITE,
            font=self.font_subtitle,
        )

    def _draw_selfie(self, img, selfie_base64):
        """Draw employee selfie with border."""
        try:
            # Decode base64 image
            if selfie_base64.startswith("data:image"):
                # Remove data URI prefix
                selfie_data = selfie_base64.split(",")[1]
            else:
                selfie_data = selfie_base64

            selfie_bytes = base64.b64decode(selfie_data)
            selfie_img = Image.open(io.BytesIO(selfie_bytes))

            # Resize to fit in the image
            selfie_size = 300
            selfie_img = selfie_img.resize(
                (selfie_size, selfie_size),
                Image.Resampling.LANCZOS
            )

            # Center horizontally
            selfie_x = (self.WIDTH - selfie_size) // 2
            selfie_y = 140

            # Draw border
            border_size = 8
            draw = ImageDraw.Draw(img)
            draw.rectangle(
                [
                    (selfie_x - border_size, selfie_y - border_size),
                    (selfie_x + selfie_size + border_size, selfie_y + selfie_size + border_size),
                ],
                fill=self.COLOR_NAVY,
            )

            # Paste selfie
            img.paste(selfie_img, (selfie_x, selfie_y))

            logger.info("Selfie pasted successfully at (%d, %d)", selfie_x, selfie_y)
            return selfie_y + selfie_size + 20

        except Exception as e:
            logger.error("Error pasting selfie: %s", str(e))
            return 140 + 300 + 20

    def _draw_employee_info(self, draw, y, name, code, dept, desig):
        """Draw employee information section."""
        x = self.MARGIN_SIDE
        gap = 10

        # Name (large)
        draw.text((x, y), name, fill=self.COLOR_DARK_GRAY, font=self.font_title)
        y += 40

        # Employee Code
        draw.text(
            (x, y),
            f"Employee Code: {code}",
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 25

        # Department
        draw.text(
            (x, y),
            f"Department: {dept}",
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 25

        # Designation
        draw.text(
            (x, y),
            f"Designation: {desig}",
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 30

        # Divider line
        draw.line(
            [(x, y), (self.WIDTH - x, y)],
            fill=self.COLOR_BORDER,
            width=2,
        )
        y += 20

        return y

    def _draw_office_info(self, draw, y, office_name, address):
        """Draw office information section."""
        x = self.MARGIN_SIDE

        draw.text(
            (x, y),
            "Office Location",
            fill=self.COLOR_DARK_GRAY,
            font=self.font_subtitle,
        )
        y += 25

        draw.text(
            (x, y),
            office_name,
            fill=self.COLOR_DARK_GRAY,
            font=self.font_text,
        )
        y += 20

        # Word-wrap address
        max_width = self.WIDTH - 2 * self.MARGIN_SIDE
        words = address.split()
        line = ""
        for word in words:
            test_line = line + (" " if line else "") + word
            bbox = draw.textbbox((0, 0), test_line, font=self.font_small)
            if bbox[2] - bbox[0] > max_width:
                if line:
                    draw.text((x, y), line, fill=self.COLOR_MEDIUM_GRAY, font=self.font_small)
                    y += 18
                line = word
            else:
                line = test_line
        if line:
            draw.text((x, y), line, fill=self.COLOR_MEDIUM_GRAY, font=self.font_small)
            y += 25

        # Divider
        draw.line(
            [(x, y), (self.WIDTH - x, y)],
            fill=self.COLOR_BORDER,
            width=2,
        )
        y += 20

        return y

    def _draw_gps_info(self, draw, y, lat, lon, acc, dist, radius):
        """Draw GPS verification section."""
        x = self.MARGIN_SIDE

        draw.text(
            (x, y),
            "GPS Verification",
            fill=self.COLOR_DARK_GRAY,
            font=self.font_subtitle,
        )
        y += 25

        # Latitude
        draw.text(
            (x, y),
            f"Latitude: {lat:.6f}°",
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 20

        # Longitude
        draw.text(
            (x, y),
            f"Longitude: {lon:.6f}°",
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 20

        # Accuracy
        draw.text(
            (x, y),
            f"GPS Accuracy: ±{acc:.1f}m",
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 20

        # Distance from office
        draw.text(
            (x, y),
            f"Distance from Office: {dist:.1f}m",
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 20

        # Allowed radius
        draw.text(
            (x, y),
            f"Allowed Radius: {radius}m",
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 25

        # Divider
        draw.line(
            [(x, y), (self.WIDTH - x, y)],
            fill=self.COLOR_BORDER,
            width=2,
        )
        y += 20

        return y

    def _draw_device_info(self, draw, y, device_info):
        """Draw device information."""
        x = self.MARGIN_SIDE

        draw.text(
            (x, y),
            "Device Information",
            fill=self.COLOR_DARK_GRAY,
            font=self.font_subtitle,
        )
        y += 25

        draw.text(
            (x, y),
            device_info,
            fill=self.COLOR_MEDIUM_GRAY,
            font=self.font_text,
        )
        y += 25

        # Divider
        draw.line(
            [(x, y), (self.WIDTH - x, y)],
            fill=self.COLOR_BORDER,
            width=2,
        )
        y += 20

        return y

    def _draw_timestamp(self, draw, y):
        """Draw IST timestamp."""
        x = self.MARGIN_SIDE

        draw.text(
            (x, y),
            "Timestamp (IST)",
            fill=self.COLOR_DARK_GRAY,
            font=self.font_subtitle,
        )
        y += 25

        # Current time in IST
        ist_time = datetime.utcnow() + __import__("datetime").timedelta(hours=5, minutes=30)
        time_str = ist_time.strftime("%d %b %Y • %I:%M:%S %p IST")

        draw.text(
            (x, y),
            time_str,
            fill=self.COLOR_DARK_GRAY,
            font=self.font_text,
        )
        y += 30

        return y

    def _draw_qr_code(self, img, y, qr_data):
        """Draw QR code."""
        try:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Resize QR code
            qr_size = 150
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

            # Center horizontally
            qr_x = (self.WIDTH - qr_size) // 2
            qr_y = y + 20

            img.paste(qr_img, (qr_x, qr_y))

            # Label below QR
            draw = ImageDraw.Draw(img)
            draw.text(
                (qr_x + 30, qr_y + qr_size + 10),
                "Attendance ID",
                fill=self.COLOR_MEDIUM_GRAY,
                font=self.font_tiny,
            )

            logger.info("QR code added at (%d, %d)", qr_x, qr_y)
        except Exception as e:
            logger.error("Error adding QR code: %s", str(e))

    def _draw_footer(self, img, draw):
        """Draw footer with branding."""
        footer_text = "Smart HRMS — Professional Attendance Management System"
        text_bbox = draw.textbbox((0, 0), footer_text, font=self.font_tiny)
        text_width = text_bbox[2] - text_bbox[0]
        x = (self.WIDTH - text_width) // 2
        y = self.HEIGHT - 30

        draw.text(
            (x, y),
            footer_text,
            fill=self.COLOR_LIGHT_TEXT,
            font=self.font_tiny,
        )
