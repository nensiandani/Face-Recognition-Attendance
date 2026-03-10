from django.contrib.auth.models import User
import face_recognition
import os


def recognize_faces(group_image_path):
    detected_users = []

    # Load group image
    group_img = face_recognition.load_image_file(group_image_path)
    group_encodings = face_recognition.face_encodings(group_img)

    # If no faces found
    if not group_encodings:
        return detected_users

    # Loop through EACH face in group photo
    for group_encoding in group_encodings:

        # Compare with each student
        for user in User.objects.filter(is_staff=False):

            try:
                # Make sure profile image exists
                if not user.profile.image:
                    continue

                student_img_path = user.profile.image.path

                if not os.path.exists(student_img_path):
                    continue

                student_img = face_recognition.load_image_file(student_img_path)
                student_encodings = face_recognition.face_encodings(student_img)

                if not student_encodings:
                    continue

                match = face_recognition.compare_faces(
                    [student_encodings[0]],
                    group_encoding,
                    tolerance=0.5
                )

                if True in match and user not in detected_users:
                    detected_users.append(user)

            except Exception as e:
                print(f"Face match error for {user.username}: {e}")
                continue

    return detected_users
