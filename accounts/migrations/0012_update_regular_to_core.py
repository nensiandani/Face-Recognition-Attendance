from django.db import migrations, models

def update_regular_to_core(apps, schema_editor):
    Subject = apps.get_model('accounts', 'Subject')
    Subject.objects.filter(subject_type='regular').update(subject_type='core')

def reverse_core_to_regular(apps, schema_editor):
    Subject = apps.get_model('accounts', 'Subject')
    Subject.objects.filter(subject_type='core').update(subject_type='regular')

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_subject_program_semester_pairs'),
    ]

    operations = [
        migrations.RunPython(update_regular_to_core, reverse_code=reverse_core_to_regular),
        migrations.AlterField(
            model_name='subject',
            name='divisions',
            field=models.ManyToManyField(blank=True, related_name='core_subjects', to='accounts.division'),
        ),
    ]
