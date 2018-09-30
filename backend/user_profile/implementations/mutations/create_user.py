import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from backend.error_responses import ServerError
from backend.user_profile.types import UserType

User = get_user_model()

USER_AUTHENTICATED = 1
EMAIL_NOT_UNIQUE = 2
USERNAME_NOT_UNIQUE = 3
USERNAME_TO_SHORT = 4
PASSWORD_TO_SHORT = 5


class CreateUserSuccess(graphene.ObjectType):
    user = graphene.Field(
        UserType, description="The newly created user object")


class CreateUserError(graphene.ObjectType):
    error_type = graphene.Int(description="ID of the error")
    error_message = graphene.String(
        description="Error message if creation fails")


class CreateUserPayload(graphene.Union):
    class Meta:
        types = (ServerError, CreateUserError, CreateUserSuccess)


class CreateUserMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(
            description="Username of the new user", required=True)
        password = graphene.String(
            description="Password of the user", required=True)
        email = graphene.String(description="Email of the user")

    create_user = CreateUserPayload()

    @staticmethod
    def description():
        return "Creates a new user"

    def mutate(self, info, username: str, password: str, email: str = None):
        if info.context.user.is_authenticated:
            return CreateUserMutation(
                create_user=CreateUserError(
                    error_type=USER_AUTHENTICATED,
                    error_message=
                    "An authenticated user can't create another user. Please logout first."
                ))

        if email is not None:
            try:
                query = User.objects.get(email=email)
                if query:
                    print("A user with this email already exists")
                    return CreateUserMutation(
                        create_user=CreateUserError(
                            error_type=EMAIL_NOT_UNIQUE,
                            error_message=
                            "A user with this email already exists"))
            except ObjectDoesNotExist as exc:
                # No user with this email address exists, go on
                pass

        if len(username) < 3:
            return CreateUserMutation(
                create_user=CreateUserError(
                    error_type=USERNAME_TO_SHORT,
                    error_message="Username must be at least 3 characters long."
                ))
        if len(password) < 8:
            return CreateUserMutation(
                create_user=CreateUserError(
                    error_type=PASSWORD_TO_SHORT,
                    error_message="Password must be at least 8 characters long."
                ))

        try:
            user = User.objects.create_user(
                username=username, email=email, password=password)
        except IntegrityError as exc:
            print(exc)
            return CreateUserMutation(
                create_user=CreateUserError(
                    error_type=USERNAME_NOT_UNIQUE, error_message=str(exc)))

        return CreateUserMutation(create_user=CreateUserSuccess(user))
