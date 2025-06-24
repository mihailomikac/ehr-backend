import graphene
from graphql_jwt.decorators import login_required
from graphql_jwt import ObtainJSONWebToken, Refresh, Verify

# Import our app schemas
from users.schema import Query as UserQuery, Mutation as UserMutation
from patients.schema import Query as PatientQuery, Mutation as PatientMutation
from doctors.schema import Query as DoctorQuery, Mutation as DoctorMutation
from appointments.schema import Query as AppointmentQuery, Mutation as AppointmentMutation
from medical_records.schema import Query as MedicalRecordQuery, Mutation as MedicalRecordMutation


class Query(
    UserQuery,
    PatientQuery,
    DoctorQuery,
    AppointmentQuery,
    MedicalRecordQuery,
    graphene.ObjectType
):
    """
    Main Query class that combines all app queries
    """
    pass


class Mutation(
    UserMutation,
    PatientMutation,
    DoctorMutation,
    AppointmentMutation,
    MedicalRecordMutation,
    graphene.ObjectType
):
    """
    Main Mutation class that combines all app mutations
    """
    # JWT Authentication mutations
    token_auth = ObtainJSONWebToken.Field()
    refresh_token = Refresh.Field()
    verify_token = Verify.Field()


# Create the schema
schema = graphene.Schema(query=Query, mutation=Mutation) 