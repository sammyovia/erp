from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import ComplianceDocument
from apps.tenants.models import Tenant, TenantUser
from apps.candidates.models import Candidate

class DocumentModelTest(TestCase):
    """Test Document model"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
        self.candidate = Candidate.objects.create(
            tenant=self.tenant,
            name="John Doe",
            email="john@example.com",
            role_applied_for="Developer"
        )
        self.document = ComplianceDocument.objects.create(
            candidate=self.candidate,
            document_type='right_to_work',
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            status='pending'
        )
    
    def test_document_creation(self):
        """Test creating a document"""
        self.assertEqual(self.document.document_type, 'right_to_work')
        self.assertEqual(self.document.status, 'pending')
        self.assertEqual(self.document.version, 1)
        self.assertTrue(self.document.is_current)

class DocumentAPITest(APITestCase):
    """Test Document API endpoints"""
    
    def setUp(self):
        # Create tenant
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant"
        )
        
        # Create user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        
        # Add user to tenant
        TenantUser.objects.create(
            user=self.user,
            tenant=self.tenant,
            role='admin'
        )
        
        # Setup client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
        
        # Create a candidate
        self.candidate = Candidate.objects.create(
            tenant=self.tenant,
            name="Jane Smith",
            email="jane@example.com",
            role_applied_for="Designer"
        )
        
        # Create a document
        self.document = ComplianceDocument.objects.create(
            candidate=self.candidate,
            document_type='certification',
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=365),
            status='pending'
        )
    
    def test_list_documents(self):
        """Test listing documents"""
        url = reverse('document-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_document(self):
        """Test creating a document"""
        url = reverse('document-list')
        data = {
            'candidate': str(self.candidate.id),
            'document_type': 'dbs',
            'issue_date': '2024-01-01',
            'expiry_date': '2025-01-01',
            'status': 'pending'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['document_type'], 'dbs')
    
    def test_document_versions(self):
        """Test getting document versions"""
        url = reverse('document-versions', args=[self.document.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_expiring_soon(self):
        """Test expiring soon endpoint"""
        url = reverse('document-expiring-soon')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)