from django.db import models


DFC_PT_URL = "https://raw.githubusercontent.com/datafoodconsortium/taxonomies/refs/heads/main/productTypes.rdf"


class ProductType(models.TextChoices):
    EXAMPLE_PRODUCT = (f"{DFC_PT_URL}#example-product", "Example product")
