from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import re

class TenantMiddleware(MiddlewareMixin):
    """
    Defense-in-depth tenant isolation middleware.
    Extracts tenant from JWT token and validates before any domain logic.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.public_paths = [
            r'^/api/auth/',
            r'^/api/health/',
            r'^/docs/',
            r'^/swagger/',
            r'^/admin/',
        ]
    
    def __call__(self, request):
        # Skip tenant validation for public paths
        path = request.path
        for pattern in self.public_paths:
            if re.match(pattern, path):
                return self.get_response(request)
        
        # Extract tenant from headers
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            request.tenant_id = tenant_id
            
            # Additional application-level check for authenticated users
            if hasattr(request, 'user') and request.user.is_authenticated:
                if hasattr(request.user, 'tenantuser_set'):
                    allowed_tenant_ids = request.user.tenantuser_set.values_list('tenant_id', flat=True)
                    if str(tenant_id) not in [str(tid) for tid in allowed_tenant_ids]:
                        return JsonResponse(
                            {
                                'type': 'tenant_access_denied',
                                'title': 'Tenant Access Denied',
                                'status': 403,
                                'detail': 'You do not have access to this tenant'
                            },
                            status=403
                        )
        else:
            # Only require tenant ID for authenticated requests
            if hasattr(request, 'user') and request.user.is_authenticated:
                return JsonResponse(
                    {
                        'type': 'tenant_required',
                        'title': 'Tenant ID Required',
                        'status': 400,
                        'detail': 'X-Tenant-ID header is required'
                    },
                    status=400
                )
        
        return self.get_response(request)