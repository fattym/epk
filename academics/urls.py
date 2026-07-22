from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GradeViewSet, PathwayViewSet, StreamViewSet, LearningAreaViewSet,
    StrandViewSet, SubStrandViewSet, LearningOutcomeViewSet, RubricDescriptorViewSet,
    TeacherAssignmentViewSet, ClassTeacherViewSet, EnrollmentViewSet,
    TimetableViewSet, AssignmentViewSet, TermViewSet, LearnerGroupViewSet,
    AITeacherAssistView,
)

router = DefaultRouter()
router.register(r'grades', GradeViewSet)
router.register(r'pathways', PathwayViewSet)
router.register(r'streams', StreamViewSet)
router.register(r'learning-areas', LearningAreaViewSet)
router.register(r'strands', StrandViewSet)
router.register(r'sub-strands', SubStrandViewSet)
router.register(r'learning-outcomes', LearningOutcomeViewSet)
router.register(r'rubric-descriptors', RubricDescriptorViewSet)
router.register(r'teacher-assignments', TeacherAssignmentViewSet)
router.register(r'class-teachers', ClassTeacherViewSet)
router.register(r'enrollments', EnrollmentViewSet)
router.register(r'timetable', TimetableViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'terms', TermViewSet)
router.register(r'learner-groups', LearnerGroupViewSet)

urlpatterns = [
    path('ai-assist/', AITeacherAssistView.as_view(), name='ai-assist'),
    path('', include(router.urls)),
]
