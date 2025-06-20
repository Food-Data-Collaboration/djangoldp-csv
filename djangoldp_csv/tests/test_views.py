import os

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from djangoldp_csv.tests.enums import ProductType
from djangoldp_csv.tests.models import SuppliedProduct


class TestCSVImportView(APITestCase):
    def setUpLoggedInUser(self, is_staff=False):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="john",
            email="jlennon@beatles.com",
            password="glass onion",
            first_name="John",
            is_staff=is_staff,
        )
        self.client.force_authenticate(self.user)

    def test_import_csv(self):
        """Uploading the test CSV to POST djangoldp-csv-import."""
        self.setUpLoggedInUser(is_staff=True)

        csv_path = os.path.join(os.path.dirname(__file__), "import.csv")
        with open(csv_path) as f:
            response = self.client.post(
                reverse("djangoldp-csv-import") + "?model-type=dfc-b%3ASuppliedProduct",
                {"csv": f},
            )
            assert response.status_code == 201

        # Exactly one product is created and it has the fields from the CSV.
        p = SuppliedProduct.objects.get()
        assert p.urlid == "http://test.host/suppliedproducts/1/"
        assert p.name == "Example"
        assert p.has_type == ProductType.EXAMPLE_PRODUCT
