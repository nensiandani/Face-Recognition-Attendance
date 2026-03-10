from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_user, name='logout_user'),

    path('admin-profile/', views.admin_profile, name='admin_profile'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('my-attendance/', views.student_attendance, name='student_attendance'),

    # 🔥 CHANGE THIS
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),

    path('attendance-history/', views.attendance_history, name='attendance_history'),
    path('download-attendance/<int:session_id>/', views.download_attendance, name='download_attendance'),

    path('divisions/', views.divisions, name='divisions'),

    path('admin-dashboard/<int:user_id>/', views.admin_dashboard, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    path('faculties/', views.faculties, name='faculties'),
    path('delete-faculty/<int:id>/', views.delete_faculty, name='delete_faculty'),
    path('edit-faculty/<int:id>/', views.edit_faculty, name='edit_faculty'),

    path('departments/', views.departments, name='departments'),
    path('edit-department/<int:id>/', views.edit_department, name='edit_department'),
    path('delete-department/<int:id>/', views.delete_department, name='delete_department'),

    path('programs/', views.programs, name='programs'),
    path('edit-program/<int:id>/', views.edit_program, name='edit_program'),
    path('delete-program/<int:id>/', views.delete_program, name='delete_program'),

    path('semesters/', views.semesters, name='semesters'),
    path('edit-semester/<int:id>/', views.edit_semester, name='edit_semester'),
    path('delete-semester/<int:id>/', views.delete_semester, name='delete_semester'),


    path('divisions/', views.divisions, name='divisions'),
    path('edit-division/<int:id>/', views.edit_division, name='edit_division'),
    path('delete-division/<int:id>/', views.delete_division, name='delete_division'),
    
    path('subjects/', views.subjects, name='subjects'),
    path('edit-subject/<int:id>/', views.edit_subject, name='edit_subject'),
    path('delete-subject/<int:id>/', views.delete_subject, name='delete_subject'),

    path('attendance/', views.attendance_view, name='attendance'),
    path('report/', views.report_view, name='report'),

]

