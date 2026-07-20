from rest_framework import serializers
from .models import (
    Course, Lesson, CourseEnrollment, LessonProgress, Topic,
    Quiz, QuizQuestion, QuizAttempt, LessonComment, LearningMaterial,
)


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'learning_area', 'title', 'order', 'is_published']
        read_only_fields = ['is_published']


class LearningMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningMaterial
        fields = ['id', 'lesson', 'material_type', 'title', 'content', 'file', 'url', 'order']


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'prompt', 'option_a', 'option_b', 'option_c', 'option_d', 'correct', 'order']


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'lesson', 'title', 'questions']


class LessonCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = LessonComment
        fields = ['id', 'lesson', 'author', 'author_name', 'body', 'created_at']
        read_only_fields = ['author', 'created_at']

    def get_author_name(self, obj):
        u = obj.author
        return f"{u.first_name} {u.last_name}".strip() or u.email

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data['school'] = self.context['request'].user.school
        return super().create(validated_data)


class LessonSerializer(serializers.ModelSerializer):
    topic = TopicSerializer(read_only=True)
    materials = LearningMaterialSerializer(many=True, read_only=True)
    is_visible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'topic', 'sub_strand', 'title', 'lesson_number',
            'strand', 'objectives', 'learning_activities', 'resources',
            'assessment', 'remarks', 'content', 'materials',
            'video_url', 'attachment', 'order', 'prerequisite', 'is_published',
            'publish_at', 'is_visible',
        ]


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    learner_name = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = ['id', 'learner', 'learner_name', 'enrolled_at']

    def get_learner_name(self, obj):
        u = obj.learner
        return f"{u.first_name} {u.last_name}".strip() or u.email


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    enrollments = CourseEnrollmentSerializer(source='enrollments', many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'learning_area', 'author', 'title', 'description', 'status', 'delivery_mode',
                  'available_from', 'requires_parent_unlock', 'cloned_from', 'version', 'lessons', 'enrollments']
        read_only_fields = ['author', 'cloned_from', 'version', 'status']


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'learner', 'is_completed', 'score', 'completed_at', 'marked_by']
        read_only_fields = ['completed_at', 'marked_by']


class QuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'learner', 'score', 'total', 'taken_at']
        read_only_fields = ['learner', 'taken_at']
