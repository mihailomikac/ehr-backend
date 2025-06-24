import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.db.models import Q
from .models import Doctor
from users.models import User


class DoctorType(DjangoObjectType):
    """
    GraphQL type for Doctor model
    """
    class Meta:
        model = Doctor
        fields = '__all__'
        filter_fields = {
            'specialization': ['exact', 'icontains'],
            'license_number': ['exact', 'icontains'],
            'user__first_name': ['exact', 'icontains'],
            'user__last_name': ['exact', 'icontains'],
            'user__email': ['exact', 'icontains'],
            'years_of_experience': ['exact', 'gte', 'lte'],
        }


class Query(graphene.ObjectType):
    """
    GraphQL queries for doctors
    """
    # Get all doctors
    all_doctors = graphene.List(DoctorType)
    
    # Get doctor by ID
    doctor_by_id = graphene.Field(DoctorType, id=graphene.ID(required=True))
    
    # Get doctor by license number
    doctor_by_license = graphene.Field(DoctorType, license_number=graphene.String(required=True))
    
    # Search doctors
    search_doctors = graphene.List(
        DoctorType, 
        search=graphene.String(),
        specialization=graphene.String()
    )
    
    def resolve_all_doctors(self, info):
        """Get all doctors (public information)"""
        return Doctor.objects.all()
    
    def resolve_doctor_by_id(self, info, id):
        """Get doctor by ID"""
        try:
            return Doctor.objects.get(id=id)
        except Doctor.DoesNotExist:
            return None
    
    def resolve_doctor_by_license(self, info, license_number):
        """Get doctor by license number"""
        try:
            return Doctor.objects.get(license_number=license_number)
        except Doctor.DoesNotExist:
            return None
    
    def resolve_search_doctors(self, info, search=None, specialization=None):
        """Search doctors with filters"""
        queryset = Doctor.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(specialization__icontains=search) |
                Q(license_number__icontains=search)
            )
        
        if specialization:
            queryset = queryset.filter(specialization=specialization)
        
        return queryset


class CreateDoctor(graphene.Mutation):
    """
    Mutation to create a new doctor
    """
    class Arguments:
        user_id = graphene.ID(required=True)
        specialization = graphene.String(required=True)
        license_number = graphene.String(required=True)
        years_of_experience = graphene.Int()
        education = graphene.String()
        certifications = graphene.String()
        office_location = graphene.String()
        office_hours = graphene.String()
    
    doctor = graphene.Field(DoctorType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @login_required
    def mutate(self, info, user_id, specialization, license_number, **kwargs):
        user = info.context.user
        
        # Only admins can create doctors
        if not user.is_admin:
            return CreateDoctor(
                doctor=None, 
                success=False, 
                errors=["Only admins can create doctors"]
            )
        
        try:
            user_obj = User.objects.get(id=user_id)
            doctor = Doctor.objects.create(
                user=user_obj,
                specialization=specialization,
                license_number=license_number,
                **kwargs
            )
            return CreateDoctor(doctor=doctor, success=True, errors=[])
        except Exception as e:
            return CreateDoctor(doctor=None, success=False, errors=[str(e)])


class UpdateDoctor(graphene.Mutation):
    """
    Mutation to update a doctor
    """
    class Arguments:
        id = graphene.ID(required=True)
        specialization = graphene.String()
        years_of_experience = graphene.Int()
        education = graphene.String()
        certifications = graphene.String()
        office_location = graphene.String()
        office_hours = graphene.String()
    
    doctor = graphene.Field(DoctorType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    @login_required
    def mutate(self, info, id, **kwargs):
        user = info.context.user
        
        try:
            doctor = Doctor.objects.get(id=id)
            
            # Check permissions
            if user.is_admin:
                pass  # Admin can update any doctor
            elif user.is_doctor and doctor.user == user:
                pass  # Doctor can update their own profile
            else:
                return UpdateDoctor(
                    doctor=None, 
                    success=False, 
                    errors=["Permission denied"]
                )
            
            # Update fields
            for field, value in kwargs.items():
                if value is not None:
                    setattr(doctor, field, value)
            
            doctor.save()
            return UpdateDoctor(doctor=doctor, success=True, errors=[])
        except Doctor.DoesNotExist:
            return UpdateDoctor(doctor=None, success=False, errors=["Doctor not found"])
        except Exception as e:
            return UpdateDoctor(doctor=None, success=False, errors=[str(e)])


class Mutation(graphene.ObjectType):
    """
    GraphQL mutations for doctors
    """
    create_doctor = CreateDoctor.Field()
    update_doctor = UpdateDoctor.Field() 