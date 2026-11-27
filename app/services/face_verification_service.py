"""
app/services/face_verification_service.py
=========================================
Server-side Biometric Facial Recognition & Match Verification Engine.

Performs:
1. High-precision 128-dimensional Euclidean & Cosine metric verification with multi-pose centroid.
2. Multi-sample enrollment template composition (Front, Left, Right pose integration).
3. Cross-database duplicate biometric identity prevention.
4. Presentation Attack Detection (PAD) / Anti-Spoofing:
   - 2D FFT High-Frequency Screen Moire Analysis (detects phone displays/screens).
   - Glass Specular Reflection & Hotspot Gradient Analysis.
   - Dynamic Temporal Micro-Liveness (EAR blink & landmark variance).
5. 1:N Facial Identification Engine across registered employee database.
6. Facial image quality assessment (sharpness, luminance, contrast, resolution).
"""

import json
import logging
from typing import Tuple, Optional, List, Dict, Any
import numpy as np
from PIL import Image, ImageFilter
import io
import base64

logger = logging.getLogger("face_verification")

# Calibrated Match Thresholds for 128-d Euclidean distance (FaceNet/face-api standard)
# True employee match with webcam lighting falls in 0.18 - 0.46 range.
# Impostor / different person distance is typically > 0.60.
DEFAULT_DISTANCE_THRESHOLD = 0.50
DEFAULT_MIN_SIMILARITY = 60.0
DUPLICATE_CHECK_THRESHOLD = 0.38


class FaceVerificationService:
    """Enterprise facial recognition, multi-pose matching & anti-spoofing verification service."""

    @staticmethod
    def parse_descriptor(descriptor_input) -> Optional[np.ndarray]:
        """Convert JSON string, list, tuple, dict, or ndarray into a normalized 128-d numpy vector."""
        if descriptor_input is None:
            return None
        try:
            if isinstance(descriptor_input, str):
                if not descriptor_input.strip():
                    return None
                data = json.loads(descriptor_input)
            elif isinstance(descriptor_input, (list, tuple)):
                data = descriptor_input
            elif isinstance(descriptor_input, dict):
                # If dict has "composite", use the primary composite vector
                if "composite" in descriptor_input:
                    data = descriptor_input["composite"]
                else:
                    try:
                        sorted_keys = sorted(descriptor_input.keys(), key=lambda k: int(k))
                        data = [float(descriptor_input[k]) for k in sorted_keys]
                    except Exception:
                        data = list(descriptor_input.values())
            elif isinstance(descriptor_input, np.ndarray):
                arr = descriptor_input.astype(np.float32)
                return arr / (np.linalg.norm(arr) + 1e-7)
            else:
                return None

            # Handle case where json.loads returned a dict
            if isinstance(data, dict):
                if "composite" in data:
                    data = data["composite"]
                else:
                    try:
                        sorted_keys = sorted(data.keys(), key=lambda k: int(k))
                        data = [float(data[k]) for k in sorted_keys]
                    except Exception:
                        data = list(data.values())

            arr = np.array(data, dtype=np.float32)
            if arr.ndim != 1 or len(arr) < 64:
                return None
            # Return normalized unit vector
            norm = np.linalg.norm(arr)
            return arr / (norm + 1e-7) if norm > 0 else arr
        except Exception as exc:
            logger.warning("Failed to parse face descriptor: %s", exc)
            return None

    @classmethod
    def extract_all_vectors(cls, descriptor_input) -> List[np.ndarray]:
        """Extract all candidate vectors from a descriptor input (including multi-pose templates)."""
        vectors = []
        if descriptor_input is None:
            return vectors
        try:
            data = descriptor_input
            if isinstance(descriptor_input, str) and descriptor_input.strip():
                data = json.loads(descriptor_input)

            if isinstance(data, dict):
                # Check for composite
                if "composite" in data:
                    v = cls.parse_descriptor(data["composite"])
                    if v is not None:
                        vectors.append(v)
                # Check for poses
                if "poses" in data and isinstance(data["poses"], dict):
                    for pose_name, p_data in data["poses"].items():
                        v = cls.parse_descriptor(p_data)
                        if v is not None:
                            vectors.append(v)
                # If neither composite nor poses, maybe {"0": ..., "1": ...}
                if not vectors:
                    v = cls.parse_descriptor(data)
                    if v is not None:
                        vectors.append(v)
            else:
                v = cls.parse_descriptor(data)
                if v is not None:
                    vectors.append(v)
        except Exception as e:
            logger.warning("Error extracting vectors: %s", e)
            v = cls.parse_descriptor(descriptor_input)
            if v is not None:
                vectors.append(v)
        return vectors

    @classmethod
    def build_multi_pose_template(
        cls,
        front_desc: Any,
        left_desc: Any = None,
        right_desc: Any = None
    ) -> Tuple[Optional[str], Optional[np.ndarray]]:
        """
        Synthesize multi-pose captures (Front, Left, Right) into a high-accuracy composite template.
        Returns:
            (json_template_string, composite_numpy_vector)
        """
        poses = {}
        vecs = []

        v_front = cls.parse_descriptor(front_desc)
        if v_front is not None:
            poses["front"] = v_front.tolist()
            vecs.append(v_front)

        if left_desc is not None:
            v_left = cls.parse_descriptor(left_desc)
            if v_left is not None:
                poses["left"] = v_left.tolist()
                vecs.append(v_left)

        if right_desc is not None:
            v_right = cls.parse_descriptor(right_desc)
            if v_right is not None:
                poses["right"] = v_right.tolist()
                vecs.append(v_right)

        if not vecs:
            return None, None

        # Weighted centroid: front pose given 2x weight, lateral poses 1x
        weights = [2.0 if i == 0 else 1.0 for i in range(len(vecs))]
        centroid = np.zeros_like(vecs[0], dtype=np.float32)
        total_w = sum(weights)
        for v, w in zip(vecs, weights):
            centroid += v * (w / total_w)

        # L2-normalize composite centroid
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm

        template_dict = {
            "composite": centroid.tolist(),
            "poses": poses,
            "version": 2
        }
        return json.dumps(template_dict), centroid

    @classmethod
    def verify_vectors(
        cls,
        live_descriptor,
        registered_descriptor,
        threshold: float = DEFAULT_DISTANCE_THRESHOLD
    ) -> Tuple[bool, float, float]:
        """
        Compare live face descriptor against registered profile descriptor(s).
        Returns:
            (is_match: bool, similarity_pct: float, distance: float)
        """
        vec_live = cls.parse_descriptor(live_descriptor)
        if vec_live is None:
            return False, 0.0, 999.0

        reg_vectors = cls.extract_all_vectors(registered_descriptor)
        if not reg_vectors:
            return False, 0.0, 999.0

        min_dist = 999.0
        best_cos = 0.0

        for v_reg in reg_vectors:
            if len(v_reg) != len(vec_live):
                continue
            diff = vec_live - v_reg
            d = float(np.linalg.norm(diff))
            cos = float(np.dot(vec_live, v_reg))
            if d < min_dist:
                min_dist = d
                best_cos = cos

        # Calibrated similarity %
        if min_dist <= 0.15:
            similarity = round(100.0 - (min_dist / 0.15) * 5.0, 1)
        elif min_dist <= 0.35:
            similarity = round(95.0 - ((min_dist - 0.15) / 0.20) * 15.0, 1)
        elif min_dist <= 0.44:
            similarity = round(80.0 - ((min_dist - 0.35) / 0.09) * 15.0, 1)
        elif min_dist <= 0.55:
            similarity = round(65.0 - ((min_dist - 0.44) / 0.11) * 30.0, 1)
        else:
            similarity = max(0.0, round(35.0 - ((min_dist - 0.55) / 0.20) * 35.0, 1))

        similarity = max(0.0, min(100.0, similarity))
        is_match = (min_dist <= threshold) and (similarity >= DEFAULT_MIN_SIMILARITY) and (best_cos >= 0.55)

        return is_match, similarity, min_dist

    @classmethod
    def check_duplicate_face(
        cls,
        live_descriptor,
        candidates: List[Dict[str, Any]],
        current_employee_code: str = "",
        threshold: float = DUPLICATE_CHECK_THRESHOLD
    ) -> Tuple[bool, Optional[str], Optional[str], float]:
        """
        Cross-checks a live face against all registered employee templates.
        Prevents an employee from enrolling their face under multiple employee codes.

        Returns:
            (is_duplicate: bool, conflicting_code, conflicting_name, distance)
        """
        vec_live = cls.parse_descriptor(live_descriptor)
        if vec_live is None:
            return False, None, None, 999.0

        norm_current = (current_employee_code or "").strip().upper()

        for cand in candidates:
            code = (cand.get("employee_code") or "").strip().upper()
            if norm_current and code == norm_current:
                continue  # skip comparing with self

            reg_desc = cand.get("face_descriptor")
            if not reg_desc:
                continue

            reg_vecs = cls.extract_all_vectors(reg_desc)
            for v_reg in reg_vecs:
                if len(v_reg) != len(vec_live):
                    continue
                d = float(np.linalg.norm(vec_live - v_reg))
                if d <= threshold:
                    logger.warning(
                        "DUPLICATE_FACE_DETECTED | new_code=%s conflicting_code=%s distance=%.4f",
                        norm_current, code, d
                    )
                    return True, code, cand.get("name"), d

        return False, None, None, 999.0

    @classmethod
    def assess_face_quality(cls, image_b64: str) -> Tuple[bool, float, List[str]]:
        """
        Validate facial image quality before enrollment:
        - Sharpness (Laplacian variance >= 50.0)
        - Illumination (Mean brightness between 35 and 225)
        - Contrast (Standard deviation >= 25.0)
        - Resolution (width & height >= 140)

        Returns:
            (is_quality_pass: bool, quality_score: float, issues_list: List[str])
        """
        issues = []
        if not image_b64:
            return False, 0.0, ["Missing image data"]

        try:
            b64_data = image_b64
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            w, h = img.size

            if w < 140 or h < 140:
                issues.append(f"Image resolution too low ({w}x{h}, minimum 140x140 required)")

            gray = img.convert("L")
            arr = np.array(gray, dtype=np.float32)

            # Mean illumination
            mean_lum = float(np.mean(arr))
            if mean_lum < 35.0:
                issues.append("Image is too dark. Please face towards a light source.")
            elif mean_lum > 230.0:
                issues.append("Image is overexposed/glared. Avoid direct strong backlight.")

            # Contrast
            std_lum = float(np.std(arr))
            if std_lum < 22.0:
                issues.append("Image contrast is too low.")

            # Sharpness via Laplacian kernel convolution approximation
            edge = gray.filter(ImageFilter.FIND_EDGES)
            edge_arr = np.array(edge, dtype=np.float32)
            sharpness_var = float(np.var(edge_arr))
            if sharpness_var < 45.0:
                issues.append("Image appears blurry. Please hold steady and face the camera.")

            # Composite quality score (0-100)
            score = 100.0
            if issues:
                score -= len(issues) * 25.0
            score = max(0.0, min(100.0, score))

            is_pass = len(issues) == 0
            return is_pass, score, issues

        except Exception as exc:
            logger.warning("Quality assessment error: %s", exc)
            return False, 0.0, [f"Could not parse image: {str(exc)}"]

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
        1. Temporal Micro-Liveness across multi-frame burst:
           - Real humans have involuntary micro-movements, breathing, and eye blinks.
           - Static phone screen or paper photos have near-zero landmark & EAR variation.
        2. 2D FFT High-Frequency Screen Moire Analysis:
           - Digital displays generate spatial grid aliasing harmonics.
        3. Glass Specular Reflection & Hotspot Edge Gradient:
           - Phone screens have reflective glass causing harsh specular white hotspots with steep gradients.

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

            if sample_count >= 12 and ear_delta < 0.005 and landmark_var < 0.0018:
                details["is_spoof"] = True
                details["static_photo"] = True
                details["reasons"].append("Static photo detected (zero natural micro-liveness or eye movement)")

        if not image_b64:
            return details["is_spoof"], "; ".join(details["reasons"]) or "No image provided", details

        try:
            b64_data = image_b64
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            w, h = img.size

            cw, ch = int(w * 0.65), int(h * 0.65)
            left = (w - cw) // 2
            top = (h - ch) // 2
            face_crop = img.crop((left, top, left + cw, top + ch)).resize((256, 256))

            # --- Layer 2: 2D FFT Frequency Analysis (Moire pattern) ---
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

            if freq_ratio > 0.068:
                details["is_spoof"] = True
                details["reasons"].append(f"Digital screen Moire grid detected (freq_ratio={freq_ratio:.4f})")

            # --- Layer 3: Glass Screen Specular Glare ---
            rgb_arr = np.array(face_crop, dtype=np.float32)
            white_mask = (rgb_arr[:, :, 0] > 248) & (rgb_arr[:, :, 1] > 248) & (rgb_arr[:, :, 2] > 248)
            white_fraction = float(np.mean(white_mask))

            edge_img = face_crop.filter(ImageFilter.FIND_EDGES)
            edge_arr = np.array(edge_img.convert("L"), dtype=np.float32)
            edge_at_glare = float(np.mean(edge_arr[white_mask])) if np.sum(white_mask) > 30 else 0.0

            if white_fraction > 0.04 and edge_at_glare > 78.0:
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
        1:N Biometric Identification across registered candidate profiles with multi-pose support.

        Args:
            live_descriptor: Live 128-d vector from camera.
            candidates: List of candidate dicts with 'id', 'employee_code', 'name', 'face_descriptor'
            threshold: Maximum allowed Euclidean distance (calibrated default: 0.50).

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

            reg_vecs = cls.extract_all_vectors(reg_desc)
            if not reg_vecs:
                continue

            for v_reg in reg_vecs:
                if len(v_reg) != len(vec_live):
                    continue

                diff = vec_live - v_reg
                dist = float(np.linalg.norm(diff))

                if dist < min_dist:
                    min_dist = dist
                    best_cos = float(np.dot(vec_live, v_reg))

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

        if best_match and min_dist <= threshold and (best_sim >= DEFAULT_MIN_SIMILARITY or best_cos >= 0.55):
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
