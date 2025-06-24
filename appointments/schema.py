import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date
from .models import Appointment
from patients.models import Patient
from doctors.models import Doctor


class AppointmentType(DjangoObjectType):
    """
    GraphQL type for Appointment model
    """
    class Meta:
        model = Appointment
        fields = '__all__'
        filter_fields = {
            'status': ['exact'],
            'appointment_date': ['exact', 'gte', 'lte'],
            'patient__user__first_name': ['exact', 'icontains'],
            'patient__user__last_name': ['exact', 'icontains'],
            'doctor__user__first_name': ['exact', 'icontains'],
            'doctor__user__last_name': ['exact', 'icontains'],
            'doctor__specialization': ['exact', 'icontains'],
        }


class Query(graphene.ObjectType):
    """
    GraphQL queries for appointments
    """
    # Get all appointments (with permissions)
    all_appointments = graphene.List(AppointmentType)
    
    # Get appointment by ID
    appointment_by_id = graphene.Field(AppointmentType, id=graphene.ID(required=True))
    
    # Get appointments by date
    appointments_by_date = graphene.List(
        AppointmentType, 
        date=graphene.Date(required=True)
    )
    
    # Get doctor's appointments
    doctor_appointments = graphene.List(
        AppointmentType,
        doctor_id=graphene.ID(),
        date=graphene.Date()
    )
    
    # Get patient's appointments
    patient_appointments = graphene.List(
        AppointmentType,
        patient_id=graphene.ID()
    )
    
    # Search appointments
    search_appointments = graphene.List(
        AppointmentType,
        search=graphene.String(),
        status=graphene.String(),
        start_date=graphene.Date(),
        end_date=graphene.Date()
    )
    
    @login_required
    def resolve_all_appointments(self, info):
        """Get appointments based on user role"""
        user = info.context.user
        
        if user.is_admin:
            return Appointment.objects.all()
        elif user.is_doctor:
            return Appointment.objects.filter(doctor__user=user)
        elif user.is_patient:
            return Appointment.objects.filter(patient__user=user)
        else:
            return Appointment.objects.none()
    
    @login_required
    def resolve_appointment_by_id(self, info, id):
        """Get appointment by ID with permissions"""
        user = info.context.user
        
        try:
            appointment = Appointment.objects.get(id=id)
            
            if user.is_admin:
                return appointment
            elif user.is_doctor and appointment.doctor.user == user:
                return appointment
            elif user.is_patient and appointment.patient.user == user:
                return appointment
            
            return None
        except Appointment.DoesNotExist:
            return None
    
    @login_required
    def resolve_appointments_by_date(self, info, date):
        """Get appointments for a specific date"""
        user = info.context.user
        
        queryset = Appointment.objects.filter(
            appointment_date__date=date
        )
        
        if user.is_admin:
            return queryset
        elif user.is_doctor:
            return queryset.filter(doctor__user=user)
        elif user.is_patient:
            return queryset.filter(patient__user=user)
        else:
            return Appointment.objects.none()
    
    @login_required
    def resolve_doctor_appointments(self, info, doctor_id=None, date=None):
        """Get doctor's appointments"""
        user = info.context.user
        
        if user.is_admin:
            queryset = Appointment.objects.all()
        elif user.is_doctor:
            queryset = Appointment.objects.filter(doctor__user=user)
        else:
            return Appointment.objects.none()
        
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        if date:
            queryset = queryset.filter(appointment_date__date=date)
        
        return queryset
    
    @login_required
    def resolve_patient_appointments(self, info, patient_id=None):
        """Get patient's appointments"""
        user = info.context.user
        
        if user.is_admin:
            queryset = Appointment.objects.all()
        elif user.is_doctor:
            queryset = Appointment.objects.filter(doctor__user=user)
        elif user.is_patient:
            queryset = Appointment.objects.filter(patient__user=user)
        else:
            return Appointment.objects.none()
        
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        return queryset
    
    @login_required
    def resolve_search_appointments(self, info, search=None, status=None, start_date=None, end_date=None):
        """Search appointments with filters"""
        user = info.context.user
        
        if user.is_admin:
            queryset = Appointment.objects.all()
        elif user.is_doctor:
            queryset = Appointment.objects.filter(doctor__user=user)
        elif user.is_patient:
            queryset = Appointment.objects.filter(patient__user=user)
        else:
            return Appointment.objects.none()
        
        if search:
            queryset = queryset.filter(
                Q(patient__user__first_name__icontains=search) |
                Q(patient__user__last_name__icontains=search) |
                Q(doctor__user__first_name__icontains=search) |
                Q(doctor__user__last_name__icontains=search) |
                Q(reason_for_visit__icontains=search) |
                Q(notes__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        if start_date:
            queryset = queryset.filter(appointment_date__date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(appointment_date__date__lte=end_date)
        
        return queryset


class CreateAppointment(graphene.Mutation):
    """
    Mutation to create a new appointment
    """
    class Arguments:
        patient_id = graphene.ID(required=True)
        doctor_id = graphene.ID(required=True)
        appointment_date = graphene.DateTime(required=True)
        reason_for_visit = graphene.String()
        notes = graphene.String()
        duration_minutes = graphene.Int()
    
    appointment = graphene.Field(AppointmentType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @login_required
    def mutate(self, info, patient_id, doctor_id, appointment_date, **kwargs):
        user = info.context.user
        
        # Only doctors and admins can create appointments
        if not (user.is_doctor or user.is_admin):
            return CreateAppointment(
                appointment=None, 
                success=False, 
                errors=["Only doctors and admins can create appointments"]
            )
        
        try:
            patient = Patient.objects.get(id=patient_id)
            doctor = Doctor.objects.get(id=doctor_id)
            
            # Check if doctor is creating appointment for their patient
            if user.is_doctor and doctor.user != user:
                return CreateAppointment(
                    appointment=None, 
                    success=False, 
                    errors=["You can only create appointments for your patients"]
                )
            
            # Check if time slot is available
            if Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                status__in=['SCHEDULED', 'CONFIRMED']
            ).exists():
                return CreateAppointment(
                    appointment=None, 
                    success=False, 
                    errors=["This time slot is already booked"]
                )
            
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                **kwargs
            )
            return CreateAppointment(appointment=appointment, success=True, errors=[])
        except (Patient.DoesNotExist, Doctor.DoesNotExist):
            return CreateAppointment(appointment=None, success=False, errors=["Patient or Doctor not found"])
        except Exception as e:
            return CreateAppointment(appointment=None, success=False, errors=[str(e)])


class UpdateAppointment(graphene.Mutation):
    """
    Mutation to update an appointment
    """
    class Arguments:
        id = graphene.ID(required=True)
        appointment_date = graphene.DateTime()
        status = graphene.String()
        reason_for_visit = graphene.String()
        notes = graphene.String()
        duration_minutes = graphene.Int()
    
    appointment = graphene.Field(AppointmentType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @login_required
    def mutate(self, info, id, **kwargs):
        user = info.context.user
        
        try:
            appointment = Appointment.objects.get(id=id)
            
            # Check permissions
            if user.is_admin:
                pass  # Admin can update any appointment
            elif user.is_doctor and appointment.doctor.user == user:
                pass  # Doctor can update their appointments
            elif user.is_patient and appointment.patient.user == user:
                # Patients can only update certain fields
                allowed_fields = ['notes']
                kwargs = {k: v for k, v in kwargs.items() if k in allowed_fields}
            else:
                return UpdateAppointment(
                    appointment=None, 
                    success=False, 
                    errors=["Permission denied"]
                )
            
            # Update fields
            for field, value in kwargs.items():
                if value is not None:
                    setattr(appointment, field, value)
            
            appointment.save()
            return UpdateAppointment(appointment=appointment, success=True, errors=[])
        except Appointment.DoesNotExist:
            return UpdateAppointment(appointment=None, success=False, errors=["Appointment not found"])
        except Exception as e:
            return UpdateAppointment(appointment=None, success=False, errors=[str(e)])


class Mutation(graphene.ObjectType):
    """
    GraphQL mutations for appointments
    """
    create_appointment = CreateAppointment.Field()
    update_appointment = UpdateAppointment.Field() 