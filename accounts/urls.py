from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('setup-secret-admin/', views.setup_secret_admin, name='setup_secret_admin'),
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_user, name='logout_user'),

    path('admin-profile/', views.admin_profile, name='admin_profile'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/bulk-register/', views.bulk_register_students, name='bulk_register'),
    path('admin-dashboard/wipe-dummy-students/', views.wipe_dummy_students, name='wipe_dummy_students'),
    path('admin-dashboard/debug-users/', views.debug_users, name='debug_users'),

    path('my-attendance/', views.student_attendance, name='student_attendance'),

    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('api/attendance-progress/', views.get_attendance_progress, name='attendance_progress'),

    path('attendance-history/', views.attendance_history, name='attendance_history'),
    path('download-attendance/<int:session_id>/', views.download_attendance, name='download_attendance'),

    path('divisions/', views.divisions, name='divisions'),

    path('admin-dashboard/<int:user_id>/', views.admin_dashboard, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin-dashboard/bulk-delete/', views.bulk_delete_users, name='bulk_delete_users'),

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

    path('edit-division/<int:id>/', views.edit_division, name='edit_division'),
    path('delete-division/<int:id>/', views.delete_division, name='delete_division'),

    path('subjects/', views.subjects, name='subjects'),
    path('edit-subject/<int:id>/', views.edit_subject, name='edit_subject'),
    path('delete-subject/<int:id>/', views.delete_subject, name='delete_subject'),

    path('attendance/', views.attendance_view, name='attendance'),
    path('report/', views.report_view, name='report'),

    path('verify-otp/', views.verify_otp, name='verify_otp'),

    path('reset_password/', views.custom_password_reset, name="password_reset"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="password_reset_complete.html"), name="password_reset_complete"),

    # ─── LIVE SCAN ──────────────────────────────────────────────────────────────
    # path('live-scan/', views.live_scan_page, name='live_scan_page'),
    # path('live-scan/<int:session_id>/', views.live_scan_page, name='live_scan_page_session'),

    # API endpoints (no CSRF — they use custom auth)
    path('api/live-scan/', views.api_live_scan, name='api_live_scan'),
    path('api/live-session/<int:session_id>/status/', views.live_session_status, name='live_session_status'),
    path('api/live-session/<int:session_id>/close/', views.close_live_session_api, name='close_live_session_api'),

    # Admin: create & manage live sessions
    path('admin-dashboard/live-sessions/', views.create_live_session, name='create_live_session'),

    # Admin: compute face encodings
    path('admin-dashboard/compute-encodings/', views.compute_encodings_api, name='compute_encodings'),

    # ─── KIOSK MODE ─────────────────────────────────────────────────────────────
    path('kiosk/<str:token>/', views.kiosk_page, name='kiosk_page'),
    path('api/kiosk-scan/', views.api_kiosk_scan, name='api_kiosk_scan'),

    # ─── SUBJECT ENROLLMENT ────────────────────────────────────────────────────
    path('subject-enrollment/', views.manage_enrollment, name='manage_enrollment'),
    path('subject-enrollment/<int:subject_id>/', views.manage_enrollment, name='manage_enrollment_subject'),

    # ─── ENROLLMENT API ──────────────────────────────────────────────────────────
    path('api/subject-context/<int:subject_id>/', views.get_subject_context, name='subject_context'),
    path('api/eligible-students/<int:subject_id>/', views.get_eligible_students, name='eligible_students'),
    path('api/enroll-student/', views.enroll_student_ajax, name='enroll_student_ajax'),
    path('api/bulk-enroll-preview/<int:subject_id>/', views.bulk_enroll_preview, name='bulk_enroll_preview'),
    path('api/bulk-enroll-confirm/<int:subject_id>/', views.bulk_enroll_confirm, name='bulk_enroll_confirm'),
    path('api/remove-enrollment/<int:enrollment_id>/', views.remove_enrollment, name='remove_enrollment'),

    # ─── PROXY MEDICAL LEAVE ────────────────────────────────────────────────────
    path('grant-medical-leave/', views.grant_medical_leave, name='grant_medical_leave'),
]
# FORCE RELOAD 2
