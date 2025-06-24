import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.db.models import Q
from .models import Patient
from users.models import User


class PatientType(DjangoObjectType):
    """
    GraphQL type for Patient model
    """
    class Meta:
        model = Patient
        fields = '__all__'
        filter_fields = {
            'medical_record_number': ['exact', 'icontains'],
            'user__first_name': ['exact', 'icontains'],
            'user__last_name': ['exact', 'icontains'],
            'user__email': ['exact', 'icontains'],
            'blood_type': ['exact'],
            'created_at': ['exact', 'gte', 'lte'],
        }


class Query(graphene.ObjectType):
    """
    GraphQL queries for patients
    """
    # Get all patients (with permissions)
    all_patients = graphene.List(PatientType)
    
    # Get patient by ID
    patient_by_id = graphene.Field(PatientType, id=graphene.ID(required=True))
    
    # Get patient by medical record number
    patient_by_mrn = graphene.Field(PatientType, mrn=graphene.String(required=True))
    
    # Search patients
    search_patients = graphene.List(
        PatientType, 
        search=graphene.String(),
        blood_type=graphene.String()
    )
    
    @login_required
    def resolve_all_patients(self, info):
        """Get patients based on user role"""
        user = info.context.user
        
        if user.is_admin:
            return Patient.objects.all()
        elif user.is_doctor:
            # Doctors see only their patients
            return Patient.objects.filter(
                appointments__doctor__user=user
            ).distinct()
        elif user.is_patient:
            # Patients see only themselves
            return Patient.objects.filter(user=user)
        else:
            return Patient.objects.none()
    
    @login_required
    def resolve_patient_by_id(self, info, id):
        """Get patient by ID with permissions"""
        user = info.context.user
        
        try:
            patient = Patient.objects.get(id=id)
            
            if user.is_admin:
                return patient
            elif user.is_doctor:
                # Check if doctor has appointments with this patient
                if patient.appointments.filter(doctor__user=user).exists():
                    return patient
            elif user.is_patient and patient.user == user:
                return patient
            
            return None
        except Patient.DoesNotExist:
            return None
    
    @login_required
    def resolve_patient_by_mrn(self, info, mrn):
        """Get patient by medical record number with permissions"""
        user = info.context.user
        
        try:
            patient = Patient.objects.get(medical_record_number=mrn)
            
            if user.is_admin:
                return patient
            elif user.is_doctor:
                if patient.appointments.filter(doctor__user=user).exists():
                    return patient
            elif user.is_patient and patient.user == user:
                return patient
            
            return None
        except Patient.DoesNotExist:
            return None
    
    @login_required
    def resolve_search_patients(self, info, search=None, blood_type=None):
        """Search patients with filters"""
        user = info.context.user
        
        if user.is_admin:
            queryset = Patient.objects.all()
        elif user.is_doctor:
            queryset = Patient.objects.filter(
                appointments__doctor__user=user
            ).distinct()
        elif user.is_patient:
            queryset = Patient.objects.filter(user=user)
        else:
            return Patient.objects.none()
        
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(medical_record_number__icontains=search)
            )
        
        if blood_type:
            queryset = queryset.filter(blood_type=blood_type)
        
        return queryset


class CreatePatient(graphene.Mutation):
    """
    Mutation to create a new patient
    """
    class Arguments:
        user_id = graphene.ID(required=True)
        medical_record_number = graphene.String(required=True)
        address = graphene.String()
        emergency_contact = graphene.String()
        emergency_contact_name = graphene.String()
        blood_type = graphene.String()
        allergies = graphene.String()
    
    patient = graphene.Field(PatientType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @login_required
    def mutate(self, info, user_id, medical_record_number, **kwargs):
        user = info.context.user
        
        # Only admins can create patients
        if not user.is_admin:
            return CreatePatient(
                patient=None, 
                success=False, 
                errors=["Only admins can create patients"]
            )
        
        try:
            user_obj = User.objects.get(id=user_id)
            patient = Patient.objects.create(
                user=user_obj,
                medical_record_number=medical_record_number,
                **kwargs
            )
            return CreatePatient(patient=patient, success=True, errors=[])
        except Exception as e:
            return CreatePatient(patient=None, success=False, errors=[str(e)])


class UpdatePatient(graphene.Mutation):
    """
    Mutation to update a patient
    """
    class Arguments:
        id = graphene.ID(required=True)
        address = graphene.String()
        emergency_contact = graphene.String()
        emergency_contact_name = graphene.String()
        blood_type = graphene.String()
        allergies = graphene.String()
    
    patient = graphene.Field(PatientType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @login_required
    def mutate(self, info, id, **kwargs):
        user = info.context.user
        
        try:
            patient = Patient.objects.get(id=id)
            
            # Check permissions
            if user.is_admin:
                pass  # Admin can update any patient
            elif user.is_doctor:
                # Doctor can only update their patients
                if not patient.appointments.filter(doctor__user=user).exists():
                    return UpdatePatient(
                        patient=None, 
                        success=False, 
                        errors=["You can only update your patients"]
                    )
            elif user.is_patient and patient.user == user:
                pass  # Patient can update their own profile
            else:
                return UpdatePatient(
                    patient=None, 
                    success=False, 
                    errors=["Permission denied"]
                )
            
            # Update fields
            for field, value in kwargs.items():
                if value is not None:
                    setattr(patient, field, value)
            
            patient.save()
            return UpdatePatient(patient=patient, success=True, errors=[])
        except Patient.DoesNotExist:
            return UpdatePatient(patient=None, success=False, errors=["Patient not found"])
        except Exception as e:
            return UpdatePatient(patient=None, success=False, errors=[str(e)])


class Mutation(graphene.ObjectType):
    """
    GraphQL mutations for patients
    """
    create_patient = CreatePatient.Field()
    update_patient = UpdatePatient.Field() 