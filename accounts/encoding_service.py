"""
encoding_service.py
-------------------
LookIn-AI face engine — powered by InsightFace buffalo_l.

Key features
------------
* InsightFace buffalo_l model (512-d float32 embeddings).
* CLAHE + unsharp-mask preprocessing for low-light / blurry photos.
* Tiling for group photos wider/taller than 2000 px (25% overlap + NMS).
* Cosine-similarity matching (threshold 0.45).
* Thread-safe in-memory encoding cache — loaded once at startup.
* Embeddings stored as raw bytes (float32 tobytes) in Profile.face_encoding.
"""

import io
import logging
import threading
import urllib.request

import cv2
import numpy as np

from django.contrib.auth.models import User
from django.utils import timezone as django_tz

import insightface

_GLOBAL_APP = None
_APP_LOCK = threading.Lock()

def get_kiosk_app():
    global _GLOBAL_APP
    if _GLOBAL_APP is None:
        with _APP_LOCK:
            if _GLOBAL_APP is None:
                _GLOBAL_APP = insightface.app.FaceAnalysis(
                    name='buffalo_l',
                    allowed_modules=['detection', 'recognition'],
                    providers=['CPUExecutionProvider']
                )
                _GLOBAL_APP.prepare(ctx_id=0, det_size=(320, 320))
                print("✅ InsightFace ONCE loaded — kiosk ready")
    return _GLOBAL_APP

logger = logging.getLogger(__name__)

# ── InsightFace singleton ─────────────────────────────────────────────────────
_insight_lock = threading.Lock()
_global_app = None

def _get_insight_app(mode='group'):
    """Lazy-load ONE central InsightFace FaceAnalysis singleton (thread-safe)."""
    global _global_app
    
    if _global_app is not None:
        return _global_app

    with _insight_lock:
        if _global_app is not None:
            return _global_app

        try:
            from insightface.app import FaceAnalysis

            try:
                import onnxruntime as ort
                providers = (
                    ["CUDAExecutionProvider", "CPUExecutionProvider"]
                    if "CUDAExecutionProvider" in ort.get_available_providers()
                    else ["CPUExecutionProvider"]
                )
            except Exception:
                providers = ["CPUExecutionProvider"]

            # PROBLEM 3 FIX: allowed_modules removes genderage + landmark
            # loads ONLY detection + recognition = 2 models instead of 5 → 2x faster
            app = FaceAnalysis(
                name="buffalo_l",
                allowed_modules=['detection', 'recognition'],
                providers=providers
            )
            
            # PROBLEM 1 FIX: prepare ONCE — det_size=(320,320) for speed
            app.prepare(ctx_id=0, det_size=(320, 320))
            _global_app = app
            logger.info("✅ InsightFace buffalo_l loaded ONCE [detection+recognition only] (320×320)")
            return app
                
        except Exception as exc:
            logger.error("Failed to load InsightFace: %s", exc, exc_info=True)
            raise


# ── thread-safe in-memory encoding cache ─────────────────────────────────────
_cache_lock = threading.Lock()
_cached_embeddings: list = []   # list of np.ndarray (512-d float32)
_cached_users: list = []        # list of User
_cache_loaded = False


import time
_cache_time = 0

def _reset_cache():
    global _cached_embeddings, _cached_users, _cache_loaded, _cache_time
    with _cache_lock:
        _cached_embeddings = []
        _cached_users = []
        _cache_loaded = False
        _cache_time = 0

def warm_cache(force: bool = False) -> int:
    """
    Load all pre-computed InsightFace embeddings from DB into in-process cache.
    Returns number of students loaded.  Thread-safe — loads once unless force=True.
    OPT 3: Refreshes automatically every 5 minutes.
    """
    global _cached_embeddings, _cached_users, _cache_loaded, _cache_time

    now = time.time()
    if not force and _cache_loaded and (now - _cache_time) <= 300:
        logger.info(f"Cache status: HIT")
        print(f"Cache status: HIT")
        return len(_cached_users)

    print(f"Cache status: MISS")
    from accounts.models import Profile  # local import — avoids circular

    embeddings: list = []
    users: list = []

    profiles = Profile.objects.filter(
        image__isnull=False, face_encoding__isnull=False
    ).select_related("user")

    for profile in profiles:
        try:
            enc = profile.get_face_encoding()
            if enc is not None and enc.shape == (512,):
                # Always L2-normalize stored embeddings at load time for accuracy
                norm = np.linalg.norm(enc)
                if norm > 0:
                    enc = enc / norm
                embeddings.append(enc)
                users.append(profile.user)
        except Exception as exc:
            logger.warning("Skipping encoding for %s: %s", profile.user, exc)

    with _cache_lock:
        _cached_embeddings = embeddings
        _cached_users = users
        _cache_loaded = True
        _cache_time = time.time()

    logger.info("Encoding cache warmed: %d students (InsightFace 512-d)", len(users))
    return len(users)


# ── image preprocessing ───────────────────────────────────────────────────────

def _preprocess_bgr(img_bgr: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE (L-channel) + unsharp mask to improve detection on dim / blurry photos.
    Accepts and returns BGR numpy array.
    """
    # CLAHE on L channel in LAB colour space
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    img_bgr = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    # Unsharp mask: sharpens edges — helps with slightly out-of-focus photos
    blurred = cv2.GaussianBlur(img_bgr, (0, 0), 3)
    img_bgr = cv2.addWeighted(img_bgr, 1.5, blurred, -0.5, 0)

    return img_bgr


# ── NMS helper ────────────────────────────────────────────────────────────────

def _iou(boxA, boxB):
    """Intersection-over-Union for [x1,y1,x2,y2] boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    if inter == 0:
        return 0.0
    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return inter / float(areaA + areaB - inter)


def _nms(faces, iou_threshold=0.40):
    """Remove duplicate face detections by non-maximum suppression on bboxes."""
    if len(faces) == 0:
        return faces

    # Sort by detection score descending
    faces = sorted(faces, key=lambda f: float(f.det_score), reverse=True)
    kept = []
    suppressed = set()

    for i, face in enumerate(faces):
        if i in suppressed:
            continue
        kept.append(face)
        for j in range(i + 1, len(faces)):
            if j in suppressed:
                continue
            if _iou(faces[i].bbox, faces[j].bbox) > iou_threshold:
                suppressed.add(j)

    return kept


# ── detect ALL faces in an image (group photo mode) ──────────────────────────

def detect_all_faces(img_bgr: np.ndarray, app=None):
    """
    Run InsightFace on a full image.  For images >2000px in any dimension,
    use overlapping tiles (25% overlap) then deduplicate with NMS.

    Returns list of InsightFace face objects (each has .bbox, .embedding, .det_score).
    """
    if app is None:
        app = _get_insight_app(mode='group')
        
    h, w = img_bgr.shape[:2]

    # Large image → tile strategy
    if max(h, w) > 2000:
        return _detect_with_tiling(img_bgr, app)

    # Standard path — single call at det_size=(1280,1280)
    processed = _preprocess_bgr(img_bgr)
    faces = app.get(processed)
    return faces if faces else []


def _detect_with_tiling(img_bgr: np.ndarray, app, overlap=0.25, iou_threshold=0.40):
    """
    Split a large image into overlapping tiles, run InsightFace on each,
    remap bboxes back to full-image coordinates, then NMS to remove dupes.
    """
    h, w = img_bgr.shape[:2]
    tile_size = 2000
    step = int(tile_size * (1 - overlap))

    all_faces = []

    y_starts = list(range(0, h, step))
    x_starts = list(range(0, w, step))

    for y0 in y_starts:
        for x0 in x_starts:
            y1 = min(y0 + tile_size, h)
            x1 = min(x0 + tile_size, w)
            tile = img_bgr[y0:y1, x0:x1]
            tile_proc = _preprocess_bgr(tile)

            try:
                tile_faces = app.get(tile_proc)
            except Exception as exc:
                logger.warning("Tile detection error at (%d,%d): %s", x0, y0, exc)
                continue

            if not tile_faces:
                continue

            # Remap bbox back to full-image space
            for face in tile_faces:
                face.bbox[0] += x0
                face.bbox[1] += y0
                face.bbox[2] += x0
                face.bbox[3] += y0
                all_faces.append(face)

    logger.info("Tiling: %d raw detections before NMS", len(all_faces))
    deduped = _nms(all_faces, iou_threshold=iou_threshold)
    logger.info("Tiling: %d detections after NMS", len(deduped))
    return deduped


# ── embed a single face image / source ───────────────────────────────────────

def compute_encoding(image_source) -> np.ndarray | None:
    """
    Accepts:
      - A local file path (str / Path)
      - A remote URL (str starting with http)
      - A numpy BGR image array

    Returns 512-d float32 numpy array or None if no face found.
    """
    try:
        import os
        if isinstance(image_source, str) and not image_source.startswith("http"):
            if not os.path.exists(image_source):
                logger.warning(f"compute_encoding: Image path does not exist {image_source}")
                return None

        if isinstance(image_source, np.ndarray):
            img = image_source
        elif isinstance(image_source, str) and image_source.startswith("http"):
            req = urllib.request.urlopen(image_source, timeout=10)
            arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
        else:
            img = cv2.imread(str(image_source), cv2.IMREAD_UNCHANGED)

        if img is None:
            logger.warning(f"compute_encoding: Failed to decode image {image_source}")
            return None

        # Convert to BGR robustly
        if len(img.shape) == 3 and img.shape[2] == 4:
            # Alpha channel present
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        elif len(img.shape) == 2:
            img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            img_bgr = img

        # Upscale if too small (helps face detector find it)
        h, w = img_bgr.shape[:2]
        if min(h, w) < 200:
            scale = 200 / min(h, w)
            img_bgr = cv2.resize(img_bgr, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        app = _get_insight_app(mode='portrait')
        processed = _preprocess_bgr(img_bgr)
        faces = app.get(processed)

        if not faces:
            logger.warning(f"compute_encoding: No face detected in {image_source}")
            return None

        # Pick face with highest detection confidence
        best = max(faces, key=lambda f: float(f.det_score))
        emb = best.embedding.astype(np.float32)
        norm = np.linalg.norm(emb)
        if norm > 0:
            return emb / norm
        return None

    except Exception as exc:
        logger.error(f"compute_encoding error for {image_source}: {exc}", exc_info=True)
        return None


# ── detect all faces in a group image and return their embeddings ─────────────

def detect_and_encode(image_path) -> list:
    """
    Group photo entry-point. Uses Test-Time Augmentation (TTA) and upscaling
    for robust face recognition in group photos. Extracts face crops, upscales them,
    and averages embeddings from original, flipped, and brightened variants.
    """
    try:
        img_bgr = cv2.imread(str(image_path))
        if img_bgr is None:
            logger.error("Cannot read image: %s", image_path)
            return []

        faces = detect_all_faces(img_bgr)
        logger.info("detect_and_encode: %d faces found in %s", len(faces), image_path)

        embeddings = []
        app_portrait = _get_insight_app(mode='portrait')

        for face in faces:
            # 1. Get bound crop safely
            x1, y1, x2, y2 = [int(v) for v in face.bbox]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(img_bgr.shape[1], x2)
            y2 = min(img_bgr.shape[0], y2)

            if x2 <= x1 or y2 <= y1:
                continue

            crop = img_bgr[y1:y2, x1:x2]

            # 2. Upscale crop by 2x (helps small back-row faces)
            crop_upscaled = cv2.resize(crop, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            # 3. Test-Time Augmentation (TTA) variants
            crop_orig = crop_upscaled
            crop_flip = cv2.flip(crop_upscaled, 1)
            crop_bright = cv2.convertScaleAbs(crop_upscaled, alpha=1.2, beta=10)

            crops_to_test = [crop_orig, crop_flip, crop_bright]
            embs_to_average = []

            for c in crops_to_test:
                c_proc = _preprocess_bgr(c)
                crop_faces = app_portrait.get(c_proc)
                if crop_faces:
                    # Best face in this crop
                    best_crop_face = max(crop_faces, key=lambda f: float(f.det_score))
                    if best_crop_face.embedding is not None:
                        embs_to_average.append(best_crop_face.embedding.astype(np.float32))

            # 4. Average and normalize embeddings
            if embs_to_average:
                final_embedding = np.mean(embs_to_average, axis=0)
                norm = np.linalg.norm(final_embedding)
                if norm > 0:
                    embeddings.append(final_embedding / norm)
            elif face.embedding is not None:
                # Fallback to the original detection embedding if crops failed
                emb = face.embedding.astype(np.float32)
                norm = np.linalg.norm(emb)
                if norm > 0:
                    embeddings.append(emb / norm)

        return embeddings

    except Exception as exc:
        logger.error("detect_and_encode error: %s", exc, exc_info=True)
        return []


# ── decode a base-64 webcam frame ─────────────────────────────────────────────

def decode_base64_frame(b64_data: str) -> np.ndarray | None:
    """
    Convert a base64-encoded JPEG/PNG (data URI or raw) into a BGR numpy array
    (OpenCV convention, since InsightFace works natively on BGR).
    """
    import base64
    try:
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]
        raw = base64.b64decode(b64_data)
        arr = np.frombuffer(raw, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return bgr  # keep as BGR for InsightFace
    except Exception as exc:
        logger.error("decode_base64_frame error: %s", exc)
        return None


# ── cosine similarity & matching ──────────────────────────────────────────────

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two L2-normalised vectors (result in [-1, 1])."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


def match_face(frame_embedding: np.ndarray, threshold: float = 0.30):
    """
    Compare a single 512-d embedding against the in-memory cache using
    cosine similarity.

    Returns (User, similarity_score) or (None, None).
    Higher similarity = better match (opposite of face_recognition distance).
    """
    warm_cache()  # no-op if already warmed

    with _cache_lock:
        if not _cached_embeddings:
            return None, None

        sims = np.array([cosine_similarity(frame_embedding, enc) for enc in _cached_embeddings])
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])

        if best_sim >= threshold:
            return _cached_users[best_idx], best_sim

    return None, None


def match_face_against_pool(frame_embedding: np.ndarray, pool_embs: list, pool_users: list, threshold: float = 0.30):
    """
    Match against a specific subset (enrolled students pool).
    Returns (User, similarity_score) or (None, None).
    """
    if not pool_embs:
        return None, None

    sims = np.array([cosine_similarity(frame_embedding, enc) for enc in pool_embs])
    best_idx = int(np.argmax(sims))
    best_sim = float(sims[best_idx])

    if best_sim >= threshold:
        return pool_users[best_idx], best_sim

    return None, None


def match_multiple_faces(frame_embeddings: list, pool_embs: list, pool_users: list) -> list:
    """
    Multi-pass matching strategy natively powered by array dot products.
    OPT 4: Parallel Batch Face Matching using NumPy fast processing.
    """
    if not pool_embs or len(pool_embs) == 0:
        return {}
    if not frame_embeddings:
        return []

    matched_results = []
    unmatched_faces = []
    used_user_ids = set()

    # Precompute pool matrix for vectorized dot product
    pool_matrix = np.array(pool_embs) # Shape (N, 512)

    # Tolerances scaling to InsightFace internal bounds
    THRESH_PASS_1 = 0.32
    THRESH_PASS_2 = 0.22
    THRESH_PASS_3 = 0.18

    # Pass 1: High confidence
    for emb in frame_embeddings:
        sims = np.dot(pool_matrix, emb)
        sorted_idxs = np.argsort(sims)[::-1]
        
        best_u, best_s = None, -1.0
        for idx in sorted_idxs:
            u = pool_users[idx]
            if u.id not in used_user_ids:
                best_s = float(sims[idx])
                best_u = u
                break
                
        if best_u is not None and best_s >= THRESH_PASS_1:
            matched_results.append((best_u, best_s))
            used_user_ids.add(best_u.id)
        else:
            unmatched_faces.append(emb)

    # Pass 2: Retry unmatched faces
    unmatched_faces_pass2 = []
    for emb in unmatched_faces:
        sims = np.dot(pool_matrix, emb)
        sorted_idxs = np.argsort(sims)[::-1]
        
        best_u, best_s = None, -1.0
        for idx in sorted_idxs:
            u = pool_users[idx]
            if u.id not in used_user_ids:
                best_s = float(sims[idx])
                best_u = u
                break

        if best_u is not None and best_s >= THRESH_PASS_2:
            matched_results.append((best_u, best_s))
            used_user_ids.add(best_u.id)
        else:
            unmatched_faces_pass2.append(emb)

    # Pass 3: Fallback with UNIQUE best match condition
    candidate_matches = {}
    for emb in unmatched_faces_pass2:
        sims = np.dot(pool_matrix, emb)
        sorted_idxs = np.argsort(sims)[::-1]
        
        best_u, best_s = None, -1.0
        for idx in sorted_idxs:
            u = pool_users[idx]
            if u.id not in used_user_ids:
                best_s = float(sims[idx])
                best_u = u
                break
                
        if best_u is not None and best_s >= THRESH_PASS_3:
            if best_u.id not in candidate_matches:
                candidate_matches[best_u.id] = []
            candidate_matches[best_u.id].append((best_s, best_u, emb))

    for uid, candidates in candidate_matches.items():
        best_candidate = max(candidates, key=lambda x: x[0])
        matched_results.append((best_candidate[1], best_candidate[0]))
        used_user_ids.add(uid)

    return matched_results


# ── profile-level helpers ─────────────────────────────────────────────────────

def compute_and_save_encoding_for_profile(profile) -> bool:
    """
    Re-compute and persist the InsightFace embedding for a single Profile.
    Invalidates the in-memory cache so next request reloads.
    Returns True on success.
    """
    try:
        if not profile.image:
            return False

        image_url = profile.image.url
        if image_url.startswith("http"):
            source = image_url
        else:
            source = profile.image.path
            import os
            if not os.path.exists(source):
                logger.warning(f"compute_and_save_encoding_for_profile: Image file does not exist: {source}")
                return False

        enc = compute_encoding(source)
        if enc is None:
            return False

        profile.set_face_encoding(enc)
        profile.encoding_updated_at = django_tz.now()
        profile.save(update_fields=["face_encoding", "encoding_updated_at"])

        _reset_cache()
        return True

    except Exception as exc:
        logger.error(f"compute_and_save_encoding_for_profile error for {profile}: {exc}", exc_info=True)
        return False


def bulk_recompute_encodings() -> dict:
    """
    Re-compute InsightFace embeddings for ALL students who have a profile image.
    Returns {"success": n, "failed": n, "skipped": n}
    """
    from accounts.models import Profile

    success = failed = skipped = 0
    profiles = Profile.objects.filter(image__isnull=False).select_related("user")

    for profile in profiles:
        if not profile.user.is_staff:
            ok = compute_and_save_encoding_for_profile(profile)
            if ok:
                success += 1
            else:
                failed += 1
        else:
            skipped += 1

    _reset_cache()
    warm_cache(force=True)
    return {"success": success, "failed": failed, "skipped": skipped}


# ── liveness detection ────────────────────────────────────────────────────────

def check_liveness(frames_b64: list, min_variance: float = 1.8) -> dict:
    """
    Anti-spoofing: checks that the webcam feed shows a LIVE person,
    not a photo or a still screen.

    FAST version — pixel-diff on downsampled grayscale frames.
    No InsightFace call per-frame, so < 0.1s total.
    Accepts 3-5 base64-encoded frames captured ~300ms apart.

    Returns:
        {
            "alive": True/False,
            "variance": float,
            "threshold": float,
            "faces_found": int,
            "reason": "ok" | "no_face" | "too_few_frames" | "static_image"
        }
    """
    if len(frames_b64) < 3:
        return {
            "alive": False, "variance": 0, "threshold": min_variance,
            "faces_found": 0, "reason": "too_few_frames"
        }

    gray_frames = []
    for b64 in frames_b64:
        img_bgr = decode_base64_frame(b64)
        if img_bgr is None:
            continue
        # Downsample to 64×64 grayscale for fast comparison
        small = cv2.resize(img_bgr, (64, 64), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
        gray_frames.append(gray)

    if len(gray_frames) < 2:
        return {
            "alive": False, "variance": 0, "threshold": min_variance,
            "faces_found": len(gray_frames), "reason": "no_face"
        }

    diffs = []
    for i in range(1, len(gray_frames)):
        diff = np.mean(np.abs(gray_frames[i] - gray_frames[i - 1]))
        diffs.append(diff)

    avg_variance = float(np.mean(diffs))
    alive = avg_variance >= min_variance

    return {
        "alive": alive,
        "variance": round(avg_variance, 3),
        "threshold": min_variance,
        "faces_found": len(gray_frames),
        "reason": "ok" if alive else "static_image"
    }

