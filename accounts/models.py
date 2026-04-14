from django.db import models
from django.contrib.auth.models import User
import numpy as np


class Faculty(models.Model):
    name = models.CharField(max_length=100)
    faculty_code = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        help_text="Short code e.g. AT, TKM, BK"
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_facultys')

    def __str__(self):
        if self.faculty_code:
            return f"[{self.faculty_code}] {self.name}"
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_departments')

    def __str__(self):
        return self.name


class Program(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_programs')

    def __str__(self):
        return self.name


class Semester(models.Model):
    name = models.CharField(max_length=20)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_semesters')

    def __str__(self):
        return self.name


class Division(models.Model):
    name = models.CharField(max_length=10)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_divisions')

    def __str__(self):
        return self.name


# ✅ Subject (Handles both Core and Elective Types)
class Subject(models.Model):
    SUBJECT_TYPES = (
        ('core', 'Core'),
        ('elective', 'Elective'),
    )
    name = models.CharField(max_length=100)
    course_code = models.CharField(
        max_length=20, unique=True, null=True, blank=True,
        help_text="Course code e.g. HM227, CS301"
    )
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPES, default='core')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_subjects')

    # Core subject: single program (FK). Elective: null here, use programs M2M below
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True, blank=True)

    # Semester fixed for Core subjects, null for Electives
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True, blank=True)

    # Pivot relations
    divisions = models.ManyToManyField(Division, blank=True, related_name='core_subjects')
    semesters = models.ManyToManyField(Semester, blank=True, related_name='elective_subjects')

    # Elective subject: multiple programs (BTech + MTech etc.)
    programs = models.ManyToManyField(Program, blank=True, related_name='elective_subjects')

    def __str__(self):
        return f"{self.name} ({self.get_subject_type_display()})"


class SubjectProgramSemester(models.Model):
    """
    For Elective subjects: links one subject to one (Program, Semester) pair.
    Example: Robotics → BTech, Sem 6
             Robotics → MTech, Sem 4
    This replaces the old M2M programs/semesters fields for electives.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='program_semester_pairs')
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('subject', 'program', 'semester')
        ordering = ['program__name', 'semester__name']

    def __str__(self):
        return f"{self.subject.name} → {self.program.name} / Sem {self.semester.name}"


# ✅ SubjectEnrollment — Subject ma kaya students enrolled che ae track kare
class SubjectEnrollment(models.Model):
    """
    Links students to the subjects they are actually enrolled in.
    Only admin/professor can manage enrollments.
    Attendance ane email ONLY enrolled students ne j lage/jaye.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subject_enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subject', 'student')
        ordering = ['subject', 'student__first_name']

    def __str__(self):
        return f"{self.student.first_name} → {self.subject.name}"


# ✅ Lecture ek j vaar define karyu — duplicate remove karyu
class Lecture(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    slot = models.IntegerField()  # 1 to 6

    def __str__(self):
        return f"{self.subject.name} - {self.date} Slot {self.slot}"


class AttendanceSession(models.Model):
    faculty = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    program = models.CharField(max_length=100)
    semester = models.CharField(max_length=50)
    division = models.CharField(max_length=50)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    lecture_slot = models.IntegerField()
    image = models.ImageField(upload_to="attendance/", null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - Slot {self.lecture_slot} - {self.date.strftime('%d-%m-%Y')}"


class Attendance(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)  # True = Present, False = Absent
    time_marked = models.TimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_attendances')

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.first_name} - {self.session.date.date()}"


class Session(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_profiles')
    mobile = models.CharField(max_length=15, blank=True, null=True)
    roll = models.CharField(max_length=20, blank=True, null=True)
    faculty = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    program = models.CharField(max_length=50, blank=True, null=True)
    semester = models.CharField(max_length=50, blank=True, null=True)
    division = models.CharField(max_length=10, blank=True, null=True)
    image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    # Pre-computed face encoding stored as binary (pickle of numpy array)
    face_encoding = models.BinaryField(blank=True, null=True)
    encoding_updated_at = models.DateTimeField(blank=True, null=True)

    def get_face_encoding(self):
        """
        Return 512-d float32 numpy array from stored bytes (InsightFace format).
        Falls back to None for any legacy pickle-serialised data (pre-migration).
        """
        if self.face_encoding:
            raw = bytes(self.face_encoding)
            try:
                # InsightFace: raw float32 bytes, always 512 * 4 = 2048 bytes
                if len(raw) == 512 * 4:
                    return np.frombuffer(raw, dtype=np.float32).copy()
                # Legacy pickle — cannot use, force re-encoding
                return None
            except Exception:
                return None
        return None

    def set_face_encoding(self, encoding_array: np.ndarray):
        """Store InsightFace 512-d float32 embedding as raw bytes."""
        arr = encoding_array.astype(np.float32)
        self.face_encoding = arr.tobytes()

    def __str__(self):
        return self.user.username


class LiveAttendanceSession(models.Model):
    """A teacher-created live session that students scan into in real time."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    faculty = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    program = models.CharField(max_length=100)
    semester = models.CharField(max_length=50)
    division = models.CharField(max_length=50)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    lecture_slot = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='live_sessions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    # Secret kiosk token — makes the kiosk URL unguessable
    kiosk_token = models.CharField(max_length=64, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.kiosk_token:
            import uuid
            self.kiosk_token = uuid.uuid4().hex  # 32 char hex string
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject} - Slot {self.lecture_slot} - {self.created_at.strftime('%d-%m-%Y %H:%M')} [{self.status}]"


class LiveAttendanceRecord(models.Model):
    """Individual scan record within a live session."""
    live_session = models.ForeignKey(LiveAttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    scanned_at = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(default=0.0)  # lower = better match

    class Meta:
        unique_together = ('live_session', 'student')

    def __str__(self):
        return f"{self.student.first_name} @ {self.live_session}"


class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100, default="Default Key")
    key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.key:
            import secrets
            self.key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.user.username}"