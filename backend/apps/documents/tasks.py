from celery import shared_task
from django.utils import timezone
from apps.documents.models import ComplianceDocument
from apps.audit.services import AuditService

@shared_task
def verify_document(document_id):
    """Async verification task with idempotency"""
    try:
        document = ComplianceDocument.objects.get(id=document_id)
        
        # Idempotency check
        if document.status != 'pending':
            return {'status': 'already_processed', 'document_id': str(document_id)}
        
        # Simulate verification process
        # In production, this would call an external service
        import random
        verification_result = random.random() > 0.2  # 80% pass rate
        
        if verification_result:
            document.status = 'verified'
            document.verified_at = timezone.now()
        else:
            document.status = 'failed'
        
        document.save()
        
        # Audit
        AuditService.log_create(
            tenant_id=document.candidate.tenant_id,
            actor_id=None,  # System actor
            record_type='document_verification',
            record_id=str(document.id),
            data={
                'status': document.status,
                'verified_at': document.verified_at.isoformat() if document.verified_at else None
            }
        )
        
        return {
            'status': 'completed',
            'document_id': str(document.id),
            'verification_result': document.status
        }
    
    except ComplianceDocument.DoesNotExist:
        return {'status': 'error', 'error': 'Document not found'}