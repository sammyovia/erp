from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.tenants.models import TenantUser

class TenantPermission(BasePermission):
    """
    Permission class to ensure tenant isolation.
    Every request must have a tenant context.
    """
    def has_permission(self, request, view):
        # Allow if user is authenticated and has tenant context
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if tenant ID is present in request
        tenant_id = getattr(request, 'tenant_id', None)
        if not tenant_id:
            return False
        
        # Verify user has access to this tenant
        try:
            TenantUser.objects.get(
                user=request.user,
                tenant_id=tenant_id
            )
            return True
        except TenantUser.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        # Check if object belongs to the tenant
        if hasattr(obj, 'tenant_id'):
            return str(obj.tenant_id) == str(request.tenant_id)
        return True

class CandidatePermission(BasePermission):
    """
    Permission class for candidate operations.
    Read operations are allowed for all authenticated users.
    Write operations require 'admin' or 'recruiter' role.
    """
    def has_permission(self, request, view):
        # Read operations for all authenticated users
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write operations need specific role
        if request.user and request.user.is_authenticated:
            tenant_user = TenantUser.objects.filter(
                user=request.user,
                tenant_id=request.tenant_id
            ).first()
            
            if tenant_user:
                return tenant_user.role in ['admin', 'recruiter']
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Read operations for all authenticated users
        if request.method in SAFE_METHODS:
            return True
        
        # Write operations need specific role
        tenant_user = TenantUser.objects.filter(
            user=request.user,
            tenant_id=request.tenant_id
        ).first()
        
        return tenant_user and tenant_user.role in ['admin', 'recruiter']

class DocumentPermission(BasePermission):
    """
    Permission class for document operations.
    """
    def has_permission(self, request, view):
        # Read operations for all authenticated users
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write operations need specific role
        if request.user and request.user.is_authenticated:
            tenant_user = TenantUser.objects.filter(
                user=request.user,
                tenant_id=request.tenant_id
            ).first()
            
            if tenant_user:
                return tenant_user.role in ['admin', 'recruiter']
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Check if document belongs to tenant
        if hasattr(obj, 'candidate') and hasattr(obj.candidate, 'tenant_id'):
            return str(obj.candidate.tenant_id) == str(request.tenant_id)
        return True

class AdminPermission(BasePermission):
    """
    Permission class for admin-only operations.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request, 'tenant_id'):
            return False
        
        tenant_user = TenantUser.objects.filter(
            user=request.user,
            tenant_id=request.tenant_id
        ).first()
        
        return tenant_user and tenant_user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)