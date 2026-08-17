from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from .models import Tenant, TenantUser
from .serializers import (
    TenantSerializer, 
    TenantDetailSerializer,
    TenantUserSerializer,
    TenantUserCreateSerializer,
    TenantSwitchSerializer
)
from apps.core.permissions import TenantPermission, AdminPermission

class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tenant operations
    Only admins can create/update tenants
    """
    
    permission_classes = [IsAuthenticated, TenantPermission, AdminPermission]
    serializer_class = TenantSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Return tenants the user has access to"""
        return Tenant.objects.filter(
            tenantuser_set__user=self.request.user,
            is_active=True
        )
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TenantDetailSerializer
        return TenantSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new tenant"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            tenant = serializer.save()
            
            # Add current user as admin of the new tenant
            TenantUser.objects.create(
                user=request.user,
                tenant=tenant,
                role='admin'
            )
        
        return Response(
            TenantDetailSerializer(tenant).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get all users for a specific tenant"""
        tenant = self.get_object()
        tenant_users = TenantUser.objects.filter(
            tenant=tenant
        ).select_related('user', 'tenant')
        
        page = self.paginate_queryset(tenant_users)
        if page is not None:
            serializer = TenantUserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TenantUserSerializer(tenant_users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_user(self, request, pk=None):
        """Add a user to a tenant"""
        tenant = self.get_object()
        serializer = TenantUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user exists
        username = serializer.validated_data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {
                    'type': 'user_not_found',
                    'title': 'User Not Found',
                    'status': 404,
                    'detail': f'User with username "{username}" not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user already has access to this tenant
        if TenantUser.objects.filter(user=user, tenant=tenant).exists():
            return Response(
                {
                    'type': 'user_already_exists',
                    'title': 'User Already Exists',
                    'status': 400,
                    'detail': f'User "{username}" already has access to this tenant'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user to tenant
        tenant_user = TenantUser.objects.create(
            user=user,
            tenant=tenant,
            role=serializer.validated_data.get('role', 'viewer')
        )
        
        return Response(
            TenantUserSerializer(tenant_user).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def remove_user(self, request, pk=None):
        """Remove a user from a tenant"""
        tenant = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {
                    'type': 'missing_user_id',
                    'title': 'Missing User ID',
                    'status': 400,
                    'detail': 'user_id is required'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't allow removing the last admin
        admin_count = TenantUser.objects.filter(
            tenant=tenant,
            role='admin'
        ).count()
        
        try:
            tenant_user = TenantUser.objects.get(
                tenant=tenant,
                user_id=user_id
            )
        except TenantUser.DoesNotExist:
            return Response(
                {
                    'type': 'user_not_found',
                    'title': 'User Not Found',
                    'status': 404,
                    'detail': 'User not found in this tenant'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent removing the last admin
        if tenant_user.role == 'admin' and admin_count <= 1:
            return Response(
                {
                    'type': 'last_admin',
                    'title': 'Cannot Remove Last Admin',
                    'status': 400,
                    'detail': 'Cannot remove the last admin of the tenant'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Don't allow removing yourself
        if tenant_user.user_id == request.user.id:
            return Response(
                {
                    'type': 'self_removal',
                    'title': 'Cannot Remove Yourself',
                    'status': 400,
                    'detail': 'You cannot remove yourself from the tenant'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tenant_user.delete()
        
        return Response(
            {'message': f'User removed from tenant "{tenant.name}" successfully'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['put'])
    def update_user_role(self, request, pk=None):
        """Update a user's role in a tenant"""
        tenant = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role')
        
        if not user_id or not role:
            return Response(
                {
                    'type': 'missing_fields',
                    'title': 'Missing Fields',
                    'status': 400,
                    'detail': 'user_id and role are required'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if role not in ['admin', 'recruiter', 'viewer']:
            return Response(
                {
                    'type': 'invalid_role',
                    'title': 'Invalid Role',
                    'status': 400,
                    'detail': 'Role must be one of: admin, recruiter, viewer'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tenant_user = TenantUser.objects.get(
                tenant=tenant,
                user_id=user_id
            )
        except TenantUser.DoesNotExist:
            return Response(
                {
                    'type': 'user_not_found',
                    'title': 'User Not Found',
                    'status': 404,
                    'detail': 'User not found in this tenant'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prevent changing role of the last admin
        if role != 'admin' and tenant_user.role == 'admin':
            admin_count = TenantUser.objects.filter(
                tenant=tenant,
                role='admin'
            ).count()
            if admin_count <= 1:
                return Response(
                    {
                        'type': 'last_admin',
                        'title': 'Cannot Demote Last Admin',
                        'status': 400,
                        'detail': 'Cannot demote the last admin of the tenant'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        tenant_user.role = role
        tenant_user.save()
        
        return Response(
            TenantUserSerializer(tenant_user).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def switch(self, request):
        """Switch to a different tenant"""
        serializer = TenantSwitchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        tenant_id = serializer.validated_data['tenant_id']
        
        # Verify user has access to this tenant
        try:
            tenant_user = TenantUser.objects.get(
                user=request.user,
                tenant_id=tenant_id
            )
        except TenantUser.DoesNotExist:
            return Response(
                {
                    'type': 'no_access',
                    'title': 'No Access',
                    'status': 403,
                    'detail': 'You do not have access to this tenant'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate new token with updated tenant
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(request.user)
        refresh.access_token['tenant_id'] = str(tenant_user.tenant.id)
        refresh.access_token['role'] = tenant_user.role
        refresh.access_token['tenant_slug'] = tenant_user.tenant.slug
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'tenant': {
                'id': str(tenant_user.tenant.id),
                'name': tenant_user.tenant.name,
                'slug': tenant_user.tenant.slug,
                'role': tenant_user.role
            },
            'message': f'Switched to tenant "{tenant_user.tenant.name}"'
        })
    
    @action(detail=True, methods=['get'])
    def my_tenants(self, request):
        """Get all tenants for the current user"""
        tenant_users = TenantUser.objects.filter(
            user=request.user
        ).select_related('tenant')
        
        tenants = [tu.tenant for tu in tenant_users]
        serializer = TenantSerializer(tenants, many=True)
        return Response(serializer.data)