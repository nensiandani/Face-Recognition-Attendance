from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_update_regular_to_core'),
    ]

    operations = [
        migrations.AddField(
            model_name='faculty',
            name='faculty_code',
            field=models.CharField(blank=True, help_text='Short code e.g. AT, TKM, BK', max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='subject',
            name='course_code',
            field=models.CharField(blank=True, help_text='Course code e.g. HM227, CS301', max_length=20, null=True, unique=True),
        ),
    ]
