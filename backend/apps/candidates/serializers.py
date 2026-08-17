from rest_framework import serializers
from .models import Candidate
from apps.documents.serializers import DocumentSerializer

class CandidateSerializer(serializers.ModelSerializer):
    """Full serializer for Candidate model"""
    
    document_count = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = Candidate
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'name',
            'email',
            'role_applied_for',
            'document_count',
            'documents',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_document_count(self, obj):
        return obj.documents.filter(is_current=True).count()
    
    def get_documents(self, obj):
        from apps.documents.serializers import DocumentSerializer
        documents = obj.documents.filter(is_current=True)
        return DocumentSerializer(documents, many=True).data
    
    def validate_email(self, value):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Invalid email format")
        return value

class CandidateListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list view"""
    
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = [
            'id',
            'name',
            'email',
            'role_applied_for',
            'document_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_document_count(self, obj):
        return obj.documents.filter(is_current=True).count()

class CandidateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating candidates"""
    
    class Meta:
        model = Candidate
        fields = ['name', 'email', 'role_applied_for']
    
    def validate_email(self, value):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Invalid email format")
        return value