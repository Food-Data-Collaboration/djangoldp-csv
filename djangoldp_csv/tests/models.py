from django.contrib.auth.models import AbstractUser
from djangoldp import fields
from djangoldp.models import Model
from djangoldp.permissions import ReadAndCreate, OwnerPermissions

from .enums import ProductType


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


class SuppliedProduct(Model):
    name = fields.TextField(
        rdf_type="dfc-b:name",
        blank=True,
        null=True,
    )  # xsd:String
    has_type = fields.CharField(
        rdf_type="dfc-b:hasType",
        verbose_name="has_type",
        choices=ProductType.choices,
        blank=True,
        null=True,
    )

    class Meta(Model.Meta):
        rdf_type = "dfc-b:SuppliedProduct"
