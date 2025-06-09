from django.contrib.auth.models import AbstractUser
from djangoldp.models import Model
from djangoldp.permissions import ReadAndCreate, OwnerPermissions


class User(AbstractUser, Model):
    class Meta(AbstractUser.Meta, Model.Meta):
        ordering = ["pk"]
        serializer_fields = [
            "@id",
            "username",
            "first_name",
            "last_name",
            "email",
        ]
        permission_classes = [ReadAndCreate | OwnerPermissions]
        rdf_type = "foaf:user"
        nested_fields = []


class Product(Model):
    class Meta(Model.Meta):
        rdf_type = "https://example_ontology.com/#Product"
