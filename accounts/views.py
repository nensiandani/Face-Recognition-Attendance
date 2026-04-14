from fileinput import filename
from django.shortcuts import render, redirect, get_object_or_404

# Force singleton init at server startup (skip during test runs)
import sys as _sys
from accounts import encoding_service as es
if 'test' not in _sys.argv:
    try:
        es.get_kiosk_app()
        print("✅ Kiosk app pre-warmed at startup")
    except Exception as e:
        print(f"Kiosk app init failed: {e}")
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from .models import AttendanceSession, Attendance, Profile, LiveAttendanceSession, LiveAttendanceRecord
import threading

import os
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl
from functools import wraps
from django.db.models import Count, Q
import calendar
from datetime import date
from .models import Division, Semester, Program, Department, Faculty, Subject, SubjectEnrollment, SubjectProgramSemester
import tempfile
import re
import json

from django.core.mail import send_mail
import urllib.request
import random

from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView


def clean_name(first, last):
    first = (first or '').strip()
    last = (last or '').strip()
    if last and last.lower() != first.lower():
        return f"{first} {last}".strip()
    return first


def isolate_qs(request, qs):
    if not request.user.is_authenticated:
        return qs.none()
    if getattr(request.user, 'is_superuser', False):
        return qs
    return qs.filter(created_by=request.user)

def admin_check(user):
    return user.is_staff    

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_login(request):
    import os
    admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@lookinai.com')
    admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    
    if not User.objects.filter(email=admin_email).exists():
        try:
            User.objects.create_superuser(username=admin_username, email=admin_email, password=admin_password)
            print(f"Force created superuser: {admin_email}")
        except Exception as e:
            print(f"Failed to force create superuser: {e}")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            request.session['admin_id'] = user.id
            return redirect("admin_dashboard")
        
        # Detailed error messages for debugging
        if user is not None:
             messages.error(request, "User doesn't have admin privileges.")
        else:
             try:
                 u = User.objects.get(email=email)
                 if not u.check_password(password):
                     messages.error(request, "Wrong password.")
                 elif not (u.is_staff or u.is_superuser):
                     messages.error(request, "User exists but is not an admin.")
             except User.DoesNotExist:
                 messages.error(request, "User not found.")
             except User.MultipleObjectsReturned:
                 messages.error(request, "Multiple users found with this email.")

    return render(request, "adminpanel/admin_login.html")

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_profile(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", user.first_name)
        user.email = request.POST.get("email", user.email)
        user.save()

        profile.mobile = request.POST.get("mobile")
        profile.faculty = request.POST.get("faculty")
        profile.department = request.POST.get("department")
        profile.program = request.POST.get("program")
        profile.semester = request.POST.get("semester")
        profile.division = request.POST.get("division")

        if request.FILES.get("image"):
            profile.image = request.FILES.get("image")

        profile.save()

        messages.success(request, "Profile updated successfully ✅")
        return redirect("admin_profile")

    return render(request, "adminpanel/admin_profile.html", {"profile": profile})

def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@login_required
def student_attendance(request):
    user = request.user
    today = date.today()

    sessions = AttendanceSession.objects.filter(date__month=today.month)
    attendance = Attendance.objects.filter(student=user, session__in=sessions)

    attendance_map = {
        att.session.id: att.status for att in attendance
    }

    lecture_data = {}
    for s in sessions:
        lecture_data.setdefault(s.date, {})[s.slot] = s

    subject_stats = (
        Attendance.objects
        .filter(student=user)
        .values('session__subject__name')
        .annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='P'))
        )
    )

    for s in subject_stats:
        s['percent'] = round((s['present'] / s['total']) * 100, 2) if s['total'] else 0

    context = {
        'lecture_data': lecture_data,
        'attendance_map': attendance_map,
        'month': calendar.month_name[today.month],
        'year': today.year,
        'subject_stats': subject_stats,
    }

    return render(request, "student/attendance.html", context)

@login_required(login_url='login')
def index(request):
    return render(request, "index.html")

# OPT 6: Progress Tracking Helper
def update_progress(request, current, total, message):
    if not request.user.is_authenticated: return
    session_key = f'attendance_progress_{request.user.id}'
    percent = int((current / total) * 100) if total > 0 else (100 if current > 0 else 0)
    request.session[session_key] = {
        'current': current,
        'total': total,
        'percent': percent,
        'message': message
    }
    request.session.save()

# OPT 6: API Endpoint
def get_attendance_progress(request):
    if not request.user.is_authenticated:
        return JsonResponse({'percent': 0, 'message': 'Unauthorized'})
    session_key = f'attendance_progress_{request.user.id}'
    data = request.session.get(session_key, {
        'current': 0, 'total': 0, 'percent': 0, 'message': 'Ready'
    })
    return JsonResponse(data)

# OPT 2: Preprocess Image max 640px (BUG 2 Fix)
def preprocess_frame(frame):
    if frame is None:
        return frame
    h, w = frame.shape[:2]
    # Resize to max 640px on longest side
    max_dim = 640
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    # Ensure RGB
    if len(frame.shape) == 3 and frame.shape[2] == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return frame


def get_valid_absent_students(session, subject, present_ids):
    from .models import SubjectEnrollment
    if not subject:
        return []
    enrolled = SubjectEnrollment.objects.filter(
        subject=subject
    ).select_related('student', 'student__profile')
    
    absent = []
    for enrollment in enrolled:
        student = enrollment.student
        profile = getattr(student, 'profile', None)
        
        # Skip if already present
        if student.id in present_ids:
            continue
            
        # For CORE: skip if wrong division
        if subject.subject_type == 'core':
            student_div = (getattr(profile, 'division', '') or '').strip().upper()
            session_div = (session.division or '').strip().upper()
            if student_div != session_div:
                print(f"SKIP email: {student.first_name} wrong division {student_div} vs {session_div}")
                continue
        
        absent.append(student)
    return absent

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def mark_attendance(request):
    detected_students = []

    if request.method == "POST" and request.FILES.getlist("media"):
        import time
        t1 = time.time()
        load_student_encodings()
        print(f"Cache load: {time.time()-t1:.2f}s")

        subject_id = request.POST.get("subject")
        subject = Subject.objects.get(id=subject_id)
        
        division_name = request.POST.get("division", "")
        if subject.subject_type == 'elective':
            division_name = "N/A"
            semester_name = "Elective"
        else:
            semester_name = subject.semester.name if subject.semester else ""

        slot = request.POST.get("slot")

        session = AttendanceSession.objects.create(
            faculty=subject.faculty.name if subject.faculty else "",
            department=subject.department.name if subject.department else "",
            program=subject.program.name if subject.program else "",
            semester=semester_name,
            division=division_name,
            subject=subject,
            lecture_slot=slot
        )

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "attendance"))

        # ── SessionBuffer: accumulate ALL matches in memory ──
        from .session_buffer import SessionBuffer
        buf = SessionBuffer(session.id)

        # ✅ ENROLLED STUDENTS PRE-FILTER
        enrolled_ids = SubjectEnrollment.objects.filter(
            subject=subject
        ).values_list('student_id', flat=True)
        enrolled_students = User.objects.filter(id__in=enrolled_ids)

        if not enrolled_students.exists():
            print("⚠️ No students enrolled in subject, falling back to division/program filter")
            enrolled_students = User.objects.filter(
                is_staff=False,
                profile__program=subject.program.name,
                profile__semester=semester_name,
                profile__division=division_name
            )

        enrolled_with_encoding = [
            s for s in enrolled_students 
            if getattr(s, 'profile', None) and s.profile.face_encoding
        ]
        if not enrolled_with_encoding:
            print("No encodings found — skipping match")
            buf.flush_attendance(enrolled_students)
            messages.warning(request, "No encodings found — skipping match")
            return redirect("attendance_success", id=session.id)

        matched_users_total = set()
        files = request.FILES.getlist('media')

        # Initialize progress
        update_progress(request, 0, len(files), "🔄 Mapping files...")
        print(f"Workers: ThreadPool active")

        # OPT 5: ThreadPoolExecutor Parallelism
        
        file_processing_list = []
        for file in files:
            filename = fs.save(file.name, file)
            file_path = os.path.join(settings.MEDIA_ROOT, "attendance", filename)
            file_processing_list.append((file_path, file.content_type))

        def process_single_file(path_info):
            f_path, c_type = path_info
            try:
                if c_type.startswith("image"):
                    # For images, pre-process them using resize
                    img = cv2.imread(f_path)
                    if img is not None:
                        img = preprocess_frame(img)
                        cv2.imwrite(f_path, img) # save resized back for detector
                    return recognize_faces_from_image(f_path, enrolled_students=enrolled_students)
                elif c_type.startswith("video"):
                    return recognize_faces_from_video(f_path, enrolled_students=enrolled_students, request=request)
            except Exception as e:
                import traceback
                print(f"❌ Face recognition FAILED for {f_path}: {e}")
            return []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_single_file, pi) for pi in file_processing_list]
            
            for index, future in enumerate(futures, 1):
                recognized_students = future.result()
                
                for student in recognized_students:
                    profile = getattr(student, 'profile', None)
                    
                    # Check enrollment
                    is_enrolled = SubjectEnrollment.objects.filter(
                        subject=subject,
                        student=student
                    ).exists()
                    if not is_enrolled:
                        print(f"SKIP: {student.first_name} not enrolled")
                        continue
                    
                    # CORE subject division check
                    if subject.subject_type == 'core':
                        student_div = (getattr(profile, 'division', '') or '').strip().upper()
                        session_div = (division_name or '').strip().upper()
                        if student_div != session_div:
                            print(f"SKIP: {student.first_name} wrong div {student_div} vs {session_div}")
                            continue

                    # Valid student — add to present list
                    matched_users_total.add(student)
                    buf.add(student.id, confidence=1.0)

                update_progress(request, index, len(files), f"✅ Done! {len(matched_users_total)} students found in {index}/{len(files)} files")

        update_progress(request, len(files), len(files), "🔄 Finalizing Database Write...")

        # Fix attendance marking: Exclude wrong division students from DB records
        valid_enrolled = []
        for st in enrolled_students:
            if subject.subject_type == 'core':
                profile = getattr(st, 'profile', None)
                student_div = (getattr(profile, 'division', '') or '').strip().upper()
                session_div = (division_name or '').strip().upper()
                if student_div != session_div:
                    continue
            valid_enrolled.append(st)

        # ── ONE bulk DB write: Present + Absent in a single call ──
        present_list, absent_list = buf.flush_attendance(valid_enrolled)

        # Strict absent list for emails using explicit helper
        present_ids = {s.id for s, _ in present_list}
        absent_only = get_valid_absent_students(session, subject, present_ids)
        
        if absent_only:
            absent_tuples = [(s, False) for s in absent_only]
            send_bulk_attendance_emails(absent_tuples, subject if subject else "Class", slot, session.date)

        enrolled_set = set(enrolled_students)
        detected_students = [u for u in matched_users_total if u in enrolled_set]
        print(f"Detected students: {len(detected_students)} (enrolled: {enrolled_students.count()})")

    return render(request, "adminpanel/attendance.html", {
        "detected_students": detected_students,
        "faculties": isolate_qs(request, Faculty.objects.all()),
        "departments": isolate_qs(request, Department.objects.all()),
        "programs": isolate_qs(request, Program.objects.all()),
        "semesters": isolate_qs(request, Semester.objects.all()),
        "divisions": isolate_qs(request, Division.objects.all()),
        "subjects": isolate_qs(request, Subject.objects.all()),
    })

# ── module-level lists mirroring the encoding_service cache ──────────────────
# These are warmed by load_student_encodings() before each group-photo session.
STUDENT_ENCODINGS = []   # list of 512-d float32 np.ndarray
STUDENT_USERS = []       # list of User

def load_student_encodings():
    """Backwards-compatible wrapper: warms the encoding_service cache."""
    from . import encoding_service as es
    # OPT 3: force=False allows 5 minute cache to protect DB hits
    count = es.warm_cache(force=False)
    # Mirror into module-level lists for match_faces()
    STUDENT_ENCODINGS.clear()
    STUDENT_USERS.clear()
    with es._cache_lock:
        STUDENT_ENCODINGS.extend(es._cached_embeddings)
        STUDENT_USERS.extend(es._cached_users)
    print("Students loaded (InsightFace cache):", count)

def match_faces(frame_embeddings, enrolled_students=None):
    """
    Match a list of 512-d InsightFace embeddings against the enrolled-student pool.
    Uses cosine similarity (threshold 0.45).
    Returns a list of matched User objects.
    """
    from . import encoding_service as es

    matched_users = []

    if not STUDENT_ENCODINGS:
        return matched_users

    # Build pool restricted to enrolled students to prevent cross-class false matches
    pool_embs = []
    pool_users = []
    if enrolled_students is not None:
        enrolled_set = set(enrolled_students)
        for enc, u in zip(STUDENT_ENCODINGS, STUDENT_USERS):
            if u in enrolled_set:
                pool_embs.append(enc)
                pool_users.append(u)
    else:
        pool_embs = STUDENT_ENCODINGS
        pool_users = STUDENT_USERS

    if not pool_embs:
        return matched_users

    matches = es.match_multiple_faces(frame_embeddings, pool_embs, pool_users)
    for u, sim in matches:
        matched_users.append(u)

    return matched_users

def recognize_faces_from_video(video_path, enrolled_students=None, request=None):
    """Process a video file, sampling every 10th frame with InsightFace (OPT 1)."""
    from . import encoding_service as es

    detected_users = set()
    frame_user_counts = {}
    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        print("❌ Cannot open video:", video_path)
        return detected_users

    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(video.get(cv2.CAP_PROP_FPS)) or 30

    pool_embs = []
    pool_users = []
    if enrolled_students is not None:
        enrolled_with_encoding = [
            s for s in enrolled_students 
            if getattr(s, 'profile', None) and s.profile.face_encoding
        ]
        if not enrolled_with_encoding:
            print("No encodings found — skipping match")
            return set()

        enrolled_set = set(enrolled_students)
        with es._cache_lock:
            for enc, u in zip(es._cached_embeddings, es._cached_users):
                if u in enrolled_set:
                    pool_embs.append(enc)
                    pool_users.append(u)
    else:
        with es._cache_lock:
            pool_embs = list(es._cached_embeddings)
            pool_users = list(es._cached_users)

    frame_count = 0
    app = es._get_insight_app()

    # OPT 1: Smart Sampling
    SAMPLE_RATE = 50
    enrolled_count = len(enrolled_students) if enrolled_students is not None else float('inf')

    while True:
        ret, frame = video.read()
        if not ret:
            break

        try:
            if frame_count % SAMPLE_RATE == 0:
                print(f"SAMPLE_RATE active: True (Frame {frame_count})")

                # OPT 2: Resize
                frame = preprocess_frame(frame)
                processed = es._preprocess_bgr(frame)
                
                import time
                t2 = time.time()
                faces = app.get(processed)
                print(f"Frame processing: {time.time()-t2:.2f}s (Faces: {len(faces) if faces else 0})")

                if faces:
                    frame_embs = []
                    for face in faces:
                        if face.embedding is not None:
                            emb = face.embedding.astype(np.float32)
                            norm = np.linalg.norm(emb)
                            if norm > 0:
                                frame_embs.append(emb / norm)
                                
                    t3 = time.time()
                    matches = es.match_multiple_faces(frame_embs, pool_embs, pool_users)
                    print(f"Face matching: {time.time()-t3:.2f}s")
                    
                    for matched_user, sim in matches:
                        frame_user_counts[matched_user] = frame_user_counts.get(matched_user, 0) + 1
                        if frame_user_counts[matched_user] >= 2:
                            detected_users.add(matched_user)

                # BUG 1 FIX: Early Exit correctly positioned outside inner face loop
                confirmed_count = len([u for u, count in frame_user_counts.items() if count >= 2])
                if request:
                    update_progress(request, frame_count, total_frames, f"📹 Scanning video frame {frame_count}/{total_frames} — {confirmed_count} students found")

                if enrolled_count != float('inf') and confirmed_count >= enrolled_count:
                    print(f"🎯 Early exit! All {confirmed_count} confirmed at frame {frame_count}")
                    if request:
                        update_progress(request, total_frames, total_frames, f"🎯 Early exit! All {confirmed_count} students identified at frame {frame_count}")
                    break

        except Exception as e:
            print("⚠ Frame error:", e)

        frame_count += 1

    video.release()
    print("Frame confirmation counts:", frame_user_counts)
    return detected_users

def recognize_faces_from_image(image_path, enrolled_students=None):
    """Enhanced face detection: CLAHE + tiling + YOLO/FR ensemble + NMS + padded encoding."""
    from . import face_detector
    encodings = face_detector.detect_and_encode(image_path)
    print("Image faces (enhanced pipeline):", len(encodings))
    return match_faces(encodings, enrolled_students=enrolled_students)

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def attendance_history(request):
    qs = AttendanceSession.objects.select_related(
        'subject', 
        'subject__program', 
        'subject__semester', 
        'subject__faculty'
    ).prefetch_related(
        'subject__divisions',
        'subject__program_semester_pairs',
        'subject__program_semester_pairs__program',
        'subject__program_semester_pairs__semester'
    ).all().order_by('-id')

    # Get filter params
    subject = request.GET.get('subject')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Apply filters
    if subject:
        qs = qs.filter(subject__id=subject)
    
    from datetime import datetime
    if date_from:
        try:
            dt = datetime.strptime(date_from, "%Y-%m-%d").date()
            qs = qs.filter(date__date__gte=dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d").date()
            qs = qs.filter(date__date__lte=dt)
        except ValueError:
            pass

    sessions_list = list(qs)
    for session in sessions_list:
        subj = getattr(session, 'subject', None)
        
        if subj is None:
            session.subject_display = 'legacy'
            
            f_code = ""
            try:
                f_obj = Faculty.objects.get(name__iexact=session.faculty)
                if f_obj.faculty_code:
                    f_code = f_obj.faculty_code
            except Exception:
                pass
            session.faculty_code = f_code
        else:
            if subj.subject_type == 'core':
                session.subject_display = 'core'
                session.subject_divs = list(subj.divisions.values_list('name', flat=True))
            else:
                session.subject_display = 'elective'
                session.subject_pairs = list(subj.program_semester_pairs.all())
                
            session.faculty_code = subj.faculty.faculty_code if subj.faculty and subj.faculty.faculty_code else ""

    subjects = isolate_qs(request, Subject.objects.all())
    
    from datetime import date
    today_date = date.today().isoformat()

    return render(request, "adminpanel/attendance_history.html", {
        "sessions": sessions_list,
        "subjects": subjects,
        "today_date": today_date
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def download_attendance(request, session_id):
    session = AttendanceSession.objects.get(id=session_id)
    
    records = list(Attendance.objects.filter(session=session).select_related('student', 'student__profile'))

    # TASK 1: Print before writing rows
    print(f"Total records to write: {len(records)}")
    print(f"First record sample: {records[0] if records else 'EMPTY'}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Report"

    # TASK 2: Do NOT create separate row per program/sem group. Group by student + subject + date only.
    headers = ["Student Name", "Roll No", "Program", "Sem", "Div", "Subject", "Status", "Date & Time"]
    ws.append(headers)

    for r in records:
        p = r.student.profile
        
        subj_display = ""
        if session.subject:
            if session.subject.course_code:
                subj_display = f"[{session.subject.course_code}] {session.subject.name}"
            else:
                subj_display = session.subject.name
                
        row = [
            clean_name(r.student.first_name, r.student.last_name) or r.student.username,
            p.roll if p.roll else "",
            p.program if p.program else session.program,
            p.semester if p.semester else session.semester,
            p.division if p.division else session.division,
            subj_display,
            "Present" if r.status else "Absent",
            str(session.date.strftime('%d %b %Y, %H:%M')),
        ]
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="attendance_report_{session_id}.xlsx"'
    wb.save(response)
    return response

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def admin_dashboard(request, user_id=None):
    if getattr(request.user, 'is_superuser', False):
        users = User.objects.filter(is_staff=False).select_related('profile')
    else:
        users = User.objects.filter(is_staff=False, profile__created_by=request.user).select_related('profile')
    edit_user = None
    profile = None

    if user_id:
        edit_user = get_object_or_404(User, id=user_id)
        profile = Profile.objects.get(user=edit_user)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        roll = request.POST.get("roll", "").strip()
        faculty = request.POST.get("faculty", "").strip()
        department = request.POST.get("department", "").strip()
        program = request.POST.get("program", "").strip()
        semester = request.POST.get("semester", "").strip()
        division = request.POST.get("division", "").strip()
        image = request.FILES.get("image")

        form_data = {
            "name": name, "email": email, "mobile": mobile, "roll": roll, "faculty": faculty,
            "department": department, "program": program, "semester": semester, "division": division,
        }

        if not all([name, email, mobile]):
            messages.error(request, "Name, Email and Mobile are required")
            return render(request, "adminpanel/dashboard.html", {"users": users, "edit_user": edit_user, "profile": profile, "form_data": form_data})

        if not mobile.isdigit():
            messages.error(request, "Mobile must contain only digits")
            return render(request, "adminpanel/dashboard.html", {"users": users, "edit_user": edit_user, "profile": profile})

        if len(mobile) != 10:
            messages.error(request, "Mobile number must be exactly 10 digits")
            return render(request, "adminpanel/dashboard.html", {"users": users, "edit_user": edit_user, "profile": profile})

        if not user_id:
            if User.objects.filter(username=email).exists():
                messages.error(request, "User with this email already exists")
                return redirect('admin_dashboard')

            user = User.objects.create_user(username=email, email=email, password="123456", first_name=name)
            Profile.objects.create(user=user, created_by=request.user, mobile=mobile, roll=roll, faculty=faculty, department=department, program=program, semester=semester, division=division, image=image)
            messages.success(request, f"Student {name} added successfully ✅")

        else:
            edit_user.first_name = name
            edit_user.email = email
            edit_user.save()

            profile.mobile = mobile
            profile.roll = roll
            profile.faculty = faculty
            profile.department = department
            profile.program = program
            profile.semester = semester
            profile.division = division
            if image:
                profile.image = image
            profile.save()

            messages.success(request, f"User {name} updated successfully ✅")

        return redirect("admin_dashboard")

    students_list = []
    for s in users:
        p = getattr(s, 'profile', None)
        students_list.append({
            'id': s.id,
            'name': clean_name(s.first_name, s.last_name) or s.username,
            'roll': p.roll if p else '',
            'program': (p.program or '').strip() if p else 'N/A',
            'branch': (p.department or '').strip() if p else 'N/A',
            'semester': (p.semester or '').strip() if p else 'N/A',
            'division': (p.division or '').strip() if p else 'N/A',
            'photo_url': p.image.url if (p and p.image) else '',
        })

    import json

    return render(request, "adminpanel/dashboard.html", {
        "users": users,
        "edit_user": edit_user,
        "profile": profile,
        "students_json": json.dumps(students_list),
        "departments": isolate_qs(request, Department.objects.all()),
        "programs": isolate_qs(request, Program.objects.all()),
        "semesters": isolate_qs(request, Semester.objects.all()),
        "divisions": isolate_qs(request, Division.objects.all()),
    })

from django.http import HttpResponse

def wipe_dummy_students(request):
    """Emergency route to delete all non-admin students who have blank avatars or 'student' in name"""
    count = 0
    for p in Profile.objects.select_related('user').all():
        if not p.user.is_staff:
            is_broken = False
            if not p.image or not str(p.image.name).strip():
                is_broken = True
            elif "student" in p.user.first_name.lower():
                is_broken = True
            elif p.user.first_name in ["meet barasara", "Kanu Bhadaraka", "Prince Chovatiya", "Student 1"]:
                is_broken = True
                
            if is_broken:
                p.user.delete()
                count += 1
    from django.http import HttpResponse
    return HttpResponse(f"<h1 style='color:green;'>✅ Successfully wiped {count} broken student accounts.</h1><p>You can now go back to the LookIn Dashboard and retry the Bulk CSV + ZIP upload!</p>")

def debug_users(request):
    from django.http import JsonResponse
    from django.contrib.auth.models import User
    
    # Force delete IDs 4, 5, 7 which we know have broken images
    deleted_count, _ = User.objects.filter(id__in=[4, 5, 7]).delete()
    
    users = []
    for p in Profile.objects.select_related('user').all():
        if not p.user.is_staff:
            users.append({
                'id': p.user.id,
                'name': p.user.first_name,
                'email': p.user.email,
                'image': str(p.image.name) if p.image else "NONE",
            })
    return JsonResponse({'status': f'Deleted {deleted_count} users', 'remaining_users': users})

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def bulk_register_students(request):
    import csv, zipfile, tempfile, os, shutil
    from io import TextIOWrapper
    from django.core.files import File
    from . import encoding_service as es

    if request.method == "POST":
        csv_file = request.FILES.get('csv_file')
        zip_file = request.FILES.get('zip_file')

        if not csv_file or not zip_file:
            messages.error(request, "Both CSV and ZIP files are required.")
            return redirect("admin_dashboard")
            
        if not csv_file.name.endswith('.csv') or not zip_file.name.endswith('.zip'):
            messages.error(request, "Please upload valid .csv and .zip files.")
            return redirect("admin_dashboard")

        temp_dir = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        except Exception as e:
            messages.error(request, f"Error reading ZIP file: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return redirect("admin_dashboard")

        try:
            csv_parsed = csv.DictReader(TextIOWrapper(csv_file.file, encoding='utf-8-sig'))
        except Exception as e:
            messages.error(request, f"Error reading CSV file: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return redirect("admin_dashboard")
            
        success_count = 0
        error_count = 0
        missing_images = 0
        profiles_to_encode = []
        
        for row in csv_parsed:
            # normalize row keys
            row_lower = {k.strip().lower(): v for k, v in row.items() if k}
            
            name = row_lower.get("name", "").strip()
            email = row_lower.get("email", "").strip().lower()
            mobile = row_lower.get("mobile", "").strip()
            roll = row_lower.get("roll", "").strip()
            faculty = row_lower.get("faculty", "").strip()
            dept = row_lower.get("department", "").strip()
            program = row_lower.get("program", "").strip()
            semester = row_lower.get("semester", "").strip()
            division = row_lower.get("division", "").strip()
            img_filename = row_lower.get("image_filename", "").strip()

            if not email or not name:
                continue

            if User.objects.filter(username=email).exists():
                error_count += 1
                continue

            try:
                user = User.objects.create_user(
                    username=email, 
                    email=email, 
                    password="LookIn@123",
                    first_name=name
                )
                
                profile = Profile.objects.create(
                    user=user, mobile=mobile, roll=roll, 
                    faculty=faculty, department=dept, 
                    program=program, semester=semester, division=division
                )
                
                found_img = False
                if img_filename:
                    search_names = [img_filename.lower(), f"{img_filename}.jpg".lower(), f"{img_filename}.png".lower(), f"{img_filename}.jpeg".lower()]
                    
                    # Case insensitive search anywhere in extracted zip
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            # Skip __MACOSX system files
                            if "__MACOSX" in root: continue
                                
                            if file.lower() in search_names:
                                img_path = os.path.join(root, file)
                                with open(img_path, 'rb') as f:
                                    profile.skip_signal = True
                                    profile.image.save(file, File(f))
                                found_img = True
                                break
                        if found_img:
                            break
                            
                profile.skip_signal = True
                profile.save()

                if found_img:
                    profiles_to_encode.append(profile)
                else:
                    missing_images += 1
                    
                success_count += 1
            except Exception as e:
                print(f"Error importing user {email}: {e}")
                error_count += 1

        shutil.rmtree(temp_dir, ignore_errors=True)

        if profiles_to_encode:
            import threading
            def _bulk_encode():
                for p in profiles_to_encode:
                    try:
                        es.compute_and_save_encoding_for_profile(p)
                        print(f"[SUCCESS] Bulk auto-encoded: {p.user.email}")
                    except Exception as exc:
                        print(f"[ERROR] Bulk auto-encode failed for {p.user.email}: {exc}")
            
            t = threading.Thread(target=_bulk_encode, daemon=True)
            t.start()
            
        msg = f"✅ Successfully registered {success_count} students."
        if missing_images > 0:
            msg += f" ⚠️ {missing_images} photos were NOT found in the zip or image names didn't match."
            
        if success_count > 0:
            messages.success(request, msg)
        if error_count > 0:
            messages.error(request, f"⚠️ Failed or skipped {error_count} students (email already exists).")

        return redirect("admin_dashboard")
    return redirect("admin_dashboard")

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_user(request, user_id):
    user = User.objects.get(id=user_id)
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        user.first_name = request.POST.get("name")
        user.email = request.POST.get("email")
        user.username = request.POST.get("email")
        profile.mobile = request.POST.get("mobile")
        profile.roll = request.POST.get("roll")
        profile.faculty = request.POST.get("faculty")
        profile.department = request.POST.get("department")
        profile.program = request.POST.get("program")
        profile.semester = request.POST.get("semester")
        profile.division = request.POST.get("division")
        if "image" in request.FILES: profile.image = request.FILES["image"]
        user.save()
        profile.save()
        messages.info(request, "User updated successfully!")
        return redirect("admin_dashboard")

    return render(request, "adminpanel/edit_user.html", {"u": user, "p": profile})

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.error(request, "User deleted successfully")
    return redirect("admin_dashboard")

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def bulk_delete_users(request):
    if request.method == "POST":
        user_ids = request.POST.getlist("user_ids")
        if user_ids:
            # Add safety: only delete non-staff users
            deleted_count, _ = User.objects.filter(id__in=user_ids, is_staff=False).delete()
            messages.success(request, f"✅ Successfully deleted {deleted_count} selected student(s).")
        else:
            messages.warning(request, "No students selected for deletion.")
    return redirect("admin_dashboard")

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def attendance(request):
    return render(request, "adminpanel/attendance.html")

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def faculties(request):
    if request.method == "POST":
        faculty_name = request.POST.get("faculty_name")
        faculty_code = request.POST.get("faculty_code", "").strip() or None
        if faculty_name:
            Faculty.objects.create(name=faculty_name, faculty_code=faculty_code, created_by=request.user)
        return redirect('faculties')
    return render(request, 'adminpanel/faculties.html', {'faculties': isolate_qs(request, Faculty.objects.all()).order_by('id')})

def delete_faculty(request, id):
    get_object_or_404(Faculty, id=id).delete()
    return redirect('faculties')

def edit_faculty(request, id):
    faculty = get_object_or_404(Faculty, id=id)
    if request.method == "POST":
        faculty_name = request.POST.get("faculty_name")
        faculty_code = request.POST.get("faculty_code", "").strip() or None
        if faculty_name:
            faculty.name = faculty_name
            faculty.faculty_code = faculty_code
            faculty.save()
        return redirect('faculties')
    return render(request, 'adminpanel/faculties.html', {'faculties': isolate_qs(request, Faculty.objects.all()).order_by('id'), 'edit_faculty': faculty})

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def departments(request):
    if request.method == "POST":
        dept_name = request.POST.get("department_name")
        if dept_name:
            Department.objects.create(name=dept_name, created_by=request.user)
        return redirect('departments')
    return render(request, 'adminpanel/departments.html', {
        'departments': isolate_qs(request, Department.objects.all()).order_by('name')
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_department(request, id):
    dept = get_object_or_404(Department, id=id)
    if request.method == "POST":
        dept.name = request.POST.get("department_name", dept.name)
        dept.save()
        return redirect('departments')
    return render(request, 'adminpanel/departments.html', {
        'departments': isolate_qs(request, Department.objects.all()).order_by('name'),
        'edit_department': dept
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_department(request, id):
    get_object_or_404(Department, id=id).delete()
    return redirect('departments')

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def programs(request):
    if request.method == "POST":
        name = request.POST.get("program_name")
        if name:
            Program.objects.create(name=name, created_by=request.user)
        return redirect('programs')
    return render(request, 'adminpanel/programs.html', {
        'programs': isolate_qs(request, Program.objects.all()).order_by('name')
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_program(request, id):
    prog = get_object_or_404(Program, id=id)
    if request.method == "POST":
        prog.name = request.POST.get("program_name", prog.name)
        prog.save()
        return redirect('programs')
    return render(request, 'adminpanel/programs.html', {
        'programs': isolate_qs(request, Program.objects.all()).order_by('name'),
        'edit_program': prog
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_program(request, id):
    get_object_or_404(Program, id=id).delete()
    return redirect('programs')

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def semesters(request):
    if request.method == "POST":
        name = request.POST.get("semester_name")
        if name and not Semester.objects.filter(name=name).exists():
            Semester.objects.create(name=name, created_by=request.user)
        return redirect('semesters')
    return render(request, 'adminpanel/semesters.html', {
        'semesters': isolate_qs(request, Semester.objects.all()).order_by('name')
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_semester(request, id):
    sem = get_object_or_404(Semester, id=id)
    if request.method == "POST":
        sem.name = request.POST.get("semester_name", sem.name)
        sem.save()
        return redirect('semesters')
    return render(request, 'adminpanel/semesters.html', {
        'semesters': isolate_qs(request, Semester.objects.all()).order_by('name'),
        'edit_semester': sem
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_semester(request, id):
    get_object_or_404(Semester, id=id).delete()
    return redirect('semesters')

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def divisions(request):
    if request.method == "POST":
        name = request.POST.get("division_name")
        if name and not Division.objects.filter(name=name).exists():
            Division.objects.create(name=name, created_by=request.user)
        return redirect('divisions')
    return render(request, 'adminpanel/divisions.html', {
        'divisions': isolate_qs(request, Division.objects.all()).order_by('name')
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_division(request, id):
    div = get_object_or_404(Division, id=id)
    if request.method == "POST":
        div.name = request.POST.get("division_name", div.name)
        div.save()
        return redirect('divisions')
    return render(request, 'adminpanel/divisions.html', {
        'divisions': isolate_qs(request, Division.objects.all()).order_by('name'),
        'edit_division': div
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_division(request, id):
    get_object_or_404(Division, id=id).delete()
    return redirect('divisions')

def attendance_view(request):
    try:
        profile = request.user.profile
    except Exception:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        from django.http import HttpResponse
        return HttpResponse("No profile exists for your account. Please contact admin.")

    selected_date_from = request.GET.get('date_from')
    selected_date_to = request.GET.get('date_to')
    selected_subject = request.GET.get('subject')
    
    from datetime import timedelta
    from django.utils import timezone
    from datetime import datetime
    
    # Default: last 7 days
    default_from = timezone.now().date() - timedelta(days=7)
    default_to = timezone.now().date()
    
    if selected_date_from:
        try:
            default_from = datetime.strptime(selected_date_from, "%Y-%m-%d").date()
        except ValueError:
            pass
            
    if selected_date_to:
        try:
            default_to = datetime.strptime(selected_date_to, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    # Fetch enrolled subjects for the dropdown
    from .models import SubjectEnrollment
    enrolled_enrollments = SubjectEnrollment.objects.filter(student=request.user).select_related('subject')
    enrolled_subjects = [e.subject for e in enrolled_enrollments]

    all_attendance = Attendance.objects.filter(student=request.user).select_related('session', 'session__subject')
    
    # Filter entirely by subject if selected
    if selected_subject:
        all_attendance = all_attendance.filter(session__subject_id=selected_subject)
    
    # Dashboard overall metrics (unfiltered by date to show total progress for selected subject)
    total_count = all_attendance.count()
    present_count = all_attendance.filter(status=True).count()
    absent_count = all_attendance.filter(status=False).count()
    attendance_pct = round((present_count / total_count) * 100) if total_count > 0 else 0
    
    # Filter for table using date range bounds
    attendance = all_attendance.filter(
        session__date__gte=default_from,
        session__date__lte=default_to
    ).order_by('-session__date')
        
    # Class Average Calculation
    class_avg_pct = 0
    class_attendances = Attendance.objects.all()
    if selected_subject:
        class_attendances = class_attendances.filter(session__subject_id=selected_subject)
    elif enrolled_subjects:
        subject_ids = [s.id for s in enrolled_subjects]
        class_attendances = class_attendances.filter(session__subject_id__in=subject_ids)
    
    class_total = class_attendances.count()
    if class_total > 0:
        class_present = class_attendances.filter(status=True).count()
        class_avg_pct = round((class_present / class_total) * 100)
    
    # Group records by subject
    from itertools import groupby
    grouped = {}
    for record in attendance:
        subject_name = record.session.subject.name if record.session.subject else "General Session"
        if subject_name not in grouped:
            grouped[subject_name] = []
        grouped[subject_name].append(record)

    return render(request, 'attendance.html', {
        'grouped_records': grouped,
        'profile': profile, 
        'default_from': default_from,
        'default_to': default_to,
        'selected_subject': int(selected_subject) if selected_subject and selected_subject.isdigit() else '',
        'enrolled_subjects': enrolled_subjects,
        'present_count': present_count,
        'absent_count': absent_count,
        'total_count': total_count,
        'attendance_pct': attendance_pct,
        'class_avg_pct': class_avg_pct
    })

@login_required
def report_view(request):
    student = request.user
    from accounts.models import Profile, SubjectEnrollment
    import json

    try:
        profile = Profile.objects.get(user=student)
    except Profile.DoesNotExist:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        from django.http import HttpResponse
        return HttpResponse("No profile exists for your account. Please contact admin.")
        
    enrolled_enrollments = SubjectEnrollment.objects.filter(student=student).select_related('subject')
    enrolled_subjects = [e.subject for e in enrolled_enrollments]
    
    selected_subject = request.GET.get('subject')

    all_attendance = Attendance.objects.filter(student=student).select_related('session', 'session__subject')
    if selected_subject:
        all_attendance = all_attendance.filter(session__subject_id=selected_subject)

    present_count = all_attendance.filter(status=True).count()
    absent_count = all_attendance.filter(status=False).count()
    total_count = all_attendance.count()
    attendance_pct = round((present_count / total_count) * 100) if total_count > 0 else 0
    
    table_data = []
    table_type = "SUBJECT"
    
    trend_labels = []
    trend_data = []
    
    if selected_subject:
        table_type = "SESSION"
        sessions = all_attendance.order_by('session__date')
        
        cumulative_present = 0
        cumulative_total = 0
        
        for idx, att in enumerate(sessions):
            cumulative_total += 1
            if att.status:
                cumulative_present += 1
                
            pct = round((cumulative_present / cumulative_total) * 100) if cumulative_total > 0 else 0
            date_str = att.session.date.strftime("%b %d")
            trend_labels.append(f"Day {idx+1}")
            trend_data.append(pct)
            
            table_data.append({
                'name': f"Lecture {idx+1} ({date_str})",
                'present': 1 if att.status else 0,
                'absent': 0 if att.status else 1,
                'total': 1,
                'pct': 100 if att.status else 0,
            })
            
        table_data.reverse() # newest first for table
    else:
        table_type = "SUBJECT"
        all_chronological = all_attendance.order_by('session__date')
        cumulative_present = 0
        cumulative_total = 0
        
        for idx, att in enumerate(all_chronological):
            cumulative_total += 1
            if att.status:
                cumulative_present += 1
            # Sample max 15 points for visual clarity
            if (idx + 1) % max(1, len(all_chronological)//15) == 0 or idx == len(all_chronological) - 1:
                pct = round((cumulative_present / cumulative_total) * 100) if cumulative_total > 0 else 0
                trend_labels.append(f"L{cumulative_total}")
                trend_data.append(pct)

        for sub in enrolled_subjects:
            sub_atts = Attendance.objects.filter(student=student, session__subject=sub)
            s_total = sub_atts.count()
            if s_total > 0:
                s_present = sub_atts.filter(status=True).count()
                s_absent = sub_atts.filter(status=False).count()
                s_pct = round((s_present / s_total) * 100)
                table_data.append({
                    'name': sub.name,
                    'present': s_present,
                    'absent': s_absent,
                    'total': s_total,
                    'pct': s_pct
                })
    
    return render(request, "report.html", {
        'profile': profile, 
        'present_count': present_count, 
        'absent_count': absent_count, 
        'total_count': total_count,
        'attendance_pct': attendance_pct,
        'trend_labels': json.dumps(trend_labels),
        'trend_data': json.dumps(trend_data),
        'table_data': table_data,
        'table_type': table_type,
        'enrolled_subjects': enrolled_subjects,
        'selected_subject': int(selected_subject) if selected_subject and selected_subject.isdigit() else '',
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def subjects(request):
    faculties = isolate_qs(request, Faculty.objects.all())
    departments = isolate_qs(request, Department.objects.all())
    programs = isolate_qs(request, Program.objects.all())
    semesters = isolate_qs(request, Semester.objects.all())
    divisions = isolate_qs(request, Division.objects.all())
    if request.method == "POST" and not request.POST.get("subject_id"):
        name = request.POST.get("subject_name")
        subject_type = request.POST.get("subject_type", "core")
        faculty_id = request.POST.get("faculty")
        department_id = request.POST.get("department")
        program_id = request.POST.get("program")  # For core only

        if name and faculty_id and department_id:
            if subject_type == 'core' and not program_id:
                return redirect('subjects')  # Core needs program

            course_code = request.POST.get("course_code", "").strip() or None
            s_obj = Subject.objects.create(
                name=name,
                course_code=course_code,
                subject_type=subject_type,
                faculty_id=faculty_id,
                department_id=department_id,
                program_id=program_id if subject_type == 'core' else None
            )
            if subject_type == 'core':
                s_obj.semester_id = request.POST.get("semester")
                s_obj.save()
                div_ids = request.POST.getlist("divisions")
                if div_ids:
                    s_obj.divisions.set(div_ids)
                s_obj.semesters.clear()
                s_obj.programs.clear()
                s_obj.program_semester_pairs.all().delete()
            else:
                s_obj.semester = None
                s_obj.save()
                s_obj.divisions.clear()
                s_obj.semesters.clear()
                s_obj.programs.clear()
                # Parse pairs JSON from form
                try:
                    pairs = json.loads(request.POST.get('pairs_json', '[]'))
                except (ValueError, TypeError):
                    pairs = []
                for pair in pairs:
                    prog_id = pair.get('program_id')
                    sem_id  = pair.get('semester_id')
                    if prog_id and sem_id:
                        SubjectProgramSemester.objects.get_or_create(
                            subject=s_obj,
                            program_id=prog_id,
                            semester_id=sem_id
                        )

        return redirect('subjects')
    
    all_subjects = Subject.objects.select_related('faculty', 'department', 'program', 'semester').prefetch_related('divisions', 'semesters', 'programs', 'program_semester_pairs__program', 'program_semester_pairs__semester').all().order_by('id')
    return render(request, 'adminpanel/subjects.html', {
        'subjects': all_subjects, 
        'faculties': faculties, 
        'departments': departments, 
        'programs': programs, 
        'semesters': semesters, 
        'divisions': divisions
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_subject(request, id):
    subject = get_object_or_404(Subject, id=id)
    if request.method == "POST":
        subject.name = request.POST.get("subject_name")
        subject.course_code = request.POST.get("course_code", "").strip() or None
        subject.subject_type = request.POST.get("subject_type", "core")
        subject.faculty_id = request.POST.get("faculty")
        subject.department_id = request.POST.get("department")
        subject.program_id = request.POST.get("program")
        
        if subject.subject_type == 'core':
            subject.semester_id = request.POST.get("semester")
            subject.program_id = request.POST.get("program")
            subject.save()
            div_ids = request.POST.getlist("divisions")
            subject.divisions.set(div_ids)
            subject.semesters.clear()
            subject.programs.clear()
            subject.program_semester_pairs.all().delete()
        else:
            subject.semester = None
            subject.program = None
            subject.save()
            subject.divisions.clear()
            subject.semesters.clear()
            subject.programs.clear()
            # Replace all pairs with newly submitted ones
            subject.program_semester_pairs.all().delete()
            try:
                pairs = json.loads(request.POST.get('pairs_json', '[]'))
            except (ValueError, TypeError):
                pairs = []
            for pair in pairs:
                prog_id = pair.get('program_id')
                sem_id  = pair.get('semester_id')
                if prog_id and sem_id:
                    SubjectProgramSemester.objects.get_or_create(
                        subject=subject,
                        program_id=prog_id,
                        semester_id=sem_id
                    )

        return redirect('subjects')
        
    all_subjects = Subject.objects.select_related('faculty', 'department', 'program', 'semester').prefetch_related('divisions', 'semesters', 'programs').all().order_by('id')
    return render(request, 'adminpanel/subjects.html', {
        'subjects': all_subjects, 
        'edit_subject': subject, 
        'faculties': isolate_qs(request, Faculty.objects.all()), 
        'departments': isolate_qs(request, Department.objects.all()), 
        'programs': isolate_qs(request, Program.objects.all()), 
        'semesters': isolate_qs(request, Semester.objects.all()), 
        'divisions': isolate_qs(request, Division.objects.all())
    })

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_subject(request, id):
    get_object_or_404(Subject, id=id).delete()
    return redirect('subjects')

def logout_user(request):
    is_admin = request.user.is_staff 
    logout(request) 
    if is_admin:
        return redirect('admin_login')
    else:
        return redirect('login')

# 💡 અહિયાંથી નીચેનો કોડ જે ઉડી ગયો હતો, એ મેં બરાબર જોડી દીધો છે.
def register(request):
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('phone', '').strip()
        password = request.POST.get('pass', '')
        cpassword = request.POST.get('cpass', '')

        context = {
            "old_name": name,
            "old_email": email,
            "old_mobile": mobile,
            "old_pass": password,
            "old_cpass": cpassword,
        }

        if not all([name, email, mobile, password, cpassword]):
            messages.error(request, "All fields are required")
            return render(request, "register.html", context)

        if not mobile.isdigit() or len(mobile) != 10:
            messages.error(request, "Mobile number must be exactly 10 digits")
            return render(request, "register.html", context)

        if password != cpassword:
            messages.error(request, "Password and Confirm Password must be same")
            return render(request, "register.html", context)
        
        # ==========================================
        # 💡 STRONG PASSWORD VALIDATION
        # ==========================================
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, "register.html", context)
        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter (A-Z).")
            return render(request, "register.html", context)
        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least one lowercase letter (a-z).")
            return render(request, "register.html", context)
        if not re.search(r'\d', password):
            messages.error(request, "Password must contain at least one number (0-9).")
            return render(request, "register.html", context)
        if not re.search(r'[@$!%*?&#]', password):
            messages.error(request, "Password must contain at least one special character (@, $, !, %, *, ?, &, #).")
            return render(request, "register.html", context)
        # ==========================================

        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered")
            return render(request, "register.html", context)

        # 💡 અહીથી OTP નો જાદુ ચાલુ...
        # 1. 6 આંકડાનો OTP બનાવો
        otp = str(random.randint(100000, 999999))

        # 2. બધો ડેટા ટેમ્પરરી Session માં સેવ કરો (ડેટાબેઝમાં નહિ)
        request.session['temp_user'] = {
            'name': name,
            'email': email,
            'mobile': mobile,
            'password': password,
            'otp': otp
        }

        # 3. ઈમેલ મોકલો
        subject = 'Verify Your Email - LookIn AI'
        message = f'Hello {name},\n\nYour OTP for registration is: {otp}\n\nPlease do not share this with anyone.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]

        try:
            send_mail(subject, message, email_from, recipient_list)
            messages.success(request, f"OTP sent to {email}. Please verify.")
            return redirect('verify_otp') # ઈમેલ મોકલીને OTP પેજ પર મોકલી દો
        except Exception as e:
            messages.error(request, "Error sending email. Please try again.")
            return render(request, "register.html", context)

    return render(request, "register.html")

# 🚀 નવું ફંક્શન: OTP ચેક કરવા માટે
def verify_otp(request):
    # જો કોઈ ડાયરેક્ટ આ પેજ ખોલે તો પાછા મોકલો
    if 'temp_user' not in request.session:
        messages.error(request, "Please register first.")
        return redirect('register')

    if request.method == "POST":
        user_otp = request.POST.get('otp', '').strip()
        temp_user = request.session['temp_user']

        # 💡 OTP ચેક કરો
        if user_otp == temp_user['otp']:
            # સાચો OTP! હવે ફાઇનલી યુઝર બનાવી દો
            user = User.objects.create_user(
                username=temp_user['email'],
                email=temp_user['email'],
                password=temp_user['password'],
                first_name=temp_user['name']
            )
            Profile.objects.create(
    user=user, 
    mobile=temp_user['mobile'],
    roll='',
    program='',
    semester='',
    division='',
)

            # Session માંથી ડેટા કાઢી નાખો
            del request.session['temp_user']

            messages.success(request, "Email verified successfully! You can now login.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "verify_otp.html", {'email': request.session['temp_user']['email']})

def login_user(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('pass')

        user = authenticate(request, username=email, password=password)

        if user and not user.is_staff:
            login(request, user)
            return redirect("profile")
        else:
            messages.error(request, "Invalid user credentials")

    return render(request, "login.html")

@login_required
def profile(request):
    if request.user.is_staff:
        return redirect('admin_dashboard')

    profile = Profile.objects.filter(user=request.user).first()

    if request.method == "POST":
        if profile is None:
            profile = Profile.objects.create(user=request.user)

        request.user.first_name = request.POST.get("first_name", request.user.first_name).strip()
        request.user.last_name = request.POST.get("last_name", request.user.last_name).strip()
        request.user.save()

        mobile = request.POST.get("mobile", "").strip()

        if mobile and not re.fullmatch(r"\d{10}", mobile):
            messages.error(request, "Mobile number must be exactly 10 digits")
            return redirect("profile")

        profile.mobile = mobile
        profile.roll = request.POST.get("roll", "").strip()
        profile.faculty = request.POST.get("faculty", "").strip()
        profile.department = request.POST.get("department", "").strip()
        profile.program = request.POST.get("program", "").strip()
        profile.semester = request.POST.get("semester", "").strip()
        profile.division = request.POST.get("division", "").strip()

        if "image" in request.FILES:
            profile.image = request.FILES["image"]

        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("profile")

    return render(request, "profile.html", {
        "profile": profile,
        "profile_exists": profile is not None
    })


# ✅ Permanent Fix - Password Reset
# Aa function views.py na LAST MA add karo
def custom_password_reset(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()

        # Pehla email thi shodho
        user = User.objects.filter(email=email).first()

        # Na malyo to username thi try karo
        if not user:
            user = User.objects.filter(username=email).first()

        # User malyo to email fix karo ane reset mail moko
        if user:
            # Username ne email sathe sync karo - future mate
            if user.username != user.email and user.email:
                pass  # email already set che
            
            from django.contrib.auth.forms import PasswordResetForm
            # User no email set karo jo username hoy
            if not user.email:
                user.email = email
                user.save()

            form = PasswordResetForm({'email': user.email})
            if form.is_valid():
                form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name='registration/password_reset_email.html',
                    subject_template_name='registration/password_reset_subject.txt',
                )

        # Security mate - user hoy ke na hoy same page dikhaao
        return redirect('password_reset_done')

    return render(request, "password_reset.html")


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE FACE SCAN VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

def _send_live_scan_email_async(student, session):
    """Fire-and-forget immediate email for live/kiosk face scan confirmation."""
    if not student.email:
        return
        
    from threading import Thread
    from django.core.mail import send_mail
    from django.utils import timezone as tz
    from django.conf import settings

    def _send():
        try:
            subject_name = session.subject.name if session.subject else "Class"
            date_str = tz.now().strftime("%d %B %Y")
            subject_title = "Face Verified \u2705 - LookIn-AI Live Scan"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="background: #10b981; padding: 20px; text-align: center;">
                    <h2 style="color: white; margin: 0; letter-spacing: 1px;">Face Verified</h2>
                </div>
                <div style="padding: 30px; background: #ffffff;">
                    <p style="font-size: 16px; color: #334155;">Hi <strong>{student.first_name or student.username}</strong>,</p>
                    <p style="font-size: 16px; color: #334155;">
                        Your face was successfully verified for today's live session!
                    </p>
                    <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin: 25px 0;">
                        <p style="margin: 0 0 10px 0; color: #475569;">📚 <strong>Subject:</strong> {subject_name}</p>
                        <p style="margin: 0 0 10px 0; color: #475569;">🕒 <strong>Lecture Slot:</strong> {session.lecture_slot}</p>
                        <p style="margin: 0; color: #475569;">📅 <strong>Date:</strong> {date_str}</p>
                    </div>
                </div>
                <div style="background: #f1f5f9; padding: 15px; text-align: center;">
                    <p style="margin: 0; font-size: 12px; color: #94a3b8;">Automated message from LookIn AI Attendance System</p>
                </div>
            </div>
            """
            from django.core.mail import get_connection, EmailMultiAlternatives
            from django.utils.html import strip_tags

            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives(subject_title, text_content, settings.EMAIL_HOST_USER, [student.email])
            msg.attach_alternative(html_content, "text/html")

            with get_connection(fail_silently=False) as connection:
                connection.send_messages([msg])
            with open('mail_debug.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{tz.now()}] SUCCESS async mail sent to {student.email}\n")

        except Exception as e:
            import traceback
            with open('mail_debug.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{tz.now()}] ERROR async mail: {traceback.format_exc()}\n")

    Thread(target=_send, daemon=True).start()


@csrf_exempt
@require_POST
def api_live_scan(request):
    """
    POST /api/live-scan/
    Body (JSON): { "frame": "<base64 image>", "session_id": <int> }

    Returns JSON:
      Success  → { "status": "match", "name": "...", "roll": "...", "already_marked": bool }
      No face  → { "status": "no_face" }
      No match → { "status": "no_match" }
      Error    → { "status": "error", "message": "..." }
    """
    import json
    from . import encoding_service as es

    try:
        body = json.loads(request.body)
        b64 = body.get("frame", "")
        session_id = body.get("session_id")

        if not b64 or not session_id:
            return JsonResponse({"status": "error", "message": "frame and session_id required"}, status=400)

        # Validate session
        try:
            live_session = LiveAttendanceSession.objects.get(id=session_id, status='active')
        except LiveAttendanceSession.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Session not found or closed"}, status=404)

        # Decode frame (BGR)
        img_bgr = es.decode_base64_frame(b64)
        if img_bgr is None:
            return JsonResponse({"status": "error", "message": "Invalid image data"}, status=400)

        # Detect faces with InsightFace
        app = es._get_insight_app()
        processed = es._preprocess_bgr(img_bgr)
        faces = app.get(processed)

        if not faces:
            return JsonResponse({"status": "no_face"})

        # Use the face with highest detection confidence
        best_face = max(faces, key=lambda f: float(f.det_score))
        if best_face.embedding is None:
            return JsonResponse({"status": "no_face"})

        emb = best_face.embedding.astype(np.float32)
        norm = np.linalg.norm(emb)
        if norm == 0:
            return JsonResponse({"status": "no_face"})
        emb = emb / norm

        # Match against cached encodings
        matched_user, sim = es.match_face(emb, threshold=0.45)
        if matched_user is None:
            return JsonResponse({"status": "no_match"})

        # Buffer match in memory (confidence = cosine similarity)
        from .session_buffer import get_live_buffer
        buf = get_live_buffer(session_id)

        already_marked = matched_user.id in buf.matched_user_ids
        buf.add(matched_user.id, confidence=round(sim, 4))
        
        if not already_marked:
            # _send_live_scan_email_async(matched_user, live_session) # DISABLED: No emails for present students
            pass

        profile = getattr(matched_user, 'profile', None)
        return JsonResponse({
            "status": "match",
            "name": matched_user.first_name or matched_user.username,
            "roll": profile.roll if profile else "",
            "division": profile.division if profile else "",
            "already_marked": already_marked,
            "confidence": round(sim * 100, 1),
            "image_url": profile.image.url if (profile and profile.image) else "",
        })

    except Exception as exc:
        import traceback
        print("api_live_scan error:", traceback.format_exc())
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def create_live_session(request):
    """Admin creates / manages live attendance sessions."""
    if request.method == "POST":
        action = request.POST.get("action", "create")

        if action == "create":
            subject_id = request.POST.get("subject", "")
            subject = None
            if subject_id:
                try:
                    subject = Subject.objects.select_related(
                        'faculty', 'department', 'program', 'semester'
                    ).get(id=subject_id)
                except (Subject.DoesNotExist, ValueError):
                    subject = None

            if not subject:
                messages.error(request, "Subject is required and must be valid.")
                return redirect('create_live_session')
                
            division_name = request.POST.get("division", "")
            if subject.subject_type == 'elective':
                division_name = "N/A"
                semester_name = "Elective"
            else:
                semester_name = subject.semester.name if subject.semester else ""
                
            faculty_name = subject.faculty.name if subject and subject.faculty else ""
            dept_name = subject.department.name if subject and subject.department else ""
            prog_name = subject.program.name if subject and subject.program else ""
                
            ls = LiveAttendanceSession.objects.create(
                faculty=faculty_name,
                department=dept_name,
                program=prog_name,
                semester=semester_name,
                division=division_name,
                subject=subject,
                lecture_slot=request.POST.get("slot", 1),
                created_by=request.user,
                status='active',
            )
            messages.success(request, f"Live session created! Share Session ID: {ls.id}")
            return redirect('create_live_session')

        elif action == "close":
            session_id = request.POST.get("session_id")
            try:
                ls = LiveAttendanceSession.objects.get(id=session_id, created_by=request.user)
                from django.utils import timezone as tz
                ls.status = 'closed'
                ls.closed_at = tz.now()
                ls.save()
                
                # Flush the live buffer to DB before transferring to permanent log
                from .session_buffer import get_live_buffer, clear_live_buffer
                buf = get_live_buffer(session_id)
                buf.flush_live_records()
                clear_live_buffer(session_id)
                
                _transfer_live_session_to_attendance(ls)
                messages.success(request, "Session closed and attendance permanently recorded.")
            except LiveAttendanceSession.DoesNotExist:
                messages.error(request, "Session not found.")
            return redirect('create_live_session')

    sessions = LiveAttendanceSession.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:20]

    # Annotate each session with record count
    for s in sessions:
        s.scan_count = s.records.count()

    return render(request, "adminpanel/create_live_session.html", {
        "sessions": sessions,
        "faculties": isolate_qs(request, Faculty.objects.all()),
        "departments": isolate_qs(request, Department.objects.all()),
        "programs": isolate_qs(request, Program.objects.all()),
        "semesters": isolate_qs(request, Semester.objects.all()),
        "divisions": isolate_qs(request, Division.objects.all()),
        "subjects": isolate_qs(request, Subject.objects.all()),
    })

def send_bulk_attendance_emails(attendance_list, subject, slot, date_obj):
    """
    Send attendance emails.
    STRICT RULE: ONLY sends to ABSENT students, with current % and low attendance warnings.
    """
    import time
    from threading import Thread
    from django.core.mail import send_mail
    from django.conf import settings
    from .models import Attendance

    print(f"=== EMAIL DEBUG ===")
    for item in attendance_list:
        if isinstance(item, tuple):
            s, st = item
        else:
            s, st = item, False
        print(f"  {s.first_name} | status={st} | div={getattr(s.profile, 'division', 'N/A')}")
        
    # NUCLEAR OPTION: filter absent only, always
    absent_only = []
    for item in attendance_list:
        if isinstance(item, tuple):
            student, status = item
        else:
            student, status = item, False
        
        if status:  # True = present → SKIP
            print(f"SKIP (present): {student.first_name}")
            continue
            
        # Division check for core subjects
        if hasattr(subject, 'subject_type') and subject.subject_type == 'core':
            profile = getattr(student, 'profile', None)
            student_div = (getattr(profile, 'division', '') or '').strip().upper()
            # Get session division from recent session
            from .models import LiveAttendanceSession
            recent = LiveAttendanceSession.objects.filter(
                subject=subject
            ).order_by('-created_at').first()
            if recent:
                session_div = (recent.division or '').strip().upper()
                if student_div != session_div:
                    print(f"SKIP (wrong div): {student.first_name} Div{student_div} vs Div{session_div}")
                    continue
        
        # ensure email address exists
        if not getattr(student, 'email', None):
            continue
            
        absent_only.append(student)
    
    if not absent_only:
        print("No valid absent students — zero emails sent")
        return

    subject_name = subject if isinstance(subject, str) else subject.name
    calc_subject = None if isinstance(subject, str) else subject

    def _send_batches():
        BATCH_SIZE = 10
        BATCH_DELAY = 5
        date_str = date_obj.strftime("%d %B %Y") if hasattr(date_obj, 'strftime') else str(date_obj)

        chunks = [absent_only[i:i + BATCH_SIZE] for i in range(0, len(absent_only), BATCH_SIZE)]

        for chunk in chunks:
            for student in chunk:
                # calculate attendance %
                if calc_subject:
                    total = Attendance.objects.filter(
                        student=student,
                        session__subject=calc_subject
                    ).count()
                    present = Attendance.objects.filter(
                        student=student,
                        session__subject=calc_subject,
                        status=True
                    ).count()
                else:
                    total = 0
                    present = 0
                
                percentage = (present / total * 100) if total > 0 else 0
                
                body = f"""Dear {student.first_name},

You were ABSENT for {subject_name} on {date_str}.
Your current attendance: {percentage:.1f}%
"""
                # Add warning in SAME email if < 75%
                if percentage < 75:
                    body += f"""
⚠️ WARNING: Your attendance is below 75%!
Please attend regularly or contact faculty.
"""
                
                # Send ONE email only
                send_mail(
                    subject=f"Absent Alert - {subject_name}",
                    message=body,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[student.email],
                    fail_silently=True
                )
                
                print(f"Email sent to {student.first_name} — Absent, {percentage:.1f}%")

            time.sleep(BATCH_DELAY)
            
        print("Present students — NO email sent")

    Thread(target=_send_batches, daemon=True).start()

def _transfer_live_session_to_attendance(ls):
    """
    Called when a live session closes. Copies the real-time Live scans into
    the permanent static Attendance/AttendanceSession tables so students
    see it in their 'Attendance Log' portal, and absentees are correctly marked.
    """
    try:
        # For testing logic: ALWAYS create a new AttendanceSession so multiple 
        # identical test lectures on the same day show up individually in the dashboard.
        perm_session = AttendanceSession.objects.create(
            faculty=ls.faculty,
            department=ls.department,
            program=ls.program,
            semester=ls.semester,
            division=ls.division,
            subject=ls.subject,
            lecture_slot=ls.lecture_slot,
        )
        # Override created timestamp to match live session start
        perm_session.date = ls.created_at
        perm_session.save(update_fields=['date'])

        # ✅ ENROLLED STUDENTS ONLY — Subject ma enrolled students ne j attendance lage
        if ls.subject:
            enrolled_ids = SubjectEnrollment.objects.filter(
                subject=ls.subject
            ).values_list('student_id', flat=True)
            expected_students = User.objects.filter(id__in=enrolled_ids)

            if not expected_students.exists():
                # Fallback: jo koi enrolled nathi to division/program match karo
                print("⚠️ No students enrolled in subject, falling back to division/program filter")
                expected_students = User.objects.filter(
                    is_staff=False,
                    profile__program=ls.program,
                    profile__semester=ls.semester,
                    profile__division=ls.division
                )
        else:
            # No subject set — fallback to division/program match
            expected_students = User.objects.filter(
                is_staff=False,
                profile__program=ls.program,
                profile__semester=ls.semester,
                profile__division=ls.division
            )
        
        # Determine who actually scanned their face today
        present_student_ids = set(ls.records.values_list('student_id', flat=True))
        
        # Merge expected students and anybody who actually scanned
        expected_student_ids = set(expected_students.values_list('id', flat=True))
        all_relevant_ids = expected_student_ids.union(present_student_ids)
        all_students = User.objects.filter(id__in=all_relevant_ids)
        
        # Fix attendance marking: Exclude wrong division students from DB records
        valid_all_students = []
        for st in all_students:
            profile = getattr(st, 'profile', None)
            if ls.subject and ls.subject.subject_type == 'core':
                student_div = (getattr(profile, 'division', '') or '').strip().upper()
                session_div = (ls.division or '').strip().upper()
                if student_div != session_div and st.id not in present_student_ids:
                    continue
            valid_all_students.append(st)

        # Create Attendance records -- ONE bulk write via SessionBuffer
        from .session_buffer import SessionBuffer
        buf = SessionBuffer(perm_session.id)
        for st in valid_all_students:
            if st.id in present_student_ids:
                buf.add(st.id, confidence=1.0)
        present_list, absent_list = buf.flush_attendance(valid_all_students)

        # Strict absent list for emails using explicit helper
        present_ids = {s.id for s, _ in present_list}
        absent_only = get_valid_absent_students(perm_session, ls.subject, present_ids)
        
        if absent_only:
            with open('mail_debug.txt', 'a', encoding='utf-8') as f:
                f.write(f"[{perm_session.date}] Absent mail sending for {len(absent_only)} absent students (present={len(present_list)}, NO email)\n")
            absent_tuples = [(s, False) for s in absent_only]
            send_bulk_attendance_emails(absent_tuples, ls.subject if ls.subject else "Class", ls.lecture_slot, perm_session.date)
    except Exception as e:
        import traceback
        with open('mail_debug.txt', 'a', encoding='utf-8') as f:
            f.write(f"Error transferring live session: {traceback.format_exc()}\n")


@login_required
def close_live_session_api(request, session_id):
    """Quick AJAX endpoint to close a session."""
    try:
        ls = LiveAttendanceSession.objects.get(id=session_id)
        if request.user.is_staff:
            from django.utils import timezone as tz
            ls.status = 'closed'
            ls.closed_at = tz.now()
            ls.save()
            
            # Flush live buffer
            from .session_buffer import get_live_buffer, clear_live_buffer
            buf = get_live_buffer(session_id)
            buf.flush_live_records()
            clear_live_buffer(session_id)
            
            _transfer_live_session_to_attendance(ls)
            return JsonResponse({"ok": True})
    except LiveAttendanceSession.DoesNotExist:
        pass
    return JsonResponse({"ok": False}, status=400)


@require_GET
def live_session_status(request, session_id):
    """
    GET /api/live-session/<id>/status/
    Returns current scan count and list of scanned students (for admin live dashboard).
    """
    try:
        ls = LiveAttendanceSession.objects.get(id=session_id)
    except LiveAttendanceSession.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    from .session_buffer import get_live_buffer
    buf = get_live_buffer(session_id)
    buffered_user_ids = buf.matched_user_ids

    # Query users that are in the buffer (since DB writes are deferred)
    from django.contrib.auth.models import User
    buffered_users = User.objects.filter(id__in=buffered_user_ids).select_related('profile')

    # Query DB records just in case (for partial flushes or closed sessions)
    records = LiveAttendanceRecord.objects.filter(
        live_session=ls
    ).select_related('student', 'student__profile').order_by('-scanned_at')

    students = []
    seen_ids = set()

    # Load buffered users (most recent first conceptually)
    from django.utils import timezone
    now_str = timezone.now().strftime("%H:%M:%S")
    for u in buffered_users:
        if u.id not in seen_ids:
            seen_ids.add(u.id)
            p = getattr(u, 'profile', None)
            students.append({
                "name": u.first_name or u.username,
                "roll": p.roll if p else "",
                "division": p.division if p else "",
                "image_url": p.image.url if (p and p.image) else "",
                "scanned_at": now_str, # Buffer is in-memory without timestamp mapping for dashboard UI simplicity
            })

    for rec in records:
        if rec.student.id not in seen_ids:
            seen_ids.add(rec.student.id)
            p = getattr(rec.student, 'profile', None)
            students.append({
                "name": rec.student.first_name or rec.student.username,
                "roll": p.roll if p else "",
                "division": p.division if p else "",
                "image_url": p.image.url if (p and p.image) else "",
                "scanned_at": rec.scanned_at.strftime("%H:%M:%S"),
            })

    return JsonResponse({
        "session_id": ls.id,
        "status": ls.status,
        "scan_count": len(students),
        "students": students,
    })


def live_scan_page(request, session_id=None):
    """
    Student-facing live scan page.
    If session_id is provided in URL, auto-select that session.
    """
    from django.shortcuts import redirect
    # Student self-scan disabled - admin only
    return redirect('login')

    active_sessions = LiveAttendanceSession.objects.filter(
        status='active'
    ).select_related('subject').order_by('-created_at')

    selected_session = None
    if session_id:
        try:
            selected_session = LiveAttendanceSession.objects.get(id=session_id, status='active')
        except LiveAttendanceSession.DoesNotExist:
            pass

    return render(request, "live_scan.html", {
        "active_sessions": active_sessions,
        "selected_session": selected_session,
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def compute_encodings_api(request):
    """
    Admin utility: re-compute and store face encodings for all students.
    Shows a progress page and results.
    """
    result = None
    if request.method == "POST":
        from . import encoding_service as es
        result = es.bulk_recompute_encodings()
        messages.success(
            request,
            f"Done! ✅ {result['success']} encoded, ❌ {result['failed']} failed, ⏭️ {result['skipped']} skipped."
        )

    students_with_no_encoding = Profile.objects.filter(
        image__isnull=False,
        face_encoding__isnull=True,
        user__is_staff=False
    ).count()

    total_encoded = Profile.objects.filter(
        face_encoding__isnull=False,
        user__is_staff=False
    ).count()

    return render(request, "adminpanel/compute_encodings.html", {
        "result": result,
        "students_with_no_encoding": students_with_no_encoding,
        "total_encoded": total_encoded,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# KIOSK MODE VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

def kiosk_page(request, token):
    """
    Kiosk page — rendered on a tablet at the classroom door.
    The token is a secret 32-char UUID hex, impossible to guess.
    No login required — the token IS the authentication.
    """
    try:
        session = LiveAttendanceSession.objects.get(
            kiosk_token=token, status='active'
        )
    except LiveAttendanceSession.DoesNotExist:
        return render(request, "kiosk.html", {"error": "Session not found or closed."})

    return render(request, "kiosk.html", {
        "session": session,
        "kiosk_token": token,
    })


@csrf_exempt
@require_POST
def api_kiosk_scan(request):
    """
    POST /api/kiosk-scan/
    Body (JSON): {
        "kiosk_token": "<32-char hex>",
        "frames": ["<base64 img>", "<base64 img>", ...]  // 3-5 frames for liveness
    }

    Flow:
    1. Validate kiosk token → find session
    2. Run liveness check on multi-frame input → reject photos
    3. Extract face encoding from best frame
    4. Match against cached encodings
    5. Mark attendance if match found

    Returns JSON with status: "match" | "no_match" | "no_face" | "spoof" | "error"
    """
    import json
    from . import encoding_service as es

    import time

    # PROBLEM 2 FIX: Guarantee cache HIT — warm_cache() is a no-op if already warm (5min TTL)
    es.warm_cache(force=False)

    try:
        body = json.loads(request.body)
        token = body.get("kiosk_token", "")
        frames = body.get("frames", [])

        if not token:
            return JsonResponse({"status": "error", "message": "kiosk_token required"}, status=400)

        if not frames or len(frames) < 3:
            return JsonResponse({"status": "error", "message": "Need at least 3 frames for liveness check"}, status=400)

        # 1. Validate token → find session
        try:
            live_session = LiveAttendanceSession.objects.get(
                kiosk_token=token, status='active'
            )
        except LiveAttendanceSession.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid or expired kiosk token"}, status=403)

        t_liveness = time.time()
        # 2. Liveness check — fast pixel-diff approach (no InsightFace per-frame)
        liveness = es.check_liveness(frames)
        print(f"[KIOSK] Liveness check: {time.time()-t_liveness:.2f}s → alive={liveness['alive']} reason={liveness['reason']}")
        if not liveness["alive"]:
            reason_msg = {
                "static_image": "Spoof detected — photo or static image. Please show your REAL face.",
                "no_face": "No face detected in frames. Position your face clearly.",
                "too_few_frames": "Not enough frames captured. Please hold still for 2 seconds.",
            }.get(liveness["reason"], "Liveness check failed.")

            return JsonResponse({
                "status": "spoof",
                "message": reason_msg,
                "liveness": liveness,
            })

        t1 = time.time()
        # 3. Extract face embedding from the middle frame (best quality)
        mid_idx = len(frames) // 2
        mid_bgr = es.decode_base64_frame(frames[mid_idx])
        if mid_bgr is None:
            return JsonResponse({"status": "error", "message": "Failed to decode frame"}, status=400)
        print(f"[KIOSK] Frame decode: {time.time()-t1:.2f}s")

        t2 = time.time()
        app = es.get_kiosk_app()
        # OPT 2: Resize frame to max 640px before detection (same as video pipeline)
        mid_bgr = preprocess_frame(mid_bgr)
        processed = es._preprocess_bgr(mid_bgr)
        faces = app.get(processed)
        print(f"[KIOSK] InsightFace detect: {time.time()-t2:.2f}s (faces={len(faces) if faces else 0})")

        if not faces:
            return JsonResponse({"status": "no_face"})

        best_face = max(faces, key=lambda f: float(f.det_score))
        if best_face.embedding is None:
            return JsonResponse({"status": "no_face"})

        emb = best_face.embedding.astype(np.float32)
        norm = np.linalg.norm(emb)
        if norm == 0:
            return JsonResponse({"status": "no_face"})
        emb = emb / norm

        t3 = time.time()
        # 4. Match against cached encodings
        matched_user, sim = es.match_face(emb, threshold=0.45)
        print(f"[KIOSK] Face matching: {time.time()-t3:.2f}s (sim={round(sim,3) if sim else None})")
        print(f"[KIOSK] Total scan time: {time.time()-t1:.2f}s")
        if matched_user is None:
            return JsonResponse({"status": "no_match"})

        profile = getattr(matched_user, 'profile', None)
        subject = live_session.subject

        # Check enrollment first
        from .models import SubjectEnrollment
        if subject:
            is_enrolled = SubjectEnrollment.objects.filter(
                subject=subject,
                student=matched_user
            ).exists()
            
            if not is_enrolled:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Not enrolled in {subject.name}',
                    'detail': 'not_enrolled'
                })
            
            # For CORE subjects, check division
            if subject.subject_type == 'core':
                student_div = (profile.division or '').strip().upper() if profile else ''
                session_div = (live_session.division or '').strip().upper()
                if student_div != session_div:
                    return JsonResponse({
                        'status': 'error', 
                        'message': f'Wrong division! You are Div {student_div}, this is Div {session_div}',
                        'detail': 'wrong_division'
                    })

        # 5. Use session buffer (NO direct DB write mid-session)
        from .session_buffer import get_live_buffer
        buf = get_live_buffer(live_session.id)
        already_marked = matched_user.id in buf.matched_user_ids
        buf.add(matched_user.id, confidence=round(sim, 4))

        if not already_marked:
            # _send_live_scan_email_async(matched_user, live_session) # DISABLED: No emails for present students
            pass

        profile = getattr(matched_user, 'profile', None)
        return JsonResponse({
            "status": "match",
            "name": matched_user.first_name or matched_user.username,
            "roll": profile.roll if profile else "",
            "division": profile.division if profile else "",
            "already_marked": already_marked,
            "confidence": round(sim * 100, 1),
            "image_url": profile.image.url if (profile and profile.image) else "",
            "liveness": liveness,
        })

    except Exception as exc:
        import traceback
        print("api_kiosk_scan error:", traceback.format_exc())
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)


# ═══════════════════════════════════════════════════════════════════════════════
# SUBJECT ENROLLMENT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def manage_enrollment(request, subject_id=None):
    """
    Admin page to manage which students are enrolled in which subjects.
    Only enrolled students will receive attendance marks and email notifications.
    """
    from .models import SubjectEnrollment

    subjects = Subject.objects.select_related(
        'faculty', 'department', 'program', 'semester'
    ).prefetch_related('divisions', 'semesters', 'program_semester_pairs__program', 'program_semester_pairs__semester').all().order_by('name')

    selected_subject = None
    enrolled_students = []
    available_students = []

    # GET parameter se subject select karo
    sid = subject_id or request.GET.get('subject_id')
    if sid:
        try:
            selected_subject = Subject.objects.select_related(
                'faculty', 'department', 'program', 'semester'
            ).get(id=sid)
        except Subject.DoesNotExist:
            messages.error(request, "Subject not found.")
            return redirect('manage_enrollment')

    # POST handling — enroll/remove
    if request.method == "POST":
        action = request.POST.get("action")
        post_subject_id = request.POST.get("subject_id")

        if post_subject_id:
            try:
                selected_subject = Subject.objects.select_related(
                    'faculty', 'department', 'program', 'semester'
                ).get(id=post_subject_id)
            except Subject.DoesNotExist:
                messages.error(request, "Subject not found.")
                return redirect('manage_enrollment')

            if action == "enroll":
                student_ids = request.POST.getlist("student_ids")
                if student_ids:
                    count = 0
                    for student_id in student_ids:
                        try:
                            student = User.objects.get(id=student_id, is_staff=False)
                            _, created = SubjectEnrollment.objects.get_or_create(
                                subject=selected_subject,
                                student=student
                            )
                            if created:
                                count += 1
                        except User.DoesNotExist:
                            continue
                    messages.success(request, f"✅ {count} students enrolled in {selected_subject.name}!")
                else:
                    messages.error(request, "Please select at least one student.")

            elif action == "remove":
                enrollment_id = request.POST.get("enrollment_id")
                try:
                    enrollment = SubjectEnrollment.objects.get(id=enrollment_id)
                    student_name = enrollment.student.first_name
                    enrollment.delete()
                    messages.success(request, f"✅ {student_name} removed from {selected_subject.name}")
                except SubjectEnrollment.DoesNotExist:
                    messages.error(request, "Enrollment not found.")

            elif action == "remove_all":
                count = SubjectEnrollment.objects.filter(subject=selected_subject).count()
                SubjectEnrollment.objects.filter(subject=selected_subject).delete()
                messages.success(request, f"✅ All {count} students removed from {selected_subject.name}")

            elif action == "bulk_csv":
                csv_file = request.FILES.get('csv_file')
                if not csv_file:
                    messages.error(request, "Please select a valid CSV file.")
                elif not csv_file.name.endswith('.csv'):
                    messages.error(request, "Invalid file format. Only CSV files are allowed.")
                else:
                    import csv
                    from io import TextIOWrapper
                    csv_parsed = csv.reader(TextIOWrapper(csv_file.file, encoding='utf-8'))
                    
                    enrolled_count = 0
                    not_found_emails = []
                    
                    for i, row in enumerate(csv_parsed):
                        if not row:
                            continue
                        
                        email = str(row[0]).strip().lower()
                        
                        # Skip empty lines or header if it looks like header
                        if not email or i == 0 and ('email' in email or 'mail' in email):
                            continue
                            
                        try:
                            student = User.objects.get(email__iexact=email, is_staff=False)
                            _, created = SubjectEnrollment.objects.get_or_create(
                                subject=selected_subject,
                                student=student
                            )
                            if created:
                                enrolled_count += 1
                        except User.DoesNotExist:
                            not_found_emails.append(email)
                            
                    if enrolled_count > 0:
                        messages.success(request, f"✅ {enrolled_count} students successfully enrolled from CSV!")
                    if not_found_emails:
                        err_str = ", ".join(not_found_emails[:10])
                        if len(not_found_emails) > 10:
                            err_str += f" ...and {len(not_found_emails) - 10} more."
                        messages.error(request, f"⚠️ The following {len(not_found_emails)} emails were not found or registerd: {err_str}")

            return redirect(f'/subject-enrollment/?subject_id={selected_subject.id}')

    # Fetch enrolled and available students for the selected subject
    if selected_subject:
        enrolled_students = SubjectEnrollment.objects.filter(
            subject=selected_subject
        ).select_related('student', 'student__profile').order_by('student__first_name')

        enrolled_ids = enrolled_students.values_list('student_id', flat=True)
        available_students = User.objects.filter(
            is_staff=False
        ).exclude(
            id__in=enrolled_ids
        ).select_related('profile').order_by('first_name')

    total_students = User.objects.filter(is_staff=False).count()

    return render(request, "adminpanel/manage_enrollment.html", {
        "subjects": subjects,
        "selected_subject": selected_subject,
        "enrolled_students": enrolled_students,
        "available_students": available_students,
        "total_subjects": subjects.count(),
        "total_students": total_students,
        "programs": isolate_qs(request, Program.objects.all()).order_by('name'),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# GRANT proxy MEDICAL LEAVE
# ═══════════════════════════════════════════════════════════════════════════════

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def grant_medical_leave(request):
    """
    Admin UI to grant proxy proxy attendance to a student for a specific date range 
    due to Medical Leave or Dean approval.
    """
    from datetime import datetime
    
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")
        subject_id = request.POST.get("subject_id")
        
        if student_id and start_date_str and end_date_str and subject_id:
            try:
                student = User.objects.get(id=student_id, is_staff=False)
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                
                # --- DATE VALIDATION LOGIC ---
                today = datetime.now().date()
                if start_date > today or end_date > today:
                    messages.error(request, "⚠️ Error: Dates cannot be in the future (Bhavishya ni date na chale!).")
                    return redirect('grant_medical_leave')
                if start_date > end_date:
                    messages.error(request, "⚠️ Error: Start Date cannot be after the End Date.")
                    return redirect('grant_medical_leave')
                
                # Fetch all attendance sessions in date range
                sessions = AttendanceSession.objects.filter(date__date__gte=start_date, date__date__lte=end_date)
                
                if subject_id != "all":
                    sessions = sessions.filter(subject_id=subject_id)
                
                # Update or create Attendance records
                updated_count = 0
                for session in sessions:
                    from .models import Attendance
                    att, created = Attendance.objects.get_or_create(session=session, student=student)
                    if not att.status:
                        att.status = True
                        att.save()
                        updated_count += 1
                    elif created:
                        updated_count += 1
                
                messages.success(request, f"✅ Granted Proxy Attendance for {student.first_name}! {updated_count} absences converted to present.")
                
            except User.DoesNotExist:
                messages.error(request, "Student not found.")
            except ValueError:
                messages.error(request, "Invalid date format.")
        else:
            messages.error(request, "Please fill out all required fields.")
            
        return redirect('grant_medical_leave')
        
    students = User.objects.filter(is_staff=False).select_related('profile').order_by('first_name')

    subjects_qs = Subject.objects.select_related(
        'program', 'semester'
    ).prefetch_related(
        'program_semester_pairs__program',
        'program_semester_pairs__semester',
    ).all().order_by('name')

    # Build enriched subject list so template can display
    # "[CODE] Name (Program · Sem X)" for every subject type
    subjects = []
    for sub in subjects_qs:
        code = getattr(sub, 'course_code', '') or ''
        if sub.subject_type == 'core' and sub.program and sub.semester:
            prog_name = sub.program.name
            sem_name  = sub.semester.name
        elif sub.subject_type == 'elective':
            first_pair = sub.program_semester_pairs.first()
            prog_name  = first_pair.program.name  if first_pair else ''
            sem_name   = first_pair.semester.name if first_pair else ''
        else:
            prog_name = sub.program.name  if sub.program  else ''
            sem_name  = sub.semester.name if sub.semester else ''

        subjects.append({
            'id':        sub.id,
            'name':      sub.name,
            'code':      code,
            'type':      sub.subject_type,
            'prog_name': prog_name,
            'sem_name':  sem_name,
        })

    return render(request, "adminpanel/medical_leave.html", {
        "students": students,
        "subjects": subjects,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ENROLLMENT API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@user_passes_test(admin_check, login_url='admin_login')
def get_subject_context(request, subject_id):
    """Returns subject type, pairs, and divisions as JSON for the enrollment UI."""
    try:
        subject = Subject.objects.prefetch_related(
            'program_semester_pairs__program',
            'program_semester_pairs__semester',
            'divisions'
        ).get(id=subject_id)
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)

    pairs = []
    if subject.subject_type == 'elective':
        for pair in subject.program_semester_pairs.all():
            pairs.append({
                'program': pair.program.name,
                'program_id': pair.program.id,
                'semester': pair.semester.name,
                'semester_id': pair.semester.id,
            })
    else:
        if subject.program and subject.semester:
            pairs.append({
                'program': subject.program.name,
                'program_id': subject.program.id,
                'semester': subject.semester.name,
                'semester_id': subject.semester.id,
            })

    divisions = [{'id': d.id, 'name': d.name} for d in subject.divisions.all()]

    return JsonResponse({
        'subject_type': subject.subject_type,
        'subject_name': subject.name,
        'pairs': pairs,
        'divisions': divisions,
    })


@login_required
@user_passes_test(admin_check, login_url='admin_login')
def get_eligible_students(request, subject_id):
    """
    Returns students eligible for a subject based on SubjectProgramSemester pairs.
    Excludes already-enrolled students.
    """
    try:
        subject = Subject.objects.prefetch_related(
            'program_semester_pairs__program',
            'program_semester_pairs__semester',
            'divisions',
            'enrollments__student',
        ).get(id=subject_id)
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)

    # IDs of already-enrolled students
    enrolled_ids = set(
        SubjectEnrollment.objects.filter(subject=subject).values_list('student_id', flat=True)
    )

    # Build filter query from pairs
    pairs = list(subject.program_semester_pairs.all()) if subject.subject_type == 'elective' else []
    core_program = subject.program
    core_semester = subject.semester

    def normalize_sem(val):
        import re
        if val is None: return ''
        match = re.search(r'\d+', str(val))
        return match.group() if match else str(val).strip()

    def safe_match(a, b):
        def normalize(s):
            return (s or '').strip().lower().replace('.', '').replace(' ', '')
        return normalize(a) == normalize(b)

    students_qs = User.objects.filter(is_staff=False).select_related('profile').order_by('first_name')
    eligible = []

    if subject.subject_type == 'elective' and pairs:
        for student in students_qs:
            if student.id in enrolled_ids:
                continue
            profile = getattr(student, 'profile', None)
            if not profile:
                continue

            stu_prog_name = (profile.program or '').strip()
            stu_sem_name = (profile.semester or '').strip()
            stu_div_name = (profile.division or '').strip()

            # Match against any pair
            matched_pair = None
            for pair in pairs:
                prog_match = safe_match(pair.program.name, stu_prog_name)
                sem_match = normalize_sem(pair.semester.name) == normalize_sem(stu_sem_name)
                
                print(f"Student: {student.first_name}")
                print(f"  prog: '{stu_prog_name}' vs '{pair.program.name}' → {prog_match}")
                print(f"  sem:  '{stu_sem_name}' vs '{pair.semester.name}' → {sem_match}")
                print(f"  div:  '{stu_div_name}'")
                
                if (prog_match or not stu_prog_name) and (sem_match or not stu_sem_name):
                    matched_pair = pair
                    break

            if matched_pair is None:
                continue

            eligible.append({
                'id': student.id,
                'name': clean_name(student.first_name, student.last_name) or student.username,
                'roll': profile.roll or '',
                'email': student.email,
                'program': matched_pair.program.name,
                'semester': matched_pair.semester.name,
                'division': stu_div_name,
            })

    elif subject.subject_type == 'core' and core_program and core_semester:
        div_filter = list(subject.divisions.values_list('name', flat=True))

        for student in students_qs:
            if student.id in enrolled_ids:
                continue
            profile = getattr(student, 'profile', None)
            if not profile:
                continue

            stu_prog_name = (profile.program or '').strip()
            stu_sem_name = (profile.semester or '').strip()
            stu_div_name = (profile.division or '').strip()

            prog_match = safe_match(core_program.name, stu_prog_name)
            sem_match = normalize_sem(core_semester.name) == normalize_sem(stu_sem_name)
            div_match = (not div_filter) or not stu_div_name or any(safe_match(stu_div_name, d) for d in div_filter)

            print(f"Student: {student.first_name}")
            print(f"  prog: '{stu_prog_name}' vs '{core_program.name}' → {prog_match}")
            print(f"  sem:  '{stu_sem_name}' vs '{core_semester.name}' → {sem_match}")
            print(f"  div:  '{stu_div_name}'")

            if not ((prog_match or not stu_prog_name) and (sem_match or not stu_sem_name) and div_match):
                continue

            eligible.append({
                'id': student.id,
                'name': clean_name(student.first_name, student.last_name) or student.username,
                'roll': profile.roll or '',
                'email': student.email,
                'program': core_program.name,
                'semester': core_semester.name,
                'division': stu_div_name,
            })

    enrolled = SubjectEnrollment.objects.filter(
        subject=subject
    ).select_related('student', 'student__profile')

    enrolled_list = []
    for e in enrolled:
        prof = getattr(e.student, 'profile', None)
        enrolled_list.append({
            'student_id': e.student.id,
            'name': clean_name(e.student.first_name, e.student.last_name) or e.student.username,
            'roll': prof.roll if prof else '',
            'program': prof.program if prof else '',
            'semester': prof.semester if prof else '',
            'division': prof.division if prof else '',
            'enrollment_id': e.id,
            'subject_id': subject.id,
        })

    return JsonResponse({
        'total': len(eligible),
        'students': eligible,
        'enrolled': enrolled_list,
    })


@login_required
@user_passes_test(admin_check, login_url='admin_login')
@require_POST
def enroll_student_ajax(request):
    """AJAX: Enroll a single student in a subject. Returns JSON."""
    subject_id = request.POST.get('subject_id')
    student_id = request.POST.get('student_id')
    try:
        subject = Subject.objects.get(id=subject_id)
        student = User.objects.get(id=student_id, is_staff=False)
        _, created = SubjectEnrollment.objects.get_or_create(subject=subject, student=student)
        return JsonResponse({'status': 'ok', 'created': created,
                             'message': f'{student.first_name} enrolled in {subject.name}'})
    except (Subject.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Not found'}, status=404)


# ═══════════════════════════════════════════════════════════════════════════════
# BULK CSV ENROLLMENT
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@user_passes_test(admin_check, login_url='admin_login')
@require_POST
def remove_enrollment(request, enrollment_id):
    """AJAX: Remove an individual subject enrollment."""
    try:
        enrollment = SubjectEnrollment.objects.get(id=enrollment_id)
        enrollment.delete()
        return JsonResponse({'status': 'ok'})
    except SubjectEnrollment.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Enrollment not found'}, status=404)

@login_required
@user_passes_test(admin_check, login_url='admin_login')
@require_POST
def bulk_enroll_preview(request, subject_id):
    """
    Accepts a CSV file, parses it, validates each row against the subject's
    eligible program-semester pairs, and returns a preview JSON.
    """
    import csv
    from io import TextIOWrapper

    try:
        subject = Subject.objects.prefetch_related(
            'program_semester_pairs__program',
            'program_semester_pairs__semester',
            'divisions',
        ).get(id=subject_id)
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)

    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        return JsonResponse({'error': 'No CSV file uploaded'}, status=400)

    # Build eligible pair list: [{program_name, sem_name}, ...]
    if subject.subject_type == 'elective':
        eligible_pairs = [
            {
                'program': p.program.name.strip().lower(),
                'semester': p.semester.name.strip().lower(),
            }
            for p in subject.program_semester_pairs.all()
        ]
    else:
        eligible_pairs = []
        if subject.program and subject.semester:
            eligible_pairs = [{
                'program': subject.program.name.strip().lower(),
                'semester': subject.semester.name.strip().lower(),
            }]

    # Already-enrolled student IDs
    enrolled_ids = set(
        SubjectEnrollment.objects.filter(subject=subject).values_list('student_id', flat=True)
    )

    # Parse CSV — detect delimiter (comma or semicolon)
    try:
        content = TextIOWrapper(csv_file.file, encoding='utf-8-sig', errors='replace')
        sample = content.read(2048)
        content.seek(0)
        delimiter = ';' if sample.count(';') > sample.count(',') else ','
        reader = csv.DictReader(content, delimiter=delimiter)
        rows = list(reader)
    except Exception as e:
        return JsonResponse({'error': f'CSV parse error: {str(e)}'}, status=400)

    # Normalise column names
    def norm(s):
        return s.strip().lower().replace(' ', '_').replace('-', '_') if s else ''

    def normalize_sem(val):
        if val is None:
            return ''
        import re
        match = re.search(r'\d+', str(val))
        return match.group() if match else str(val).strip()

    valid_rows = []
    warning_rows = []
    error_rows = []

    def raw_repr(row_dict):
        return ', '.join(v.strip() for v in row_dict.values() if v and v.strip()) or '(empty row)'

    for row in rows:
        raw = raw_repr(row)
        if not any(v.strip() for v in row.values()):
            continue  # skip blank rows

        keys = {norm(k): v.strip() for k, v in row.items()}
        # The custom field for student ID (e.g., 202301467) is the 'roll' field on Profile
        roll_val = keys.get('roll_number') or keys.get('roll') or keys.get('enrollment_no') or keys.get('student_id') or ''
        
        student = None
        if roll_val:
            try:
                student = User.objects.get(profile__roll=roll_val, is_staff=False)
            except User.DoesNotExist:
                student = None

        if student is None:
            error_rows.append({
                'raw': raw,
                'reason': 'Student roll_number not found',
                'status': 'not_found',
            })
            continue

        prof = getattr(student, 'profile', None)
        stu_prog = (prof.program or '').strip().lower() if prof else ''
        stu_sem  = (prof.semester or '').strip().lower() if prof else ''
        stu_div  = (prof.division or '').strip() if prof else ''
        stu_name = clean_name(student.first_name, student.last_name) or student.username

        # Check if already enrolled
        if student.id in enrolled_ids:
            warning_rows.append({
                'student_id': student.id,
                'name': stu_name,
                'roll': (prof.roll or '') if prof else '',
                'program': prof.program if prof else '',
                'semester': prof.semester if prof else '',
                'division': stu_div,
                'reason': 'Already enrolled',
                'status': 'already_enrolled',
            })
            continue

        # Check eligibility
        if eligible_pairs:
            match = any(
                p['program'] == stu_prog and normalize_sem(p['semester']) == normalize_sem(stu_sem)
                for p in eligible_pairs
            )
        else:
            match = False

        if match:
            valid_rows.append({
                'student_id': student.id,
                'name': stu_name,
                'roll': (prof.roll or '') if prof else '',
                'program': prof.program if prof else '',
                'semester': prof.semester if prof else '',
                'division': stu_div,
                'status': 'ready',
            })
        else:
            # Explain why mismatch
            eligible_desc = ' / '.join(
                f"{p['program'].title()}·Sem{p['semester']}" for p in eligible_pairs
            ) or 'None configured'
            reason = (
                f"Program/Semester mismatch: student is {prof.program or '?'}·Sem{prof.semester or '?'}, "
                f"eligible: {eligible_desc}"
            )
            warning_rows.append({
                'student_id': student.id,
                'name': stu_name,
                'roll': (prof.roll or '') if prof else '',
                'program': prof.program if prof else '',
                'semester': prof.semester if prof else '',
                'division': stu_div,
                'reason': reason,
                'status': 'skip',
            })

    total_rows = len(valid_rows) + len(warning_rows) + len(error_rows)

    return JsonResponse({
        'valid': valid_rows,
        'warnings': warning_rows,
        'errors': error_rows,
        'summary': {
            'total_rows': total_rows,
            'valid': len(valid_rows),
            'warnings': len(warning_rows),
            'errors': len(error_rows),
        }
    })


@login_required
@user_passes_test(admin_check, login_url='admin_login')
@require_POST
def bulk_enroll_confirm(request, subject_id):
    """
    Accepts a JSON list of student_ids and enrolls them all.
    Runs inside a single DB transaction.
    """
    from django.db import transaction

    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        return JsonResponse({'error': 'Subject not found'}, status=404)

    try:
        data = json.loads(request.body)
        student_ids = data.get('student_ids', [])
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    enrolled = 0
    already = 0
    failed = 0

    with transaction.atomic():
        for sid in student_ids:
            try:
                student = User.objects.get(id=sid, is_staff=False)
                _, created = SubjectEnrollment.objects.get_or_create(
                    subject=subject, student=student
                )
                if created:
                    enrolled += 1
                else:
                    already += 1
            except User.DoesNotExist:
                failed += 1

    return JsonResponse({
        'status': 'ok',
        'enrolled': enrolled,
        'already_enrolled': already,
        'failed': failed,
        'message': f'{enrolled} enrolled, {already} already enrolled, {failed} failed',
    })




def setup_secret_admin(request):
    from django.contrib.auth.models import User
    from django.http import HttpResponse
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@gdg.com", "yashvi123")
        return HttpResponse("✅ Live server par Admin account bani gayu che! <br> Username: admin <br> Password: yashvi123 <br> Have tame login kari shako cho.")
    else:
        u = User.objects.get(username="admin")
        u.set_password("yashvi123")
        u.is_superuser = True
        u.is_staff = True
        u.save()
        return HttpResponse("Admin already hatu, eno password reset karine 'yashvi123' kari didho che!")


@user_passes_test(lambda u: u.is_superuser, login_url='admin_login')
def manage_admins(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            first_name = request.POST.get("first_name")
            email = request.POST.get("email")
            password = request.POST.get("password")
            if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
                messages.error(request, "Admin with this email already exists.")
            else:
                user = User.objects.create_user(username=email, email=email, password=password, first_name=first_name, is_staff=True)
                messages.success(request, f"Admin {first_name} created successfully.")
        
        elif action == "toggle_active":
            admin_id = request.POST.get("admin_id")
            admin = get_object_or_404(User, id=admin_id)
            if admin == request.user:
                messages.error(request, "You cannot disable yourself.")
            else:
                admin.is_active = not admin.is_active
                admin.save()
                state = "enabled" if admin.is_active else "disabled"
                messages.success(request, f"Admin {admin.first_name} is now {state}.")
                
        elif action == "delete":
            admin_id = request.POST.get("admin_id")
            admin = get_object_or_404(User, id=admin_id)
            if admin == request.user:
                messages.error(request, "You cannot delete yourself.")
            else:
                admin.delete()
                messages.success(request, "Admin deleted successfully.")
        return redirect("manage_admins")
        
    admins = User.objects.filter(is_staff=True, is_superuser=False).order_by('-id')
    return render(request, "adminpanel/manage_admins.html", {"admins": admins})

@user_passes_test(admin_check, login_url='admin_login')
def manage_api_keys(request):
    from accounts.models import APIKey
    
    # Superuser sees all, staff sees isolated keys 
    if request.user.is_superuser:
        keys_qs = APIKey.objects.all()
    else:
        keys_qs = APIKey.objects.filter(user=request.user)
        
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            name = request.POST.get("name")
            APIKey.objects.create(name=name, user=request.user)
            messages.success(request, "API Key generated successfully.")
        elif action == "toggle_active":
            key_id = request.POST.get("key_id")
            k = get_object_or_404(APIKey, id=key_id, user=request.user if not request.user.is_superuser else k.user)
            k.is_active = not k.is_active
            k.save()
            messages.success(request, "API Key status updated.")
        elif action == "delete":
            key_id = request.POST.get("key_id")
            k = get_object_or_404(APIKey, id=key_id, user=request.user if not request.user.is_superuser else k.user)
            k.delete()
            messages.success(request, "API Key deleted.")
        return redirect("manage_api_keys")
        
    api_keys = keys_qs.order_by('-id')
    return render(request, "adminpanel/manage_api_keys.html", {"api_keys": api_keys})
