from fileinput import filename
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from .models import AttendanceSession, Attendance, Profile

import os
import cv2
import numpy as np
import face_recognition

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User


from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from .models import AttendanceSession, Attendance
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import openpyxl
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Q
import calendar
from datetime import date
from .models import Division, Semester, Program, Department, Faculty , Subject
import cv2
import tempfile
import numpy as np
import re

from django.core.mail import send_mail
from django.conf import settings

import urllib.request

def admin_check(user):
    return user.is_staff    

from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_login(request):       
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        users = User.objects.filter(email=email, is_staff=True)

        for user in users:
            if user.check_password(password):
                login(request, user)
                request.session['admin_id'] = user.id
                return redirect("admin_dashboard")

        messages.error(request, "Invalid admin credentials")

    return render(request, "adminpanel/admin_login.html")



@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_profile(request):
    return render(request, "adminpanel/admin_profile.html")



@login_required
def admin_profile(request):
    user = request.user

    # ✅ SAFE — auto create profile if missing
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
    # session.flush() ni jarur nathi, logout() pote j badhu clean kari nakhe che
    return redirect('admin_login')


@login_required
def student_attendance(request):
    user = request.user
    today = date.today()

    # All sessions for this month
    sessions = AttendanceSession.objects.filter(date__month=today.month)

    # Attendance records of this student
    attendance = Attendance.objects.filter(student=user, session__in=sessions)

    # Map session id → status
    attendance_map = {
        att.session.id: att.status for att in attendance
    }

    # Group sessions by date
    lecture_data = {}
    for s in sessions:
        lecture_data.setdefault(s.date, {})[s.slot] = s

    # Subject-wise stats
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


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def mark_attendance(request):

    detected_students = []

    if request.method == "POST" and request.FILES.getlist("media"):

        # 🔥 Load encodings once
        load_student_encodings()

        faculty = request.POST.get("faculty")
        department = request.POST.get("department")
        program = request.POST.get("program")
        semester = request.POST.get("semester")
        division = request.POST.get("division")
        subject_id = request.POST.get("subject")
        slot = request.POST.get("slot")

        subject = Subject.objects.get(id=subject_id)

        session = AttendanceSession.objects.create(
            faculty=faculty,
            department=department,
            program=program,
            semester=semester,
            division=division,
            subject=subject,
            lecture_slot=slot
        )

        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, "attendance"))

        matched_users_total = set()
        files = request.FILES.getlist('media')

        for file in files:
            filename = fs.save(file.name, file)
            file_path = os.path.join(settings.MEDIA_ROOT, "attendance", filename)

            print("Processing file:", file_path)

            # 📸 IMAGE
            if file.content_type.startswith("image"):
                users = recognize_faces_from_image(file_path)

            # 🎥 VIDEO
            elif file.content_type.startswith("video"):
                users = recognize_faces_from_video(file_path)

            else:
                users = []

            for user in users:
                matched_users_total.add(user)

        # ✅ PRESENT SAVE
        for user in matched_users_total:
            Attendance.objects.create(
                session=session,
                student=user,
                status=True
            )

        # ❌ ABSENT SAVE + EMAIL
        all_students = User.objects.filter(is_staff=False)

        for student in all_students:
            if student not in matched_users_total:

                Attendance.objects.create(
                    session=session,
                    student=student,
                    status=False
                )

                # 📧 Send email to absent student
                if student.email:
                    try:
                        send_mail(
                            subject="Absent Alert – Vision AI",
                            message=f"""
Dear {student.first_name},

You were marked ABSENT today.

📚 Subject: {subject.name}
🕒 Lecture Slot: {slot}
📅 Date: {session.date}

Please attend next lecture.

– Vision AI Attendance System
""",
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[student.email],
                            fail_silently=False,
                        )

                        print("Email sent to:", student.email)

                    except Exception as e:
                        print("Email error:", e)

        detected_students = list(matched_users_total)

        print("Detected students:", len(detected_students))

    return render(request, "adminpanel/attendance.html", {
        "detected_students": detected_students,
        "faculties": Faculty.objects.all(),
        "departments": Department.objects.all(),
        "programs": Program.objects.all(),
        "semesters": Semester.objects.all(),
        "divisions": Division.objects.all(),
        "subjects": Subject.objects.all(),
    })

STUDENT_ENCODINGS = []
STUDENT_USERS = []


def load_student_encodings():
    STUDENT_ENCODINGS.clear()
    STUDENT_USERS.clear()

    students = User.objects.filter(is_staff=False)

    for user in students:
        try:
            if not user.profile.image:
                continue

            # 🔥 Cloudinary URL Support (ઓનલાઈન ફોટો વાંચવા માટે) 🔥
            image_url = user.profile.image.url
            
            if image_url.startswith('http'):
                req = urllib.request.urlopen(image_url)
                img_array = np.asarray(bytearray(req.read()), dtype=np.uint8)
                img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            else:
                img_path = user.profile.image.path
                if not os.path.exists(img_path):
                    continue
                img = face_recognition.load_image_file(img_path)

            encodings = face_recognition.face_encodings(img)

            if encodings:
                STUDENT_ENCODINGS.append(encodings[0])
                STUDENT_USERS.append(user)

        except Exception as e:
            print(f"Encoding load error for {user.username}:", e)

    print("Students loaded:", len(STUDENT_ENCODINGS))

def match_faces(frame_encodings):
    matched_users = []

    if not STUDENT_ENCODINGS:
        return matched_users

    for face_encoding in frame_encodings:
        distances = face_recognition.face_distance(STUDENT_ENCODINGS, face_encoding)
        
        best_index = np.argmin(distances)
        best_distance = distances[best_index]

        # 🔥 કડકાઈ ઓછી કરી (0.45 થી 0.55 કર્યું, જેથી ક્લાસરૂમના ફોટા પણ ઓળખી લે) 🔥
        if best_distance > 0.55:
            continue

        matches = face_recognition.compare_faces(
            STUDENT_ENCODINGS,
            face_encoding,
            tolerance=0.55
        )

        if matches[best_index]:
            matched_users.append(STUDENT_USERS[best_index])

    return matched_users
def recognize_faces_from_video(video_path):
    detected_users = set()
    frame_user_counts = {}

    video = cv2.VideoCapture(video_path)

    if not video.isOpened():
        print("❌ Cannot open video:", video_path)
        return detected_users

    frame_count = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break

        try:
            small_frame = cv2.resize(frame, (0, 0), fx=0.6, fy=0.6)
            rgb_frame = small_frame[:, :, ::-1]
            rgb_frame = np.ascontiguousarray(rgb_frame)

            # 🔥 every 5th frame process (more chances)
            if frame_count % 5 == 0:

                face_locations = face_recognition.face_locations(rgb_frame)
                encodings = face_recognition.face_encodings(
                    rgb_frame,
                    face_locations
                )

                print("Frame", frame_count, "faces:", len(encodings))

                if encodings:
                    users = match_faces(encodings)

                    for user in users:
                        frame_user_counts[user] = frame_user_counts.get(user, 0) + 1

                        # 🔥 2 frame confirmation (classroom friendly)
                        if frame_user_counts[user] >= 2:
                            detected_users.add(user)

        except Exception as e:
            print("⚠ Frame error:", e)

        frame_count += 1

    video.release()

    print("Frame confirmation counts:", frame_user_counts)

    return detected_users

def recognize_faces_from_image(image_path):
    img = face_recognition.load_image_file(image_path)

    face_locations = face_recognition.face_locations(img)
    encodings = face_recognition.face_encodings(img, face_locations)

    print("Image faces:", len(encodings))

    return match_faces(encodings)

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def attendance_history(request):
    sessions = AttendanceSession.objects.all().order_by('-id')
    return render(request, "adminpanel/attendance_history.html", {"sessions": sessions})

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def download_attendance(request, session_id):
    session = AttendanceSession.objects.get(id=session_id)

    records = Attendance.objects.filter(
        session=session
    ).select_related('student', 'student__profile')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Report"

    # ✅ HEADER ROW (Subject added)
    ws.append([
        "Date",
        "Faculty",
        "Department",
        "Program",
        "Semester",
        "Division",
        "Subject",
        "Student Name",
        "Email",
        "Mobile",
        "Roll",
        "Status"
    ])

    for r in records:
        p = r.student.profile

        ws.append([
            str(session.date),
            session.faculty,
            session.department,
            session.program,
            session.semester,
            session.division,

            session.subject if session.subject else "",  # ✅ FIX

            r.student.first_name,
            r.student.email,
            p.mobile if p.mobile else "",
            p.roll if p.roll else "",
            "Present" if r.status else "Absent"
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="attendance_report.xlsx"'

    wb.save(response)
    return response



@user_passes_test(admin_check, login_url='admin_login')
@login_required
def admin_dashboard(request, user_id=None):
    

    users = User.objects.filter(is_staff=False).select_related('profile')
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
            "name": name,
            "email": email,
            "mobile": mobile,
            "roll": roll,
            "faculty": faculty,
            "department": department,
            "program": program,
            "semester": semester,
            "division": division,
        }

        # ❌ Required fields
        if not all([name, email, mobile]):
            messages.error(request, "Name, Email and Mobile are required")
            return render(request, "adminpanel/dashboard.html", {
                "users": users,
                "edit_user": edit_user,
                "profile": profile,
                "form_data": form_data
            })

        # ❌ Mobile digits
        if not mobile.isdigit():
            messages.error(request, "Mobile must contain only digits")
            return render(request, "adminpanel/dashboard.html", {
                "users": users,
                "edit_user": edit_user,
                "profile": profile,
                "form_data": form_data
            })

        # ❌ Mobile length
        if len(mobile) != 10:
            messages.error(request, "Mobile number must be exactly 10 digits")
            return render(request, "adminpanel/dashboard.html", {
                "users": users,
                "edit_user": edit_user,
                "profile": profile,
                "form_data": form_data
            })

        # ================= ADD USER =================
        if not user_id:
            if User.objects.filter(username=email).exists():
                messages.error(request, "User with this email already exists")
                return render(request, "adminpanel/dashboard.html", {
                    "users": users,
                    "edit_user": edit_user,
                    "profile": profile,
                    "form_data": form_data
                })

            user = User.objects.create_user(
                username=email,
                email=email,
                password="123456",
                first_name=name
            )

            Profile.objects.create(
                user=user,
                mobile=mobile,
                roll=roll,
                faculty=faculty,
                department=department,
                program=program,
                semester=semester,
                division=division,
                image=image
            )

            messages.success(request, "User added successfully")
            return redirect("admin_dashboard")

        # ================= UPDATE USER =================
        else:
            if User.objects.filter(username=email).exclude(id=edit_user.id).exists():
                messages.error(request, "Another user with this email already exists")
                return render(request, "adminpanel/dashboard.html", {
                    "users": users,
                    "edit_user": edit_user,
                    "profile": profile,
                    "form_data": form_data
                })

            edit_user.first_name = name
            edit_user.email = email
            edit_user.username = email
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

            messages.success(request, "User updated successfully")
            return redirect("admin_dashboard")

    return render(request, "adminpanel/dashboard.html", {
        "users": users,
        "edit_user": edit_user,
        "profile": profile
    })

    return render(request, "adminpanel/dashboard.html", {
        "users": users,
        "edit_user": edit_user,
        "profile": profile
    })


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

        if "image" in request.FILES:
            profile.image = request.FILES["image"]

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
def attendance(request):
    return render(request, "adminpanel/attendance.html")


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def faculties(request):
    return render(request, "adminpanel/faculties.html")
@user_passes_test(admin_check, login_url='admin_login')
@login_required
def departments(request):
    return render(request, "adminpanel/departments.html")

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def programs(request):
    return render(request, "adminpanel/programs.html")

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def semesters(request):
    return render(request, "adminpanel/semesters.html")
@user_passes_test(admin_check, login_url='admin_login')
@login_required
def divisions(request):
    return render(request, "adminpanel/divisions.html")


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

        # 🔴 REQUIRED FIELDS
        if not all([name, email, mobile, password, cpassword]):
            messages.error(request, "All fields are required")
            return render(request, "register.html", context)

        # 🔴 MOBILE VALIDATION
        if not mobile.isdigit() or len(mobile) != 10:
            messages.error(request, "Mobile number must be exactly 10 digits")
            return render(request, "register.html", context)

        # 🔴 PASSWORD MATCH
        if password != cpassword:
            messages.error(request, "Password and Confirm Password must be same")
            return render(request, "register.html", context)

        # 🔴 EMAIL UNIQUE
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered")
            return render(request, "register.html", context)

        # ✅ CREATE USER
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )

        Profile.objects.create(user=user, mobile=mobile)

        messages.success(request, "Registration successful. Please login.")
        return redirect('login')

    return render(request, "register.html")



def login_user(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('pass')

        user = authenticate(request, username=email, password=password)

        if user and not user.is_staff:
            login(request, user)   # Django session for normal user
            return redirect("profile")
        else:
            messages.error(request, "Invalid user credentials")

    return render(request, "login.html")


    return render(request, "login.html")
@login_required
def profile(request):
    # 🔒 Admin ne user profile ma aavta rokva
    if request.user.is_staff:
        return redirect('admin_dashboard')

    profile = Profile.objects.filter(user=request.user).first()

    if request.method == "POST":
        if profile is None:
            profile = Profile.objects.create(user=request.user)

        mobile = request.POST.get("mobile", "").strip()

        # 🔴 Mobile Validation
        if mobile and not re.fullmatch(r"\d{10}", mobile):
            messages.error(request, "Mobile number must be exactly 10 digits")
            return redirect("profile")

        # ✅ Save Data
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




@user_passes_test(admin_check, login_url='admin_login')
@login_required
def faculties(request):
    if request.method == "POST":
        faculty_name = request.POST.get("faculty_name")
        if faculty_name:
            Faculty.objects.create(name=faculty_name)
        return redirect('faculties')

    faculties = Faculty.objects.all().order_by('id')
    return render(request, 'adminpanel/faculties.html', {'faculties': faculties})

def delete_faculty(request, id):
    faculty = get_object_or_404(Faculty, id=id)
    faculty.delete()
    return redirect('faculties')


def edit_faculty(request, id):
    faculty = get_object_or_404(Faculty, id=id)

    if request.method == "POST":
        faculty_name = request.POST.get("faculty_name")
        if faculty_name:
            faculty.name = faculty_name   # ✔ same id update
            faculty.save()
        return redirect('faculties')

    faculties = Faculty.objects.all().order_by('id')
    return render(request, 'adminpanel/faculties.html', {
        'faculties': faculties,
        'edit_faculty': faculty
    })



@user_passes_test(admin_check, login_url='admin_login')
@login_required
def departments(request):
    faculties = Faculty.objects.all()

    # 🔴 ADD Department
    if request.method == "POST" and not request.POST.get("dept_id"):
        dept_name = request.POST.get("department_name")
        faculty_id = request.POST.get("faculty")

        if dept_name and faculty_id:
            Department.objects.create(
                name=dept_name,
                faculty_id=faculty_id
            )
        return redirect('departments')

    departments = Department.objects.select_related('faculty').all().order_by('id')

    return render(request, 'adminpanel/departments.html', {
        'departments': departments,
        'faculties': faculties
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_department(request, id):
    dept = get_object_or_404(Department, id=id)
    faculties = Faculty.objects.all()

    # 🔴 UPDATE Department
    if request.method == "POST":
        dept.name = request.POST.get("department_name")
        dept.faculty_id = request.POST.get("faculty")
        dept.save()
        return redirect('departments')

    departments = Department.objects.select_related('faculty').all().order_by('id')

    return render(request, 'adminpanel/departments.html', {
        'departments': departments,
        'faculties': faculties,
        'edit_department': dept
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_department(request, id):
    dept = get_object_or_404(Department, id=id)
    dept.delete()
    return redirect('departments')




@user_passes_test(admin_check, login_url='admin_login')
@login_required
def programs(request):
    faculties = Faculty.objects.all()
    departments = Department.objects.select_related('faculty').all()

    # 🔴 ADD
    if request.method == "POST" and not request.POST.get("program_id"):
        name = request.POST.get("program_name")
        faculty_id = request.POST.get("faculty")
        department_id = request.POST.get("department")

        if name and faculty_id and department_id:
            Program.objects.create(
                name=name,
                faculty_id=faculty_id,
                department_id=department_id
            )
        return redirect('programs')

    programs = Program.objects.select_related('faculty', 'department').all().order_by('id')

    return render(request, 'adminpanel/programs.html', {
        'programs': programs,
        'faculties': faculties,
        'departments': departments
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_program(request, id):
    prog = get_object_or_404(Program, id=id)
    faculties = Faculty.objects.all()
    departments = Department.objects.select_related('faculty').all()

    if request.method == "POST":
        prog.name = request.POST.get("program_name")
        prog.faculty_id = request.POST.get("faculty")
        prog.department_id = request.POST.get("department")
        prog.save()
        return redirect('programs')

    programs = Program.objects.select_related('faculty', 'department').all().order_by('id')

    return render(request, 'adminpanel/programs.html', {
        'programs': programs,
        'faculties': faculties,
        'departments': departments,
        'edit_program': prog
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_program(request, id):
    prog = get_object_or_404(Program, id=id)
    prog.delete()
    return redirect('programs')




@user_passes_test(admin_check, login_url='admin_login')
@login_required
def semesters(request):
    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    programs = Program.objects.all()

    # 🔴 ADD
    if request.method == "POST" and not request.POST.get("semester_id"):
        name = request.POST.get("semester_name")
        faculty_id = request.POST.get("faculty")
        department_id = request.POST.get("department")
        program_id = request.POST.get("program")

        if name and faculty_id and department_id and program_id:
            Semester.objects.create(
                name=name,
                faculty_id=faculty_id,
                department_id=department_id,
                program_id=program_id
            )
        return redirect('semesters')

    semesters = Semester.objects.select_related(
        'faculty', 'department', 'program'
    ).all().order_by('id')

    return render(request, 'adminpanel/semesters.html', {
        'semesters': semesters,
        'faculties': faculties,
        'departments': departments,
        'programs': programs
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_semester(request, id):
    sem = get_object_or_404(Semester, id=id)

    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    programs = Program.objects.all()

    if request.method == "POST":
        sem.name = request.POST.get("semester_name")
        sem.faculty_id = request.POST.get("faculty")
        sem.department_id = request.POST.get("department")
        sem.program_id = request.POST.get("program")
        sem.save()
        return redirect('semesters')

    semesters = Semester.objects.select_related(
        'faculty', 'department', 'program'
    ).all().order_by('id')

    return render(request, 'adminpanel/semesters.html', {
        'semesters': semesters,
        'faculties': faculties,
        'departments': departments,
        'programs': programs,
        'edit_semester': sem
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_semester(request, id):
    sem = get_object_or_404(Semester, id=id)
    sem.delete()
    return redirect('semesters')



@user_passes_test(admin_check, login_url='admin_login')
@login_required
def divisions(request):
    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    programs = Program.objects.all()
    semesters = Semester.objects.all()

    # 🔴 ADD
    if request.method == "POST" and not request.POST.get("division_id"):
        name = request.POST.get("division_name")
        faculty_id = request.POST.get("faculty")
        department_id = request.POST.get("department")
        program_id = request.POST.get("program")
        semester_id = request.POST.get("semester")

        if name and faculty_id and department_id and program_id and semester_id:
            Division.objects.create(
                name=name,
                faculty_id=faculty_id,
                department_id=department_id,
                program_id=program_id,
                semester_id=semester_id
            )
        return redirect('divisions')

    divisions = Division.objects.select_related(
        'faculty', 'department', 'program', 'semester'
    ).all().order_by('id')

    return render(request, 'adminpanel/divisions.html', {
        'divisions': divisions,
        'faculties': faculties,
        'departments': departments,
        'programs': programs,
        'semesters': semesters
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def edit_division(request, id):
    div = get_object_or_404(Division, id=id)

    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    programs = Program.objects.all()
    semesters = Semester.objects.all()

    if request.method == "POST":
        div.name = request.POST.get("division_name")
        div.faculty_id = request.POST.get("faculty")
        div.department_id = request.POST.get("department")
        div.program_id = request.POST.get("program")
        div.semester_id = request.POST.get("semester")
        div.save()
        return redirect('divisions')

    divisions = Division.objects.select_related(
        'faculty', 'department', 'program', 'semester'
    ).all().order_by('id')

    return render(request, 'adminpanel/divisions.html', {
        'divisions': divisions,
        'faculties': faculties,
        'departments': departments,
        'programs': programs,
        'semesters': semesters,
        'edit_division': div
    })


@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_division(request, id):
    div = get_object_or_404(Division, id=id)
    div.delete()
    return redirect('divisions')


from django.shortcuts import render
from .models import Attendance

from django.utils.dateparse import parse_date

def attendance_view(request):
    profile = request.user.profile
    selected_date = request.GET.get('date')

    attendance = Attendance.objects.filter(
        student=request.user
    ).select_related('session')

    # 📅 DATE FILTER
    if selected_date:
        attendance = attendance.filter(session__date__date=selected_date)

    attendance = attendance.order_by('-session__date')

    return render(request, 'attendance.html', {
        'attendance': attendance,
        'profile': profile,
        'selected_date': selected_date
    })



from django.db.models import Count
from collections import defaultdict

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Attendance
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Attendance, Profile

@login_required
def report_view(request):

    student = request.user   # 🔥 important (user nahi, student)

    profile = Profile.objects.get(user=request.user)

    # 🔹 Overall present/absent
    present_count = Attendance.objects.filter(student=student, status=True).count()
    absent_count = Attendance.objects.filter(student=student, status=False).count()

    # 🔹 Session wise %
    sessions = Attendance.objects.filter(student=student).values_list('session', flat=True).distinct()

    session_labels = []
    session_counts = []

    for s in sessions:
        total = Attendance.objects.filter(student=student, session=s).count()
        present = Attendance.objects.filter(student=student, session=s, status=True).count()

        percentage = round((present / total) * 100) if total > 0 else 0

        session_labels.append(str(s))
        session_counts.append(percentage)

    context = {
        'profile': profile,
        'present_count': present_count,
        'absent_count': absent_count,
        'subject_labels': session_labels,
        'subject_counts': session_counts,
    }

    return render(request, "report.html", context)

@user_passes_test(admin_check, login_url='admin_login')
@login_required
def subjects(request):

    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    programs = Program.objects.all()
    semesters = Semester.objects.all()
    divisions = Division.objects.all()

    # 🔴 ADD
    if request.method == "POST" and not request.POST.get("subject_id"):
        name = request.POST.get("subject_name")
        faculty_id = request.POST.get("faculty")
        department_id = request.POST.get("department")
        program_id = request.POST.get("program")
        semester_id = request.POST.get("semester")
        division_id = request.POST.get("division")

        if name and faculty_id and department_id and program_id and semester_id and division_id:
            Subject.objects.create(
                name=name,
                faculty_id=faculty_id,
                department_id=department_id,
                program_id=program_id,
                semester_id=semester_id,
                division_id=division_id
            )

        return redirect('subjects')

    subjects = Subject.objects.select_related(
        'faculty', 'department', 'program', 'semester', 'division'
    ).all().order_by('id')

    return render(request, 'adminpanel/subjects.html', {
        'subjects': subjects,
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

    faculties = Faculty.objects.all()
    departments = Department.objects.all()
    programs = Program.objects.all()
    semesters = Semester.objects.all()
    divisions = Division.objects.all()

    if request.method == "POST":
        subject.name = request.POST.get("subject_name")

        subject.faculty_id = request.POST.get("faculty")
        subject.department_id = request.POST.get("department")
        subject.program_id = request.POST.get("program")
        subject.semester_id = request.POST.get("semester")
        subject.division_id = request.POST.get("division")

        subject.save()
        return redirect('subjects')

    subjects = Subject.objects.all().order_by('id')

    return render(request, 'adminpanel/subjects.html', {
        'subjects': subjects,
        'edit_subject': subject,
        'faculties': faculties,
        'departments': departments,
        'programs': programs,
        'semesters': semesters,
        'divisions': divisions,
    })
@user_passes_test(admin_check, login_url='admin_login')
@login_required
def delete_subject(request, id):

    subject = get_object_or_404(Subject, id=id)
    subject.delete()
    return redirect('subjects')


def logout_user(request):
    # Logout karya pehla check kari lo ke user admin che ke nahi
    is_admin = request.user.is_staff 
    
    logout(request) # Have detail clear thai jase
    
    if is_admin:
        return redirect('admin_login')
    else:
        return redirect('login')