from django.db import models
from apps.tenants.models import Tenant
import uuid

class AuditLog(models.Model):
    """
    Immutable audit log model.
    Records are never updated or deleted.
    """
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('READ', 'Read'),
        ('VERIFY', 'Verify'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='audit_logs',
        db_index=True
    )
    actor_id = models.IntegerField(db_index=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, db_index=True)
    record_type = models.CharField(max_length=50, db_index=True)
    record_id = models.CharField(max_length=36, db_index=True)
    before_hash = models.CharField(max_length=64, blank=True, null=True)
    after_hash = models.CharField(max_length=64, blank=True, null=True)
    data = models.JSONField(default=dict)
    previous_version = models.CharField(max_length=36, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['record_type', 'record_id']),
            models.Index(fields=['action']),
            models.Index(fields=['actor_id']),
            models.Index(fields=['tenant', 'action']),
        ]
    
    def __str__(self):
        return f"Audit {self.action} - {self.record_type} - {self.record_id} at {self.created_at}"
    
    def save(self, *args, **kwargs):
        """Override save to enforce immutability - allow creation, prevent updates"""
        # Check if this is an existing record being updated
        if self.pk and not kwargs.get('force_insert', False):
            # If updating, raise an error to prevent changes
            raise ValueError("Audit logs are immutable and cannot be updated")
        # If it's a new record, allow creation
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete to enforce immutability"""
        raise ValueError("Audit logs are immutable and cannot be deleted")
    
    @classmethod
    def get_for_record(cls, record_type, record_id, tenant_id=None):
        """Get all audit logs for a specific record"""
        queryset = cls.objects.filter(record_type=record_type, record_id=record_id)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        return queryset.order_by('created_at')
    
    @classmethod
    def get_recent(cls, tenant_id, days=7):
        """Get recent audit logs for a tenant"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=cutoff
        ).order_by('-created_at')