from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    """Full serializer for AuditLog model"""
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'actor_id',
            'action',
            'action_display',
            'record_type',
            'record_id',
            'before_hash',
            'after_hash',
            'data',
            'previous_version',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class AuditLogListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list view"""
    
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'action_display',
            'record_type',
            'record_id',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class AuditStatsSerializer(serializers.Serializer):
    """Serializer for audit statistics"""
    
    total_logs = serializers.IntegerField()
    action_breakdown = serializers.DictField()
    record_type_breakdown = serializers.DictField()
    daily_breakdown = serializers.ListField()
    most_active_users = serializers.ListField()
    period = serializers.DictField()