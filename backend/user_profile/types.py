from django.contrib.auth import get_user_model
from graphene_django.types import DjangoObjectType

User = get_user_model()


class UserType(DjangoObjectType):
    class Meta:
        model = User
        only_fields = ["id", "username", "email"]
