from django.urls import path
from .views import (
    overview, attendance_trend, results, performance,
    teachers_report, export_csv,
    dashboard_kpis, performance_by_subject, performance_by_class,
    progress_over_terms, performance_distribution,
    attendance_trend_chart, marking_completion, at_risk_students,
)

urlpatterns = [
    path('overview/', overview, name='overview'),
    path('attendance/', attendance_trend, name='attendance-trend'),
    path('results/', results, name='results'),
    path('performance/', performance, name='performance'),
    path('teachers/', teachers_report, name='teachers-report'),
    path('export/', export_csv, name='export-csv'),
    # Analytics Dashboard endpoints
    path('dashboard-kpis/', dashboard_kpis, name='dashboard-kpis'),
    path('performance-by-subject/', performance_by_subject, name='performance-by-subject'),
    path('performance-by-class/', performance_by_class, name='performance-by-class'),
    path('progress-over-terms/', progress_over_terms, name='progress-over-terms'),
    path('performance-distribution/', performance_distribution, name='performance-distribution'),
    path('attendance-trend/', attendance_trend_chart, name='attendance-trend-analytics'),
    path('marking-completion/', marking_completion, name='marking-completion'),
    path('at-risk-students/', at_risk_students, name='at-risk-students'),
]
