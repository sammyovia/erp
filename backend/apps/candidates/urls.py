from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandidateViewSet

router = DefaultRouter()
router.register(r'', CandidateViewSet, basename='candidate')

urlpatterns = [
    path('', include(router.urls)),
]