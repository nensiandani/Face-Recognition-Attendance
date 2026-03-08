import face_recognition
from django.contrib.auth.models import User
import os

def recognize_faces(group_image_path):
    detected_users = []

    print("📸 Processing image:", group_image_path)

    group_img = face_recognition.load_image_file(group_image_path)
    group_encodings = face_recognition.face_encodings(group_img)

    print("👥 Faces found in group photo:", len(group_encodings))

    if not group_encodings:
        return detected_users

    for group_encoding in group_encodings:
        for user in User.objects.filter(is_staff=False):
            try:
                profile = user.profile

                if not profile.image:
                    continue

                student_path = profile.image.path

                if not os.path.exists(student_path):
                    continue

                student_img = face_recognition.load_image_file(student_path)
                student_encodings = face_recognition.face_encodings(student_img)

                if not student_encodings:
                    continue

                match = face_recognition.compare_faces(
                    [student_encodings[0]],
                    group_encoding,
                    tolerance=0.55   # 👈 slightly relaxed
                )

                if True in match and user not in detected_users:
                    print("✅ Match found:", user.username)
                    detected_users.append(user)

            except Exception as e:
                print("❌ Face error:", e)

    print("🎯 Total detected:", len(detected_users))
    return detected_users
