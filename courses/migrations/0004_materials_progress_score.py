from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_lms_lesson_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='prerequisite',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dependents', to='courses.lesson'),
        ),
        migrations.AddField(
            model_name='lessonprogress',
            name='score',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='LearningMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('material_type', models.CharField(choices=[('video', 'Video'), ('pdf', 'PDF / Notes'), ('quiz', 'Quiz'), ('assignment', 'Assignment')], default='pdf', max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField(blank=True, help_text='Notes text or assignment description')),
                ('file', models.FileField(blank=True, null=True, upload_to='course_materials/%Y/%m/')),
                ('url', models.URLField(blank=True, help_text='Video or external link', max_length=500)),
                ('order', models.PositiveIntegerField(default=0)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materials', to='courses.lesson')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_materials', to='tenants.school')),
            ],
            options={
                'ordering': ['order', 'id'],
            },
        ),
    ]
