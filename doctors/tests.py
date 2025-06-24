from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token
from .models import Doctor
from .schema import Query, Mutation
import graphene

User = get_user_model()


class DoctorModelTest(TestCase):
    """Test cases for Doctor model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='doctor1',
            email='doctor1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            role='DOCTOR'
        )
        
        self.doctor_data = {
            'user': self.user,
            'specialization': 'Cardiology',
            'phone': '123456789',
            'license_number': 'DOC123456',
            'date_of_birth': '1980-01-01',
            'address': '123 Medical St, City',
            'is_active': True
        }
    
    def test_create_doctor(self):
        """Test creating a new doctor"""
        doctor = Doctor.objects.create(**self.doctor_data)
        self.assertEqual(doctor.user.username, 'doctor1')
        self.assertEqual(doctor.specialization, 'Cardiology')
        self.assertEqual(doctor.license_number, 'DOC123456')
        self.assertTrue(doctor.is_active)
    
    def test_doctor_str_representation(self):
        """Test doctor string representation"""
        doctor = Doctor.objects.create(**self.doctor_data)
        expected = f"Dr. {doctor.user.first_name} {doctor.user.last_name} - {doctor.specialization}"
        self.assertEqual(str(doctor), expected)
    
    def test_doctor_specialization_choices(self):
        """Test doctor specialization choices"""
        doctor = Doctor.objects.create(**self.doctor_data)
        self.assertIn(doctor.specialization, [choice[0] for choice in Doctor.SPECIALIZATION_CHOICES])


class DoctorGraphQLTest(GraphQLTestCase):
    """Test cases for Doctor GraphQL operations"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        # Create doctor user
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            role='DOCTOR'
        )
        
        # Create doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='Cardiology',
            phone='123456789',
            license_number='DOC123456',
            date_of_birth='1980-01-01',
            address='123 Medical St, City',
            is_active=True
        )
    
    def test_create_doctor_mutation(self):
        """Test createDoctor mutation"""
        # First create a user for the doctor
        user_mutation = '''
        mutation {
            createUser(
                username: "doctor2"
                email: "doctor2@example.com"
                password: "testpass123"
                firstName: "Jane"
                lastName: "Smith"
                role: "DOCTOR"
                phone: "987654321"
                dateOfBirth: "1985-05-15"
            ) {
                user {
                    id
                    username
                }
                success
            }
        }
        '''
        user_response = self.query(user_mutation)
        user_id = user_response.json()['data']['createUser']['user']['id']
        
        # Create doctor
        mutation = '''
        mutation {
            createDoctor(
                userId: "%s"
                specialization: "Neurology"
                phone: "555123456"
                licenseNumber: "DOC789012"
                dateOfBirth: "1985-05-15"
                address: "456 Health Ave, City"
                isActive: true
            ) {
                doctor {
                    id
                    specialization
                    licenseNumber
                    isActive
                }
                success
                errors
            }
        }
        ''' % user_id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['createDoctor']
        self.assertTrue(data['success'])
        self.assertEqual(data['doctor']['specialization'], 'Neurology')
        self.assertEqual(data['doctor']['licenseNumber'], 'DOC789012')
    
    def test_all_doctors_query(self):
        """Test allDoctors query"""
        query = '''
        query {
            allDoctors {
                id
                specialization
                licenseNumber
                isActive
                user {
                    id
                    username
                    firstName
                    lastName
                }
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['allDoctors']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['specialization'], 'Cardiology')
        self.assertEqual(data[0]['user']['username'], 'doctor1')
    
    def test_doctor_by_id_query(self):
        """Test doctorById query"""
        query = '''
        query {
            doctorById(id: "%s") {
                id
                specialization
                licenseNumber
                user {
                    username
                    firstName
                    lastName
                }
            }
        }
        ''' % self.doctor.id
        
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['doctorById']
        self.assertEqual(data['specialization'], 'Cardiology')
        self.assertEqual(data['user']['username'], 'doctor1')
    
    def test_doctor_by_id_not_found(self):
        """Test doctorById query with non-existent ID"""
        query = '''
        query {
            doctorById(id: "999") {
                id
                specialization
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['doctorById']
        self.assertIsNone(data)
    
    def test_update_doctor_mutation(self):
        """Test updateDoctor mutation"""
        mutation = '''
        mutation {
            updateDoctor(
                id: "%s"
                specialization: "Pediatrics"
                phone: "555999888"
                isActive: false
            ) {
                doctor {
                    id
                    specialization
                    phone
                    isActive
                }
                success
                errors
            }
        }
        ''' % self.doctor.id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['updateDoctor']
        self.assertTrue(data['success'])
        self.assertEqual(data['doctor']['specialization'], 'Pediatrics')
        self.assertEqual(data['doctor']['phone'], '555999888')
        self.assertFalse(data['doctor']['isActive'])
    
    def test_delete_doctor_mutation(self):
        """Test deleteDoctor mutation"""
        mutation = '''
        mutation {
            deleteDoctor(id: "%s") {
                success
                errors
            }
        }
        ''' % self.doctor.id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['deleteDoctor']
        self.assertTrue(data['success'])
        
        # Verify doctor is deleted
        query = '''
        query {
            allDoctors {
                id
            }
        }
        '''
        response = self.query(query)
        data = response.json()['data']['allDoctors']
        self.assertEqual(len(data), 0)


class DoctorAPITest(TestCase):
    """Test cases for Doctor API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='doctor1',
            email='doctor1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            role='DOCTOR'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.user,
            specialization='Cardiology',
            phone='123456789',
            license_number='DOC123456',
            date_of_birth='1980-01-01',
            address='123 Medical St, City',
            is_active=True
        )
    
    def test_doctor_creation(self):
        """Test doctor creation"""
        self.assertEqual(self.doctor.user.username, 'doctor1')
        self.assertEqual(self.doctor.specialization, 'Cardiology')
        self.assertTrue(self.doctor.is_active)
    
    def test_doctor_validation(self):
        """Test doctor model validation"""
        # Test unique license number
        with self.assertRaises(Exception):
            Doctor.objects.create(
                user=self.user,
                specialization='Neurology',
                phone='987654321',
                license_number='DOC123456',  # Same license number
                date_of_birth='1985-05-15',
                address='456 Health Ave, City',
                is_active=True
            )
