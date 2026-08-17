from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Tenant, TenantUser

class TenantSerializer(serializers.ModelSerializer):
    """Base serializer for Tenant model"""
    
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 
            'name', 
            'slug', 
            'is_active',
            'user_count',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        """Get count of users in this tenant"""
        return obj.tenantuser_set.count()
    
    def validate_slug(self, value):
        """Validate slug is unique"""
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("A tenant with this slug already exists")
        return value

class TenantDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Tenant model with users"""
    
    user_count = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 
            'name', 
            'slug', 
            'is_active',
            'user_count',
            'users',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        return obj.tenantuser_set.count()
    
    def get_users(self, obj):
        """Get all users in this tenant"""
        tenant_users = obj.tenantuser_set.select_related('user')
        return TenantUserSerializer(tenant_users, many=True).data

class TenantUserSerializer(serializers.ModelSerializer):
    """Serializer for TenantUser model"""
    
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)
    
    class Meta:
        model = TenantUser
        fields = [
            'id',
            'user_id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'tenant',
            'tenant_name',
            'tenant_slug',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

class TenantUserCreateSerializer(serializers.Serializer):
    """Serializer for creating a tenant user"""
    
    username = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(choices=['admin', 'recruiter', 'viewer'], default='viewer')
    
    def validate_username(self, value):
        """Check if user exists"""
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError(f"User '{value}' does not exist")
        return value

class TenantSwitchSerializer(serializers.Serializer):
    """Serializer for switching tenants"""
    
    tenant_id = serializers.UUIDField(required=True)
    
    def validate_tenant_id(self, value):
        """Validate tenant exists"""
        if not Tenant.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Tenant not found or inactive")
        return value

class TenantStatsSerializer(serializers.Serializer):
    """Serializer for tenant statistics"""
    
    tenant_id = serializers.UUIDField()
    tenant_name = serializers.CharField()
    user_count = serializers.IntegerField()
    candidate_count = serializers.IntegerField()
    document_count = serializers.IntegerField()
    audit_log_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()