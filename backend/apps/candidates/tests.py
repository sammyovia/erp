from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import Candidate
from apps.tenants.models import Tenant, TenantUser

class CandidateModelTest(TestCase):
    """Test Candidate model"""
    
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
    
    def test_candidate_creation(self):
        """Test creating a candidate"""
        self.assertEqual(self.candidate.name, "John Doe")
        self.assertEqual(self.candidate.email, "john@example.com")
        self.assertEqual(self.candidate.role_applied_for, "Developer")
        self.assertTrue(self.candidate.is_active)
    
    def test_candidate_str(self):
        """Test candidate string representation"""
        expected = f"John Doe - Test Tenant"
        self.assertEqual(str(self.candidate), expected)
    
    def test_document_count(self):
        """Test document count property"""
        self.assertEqual(self.candidate.document_count, 0)

class CandidateAPITest(APITestCase):
    """Test Candidate API endpoints"""
    
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
    
    def test_list_candidates(self):
        """Test listing candidates"""
        url = reverse('candidate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_candidate(self):
        """Test creating a candidate"""
        url = reverse('candidate-list')
        data = {
            'name': 'New Candidate',
            'email': 'new@example.com',
            'role_applied_for': 'Manager'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Candidate')
    
    def test_retrieve_candidate(self):
        """Test retrieving a candidate"""
        url = reverse('candidate-detail', args=[self.candidate.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Jane Smith')
    
    def test_update_candidate(self):
        """Test updating a candidate"""
        url = reverse('candidate-detail', args=[self.candidate.id])
        data = {'name': 'Updated Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')
    
    def test_delete_candidate(self):
        """Test deleting a candidate"""
        url = reverse('candidate-detail', args=[self.candidate.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify candidate is inactive
        candidate = Candidate.objects.get(id=self.candidate.id)
        self.assertFalse(candidate.is_active)