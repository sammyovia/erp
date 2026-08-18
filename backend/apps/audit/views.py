from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from .serializers import (
    AuditLogSerializer, 
    AuditLogListSerializer,
    AuditStatsSerializer
)
from apps.core.permissions import TenantPermission, AdminPermission

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs
    Only admins can view audit logs
    """
    
    permission_classes = [IsAuthenticated, TenantPermission, AdminPermission]
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'record_type', 'actor_id']
    search_fields = ['record_id', 'data']
    ordering_fields = ['created_at', 'action', 'record_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return audit logs for the current tenant only"""
        return AuditLog.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related('tenant')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer
    
    @action(detail=False, methods=['get'])
    def by_record(self, request):
        """Get audit logs for a specific record"""
        record_type = request.query_params.get('record_type')
        record_id = request.query_params.get('record_id')
        
        if not record_type or not record_id:
            return Response(
                {
                    'type': 'missing_parameters',
                    'title': 'Missing Parameters',
                    'status': 400,
                    'detail': 'record_type and record_id are required'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = self.get_queryset().filter(
            record_type=record_type,
            record_id=record_id
        )
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_actor(self, request):
        """Get audit logs for a specific actor"""
        actor_id = request.query_params.get('actor_id')
        
        if not actor_id:
            return Response(
                {
                    'type': 'missing_parameter',
                    'title': 'Missing Parameter',
                    'status': 400,
                    'detail': 'actor_id is required'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = self.get_queryset().filter(actor_id=actor_id)
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent audit logs"""
        days = int(request.query_params.get('days', 7))
        cutoff_date = timezone.now() - timedelta(days=days)
        
        logs = self.get_queryset().filter(created_at__gte=cutoff_date)
        
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of audit logs"""
        queryset = self.get_queryset()
        
        # Count by action
        action_counts = queryset.values('action').annotate(count=Count('id'))
        
        # Count by record type
        record_type_counts = queryset.values('record_type').annotate(count=Count('id'))
        
        # Count by day (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        from django.db import connection
        daily_counts = queryset.filter(
            created_at__gte=thirty_days_ago
        ).extra(
            {'date': "date(created_at)"}
        ).values('date').annotate(count=Count('id')).order_by('-date')
        
        return Response({
            'total_logs': queryset.count(),
            'action_breakdown': action_counts,
            'record_type_breakdown': record_type_counts,
            'daily_breakdown': daily_counts,
            'time_range': {
                'start': thirty_days_ago,
                'end': timezone.now()
            }
        })

class AuditStatsView(APIView):
    """
    View for audit statistics
    """
    permission_classes = [IsAuthenticated, TenantPermission, AdminPermission]
    
    def get(self, request):
        """Get audit statistics"""
        tenant_id = request.tenant_id
        queryset = AuditLog.objects.filter(tenant_id=tenant_id)
        
        # Total logs
        total_logs = queryset.count()
        
        # Logs by action
        action_stats = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Logs by record type
        record_type_stats = queryset.values('record_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Logs by day (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        daily_stats = queryset.filter(
            created_at__gte=seven_days_ago
        ).extra(
            {'date': "date(created_at)"}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Most active users
        user_stats = queryset.values('actor_id').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Get usernames for most active users
        from django.contrib.auth.models import User
        user_ids = [stat['actor_id'] for stat in user_stats]
        users = User.objects.filter(id__in=user_ids)
        user_map = {str(user.id): user.username for user in users}
        
        user_stats_with_names = []
        for stat in user_stats:
            user_stats_with_names.append({
                'actor_id': stat['actor_id'],
                'username': user_map.get(str(stat['actor_id']), 'Unknown'),
                'count': stat['count']
            })
        
        return Response({
            'total_logs': total_logs,
            'action_breakdown': action_stats,
            'record_type_breakdown': record_type_stats,
            'daily_breakdown': daily_stats,
            'most_active_users': user_stats_with_names,
            'period': {
                'start': seven_days_ago,
                'end': timezone.now()
            }
        })