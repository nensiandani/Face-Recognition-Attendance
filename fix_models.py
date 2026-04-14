import re

with open('accounts/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

models = ["Faculty", "Department", "Program", "Semester", "Division", "Subject", "Attendance"]

for model in models:
    # Find the created_by line inside the model
    # Wait, the simplest replacing is just finding:
    # class Faculty(models.Model): ... created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # We can just replace:
    # created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # with
    # created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_classname')
    # but since they all have the same exact string, we should use re to do it per class.
    
    pattern = rf'(class {model}\(models\.Model\):.*?)(created_by = models\.ForeignKey\(User, on_delete=models\.CASCADE, null=True, blank=True\))'
    
    def replacer(match):
        class_part = match.group(1)
        # created_something_set isn't needed, just a unique string
        return f"{class_part}created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='created_{model.lower()}s')"
        
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)

with open('accounts/models.py', 'w', encoding='utf-8') as f:
    f.write(content)
