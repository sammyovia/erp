from rest_framework import serializers
from django.utils import timezone
from .models import ComplianceDocument

class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for ComplianceDocument"""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceDocument
        fields = [
            'id',
            'candidate',
            'candidate_name',
            'document_type',
            'document_type_display',
            'issue_date',
            'expiry_date',
            'status',
            'status_display',
            'file_url',
            'version',
            'is_current',
            'verified_at',
            'created_at',
            'updated_at',
            'days_until_expiry'
        ]
        read_only_fields = ['id', 'version', 'is_current', 'verified_at', 'created_at', 'updated_at']
    
    def get_days_until_expiry(self, obj):
        if obj.expiry_date:
            delta = obj.expiry_date - timezone.now().date()
            return delta.days
        return None

class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new documents"""
    
    class Meta:
        model = ComplianceDocument
        fields = [
            'document_type',
            'issue_date',
            'expiry_date',
            'status',
            'file_url',
        ]
    
    def validate(self, data):
        if data.get('issue_date') and data.get('expiry_date'):
            if data['issue_date'] > data['expiry_date']:
                raise serializers.ValidationError("Issue date must be before expiry date")
        return data

class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document versions"""
    
    class Meta:
        model = ComplianceDocument
        fields = [
            'id',
            'version',
            'is_current',
            'status',
            'verified_at',
            'created_at',
        ]