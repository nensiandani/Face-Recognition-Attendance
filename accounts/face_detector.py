"""
face_detector.py
────────────────
Thin wrapper — delegates entirely to encoding_service so that any existing
import of 'from . import face_detector' continues to work unchanged.
"""

from . import encoding_service as es


def detect_and_encode(image_path) -> list:
    """
    Detect ALL faces in image_path and return a list of 512-d float32
    embeddings (L2-normalised).  Replaces the old dlib/HOG pipeline.
    """
    return es.detect_and_encode(image_path)
