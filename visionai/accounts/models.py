from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


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

    subject = models.CharField(max_length=100)   # 🔥 NEW
    lecture_slot = models.IntegerField()         # 🔥 NEW

    image = models.ImageField(upload_to="attendance/", null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - Slot {self.lecture_slot} - {self.date.strftime('%d-%m-%Y')}"

class Attendance(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)  # True = Present, False = Absent
    time_marked = models.TimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.first_name} - {self.session.date.date()}"


# class Attendance(models.Model):
#     session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE)
#     student = models.ForeignKey(User, on_delete=models.CASCADE)
#     status = models.BooleanField(default=True)  # Present / Absent
#     time_marked = models.TimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('session', 'student')

#     def __str__(self):
#         return f"{self.student.first_name} - {self.session.date.date()}"



class Session(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# accounts/models.py
# accounts/models.py
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    roll = models.CharField(max_length=20)
    
    # Faculty field ne optional rakho (karan ke tame HTML mathi kadhi nakhyu che)
    faculty = models.CharField(max_length=100, blank=True, null=True)
    
    # Department field database ma 'department' rahese pan tya 'ICT/MnC' save thase
    department = models.CharField(max_length=100, blank=True, null=True)
    
    program = models.CharField(max_length=50)
    semester = models.CharField(max_length=50)
    division = models.CharField(max_length=10)
    image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.user.username



class Faculty(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class Program(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Semester(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Division(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class Subject(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    division = models.ForeignKey(Division, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class Lecture(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    slot = models.IntegerField()  # 1 to 6

    def __str__(self):
        return f"{self.subject.name} - {self.date} Slot {self.slot}"