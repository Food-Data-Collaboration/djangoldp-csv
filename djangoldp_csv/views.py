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

    def _process_csv_fields(self, model, row):
        """Attempts to resolve a dictionary mapping model field names to RDF properties from the CSV"""
        fields = {}

        for key in row.keys():
            model_field = model.get_field_from_rdf_type(key)
            if model_field is None:
                # NOTE: A future version of DjangoLDP will provide a JSONField where we can store additional fields.
                logger.warning(
                    f"WARN unable to find model field for value {key} on {model}. Not storing this data"
                )
                continue
            fields[model_field.name] = key

        return fields

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

        # Attempt to resolve the fields from the document.
        first_row = next(imported_file)
        fields = self._process_csv_fields(model_type, first_row)

        rows_to_create = []
        rows_to_update = []

        def process_row(row):
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

            for key in fields.keys():
                setattr(instance, key, row[fields[key]])

            if row_exists:
                rows_to_update.append(instance)
            else:
                rows_to_create.append(instance)

        # Workaround for performance:
        # We only want to process the fields once in the CSV, so we used next() once already to process them.
        # Process this row first and then return to the stream.
        process_row(first_row)
        for row in imported_file:
            process_row(row)

        model_type.objects.bulk_create(rows_to_create)
        model_type.objects.bulk_update(rows_to_update, fields=fields.keys())
        return render(
            request, "csv_import.html", {"form": CSVImportForm(), "success": True}
        )
