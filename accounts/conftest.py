"""
conftest.py — Pre-patches InsightFace so tests don't load the real model.
This file is automatically picked up by pytest / Django test runner.
"""

import sys
from unittest.mock import MagicMock

# Create a fake insightface module BEFORE any app code imports it
mock_insightface = MagicMock()
mock_insightface.app.FaceAnalysis.return_value = MagicMock()
sys.modules['insightface'] = mock_insightface
sys.modules['insightface.app'] = mock_insightface.app
