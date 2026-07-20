from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_topic_lesson_publishing_quiz_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='title',
            field=models.CharField(blank=True, default='Untitled Course', max_length=255),
        ),
        migrations.AddField(
            model_name='lesson',
            name='lesson_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='lesson',
            name='strand',
            field=models.CharField(blank=True, help_text='Strand / Topic', max_length=255),
        ),
        migrations.AddField(
            model_name='lesson',
            name='objectives',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='learning_activities',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='resources',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='assessment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='remarks',
            field=models.TextField(blank=True),
        ),
    ]
