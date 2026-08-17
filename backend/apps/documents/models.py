from django.db import models
from apps.candidates.models import Candidate
import uuid

class ComplianceDocument(models.Model):
    """Compliance document model with versioning"""
    
    DOCUMENT_TYPES = [
        ('right_to_work', 'Right to Work'),
        ('dbs', 'DBS Check'),
        ('certification', 'Professional Certification'),
        ('qualification', 'Qualification'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_url = models.URLField(blank=True, null=True)
    version = models.IntegerField(default=1)
    is_current = models.BooleanField(default=True)
    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'compliance_documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate', 'is_current']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.candidate.name} (v{self.version})"