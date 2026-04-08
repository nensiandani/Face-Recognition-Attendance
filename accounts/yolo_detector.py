"""
yolo_detector.py
────────────────
DEPRECATED — YOLO is no longer used.
InsightFace buffalo_l (in encoding_service.py) replaces both YOLO and dlib.
This stub is kept for import compatibility only.
"""


def recognize_faces(group_image_path):
    """Deprecated stub — use encoding_service.detect_and_encode() instead."""
    raise NotImplementedError(
        "yolo_detector is deprecated. Use encoding_service.detect_and_encode()."
    )
