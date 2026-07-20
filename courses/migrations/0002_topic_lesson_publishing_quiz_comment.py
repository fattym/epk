from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
        ('academics', '0003_alter_teacherassignment_options_and_more'),
        ('tenants', '0002_schoolsettings_requires_course_review'),
    ]

    operations = [
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_published', models.BooleanField(default=False)),
                ('learning_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='academics.learningarea')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topics', to='tenants.school')),
            ],
            options={
                'ordering': ['learning_area', 'order'],
            },
        ),
        migrations.AddField(
            model_name='lesson',
            name='topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lessons', to='courses.topic'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='video_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='lesson',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='course_attachments/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='is_published',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lesson',
            name='publish_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='quiz',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quizzes', to='tenants.school'),
        ),
        migrations.CreateModel(
            name='QuizQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prompt', models.TextField()),
                ('option_a', models.CharField(max_length=255)),
                ('option_b', models.CharField(max_length=255)),
                ('option_c', models.CharField(blank=True, max_length=255)),
                ('option_d', models.CharField(blank=True, max_length=255)),
                ('correct', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1)),
                ('order', models.PositiveIntegerField(default=0)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='courses.quiz')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveIntegerField(default=0)),
                ('total', models.PositiveIntegerField(default=0)),
                ('taken_at', models.DateTimeField(auto_now_add=True)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='courses.quiz')),
                ('learner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to='tenants.school')),
            ],
            options={
                'ordering': ['-taken_at'],
            },
        ),
        migrations.CreateModel(
            name='LessonComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_comments', to=settings.AUTH_USER_MODEL)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='courses.lesson')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_comments', to='tenants.school')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
