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

    def open_test_csv(self):
        csv_path = os.path.join(os.path.dirname(__file__), "import.csv")
        return open(csv_path)

    def test_import_csv(self):
        """Uploading the test CSV to POST djangoldp-csv-import."""
        self.setUpLoggedInUser(is_staff=True)

        with self.open_test_csv() as f:
            response = self.client.post(
                reverse("djangoldp-csv-import") + "?model-type=dfc-b%3ASuppliedProduct",
                {"csv": f},
            )
            assert response.status_code == 200

        # Exactly one product is created and it has the fields from the CSV.
        p = SuppliedProduct.objects.get()
        assert p.urlid == "http://test.host/suppliedproducts/1/"
        assert p.name == "Example"
        assert p.has_type == ProductType.EXAMPLE_PRODUCT

    def test_import_csv_none_passed(self):
        self.setUpLoggedInUser(is_staff=True)
        response = self.client.post(reverse("djangoldp-csv-import"))
        assert response.status_code == 400

    def test_import_csv_no_model_type_passed(self):
        self.setUpLoggedInUser(is_staff=True)

        with self.open_test_csv() as f:
            response = self.client.post(reverse("djangoldp-csv-import"), {"csv": f})
            assert response.status_code == 404
            assert (
                response.data["error"]
                == "No model could be found with the requested type"
            )

    def test_import_csv_model_type_does_not_exist(self):
        self.setUpLoggedInUser(is_staff=True)

        with self.open_test_csv() as f:
            response = self.client.post(
                reverse("djangoldp-csv-import") + "?model-type=dfc-b%3ADoesNotExist",
                {"csv": f},
            )
            assert response.status_code == 404
            assert (
                response.data["error"]
                == "No model could be found with the requested type"
            )

    def test_import_csv_not_staff(self):
        self.setUpLoggedInUser(is_staff=False)

        with self.open_test_csv() as f:
            response = self.client.post(
                reverse("djangoldp-csv-import") + "?model-type=dfc-b%3ASuppliedProduct",
                {"csv": f},
            )
            assert response.status_code == 403
