from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend
from .models import Candidate
from .serializers import CandidateSerializer, CandidateListSerializer, CandidateCreateSerializer
from apps.documents.models import ComplianceDocument
from apps.documents.serializers import DocumentCreateSerializer, DocumentSerializer
from apps.audit.services import AuditService
from apps.core.permissions import TenantPermission, CandidatePermission

class CandidateViewSet(viewsets.ModelViewSet):
    """ViewSet for Candidate operations"""
    
    permission_classes = [IsAuthenticated, TenantPermission, CandidatePermission]
    serializer_class = CandidateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role_applied_for', 'is_active']
    search_fields = ['name', 'email', 'role_applied_for']
    ordering_fields = ['name', 'email', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return candidates for the current tenant only"""
        return Candidate.objects.filter(
            tenant_id=self.request.tenant_id,
            is_active=True
        ).prefetch_related('documents')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CandidateListSerializer
        elif self.action == 'create':
            return CandidateCreateSerializer
        return CandidateSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new candidate with audit trail"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        candidate = serializer.save(tenant_id=request.tenant_id)
        
        # Audit trail
        AuditService.log_create(
            tenant_id=request.tenant_id,
            actor_id=request.user.id,
            record_type='candidate',
            record_id=str(candidate.id),
            data=serializer.validated_data
        )
        
        return Response(
            CandidateSerializer(candidate).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """Add a document to a candidate"""
        candidate = self.get_object()
        
        # Verify candidate belongs to tenant
        if str(candidate.tenant_id) != str(request.tenant_id):
            return Response(
                {'error': 'Candidate does not belong to your tenant'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Versioning: if document exists, create new version
            existing_doc = ComplianceDocument.objects.filter(
                candidate=candidate,
                document_type=serializer.validated_data['document_type'],
                is_current=True
            ).first()
            
            if existing_doc:
                existing_doc.is_current = False
                existing_doc.save()
            
            new_doc = ComplianceDocument.objects.create(
                candidate=candidate,
                **serializer.validated_data,
                version=(existing_doc.version + 1) if existing_doc else 1,
                superseded_by=existing_doc,
                is_current=True
            )
            
            # Audit
            AuditService.log_create(
                tenant_id=request.tenant_id,
                actor_id=request.user.id,
                record_type='compliance_document',
                record_id=str(new_doc.id),
                data=serializer.validated_data,
                previous_version=str(existing_doc.id) if existing_doc else None
            )
        
        return Response(
            DocumentSerializer(new_doc).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def expiring_documents(self, request):
        """Get documents expiring within 30 days"""
        thirty_days_later = timezone.now().date() + timedelta(days=30)
        
        candidates = self.get_queryset()
        expiring_documents = ComplianceDocument.objects.filter(
            candidate__in=candidates,
            expiry_date__lte=thirty_days_later,
            expiry_date__gt=timezone.now().date(),
            is_current=True
        ).select_related('candidate')
        
        result = []
        for doc in expiring_documents:
            result.append({
                'candidate_id': str(doc.candidate.id),
                'candidate_name': doc.candidate.name,
                'candidate_email': doc.candidate.email,
                'document_type': doc.get_document_type_display(),
                'expiry_date': doc.expiry_date,
                'days_until_expiry': (doc.expiry_date - timezone.now().date()).days,
                'status': doc.status,
                'document_id': str(doc.id)
            })
        
        result.sort(key=lambda x: x['days_until_expiry'])
        
        return Response({
            'count': len(result),
            'results': result
        })