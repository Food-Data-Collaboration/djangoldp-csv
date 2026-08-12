from django.contrib.auth.models import AbstractUser
from django.db import models
from djangoldp import fields
from djangoldp.models import Model
from djangoldp.permissions import OwnerPermissions, ReadAndCreate

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
        max_length=255,
    )
    supplied_by = fields.ForeignKey(
        "Enterprise",
        rdf_type="dfc-b:suppliedBy",
        related_rdf_type="dfc-b:supplies",
        blank=True,
        null=True,
        related_name="supplied_products",
        on_delete=models.SET_NULL,
    )

    class Meta(Model.Meta):
        rdf_type = "dfc-b:SuppliedProduct"


class Enterprise(Model):
    name = fields.TextField(
        rdf_type="dfc-b:name",
        blank=True,
        null=True,
    )  # xsd:String

    class Meta(Model.Meta):
        rdf_type = "dfc-b:Organization"
