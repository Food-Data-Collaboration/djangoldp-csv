from urllib import parse

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import render
from django.urls import reverse
from djangoldp.models import Model
from rest_framework.response import Response
from rest_framework.views import APIView
from djangoldp_csv.errors import FieldParsingError
from djangoldp_csv.forms import CSVImportForm
from djangoldp_csv.permissions import IsSuperuser
from djangoldp_csv.utils import get_all_model_rdf_types


class BaseCSVImportView(APIView):
    """
    A basic view for interfacing with CSV import forms.
    """

    permission_classes = [IsSuperuser]

    def get_form_class(self, *args, **kwargs):
        return CSVImportForm(*args, **kwargs)

    def process_form(self, form, model_type=None):
        with transaction.atomic():
            form.process_all_files(model_type)


class CSVImportView(BaseCSVImportView):
    """
    An implementation of CSV import view which allows for model selection,
    via query parameters and server settings.
    """

    def resolve_model_type(self, request):
        # Resolve the model type of the CSV file contents.
        # We consider the query parameter and the explicit contents of the CSV file,
        # but we could expand this in future to fallback on requesting the URI of a given row,
        # or to compare the fields included with the models configured.
        if request.GET.get("model-type") is None:
            raise ObjectDoesNotExist()
        model_type = Model.get_subclass_with_rdf_type(request.GET["model-type"])
        if model_type is not None:
            return model_type
        raise ObjectDoesNotExist()

    def _given_model_permitted(self, request):
        return "model-type" in request.GET and (
            not hasattr(settings, "DJANGOLDP_CSV_MODELS")
            or request.GET["model-type"] in settings.DJANGOLDP_CSV_MODELS
        )

    def render_csv_import(self, request, success=False):
        return render(
            request,
            "csv_import.html",
            {
                "form": self.get_form_class(),
                "success": success,
                "model_type": parse.quote_plus(request.GET["model-type"]),
            },
        )

    def render_model_select(self, request):
        model_types = getattr(
            settings, "DJANGOLDP_CSV_MODELS", get_all_model_rdf_types()
        )
        context = {
            "model_types": [
                {
                    "label": m,
                    "link": f"{reverse('djangoldp-csv-import')}?model-type={parse.quote_plus(m)}",
                }
                for m in model_types
            ]
        }
        return render(request, "model_select.html", context)

    def get(self, request, *args, **kwargs):
        if not self._given_model_permitted(request):
            return self.render_model_select(request)
        return self.render_csv_import(request)

    def post(self, request, *args, **kwargs):
        form = self.get_form_class(request.POST, request.FILES)
        if not form.is_valid():
            return Response(form.errors, status=400)

        # Verify model given is permitted.
        if not self._given_model_permitted(request):
            return Response(
                {"error": "No model could be found with the requested type"}, status=404
            )

        try:
            # Retrieve model configured with given RDF type (if any).
            model_type = self.resolve_model_type(request)
            self.process_form(form, model_type)
        except FieldParsingError:
            return Response(
                {
                    "error": (
                        "None of the fields in this CSV could be parsed. "
                        "Please use URLs to RDF properties as they are configured in the DjangoLDP model"
                    )
                },
                status=400,
            )
        except ObjectDoesNotExist:
            return Response(
                {"error": "No model could be found with the requested type"}, status=404
            )

        return self.render_csv_import(request, success=True)
