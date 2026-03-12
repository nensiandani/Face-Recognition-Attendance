"""
URL configuration for visionai project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

     # 🔴 LOGOUT URL
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', include('accounts.urls')),
    
    # 💡 આ નવી લાઈન ગૂગલ ઓથ (Google Auth) માટે ઉમેરી છે
    path('accounts/', include('allauth.urls')), 
]

# 🔥 MEDIA FILES
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)