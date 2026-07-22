from rest_framework import serializers
from .models import (
    Course, Lesson, CourseEnrollment, LessonProgress, Topic,
    Quiz, QuizQuestion, QuizAttempt, LessonComment, LearningMaterial,
    Post, PostComment, Assignment, Submission,
)


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'course', 'scheme_entry', 'title', 'week', 'order', 'is_published', 'learning_area', 'school', 'sub_strand', 'learning_outcomes']
        read_only_fields = ['is_published', 'school']


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
    topic_id = serializers.PrimaryKeyRelatedField(
        source='topic',
        queryset=Topic.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )
    materials = LearningMaterialSerializer(many=True, read_only=True)
    is_visible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'course', 'topic', 'topic_id', 'sub_strand', 'title', 'lesson_number',
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
    enrollments = CourseEnrollmentSerializer(many=True, read_only=True)
    grade_name = serializers.SerializerMethodField()
    stream_name = serializers.SerializerMethodField()
    term_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'learning_area', 'author', 'teacher', 'grade', 'grade_name', 'stream', 'stream_name', 'term', 'term_name', 'year', 'title', 'description', 'status', 'delivery_mode',
                  'available_from', 'requires_parent_unlock', 'section', 'room', 'course_code', 'allow_student_posts', 'core_competencies', 'values', 'pcis', 'cloned_from', 'version', 'lessons', 'enrollments', 'teacher_name']
        read_only_fields = ['author', 'cloned_from', 'version', 'status', 'course_code']

    def get_grade_name(self, obj):
        return obj.grade.name if obj.grade else None

    def get_stream_name(self, obj):
        return str(obj.stream) if obj.stream else None

    def get_term_name(self, obj):
        return obj.term.name if obj.term else None

    def get_teacher_name(self, obj):
        u = obj.teacher or obj.author
        return f"{u.first_name} {u.last_name}".strip() or u.email if u else None


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


class PostSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'course', 'topic', 'teacher', 'teacher_name', 'post_type', 'title', 'content', 'due_date', 'attachments', 'created_at', 'comment_count']
        read_only_fields = ['teacher', 'created_at']

    def get_teacher_name(self, obj):
        u = obj.teacher
        return f"{u.first_name} {u.last_name}".strip() or u.email

    def get_comment_count(self, obj):
        return obj.comments.count()

    def create(self, validated_data):
        validated_data['teacher'] = self.context['request'].user
        validated_data['school'] = self.context['request'].user.school
        return super().create(validated_data)


class PostCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ['id', 'post', 'user', 'user_name', 'message', 'created_at']
        read_only_fields = ['user', 'created_at']

    def get_user_name(self, obj):
        u = obj.user
        return f"{u.first_name} {u.last_name}".strip() or u.email

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['school'] = self.context['request'].user.school
        return super().create(validated_data)


class CourseAssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    submission_count = serializers.SerializerMethodField()
    my_submission = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = ['id', 'topic', 'course', 'title', 'instructions', 'due_date', 'teacher', 'teacher_name', 'created_at', 'submission_count', 'my_submission']
        read_only_fields = ['teacher', 'created_at']

    def get_teacher_name(self, obj):
        u = obj.teacher
        return f"{u.first_name} {u.last_name}".strip() or u.email

    def get_submission_count(self, obj):
        return obj.submissions.count()

    def get_my_submission(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        sub = obj.submissions.filter(student=request.user).first()
        if not sub:
            return None
        return {
            'id': sub.id,
            'answer': sub.answer,
            'file': sub.file.url if sub.file else None,
            'score': sub.score,
            'submitted_at': sub.submitted_at,
            'graded_at': sub.graded_at,
        }

    def create(self, validated_data):
        validated_data['teacher'] = self.context['request'].user
        validated_data['school'] = self.context['request'].user.school
        return super().create(validated_data)


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ['id', 'assignment', 'student', 'student_name', 'answer', 'file', 'score', 'submitted_at', 'graded_at', 'graded_by']
        read_only_fields = ['student', 'submitted_at', 'graded_at', 'graded_by']

    def get_student_name(self, obj):
        u = obj.student
        return f"{u.first_name} {u.last_name}".strip() or u.email

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        validated_data['school'] = self.context['request'].user.school
        return super().create(validated_data)
