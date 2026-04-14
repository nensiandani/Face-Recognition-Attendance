import json
import base64
import numpy as np
import cv2
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.models import APIKey
from accounts import encoding_service as es

def verify_api_key(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    key_str = auth_header.split(" ")[1]
    try:
        api_key = APIKey.objects.get(key=key_str, is_active=True)
        return True
    except APIKey.DoesNotExist:
        return False

@csrf_exempt
def get_face_encoding(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST is allowed"}, status=405)
    
    if not verify_api_key(request):
        return JsonResponse({"error": "Invalid or missing API key"}, status=401)
    
    try:
        body = json.loads(request.body)
        frames_b64 = body.get("frames", [])
        if not frames_b64 or len(frames_b64) != 3:
            return JsonResponse({"error": "Must provide exactly 3 frames (base64)."}, status=400)
        
        # Run existing liveness check
        liveness = es.check_liveness(frames_b64)
        if not liveness.get("alive"):
             return JsonResponse({"status": "failed", "liveness_passed": False, "error": liveness.get("reason", "Spoofing detected"), "embedding": []}, status=400)

        frames = []
        for b64 in frames_b64:
            if "," in b64:
                b64 = b64.split(",")[1]
            try:
                img_data = base64.b64decode(b64)
                np_arr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if img is not None:
                    frames.append(img)
            except Exception:
                continue
                
        if not frames:
             return JsonResponse({"error": "Could not decode frames."}, status=400)
             
        # Get face encoding from first frame that has a face
        app = es._get_insight_app()
        faces = None
        for frame in frames:
            processed = es._preprocess_bgr(frame)
            faces = app.get(processed)
            if faces:
                break
                
        if not faces:
            return JsonResponse({"status": "failed", "error": "No face detected in any frame", "embedding": []}, status=400)
            
        emb = faces[0].embedding
        if emb is None:
            return JsonResponse({"status": "failed", "error": "Failed to extract embedding", "embedding": []}, status=400)
            
        emb_list = [float(x) for x in emb]
        
        return JsonResponse({
            "status": "success",
            "liveness_passed": True,
            "embedding": emb_list
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
