from django.urls import path
from .views import (
    overview, attendance_trend, results, performance, teachers_report, export_csv,
)

urlpatterns = [
    path('overview/', overview, name='overview'),
    path('attendance/', attendance_trend, name='attendance'),
    path('results/', results, name='results'),
    path('performance/', performance, name='performance'),
    path('teachers/', teachers_report, name='teachers'),
    path('export/', export_csv, name='export'),
]
