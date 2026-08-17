from django.db import models
from django.contrib.auth.models import User
import uuid

class Tenant(models.Model):
    """Tenant model for multi-tenant isolation"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenants'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def user_count(self):
        """Get count of users in this tenant"""
        return self.tenantuser_set.count()
    
    @property
    def candidate_count(self):
        """Get count of candidates in this tenant"""
        from apps.candidates.models import Candidate
        return Candidate.objects.filter(tenant=self).count()

class TenantUser(models.Model):
    """Model linking users to tenants with roles"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('recruiter', 'Recruiter'),
        ('viewer', 'Viewer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='tenantuser_set'
    )
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='tenantuser_set'
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenant_users'
        unique_together = ['user', 'tenant']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'tenant']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.tenant.name} ({self.role})"
    
    def is_admin(self):
        """Check if user is admin of this tenant"""
        return self.role == 'admin'
    
    def is_recruiter(self):
        """Check if user is recruiter of this tenant"""
        return self.role == 'recruiter' or self.role == 'admin'