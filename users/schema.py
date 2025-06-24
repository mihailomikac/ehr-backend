import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.contrib.auth import authenticate
from .models import User


class UserType(DjangoObjectType):
    """
    GraphQL type for User model
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'date_of_birth', 'is_active', 'date_joined')
        filter_fields = {
            'username': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'role': ['exact'],
            'is_active': ['exact'],
        }


class Query(graphene.ObjectType):
    """
    GraphQL queries for users
    """
    # Get current user
    me = graphene.Field(UserType)
    
    # Get all users (admin only)
    all_users = graphene.List(UserType)
    
    # Get user by ID
    user_by_id = graphene.Field(UserType, id=graphene.ID(required=True))
    
    @login_required
    def resolve_me(self, info):
        """Get current authenticated user"""
        return info.context.user
    
    @login_required
    def resolve_all_users(self, info):
        """Get all users (admin only)"""
        user = info.context.user
        if user.is_admin:
            return User.objects.all()
        return User.objects.none()
    
    def resolve_user_by_id(self, info, id):
        """Get user by ID"""
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None


class CreateUser(graphene.Mutation):
    """
    Mutation to create a new user
    """
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        role = graphene.String()
        phone = graphene.String()
        date_of_birth = graphene.Date()
    
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, username, email, password, **kwargs):
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                **kwargs
            )
            return CreateUser(user=user, success=True, errors=[])
        except Exception as e:
            return CreateUser(user=None, success=False, errors=[str(e)])


class LoginMutation(graphene.Mutation):
    """
    Custom login mutation that returns both token and user
    """
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
    
    token = graphene.String()
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, username, password):
        try:
            user = authenticate(username=username, password=password)
            if user is not None:
                from graphql_jwt.shortcuts import create_refresh_token, get_token
                token = get_token(user)
                return LoginMutation(
                    token=token,
                    user=user,
                    success=True,
                    errors=[]
                )
            else:
                return LoginMutation(
                    token=None,
                    user=None,
                    success=False,
                    errors=["Invalid credentials"]
                )
        except Exception as e:
            return LoginMutation(
                token=None,
                user=None,
                success=False,
                errors=[str(e)]
            )


class Mutation(graphene.ObjectType):
    """
    GraphQL mutations for users
    """
    create_user = CreateUser.Field()
    login = LoginMutation.Field()
    # JWT mutations are automatically included by graphql_jwt 