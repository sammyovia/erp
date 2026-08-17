from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import ComplianceDocument
from .serializers import DocumentSerializer, DocumentCreateSerializer, DocumentVersionSerializer
from apps.core.permissions import TenantPermission, DocumentPermission
from apps.audit.services import AuditService

class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for ComplianceDocument operations"""
    
    permission_classes = [IsAuthenticated, TenantPermission, DocumentPermission]
    serializer_class = DocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'status', 'is_current']
    search_fields = ['candidate__name', 'candidate__email']
    ordering_fields = ['created_at', 'expiry_date', 'issue_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return documents for the current tenant only"""
        return ComplianceDocument.objects.filter(
            candidate__tenant_id=self.request.tenant_id
        ).select_related('candidate', 'candidate__tenant')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentCreateSerializer
        elif self.action == 'versions':
            return DocumentVersionSerializer
        return DocumentSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new document with audit trail"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify candidate belongs to tenant
        from apps.candidates.models import Candidate
        candidate_id = request.data.get('candidate')
        if candidate_id:
            try:
                candidate = Candidate.objects.get(
                    id=candidate_id,
                    tenant_id=request.tenant_id
                )
            except Candidate.DoesNotExist:
                return Response(
                    {'error': 'Candidate does not exist or belongs to another tenant'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        document = serializer.save()
        
        # Audit trail
        AuditService.log_create(
            tenant_id=request.tenant_id,
            actor_id=request.user.id,
            record_type='compliance_document',
            record_id=str(document.id),
            data=serializer.validated_data
        )
        
        return Response(
            DocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get all versions of a document"""
        document = self.get_object()
        versions = ComplianceDocument.objects.filter(
            candidate=document.candidate,
            document_type=document.document_type
        ).order_by('-version')
        
        serializer = DocumentVersionSerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get documents expiring within 30 days"""
        thirty_days_later = timezone.now().date() + timezone.timedelta(days=30)
        
        documents = self.get_queryset().filter(
            expiry_date__lte=thirty_days_later,
            expiry_date__gt=timezone.now().date(),
            is_current=True
        ).select_related('candidate')
        
        serializer = DocumentSerializer(documents, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })