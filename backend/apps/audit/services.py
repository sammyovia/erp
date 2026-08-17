from django.db import models
from django.utils import timezone
import json
import hashlib
from .models import AuditLog

class AuditService:
    @staticmethod
    def log_create(tenant_id, actor_id, record_type, record_id, data, previous_version=None):
        """Log create/update operations"""
        AuditLog.objects.create(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action='CREATE',
            record_type=record_type,
            record_id=record_id,
            before_hash=AuditService._compute_hash({}),
            after_hash=AuditService._compute_hash(data),
            data=json.dumps(data),
            previous_version=previous_version
        )
    
    @staticmethod
    def log_read(tenant_id, actor_id, record_type, record_id, data):
        """Log sensitive read operations"""
        AuditLog.objects.create(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action='READ',
            record_type=record_type,
            record_id=record_id,
            data=json.dumps(data)
        )
    
    @staticmethod
    def _compute_hash(data):
        """Compute hash of data for audit trail"""
        if not data:
            data = {}
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()