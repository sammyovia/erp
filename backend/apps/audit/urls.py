from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, AuditStatsView

# Create router for ViewSet
router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-logs')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Statistics endpoint
    path('stats/', AuditStatsView.as_view(), name='audit-stats'),
]