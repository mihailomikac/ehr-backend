from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token
from datetime import datetime, timedelta
from .models import Appointment
from doctors.models import Doctor
from patients.models import Patient
from .schema import Query, Mutation
import graphene

User = get_user_model()


class AppointmentModelTest(TestCase):
    """Test cases for Appointment model"""
    
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
        
        # Create appointment
        self.appointment_data = {
            'patient': self.patient,
            'doctor': self.doctor,
            'appointment_date': timezone.now() + timedelta(days=1),
            'appointment_time': '10:00:00',
            'reason': 'Regular checkup',
            'status': 'SCHEDULED',
            'notes': 'Patient has hypertension'
        }
    
    def test_create_appointment(self):
        """Test creating a new appointment"""
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertEqual(appointment.patient.user.username, 'patient1')
        self.assertEqual(appointment.doctor.user.username, 'doctor1')
        self.assertEqual(appointment.status, 'SCHEDULED')
        self.assertEqual(appointment.reason, 'Regular checkup')
    
    def test_appointment_str_representation(self):
        """Test appointment string representation"""
        appointment = Appointment.objects.create(**self.appointment_data)
        expected = f"{appointment.patient.user.first_name} {appointment.patient.user.last_name} - {appointment.doctor.user.first_name} {appointment.doctor.user.last_name} - {appointment.appointment_date.strftime('%Y-%m-%d')}"
        self.assertEqual(str(appointment), expected)
    
    def test_appointment_status_choices(self):
        """Test appointment status choices"""
        appointment = Appointment.objects.create(**self.appointment_data)
        self.assertIn(appointment.status, [choice[0] for choice in Appointment.STATUS_CHOICES])


class AppointmentGraphQLTest(GraphQLTestCase):
    """Test cases for Appointment GraphQL operations"""
    
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
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=timezone.now() + timedelta(days=1),
            appointment_time='10:00:00',
            reason='Regular checkup',
            status='SCHEDULED',
            notes='Patient has hypertension'
        )
    
    def test_create_appointment_mutation(self):
        """Test createAppointment mutation"""
        tomorrow = (timezone.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        mutation = '''
        mutation {
            createAppointment(
                patientId: "%s"
                doctorId: "%s"
                appointmentDate: "%s"
                appointmentTime: "14:00:00"
                reason: "Follow-up consultation"
                status: "SCHEDULED"
                notes: "Patient needs follow-up"
            ) {
                appointment {
                    id
                    reason
                    status
                    notes
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
        ''' % (self.patient.id, self.doctor.id, tomorrow)
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['createAppointment']
        self.assertTrue(data['success'])
        self.assertEqual(data['appointment']['reason'], 'Follow-up consultation')
        self.assertEqual(data['appointment']['status'], 'SCHEDULED')
    
    def test_all_appointments_query(self):
        """Test allAppointments query"""
        query = '''
        query {
            allAppointments {
                id
                reason
                status
                appointmentDate
                appointmentTime
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
        data = response.json()['data']['allAppointments']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['reason'], 'Regular checkup')
        self.assertEqual(data[0]['status'], 'SCHEDULED')
        self.assertEqual(data[0]['patient']['user']['username'], 'patient1')
        self.assertEqual(data[0]['doctor']['user']['username'], 'doctor1')
    
    def test_appointment_by_id_query(self):
        """Test appointmentById query"""
        query = '''
        query {
            appointmentById(id: "%s") {
                id
                reason
                status
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
        ''' % self.appointment.id
        
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['appointmentById']
        self.assertEqual(data['reason'], 'Regular checkup')
        self.assertEqual(data['patient']['user']['username'], 'patient1')
        self.assertEqual(data['doctor']['user']['username'], 'doctor1')
    
    def test_appointment_by_id_not_found(self):
        """Test appointmentById query with non-existent ID"""
        query = '''
        query {
            appointmentById(id: "999") {
                id
                reason
            }
        }
        '''
        response = self.query(query)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['appointmentById']
        self.assertIsNone(data)
    
    def test_update_appointment_mutation(self):
        """Test updateAppointment mutation"""
        mutation = '''
        mutation {
            updateAppointment(
                id: "%s"
                reason: "Emergency consultation"
                status: "COMPLETED"
                notes: "Patient treated successfully"
            ) {
                appointment {
                    id
                    reason
                    status
                    notes
                }
                success
                errors
            }
        }
        ''' % self.appointment.id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['updateAppointment']
        self.assertTrue(data['success'])
        self.assertEqual(data['appointment']['reason'], 'Emergency consultation')
        self.assertEqual(data['appointment']['status'], 'COMPLETED')
        self.assertEqual(data['appointment']['notes'], 'Patient treated successfully')
    
    def test_delete_appointment_mutation(self):
        """Test deleteAppointment mutation"""
        mutation = '''
        mutation {
            deleteAppointment(id: "%s") {
                success
                errors
            }
        }
        ''' % self.appointment.id
        
        response = self.query(mutation)
        self.assertResponseNoErrors(response)
        data = response.json()['data']['deleteAppointment']
        self.assertTrue(data['success'])
        
        # Verify appointment is deleted
        query = '''
        query {
            allAppointments {
                id
            }
        }
        '''
        response = self.query(query)
        data = response.json()['data']['allAppointments']
        self.assertEqual(len(data), 0)


class AppointmentAPITest(TestCase):
    """Test cases for Appointment API endpoints"""
    
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
        
        # Create appointment
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=timezone.now() + timedelta(days=1),
            appointment_time='10:00:00',
            reason='Regular checkup',
            status='SCHEDULED',
            notes='Patient has hypertension'
        )
    
    def test_appointment_creation(self):
        """Test appointment creation"""
        self.assertEqual(self.appointment.patient.user.username, 'patient1')
        self.assertEqual(self.appointment.doctor.user.username, 'doctor1')
        self.assertEqual(self.appointment.status, 'SCHEDULED')
        self.assertEqual(self.appointment.reason, 'Regular checkup')
    
    def test_appointment_validation(self):
        """Test appointment model validation"""
        # Test valid status
        self.assertIn(self.appointment.status, [choice[0] for choice in Appointment.STATUS_CHOICES])
        
        # Test future appointment date
        self.assertGreater(self.appointment.appointment_date, timezone.now())
