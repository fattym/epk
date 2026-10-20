from rest_framework import serializers
from .models import WebsiteConfig
from notices.models import Notice
from events.models import Event
from shop.models import Product


class WebsiteConfigSerializer(serializers.ModelSerializer):
    """Serializer for the school website configuration (protected CRUD)."""

    logo_url = serializers.SerializerMethodField()
    hero_image_url = serializers.SerializerMethodField()

    class Meta:
        model = WebsiteConfig
        fields = [
            'id', 'school', 'status',
            'primary_color', 'secondary_color', 'display_name', 'tagline',
            'homepage_title', 'homepage_subtitle',
            'logo', 'logo_url', 'hero_image', 'hero_image_url',
            'about_school', 'school_history', 'mission', 'headteacher_message',
            'admissions_info', 'contact_info', 'school_location',
            'sections', 'featured_notice_ids', 'featured_product_ids',
            'created_at', 'updated_at', 'published_at', 'last_saved_at',
        ]
        read_only_fields = [
            'id', 'school', 'created_at', 'updated_at',
            'published_at', 'last_saved_at',
        ]

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and hasattr(obj.logo, 'url'):
            url = obj.logo.url
            if request is not None and not url.startswith('http'):
                return request.build_absolute_uri(url)
            return url
        return None

    def get_hero_image_url(self, obj):
        request = self.context.get('request')
        if obj.hero_image and hasattr(obj.hero_image, 'url'):
            url = obj.hero_image.url
            if request is not None and not url.startswith('http'):
                return request.build_absolute_uri(url)
            return url
        return None

    def validate_status(self, value):
        return value

    def validate(self, attrs):
        # School is immutable once set; enforced via view + read_only field.
        return attrs


class PublicNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ['id', 'title', 'content', 'is_pinned', 'created_at']


class PublicEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'event_type', 'start_date', 'end_date', 'location']


class PublicProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image', 'image_url', 'is_active']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if request is not None and not url.startswith('http'):
                return request.build_absolute_uri(url)
            return url
        return None


class PublicWebsiteSerializer(serializers.Serializer):
    """Read-only serializer for the public website payload.

    Combines WebsiteConfig with the school's public notices, events and
    products.  Never exposes learner, payment, or internal data.
    """

    school = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    branding = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    notices = PublicNoticeSerializer(many=True, read_only=True)
    events = PublicEventSerializer(many=True, read_only=True)
    products = PublicProductSerializer(many=True, read_only=True)

    def get_school(self, obj):
        school = obj.get('school')
        if not school:
            return None
        return {
            'id': school.id,
            'name': school.name,
            'code': school.code,
            'address': school.address,
            'phone': school.phone,
            'email': school.email,
            'website': school.website,
            'logo_url': obj.get('logo_url'),
        }

    def get_status(self, obj):
        return obj.get('status')

    def get_branding(self, obj):
        school = obj.get('school')
        school_name = school.name if school else ''
        return {
            'primary_color': obj.get('primary_color'),
            'secondary_color': obj.get('secondary_color'),
            'display_name': obj.get('display_name') or school_name,
            'tagline': obj.get('tagline'),
            'homepage_title': obj.get('homepage_title'),
            'homepage_subtitle': obj.get('homepage_subtitle'),
            'logo_url': obj.get('logo_url'),
            'hero_image_url': obj.get('hero_image_url'),
        }

    def get_content(self, obj):
        return {
            'about_school': obj.get('about_school'),
            'school_history': obj.get('school_history'),
            'mission': obj.get('mission'),
            'headteacher_message': obj.get('headteacher_message'),
            'admissions_info': obj.get('admissions_info'),
            'contact_info': obj.get('contact_info'),
            'school_location': obj.get('school_location'),
        }

    def get_sections(self, obj):
        return obj.get('sections', {})
