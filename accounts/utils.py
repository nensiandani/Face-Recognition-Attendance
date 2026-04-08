"""
utils.py
--------
Legacy recognition helper — now backed by InsightFace via encoding_service.
Kept for any code that still imports recognize_faces() from this module.
"""

import logging
import numpy as np
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def recognize_faces(group_image_path):
    """
    Detect all faces in group_image_path and match them against all registered
    students using InsightFace cosine-similarity.

    Returns a list of matched User objects.
    """
    from . import encoding_service as es

    # Ensure cache is warm
    es.warm_cache()

    with es._cache_lock:
        pool_embs = list(es._cached_embeddings)
        pool_users = list(es._cached_users)

    # Get all embeddings for detected faces in the group image
    face_embeddings = es.detect_and_encode(group_image_path)

    if not face_embeddings:
        logger.info("utils.recognize_faces: no faces detected in %s", group_image_path)
        return []

    detected_users = []
    
    matches = es.match_multiple_faces(face_embeddings, pool_embs, pool_users)
    
    for matched_user, sim in matches:
        detected_users.append(matched_user)
        logger.info(
            "utils.recognize_faces: matched %s (sim=%.3f)",
            matched_user.username, sim
        )

    logger.info(
        "utils.recognize_faces: %d faces detected, %d matched",
        len(face_embeddings), len(detected_users)
    )
    return detected_users
