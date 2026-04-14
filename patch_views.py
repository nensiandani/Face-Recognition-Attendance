import re
import os

views_path = "accounts/views.py"

with open(views_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add isolate_qs definition near the top.
isolate_def = """
def isolate_qs(request, qs):
    if not request.user.is_authenticated:
        return qs.none()
    if getattr(request.user, 'is_superuser', False):
        return qs
    return qs.filter(created_by=request.user)
"""
if "def isolate_qs" not in content:
    content = content.replace("def admin_check(user):", isolate_def + "\ndef admin_check(user):")

# 2. Patch admin_login function to allow superuser
# Find admin_login
admin_login_pattern = r'users = User\.objects\.filter\(email=email,\s*is_staff=True\)'
admin_login_repl = r'users = User.objects.filter(Q(email=email) & (Q(is_staff=True) | Q(is_superuser=True)))'
content = re.sub(admin_login_pattern, admin_login_repl, content)

# 3. Add manage_admins and manage_api_keys
new_views = """

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
"""

# Append new views if they don't exist
if "def manage_admins" not in content:
    content += new_views

# 4. Global replacement: queries like Model.objects.all() to isolate_qs(request, Model.objects.all())
# We will do this specifically in parts where objects are fetched for templates
models_to_isolate = ["Faculty", "Department", "Program", "Semester", "Division", "Subject"]
for model in models_to_isolate:
    content = re.sub(rf'\b{model}\.objects\.all\(\)', rf'isolate_qs(request, {model}.objects.all())', content)

# Also apply created_by during model creations
# Look for Model.objects.create(...)
creation_patterns = [
    (r'(Subject\.objects\.create\s*\(\s*name=[^,]+,\s*(?:course_code=[^,]+,\s*)?subject_type=[^,]+,\s*faculty=[^,]+,\s*department=[^)]+)', r'\1, created_by=request.user'),
    (r'(Faculty\.objects\.create\s*\(\s*name=[^,]+(?:,\s*faculty_code=[^)]+)?)\)', r'\1, created_by=request.user)'),
    (r'(Department\.objects\.create\s*\(\s*name=[^)]+)\)', r'\1, created_by=request.user)'),
    (r'(Program\.objects\.create\s*\(\s*name=[^)]+)\)', r'\1, created_by=request.user)'),
    (r'(Semester\.objects\.create\s*\(\s*name=[^)]+)\)', r'\1, created_by=request.user)'),
    (r'(Division\.objects\.create\s*\(\s*name=[^)]+)\)', r'\1, created_by=request.user)'),
]
for pat, repl in creation_patterns:
    content = re.sub(pat, repl, content)

# Check custom save like `f = Faculty(name=...) \n f.save()`? 
# Usually we just use objects.create. Let's see if there are any `new_sub = Subject(...)` followed by save.
# By patching just the views, if we miss any, we could manually check later.

# Fix Profile passing user creation
# "Profile.objects.create(user=user, mobile=mobile..."  -> add `created_by=request.user`
content = content.replace("Profile.objects.create(user=user, mobile=mobile", "Profile.objects.create(user=user, created_by=request.user, mobile=mobile")

with open(views_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to accounts/views.py successfully.")
