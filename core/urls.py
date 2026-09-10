"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.http import FileResponse, Http404
import os

FRONTEND_DIST_DIR = '/home/joe/Documents/Code/my-django-project/frontend/codingclubskenya/dist'


class FrontendAppView(TemplateView):
    template_name = 'index.html'


def serve_frontend(request, path=''):
    """Serve frontend build files for /schoolsystem/ SPA routing."""
    if not path:
        path = 'index.html'
    file_path = os.path.join(FRONTEND_DIST_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(open(file_path, 'rb'))
    # Fall back to index.html for SPA routing
    index_path = os.path.join(FRONTEND_DIST_DIR, 'index.html')
    if os.path.isfile(index_path):
        return FileResponse(open(index_path, 'rb'))
    raise Http404("Frontend build not found")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/tenants/', include('tenants.urls')),
    path('api/academics/', include('academics.urls')),
    path('api/assessment/', include('assessment.urls')),
    path('api/curriculum/', include('curriculum.urls')),
    path('api/shop/', include('shop.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/exams/', include('exams.urls')),
    path('api/fees/', include('fees.urls')),
    path('api/library/', include('library.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/clubs/', include('clubs.urls')),
    path('api/recruitment/', include('recruitment.urls')),
    path('api/distributor/', include('distributor.urls')),
    path('api/requirements/', include('requirements.urls')),
    path('api/complaints/', include('complaints.urls')),
    path('api/events/', include('events.urls')),
    path('api/homework/', include('homework.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/notices/', include('notices.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schoolsystem/', lambda request: serve_frontend(request, 'index.html'), name='frontend'),
    re_path(r'^schoolsystem/(?P<path>.*)$', lambda request, path: serve_frontend(request, path), name='frontend-spa'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
