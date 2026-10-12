from django.urls import path

from .views import learner_report, learner_roster, update_learner_assessment

urlpatterns = [
    path("learners/", learner_roster, name="gradebook-learner-roster"),
    path("learners/<int:pk>/report/", learner_report, name="gradebook-learner-report"),
    path("learners/<int:pk>/assessments/", update_learner_assessment, name="gradebook-learner-assessments"),
]
