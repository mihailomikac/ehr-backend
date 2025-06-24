from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token
from datetime import datetime, timedelta
from .models import MedicalRecord
from doctors.models import Doctor
from patients.models import Patient
from .schema import Query, Mutation
import graphene

User = get_user_model()


class MedicalRecordModelTest(TestCase):
    """Test cases for MedicalRecord model"""
    
    def setUp(self):
        """Set up test data"""
        # Create doctor user and doctor
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            role='DOCTOR'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='Cardiology',
            phone='123456789',
            license_number='DOC123456',
            date_of_birth='1980-01-01',
            address='123 Medical St, City',
            is_active=True
        )
        
        # Create patient user and patient
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient1@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            role='PATIENT'
        )
        
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
        
        # Create medical record
        self.medical_record_data = {
            'patient': self.patient,
            'doctor': self.doctor,
            'record_number': 'MR001',
            'visit_date': timezone.now().date(),
            'diagnosis': 'Hypertension',
            'symptoms': 'High blood pressure, headache',
            'treatment': 'Prescribed medication',
            'prescription': 'Lisinopril 10mg daily',
            'notes': 'Patient needs regular monitoring',
            'follow_up_date': timezone.now().date() + timedelta(days=30),
            'is_active': True
        }
    
    def test_create_medical_record(self):
        """Test creating a new medical record"""
        medical_record = MedicalRecord.objects.create(**self.medical_record_data)
        self.assertEqual(medical_record.patient.user.username, 'patient1')
        self.assertEqual(medical_record.doctor.user.username, 'doctor1')
        self.assertEqual(medical_record.record_number, 'MR001')
        self.assertEqual(medical_record.diagnosis, 'Hypertension')
        self.assertTrue(medical_record.is_active)
    
    def test_medical_record_str_representation(self):
        """Test medical record string representation"""
        medical_record = MedicalRecord.objects.create(**self.medical_record_data)
        expected = f"MR{medical_record.id:06d} - {medical_record.patient.user.first_name} {medical_record.patient.user.last_name} - {medical_record.diagnosis}"
        self.assertEqual(str(medical_record), expected)
    
    def test_medical_record_unique_record_number(self):
        """Test medical record unique record number"""
        MedicalRecord.objects.create(**self.medical_record_data)
        
        # Try to create another record with same number
        with self.assertRaises(Exception):
            MedicalRecord.objects.create(**self.medical_record_data)


class MedicalRecordGraphQLTest(GraphQLTestCase):
    """Test cases for MedicalRecord GraphQL operations"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        # Create doctor user and doctor
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            role='DOCTOR'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='Cardiology',
            phone='123456789',
            license_number='DOC123456',
            date_of_birth='1980-01-01',
            address='123 Medical St, City',
            is_active=True
        )
        
        # Create patient user and patient
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient1@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            role='PATIENT'
        )
        
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
        
        # Create medical record
        self.medical_record = MedicalRecord.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            record_number='MR001',
            visit_date=timezone.now().date(),
            diagnosis='Hypertension',
            symptoms='High blood pressure, headache',
            treatment='Prescribed medication',
            prescription='Lisinopril 10mg daily',
            notes='Patient needs regular monitoring',
            follow_up_date=timezone.now().date() + timedelta(days=30),
            is_active=True
        )
    
    def test_create_medical_record_mutation(self):
        """Test createMedicalRecord mutation"""
        today = timezone.now().date().strftime('%Y-%m-%d')
        follow_up = (timezone.now().date() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        mutation = '''
        mutation {
            createMedicalRecord(
                patientId: "%s"
                doctorId: "%s"
                recordNumber: "MR002"
                visitDate: "%s"
                diagnosis: "Diabetes Type 2"
                symptoms: "Increased thirst, frequent urination"
                treatment: "Diet and exercise"
                prescription: "Metformin 500mg twice daily"
                notes: "Patient needs lifestyle changes"
                followUpDate: "%s"
                isActive: true
            ) {
                medicalRecord {
                    id
                    recordNumber
                    diagnosis
                    symptoms
                    treatment
                    prescription
                    isActive
                    patient {
                        user {
                            username
                        }
                    }
                    doctor {
                        user {
                            username
                        }
                    }
                }
                success
                errors
            }
        }
        ''' % (self.patient.id, self.doctor.id, today, follow_up)
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['createMedicalRecord']
        self.assertTrue(data['success'])
        self.assertEqual(data['medicalRecord']['recordNumber'], 'MR002')
        self.assertEqual(data['medicalRecord']['diagnosis'], 'Diabetes Type 2')
        self.assertEqual(data['medicalRecord']['symptoms'], 'Increased thirst, frequent urination')
    
    def test_all_medical_records_query(self):
        """Test allMedicalRecords query"""
        query = '''
        query {
            allMedicalRecords {
                id
                recordNumber
                diagnosis
                symptoms
                treatment
                visitDate
                isActive
                patient {
                    user {
                        username
                        firstName
                        lastName
                    }
                }
                doctor {
                    user {
                        username
                        firstName
                        lastName
                    }
                }
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['allMedicalRecords']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['recordNumber'], 'MR001')
        self.assertEqual(data[0]['diagnosis'], 'Hypertension')
        self.assertEqual(data[0]['patient']['user']['username'], 'patient1')
        self.assertEqual(data[0]['doctor']['user']['username'], 'doctor1')
    
    def test_medical_record_by_id_query(self):
        """Test medicalRecordById query"""
        query = '''
        query {
            medicalRecordById(id: "%s") {
                id
                recordNumber
                diagnosis
                symptoms
                patient {
                    user {
                        username
                    }
                }
                doctor {
                    user {
                        username
                    }
                }
            }
        }
        ''' % self.medical_record.id
        
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['medicalRecordById']
        self.assertEqual(data['recordNumber'], 'MR001')
        self.assertEqual(data['diagnosis'], 'Hypertension')
        self.assertEqual(data['patient']['user']['username'], 'patient1')
        self.assertEqual(data['doctor']['user']['username'], 'doctor1')
    
    def test_medical_record_by_id_not_found(self):
        """Test medicalRecordById query with non-existent ID"""
        query = '''
        query {
            medicalRecordById(id: "999") {
                id
                recordNumber
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['medicalRecordById']
        self.assertIsNone(data)
    
    def test_update_medical_record_mutation(self):
        """Test updateMedicalRecord mutation"""
        mutation = '''
        mutation {
            updateMedicalRecord(
                id: "%s"
                diagnosis: "Hypertension Stage 2"
                symptoms: "Severe headache, dizziness"
                treatment: "Increased medication dosage"
                prescription: "Lisinopril 20mg daily"
                notes: "Patient condition worsened"
                isActive: false
            ) {
                medicalRecord {
                    id
                    diagnosis
                    symptoms
                    treatment
                    prescription
                    notes
                    isActive
                }
                success
                errors
            }
        }
        ''' % self.medical_record.id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['updateMedicalRecord']
        self.assertTrue(data['success'])
        self.assertEqual(data['medicalRecord']['diagnosis'], 'Hypertension Stage 2')
        self.assertEqual(data['medicalRecord']['symptoms'], 'Severe headache, dizziness')
        self.assertEqual(data['medicalRecord']['treatment'], 'Increased medication dosage')
        self.assertFalse(data['medicalRecord']['isActive'])
    
    def test_delete_medical_record_mutation(self):
        """Test deleteMedicalRecord mutation"""
        mutation = '''
        mutation {
            deleteMedicalRecord(id: "%s") {
                success
                errors
            }
        }
        ''' % self.medical_record.id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['deleteMedicalRecord']
        self.assertTrue(data['success'])
        
        # Verify medical record is deleted
        query = '''
        query {
            allMedicalRecords {
                id
            }
        }
        '''
        response = self.query(query)
        data = response.json()['data']['allMedicalRecords']
        self.assertEqual(len(data), 0)


class MedicalRecordAPITest(TestCase):
    """Test cases for MedicalRecord API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create doctor user and doctor
        self.doctor_user = User.objects.create_user(
            username='doctor1',
            email='doctor1@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            role='DOCTOR'
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='Cardiology',
            phone='123456789',
            license_number='DOC123456',
            date_of_birth='1980-01-01',
            address='123 Medical St, City',
            is_active=True
        )
        
        # Create patient user and patient
        self.patient_user = User.objects.create_user(
            username='patient1',
            email='patient1@example.com',
            password='testpass123',
            first_name='Jane',
            last_name='Smith',
            role='PATIENT'
        )
        
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
        
        # Create medical record
        self.medical_record = MedicalRecord.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            record_number='MR001',
            visit_date=timezone.now().date(),
            diagnosis='Hypertension',
            symptoms='High blood pressure, headache',
            treatment='Prescribed medication',
            prescription='Lisinopril 10mg daily',
            notes='Patient needs regular monitoring',
            follow_up_date=timezone.now().date() + timedelta(days=30),
            is_active=True
        )
    
    def test_medical_record_creation(self):
        """Test medical record creation"""
        self.assertEqual(self.medical_record.patient.user.username, 'patient1')
        self.assertEqual(self.medical_record.doctor.user.username, 'doctor1')
        self.assertEqual(self.medical_record.record_number, 'MR001')
        self.assertEqual(self.medical_record.diagnosis, 'Hypertension')
        self.assertTrue(self.medical_record.is_active)
    
    def test_medical_record_validation(self):
        """Test medical record model validation"""
        # Test unique record number
        with self.assertRaises(Exception):
            MedicalRecord.objects.create(
                patient=self.patient,
                doctor=self.doctor,
                record_number='MR001',  # Same record number
                visit_date=timezone.now().date(),
                diagnosis='Diabetes',
                symptoms='Increased thirst',
                treatment='Diet',
                prescription='Metformin',
                notes='Test',
                follow_up_date=timezone.now().date() + timedelta(days=30),
                is_active=True
            )
