from django.db import models
from apps.tenants.models import Tenant
import uuid

class Candidate(models.Model):
    """Candidate model for tenant-based candidate management"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    role_applied_for = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'candidates'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.tenant.name}"
    
    @property
    def document_count(self):
        """Get count of current documents"""
        return self.documents.filter(is_current=True).count()