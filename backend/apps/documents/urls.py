from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet

# Create router
router = DefaultRouter()
router.register(r'', DocumentViewSet, basename='document')

# urlpatterns MUST be defined
urlpatterns = [
    path('', include(router.urls)),
]