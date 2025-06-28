import csv
import io
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from djangoldp.models import Model
from rest_framework.response import Response
from rest_framework.views import APIView
from djangoldp_csv.forms import CSVImportForm
from djangoldp_csv.permissions import IsSuperuser


logger = logging.getLogger("djangoldp")


class CSVImportView(APIView):
    permission_classes = [IsSuperuser]

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

    def get(self, request, *args, **kwargs):
        return render(request, "csv_import.html", {"form": CSVImportForm()})

    def post(self, request, *args, **kwargs):
        form = CSVImportForm(request.POST, request.FILES)
        if not form.is_valid():
            return Response(form.errors, status=400)

        try:
            model_type = self.resolve_model_type(request)
        except ObjectDoesNotExist:
            return Response(
                {"error": "No model could be found with the requested type"}, status=404
            )

        imported_file = csv.DictReader(
            io.StringIO(request.FILES["csv"].read().decode("utf-8"))
        )

        rows_to_create = []
        rows_to_update = []
        fields = []

        for row in imported_file:
            # Fetch instance if it already exists, else create a new row.
            row_exists = True
            instance = (
                model_type.objects.filter(urlid=row["urlid"]).first()
                if "urlid" in row
                else None
            )
            if instance is None:
                row_exists = False
                instance = model_type()

            # Parse RDF properties of row.
            for field in row.keys():
                model_field = model_type.get_field_from_rdf_type(field)
                if model_field is None:
                    # NOTE: A future version of DjangoLDP will provide a JSONField where we can store additional fields.
                    logger.warning(
                        f"WARN unable to find model field for value {field} on {model_type}. Not storing this data"
                    )
                    continue
                setattr(instance, model_field.name, row[field])
                fields.append(model_field.name)

            if row_exists:
                rows_to_update.append(instance)
            else:
                rows_to_create.append(instance)

        model_type.objects.bulk_create(rows_to_create)
        model_type.objects.bulk_update(rows_to_update, fields=fields)
        return render(
            request, "csv_import.html", {"form": CSVImportForm(), "success": True}
        )
