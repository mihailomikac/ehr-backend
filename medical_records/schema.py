import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date
from .models import MedicalRecord
from patients.models import Patient
from doctors.models import Doctor


class MedicalRecordType(DjangoObjectType):
    """
    GraphQL type for MedicalRecord model
    """
    class Meta:
        model = MedicalRecord
        fields = '__all__'
        filter_fields = {
            'visit_date': ['exact', 'gte', 'lte'],
            'diagnosis': ['exact', 'icontains'],
            'patient__user__first_name': ['exact', 'icontains'],
            'patient__user__last_name': ['exact', 'icontains'],
            'doctor__user__first_name': ['exact', 'icontains'],
            'doctor__user__last_name': ['exact', 'icontains'],
            'follow_up_required': ['exact'],
        }


class Query(graphene.ObjectType):
    """
    GraphQL queries for medical records
    """
    # Get all medical records (with permissions)
    all_medical_records = graphene.List(MedicalRecordType)
    
    # Get medical record by ID
    medical_record_by_id = graphene.Field(MedicalRecordType, id=graphene.ID(required=True))
    
    # Get patient's medical records
    patient_medical_records = graphene.List(
        MedicalRecordType,
        patient_id=graphene.ID()
    )
    
    # Get doctor's medical records
    doctor_medical_records = graphene.List(
        MedicalRecordType,
        doctor_id=graphene.ID()
    )
    
    # Search medical records
    search_medical_records = graphene.List(
        MedicalRecordType,
        search=graphene.String(),
        start_date=graphene.Date(),
        end_date=graphene.Date(),
        follow_up_required=graphene.Boolean()
    )
    
    @login_required
    def resolve_all_medical_records(self, info):
        """Get medical records based on user role"""
        user = info.context.user
        
        if user.is_admin:
            return MedicalRecord.objects.all()
        elif user.is_doctor:
            return MedicalRecord.objects.filter(doctor__user=user)
        elif user.is_patient:
            return MedicalRecord.objects.filter(patient__user=user)
        else:
            return MedicalRecord.objects.none()
    
    @login_required
    def resolve_medical_record_by_id(self, info, id):
        """Get medical record by ID with permissions"""
        user = info.context.user
        
        try:
            medical_record = MedicalRecord.objects.get(id=id)
            
            if user.is_admin:
                return medical_record
            elif user.is_doctor and medical_record.doctor.user == user:
                return medical_record
            elif user.is_patient and medical_record.patient.user == user:
                return medical_record
            
            return None
        except MedicalRecord.DoesNotExist:
            return None
    
    @login_required
    def resolve_patient_medical_records(self, info, patient_id=None):
        """Get patient's medical records"""
        user = info.context.user
        
        if user.is_admin:
            queryset = MedicalRecord.objects.all()
        elif user.is_doctor:
            queryset = MedicalRecord.objects.filter(doctor__user=user)
        elif user.is_patient:
            queryset = MedicalRecord.objects.filter(patient__user=user)
        else:
            return MedicalRecord.objects.none()
        
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset.order_by('-visit_date')
    
    @login_required
    def resolve_doctor_medical_records(self, info, doctor_id=None):
        """Get doctor's medical records"""
        user = info.context.user
        
        if user.is_admin:
            queryset = MedicalRecord.objects.all()
        elif user.is_doctor:
            queryset = MedicalRecord.objects.filter(doctor__user=user)
        else:
            return MedicalRecord.objects.none()
        
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        return queryset.order_by('-visit_date')
    
    @login_required
    def resolve_search_medical_records(self, info, search=None, start_date=None, end_date=None, follow_up_required=None):
        """Search medical records with filters"""
        user = info.context.user
        
        if user.is_admin:
            queryset = MedicalRecord.objects.all()
        elif user.is_doctor:
            queryset = MedicalRecord.objects.filter(doctor__user=user)
        elif user.is_patient:
            queryset = MedicalRecord.objects.filter(patient__user=user)
        else:
            return MedicalRecord.objects.none()
        
        if search:
            queryset = queryset.filter(
                Q(diagnosis__icontains=search) |
                Q(symptoms__icontains=search) |
                Q(treatment_notes__icontains=search) |
                Q(medications_prescribed__icontains=search) |
                Q(patient__user__first_name__icontains=search) |
                Q(patient__user__last_name__icontains=search)
            )
        
        if start_date:
            queryset = queryset.filter(visit_date__date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(visit_date__date__lte=end_date)
        
        if follow_up_required is not None:
            queryset = queryset.filter(follow_up_required=follow_up_required)
        
        return queryset.order_by('-visit_date')


class CreateMedicalRecord(graphene.Mutation):
    """
    Mutation to create a new medical record
    """
    class Arguments:
        patient_id = graphene.ID(required=True)
        doctor_id = graphene.ID(required=True)
        visit_date = graphene.DateTime(required=True)
        diagnosis = graphene.String(required=True)
        treatment_notes = graphene.String(required=True)
        symptoms = graphene.String()
        vital_signs = graphene.JSONString()
        medications_prescribed = graphene.String()
        follow_up_required = graphene.Boolean()
        follow_up_date = graphene.Date()
        lab_results = graphene.String()
        imaging_results = graphene.String()
    
    medical_record = graphene.Field(MedicalRecordType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @login_required
    def mutate(self, info, patient_id, doctor_id, visit_date, diagnosis, treatment_notes, **kwargs):
        user = info.context.user
        
        # Only doctors and admins can create medical records
        if not (user.is_doctor or user.is_admin):
            return CreateMedicalRecord(
                medical_record=None, 
                success=False, 
                errors=["Only doctors and admins can create medical records"]
            )
        
        try:
            patient = Patient.objects.get(id=patient_id)
            doctor = Doctor.objects.get(id=doctor_id)
            
            # Check if doctor is creating record for their patient
            if user.is_doctor and doctor.user != user:
                return CreateMedicalRecord(
                    medical_record=None, 
                    success=False, 
                    errors=["You can only create medical records for your patients"]
                )
            
            medical_record = MedicalRecord.objects.create(
                patient=patient,
                doctor=doctor,
                visit_date=visit_date,
                diagnosis=diagnosis,
                treatment_notes=treatment_notes,
                **kwargs
            )
            return CreateMedicalRecord(medical_record=medical_record, success=True, errors=[])
        except (Patient.DoesNotExist, Doctor.DoesNotExist):
            return CreateMedicalRecord(medical_record=None, success=False, errors=["Patient or Doctor not found"])
        except Exception as e:
            return CreateMedicalRecord(medical_record=None, success=False, errors=[str(e)])


class UpdateMedicalRecord(graphene.Mutation):
    """
    Mutation to update a medical record
    """
    class Arguments:
        id = graphene.ID(required=True)
        diagnosis = graphene.String()
        treatment_notes = graphene.String()
        symptoms = graphene.String()
        vital_signs = graphene.JSONString()
        medications_prescribed = graphene.String()
        follow_up_required = graphene.Boolean()
        follow_up_date = graphene.Date()
        lab_results = graphene.String()
        imaging_results = graphene.String()
    
    medical_record = graphene.Field(MedicalRecordType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @login_required
    def mutate(self, info, id, **kwargs):
        user = info.context.user
        
        try:
            medical_record = MedicalRecord.objects.get(id=id)
            
            # Check permissions
            if user.is_admin:
                pass  # Admin can update any medical record
            elif user.is_doctor and medical_record.doctor.user == user:
                pass  # Doctor can update their medical records
            else:
                return UpdateMedicalRecord(
                    medical_record=None, 
                    success=False, 
                    errors=["Permission denied"]
                )
            
            # Update fields
            for field, value in kwargs.items():
                if value is not None:
                    setattr(medical_record, field, value)
            
            medical_record.save()
            return UpdateMedicalRecord(medical_record=medical_record, success=True, errors=[])
        except MedicalRecord.DoesNotExist:
            return UpdateMedicalRecord(medical_record=None, success=False, errors=["Medical record not found"])
        except Exception as e:
            return UpdateMedicalRecord(medical_record=None, success=False, errors=[str(e)])


class Mutation(graphene.ObjectType):
    """
    GraphQL mutations for medical records
    """
    create_medical_record = CreateMedicalRecord.Field()
    update_medical_record = UpdateMedicalRecord.Field() 