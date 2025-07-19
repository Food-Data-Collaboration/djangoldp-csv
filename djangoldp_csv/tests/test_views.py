import os

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from djangoldp_csv.tests.enums import ProductType
from djangoldp_csv.tests.models import Enterprise, SuppliedProduct


class TestCSVImportView(APITestCase):
    def setUpLoggedInUser(self, **kwargs):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="john",
            email="jlennon@beatles.com",
            password="glass onion",
            first_name="John",
            **kwargs,
        )
        self.client.force_authenticate(self.user)

    def open_test_csv(self, filename="import.csv"):
        csv_path = os.path.join(os.path.dirname(__file__), filename)
        return open(csv_path)

    def test_select_model(self):
        self.setUpLoggedInUser(is_superuser=True)

        response = self.client.get(reverse("djangoldp-csv-import"))
        assert response.status_code == 200
        self.assertTemplateUsed(response, "model_select.html")

    @override_settings(DJANGOLDP_CSV_MODELS=["dfc-b:SuppliedProduct"])
    def test_select_model_excluded(self):
        self.setUpLoggedInUser(is_superuser=True)

        allowed_url = (
            reverse("djangoldp-csv-import") + "?model-type=dfc-b%3ASuppliedProduct"
        )
        forbidden_url = (
            reverse("djangoldp-csv-import") + "?model-type=dfc-b%3AEnterprise"
        )

        response = self.client.get(allowed_url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "csv_import.html")

        response = self.client.get(forbidden_url)
        assert response.status_code == 200
        self.assertTemplateUsed(response, "model_select.html")

        with self.open_test_csv() as f:
            response = self.client.post(forbidden_url, {"csv": f})
            assert response.status_code == 404
            assert (
                response.data["error"]
                == "No model could be found with the requested type"
            )
            assert Enterprise.objects.count() == 0

    def test_import_csv(self):
        """Uploading the test CSV to POST djangoldp-csv-import."""
        self.setUpLoggedInUser(is_superuser=True)

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

        # An Enterprise should also have been created
        e = Enterprise.objects.get()
        assert (
            e.urlid == "http://localhost:8000/enterprises/1/"
        )  # value from import.csv
        assert p.supplied_by == e

        # Re-uploading the CSV will perform a PUT operation.
        with self.open_test_csv() as f:
            p.name = "Modified Example"
            p.save()

            response = self.client.post(
                reverse("djangoldp-csv-import") + "?model-type=dfc-b%3ASuppliedProduct",
                {"csv": f},
            )
            assert response.status_code == 200

        p = SuppliedProduct.objects.get()
        assert p.urlid == "http://test.host/suppliedproducts/1/"
        assert p.name == "Example"
        assert p.has_type == ProductType.EXAMPLE_PRODUCT

        assert Enterprise.objects.count() == 1

    def test_import_csv_none_passed(self):
        self.setUpLoggedInUser(is_superuser=True)
        response = self.client.post(reverse("djangoldp-csv-import"))
        assert response.status_code == 400

    def test_import_csv_no_model_type_passed(self):
        self.setUpLoggedInUser(is_superuser=True)

        with self.open_test_csv() as f:
            response = self.client.post(reverse("djangoldp-csv-import"), {"csv": f})
            assert response.status_code == 404
            assert (
                response.data["error"]
                == "No model could be found with the requested type"
            )

    def test_import_csv_model_type_does_not_exist(self):
        self.setUpLoggedInUser(is_superuser=True)

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

    def test_import_csv_not_superuser(self):
        self.setUpLoggedInUser(is_superuser=False, is_staff=True)

        with self.open_test_csv() as f:
            response = self.client.post(
                reverse("djangoldp-csv-import") + "?model-type=dfc-b%3ASuppliedProduct",
                {"csv": f},
            )
            assert response.status_code == 403

    def test_import_fieldless_csv(self):
        # Upload a CSV without any RDF-mapped fields.
        self.setUpLoggedInUser(is_superuser=True)

        with self.open_test_csv(filename="error-fieldless-test.csv") as f:
            response = self.client.post(
                reverse("djangoldp-csv-import") + "?model-type=dfc-b%3ASuppliedProduct",
                {"csv": f},
            )
            assert response.status_code == 400
            assert SuppliedProduct.objects.count() == 0
