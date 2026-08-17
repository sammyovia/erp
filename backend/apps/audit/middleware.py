from django.utils.deprecation import MiddlewareMixin
from .services import AuditService

class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to capture IP address and user agent for audit logs
    """
    
    def process_request(self, request):
        """Store request info for later use in audit logs"""
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Store in request for audit services to use
        request.audit_ip = ip
        request.audit_user_agent = user_agent
        
        return None