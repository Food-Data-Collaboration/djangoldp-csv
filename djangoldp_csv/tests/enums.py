from django.db import models


DFC_PT_URL = "https://github.com/datafoodconsortium/taxonomies/releases/latest/download/productTypes.rdf"


class ProductType(models.TextChoices):
    EXAMPLE_PRODUCT = (f"{DFC_PT_URL}#example-product", "Example product")
