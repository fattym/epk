from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, LessonProgressViewSet, LessonViewSet,
    TopicViewSet, QuizViewSet, LessonCommentViewSet, LearningMaterialViewSet,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'lesson-comments', LessonCommentViewSet, basename='lesson-comment')
router.register(r'learning-materials', LearningMaterialViewSet, basename='learning-material')
router.register(r'lesson-progress', LessonProgressViewSet, basename='lesson-progress')

urlpatterns = [
    path('', include(router.urls)),
]
