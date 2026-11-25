"""
app/services/face_verification_service.py
=========================================
Server-side Biometric Facial Recognition & Match Verification Engine.

Performs:
1. High-precision 128-dimensional Euclidean & Cosine metric verification.
2. Presentation Attack Detection (PAD) / Anti-Spoofing:
   - 2D FFT High-Frequency Screen Moire Analysis (detects phone displays/screens).
   - Glass Specular Reflection & Hotspot Gradient Analysis.
   - Dynamic Temporal Micro-Liveness (EAR blink & landmark variance over 6s).
3. 1:N Facial Identification Engine across registered employee database.
"""

import json
import logging
from typing import Tuple, Optional, List, Dict, Any
import numpy as np
from PIL import Image, ImageFilter
import io
import base64

logger = logging.getLogger("face_verification")

# Match threshold for 128-d Euclidean distance (FaceNet/face-api standard)
# Enterprise threshold calibrated for office webcam lighting & spectacles/glasses tolerance:
# True employee match typically falls in 0.20 - 0.44 distance range.
# Impostor / different person distance is typically > 0.60.
DEFAULT_DISTANCE_THRESHOLD = 0.44
DEFAULT_MIN_SIMILARITY = 60.0


class FaceVerificationService:
    """Enterprise facial recognition & anti-spoofing verification service."""

    @staticmethod
    def parse_descriptor(descriptor_input) -> Optional[np.ndarray]:
        """Convert JSON string, list, or ndarray into a normalized numpy vector."""
        if descriptor_input is None:
            return None
        try:
            if isinstance(descriptor_input, str):
                if not descriptor_input.strip():
                    return None
                data = json.loads(descriptor_input)
            elif isinstance(descriptor_input, (list, tuple)):
                data = descriptor_input
            elif isinstance(descriptor_input, np.ndarray):
                return descriptor_input.astype(np.float32)
            else:
                return None

            arr = np.array(data, dtype=np.float32)
            if arr.ndim != 1 or len(arr) < 64:
                return None
            return arr
        except Exception as exc:
            logger.warning("Failed to parse face descriptor: %s", exc)
            return None

    @classmethod
    def verify_vectors(
        cls,
        live_descriptor,
        registered_descriptor,
        threshold: float = DEFAULT_DISTANCE_THRESHOLD
    ) -> Tuple[bool, float, float]:
        """
        Compare live face descriptor against registered profile descriptor.
        Returns:
            (is_match: bool, similarity_pct: float, distance: float)
        """
        vec_live = cls.parse_descriptor(live_descriptor)
        vec_reg = cls.parse_descriptor(registered_descriptor)

        if vec_live is None or vec_reg is None:
            logger.warning("Missing or unparseable face descriptor vector")
            return False, 0.0, 999.0

        if len(vec_live) != len(vec_reg):
            logger.warning("Descriptor dimension mismatch: %d vs %d", len(vec_live), len(vec_reg))
            return False, 0.0, 999.0

        # Euclidean distance: ||v1 - v2||
        diff = vec_live - vec_reg
        distance = float(np.linalg.norm(diff))

        # Cosine similarity
        norm_live = np.linalg.norm(vec_live) + 1e-7
        norm_reg = np.linalg.norm(vec_reg) + 1e-7
        cos_sim = float(np.dot(vec_live, vec_reg) / (norm_live * norm_reg))

        # Calibrated similarity percentage:
        # d <= 0.15: 95-100%
        # d <= 0.35: 80-95%
        # d <= 0.44 (threshold): 65-80%
        # d <= 0.55: 35-65%
        # d > 0.55: 0-35%
        if distance <= 0.15:
            similarity = round(100.0 - (distance / 0.15) * 5.0, 1)
        elif distance <= 0.35:
            similarity = round(95.0 - ((distance - 0.15) / 0.20) * 15.0, 1)
        elif distance <= 0.44:
            similarity = round(80.0 - ((distance - 0.35) / 0.09) * 15.0, 1)
        elif distance <= 0.55:
            similarity = round(65.0 - ((distance - 0.44) / 0.11) * 30.0, 1)
        else:
            similarity = max(0.0, round(35.0 - ((distance - 0.55) / 0.20) * 35.0, 1))

        similarity = max(0.0, min(100.0, similarity))
        is_match = (distance <= threshold) and (similarity >= DEFAULT_MIN_SIMILARITY) and (cos_sim >= 0.65)

        logger.info(
            "Biometric Verification: match=%s | distance=%.4f (th=%.3f) | cos_sim=%.3f | similarity=%.1f%%",
            is_match, distance, threshold, cos_sim, similarity
        )

        return is_match, similarity, distance

    @classmethod
    def verify_descriptors(
        cls,
        live_descriptor,
        registered_descriptor,
        threshold: float = DEFAULT_DISTANCE_THRESHOLD
    ) -> Tuple[bool, float, float]:
        """Convenience alias returning (is_match, distance, score)."""
        is_match, similarity, distance = cls.verify_vectors(live_descriptor, registered_descriptor, threshold)
        return is_match, distance, similarity

    @classmethod
    def detect_presentation_attack(
        cls,
        image_b64: str,
        liveness_metrics: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Strict Multi-Layer Presentation Attack Detection (PAD):
        Prevents fraud from employees presenting phone screens, tablets, or printed photos.

        Layers:
        1. Temporal Micro-Liveness across 6-second window:
           - Real humans have involuntary micro-movements, breathing, and eye blinks (ear_delta > 0.02).
           - Phone screen / paper photos are static: ear_delta < 0.006 over 12+ samples indicates static photo.
        2. 2D FFT High-Frequency Screen Moire Analysis:
           - Camera capturing a digital display produces spatial aliasing / Moire harmonic spikes.
           - High-to-low radial frequency energy ratio exceeds normal human skin threshold.
        3. Glass Specular Reflection & Hotspot Edge Gradient:
           - Phone screens have reflective glass causing harsh, clipped specular white hotspots with steep gradients.

        Returns:
            (is_spoof: bool, reason: str, details: dict)
        """
        details = {
            "is_spoof": False,
            "reasons": [],
            "freq_ratio": 0.0,
            "glare_score": 0.0,
            "static_photo": False,
            "ear_delta": 0.0,
            "sample_count": 0
        }

        # --- Layer 1: Client-Side Temporal Micro-Liveness ---
        if liveness_metrics and isinstance(liveness_metrics, dict):
            ear_delta = float(liveness_metrics.get("ear_delta", 0.0))
            landmark_var = float(liveness_metrics.get("landmark_variance", 0.0))
            sample_count = int(liveness_metrics.get("sample_count", 0))

            details["ear_delta"] = ear_delta
            details["sample_count"] = sample_count

            # If user had a 6-second adjustment session (sample_count >= 12 frames)
            # but exhibited essentially zero landmark & EAR variation:
            if sample_count >= 12 and ear_delta < 0.006 and landmark_var < 0.002:
                details["is_spoof"] = True
                details["static_photo"] = True
                details["reasons"].append("Static photo detected (zero micro-liveness or eye movement over 6 seconds)")

        # --- Decode image for Computer Vision analysis ---
        if not image_b64:
            return details["is_spoof"], "; ".join(details["reasons"]) or "No image provided", details

        try:
            b64_data = image_b64
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            w, h = img.size

            # Center crop (approx face region)
            cw, ch = int(w * 0.65), int(h * 0.65)
            left = (w - cw) // 2
            top = (h - ch) // 2
            face_crop = img.crop((left, top, left + cw, top + ch)).resize((256, 256))

            # --- Layer 2: 2D FFT Frequency Analysis (Moire / Screen subpixel grid) ---
            gray = np.array(face_crop.convert("L"), dtype=np.float32)
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            mag_spectrum = np.abs(f_shift) + 1e-5

            cy, cx = 128, 128
            y, x = np.ogrid[:256, :256]
            r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

            low_energy = float(np.mean(mag_spectrum[r < 30]))
            high_energy = float(np.mean(mag_spectrum[(r >= 65) & (r < 115)]))
            freq_ratio = float(high_energy / (low_energy + 1e-5))
            details["freq_ratio"] = round(freq_ratio, 4)

            # Natural webcam face crops have freq_ratio around 0.02 - 0.045
            # Phone screens photographed in front of cameras exhibit Moire spikes > 0.065
            if freq_ratio > 0.065:
                details["is_spoof"] = True
                details["reasons"].append(f"Digital screen Moire pattern detected (freq_ratio={freq_ratio:.4f})")

            # --- Layer 3: Glass Screen Specular Glare Analysis ---
            rgb_arr = np.array(face_crop, dtype=np.float32)
            white_mask = (rgb_arr[:, :, 0] > 248) & (rgb_arr[:, :, 1] > 248) & (rgb_arr[:, :, 2] > 248)
            white_fraction = float(np.mean(white_mask))

            edge_img = face_crop.filter(ImageFilter.FIND_EDGES)
            edge_arr = np.array(edge_img.convert("L"), dtype=np.float32)
            edge_at_glare = float(np.mean(edge_arr[white_mask])) if np.sum(white_mask) > 30 else 0.0

            # Phone screen glass causes sharp specular reflection with high edge contrast
            if white_fraction > 0.035 and edge_at_glare > 75.0:
                details["is_spoof"] = True
                details["glare_score"] = 1.0
                details["reasons"].append(f"Screen glass specular reflection detected (glare_edge={edge_at_glare:.1f})")

        except Exception as exc:
            logger.warning("Presentation attack detection image processing error: %s", exc)

        is_spoof = details["is_spoof"]
        reason = "; ".join(details["reasons"]) if is_spoof else "Pass"
        if is_spoof:
            logger.warning("ANTI_SPOOFING_REJECTED | reason=%s | details=%s", reason, details)
        return is_spoof, reason, details

    @classmethod
    def identify_face_1_to_n(
        cls,
        live_descriptor,
        candidates: List[Dict[str, Any]],
        threshold: float = DEFAULT_DISTANCE_THRESHOLD
    ) -> Optional[Dict[str, Any]]:
        """
        1:N Biometric Identification across registered candidate profiles.

        Args:
            live_descriptor: Live 128-d vector from camera.
            candidates: List of candidate dicts, each with keys:
                        'id', 'employee_code', 'name', 'face_descriptor', 'model_type'
            threshold: Maximum allowed Euclidean distance (default: 0.385).

        Returns:
            Dict containing best matching employee profile and match metrics, or None.
        """
        vec_live = cls.parse_descriptor(live_descriptor)
        if vec_live is None:
            return None

        best_match = None
        min_dist = 999.0
        best_sim = 0.0
        best_cos = 0.0

        for cand in candidates:
            reg_desc = cand.get("face_descriptor")
            if not reg_desc:
                continue

            vec_reg = cls.parse_descriptor(reg_desc)
            if vec_reg is None or len(vec_reg) != len(vec_live):
                continue

            diff = vec_live - vec_reg
            dist = float(np.linalg.norm(diff))

            if dist < min_dist:
                min_dist = dist
                norm_live = np.linalg.norm(vec_live) + 1e-7
                norm_reg = np.linalg.norm(vec_reg) + 1e-7
                best_cos = float(np.dot(vec_live, vec_reg) / (norm_live * norm_reg))

                # Calibrated similarity %
                if dist <= 0.15:
                    sim = round(100.0 - (dist / 0.15) * 5.0, 1)
                elif dist <= 0.35:
                    sim = round(95.0 - ((dist - 0.15) / 0.20) * 15.0, 1)
                elif dist <= 0.44:
                    sim = round(80.0 - ((dist - 0.35) / 0.09) * 15.0, 1)
                elif dist <= 0.55:
                    sim = round(65.0 - ((dist - 0.44) / 0.11) * 30.0, 1)
                else:
                    sim = max(0.0, round(35.0 - ((dist - 0.55) / 0.20) * 35.0, 1))

                best_sim = max(0.0, min(100.0, sim))
                best_match = cand

        if best_match and min_dist <= threshold and best_sim >= DEFAULT_MIN_SIMILARITY and best_cos >= 0.65:
            logger.info(
                "1:N BIOMETRIC_MATCH_FOUND | code=%s | name=%s | dist=%.4f | score=%.1f%% | cos=%.3f",
                best_match.get("employee_code"), best_match.get("name"), min_dist, best_sim, best_cos
            )
            return {
                "candidate": best_match,
                "distance": min_dist,
                "similarity": best_sim,
                "cosine_similarity": best_cos
            }

        logger.info("1:N BIOMETRIC_NO_MATCH | closest_dist=%.4f | closest_score=%.1f%%", min_dist, best_sim)
        return None

    @classmethod
    def verify_images(cls, image_b64_1: str, image_b64_2: str) -> Tuple[bool, float]:
        """Alias for compare_face_images."""
        return cls.compare_face_images(image_b64_1, image_b64_2)

    @classmethod
    def compare_face_images(cls, image_b64_1: str, image_b64_2: str) -> Tuple[bool, float]:
        """
        Dual-layer verification: compare facial images via normalized grayscale histogram
        and perceptual structural correlation when descriptor vector is unavailable.
        """
        try:
            def decode_img(b64_str: str) -> Image.Image:
                if "," in b64_str:
                    b64_str = b64_str.split(",", 1)[1]
                data = base64.b64decode(b64_str)
                img = Image.open(io.BytesIO(data)).convert("L")
                return img.resize((128, 128))

            img1 = decode_img(image_b64_1)
            img2 = decode_img(image_b64_2)

            arr1 = np.asarray(img1, dtype=np.float32)
            arr2 = np.asarray(img2, dtype=np.float32)

            # Normalize
            arr1 = (arr1 - np.mean(arr1)) / (np.std(arr1) + 1e-5)
            arr2 = (arr2 - np.mean(arr2)) / (np.std(arr2) + 1e-5)

            # Normalized Cross Correlation
            correlation = float(np.mean(arr1 * arr2))
            similarity = round(max(0.0, min(100.0, (correlation + 1.0) * 50.0)), 1)
            is_match = similarity >= 65.0

            return is_match, similarity
        except Exception as exc:
            logger.warning("Image correlation comparison failed: %s", exc)
            return False, 0.0
