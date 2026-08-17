from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Tenant
from apps.candidates.models import Candidate
import uuid

class AIExtraction(models.Model):
    """Model for storing AI extraction results"""
    
    STATUS_CHOICES = [
        ('pending_confirmation', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ai_extractions')
    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_extractions')
    raw_text = models.TextField(help_text="Raw text extracted from CV")
    extracted_data = models.JSONField(default=dict, help_text="Structured data extracted by AI")
    model_used = models.CharField(max_length=100, default='mock', help_text="AI model used for extraction")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending_confirmation')
    confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence score (0-1)")
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_extractions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_extractions'
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['candidate']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AI Extraction {self.id} - {self.status}"
    
    def get_extracted_fields(self):
        """Get list of extracted field names"""
        return list(self.extracted_data.keys()) if self.extracted_data else []
    
    def is_pending(self):
        """Check if extraction is pending confirmation"""
        return self.status == 'pending_confirmation'
    
    def confirm(self, user, edited_data=None):
        """Confirm the extraction"""
        if edited_data:
            self.extracted_data = edited_data
        self.status = 'confirmed'
        self.confirmed_at = models.DateTimeField(auto_now_add=True)
        self.confirmed_by = user
        self.save()
    
    def reject(self, user):
        """Reject the extraction"""
        self.status = 'rejected'
        self.confirmed_at = models.DateTimeField(auto_now_add=True)
        self.confirmed_by = user
        self.save()

class AIAuditLog(models.Model):
    """Model for AI audit logs"""
    
    ACTION_CHOICES = [
        ('extraction', 'Extraction'),
        ('confirmation', 'Confirmation'),
        ('rejection', 'Rejection'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='ai_audit_logs')
    extraction = models.ForeignKey(AIExtraction, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    model_used = models.CharField(max_length=100)
    input_hash = models.CharField(max_length=64, help_text="Hash of input text")
    output_hash = models.CharField(max_length=64, help_text="Hash of extracted data")
    metadata = models.JSONField(default=dict, help_text="Additional metadata")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_audit_logs'
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['extraction']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AI Audit {self.id} - {self.action}"