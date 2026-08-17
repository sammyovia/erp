from rest_framework import serializers
from .models import AIExtraction, AIAuditLog

class AIExtractionSerializer(serializers.ModelSerializer):
    """Serializer for AIExtraction model"""
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    candidate_name = serializers.CharField(source='candidate.name', read_only=True, default=None)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True, default=None)
    confirmed_by_username = serializers.CharField(source='confirmed_by.username', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AIExtraction
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'candidate',
            'candidate_name',
            'candidate_email',
            'extracted_data',
            'model_used',
            'status',
            'status_display',
            'confidence_score',
            'confirmed_at',
            'confirmed_by',
            'confirmed_by_username',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AIExtractionCreateSerializer(serializers.Serializer):
    """Serializer for creating AI extraction"""
    
    candidate_id = serializers.UUIDField(required=False, allow_null=True)
    file = serializers.FileField(required=True)
    
    def validate_file(self, value):
        """Validate uploaded file"""
        import os
        allowed_extensions = ['.pdf', '.txt', '.text']
        ext = os.path.splitext(value.name)[1].lower()
        
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f'Unsupported file type. Allowed types: {", ".join(allowed_extensions)}'
            )
        
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError('File size exceeds 10MB limit')
        
        return value

class AIExtractionConfirmSerializer(serializers.Serializer):
    """Serializer for confirming/rejecting AI extraction"""
    
    action = serializers.ChoiceField(choices=['confirm', 'reject'])
    edited_data = serializers.JSONField(required=False)
    
    def validate(self, data):
        if data['action'] == 'confirm' and not data.get('edited_data'):
            raise serializers.ValidationError(
                "edited_data is required when confirming extraction"
            )
        return data

class AIAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AIAuditLog model"""
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    
    class Meta:
        model = AIAuditLog
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'extraction',
            'action',
            'actor',
            'actor_username',
            'model_used',
            'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']