#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ehr.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import User
from doctors.models import Doctor
from patients.models import Patient
from medical_records.models import MedicalRecord
from appointments.models import Appointment

User = get_user_model()

def create_test_data():
    print("Creating test data...")

    # 1. Create a doctor
    print("1. Creating doctor...")
    doctor_user = User.objects.create_user(
        username='dr.jones9',
        email='dr.jones@clinicusa.com',
        password='testpass123',
        first_name='Emily',
        last_name='Jones',
        role='DOCTOR',
        phone='+1-202-555-0133'
    )

    doctor = Doctor.objects.create(
        user=doctor_user,
        specialization='Cardiology',
        license_number='USMD123456',
        office_location='123 Main Street, Springfield, IL'
    )
    print(f"✓ Doctor created: {doctor.user.get_full_name()}")

    # 2. Create patients
    print("\n2. Creating patients...")
    patients_data = [
        {
            'first_name': 'Jessica',
            'last_name': 'Williams',
            'email': 'jessica.williams@example.com',
            'phone': '+1-202-555-0101',
            'date_of_birth': '1987-02-12',
            'address': '742 Evergreen Terrace, Springfield, IL',
            'emergency_contact': '+1-202-555-0144'
        },
        {
            'first_name': 'Michael',
            'last_name': 'Brown',
            'email': 'michael.brown@example.com',
            'phone': '+1-202-555-0102',
            'date_of_birth': '1975-06-23',
            'address': '1600 Pennsylvania Avenue, Washington, DC',
            'emergency_contact': '+1-202-555-0177'
        },
        {
            'first_name': 'Ashley',
            'last_name': 'Johnson',
            'email': 'ashley.johnson@example.com',
            'phone': '+1-202-555-0103',
            'date_of_birth': '1990-09-30',
            'address': '1234 Elm Street, Anytown, TX',
            'emergency_contact': '+1-202-555-0166'
        },
        {
            'first_name': 'David',
            'last_name': 'Miller',
            'email': 'david.miller@example.com',
            'phone': '+1-202-555-0104',
            'date_of_birth': '1982-11-17',
            'address': '100 Market Street, San Francisco, CA',
            'emergency_contact': '+1-202-555-0199'
        },
        {
            'first_name': 'Sarah',
            'last_name': 'Davis',
            'email': 'sarah.davis@example.com',
            'phone': '+1-202-555-0105',
            'date_of_birth': '1993-04-08',
            'address': '500 Sunset Blvd, Los Angeles, CA',
            'emergency_contact': '+1-202-555-0111'
        }
    ]

    patients = []
    for i, data in enumerate(patients_data):
        patient_user = User.objects.create_user(
            username=f'patient_us__{i+1}',
            email=data['email'],
            password='testpass123',
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='PATIENT',
            phone=data['phone'],
            date_of_birth=data['date_of_birth']
        )

        patient = Patient.objects.create(
            user=patient_user,
            medical_record_number=f'MRN_US_{i+1:06d}',
            address=data['address'],
            emergency_contact=data['emergency_contact']
        )
        patients.append(patient)
        print(f"✓ Patient created: {patient.user.get_full_name()}")

    # 3. Create medical records
    print("\n3. Creating medical records...")
    conditions = [
        'Hypertension',
        'Type 2 Diabetes',
        'Asthma',
        'Arthritis',
        'Migraine',
        'Anxiety',
        'Depression',
        'Insomnia',
        'Gastritis',
        'Penicillin Allergy'
    ]

    treatments = [
        'Lisinopril 10mg daily',
        'Metformin 500mg twice daily',
        'Albuterol inhaler as needed',
        'Ibuprofen 400mg three times daily',
        'Sumatriptan 50mg as needed',
        'Sertraline 50mg daily',
        'Fluoxetine 20mg daily',
        'Melatonin 5mg before bed',
        'Omeprazole 20mg daily',
        'Cetirizine 10mg daily'
    ]

    for patient in patients:
        for _ in range(random.randint(2, 3)):
            condition = random.choice(conditions)
            treatment = random.choice(treatments)
            visit_date = datetime.now() - timedelta(days=random.randint(1, 30))

            MedicalRecord.objects.create(
                patient=patient,
                doctor=doctor,
                visit_date=visit_date,
                diagnosis=condition,
                treatment_notes=treatment,
                symptoms=f"Patient reports symptoms consistent with {condition.lower()}",
                medications_prescribed=treatment,
                follow_up_required=random.choice([True, False])
            )
            print(f"✓ Record added for {patient.user.get_full_name()} - {condition}")

    # 4. Create appointments
    print("\n4. Creating appointments...")
    reasons = [
        'Follow-up visit',
        'Initial consultation',
        'Therapy monitoring',
        'Emergency consultation',
        'Routine check-up'
    ]

    for _ in range(15):
        patient = random.choice(patients)
        reason = random.choice(reasons)
        date = datetime.now().date() + timedelta(days=random.randint(1, 30))
        hour = random.randint(9, 17)
        minute = random.choice([0, 15, 30, 45])
        appointment_time = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))

        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_time,
            duration_minutes=30,
            notes=f"Appointment for {reason.lower()}",
            reason_for_visit=reason,
            status=random.choice(['SCHEDULED', 'CONFIRMED'])
        )
        print(f"✓ Appointment set for {patient.user.get_full_name()} - {reason} - {appointment_time.strftime('%m/%d/%Y %I:%M %p')}")

    print("\n🎉 Test data successfully created!")
    print("📊 Summary:")
    print(f"   • Doctors: 1")
    print(f"   • Patients: {len(patients)}")
    print(f"   • Medical Records: {MedicalRecord.objects.count()}")
    print(f"   • Appointments: {Appointment.objects.count()}")
    print("\n🔑 Login credentials:")
    print("   Doctor: dr.jones9 / testpass123")
    print("   Patients: patient_us__1 ... patient_us__5 / testpass123")

if __name__ == '__main__':
    create_test_data()
