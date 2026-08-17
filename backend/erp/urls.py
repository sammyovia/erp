from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Erp API",
        default_version='v1',
        description="Multi-tenant compliance platform API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@e3os.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/candidates/', include('apps.candidates.urls')),
    path('api/documents/', include('apps.documents.urls')),
    path('api/ai/', include('apps.ai.urls')),  
    path('api/tenants/', include('apps.tenants.urls')),
    path('api/audit/', include('apps.audit.urls')),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
]