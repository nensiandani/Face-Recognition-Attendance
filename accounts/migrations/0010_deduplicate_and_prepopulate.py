from django.db import migrations


def deduplicate_and_prepopulate(apps, schema_editor):
    Program = apps.get_model('accounts', 'Program')
    Semester = apps.get_model('accounts', 'Semester')
    Division = apps.get_model('accounts', 'Division')
    Department = apps.get_model('accounts', 'Department')
    Subject = apps.get_model('accounts', 'Subject')

    # ── 1. DEDUPLICATE DEPARTMENTS ────────────────────────────────────────────
    seen_dept = {}
    for dept in Department.objects.order_by('id'):
        key = dept.name.strip().lower()
        if key in seen_dept:
            # Redirect all Subject FKs to the keeper
            keeper_id = seen_dept[key]
            Subject.objects.filter(department_id=dept.id).update(department_id=keeper_id)
            dept.delete()
        else:
            seen_dept[key] = dept.id

    # ── 2. DEDUPLICATE PROGRAMS ───────────────────────────────────────────────
    seen_prog = {}
    for prog in Program.objects.order_by('id'):
        key = prog.name.strip().lower()
        if key in seen_prog:
            keeper_id = seen_prog[key]
            keeper = Program.objects.get(id=keeper_id)
            # Update Subject FK (regular program)
            Subject.objects.filter(program_id=prog.id).update(program_id=keeper_id)
            # Update Subject M2M (programs for elective)
            for subj in Subject.objects.filter(programs=prog):
                subj.programs.add(keeper)
                subj.programs.remove(prog)
            prog.delete()
        else:
            seen_prog[key] = prog.id

    # ── 3. DEDUPLICATE SEMESTERS ──────────────────────────────────────────────
    seen_sem = {}
    for sem in Semester.objects.order_by('id'):
        key = sem.name.strip().lower()
        if key in seen_sem:
            keeper_id = seen_sem[key]
            keeper = Semester.objects.get(id=keeper_id)
            # Update Subject FK (regular semester)
            Subject.objects.filter(semester_id=sem.id).update(semester_id=keeper_id)
            # Update Subject M2M (semesters for elective)
            for subj in Subject.objects.filter(semesters=sem):
                subj.semesters.add(keeper)
                subj.semesters.remove(sem)
            sem.delete()
        else:
            seen_sem[key] = sem.id

    # ── 4. DEDUPLICATE DIVISIONS ──────────────────────────────────────────────
    seen_div = {}
    for div in Division.objects.order_by('id'):
        key = div.name.strip().lower()
        if key in seen_div:
            keeper_id = seen_div[key]
            keeper = Division.objects.get(id=keeper_id)
            # Update Subject M2M (divisions for regular)
            for subj in Subject.objects.filter(divisions=div):
                subj.divisions.add(keeper)
                subj.divisions.remove(div)
            div.delete()
        else:
            seen_div[key] = div.id

    # ── 5. PRE-POPULATE SEMESTERS 1-8 ────────────────────────────────────────
    for num in range(1, 9):
        name = str(num)
        if not Semester.objects.filter(name=name).exists():
            Semester.objects.create(name=name)

    # ── 6. PRE-POPULATE DIVISIONS A, B, C ────────────────────────────────────
    for letter in ['A', 'B', 'C']:
        if not Division.objects.filter(name=letter).exists():
            Division.objects.create(name=letter)


def reverse_migration(apps, schema_editor):
    # Reverse is a no-op — we cannot restore deleted duplicates
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_standalone_setup_models'),
    ]

    operations = [
        migrations.RunPython(deduplicate_and_prepopulate, reverse_migration),
    ]
