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
    print("Kreiranje test podataka...")
    
    # 1. Kreiranje doktora
    print("1. Kreiranje doktora...")
    doctor_user = User.objects.create_user(
        username='dr.smith9',
        email='dr.smith@hospital.com',
        password='testpass123',
        first_name='John',
        last_name='Smith',
        role='DOCTOR',
        phone='+38111123456'
    )
    
    doctor = Doctor.objects.create(
        user=doctor_user,
        specialization='Kardiologija',
        license_number='DR12345112',
        office_location='Bulevar oslobođenja 123, Beograd'
    )
    print(f"✓ Doktor kreiran: {doctor.user.get_full_name()}")
    
    # 2. Kreiranje pacijenata
    print("\n2. Kreiranje pacijenata...")
    patients_data = [
        {
            'first_name': 'Ana',
            'last_name': 'Petrović',
            'email': 'ana.petrovic@email.com',
            'phone': '+38160123456',
            'date_of_birth': '1985-03-15',
            'address': 'Knez Mihailova 45, Beograd',
            'emergency_contact': '+38160987654'
        },
        {
            'first_name': 'Marko',
            'last_name': 'Jovanović',
            'email': 'marko.jovanovic@email.com',
            'phone': '+38161234567',
            'date_of_birth': '1978-07-22',
            'address': 'Terazije 78, Beograd',
            'emergency_contact': '+38161876543'
        },
        {
            'first_name': 'Jelena',
            'last_name': 'Nikolić',
            'email': 'jelena.nikolic@email.com',
            'phone': '+38162345678',
            'date_of_birth': '1992-11-08',
            'address': 'Skadarlija 12, Beograd',
            'emergency_contact': '+38162765432'
        },
        {
            'first_name': 'Stefan',
            'last_name': 'Đorđević',
            'email': 'stefan.djordjevic@email.com',
            'phone': '+38163456789',
            'date_of_birth': '1980-12-03',
            'address': 'Vračar 34, Beograd',
            'emergency_contact': '+38163654321'
        },
        {
            'first_name': 'Marija',
            'last_name': 'Stojanović',
            'email': 'marija.stojanovic@email.com',
            'phone': '+38164567890',
            'date_of_birth': '1988-05-18',
            'address': 'Zvezdara 56, Beograd',
            'emergency_contact': '+38164543210'
        }
    ]
    
    patients = []
    for i, data in enumerate(patients_data):
        patient_user = User.objects.create_user(
            username=f'patient_new___{i+1}',
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
            medical_record_number=f'MRN__{i+1:06d}',  # MRN000001, MRN000002, etc.
            address=data['address'],
            emergency_contact=data['emergency_contact']
        )
        patients.append(patient)
        print(f"✓ Pacijent kreiran: {patient.user.get_full_name()}")
    
    # 3. Kreiranje medicinskih izveštaja
    print("\n3. Kreiranje medicinskih izveštaja...")
    medical_conditions = [
        'Hipertenzija',
        'Dijabetes tip 2',
        'Astma',
        'Artritis',
        'Migrena',
        'Anksioznost',
        'Depresija',
        'Insomnija',
        'Gastritis',
        'Alergija na penicilin'
    ]
    
    treatments = [
        'Lisinopril 10mg dnevno',
        'Metformin 500mg 2x dnevno',
        'Ventolin inhalator po potrebi',
        'Ibuprofen 400mg 3x dnevno',
        'Sumatriptan 50mg po potrebi',
        'Sertralin 50mg dnevno',
        'Fluoksetin 20mg dnevno',
        'Melatonin 5mg pre spavanja',
        'Omeprazol 20mg dnevno',
        'Cetirizin 10mg dnevno'
    ]
    
    for i, patient in enumerate(patients):
        # Kreiranje 2-3 izveštaja za svakog pacijenta
        for j in range(random.randint(2, 3)):
            condition = random.choice(medical_conditions)
            treatment = random.choice(treatments)
            
            # Nasumični datum posete u prošlosti
            visit_date = datetime.now() - timedelta(days=random.randint(1, 30))
            
            record = MedicalRecord.objects.create(
                patient=patient,
                doctor=doctor,
                visit_date=visit_date,
                diagnosis=condition,
                treatment_notes=treatment,
                symptoms=f"Pacijent se žali na {condition.lower()}",
                medications_prescribed=treatment,
                follow_up_required=random.choice([True, False])
            )
            print(f"✓ Izveštaj kreiran za {patient.user.get_full_name()}: {condition}")
    
    # 4. Kreiranje termina
    print("\n4. Kreiranje termina...")
    appointment_reasons = [
        'Kontrola',
        'Prvi pregled',
        'Pratnja terapije',
        'Hitna intervencija',
        'Redovna kontrola'
    ]
    
    # Kreiranje termina za sledećih 30 dana
    for i in range(15):  # 15 termina
        patient = random.choice(patients)
        reason = random.choice(appointment_reasons)
        
        # Nasumični datum u sledećih 30 dana
        appointment_date = datetime.now().date() + timedelta(days=random.randint(1, 30))
        
        # Nasumično vreme između 9:00 i 17:00
        hour = random.randint(9, 17)
        minute = random.choice([0, 15, 30, 45])
        appointment_datetime = datetime.combine(appointment_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_datetime,
            duration_minutes=30,
            notes=f"Termin za {reason.lower()}",
            reason_for_visit=reason,
            status=random.choice(['SCHEDULED', 'CONFIRMED'])
        )
        print(f"✓ Termin kreiran: {patient.user.get_full_name()} - {reason} - {appointment_datetime.strftime('%d.%m.%Y %H:%M')}")
    
    print(f"\n🎉 Test podaci uspešno kreirani!")
    print(f"📊 Pregled:")
    print(f"   • Doktora: 1")
    print(f"   • Pacijenata: {len(patients)}")
    print(f"   • Medicinskih izveštaja: {MedicalRecord.objects.count()}")
    print(f"   • Termina: {Appointment.objects.count()}")
    print(f"\n🔑 Login podaci:")
    print(f"   Doktor: dr.smith7 / testpass123")
    print(f"   Pacijenti: patient_new__1, patient_new__2, patient_new__3, patient_new__4, patient_new__5 / testpass123")

if __name__ == '__main__':
    create_test_data() 