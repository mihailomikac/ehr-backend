from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token
from .models import Patient
from .schema import Query, Mutation
import graphene

User = get_user_model()


class PatientModelTest(TestCase):
    """Test cases for Patient model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='patient1',
            email='patient1@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            role='PATIENT'
        )
        
        self.patient_data = {
            'user': self.user,
            'date_of_birth': '1990-05-15',
            'phone': '123456789',
            'address': '123 Patient St, City',
            'emergency_contact': 'John Smith',
            'emergency_phone': '987654321',
            'blood_type': 'A+',
            'allergies': 'Penicillin',
            'medical_history': 'Hypertension',
            'is_active': True
        }
    
    def test_create_patient(self):
        """Test creating a new patient"""
        patient = Patient.objects.create(**self.patient_data)
        self.assertEqual(patient.user.username, 'patient1')
        self.assertEqual(patient.blood_type, 'A+')
        self.assertEqual(patient.allergies, 'Penicillin')
        self.assertTrue(patient.is_active)
    
    def test_patient_str_representation(self):
        """Test patient string representation"""
        patient = Patient.objects.create(**self.patient_data)
        expected = f"{patient.user.first_name} {patient.user.last_name} - Patient"
        self.assertEqual(str(patient), expected)
    
    def test_patient_blood_type_choices(self):
        """Test patient blood type choices"""
        patient = Patient.objects.create(**self.patient_data)
        self.assertIn(patient.blood_type, [choice[0] for choice in Patient.BLOOD_TYPE_CHOICES])


class PatientGraphQLTest(GraphQLTestCase):
    """Test cases for Patient GraphQL operations"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        # Create patient user
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient1@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            role='PATIENT'
        )
        
        # Create patient
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth='1990-05-15',
            phone='123456789',
            address='123 Patient St, City',
            emergency_contact='John Smith',
            emergency_phone='987654321',
            blood_type='A+',
            allergies='Penicillin',
            medical_history='Hypertension',
            is_active=True
        )
    
    def test_create_patient_mutation(self):
        """Test createPatient mutation"""
        # First create a user for the patient
        user_mutation = '''
        mutation {
            createUser(
                username: "patient2"
                email: "patient2@example.com"
                password: "testpass123"
                firstName: "Bob"
                lastName: "Johnson"
                role: "PATIENT"
                phone: "555123456"
                dateOfBirth: "1985-10-20"
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
        
        # Create patient
        mutation = '''
        mutation {
            createPatient(
                userId: "%s"
                dateOfBirth: "1985-10-20"
                phone: "555123456"
                address: "456 Health Ave, City"
                emergencyContact: "Mary Johnson"
                emergencyPhone: "555987654"
                bloodType: "O+"
                allergies: "None"
                medicalHistory: "Diabetes"
                isActive: true
            ) {
                patient {
                    id
                    bloodType
                    allergies
                    medicalHistory
                    isActive
                }
                success
                errors
            }
        }
        ''' % user_id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['createPatient']
        self.assertTrue(data['success'])
        self.assertEqual(data['patient']['bloodType'], 'O+')
        self.assertEqual(data['patient']['allergies'], 'None')
    
    def test_all_patients_query(self):
        """Test allPatients query"""
        query = '''
        query {
            allPatients {
                id
                bloodType
                allergies
                medicalHistory
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
        data = response.json()['data']['allPatients']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['bloodType'], 'A+')
        self.assertEqual(data[0]['user']['username'], 'patient1')
    
    def test_patient_by_id_query(self):
        """Test patientById query"""
        query = '''
        query {
            patientById(id: "%s") {
                id
                bloodType
                allergies
                user {
                    username
                    firstName
                    lastName
                }
            }
        }
        ''' % self.patient.id
        
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['patientById']
        self.assertEqual(data['bloodType'], 'A+')
        self.assertEqual(data['user']['username'], 'patient1')
    
    def test_patient_by_id_not_found(self):
        """Test patientById query with non-existent ID"""
        query = '''
        query {
            patientById(id: "999") {
                id
                bloodType
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['patientById']
        self.assertIsNone(data)
    
    def test_update_patient_mutation(self):
        """Test updatePatient mutation"""
        mutation = '''
        mutation {
            updatePatient(
                id: "%s"
                bloodType: "B+"
                allergies: "Latex"
                medicalHistory: "Asthma"
                isActive: false
            ) {
                patient {
                    id
                    bloodType
                    allergies
                    medicalHistory
                    isActive
                }
                success
                errors
            }
        }
        ''' % self.patient.id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['updatePatient']
        self.assertTrue(data['success'])
        self.assertEqual(data['patient']['bloodType'], 'B+')
        self.assertEqual(data['patient']['allergies'], 'Latex')
        self.assertFalse(data['patient']['isActive'])
    
    def test_delete_patient_mutation(self):
        """Test deletePatient mutation"""
        mutation = '''
        mutation {
            deletePatient(id: "%s") {
                success
                errors
            }
        }
        ''' % self.patient.id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['deletePatient']
        self.assertTrue(data['success'])
        
        # Verify patient is deleted
        query = '''
        query {
            allPatients {
                id
            }
        }
        '''
        response = self.query(query)
        data = response.json()['data']['allPatients']
        self.assertEqual(len(data), 0)


class PatientAPITest(TestCase):
    """Test cases for Patient API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='patient1',
            email='patient1@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            role='PATIENT'
        )
        
        self.patient = Patient.objects.create(
            user=self.user,
            date_of_birth='1990-05-15',
            phone='123456789',
            address='123 Patient St, City',
            emergency_contact='John Smith',
            emergency_phone='987654321',
            blood_type='A+',
            allergies='Penicillin',
            medical_history='Hypertension',
            is_active=True
        )
    
    def test_patient_creation(self):
        """Test patient creation"""
        self.assertEqual(self.patient.user.username, 'patient1')
        self.assertEqual(self.patient.blood_type, 'A+')
        self.assertEqual(self.patient.allergies, 'Penicillin')
        self.assertTrue(self.patient.is_active)
    
    def test_patient_validation(self):
        """Test patient model validation"""
        # Test valid blood type
        self.assertIn(self.patient.blood_type, [choice[0] for choice in Patient.BLOOD_TYPE_CHOICES])
        
        # Test required fields
        with self.assertRaises(Exception):
            Patient.objects.create(
                user=self.user,
                # Missing required fields
            )
