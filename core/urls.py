"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
