from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from tenants.models import School
from .models import WebsiteConfig
from .serializers import WebsiteConfigSerializer, PublicWebsiteSerializer
from notices.models import Notice
from events.models import Event
from shop.models import Product


class IsSchoolAdmin(permissions.BasePermission):
    """Only school ADMINs can manage website configuration."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == 'ADMIN')

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated and user.role == 'ADMIN'):
            return False
        return obj.school_id == getattr(user, 'school_id', None)


class WebsiteConfigViewSet(viewsets.ModelViewSet):
    """CRUD for a school's website configuration.

    Scoped to the requesting user's school.  Only ADMINs may write.
    Draft saves never touch the published site; publish/unpublish actions
    control public visibility.
    """

    serializer_class = WebsiteConfigSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]

    def get_queryset(self):
        return WebsiteConfig.objects.filter(school=self.request.user.school)

    def get_object(self):
        # Always return the config for the user's school, creating a default
        # one on first access so new schools get a working template.
        obj = WebsiteConfig.objects.filter(school=self.request.user.school).first()
        if obj is None:
            obj = WebsiteConfig.objects.create(
                school=self.request.user.school,
                status='draft',
                sections=self._default_sections(),
            )
        return obj

    def list(self, request, *args, **kwargs):
        """Return the singleton website config for the user's school."""
        config = self.get_object()
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        config = self.get_object()
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], url_path='update')
    def update_config(self, request, *args, **kwargs):
        config = self.get_object()
        serializer = self.get_serializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.last_saved_at = timezone.now()
        instance.save(update_fields=['last_saved_at'])

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Website configuration cannot be deleted.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def _default_sections(self):
        return {
            'hero': {'visible': True, 'order': 1},
            'about': {'visible': True, 'order': 2},
            'headteacher': {'visible': True, 'order': 3},
            'programmes': {'visible': True, 'order': 4},
            'admissions': {'visible': True, 'order': 5},
            'announcements': {'visible': True, 'order': 6},
            'events': {'visible': True, 'order': 7},
            'products': {'visible': True, 'order': 8},
            'contact': {'visible': True, 'order': 9},
        }

    def perform_update(self, serializer):
        from datetime import timedelta
        instance = serializer.save()
        instance.last_saved_at = timezone.now()
        instance.save(update_fields=['last_saved_at'])

    @action(detail=False, methods=['post'])
    def publish(self, request):
        """Publish the current configuration, making it publicly visible."""
        config = self.get_object()
        config.status = 'published'
        config.published_at = timezone.now()
        config.last_saved_at = timezone.now()
        config.save(update_fields=['status', 'published_at', 'last_saved_at'])
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def unpublish(self, request):
        """Take the public site down without deleting configuration."""
        config = self.get_object()
        config.status = 'unpublished'
        config.last_saved_at = timezone.now()
        config.save(update_fields=['status', 'last_saved_at'])
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def reset_defaults(self, request):
        """Restore default template config while preserving school records."""
        config = self.get_object()
        config.primary_color = '#2563eb'
        config.secondary_color = '#0ea5e9'
        config.display_name = ''
        config.tagline = ''
        config.homepage_title = ''
        config.homepage_subtitle = ''
        config.about_school = ''
        config.school_history = ''
        config.mission = ''
        config.headteacher_message = ''
        config.admissions_info = ''
        config.contact_info = ''
        config.school_location = ''
        config.sections = self._default_sections()
        config.featured_notice_ids = []
        config.featured_product_ids = []
        config.status = 'draft'
        config.last_saved_at = timezone.now()
        config.save()
        serializer = self.get_serializer(config)
        return Response(serializer.data)


class PublicWebsiteView(APIView):
    """Public read-only endpoint for a school's published website.

    Resolves the school by its unique code (slug).  Returns the website
    configuration plus public notices, events and products.  Unauthenticated
    access is allowed.  Draft/unpublished sites return 404.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            school = School.objects.get(code=slug, is_active=True)
        except School.DoesNotExist:
            return Response({'detail': 'School not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            config = WebsiteConfig.objects.get(school=school)
        except WebsiteConfig.DoesNotExist:
            return Response({'detail': 'Website not configured for this school.'}, status=status.HTTP_404_NOT_FOUND)

        if config.status != 'published':
            return Response({'detail': 'Website is not published.'}, status=status.HTTP_404_NOT_FOUND)

        # Gather public content for this school.
        notices_qs = Notice.objects.filter(school=school, is_published=True).order_by('-is_pinned', '-created_at')[:20]
        events_qs = Event.objects.filter(school=school).order_by('start_date')[:20]
        product_ids = config.featured_product_ids or []
        products_qs = Product.objects.filter(
            school=school, is_active=True, id__in=product_ids
        )[:12] if product_ids else Product.objects.filter(school=school, is_active=True)[:12]

        notice_ids = config.featured_notice_ids or []
        if notice_ids:
            notices_qs = notices_qs.filter(id__in=notice_ids)

        data = {
            'school': school,
            'status': config.status,
            'primary_color': config.primary_color,
            'secondary_color': config.secondary_color,
            'display_name': config.display_name,
            'tagline': config.tagline,
            'homepage_title': config.homepage_title,
            'homepage_subtitle': config.homepage_subtitle,
            'logo_url': request.build_absolute_uri(config.logo.url) if config.logo else None,
            'hero_image_url': request.build_absolute_uri(config.hero_image.url) if config.hero_image else None,
            'about_school': config.about_school,
            'school_history': config.school_history,
            'mission': config.mission,
            'headteacher_message': config.headteacher_message,
            'admissions_info': config.admissions_info,
            'contact_info': config.contact_info,
            'school_location': config.school_location,
            'sections': config.sections or {},
            'notices': notices_qs,
            'events': events_qs,
            'products': products_qs,
        }

        serializer = PublicWebsiteSerializer(data, context={'request': request})
        return Response(serializer.data)
