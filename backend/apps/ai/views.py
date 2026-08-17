import json
import hashlib
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from .services import LLMService
from .models import AIExtraction, AIAuditLog
from .serializers import (
    AIExtractionSerializer,
    AIExtractionCreateSerializer,
    AIExtractionConfirmSerializer,
    AIAuditLogSerializer
)
from apps.audit.services import AuditService
from apps.candidates.models import Candidate
from apps.candidates.serializers import CandidateSerializer

class CVAnalysisView(APIView):
    """Upload and analyze CV"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        tenant_id = request.tenant_id
        
        # Validate request
        serializer = AIExtractionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        candidate_id = serializer.validated_data.get('candidate_id')
        
        # Verify candidate if provided
        candidate = None
        if candidate_id:
            try:
                candidate = Candidate.objects.get(id=candidate_id, tenant_id=tenant_id)
            except Candidate.DoesNotExist:
                return Response(
                    {'error': 'Candidate not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Extract text from file
        try:
            if file.name.endswith('.pdf'):
                import PyPDF2
                from io import BytesIO
                pdf_file = BytesIO(file.read())
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text() + '\n'
            else:
                text = file.read().decode('utf-8')
        except Exception as e:
            return Response(
                {'error': f'Failed to parse file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract data using LLM
        llm_service = LLMService()
        result = llm_service.extract_cv_data(text)
        
        if not result.get('success'):
            return Response(
                {'error': result.get('error', 'Extraction failed')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save extraction
        with transaction.atomic():
            extraction = AIExtraction.objects.create(
                tenant_id=tenant_id,
                candidate=candidate,
                raw_text=text[:10000],
                extracted_data=result['data'],
                model_used=result.get('model', 'unknown'),
                status='pending_confirmation'
            )
            
            # Create audit log
            AIAuditLog.objects.create(
                tenant_id=tenant_id,
                extraction=extraction,
                action='extraction',
                actor=request.user,
                model_used=result.get('model', 'unknown'),
                input_hash=hashlib.sha256(text.encode()).hexdigest(),
                output_hash=hashlib.sha256(json.dumps(result['data'], sort_keys=True).encode()).hexdigest(),
                metadata={'file_name': file.name, 'file_size': file.size}
            )
            
            # Regular audit
            AuditService.log_create(
                tenant_id=tenant_id,
                actor_id=request.user.id,
                record_type='ai_extraction',
                record_id=str(extraction.id),
                data={'model': result.get('model'), 'status': 'pending_confirmation'}
            )
        
        return Response(AIExtractionSerializer(extraction).data, status=status.HTTP_200_OK)

class AIExtractionConfirmView(APIView):
    """Confirm or reject AI extraction"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, extraction_id):
        tenant_id = request.tenant_id
        
        # Validate request
        serializer = AIExtractionConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get extraction
        try:
            extraction = AIExtraction.objects.get(id=extraction_id, tenant_id=tenant_id)
        except AIExtraction.DoesNotExist:
            return Response({'error': 'Extraction not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if extraction.status != 'pending_confirmation':
            return Response(
                {'error': f'Extraction already {extraction.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = serializer.validated_data['action']
        
        if action == 'confirm':
            return self._confirm_extraction(request, extraction, serializer.validated_data.get('edited_data'))
        else:
            return self._reject_extraction(request, extraction)
    
    def _confirm_extraction(self, request, extraction, edited_data):
        data = edited_data or extraction.extracted_data
        
        if not data.get('full_name'):
            return Response(
                {'error': 'Full name is required to create a candidate'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create candidate
            candidate = Candidate.objects.create(
                tenant_id=request.tenant_id,
                name=data.get('full_name', ''),
                email=data.get('email', ''),
                role_applied_for=data.get('role', 'Developer'),
            )
            
            # Update extraction
            extraction.candidate = candidate
            extraction.extracted_data = data
            extraction.status = 'confirmed'
            extraction.confirmed_at = timezone.now()
            extraction.confirmed_by = request.user
            extraction.save()
            
            # Create audit log
            AIAuditLog.objects.create(
                tenant_id=request.tenant_id,
                extraction=extraction,
                action='confirmation',
                actor=request.user,
                model_used=extraction.model_used,
                input_hash=hashlib.sha256(extraction.raw_text.encode()).hexdigest(),
                output_hash=hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
                metadata={'candidate_id': str(candidate.id), 'edited': bool(edited_data)}
            )
            
            # Regular audit
            AuditService.log_create(
                tenant_id=request.tenant_id,
                actor_id=request.user.id,
                record_type='candidate',
                record_id=str(candidate.id),
                data=data
            )
        
        return Response({
            'candidate': CandidateSerializer(candidate).data,
            'status': 'confirmed',
            'message': 'Candidate created successfully'
        })
    
    def _reject_extraction(self, request, extraction):
        with transaction.atomic():
            extraction.status = 'rejected'
            extraction.confirmed_at = timezone.now()
            extraction.confirmed_by = request.user
            extraction.save()
            
            AIAuditLog.objects.create(
                tenant_id=request.tenant_id,
                extraction=extraction,
                action='rejection',
                actor=request.user,
                model_used=extraction.model_used,
                input_hash=hashlib.sha256(extraction.raw_text.encode()).hexdigest(),
                output_hash=hashlib.sha256(json.dumps(extraction.extracted_data, sort_keys=True).encode()).hexdigest(),
                metadata={'reason': 'User rejected extraction'}
            )
        
        return Response({
            'status': 'rejected',
            'message': 'Extraction rejected. Candidate can be created manually.'
        })

class AIExtractionListView(APIView):
    """List AI extractions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        tenant_id = request.tenant_id
        
        extractions = AIExtraction.objects.filter(tenant_id=tenant_id)
        
        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            extractions = extractions.filter(status=status_filter)
        
        extractions = extractions.order_by('-created_at')
        
        # Simple pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total = extractions.count()
        
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'results': AIExtractionSerializer(extractions[start:end], many=True).data
        })