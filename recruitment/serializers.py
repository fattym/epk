from rest_framework import serializers
from .models import PipelineStage, JobPosting, Candidate, Application, Interview, ScoreCard, Offer


class PipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStage
        fields = ['id', 'school', 'name', 'order', 'is_default']
        read_only_fields = ['id', 'school']


class JobPostingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPosting
        fields = [
            'id', 'school', 'title', 'description', 'department',
            'employment_type', 'location', 'requirements', 'responsibilities',
            'benefits', 'application_deadline', 'is_active', 'is_published',
            'posted_by', 'created_at', 'updated_at', 'views_count',
        ]
        read_only_fields = ['id', 'school', 'posted_by', 'created_at', 'updated_at', 'views_count']


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'resume', 'cover_letter', 'source', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_resume(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('Resume file size must be under 5MB.')
        allowed_types = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('Resume must be a PDF or Word document.')
        return value


class ApplicationSerializer(serializers.ModelSerializer):
    candidate = CandidateSerializer()
    job_posting = serializers.StringRelatedField()

    class Meta:
        model = Application
        fields = ['id', 'job_posting', 'candidate', 'school', 'status', 'applied_at', 'notes']
        read_only_fields = ['id', 'school', 'applied_at']

    def validate(self, data):
        if not self.context.get('is_public'):
            return data
        if not data.get('candidate', {}).get('email'):
            raise serializers.ValidationError({'email': 'This field is required.'})
        return data

    def create(self, validated_data):
        candidate_data = validated_data.pop('candidate')
        email = candidate_data['email']
        candidate, created = Candidate.objects.get_or_create(
            email=email,
            defaults={
                'first_name': candidate_data.get('first_name', ''),
                'last_name': candidate_data.get('last_name', ''),
                'phone': candidate_data.get('phone', ''),
                'resume': candidate_data.get('resume'),
                'cover_letter': candidate_data.get('cover_letter', ''),
                'source': candidate_data.get('source', 'WEBSITE'),
            }
        )
        validated_data['candidate'] = candidate
        validated_data['school'] = validated_data['job_posting'].school
        return super().create(validated_data)


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'scheduled_at', 'duration_minutes',
            'location', 'video_link', 'interviewers', 'notes', 'status',
            'created_by', 'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class ScoreCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreCard
        fields = [
            'id', 'interview', 'interviewer', 'rating', 'recommendation',
            'strengths', 'concerns', 'notes', 'submitted_at',
        ]
        read_only_fields = ['id', 'submitted_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = [
            'id', 'application', 'position', 'salary_offered',
            'start_date', 'expiry_date', 'status', 'notes',
            'created_by', 'created_at', 'accepted_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'accepted_at']
